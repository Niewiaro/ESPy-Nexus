#include "UdpDataPlane.h"
#include <string.h>

UdpDataPlane::UdpDataPlane() : rx_index(0), wifi_connected(false) {}

bool UdpDataPlane::begin()
{
    rx_index = 0;

#if NETWORK_MODE == 1
    bool networkReady = (WiFi.softAPIP()[0] != 0);
#elif NETWORK_MODE == 2
    bool networkReady = (WiFi.status() == WL_CONNECTED);
#else
    bool networkReady = false;
#endif

    if (networkReady)
    {
        udp.stop();

        if (udp.begin(UDP_PORT))
        {
            wifi_connected = true;
            return true;
        }
    }

    wifi_connected = false;
    return false;
}

void UdpDataPlane::process(TestRecord *buffer, volatile uint32_t &recordCount, uint32_t maxRecords, QueueHandle_t ctrlQueue)
{
    if (!wifi_connected)
        return;

    int packetSize = udp.parsePacket();

    if (packetSize > 0)
    {
        int64_t esp_ts = esp_timer_get_time();

        int bytesToRead = udp.available();
        if (bytesToRead > sizeof(rx_buffer))
            bytesToRead = sizeof(rx_buffer);

        int len = udp.read(rx_buffer, bytesToRead);

        if (len > 0)
        {
            if (recordCount < maxRecords)
            {
                uint32_t p_id;
                memcpy(&p_id, rx_buffer, sizeof(uint32_t));

                buffer[recordCount].packet_id = p_id;
                buffer[recordCount].esp_timestamp_us = esp_ts;
                recordCount++;
            }
        }

        udp.flush();
    }
}

void UdpDataPlane::end()
{
    udp.stop();
}
