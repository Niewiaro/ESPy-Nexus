from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True, slots=True)
class PdrResult:
    ratio_percent: float
    total_expected: int
    unique_received: int
    lost_count: int
    duplicates_count: int


def calculate_pdr(received_ids: pd.Series, total_sent: int) -> PdrResult:
    """
    Analyzes packet delivery ratio (PDR), packet loss, and duplicates.

    Args:
        received_ids: Series containing received packet IDs.
        total_sent: Total number of packets sent by the transmitter.

    Returns:
        PdrResult object with complete statistics.
    """
    if total_sent <= 0:
        raise ValueError("total_sent must be a positive integer.")

    unique_received = int(received_ids.nunique())
    lost_count = max(0, total_sent - unique_received)
    duplicates_count = int(len(received_ids) - unique_received)
    ratio_percent = min(100.0, (unique_received / total_sent) * 100.0)

    return PdrResult(
        ratio_percent=ratio_percent,
        total_expected=total_sent,
        unique_received=unique_received,
        lost_count=lost_count,
        duplicates_count=duplicates_count,
    )


if __name__ == "__main__":
    # Simulation of received packet IDs with some losses and duplicates
    packet_id = [1, 2, 3, 3, 5]  # Missing 4, but 3 is duplicated (MAC duplicate)
    esp_ts = [100, 200, 300, 310, 500]
    df = pd.DataFrame(
        {
            "packet_id": packet_id,
            "esp_ts": esp_ts,
        }
    )

    TOTAL_SENT = 5

    print("\n--- PDR Analysis ---")
    result_pdr = calculate_pdr(df["packet_id"], TOTAL_SENT)

    print(f"PDR: {result_pdr.ratio_percent:.2f}%")
    print(f"Total Expected: {result_pdr.total_expected}")
    print(f"Unique Received: {result_pdr.unique_received}")
    print(f"Lost Count: {result_pdr.lost_count}")
    print(f"Duplicates Count: {result_pdr.duplicates_count}")
