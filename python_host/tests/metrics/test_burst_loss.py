import pytest
import pandas as pd

from espy_nexus.metrics.burst_loss import calculate_burst_loss


class TestCalculateBurstLoss:

    def test_burst_perfect_network(self):
        """Scenario: All 5 packets (ID: 0, 1, 2, 3, 4) arrived without issues."""
        total_sent = 5
        expected_iat_us = 10_000.0  # 10 ms
        received_ids = pd.Series([0, 1, 2, 3, 4])

        result = calculate_burst_loss(received_ids, total_sent, expected_iat_us)

        assert result.total_burst_events == 0
        assert result.max_burst_length == 0
        assert result.max_blackout_time_ms == 0.0
        assert result.burst_events == {}

    def test_burst_single_random_losses(self):
        """Scenario: Background noise. Single packets lost (ID: 2 and 7)."""
        total_sent = 10
        expected_iat_us = 10_000.0  # 10 ms
        # Sent 0-9, missing 2 and 7
        received_ids = pd.Series([0, 1, 3, 4, 5, 6, 8, 9])

        result = calculate_burst_loss(received_ids, total_sent, expected_iat_us)

        assert result.total_burst_events == 2
        assert result.max_burst_length == 1
        # Max blackout = 1 missing packet * 10 ms = 10.0 ms
        assert result.max_blackout_time_ms == 10.0
        # Expected two bursts of length 1, starting from ID 2 and 7
        assert result.burst_events == {1: [2, 7]}

    def test_burst_multiple_lengths(self):
        """
        Scenario: Mixed failure.
        - Noise loses packet ID 1 (length 1).
        - Buffer overflow loses packets ID 4, 5, 6 (length 3).
        """
        total_sent = 10
        expected_iat_us = 5_000.0  # 5 ms (e.g., 200 Hz)
        # Sent 0-9, missing 1, 4, 5, 6
        received_ids = pd.Series([0, 2, 3, 7, 8, 9])

        result = calculate_burst_loss(received_ids, total_sent, expected_iat_us)

        assert result.total_burst_events == 2
        assert result.max_burst_length == 3
        # Max blackout = 3 missing packets * 5 ms = 15.0 ms
        assert result.max_blackout_time_ms == 15.0
        assert result.burst_events == {
            1: [1],  # One burst of length 1 starting from ID 1
            3: [4],  # One burst of length 3 starting from ID 4
        }

    def test_burst_at_edges(self):
        """
        Edge case scenario: Packet loss at the beginning and end.
        Tests if loops correctly close and register bursts at interval boundaries.
        """
        total_sent = 10
        expected_iat_us = 2_000.0  # 2 ms (e.g., 500 Hz)
        # Missing 0, 1 (start) and 8, 9 (end)
        received_ids = pd.Series([2, 3, 4, 5, 6, 7])

        result = calculate_burst_loss(received_ids, total_sent, expected_iat_us)

        assert result.total_burst_events == 2
        assert result.max_burst_length == 2
        # Max blackout = 2 missing packets * 2 ms = 4.0 ms
        assert result.max_blackout_time_ms == 4.0
        assert result.burst_events == {
            2: [0, 8]  # Two bursts of length 2. First from ID 0, second from ID 8.
        }

    def test_burst_complete_blackout(self):
        """Scenario: ESP32 received no bytes at all."""
        total_sent = 100
        expected_iat_us = 1_000.0  # 1 ms (1000 Hz)
        received_ids = pd.Series([], dtype=int)

        result = calculate_burst_loss(received_ids, total_sent, expected_iat_us)

        assert result.total_burst_events == 1
        assert result.max_burst_length == 100
        # Max blackout = 100 packets * 1 ms = 100.0 ms
        assert result.max_blackout_time_ms == 100.0
        # Expected one large burst starting from ID 0
        assert result.burst_events == {100: [0]}

    def test_burst_ignores_mac_duplicates(self):
        """
        Scenario: Duplicates from MAC layer should not break calculations.
        Lost ID 2, duplicated ID 3 and 4.
        """
        total_sent = 5
        expected_iat_us = 1_000.0
        # Expected: 0, 1, 2, 3, 4.
        # Actual: 0, 1, 3, 3, 4, 4 (Missing 2)
        received_ids = pd.Series([0, 1, 3, 3, 4, 4])

        result = calculate_burst_loss(received_ids, total_sent, expected_iat_us)

        assert result.total_burst_events == 1
        assert result.max_burst_length == 1
        assert result.max_blackout_time_ms == 1.0
        assert result.burst_events == {1: [2]}
