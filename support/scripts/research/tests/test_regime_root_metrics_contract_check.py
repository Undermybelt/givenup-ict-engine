from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import regime_root_metrics_contract_check as checker  # noqa: E402


class RegimeRootMetricsContractCheckTests(unittest.TestCase):
    def test_rejects_provider_market_symbol_timeframe_prefix_as_branch_root(self) -> None:
        metrics = {
            "branch_path": (
                "IBKR -> FUTURES -> MNQ -> 1m -> TrendExpansion -> "
                "RootEvidencePullbackMssCisd -> factor_v1"
            ),
            "branch_fields_preserved": True,
            "exact_1m_survivors_5bps": ["MNQ/1m/dense"],
            "cost_stress": [
                {
                    "label": "MNQ/1m/dense",
                    "trade_count": 42,
                    "trades_per_day": 1.5,
                    "survives_5bps_per_side": True,
                }
            ],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertFalse(report["ok"])
        self.assertIn(
            "branch_path_not_canonical_regime_root",
            report["violations"],
        )
        self.assertEqual(
            report["normalized"]["canonical_branch_path"],
            "TrendExpansion -> RootEvidencePullbackMssCisd -> factor_v1",
        )

    def test_rejects_downstream_opened_by_2bps_survivors_without_5bps_survivor(self) -> None:
        metrics = {
            "branch_path": "TrendExpansion -> PullbackReclaim -> factor_v1",
            "branch_fields_preserved": True,
            "exact_1m_survivors_2bps": ["MNQ/1m/dense"],
            "exact_1m_survivors_5bps": [],
            "cost_stress": [
                {
                    "label": "MNQ/1m/dense",
                    "trade_count": 44,
                    "trades_per_day": 1.57,
                    "survives_2bps_per_side": True,
                    "survives_5bps_per_side": False,
                    "net_after_5bps_side_pct": -0.13,
                }
            ],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertFalse(report["ok"])
        self.assertIn("downstream_open_without_exact_real_cost_survivor", report["violations"])
        self.assertIn("survivors_2bps_used_as_downstream_gate", report["violations"])

    def test_accepts_futures_instrument_cost_survivor_when_5bps_stress_fails(self) -> None:
        metrics = {
            "branch_path": "RangeReversion -> FuturesCostRevival -> factor_v1",
            "branch_fields_preserved": True,
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
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])
        self.assertEqual(report["survivors"]["exact_5bps"], [])
        self.assertEqual(report["survivors"]["instrument_cost"], ["NQ/5m/cost_revival"])
        self.assertEqual(report["survivors"]["real_cost"], ["NQ/5m/cost_revival"])

    def test_rejects_unverified_default_futures_instrument_cost_survivor(self) -> None:
        metrics = {
            "branch_path": "RangeReversion -> FuturesCostRevival -> factor_v1",
            "branch_fields_preserved": True,
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
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertFalse(report["ok"])
        self.assertIn("downstream_open_without_exact_real_cost_survivor", report["violations"])
        self.assertEqual(report["survivors"]["instrument_cost"], [])
        self.assertEqual(report["survivors"]["real_cost"], [])

    def test_rejects_futures_5bps_stress_survivor_without_instrument_cost(self) -> None:
        metrics = {
            "branch_path": "RangeReversion -> PullbackReclaim -> tomac_nq_stress_only_v1",
            "branch_fields_preserved": True,
            "exact_1m_survivors_5bps": ["NQ/1m/stress-only"],
            "cost_stress": [
                {
                    "label": "NQ/1m/stress-only",
                    "symbol": "NQ",
                    "asset_class": "futures",
                    "trade_count": 44,
                    "survives_5bps_per_side": True,
                    "net_after_5bps_side_pct": 0.41,
                    "cost_stress_5bps_role": "telemetry_not_futures_hard_gate",
                }
            ],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertFalse(report["ok"])
        self.assertIn("downstream_open_without_exact_real_cost_survivor", report["violations"])
        self.assertEqual(report["survivors"]["exact_5bps"], ["NQ/1m/stress-only"])
        self.assertEqual(report["survivors"]["real_cost"], [])

    def test_accepts_canonical_branch_with_exact_non_futures_5bps_gate(self) -> None:
        metrics = {
            "branch_path": "RangeReversion -> PullbackReclaim -> factor_v1",
            "branch_fields_preserved": True,
            "exact_1m_survivors_2bps": ["DELL/1m/dense"],
            "exact_1m_survivors_5bps": ["DELL/1m/dense"],
            "cost_stress": [
                {
                    "label": "DELL/1m/dense",
                    "trade_count": 44,
                    "trades_per_day": 1.57,
                    "survives_2bps_per_side": True,
                    "survives_5bps_per_side": True,
                    "net_after_5bps_side_pct": 0.41,
                }
            ],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])
        self.assertEqual(report["decision"], "contract_ok")

    def test_accepts_futures_downstream_with_instrument_cost_survivor_and_5bps_stress_failure(self) -> None:
        metrics = {
            "branch_path": "RangeReversion -> PullbackReclaim -> futures_factor_v1",
            "branch_fields_preserved": True,
            "cost_gate_authority": "instrument_cost",
            "cost_stress_5bps_role": "telemetry_not_futures_hard_gate",
            "survivors_instrument_cost": ["NQ/5m/repriced"],
            "cost_stress": [
                {
                    "label": "NQ/5m/repriced",
                    "trade_count": 1362,
                    "trades_per_day": 1.08,
                    "survives_instrument_cost": True,
                    "instrument_cost_total_profit_pct": 1.05,
                    "survives_5bps_per_side": False,
                    "5bps_per_side_total_profit_pct": -118.03,
                    "symbol": "NQ",
                    "asset_class": "futures",
                    "cost_profile_id": "CME_NQ_IBKR_verified_20260530_v1",
                    "cost_model_status": "verified_ibkr_broker_side",
                    "cost_model_verified_for_promotion": True,
                }
            ],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])
        self.assertEqual(report["decision"], "contract_ok")
        self.assertEqual(report["survivors"]["instrument_cost"], ["NQ/5m/repriced"])
        self.assertEqual(report["survivors"]["exact_5bps"], [])

    def test_accepts_per_timeframe_exact_5bps_gate(self) -> None:
        for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d"):
            with self.subTest(timeframe=timeframe):
                label = f"DELL/{timeframe}/dense"
                metrics = {
                    "branch_path": "RangeReversion -> PullbackReclaim -> factor_v1",
                    "branch_fields_preserved": True,
                    f"exact_{timeframe}_survivors_5bps": [label],
                    f"exact_{timeframe}_cost_stress": [
                        {
                            "label": label,
                            "trade_count": 44,
                            "trades_per_day": 1.57,
                            "survives_5bps_per_side": True,
                            "net_after_5bps_side_pct": 0.41,
                        }
                    ],
                    "downstream_allowed": True,
                    "pre_bayes_allowed": True,
                    "bbn_allowed": True,
                    "catboost_allowed": True,
                    "execution_tree_allowed": True,
                }

                with tempfile.TemporaryDirectory() as tmpdir:
                    path = Path(tmpdir) / "terminal_metrics.json"
                    path.write_text(json.dumps(metrics), encoding="utf-8")

                    report = checker.check_metrics_file(path)

                self.assertTrue(report["ok"])
                self.assertEqual(report["violations"], [])
                self.assertEqual(report["survivors"]["exact_5bps"], [label])

    def test_accepts_single_trade_sparse_5bps_survivor_without_daily_density_floor(self) -> None:
        metrics = {
            "branch_path": "RangeReversion -> PullbackReclaim -> factor_v1",
            "branch_fields_preserved": True,
            "exact_5m_survivors_5bps": ["DELL/5m/soup_quality"],
            "exact_5m_cost_stress": [
                {
                    "label": "DELL/5m/soup_quality",
                    "trade_count": 1,
                    "trades_per_day": 0.02,
                    "survives_5bps_per_side": True,
                    "net_after_5bps_side_pct": 0.03,
                }
            ],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])
        self.assertEqual(report["survivors"]["exact_5bps"], ["DELL/5m/soup_quality"])
        self.assertEqual(report["density_gate"]["status"], "cancelled")
        self.assertIsNone(report["density_gate"]["min_trades_per_day"])
        self.assertEqual(
            report["density_gate"]["requirement"],
            "trade_count_gt_0_and_positive_exact_real_cost",
        )

    def test_deprecated_min_trades_per_day_argument_does_not_block_sparse_survivor(self) -> None:
        metrics = {
            "branch_path": "RangeReversion -> PullbackReclaim -> factor_v1",
            "branch_fields_preserved": True,
            "exact_5m_survivors_5bps": ["DELL/5m/soup_quality"],
            "exact_5m_cost_stress": [
                {
                    "label": "DELL/5m/soup_quality",
                    "trade_count": 1,
                    "trades_per_day": 0.02,
                    "survives_5bps_per_side": True,
                    "net_after_5bps_side_pct": 0.03,
                }
            ],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path, min_trades_per_day=1.0)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])
        self.assertEqual(report["survivors"]["exact_5bps"], ["DELL/5m/soup_quality"])
        self.assertEqual(report["density_gate"]["status"], "cancelled")

    def test_accepts_real_exact_timeframe_density_survivor_schema(self) -> None:
        metrics = {
            "branch_path": "RangeReversion -> PullbackReclaim -> factor_v1",
            "branch_fields_preserved": True,
            "exact_timeframe": "5m",
            "exact_5m_survivors_5bps_density": ["DELL/5m/balanced"],
            "survivors_5bps_per_side": ["DELL/5m/balanced"],
            "cost_stress_rows": [
                {
                    "label": "DELL/5m/balanced",
                    "timeframe": "5m",
                    "trade_count": 86,
                    "density_per_day": 1.34375,
                    "practical_density": True,
                    "survives_5bps_per_side": True,
                    "5bps_per_side_total_profit_pct": 12.45,
                }
            ],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])
        self.assertEqual(report["survivors"]["five_bps"], ["DELL/5m/balanced"])
        self.assertEqual(report["survivors"]["exact_5bps"], ["DELL/5m/balanced"])

    def test_rejects_trend_pullback_downstream_without_root_evidence_packet(self) -> None:
        metrics = {
            "branch_path": "TrendExpansion -> PullbackReclaim -> factor_v1",
            "branch_fields_preserved": True,
            "exact_1m_survivors_5bps": ["DELL/1m/dense"],
            "cost_stress": [
                {
                    "label": "DELL/1m/dense",
                    "trade_count": 44,
                    "trades_per_day": 1.57,
                    "survives_5bps_per_side": True,
                    "net_after_5bps_side_pct": 0.41,
                }
            ],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertFalse(report["ok"])
        self.assertIn("trend_root_evidence_packet_missing", report["violations"])
        self.assertIn("trend_root_posterior_missing", report["violations"])
        self.assertIn("trend_root_loss_boundary_labels_missing", report["violations"])

    def test_accepts_trend_continuation_downstream_with_root_evidence_and_loss_boundaries(self) -> None:
        metrics = {
            "branch_path": "TrendExpansion -> PullbackContinuation -> factor_v1",
            "branch_fields_preserved": True,
            "root_regime_evidence_packet": {
                "schema_version": "trend-root-evidence/v1",
                "root_regime": "TrendExpansion",
                "trend_posterior": 0.83,
                "mss_confirmed": True,
                "cisd_confirmed": True,
            },
            "loss_boundary_labels": [
                "low_trend_probability_loss",
                "terminal_trend_loss",
                "valid_trend_pullback_loss",
            ],
            "exact_1m_survivors_5bps": ["DELL/1m/dense"],
            "cost_stress": [
                {
                    "label": "DELL/1m/dense",
                    "trade_count": 44,
                    "trades_per_day": 1.57,
                    "survives_5bps_per_side": True,
                    "net_after_5bps_side_pct": 0.41,
                }
            ],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_rejects_5bps_survivor_names_without_cost_rows(self) -> None:
        metrics = {
            "branch_path": "TrendExpansion -> PullbackReclaim -> factor_v1",
            "branch_fields_preserved": True,
            "exact_1m_survivors_5bps": ["MNQ/1m/dense"],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertFalse(report["ok"])
        self.assertIn("downstream_open_without_exact_real_cost_survivor", report["violations"])
        self.assertIn("survivors_5bps_without_cost_row_used_as_downstream_gate", report["violations"])

    def test_rejects_5bps_positive_cost_rows_without_trade_count_proof(self) -> None:
        metrics = {
            "branch_path": "RangeReversion -> PullbackReclaim -> factor_v1",
            "branch_fields_preserved": True,
            "cost_stress": [
                {
                    "package_id": "range-reversion-15m-v1",
                    "net_after_5bps_per_side_pct": 0.71,
                    "survives_5bps_per_side": True,
                }
            ],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertFalse(report["ok"])
        self.assertIn("downstream_open_without_exact_real_cost_survivor", report["violations"])
        self.assertIn("cost_rows_5bps_positive_without_trade_count_proof", report["violations"])

    def test_rejects_trend_root_mss_cisd_downstream_without_evidence_packet(self) -> None:
        metrics = {
            "branch_path": (
                "TrendExpansion -> RootEvidencePullbackMssCisd -> "
                "strict_trend_root_pullback_mss_cisd"
            ),
            "branch_fields_preserved": True,
            "cost_gate_authority": "instrument_cost",
            "survivors_instrument_cost": ["MNQ/1m/dense"],
            "cost_stress": [
                {
                    "label": "MNQ/1m/dense",
                    "symbol": "MNQ",
                    "asset_class": "futures",
                    "trade_count": 44,
                    "trades_per_day": 1.57,
                    "survives_instrument_cost": True,
                    "instrument_cost_total_profit_pct": 0.41,
                    "survives_5bps_per_side": False,
                    "net_after_5bps_side_pct": -0.13,
                    "cost_profile_id": "CME_MNQ_IBKR_verified_20260530_v1",
                    "cost_model_status": "verified_ibkr_broker_side",
                    "cost_model_verified_for_promotion": True,
                    "cost_stress_5bps_role": "telemetry_not_futures_hard_gate",
                }
            ],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertFalse(report["ok"])
        self.assertIn("trend_root_evidence_packet_missing", report["violations"])
        self.assertIn("trend_root_mss_confirmation_missing", report["violations"])
        self.assertIn("trend_root_cisd_confirmation_missing", report["violations"])
        self.assertIn("trend_root_posterior_missing", report["violations"])

    def test_accepts_trend_root_mss_cisd_downstream_with_evidence_packet(self) -> None:
        metrics = {
            "branch_path": (
                "TrendExpansion -> RootEvidencePullbackMssCisd -> "
                "strict_trend_root_pullback_mss_cisd"
            ),
            "branch_fields_preserved": True,
            "root_regime_evidence_packet": {
                "schema_version": "trend-root-evidence/v1",
                "root_regime": "TrendExpansion",
                "trend_posterior": 0.83,
                "mss_confirmed": True,
                "cisd_confirmed": True,
                "pda_hybrid_alignment": True,
            },
            "loss_boundary_labels": [
                "low_trend_probability_loss",
                "terminal_trend_loss",
                "valid_trend_pullback_loss",
            ],
            "exact_1m_survivors_5bps": ["DELL/1m/dense"],
            "cost_stress": [
                {
                    "label": "DELL/1m/dense",
                    "trade_count": 44,
                    "trades_per_day": 1.57,
                    "survives_5bps_per_side": True,
                    "net_after_5bps_side_pct": 0.41,
                }
            ],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_rejects_low_probability_trend_root_downstream(self) -> None:
        metrics = {
            "branch_path": (
                "TrendExpansion -> RootEvidencePullbackMssCisd -> "
                "strict_trend_root_pullback_mss_cisd"
            ),
            "branch_fields_preserved": True,
            "root_regime_evidence_packet": {
                "schema_version": "trend-root-evidence/v1",
                "root_regime": "TrendExpansion",
                "trend_posterior": 0.42,
                "mss_confirmed": True,
                "cisd_confirmed": True,
            },
            "exact_1m_survivors_5bps": ["MNQ/1m/dense"],
            "cost_stress": [
                {
                    "label": "MNQ/1m/dense",
                    "trade_count": 44,
                    "trades_per_day": 1.57,
                    "survives_5bps_per_side": True,
                    "net_after_5bps_side_pct": 0.41,
                }
            ],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertFalse(report["ok"])
        self.assertIn("trend_root_posterior_below_threshold", report["violations"])

    def test_quarantines_downstream_open_contract_violations_from_feedback_admission(self) -> None:
        metrics = {
            "branch_path": (
                "TrendExpansion -> RootEvidencePullbackMssCisd -> "
                "strict_trend_root_pullback_mss_cisd"
            ),
            "branch_fields_preserved": True,
            "exact_1m_survivors_2bps": ["MNQ/1m/dense"],
            "cost_stress": [
                {
                    "label": "MNQ/1m/dense",
                    "trade_count": 44,
                    "trades_per_day": 1.57,
                    "survives_2bps_per_side": True,
                    "survives_5bps_per_side": False,
                    "net_after_5bps_side_pct": -0.13,
                }
            ],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertFalse(report["ok"])
        self.assertTrue(report["feedback_admission"]["quarantine_required"])
        self.assertEqual(
            report["feedback_admission"]["decision"],
            "quarantine_downstream_contract_violation",
        )
        self.assertEqual(
            report["feedback_admission"]["allowed_targets"],
            {
                "pre_bayes_feedback": False,
                "bbn_feedback": False,
                "catboost_training": False,
                "execution_tree_training": False,
            },
        )
        self.assertIn(
            "trend_root_evidence_packet_missing",
            report["feedback_admission"]["blocking_violations"],
        )
        self.assertIn(
            "downstream_open_without_exact_real_cost_survivor",
            report["feedback_admission"]["blocking_violations"],
        )

    def test_rejects_trade_usable_or_promotion_before_extension_complete(self) -> None:
        metrics = {
            "branch_path": (
                "TrendExpansion -> ElectricalEquipmentGannHiloActivator -> "
                "gann_hilo_activator -> ibkr_etn_gann_hilo_5m_quality_exact_v1"
            ),
            "branch_fields_preserved": True,
            "exact_1m_survivors_5bps": ["ETN/5m/quality"],
            "cost_stress": [
                {
                    "label": "ETN/5m/quality",
                    "trade_count": 123,
                    "trades_per_day": 1.92,
                    "survives_5bps_per_side": True,
                    "net_after_5bps_side_pct": 6.35,
                }
            ],
            "downstream_allowed": True,
            "pre_bayes_allowed": True,
            "bbn_allowed": True,
            "catboost_allowed": True,
            "execution_tree_allowed": True,
            "execution_candidate_actionable": True,
            "execution_readiness": 0.67,
            "transition_hazard": 0.369,
            "pda_hybrid_alignment": True,
            "promotion_allowed": True,
            "trade_usable": True,
            "extension_complete": False,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertFalse(report["ok"])
        self.assertIn(
            "trade_usable_before_extension_complete",
            report["violations"],
        )
        self.assertIn(
            "promotion_before_extension_complete",
            report["violations"],
        )
        self.assertEqual(
            report["practical_admission"]["decision"],
            "branch_local_only_extension_incomplete",
        )
        self.assertEqual(
            report["practical_admission"]["allowed_targets"],
            {
                "promotion_allowed": False,
                "trade_usable": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
