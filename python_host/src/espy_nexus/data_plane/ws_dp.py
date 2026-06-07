import struct
import time
import logging
from espy_nexus.data_plane.base import BaseDataPlane

# Use websocket-client library for synchronous WebSocket communication.
# Asynchronous libraries like websockets or aiohttp are not suitable for precise timing in this context.
from websocket import create_connection, ABNF


class WsDataPlane(BaseDataPlane):
    def __init__(self, ip_address: str = "192.168.4.1", port: int = 8080):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.ip_address = ip_address
        self.port = port
        self.ws = None
        self.tx_timestamps = []

    def connect(self) -> None:
        ws_url = f"ws://{self.ip_address}:{self.port}/"
        self.logger.debug(
            f"Establishing HTTP connection and upgrading to WebSocket: {ws_url}"
        )
        try:
            self.ws = create_connection(ws_url, timeout=5.0)
            self.logger.debug("WebSocket tunnel established successfully.")
        except Exception as e:
            self.logger.error(f"Failed to connect via WebSocket: {e}")
            raise

    def disconnect(self) -> None:
        if self.ws:
            self.logger.debug("Closing WebSocket tunnel (sending CLOSE frame).")
            try:
                self.ws.close()
            except Exception as e:
                self.logger.warning(f"Error while closing WebSocket: {e}")
            finally:
                self.ws = None

    def prepare_payloads(
        self, packet_count: int, payload_size_bytes: int
    ) -> list[tuple[int, bytes]]:
        """Compiles native binary packets. WebSocket handles framing automatically (no COBS)."""
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
        if not self.ws:
            raise ConnectionError(
                "Attempted transmission without an open WS socket. Call connect()."
            )

        packet_count = len(precompiled_packets)
        self.tx_timestamps = [
            {"packet_id": 0, "pc_tx_ts": 0} for _ in range(packet_count)
        ]
        interval_ns = int(1_000_000_000 / frequency_hz)

        self.logger.debug(
            f"Starting WebSocket transmitter: {packet_count} packets @ {frequency_hz} Hz"
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

            # Send as binary frame (opcode=2) - WebSocket client will handle framing and escaping
            self.ws.send(raw_bytes, opcode=ABNF.OPCODE_BINARY)
            next_transmission_time += interval_ns

        self.logger.debug("WebSocket frame transmission completed.")
        return self.tx_timestamps
