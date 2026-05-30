from __future__ import annotations

import json
import sys
import tempfile
import unittest
import csv
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import futures_bps_false_negative_revival as revival  # noqa: E402


class FuturesBpsFalseNegativeRevivalTests(unittest.TestCase):
    def classify(self, row: dict) -> dict:
        result = revival.classify_row(row, source_file=Path("gate.json"))
        assert result is not None
        return result

    def test_classifies_bps_stress_false_negative_recheck(self) -> None:
        row = {
            "label": "NQ/1m/gross_between_real_cost_and_5bps",
            "symbol": "NQ",
            "trade_count": 100,
            "raw_total_profit_pct": 0.8,
            "representative_entry_price": 15000,
            "5bps_per_side_total_profit_pct": -9.2,
        }

        classified = self.classify(row)

        self.assertEqual(classified["classification"], "bps_stress_false_negative_recheck")
        self.assertGreater(classified["instrument_all_in_total_profit_pct"], 0.0)
        self.assertLess(classified["stress_5bps_side_total_profit_pct"], 0.0)
        self.assertFalse(classified["promotion_allowed"])
        self.assertFalse(classified["trade_usable"])

    def test_keeps_zero_edge_churn_dead_under_realistic_cost(self) -> None:
        row = {
            "label": "NQ/1m/highfreq_churn",
            "symbol": "NQ",
            "trade_count": 26304,
            "raw_total_profit_pct": 8.52,
            "representative_entry_price": 15000,
        }

        classified = self.classify(row)

        self.assertEqual(classified["classification"], "zero_edge_churn_not_rescued_by_realistic_cost")
        self.assertAlmostEqual(classified["gross_edge_bps_per_trade"], 0.032391, places=5)
        self.assertLess(classified["instrument_all_in_total_profit_pct"], 0.0)
        self.assertLess(classified["instrument_fee_only_total_profit_pct"], 0.0)

    def test_verified_realistic_survivor_that_also_beats_stress_is_not_false_negative(self) -> None:
        row = {
            "label": "NQ/1h/large_move_low_turnover",
            "symbol": "NQ",
            "trade_count": 20,
            "raw_total_profit_pct": 4.0,
            "representative_entry_price": 15000,
        }

        classified = self.classify(row)

        self.assertEqual(classified["classification"], "large_move_low_turnover_cost_negligible")
        self.assertGreater(classified["stress_5bps_side_total_profit_pct"], 0.0)

    def test_unverified_root_is_not_rehabilitated(self) -> None:
        row = {
            "label": "XAU/1m/alias_without_verified_contract",
            "symbol": "XAU",
            "trade_count": 10,
            "raw_total_profit_pct": 2.0,
        }

        classified = self.classify(row)

        self.assertEqual(classified["classification"], "cost_model_unverified")
        self.assertEqual(classified["cost_model_status"], "default_assumption_unverified")

    def test_recovers_gross_from_negative_5bps_stress_when_raw_missing(self) -> None:
        row = {
            "label": "NQ/1m/recover_from_stress_net",
            "symbol": "NQ",
            "trade_count": 100,
            "5bps_per_side_total_profit_pct": -9.2,
            "representative_entry_price": 15000,
        }

        classified = self.classify(row)

        self.assertAlmostEqual(classified["gross_total_profit_pct"], 0.8, places=6)
        self.assertEqual(classified["classification"], "bps_stress_false_negative_recheck")

    def test_audit_files_counts_rows_by_classification(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(
                json.dumps(
                    {
                        "rows": [
                            {
                                "label": "NQ/recheck",
                                "symbol": "NQ",
                                "trade_count": 100,
                                "raw_total_profit_pct": 0.8,
                                "representative_entry_price": 15000,
                            },
                            {
                                "label": "NQ/churn",
                                "symbol": "NQ",
                                "trade_count": 26304,
                                "raw_total_profit_pct": 8.52,
                                "representative_entry_price": 15000,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            report = revival.audit_files([path])

        self.assertEqual(report["revival_recheck_count"], 1)
        self.assertEqual(report["zero_edge_churn_count"], 1)
        self.assertFalse(report["promotion_allowed"])
        self.assertFalse(report["trade_usable"])

    def test_artifact_files_includes_autoquant_clean_rows_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            summaries = root / "aq" / "summaries"
            summaries.mkdir(parents=True)
            csv_path = summaries / "autoquant_clean_1m_rows.csv"
            csv_path.write_text("symbol,factor_id,trade_count,raw_total_profit_pct,5bps_per_side_total_profit_pct\n", encoding="utf-8")

            files = revival.artifact_files([root])

        self.assertIn(csv_path, files)

    def test_audit_files_reads_csv_row_level_gate_packets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "autoquant_clean_1m_rows.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "symbol",
                        "factor_id",
                        "trade_count",
                        "raw_total_profit_pct",
                        "5bps_per_side_total_profit_pct",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "symbol": "NQ",
                        "factor_id": "nq_csv_false_negative",
                        "trade_count": "100",
                        "raw_total_profit_pct": "0.8",
                        "5bps_per_side_total_profit_pct": "-9.2",
                    }
                )

            report = revival.audit_files([path])

        self.assertEqual(report["revival_recheck_count"], 1)
        self.assertEqual(report["revival_recheck_candidates"][0]["label"], "nq_csv_false_negative")

    def test_reads_nested_terminal_window_summaries_with_inherited_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(
                json.dumps(
                    {
                        "factor_id": "nq_compound_v1",
                        "branch_path": "HtfTrend -> FixedRrrBracket",
                        "market_product_symbol_origin_tf": "US index futures / NQ / 1m",
                        "full_window": {
                            "n_distinct_trades": 564,
                            "raw_total_ret_pct": 203.9751,
                            "net5bps_total_ret_pct": 147.5751,
                        },
                    }
                ),
                encoding="utf-8",
            )

            report = revival.audit_files([path])

        self.assertEqual(report["candidate_rows_classified"], 1)
        row = report["rows"][0]
        self.assertEqual(row["label"], "nq_compound_v1")
        self.assertEqual(row["symbol_root"], "NQ")
        self.assertEqual(row["classification"], "large_move_low_turnover_cost_negligible")

    def test_directory_scan_includes_highfreq_csv_and_classifies_zero_edge_churn(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            csv_path = root / "materials" / "highfreq_20_to_800_per_day_rows.csv"
            csv_path.parent.mkdir(parents=True)
            with csv_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["symbol", "family", "trades", "gross_total_pct", "net_5bps_total_pct"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "symbol": "NQ",
                        "family": "MicroburstContinuation",
                        "trades": "26304",
                        "gross_total_pct": "8.52",
                        "net_5bps_total_pct": "-2621.88",
                    }
                )

            files = revival.artifact_files([root])
            report = revival.audit_files(files)

        self.assertIn(csv_path, files)
        self.assertEqual(report["zero_edge_churn_count"], 1)
        row = report["rows"][0]
        self.assertEqual(row["classification"], "zero_edge_churn_not_rescued_by_realistic_cost")
        self.assertAlmostEqual(row["gross_edge_bps_per_trade"], 0.032391, places=5)


if __name__ == "__main__":
    unittest.main()
