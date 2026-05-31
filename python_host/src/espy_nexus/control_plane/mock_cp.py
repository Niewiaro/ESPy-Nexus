import time
import logging

from espy_nexus.control_plane.base import BaseControlPlane


class MockControlPlane(BaseControlPlane):
    """
    Mock Control Plane version that does not require physical hardware.
    It simulates hardware responses, delays, and synthetic telemetry data.
    """

    def __init__(self, port: str = "MOCK", baudrate: int = 0, timeout_s: float = 2.0):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.port = port
        self.baudrate = baudrate
        self.timeout_s = timeout_s
        self.is_connected = False

        # Configuration options for testing different scenarios
        self.simulate_errors = False
        self.mock_records_to_generate = 50

    def connect(self) -> None:
        self.logger.debug(f"Connected to virtual port: {self.port}")
        self.is_connected = True

    def disconnect(self) -> None:
        self.logger.debug("Disconnected virtual device.")
        self.is_connected = False

    def send_command(self, cmd: str, expected_ack: str, max_attempts: int = 3) -> bool:
        """Simulates sending a command and waiting for an ACK."""
        _ = max_attempts
        if not self.is_connected:
            self.logger.error("No virtual connection available!")
            return False

        self.logger.debug(f"Sending command: {cmd}...")

        # Simulate behavior in case of hardware issues
        if self.simulate_errors and cmd != "STOP":
            self.logger.warning(f"No response for: {cmd}")
            return False

        # Simulate propagation/processing delay on the ESP32 (e.g. 50 ms)
        time.sleep(0.05)

        self.logger.debug(f"Received (simulated): {expected_ack}")
        return True

    def fetch_data(self, timeout_data: float = 5.0) -> list[dict[str, int]]:
        """Simulates fetching buffered logs by generating synthetic data."""
        _ = timeout_data
        self.logger.debug("[Mock Control Plane] Fetching data...")

        if not self.send_command("GET_DATA", expected_ack="ACK_GET_DATA"):
            self.logger.error(
                "[Mock Control Plane Error] Error during transfer simulation."
            )
            return []

        records = []
        # Base timestamp (for example, in microseconds)
        base_pc_ts = int(time.time() * 1_000_000)

        # Simulate packet transfer and generation
        for i in range(self.mock_records_to_generate):
            # The ESP32 has its own hardware clock;
            # simulate it by adding a small fixed offset, e.g. 120 us
            esp_offset = 120

            # Interval between packets, e.g. 1000 us (1 ms)
            time_delta = i * 1000

            records.append(
                {
                    "packet_id": i + 1,
                    "esp_rx_ts": base_pc_ts + time_delta + esp_offset,
                }
            )

        # Simulate the duration of the UART transfer
        time.sleep(self.mock_records_to_generate * 0.001)

        self.logger.debug(f"Fetch complete. Generated {len(records)} logs.")
        return records


if __name__ == "__main__":
    from espy_nexus.core.logger import setup_global_logging

    setup_global_logging()
    logger = logging.getLogger(__name__)

    logger.info("--- Scenario 1: Virtual Ping Test (Happy Path) ---")
    mock_cp = MockControlPlane()

    try:
        mock_cp.connect()
        if mock_cp.send_command("TEST", "ACK_TEST"):
            logger.info("[+] ACK_TEST received correctly!")

        logs = mock_cp.fetch_data()
        logger.info(f"First log fetched: {logs[0] if logs else 'None'}")

    except Exception as e:
        logger.exception(e)
    finally:
        mock_cp.disconnect()
        logger.info("--- End of Test ---")

    logger.info("--- Scenario 2: Hardware Failure Simulation ---")
    bad_cp = MockControlPlane()
    bad_cp.simulate_errors = True

    try:
        bad_cp.connect()
        if not bad_cp.send_command("START_SERIAL", "ACK_START_SERIAL"):
            logger.info("[-] ESP32 no-response behavior simulated correctly.")
    finally:
        bad_cp.disconnect()
