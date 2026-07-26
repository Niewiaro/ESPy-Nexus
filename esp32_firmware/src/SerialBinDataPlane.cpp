#include "SerialBinDataPlane.h"
#include <string.h>

SerialBinDataPlane::SerialBinDataPlane() : rx_index(0) {}

size_t SerialBinDataPlane::cobs_decode(const uint8_t *input, size_t length, uint8_t *output)
{
    size_t read_index = 0;
    size_t write_index = 0;
    uint8_t code;
    uint8_t i;

    while (read_index < length)
    {
        code = input[read_index];
        if (read_index + code > length && code != 1)
        {
            return 0;
        }
        read_index++;
        for (i = 1; i < code; i++)
        {
            output[write_index++] = input[read_index++];
        }
        if (code < 0xFF && read_index != length)
        {
            output[write_index++] = '\0';
        }
    }
    return write_index;
}

bool SerialBinDataPlane::begin()
{
    rx_index = 0;
    while (Serial.available())
    {
        Serial.read(); // Hard reset of the hardware buffer before startup
    }
    return true;
}

void SerialBinDataPlane::process(TestRecord *buffer, volatile uint32_t &recordCount, uint32_t maxRecords, QueueHandle_t ctrlQueue)
{
    while (Serial.available() > 0)
    {
        uint8_t c = Serial.read();

        // 1. The COBS binary frame delimiter is the zero byte (0x00)
        if (c == 0x00)
        {
            if (rx_index == 0)
                continue;

            int64_t esp_ts = esp_timer_get_time();

            // Use the class heap buffer (this->decoded_payload)
            size_t decoded_len = cobs_decode(rx_buffer, rx_index, this->decoded_payload);

            if (decoded_len >= sizeof(uint32_t))
            {
                if (recordCount < maxRecords)
                {
                    uint32_t packet_id;
                    memcpy(&packet_id, this->decoded_payload, sizeof(uint32_t));

                    buffer[recordCount].packet_id = packet_id;
                    buffer[recordCount].esp_timestamp_us = esp_ts;
                    recordCount++;
                }
            }
            rx_index = 0; // Frame decoded, reset the index
        }
        else
        {
            // 2. Safe buffering in the ELSE block
            if (rx_index < sizeof(rx_buffer) - 1)
            {
                rx_buffer[rx_index++] = c;

                // Safety check: if a newline appears in the binary stream,
                // verify whether the PC sent the text STOP command.
                if (c == '\n' || c == '\r')
                {
                    rx_buffer[rx_index] = '\0';
                    if (strstr((char *)rx_buffer, "STOP") != nullptr)
                    {
                        char cmd[32] = "STOP";
                        xQueueSend(ctrlQueue, &cmd, 0);
                        rx_index = 0;
                    }
                }
            }
            else
            {
                // CRITICAL: The buffer overflowed without finding 0x00!
                // Corrupted frame / desynchronization. Reset the index.
                rx_index = 0;
            }
        }
    }
}

void SerialBinDataPlane::end()
{
    rx_index = 0;
}
