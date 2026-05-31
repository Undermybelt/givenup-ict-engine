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
        self.assertLess(classified["legacy_wall_total_profit_pct"], 0.0)
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
        self.assertGreater(classified["legacy_wall_total_profit_pct"], 0.0)

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

    def test_recovers_gross_from_negative_2bps_stress_when_raw_missing(self) -> None:
        row = {
            "label": "NQ/1m/recover_from_2bps_stress_net",
            "symbol": "NQ",
            "trade_count": 100,
            "net_2bps_total_pct": -3.2,
            "representative_entry_price": 15000,
        }

        classified = self.classify(row)

        self.assertAlmostEqual(classified["gross_total_profit_pct"], 0.8, places=6)
        self.assertEqual(classified["legacy_wall_total_profit_pct"], -3.2)
        self.assertEqual(classified["legacy_wall_basis_points_per_side"], 2.0)
        self.assertEqual(classified["legacy_wall_source_key"], "net_2bps_total_pct")
        self.assertEqual(classified["classification"], "bps_stress_false_negative_recheck")

    def test_explicit_10bps_wall_can_rescue_even_when_default_5bps_wall_would_survive(self) -> None:
        row = {
            "label": "NQ/1h/killed_by_10bps_wall_only",
            "symbol": "NQ",
            "trade_count": 100,
            "raw_total_profit_pct": 15.0,
            "10bps_per_side_total_profit_pct": -5.0,
            "representative_entry_price": 15000,
        }

        classified = self.classify(row)

        self.assertEqual(classified["classification"], "bps_stress_false_negative_recheck")
        self.assertEqual(classified["legacy_wall_total_profit_pct"], -5.0)
        self.assertEqual(classified["legacy_wall_basis_points_per_side"], 10.0)
        self.assertGreater(classified["instrument_all_in_total_profit_pct"], 0.0)

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

    def test_false_negative_rows_preserve_session_and_trade_sample_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(
                json.dumps(
                    {
                        "top_rows": [
                            {
                                "symbol": "NQ",
                                "factor_id": "tomac_nq_reaccel_30m_v1",
                                "branch_path": "TrendExpansion -> PullbackReacceleration -> tomac_nq_reaccel_30m_v1",
                                "timeframe": "30m",
                                "variant": "tight_vol",
                                "trade_count": 1902,
                                "trades_per_day": 1.22,
                                "raw_total_profit_pct": 85.860575,
                                "stress_5bps_total_pct": -104.339425,
                                "session_scope": "ETH/full_retained_session",
                                "rth_filter_applied": False,
                                "outside_rth_rows": 36576,
                                "eth_full_retained_session_evidence": True,
                                "positive_years": 4,
                                "years": 5,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            report = revival.audit_files([path])

        self.assertEqual(report["revival_recheck_count"], 1)
        self.assertEqual(report["unique_revival_recheck_count"], 1)
        row = report["revival_recheck_candidates"][0]
        self.assertEqual(row["factor_id"], "tomac_nq_reaccel_30m_v1")
        self.assertEqual(row["timeframe"], "30m")
        self.assertEqual(row["variant"], "tight_vol")
        self.assertEqual(row["session_scope"], "ETH/full_retained_session")
        self.assertFalse(row["rth_filter_applied"])
        self.assertTrue(row["eth_full_retained_session_evidence"])
        self.assertTrue(row["minimum_trade_sample_floor_met"])
        self.assertNotIn("density_target_1_to_3_per_day", row)
        self.assertTrue(row["year_coverage_ok"])

    def test_unique_false_negative_output_dedupes_and_preserves_gate_fields(self) -> None:
        rows = [
            {
                "label": "nq_reaccel",
                "source_file": "/tmp/root/materials/leaderboard.csv",
                "symbol_root": "NQ",
                "factor_id": "nq_reaccel_30m_v1",
                "timeframe": "30m",
                "variant": "tight_vol",
                "classification": "bps_stress_false_negative_recheck",
                "trade_count": 1902,
                "gross_total_profit_pct": 85.860575,
                "legacy_wall_total_profit_pct": -104.339425,
                "instrument_all_in_total_profit_pct": 73.497575,
                "session_scope": "ETH/full_retained_session",
                "rth_filter_applied": False,
                "eth_full_retained_session_evidence": True,
                "density_target_1_to_3_per_day": True,
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
            {
                "label": "nq_reaccel",
                "source_file": "/tmp/root/checks/terminal_metrics.json",
                "symbol_root": "NQ",
                "factor_id": "nq_reaccel_30m_v1",
                "timeframe": "30m",
                "variant": "tight_vol",
                "classification": "bps_stress_false_negative_recheck",
                "trade_count": 1902,
                "gross_total_profit_pct": 85.860575,
                "legacy_wall_total_profit_pct": -104.339425,
                "instrument_all_in_total_profit_pct": 73.497575,
                "session_scope": "ETH/full_retained_session",
                "rth_filter_applied": False,
                "eth_full_retained_session_evidence": True,
                "density_target_1_to_3_per_day": True,
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            },
        ]

        unique = revival.unique_false_negative_candidates(rows)

        self.assertEqual(len(unique), 1)
        self.assertEqual(unique[0]["source_file"], "/tmp/root/checks/terminal_metrics.json")
        self.assertEqual(unique[0]["duplicate_source_count"], 2)
        self.assertEqual(unique[0]["session_scope"], "ETH/full_retained_session")
        self.assertTrue(unique[0]["eth_full_retained_session_evidence"])
        self.assertFalse(unique[0]["promotion_allowed"])

    def test_main_writes_unique_false_negative_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "terminal_metrics.json"
            output = root / "unique.csv"
            source.write_text(
                json.dumps(
                    {
                        "top_rows": [
                            {
                                "symbol": "NQ",
                                "factor_id": "nq_reaccel_30m_v1",
                                "timeframe": "30m",
                                "trade_count": 100,
                                "raw_total_profit_pct": 0.8,
                                "stress_5bps_total_pct": -9.2,
                                "session_scope": "ETH/full_retained_session",
                                "rth_filter_applied": False,
                                "eth_full_retained_session_evidence": True,
                                "trades_per_day": 0.1,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            exit_code = revival.main([str(source), "--output-unique-csv", str(output)])

            with output.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(exit_code, 0)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["factor_id"], "nq_reaccel_30m_v1")
        self.assertEqual(rows[0]["session_scope"], "ETH/full_retained_session")
        self.assertEqual(rows[0]["trades_per_day"], "0.1")
        self.assertNotIn("density_target_1_to_3_per_day", rows[0])

    def test_audit_files_reads_exact_replay_queue_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "exact_replay_rescue_queue.json"
            path.write_text(
                json.dumps(
                    {
                        "exact_replay_queue": [
                            {
                                "factor_id": "tomac_nq_fee_false_negative_v1",
                                "symbol": "NQ",
                                "timeframe": "30m",
                                "side": "short",
                                "trade_count": 462,
                                "gross_total_pct": 15.939886,
                                "stress_5bps_total_pct": -30.260114,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            report = revival.audit_files([path])

        self.assertEqual(report["revival_recheck_count"], 1)
        row = report["revival_recheck_candidates"][0]
        self.assertEqual(row["label"], "tomac_nq_fee_false_negative_v1")
        self.assertEqual(row["legacy_wall_total_profit_pct"], -30.260114)

    def test_directory_scan_includes_fee_rescue_judgment_ledger_materials(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path = root / "materials" / "fee_rescue_judgment_ledger.json"
            path.parent.mkdir(parents=True)
            path.write_text(
                json.dumps(
                    {
                        "rescued_for_exact_replay": [
                            {
                                "factor_id": "tomac_nq_judgment_ledger_false_negative_v1",
                                "symbol": "NQ",
                                "timeframe": "30m",
                                "side": "short",
                                "trade_count": 462,
                                "gross_total_pct": 15.939886,
                                "stress_5bps_total_pct": -30.260114,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            files = revival.artifact_files([root])
            report = revival.audit_files(files)

        self.assertIn(path, files)
        self.assertEqual(report["revival_recheck_count"], 1)
        self.assertEqual(
            report["revival_recheck_candidates"][0]["label"],
            "tomac_nq_judgment_ledger_false_negative_v1",
        )

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
