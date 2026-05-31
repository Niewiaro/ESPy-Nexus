from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass(frozen=True, slots=True)
class TimingTrendsResult:
    clock_drift_ppm: float  # Clock drift in Parts Per Million
    max_queuing_delay_us: float  # Maximum relative deviation (queuing peak)
    avg_queuing_delay_us: float  # Average buffer fill
    queuing_delay_percent: (
        float  # Percentage of time spent in buffer (relative to total OWD)
    )
    trend_slope: float  # Slope coefficient (μs delay per μs of test)


def calculate_timing_trends(
    pc_timestamps: pd.Series, esp_timestamps: pd.Series, expected_iat_us: float
) -> TimingTrendsResult:
    """
    Calculates relative delay trend (Queuing Delay) and hardware crystal drift.
    Assumes both series are aligned (refer to the same successfully received packets).

    Args:
        pc_timestamps: Series with packet transmission times (PC).
        esp_timestamps: Series with packet reception times (ESP32).
    Returns:
        TimingTrendsResult object with timing trend analysis.
    """
    if len(pc_timestamps) != len(esp_timestamps):
        raise ValueError(
            "PC and ESP time series must have identical length (received packets only)."
        )

    if len(pc_timestamps) < 2:
        return TimingTrendsResult(0.0, 0.0, 0.0, 0.0, 0.0)

    # One-Way Delay (OWD)
    owd_raw = esp_timestamps - pc_timestamps

    # Relative OWD (Queuing Delay)
    # Assume the packet with minimum OWD_raw had zero queueing on the router.
    # This normalizes the Y axis to zero. Each value > 0 represents time spent in L3/L4 buffers (or drift).
    owd_rel = owd_raw - owd_raw.min()

    max_queuing_delay_us = float(owd_rel.max())
    avg_queuing_delay_us = float(owd_rel.mean())
    queuing_delay_percent = (avg_queuing_delay_us / expected_iat_us) * 100

    # Hardware Clock Drift in PPM
    # Measure total test duration (from first to last received packet)
    duration_pc = float(pc_timestamps.iloc[-1] - pc_timestamps.iloc[0])
    duration_esp = float(esp_timestamps.iloc[-1] - esp_timestamps.iloc[0])

    drift_ppm = 0.0
    if duration_pc > 0:
        # PPM = ((time_measured_by_ESP - actual_time_PC) / actual_time_PC) * 1 000 000
        drift_ppm = ((duration_esp - duration_pc) / duration_pc) * 1_000_000.0

    # Linear Trend Analysis (Queuing Delay Direction)
    # Use linear regression (least squares) to find the slope.
    # If slope is strongly positive, queuing delay grows infinitely (control failure).
    try:
        # Normalize pc_timestamps to zero for better floating-point precision
        x = pc_timestamps - pc_timestamps.iloc[0]
        # First-degree polynomial (y = ax + b), extract 'a'
        poly = np.polyfit(x, owd_rel, 1)
        slope = float(poly[0])
    except Exception:
        slope = 0.0

    return TimingTrendsResult(
        clock_drift_ppm=drift_ppm,
        max_queuing_delay_us=max_queuing_delay_us,
        avg_queuing_delay_us=avg_queuing_delay_us,
        queuing_delay_percent=queuing_delay_percent,
        trend_slope=slope,
    )


def print_timing_trends_result(result: TimingTrendsResult) -> None:
    print("--- Timing Trends Analysis (Queuing Delay & Hardware Drift) ---")
    print(f"Clock Drift: {result.clock_drift_ppm:.2f} ppm")
    print(f"Max Queuing Delay: {result.max_queuing_delay_us:.2f} μs")
    print(f"Avg Queuing Delay: {result.avg_queuing_delay_us:.2f} μs")
    print(f"Queuing Delay Percent: {result.queuing_delay_percent:.2f}%")
    print(f"Queuing Delay Trend Slope: {result.trend_slope:.6f} μs/μs")


if __name__ == "__main__":
    from espy_nexus.metrics.simulation import MockTestScenario

    mock_test_scenario = MockTestScenario()
    print(mock_test_scenario.df)
    result = calculate_timing_trends(
        mock_test_scenario.df["pc_ts"],
        mock_test_scenario.df["esp_ts"],
        mock_test_scenario.expected_iat_us,
    )
    print_timing_trends_result(result)
