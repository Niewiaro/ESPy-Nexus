#pragma once
#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include "TestRecord.h"

class IDataPlane
{
public:
    virtual ~IDataPlane() = default;

    virtual bool begin() = 0;
    virtual void process(TestRecord *buffer, volatile uint32_t &recordCount, uint32_t maxRecords, QueueHandle_t ctrlQueue) = 0;
    virtual void end() = 0;
};
