from abc import ABC, abstractmethod


class BaseDataPlane(ABC):
    """
    Abstract interface (Strategy Pattern) for the data plane.
    Enforces each protocol (Serial, UDP, TCP) to have a standardized interface
    for establishing connections and rigorous data transmission.
    """

    @abstractmethod
    def connect(self) -> None:
        """Establishes a dedicated connection for high-volume data transmission."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Closes the physical connection (releases socket/port)."""
        pass

    @abstractmethod
    def transmit(self, packet_count: int, frequency_hz: int) -> None:
        """
        Main transmission loop.
        Responsible for sending `packet_count` packets at the specified `frequency_hz`,
        guaranteeing timing precision and consistent inter-packet spacing.
        """
        pass
