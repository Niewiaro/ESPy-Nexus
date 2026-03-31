from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True, slots=True)
class PdrResult:
    ratio_percent: float
    total_expected: int
    unique_received: int
    lost_count: int
    mac_duplicates_count: int  # instant duplicates (ACK fail)
    ghost_duplicates_count: int  # delayed duplicates (retransmissions)


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

    total_duplicates = int(len(received_ids) - unique_received)

    mac_duplicates = 0
    ghost_duplicates = 0

    if total_duplicates > 0:
        immediate_mask = received_ids == received_ids.shift(1)
        mac_duplicates = int(immediate_mask.sum())

        ghost_duplicates = total_duplicates - mac_duplicates

    ratio_percent = min(100.0, (unique_received / total_sent) * 100.0)

    return PdrResult(
        ratio_percent=ratio_percent,
        total_expected=total_sent,
        unique_received=unique_received,
        lost_count=lost_count,
        mac_duplicates_count=mac_duplicates,
        ghost_duplicates_count=ghost_duplicates,
    )


def print_pdr_result(result: PdrResult) -> None:
    print("--- PDR Analysis ---")
    print(f"PDR: {result.ratio_percent:.2f}%")
    print(f"Total Expected: {result.total_expected}")
    print(f"Unique Received: {result.unique_received}")
    print(f"Lost Count: {result.lost_count}")
    print(f"MAC Duplicates: {result.mac_duplicates_count}")
    print(f"Ghost Duplicates: {result.ghost_duplicates_count}")


if __name__ == "__main__":
    from simulation import MockTestScenario

    mock_test_scenario = MockTestScenario()

    result_pdr = calculate_pdr(
        mock_test_scenario.df["packet_id"], mock_test_scenario.total_sent
    )
    print_pdr_result(result_pdr)
