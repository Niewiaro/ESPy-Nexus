from enum import Enum
from dataclasses import dataclass


class RouterTopology(str, Enum):
    """Possible network topologies for ESP32 connectivity."""

    NONE = "NONE"
    AP = "AP"
    STA = "STA"
    STA_MOBILE = "STA_MOBILE"


class ControlPlane(str, Enum):
    """Supported control plane implementations."""

    SERIAL = "SERIAL"
    MOCK = "MOCK"


class Protocol(str, Enum):
    """Supported transport layers."""

    MOCK = "MOCK"
    SERIAL_STR = "SERIAL_STR"
    SERIAL_BIN = "SERIAL_BIN"
    UDP = "UDP"
    TCP = "TCP"
    WS = "WS"


class RateType(str, Enum):
    """Types of frequency sweeps."""

    LINEAR = "LINEAR"
    EXPONENTIAL = "EXPONENTIAL"


@dataclass(frozen=True, slots=True)
class TestConfig:
    """Immutable definition of a single test scenario."""

    router_topology: RouterTopology
    protocol: Protocol
    frequency_hz: int
    packet_count: int
    payload_size_bytes: int

    def __post_init__(self):
        if self.frequency_hz <= 0:
            raise ValueError(f"Frequency must be positive. Got: {self.frequency_hz}")
        if self.packet_count <= 0:
            raise ValueError(f"Packet count must be positive. Got: {self.packet_count}")
        if self.payload_size_bytes <= 0:
            raise ValueError(
                f"Payload size must be positive. Got: {self.payload_size_bytes}"
            )
