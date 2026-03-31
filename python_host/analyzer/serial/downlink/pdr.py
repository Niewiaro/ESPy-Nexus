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


def print_pdr_result(result: PdrResult) -> None:
    print("--- PDR Analysis ---")
    print(f"PDR: {result.ratio_percent:.2f}%")
    print(f"Total Expected: {result.total_expected}")
    print(f"Unique Received: {result.unique_received}")
    print(f"Lost Count: {result.lost_count}")
    print(f"Duplicates Count: {result.duplicates_count}")


if __name__ == "__main__":
    from simulation import Config

    config = Config()

    result_pdr = calculate_pdr(config.df["packet_id"], config.total_sent)
    print_pdr_result(result_pdr)
