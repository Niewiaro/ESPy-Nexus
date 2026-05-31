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
        self.tx_timestamps: list[int] = []

    def connect(self) -> None:
        self.logger.debug(
            f"Opening virtual socket for Data Plane (Port: {self.port}, Baud Rate: {self.baudrate})"
        )
        self.is_connected = True

    def disconnect(self) -> None:
        self.logger.debug(f"Closing virtual Data Plane socket.")
        self.is_connected = False

    def prepare_payloads(
        self, packet_count: int, payload_size_bytes: int
    ) -> list[tuple[int, bytes]]:
        self.logger.debug("Preparing ASCII payloads...")
        precompiled = []
        for i in range(packet_count):
            header = f"D,{i}\n".encode("ascii")
            padding_size = max(0, payload_size_bytes - len(header))
            padding = b"X" * padding_size
            precompiled.append((i, header + padding))
        return precompiled

    def transmit(
        self, precompiled_packets: list[tuple[int, bytes]], frequency_hz: int
    ) -> list[dict[str, int]]:
        if not self.is_connected:
            self.logger.error("Error: Data Plane is not connected before transmission!")
            return []

        packet_count = len(precompiled_packets)
        self.tx_timestamps = []

        self.logger.debug(
            f"Starting simulated transmission: {packet_count} packets @ {frequency_hz} Hz"
        )

        for i in range(packet_count):
            packet_id, raw_bytes = precompiled_packets[i]

            # Simulate packet handling and timestamp capture without hardware IO.
            _ = packet_id, raw_bytes
            self.tx_timestamps.append(time.time_ns() // 1000)

            # Log every 1000 packets to avoid cluttering console/file
            if (i + 1) % 1000 == 0:
                self.logger.debug(f"  ...sent {i + 1} / {packet_count} virtual packets")

        self.logger.debug("Simulated transmission completed successfully.")

        return [
            {"packet_id": precompiled_packets[i][0], "pc_tx_ts": self.tx_timestamps[i]}
            for i in range(packet_count)
        ]
