# Bootloader Firmware Update (STM32 - UART)

Dự án bootloader cho STM32F4, hỗ trợ cập nhật firmware ứng dụng qua UART. Bootloader sẽ kiểm tra trạng thái nút nhấn để chọn chạy Application 1 hoặc Application 2, hoặc nhận firmware mới gửi từ PC qua giao diện UART GUI (Python).

## Cấu trúc thư mục

```
Bootloader_firmware_update/
├── Bootloader/              # Project STM32CubeIDE của Bootloader
├── Firmware_update_uart/    # Project STM32CubeIDE của Application (firmware nhận update qua UART)
├── FW_Led_orange.bin        # File firmware mẫu (LED cam) để test update
├── FW_Led_red.bin           # File firmware mẫu (LED đỏ) để test update
├── UART_GUI.py               # Công cụ GUI Python để gửi/nhận dữ liệu UART và gửi file firmware
└── README.md
```

## Yêu cầu phần cứng

- Board STM32F4 (ví dụ STM32F411VETx)
- Mạch chuyển USB-UART (USB to TTL) nếu không dùng UART tích hợp ST-Link
- Cáp kết nối TX/RX/GND giữa board và PC (chú ý: TX của mạch nối vào RX của STM32 và ngược lại)

## Yêu cầu phần mềm

- [STM32CubeIDE](https://www.st.com/en/development-tools/stm32cubeide.html) để build và flash firmware
- Python 3 và các thư viện:
  ```bash
  pip install pyserial
  sudo apt install python3-tk   # nếu chạy trên Linux và chưa có tkinter
  ```

## Cấu hình linker script (.ld) cho từng firmware

Mỗi project (Bootloader, Application) cần chỉnh đúng vùng nhớ `FLASH` trong file linker script `.ld` (Project → file `STM32F411VETX_FLASH.ld`) để khớp với địa chỉ mà Bootloader sẽ nhảy tới:

| Firmware | Địa chỉ bắt đầu (`ORIGIN`) | Kích thước (`LENGTH`) |
|---|---|---|
| Bootloader | `0x08000000` | `16K` |
| Firmware_update_uart (App2 - nhận update qua UART) | `0x08004000` | `16K` |
| Firmware build ra `.bin` để nạp vào board (App1, ví dụ `FW_Led_orange.bin`, `FW_Led_red.bin`) | `0x08008000` | `16K` |

Ví dụ đoạn cấu hình trong file `.ld` cho firmware App1:

```ld
MEMORY
{
  FLASH (rx)      : ORIGIN = 0x08008000, LENGTH = 16K
  RAM (xrw)        : ORIGIN = 0x20000000, LENGTH = 128K
}
```

> Lưu ý: cần sửa đúng giá trị `ORIGIN` và `LENGTH` trong mục `FLASH` của file `.ld`, không sửa nhầm vùng `RAM`. Sau khi sửa `.ld`, build lại project để file `.bin` xuất ra đúng được định vị tại địa chỉ flash mong muốn.

## Cách sử dụng

### 1. Build và flash Bootloader

1. Mở project trong thư mục `Bootloader/` bằng STM32CubeIDE.
2. Build project (Project → Build Project).
3. Flash bootloader vào board qua ST-Link:
   ```bash
   st-flash write Bootloader/Debug/Bootloader.bin 0x08000000
   ```
   (hoặc dùng nút Run/Debug trực tiếp trong STM32CubeIDE)

### 2. Build firmware Application

1. Mở project trong thư mục `Firmware_update_uart/` bằng STM32CubeIDE.
2. Build project để tạo ra file `.bin` (ví dụ tương tự `FW_Led_orange.bin`, `FW_Led_red.bin`).
3. Project này được build và flash vào vùng nhớ flash bắt đầu từ địa chỉ **`0x08004000`** (cần cấu hình đúng địa chỉ này trong linker script `.ld` của project, mục `FLASH` origin).
3. Flash bootloader vào board qua ST-Link:
   ```bash
   st-flash write Bootloader/Debug/Firmware_update_uart.bin 0x08008000
   ```
   (hoặc dùng nút Run/Debug trực tiếp trong STM32CubeIDE)

### 3. Vào chế độ cập nhật firmware qua UART (App2)

Trước khi gửi firmware mới, cần đưa board vào chế độ chờ nhận UART (App2 = `Firmware_update_uart`):

1. **Giữ nút User Button** (không thả ra).
2. Nhấn **nút Reset** trên board (trong khi vẫn đang giữ User Button).
3. Có thể thả nút User Button ra sau khi reset xong.

→ Bootloader đọc trạng thái nút lúc reset, thấy đang được giữ (nút ở mức tương ứng) nên sẽ nhảy vào App2 (`Firmware_update_uart`), sẵn sàng nhận dữ liệu firmware mới từ `UART_GUI.py`.

Nếu **không giữ nút** lúc reset → bootloader sẽ nhảy vào chạy **App1** (firmware bình thường, ví dụ `FW_Led_orange.bin`/`FW_Led_red.bin`).

### 4. Cập nhật firmware qua UART bằng GUI

1. Cắm mạch UART-USB vào PC, xác định cổng UART đang dùng:
   ```bash
   ls /dev/tty*
   ```
2. Chạy công cụ GUI:
   ```bash
   python3 UART_GUI.py
   ```
3. Trong GUI:
   - Chọn **cổng** UART và **baudrate** đúng với cấu hình UART trên STM32.
   - Bấm **Kết nối**.
   - Bấm **Chọn file...** trong khung "Gửi file lên STM32", chọn 1 trong các file `.bin` có sẵn (`FW_Led_orange.bin` hoặc `FW_Led_red.bin`) hoặc file `.bin` vừa build từ project `Firmware_update_uart/`.
     - Khi chọn file, GUI sẽ tự gửi 1 dòng chứa **size** của file xuống STM32 trước.
   - Bấm **Gửi file** để truyền nội dung firmware xuống board.
   - Theo dõi tiến trình gửi qua thanh progress bar, và xem log/phản hồi từ STM32 ở khung "Dữ liệu nhận từ STM32".
## Hướng dẫn sử dụng GUI (từng bước thực tế)

Dưới đây là quy trình cập nhật firmware đầy đủ, theo đúng log thực tế nhận được từ STM32 khi dùng `UART_GUI.py`:

**Bước 1: Mở GUI và kết nối**
```bash
python3 UART_GUI.py
```
- Chọn **Cổng** (ví dụ `/dev/ttyUSB0`)
- Chọn **Baudrate** (ví dụ `9600`, phải khớp với cấu hình UART trên STM32)
- Bấm **Kết nối** → trạng thái chuyển thành "Đã kết nối /dev/ttyUSB0"

**Bước 2: Vào Firmware Update Mode trên board**
- Giữ **nút User Button**
- Nhấn **nút Reset** (vẫn giữ User Button)
- Thả nút ra sau khi reset xong

→ Khung "Dữ liệu nhận từ STM32" sẽ hiện:
```
UPDATE FIRMWARE MODE
PLEASE SEND FW SIZE
```
Đây là dấu hiệu xác nhận board đã vào đúng chế độ chờ nhận firmware mới (App2 - `Firmware_update_uart`), đang chờ PC gửi size.

**Bước 3: Chọn file firmware .bin**
- Bấm **Chọn file...** trong khung "Gửi file lên STM32"
- Chọn file `.bin` cần nạp (ví dụ `FW_1.bin`)
- Ngay khi chọn xong, GUI **tự động gửi size file xuống STM32**

→ Khung nhận sẽ hiện thêm dòng:
```
PLEASE SEND FW
```
Báo board đã nhận được size và đang chờ nhận dữ liệu firmware thực tế. Khung "Gửi file lên STM32" cũng hiển thị tên file + size (ví dụ `FW_1.bin (5016 bytes)`).

**Bước 4: Gửi file firmware**
- Bấm **Gửi file**

→ Khung nhận sẽ hiện thêm:
```
Waiting for update FW
```
Thanh progress bar chạy tới 100%, label hiển thị "Đã gửi xong". Sau khi STM32 ghi xong toàn bộ dữ liệu vào flash, khung nhận sẽ hiện:
```
Success
```
→ Xác nhận firmware mới đã được ghi thành công vào vùng nhớ flash tương ứng.

**Bước 5: Chạy firmware mới**
- Nhấn **nút Reset** (lần này **không giữ** User Button)

→ Bootloader sẽ nhảy vào chạy firmware vừa được cập nhật (App1, địa chỉ `0x08008000`) thay vì vào lại Firmware Update Mode.

## Sơ đồ hoạt động tổng quát

```
PC (UART_GUI.py) --[UART: size + data]--> Bootloader (STM32)
                                              │
                                              ├── Erase sector tương ứng
                                              ├── Ghi (program) dữ liệu vào flash
                                              └── Sau khi reset: nhảy vào Application 1 hoặc 2
                                                  tùy theo trạng thái nút nhấn
```

## Ghi chú

- Giao thức truyền hiện tại: gửi 1 dòng text chứa kích thước file (`<size>\n`), sau đó gửi toàn bộ nội dung file dạng raw byte theo từng chunk 256 byte.
- `Firmware_update_uart` được flash vào địa chỉ **`0x08004000`** trong bộ nhớ flash của STM32 — Bootloader sẽ ghi dữ liệu nhận được qua UART vào đúng vùng nhớ này.
- Cần đảm bảo baudrate giữa PC và STM32 khớp nhau, và firmware Bootloader đã được cấu hình UART đúng chân TX/RX.
- Các file `.bin` mẫu (`FW_Led_orange.bin`, `FW_Led_red.bin`) dùng để test nhanh quá trình update mà không cần build lại firmware.

