from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass(frozen=True, slots=True)
class TimingTrendsResult:
    clock_drift_ppm: float  # Clock drift in Parts Per Million
    max_bufferbloat_us: float  # Maximum relative deviation (queuing peak)
    avg_bufferbloat_us: float  # Average buffer fill
    trend_slope: float  # Slope coefficient (μs delay per μs of test)


def calculate_timing_trends(
    pc_timestamps: pd.Series, esp_timestamps: pd.Series
) -> TimingTrendsResult:
    """
    Calculates relative delay trend (Bufferbloat) and hardware crystal drift.
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
        return TimingTrendsResult(0.0, 0.0, 0.0, 0.0)

    # One-Way Delay (OWD)
    owd_raw = esp_timestamps - pc_timestamps

    # Relative OWD (Bufferbloat)
    # Assume the packet with minimum OWD_raw had zero queueing on the router.
    # This normalizes the Y axis to zero. Each value > 0 represents time spent in L3/L4 buffers (or drift).
    owd_rel = owd_raw - owd_raw.min()

    max_bufferbloat = float(owd_rel.max())
    avg_bufferbloat = float(owd_rel.mean())

    # Hardware Clock Drift in PPM
    # Measure total test duration (from first to last received packet)
    duration_pc = float(pc_timestamps.iloc[-1] - pc_timestamps.iloc[0])
    duration_esp = float(esp_timestamps.iloc[-1] - esp_timestamps.iloc[0])

    drift_ppm = 0.0
    if duration_pc > 0:
        # PPM = ((time_measured_by_ESP - actual_time_PC) / actual_time_PC) * 1 000 000
        drift_ppm = ((duration_esp - duration_pc) / duration_pc) * 1_000_000.0

    # Linear Trend Analysis (Bufferbloat Direction)
    # Use linear regression (least squares) to find the slope.
    # If slope is strongly positive, buffer grows infinitely (control failure).
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
        max_bufferbloat_us=max_bufferbloat,
        avg_bufferbloat_us=avg_bufferbloat,
        trend_slope=slope,
    )


def print_timing_trends_result(result: TimingTrendsResult) -> None:
    print("--- Timing Trends Analysis ---")
    print(f"Clock Drift: {result.clock_drift_ppm:.2f} ppm")
    print(f"Max Bufferbloat: {result.max_bufferbloat_us:.2f} μs")
    print(f"Avg Bufferbloat: {result.avg_bufferbloat_us:.2f} μs")
    print(f"Bufferbloat Trend Slope: {result.trend_slope:.6f} μs/μs")


if __name__ == "__main__":
    from simulation import MockTestScenario

    mockTestScenario = MockTestScenario()
    print(mockTestScenario.df)
    result = calculate_timing_trends(
        mockTestScenario.df["pc_ts"], mockTestScenario.df["esp_ts"]
    )
    print_timing_trends_result(result)
