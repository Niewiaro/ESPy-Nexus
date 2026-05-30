import time
import logging
from espy_nexus.data_plane.base import BaseDataPlane


class MockDataPlane(BaseDataPlane):
    """
    Atrapa Data Plane do szybkiego testowania całego systemu bez sprzętu.
    Nie używa busy-wait, aby nie obciążać procesora podczas pracy w IDE.
    """

    def __init__(self, port: str = "MOCK", baudrate: int = 0):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.port = port
        self.baudrate = baudrate
        self.is_connected = False

    def connect(self) -> None:
        self.logger.info(
            f"Otwieranie wirtualnego gniazda dla Data Plane (Port: {self.port}, Baudrate: {self.baudrate})"
        )
        self.is_connected = True

    def disconnect(self) -> None:
        self.logger.info(f"Zamykanie wirtualnego gniazda Data Plane.")
        self.is_connected = False

    def transmit(self, packet_count: int, frequency_hz: int) -> None:
        if not self.is_connected:
            self.logger.error("Błąd: Data Plane nie jest podłączony przed transmisją!")
            return

        self.logger.info(
            f"Rozpoczęto symulowaną transmisję: {packet_count} pakietów @ {frequency_hz} Hz"
        )

        # Odstęp między pakietami w sekundach
        interval_s = 1.0 / frequency_hz

        # Symulacja wysyłki
        # Używamy sleep w MOCKU, ponieważ dokładność czasowa nie ma tu znaczenia
        # dla działania samej maszyny stanowej TestEngine.
        for i in range(packet_count):
            # Tutaj normalnie szłyby dane do kabla
            time.sleep(interval_s)

            # (Opcjonalnie: logowanie co 1000 pakietu, żeby nie zaśmiecić konsoli)
            if (i + 1) % 1000 == 0:
                self.logger.debug(
                    f"  ...wysłano {i + 1} / {packet_count} wirtualnych pakietów"
                )

        self.logger.info("Transmisja symulowana ukończona sukcesem.")
