from enum import Enum, auto
from dataclasses import dataclass, field
import pandas as pd
import numpy as np


class AnomalyType(Enum):
    IDEAL = auto()
    PDR_AND_DUPLICATES = auto()
    JITTER = auto()
    BURST_LOSS = auto()
    GOODPUT = auto()
    OUT_OF_ORDER = auto()
    QUEUING_AND_DRIFT = auto()


@dataclass
class MockTestScenario:
    """
    Generator of prepared test data imitating the structure
    after performing an OUTER JOIN operation in TestEngine.
    """

    anomaly: AnomalyType = AnomalyType.IDEAL

    total_sent: int = 5
    expected_iat_us: float = 100.0
    frequency_hz: float = 1_000_000 / 100.0  # 10 kHz

    packet_ids: list[int] = field(init=False)
    pc_tx_ts: list[int] = field(init=False)
    esp_rx_ts: list[float] = field(init=False)

    df: pd.DataFrame = field(init=False)

    def __post_init__(self) -> None:
        """
        --- PDR Analysis & Duplicate Detection ---
        PDR: 100.00%
        Total Expected: 5
        Unique Received: 5
        Lost Count: 0
        MAC Duplicates: 0
        Ghost Duplicates: 0

        --- Jitter Analysis ---
        Expected IAT: 100.00 us
        Mean IAT: 100.00 us
        Mean Error from Expected: 0.00 us
        Jitter (Std Dev): 0.00 us
        Coefficient of Variation: 0.00 %
        Max IAT: 100.00 us
        Min IAT: 100.00 us
        Max Deviation from Mean: 0.00 us
        Min Deviation from Mean: 0.00 us

        --- Burst Loss Analysis ---
        Total Burst Events: 0
        Max Burst Length: 0
        Max Blackout Time (ms): 0.00
        Burst Events by Length:

        --- Goodput Analysis ---
        Goodput: 200000.00 B/s
        Efficiency: 100.00 %
        Goodput: 195.31 KB/s
        Goodput: 1.60 Mbps

        --- Out-of-Order Analysis ---
        Total Out-of-Order Count: 0
        Out-of-Order IDs: []
        Max ID Displacement: 0
        """
        # 1. BASE: IDEAL SCENARIO
        self.packet_ids = [0, 1, 2, 3, 4]
        self.pc_tx_ts = [1_000_000, 1_000_100, 1_000_200, 1_000_300, 1_000_400]
        self.esp_rx_ts = [100.0, 200.0, 300.0, 400.0, 500.0]

        # 2. SCENARIO-DEPENDENT MUTATIONS
        if self.anomaly == AnomalyType.PDR_AND_DUPLICATES:
            """
            --- PDR Analysis & Duplicate Detection ---
            PDR: 80.00%
            Unique Received: 4
            Lost Count: 1
            MAC Duplicates: 1
            Ghost Duplicates: 1

            --- Jitter Analysis ---
            Mean IAT: 133.33 us
            Jitter (Std Dev): 57.74 us
            Coefficient of Variation: 43.30 %
            Max IAT: 200.00 us

            --- Burst Loss Analysis ---
            Total Burst Events: 1
            Max Burst Length: 1

            --- Goodput Analysis ---
            Goodput: 150000.00 B/s
            Efficiency: 75.00 %

            --- Out-of-Order Analysis ---
            Total Out-of-Order Count: 1
            Out-of-Order IDs: [0]
            """
            self.packet_ids = [0, 0, 1, 1, 2, 3, 4]
            self.pc_tx_ts = [
                1_000_000,
                1_000_000,
                1_000_100,
                1_000_100,
                1_000_200,
                1_000_300,
                1_000_400,
            ]
            self.esp_rx_ts = [100.0, 250.0, 200.0, 210.0, np.nan, 400.0, 500.0]

        elif self.anomaly == AnomalyType.JITTER:
            """
            --- Jitter Analysis ---
            Jitter (Std Dev): 58.31 us
            Coefficient of Variation: 58.31 %
            Max IAT: 150.00 us
            Min IAT: 40.00 us
            Max Deviation from Mean: 50.00 us
            Min Deviation from Mean: -60.00 us

            --- Timing Trends Analysis ---
            Max Queuing Delay: 100.00 μs
            Avg Queuing Delay: 52.00 μs
            Queuing Delay Percent: 52.00%
            Queuing Delay Trend Slope: -0.100000 μs/μs
            """
            self.esp_rx_ts = [100.0, 250.0, 310.0, 350.0, 500.0]

        elif self.anomaly == AnomalyType.BURST_LOSS:
            """
            --- PDR Analysis & Duplicate Detection ---
            PDR: 40.00%
            Unique Received: 2
            Lost Count: 3

            --- Jitter Analysis ---
            Mean IAT: 400.00 us
            Mean Error from Expected: 300.00 us
            Jitter (Std Dev): 0.00 us

            --- Burst Loss Analysis ---
            Total Burst Events: 1
            Max Burst Length: 3
            Max Blackout Time (ms): 0.30
            Burst Events by Length:
              Length 3: 1 bursts, starting at IDs [1]

            --- Goodput Analysis ---
            Goodput: 50000.00 B/s
            Efficiency: 25.00 %
            """
            self.esp_rx_ts = [100.0, np.nan, np.nan, np.nan, 500.0]

        elif self.anomaly == AnomalyType.GOODPUT:
            """
            --- PDR Analysis & Duplicate Detection ---
            PDR: 80.00%
            Lost Count: 1
            MAC Duplicates: 1

            --- Jitter Analysis ---
            Mean IAT: 133.33 us
            Jitter (Std Dev): 57.74 us
            Coefficient of Variation: 43.30 %
            Max IAT: 200.00 us

            --- Burst Loss Analysis ---
            Total Burst Events: 1
            Max Burst Length: 1
            Max Blackout Time (ms): 0.10
            Burst Events by Length: Length 1: 1 bursts, starting at IDs [3]

            --- Goodput Analysis ---
            Goodput: 150000.00 B/s
            Efficiency: 75.00 %
            Goodput: 146.48 KB/s
            Goodput: 1.20 Mbps
            """
            self.packet_ids = [0, 1, 2, 2, 3, 4]
            self.pc_tx_ts = [
                1_000_000,
                1_000_100,
                1_000_200,
                1_000_200,
                1_000_300,
                1_000_400,
            ]
            self.esp_rx_ts = [100.0, 200.0, 300.0, 310.0, np.nan, 500.0]

        elif self.anomaly == AnomalyType.OUT_OF_ORDER:
            """
            --- Jitter Analysis ---
            Jitter (Std Dev): 141.42 us
            Coefficient of Variation: 141.42 %
            Max IAT: 200.00 us
            Min IAT: -100.00 us
            Max Deviation from Mean: 100.00 us
            Min Deviation from Mean: -200.00 us

            --- Out-of-Order Analysis ---
            Total Out-of-Order Count: 1
            Out-of-Order IDs: [2]
            Max ID Displacement: 1

            --- Timing Trends Analysis ---
            Max Queuing Delay: 200.00 μs
            Avg Queuing Delay: 100.00 μs
            Queuing Delay Percent: 100.00%
            Queuing Delay Trend Slope: -0.100000 μs/μs
            """
            self.esp_rx_ts[2] = 400.0
            self.esp_rx_ts[3] = 300.0

        elif self.anomaly == AnomalyType.QUEUING_AND_DRIFT:
            """
            --- Jitter Analysis ---
            Mean IAT: 142.50 us
            Mean Error from Expected: 42.50 us
            Jitter (Std Dev): 17.08 us
            Coefficient of Variation: 11.98 %
            Max IAT: 165.00 us
            Min IAT: 125.00 us
            Max Deviation from Mean: 22.50 us
            Min Deviation from Mean: -17.50 us

            --- Goodput Analysis ---
            Goodput: 140350.88 B/s
            Efficiency: 70.18 %
            Goodput: 137.06 KB/s
            Goodput: 1.12 Mbps

            --- Timing Trends Analysis ---
            Clock Drift: 425000.00 ppm
            Max Queuing Delay: 170.00 μs
            Avg Queuing Delay: 72.00 μs
            Queuing Delay Percent: 72.00%
            Queuing Delay Trend Slope: 0.420000 μs/μs
            """
            self.esp_rx_ts = [100.0, 225.0, 360.0, 505.0, 670.0]

        # 3. COMPOSE INTO DATAFRAME
        lengths = {
            len(self.packet_ids),
            len(self.pc_tx_ts),
            len(self.esp_rx_ts),
        }

        if len(lengths) > 1:
            raise ValueError(
                f"Data consistency error for scenario {self.anomaly.name}!"
            )

        self.df = pd.DataFrame(
            {
                "packet_id": self.packet_ids,
                "pc_tx_ts": self.pc_tx_ts,
                "esp_rx_ts": self.esp_rx_ts,
            }
        )


if __name__ == "__main__":
    from espy_nexus.pipeline.downlink import DownlinkAnalyzer

    for anomaly in AnomalyType:
        scenario = MockTestScenario(anomaly=anomaly)
        print(f"\n{'='*50}\nSCENARIO: {anomaly.name}\n{'='*50}")
        print(scenario.df.to_string(index=False))

        analyzer = DownlinkAnalyzer(
            payload_size_bytes=20, frequency_hz=scenario.frequency_hz
        )
        metrics = analyzer.calculate_all_metrics(scenario.df, scenario.total_sent)
        analyzer.print_report(metrics)
