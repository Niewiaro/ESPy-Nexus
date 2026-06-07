#include "TcpDataPlane.h"
#include <string.h>

TcpDataPlane::TcpDataPlane() : server(TCP_PORT), rx_index(0), server_running(false) {}

size_t TcpDataPlane::cobs_decode(const uint8_t *input, size_t length, uint8_t *output)
{
    size_t read_index = 0;
    size_t write_index = 0;
    uint8_t code;

    while (read_index < length)
    {
        code = input[read_index];
        if (read_index + code > length && code != 1)
            return 0;
        read_index++;
        for (uint8_t i = 1; i < code; i++)
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

bool TcpDataPlane::begin()
{
    rx_index = 0;

#if MY_HIL_ROUTER_MODE == 1
    bool networkReady = (WiFi.softAPIP()[0] != 0);
#else
    bool networkReady = (WiFi.status() == WL_CONNECTED);
#endif

    if (networkReady)
    {
        server.begin(TCP_PORT);
        server_running = true;
        return true;
    }

    server_running = false;
    return false;
}

void TcpDataPlane::process(TestRecord *buffer, volatile uint32_t &recordCount, uint32_t maxRecords, QueueHandle_t ctrlQueue)
{
    if (!server_running)
        return;

    if (!client || !client.connected())
    {
        client = server.available();
    }

    if (client && client.connected())
    {
        while (client.available() > 0)
        {
            uint8_t c = client.read();

            // COBS framing algorithm: Detecting the end of a COBS packet
            if (c == 0x00)
            {
                if (rx_index == 0)
                    continue;

                int64_t esp_ts = esp_timer_get_time();

                uint8_t decoded_payload[256];
                size_t decoded_len = cobs_decode(rx_buffer, rx_index, decoded_payload);

                if (decoded_len >= sizeof(uint32_t))
                {
                    if (recordCount < maxRecords)
                    {
                        uint32_t packet_id;
                        memcpy(&packet_id, decoded_payload, sizeof(uint32_t));

                        buffer[recordCount].packet_id = packet_id;
                        buffer[recordCount].esp_timestamp_us = esp_ts;
                        recordCount++;
                    }
                }
                rx_index = 0;
            }
            else
            {
                if (rx_index < sizeof(rx_buffer) - 1)
                {
                    rx_buffer[rx_index++] = c;
                }
                else
                {
                    rx_index = 0;
                }
            }
        }
    }
}

void TcpDataPlane::end()
{
    if (client)
    {
        client.stop();
    }
    server.end();
    server_running = false;
}
