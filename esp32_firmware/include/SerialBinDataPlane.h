#pragma once
#include "IDataPlane.h"

class SerialBinDataPlane : public IDataPlane
{
private:
    uint8_t rx_buffer[2048];
    uint8_t decoded_payload[2048];
    uint16_t rx_index;

    size_t cobs_decode(const uint8_t *input, size_t length, uint8_t *output);

public:
    SerialBinDataPlane();

    bool begin() override;
    void process(TestRecord *buffer, volatile uint32_t &recordCount, uint32_t maxRecords, QueueHandle_t ctrlQueue) override;
    void end() override;
};