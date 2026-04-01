import time

from espy_nexus.control_plane.connection_manager import SerialConnectionManager


class SerialControlPlane:
    """
    Control Plane. Uses the Connection Manager
    to send commands and retrieve logs from ESP32.
    """

    def __init__(self, port: str, baudrate: int, timeout_s: float = 2.0):
        self.timeout_s = timeout_s
        self.manager = SerialConnectionManager(port, baudrate, timeout_s)

    def connect(self) -> None:
        self.manager.connect()

    def disconnect(self) -> None:
        self.manager.disconnect()

    def send_command(self, cmd: str, expected_ack: str, max_attempts: int = 3) -> bool:
        """Send command and wait for acknowledgment."""
        # get pointer to the serial port from the manager
        serial = self.manager.get_serial()
        print(f"[Control Plane] Sending command {cmd}...")

        for attempt in range(max_attempts):
            serial.reset_input_buffer()

            formatted_cmd = f"{cmd}\n"
            serial.write(formatted_cmd.encode("ascii"))
            serial.flush()

            start_time = time.time()
            while (time.time() - start_time) < self.timeout_s:
                if serial.in_waiting > 0:
                    line = serial.readline().decode("ascii", errors="replace").strip()

                    if not line:
                        continue

                    if line == expected_ack:
                        return True
                    elif line.startswith("WARNING:"):
                        print(f"[Control Plane Warning] {line}")
                        continue
                    elif line.startswith("ERROR:"):
                        print(f"[Control Plane Error] {line}")
                        return False
                    else:
                        print(f"[ESP32 Log] {line}")

            print(
                f"[Control Plane] Timeout waiting for '{expected_ack}' (Attempt {attempt + 1}/{max_attempts})."
            )

        return False

    def fetch_data(self, timeout_data: float = 5.0) -> list[dict[str, int]]:
        """Fetches result data from ESP32."""
        serial = self.manager.get_serial()
        print("[Control Plane] Fetching data...")

        if not self.send_command("GET_DATA", expected_ack="ACK_GET_DATA"):
            print("[Control Plane Error] Transfer failed.")
            return []

        records = []
        start_time = time.time()

        while (time.time() - start_time) < timeout_data:
            if serial.in_waiting > 0:
                line = serial.readline().decode("ascii", errors="replace").strip()

                start_time = time.time()

                if line.startswith("D,"):
                    try:
                        parts = line.split(",")
                        records.append(
                            {
                                "packet_id": int(parts[1]),
                                "pc_ts": int(parts[2]),
                                "esp_ts": int(parts[3]),
                            }
                        )
                    except (IndexError, ValueError):
                        print(f"[Control Plane] Invalid data line: {line}")

                elif line == "END_DATA":
                    print(
                        f"[Control Plane] Data retrieval complete. Fetched {len(records)} logs."
                    )
                    break

        return records


if __name__ == "__main__":
    PORT = "COM5"
    BAUDRATE = 921600

    print("--- Scenario 1: Test Ping ---")

    cp = SerialControlPlane(port=PORT, baudrate=BAUDRATE)

    try:
        cp.connect()

        print("\n[*] Sending: 'TEST'")
        if cp.send_command("TEST", "ACK_TEST"):
            print("[+] Received ACK_TEST!")
        else:
            print("[-] No response or error.")

    except Exception as e:
        print(f"\n[E]: {e}")
    finally:
        cp.disconnect()
        print("--- Test End ---\n")
