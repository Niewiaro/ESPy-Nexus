from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True, slots=True)
class OutOfOrderResult:
    total_ooo_count: int
    ooo_ids: list[int]
    max_id_displacement: int


def calculate_out_of_order(received_ids: pd.Series) -> OutOfOrderResult:
    """
    Analyze the stream for chronology violations.
    Correctly detects delayed duplicates (Ghost Packets) and packets
    received out of sequence, while ignoring immediate hardware-level
    retransmissions (MAC Layer Stutter).

    Args:
        received_ids: Series containing received packet identifiers.
    Returns:
        OutOfOrderResult with the number of violations.
    """
    if received_ids.empty:
        return OutOfOrderResult(0, [], 0)

    ooo_ids: list[int] = []
    max_displacement = 0
    max_id_seen = -1

    for current_id in received_ids.dropna().astype(int):
        if current_id > max_id_seen:
            max_id_seen = current_id

        elif current_id < max_id_seen:
            ooo_ids.append(current_id)

            displacement = max_id_seen - current_id
            if displacement > max_displacement:
                max_displacement = displacement

        else:
            # current_id == max_id_seen
            # MAC duplicate, ignore for out-of-order analysis
            pass

    return OutOfOrderResult(
        total_ooo_count=len(ooo_ids),
        ooo_ids=ooo_ids,
        max_id_displacement=max_displacement,
    )


def print_out_of_order_result(result: OutOfOrderResult) -> None:
    print("--- Out-of-Order Analysis ---")
    print(f"Total Out-of-Order Count: {result.total_ooo_count}")
    print(f"Out-of-Order IDs: {result.ooo_ids}")
    print(f"Max ID Displacement: {result.max_id_displacement}")


if __name__ == "__main__":
    from espy_nexus.metrics.simulation import MockTestScenario

    mock_test_scenario = MockTestScenario()

    result_jitter = calculate_out_of_order(mock_test_scenario.df["packet_id"])
    print_out_of_order_result(result_jitter)
