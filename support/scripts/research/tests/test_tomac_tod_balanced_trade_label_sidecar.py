from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tomac_tod_balanced_trade_label_sidecar as module


class TomacTodBalancedTradeLabelSidecarTests(unittest.TestCase):
    def test_build_trade_labels_reconstructs_long_and_short(self) -> None:
        signals = pd.DataFrame(
            [
                {
                    "pair": "NQ/USD",
                    "date": "2026-01-01T00:00:00Z",
                    "tod_enter_long": 1,
                    "tod_enter_short": 0,
                    "tod_exit_long": 0,
                    "tod_exit_short": 0,
                    "tod_factor_ids": "alpha",
                },
                {
                    "pair": "NQ/USD",
                    "date": "2026-01-01T00:01:00Z",
                    "tod_enter_long": 0,
                    "tod_enter_short": 0,
                    "tod_exit_long": 1,
                    "tod_exit_short": 0,
                    "tod_factor_ids": "",
                },
                {
                    "pair": "XAU/USD",
                    "date": "2026-01-01T00:00:00Z",
                    "tod_enter_long": 0,
                    "tod_enter_short": 1,
                    "tod_exit_long": 0,
                    "tod_exit_short": 0,
                    "tod_factor_ids": "beta",
                },
                {
                    "pair": "XAU/USD",
                    "date": "2026-01-01T00:01:00Z",
                    "tod_enter_long": 0,
                    "tod_enter_short": 0,
                    "tod_exit_long": 0,
                    "tod_exit_short": 1,
                    "tod_factor_ids": "",
                },
            ]
        )
        signals["ts"] = pd.to_datetime(signals["date"], utc=True)
        price_frames = {
            "NQ/USD": pd.DataFrame(
                {
                    "timestamp": ["2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z"],
                    "open": [100.0, 100.0],
                    "high": [101.5, 103.0],
                    "low": [99.5, 99.0],
                    "close": [100.0, 102.0],
                    "volume": [1.0, 1.0],
                    "ts": pd.to_datetime(["2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z"], utc=True),
                }
            ),
            "XAU/USD": pd.DataFrame(
                {
                    "timestamp": ["2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z"],
                    "open": [200.0, 200.0],
                    "high": [201.0, 201.0],
                    "low": [199.0, 194.0],
                    "close": [200.0, 195.0],
                    "volume": [1.0, 1.0],
                    "ts": pd.to_datetime(["2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z"], utc=True),
                }
            ),
        }

        labels, diagnostics = module.build_trade_labels(
            signals=signals,
            price_frames=price_frames,
            factor_id="factor",
            branch_path="root",
            sl_mult=0.01,
            round_trip_cost_fraction=0.001,
        )

        self.assertEqual(len(labels), 2)
        self.assertEqual(diagnostics["open_position_count"], 0)
        self.assertEqual(labels[0]["pair"], "NQ/USD")
        self.assertEqual(labels[0]["meta_label"], 1)
        self.assertEqual(labels[0]["open_ts_ms"], 1767225600000)
        self.assertEqual(labels[0]["close_ts_ms"], 1767225660000)
        self.assertAlmostEqual(labels[0]["gross_return"], 0.02, places=6)
        self.assertAlmostEqual(labels[0]["net_return"], 0.019, places=6)
        self.assertAlmostEqual(labels[0]["realized_R"], 1.9, places=6)
        self.assertEqual(labels[1]["pair"], "XAU/USD")
        self.assertEqual(labels[1]["side"], -1)
        self.assertGreater(labels[1]["realized_R"], 0.0)

    def test_run_sidecar_writes_summary_with_trade_count_parity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "exact"
            (root / "aq_workspace/user_data/data/futures").mkdir(parents=True)
            (root / "checks").mkdir(parents=True)
            signals = pd.DataFrame(
                [
                    {
                        "pair": "NQ/USD",
                        "date": "2026-01-01T00:00:00Z",
                        "tod_enter_long": 1,
                        "tod_enter_short": 0,
                        "tod_exit_long": 0,
                        "tod_exit_short": 0,
                        "tod_factor_ids": "alpha",
                    },
                    {
                        "pair": "NQ/USD",
                        "date": "2026-01-01T00:01:00Z",
                        "tod_enter_long": 0,
                        "tod_enter_short": 0,
                        "tod_exit_long": 1,
                        "tod_exit_short": 0,
                        "tod_factor_ids": "",
                    },
                ]
            )
            signals.to_feather(root / "aq_workspace/user_data/tod_portfolio_signals.feather")
            prices = pd.DataFrame(
                {
                    "date": ["2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z"],
                    "open": [100.0, 100.0],
                    "high": [101.5, 103.0],
                    "low": [99.0, 99.5],
                    "close": [100.0, 102.0],
                    "volume": [1.0, 1.0],
                }
            )
            prices.to_feather(root / "aq_workspace/user_data/data/futures/NQ_USD-1m-futures.feather")
            (root / "checks/terminal_metrics.json").write_text(
                json.dumps(
                    {
                        "factor_id": "factor",
                        "branch_path": "root",
                        "trade_count": 1,
                        "gate1_survivor": True,
                    }
                ),
                encoding="utf-8",
            )

            summary = module.run_sidecar(
                exact_root=root,
                output_dir=Path(tmpdir) / "out",
                sl_mult=0.01,
                round_trip_cost_fraction=0.001,
                nb_trials=1,
                periods_per_year=252,
                embargo_bars=1,
                fold_count=2,
            )

            self.assertTrue(summary["trade_count_parity"])
            self.assertEqual(summary["label_count"], 1)
            self.assertTrue(Path(summary["artifact_paths"]["labels_jsonl"]).exists())
            self.assertTrue(Path(summary["artifact_paths"]["payoff_report_json"]).exists())
            guard = json.loads(
                Path(summary["artifact_paths"]["simulated_feedback_admission_guard_json"]).read_text(encoding="utf-8")
            )
            self.assertFalse(any("missing_open_timestamp" in violation for violation in guard["violations"]))

    def test_run_sidecar_hydrates_downstream_summary_from_sibling_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            root = base / "top1965_comp40_floor50_exact_suppressed"
            downstream = base / "downstream-exact-tomac-tod-balanced-r2-20260527T084055+0800"
            (root / "aq_workspace/user_data/data/futures").mkdir(parents=True)
            (root / "checks").mkdir(parents=True)
            (downstream / "checks").mkdir(parents=True)
            (downstream / "path_ranker_model").mkdir(parents=True)

            signals = pd.DataFrame(
                [
                    {
                        "pair": "NQ/USD",
                        "date": "2026-01-01T00:00:00Z",
                        "tod_enter_long": 1,
                        "tod_enter_short": 0,
                        "tod_exit_long": 0,
                        "tod_exit_short": 0,
                        "tod_factor_ids": "alpha",
                    },
                    {
                        "pair": "NQ/USD",
                        "date": "2026-01-01T00:01:00Z",
                        "tod_enter_long": 0,
                        "tod_enter_short": 0,
                        "tod_exit_long": 1,
                        "tod_exit_short": 0,
                        "tod_factor_ids": "",
                    },
                ]
            )
            signals.to_feather(root / "aq_workspace/user_data/tod_portfolio_signals.feather")
            prices = pd.DataFrame(
                {
                    "date": ["2026-01-01T00:00:00Z", "2026-01-01T00:01:00Z"],
                    "open": [100.0, 100.0],
                    "high": [101.5, 103.0],
                    "low": [99.0, 99.5],
                    "close": [100.0, 102.0],
                    "volume": [1.0, 1.0],
                }
            )
            prices.to_feather(root / "aq_workspace/user_data/data/futures/NQ_USD-1m-futures.feather")
            (root / "checks/terminal_metrics.json").write_text(
                json.dumps(
                    {
                        "factor_id": "factor",
                        "branch_path": "root",
                        "trade_count": 1,
                        "gate1_survivor": True,
                    }
                ),
                encoding="utf-8",
            )
            (root / "checks/provider_parity_probe.json").write_text(
                json.dumps({"ok": True, "decision": "bounded_provider_parity_recent_rows_present"}),
                encoding="utf-8",
            )
            (downstream / "checks/terminal_metrics.json").write_text(
                json.dumps(
                    {
                        "execution_readiness": 0.72,
                        "transition_hazard": 0.18,
                        "execution_candidate_actionable": True,
                        "validation_counters": {
                            "raw_scored_mature": "31/30",
                            "production_validation": "30/30",
                            "observation_validation": "32/30",
                        },
                    }
                ),
                encoding="utf-8",
            )
            (downstream / "path_ranker_model/trainer_artifact.json").write_text(
                json.dumps(
                    {
                        "validation_metrics": {
                            "raw_scored_mature_rows": 31,
                            "production_validation_rows": 30,
                            "observation_validation_rows": 32,
                        }
                    }
                ),
                encoding="utf-8",
            )

            summary = module.run_sidecar(
                exact_root=root,
                output_dir=base / "out",
                sl_mult=0.01,
                round_trip_cost_fraction=0.001,
                nb_trials=1,
                periods_per_year=252,
                embargo_bars=1,
                fold_count=2,
            )

            self.assertEqual(summary["label_count"], 1)
            guard = json.loads(
                Path(summary["artifact_paths"]["simulated_feedback_admission_guard_json"]).read_text(encoding="utf-8")
            )
            self.assertTrue(guard["blocker_categories"]["provider_parity"]["ok"])
            self.assertTrue(guard["blocker_categories"]["validation"]["ok"])
            self.assertTrue(guard["blocker_categories"]["execution_readiness"]["ok"])
            self.assertNotIn("prove_provider_parity", guard["next_action_keywords"])
            self.assertNotIn("repair_validation_rows", guard["next_action_keywords"])
            self.assertNotIn("repair_execution_readiness", guard["next_action_keywords"])


if __name__ == "__main__":
    unittest.main()
