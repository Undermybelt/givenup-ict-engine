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

    def test_high_frequency_churn_with_tiny_gross_edge_is_not_reprice_replay(self) -> None:
        row = audit.normalize_row(
            {
                "factor_id": "tomac_nq_microburst_churn_v1",
                "symbol": "NQ",
                "timeframe": "1m",
                "trade_count": 26304,
                "gross_total_profit_pct": 8.52,
                "5bps_per_side_total_profit_pct": -2621.88,
                "representative_price": 15000,
                "session_scope": "ETH/full_retained_session",
                "rth_filter_applied": "False",
            },
            "highfreq_rows.csv",
            "csv",
            0,
        )

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.rescue_class, "not_rescued_zero_edge_churn_realistic_cost_negative")
        self.assertIn("gross_edge_below_realistic_all_in_cost", row.reason_codes)
        self.assertIsNone(row.instrument_cost_total_pct)
        self.assertFalse(row.survives_legacy_fixed_cost)

    def test_fee_positive_density_failed_rows_are_rescued_after_density_gate_removed(self) -> None:
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
        self.assertEqual(row.rescue_class, "rescued_for_exact_aq")
        self.assertTrue(row.survives_instrument_cost)
        self.assertFalse(row.survives_legacy_fixed_cost)
        self.assertNotIn("density_floor_not_met", row.reason_codes)

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

    def test_stress_5bps_total_pct_alias_allows_ledger_rescue(self) -> None:
        row = audit.normalize_row(
            {
                "factor_id": "tomac_nq_ledger_stress_alias_v1",
                "symbol": "NQ",
                "timeframe": "30m",
                "trade_count": "462.0",
                "instrument_cost_total_pct": "13.010348",
                "stress_5bps_total_pct": "-30.260114",
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
        self.assertEqual(row.legacy_fixed_cost_total_pct, -30.260114)
        self.assertFalse(row.survives_legacy_fixed_cost)
        self.assertEqual(row.rescue_class, "rescued_for_exact_aq")

    def test_2bps_total_profit_alias_is_old_fixed_cost_wall_evidence(self) -> None:
        row = audit.normalize_row(
            {
                "factor_id": "tomac_nq_ledger_2bps_alias_v1",
                "symbol": "NQ",
                "timeframe": "30m",
                "trade_count": "462",
                "instrument_cost_total_pct": "13.010348",
                "2bps_per_side_total_profit_pct": "-3.260114",
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
        self.assertEqual(row.legacy_fixed_cost_total_pct, -3.260114)
        self.assertFalse(row.survives_legacy_fixed_cost)
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

    def test_report_reclassifies_fee_cleared_density_rejects_into_exact_rescue_queue(self) -> None:
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

        self.assertEqual(report["strict_rescue_count"], 1)
        self.assertEqual(report["fee_cleared_but_blocked_count"], 0)
        self.assertEqual(report["class_counts"], {"rescued_for_exact_aq": 1})
        self.assertEqual(report["other_class_count"], 0)
        self.assertEqual(
            report["rescued_for_exact_aq"][0]["factor_id"],
            "tomac_nq_fee_cleared_sparse_v1",
        )

    def test_parameter_distinct_leaderboard_labels_are_not_collapsed_by_family_dedupe(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "leaderboard.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "label",
                        "symbol_root",
                        "factor_id",
                        "side",
                        "trade_count",
                        "instrument_all_in_total_profit_pct",
                        "legacy_wall_total_profit_pct",
                        "session_scope",
                        "rth_filter_applied",
                        "eth_full_retained_session_evidence",
                        "minimum_trade_sample_floor_met",
                        "density_target_1_to_3_per_day",
                        "positive_years",
                        "years",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "label": "NQ_fade_long_st2_z0.8_rvmax1_q4_mtf0_h3_cd2",
                        "symbol_root": "NQ",
                        "factor_id": "tomac_hf_streak_exhaustion_reversal_micro_proxy_v1",
                        "side": "long",
                        "trade_count": "502",
                        "instrument_all_in_total_profit_pct": "2.34018",
                        "legacy_wall_total_profit_pct": "-44.59682",
                        "session_scope": "ETH/full_retained_session",
                        "rth_filter_applied": "False",
                        "eth_full_retained_session_evidence": "True",
                        "minimum_trade_sample_floor_met": "True",
                        "density_target_1_to_3_per_day": "True",
                        "positive_years": "4",
                        "years": "5",
                    }
                )
                writer.writerow(
                    {
                        "label": "NQ_fade_long_st2_z0.55_rvmax1_q4_mtf0_h3_cd2",
                        "symbol_root": "NQ",
                        "factor_id": "tomac_hf_streak_exhaustion_reversal_micro_proxy_v1",
                        "side": "long",
                        "trade_count": "585",
                        "instrument_all_in_total_profit_pct": "1.848607",
                        "legacy_wall_total_profit_pct": "-52.848893",
                        "session_scope": "ETH/full_retained_session",
                        "rth_filter_applied": "False",
                        "eth_full_retained_session_evidence": "True",
                        "minimum_trade_sample_floor_met": "True",
                        "density_target_1_to_3_per_day": "True",
                        "positive_years": "4",
                        "years": "5",
                    }
                )

            report = audit.build_report([source])

        self.assertEqual(report["strict_rescue_count"], 2)
        self.assertEqual(
            {row["candidate_label"] for row in report["rescued_for_exact_aq"]},
            {
                "NQ_fade_long_st2_z0.8_rvmax1_q4_mtf0_h3_cd2",
                "NQ_fade_long_st2_z0.55_rvmax1_q4_mtf0_h3_cd2",
            },
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

    def test_fee_cleared_priority_queue_does_not_treat_total_trades_as_density(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "fee_cleared_rows.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "effective_symbol",
                        "label",
                        "trade_count",
                        "instrument_cost_total_profit_pct",
                        "legacy_fixed_cost_total_profit_pct",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "effective_symbol": "GC",
                        "label": "tomac_xau_overtrade_v1",
                        "trade_count": "72144",
                        "instrument_cost_total_profit_pct": "151.4",
                        "legacy_fixed_cost_total_profit_pct": "-5964",
                    }
                )
                writer.writerow(
                    {
                        "effective_symbol": "M2K",
                        "label": "m2k_balanced_1m_short",
                        "trade_count": "54",
                        "instrument_cost_total_profit_pct": "1.020857",
                        "legacy_fixed_cost_total_profit_pct": "-2.97",
                    }
                )
                writer.writerow(
                    {
                        "effective_symbol": "MES",
                        "label": "mes_high_trade_tiny_edge",
                        "trade_count": "59",
                        "instrument_cost_total_profit_pct": "0.03765",
                        "legacy_fixed_cost_total_profit_pct": "-4.73",
                    }
                )
                writer.writerow(
                    {
                        "effective_symbol": "MGC",
                        "label": "mgc_dense_5m_sparse",
                        "trade_count": "23",
                        "instrument_cost_total_profit_pct": "1.006",
                        "legacy_fixed_cost_total_profit_pct": "-0.8",
                    }
                )

            report = audit.build_report([source])

        queue = report["fee_cleared_priority_queue"]
        self.assertEqual(report["fee_cleared_priority_count"], 4)
        self.assertEqual(queue[0]["factor_id"], "tomac_xau_overtrade_v1")
        self.assertEqual(queue[0]["priority_bucket"], "exact_recheck_first")
        self.assertEqual(queue[0]["next_action"], "exact_recheck_after_runtime_clears")
        self.assertFalse(queue[0]["promotion_allowed"])
        self.assertFalse(queue[0]["trade_usable"])

    def test_casebook_revival_unique_csv_shape_feeds_priority_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "current_revival_unique.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "label",
                        "symbol_root",
                        "trade_count",
                        "legacy_wall_total_profit_pct",
                        "instrument_all_in_total_profit_pct",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "label": "tomac_idxfut_clean_low_volatility_trend_pullback_reacceleration_30m_v1",
                        "symbol_root": "NQ",
                        "trade_count": "1902",
                        "legacy_wall_total_profit_pct": "-104.339425",
                        "instrument_all_in_total_profit_pct": "73.497575",
                    }
                )
                writer.writerow(
                    {
                        "label": "density_midrange_reaccel_or6_atr4_rrr2_er30",
                        "symbol_root": "NQ",
                        "trade_count": "613",
                        "legacy_wall_total_profit_pct": "-4.488035",
                        "instrument_all_in_total_profit_pct": "52.827465",
                    }
                )

            report = audit.build_report([source])

        self.assertEqual(report["row_count"], 2)
        self.assertEqual(report["needs_eth_full_session_replay_count"], 2)
        self.assertEqual(report["fee_cleared_priority_count"], 2)
        queue = report["fee_cleared_priority_queue"]
        self.assertEqual(queue[0]["factor_id"], "tomac_idxfut_clean_low_volatility_trend_pullback_reacceleration_30m_v1")
        self.assertEqual(queue[0]["priority_bucket"], "exact_recheck_first")
        self.assertEqual(queue[1]["priority_bucket"], "exact_recheck_first")
        self.assertFalse(queue[0]["promotion_allowed"])
        self.assertFalse(queue[0]["trade_usable"])

    def test_casebook_unique_with_carried_session_evidence_is_not_session_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "current_revival_unique.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "label",
                        "symbol_root",
                        "timeframe",
                        "variant",
                        "branch_path",
                        "trade_count",
                        "legacy_wall_total_profit_pct",
                        "instrument_all_in_total_profit_pct",
                        "session_scope",
                        "rth_filter_applied",
                        "eth_full_retained_session_evidence",
                        "minimum_trade_sample_floor_met",
                        "trades_per_day",
                        "density_target_1_to_3_per_day",
                        "positive_years",
                        "years",
                        "year_coverage_ok",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "label": "tomac_nq_fee_false_negative_30m_v1",
                        "symbol_root": "NQ",
                        "timeframe": "30m",
                        "variant": "tight_vol",
                        "branch_path": "TrendExpansion -> PullbackReacceleration -> tomac_nq_fee_false_negative_30m_v1",
                        "trade_count": "1902",
                        "legacy_wall_total_profit_pct": "-104.339425",
                        "instrument_all_in_total_profit_pct": "73.497575",
                        "session_scope": "ETH/full_retained_session",
                        "rth_filter_applied": "False",
                        "eth_full_retained_session_evidence": "True",
                        "minimum_trade_sample_floor_met": "True",
                        "trades_per_day": "1.22",
                        "density_target_1_to_3_per_day": "True",
                        "positive_years": "4",
                        "years": "5",
                        "year_coverage_ok": "True",
                    }
                )

            report = audit.build_report([source])

        self.assertEqual(report["strict_rescue_count"], 1)
        self.assertEqual(report["needs_eth_full_session_replay_count"], 0)
        rescued = report["rescued_for_exact_aq"][0]
        self.assertEqual(rescued["factor_id"], "tomac_nq_fee_false_negative_30m_v1")
        self.assertEqual(rescued["timeframe"], "30m")
        self.assertTrue(rescued["density_target_1_to_3_per_day"])

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
