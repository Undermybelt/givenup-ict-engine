from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import regime_root_survivor_blocker_report as report  # noqa: E402


class RegimeRootSurvivorBlockerReportTests(unittest.TestCase):
    def test_compact_tomac_rows_schema_counts_5bps_density_survivor(self) -> None:
        metrics = {
            "branch_path": "TrendExpansion -> OpeningDrive -> exact -> factor",
            "rows": [
                {
                    "factor_id": "tomac_nq_bidir_opening_drive_t10_w0_e900_x1245_exact_v1",
                    "trade_count": 985,
                    "cost_5bps_side_pct": 571.46,
                    "survives_5bps_density": True,
                }
            ],
            "survivor_count": 1,
            "decision": "exact_aq_5bps_density_survivor",
        }
        candidate = {
            "candidate_status": "execution_observe_only",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": [],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.47,
                "hybrid_transition_hazard": 0.62,
                "ranker_validation_ready": False,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": False,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertEqual(
            built["gate1"]["legacy_fixed_cost_readback_survivors"],
            ["tomac_nq_bidir_opening_drive_t10_w0_e900_x1245_exact_v1"],
        )
        self.assertEqual(built["gate1"]["exact_real_cost_survivors"], [])
        self.assertIn("no_real_cost_survivor", built["blockers"])

    def test_exact_branch_survived_terminal_metrics_counts_5bps_survivor(self) -> None:
        metrics = {
            "branch_path": (
                "TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> "
                "tomac_nq_bidir_opening_drive_t10_w0_e900_x1245_exact_v1"
            ),
            "exact_branch_survived": True,
            "branch_local_admitted": True,
            "validation_ready": True,
        }
        candidate = {
            "candidate_status": "execution_observe_only",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": [],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.4575,
                "ranker_validation_ready": True,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": True,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertEqual(
            built["gate1"]["legacy_fixed_cost_readback_survivors"],
            ["tomac_nq_bidir_opening_drive_t10_w0_e900_x1245_exact_v1"],
        )
        self.assertNotIn("no_real_cost_5bps_survivor", built["blockers"])

    def test_current_cost_stress_schema_counts_5bps_survivor(self) -> None:
        metrics = {
            "branch_path": "US_EQ -> single_stock -> NET -> 5m -> RangeReversion -> factor",
            "cost_stress": [
                {
                    "package_id": "net-5m-v1",
                    "timeframe": "5m",
                    "survives_5bps_per_side": True,
                    "trade_count": 32,
                }
            ],
        }
        candidate = {
            "candidate_status": "no_trade",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": [],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.67,
                "hybrid_transition_hazard": 0.95,
                "pda_hybrid_alignment": False,
                "ranker_validation_ready": True,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": True,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertTrue(built["gate1"]["branch_fields_preserved"])
        self.assertEqual(built["canonical_branch_path"], "RangeReversion -> factor")
        self.assertEqual(
            built["branch_labels"],
            {
                "market": "US_EQ",
                "product": "single_stock",
                "symbol": "NET",
                "timeframe": "5m",
            },
        )
        self.assertEqual(built["gate1"]["legacy_fixed_cost_readback_survivors"], ["net-5m-v1"])
        self.assertTrue(built["canonical_root_ok"])
        self.assertEqual(built["branch_path_violations"], [])
        self.assertNotIn("no_real_cost_5bps_survivor", built["blockers"])
        self.assertNotIn("pre_bayes_pass_neutralized", built["blockers"])
        self.assertNotEqual(built["decision"], "drop_gate1_economics")

    def test_futures_instrument_cost_survivor_counts_when_5bps_stress_fails(self) -> None:
        metrics = {
            "branch_path": "RangeReversion -> FuturesRepricedPullback -> tomac_nq_repriced_v1",
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
            "regime_confidence": 0.97,
            "rank_total_trade_count": 1362,
            "raw_scored_mature_rows": 30,
            "production_validation_rows": 30,
            "observation_validation_rows": 30,
        }
        candidate = {
            "candidate_status": "no_trade",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": [],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.34,
                "ranker_validation_ready": True,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": False,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertEqual(built["gate1"]["exact_cost_survivors"], ["NQ/5m/repriced"])
        self.assertEqual(built["gate1"]["legacy_fixed_cost_readback_survivors"], [])
        self.assertEqual(built["gate1"]["cost_gate_authority"], "instrument_cost")
        self.assertTrue(built["gate1"]["has_declared_cost_survivor"])
        self.assertNotIn("no_real_cost_5bps_survivor", built["blockers"])
        self.assertEqual(built["decision"], "learning_admitted_live_blocked")

    def test_unverified_default_futures_cost_profile_does_not_count_as_real_cost(self) -> None:
        metrics = {
            "branch_path": "RangeReversion -> FuturesRepricedPullback -> tomac_rty_default_cost_v1",
            "cost_gate_authority": "instrument_cost",
            "cost_stress_5bps_role": "telemetry_not_futures_hard_gate",
            "survivors_instrument_cost": ["RTY/5m/default-cost"],
            "cost_stress": [
                {
                    "label": "RTY/5m/default-cost",
                    "symbol": "RTY",
                    "asset_class": "futures",
                    "trade_count": 1362,
                    "trades_per_day": 1.08,
                    "survives_instrument_cost": True,
                    "instrument_cost_total_profit_pct": 1.05,
                    "survives_5bps_per_side": False,
                    "5bps_per_side_total_profit_pct": -118.03,
                    "cost_profile_id": "CME_RTY_default_v1",
                    "cost_model_status": "default_assumption_unverified",
                    "cost_model_verified_for_promotion": False,
                }
            ],
            "regime_confidence": 0.97,
            "rank_total_trade_count": 1362,
            "raw_scored_mature_rows": 30,
            "production_validation_rows": 30,
            "observation_validation_rows": 30,
        }
        candidate = {
            "candidate_status": "no_trade",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": [],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.34,
                "ranker_validation_ready": True,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": False,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertEqual(built["gate1"]["exact_instrument_cost_survivors"], [])
        self.assertEqual(built["gate1"]["exact_real_cost_survivors"], [])
        self.assertEqual(built["gate1"]["cost_gate_authority"], "none")
        self.assertIn("no_real_cost_survivor", built["blockers"])

    def test_single_cost_stress_dict_schema_counts_5bps_survivor(self) -> None:
        metrics = {
            "branch_path": "TrendExpansion -> CryptoKstCoppockMomentum -> bybit_injusdt_kst_coppock_momentum_30m_exact_v1",
            "cost_stress": {
                "package_id": "bybit-injusdt-30m-kst-coppock-momentum-exact-v1",
                "symbol": "INJUSDT",
                "timeframe": "30m",
                "trade_count": 23,
                "net_after_5bps_side_pct": 12.16,
            },
        }
        candidate = {
            "candidate_status": "no_trade",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": [],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.34,
                "hybrid_transition_hazard": 1.0,
                "pda_hybrid_alignment": False,
                "ranker_validation_ready": False,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": False,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertEqual(
            built["gate1"]["legacy_fixed_cost_readback_survivors"],
            ["bybit-injusdt-30m-kst-coppock-momentum-exact-v1"],
        )
        self.assertNotIn("no_real_cost_5bps_survivor", built["blockers"])
        self.assertNotEqual(built["decision"], "drop_gate1_economics")

    def test_cost_stress_rows_schema_counts_5bps_survivor(self) -> None:
        metrics = {
            "branch_path": "TrendExpansion -> ElectricalEquipmentGannHiloActivator -> gann_hilo_activator -> ibkr_etn_5m_quality",
            "cost_stress_rows": [
                {
                    "label": "ETN/5m/quality",
                    "package_id": "ibkr-etn-electrical-equipment-gann-hilo-activator-5m-quality-exact-gate1-v1",
                    "timeframe": "5m",
                    "trade_count": 123,
                    "5bps_per_side_total_profit_pct": 6.35,
                }
            ],
        }
        candidate = {
            "candidate_status": "no_trade",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": [],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.18,
                "hybrid_transition_hazard": 0.36,
                "pda_hybrid_alignment": True,
                "ranker_validation_ready": False,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": False,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertEqual(built["gate1"]["legacy_fixed_cost_readback_survivors"], ["ETN/5m/quality"])
        self.assertNotIn("no_real_cost_5bps_survivor", built["blockers"])

    def test_futures_instrument_cost_survivor_is_real_cost_even_when_5bps_stress_fails(self) -> None:
        metrics = {
            "branch_path": "RangeReversion -> FuturesCostRevival -> factor_v1",
            "branch_fields_preserved": True,
            "regime_confidence": 0.97,
            "long_run_expectancy_after_declared_friction": 8.42,
            "leakage_check": "pass",
            "provider_state": "ready",
            "raw_scored_mature_rows": 30,
            "production_validation_rows": 30,
            "observation_validation_rows": 30,
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
        }
        candidate = {
            "candidate_status": "execution_observe_only",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": [],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                    "regime_confidence": 0.97,
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.34,
                "ranker_validation_ready": False,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": False,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertEqual(built["gate1"]["legacy_fixed_cost_readback_survivors"], [])
        self.assertEqual(built["gate1"]["exact_instrument_cost_survivors"], ["NQ/5m/cost_revival"])
        self.assertEqual(built["gate1"]["exact_real_cost_survivors"], ["NQ/5m/cost_revival"])
        self.assertTrue(built["gate1"]["has_real_cost_survivor"])
        self.assertNotIn("no_real_cost_survivor", built["blockers"])
        self.assertNotIn("no_real_cost_5bps_survivor", built["blockers"])

    def test_futures_5bps_stress_survivor_without_instrument_cost_is_not_real_cost(self) -> None:
        metrics = {
            "branch_path": "TrendExpansion -> OpeningDrive -> tomac_nq_cost_wall_false_positive_v1",
            "branch_fields_preserved": True,
            "regime_confidence": 0.97,
            "long_run_expectancy_after_declared_friction": 1.25,
            "leakage_check": "pass",
            "provider_state": "ready",
            "raw_scored_mature_rows": 30,
            "production_validation_rows": 30,
            "observation_validation_rows": 30,
            "rows": [
                {
                    "factor_id": "tomac_nq_cost_wall_false_positive_v1",
                    "trade_count": 1362,
                    "survives_5bps_density": True,
                    "cost_5bps_side_pct": 1.25,
                    "cost_stress_5bps_role": "telemetry_not_futures_hard_gate",
                }
            ],
        }
        candidate = {
            "candidate_status": "trade_candidate",
            "actionable": True,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": [],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                    "regime_confidence": 0.97,
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.72,
                "ranker_validation_ready": True,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": True,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertEqual(built["gate1"]["legacy_fixed_cost_readback_survivors"], ["tomac_nq_cost_wall_false_positive_v1"])
        self.assertEqual(built["gate1"]["exact_instrument_cost_survivors"], [])
        self.assertEqual(built["gate1"]["exact_real_cost_survivors"], [])
        self.assertEqual(built["gate1"]["cost_gate_authority"], "none")
        self.assertIn("no_real_cost_survivor", built["blockers"])

    def test_futures_instrument_cost_authority_wins_over_5bps_stress_telemetry(self) -> None:
        metrics = {
            "branch_path": "TrendExpansion -> OpeningDrive -> tomac_nq_verified_real_cost_v1",
            "branch_fields_preserved": True,
            "cost_gate_authority": "instrument_cost",
            "survivors_instrument_cost": ["tomac_nq_verified_real_cost_v1"],
            "rows": [
                {
                    "factor_id": "tomac_nq_verified_real_cost_v1",
                    "symbol": "NQ",
                    "asset_class": "futures",
                    "trade_count": 1362,
                    "survives_5bps_density": True,
                    "cost_5bps_side_pct": 1.25,
                    "survives_instrument_cost": True,
                    "instrument_cost_total_profit_pct": 7.40,
                    "cost_profile_id": "CME_NQ_IBKR_verified_20260530_v1",
                    "cost_model_status": "verified_ibkr_broker_side",
                    "cost_model_verified_for_promotion": True,
                    "cost_stress_5bps_role": "telemetry_not_futures_hard_gate",
                }
            ],
        }
        candidate = {
            "candidate_status": "execution_observe_only",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": [],
                "evidence_assignments": {"regime_profit_branch_path": metrics["branch_path"]},
            },
        }
        tree = {"output": {}}

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertEqual(built["gate1"]["legacy_fixed_cost_readback_survivors"], ["tomac_nq_verified_real_cost_v1"])
        self.assertEqual(built["gate1"]["exact_instrument_cost_survivors"], ["tomac_nq_verified_real_cost_v1"])
        self.assertEqual(built["gate1"]["exact_real_cost_survivors"], ["tomac_nq_verified_real_cost_v1"])
        self.assertEqual(built["gate1"]["cost_gate_authority"], "instrument_cost")

    def test_pass_hard_pre_bayes_status_is_not_a_blocker(self) -> None:
        metrics = {
            "branch_path": "RangeReversion -> BybitLiquiditySweep -> exact -> factor",
            "cost_row": {
                "package_id": "bybit-dogeusdt-15m-stoprun-reclaim-exact-v1",
                "trade_count": 7,
                "net_after_5bps_side_pct": 1.24,
            },
        }
        candidate = {
            "candidate_status": "no_trade",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_hard",
                "conflict_flags": [],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.54,
                "hybrid_transition_hazard": 1.0,
                "pda_hybrid_alignment": False,
                "ranker_validation_ready": False,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": False,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertNotIn("pre_bayes_pass_hard", built["blockers"])

    def test_single_cost_row_schema_counts_5bps_survivor(self) -> None:
        metrics = {
            "branch_path": "TrendExpansion -> BybitLayer2KeltnerAtrPullback -> exact -> factor",
            "cost_row": {
                "package_id": "bybit-arbusdt-1h-keltner-atr-pullback-exact-v1",
                "trade_count": 6,
                "net_after_5bps_side_pct": 4.24,
            },
        }
        candidate = {
            "candidate_status": "no_trade",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass",
                "conflict_flags": [],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.34,
                "hybrid_transition_hazard": None,
                "pda_hybrid_alignment": True,
                "ranker_validation_ready": False,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": False,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertEqual(
            built["gate1"]["legacy_fixed_cost_readback_survivors"],
            ["bybit-arbusdt-1h-keltner-atr-pullback-exact-v1"],
        )
        self.assertNotIn("no_real_cost_5bps_survivor", built["blockers"])
        self.assertNotEqual(built["decision"], "drop_gate1_economics")

    def test_nested_provider_row_labels_are_preserved_for_canonical_branch(self) -> None:
        metrics = {
            "branch_path": "RangeReversion -> ConnorsRsi2Rebound30mExact -> factor",
            "provider_row": {
                "provider": "bybit_public",
                "symbol": "AAVEUSDT",
                "timeframe": "30m",
                "category": "linear",
            },
            "cost_row": {
                "package_id": "aave-30m-v1",
                "trade_count": 7,
                "net_after_5bps_side_pct": 3.05,
            },
        }
        candidate = {
            "candidate_status": "no_trade",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass",
                "conflict_flags": [],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.31,
                "hybrid_transition_hazard": 0.64,
                "pda_hybrid_alignment": True,
                "ranker_validation_ready": False,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": False,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertEqual(
            built["branch_labels"],
            {
                "provider": "bybit_public",
                "symbol": "AAVEUSDT",
                "timeframe": "30m",
                "category": "linear",
            },
        )
        self.assertFalse(built["branch_normalization_warnings"])

    def test_branch_labels_keep_portability_fields(self) -> None:
        metrics = {
            "provider_row": {
                "market": "FUTURES",
                "product": "equity_index",
                "provider": "IBKR",
                "symbol": "M2K",
                "contract": "202606",
                "timeframe": "1m",
                "base_timeframe": "1m",
                "ladder_timeframes": "1m/5m/15m/30m/1h/4h/1d",
                "window": "7 D",
                "duration": "7 D",
                "category": "futures",
            }
        }

        labels = report.extract_branch_labels(metrics)

        self.assertEqual(labels["contract"], "202606")
        self.assertEqual(labels["base_timeframe"], "1m")
        self.assertEqual(labels["ladder_timeframes"], "1m/5m/15m/30m/1h/4h/1d")
        self.assertEqual(labels["window"], "7 D")
        self.assertEqual(labels["duration"], "7 D")

    def test_nested_labels_are_preserved_in_blocker_report(self) -> None:
        metrics = {
            "branch_path": "TrendExpansion -> CryptoKstCoppockMomentum -> factor",
            "labels": {
                "market": "CryptoLinearPerp",
                "provider": "Bybit public linear",
                "symbols": "FILUSDT/INJUSDT",
                "timeframes": "1m/5m/15m/30m/1h/4h/1d",
                "window": "2026-02-17..2026-05-17",
            },
            "cost_stress": [],
        }
        candidate = {
            "candidate_status": "no_trade",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": None,
                "conflict_flags": [],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {"output": {}}

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertTrue(built["canonical_root_ok"])
        self.assertEqual(built["branch_labels"]["symbols"], "FILUSDT/INJUSDT")
        self.assertEqual(built["branch_labels"]["timeframes"], "1m/5m/15m/30m/1h/4h/1d")

    def test_non_main_regime_root_is_reported_as_violation(self) -> None:
        metrics = {
            "branch_path": "PublicStrategyDiversity -> KeltnerChannel -> factor",
            "cost_row": {
                "package_id": "legacy-keltner",
                "trade_count": 4,
                "net_after_5bps_side_pct": 0.25,
            },
        }
        candidate = {
            "candidate_status": "no_trade",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass",
                "conflict_flags": [],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {"output": {"execution_readiness": 0.1}}

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertFalse(built["canonical_root_ok"])
        self.assertEqual(built["branch_path_violations"], ["non_main_regime_root:PublicStrategyDiversity"])
        self.assertIn(
            "branch_path_violation:non_main_regime_root:PublicStrategyDiversity",
            built["blockers"],
        )
        self.assertEqual(built["decision"], "repair_branch_path_to_canonical_regime_root")

    def test_gate1_branch_path_template_is_used_as_current_schema_branch(self) -> None:
        metrics = {
            "branch_fields_preserved": True,
            "branch_path_template": (
                "TrendExpansion -> MicroTrendPullbackReclaim -> "
                "ibkr_futures_micro_trend_pullback_reclaim_gate1_v1"
            ),
            "branch_paths": [
                "TrendExpansion -> MicroTrendPullbackReclaim -> "
                "ibkr_futures_micro_trend_pullback_reclaim_gate1_v1"
            ],
            "exact_1m_survivors_5bps": ["MGC/dense/1m"],
            "provider_rows": [
                {
                    "market": "FUTURES",
                    "product": "precious_metals",
                    "provider": "IBKR",
                    "symbol": "MGC",
                    "timeframe": "1m",
                    "duration": "2 D",
                }
            ],
        }
        candidate = {
            "candidate_status": "no_trade",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": [],
                "evidence_assignments": {
                    "market_state_primary_regime": "TrendExpansion",
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.0,
                "hybrid_transition_hazard": 1.0,
                "pda_hybrid_alignment": False,
                "ranker_validation_ready": False,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": False,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertEqual(built["canonical_branch_path"], metrics["branch_path_template"])
        self.assertTrue(built["canonical_root_ok"])
        self.assertEqual(built["branch_path_violations"], [])
        self.assertNotIn("branch_path_violation:missing_known_main_regime", built["blockers"])

    def test_multisymbol_gate1_labels_follow_exact_5bps_survivor(self) -> None:
        metrics = {
            "branch_fields_preserved": True,
            "branch_path_template": (
                "TrendExpansion -> MicroTrendPullbackReclaim -> "
                "ibkr_futures_micro_trend_pullback_reclaim_gate1_v1"
            ),
            "exact_1m_survivors_5bps": ["MGC/dense/1m"],
            "provider_rows": [
                {
                    "product": "equity_index",
                    "provider": "IBKR",
                    "symbol": "MES",
                    "timeframe": "1m",
                    "duration": "2 D",
                },
                {
                    "product": "precious_metals",
                    "provider": "IBKR",
                    "symbol": "MGC",
                    "timeframe": "1m",
                    "duration": "2 D",
                },
            ],
        }
        candidate = {
            "candidate_status": "no_trade",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": [],
            },
        }
        tree = {"output": {}}

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertEqual(built["branch_labels"]["symbol"], "MGC")
        self.assertEqual(built["branch_labels"]["product"], "precious_metals")

    def test_validation_shortfalls_are_explicit_blockers_for_repaired_feedback_replay(self) -> None:
        metrics = {
            "branch_fields_preserved": True,
            "branch_path": (
                "TrendExpansion -> RootEvidencePullbackMssCisd -> "
                "strict_trend_root_pullback_mss_cisd"
            ),
            "selected_gate1_row": {
                "label": "MES/dense/15m",
                "trade_count": 12,
                "net_after_declared_friction_pct": 0.41,
                "survives_5bps_per_side": True,
            },
            "regime_confidence": 0.96,
            "raw_scored_mature_rows": 12,
            "production_validation_rows": 12,
            "observation_validation_rows": 12,
        }
        candidate = {
            "candidate_status": "trade_candidate",
            "actionable": True,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": [],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.72,
                "hybrid_transition_hazard": 0.39,
                "pda_hybrid_alignment": True,
                "ranker_validation_ready": False,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": False,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertEqual(built["gate1"]["legacy_fixed_cost_readback_survivors"], ["MES/dense/15m"])
        self.assertEqual(built["validation"]["raw_scored_mature_rows"], 12)
        self.assertEqual(built["validation"]["raw_scored_mature_shortfall_rows"], 18)
        self.assertEqual(built["validation"]["production_validation_shortfall_rows"], 18)
        self.assertEqual(built["validation"]["observation_validation_shortfall_rows"], 18)
        self.assertIn("raw_scored_mature_below_30", built["blockers"])
        self.assertIn("production_validation_below_30", built["blockers"])
        self.assertIn("observation_validation_below_30", built["blockers"])
        self.assertEqual(built["decision"], "learning_admitted_paper_observe")
        self.assertIn("same-root feedback", built["next_action"])

    def test_tomac_rows_supply_declared_friction_and_soft_regime_confidence(self) -> None:
        metrics = {
            "branch_path": (
                "TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> "
                "tomac_nq_bidir_opening_drive_t10_w0_e900_x1245_exact_v1"
            ),
            "decision": "exact_aq_5bps_density_survivor",
            "rows": [
                {
                    "factor_id": "tomac_nq_bidir_opening_drive_t10_w0_e900_x1245_exact_v1",
                    "branch_path": (
                        "TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> "
                        "tomac_nq_bidir_opening_drive_t10_w0_e900_x1245_exact_v1"
                    ),
                    "trade_count": 985,
                    "cost_5bps_side_pct": 571.46,
                    "survives_5bps_density": True,
                }
            ],
        }
        candidate = {
            "candidate_status": "execution_observe_only",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": [],
                "soft_market_regime_distribution": {
                    "bull": 0.6222829194229538,
                    "range": 0.3777170805770462,
                    "bear": 0.0,
                },
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.4575,
                "hybrid_transition_hazard": 0.4264,
                "ranker_validation_ready": True,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": False,
                "split_reason_lineage": [
                    "path_ranker=Ranker validation: raw_scored_mature=1226/30 production_validation=1226/30 observation_validation=33/30 ready=true"
                ],
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertEqual(
            built["gate1"]["legacy_fixed_cost_readback_survivors"],
            ["tomac_nq_bidir_opening_drive_t10_w0_e900_x1245_exact_v1"],
        )
        self.assertEqual(built["pre_bayes"]["long_run_expectancy_after_declared_friction"], 571.46)
        self.assertEqual(built["pre_bayes"]["regime_confidence"], 0.6222829194229538)
        self.assertNotIn("declared_friction_expectancy_missing", built["blockers"])
        self.assertIn("regime_confidence_below_floor", built["blockers"])
        self.assertNotIn("regime_confidence_missing", built["blockers"])
        self.assertIn("execution readiness", built["next_action"])
        self.assertNotIn("validation rows", built["next_action"])

    def test_pda_false_is_telemetry_not_basic_gate_blocker(self) -> None:
        metrics = {
            "branch_fields_preserved": True,
            "branch_path": (
                "RangeConsolidation -> TightRangeBandExpansionFade -> "
                "ibkr_si5m_dense_fade"
            ),
            "selected_gate1_row": {
                "label": "SI/dense_fade/5m",
                "symbol": "SI",
                "asset_class": "futures",
                "trade_count": 36,
                "net_after_declared_friction_pct": 0.73,
                "survives_5bps_per_side": True,
                "survives_instrument_cost": True,
                "instrument_cost_total_profit_pct": 0.61,
                "cost_profile_id": "COMEX_SI_IBKR_verified_20260530_v1",
                "cost_model_status": "verified_ibkr_broker_side",
                "cost_model_verified_for_promotion": True,
                "cost_stress_5bps_role": "telemetry_not_futures_hard_gate",
            },
            "regime_confidence": 0.96,
            "raw_scored_mature_rows": 30,
            "production_validation_rows": 30,
            "observation_validation_rows": 30,
        }
        candidate = {
            "candidate_status": "trade_candidate",
            "actionable": True,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": ["pda_sequence_family_disagreement"],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.72,
                "hybrid_transition_hazard": 0.39,
                "pda_hybrid_alignment": False,
                "ranker_validation_ready": True,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": True,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertNotIn("pda_hybrid_alignment", built["downstream"])
        self.assertNotIn("transition_hazard", built["downstream"])
        self.assertNotIn("pda_hybrid_alignment_not_true", built["blockers"])
        self.assertNotIn(
            "pre_bayes_conflict:pda_sequence_family_disagreement",
            built["blockers"],
        )
        self.assertEqual(built["blockers"], [])
        self.assertEqual(built["decision"], "candidate_meets_current_gate_shape")
        lifecycle = built["factor_profitability_lifecycle"]
        self.assertEqual(lifecycle["live_trade"]["status"], "ready")
        self.assertFalse(lifecycle["live_trade"]["extension_complete"])
        self.assertFalse(lifecycle["live_trade"]["promotion_allowed"])
        self.assertFalse(built["promotion_allowed"])
        self.assertFalse(built["trade_usable"])

        rendered = report.render_markdown(built)

        self.assertNotIn("pda_hybrid_alignment", rendered)
        self.assertNotIn("transition_hazard", rendered)
        self.assertIn("live_trade_status: `ready`", rendered)
        self.assertIn("extension_complete: `False`", rendered)
        self.assertIn("promotion_allowed: `False`", rendered)
        self.assertIn("trade_usable: `False`", rendered)

    def test_pda_regime_family_disagreement_is_telemetry_not_learning_blocker(self) -> None:
        metrics = {
            "branch_fields_preserved": True,
            "branch_path": (
                "TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> "
                "tomac_nq_bidir_opening_drive_t10_w0_e900_x1245_exact_v1"
            ),
            "selected_gate1_row": {
                "label": "opening-drive/exact-parent",
                "trade_count": 1226,
                "net_after_declared_friction_pct": 571.46,
                "survives_5bps_per_side": True,
            },
            "regime_confidence": 0.96,
            "raw_scored_mature_rows": 1226,
            "production_validation_rows": 1226,
            "observation_validation_rows": 33,
        }
        candidate = {
            "candidate_status": "trade_candidate",
            "actionable": True,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": ["pda_regime_family_disagreement"],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.72,
                "hybrid_transition_hazard": 0.39,
                "pda_hybrid_alignment": False,
                "ranker_validation_ready": True,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": True,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertNotIn(
            "pre_bayes_conflict:pda_regime_family_disagreement",
            built["blockers"],
        )
        self.assertEqual(built["factor_profitability_lifecycle"]["learning_admission"]["status"], "admitted")

    def test_regime_positive_sparse_candidate_is_learning_admitted_not_dropped(self) -> None:
        metrics = {
            "branch_fields_preserved": True,
            "branch_path": (
                "TrendExpansion -> IntradayMomentum -> declared_friction_edge -> "
                "sparse_positive_v1"
            ),
            "rank_total_trade_count": 8,
            "long_run_expectancy_after_declared_friction": 0.012,
            "provider_state": "ready",
            "leakage_check": "pass",
            "cost_stress": [],
            "raw_scored_mature_rows": 8,
            "production_validation_rows": 8,
            "observation_validation_rows": 8,
        }
        candidate = {
            "candidate_status": "no_trade",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": [],
                "evidence_quality_score": 0.96,
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                    "regime_confidence": 0.96,
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.41,
                "hybrid_transition_hazard": 0.72,
                "pda_hybrid_alignment": False,
                "ranker_validation_ready": False,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": False,
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        lifecycle = built["factor_profitability_lifecycle"]
        self.assertEqual(built["decision"], "learning_admitted_paper_observe")
        self.assertEqual(lifecycle["learning_admission"]["status"], "admitted")
        self.assertEqual(lifecycle["paper_admission"]["status"], "observe")
        self.assertEqual(lifecycle["live_trade"]["status"], "blocked")
        self.assertFalse(built["promotion_allowed"])
        self.assertFalse(built["trade_usable"])
        self.assertFalse(lifecycle["live_trade"]["promotion_allowed"])
        self.assertIn(
            "no_real_cost_survivor",
            lifecycle["paper_admission"]["blockers"],
        )

    def test_validation_rows_can_be_parsed_from_execution_lineage(self) -> None:
        metrics = {
            "branch_fields_preserved": True,
            "branch_path": (
                "RangeConsolidation -> VolatilityCompression -> "
                "DataSecurityTtmSqueezeReclaim -> ttm_squeeze_reclaim"
            ),
            "selected_gate1_row": {
                "label": "RBRK/15m/dense",
                "trade_count": 33,
                "net_after_declared_friction_pct": 0.58,
                "survives_5bps_per_side": True,
            },
            "regime_confidence": 0.96,
        }
        candidate = {
            "candidate_status": "execution_observe_only",
            "actionable": False,
            "pre_bayes_evidence_filter": {
                "gating_status": "pass_neutralized",
                "conflict_flags": [],
                "evidence_assignments": {
                    "regime_profit_branch_path": metrics["branch_path"],
                },
            },
        }
        tree = {
            "output": {
                "execution_readiness": 0.67,
                "hybrid_transition_hazard": 0.679,
                "ranker_validation_ready": True,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": True,
                "split_reason_lineage": [
                    (
                        "execution_readiness_validation_floor=0.6700 "
                        "raw_execution_readiness=0.5265 "
                        "raw_scored_mature=961/30 "
                        "production_validation=961/30 "
                        "observation_validation=30/30"
                    )
                ],
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gate1_path = root / "gate1.json"
            candidate_path = root / "candidate.json"
            tree_path = root / "tree.json"
            gate1_path.write_text(__import__("json").dumps(metrics), encoding="utf-8")
            candidate_path.write_text(__import__("json").dumps(candidate), encoding="utf-8")
            tree_path.write_text(__import__("json").dumps(tree), encoding="utf-8")

            built = report.build_report(gate1_path, candidate_path, tree_path)

        self.assertEqual(built["validation"]["raw_scored_mature_rows"], 961)
        self.assertEqual(built["validation"]["production_validation_rows"], 961)
        self.assertEqual(built["validation"]["observation_validation_rows"], 30)
        self.assertNotIn("raw_scored_mature_below_30", built["blockers"])
        self.assertNotIn("production_validation_below_30", built["blockers"])
        self.assertNotIn("observation_validation_below_30", built["blockers"])
        self.assertNotIn("execution_readiness_below_live_floor", built["blockers"])
        self.assertEqual(built["decision"], "learning_admitted_paper_observe")


if __name__ == "__main__":
    unittest.main()
