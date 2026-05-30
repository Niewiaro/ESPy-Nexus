import time
import logging
from espy_nexus.data_plane.base import BaseDataPlane
from espy_nexus.control_plane.connection_manager import SerialConnectionManager


class SerialDataPlane(BaseDataPlane):
    """
    Data Plane dla portu szeregowego (Serial port).
    Generuje i wysyła pakiety testowe z wysoką precyzją, wymuszając rygor
    czasowy na poziomie mikrosekund za pomocą pętli "Busy-Wait".
    """

    def __init__(self, port: str, baudrate: int):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.manager = SerialConnectionManager(port, baudrate)

    def connect(self) -> None:
        """Pobiera zasoby systemowe portu szeregowego."""
        self.logger.info(
            "Konfiguracja buforów systemowych dla szybkiej transmisji po Serialu."
        )
        self.manager.connect()

    def disconnect(self) -> None:
        """Zwalnia port, aby inny skrypt/narzędzie mogło go użyć."""
        self.logger.info("Zwalnianie zasobów Serial Data Plane.")
        self.manager.disconnect()

    def transmit(self, packet_count: int, frequency_hz: int) -> None:
        """
        Główna, rygorystyczna pętla nadawcza.
        UWAGA: Ta funkcja celowo blokuje całkowicie 1 rdzeń procesora (Busy-Wait).
        Nigdy nie używać tutaj time.sleep() (błąd planisty rzędu ~15ms w systemach Windows).
        """
        serial = self.manager.get_serial()
        if not serial:
            self.logger.error(
                "Transmisja przerwana: Zwrócono pusty uchwyt portu Serial."
            )
            return

        self.logger.info(
            f"Rozpoczynanie agresywnego nadawania: {packet_count} Pkts @ {frequency_hz} Hz"
        )

        # Obliczenie idealnego odstępu w nanosekundach
        interval_ns = 1_000_000_000 / frequency_hz

        # Wyczyszczenie brudów w buforze wysyłkowym systemu OS
        serial.flush()

        # Wyznaczenie punktu zerowego dla naszego bardzo precyzyjnego zegara sprzętowego
        next_transmission_time = time.perf_counter_ns()

        for i in range(packet_count):

            # --- BLOKADA ZASOBÓW (BUSY-WAIT) ---
            # Ten kod kręci się w miejscu, pożerając CPU, aż osiągnie dokładny interwał.
            # Zapewnia to pominięcie niedokładnego planisty (system scheduler).
            while time.perf_counter_ns() < next_transmission_time:
                pass

            # Pobranie stempla czasowego (TS) wysyłki po wyjściu z busy-wait
            pc_timestamp_us = time.time_ns() // 1000

            # Budowa pakietu do sprzętu: "D,<Id_Pakietu>,<Stempel_Czasowy_PC>\n"
            packet = f"D,{i},{pc_timestamp_us}\n".encode("ascii")

            # Wrzucenie strumienia bajtów na USB (system OS przerzuca to do sterownika CH340/CP2102)
            serial.write(packet)

            # Przesunięcie znacznika czasu do przodu.
            # Ważne: ZAWSZE dodajemy interwał do teoretycznego punktu w czasie,
            # aby błędy systemowe nie kumulowały się (drift prevention).
            next_transmission_time += interval_ns

        # Wymuszenie fizycznego opróżnienia kolejki FIFO portu z ostatnich pakietów
        serial.flush()
        self.logger.info("Fizyczna wysyłka portem sprzętowym zakończona.")
