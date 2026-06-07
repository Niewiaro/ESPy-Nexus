import time
import logging
import pandas as pd
import os
from typing import Any
from datetime import datetime, timedelta

from espy_nexus.core.config import TestConfig, Protocol
from espy_nexus.control_plane.base import BaseControlPlane
from espy_nexus.data_plane.base import BaseDataPlane
from espy_nexus.pipeline.downlink import DownlinkAnalyzer, DownlinkMetrics

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
    It manages the control plane, data planes and analysis.
    """

    def __init__(
        self,
        control_plane: BaseControlPlane,
        data_planes: dict[Protocol, BaseDataPlane],
    ):
        # 1. Logger for the engine itself
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 2. Control Plane Dependence Injection (Strategy Pattern)
        self.control_plane = control_plane

        # 3. Data Plane Dependence Injection (Strategy Pattern)
        self.data_planes = data_planes

    def run_matrix(
        self,
        matrix: list[TestConfig],
        output_csv: str = "matrix_results.csv",
        cooldown_s: float = 5.0,
    ) -> None:

        self._print_schedule(matrix, cooldown_s)

        try:
            input("\nPress [ENTER] to start tests (or Ctrl+C to cancel)...")
        except KeyboardInterrupt:
            self.logger.warning("\nTests cancelled before starting.")
            return

        self.logger.info("=" * ROW_SEP_LEN)
        self.logger.info("🚀 STARTING TEST MATRIX")
        self.logger.info("=" * ROW_SEP_LEN)

        total_matrix_start = time.perf_counter()

        try:
            self.control_plane.connect()

            for i, config in enumerate(matrix, 1):
                start_dt = datetime.now()
                est_test_duration = (
                    (config.packet_count / config.frequency_hz) + cooldown_s + 1.0
                )
                end_dt = start_dt + timedelta(seconds=est_test_duration)

                self.logger.info(
                    f"[{i}/{len(matrix)}] >>> {config.protocol.value} {config.frequency_hz} Hz"
                )
                self.logger.info(
                    f"⏳ Estimated time: {format_duration(est_test_duration, compact=True)} | "
                    f"Planned end time: {end_dt.strftime('%H:%M:%S')}"
                )

                test_start_perf = time.perf_counter()

                self._run_single_test(config, output_csv)

                test_actual_duration = time.perf_counter() - test_start_perf
                self.logger.info(
                    f"✅ Completed. Actual time: {format_duration(test_actual_duration)}"
                )

                if i < len(matrix):
                    self.logger.debug(
                        f"Cooling down for {cooldown_s} seconds before next test..."
                    )
                    time.sleep(cooldown_s)

        except KeyboardInterrupt:
            self.logger.warning("\n[!] Tests cancelled by user (Ctrl+C).")
        finally:
            self.control_plane.disconnect()

            total_matrix_s = time.perf_counter() - total_matrix_start
            self.logger.info("=" * ROW_SEP_LEN)
            self.logger.info(
                f"📊 END OF TEST MATRIX | actual time: {format_duration(total_matrix_s)}"
            )
            self.logger.info("=" * ROW_SEP_LEN)

    # =========================================================================
    # SCHEDULE AND TABLE PRINTING
    # =========================================================================

    def _print_schedule(self, matrix: list[TestConfig], cooldown_s: float) -> None:
        now = datetime.now()
        current_time = now
        total_duration = 0.0

        ROW_SEP_LEN = 74

        schedule_rows = []

        for config in matrix:
            tx_s = config.packet_count / config.frequency_hz
            overhead = 1.0
            test_total_s = tx_s + overhead + cooldown_s

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
        self.logger.info(f"Router topology:\t\t{matrix[0].router_topology.value}")
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
    # SINGLE TEST EXECUTION
    # =========================================================================

    def _run_single_test(self, config: TestConfig, output_csv: str) -> None:
        total_loop_start = time.perf_counter()
        theoretical_tx_s = config.packet_count / config.frequency_hz

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
            self._handle_error(config, "ERR_START", output_csv)
            return

        # 4. Data Transmission with timing
        tx_records = []
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
        except Exception as e:
            self.logger.error(f"[!] Critical error during transmission: {e}")
            self._handle_error(config, f"ERR_DATA_PLANE: {e}", output_csv)
            return
        finally:
            data_plane.disconnect()

        # 5. Closing and fetching results from Control Plane
        self.control_plane.send_command("STOP", expected_ack="ACK_STOP")
        rx_records, actual_fetch_s = self._fetch_logs()

        # 6. Data Join
        if not rx_records:
            extra_data = {"time_tx_actual": actual_tx_s, "time_fetch": actual_fetch_s}
            self._handle_error(config, "NO_DATA", output_csv, **extra_data)
            return

        df_tx = pd.DataFrame(tx_records)  # [packet_id, pc_tx_ts]
        df_rx = pd.DataFrame(rx_records)  # [packet_id, esp_rx_ts]

        if not df_rx.empty:
            df_rx["rx_seq"] = df_rx.index
        else:
            df_rx["rx_seq"] = []

        # Outer Join
        df_merged = pd.merge(df_tx, df_rx, on="packet_id", how="outer")

        df_merged.sort_values(by="packet_id", inplace=True)
        df_merged.reset_index(drop=True, inplace=True)

        # 7. Analysis
        self._analyze_and_save(
            config=config,
            records_df=df_merged,
            output_csv=output_csv,
            time_data=(total_loop_start, theoretical_tx_s, actual_tx_s, actual_fetch_s),
        )

    # =========================================================================
    # HELPER METHODS FOR TEST EXECUTION
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

    def _analyze_and_save(
        self,
        config: TestConfig,
        records_df: pd.DataFrame,
        output_csv: str,
        time_data: tuple,
    ) -> None:
        total_loop_start, theoretical_tx_s, actual_tx_s, actual_fetch_s = time_data
        analyzer = DownlinkAnalyzer(
            payload_size_bytes=config.payload_size_bytes,
            frequency_hz=config.frequency_hz,
        )

        try:
            metrics = analyzer.calculate_all_metrics(
                records_df, total_sent=config.packet_count
            )
            total_loop_s = time.perf_counter() - total_loop_start

            result_row = self._flatten_metrics(config, metrics)
            result_row.update(
                {
                    "engine_time_tx_theory": theoretical_tx_s,
                    "engine_time_tx_actual": actual_tx_s,
                    "engine_time_fetch": actual_fetch_s,
                    "engine_time_total_loop": total_loop_s,
                }
            )

            self._save_to_csv(result_row, output_csv)

            self.logger.info(
                f"[+] OK. PDR: {metrics.pdr.ratio_percent}% | Jitter CV: {metrics.jitter.cv_percent:.2f}% | "
                f"Loop: {format_duration(total_loop_s)}"
            )

        except Exception as e:
            self.logger.error(f"\t[!] Error analyzing data: {e}")
            self._handle_error(config, f"ERR_ANALYZE: {e}", output_csv)

    def _handle_error(
        self, config: TestConfig, status: str, output_csv: str, **kwargs
    ) -> None:
        row = self._create_empty_row(config, status)
        row.update(kwargs)
        self._save_to_csv(row, output_csv)

    def _flatten_metrics(
        self, config: TestConfig, m: DownlinkMetrics
    ) -> dict[str, Any]:
        return {
            "router_topology": config.router_topology.value,
            "protocol": config.protocol.value,
            "freq_hz": config.frequency_hz,
            "status": "OK",
            "payload_b": config.payload_size_bytes,
            "expected_cnt": config.packet_count,
            # PDR
            "pdr_ratio_percent": m.pdr.ratio_percent,
            "pdr_expected": m.pdr.total_expected,
            "pdr_received": m.pdr.unique_received,
            "pdr_lost": m.pdr.lost_count,
            "pdr_mac_dups": m.pdr.mac_duplicates_count,
            "pdr_ghost_dups": m.pdr.ghost_duplicates_count,
            # Jitter
            "jitter_expected_iat_us": m.jitter.expected_iat_us,
            "jitter_mean_iat_us": m.jitter.mean_us,
            "jitter_err_iat_us": m.jitter.mean_error_us,
            "jitter_std_us": m.jitter.std_us,
            "jitter_cv_percent": m.jitter.cv_percent,
            "jitter_max_iat_us": m.jitter.max_us,
            "jitter_min_iat_us": m.jitter.min_us,
            "jitter_max_iat_dev_us": m.jitter.max_deviation_us,
            "jitter_min_iat_dev_us": m.jitter.min_deviation_us,
            # Burst Loss
            "burst_total_events": m.burst_loss.total_burst_events,
            "burst_max_len": m.burst_loss.max_burst_length,
            "burst_max_blackout_ms": m.burst_loss.max_blackout_time_ms,
            "burst_events": m.burst_loss.burst_events,
            # Goodput
            "goodput_bytes_sec": m.goodput.bytes_per_sec,
            "goodput_efficiency_percent": m.goodput.efficiency_percent,
            "goodput_kbps": m.goodput.kilobytes_per_sec,
            "goodput_mbps": m.goodput.megabits_per_sec,
            # Out of Order
            "ooo_count": m.out_of_order.total_ooo_count,
            "ooo_max_dist": m.out_of_order.max_id_displacement,
            "ooo_events": m.out_of_order.ooo_ids,
            # Timing
            "timing_drift_ppm": m.timing_trends.clock_drift_ppm,
            "timing_max_bloat_us": m.timing_trends.max_queuing_delay_us,
            "timing_avg_bloat_us": m.timing_trends.avg_queuing_delay_us,
            "timing_bloat_percent": m.timing_trends.queuing_delay_percent,
            "timing_slope": m.timing_trends.trend_slope,
        }

    def _create_empty_row(self, config: TestConfig, status: str) -> dict[str, Any]:
        return {
            "router_topology": config.router_topology.value,
            "protocol": config.protocol.value,
            "freq_hz": config.frequency_hz,
            "status": status,
        }

    def _save_to_csv(self, row_dict: dict[str, Any], filename: str) -> None:
        df = pd.DataFrame([row_dict])
        file_exists = os.path.isfile(filename)
        df.to_csv(filename, mode="a", index=False, header=not file_exists)
