#pragma once
#include "IDataPlane.h"
#include <WiFi.h>

class TcpDataPlane : public IDataPlane
{
private:
    WiFiServer server;
    WiFiClient client;
    uint8_t rx_buffer[256];
    uint16_t rx_index;
    bool server_running;

    size_t cobs_decode(const uint8_t *input, size_t length, uint8_t *output);

public:
    TcpDataPlane();
    bool begin() override;
    void process(TestRecord *buffer, volatile uint32_t &recordCount, uint32_t maxRecords, QueueHandle_t ctrlQueue) override;
    void end() override;
};
