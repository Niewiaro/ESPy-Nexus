#include <Arduino.h>
#include <WiFi.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <freertos/task.h>
#include "TestRecord.h"
#include "IDataPlane.h"
#include "SerialStrDataPlane.h"
#include "SerialBinDataPlane.h"
#include "UdpDataPlane.h"
#include "TcpDataPlane.h"

#define SERIAL_BAUDRATE 921600
const uint32_t MAX_RECORDS = 50000;

TestRecord *resultBuffer = nullptr;

volatile uint32_t recordCount = 0;
volatile bool isTestRunning = false;
volatile bool serialPortOwnedByDataPlane = false;

QueueHandle_t controlQueue;

SerialStrDataPlane serialStrDataPlane;
SerialBinDataPlane serialBinDataPlane;
UdpDataPlane udpDataPlane;
TcpDataPlane tcpDataPlane;

IDataPlane *currentDataPlane = nullptr;

void uartListenerTask(void *pvParameters)
{
  char rx_buffer[32];
  uint8_t rx_index = 0;

  for (;;)
  {
    if (!serialPortOwnedByDataPlane)
    {
      while (Serial.available() > 0)
      {
        char c = Serial.read();

        if (c == '\n' || c == '\r')
        {
          if (rx_index > 0)
          {
            rx_buffer[rx_index] = '\0';
            xQueueSend(controlQueue, &rx_buffer, 0);
            rx_index = 0;
          }
        }
        else if (rx_index < sizeof(rx_buffer) - 1)
        {
          rx_buffer[rx_index++] = c;
        }
      }
    }
    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

void dataPlaneTask(void *pvParameters)
{
  for (;;)
  {
    if (isTestRunning && currentDataPlane != nullptr)
    {
      currentDataPlane->process(resultBuffer, recordCount, MAX_RECORDS, controlQueue);
    }
    taskYIELD();
  }
}

void controlPlaneTask(void *pvParameters)
{
  char cmd[32];
  String currentProtocol = "NONE";

  for (;;)
  {
    if (xQueueReceive(controlQueue, &cmd, portMAX_DELAY) == pdPASS)
    {
      String command(cmd);
      command.trim();

      if (command.startsWith("START_"))
      {
        String protocol = command.substring(6); // get protocol name after "START_"

        if (currentDataPlane)
        {
          currentDataPlane->end();
          currentDataPlane = nullptr;
        }

        bool initSuccess = false;

        // STRATEGY
        if (protocol == "SERIAL_STR")
        {
          currentDataPlane = &serialStrDataPlane;
          initSuccess = currentDataPlane->begin();
          serialPortOwnedByDataPlane = true;
        }
        else if (protocol == "SERIAL_BIN")
        {
          currentDataPlane = &serialBinDataPlane;
          initSuccess = currentDataPlane->begin();
          serialPortOwnedByDataPlane = true;
        }
        else if (protocol == "UDP")
        {
          currentDataPlane = &udpDataPlane;
          initSuccess = currentDataPlane->begin();
          serialPortOwnedByDataPlane = false;
        }
        else if (protocol == "TCP")
        {
          currentDataPlane = &tcpDataPlane;
          initSuccess = currentDataPlane->begin();
          serialPortOwnedByDataPlane = false;
        }
        else
        {
          Serial.printf("ERROR_UNKNOWN_PROTOCOL_[%s]\n", protocol.c_str());
          continue;
        }

        if (initSuccess)
        {
          recordCount = 0;
          isTestRunning = true;
          Serial.printf("ACK_START_%s\n", protocol.c_str());
        }
        else
        {
          Serial.printf("ERROR_START_FAILED_%s\n", protocol.c_str());
        }
      }
      else if (command == "STOP")
      {
        isTestRunning = false;
        Serial.println("ACK_STOP");
        serialPortOwnedByDataPlane = false;
      }
      else if (command == "GET_DATA" && !isTestRunning)
      {
        // Serial data dump
        // Serial.println("ACK_GET_DATA");
        // for (uint32_t i = 0; i < recordCount; i++)
        // {
        //   Serial.printf("D,%u,%u\n",
        //                 resultBuffer[i].packet_id,
        //                 resultBuffer[i].esp_timestamp_us);

        //   if (i % 1000 == 0)
        //   {
        //     vTaskDelay(pdMS_TO_TICKS(1));
        //   }
        // }
        // Serial.println("END_DATA");

        // Binary data dump
        Serial.printf("ACK_GET_DATA,%u\n", recordCount);
        vTaskDelay(pdMS_TO_TICKS(10));

        if (recordCount > 0)
        {
          Serial.write((uint8_t *)resultBuffer, recordCount * sizeof(TestRecord));
        }
      }
      else
      {
        Serial.printf("WARNING:UNKNOWN_CMD_[%s]\n", command.c_str());
      }
    }
  }
}

void setup()
{
  // Serial port initialization
  Serial.begin(SERIAL_BAUDRATE);
  Serial.setRxBufferSize(4096);

  vTaskDelay(pdMS_TO_TICKS(1000));

  Serial.println("\n--- Init ESPy-Nexus (RTOS Strategy Architecture) ---");

  // PSRAM allocation for result buffer
  if (psramFound())
  {
    Serial.printf("Allocating PSRAM for %u records...\n", MAX_RECORDS);
    resultBuffer = (TestRecord *)ps_malloc(MAX_RECORDS * sizeof(TestRecord));

    if (resultBuffer != nullptr)
    {
      Serial.printf("OK! Allocated %u bytes.\n", MAX_RECORDS * sizeof(TestRecord));
    }
    else
    {
      Serial.println("FATAL ERROR: PSRAM allocation failed!");
      while (1)
        ;
    }
  }
  else
  {
    Serial.println("FATAL ERROR: PSRAM not detected!");
    while (1)
      ;
  }

  // Wi-Fi initialization
  // If ESPy-Nexus is configured to run in Access Point mode, it will create its own Wi-Fi network.
  // Otherwise, it will connect to the specified home Wi-Fi network.
#if IS_ESPY_NEXUS_AP == 1
  Serial.printf("\n[Wi-Fi] Starting Access Point mode: %s \n", WIFI_AP_SSID);

  WiFi.mode(WIFI_AP); // Set the board to AP mode

  // Create network (SSID, Password, Channel (e.g. 1), Hide network (0 = visible), Max connections (e.g. 4))
  bool apStatus = WiFi.softAP(WIFI_AP_SSID, WIFI_AP_PASS, 1, 0, 4);

  if (apStatus)
  {
    Serial.println("[+] AP network started successfully!");
    Serial.print("Connect your computer to this network. IP address for Python: ");
    // In AP mode, ESP32 typically defaults to 192.168.4.1
    Serial.println(WiFi.softAPIP());
  }
  else
  {
    Serial.println("[-] FATAL ERROR: Failed to start AP mode!");
    while (1)
      ;
  }

#else
  Serial.printf("\n[Wi-Fi] Connecting to home network: %s ", WIFI_STA_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_STA_SSID, WIFI_STA_PASS);

  while (WiFi.status() != WL_CONNECTED)
  {
    vTaskDelay(pdMS_TO_TICKS(500));
    Serial.print(".");
  }

  Serial.println("\n[+] Connected to Wi-Fi!");
  Serial.print("IP address assigned by router: ");
  Serial.println(WiFi.localIP());
#endif

  // Create control queue and tasks
  controlQueue = xQueueCreate(10, sizeof(char[32]));

  xTaskCreatePinnedToCore(
      uartListenerTask, "UartListener", 2048, NULL, 2, NULL, 0);

  xTaskCreatePinnedToCore(
      controlPlaneTask, "ControlTask", 4096, NULL, 1, NULL, 0);

  xTaskCreatePinnedToCore(
      dataPlaneTask, "DataTask", 8192, NULL, configMAX_PRIORITIES - 1, NULL, 1);

  Serial.println("\n--- System Ready ---");
}

void loop()
{
  vTaskDelete(NULL);
}
