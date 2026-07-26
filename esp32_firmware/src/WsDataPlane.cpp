#include "WsDataPlane.h"

WsDataPlane::WsDataPlane() : webSocket(WS_PORT), server_running(false)
{
    currentBuffer = nullptr;
    currentRecordCount = nullptr;
    currentMaxRecords = 0;
}

void WsDataPlane::webSocketEvent(uint8_t num, WStype_t type, uint8_t *payload, size_t length)
{
    if (type != WStype_BIN)
    {
        return;
    }

    int64_t esp_ts = esp_timer_get_time();

    if (currentBuffer != nullptr && currentRecordCount != nullptr)
    {
        if (length >= sizeof(uint32_t))
        {
            if (*currentRecordCount < currentMaxRecords)
            {
                uint32_t packet_id;
                memcpy(&packet_id, payload, sizeof(uint32_t));

                currentBuffer[*currentRecordCount].packet_id = packet_id;
                currentBuffer[*currentRecordCount].esp_timestamp_us = esp_ts;
                (*currentRecordCount)++;
            }
        }
    }
}

bool WsDataPlane::begin()
{
#if NETWORK_MODE == 1
    bool networkReady = (WiFi.softAPIP()[0] != 0);
#elif NETWORK_MODE == 2
    bool networkReady = (WiFi.status() == WL_CONNECTED);
#else
    bool networkReady = false;
#endif

    if (networkReady)
    {
        webSocket.onEvent([this](uint8_t num, WStype_t type, uint8_t *payload, size_t length)
                          { this->webSocketEvent(num, type, payload, length); });
        webSocket.begin();
        server_running = true;
        return true;
    }

    server_running = false;
    return false;
}

void WsDataPlane::process(TestRecord *buffer, volatile uint32_t &recordCount, uint32_t maxRecords, QueueHandle_t ctrlQueue)
{
    if (!server_running)
        return;

    // Attaching current memory pointers for the Callback's needs
    currentBuffer = buffer;
    currentRecordCount = &recordCount;
    currentMaxRecords = maxRecords;

    // The main loop of the WebSocketsServer library.
    // It checks the TCP socket, unpacks the payload and automatically calls our webSocketEvent().
    webSocket.loop();
}

void WsDataPlane::end()
{
    webSocket.close();
    server_running = false;
}
