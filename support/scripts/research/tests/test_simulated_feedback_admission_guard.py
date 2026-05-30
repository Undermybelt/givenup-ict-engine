from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import simulated_feedback_admission_guard as guard  # noqa: E402


class SimulatedFeedbackAdmissionGuardTests(unittest.TestCase):
    def test_allows_observation_only_retained_real_feedback(self) -> None:
        rows = [
            {
                "trade_id": "sim-1",
                "feedback_source": "retained_real_event_label_simulation",
                "open_ts_ms": 1778248740000,
                "branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_mim_v1",
                "regime_profit_branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_mim_v1",
                "main_regime": "TrendExpansion",
                "mtf_trend_resonance": {
                    "enabled": True,
                    "aligned": True,
                    "min_aligned": 3,
                    "aligned_timeframes": ["5m", "15m", "30m"],
                    "resonance_score": 1.0,
                },
                "broker_fill_evidence": False,
                "provider_fetch_started": False,
                "auto_quant_started": False,
                "promotion_allowed": False,
                "trade_usable": False,
                "downstream_allowed": False,
            }
        ]
        summary = {
            "source": "retained_real_event_label_simulation",
            "provider_fetch_started": False,
            "auto_quant_started": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "downstream_allowed": False,
        }

        result = guard.validate_bundle(rows, summary=summary)

        self.assertTrue(result["ok"])
        self.assertEqual(result["row_count"], 1)
        self.assertEqual(result["violations"], [])
        self.assertFalse(result["promotion_allowed"])
        self.assertFalse(result["trade_usable"])

    def test_rejects_non_trend_or_weak_mtf_feedback_shape(self) -> None:
        rows = [
            {
                "trade_id": "sim-range",
                "feedback_source": "retained_real_event_label_simulation",
                "open_ts_ms": 1778248740000,
                "branch_path": "RangeReversion -> Snapback -> test_v1",
                "regime_profit_branch_path": "RangeReversion -> Snapback -> test_v1",
                "main_regime": "RangeReversion",
                "mtf_trend_resonance": {
                    "enabled": True,
                    "aligned": True,
                    "min_aligned": 3,
                    "aligned_timeframes": ["5m", "15m", "30m"],
                },
            },
            {
                "trade_id": "sim-weak-mtf",
                "feedback_source": "retained_real_event_label_simulation",
                "open_ts_ms": 1778507940000,
                "branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> weak_mtf -> test_v1",
                "regime_profit_branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> weak_mtf -> test_v1",
                "main_regime": "TrendExpansion",
                "mtf_trend_resonance": {
                    "enabled": True,
                    "aligned": False,
                    "min_aligned": 3,
                    "aligned_timeframes": ["5m", "15m"],
                },
            },
        ]

        result = guard.validate_bundle(rows, summary={"source": "retained_real_event_label_simulation"})

        self.assertFalse(result["ok"])
        self.assertIn("row[0].non_trend_root:RangeReversion", result["violations"])
        self.assertIn("row[1].mtf_aligned_false", result["violations"])
        self.assertIn("row[1].mtf_aligned_timeframes_lt_min:2<3", result["violations"])

    def test_rejects_branch_identity_mismatch(self) -> None:
        rows = [
            {
                "trade_id": "sim-mismatch",
                "feedback_source": "retained_real_event_label_simulation",
                "open_ts_ms": 1778248740000,
                "branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> a -> test_v1",
                "regime_profit_branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> b -> test_v1",
                "main_regime": "TrendExpansion",
                "mtf_trend_resonance": {
                    "enabled": True,
                    "aligned": True,
                    "min_aligned": 3,
                    "aligned_timeframes": ["5m", "15m", "30m"],
                },
            }
        ]

        result = guard.validate_bundle(rows, summary={"source": "retained_real_event_label_simulation"})

        self.assertFalse(result["ok"])
        self.assertIn("row[0].branch_path_mismatch", result["violations"])

    def test_rejects_trade_frequency_outside_requested_window(self) -> None:
        base = {
            "feedback_source": "retained_real_event_label_simulation",
            "branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_mim_v1",
            "regime_profit_branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_mim_v1",
            "main_regime": "TrendExpansion",
            "mtf_trend_resonance": {
                "enabled": True,
                "aligned": True,
                "min_aligned": 3,
                "aligned_timeframes": ["5m", "15m", "30m"],
            },
        }
        rows = [
            {**base, "trade_id": "sim-fast-1", "open_ts_ms": 1778248740000},
            {**base, "trade_id": "sim-fast-2", "open_ts_ms": 1778248800000},
            {**base, "trade_id": "sim-fast-3", "open_ts_ms": 1778248860000},
            {**base, "trade_id": "sim-fast-4", "open_ts_ms": 1778248920000},
            {**base, "trade_id": "sim-slow", "open_ts_ms": 1779458340000},
        ]

        result = guard.validate_bundle(rows, summary={"source": "retained_real_event_label_simulation"})

        self.assertFalse(result["ok"])
        self.assertIn("frequency.trades_per_day_gt_max:4.00>3.00", result["violations"])
        self.assertIn("frequency.max_gap_days_gt_allowed:14.00>3.00", result["violations"])
        self.assertFalse(result["blocker_categories"]["frequency"]["ok"])
        self.assertIn("repair_trade_frequency_or_window", result["next_action_keywords"])

    def test_pair_scoped_daily_frequency_does_not_fail_multi_pair_portfolio(self) -> None:
        base = {
            "feedback_source": "retained_real_event_label_simulation",
            "branch_path": "TrendExpansion -> Basket -> balanced_portfolio -> test_v1",
            "regime_profit_branch_path": "TrendExpansion -> Basket -> balanced_portfolio -> test_v1",
            "main_regime": "TrendExpansion",
            "mtf_trend_resonance": {
                "enabled": True,
                "aligned": True,
                "min_aligned": 3,
                "aligned_timeframes": ["5m", "15m", "30m"],
            },
        }
        rows = [
            {**base, "trade_id": "nq-1", "pair": "NQ/USD", "open_ts_ms": 1778248740000},
            {**base, "trade_id": "nq-2", "pair": "NQ/USD", "open_ts_ms": 1778248800000},
            {**base, "trade_id": "nq-3", "pair": "NQ/USD", "open_ts_ms": 1778248860000},
            {**base, "trade_id": "ym-1", "pair": "YM/USD", "open_ts_ms": 1778248920000},
            {**base, "trade_id": "xau-1", "pair": "XAU/USD", "open_ts_ms": 1778248980000},
            {**base, "trade_id": "late", "pair": "NQ/USD", "open_ts_ms": 1779458340000},
        ]

        result = guard.validate_bundle(rows, summary={"source": "retained_real_event_label_simulation"})

        self.assertFalse(result["ok"])
        self.assertNotIn("frequency.trades_per_day_gt_max:5.00>3.00", result["violations"])
        self.assertIn("frequency.max_gap_days_gt_allowed:14.00>3.00", result["violations"])

    def test_classifies_downstream_prerequisite_blockers(self) -> None:
        rows = [
            {
                "trade_id": "sim-1",
                "feedback_source": "retained_real_event_label_simulation",
                "open_ts_ms": 1778248740000,
                "branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_mim_v1",
                "regime_profit_branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_mim_v1",
                "main_regime": "TrendExpansion",
                "mtf_trend_resonance": {
                    "enabled": True,
                    "aligned": True,
                    "min_aligned": 3,
                    "aligned_timeframes": ["5m", "15m", "30m"],
                },
            }
        ]
        summary = {
            "source": "retained_real_event_label_simulation",
            "trade_count": 0,
            "provider_parity": False,
            "cost_stress_rows": [
                {
                    "label": "1m/dense",
                    "trade_count": 4,
                    "survives_5bps_per_side": False,
                    "5bps_per_side_total_profit_pct": -0.4,
                }
            ],
            "raw_scored_mature_rows": 12,
            "production_validation_rows": 10,
            "observation_validation_rows": 29,
            "execution_readiness": 0.44,
            "transition_hazard": 0.75,
            "actionable": False,
        }

        result = guard.validate_bundle(rows, summary=summary)

        self.assertFalse(result["blocker_categories"]["cost_real"]["ok"])
        self.assertFalse(result["blocker_categories"]["provider_parity"]["ok"])
        self.assertFalse(result["blocker_categories"]["validation"]["ok"])
        self.assertFalse(result["blocker_categories"]["execution_readiness"]["ok"])
        self.assertIn("rerun_exact_real_cost_check", result["next_action_keywords"])
        self.assertIn("prove_provider_parity", result["next_action_keywords"])
        self.assertIn("repair_validation_rows", result["next_action_keywords"])
        self.assertIn("repair_execution_readiness", result["next_action_keywords"])

    def test_allows_futures_instrument_cost_when_5bps_stress_fails(self) -> None:
        rows = [
            {
                "trade_id": "sim-1",
                "feedback_source": "retained_real_event_label_simulation",
                "open_ts_ms": 1778248740000,
                "branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> futures_cost_revival -> test_v1",
                "regime_profit_branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> futures_cost_revival -> test_v1",
                "main_regime": "TrendExpansion",
                "mtf_trend_resonance": {
                    "enabled": True,
                    "aligned": True,
                    "min_aligned": 3,
                    "aligned_timeframes": ["5m", "15m", "30m"],
                },
            }
        ]
        summary = {
            "source": "retained_real_event_label_simulation",
            "trade_count": 1362,
            "provider_parity": True,
            "cost_stress": [
                {
                    "label": "NQ/5m/cost_revival",
                    "symbol": "NQ",
                    "asset_class": "futures",
                    "trade_count": 1362,
                    "survives_5bps_per_side": False,
                    "5bps_per_side_total_profit_pct": -118.03,
                    "survives_instrument_cost": True,
                    "instrument_cost_total_profit_pct": 8.42,
                    "cost_profile_id": "CME_NQ_IBKR_verified_20260530_v1",
                    "cost_stress_5bps_role": "telemetry_not_futures_hard_gate",
                }
            ],
            "raw_scored_mature_rows": 30,
            "production_validation_rows": 30,
            "observation_validation_rows": 30,
            "execution_readiness": 0.45,
            "actionable": True,
        }

        result = guard.validate_bundle(rows, summary=summary)

        self.assertTrue(result["blocker_categories"]["cost_real"]["ok"])
        self.assertNotIn("rerun_exact_real_cost_check", result["next_action_keywords"])

    def test_rejects_unverified_default_futures_instrument_cost_profile(self) -> None:
        rows = [
            {
                "trade_id": "sim-1",
                "feedback_source": "retained_real_event_label_simulation",
                "open_ts_ms": 1778248740000,
                "branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> futures_cost_revival -> test_v1",
                "regime_profit_branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> futures_cost_revival -> test_v1",
                "main_regime": "TrendExpansion",
                "mtf_trend_resonance": {
                    "enabled": True,
                    "aligned": True,
                    "min_aligned": 3,
                    "aligned_timeframes": ["5m", "15m", "30m"],
                },
            }
        ]
        summary = {
            "source": "retained_real_event_label_simulation",
            "trade_count": 1362,
            "provider_parity": True,
            "cost_gate_authority": "instrument_cost",
            "survivors_instrument_cost": ["RTY/5m/default-cost"],
            "cost_stress": [
                {
                    "label": "RTY/5m/default-cost",
                    "symbol": "RTY",
                    "asset_class": "futures",
                    "trade_count": 1362,
                    "survives_5bps_per_side": False,
                    "5bps_per_side_total_profit_pct": -118.03,
                    "survives_instrument_cost": True,
                    "instrument_cost_total_profit_pct": 8.42,
                    "cost_profile_id": "CME_RTY_default_v1",
                    "cost_model_status": "default_assumption_unverified",
                    "cost_model_verified_for_promotion": False,
                    "cost_stress_5bps_role": "telemetry_not_futures_hard_gate",
                }
            ],
            "raw_scored_mature_rows": 30,
            "production_validation_rows": 30,
            "observation_validation_rows": 30,
            "execution_readiness": 0.45,
            "actionable": True,
        }

        result = guard.validate_bundle(rows, summary=summary)

        self.assertFalse(result["blocker_categories"]["cost_real"]["ok"])
        self.assertIn("rerun_exact_real_cost_check", result["next_action_keywords"])

    def test_rejects_futures_5bps_stress_survivor_without_instrument_cost(self) -> None:
        rows = [
            {
                "trade_id": "sim-1",
                "feedback_source": "retained_real_event_label_simulation",
                "open_ts_ms": 1778248740000,
                "branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> futures_cost_wall_false_positive -> test_v1",
                "regime_profit_branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> futures_cost_wall_false_positive -> test_v1",
                "main_regime": "TrendExpansion",
                "mtf_trend_resonance": {
                    "enabled": True,
                    "aligned": True,
                    "min_aligned": 3,
                    "aligned_timeframes": ["5m", "15m", "30m"],
                },
            }
        ]
        summary = {
            "source": "retained_real_event_label_simulation",
            "trade_count": 1362,
            "provider_parity": True,
            "exact_5bps_survivors": ["tomac_nq_cost_wall_false_positive_v1"],
            "cost_stress": [
                {
                    "factor_id": "tomac_nq_cost_wall_false_positive_v1",
                    "trade_count": 1362,
                    "survives_5bps_per_side": True,
                    "5bps_per_side_total_profit_pct": 1.25,
                    "cost_stress_5bps_role": "telemetry_not_futures_hard_gate",
                }
            ],
            "raw_scored_mature_rows": 30,
            "production_validation_rows": 30,
            "observation_validation_rows": 30,
            "execution_readiness": 0.45,
            "actionable": True,
        }

        result = guard.validate_bundle(rows, summary=summary)

        self.assertFalse(result["blocker_categories"]["cost_real"]["ok"])
        self.assertIn("rerun_exact_real_cost_check", result["next_action_keywords"])

    def test_futures_instrument_cost_summary_wins_over_5bps_stress(self) -> None:
        rows = [
            {
                "trade_id": "sim-1",
                "feedback_source": "retained_real_event_label_simulation",
                "open_ts_ms": 1778248740000,
                "branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> futures_cost_revival -> test_v1",
                "regime_profit_branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> futures_cost_revival -> test_v1",
                "main_regime": "TrendExpansion",
                "mtf_trend_resonance": {
                    "enabled": True,
                    "aligned": True,
                    "min_aligned": 3,
                    "aligned_timeframes": ["5m", "15m", "30m"],
                },
            }
        ]
        summary = {
            "source": "retained_real_event_label_simulation",
            "trade_count": 1362,
            "provider_parity": True,
            "cost_gate_authority": "instrument_cost",
            "exact_5bps_survivors": ["tomac_nq_verified_real_cost_v1"],
            "survivors_instrument_cost": ["tomac_nq_verified_real_cost_v1"],
            "cost_stress": [
                {
                    "factor_id": "tomac_nq_verified_real_cost_v1",
                    "symbol": "NQ",
                    "asset_class": "futures",
                    "trade_count": 1362,
                    "survives_5bps_per_side": True,
                    "5bps_per_side_total_profit_pct": 1.25,
                    "survives_instrument_cost": True,
                    "instrument_cost_total_profit_pct": 7.40,
                    "cost_profile_id": "CME_NQ_IBKR_verified_20260530_v1",
                    "cost_model_status": "verified_ibkr_broker_side",
                    "cost_model_verified_for_promotion": True,
                    "cost_stress_5bps_role": "telemetry_not_futures_hard_gate",
                }
            ],
            "raw_scored_mature_rows": 30,
            "production_validation_rows": 30,
            "observation_validation_rows": 30,
            "execution_readiness": 0.45,
            "actionable": True,
        }

        result = guard.validate_bundle(rows, summary=summary)

        self.assertTrue(result["blocker_categories"]["cost_real"]["ok"])
        self.assertNotIn("rerun_exact_real_cost_check", result["next_action_keywords"])

    def test_allows_downstream_prerequisite_summary_when_all_evidence_present(self) -> None:
        rows = [
            {
                "trade_id": "sim-1",
                "feedback_source": "retained_real_event_label_simulation",
                "open_ts_ms": 1778248740000,
                "branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_mim_v1",
                "regime_profit_branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_mim_v1",
                "main_regime": "TrendExpansion",
                "mtf_trend_resonance": {
                    "enabled": True,
                    "aligned": True,
                    "min_aligned": 3,
                    "aligned_timeframes": ["5m", "15m", "30m"],
                },
            }
        ]
        summary = {
            "source": "retained_real_event_label_simulation",
            "trade_count": 8,
            "provider_parity": True,
            "cost_gate_authority": "instrument_cost",
            "survivors_instrument_cost": ["NQ/1m/dense"],
            "cost_stress": [
                {
                    "label": "NQ/1m/dense",
                    "symbol": "NQ",
                    "asset_class": "futures",
                    "trade_count": 8,
                    "survives_instrument_cost": True,
                    "instrument_cost_total_profit_pct": 0.42,
                    "cost_profile_id": "CME_NQ_IBKR_verified_20260530_v1",
                    "cost_model_status": "verified_ibkr_broker_side",
                    "cost_model_verified_for_promotion": True,
                }
            ],
            "raw_scored_mature_rows": 30,
            "production_validation_rows": 30,
            "observation_validation_rows": 30,
            "execution_readiness": 0.45,
            "transition_hazard": 0.9,
            "actionable": True,
        }

        result = guard.validate_bundle(rows, summary=summary)

        self.assertEqual(result["next_action_keywords"], [])
        for category in result["blocker_categories"].values():
            self.assertTrue(category["ok"])

    def test_rejects_simulated_feedback_with_admission_flags(self) -> None:
        rows = [
            {
                "trade_id": "sim-1",
                "feedback_source": "retained_real_event_label_simulation",
                "broker_fill_evidence": False,
                "promotion_allowed": True,
                "trade_usable": False,
                "downstream_allowed": False,
            },
            {
                "trade_id": "sim-2",
                "feedback_source": "retained_real_event_label_simulation",
                "broker_fill_evidence": True,
                "promotion_allowed": False,
                "trade_usable": False,
                "downstream_allowed": True,
            },
        ]
        summary = {
            "source": "retained_real_event_label_simulation",
            "promotion_allowed": False,
            "trade_usable": True,
        }

        result = guard.validate_bundle(rows, summary=summary)

        self.assertFalse(result["ok"])
        self.assertIn("row[0].promotion_allowed_true", result["violations"])
        self.assertIn("row[1].broker_fill_evidence_true", result["violations"])
        self.assertIn("row[1].downstream_allowed_true", result["violations"])
        self.assertIn("summary.trade_usable_true", result["violations"])

    def test_cli_exits_nonzero_on_unsafe_bundle(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            feedback_path = tmp / "feedback.jsonl"
            summary_path = tmp / "summary.json"
            report_path = tmp / "guard.json"
            feedback_path.write_text(
                json.dumps(
                    {
                        "trade_id": "sim-unsafe",
                        "feedback_source": "retained_real_event_label_simulation",
                        "promotion_allowed": True,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            summary_path.write_text(json.dumps({"promotion_allowed": False}), encoding="utf-8")

            exit_code = guard.main(
                [
                    "--feedback-jsonl",
                    str(feedback_path),
                    "--summary-json",
                    str(summary_path),
                    "--report-json",
                    str(report_path),
                ]
            )

            self.assertEqual(exit_code, 2)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertFalse(report["ok"])
            self.assertIn("row[0].promotion_allowed_true", report["violations"])


if __name__ == "__main__":
    unittest.main()
