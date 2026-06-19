/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "string.h"
#include <stdio.h>

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
char rev_dt[16384]={0};
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
void flash_erase_sector(char sector);
void flash_program(uint8_t *addr, uint8_t data);
void uart_init(void);
void transmit_1char(char data);
void transmit_string(char* data);
char recive_char(void);
void dma_uart1_init(int size);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  /* USER CODE BEGIN 2 */
  uart_init();
  transmit_string("UPDATE FIRMWARE MODE\n");
  transmit_string("PLEASE SEND FW SIZE\n");
  int i =0;
  while(strstr(rev_dt,"\n")==NULL)
  {
	  rev_dt[i++] =recive_char();
  }
  int fw_size = 0;
  sscanf(rev_dt,"%d\n",&fw_size);
  transmit_string("PLEASE SEND FW\n");
  i = 0;
  while(i<fw_size){
	  rev_dt[i++] =recive_char();
  }
  transmit_string("Waiting for update FW\n");
  flash_erase_sector(2);
  for(int i = 0;i<fw_size;i++)
  {
	  flash_program((uint8_t*)(0x08008000+i), rev_dt[i]);
  }
  transmit_string("Success\n");
  /* USER CODE END 2 */
  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */
	  HAL_Delay(1000);
    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOA_CLK_ENABLE();

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */
void flash_erase_sector(char sector)
{
	while(((FLASH->CR>>FLASH_CR_LOCK_Pos)&1)==1){
		FLASH->KEYR = 0x45670123;
		FLASH->KEYR = 0xCDEF89AB;
	}// unlock FLASH_Register
	//sequence erase sector
	while(((FLASH->SR>>FLASH_SR_BSY_Pos)&1)==1){}//check bit BSY
	FLASH->CR |=(FLASH_CR_SER);
	FLASH->CR &=~(0b111<<FLASH_CR_SNB_Pos);
	FLASH->CR |= (sector<<FLASH_CR_SNB_Pos);
	FLASH->CR |= (FLASH_CR_STRT);


}
void flash_program(uint8_t *addr, uint8_t data)
{
	while(((FLASH->CR>>FLASH_CR_LOCK_Pos)&1)==1){
		FLASH->KEYR = 0x45670123;
		FLASH->KEYR = 0xCDEF89AB;
	}// unlock FLASH_Register
	//sequence program flash address
	while(((FLASH->SR>>FLASH_SR_BSY_Pos)&1)==1){} //check bit BSY
	FLASH->CR &=~(0xf<<FLASH_CR_PSIZE_Pos);
	FLASH->CR |= (0b00<<FLASH_CR_PSIZE_Pos);// only write 1byte =8bit
	FLASH->CR |=(FLASH_CR_PG);
	*addr = data;
	while(((FLASH->SR>>FLASH_SR_BSY_Pos)&1)==1){}
}
void uart_init()
{
 // PD5(TX-AF07) PD6(RX-AF07)
	__HAL_RCC_GPIOD_CLK_ENABLE();
	__HAL_RCC_USART2_CLK_ENABLE();
	GPIOD->MODER &=~(0xf<<10);
	GPIOD->MODER |= (0b1010<<10);
	GPIOD->AFR[0] &=~(0xff<<20);
	GPIOD->AFR[0] |= (0b01110111<<20);
	USART2->BRR = (104<<4)|3;
	USART2->CR1 &=~(USART_CR1_M|USART_CR1_PCE);
	USART2->CR1 |= (USART_CR1_TE|USART_CR1_RE|USART_CR1_UE);
	// DMA USART2->address's rev_dt
	USART2->CR3 |=(USART_CR3_DMAR);
}
void dma_uart1_init(int size)
{
	__HAL_RCC_DMA1_CLK_ENABLE();
	//usart2_rx: DMA1, stream5, channel4
	DMA1_Stream5->CR &=~(0b111<<25);
	DMA1_Stream5->CR |= (0b100<<25);
	DMA1_Stream5->NDTR = size;
	DMA1_Stream5->PAR = 0x40004404;
	DMA1_Stream5->M0AR = (uint32_t)rev_dt;
	DMA1_Stream5->CR |= (DMA_SxCR_MINC);// Enable increment mode
	DMA1_Stream5->CR |= (DMA_SxCR_EN);// Enable DMA
	DMA1_Stream5->CR |= (DMA_SxCR_TCIE);
	NVIC->ISER[0] |=(1<<16);
}
void transmit_1char(char data)
{
	while (!(USART2->SR & (1 << 7))){}
	USART2->DR = data;
	while (!(USART2->SR & (1 << 6))){}
	USART2->SR &=~(1<<6);
}
void transmit_string(char* data)
{
	int datalen = strlen(data);
	for(int i = 0; i<datalen; i++)
	{
		transmit_1char(data[i]);
	}
}
char recive_char()
{
    while (!(USART2->SR & USART_SR_RXNE)){}
    return (uint8_t)(USART2->DR & 0xFF);
}
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
