import pandas as pd
from dataclasses import dataclass


from pdr import PdrResult, calculate_pdr, print_pdr_result
from jitter import JitterResult, calculate_jitter, print_jitter_result
from burst_loss import BurstLossResult, calculate_burst_loss, print_burst_loss_result
from goodput import GoodputResult, calculate_goodput, print_goodput_result
from out_of_order import (
    OutOfOrderResult,
    calculate_out_of_order,
    print_out_of_order_result,
)
from timing_trends import (
    TimingTrendsResult,
    calculate_timing_trends,
    print_timing_trends_result,
)


@dataclass(frozen=True, slots=True)
class DownlinkMetrics:
    pdr: PdrResult
    jitter: JitterResult
    burst_loss: BurstLossResult
    goodput: GoodputResult
    out_of_order: OutOfOrderResult
    timing_trends: TimingTrendsResult


class DownlinkAnalyzer:
    """Main downlink analyzer (PC -> ESP32)."""

    def __init__(self, payload_size_bytes: int = 16) -> None:
        self.payload_size_bytes = payload_size_bytes

    def calculate_all_metrics(
        self, df: pd.DataFrame, total_sent: int
    ) -> DownlinkMetrics:
        if df.empty:
            raise ValueError("Input DataFrame is empty. Cannot calculate metrics.")

        if not {"packet_id", "pc_ts", "esp_ts"}.issubset(df.columns):
            raise ValueError(
                "DataFrame must contain 'packet_id', 'pc_ts', and 'esp_ts' columns."
            )

        if total_sent <= 0:
            raise ValueError("total_sent must be a positive integer.")

        clean_df = df.dropna(subset=["packet_id", "pc_ts", "esp_ts"])

        packet_ids = clean_df["packet_id"]
        pc_timestamps = clean_df["pc_ts"]
        esp_timestamps = clean_df["esp_ts"]

        result_pdr = calculate_pdr(packet_ids, total_sent)
        result_jitter = calculate_jitter(esp_timestamps)
        result_burst_loss = calculate_burst_loss(packet_ids, total_sent)
        result_goodput = calculate_goodput(
            packet_ids, esp_timestamps, self.payload_size_bytes
        )
        result_out_of_order = calculate_out_of_order(packet_ids)
        result_timing_trends = calculate_timing_trends(pc_timestamps, esp_timestamps)

        return DownlinkMetrics(
            pdr=result_pdr,
            jitter=result_jitter,
            burst_loss=result_burst_loss,
            goodput=result_goodput,
            out_of_order=result_out_of_order,
            timing_trends=result_timing_trends,
        )

    def print_report(self, metrics: DownlinkMetrics) -> None:
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
