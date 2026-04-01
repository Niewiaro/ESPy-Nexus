import pytest
import pandas as pd
from espy_nexus.metrics.timing_trends import calculate_timing_trends


class TestCalculateTimingTrends:

    def test_timing_trends_perfect_conditions(self):
        """
        Scenario: Ideal network and ideal clocks (0 PPM, 0 Bufferbloat).
        PC and ESP timestamp vectors have constant interval equal to 1000 µs (Offset).
        """
        pc_ts = pd.Series([1000, 2000, 3000, 4000])
        esp_ts = pd.Series([2000, 3000, 4000, 5000])
        expected_iat = 1000.0

        result = calculate_timing_trends(pc_ts, esp_ts, expected_iat)

        assert result.clock_drift_ppm == 0.0
        assert result.max_bufferbloat_us == 0.0
        assert result.avg_bufferbloat_us == 0.0
        assert result.bufferbloat_percent == 0.0  # Zero zatoru
        assert result.trend_slope == 0.0

    def test_timing_trends_microscopic_anomaly(self):
        """
        Scenario: Ideal quartz (0 PPM), one microscopic anomaly in middle of test (duplicate MAC).
        """
        pc_ts = pd.Series([1000000, 1000100, 1000200, 1000200, 1000400])
        esp_ts = pd.Series([100, 200, 300, 310, 500])
        expected_iat = 100.0  # Na podstawie pc_ts odstęp to 100 µs

        result = calculate_timing_trends(pc_ts, esp_ts, expected_iat)

        # Measurement time for both is exactly 400 µs -> 0 Drift
        assert result.clock_drift_ppm == 0.0
        # OWD_rel: [0, 0, 0, 10, 0]
        assert result.max_bufferbloat_us == 10.0
        assert result.avg_bufferbloat_us == 2.0
        # 2.0 / 100.0 * 100 = 2.0%
        assert result.bufferbloat_percent == 2.0
        assert result.trend_slope == pytest.approx(0.002273, abs=1e-5)

    def test_timing_trends_extreme_clock_drift(self):
        """
        Scenario: Extremely slow ESP32 clock.
        Verifies that algorithm does not fail with strong negative offsets
        and 'time compression' phenomenon (negative slope).
        """
        pc_ts = pd.Series([1000000, 1100000, 1200000, 1200000, 1500000])
        esp_ts = pd.Series([100, 200, 300, 310, 500])
        expected_iat = 100000.0  # Odstępy w pc_ts wynoszą 100 000 µs

        result = calculate_timing_trends(pc_ts, esp_ts, expected_iat)

        assert result.clock_drift_ppm == pytest.approx(-999200.0)
        assert result.max_bufferbloat_us == 499600.0
        assert result.avg_bufferbloat_us == 299782.0
        # 299782.0 / 100000.0 * 100 = 299.782%
        assert result.bufferbloat_percent == pytest.approx(299.782)
        assert result.trend_slope == pytest.approx(-0.999214, abs=1e-5)

    def test_timing_trends_pure_bufferbloat_spike(self):
        """
        Scenario: Pure network congestion without quartz drift.
        Middle packet got stuck in buffer for 50 µs. Last packet arrived on time.
        """
        pc_ts = pd.Series([0, 100, 200, 300])
        # P2 experiences 'lag' of 50 µs, but P3 arrives normally.
        esp_ts = pd.Series([1000, 1100, 1250, 1300])
        expected_iat = 100.0

        result = calculate_timing_trends(pc_ts, esp_ts, expected_iat)

        assert result.clock_drift_ppm == 0.0
        # OWD_raw: 1000, 1000, 1050, 1000 -> OWD_rel: 0, 0, 50, 0
        assert result.max_bufferbloat_us == 50.0
        assert result.avg_bufferbloat_us == 12.5  # (0 + 0 + 50 + 0) / 4
        # 12.5 / 100.0 * 100 = 12.5%
        assert result.bufferbloat_percent == 12.5

    def test_timing_trends_increasing_bufferbloat(self):
        """
        Scenario: Chronic network under-performance (increasing buffer).
        Systematically increasing delay should generate distinct positive slope.
        """
        pc_ts = pd.Series([100, 200, 300, 400])
        # Each subsequent packet spends additional 20 µs in router.
        esp_ts = pd.Series([1000, 1120, 1240, 1360])
        expected_iat = 100.0

        result = calculate_timing_trends(pc_ts, esp_ts, expected_iat)

        # Drift is not zero here (because last packet arrived later),
        # which is physical norm with chronic buffer congestion at test end.
        assert result.clock_drift_ppm > 0.0

        # OWD_raw: 900, 920, 940, 960 -> OWD_rel: 0, 20, 40, 60
        assert result.max_bufferbloat_us == 60.0
        assert result.avg_bufferbloat_us == 30.0  # (0 + 20 + 40 + 60) / 4
        assert result.bufferbloat_percent == 30.0
        assert result.trend_slope > 0.1  # Proves constant, positive delay increase

    def test_timing_trends_insufficient_data(self):
        """Fail-Fast Scenario: Insufficient data for trend analysis."""
        expected_iat = 1000.0
        result_empty = calculate_timing_trends(
            pd.Series([], dtype=float), pd.Series([], dtype=float), expected_iat
        )
        assert result_empty.max_bufferbloat_us == 0.0
        assert result_empty.bufferbloat_percent == 0.0

        result_single = calculate_timing_trends(
            pd.Series([100]), pd.Series([200]), expected_iat
        )
        assert result_single.clock_drift_ppm == 0.0
        assert result_single.bufferbloat_percent == 0.0

    def test_timing_trends_mismatched_vectors(self):
        """
        Fail-Fast Scenario: Vectors must be aligned (properly joined in parser).
        """
        pc_ts = pd.Series([1, 2, 3])
        esp_ts = pd.Series([1, 2])
        expected_iat = 1000.0

        with pytest.raises(ValueError, match="identical length"):
            calculate_timing_trends(pc_ts, esp_ts, expected_iat)
