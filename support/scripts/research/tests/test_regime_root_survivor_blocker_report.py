from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import regime_root_survivor_blocker_report as report  # noqa: E402


class RegimeRootSurvivorBlockerReportTests(unittest.TestCase):
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
        self.assertEqual(built["gate1"]["exact_5bps_survivors"], ["net-5m-v1"])
        self.assertTrue(built["canonical_root_ok"])
        self.assertEqual(built["branch_path_violations"], [])
        self.assertNotIn("no_real_cost_5bps_survivor", built["blockers"])
        self.assertNotIn("pre_bayes_pass_neutralized", built["blockers"])
        self.assertNotEqual(built["decision"], "drop_gate1_economics")

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
            built["gate1"]["exact_5bps_survivors"],
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

        self.assertEqual(built["gate1"]["exact_5bps_survivors"], ["ETN/5m/quality"])
        self.assertNotIn("no_real_cost_5bps_survivor", built["blockers"])

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
            built["gate1"]["exact_5bps_survivors"],
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
                "survives_5bps_per_side": True,
            },
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

        self.assertEqual(built["gate1"]["exact_5bps_survivors"], ["MES/dense/15m"])
        self.assertEqual(built["validation"]["raw_scored_mature_rows"], 12)
        self.assertEqual(built["validation"]["raw_scored_mature_shortfall_rows"], 18)
        self.assertEqual(built["validation"]["production_validation_shortfall_rows"], 18)
        self.assertEqual(built["validation"]["observation_validation_shortfall_rows"], 18)
        self.assertIn("raw_scored_mature_below_30", built["blockers"])
        self.assertIn("production_validation_below_30", built["blockers"])
        self.assertIn("observation_validation_below_30", built["blockers"])
        self.assertEqual(built["decision"], "repair_same_root_validation_rows")
        self.assertIn("same-root feedback", built["next_action"])

    def test_pda_false_is_telemetry_not_basic_gate_blocker(self) -> None:
        metrics = {
            "branch_fields_preserved": True,
            "branch_path": (
                "RangeConsolidation -> TightRangeBandExpansionFade -> "
                "ibkr_si5m_dense_fade"
            ),
            "selected_gate1_row": {
                "label": "SI/dense_fade/5m",
                "trade_count": 36,
                "survives_5bps_per_side": True,
            },
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

        self.assertFalse(built["downstream"]["pda_hybrid_alignment"])
        self.assertNotIn("pda_hybrid_alignment_not_true", built["blockers"])
        self.assertNotIn(
            "pre_bayes_conflict:pda_sequence_family_disagreement",
            built["blockers"],
        )
        self.assertEqual(built["blockers"], [])
        self.assertEqual(built["decision"], "candidate_meets_current_gate_shape")

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
                "survives_5bps_per_side": True,
            },
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
        self.assertEqual(built["decision"], "observe_only_execution_blocked")


if __name__ == "__main__":
    unittest.main()
