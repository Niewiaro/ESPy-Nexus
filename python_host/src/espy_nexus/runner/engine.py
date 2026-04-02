import time
import pandas as pd
import os
from typing import Any

from espy_nexus.core.config import TestConfig, Protocol
from espy_nexus.control_plane.serial_cp import SerialControlPlane
from espy_nexus.data_plane.serial_dp import SerialDataPlane
from espy_nexus.pipeline.downlink import DownlinkAnalyzer, DownlinkMetrics


def convert_seconds_to_formatted(seconds: float) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, remainder = divmod(remainder, 60)
    secs = int(remainder)
    millis = int((remainder - secs) * 1000)
    return f"{int(hours):02d}h {int(minutes):02d}m {secs:02d}s {millis:03d}ms"


class TestEngine:
    """
    Orchestrator executing a test matrix on hardware (Hardware-in-the-Loop).
    Manages control/data planes, analyzer, and exports results to CSV.
    """

    def __init__(self, port: str, baudrate: int):
        self.port = port
        self.baudrate = baudrate
        # Control plane always uses serial connection, independent of data protocol
        self.control_plane = SerialControlPlane(port=port, baudrate=baudrate)

    def run_matrix(
        self,
        matrix: list[TestConfig],
        output_csv: str = "matrix_results.csv",
        cooldown_s: float = 5,
    ) -> None:

        # calculate estimated duration for user information
        total_estimated_tx_time = sum(
            config.packet_count / config.frequency_hz for config in matrix
        )
        total_estimated_cooldown_time = len(matrix) * cooldown_s
        estimated_overhead = len(matrix) * 1.0

        total_estimated_s = (
            total_estimated_tx_time + total_estimated_cooldown_time + estimated_overhead
        )
        total_estimated_formatted = convert_seconds_to_formatted(total_estimated_s)

        print("=" * 60)
        print(f"⚙️ Lunching test matrix ({len(matrix)} testruns)")
        print(f"⏳ Estimated duration: {total_estimated_formatted}")
        print("=" * 60)
        total_matrix_start = time.perf_counter()

        try:
            self.control_plane.connect()

            for i, config in enumerate(matrix, 1):
                total_loop_start = time.perf_counter()

                print(
                    f"\n[{i}/{len(matrix)}] >>> {config.test_id} ({config.frequency_hz} Hz)"
                )

                theoretical_tx_s = config.packet_count / config.frequency_hz
                theoretical_tx_formatted = convert_seconds_to_formatted(
                    theoretical_tx_s
                )
                print(f"\t[Time] Theoretical: {theoretical_tx_formatted}")

                # Strategy pattern for data plane instantiation based on protocol
                if config.protocol == Protocol.SERIAL:
                    data_plane = SerialDataPlane(port=self.port, baudrate=self.baudrate)
                else:
                    print(f"\t[-] Unknown protocol: {config.protocol.value}. Skipping.")
                    continue

                # Negotiation and handshakes (Control Plane)
                if not self.control_plane.send_command(
                    f"START_{config.protocol.value}",
                    expected_ack=f"ACK_START_{config.protocol.value}",
                ):
                    print(
                        f"\t[-] ESP32 did not acknowledge start. Marking test as failed."
                    )
                    self._save_to_csv(
                        self._create_empty_row(config, "ERR_START"), output_csv
                    )
                    continue

                # Aggressive Data Transmission (Data Plane)
                actual_tx_start = time.perf_counter()

                data_plane.transmit(
                    packet_count=config.packet_count, frequency_hz=config.frequency_hz
                )

                actual_tx_end = time.perf_counter()
                actual_tx_s = actual_tx_end - actual_tx_start
                actual_tx_formatted = convert_seconds_to_formatted(actual_tx_s)
                print(f"\t[Time] Actual transmission: {actual_tx_formatted}")

                # Safe Shutdown (Control Plane)
                self.control_plane.send_command("STOP", expected_ack="ACK_STOP")

                # Get buffered logs (Control Plane)
                actual_fetch_start = time.perf_counter()

                records = self.control_plane.fetch_data()

                actual_fetch_end = time.perf_counter()
                actual_fetch_s = actual_fetch_end - actual_fetch_start
                actual_fetch_end_formatted = convert_seconds_to_formatted(
                    actual_fetch_s
                )
                print(f"\t[Time] Data fetch: {actual_fetch_end_formatted}")

                # Analyze
                if not records:
                    row = self._create_empty_row(config, "NO_DATA")
                    row.update(
                        {
                            "time_tx_actual": actual_tx_s,
                            "time_fetch": actual_fetch_s,
                        }
                    )
                    self._save_to_csv(row, output_csv)
                    continue

                df_raw = pd.DataFrame(records)
                analyzer = DownlinkAnalyzer(
                    payload_size_bytes=config.payload_size_bytes,
                    frequency_hz=config.frequency_hz,
                )

                try:
                    metrics = analyzer.calculate_all_metrics(
                        df_raw,
                        total_sent=config.packet_count,
                    )
                    total_loop_end = time.perf_counter()
                    total_loop_s = total_loop_end - total_loop_start
                    total_loop_formatted = convert_seconds_to_formatted(total_loop_s)

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

                    print(
                        f"\t[+] OK. PDR: {metrics.pdr.ratio_percent}% | Jitter CV: {metrics.jitter.cv_percent:.2f} % | "
                        f"Loop: {total_loop_formatted} (Tx: {actual_tx_formatted}, Fetch: {actual_fetch_end_formatted})"
                    )

                except Exception as e:
                    print(f"\t[!] Analyze error: {e}")
                    self._save_to_csv(
                        self._create_empty_row(config, f"ERR_ANALYZE: {e}"), output_csv
                    )

                time.sleep(cooldown_s)

        except KeyboardInterrupt:
            print("\n\t[!] Keyboard interrupt (Ctrl+C).")
        finally:
            self.control_plane.disconnect()

            total_matrix_end = time.perf_counter()
            total_matrix_s = total_matrix_end - total_matrix_start
            total_matrix_formatted = convert_seconds_to_formatted(total_matrix_s)

            print("\n" + "=" * 60)
            print(f"📊 End test matrix (took {total_matrix_formatted})")
            print("=" * 60)

    def _flatten_metrics(
        self, config: TestConfig, m: DownlinkMetrics
    ) -> dict[str, Any]:
        return {
            "test_id": config.test_id,
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
            "timing_max_bloat_us": m.timing_trends.max_bufferbloat_us,
            "timing_avg_bloat_us": m.timing_trends.avg_bufferbloat_us,
            "timing_bloat_percent": m.timing_trends.bufferbloat_percent,
            "timing_slope": m.timing_trends.trend_slope,
        }

    def _create_empty_row(self, config: TestConfig, status: str) -> dict[str, Any]:
        return {
            "test_id": config.test_id,
            "protocol": config.protocol.value,
            "freq_hz": config.frequency_hz,
            "status": status,
        }

    def _save_to_csv(self, row_dict: dict[str, Any], filename: str):
        df = pd.DataFrame([row_dict])
        file_exists = os.path.isfile(filename)
        df.to_csv(filename, mode="a", index=False, header=not file_exists)
