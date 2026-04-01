import itertools
from espy_nexus.core.config import TestConfig, Protocol


def generate_linear_rates(start: int, stop: int, step: int) -> list[int]:
    """Generates linear frequency increase (e.g., 100, 200, 300...)."""
    rates = []
    current = start
    while current <= stop:
        rates.append(round(current, 2))
        current += step
    return rates


def generate_exponential_rates(base: int, max_val: int) -> list[int]:
    """
    Generates exponential increase (e.g., 10, 100, 1000...),
    useful for finding performance limits.
    """
    rates = []
    current = base
    while current <= max_val:
        rates.append(int(current))
        current *= 10
    return rates


def generate_test_matrix(
    protocols: list[Protocol],
    rates_hz: list[int],
    payloads_bytes: list[int],
    packet_count: int = 1000,
) -> list[TestConfig]:
    """
    Creates a Cartesian product (each with each) from the given parameters,
    building a ready-made list of immutable test configurations.
    """
    matrix = []

    for protocol, frequency_hz, payload in itertools.product(
        protocols, rates_hz, payloads_bytes
    ):
        test_id = f"{protocol.value}_{int(frequency_hz)}Hz_{payload}B"

        config = TestConfig(
            test_id=test_id,
            protocol=protocol,
            frequency_hz=frequency_hz,
            packet_count=packet_count,
            payload_size_bytes=payload,
        )
        matrix.append(config)

    return matrix
