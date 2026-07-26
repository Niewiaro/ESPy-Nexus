import json

# Mocking the IoT sensor variables with realistic maximum/typical values
# to simulate the exact payload structure from your C++ code
payload_data = {
    "acceleration_x": -16384,
    "acceleration_y": 16384,
    "acceleration_z": 32767,
    "gyro_x": -32768,
    "gyro_y": 32768,
    "gyro_z": 32767,
    "temperature": 35,
    "flame_status": 1,
    "gas_level": 1023,
    "temperature_out": 25.50,
    "humidity_out": 85.75,
    "motor_adc": 4095,
}

# 1. Convert dictionary to a JSON string matching the snprintf format
json_string = json.dumps(payload_data)

# 2. Convert string to UTF-8 encoded bytes to get the exact network payload size
payload_bytes = json_string.encode("utf-8")

# Output the results
print(f"Generated JSON:")
print(json_string)
print("-" * 50)
print(f"String length (characters): {len(json_string)}")
print(f"Payload size (bytes in UTF-8): {len(payload_bytes)} bytes")

# Compare with the static buffer size allocated in C++ (char msg[256])
buffer_limit = 256
print(f"C++ Buffer Allocation: {buffer_limit} bytes")
if len(payload_bytes) < buffer_limit:
    print(
        f"Status: SAFE ({buffer_limit - len(payload_bytes)} bytes remaining in buffer)"
    )
else:
    print(
        f"Status: WARNING! Payload exceeds buffer size by {len(payload_bytes) - buffer_limit} bytes!"
    )
