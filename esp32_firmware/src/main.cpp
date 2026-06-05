#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <freertos/task.h>
#include "TestRecord.h"
#include "IDataPlane.h"
#include "SerialStrDataPlane.h"
#include "SerialBinDataPlane.h"

#define SERIAL_BAUDRATE 921600
const uint32_t MAX_RECORDS = 50000;

TestRecord *resultBuffer = nullptr;

volatile uint32_t recordCount = 0;
volatile bool isTestRunning = false;

QueueHandle_t controlQueue;

SerialStrDataPlane serialStrDataPlane;
SerialBinDataPlane serialBinDataPlane;

IDataPlane *currentDataPlane = nullptr;

void dataPlaneTask(void *pvParameters)
{
  for (;;)
  {
    if (isTestRunning && currentDataPlane != nullptr)
    {
      currentDataPlane->process(resultBuffer, recordCount, MAX_RECORDS, controlQueue);
    }
    else
    {
      while (Serial.available() > 0)
      {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        if (cmd.length() > 0)
        {
          char raw_cmd[32];
          strncpy(raw_cmd, cmd.c_str(), 31);
          xQueueSend(controlQueue, &raw_cmd, 0);
        }
      }
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
        }
        else if (protocol == "SERIAL_BIN")
        {
          currentDataPlane = &serialBinDataPlane;
          initSuccess = currentDataPlane->begin();
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
  Serial.begin(SERIAL_BAUDRATE);

  Serial.setRxBufferSize(4096);

  vTaskDelay(pdMS_TO_TICKS(1000));
  Serial.println("\n--- Init ESPy-Nexus (RTOS Strategy Architecture) ---");

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

  controlQueue = xQueueCreate(10, sizeof(char[32]));

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
