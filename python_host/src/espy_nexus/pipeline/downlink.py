import pandas as pd
from dataclasses import dataclass

from espy_nexus.metrics.pdr import PdrResult, calculate_pdr, print_pdr_result
from espy_nexus.metrics.jitter import (
    JitterResult,
    calculate_jitter,
    print_jitter_result,
)
from espy_nexus.metrics.burst_loss import (
    BurstLossResult,
    calculate_burst_loss,
    print_burst_loss_result,
)
from espy_nexus.metrics.goodput import (
    GoodputResult,
    calculate_goodput,
    print_goodput_result,
)
from espy_nexus.metrics.out_of_order import (
    OutOfOrderResult,
    calculate_out_of_order,
    print_out_of_order_result,
)
from espy_nexus.metrics.timing_trends import (
    TimingTrendsResult,
    calculate_timing_trends,
    print_timing_trends_result,
)


@dataclass(frozen=True, slots=True)
class DownlinkMetrics:
    """Structure holding the complete report from Downlink signal analysis."""

    pdr: PdrResult
    jitter: JitterResult
    burst_loss: BurstLossResult
    goodput: GoodputResult
    out_of_order: OutOfOrderResult
    timing_trends: TimingTrendsResult


class DownlinkAnalyzer:
    """
    Main Downlink analyzer (PC -> ESP32) - Facade pattern.
    Expects a DataFrame structure joined by TestEngine (Outer Join).
    Prepares, cleans, and safely sorts the data before passing it
    to specialized mathematical modules.
    """

    def __init__(self, frequency_hz: float, payload_size_bytes: int = 16) -> None:
        self.payload_size_bytes = payload_size_bytes
        self.frequency_hz = frequency_hz
        self.expected_iat_us = 1_000_000 / frequency_hz

    def calculate_all_metrics(
        self, df: pd.DataFrame, total_sent: int
    ) -> DownlinkMetrics:

        # --- Input Validation ---
        if df.empty:
            raise ValueError(
                "The input DataFrame is empty. Metrics cannot be calculated."
            )

        expected_columns = {"packet_id", "pc_tx_ts", "esp_rx_ts", "rx_seq"}
        if not expected_columns.issubset(df.columns):
            raise ValueError(
                f"The TestEngine DataFrame must contain the following columns: {expected_columns}"
            )

        if total_sent <= 0:
            raise ValueError("The total_sent parameter must be a positive number.")

        # =========================================================
        # 1. PDR and LOST PACKETS (Analysis on the full dataset)
        # =========================================================
        # For PDR, pass IDs of packets that have a real receive timestamp
        # (they were not lost on the bus).
        received_mask = df["esp_rx_ts"].notna()
        rx_sorted_df = df[received_mask].sort_values(by="rx_seq")
        successfully_received_ids = rx_sorted_df["packet_id"]

        result_pdr = calculate_pdr(successfully_received_ids, total_sent)

        # =========================================================
        # 2. BURST LOSS
        # =========================================================
        # Burst loss analysis requires knowledge of all transmission attempts
        # (including those marked as NaN after the Outer Join).
        result_burst_loss = calculate_burst_loss(
            successfully_received_ids, total_sent, self.expected_iat_us
        )

        # =========================================================
        # 3. DATA CLEANING
        # =========================================================
        # From this point on, time-based analysis requires completely clean data.
        # We drop lost packets (NaN). Only duplicates and correctly delivered
        # packets are kept.
        clean_df = df.dropna(subset=["pc_tx_ts", "esp_rx_ts", "rx_seq"]).copy()

        if clean_df.empty:
            raise ValueError(
                "No correctly received packets. "
                "Signal quality analysis (Jitter/Goodput) is impossible (PDR = 0%)."
            )

        # =========================================================
        # 4. RECEIVE ORDER (OUT-OF-ORDER)
        # =========================================================
        # Sort the DataFrame in the order packets were physically received over time.
        # Only then will the Out-Of-Order algorithm detect shifts in 'packet_id'.
        ordered_by_rx = clean_df.sort_values(by="rx_seq")
        result_out_of_order = calculate_out_of_order(ordered_by_rx["packet_id"])

        # =========================================================
        # 5. TIME METRICS (JITTER & TRENDS)
        # =========================================================
        # Sorting change: For Jitter and delays, the data must be ordered
        # chronologically by transmission intent (packet_id). Otherwise,
        # time-shifted packets (Out-Of-Order) will create unrealistic, massive
        # noise in the calculations.
        deduplicated_df = clean_df.drop_duplicates(
            subset=["packet_id"], keep="first"
        ).copy()

        deduplicated_df.sort_values(by="packet_id", inplace=True)

        pc_timestamps = deduplicated_df["pc_tx_ts"]
        esp_timestamps = deduplicated_df["esp_rx_ts"]

        result_jitter = calculate_jitter(esp_timestamps, self.expected_iat_us)
        result_timing_trends = calculate_timing_trends(
            pc_timestamps, esp_timestamps, self.expected_iat_us
        )

        # =========================================================
        # 6. THROUGHPUT (GOODPUT)
        # =========================================================
        # Goodput ignores retransmissions, so we pass a list from which the
        # calculation function will internally remove duplicate IDs.
        result_goodput = calculate_goodput(
            deduplicated_df["packet_id"],
            deduplicated_df["esp_rx_ts"],
            self.frequency_hz,
            self.payload_size_bytes,
        )

        # Build the result facade
        return DownlinkMetrics(
            pdr=result_pdr,
            jitter=result_jitter,
            burst_loss=result_burst_loss,
            goodput=result_goodput,
            out_of_order=result_out_of_order,
            timing_trends=result_timing_trends,
        )

    def print_report(self, metrics: DownlinkMetrics) -> None:
        """Short console reporting of results (used mainly outside TestEngine)."""
        print_pdr_result(metrics.pdr)
        print()
        print_jitter_result(metrics.jitter)
        print()
        print_burst_loss_result(metrics.burst_loss)
        print()
        print_goodput_result(metrics.goodput)
        print()
        print_out_of_order_result(metrics.out_of_order)
        print()
        print_timing_trends_result(metrics.timing_trends)


if __name__ == "__main__":
    # Quick facade test if the MockTestScenario class generates a valid DataFrame
    try:
        from espy_nexus.metrics.simulation import MockTestScenario

        mock_test_scenario = MockTestScenario()

        # If MockTestScenario generates the old format (pc_ts, esp_ts),
        # make sure the test structure contains:
        # 'packet_id', 'pc_tx_ts', 'esp_rx_ts', and 'rx_seq' before testing here.

        analyzer = DownlinkAnalyzer(
            payload_size_bytes=20, frequency_hz=mock_test_scenario.frequency_hz
        )
        metrics = analyzer.calculate_all_metrics(
            mock_test_scenario.df, mock_test_scenario.total_sent
        )
        analyzer.print_report(metrics)
    except Exception as e:
        print(
            f"[TEST FAIL] Make sure MockTestScenario uses the updated column names from the Outer Join: {e}"
        )
