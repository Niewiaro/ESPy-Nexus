import struct
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

    def fetch_str_data(self, timeout_data: float = 5.0) -> list[dict[str, int]]:
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

    def fetch_data(self, timeout_data: float = 5.0) -> list[dict[str, int]]:
        """Fetches binary result data from ESP32."""
        serial_obj = self.manager.get_serial()
        self.logger.debug("Fetching binary data...")

        serial_obj.reset_input_buffer()

        serial_obj.write(b"GET_DATA\n")
        serial_obj.flush()

        start_time = time.time()
        record_count = 0
        ack_received = False

        while (time.time() - start_time) < timeout_data:
            if serial_obj.in_waiting > 0:
                line = serial_obj.readline().decode("ascii", errors="replace").strip()

                if line.startswith("ACK_GET_DATA,"):
                    try:
                        record_count = int(line.split(",")[1])
                        ack_received = True
                        self.logger.debug(
                            f"Hardware reported {record_count} records in PSRAM."
                        )
                        break
                    except ValueError:
                        self.logger.error("Failed to parse record count from ACK.")
                        return []
                elif line.startswith("WARNING:") or line.startswith("ERROR:"):
                    self.logger.warning(f"[ESP32] {line}")
            else:
                time.sleep(0.001)

        if not ack_received:
            self.logger.error("Timeout waiting for ACK_GET_DATA.")
            return []

        if record_count == 0:
            self.logger.warning("ESP32 reported 0 records.")
            return []

        # C++: uint32_t (4) + int64_t (8) = 12 bits per record
        bytes_per_record = 12
        expected_bytes = record_count * bytes_per_record

        self.logger.debug(f"Downloading {expected_bytes} bytes of raw PSRAM...")

        raw_bytes = serial_obj.read(expected_bytes)

        if len(raw_bytes) != expected_bytes:
            self.logger.error(
                f"Download incomplete. Got {len(raw_bytes)}/{expected_bytes} bytes."
            )
            return []

        # C++: '<' (Little Endian), 'I' (uint32_t = 4B), 'q' (int64_t = 8B)
        self.logger.debug("Unpacking binary structs...")
        records = []

        try:
            for struct_tuple in struct.iter_unpack("<Iq", raw_bytes):
                records.append(
                    {"packet_id": struct_tuple[0], "esp_rx_ts": struct_tuple[1]}
                )
        except struct.error as e:
            self.logger.error(f"Failed to unpack struct: {e}")
            return []

        self.logger.info(
            f"Data retrieval complete. Fetched {len(records)} records instantly."
        )
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
