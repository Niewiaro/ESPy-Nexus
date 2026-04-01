from enum import Enum
from dataclasses import dataclass


class Protocol(str, Enum):
    """Supported transport layers."""

    SERIAL = "SERIAL"
    # UDP = "UDP"
    # TCP = "TCP"


@dataclass(frozen=True, slots=True)
class TestConfig:
    """Immutable definition of a single test scenario."""

    test_id: str
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
