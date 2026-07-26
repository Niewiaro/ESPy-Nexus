#pragma once
#include "IDataPlane.h"

class SerialStrDataPlane : public IDataPlane
{
private:
    char rx_buffer[2048];
    uint16_t rx_index;

    inline uint32_t fast_atoi(const char *str);

public:
    SerialStrDataPlane();

    bool begin() override;
    void process(TestRecord *buffer, volatile uint32_t &recordCount, uint32_t maxRecords, QueueHandle_t ctrlQueue) override;
    void end() override;
};
