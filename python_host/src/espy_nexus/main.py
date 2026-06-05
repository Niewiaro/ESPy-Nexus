import logging

from espy_nexus.core.settings import RunnerSettings
from espy_nexus.runner.matrix import (
    generate_test_matrix,
    generate_linear_rates,
    generate_exponential_rates,
)
from espy_nexus.runner.engine import TestEngine
from espy_nexus.core.logger import setup_global_logging
from espy_nexus.core.config import ControlPlane, Protocol, RateType, TestConfig

# Interfaces (for typing and dependency injection)
from espy_nexus.control_plane.base import BaseControlPlane
from espy_nexus.data_plane.base import BaseDataPlane

# Implementations Control Planes
from espy_nexus.control_plane.mock_cp import MockControlPlane
from espy_nexus.control_plane.serial_cp import SerialControlPlane

# Implementations Data Planes
from espy_nexus.data_plane.mock_dp import MockDataPlane
from espy_nexus.data_plane.serial_str_dp import SerialStrDataPlane
from espy_nexus.data_plane.serial_bin_dp import SerialBinDataPlane

# Global logging initialization
setup_global_logging()
logger = logging.getLogger(__name__)


# =========================================================================
# [1] CONFIGURATION (Profiles)
# =========================================================================


def get_active_profile() -> RunnerSettings:
    """Return the active configuration profile for the current run."""

    # --- PROFILE A: Fast developer tests (MOCK) ---
    # return RunnerSettings()

    # --- PROFILE B: Full hardware test (HARDWARE) ---
    return RunnerSettings(
        control_plane_type=ControlPlane.SERIAL,
        protocols=[Protocol.SERIAL_STR, Protocol.SERIAL_BIN],
        control_plane_port="COM3",
        data_plane_port="COM3",
        baudrate=921600,
        packet_count=1000,
        rate_type=RateType.EXPONENTIAL,
        freq_start=100,
        freq_stop=10000,
        freq_step=500,
        exp_base=100,
        exp_max=10000,
    )


# =========================================================================
# [2] FACTORIES (Dependency Injection Setup)
# =========================================================================


def build_control_plane(config: RunnerSettings) -> BaseControlPlane:
    """Factory pattern: build and return the configured control plane."""
    if config.control_plane_type == ControlPlane.MOCK:
        control_plane = MockControlPlane(
            port=config.control_plane_port, baudrate=config.baudrate
        )

        # Set to True to test error handling
        control_plane.simulate_errors = False
        # For realistic log generation
        control_plane.mock_records_to_generate = config.packet_count

        return control_plane
    elif config.control_plane_type == ControlPlane.SERIAL:
        return SerialControlPlane(
            port=config.control_plane_port, baudrate=config.baudrate
        )

    raise ValueError(f"Unsupported Control Plane type: {config.control_plane_type}")


def build_data_planes(config: RunnerSettings) -> dict[Protocol, BaseDataPlane]:
    """Factory pattern: build a map of configured data planes."""
    data_plane_map: dict[Protocol, BaseDataPlane] = {}

    for protocol in config.protocols:
        if protocol == Protocol.MOCK:
            data_plane_map[protocol] = MockDataPlane(
                port=config.data_plane_port, baudrate=config.baudrate
            )
        elif protocol == Protocol.SERIAL_STR:
            data_plane_map[protocol] = SerialStrDataPlane(
                port=config.data_plane_port, baudrate=config.baudrate
            )
        elif protocol == Protocol.SERIAL_BIN:
            data_plane_map[protocol] = SerialBinDataPlane(
                port=config.data_plane_port, baudrate=config.baudrate
            )
        else:
            logger.warning(f"No Data Plane implementation for: {protocol.value}")

    if not data_plane_map:
        raise RuntimeError("No Data Plane was initialized. Check config.protocols.")

    return data_plane_map


def build_matrix(config: RunnerSettings) -> list[TestConfig]:
    """Build the final test matrix based on configuration."""
    if config.rate_type == RateType.LINEAR:
        frequencies = generate_linear_rates(
            start=config.freq_start, stop=config.freq_stop, step=config.freq_step
        )
    elif config.rate_type == RateType.EXPONENTIAL:
        frequencies = generate_exponential_rates(
            base=config.exp_base, max_val=config.exp_max
        )
    else:
        raise ValueError(f"Unsupported rate type: {config.rate_type}")

    return generate_test_matrix(
        protocols=config.protocols,
        rates_hz=frequencies,
        # payloads_bytes=[config.payload_size_bytes],
        payloads_bytes=[16, 64],
        packet_count=config.packet_count,
    )


# =========================================================================
# [3] MAIN ORCHESTRATION FLOW
# =========================================================================


def main() -> None:
    # 1. Load configuration
    config = get_active_profile()
    logger.info(
        f"Initializing environment (Control Plane mode: {config.control_plane_type.value})"
    )

    # 2. Initialize hardware/mocks (Dependency Injection Container)
    control_plane = build_control_plane(config)
    data_planes = build_data_planes(config)

    # 3. Build test logic
    test_matrix = build_matrix(config)

    # 4. Run TestEngine state machine
    engine = TestEngine(control_plane=control_plane, data_planes=data_planes)
    engine.run_matrix(matrix=test_matrix, output_csv=config.output_csv)


if __name__ == "__main__":
    main()
