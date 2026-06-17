import itertools
import logging

from espy_nexus.core.config import TestConfig, Protocol, RouterTopology

logger = logging.getLogger(__name__)


def generate_linear_rates(
    start: int,
    stop: int,
    step: int,
) -> list[int]:
    """
    Generates linear frequency increase (e.g., 10, 20, 30...).
    Useful for detailed performance profiling across a range.
    """
    rates = list(range(start, stop + step, step))
    if start == 0:
        rates[0] = 1  # Replace zero with one to avoid invalid frequency
    return rates


def generate_exponential_rates(base: int, max_val: int) -> list[int]:
    """
    Generates exponential increase (e.g., 10, 100, 1000...).
    Useful for finding performance limits.
    """
    rates = []
    current = base
    while current <= max_val:
        rates.append(int(current))
        current *= 10
    return rates


def generate_test_matrix(
    router_topology: RouterTopology,
    protocols: list[Protocol],
    rates_hz: list[int],
    payloads_bytes: list[int],
    packet_count: int = 1000,
    drain_time_s: float = 5.0,
    cooldown_s: float = 5.0,
) -> list[TestConfig]:
    """
    Creates a Cartesian product (each with each) from the provided parameters,
    building a ready list of immutable test configurations.
    """

    matrix = [
        TestConfig(
            router_topology=router_topology,
            protocol=protocol,
            frequency_hz=freq,
            packet_count=packet_count,
            payload_size_bytes=payload,
            drain_time_s=drain_time_s,
            cooldown_s=cooldown_s,
        )
        for protocol, freq, payload in itertools.product(
            protocols, rates_hz, payloads_bytes
        )
    ]

    logger.info(
        f"Generated test matrix containing {len(matrix)} unique test configurations."
    )

    return matrix
