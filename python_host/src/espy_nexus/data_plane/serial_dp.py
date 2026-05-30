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

    def transmit(self, packet_count: int, frequency_hz: int) -> None:
        """
        Main strict transmission loop.
        NOTE: This function intentionally fully occupies one CPU core (busy-wait).
        Never use time.sleep() here (scheduler delay is about ~15ms on Windows systems).
        """
        serial_obj = self.manager.get_serial()
        if not serial_obj:
            self.logger.error(
                "Transmission aborted: received an empty serial port handle."
            )
            return

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

            # --- RESOURCE BLOCKING (BUSY-WAIT) ---
            # This code spins in place, consuming CPU until the exact interval is reached.
            # This avoids relying on the imprecise system scheduler.
            while time.perf_counter_ns() < next_transmission_time:
                pass

            # Capture the transmission timestamp after leaving busy-wait.
            pc_timestamp_us = time.time_ns() // 1000

            # Build the packet for the hardware: "D,<PacketId>,<PC_Timestamp>\n"
            packet = f"D,{i},{pc_timestamp_us}\n".encode("ascii")

            # Push the byte stream over USB (the OS forwards it to the CH340/CP2102 driver).
            serial_obj.write(packet)

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
