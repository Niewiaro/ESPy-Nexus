import serial
import time


class SerialConnectionManager:
    """
    Multiton pattern (Registry). Ensures only one instance
    of the connection manager for each physical COM port.
    """

    _instances: dict[str, "SerialConnectionManager"] = {}

    def __new__(cls, port: str, baudrate: int = 921600, timeout_s: float = 2.0):
        port_key = port.upper()

        if port_key not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[port_key] = instance
            instance._init_connection(port_key, baudrate, timeout_s)

        return cls._instances[port_key]

    def _init_connection(self, port: str, baudrate: int, timeout_s: float):
        self.port = port
        self.baudrate = baudrate
        self.timeout_s = timeout_s
        self.serial_obj = serial.Serial()
        self.serial_obj.port = self.port
        self.serial_obj.baudrate = self.baudrate
        self.serial_obj.timeout = self.timeout_s

    def connect(self) -> None:
        if not self.serial_obj.is_open:
            self.serial_obj.open()
            time.sleep(0.1)
            self.serial_obj.reset_input_buffer()
            self.serial_obj.reset_output_buffer()
            print(
                f"[SerialConnectionManager] Port {self.port} @ {self.baudrate} bps has been opened."
            )
        else:
            print(
                f"[SerialConnectionManager] Port {self.port} @ {self.baudrate} bps is already open."
            )

    def disconnect(self) -> None:
        if self.serial_obj.is_open:
            self.serial_obj.close()
            print(
                f"[SerialConnectionManager] Port {self.port} @ {self.baudrate} bps has been closed."
            )
        else:
            print(
                f"[SerialConnectionManager] Port {self.port} @ {self.baudrate} bps is already closed."
            )

    def get_serial(self) -> serial.Serial:
        if not self.serial_obj.is_open:
            raise ConnectionError(
                f"[SerialConnectionManager] Port {self.port} is not open!"
            )
        return self.serial_obj


if __name__ == "__main__":
    manager_00 = SerialConnectionManager("COM5")
    manager_00.connect()

    manager_01 = SerialConnectionManager("COM5")
    manager_01.connect()

    print(manager_00 is manager_01)

    manager_00.disconnect()
    manager_01.disconnect()
