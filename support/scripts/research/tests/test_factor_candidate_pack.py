from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import zipfile

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import factor_candidate_pack as pack  # noqa: E402
import factor_signal_diagnostics as diagnostics  # noqa: E402


class FactorCandidatePackTests(unittest.TestCase):
    def test_build_manifest_from_freqtrade_backtest_zip_extracts_strategy_metrics(self) -> None:
        backtest_payload = {
            "strategy": {
                "TomacNQ_RegimeTrendPullbackDense15m": {
                    "strategy_name": "TomacNQ_RegimeTrendPullbackDense15m",
                    "results_per_pair": [
                        {
                            "key": "NQ/USD",
                            "trades": 103,
                            "winrate": 0.31,
                            "sharpe": 0.1211,
                            "profit_factor": 1.21,
                            "profit_total_pct": 3.92,
                            "max_drawdown_account": 0.0321,
                        },
                        {
                            "key": "TOTAL",
                            "trades": 103,
                            "winrate": 0.31,
                            "sharpe": 0.1211,
                            "profit_factor": 1.21,
                            "profit_total_pct": 3.92,
                            "max_drawdown_account": 0.0321,
                        },
                    ],
                    "total_trades": 103,
                    "wins": 32,
                    "losses": 71,
                    "draws": 0,
                    "sharpe": 0.1211,
                    "profit_factor": 1.21,
                    "profit_total": 0.0392,
                    "max_drawdown_account": 0.0321,
                    "backtest_start": "2023-01-01 00:00:00",
                    "backtest_end": "2025-12-31 00:00:00",
                    "timeframe": "15m",
                }
            }
        }
        config_payload = {"timeframe": "15m", "exchange": {"pair_whitelist": ["NQ/USD"]}}
        strategy_source = '''"""
Paradigm: regime-cluster trend pullback
Hypothesis: 15m pullback density unlock with 1h/4h resonance
Parent: TomacNQ_RegimeTrendPullbackDense
Status: density-via-timeframe probe
Uses MTF: yes
"""
'''

        with TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "backtest.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("backtest-result.json", json.dumps(backtest_payload))
                archive.writestr(
                    "backtest-result_config.json", json.dumps(config_payload)
                )
                archive.writestr(
                    "backtest-result_TomacNQ_RegimeTrendPullbackDense15m.py",
                    strategy_source,
                )

            manifest = pack.build_manifest_from_freqtrade_backtest_zip(zip_path)

        self.assertEqual(manifest["timeframe"], "15m")
        self.assertEqual(len(manifest["strategies"]), 1)
        strategy = manifest["strategies"][0]
        self.assertEqual(strategy["name"], "TomacNQ_RegimeTrendPullbackDense15m")
        self.assertEqual(strategy["metadata"]["paradigm"], "regime-cluster trend pullback")
        self.assertEqual(
            strategy["metadata"]["parent_strategy"],
            "TomacNQ_RegimeTrendPullbackDense",
        )
        self.assertTrue(strategy["metadata"]["uses_mtf"])
        self.assertEqual(strategy["validation_metrics"]["trade_count"], 103)
        self.assertEqual(strategy["validation_metrics"]["win_rate_pct"], 31.067961)
        self.assertEqual(
            strategy["per_pair_metrics"]["NQ/USD"]["max_drawdown_pct"],
            3.21,
        )

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
            "cross_market_metrics": {
                "GLD/USD": {
                    "sharpe": 0.641,
                    "trade_count": 140,
                    "win_rate_pct": 54.0,
                    "profit_factor": 1.44,
                    "total_profit_pct": 6.7,
                    "max_drawdown_pct": 5.2,
                    "window": "2025-05-07->2026-05-06",
                },
                "SPY/USD": {
                    "sharpe": 0.605,
                    "trade_count": None,
                    "win_rate_pct": None,
                    "profit_factor": None,
                    "total_profit_pct": None,
                    "max_drawdown_pct": None,
                    "window": "2025-05-07->2026-05-06",
                },
            },
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
            bundle["factor_eval_grid_summary"]["breadth_matrix"]["GLD/USD"]["status"],
            "covered",
        )
        self.assertEqual(
            bundle["factor_eval_grid_summary"]["breadth_matrix"]["SPY/USD"]["status"],
            "covered",
        )
        self.assertEqual(
            bundle["transfer_score"]["status"],
            "cross_market_candidate",
        )
        self.assertGreater(bundle["transfer_score"]["overall_transfer_score"], 0.45)
        self.assertEqual(
            bundle["transfer_score"]["profitability_status"],
            "declared_friction_missing",
        )
        self.assertIn("GLD/USD", bundle["transfer_score"]["covered_markets"])
        self.assertEqual(bundle["transfer_score"]["markets_without_trade_counts"], [])

    def test_build_candidate_pack_projects_regime_ladder_contract_fields(self) -> None:
        manifest = {
            "manifest_version": "1.0",
            "timeframe": "15m_with_4h_confirmation",
            "strategies": [
                {
                    "name": "SweepReclaim15mWide4hConfirm",
                    "status": "ok",
                    "metadata": {
                        "mutation_id": "sweep-ladder",
                        "base_factor": "sweep_quality",
                        "hypothesis": "15m sweep reclaim with 4h confirmation",
                        "paradigm": "regime-rooted liquidity sweep",
                        "expected_regime": "Transition",
                        "factors_used": ["liquidity_sweep_reclaim"],
                    },
                    "validation_metrics": {
                        "sharpe": 0.2452,
                        "trade_count": 62,
                        "win_rate_pct": 48.3871,
                        "profit_factor": 1.7157,
                        "total_profit_pct": 8.67,
                        "max_drawdown_pct": -1.9231,
                    },
                    "per_pair_metrics": {
                        "NQ/USD": {
                            "sharpe": 0.2452,
                            "trade_count": 62,
                            "win_rate_pct": 48.3871,
                            "profit_factor": 1.7157,
                        }
                    },
                }
            ],
        }
        branch_path = (
            "Transition -> LiquiditySweep -> sweep_reclaim_small_cycle -> "
            "liquidity_sweep_reclaim_15m_wide_v1"
        )
        candidate_spec = {
            "candidate_id": "liquidity_sweep_reclaim_ladder_v1",
            "family": "sweep_quality",
            "base_timeframe": "15m",
            "context_timeframes": ["5m", "1h", "4h"],
            "expected_regime": branch_path,
            "resonance_summary": {
                "base_timeframe": "15m",
                "context_stack": ["5m", "1h", "4h"],
                "resonance_by_timeframe": {
                    "5m": {"decision": "incubate", "trade_count": 100},
                    "15m": {"decision": "keep_small_cycle", "trade_count": 62},
                    "1h": {"decision": "lift_to_confirmation", "trade_count": 18},
                    "4h": {"decision": "handoff_confirmed", "trade_count": 62},
                },
            },
        }

        bundle = pack.build_factor_candidate_pack(
            manifest=manifest,
            strategy_name="SweepReclaim15mWide4hConfirm",
            candidate_spec=candidate_spec,
        )

        self.assertEqual(
            bundle["factor_expression"]["branch_path_contract"][
                "regime_profit_branch_path"
            ],
            branch_path,
        )
        self.assertEqual(
            bundle["factor_expression"]["branch_path_contract"]["main_regime"],
            "Transition",
        )
        self.assertEqual(
            bundle["factor_expression"]["branch_path_contract"]["profit_factor"],
            "liquidity_sweep_reclaim_15m_wide_v1",
        )
        self.assertEqual(
            bundle["factor_expression"]["branch_path_contract"]["training_timeframe"],
            "15m_and_5m",
        )
        self.assertEqual(
            bundle["factor_eval_grid_summary"]["timeframe_ladder_evidence"][
                "branch_path"
            ],
            branch_path,
        )
        self.assertEqual(
            bundle["factor_eval_grid_summary"]["timeframe_ladder_evidence"][
                "neutralization_timeframe"
            ],
            "1h",
        )
        self.assertEqual(
            bundle["transfer_score"]["branch_path_contract"][
                "regime_profit_branch_path"
            ],
            branch_path,
        )
        self.assertEqual(
            bundle["transfer_score"]["timeframe_ladder_transfer"][
                "high_timeframe_confirmation_result"
            ],
            "handoff_confirmed_not_promotion",
        )
        self.assertFalse(
            bundle["transfer_score"]["timeframe_ladder_transfer"]["promotion_allowed"]
        )

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

    def test_candidate_pack_emits_factor_profitability_lifecycle_for_regime_conditioned_edge(self) -> None:
        manifest = {
            "manifest_version": "1.0",
            "timeframe": "1m",
            "strategies": [
                {
                    "name": "SparseRegimeEdge",
                    "status": "ok",
                    "metadata": {
                        "strategy": "SparseRegimeEdge",
                        "mutation_id": "sparse-regime-edge",
                        "base_factor": "vwap_reclaim",
                        "hypothesis": "sparse but positive after declared friction",
                        "paradigm": "regime_conditioned",
                        "expected_regime": "TrendExpansion -> IntradayMomentum -> declared_friction_edge -> sparse_regime_edge_v1",
                        "factors_used": ["vwap", "rvol"],
                    },
                    "validation_metrics": {
                        "sharpe": 0.41,
                        "trade_count": 8,
                        "win_rate_pct": 62.5,
                        "profit_factor": 1.44,
                        "net_after_declared_friction_pct": 1.2,
                    },
                    "per_pair_metrics": {
                        "NQ/USD": {
                            "sharpe": 0.41,
                            "trade_count": 8,
                            "win_rate_pct": 62.5,
                            "profit_factor": 1.44,
                            "net_after_declared_friction_pct": 1.2,
                        }
                    },
                }
            ],
        }
        candidate_spec = {
            "candidate_id": "sparse_regime_edge_v1",
            "expected_regime": "TrendExpansion -> IntradayMomentum -> declared_friction_edge -> sparse_regime_edge_v1",
            "regime_confidence": 0.96,
            "regime_confidence_floor": 0.95,
            "provider_state": "ready",
            "leakage_check": "pass",
            "execution_readiness": 0.41,
            "transition_hazard": 0.72,
            "pda_hybrid_alignment": False,
            "execution_gate_status": "blocked",
            "timeframe_ladder_transfer": {
                "promotion_allowed": False,
                "trade_usable": False,
            },
        }

        bundle = pack.build_factor_candidate_pack(
            manifest=manifest,
            strategy_name="SparseRegimeEdge",
            candidate_spec=candidate_spec,
        )

        lifecycle = bundle["factor_eval_grid_summary"]["factor_profitability_lifecycle"]
        self.assertEqual(
            lifecycle["schema_version"],
            "factor-profitability-lifecycle/v1",
        )
        self.assertEqual(lifecycle["learning_admission"]["status"], "admitted")
        self.assertEqual(
            lifecycle["learning_admission"][
                "long_run_expectancy_after_declared_friction"
            ],
            1.2,
        )
        self.assertEqual(lifecycle["paper_admission"]["status"], "observe")
        self.assertEqual(lifecycle["live_trade"]["status"], "blocked")
        self.assertFalse(lifecycle["live_trade"]["promotion_allowed"])
        self.assertFalse(lifecycle["live_trade"]["trade_usable"])
        self.assertEqual(
            bundle["transfer_score"]["profitability_status"],
            "declared_friction_positive",
        )
        self.assertEqual(
            bundle["transfer_score"]["long_run_expectancy_after_declared_friction"],
            1.2,
        )
        self.assertFalse(
            bundle["transfer_score"]["timeframe_ladder_transfer"]["promotion_allowed"]
        )
        self.assertFalse(
            bundle["transfer_score"]["timeframe_ladder_transfer"]["trade_usable"]
        )

    def test_transfer_score_penalizes_raw_only_profit_without_declared_friction(self) -> None:
        manifest = {
            "manifest_version": "1.0",
            "timeframe": "15m",
            "strategies": [
                {
                    "name": "RawOnlyPrettyButCostUnproven",
                    "status": "ok",
                    "validation_metrics": {
                        "sharpe": 1.8,
                        "trade_count": 180,
                        "win_rate_pct": 61.0,
                        "profit_factor": 1.6,
                        "total_profit_pct": 4.8,
                    },
                    "per_pair_metrics": {
                        "SPY/USD": {"sharpe": 1.7, "trade_count": 160},
                        "QQQ/USD": {"sharpe": 1.9, "trade_count": 190},
                    },
                }
            ],
        }
        candidate_spec = {
            "candidate_id": "raw_only_pretty_but_cost_unproven_v1",
            "expected_regime": "TrendExpansion -> MomentumPersistence -> raw_only_pretty -> raw_only_pretty_but_cost_unproven_v1",
            "regime_confidence": 0.97,
            "provider_state": "ready",
            "leakage_check": "pass",
        }

        bundle = pack.build_factor_candidate_pack(
            manifest=manifest,
            strategy_name="RawOnlyPrettyButCostUnproven",
            candidate_spec=candidate_spec,
        )

        self.assertEqual(
            bundle["transfer_score"]["profitability_status"],
            "declared_friction_missing",
        )
        self.assertIn(
            "declared_friction_missing_raw_profit_only",
            bundle["transfer_score"]["profitability_blockers"],
        )
        self.assertEqual(
            bundle["factor_eval_grid_summary"]["factor_profitability_lifecycle"][
                "learning_admission"
            ]["status"],
            "blocked",
        )

    def test_build_strategy_library_manifest_from_freqtrade_backtest_zip(self) -> None:
        backtest_payload = {
            "strategy": {
                "TomacNQ_RegimeFVGRetrace": {
                    "strategy_name": "TomacNQ_RegimeFVGRetrace",
                    "results_per_pair": [
                        {
                            "key": "NQ/USD",
                            "trades": 12,
                            "winrate": 0.58333333,
                            "sharpe": 0.014993373176821853,
                            "profit_factor": 1.92,
                            "profit_total_pct": 0.57,
                            "max_drawdown_account": 0.00548,
                        },
                        {
                            "key": "TOTAL",
                            "trades": 12,
                            "winrate": 0.58333333,
                            "sharpe": 0.014993373176821853,
                            "profit_factor": 1.92,
                            "profit_total_pct": 0.57,
                            "max_drawdown_account": 0.00548,
                        },
                    ],
                    "total_trades": 12,
                    "wins": 7,
                    "losses": 5,
                    "draws": 0,
                    "sharpe": 0.014993373176821853,
                    "profit_factor": 1.92,
                    "profit_total": 0.0057,
                    "max_drawdown_account": 0.00548,
                    "backtest_start": "2018-01-01 00:00:00",
                    "backtest_end": "2025-12-31 00:00:00",
                    "timeframe": "1h",
                }
            }
        }
        config_payload = {"timeframe": "1h", "exchange": {"pair_whitelist": ["NQ/USD"]}}
        strategy_source = '''"""
Paradigm: structural retrace imbalance retest
Hypothesis: bullish fair-value-gap exists, later retraces into the gap, rejects back above the lower bound, and fires only when 4h trend remains aligned
Parent: TomacNQ_KillzoneBreakout
Status: active
External Data: no
Uses MTF: yes
"""
'''

        with TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "backtest.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("backtest-result.json", json.dumps(backtest_payload))
                archive.writestr(
                    "backtest-result_config.json", json.dumps(config_payload)
                )
                archive.writestr(
                    "backtest-result_TomacNQ_RegimeFVGRetrace.py",
                    strategy_source,
                )

            manifest = pack.build_strategy_library_manifest_from_freqtrade_backtest_zip(
                zip_path,
                repo_url="local-auto-quant",
                pinned_ref="abc123",
                config_path="config.tomac.json",
                log_path="run_tomac_fvg.log",
            )

        self.assertEqual(manifest["manifest_version"], "1.0")
        self.assertEqual(manifest["timeframe"], "1h")
        self.assertEqual(manifest["auto_quant_repo_url"], "local-auto-quant")
        self.assertEqual(manifest["auto_quant_pinned_ref"], "abc123")
        self.assertEqual(manifest["config_path"], "config.tomac.json")
        self.assertEqual(manifest["log_path"], "run_tomac_fvg.log")
        self.assertEqual(manifest["validation_errors"], [])

    def test_build_strategy_library_manifest_preserves_auto_quant_meta_block(self) -> None:
        backtest_payload = {
            "strategy": {
                "TomacNQ_KillzoneBreakout": {
                    "strategy_name": "TomacNQ_KillzoneBreakout",
                    "results_per_pair": [
                        {
                            "key": "QQQ/USD",
                            "trades": 10,
                            "winrate": 0.8,
                            "sharpe": 4.288364283701947,
                            "profit_factor": 4.298973650152414,
                            "profit_total_pct": 5.52,
                            "max_drawdown_account": 0.01121424,
                        },
                        {
                            "key": "TOTAL",
                            "trades": 10,
                            "winrate": 0.8,
                            "sharpe": 4.288364283701947,
                            "profit_factor": 4.298973650152414,
                            "profit_total_pct": 5.52,
                            "max_drawdown_account": 0.01121424,
                        },
                    ],
                    "total_trades": 10,
                    "wins": 8,
                    "losses": 2,
                    "draws": 0,
                    "sharpe": 4.288364283701947,
                    "profit_factor": 4.298973650152414,
                    "profit_total": 0.05524414,
                    "max_drawdown_account": 0.01121424,
                    "backtest_start": "2026-04-12 23:00:00",
                    "backtest_end": "2026-05-13 19:00:00",
                    "timeframe": "1h",
                }
            }
        }
        config_payload = {"timeframe": "1h", "exchange": {"pair_whitelist": ["QQQ/USD"]}}
        strategy_source = '''"""
Paradigm: breakout
Hypothesis: base hypothesis
Parent: root
Status: active
Uses MTF: yes

# AUTO_QUANT_META v1
Strategy:        TomacNQ_KillzoneBreakout
Mutation_id:     synthetic-ohlcv-TomacNQ_KillzoneBreakout
Base_factor:     tomac_n_q__killzone_breakout
Hypothesis:      richer metadata hypothesis
Paradigm:        breakout
Expected_regime: multi_timeframe_intraday_resonance
Factors_used:    tomac_n_q__killzone_breakout
Parent:          TomacKillzoneBreakout
Asset_class:     synthetic_ohlcv
Status:          active
Created:         pending-first-commit
# END_AUTO_QUANT_META
"""
'''

        with TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "backtest.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("backtest-result.json", json.dumps(backtest_payload))
                archive.writestr(
                    "backtest-result_config.json", json.dumps(config_payload)
                )
                archive.writestr(
                    "backtest-result_TomacNQ_KillzoneBreakout.py",
                    strategy_source,
                )

            manifest = pack.build_strategy_library_manifest_from_freqtrade_backtest_zip(
                zip_path,
                repo_url="local-auto-quant",
                pinned_ref="abc123",
                config_path="config.tomac.json",
                log_path="run_tomac.log",
            )

        strategy = manifest["strategies"][0]
        self.assertEqual(
            strategy["metadata"]["mutation_id"],
            "synthetic-ohlcv-TomacNQ_KillzoneBreakout",
        )
        self.assertEqual(
            strategy["metadata"]["base_factor"], "tomac_n_q__killzone_breakout"
        )
        self.assertEqual(
            strategy["metadata"]["expected_regime"],
            "multi_timeframe_intraday_resonance",
        )
        self.assertEqual(
            strategy["metadata"]["main_regime"],
            "multi_timeframe_intraday_resonance",
        )
        self.assertEqual(strategy["metadata"]["sub_regime"], "")
        self.assertEqual(
            strategy["metadata"]["sub_sub_regime_or_profit_factor"], ""
        )
        self.assertEqual(strategy["metadata"]["profit_factor"], "")
        self.assertEqual(
            strategy["metadata"]["regime_profit_branch_path"],
            "multi_timeframe_intraday_resonance",
        )
        self.assertEqual(
            strategy["metadata"]["factors_used"],
            ["tomac_n_q__killzone_breakout"],
        )
        self.assertEqual(strategy["metadata"]["asset_class"], "synthetic_ohlcv")

    def test_build_strategy_library_manifest_splits_expected_regime_branch_path(self) -> None:
        backtest_payload = {
            "strategy": {
                "BranchAwareStrategy": {
                    "strategy_name": "BranchAwareStrategy",
                    "results_per_pair": [
                        {"key": "TOTAL", "trades": 2, "winrate": 0.5, "sharpe": 1.0}
                    ],
                    "total_trades": 2,
                    "wins": 1,
                    "losses": 1,
                    "draws": 0,
                    "timeframe": "15m",
                }
            }
        }
        strategy_source = '''"""
Mutation_id: branch-aware-001
Expected_regime: TrendTransition -> LiquidityReclaim -> family_d_liquidity_sweep_reclaim_15m_wide_v1 -> liquidity_sweep_reclaim_long
"""
'''
        with TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "backtest.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("backtest-result.json", json.dumps(backtest_payload))
                archive.writestr(
                    "backtest-result_BranchAwareStrategy.py",
                    strategy_source,
                )

            manifest = pack.build_strategy_library_manifest_from_freqtrade_backtest_zip(
                zip_path
            )

        metadata = manifest["strategies"][0]["metadata"]
        self.assertEqual(metadata["main_regime"], "TrendTransition")
        self.assertEqual(metadata["sub_regime"], "LiquidityReclaim")
        self.assertEqual(
            metadata["sub_sub_regime_or_profit_factor"],
            "family_d_liquidity_sweep_reclaim_15m_wide_v1",
        )
        self.assertEqual(
            metadata["profit_factor"],
            "liquidity_sweep_reclaim_long",
        )
        self.assertEqual(
            metadata["regime_profit_branch_path"],
            "TrendTransition -> LiquidityReclaim -> family_d_liquidity_sweep_reclaim_15m_wide_v1 -> liquidity_sweep_reclaim_long",
        )
        self.assertEqual(
            metadata["branch_path_segments"],
            [
                "TrendTransition",
                "LiquidityReclaim",
                "family_d_liquidity_sweep_reclaim_15m_wide_v1",
                "liquidity_sweep_reclaim_long",
            ],
        )
        self.assertEqual(metadata["branch_path_depth"], 4)
        self.assertEqual(metadata["branch_path_leaf"], "liquidity_sweep_reclaim_long")

    def test_branch_path_contract_preserves_recursive_profit_factor_suffix(self) -> None:
        branch_path = (
            "TrendExpansion -> RootEvidencePullbackMssCisd -> "
            "strict_trend_root_pullback_mss_cisd -> "
            "vwap_reclaim_overlay -> pda_transition_guard"
        )
        contract = pack._branch_path_contract(
            {
                "expected_regime": branch_path,
                "base_timeframe": "1m",
                "context_timeframes": ["5m", "15m", "30m", "1h", "4h", "1d"],
            },
            {"timeframe": "1m"},
        )

        self.assertIsNotNone(contract)
        assert contract is not None
        self.assertEqual(contract["main_regime"], "TrendExpansion")
        self.assertEqual(contract["sub_regime"], "RootEvidencePullbackMssCisd")
        self.assertEqual(
            contract["sub_sub_regime_or_profit_factor"],
            "strict_trend_root_pullback_mss_cisd",
        )
        self.assertEqual(
            contract["profit_factor"],
            "vwap_reclaim_overlay -> pda_transition_guard",
        )
        self.assertEqual(
            contract["branch_path_segments"],
            [
                "TrendExpansion",
                "RootEvidencePullbackMssCisd",
                "strict_trend_root_pullback_mss_cisd",
                "vwap_reclaim_overlay",
                "pda_transition_guard",
            ],
        )
        self.assertEqual(contract["branch_path_depth"], 5)
        self.assertEqual(contract["branch_path_leaf"], "pda_transition_guard")
        self.assertEqual(contract["regime_profit_branch_path"], branch_path)
        self.assertEqual(contract["training_timeframe"], "1m_and_5m")
        self.assertEqual(contract["neutralization_timeframe"], "15m")
        self.assertEqual(contract["confirmation_timeframe"], "1d")

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

    def test_main_accepts_freqtrade_backtest_zip(self) -> None:
        backtest_payload = {
            "strategy": {
                "TomacNQ_RegimeVRPCompression15m": {
                    "strategy_name": "TomacNQ_RegimeVRPCompression15m",
                    "results_per_pair": [
                        {
                            "key": "NQ/USD",
                            "trades": 334,
                            "winrate": 0.34,
                            "sharpe": 0.339,
                            "profit_factor": 1.64,
                            "profit_total_pct": 28.95,
                            "max_drawdown_account": 0.041,
                        },
                        {
                            "key": "TOTAL",
                            "trades": 334,
                            "winrate": 0.34,
                            "sharpe": 0.339,
                            "profit_factor": 1.64,
                            "profit_total_pct": 28.95,
                            "max_drawdown_account": 0.041,
                        },
                    ],
                    "total_trades": 334,
                    "wins": 114,
                    "losses": 220,
                    "draws": 0,
                    "sharpe": 0.339,
                    "profit_factor": 1.64,
                    "profit_total": 0.2895,
                    "max_drawdown_account": 0.041,
                    "backtest_start": "2018-01-01 00:00:00",
                    "backtest_end": "2025-12-31 00:00:00",
                    "timeframe": "15m",
                }
            }
        }
        candidate_spec = {
            "candidate_id": "family_f_vrp_compression_v1",
            "display_name": "VRP Compression 15m",
            "family": "Family F",
            "status": "active",
            "promotion_state": "promotable",
            "expression_text": "iv_pct_rank_252 < 0.30 and hv_pct_rank_252 < 0.30",
            "operator_set": ["iv_pct_rank_252", "hv_pct_rank_252", "ema89", "ema_fast_4h"],
            "base_timeframe": "15m",
            "context_timeframes": ["4h", "1d"],
            "regime_role": "mixed",
            "pre_bayes_targets": ["volatility_compression_gate"],
            "belief_targets": ["bbn_vol_regime_evidence"],
            "path_ranking_targets": ["structural_path_confidence"],
            "execution_tree_targets": ["transition_guardrail", "observe_gate"],
            "structural_feedback_required": True,
        }

        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            zip_path = root / "backtest.zip"
            spec_path = root / "candidate_spec.json"
            output_dir = root / "out"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("backtest-result.json", json.dumps(backtest_payload))
                archive.writestr(
                    "backtest-result_config.json", json.dumps({"timeframe": "15m"})
                )
                archive.writestr(
                    "backtest-result_TomacNQ_RegimeVRPCompression15m.py",
                    '"""\nParadigm: vol regime compression\nHypothesis: compressed IV/HV regime expansion\nUses MTF: yes\n"""',
                )
            spec_path.write_text(json.dumps(candidate_spec), encoding="utf-8")

            exit_code = pack.main(
                [
                    "--freqtrade-backtest-zip",
                    str(zip_path),
                    "--strategy-name",
                    "TomacNQ_RegimeVRPCompression15m",
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

            self.assertEqual(expression["candidate_id"], "family_f_vrp_compression_v1")
            self.assertEqual(grid["trade_density_summary"]["aggregate_trade_count"], 334)
            self.assertEqual(
                grid["aggregate_metrics"]["max_drawdown_pct"],
                4.1,
            )

    def test_main_can_emit_strategy_library_manifest_from_freqtrade_backtest_zip(self) -> None:
        backtest_payload = {
            "strategy": {
                "TomacNQ_RegimeFVGRetrace": {
                    "strategy_name": "TomacNQ_RegimeFVGRetrace",
                    "results_per_pair": [
                        {
                            "key": "NQ/USD",
                            "trades": 12,
                            "winrate": 0.58333333,
                            "sharpe": 0.014993373176821853,
                            "profit_factor": 1.92,
                            "profit_total_pct": 0.57,
                            "max_drawdown_account": 0.00548,
                        },
                        {
                            "key": "TOTAL",
                            "trades": 12,
                            "winrate": 0.58333333,
                            "sharpe": 0.014993373176821853,
                            "profit_factor": 1.92,
                            "profit_total_pct": 0.57,
                            "max_drawdown_account": 0.00548,
                        },
                    ],
                    "total_trades": 12,
                    "wins": 7,
                    "losses": 5,
                    "draws": 0,
                    "sharpe": 0.014993373176821853,
                    "profit_factor": 1.92,
                    "profit_total": 0.0057,
                    "max_drawdown_account": 0.00548,
                    "backtest_start": "2018-01-01 00:00:00",
                    "backtest_end": "2025-12-31 00:00:00",
                    "timeframe": "1h",
                }
            }
        }

        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            zip_path = root / "backtest.zip"
            output_manifest = root / "strategy_library.json"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("backtest-result.json", json.dumps(backtest_payload))
                archive.writestr(
                    "backtest-result_config.json", json.dumps({"timeframe": "1h"})
                )
                archive.writestr(
                    "backtest-result_TomacNQ_RegimeFVGRetrace.py",
                    '"""\nParadigm: structural retrace imbalance retest\nHypothesis: bullish fair-value-gap retest\nParent: TomacNQ_KillzoneBreakout\nStatus: active\nUses MTF: yes\n"""',
                )

            exit_code = pack.main(
                [
                    "--freqtrade-backtest-zip",
                    str(zip_path),
                    "--emit-strategy-library-json",
                    str(output_manifest),
                    "--repo-url",
                    "local-auto-quant",
                    "--pinned-ref",
                    "abc123",
                    "--config-path",
                    "config.tomac.json",
                    "--log-path",
                    "run_tomac_fvg.log",
                    "--output-dir",
                    str(root / "candidate-pack"),
                ]
            )

            self.assertEqual(exit_code, 0)
            manifest = json.loads(output_manifest.read_text(encoding="utf-8"))
            self.assertEqual(manifest["manifest_version"], "1.0")
            self.assertEqual(manifest["auto_quant_repo_url"], "local-auto-quant")
            self.assertEqual(manifest["strategies"][0]["name"], "TomacNQ_RegimeFVGRetrace")

    def test_main_accepts_signal_diagnostics_evidence(self) -> None:
        manifest = {
            "manifest_version": "1.0",
            "timeframe": "1m",
            "strategies": [
                {
                    "name": "DiagnosticAware",
                    "status": "ok",
                    "metadata": {
                        "strategy": "DiagnosticAware",
                        "mutation_id": "diag-001",
                        "base_factor": "vwap_reclaim",
                        "hypothesis": "diagnostic evidence intake",
                        "paradigm": "transition",
                        "expected_regime": "Transition",
                        "factors_used": ["vwap", "rvol"],
                    },
                    "validation_metrics": {"sharpe": 1.0, "trade_count": 40},
                    "per_pair_metrics": {
                        "DEMO/USD": {"sharpe": 1.0, "trade_count": 40}
                    },
                }
            ],
        }
        signal_diagnostics = {
            "schema_version": "ict-engine-factor-signal-diagnostics/v1",
            "promotion_allowed": True,
            "trade_usable": False,
            "trade_usable_reason": "diagnostic_only_hotplug; downstream gates still required",
            "best_bucket": {
                "horizon": "1m",
                "regime": "Transition",
                "n": 40,
                "t_stat": 3.2,
                "ic_spearman": 0.12,
                "mean_signed_return_bps_after_cost": 4.5,
                "candidate_passed_gate": True,
            },
            "timeframe_ladder_summary": {
                "expected_ladder": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
                "covered_timeframes": ["1m", "5m"],
                "missing_timeframes": ["15m", "30m", "1h", "4h", "1d"],
                "passed_timeframes": ["1m"],
                "all_expected_timeframes_covered": False,
                "all_expected_timeframes_passed": False,
            },
        }

        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_path = root / "manifest.json"
            diagnostics_path = root / "signal_diagnostics.json"
            output_dir = root / "out"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            diagnostics_path.write_text(json.dumps(signal_diagnostics), encoding="utf-8")

            exit_code = pack.main(
                [
                    "--manifest-json",
                    str(manifest_path),
                    "--strategy-name",
                    "DiagnosticAware",
                    "--signal-diagnostics-json",
                    str(diagnostics_path),
                    "--output-dir",
                    str(output_dir),
                ]
            )

            self.assertEqual(exit_code, 0)
            grid = json.loads(
                (output_dir / "factor_eval_grid_summary.json").read_text(
                    encoding="utf-8"
                )
            )

        evidence = grid["signal_diagnostics_evidence"]
        self.assertEqual(
            evidence["schema_version"],
            "candidate-pack-signal-diagnostics-evidence/v1",
        )
        self.assertTrue(evidence["diagnostic_only"])
        self.assertNotIn("promotion_allowed", evidence)
        self.assertNotIn("trade_usable", evidence)
        self.assertNotIn("update_goal", evidence)
        self.assertTrue(evidence["diagnostic_candidate_passed_gate"])
        self.assertTrue(evidence["requires_downstream_live_gates"])
        self.assertEqual(evidence["best_bucket"]["horizon"], "1m")
        self.assertEqual(
            evidence["timeframe_ladder_summary"]["missing_timeframes"],
            ["15m", "30m", "1h", "4h", "1d"],
        )

    def test_main_demo_writes_zero_config_candidate_pack(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "pack"
            exit_code = pack.main(["--demo", "--output-dir", str(output_dir)])

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

        self.assertEqual(expression["strategy_name"], "DemoSignalDiagnosticsCandidate")
        self.assertEqual(expression["base_timeframe"], "1m")
        self.assertEqual(grid["trade_density_summary"]["aggregate_trade_count"], 40)
        self.assertEqual(transfer["covered_markets"], ["DEMO/USD"])

    def test_main_demo_can_attach_demo_signal_diagnostics(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            diagnostics_path = root / "signal_diagnostics.json"
            output_dir = root / "pack"

            diag_exit = diagnostics.main(
                ["--demo", "--output", str(diagnostics_path), "--compact"]
            )
            pack_exit = pack.main(
                [
                    "--demo",
                    "--signal-diagnostics-json",
                    str(diagnostics_path),
                    "--output-dir",
                    str(output_dir),
                ]
            )

            self.assertEqual(diag_exit, 0)
            self.assertEqual(pack_exit, 0)
            grid = json.loads(
                (output_dir / "factor_eval_grid_summary.json").read_text(
                    encoding="utf-8"
                )
            )

        evidence = grid["signal_diagnostics_evidence"]
        self.assertEqual(
            evidence["schema_version"],
            "candidate-pack-signal-diagnostics-evidence/v1",
        )
        self.assertTrue(evidence["diagnostic_only"])
        self.assertNotIn("promotion_allowed", evidence)
        self.assertNotIn("trade_usable", evidence)
        self.assertNotIn("update_goal", evidence)
        self.assertTrue(evidence["requires_downstream_live_gates"])
        self.assertEqual(evidence["best_bucket"]["regime"], "Transition")

    def test_main_demo_compact_prints_one_line(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "pack"
            exit_code = pack.main(
                ["--demo", "--output-dir", str(output_dir), "--compact"]
            )

        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
