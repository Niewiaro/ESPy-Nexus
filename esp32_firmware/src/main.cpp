#include <Arduino.h>

#define SERIAL_BAUDRATE 921600

// TestRecord array
struct __attribute__((packed)) TestRecord
{
  uint32_t packet_id;        // 4 bytes: ID
  uint64_t pc_timestamp;     // 8 bytes: PC timestamp (microseconds)
  uint32_t esp_timestamp_us; // 4 bytes: Local reception time (microseconds)
};
const uint32_t MAX_RECORDS = 50000;
TestRecord *resultBuffer = nullptr;
uint32_t recordCount = 0;

// test control variables
bool isTestRunning = false;
String currentProtocol = "NONE";

TaskHandle_t SerialControlTaskHandle = NULL;

void serialTask(void *pvParameters)
{
  String inputBuffer = "";
  inputBuffer.reserve(128);

  for (;;)
  {
    while (Serial.available() > 0)
    {
      char c = Serial.read();

      if (c != '\n' && c != '\r')
      {
        inputBuffer += c;
        continue;
      }

      if (inputBuffer.length() > 0)
      {
        uint32_t esp_ts = micros();

        inputBuffer.trim();

        if (isTestRunning && currentProtocol == "SERIAL" && inputBuffer.startsWith("D,"))
        {
          if (recordCount < MAX_RECORDS)
          {
            const char *str = inputBuffer.c_str() + 2; // skip "D,"
            char *endPtr;

            // get packet ID, move endPtr to the position after the number
            uint32_t p_id = strtoul(str, &endPtr, 10);

            // get PC timestamp, which should be after the comma following the packet ID
            if (*endPtr == ',')
            {
              uint64_t pc_ts = strtoull(endPtr + 1, NULL, 10);

              resultBuffer[recordCount].packet_id = p_id;
              resultBuffer[recordCount].pc_timestamp = pc_ts;
              resultBuffer[recordCount].esp_timestamp_us = esp_ts;
              recordCount++;
            }
          }
        }
        else if (inputBuffer == "STOP")
        {
          isTestRunning = false;
          Serial.println("ACK_STOP");
        }
        else if (inputBuffer.startsWith("START_") && inputBuffer.length() > 6)
        {
          currentProtocol = inputBuffer.substring(6);
          recordCount = 0; // reset record count for new test
          isTestRunning = true;
          Serial.printf("ACK_START_%s\n", currentProtocol.c_str());
        }
        else if (inputBuffer == "GET_DATA" && !isTestRunning)
        {
          Serial.println("ACK_GET_DATA");

          // convert data to CSV format and send over Serial
          for (uint32_t i = 0; i < recordCount; i++)
          {
            Serial.printf("D,%u,%llu,%u\n",
                          resultBuffer[i].packet_id,
                          resultBuffer[i].pc_timestamp,
                          resultBuffer[i].esp_timestamp_us);

            // Small delay every 1000 records to reset watchdog
            if (i % 1000 == 0)
            {
              vTaskDelay(pdMS_TO_TICKS(1));
            }
          }
          Serial.println("END_DATA");
        }
        else if (inputBuffer == "TEST")
        {
          Serial.println("ACK_TEST");
        }
        else
        {
          if (!isTestRunning)
          {
            Serial.println("ERROR:UNKNOWN_CMD");
          }
          else
          {
            Serial.println("WARNING:TEST_RUNNING");
          }
        }

        inputBuffer.clear(); // clear buffer for next command
      }
    }
    vTaskDelay(pdMS_TO_TICKS(1)); // give some time to watchdog and other tasks
  }
}

void setup()
{
  Serial.begin(SERIAL_BAUDRATE);
  vTaskDelay(pdMS_TO_TICKS(1000));

  Serial.println("\n--- Init ESPy-Nexus ---");

  // PSRAM (WROOMER only) check and allocation
  if (psramFound())
  {
    Serial.printf("Allocating buffer for %u records in PSRAM...\n", MAX_RECORDS);

    // ps_malloc alocks in PSRAM, not in RAM
    resultBuffer = (TestRecord *)ps_malloc(MAX_RECORDS * sizeof(TestRecord));

    if (resultBuffer != nullptr)
    {
      Serial.printf("Success! Allocated %u bytes.\n", MAX_RECORDS * sizeof(TestRecord));
    }
    else
    {
      Serial.println("FATAL ERROR: Failed to allocate PSRAM!");
      while (1)
        ; // Halt system
    }
  }
  else
  {
    Serial.println("FATAL ERROR: No hardware PSRAM found!");
    while (1)
      ;
  }

  Serial.println("\n --- System Ready ---");

  xTaskCreatePinnedToCore(
      serialTask,
      "SerialCtrl",
      8192,
      NULL,
      2,
      &SerialControlTaskHandle,
      1);
}

void loop()
{
  vTaskDelete(NULL);
}
