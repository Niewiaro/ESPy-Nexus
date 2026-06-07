import socket
import struct
import time
import logging
from espy_nexus.data_plane.base import BaseDataPlane


class TcpDataPlane(BaseDataPlane):
    def __init__(self, ip_address: str = "192.168.4.1", port: int = 8080):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.ip_address = ip_address
        self.port = port
        self.sock: socket.socket | None = None
        self.tx_timestamps = []

    def connect(self) -> None:
        self.logger.debug(
            f"Establishing TCP connection (3-way handshake) with {self.ip_address}:{self.port}"
        )
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Disable Nagle's algorithm to minimize latency for small packets
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            self.sock.connect((self.ip_address, self.port))
            self.logger.debug("TCP session established successfully.")
        except Exception as e:
            self.logger.error(f"Failed to connect via TCP: {e}")
            raise

    def disconnect(self) -> None:
        if self.sock:
            self.logger.debug("Closing TCP session (FIN/ACK).")
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except Exception as e:
                self.logger.warning(f"Error while closing TCP socket: {e}")
            finally:
                self.sock = None

    def _cobs_encode(self, data: bytes) -> bytes:
        """COBS encoding for the TCP stream."""
        encoded = bytearray()
        zero_index = 0
        for i, b in enumerate(data):
            if b == 0:
                encoded.append(i - zero_index + 1)
                encoded.extend(data[zero_index:i])
                zero_index = i + 1
        encoded.append(len(data) - zero_index + 1)
        encoded.extend(data[zero_index:])
        return bytes(encoded)

    def prepare_payloads(
        self, packet_count: int, payload_size_bytes: int
    ) -> list[tuple[int, bytes]]:
        precompiled = []
        padding_bytes = max(0, payload_size_bytes - 4)
        struct_format = f"<I{padding_bytes}x"

        for i in range(packet_count):
            raw_binary = struct.pack(struct_format, i)
            cobs_data = self._cobs_encode(raw_binary)
            full_frame = cobs_data + b"\x00"
            precompiled.append((i, full_frame))

        return precompiled

    def transmit(
        self, precompiled_packets: list[tuple[int, bytes]], frequency_hz: int
    ) -> list[dict[str, int]]:
        if not self.sock:
            raise ConnectionError(
                "Attempted transmission without an open TCP socket! Call connect() first."
            )

        packet_count = len(precompiled_packets)
        self.tx_timestamps = [
            {"packet_id": 0, "pc_tx_ts": 0} for _ in range(packet_count)
        ]
        interval_ns = int(1_000_000_000 / frequency_hz)

        self.logger.debug(
            f"Starting TCP transmitter: {packet_count} packets @ {frequency_hz} Hz"
        )
        next_transmission_time = time.perf_counter_ns()

        for i in range(packet_count):
            packet_id, raw_bytes = precompiled_packets[i]

            while time.perf_counter_ns() < next_transmission_time:
                pass

            self.tx_timestamps[i] = {
                "packet_id": packet_id,
                "pc_tx_ts": time.time_ns() // 1000,
            }

            self.sock.sendall(raw_bytes)
            next_transmission_time += interval_ns

        self.logger.debug("TCP stream transmission completed.")
        return self.tx_timestamps
