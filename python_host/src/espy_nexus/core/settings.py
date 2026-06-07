from dataclasses import dataclass, field
from espy_nexus.core.config import ControlPlane, Protocol, RateType, RouterTopology


@dataclass(frozen=True, slots=True)
class RunnerSettings:
    """
    Central configuration for the Test Engine lifecycle.
    Based on default values that can be overridden during initialization.
    """

    # --- Network Configuration ---
    router_topology: RouterTopology = RouterTopology.AP

    # --- Environment Configuration ---
    control_plane_type: ControlPlane = ControlPlane.MOCK
    control_plane_port: str = "MOCK_CP"
    data_plane_mock_port: str = "MOCK_DP"
    data_plane_serial_port: str = "COM3"
    data_plane_ip_address: str = "127.0.0.1"
    data_plane_udp_port: int = 8080
    baudrate: int = 921600

    # --- Test Parameters ---
    protocols: list[Protocol] = field(default_factory=lambda: [Protocol.MOCK])
    payload_size_bytes: int = 16
    packet_count: int = 100
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

    def __post_init__(self):
        if (
            self.control_plane_type == ControlPlane.MOCK
            and self.control_plane_port != "MOCK_CP"
        ):
            raise ValueError("Mock Control Plane must use port 'MOCK_CP'.")

        if self.rate_type == RateType.LINEAR:
            if self.freq_start <= 0 or self.freq_stop <= 0 or self.freq_step <= 0:
                raise ValueError(
                    "Linear rates must have positive start, stop, and step values."
                )
            if self.freq_start >= self.freq_stop:
                raise ValueError("Linear freq_start must be less than freq_stop.")
        elif self.rate_type == RateType.EXPONENTIAL:
            if self.exp_base < 1:
                raise ValueError("Exponential base must be at least 1.")
            if self.exp_max <= 1:
                raise ValueError("Exponential max must be greater than 1.")
            if self.exp_base >= self.exp_max:
                raise ValueError("Exponential base must be less than exp_max.")
        else:
            raise ValueError(f"Unsupported rate type: {self.rate_type}")

        if self.payload_size_bytes <= 0:
            raise ValueError("Payload size must be a positive integer.")

        if self.packet_count <= 0:
            raise ValueError("Packet count must be a positive integer.")
        if self.packet_count < 100:
            raise ValueError("Packet count must be at least 100 stable analyses.")
