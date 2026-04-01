import time
import itertools
import pandas as pd
from dataclasses import dataclass

# Importy naszej architektury
from espy_nexus.control_plane.serial_cp import SerialControlPlane
from espy_nexus.data_plane.serial_dp import SerialDataPlane
from espy_nexus.pipeline.downlink import DownlinkAnalyzer


@dataclass(frozen=True)
class TestConfig:
    """Definicja pojedynczego scenariusza testowego."""

    test_id: str
    frequency_hz: int
    packet_count: int
    payload_size_bytes: int


def generate_matrix() -> list[TestConfig]:
    """Generuje listę wszystkich kombinacji do przetestowania."""
    # Szukamy punktu załamania: od spokojnych 50 Hz do morderczych 2000 Hz
    frequencies = [50, 100, 250, 500, 750, 1000, 1500, 2000]
    packet_count = 10000  # Stała liczba paczek dla każdego testu
    payload_size = 16  # Szacowany rozmiar paczki ASCII w bajtach

    matrix = []
    for freq in frequencies:
        config = TestConfig(
            test_id=f"SERIAL_{freq}Hz",
            frequency_hz=freq,
            packet_count=packet_count,
            payload_size_bytes=payload_size,
        )
        matrix.append(config)

    return matrix


def main():
    PORT = "COM5"
    BAUDRATE = 921600

    matrix = generate_matrix()
    global_results = []

    print("=" * 60)
    print(f"🔬 START MACIERZY TESTOWEJ: Zaplanowano {len(matrix)} testów.")
    print("=" * 60)

    # Inicjujemy współdzielone zasoby
    cp = SerialControlPlane(port=PORT, baudrate=BAUDRATE)
    dp = SerialDataPlane(port=PORT, baudrate=BAUDRATE)

    try:
        cp.connect()

        for i, config in enumerate(matrix, 1):
            print(
                f"\n[{i}/{len(matrix)}] Uruchamianie testu: {config.test_id} ({config.frequency_hz} Hz)"
            )

            # 1. Negocjacja
            if not cp.send_command("START_SERIAL", expected_ack="ACK_START_SERIAL"):
                print(
                    f"[-] Pomijam {config.test_id} - ESP32 nie odpowiedziało na START."
                )
                continue

            # 2. Uderzenie danych
            dp.transmit(
                packet_count=config.packet_count, frequency_hz=config.frequency_hz
            )

            # 3. Zatrzymanie
            cp.send_command("STOP", expected_ack="ACK_STOP")

            # 4. Pobranie i Analiza
            records = cp.fetch_data()
            if not records:
                print(f"[-] Test {config.test_id} nie zwrócił danych.")
                continue

            df_raw = pd.DataFrame(records)
            analyzer = DownlinkAnalyzer(payload_size_bytes=config.payload_size_bytes)

            try:
                metrics = analyzer.calculate_all_metrics(
                    df_raw, total_sent=config.packet_count
                )

                # Zapisujemy najważniejsze parametry do zbiorczego raportu
                global_results.append(
                    {
                        "Test_ID": config.test_id,
                        "Frequency_Hz": config.frequency_hz,
                        "Total_Sent": config.packet_count,
                        "Received": metrics.pdr.unique_received,
                        "PDR_%": metrics.pdr.ratio_percent,
                        "Mean_Jitter_us": round(metrics.jitter.mean_us, 2),
                        "Max_Bufferbloat_us": metrics.timing_trends.max_bufferbloat_us,
                        "Clock_Drift_ppm": round(
                            metrics.timing_trends.clock_drift_ppm, 2
                        ),
                    }
                )
                print(
                    f"[+] Sukces. PDR: {metrics.pdr.ratio_percent}%, Jitter: {round(metrics.jitter.mean_us, 2)} us"
                )

            except Exception as e:
                print(f"[!] Błąd analizy matematycznej dla {config.test_id}: {e}")

            # Dajemy ESP32 chwilę na "ostygnięcie" i wyczyszczenie pamięci przed kolejnym uderzeniem
            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n[!] Przerwano przez użytkownika.")
    finally:
        cp.disconnect()

        # ZAPIS WYNIKÓW KOŃCOWYCH
        if global_results:
            results_df = pd.DataFrame(global_results)
            print("\n" + "=" * 60)
            print("📊 PODSUMOWANIE WYNIKÓW:")
            print(results_df.to_string(index=False))

            filename = "matrix_results_serial.csv"
            results_df.to_csv(filename, index=False)
            print(f"\n[*] Zapisano pełny raport do pliku: {filename}")
        else:
            print("\n[-] Brak wyników do zapisania.")


if __name__ == "__main__":
    main()
