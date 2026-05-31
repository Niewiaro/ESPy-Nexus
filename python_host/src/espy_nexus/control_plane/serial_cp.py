import time
import logging

from espy_nexus.control_plane.base import BaseControlPlane
from espy_nexus.control_plane.connection_manager import SerialConnectionManager


class SerialControlPlane(BaseControlPlane):
    """
    Control Plane. Uses the Connection Manager
    to send commands and retrieve logs from ESP32.
    """

    def __init__(self, port: str, baudrate: int, timeout_s: float = 2.0):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.timeout_s = timeout_s
        self.manager = SerialConnectionManager(port, baudrate, timeout_s)

    def connect(self) -> None:
        self.manager.connect()

    def disconnect(self) -> None:
        self.manager.disconnect()

    def send_command(self, cmd: str, expected_ack: str, max_attempts: int = 3) -> bool:
        """Send command and wait for acknowledgment."""
        # get pointer to the serial port from the manager
        serial_obj = self.manager.get_serial()
        self.logger.debug(f"Sending command {cmd}...")

        for attempt in range(max_attempts):
            serial_obj.reset_input_buffer()

            formatted_cmd = f"{cmd}\n"
            serial_obj.write(formatted_cmd.encode("ascii"))
            serial_obj.flush()

            start_time = time.time()

            while (time.time() - start_time) < self.timeout_s:
                if serial_obj.in_waiting > 0:
                    line = (
                        serial_obj.readline().decode("ascii", errors="replace").strip()
                    )

                    if not line:
                        continue

                    if line == expected_ack:
                        self.logger.debug(f"Received expected ACK: {line}")
                        return True
                    elif line.startswith("WARNING:"):
                        self.logger.warning(f"[Hardware Warning] {line}")
                        continue
                    elif line.startswith("ERROR:"):
                        self.logger.error(f"[Hardware Error] {line}")
                        return False
                    else:
                        self.logger.debug(f"[ESP32 Log] {line}")
                else:
                    time.sleep(0.001)

            self.logger.debug(
                f"Timeout waiting for '{expected_ack}' (Attempt {attempt + 1}/{max_attempts})."
            )

        return False

    def fetch_data(self, timeout_data: float = 5.0) -> list[dict[str, int]]:
        """Fetches result data from ESP32."""
        serial_obj = self.manager.get_serial()
        self.logger.debug("Fetching data...")

        if not self.send_command("GET_DATA", expected_ack="ACK_GET_DATA"):
            self.logger.error("Transfer failed.")
            return []

        records = []
        start_time = time.time()

        while (time.time() - start_time) < timeout_data:
            if serial_obj.in_waiting > 0:
                line = serial_obj.readline().decode("ascii", errors="replace").strip()

                start_time = time.time()

                if line.startswith("D,"):
                    try:
                        parts = line.split(",")
                        records.append(
                            {
                                "packet_id": int(parts[1]),
                                "esp_rx_ts": int(parts[2]),
                            }
                        )
                    except (IndexError, ValueError):
                        self.logger.error(f"Invalid data line: {line}")

                elif line == "END_DATA":
                    self.logger.debug(
                        f"Data retrieval complete. Fetched {len(records)} logs."
                    )
                    break
            else:
                time.sleep(0.001)

        return records


if __name__ == "__main__":
    from espy_nexus.core.logger import setup_global_logging

    setup_global_logging()
    logger = logging.getLogger(__name__)

    PORT = "COM5"
    BAUDRATE = 921600

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("--- Scenario 1: Test Ping ---")

    cp = SerialControlPlane(port=PORT, baudrate=BAUDRATE)

    try:
        cp.connect()

        logger.info("\n[*] Sending: 'TEST'")
        if cp.send_command("TEST", "ACK_TEST"):
            logger.info("[+] Received ACK_TEST!")
        else:
            logger.info("[-] No response or error.")

    except Exception as e:
        logger.error(f"\n[E]: {e}")
    finally:
        cp.disconnect()
        logger.info("--- Test End ---\n")
