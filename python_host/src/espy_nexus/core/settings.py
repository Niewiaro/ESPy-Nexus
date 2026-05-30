from dataclasses import dataclass, field
from espy_nexus.core.config import ControlPlane, Protocol, RateType


@dataclass(frozen=True, slots=True)
class RunnerSettings:
    """
    Central configuration for the Test Engine lifecycle.
    Based on default values that can be overridden during initialization.
    """

    # --- Environment Configuration ---
    control_plane_type: ControlPlane = ControlPlane.MOCK
    control_plane_port: str = "MOCK_CP"
    data_plane_port: str = "MOCK_DP"
    baudrate: int = 921600

    # --- Test Parameters ---
    protocols: list[Protocol] = field(default_factory=lambda: [Protocol.MOCK])
    payload_size_bytes: int = 16
    packet_count: int = 10000
    output_csv: str = "test_matrix_results.csv"

    # --- Frequency Parameters (Sweep) ---
    rate_type: RateType = RateType.EXPONENTIAL

    # linear
    freq_start: int = 10
    freq_stop: int = 10000
    freq_step: int = 10

    # exponential
    exp_base: int = 10
    exp_max: int = 10000
