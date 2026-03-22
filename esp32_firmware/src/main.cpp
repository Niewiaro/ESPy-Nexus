#include <Arduino.h>

TaskHandle_t HelloTaskHandle = NULL;

void helloWorldTask(void *pvParameters)
{
  for (;;)
  {
    Serial.println("Hello World!");
    vTaskDelay(pdMS_TO_TICKS(2000));
  }
}

void setup()
{
  Serial.begin(115200);
  // Wait a moment for the serial monitor to initialize
  vTaskDelay(pdMS_TO_TICKS(1000));

  Serial.println("\n=========================================");
  Serial.printf("Internal RAM (SRAM): %d bytes free\n", ESP.getFreeHeap());

  // Check if our flags from platformio.ini worked
  if (psramFound())
  {
    Serial.printf("External PSRAM FOUND! Free: %d bytes\n", ESP.getFreePsram());
    Serial.println("Your hardware is ready for heavy load tests!");
  }
  else
  {
    Serial.println("WARNING: PSRAM not detected. Check platformio.ini!");
  }
  Serial.println("=========================================\n");

  xTaskCreatePinnedToCore(
      helloWorldTask,
      "HelloTask",
      2048,
      NULL,
      1,
      &HelloTaskHandle,
      1);
}

void loop()
{
  vTaskDelete(NULL);
}
