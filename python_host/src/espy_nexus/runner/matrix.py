import itertools
import logging

from espy_nexus.core.config import TestConfig, Protocol, RouterTopology

logger = logging.getLogger(__name__)


def generate_linear_rates(
    start: int,
    max_val: int,
    step: int,
) -> list[int]:
    """
    Generates linear frequency increase (e.g., 10, 20, 30...).
    Useful for detailed performance profiling across a range.
    """
    if step <= 0 or max_val < start:
        return []

    rates = list(range(start, max_val + 1, step))

    if start == 0:
        rates[0] = 1  # Replace zero with one to avoid invalid frequency
    return rates


def generate_exponential_rates(base: int, max_val: int) -> list[int]:
    """
    Generates exponential increase (e.g., 10, 100, 1000...).
    Useful for finding performance limits.
    """
    if base <= 1 or max_val < 1:
        return []

    rates: list[int] = []
    val = 1

    while val <= max_val:
        rates.append(val)
        val *= base

    return rates


def generate_log_rates(max_val: int) -> list[int]:
    """
    Generates a log-scale-like sequence:
    1, 2, 3, ..., 9, 10, 20, 30, ..., 90, 100, 200, ...
    Useful for broad performance profiling with denser low-end coverage.
    """
    if max_val < 1:
        return []

    rates: list[int] = []
    magnitude = 1

    while magnitude <= max_val:
        for multiplier in range(1, 10):
            value = multiplier * magnitude
            if value > max_val:
                break
            rates.append(value)
        magnitude *= 10

    return rates


def generate_smart_rates(
    exp_base: int,
    linear_start: int,
    linear_step: int,
    max_val: int,
) -> list[int]:
    rates = set()
    rates.update(generate_log_rates(max_val))
    rates.update(generate_exponential_rates(exp_base, max_val))
    rates.update(generate_linear_rates(linear_start, max_val, linear_step))

    # return sorted([r for r in rates if r >= 100])
    return sorted(list(rates))


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


if __name__ == "__main__":
    final_rates = generate_smart_rates(
        exp_base=2,  # exp 2 (1, 2, 4, 8, 16...)
        linear_start=100,  # start 100
        linear_step=100,  # step 100 (100, 200, 300...)
        max_val=10000,  # limit 10k
    )

    print(f"Number of test configurations: {len(final_rates)}")
    print(final_rates)
