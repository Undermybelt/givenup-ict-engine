from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import tomac_tod_balanced_practical_sidecar as sidecar  # noqa: E402


class TomacTodBalancedPracticalSidecarTests(unittest.TestCase):
    def test_normalize_backtest_trade_preserves_pair_direction_and_branch_fields(self) -> None:
        normalized = sidecar.normalize_backtest_trade(
            {
                "pair": "NQ/USD",
                "is_short": True,
                "open_date": "2024-01-01T00:00:00+00:00",
                "close_date": "2024-01-01T00:02:00+00:00",
                "open_rate": 100.0,
                "close_rate": 99.0,
                "profit_ratio": 0.01,
                "min_rate": 98.0,
                "max_rate": 101.0,
                "enter_tag": "balanced-root",
                "exit_reason": "exit_signal",
            },
            trade_id="demo-00001",
            factor_id="balanced-demo",
        )

        self.assertEqual(normalized["trade_id"], "demo-00001")
        self.assertEqual(normalized["pair"], "NQ/USD")
        self.assertEqual(normalized["direction"], "short")
        self.assertEqual(normalized["regime_profit_branch_path"], "balanced-root")
        self.assertEqual(normalized["sub_sub_regime_or_profit_factor"], "balanced-demo")

    def test_run_sidecar_writes_portfolio_and_pair_artifacts(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            output_dir = tmp / "out"
            candles = [
                {"timestamp": "2024-01-01T00:00:00+00:00", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0},
                {"timestamp": "2024-01-01T00:01:00+00:00", "open": 100.0, "high": 102.0, "low": 99.0, "close": 101.0, "volume": 1.0},
                {"timestamp": "2024-01-01T00:02:00+00:00", "open": 101.0, "high": 103.0, "low": 100.0, "close": 102.0, "volume": 1.0},
            ]
            trades = [
                {
                    "trade_id": "balanced-00001",
                    "pair": "NQ/USD",
                    "direction": "long",
                    "open_ts_ms": sidecar.trade_labels._timestamp_ms("2024-01-01T00:00:00+00:00"),
                    "close_ts_ms": sidecar.trade_labels._timestamp_ms("2024-01-01T00:02:00+00:00"),
                    "open_rate": 100.0,
                    "close_rate": 102.0,
                    "profit_ratio": 0.02,
                    "pnl": 2.0,
                    "min_rate": 99.0,
                    "max_rate": 103.0,
                    "realized_outcome": "win",
                    "regime_profit_branch_path": "balanced-root",
                    "main_regime": "SessionRhythm",
                    "sub_regime": "TimeOfDaySeasonality",
                    "sub_sub_regime_or_profit_factor": "balanced-demo",
                    "profit_factor": "balanced-demo",
                    "structural_feedback": {"exit_reason": "exit_signal"},
                    "factors_used": [{"category": "regime_profit_branch_path", "confidence": 1.0}],
                }
            ]

            result = sidecar.run_sidecar(
                output_dir=output_dir,
                factor_id="balanced-demo",
                symbol="NQ_XAU_YM",
                sl_mult=0.01,
                candles_by_pair={"NQ/USD": candles},
                trades=trades,
            )

            self.assertTrue((output_dir / "summary.json").is_file())
            self.assertTrue((output_dir / "trades.jsonl").is_file())
            self.assertTrue((output_dir / "labels" / "portfolio_labels.jsonl").is_file())
            self.assertTrue((output_dir / "payoff" / "portfolio_payoff_report.json").is_file())
            self.assertTrue((output_dir / "path_ranker" / "path_ranker_handoff_summary.json").is_file())
            self.assertEqual(result["trade_count"], 1)
            self.assertEqual(result["portfolio_summary"]["pair_breakdown"]["NQ/USD"]["label_count"], 1)
            self.assertEqual(result["instrument_cost_models"]["NQ/USD"]["cost_model_status"], "verified_ibkr_broker_side")
            summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["factor_id"], "balanced-demo")


if __name__ == "__main__":
    unittest.main()
