from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import futures_real_cost_rescue_audit as audit  # noqa: E402


class FuturesRealCostRescueAuditTests(unittest.TestCase):
    def test_strict_rescue_when_instrument_cost_positive_but_5bps_negative(self) -> None:
        row = audit.normalize_row(
            {
                "factor_id": "tomac_nq_repriced_30m_v1",
                "symbol": "NQ",
                "timeframe": "30m",
                "trade_count": 462,
                "instrument_cost_total_ret_pct": 13.01,
                "5bps_per_side_total_profit_pct": -30.26,
                "session_scope": "ETH/full_retained_session",
                "rth_filter_applied": False,
                "eth_full_retained_session_evidence": True,
                "minimum_trade_sample_floor_met": True,
                "density_target_1_to_3_per_day": True,
            },
            "artifact.json",
            "top_rows",
            0,
        )

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.rescue_class, "rescued_for_exact_aq")
        self.assertTrue(row.survives_instrument_cost)
        self.assertFalse(row.survives_legacy_fixed_cost)

    def test_reprice_replay_needed_when_old_artifact_has_no_instrument_cost(self) -> None:
        row = audit.normalize_row(
            {
                "factor_id": "tomac_nq_old_gate1_v1",
                "symbol": "NQ",
                "timeframe": "5m",
                "trade_count": 859,
                "0bps_per_side_total_profit_pct": 11.25,
                "5bps_per_side_total_profit_pct": -74.64,
                "session_scope": "ETH/full_retained_session_screen_from_local_TOMAC_cache",
                "rth_filter_applied": "False",
                "decision": "reject_5bps_economics",
            },
            "screen_rows.csv",
            "csv",
            3,
        )

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.rescue_class, "needs_reprice_replay")
        self.assertIsNone(row.instrument_cost_total_pct)
        self.assertFalse(row.survives_legacy_fixed_cost)

    def test_fee_positive_density_failed_rows_are_blocked_not_exact_rescued(self) -> None:
        row = audit.normalize_row(
            {
                "factor_id": "tomac_nq_sparse_real_cost_positive_v1",
                "symbol": "NQ",
                "timeframe": "1h",
                "trade_count": 275,
                "instrument_cost_total_ret_pct": 14.22,
                "5bps_per_side_total_profit_pct": -11.52,
                "session_scope": "ETH/full_retained_session",
                "rth_filter_applied": False,
                "eth_full_retained_session_evidence": True,
                "minimum_trade_sample_floor_met": True,
                "density_target_1_to_3_per_day": False,
            },
            "artifact.json",
            "top_rows",
            2,
        )

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.rescue_class, "fee_cleared_but_blocked_non_cost")
        self.assertTrue(row.survives_instrument_cost)
        self.assertFalse(row.survives_legacy_fixed_cost)
        self.assertIn("density_floor_not_met", row.reason_codes)

    def test_density_floor_met_alias_allows_ledger_rescue(self) -> None:
        row = audit.normalize_row(
            {
                "factor_id": "tomac_nq_ledger_density_alias_v1",
                "symbol": "NQ",
                "timeframe": "30m",
                "trade_count": 462,
                "instrument_cost_total_ret_pct": 13.01,
                "5bps_per_side_total_profit_pct": -30.26,
                "session_scope": "ETH/full_retained_session",
                "rth_filter_applied": "False",
                "eth_full_retained_session_evidence": "True",
                "minimum_trade_sample_floor_met": "True",
                "density_floor_met": "True",
                "positive_years": "4",
                "years": "5",
            },
            "ledger.csv",
            "csv",
            0,
        )

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.rescue_class, "rescued_for_exact_aq")

    def test_fee_positive_weak_year_coverage_is_blocked_not_exact_rescued(self) -> None:
        row = audit.normalize_row(
            {
                "factor_id": "tomac_nq_weak_years_v1",
                "symbol": "NQ",
                "timeframe": "30m",
                "trade_count": 428,
                "instrument_cost_total_ret_pct": 8.51,
                "5bps_per_side_total_profit_pct": -31.63,
                "session_scope": "ETH/full_retained_session",
                "rth_filter_applied": "False",
                "eth_full_retained_session_evidence": "True",
                "minimum_trade_sample_floor_met": "True",
                "density_floor_met": "True",
                "positive_years": "2",
                "years": "5",
            },
            "blocked.csv",
            "csv",
            1,
        )

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.rescue_class, "fee_cleared_but_blocked_non_cost")
        self.assertIn("positive_year_coverage_too_weak_or_missing", row.reason_codes)

    def test_report_separates_fee_cleared_blocked_rows_from_exact_rescue_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "screen_rows.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "symbol",
                        "factor_id",
                        "trade_count",
                        "instrument_cost_total_ret_pct",
                        "5bps_per_side_total_profit_pct",
                        "session_scope",
                        "rth_filter_applied",
                        "eth_full_retained_session_evidence",
                        "minimum_trade_sample_floor_met",
                        "density_target_1_to_3_per_day",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "symbol": "NQ",
                        "factor_id": "tomac_nq_fee_cleared_sparse_v1",
                        "trade_count": "252",
                        "instrument_cost_total_ret_pct": "20.116386",
                        "5bps_per_side_total_profit_pct": "-3.538685",
                        "session_scope": "ETH/full_retained_session",
                        "rth_filter_applied": "False",
                        "eth_full_retained_session_evidence": "True",
                        "minimum_trade_sample_floor_met": "True",
                        "density_target_1_to_3_per_day": "False",
                    }
                )

            report = audit.build_report([source])

        self.assertEqual(report["strict_rescue_count"], 0)
        self.assertEqual(report["fee_cleared_but_blocked_count"], 1)
        self.assertEqual(report["class_counts"], {"fee_cleared_but_blocked_non_cost": 1})
        self.assertEqual(report["other_class_count"], 0)
        self.assertEqual(
            report["fee_cleared_but_blocked"][0]["factor_id"],
            "tomac_nq_fee_cleared_sparse_v1",
        )

    def test_cost_negative_rows_are_not_rescued(self) -> None:
        row = audit.normalize_row(
            {
                "factor_id": "tomac_6e_bad_v1",
                "symbol": "6E",
                "timeframe": "1m",
                "trade_count": 683,
                "gross_total_profit_pct": -2.95,
                "instrument_cost_total_profit_pct": -12.64,
                "5bps_per_side_total_profit_pct": -71.25,
                "session_scope": "ETH/full_retained_session",
                "rth_filter_applied": False,
            },
            "bad.csv",
            "csv",
            1,
        )

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.rescue_class, "not_rescued_cost_negative")

    def test_real_cost_positive_without_old_cost_wall_evidence_is_not_rescued(self) -> None:
        row = audit.normalize_row(
            {
                "factor_id": "tomac_nq_real_cost_positive_no_legacy_wall_v1",
                "symbol": "NQ",
                "trade_count": 120,
                "instrument_cost_total_profit_pct": 3.2,
                "session_scope": "ETH/full_retained_session",
                "rth_filter_applied": False,
                "minimum_trade_sample_floor_met": True,
                "density_target_1_to_3_per_day": True,
            },
            "positive_without_legacy_wall.json",
            "top_rows",
            0,
        )

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.rescue_class, "not_rescued_no_cost_wall_evidence")

    def test_eth_replay_rows_are_reported_not_silently_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "screen_rows.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "symbol",
                        "factor_id",
                        "trade_count",
                        "instrument_cost_total_ret_pct",
                        "5bps_per_side_total_profit_pct",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "symbol": "NQ",
                        "factor_id": "tomac_nq_missing_eth_evidence_v1",
                        "trade_count": "518",
                        "instrument_cost_total_ret_pct": "7.744689",
                        "5bps_per_side_total_profit_pct": "-41.92",
                    }
                )

            report = audit.build_report([source])

        self.assertEqual(report["row_count"], 1)
        self.assertEqual(report["class_counts"], {"needs_eth_full_session_replay": 1})
        self.assertEqual(report["strict_rescue_count"], 0)
        self.assertEqual(report["needs_eth_full_session_replay_count"], 1)
        self.assertEqual(
            report["needs_eth_full_session_replay"][0]["factor_id"],
            "tomac_nq_missing_eth_evidence_v1",
        )

    def test_already_survives_stress_rows_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "screen_rows.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "symbol",
                        "factor_id",
                        "trade_count",
                        "instrument_cost_total_ret_pct",
                        "5bps_per_side_total_profit_pct",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "symbol": "ES",
                        "factor_id": "tomac_es_not_fee_false_negative_v1",
                        "trade_count": "20",
                        "instrument_cost_total_ret_pct": "2.25",
                        "5bps_per_side_total_profit_pct": "0.48",
                    }
                )

            report = audit.build_report([source])

        self.assertEqual(report["class_counts"], {"already_survives_legacy_fixed_cost": 1})
        self.assertEqual(report["already_survives_legacy_fixed_cost_count"], 1)
        self.assertEqual(report["already_survives_legacy_fixed_cost"][0]["factor_id"], "tomac_es_not_fee_false_negative_v1")

    def test_build_report_dedupes_strict_rescues_and_writes_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "screen_rows.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "symbol",
                        "factor_id",
                        "timeframe",
                        "trade_count",
                        "instrument_cost_total_ret_pct",
                        "5bps_per_side_total_profit_pct",
                        "session_scope",
                        "rth_filter_applied",
                        "eth_full_retained_session_evidence",
                        "minimum_trade_sample_floor_met",
                        "density_target_1_to_3_per_day",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "symbol": "NQ",
                        "factor_id": "tomac_nq_repriced_30m_v1",
                        "timeframe": "30m",
                        "trade_count": 462,
                        "instrument_cost_total_ret_pct": 13.01,
                        "5bps_per_side_total_profit_pct": -30.26,
                        "session_scope": "ETH/full_retained_session",
                        "rth_filter_applied": "False",
                        "eth_full_retained_session_evidence": "True",
                        "minimum_trade_sample_floor_met": "True",
                        "density_target_1_to_3_per_day": "True",
                    }
                )
                writer.writerow(
                    {
                        "symbol": "NQ",
                        "factor_id": "tomac_nq_repriced_30m_v1",
                        "timeframe": "30m",
                        "trade_count": 460,
                        "instrument_cost_total_ret_pct": 12.5,
                        "5bps_per_side_total_profit_pct": -30.0,
                        "session_scope": "ETH/full_retained_session",
                        "rth_filter_applied": "False",
                        "eth_full_retained_session_evidence": "True",
                        "minimum_trade_sample_floor_met": "True",
                        "density_target_1_to_3_per_day": "True",
                    }
                )
            report_path = root / "report.json"
            csv_path = root / "queue.csv"

            report = audit.build_report([source], report_path=report_path, csv_path=csv_path)

            self.assertEqual(report["strict_rescue_count"], 1)
            self.assertEqual(report["rescued_for_exact_aq"][0]["factor_id"], "tomac_nq_repriced_30m_v1")
            self.assertTrue(report_path.exists())
            self.assertTrue(csv_path.exists())


if __name__ == "__main__":
    unittest.main()
