import pytest
import pandas as pd

from analyzer.serial.downlink.pdr import calculate_pdr


class TestCalculatePDR:

    def test_pdr_perfect_conditions(self):
        """Scenario: Ideal wired network, 100% delivered, 0 lost, 0 duplicates."""
        total_sent = 5
        received_ids = pd.Series([1, 2, 3, 4, 5])

        result = calculate_pdr(received_ids, total_sent)

        assert result.ratio_percent == 100.0
        assert result.unique_received == 5
        assert result.lost_count == 0
        assert result.mac_duplicates_count == 0
        assert result.ghost_duplicates_count == 0

    def test_pdr_with_packet_loss(self):
        """Scenario: Weak Wi-Fi signal, packets are irreversibly lost in transit."""
        total_sent = 5
        # Missing IDs 2 and 4
        received_ids = pd.Series([1, 3, 5])

        result = calculate_pdr(received_ids, total_sent)

        assert result.ratio_percent == 60.0
        assert result.unique_received == 3
        assert result.lost_count == 2
        assert result.mac_duplicates_count == 0
        assert result.ghost_duplicates_count == 0

    def test_pdr_with_mac_layer_duplicates(self):
        """Scenario: ACK interference. Network delivered everything, but with immediate duplicates."""
        total_sent = 5
        # IDs 3 and 5 arrived twice, one after another
        received_ids = pd.Series([1, 2, 3, 3, 4, 5, 5])

        result = calculate_pdr(received_ids, total_sent)

        assert result.ratio_percent == 100.0
        assert result.unique_received == 5
        assert result.lost_count == 0
        assert result.mac_duplicates_count == 2
        assert result.ghost_duplicates_count == 0

    def test_pdr_mixed_chaos(self):
        """Scenario: Total hackathon chaos. Lost and immediate duplicates at the same time."""
        total_sent = 10
        # Lost: 4, 5, 6, 7 (4 packets)
        # Immediate Duplicated: 2, 9 (2 packets)
        received_ids = pd.Series([1, 2, 2, 3, 8, 9, 9, 10])

        result = calculate_pdr(received_ids, total_sent)

        assert result.ratio_percent == 60.0  # (6 unique / 10 sent) * 100
        assert result.unique_received == 6
        assert result.lost_count == 4
        assert result.mac_duplicates_count == 2
        assert result.ghost_duplicates_count == 0

    def test_pdr_with_ghost_duplicates(self):
        """Scenario: Bufferbloat/Routing issue. A packet arrives again after a long delay."""
        total_sent = 5
        # Packet '2' arrives again after '5'
        received_ids = pd.Series([1, 2, 3, 4, 5, 2])

        result = calculate_pdr(received_ids, total_sent)

        assert result.ratio_percent == 100.0
        assert result.unique_received == 5
        assert result.lost_count == 0
        assert result.mac_duplicates_count == 0
        assert result.ghost_duplicates_count == 1

    def test_pdr_complex_duplicate_scenario(self):
        """Scenario: Both MAC layer stutters and Ghost packets in the same stream."""
        total_sent = 5
        # Immediate duplicate of '2'. Delayed duplicate of '1'.
        received_ids = pd.Series([1, 2, 2, 3, 4, 1, 5])

        result = calculate_pdr(received_ids, total_sent)

        assert result.ratio_percent == 100.0
        assert result.unique_received == 5
        assert result.lost_count == 0
        assert result.mac_duplicates_count == 1
        assert result.ghost_duplicates_count == 1

    def test_pdr_empty_series_total_loss(self):
        """Scenario: ESP32 disconnected from the network, nothing was received."""
        total_sent = 100
        received_ids = pd.Series([], dtype=int)

        result = calculate_pdr(received_ids, total_sent)

        assert result.ratio_percent == 0.0
        assert result.unique_received == 0
        assert result.lost_count == 100
        assert result.mac_duplicates_count == 0
        assert result.ghost_duplicates_count == 0

    def test_pdr_raises_value_error_on_invalid_total(self):
        """Fail-fast scenario: Guard against invalid test configuration."""
        received_ids = pd.Series([1, 2, 3])

        with pytest.raises(ValueError, match="positive integer"):
            calculate_pdr(received_ids, 0)

        with pytest.raises(ValueError, match="positive integer"):
            calculate_pdr(received_ids, -5)
