import time
from espy_nexus.data_plane.base import BaseDataPlane
from espy_nexus.control_plane.connection_manager import SerialConnectionManager


class SerialDataPlane(BaseDataPlane):
    """
    Data Plane for serial port.
    Generating and sending test data payloads at a precise frequency using busy-waiting.
    This class is responsible only for generating and sending a fast test payload
    """

    def __init__(self, port: str, baudrate: int):
        self.manager = SerialConnectionManager(port, baudrate)

    def transmit(self, packet_count: int, frequency_hz: int) -> None:
        """
        Main transmission loop.
        Uses "Busy-Wait" with time.perf_counter_ns() to avoid
        inaccuracy of system scheduler (Windows/Linux time.sleep).
        """
        # Get the physical serial port object from the manager
        serial = self.manager.get_serial()

        print(
            f"[Data Plane] Start transmission: {packet_count} packets @ {frequency_hz} Hz"
        )

        # Interval between packets in nanoseconds (1 second = 1 billion ns)
        interval_ns = 1_000_000_000 / frequency_hz

        # Flush any garbage from the port before the critical test
        serial.flush()

        # Set time zero point for our precise clock
        next_transmission_time = time.perf_counter_ns()

        for i in range(packet_count):
            # precise wait (Busy-Wait Loop)
            # While loop blocks 1 CPU core for a millisecond fraction,
            # but guarantees jitter at hardware level.
            while time.perf_counter_ns() < next_transmission_time:
                pass

            # get sender timestamp (pc_ts in microseconds)
            pc_timestamp_us = time.time_ns() // 1000

            # build packet (Currently ASCII format)
            packet = f"D,{i},{pc_timestamp_us}\n".encode("ascii")

            # physically write to serial port
            serial.write(packet)

            # schedule next transmission time
            # Always add interval to *theoretical* time, not to "now".
            # This avoids cumulative drift.
            next_transmission_time += interval_ns

        # Ensure the last bytes physically left the computer's USB buffer
        serial.flush()
        print("[Data Plane] Transmission completed successfully.")
