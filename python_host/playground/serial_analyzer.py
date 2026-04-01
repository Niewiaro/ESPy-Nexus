import serial
import time
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Dodaj katalog python_host do sys.path, aby znaleźć moduł analyzer
sys.path.insert(0, str(Path(__file__).parent.parent))

# Konfiguracja
PORT = "COM5"  # ZMIEŃ NA SWÓJ PORT!
BAUDRATE = 921600
RATE_HZ = 1000  # Częstotliwość (np. 100 paczek na sekundę)
NUM_PACKETS = 10000  # Ilość paczek do wysłania (1000 przy 100Hz = 10 sekund testu)


def run_test():
    print(f"Otwieranie portu {PORT} z prędkością {BAUDRATE}...")

    # timeout=1 zapobiega wiecznemu zawieszeniu w przypadku braku odpowiedzi
    with serial.Serial(PORT, BAUDRATE, timeout=1) as ser:
        time.sleep(2)  # Czekamy na reset płytki po otwarciu portu
        ser.reset_input_buffer()

        # 1. INICJALIZACJA
        print("Wysyłanie START...")
        ser.write(b"START_SERIAL\n")
        response = ser.readline().decode().strip()
        print(f"Odpowiedź ESP: {response}")
        if response != "ACK_START_SERIAL":
            print("Błąd inicjalizacji!")
            return None

        # 2. BOMBARDOWANIE DANYMI (Z zachowaniem ścisłego reżimu czasowego)
        print(f"Rozpoczynam wysyłanie {NUM_PACKETS} paczek z f = {RATE_HZ} Hz...")
        interval_ns = int((1.0 / RATE_HZ) * 1_000_000_000)  # Interwał w nanosekundach

        next_wake_time = time.perf_counter_ns()

        for i in range(0, NUM_PACKETS):
            # Aktywne czekanie (Busy-wait) dla mikrosekundowej precyzji w Windows/Linux
            # W testach profesjonalnych to lepsze niż time.sleep(), które jest niedokładne.
            while time.perf_counter_ns() < next_wake_time:
                pass

            # Pobieramy czas w mikrosekundach z PC
            pc_timestamp_us = time.time_ns() // 1000

            # Pakujemy stringa (zgodnie z naszym obecnym kodem na ESP32)
            packet = f"D,{i},{pc_timestamp_us}\n".encode("ascii")
            ser.write(packet)

            next_wake_time += interval_ns

        time.sleep(10)
        # 3. ZATRZYMANIE
        print("Wysłano wszystkie paczki. Zatrzymywanie...")
        ser.write(b"STOP\n")
        print(f"Odpowiedź ESP: {ser.readline().decode().strip()}")

        # 4. POBRANIE DANYCH
        print("Pobieranie wyników (GET_DATA)...")
        ser.write(b"GET_DATA\n")
        print(f"Odpowiedź ESP: {ser.readline().decode().strip()}")

        records = []
        while True:
            line = ser.readline().decode().strip()
            if line == "END_DATA":
                break
            if line:
                # Rozbijamy CSV: D,1,pc_time,esp_time
                parts = line.split(",")
                if len(parts) == 3:
                    records.append(
                        {
                            "packet_id": int(parts[0]),
                            "pc_ts": int(parts[1]),
                            "esp_ts": int(parts[2]),
                        }
                    )

        print(f"Pobrano {len(records)} rekordów.")
        return pd.DataFrame(records)


def analyze_data(df: pd.DataFrame):
    from analyzer.serial.downlink.pipeline import DownlinkAnalyzer

    analyzer = DownlinkAnalyzer(payload_size_bytes=16)
    metrics = analyzer.calculate_all_metrics(df, total_sent=NUM_PACKETS)
    analyzer.print_report(metrics)


if __name__ == "__main__":
    df_results = run_test()
    if df_results is not None:
        analyze_data(df_results)
