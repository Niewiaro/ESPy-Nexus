from abc import ABC, abstractmethod


class BaseDataPlane(ABC):
    """
    Abstract interface (Strategy) for the Data Plane.
    Enforces each protocol (Serial, UDP, TCP) to have standardized methods.
    """

    @abstractmethod
    def transmit(self, packet_count: int, frequency_hz: int) -> None:
        """
        Physically sends the test payload (Data Payload) over network or cable.
        Must guarantee the specified frequency and number of packets.
        """
        pass
