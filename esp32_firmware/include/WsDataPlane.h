#pragma once
#include "IDataPlane.h"
#include <WebSocketsServer.h>

class WsDataPlane : public IDataPlane
{
private:
    WebSocketsServer webSocket;
    bool server_running;

    // Buffer pointers to allow the event callback to access the main HIL memory
    TestRecord *currentBuffer;
    volatile uint32_t *currentRecordCount;
    uint32_t currentMaxRecords;

    // Function automatically called by the library when a new packet arrives
    void webSocketEvent(uint8_t num, WStype_t type, uint8_t *payload, size_t length);

public:
    WsDataPlane();
    bool begin() override;
    void process(TestRecord *buffer, volatile uint32_t &recordCount, uint32_t maxRecords, QueueHandle_t ctrlQueue) override;
    void end() override;
};
