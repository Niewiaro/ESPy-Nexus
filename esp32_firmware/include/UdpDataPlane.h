#pragma once
#include "IDataPlane.h"
#include <WiFi.h>
#include <WiFiUdp.h>

class UdpDataPlane : public IDataPlane
{
private:
    WiFiUDP udp;

    uint8_t rx_buffer[2048];
    bool wifi_connected;

public:
    UdpDataPlane();

    bool begin() override;
    void process(TestRecord *buffer, volatile uint32_t &recordCount, uint32_t maxRecords, QueueHandle_t ctrlQueue) override;
    void end() override;
};