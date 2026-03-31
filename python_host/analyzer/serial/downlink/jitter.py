from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True, slots=True)
class JitterResult:
    mean_us: float  # Mean inter-arrival time
    std_us: float  # Standard deviation (classical Jitter)
    max_us: float  # Longest interval in communication
    min_us: float  # Shortest interval (burst detection)
    max_deviation_us: float  # Peak delay relative to mean (max - mean)
    min_deviation_us: float  # Peak acceleration relative to mean (min - mean)


def calculate_jitter(esp_timestamps: pd.Series) -> JitterResult:
    """
    Calculates the complete jitter profile based on inter-arrival times (IAT) of packets.

    Args:
        esp_timestamps: Series containing timestamps from ESP32 (in microseconds).

    Returns:
        JitterResult object. Returns zeroed object if insufficient data (fewer than 2 packets).
    """
    if len(esp_timestamps) < 2:
        return JitterResult(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

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

    return JitterResult(
        mean_us=mean_val,
        std_us=std_val,
        max_us=max_val,
        min_us=min_val,
        max_deviation_us=max_val - mean_val,
        min_deviation_us=min_val - mean_val,
    )


def print_jitter_result(result: JitterResult) -> None:
    print("--- Jitter Analysis ---")
    print(f"Mean IAT: {result.mean_us:.2f} us")
    print(f"Jitter (Std Dev): {result.std_us:.2f} us")
    print(f"Max IAT: {result.max_us:.2f} us")
    print(f"Min IAT: {result.min_us:.2f} us")
    print(f"Max Deviation from Mean: {result.max_deviation_us:.2f} us")
    print(f"Min Deviation from Mean: {result.min_deviation_us:.2f} us")


if __name__ == "__main__":
    from simulation import Config

    config = Config()

    result_jitter = calculate_jitter(config.df["esp_ts"])
    print_jitter_result(result_jitter)
