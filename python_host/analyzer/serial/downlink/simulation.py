from dataclasses import dataclass, field
import pandas as pd


from pdr import calculate_pdr, print_pdr_result
from jitter import calculate_jitter, print_jitter_result
from burst_loss import calculate_burst_loss, print_burst_loss_result
from goodput import calculate_goodput, print_goodput_result
from out_of_order import calculate_out_of_order, print_out_of_order_result
from timing_trends import calculate_timing_trends, print_timing_trends_result


@dataclass
class MockTestScenario:
    """Container for mock test data simulating a downlink scenario with specific anomalies."""

    total_sent: int = 5
    packet_ids: list[int] = field(default_factory=lambda: [0, 1, 2, 2, 4])
    pc_ts: list[int] = field(
        default_factory=lambda: [1_000_000, 1_000_100, 1_000_200, 1_000_200, 1_000_400]
    )
    esp_ts: list[int] = field(default_factory=lambda: [100, 200, 300, 310, 500])
    df: pd.DataFrame = field(init=False)

    def __post_init__(self) -> None:
        lengths = {len(self.packet_ids), len(self.pc_ts), len(self.esp_ts)}
        if len(lengths) > 1:
            raise ValueError(
                f"Inconsistent data vectors! packet_ids: {len(self.packet_ids)}, "
                f"pc_ts: {len(self.pc_ts)}, esp_ts: {len(self.esp_ts)}"
            )

        self.df = pd.DataFrame(
            {
                "packet_id": self.packet_ids,
                "pc_ts": self.pc_ts,
                "esp_ts": self.esp_ts,
            }
        )


def main() -> None:
    mockTestScenario = MockTestScenario()

    result_pdr = calculate_pdr(
        mockTestScenario.df["packet_id"], mockTestScenario.total_sent
    )
    print_pdr_result(result_pdr)
    print()

    result_jitter = calculate_jitter(mockTestScenario.df["esp_ts"])
    print_jitter_result(result_jitter)
    print()

    result_burst_loss = calculate_burst_loss(
        mockTestScenario.df["packet_id"], mockTestScenario.total_sent
    )
    print_burst_loss_result(result_burst_loss)
    print()

    result_goodput = calculate_goodput(
        mockTestScenario.df["packet_id"],
        mockTestScenario.df["esp_ts"],
        payload_size_bytes=20,
    )
    print_goodput_result(result_goodput)
    print()

    result_out_of_order = calculate_out_of_order(mockTestScenario.df["packet_id"])
    print_out_of_order_result(result_out_of_order)
    print()

    result_timing_trends = calculate_timing_trends(
        mockTestScenario.df["pc_ts"], mockTestScenario.df["esp_ts"]
    )
    print_timing_trends_result(result_timing_trends)
    print()


if __name__ == "__main__":
    main()
