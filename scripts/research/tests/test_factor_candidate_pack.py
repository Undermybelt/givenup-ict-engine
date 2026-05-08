from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import factor_candidate_pack as pack  # noqa: E402


class FactorCandidatePackTests(unittest.TestCase):
    def test_build_candidate_pack_uses_candidate_spec_and_cross_market_metrics(self) -> None:
        manifest = {
            "manifest_version": "1.0",
            "timeframe": "15m",
            "strategies": [
                {
                    "name": "TrendPullbackDense15m",
                    "status": "ok",
                    "metadata": {
                        "strategy": "TrendPullbackDense15m",
                        "mutation_id": "slice-083",
                        "base_factor": "trend_pullback",
                        "hypothesis": "pullback after higher timeframe trend continuation",
                        "paradigm": "trend",
                        "expected_regime": "expansion",
                        "factors_used": ["ema_fast", "ema_slow", "pullback_zone"],
                        "asset_class": "index_futures",
                    },
                    "validation_metrics": {
                        "sharpe": 1.42,
                        "trade_count": 87,
                        "win_rate_pct": 54.5,
                        "profit_factor": 1.85,
                        "total_profit_pct": 12.3,
                        "max_drawdown_pct": -3.2,
                    },
                    "per_pair_metrics": {
                        "NQ/USD": {"sharpe": 1.42, "trade_count": 87, "win_rate_pct": 54.5},
                        "SPY/USD": {"sharpe": 1.10, "trade_count": 50, "win_rate_pct": 56.0},
                        "GLD/USD": {"sharpe": 0.72, "trade_count": 34, "win_rate_pct": 53.0},
                    },
                }
            ],
        }
        candidate_spec = {
            "expression_text": "ema_fast > ema_slow and pullback_zone <= 0.4",
            "operator_set": ["ema", "pullback_zone", "trend_gate"],
            "complexity": 3,
            "target_market_hypothesis": ["NQ", "SPY", "GLD"],
            "base_timeframe": "15m",
            "context_timeframes": ["1h", "4h"],
            "pre_bayes_targets": ["filtered_resonance_label", "factor_uncertainty"],
            "belief_targets": ["entry_quality", "multi_timeframe_resonance"],
            "path_ranking_targets": ["experience_prior", "current_posterior"],
            "execution_tree_targets": ["execution_readiness", "prediction_vote_score"],
            "structural_feedback_required": True,
            "resonance_summary": {
                "base_timeframe": "15m",
                "context_stack": ["1h", "4h"],
                "resonance_by_timeframe": {"1h": "aligned", "4h": "aligned"},
            },
            "regime_role": "mixed",
        }
        autoresearch_status = {
            "effective_status": "completed",
            "best_attempt": {
                "attempt_id": "attempt-3",
                "decision": {"score_delta": 0.19, "status": "keep"},
            },
            "decision_counts": {"keep": 2, "discard": 1},
            "failure_tag_counts": {"thin_trade_count": 1},
        }

        bundle = pack.build_factor_candidate_pack(
            manifest=manifest,
            strategy_name="TrendPullbackDense15m",
            candidate_spec=candidate_spec,
            autoresearch_status=autoresearch_status,
        )

        self.assertEqual(
            bundle["factor_expression"]["strategy_name"],
            "TrendPullbackDense15m",
        )
        self.assertEqual(
            bundle["factor_expression"]["expression_text"],
            "ema_fast > ema_slow and pullback_zone <= 0.4",
        )
        self.assertEqual(
            bundle["factor_expression"]["filter_belief_execution_mapping"]["pre_bayes_targets"],
            ["filtered_resonance_label", "factor_uncertainty"],
        )
        self.assertEqual(
            bundle["factor_expression"]["filter_belief_execution_mapping"]["execution_tree_targets"],
            ["execution_readiness", "prediction_vote_score"],
        )
        self.assertTrue(
            bundle["factor_expression"]["filter_belief_execution_mapping"]["structural_feedback_required"]
        )
        self.assertEqual(
            bundle["factor_eval_grid_summary"]["trade_density_summary"]["aggregate_label"],
            "preferred_density",
        )
        self.assertEqual(
            bundle["factor_eval_grid_summary"]["breadth_matrix"]["SPY/USD"]["status"],
            "covered",
        )
        self.assertEqual(
            bundle["transfer_score"]["status"],
            "cross_market_candidate",
        )
        self.assertGreater(bundle["transfer_score"]["overall_transfer_score"], 0.5)

    def test_build_candidate_pack_falls_back_to_manifest_hypothesis(self) -> None:
        manifest = {
            "manifest_version": "1.0",
            "timeframe": "1h",
            "strategies": [
                {
                    "name": "VRPCarry",
                    "status": "ok",
                    "metadata": {
                        "strategy": "VRPCarry",
                        "mutation_id": "slice-140",
                        "base_factor": "vrp_carry",
                        "hypothesis": "carry-style compression regime harvest",
                        "paradigm": "carry",
                        "expected_regime": "compression",
                        "factors_used": ["rv_zscore", "value_zone"],
                        "asset_class": "index_futures",
                    },
                    "validation_metrics": {
                        "sharpe": 0.83,
                        "trade_count": 12,
                        "win_rate_pct": 58.0,
                        "profit_factor": 1.21,
                    },
                    "per_pair_metrics": {
                        "NQ/USD": {"sharpe": 0.83, "trade_count": 12, "win_rate_pct": 58.0}
                    },
                }
            ],
        }

        bundle = pack.build_factor_candidate_pack(manifest=manifest)

        self.assertEqual(
            bundle["factor_expression"]["expression_text"],
            "carry-style compression regime harvest",
        )
        self.assertEqual(
            bundle["factor_expression"]["operator_set"],
            ["rv_zscore", "value_zone"],
        )
        self.assertEqual(
            bundle["factor_expression"]["filter_belief_execution_mapping"]["pre_bayes_targets"],
            [],
        )
        self.assertFalse(
            bundle["factor_expression"]["filter_belief_execution_mapping"]["structural_feedback_required"]
        )
        self.assertEqual(
            bundle["factor_eval_grid_summary"]["trade_density_summary"]["aggregate_label"],
            "probe_only",
        )
        self.assertEqual(bundle["transfer_score"]["status"], "single_market_only")

    def test_main_writes_artifacts(self) -> None:
        manifest = {
            "manifest_version": "1.0",
            "timeframe": "5m",
            "strategies": [
                {
                    "name": "SweepReclaimWide",
                    "status": "ok",
                    "metadata": {
                        "strategy": "SweepReclaimWide",
                        "mutation_id": "slice-086",
                        "base_factor": "sweep_reclaim",
                        "hypothesis": "wide liquidity sweep reclaim",
                        "paradigm": "reversal",
                        "expected_regime": "liquidity_sweep",
                        "factors_used": ["sweep_window", "reclaim_gate"],
                        "asset_class": "index_futures",
                    },
                    "validation_metrics": {
                        "sharpe": 1.12,
                        "trade_count": 31,
                        "win_rate_pct": 51.0,
                        "profit_factor": 1.33,
                    },
                    "per_pair_metrics": {
                        "NQ/USD": {"sharpe": 1.12, "trade_count": 31, "win_rate_pct": 51.0},
                        "ES/USD": {"sharpe": 0.65, "trade_count": 16, "win_rate_pct": 49.0},
                    },
                }
            ],
        }
        candidate_spec = {
            "base_timeframe": "5m",
            "context_timeframes": ["15m", "1h", "4h"],
            "regime_role": "execution_only",
        }

        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = root / "strategy_library.json"
            spec_path = root / "candidate_spec.json"
            output_dir = root / "out"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            spec_path.write_text(json.dumps(candidate_spec), encoding="utf-8")

            exit_code = pack.main(
                [
                    "--manifest-json",
                    str(manifest_path),
                    "--strategy-name",
                    "SweepReclaimWide",
                    "--candidate-spec-json",
                    str(spec_path),
                    "--output-dir",
                    str(output_dir),
                ]
            )

            self.assertEqual(exit_code, 0)
            expression = json.loads(
                (output_dir / "factor_expression.json").read_text(encoding="utf-8")
            )
            grid = json.loads(
                (output_dir / "factor_eval_grid_summary.json").read_text(
                    encoding="utf-8"
                )
            )
            transfer = json.loads(
                (output_dir / "transfer_score.json").read_text(encoding="utf-8")
            )

            self.assertEqual(expression["strategy_name"], "SweepReclaimWide")
            self.assertEqual(grid["selected_strategy"], "SweepReclaimWide")
            self.assertEqual(transfer["covered_market_count"], 2)


if __name__ == "__main__":
    unittest.main()
