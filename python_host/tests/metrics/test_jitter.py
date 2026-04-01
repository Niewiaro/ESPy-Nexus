import pytest
import pandas as pd

from espy_nexus.metrics.jitter import calculate_jitter


class TestCalculateJitter:

    def test_jitter_perfect_intervals(self):
        """
        Scenario: Perfect timing (e.g., Serial or ESP-NOW in lab).
        All intervals are identical (10ms).
        """
        # Inter-arrival times (IAT): 10000, 10000, 10000, 10000
        esp_timestamps = pd.Series([10000, 20000, 30000, 40000, 50000])
        expected_iat = 10000.0

        result = calculate_jitter(esp_timestamps, expected_iat)

        assert result.expected_iat_us == 10000.0
        assert result.mean_us == 10000.0
        assert result.mean_error_us == 0.0  # Średnia idealnie pokrywa się z oczekiwaną
        assert result.std_us == 0.0
        assert result.cv_percent == 0.0  # Brak zmienności
        assert result.max_us == 10000.0
        assert result.min_us == 10000.0
        assert result.max_deviation_us == 0.0
        assert result.min_deviation_us == 0.0

    def test_jitter_variable_network(self):
        """
        Scenario: Typical Wi-Fi. Intervals vary.
        """
        # Inter-arrival times (IAT): 11000, 9000, 10500, 9500 (Mean: 10000)
        esp_timestamps = pd.Series([0, 11000, 20000, 30500, 40000])
        expected_iat = 10000.0

        result = calculate_jitter(esp_timestamps, expected_iat)

        assert result.expected_iat_us == 10000.0
        assert result.mean_us == 10000.0
        assert result.mean_error_us == 0.0  # Mimo skoków, średnia jest idealna
        assert result.max_us == 11000.0
        assert result.min_us == 9000.0
        assert result.max_deviation_us == 1000.0
        assert result.min_deviation_us == -1000.0
        # std for [11000, 9000, 10500, 9500]
        assert result.std_us == pytest.approx(912.87, rel=1e-2)
        # cv_percent = (std / mean) * 100
        assert result.cv_percent == pytest.approx(9.13, rel=1e-2)

    def test_jitter_burst_and_freeze(self):
        """
        Scenario: Network hiccup (Freeze).
        Long pause followed by two packets burst.
        """
        # Inter-arrival times (IAT): 10000, 50000 (Freeze!), 0 (Burst!)
        esp_timestamps = pd.Series([0, 10000, 60000, 60000])
        expected_iat = 10000.0

        result = calculate_jitter(esp_timestamps, expected_iat)

        assert result.expected_iat_us == 10000.0
        assert result.mean_us == 20000.0
        assert (
            result.mean_error_us == 10000.0
        )  # Paczki są średnio spóźnione o całe 10ms!
        assert result.max_us == 50000.0
        assert result.min_us == 0.0
        assert result.max_deviation_us == 30000.0
        assert result.min_deviation_us == -20000.0
        assert result.cv_percent > 100.0  # Zmienność uderza w sufit, absolutny chaos

    def test_jitter_insufficient_data(self):
        """
        Scenario: Missing data or only one packet.
        Should safely return expected_iat and all zeros for metrics.
        """
        expected_iat = 10000.0
        res_empty = calculate_jitter(pd.Series([], dtype=float), expected_iat)
        res_single = calculate_jitter(pd.Series([123456]), expected_iat)

        for r in [res_empty, res_single]:
            assert r.expected_iat_us == 10000.0
            assert r.mean_us == 0.0
            assert r.mean_error_us == 0.0
            assert r.std_us == 0.0
            assert r.cv_percent == 0.0
            assert r.max_us == 0.0
            assert r.min_us == 0.0

    def test_jitter_two_packets(self):
        """
        Scenario: Only two packets (one interval).
        Std and CV should be 0, as there is no variability between intervals.
        """
        # One interval: 15000
        esp_timestamps = pd.Series([10000, 25000])
        expected_iat = 10000.0

        result = calculate_jitter(esp_timestamps, expected_iat)

        assert result.expected_iat_us == 10000.0
        assert result.mean_us == 15000.0
        assert result.mean_error_us == 5000.0  # Stałe spóźnienie
        assert result.std_us == 0.0
        assert (
            result.cv_percent == 0.0
        )  # Brak zmienności, odstępy są równe (bo jest tylko jeden)
        assert result.max_us == 15000.0
        assert result.min_us == 15000.0
        assert result.max_deviation_us == 0.0
        assert result.min_deviation_us == 0.0
