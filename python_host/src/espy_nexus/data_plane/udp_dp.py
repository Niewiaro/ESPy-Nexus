import socket
import struct
import time
import logging
from espy_nexus.data_plane.base import BaseDataPlane


class UdpDataPlane(BaseDataPlane):
    def __init__(self, ip_address: str = "127.0.0.1", port: int = 8080):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.ip_address = ip_address
        self.port = port

        self.sock: socket.socket | None = None
        self.tx_timestamps = []

    def connect(self) -> None:
        self.logger.debug(
            f"Configuring UDP socket for address {self.ip_address}:{self.port}"
        )
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
        except Exception as e:
            self.logger.error(f"Failed to open UDP socket: {e}")
            raise

    def disconnect(self) -> None:
        if self.sock:
            self.logger.debug("Releasing UDP resources and closing socket.")
            try:
                self.sock.close()
            except Exception as e:
                self.logger.warning(f"Error while closing UDP socket: {e}")
            finally:
                self.sock = None

    def prepare_payloads(
        self, packet_count: int, payload_size_bytes: int
    ) -> list[tuple[int, bytes]]:
        precompiled = []
        padding_bytes = max(0, payload_size_bytes - 4)
        struct_format = f"<I{padding_bytes}x"

        for i in range(packet_count):
            raw_binary = struct.pack(struct_format, i)
            precompiled.append((i, raw_binary))

        return precompiled

    def transmit(
        self, precompiled_packets: list[tuple[int, bytes]], frequency_hz: int
    ) -> list[dict[str, int]]:
        if not self.sock:
            raise ConnectionError(
                "Attempted transmission without an open UDP socket! Call connect() first."
            )

        packet_count = len(precompiled_packets)
        self.tx_timestamps = [
            {"packet_id": 0, "pc_tx_ts": 0} for _ in range(packet_count)
        ]

        interval_ns = int(1_000_000_000 / frequency_hz)

        self.logger.debug(
            f"Starting UDP transmitter: {packet_count} packets @ {frequency_hz} Hz"
        )

        next_transmission_time = time.perf_counter_ns()

        for i in range(packet_count):
            packet_id, raw_bytes = precompiled_packets[i]

            # Busy-Wait
            while time.perf_counter_ns() < next_transmission_time:
                pass

            self.tx_timestamps[i] = {
                "packet_id": packet_id,
                "pc_tx_ts": time.time_ns() // 1000,
            }

            self.sock.sendto(raw_bytes, (self.ip_address, self.port))
            next_transmission_time += interval_ns

        self.logger.debug("UDP transmission completed.")
        return self.tx_timestamps
