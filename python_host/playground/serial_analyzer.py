import serial
import time
import pandas as pd
import numpy as np

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

        for i in range(1, NUM_PACKETS + 1):
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
    if df.empty:
        print("Brak danych do analizy.")
        return

    print("\n" + "=" * 40)
    print(" 📊 RAPORT ANALIZY MATEMATYCZNEJ 📊")
    print("=" * 40)

    # 1. Analiza Strat (PDR)
    expected_ids = set(range(1, NUM_PACKETS + 1))
    received_ids = set(df["packet_id"])
    missing_ids = expected_ids - received_ids

    pdr = (len(received_ids) / NUM_PACKETS) * 100
    print(f"Dostarczono paczek: {len(received_ids)} / {NUM_PACKETS} ({pdr:.2f}%)")
    if missing_ids:
        print(
            f"Zgubiono {len(missing_ids)} paczek. Przykładowe ID: {list(missing_ids)[:5]}"
        )

    # 2. Analiza Kolejności
    # Sprawdzamy czy lista ID jest ściśle rosnąca
    is_sorted = df["packet_id"].is_monotonic_increasing
    print(f"Czy paczki zachowały kolejność: {'TAK' if is_sorted else 'NIE'}")

    # 3. Różnica Zegarów (Offset i Drift)
    # Różnica czasu między ESP a PC dla każdej paczki
    df["clock_diff"] = df["esp_ts"] - df["pc_ts"]

    offset_median = df["clock_diff"].median()
    offset_std = df["clock_diff"].std()

    # Prostą regresją liniową liczymy średni dryf zegara (ile mikrosekund na paczkę)
    drift_poly = np.polyfit(df["packet_id"], df["clock_diff"], 1)
    drift_us_per_packet = drift_poly[0]

    print("\n--- Zegary (ESP vs PC) ---")
    print(f"Mediana różnicy: {offset_median:.2f} us")
    print(f"Szum różnicy (Odch. Std.): {offset_std:.2f} us")
    print(f"Zauważony dryf kwarców: {drift_us_per_packet:.4f} us na każdą paczkę")

    # 4. Analiza Jittera (Na podstawie czasu na ESP32)
    # Obliczamy interwał między nadejściem paczek (Delta T)
    df["iat_esp"] = df["esp_ts"].diff()  # Różnica między i a (i-1)

    iat_mean = df["iat_esp"].mean()
    # Jitter to w inżynierii często odchylenie standardowe interwałów
    jitter_std = df["iat_esp"].std()
    jitter_max = df["iat_esp"].max() - iat_mean

    print("\n--- Jitter i Płynność (Odebrane przez ESP) ---")
    print(f"Oczekiwany odstęp: {1_000_000 / RATE_HZ:.2f} us")
    print(f"Średni rzeczywisty odstęp: {iat_mean:.2f} us")
    print(f"JITTER (Odch. Std. odstępów): {jitter_std:.2f} us")
    print(f"Największe 'szarpnięcie' (Max Jitter): {jitter_max:.2f} us")
    print("=" * 40)


if __name__ == "__main__":
    df_results = run_test()
    if df_results is not None:
        analyze_data(df_results)
        # Opcjonalnie: Zapis do pliku by pooglądać to w Excelu
        # df_results.to_csv("serial_test_results.csv", index=False)
