import pytest
import pandas as pd

from espy_nexus.metrics.goodput import calculate_goodput


class TestCalculateGoodput:

    def test_goodput_ideal_conditions(self):
        """
        Scenario: 5 packets, 1000 bytes each.
        Test duration: exactly 1 second (from 0 to 1,000,000 us).
        Expected Goodput: 5000 B/s (because 5 packets were received).
        """
        payload_size = 1000
        received_ids = pd.Series([1, 2, 3, 4, 5])
        # Time window: max(1,000,000) - min(0) = 1 second
        esp_ts = pd.Series([0, 250_000, 500_000, 750_000, 1_000_000])

        res = calculate_goodput(received_ids, esp_ts, payload_size)

        assert res.bytes_per_sec == 5000.0
        assert res.kilobytes_per_sec == 5000.0 / 1024.0
        assert res.megabits_per_sec == (5000.0 * 8) / 1_000_000.0

    def test_goodput_ignores_duplicates(self):
        """
        Critical scenario: Hardware MAC duplicate.
        We receive packet ID 2 twice after 100ms.
        Function MUST reject it and not count its payload twice.
        """
        payload_size = 100
        # Packet 2 appears twice
        received_ids = pd.Series([1, 2, 2, 3])
        # Times: 0, 500k, 600k (duplicate time), 1M
        esp_ts = pd.Series([0, 500_000, 600_000, 1_000_000])

        res = calculate_goodput(received_ids, esp_ts, payload_size)

        # We have only 3 UNIQUE packets in 1 second window. 3 * 100B = 300 B/s.
        assert res.bytes_per_sec == 300.0
        assert res.kilobytes_per_sec == 300.0 / 1024.0
        assert res.megabits_per_sec == (300.0 * 8) / 1_000_000.0

    def test_goodput_out_of_order(self):
        """
        Scenario: Packets arrive out of order (UDP in loose network).
        Time window should be determined by absolute minimum and maximum time,
        regardless of what the IDs were.
        """
        payload_size = 50
        # ID 3 arrived before ID 2
        received_ids = pd.Series([1, 3, 2])
        # Times: 0, 200k, 500k. Window is max(500k) - min(0) = 0.5s.
        esp_ts = pd.Series([0, 200_000, 500_000])

        res = calculate_goodput(received_ids, esp_ts, payload_size)

        # 3 packets * 50B = 150B. In 0.5s time gives 300 B/s.
        assert res.bytes_per_sec == 300.0
        assert res.kilobytes_per_sec == 300.0 / 1024.0
        assert res.megabits_per_sec == (300.0 * 8) / 1_000_000.0

    def test_goodput_insufficient_data(self):
        """
        Scenario: Less than 2 packets.
        Cannot determine time window (division by zero).
        Should return safe zeros.
        """
        payload_size = 100
        res_empty = calculate_goodput(
            pd.Series([], dtype=int), pd.Series([], dtype=float), payload_size
        )
        res_single = calculate_goodput(pd.Series([1]), pd.Series([1000]), payload_size)

        for r in [res_empty, res_single]:
            assert r.bytes_per_sec == 0.0
            assert r.kilobytes_per_sec == 0.0
            assert r.megabits_per_sec == 0.0

    def test_goodput_invalid_payload(self):
        """
        Fail-Fast scenario: Raise exception on invalid test configuration.
        """
        ids = pd.Series([1, 2])
        ts = pd.Series([0, 1000])

        with pytest.raises(ValueError, match="positive integer"):
            calculate_goodput(ids, ts, 0)

        with pytest.raises(ValueError, match="positive integer"):
            calculate_goodput(ids, ts, -10)
