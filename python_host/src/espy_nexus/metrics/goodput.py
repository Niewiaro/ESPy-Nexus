from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True, slots=True)
class GoodputResult:
    bytes_per_sec: float  # [B/s] For precise calculations in microcontrollers
    efficiency_percent: (
        float  # Useful for comparing different payload sizes and frequencies
    )
    kilobytes_per_sec: float  # [KB/s] Classical unit (divided by 1024)
    megabits_per_sec: float  # [Mbps] Standard in telecommunications publications


def calculate_goodput(
    received_ids: pd.Series,
    esp_timestamps: pd.Series,
    frequency_hz: float,
    payload_size_bytes: int,
) -> GoodputResult:
    """
    Calculates Goodput based on the precise receiver time window,
    ignoring retransmissions and duplicates.

    Args:
        received_ids: Column with received packet IDs.
        esp_timestamps: Column with reception timestamps (in microseconds).
        frequency_hz: Frequency of the communication channel (in Hz).
        payload_size_bytes: Size in bytes of a SINGLE, pure data structure (without network overhead).

    Returns:
        GoodputResult object with converted units.
    """
    if payload_size_bytes <= 0:
        raise ValueError("Payload size must be a positive integer.")

    if len(received_ids) < 2:
        return GoodputResult(0.0, 0.0, 0.0, 0.0)

    df_temp = pd.DataFrame({"id": received_ids, "ts": esp_timestamps})

    # Remove duplicates (MAC layer retransmissions).
    df_unique = df_temp.drop_duplicates(subset="id", keep="first")

    unique_count = len(df_unique)
    if unique_count < 2:
        return GoodputResult(0.0, 0.0, 0.0, 0.0)

    # Determine the actual receiving window.
    # Even if packets arrived out of order, we care about absolute min and max on ESP32 time axis.
    duration_us = float(df_unique["ts"].max() - df_unique["ts"].min())

    if duration_us <= 0.0:
        return GoodputResult(0.0, 0.0, 0.0, 0.0)

    duration_s = duration_us / 1_000_000.0

    # Calculate total useful bytes
    total_useful_bytes = unique_count * payload_size_bytes

    bps = total_useful_bytes / duration_s
    kbps = bps / 1024.0

    # 1 Mb = 1,000,000 bits
    actual_bits_per_s = bps * 8
    mbps = actual_bits_per_s / 1_000_000.0

    # Theoretical maximum goodput (Offered Load in bits per second)
    offered_load_bits_per_s = frequency_hz * payload_size_bytes * 8

    # Efficiency is (Actual Bits/s / Theoretical Bits/s) * 100
    efficiency_percent = (
        (actual_bits_per_s / offered_load_bits_per_s * 100.0)
        if offered_load_bits_per_s > 0
        else 0.0
    )

    return GoodputResult(
        bytes_per_sec=bps,
        efficiency_percent=efficiency_percent,
        kilobytes_per_sec=kbps,
        megabits_per_sec=mbps,
    )


def print_goodput_result(result: GoodputResult) -> None:
    print("--- Goodput Analysis ---")
    print(f"Goodput: {result.bytes_per_sec:.2f} B/s")
    print(f"Efficiency: {result.efficiency_percent:.2f} %")
    print(f"Goodput: {result.kilobytes_per_sec:.2f} KB/s")
    print(f"Goodput: {result.megabits_per_sec:.2f} Mbps")


if __name__ == "__main__":
    from espy_nexus.metrics.simulation import MockTestScenario

    mock_test_scenario = MockTestScenario()

    result_jitter = calculate_goodput(
        mock_test_scenario.df["packet_id"],
        mock_test_scenario.df["esp_ts"],
        mock_test_scenario.frequency_hz,
        payload_size_bytes=20,
    )
    print_goodput_result(result_jitter)
