import pytest
import pandas as pd

from analyzer.serial.downlink.out_of_order import calculate_out_of_order


class TestCalculateOutOfOrder:

    def test_out_of_order_perfect_order(self):
        """Scenario: Packets arrive in perfect order, no packet loss or duplicates."""
        ids = pd.Series([1, 2, 3, 4, 5])
        result = calculate_out_of_order(ids)

        assert result.total_ooo_count == 0
        assert result.ooo_ids == []
        assert result.max_id_displacement == 0

    def test_out_of_order_with_pure_packet_loss(self):
        """Scenario: Simple packet loss without violating chronological order."""
        # Packets 2 and 4 are missing, but received packets maintain order
        ids = pd.Series([1, 3, 5, 6])
        result = calculate_out_of_order(ids)

        assert result.total_ooo_count == 0
        assert result.ooo_ids == []
        assert result.max_id_displacement == 0

    def test_out_of_order_simple_inversion(self):
        """Scenario: Typical Wi-Fi jitter. Two adjacent packets swapped."""
        # Packet 3 arrives before packet 2
        ids = pd.Series([1, 3, 2, 4])
        result = calculate_out_of_order(ids)

        assert result.total_ooo_count == 1
        assert result.ooo_ids == [2]
        # Max ID seen before receiving '2' was '3'. Difference: 3 - 2 = 1.
        assert result.max_id_displacement == 1

    def test_out_of_order_delayed_duplicate(self):
        """
        Critical Scenario: Delayed duplicate (Ghost Packet).
        Packet 2 arrives at the beginning, then again much later, causing state regression.
        """
        ids = pd.Series([1, 2, 3, 4, 5, 2, 6])
        result = calculate_out_of_order(ids)

        assert result.total_ooo_count == 1
        assert result.ooo_ids == [2]
        # When system receives the second '2', highest seen ID is '5'. Difference: 5 - 2 = 3.
        assert result.max_id_displacement == 3

    def test_out_of_order_immediate_duplicate_ignored(self):
        """
        Scenario: Immediate duplicates (MAC Layer Stutter) must be ignored.
        They do not cause application state regression.
        """
        ids = pd.Series([1, 2, 2, 3, 4, 4, 5])
        result = calculate_out_of_order(ids)

        assert result.total_ooo_count == 0
        assert result.ooo_ids == []
        assert result.max_id_displacement == 0

    def test_out_of_order_major_buffer_reordering(self):
        """Scenario: Deep buffering in routing layer. Packet severely delayed."""
        # Packet '2' stuck for a long time, system progressed to '11'.
        ids = pd.Series([1, 10, 11, 2, 12])
        result = calculate_out_of_order(ids)

        assert result.total_ooo_count == 1
        assert result.ooo_ids == [2]
        # Max ID seen before '2' is '11'. Difference: 11 - 2 = 9.
        assert result.max_id_displacement == 9

    def test_out_of_order_multiple_issues(self):
        """Scenario: Multiple chronological violations with varying severity."""
        ids = pd.Series([1, 10, 5, 11, 3, 12])
        result = calculate_out_of_order(ids)

        assert result.total_ooo_count == 2
        assert result.ooo_ids == [5, 3]
        # For '5' displacement is 10 - 5 = 5.
        # For '3' displacement is 11 - 3 = 8.
        # We expect the maximum of these two, which is 8.
        assert result.max_id_displacement == 8

    def test_out_of_order_empty_and_single(self):
        """Edge case scenario: Safeguard against insufficient data."""
        res_empty = calculate_out_of_order(pd.Series([], dtype=int))
        assert res_empty.total_ooo_count == 0

        res_single = calculate_out_of_order(pd.Series([1]))
        assert res_single.total_ooo_count == 0
