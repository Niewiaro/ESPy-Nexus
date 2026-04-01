from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True, slots=True)
class BurstLossResult:
    total_burst_events: int
    max_burst_length: int
    # key: burst length, value: list of starting packet IDs for that burst length
    burst_events: dict[int, list[int]]


def calculate_burst_loss(received_ids: pd.Series, total_sent: int) -> BurstLossResult:
    """
    Analyzes the topology of lost packets by grouping them into bursts
    and recording their starting point.

    Args:
        received_ids: Series containing received packet IDs.
        total_sent: Total number of packets sent by the transmitter.

    Returns:
        BurstLossResult object with complete statistics about burst losses.
    """
    if total_sent <= 0:
        return BurstLossResult(0, 0, {})

    # Edge case: all packets lost. One burst of length total_sent, starting at ID 0.
    if received_ids.empty:
        return BurstLossResult(1, total_sent, {total_sent: [0]})

    # remove duplicates and NaN
    received_set = set(received_ids.dropna().astype(int))

    burst_events: dict[int, list[int]] = {}
    current_burst_len = 0
    current_burst_start = -1
    total_events = 0

    for packet_id in range(0, total_sent):
        if packet_id not in received_set:
            if current_burst_len == 0:
                current_burst_start = packet_id
            current_burst_len += 1
        else:
            if current_burst_len > 0:
                if current_burst_len not in burst_events:
                    burst_events[current_burst_len] = []
                burst_events[current_burst_len].append(current_burst_start)

                total_events += 1
                current_burst_len = 0

    # Edge case: if the last packets were lost, we need to record that burst as well
    if current_burst_len > 0:
        if current_burst_len not in burst_events:
            burst_events[current_burst_len] = []
        burst_events[current_burst_len].append(current_burst_start)
        total_events += 1

    max_len = max(burst_events.keys()) if burst_events else 0

    return BurstLossResult(
        total_burst_events=total_events,
        max_burst_length=max_len,
        burst_events=burst_events,
    )


def print_burst_loss_result(result: BurstLossResult) -> None:
    print("--- Burst Loss Analysis ---")
    print(f"Total Burst Events: {result.total_burst_events}")
    print(f"Max Burst Length: {result.max_burst_length}")
    print("Burst Events by Length:")
    for length, starts in sorted(result.burst_events.items()):
        print(f"  Length {length}: {len(starts)} bursts, starting at IDs {starts}")


if __name__ == "__main__":
    from espy_nexus.metrics.simulation import MockTestScenario

    mock_test_scenario = MockTestScenario()

    result_jitter = calculate_burst_loss(
        mock_test_scenario.df["packet_id"], mock_test_scenario.total_sent
    )
    print_burst_loss_result(result_jitter)
