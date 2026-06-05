#include "SerialStrDataPlane.h"

SerialStrDataPlane::SerialStrDataPlane() : rx_index(0) {}

inline uint32_t SerialStrDataPlane::fast_atoi(const char *str)
{
    uint32_t val = 0;
    while (*str >= '0' && *str <= '9')
    {
        val = val * 10 + (*str++ - '0');
    }
    return val;
}

bool SerialStrDataPlane::begin()
{
    rx_index = 0;
    while (Serial.available())
    {
        Serial.read();
    }
    return true;
}

void SerialStrDataPlane::process(TestRecord *buffer, volatile uint32_t &recordCount, uint32_t maxRecords, QueueHandle_t ctrlQueue)
{
    while (Serial.available() > 0)
    {
        char c = Serial.read();

        if (c == '\n' || c == '\r')
        {
            if (rx_index == 0)
                continue;

            int64_t esp_ts = esp_timer_get_time();

            rx_buffer[rx_index] = '\0';

            if (rx_buffer[0] == 'D' && rx_buffer[1] == ',')
            {
                if (recordCount < maxRecords)
                {
                    buffer[recordCount].packet_id = fast_atoi(&rx_buffer[2]);
                    buffer[recordCount].esp_timestamp_us = esp_ts;
                    recordCount++;
                }
            }
            else
            {
                char cmd[32] = {0};
                strncpy(cmd, rx_buffer, 31);

                xQueueSend(ctrlQueue, &cmd, 0);
            }
            rx_index = 0;
        }
        else if (rx_index < sizeof(rx_buffer) - 1)
        {
            rx_buffer[rx_index++] = c;
        }
    }
}

void SerialStrDataPlane::end()
{
    rx_index = 0;
}
