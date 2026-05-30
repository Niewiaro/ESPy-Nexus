import serial
import time
import logging


class SerialConnectionManager:
    """
    Multiton pattern (Registry). Ensures only one instance
    of the connection manager for each physical COM port.
    """

    _instances: dict[str, "SerialConnectionManager"] = {}

    def __new__(cls, port: str, baudrate: int = 921600, timeout_s: float = 2.0):
        port_key = port.upper()

        if port_key not in cls._instances:
            # Creating a completely new instance for a new port
            instance = super().__new__(cls)
            cls._instances[port_key] = instance
            instance._init_connection(port_key, baudrate, timeout_s)
        else:
            # If the instance exists but a new baudrate/timeout is requested, we must ensure that the physical port is updated.
            instance = cls._instances[port_key]
            instance._update_connection(baudrate, timeout_s)

        return cls._instances[port_key]

    def _init_connection(self, port: str, baudrate: int, timeout_s: float) -> None:
        """Initialize internal variables and the PySerial object."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.port = port
        self.baudrate = baudrate
        self.timeout_s = timeout_s

        self._ref_count = 0  # Track how many times this port is requested

        self.serial_obj = serial.Serial()
        self.serial_obj.port = self.port
        self.serial_obj.baudrate = self.baudrate
        self.serial_obj.timeout = self.timeout_s

    def _update_connection(self, baudrate: int, timeout_s: float) -> None:
        """Update the parameters of the existing port, if required."""
        if self.baudrate != baudrate or self.timeout_s != timeout_s:
            if self.serial_obj.is_open:
                self.logger.warning(
                    f"Changing parameters on open port {self.port}. "
                    f"Closing the port before reconfiguration."
                )
                self.serial_obj.close()

            self.baudrate = baudrate
            self.timeout_s = timeout_s
            self.serial_obj.baudrate = baudrate
            self.serial_obj.timeout = timeout_s
            self.logger.debug(
                f"Updated parameters for port {self.port} ({baudrate} bps)."
            )

    def connect(self) -> None:
        """Open the physical communication port."""
        self._ref_count += 1

        if self._ref_count == 1:
            if not self.serial_obj.is_open:
                try:
                    self.serial_obj.open()
                    # Short delay to allow voltages to stabilize after DTR/RTS reset
                    time.sleep(0.1)
                    self.serial_obj.reset_input_buffer()
                    self.serial_obj.reset_output_buffer()
                    self.logger.debug(
                        f"Port {self.port} @ {self.baudrate} bps has been opened."
                    )
                except serial.SerialException as e:
                    self._ref_count -= 1
                    self.logger.error(f"Failed to open port {self.port}: {e}")
                    raise
        else:
            self.logger.debug(
                f"Port {self.port} is already open (active clients: {self._ref_count})."
            )

    def disconnect(self) -> None:
        """Close the physical communication port."""
        if self._ref_count > 0:
            self._ref_count -= 1

        if self._ref_count == 0:
            if self.serial_obj.is_open:
                self.serial_obj.close()
                self.logger.debug(f"Last client has closed port {self.port}.")
        else:
            self.logger.debug(
                f"Client disconnected from port {self.port} (remaining clients: {self._ref_count})."
            )

    def get_serial(self) -> serial.Serial:
        """Return the active handle to the hardware port."""
        if not self.serial_obj.is_open:
            raise ConnectionError(
                f"Cannot return handle: Port {self.port} is not open!"
            )
        return self.serial_obj


if __name__ == "__main__":
    from espy_nexus.core.logger import setup_global_logging

    setup_global_logging()
    logger = logging.getLogger(__name__)

    PORT = "COM5"

    logger.info("--- Multiton Test ---")
    manager_00 = SerialConnectionManager(PORT, baudrate=115200)
    manager_00.connect()

    # Simulation: another part of the code requests the same port, but a faster baudrate
    manager_01 = SerialConnectionManager(PORT, baudrate=921600)
    manager_01.connect()

    logger.info(
        f"Is it the same object in memory? {'Yes' if manager_00 is manager_01 else 'No'}"
    )
    logger.info(f"Active object baudrate: {manager_00.serial_obj.baudrate}")

    manager_00.disconnect()
    manager_01.disconnect()  # Safe to call multiple times
