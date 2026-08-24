# ESPy-Nexus

ESPy-Nexus is a Hardware-in-the-Loop platform for testing communication performance on an ESP32 device.

## Components

- **ESP32 firmware** - receives control commands, runs the selected communication protocol, timestamps received packets, and stores measurement records in PSRAM.
- **Python Test Engine** - configures and executes test scenarios, generates network traffic, communicates with the ESP32, and stores raw results in relative DB (SQLite).
- **Python Analyzer** - processes raw measurements and calculates QoS metrics such as PDR, jitter, burst loss, goodput, out-of-order events, and relative delay.
- **Nuxt dashboard** - provides an interactive web interface for filtering, comparing, and visualizing the aggregated results.

## Data Flow

```mermaid
flowchart LR
	PC1[PC: Python Test Engine] -->|Control commands and test traffic| ESP32[ESP32 firmware]
	ESP32 -->|Measurement records and timestamps| PC2[PC: Python Analyzer]
	PC2 -->|Aggregated QoS results| NUXT[Nuxt dashboard]
	NUXT -->|Deployment and delivery| CF[Cloudflare]
	CF --> USER[User]
```

## Dashboard

[Open the ESPy-Nexus dashboard](https://espy-nexus.niewiaro.cc/en)
