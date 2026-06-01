#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd


SCRIPT = Path(__file__).with_name("run_tomac_cross_index_pca_residual_reclaim_local_gate1_v1.py")


def load_runner():
    assert SCRIPT.exists(), f"missing runner: {SCRIPT}"
    spec = importlib.util.spec_from_file_location("tomac_cross_index_pca_residual_local_gate1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TomacCrossIndexPcaResidualReclaimLocalGate1Test(unittest.TestCase):
    def assert_no_fixed_cost_fields(self, payload: dict[str, object]) -> None:
        forbidden_parts = (
            "bps_per_side",
            "cost_bps",
            "fee_bps",
            "legacy_stress",
            "net5bps",
            "net_5bps",
            "0bps_",
            "1bps_",
            "2bps_",
            "5bps_",
            "10bps_",
        )
        self.assertFalse(
            [key for key in payload if any(part in key for part in forbidden_parts)],
            f"fixed-cost fields leaked: {sorted(payload)}",
        )

    def assert_no_fixed_cost_text(self, text: str) -> None:
        forbidden_parts = (
            "bps_per_side",
            "cost_bps",
            "fee_bps",
            "legacy_stress",
            "net5bps",
            "net_5bps",
            "0bps_",
            "1bps_",
            "2bps_",
            "5bps",
            "10bps",
        )
        self.assertFalse(
            [part for part in forbidden_parts if part in text],
            "fixed-cost bps text leaked",
        )

    def test_pca_residual_features_are_shifted(self) -> None:
        runner = load_runner()
        idx = pd.date_range("2024-01-02 00:00:00Z", periods=180, freq="min")
        common = pd.Series(range(len(idx)), index=idx, dtype="float64") * 0.03
        nq_close = 100.0 + common + pd.Series([(i % 17) * 0.01 for i in range(len(idx))], index=idx)
        es_close = 100.0 + common * 0.85
        ym_close = 100.0 + common * 0.65

        frames = {
            "NQ": pd.DataFrame({"open": nq_close, "high": nq_close + 0.25, "low": nq_close - 0.25, "close": nq_close, "volume": 1000}, index=idx),
            "ES": pd.DataFrame({"open": es_close, "high": es_close + 0.20, "low": es_close - 0.20, "close": es_close, "volume": 1000}, index=idx),
            "YM": pd.DataFrame({"open": ym_close, "high": ym_close + 0.15, "low": ym_close - 0.15, "close": ym_close, "volume": 1000}, index=idx),
        }

        featured = runner.add_cross_index_pca_residual_features(frames, "NQ", lookback=40, z_window=60)

        self.assertIn("pca_residual", featured.columns)
        self.assertIn("pca_residual_z", featured.columns)
        self.assertIn("pca_residual_momentum_bps", featured.columns)
        self.assertTrue(pd.isna(featured.iloc[40]["pca_residual_z"]))
        self.assertTrue(pd.notna(featured.iloc[-1]["pca_residual_z"]))

    def test_classify_keeps_local_candidate_non_trade_usable(self) -> None:
        runner = load_runner()
        row = {
            "trade_count": 160,
            "trades_per_session": 0.9,
            "instrument_cost_total_profit_pct": 18.0,
            "instrument_cost_profit_factor": 1.35,
            "train_instrument_cost_total_profit_pct": 5.0,
            "validation_instrument_cost_total_profit_pct": 6.0,
            "test_instrument_cost_total_profit_pct": 7.0,
            "promotion_cost_verified": True,
        }

        classified = runner.classify(row)

        self.assertTrue(classified["instrument_cost_candidate"])
        self.assertFalse(classified["gate1_survivor"])
        self.assertEqual(classified["decision"], "local_instrument_cost_candidate_needs_exact_aq_downstream")
        self.assertFalse(classified["promotion_allowed"])
        self.assertFalse(classified["trade_usable"])
        self.assertFalse(classified["update_goal"])

    def test_branch_paths_are_regime_rooted_without_provenance_prefixes(self) -> None:
        runner = load_runner()

        self.assertTrue(runner.BRANCH_PATH.startswith("TrendExpansion ->"))
        self.assertNotIn("FUTURES", runner.BRANCH_PATH)
        self.assertNotIn("IndexFutures", runner.BRANCH_PATH)
        self.assertNotIn("ETH/full_retained_session", runner.BRANCH_PATH)
        self.assertNotIn("1m execution origin", runner.BRANCH_PATH)
        for variant in runner.variants():
            self.assertTrue(variant.branch_path.startswith("TrendExpansion ->"))

    def test_score_trades_emits_only_raw_and_instrument_cost_economics(self) -> None:
        runner = load_runner()
        trades = [
            {
                "raw_return": 0.0020,
                "net_instrument_cost_return": 0.0019,
                "entry": 4000.0,
                "year": 2024,
            },
            {
                "raw_return": -0.0005,
                "net_instrument_cost_return": -0.0006,
                "entry": 4010.0,
                "year": 2024,
            },
        ]

        row = runner.score_trades(trades, sessions=10, symbol="ES")

        self.assertIn("raw_total_profit_pct", row)
        self.assertIn("instrument_cost_total_profit_pct", row)
        self.assertIn("year_instrument_cost_total_profit_pct", row)
        self.assertNotIn("0bps_per_side_total_profit_pct", row)
        self.assert_no_fixed_cost_fields(row)

    def test_simulated_trade_rows_do_not_emit_fixed_cost_telemetry(self) -> None:
        runner = load_runner()
        idx = pd.date_range("2024-01-02 00:00:00Z", periods=8, freq="min")
        frame = pd.DataFrame(
            {
                "open": [4000.0, 4001.0, 4002.0, 4003.0, 4004.0, 4005.0, 4006.0, 4007.0],
                "high": [4001.0, 4002.0, 4004.0, 4005.0, 4006.0, 4007.0, 4008.0, 4009.0],
                "low": [3999.0, 4000.0, 4001.0, 4002.0, 4003.0, 4004.0, 4005.0, 4006.0],
                "close": [4000.5, 4001.5, 4002.5, 4003.5, 4004.5, 4005.5, 4006.5, 4007.5],
                "atr14": [1.0] * 8,
                "session_date": ["2024-01-02"] * 8,
            },
            index=idx,
        )
        variant = runner.variants()[0]

        with mock.patch.object(runner, "build_signal", return_value=pd.Series([False, True, False, False, False, False, False, False], index=idx)):
            trades = runner.simulate_trades("ES", frame, variant)

        self.assertEqual(len(trades), 1)
        self.assertIn("net_instrument_cost_return", trades[0])
        self.assert_no_fixed_cost_fields(trades[0])

    def test_main_writes_no_launch_terminal_metrics(self) -> None:
        runner = load_runner()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.run(runner.parse_args(["--root", tmpdir, "--symbols", "ES", "YM", "NQ"]))

            terminal = json.loads((Path(tmpdir) / "checks" / "terminal_metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(result["factor_id"], "cross_index_pca_residual_reclaim_v1")
            self.assertEqual(terminal["session_scope"], "ETH/full_retained_session")
            self.assertFalse(terminal["rth_filter_applied"])
            self.assertTrue(terminal["local_screen_only"])
            self.assertFalse(terminal["provider_attempted"])
            self.assertFalse(terminal["ibkr_historical_attempted"])
            self.assertFalse(terminal["autoquant_attempted"])
            self.assertFalse(terminal["promotion_allowed"])
            self.assertFalse(terminal["trade_usable"])
            self.assertFalse(terminal["update_goal"])
            self.assertEqual(terminal["gate1_survivor_count"], 0)
            self.assertGreaterEqual(terminal["candidate_count"], 1)
            self.assertNotIn("top_by_5bps", terminal)
            self.assert_no_fixed_cost_fields(terminal)
            rows_csv = Path(tmpdir) / "summaries" / "screen_rows.csv"
            summary_md = Path(tmpdir) / "summaries" / "terminal_summary.md"
            self.assertTrue(rows_csv.exists())
            self.assert_no_fixed_cost_text(rows_csv.read_text(encoding="utf-8"))
            self.assert_no_fixed_cost_text(summary_md.read_text(encoding="utf-8"))

    def test_execute_local_screen_can_run_against_synthetic_frames(self) -> None:
        runner = load_runner()
        idx = pd.date_range("2024-01-02 00:00:00Z", periods=520, freq="min")

        def frame(multiplier: float, pulse: float) -> pd.DataFrame:
            close = [100.0 + i * multiplier + (pulse if i > 280 and i % 19 == 0 else 0.0) for i in range(len(idx))]
            return pd.DataFrame(
                {
                    "open": close,
                    "high": [item + 0.35 for item in close],
                    "low": [item - 0.35 for item in close],
                    "close": close,
                    "volume": [1000.0 + (i % 23) * 10.0 for i in range(len(idx))],
                },
                index=idx,
            )

        synthetic = {"ES": frame(0.07, 0.05), "YM": frame(0.05, -0.02), "NQ": frame(0.11, 0.18)}
        stats = {symbol: {"rows_1m": len(data), "retained_session_coverage": {"status": "pass", "non_rth_rows": len(data)}} for symbol, data in synthetic.items()}

        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(runner, "load_claim_audit", return_value={"claims": [], "live_factor_processes": []}), mock.patch.object(runner, "load_symbol_frames", return_value=(synthetic, stats)):
            result = runner.run(
                runner.parse_args(
                    [
                        "--root",
                        tmpdir,
                        "--symbols",
                        "ES",
                        "YM",
                        "NQ",
                        "--target",
                        "NQ",
                        "--execute-local-screen",
                    ]
                )
            )

            terminal = json.loads((Path(tmpdir) / "checks" / "terminal_metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(result["factor_id"], "cross_index_pca_residual_reclaim_v1")
            self.assertTrue(terminal["execute_local_screen"])
            self.assertEqual(terminal["data_stats"]["target"], "NQ")
            self.assertEqual(terminal["candidate_count"], len(runner.variants()))
            self.assertFalse(terminal["provider_attempted"])
            self.assertFalse(terminal["ibkr_historical_attempted"])
            self.assertFalse(terminal["autoquant_attempted"])
            self.assertFalse(terminal["promotion_allowed"])
            self.assertFalse(terminal["trade_usable"])

    def test_execute_local_screen_blocks_on_foreign_active_claim_before_loading_data(self) -> None:
        runner = load_runner()
        audit = {
            "claims": [
                {
                    "status": "active",
                    "coordination_only": False,
                    "claim_file": "foreign.claim",
                    "run_root": "/tmp/foreign-root",
                }
            ],
            "live_factor_processes": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(runner, "load_claim_audit", return_value=audit), mock.patch.object(runner, "load_symbol_frames") as load_frames:
            result = runner.run(
                runner.parse_args(
                    [
                        "--root",
                        tmpdir,
                        "--symbols",
                        "ES",
                        "YM",
                        "NQ",
                        "--target",
                        "NQ",
                        "--execute-local-screen",
                    ]
                )
            )

            load_frames.assert_not_called()
            terminal = json.loads((Path(tmpdir) / "checks" / "terminal_metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(result["decision"], "launch_blocked_by_collision_guard")
            self.assertEqual(terminal["decision"], "launch_blocked_by_collision_guard")
            self.assertTrue(terminal["execute_local_screen"])
            self.assertFalse(terminal["local_screen_executed"])
            self.assertEqual(terminal["collision_guard"]["foreign_active_claims"], ["foreign.claim"])
            self.assertFalse(terminal["provider_attempted"])
            self.assertFalse(terminal["autoquant_attempted"])
            self.assertFalse(terminal["promotion_allowed"])
            self.assertFalse(terminal["trade_usable"])

    def test_load_symbol_frames_reports_actual_feather_cache_path(self) -> None:
        runner = load_runner()
        idx = pd.date_range("2024-01-02 00:00:00Z", periods=30, freq="min")
        frame = pd.DataFrame(
            {
                "open": [100.0] * len(idx),
                "high": [101.0] * len(idx),
                "low": [99.0] * len(idx),
                "close": [100.5] * len(idx),
                "volume": [1000.0] * len(idx),
            },
            index=idx,
        )

        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(runner, "PARQUET_CACHE", Path(tmpdir) / "parquet"), mock.patch.object(runner, "FEATHER_CACHE", Path(tmpdir) / "feather"), mock.patch.object(runner, "read_frame", return_value=frame):
            feather = Path(tmpdir) / "feather" / "ES_USD-1m.feather"
            feather.parent.mkdir(parents=True)
            feather.touch()

            _, stats = runner.load_symbol_frames(["ES"], "1m", "2024-01-02", "2024-01-03", None)

            self.assertEqual(stats["ES"]["cache_path"], str(feather))

    def test_read_frame_uses_futures_feather_fallback(self) -> None:
        runner = load_runner()
        idx = pd.date_range("2024-01-02 00:00:00Z", periods=5, freq="min")
        raw = pd.DataFrame(
            {
                "datetime": idx,
                "open": [100.0] * len(idx),
                "high": [101.0] * len(idx),
                "low": [99.0] * len(idx),
                "close": [100.5] * len(idx),
                "volume": [1000.0] * len(idx),
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(runner, "PARQUET_CACHE", Path(tmpdir) / "parquet"), mock.patch.object(runner, "FEATHER_CACHE", Path(tmpdir) / "feather"), mock.patch.object(runner.pd, "read_feather", return_value=raw) as read_feather:
            futures_feather = Path(tmpdir) / "feather" / "futures" / "ES_USD-1m-futures.feather"
            futures_feather.parent.mkdir(parents=True)
            futures_feather.touch()

            out = runner.read_frame("ES", "1m")

            read_feather.assert_called_once_with(futures_feather)
            self.assertEqual(len(out), len(raw))


if __name__ == "__main__":
    unittest.main()
