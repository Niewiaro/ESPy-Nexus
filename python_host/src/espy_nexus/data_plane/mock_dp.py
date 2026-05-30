import time
import logging
from espy_nexus.data_plane.base import BaseDataPlane


class MockDataPlane(BaseDataPlane):
    """
    Mock Data Plane for fast system testing without hardware.
    Does not use busy-wait to avoid consuming CPU during IDE execution.
    """

    def __init__(self, port: str = "MOCK", baudrate: int = 0):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.port = port
        self.baudrate = baudrate
        self.is_connected = False

    def connect(self) -> None:
        self.logger.debug(
            f"Opening virtual socket for Data Plane (Port: {self.port}, Baud Rate: {self.baudrate})"
        )
        self.is_connected = True

    def disconnect(self) -> None:
        self.logger.debug(f"Closing virtual Data Plane socket.")
        self.is_connected = False

    def transmit(self, packet_count: int, frequency_hz: int) -> None:
        if not self.is_connected:
            self.logger.error("Error: Data Plane is not connected before transmission!")
            return

        self.logger.debug(
            f"Starting simulated transmission: {packet_count} packets @ {frequency_hz} Hz"
        )

        # Interval between packets in seconds
        interval_s = 1.0 / frequency_hz

        # Transmission simulation
        for i in range(packet_count):
            # Here normally data would go to the cable
            time.sleep(interval_s)

            # Log every 1000 packets to avoid cluttering console/file
            if (i + 1) % 1000 == 0:
                self.logger.debug(f"  ...sent {i + 1} / {packet_count} virtual packets")

        self.logger.debug("Simulated transmission completed successfully.")
