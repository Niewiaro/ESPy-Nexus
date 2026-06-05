#pragma once
#include <Arduino.h>

// __attribute__((packed)) removes hardware padding (empty alignment bytes).
struct __attribute__((packed)) TestRecord
{
    uint32_t packet_id;        // 4 bytes
    int64_t esp_timestamp_us;  // 8 bytes
};
// Total size of the new struct: 12 bytes
