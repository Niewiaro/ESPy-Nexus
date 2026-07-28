from dataclasses import dataclass, field
from espy_nexus.core.config import ControlPlane, Protocol, RateType, RouterTopology


@dataclass(frozen=True, slots=True)
class RunnerSettings:
    """
    Central configuration for the Test Engine lifecycle.
    Based on default values that can be overridden during initialization.
    """

    # --- Network Configuration ---
    router_topology: RouterTopology = RouterTopology.AP_ESP

    # --- Environment Configuration ---
    control_plane_type: ControlPlane = ControlPlane.MOCK
    control_plane_port: str = "MOCK_CP"
    data_plane_mock_port: str = "MOCK_DP"
    data_plane_serial_port: str = "COM3"
    data_plane_ip_address: str = "127.0.0.1"
    data_plane_udp_port: int = 8080
    data_plane_tcp_port: int = 8080
    data_plane_ws_port: int = 8080
    baudrate: int = 921600

    # --- Test Parameters ---
    protocols: list[Protocol] = field(default_factory=lambda: [Protocol.MOCK])
    payloads_bytes: list[int] = field(default_factory=lambda: [16])
    packet_count: int = 100

    # --- Output Configuration ---
    raw_db_path: str = "hil_raw_data.sqlite"
    analytics_db_path: str | None = "hil_analytics.sqlite"
    output_csv_path: str | None = "hil_analytics.csv"

    # --- Frequency Parameters (Sweep) ---
    rate_type: RateType = RateType.EXPONENTIAL

    # linear
    freq_start: int = 10
    freq_stop: int = 10000
    freq_step: int = 10

    # exponential
    exp_base: int = 10
    exp_max: int = 10000

    # timing parameters
    drain_time_s: float = 5.0
    cooldown_s: float = 5.0

    def __post_init__(self):
        if (
            self.control_plane_type == ControlPlane.MOCK
            and self.control_plane_port != "MOCK_CP"
        ):
            raise ValueError("Mock Control Plane must use port 'MOCK_CP'.")

        if self.rate_type == RateType.LINEAR:
            # start can be zero for linear rates, but stop and step must be positive.
            # if start is zero, we will replace it with 1
            # this feature allows to generate list like [1, 10, 20, 30, ...] instead of [0, 10, 20, 30, ...]
            if self.freq_start < 0 or self.freq_stop <= 0 or self.freq_step <= 0:
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
        elif self.rate_type == RateType.LOG:
            if self.exp_max <= 1:
                raise ValueError("Logarithmic max must be greater than 1.")
        elif self.rate_type == RateType.SMART:
            if self.exp_base < 1:
                raise ValueError("Exponential base must be at least 1.")
            if self.freq_start < 0 or self.freq_step <= 0:
                raise ValueError(
                    "Linear start must be non-negative and linear step must be positive."
                )
        else:
            raise ValueError(f"Unsupported rate type: {self.rate_type}")

        if not self.payloads_bytes:
            raise ValueError("At least one payload size must be specified.")

        if self.packet_count <= 0:
            raise ValueError("Packet count must be a positive integer.")
        if self.packet_count < 100:
            raise ValueError("Packet count must be at least 100 stable analyses.")
