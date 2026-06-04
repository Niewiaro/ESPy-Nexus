import time
import logging
from espy_nexus.data_plane.base import BaseDataPlane
from espy_nexus.control_plane.connection_manager import SerialConnectionManager


class SerialDataPlane(BaseDataPlane):
    """
    Data plane for the serial port.
    Generates and sends test packets with high precision, enforcing timing
    constraints at the microsecond level using a busy-wait loop.
    """

    def __init__(self, port: str, baudrate: int):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.manager = SerialConnectionManager(port, baudrate)

        self.tx_timestamps: list[int] = []

    def connect(self) -> None:
        """Acquires system resources for the serial port."""
        self.logger.debug(
            "Configuring system buffers for high-speed serial transmission."
        )
        self.manager.connect()

    def disconnect(self) -> None:
        """Releases the port so another script or tool can use it."""
        self.logger.debug("Releasing Serial Data Plane resources.")
        self.manager.disconnect()

    def prepare_payloads(
        self, packet_count: int, payload_size_bytes: int
    ) -> list[tuple[int, bytes]]:
        self.logger.debug("Preparing ASCII payloads...")
        precompiled = []
        for i in range(packet_count):
            header_str = f"D,{i},"

            padding_size = max(0, payload_size_bytes - len(header_str) - 1)
            padding_str = "X" * padding_size
            full_frame = f"{header_str}{padding_str}\n".encode("ascii")

            precompiled.append((i, full_frame))
        return precompiled

    def transmit(
        self, precompiled_packets: list[tuple[int, bytes]], frequency_hz: int
    ) -> list[dict[str, int]]:
        """
        Main strict transmission loop.
        NOTE: This function intentionally fully occupies one CPU core (busy-wait).
        Never use time.sleep() here (scheduler delay is about ~15ms on Windows systems).
        """
        serial_obj = self.manager.get_serial()
        packet_count = len(precompiled_packets)

        self.tx_timestamps = [0] * packet_count  # Pre-allocate for performance

        if not serial_obj:
            self.logger.error(
                "Transmission aborted: received an empty serial port handle."
            )
            return []

        self.logger.debug(
            f"Starting aggressive transmission: {packet_count} packets @ {frequency_hz} Hz"
        )

        # Calculate the ideal interval in nanoseconds (force int type!).
        interval_ns = int(1_000_000_000 / frequency_hz)

        # Clear the OS transmit buffer.
        serial_obj.flush()

        # Establish the zero point for our very precise hardware clock.
        next_transmission_time = time.perf_counter_ns()

        for i in range(packet_count):
            packet_id, raw_bytes = precompiled_packets[i]

            # --- RESOURCE BLOCKING (BUSY-WAIT) ---
            while time.perf_counter_ns() < next_transmission_time:
                pass

            # Capture the transmission timestamp after leaving busy-wait.
            self.tx_timestamps[i] = time.time_ns() // 1000

            # Push the byte stream over USB (the OS forwards it to the CH340/CP2102 driver).
            serial_obj.write(raw_bytes)

            # Log progress every 1000 packets (for DEBUG logs).
            if (i + 1) % 1000 == 0:
                self.logger.debug(
                    f"  ...sent {i + 1} / {packet_count} physical packets"
                )

            # Move the timestamp forward.
            # Important: ALWAYS add the interval to the theoretical point in time
            # so system errors do not accumulate (drift prevention).
            next_transmission_time += interval_ns

        # Force the port FIFO queue to flush the remaining packets.
        serial_obj.flush()
        self.logger.debug("Physical transmission over the hardware port completed.")

        return [
            {"packet_id": precompiled_packets[i][0], "pc_tx_ts": self.tx_timestamps[i]}
            for i in range(packet_count)
        ]
