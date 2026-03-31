from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True, slots=True)
class GoodputResult:
    bytes_per_sec: float  # [B/s] For precise calculations in microcontrollers
    kilobytes_per_sec: float  # [KB/s] Classical unit (divided by 1024)
    megabits_per_sec: float  # [Mbps] Standard in telecommunications publications


def calculate_goodput(
    received_ids: pd.Series, esp_timestamps: pd.Series, payload_size_bytes: int
) -> GoodputResult:
    """
    Calculates Goodput based on the precise receiver time window,
    ignoring retransmissions and duplicates.

    Args:
        received_ids: Column with received packet IDs.
        esp_timestamps: Column with reception timestamps (in microseconds).
        payload_size_bytes: Size in bytes of a SINGLE, pure data structure (without network overhead).

    Returns:
        GoodputResult object with converted units.
    """
    if payload_size_bytes <= 0:
        raise ValueError("Payload size must be a positive integer.")

    if len(received_ids) < 2:
        return GoodputResult(0.0, 0.0, 0.0)

    df_temp = pd.DataFrame({"id": received_ids, "ts": esp_timestamps})

    # Remove duplicates (MAC layer retransmissions).
    df_unique = df_temp.drop_duplicates(subset="id", keep="first")

    unique_count = len(df_unique)
    if unique_count < 2:
        return GoodputResult(0.0, 0.0, 0.0)

    # Determine the actual receiving window.
    # Even if packets arrived out of order, we care about absolute min and max on ESP32 time axis.
    duration_us = float(df_unique["ts"].max() - df_unique["ts"].min())

    if duration_us <= 0.0:
        return GoodputResult(0.0, 0.0, 0.0)

    duration_s = duration_us / 1_000_000.0

    # Calculate total useful bytes
    total_useful_bytes = unique_count * payload_size_bytes

    bps = total_useful_bytes / duration_s
    kbps = bps / 1024.0
    mbps = (
        bps * 8
    ) / 1_000_000.0  # 1 Mb = 1,000,000 bits (network standard SI, not 1024^2)

    return GoodputResult(
        bytes_per_sec=bps, kilobytes_per_sec=kbps, megabits_per_sec=mbps
    )


def print_goodput_result(result: GoodputResult) -> None:
    print(f"Goodput: {result.bytes_per_sec:.2f} B/s")
    print(f"Goodput: {result.kilobytes_per_sec:.2f} KB/s")
    print(f"Goodput: {result.megabits_per_sec:.2f} Mbps")


if __name__ == "__main__":
    from simulation import Config

    config = Config()

    result_jitter = calculate_goodput(
        config.df["packet_id"], config.df["esp_ts"], payload_size_bytes=20
    )
    print_goodput_result(result_jitter)
