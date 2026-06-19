"""
GUI gửi/nhận dữ liệu UART với STM32
Yêu cầu: pip install pyserial
Chạy: python3 uart_gui.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import queue
import time
import os


class UartGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("UART STM32 <-> PC")
        self.root.geometry("700x550")

        self.ser = None
        self.read_thread = None
        self.is_running = False
        self.rx_queue = queue.Queue()

        self.selected_file = None
        self.is_sending_file = False

        self._build_ui()
        self._refresh_ports()

        # Định kỳ kiểm tra queue để cập nhật GUI (an toàn thread)
        self.root.after(50, self._process_rx_queue)

    # ---------------- UI ----------------
    def _build_ui(self):
        # Frame cấu hình kết nối
        conn_frame = ttk.LabelFrame(self.root, text="Kết nối")
        conn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(conn_frame, text="Cổng:").grid(row=0, column=0, padx=5, pady=5)
        self.port_combo = ttk.Combobox(conn_frame, width=15, state="readonly")
        self.port_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(conn_frame, text="Refresh", command=self._refresh_ports).grid(
            row=0, column=2, padx=5, pady=5
        )

        ttk.Label(conn_frame, text="Baudrate:").grid(row=0, column=3, padx=5, pady=5)
        self.baud_combo = ttk.Combobox(
            conn_frame,
            width=10,
            values=["9600", "19200", "38400", "57600", "115200", "230400"],
        )
        self.baud_combo.set("115200")
        self.baud_combo.grid(row=0, column=4, padx=5, pady=5)

        self.connect_btn = ttk.Button(
            conn_frame, text="Kết nối", command=self._toggle_connect
        )
        self.connect_btn.grid(row=0, column=5, padx=5, pady=5)

        self.status_label = ttk.Label(conn_frame, text="Chưa kết nối", foreground="red")
        self.status_label.grid(row=0, column=6, padx=10, pady=5)

        # Frame gửi dữ liệu - pack TRƯỚC với side="bottom" để luôn neo ở đáy,
        # không bị khung nhận (expand=True) đè mất khi resize cửa sổ nhỏ
        tx_frame = ttk.LabelFrame(self.root, text="Gửi dữ liệu lên STM32")
        tx_frame.pack(side="bottom", fill="x", padx=10, pady=5)

        self.tx_entry = ttk.Entry(tx_frame, font=("Consolas", 10))
        self.tx_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.tx_entry.bind("<Return>", lambda event: self._send_data())

        self.add_newline = tk.BooleanVar(value=True)
        ttk.Checkbutton(tx_frame, text="Thêm \\n", variable=self.add_newline).pack(
            side="left", padx=5
        )

        ttk.Button(tx_frame, text="Gửi", command=self._send_data).pack(
            side="left", padx=5, pady=5
        )

        # Frame gửi file - cũng neo ở đáy, nằm trên khung gửi text
        file_frame = ttk.LabelFrame(self.root, text="Gửi file lên STM32")
        file_frame.pack(side="bottom", fill="x", padx=10, pady=5)

        self.file_path_label = ttk.Label(
            file_frame, text="Chưa chọn file", foreground="gray"
        )
        self.file_path_label.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        ttk.Button(file_frame, text="Chọn file...", command=self._browse_file).pack(
            side="left", padx=5, pady=5
        )

        self.send_file_btn = ttk.Button(
            file_frame, text="Gửi file", command=self._send_file
        )
        self.send_file_btn.pack(side="left", padx=5, pady=5)

        self.file_progress = ttk.Progressbar(
            file_frame, orient="horizontal", mode="determinate", length=150
        )
        self.file_progress.pack(side="left", padx=5, pady=5)

        self.file_progress_label = ttk.Label(file_frame, text="")
        self.file_progress_label.pack(side="left", padx=5)

        # Frame dữ liệu nhận
        rx_frame = ttk.LabelFrame(self.root, text="Dữ liệu nhận từ STM32")
        rx_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.rx_text = scrolledtext.ScrolledText(
            rx_frame, wrap="word", state="disabled", font=("Consolas", 10)
        )
        self.rx_text.pack(fill="both", expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(rx_frame)
        btn_frame.pack(fill="x", padx=5, pady=2)

        ttk.Button(btn_frame, text="Xóa màn hình", command=self._clear_rx).pack(
            side="left"
        )

        self.hex_view = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            btn_frame, text="Hiển thị dạng HEX", variable=self.hex_view
        ).pack(side="left", padx=10)

        self.autoscroll = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            btn_frame, text="Tự động cuộn", variable=self.autoscroll
        ).pack(side="left", padx=10)

    # ---------------- Port handling ----------------
    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo["values"] = ports
        if ports:
            self.port_combo.set(ports[0])
        else:
            self.port_combo.set("")

    # ---------------- Connect / Disconnect ----------------
    def _toggle_connect(self):
        if self.ser and self.ser.is_open:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        port = self.port_combo.get()
        baud = self.baud_combo.get()

        if not port:
            messagebox.showwarning("Cảnh báo", "Chưa chọn cổng UART")
            return
        try:
            baudrate = int(baud)
        except ValueError:
            messagebox.showwarning("Cảnh báo", "Baudrate không hợp lệ")
            return

        try:
            self.ser = serial.Serial(port, baudrate, timeout=0.1)
        except serial.SerialException as e:
            messagebox.showerror("Lỗi kết nối", str(e))
            return

        self.is_running = True
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()

        self.connect_btn.config(text="Ngắt kết nối")
        self.status_label.config(text=f"Đã kết nối {port} @ {baudrate}", foreground="green")

    def _disconnect(self):
        self.is_running = False
        if self.read_thread:
            self.read_thread.join(timeout=1)

        if self.ser and self.ser.is_open:
            self.ser.close()

        self.connect_btn.config(text="Kết nối")
        self.status_label.config(text="Chưa kết nối", foreground="red")

    # ---------------- Reading thread ----------------
    def _read_loop(self):
        while self.is_running:
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    if data:
                        self.rx_queue.put(data)
                else:
                    time.sleep(0.01)
            except serial.SerialException:
                self.rx_queue.put(b"\n[Mat ket noi UART]\n")
                self.is_running = False
                break

    def _process_rx_queue(self):
        while not self.rx_queue.empty():
            data = self.rx_queue.get()
            self._append_rx(data)
        self.root.after(50, self._process_rx_queue)

    def _append_rx(self, data: bytes):
        if self.hex_view.get():
            text = data.hex(" ") + " "
        else:
            text = data.decode("utf-8", errors="replace")

        self.rx_text.config(state="normal")
        self.rx_text.insert("end", text)
        self.rx_text.config(state="disabled")

        if self.autoscroll.get():
            self.rx_text.see("end")

    def _clear_rx(self):
        self.rx_text.config(state="normal")
        self.rx_text.delete("1.0", "end")
        self.rx_text.config(state="disabled")

    # ---------------- Sending ----------------
    def _send_data(self):
        if not (self.ser and self.ser.is_open):
            messagebox.showwarning("Cảnh báo", "Chưa kết nối UART")
            return

        text = self.tx_entry.get()
        if not text:
            return

        payload = text
        if self.add_newline.get():
            payload += "\n"

        try:
            self.ser.write(payload.encode("utf-8"))
        except serial.SerialException as e:
            messagebox.showerror("Lỗi gửi dữ liệu", str(e))
            return

        self.tx_entry.delete(0, "end")

    # ---------------- Sending file ----------------
    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Chọn file để gửi",
            filetypes=[("Binary files", "*.bin"), ("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.selected_file = path
            size = os.path.getsize(path)
            self.file_path_label.config(
                text=f"{os.path.basename(path)} ({size} bytes)", foreground="black"
            )

            # Gửi ngay 1 dòng size xuống STM32 khi vừa load file (nếu đã kết nối UART)
            if self.ser and self.ser.is_open:
                try:
                    size_line = f"{size}\n"
                    self.ser.write(size_line.encode("utf-8"))
                    self.file_progress_label.config(text=f"Đã gửi size: {size} bytes")
                except serial.SerialException as e:
                    messagebox.showerror("Lỗi gửi size", str(e))
            else:
                messagebox.showwarning(
                    "Cảnh báo", "Chưa kết nối UART, chưa gửi được size file"
                )

    def _send_file(self):
        if not (self.ser and self.ser.is_open):
            messagebox.showwarning("Cảnh báo", "Chưa kết nối UART")
            return

        if not self.selected_file:
            messagebox.showwarning("Cảnh báo", "Chưa chọn file để gửi")
            return

        if self.is_sending_file:
            messagebox.showinfo("Thông báo", "Đang gửi file, vui lòng đợi...")
            return

        # Chạy gửi file trong thread riêng để không làm treo GUI
        self.is_sending_file = True
        self.send_file_btn.config(state="disabled")
        threading.Thread(target=self._send_file_worker, daemon=True).start()

    def _send_file_worker(self):
        CHUNK_SIZE = 256  # số byte gửi mỗi lần, có thể chỉnh theo buffer UART của STM32

        try:
            total_size = os.path.getsize(self.selected_file)
            sent_size = 0

            self.root.after(0, lambda: self.file_progress.config(value=0))

            with open(self.selected_file, "rb") as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break

                    self.ser.write(chunk)
                    sent_size += len(chunk)

                    percent = int(sent_size * 100 / total_size) if total_size else 100
                    self.root.after(0, self._update_file_progress, percent, sent_size, total_size)

                    # Cho STM32 thời gian xử lý/lưu flash giữa các chunk (chỉnh nếu cần)
                    time.sleep(0.01)

            self.root.after(0, self._file_send_done, True, None)

        except (serial.SerialException, OSError) as e:
            self.root.after(0, self._file_send_done, False, str(e))

    def _update_file_progress(self, percent, sent, total):
        self.file_progress.config(value=percent)
        self.file_progress_label.config(text=f"{sent}/{total} bytes ({percent}%)")

    def _file_send_done(self, success, error_msg):
        self.is_sending_file = False
        self.send_file_btn.config(state="normal")

        if success:
            self.file_progress_label.config(text="Đã gửi xong")
        else:
            self.file_progress_label.config(text="Lỗi gửi file")
            messagebox.showerror("Lỗi gửi file", error_msg)

    # ---------------- Cleanup ----------------
    def on_close(self):
        self._disconnect()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = UartGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
