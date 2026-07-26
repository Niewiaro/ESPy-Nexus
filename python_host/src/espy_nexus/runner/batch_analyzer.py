import sqlite3
import pandas as pd
import numpy as np
import logging
import time
from typing import Any

from espy_nexus.pipeline.downlink import DownlinkAnalyzer

ROW_SEP_LEN = 74


class BatchAnalyzer:
    """
    Offline Data Pipeline (ETL) for processing HIL raw telemetry.
    Extracts data from local SQLite (DAQ), Transforms it using DownlinkAnalyzer,
    and Loads the summarized QoS metrics into an Analytics SQLite DB and CSV.
    """

    def __init__(
        self,
        raw_db_path: str = "hil_raw_data.sqlite",
        analytics_db_path: str | None = "hil_analytics.sqlite",
        output_csv_path: str | None = "hil_analytics.csv",
        json_csv_path: str | None = "hil_analytics.json",
    ):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.raw_db_path = raw_db_path
        self.analytics_db_path = analytics_db_path
        self.output_csv_path = output_csv_path
        self.json_csv_path = json_csv_path

        if not self.raw_db_path:
            self.logger.critical("Raw DB path is not set. Exiting.")
            raise ValueError("Raw DB path must be provided.")

        if (
            not self.output_csv_path
            and not self.analytics_db_path
            and not self.json_csv_path
        ):
            self.logger.critical("All output paths are None. No results will be saved.")
            raise ValueError(
                "At least one of output_csv_path, analytics_db_path, or json_csv_path must be provided."
            )

        self._init_analytics_db()

    def run_pipeline(self) -> None:
        """Executes the full ETL pipeline."""
        total_start = time.perf_counter()

        self.logger.info("=" * ROW_SEP_LEN)
        self.logger.info("🚀 STARTING BATCH ANALYSIS (ETL PIPELINE)")
        self.logger.info("=" * ROW_SEP_LEN)

        # 1. EXTRACT: fetch successful tests from the raw DB
        tests_df = self._extract_successful_tests()
        if tests_df is None or tests_df.empty:
            self.logger.warning("[!] No successful tests found to process. Exiting.")
            return

        self.logger.info(
            f"Found {len(tests_df)} successful test runs. Starting sequential processing..."
        )

        # 2. TRANSFORM: process each test and calculate metrics
        all_results = self._process_tests(tests_df)

        # 3. LOAD: Save results
        self._load_results(all_results)

        total_s = time.perf_counter() - total_start
        self.logger.info("=" * ROW_SEP_LEN)
        self.logger.info(f"✅ BATCH PROCESSING COMPLETE | Total time: {total_s:.2f} s")
        self.logger.info("=" * ROW_SEP_LEN)

    # =========================================================================
    # EXTRACT
    # =========================================================================

    def _extract_successful_tests(self) -> pd.DataFrame | None:
        """Fetch tests with status 'OK'."""
        try:
            with sqlite3.connect(self.raw_db_path) as conn:
                query = "SELECT * FROM test_runs WHERE status = 'OK'"
                return pd.read_sql_query(query, conn)
        except sqlite3.Error as e:
            self.logger.error(f"Database connection error ({self.raw_db_path}): {e}")
            return None
        except pd.errors.DatabaseError:
            self.logger.error(
                f"Table 'test_runs' does not exist in {self.raw_db_path}."
            )
            return None

    def _extract_raw_packets(self, test_id: int) -> pd.DataFrame:
        """Extract raw packets for a specific test."""
        try:
            with sqlite3.connect(self.raw_db_path) as conn:
                query = f"""
                    SELECT packet_id, pc_tx_ts_us, esp_rx_ts_us 
                    FROM raw_packets 
                    WHERE test_id = {test_id} 
                    ORDER BY packet_id
                """
                df = pd.read_sql_query(query, conn)

                df.rename(
                    columns={"pc_tx_ts_us": "pc_tx_ts", "esp_rx_ts_us": "esp_rx_ts"},
                    inplace=True,
                )

                return df
        except Exception as e:
            self.logger.error(f"Failed to extract packets for test {test_id}: {e}")
            return pd.DataFrame()

    # =========================================================================
    # TRANSFORM
    # =========================================================================

    def _process_tests(self, tests_df: pd.DataFrame) -> list[dict[str, Any]]:
        """Process each test and calculate metrics."""
        results = []

        for _, test_row in tests_df.iterrows():
            test_id = test_row["test_id"]
            protocol = test_row["protocol"]
            freq = test_row["freq_hz"]
            expected_cnt = test_row["expected_count"]
            payload_size = test_row["payload_size"]

            # Extract raw packets for this test
            raw_df = self._extract_raw_packets(test_id)
            if raw_df.empty:
                self.logger.warning(
                    f"Test {test_id:03d} | No packets found in DB. Skipping."
                )
                continue

            # Transform: Calculate metrics using DownlinkAnalyzer
            analyzer = DownlinkAnalyzer(
                payload_size_bytes=payload_size, frequency_hz=freq
            )

            try:
                metrics = analyzer.calculate_all_metrics(
                    raw_df, total_sent=expected_cnt
                )
                row_dict = self._flatten_metrics(test_row, metrics)
                results.append(row_dict)

                self.logger.info(
                    f"Test {test_id:03d} | {protocol:5s} | {freq:5d} Hz | {payload_size:5d} B -> "
                    f"PDR: {metrics.pdr.ratio_percent:5.1f}% | "
                    f"Bloat: {metrics.timing_trends.max_queuing_delay_us / 1000:7.1f} ms | "
                    f"Jitter CV: {metrics.jitter.cv_percent:5.1f}%"
                )
            except Exception as e:
                self.logger.error(
                    f"[X] Analysis failed for Test {test_id} ({protocol} | {freq} Hz | {payload_size} B): {e}"
                )

        return results

    def _flatten_metrics(self, test_row: pd.Series, metrics: Any) -> dict[str, Any]:
        freq_hz = float(test_row["freq_hz"])
        expected_cnt = float(test_row["expected_count"])
        theoretical_tx_s = expected_cnt / freq_hz if freq_hz > 0 else 0.0

        return {
            "test_id": test_row["test_id"],
            "router_topology": test_row["topology"],
            "protocol": test_row["protocol"],
            "freq_hz": test_row["freq_hz"],
            "status": test_row["status"],
            "payload_b": test_row["payload_size"],
            "expected_cnt": test_row["expected_count"],
            # PDR
            "pdr_ratio_percent": metrics.pdr.ratio_percent,
            "pdr_expected": metrics.pdr.total_expected,
            "pdr_received": metrics.pdr.unique_received,
            "pdr_lost": metrics.pdr.lost_count,
            "pdr_mac_dups": metrics.pdr.mac_duplicates_count,
            "pdr_ghost_dups": metrics.pdr.ghost_duplicates_count,
            # Jitter
            "jitter_expected_iat_us": metrics.jitter.expected_iat_us,
            "jitter_mean_iat_us": metrics.jitter.mean_us,
            "jitter_err_iat_us": metrics.jitter.mean_error_us,
            "jitter_std_us": metrics.jitter.std_us,
            "jitter_cv_percent": metrics.jitter.cv_percent,
            "jitter_max_iat_us": metrics.jitter.max_us,
            "jitter_min_iat_us": metrics.jitter.min_us,
            "jitter_max_iat_dev_us": metrics.jitter.max_deviation_us,
            "jitter_min_iat_dev_us": metrics.jitter.min_deviation_us,
            # Burst Loss
            "burst_total_events": metrics.burst_loss.total_burst_events,
            "burst_max_len": metrics.burst_loss.max_burst_length,
            "burst_max_blackout_ms": metrics.burst_loss.max_blackout_time_ms,
            "burst_events": str(
                metrics.burst_loss.burst_events
            ),  # JSON / Dict as string
            # Goodput
            "goodput_bytes_sec": metrics.goodput.bytes_per_sec,
            "goodput_efficiency_percent": metrics.goodput.efficiency_percent,
            "goodput_kbps": metrics.goodput.kilobytes_per_sec,
            "goodput_mbps": metrics.goodput.megabits_per_sec,
            # Out of Order
            "ooo_count": metrics.out_of_order.total_ooo_count,
            "ooo_max_dist": metrics.out_of_order.max_id_displacement,
            "ooo_events": str(metrics.out_of_order.ooo_ids),  # List as string
            # Timing Trends / Bloat
            "timing_drift_ppm": metrics.timing_trends.clock_drift_ppm,
            "timing_max_bloat_us": metrics.timing_trends.max_queuing_delay_us,
            "timing_avg_bloat_us": metrics.timing_trends.avg_queuing_delay_us,
            "timing_bloat_percent": metrics.timing_trends.queuing_delay_percent,
            "timing_slope": metrics.timing_trends.trend_slope,
            # Engine timing
            "engine_time_tx_theory": theoretical_tx_s,
            "engine_time_tx_actual": test_row["engine_time_tx_actual"],
            "engine_time_fetch": test_row["engine_time_fetch"],
            "engine_time_total_loop": test_row["engine_time_tx_actual"]
            + test_row["engine_time_fetch"],
        }

    # =========================================================================
    # LOAD
    # =========================================================================

    def _init_analytics_db(self) -> None:
        if self.analytics_db_path is None:
            self.logger.warning(
                "Analytics DB path is None. Results will not be saved to SQLite."
            )
            return

        try:
            with sqlite3.connect(self.analytics_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS test_results (
                        test_id INTEGER PRIMARY KEY,
                        router_topology TEXT,
                        protocol TEXT,
                        freq_hz INTEGER,
                        status TEXT,
                        payload_b INTEGER,
                        expected_cnt INTEGER,
                        
                        -- PDR
                        pdr_ratio_percent REAL,
                        pdr_expected INTEGER,
                        pdr_received INTEGER,
                        pdr_lost INTEGER,
                        pdr_mac_dups INTEGER,
                        pdr_ghost_dups INTEGER,
                        
                        -- Jitter
                        jitter_expected_iat_us REAL,
                        jitter_mean_iat_us REAL,
                        jitter_err_iat_us REAL,
                        jitter_std_us REAL,
                        jitter_cv_percent REAL,
                        jitter_max_iat_us REAL,
                        jitter_min_iat_us REAL,
                        jitter_max_iat_dev_us REAL,
                        jitter_min_iat_dev_us REAL,
                        
                        -- Burst Loss
                        burst_total_events INTEGER,
                        burst_max_len INTEGER,
                        burst_max_blackout_ms REAL,
                        burst_events TEXT,
                        
                        -- Goodput
                        goodput_bytes_sec REAL,
                        goodput_efficiency_percent REAL,
                        goodput_kbps REAL,
                        goodput_mbps REAL,
                        
                        -- Out of Order
                        ooo_count INTEGER,
                        ooo_max_dist INTEGER,
                        ooo_events TEXT,
                        
                        -- Timing Trends
                        timing_drift_ppm REAL,
                        timing_max_bloat_us REAL,
                        timing_avg_bloat_us REAL,
                        timing_bloat_percent REAL,
                        timing_slope REAL,
                        
                        -- Engine Diagnostics
                        engine_time_tx_theory REAL,
                        engine_time_tx_actual REAL,
                        engine_time_fetch REAL,
                        engine_time_total_loop REAL
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            self.logger.critical(f"Failed to initialize Analytics DB: {e}")
            raise

    def _load_results(self, all_results: list[dict[str, Any]]) -> None:
        """Saves the processed results to SQLite and/or CSV."""
        if not all_results:
            self.logger.warning("No results to save.")
            return

        df_final = pd.DataFrame(all_results)

        # SQLite
        if self.analytics_db_path is not None:
            try:
                with sqlite3.connect(self.analytics_db_path) as conn:
                    df_final.to_sql(
                        "test_results", conn, if_exists="replace", index=False
                    )
                    self.logger.info(
                        f"Loaded {len(df_final)} rows into SQLite DB: {self.analytics_db_path}"
                    )
            except sqlite3.Error as e:
                self.logger.error(f"Failed to save results to SQLite: {e}")

        # CSV
        if self.output_csv_path is not None:
            try:
                df_final.to_csv(self.output_csv_path, index=False)
                self.logger.info(
                    f"Loaded {len(df_final)} rows into CSV file: {self.output_csv_path}"
                )
            except Exception as e:
                self.logger.error(f"Failed to save results to CSV: {e}")

        # JSON
        if self.json_csv_path is not None:
            try:
                df_final_json = df_final.copy()
                df_final_json.drop(
                    columns=["ooo_events", "burst_events"], inplace=True
                )  # Drop complex columns
                df_final_json.to_json(self.json_csv_path, orient="records", indent=2)
                self.logger.info(
                    f"Loaded {len(df_final_json)} rows into JSON file: {self.json_csv_path}"
                )
            except Exception as e:
                self.logger.error(f"Failed to save results to JSON: {e}")


if __name__ == "__main__":
    analyzer_pipeline = BatchAnalyzer()
    analyzer_pipeline.run_pipeline()
