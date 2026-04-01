from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True, slots=True)
class JitterResult:
    expected_iat_us: (
        float  # Expected inter-arrival time in microseconds (for reference)
    )
    mean_us: float  # Mean inter-arrival time
    mean_error_us: float  # Mean error from expected IAT (mean - expected)
    std_us: float  # Standard deviation (classical Jitter)
    cv_percent: float  # Coefficient of Variation (std/mean * 100) for relative jitter
    max_us: float  # Longest interval in communication
    min_us: float  # Shortest interval (burst detection)
    max_deviation_us: float  # Peak delay relative to mean (max - mean)
    min_deviation_us: float  # Peak acceleration relative to mean (min - mean)


def calculate_jitter(esp_timestamps: pd.Series, expected_iat_us: float) -> JitterResult:
    """
    Calculates the complete jitter profile based on inter-arrival times (IAT) of packets.

    Args:
        esp_timestamps: Series containing timestamps from ESP32 (in microseconds).
        expected_iat_us: Expected inter-arrival time in microseconds.

    Returns:
        JitterResult object. Returns zeroed object if insufficient data (fewer than 2 packets).
    """
    if len(esp_timestamps) < 2:
        return JitterResult(expected_iat_us, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    # Calculate inter-arrival time intervals (IAT) and drop the first empty row
    iat = esp_timestamps.diff().dropna()

    # Calculate basic metrics using vectorized Pandas functions
    mean_val = float(iat.mean())
    max_val = float(iat.max())
    min_val = float(iat.min())

    # Standard deviation requires at least 2 intervals (3 packets) for meaningful results,
    std_val = float(iat.std())
    if pd.isna(std_val):
        std_val = 0.0

    cv_val = (std_val / mean_val * 100.0) if mean_val > 0 else 0.0

    return JitterResult(
        expected_iat_us=expected_iat_us,
        mean_us=mean_val,
        mean_error_us=mean_val - expected_iat_us,
        std_us=std_val,
        cv_percent=cv_val,
        max_us=max_val,
        min_us=min_val,
        max_deviation_us=max_val - mean_val,
        min_deviation_us=min_val - mean_val,
    )


def print_jitter_result(result: JitterResult) -> None:
    print("--- Jitter Analysis ---")
    print(f"Expected IAT: {result.expected_iat_us:.2f} us")
    print(f"Mean IAT: {result.mean_us:.2f} us")
    print(f"Mean Error from Expected: {result.mean_error_us:.2f} us")
    print(f"Jitter (Std Dev): {result.std_us:.2f} us")
    print(f"Coefficient of Variation: {result.cv_percent:.2f} %")
    print(f"Max IAT: {result.max_us:.2f} us")
    print(f"Min IAT: {result.min_us:.2f} us")
    print(f"Max Deviation from Mean: {result.max_deviation_us:.2f} us")
    print(f"Min Deviation from Mean: {result.min_deviation_us:.2f} us")


if __name__ == "__main__":
    from espy_nexus.metrics.simulation import MockTestScenario

    mock_test_scenario = MockTestScenario()

    result_jitter = calculate_jitter(
        mock_test_scenario.df["esp_ts"], mock_test_scenario.expected_iat_us
    )
    print_jitter_result(result_jitter)
