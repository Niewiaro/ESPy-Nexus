import pandas as pd

from espy_nexus.control_plane.serial_cp import SerialControlPlane
from espy_nexus.data_plane.serial_dp import SerialDataPlane

from espy_nexus.pipeline.downlink import DownlinkAnalyzer


def main() -> None:
    PORT = "COM5"
    BAUDRATE = 921600
    PACKETS_TO_SEND = 1000
    FREQUENCY_HZ = 100
    PAYLOAD_SIZE = 16

    print("=" * 60)
    print(f"🚀 START TESTU: {PACKETS_TO_SEND} paczek @ {FREQUENCY_HZ} Hz")
    print("=" * 60)

    # Narzędzia sprzętowe
    cp = SerialControlPlane(port=PORT, baudrate=BAUDRATE)

    # Strategię Data Plane
    dp = SerialDataPlane(port=PORT, baudrate=BAUDRATE)

    # Analizator
    analyzer = DownlinkAnalyzer(payload_size_bytes=PAYLOAD_SIZE)

    try:
        cp.connect()
        print("\n[1] Negocjacja startu...")
        if not cp.send_command("START_SERIAL", expected_ack="ACK_START_SERIAL"):
            print("[-] Test przerwany: ESP32 nie odpowiedziało na START.")
            return
        print("[+] ESP32 gotowe.")

        print("\n[2] Faza Data Plane (Transmisja)...")
        dp.transmit(packet_count=PACKETS_TO_SEND, frequency_hz=FREQUENCY_HZ)

        print("\n[3] Negocjacja stopu...")
        if not cp.send_command("STOP", expected_ack="ACK_STOP"):
            print("[-] Ostrzeżenie: ESP32 nie potwierdziło zatrzymania (ACK_STOP).")

        print("\n[4] Zrzut pamięci z mikrokontrolera...")
        records = cp.fetch_data()
        if not records:
            print("[-] Brak danych do analizy!")
            return

        print("\n[5] Uruchamianie silnika analitycznego (Pandas)...")
        df_raw = pd.DataFrame(records)

        metrics = analyzer.calculate_all_metrics(df_raw, total_sent=PACKETS_TO_SEND)
        analyzer.print_report(metrics)

    except Exception as e:
        print(f"\n[BŁĄD KRYTYCZNY]: {e}")
    finally:
        cp.disconnect()
        print("\n[*] Zasoby zwolnione. Koniec programu.")


if __name__ == "__main__":
    main()
