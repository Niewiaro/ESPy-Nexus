import time
import logging
import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime, timedelta

from espy_nexus.core.config import TestConfig, Protocol
from espy_nexus.control_plane.base import BaseControlPlane
from espy_nexus.data_plane.base import BaseDataPlane

ROW_SEP_LEN = 74


def format_duration(seconds: float, compact: bool = False) -> str:
    """Konwertuje sekundy na czytelny format. Z opcją skróconą dla tabel."""
    hours, remainder = divmod(seconds, 3600)
    minutes, remainder = divmod(remainder, 60)
    secs = int(remainder)
    millis = int((remainder - secs) * 1000)

    if compact:
        if hours > 0:
            return f"{int(hours):02d}h {int(minutes):02d}m {secs:02d}s"
        return f"{int(minutes):02d}m {secs:02d}s {millis:03d}ms"

    return f"{int(hours):02d}h {int(minutes):02d}m {secs:02d}s {millis:03d}ms"


class TestEngine:
    """
    The Test Engine orchestrates the execution of a test matrix on hardware (Hardware-in-the-Loop).
    It acts as a Data Acquisition System (DAQ), storing raw telemetry into SQLite for offline analysis.
    """

    def __init__(
        self,
        control_plane: BaseControlPlane,
        data_planes: dict[Protocol, BaseDataPlane],
        db_path: str = "hil_raw_data.sqlite",
    ):
        # 1. Logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 2. DI - Control Plane
        self.control_plane = control_plane

        # 3. DI - Data Planes
        self.data_planes = data_planes

        # 4. Inicjalizacja bazy danych surowych logów (DAQ)
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Inicjalizuje schemat relacyjnej bazy danych SQLite dla surowych danych."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Table 1: Metadata for each test run (one row per test)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS test_runs (
                        test_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_datetime TEXT,
                        topology TEXT,
                        protocol TEXT,
                        freq_hz INTEGER,
                        status TEXT,
                        payload_size INTEGER,
                        expected_count INTEGER,
                        engine_time_tx_actual REAL,
                        engine_time_fetch REAL
                    )
                """)

                # Table 2: Raw packet logs for each test run (multiple rows per test)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS raw_packets (
                        test_id INTEGER,
                        packet_id INTEGER,
                        pc_tx_ts_us INTEGER,
                        esp_rx_ts_us INTEGER,
                        FOREIGN KEY(test_id) REFERENCES test_runs(test_id)
                    )
                """)

                # Index for faster queries on raw_packets by test_id
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_test_id ON raw_packets(test_id)"
                )

                conn.commit()
                self.logger.info(f"Database initialized/verified at: {self.db_path}")
        except sqlite3.Error as e:
            self.logger.critical(f"Failed to initialize SQLite Database: {e}")
            raise

    def run_matrix(self, matrix: list[TestConfig]) -> None:

        self._print_schedule(matrix)

        try:
            input("\nPress [ENTER] to start tests (or Ctrl+C to cancel)...")
        except KeyboardInterrupt:
            self.logger.warning("\nTests cancelled before starting.")
            return

        self.logger.info("=" * ROW_SEP_LEN)
        self.logger.info("🚀 STARTING TEST MATRIX (DATA ACQUISITION MODE)")
        self.logger.info("=" * ROW_SEP_LEN)

        total_matrix_start = time.perf_counter()

        try:
            self.control_plane.connect()

            for i, config in enumerate(matrix, 1):
                start_dt = datetime.now()
                est_test_duration = (
                    config.packet_count / config.frequency_hz
                ) + config.cooldown_s
                end_dt = start_dt + timedelta(seconds=est_test_duration)

                self.logger.info(
                    f"[{i}/{len(matrix)}] >>> {config.protocol.value} {config.frequency_hz} Hz"
                )
                self.logger.info(
                    f"⏳ Estimated time: {format_duration(est_test_duration, compact=True)} | "
                    f"Planned end time: {end_dt.strftime('%H:%M:%S')}"
                )

                test_start_perf = time.perf_counter()

                self._run_single_test(config)

                test_actual_duration = time.perf_counter() - test_start_perf
                self.logger.info(
                    f"✅ Completed. Actual time: {format_duration(test_actual_duration)}"
                )

                if i < len(matrix):
                    self.logger.debug(
                        f"Cooling down for {config.cooldown_s} seconds before next test..."
                    )
                    time.sleep(config.cooldown_s)

        except KeyboardInterrupt:
            self.logger.warning("\n[!] Tests cancelled by user (Ctrl+C).")
        finally:
            self.control_plane.disconnect()

            total_matrix_s = time.perf_counter() - total_matrix_start
            self.logger.info("=" * ROW_SEP_LEN)
            self.logger.info(
                f"📊 END OF ACQUISITION | total time: {format_duration(total_matrix_s)}"
            )
            self.logger.info("=" * ROW_SEP_LEN)

    # =========================================================================
    # SCHEDULE AND TABLE PRINTING
    # =========================================================================

    def _print_schedule(self, matrix: list[TestConfig]) -> None:
        now = datetime.now()
        current_time = now
        total_duration = 0.0

        schedule_rows = []

        for config in matrix:
            tx_s = config.packet_count / config.frequency_hz
            test_total_s = tx_s + config.cooldown_s + config.drain_time_s

            start_str = current_time.strftime("%H:%M:%S")
            current_time += timedelta(seconds=test_total_s)
            end_str = current_time.strftime("%H:%M:%S")

            schedule_rows.append(
                f"{config.protocol.value:<10} | {config.frequency_hz:<10d} Hz | {format_duration(test_total_s, compact=True):<14} | {start_str:<10} | {end_str:<10}"
            )
            total_duration += test_total_s

        self.logger.info("=" * ROW_SEP_LEN)
        self.logger.info("📅 TEST MATRIX SCHEDULE")
        self.logger.info("=" * ROW_SEP_LEN)
        self.logger.info(f"Total tests:\t\t{len(matrix)}")
        self.logger.info(f"Router topology:\t{matrix[0].router_topology.value}")
        self.logger.info(f"Payload size:\t\t{matrix[0].payload_size_bytes} B")
        self.logger.info(f"Packet count:\t\t{matrix[0].packet_count}")
        self.logger.info(f"Start time:\t\t{now.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(
            f"End estimated time:\t{current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.logger.info(f"Total estimated time:\t{format_duration(total_duration)}")
        self.logger.info("-" * ROW_SEP_LEN)
        self.logger.info(
            f"{'#':<3} | {'PROTOCOL':<10} | {'FREQUENCY':<13} | {'DURATION':<14} | {'START':<10} | {'END':<10}"
        )
        self.logger.info("-" * ROW_SEP_LEN)
        for index, row in enumerate(schedule_rows):
            self.logger.info(f"{index + 1:3d} | {row}")
        self.logger.info("=" * ROW_SEP_LEN)

    # =========================================================================
    # SINGLE TEST EXECUTION (ACQUISITION ONLY)
    # =========================================================================

    def _run_single_test(self, config: TestConfig) -> None:
        # 1. Data Plane Dependency Injection
        data_plane = self.data_planes.get(config.protocol)
        if not data_plane:
            self.logger.warning(
                f"[-] No data plane found for protocol: {config.protocol.value}. Skipping..."
            )
            return

        # 2. Prepare payloads (pre-compilation step)
        precompiled_packets = data_plane.prepare_payloads(
            config.packet_count, config.payload_size_bytes
        )

        # 3. Control Plane Handshake (START command)
        if not self._perform_start_handshake(config):
            self._handle_error(config, "ERR_START")
            return

        # 4. Data Transmission with timing
        tx_records = []
        actual_tx_s = 0.0
        try:
            data_plane.connect()
            tx_start = time.perf_counter()
            tx_records = data_plane.transmit(
                precompiled_packets, frequency_hz=config.frequency_hz
            )
            actual_tx_s = time.perf_counter() - tx_start
            self.logger.info(
                f"Transmit data actual time: {format_duration(actual_tx_s)}"
            )
            self.logger.debug(
                f"Waiting {config.drain_time_s}s for delayed packets to arrive in the network..."
            )
            time.sleep(config.drain_time_s)
        except Exception as e:
            self.logger.error(f"[!] Critical error during transmission: {e}")
            self._handle_error(config, f"ERR_DATA_PLANE: {e}")
            return
        finally:
            data_plane.disconnect()

        # 5. Closing and fetching results from Control Plane
        self.control_plane.send_command("STOP", expected_ack="ACK_STOP")
        rx_records, actual_fetch_s = self._fetch_logs()

        # 6. Data Integrity Check & Join
        if not rx_records:
            self._handle_error(config, "NO_DATA", actual_tx_s, actual_fetch_s)
            return

        df_tx = pd.DataFrame(tx_records)  # Expected: [packet_id, pc_tx_ts]
        df_rx = pd.DataFrame(rx_records)  # Expected: [packet_id, esp_rx_ts]

        # safe join (merge) to ensure all packets are accounted for, even if lost
        if not df_tx.empty and not df_rx.empty:
            df_merged = pd.merge(df_tx, df_rx, on="packet_id", how="outer")
        elif not df_tx.empty:
            df_merged = df_tx.copy()
            df_merged["esp_rx_ts"] = np.nan
        else:
            df_merged = pd.DataFrame(columns=["packet_id", "pc_tx_ts", "esp_rx_ts"])

        df_merged.sort_values(by="packet_id", inplace=True)

        # Rename columns for clarity before saving to DB
        df_merged.rename(
            columns={"pc_tx_ts": "pc_tx_ts_us", "esp_rx_ts": "esp_rx_ts_us"},
            inplace=True,
        )

        # 7. Commit to SQLite Database (ACID Transaction)
        self._commit_to_db(
            config=config,
            records_df=df_merged,
            actual_tx_s=actual_tx_s,
            actual_fetch_s=actual_fetch_s,
            status="OK",
        )

    # =========================================================================
    # HELPER METHODS FOR TEST EXECUTION & DB TRANSACTIONS
    # =========================================================================

    def _perform_start_handshake(self, config: TestConfig) -> bool:
        cmd = f"START_{config.protocol.value}"
        ack = f"ACK_START_{config.protocol.value}"
        success = self.control_plane.send_command(cmd, expected_ack=ack)
        if not success:
            self.logger.error(
                "[-] No ACK received for START command. Control Plane handshake failed."
            )
        return success

    def _fetch_logs(self) -> tuple[list[dict], float]:
        fetch_start = time.perf_counter()
        records = self.control_plane.fetch_data()
        fetch_duration = time.perf_counter() - fetch_start
        self.logger.info(f"Fetch logs actual time: {format_duration(fetch_duration)}")
        return records, fetch_duration

    def _handle_error(
        self,
        config: TestConfig,
        error_msg: str,
        tx_s: float = 0.0,
        fetch_s: float = 0.0,
    ) -> None:
        """Handles test errors by committing the error status to the database."""
        self.logger.error(f"[X] {error_msg}")
        self._commit_to_db(config, pd.DataFrame(), tx_s, fetch_s, status=error_msg)

    def _commit_to_db(
        self,
        config: TestConfig,
        records_df: pd.DataFrame,
        actual_tx_s: float,
        actual_fetch_s: float,
        status: str,
    ) -> None:
        """Commits the test results to the SQLite database (ACID Transaction)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 1. Insert metadata for the test run into test_runs table
                cursor.execute(
                    """
                    INSERT INTO test_runs (run_datetime, topology, protocol, freq_hz, status, payload_size, expected_count, engine_time_tx_actual, engine_time_fetch)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        datetime.now().isoformat(),
                        config.router_topology.value,
                        config.protocol.value,
                        config.frequency_hz,
                        status,
                        config.payload_size_bytes,
                        config.packet_count,
                        actual_tx_s,
                        actual_fetch_s,
                    ),
                )

                test_id = (
                    cursor.lastrowid
                )  # Retrieve the auto-generated test_id for the inserted row

                # 2. Insert raw packet logs into raw_packets table if records exist
                if not records_df.empty:
                    # Add test_id to each row in the DataFrame before inserting into raw_packets
                    records_df["test_id"] = test_id

                    # Select only the necessary columns to match the raw_packets table schema
                    cols_to_save = [
                        "test_id",
                        "packet_id",
                        "pc_tx_ts_us",
                        "esp_rx_ts_us",
                    ]

                    # Ensure all required columns exist in the DataFrame, even if they are empty
                    for col in cols_to_save:
                        if col not in records_df.columns:
                            records_df[col] = np.nan

                    records_df = records_df[cols_to_save]

                    # Commit to SQLite Database (ACID Transaction)
                    records_df.to_sql(
                        "raw_packets", conn, if_exists="append", index=False
                    )

                conn.commit()
                self.logger.info(
                    f"[DB] Saved Test ID: {test_id} | Status: {status} | Packets logged: {len(records_df)}"
                )

        except sqlite3.Error as e:
            self.logger.critical(f"[DB] Critical Error during database commit: {e}")
