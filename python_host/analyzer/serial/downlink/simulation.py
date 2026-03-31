from dataclasses import dataclass, field
import pandas as pd


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
    from pipeline import DownlinkAnalyzer

    mock_test_scenario = MockTestScenario()
    analyzer = DownlinkAnalyzer(payload_size_bytes=20)
    metrics = analyzer.calculate_all_metrics(
        mock_test_scenario.df, mock_test_scenario.total_sent
    )
    analyzer.print_report(metrics)


if __name__ == "__main__":
    main()
