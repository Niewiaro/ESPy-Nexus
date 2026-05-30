from abc import ABC, abstractmethod


class BaseControlPlane(ABC):
    """
    Abstract interface (Strategy Pattern) for the control plane.
    Ensures consistency between hardware implementation and test mocks.
    """

    @abstractmethod
    def connect(self) -> None:
        """Establishes connection with the endpoint."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Safely closes the connection and releases resources."""
        pass

    @abstractmethod
    def send_command(self, cmd: str, expected_ack: str, max_attempts: int = 3) -> bool:
        """
        Sends a command and waits for specific acknowledgment.

        Returns:
            bool: True if ACK received, False on error or timeout.
        """
        pass

    @abstractmethod
    def fetch_data(self, timeout_data: float = 5.0) -> list[dict[str, int]]:
        """
        Fetches buffered logs from the device.

        Returns:
            List of dictionaries where each dictionary represents a single log entry (e.g., packet with timestamps).
        """
        pass
