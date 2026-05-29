from __future__ import annotations

import json
import sys
import textwrap
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import freqtrade_workspace_trade_export as exporter  # noqa: E402


class FreqtradeWorkspaceTradeExportTests(unittest.TestCase):
    def test_workspace_runner_exports_trades_from_fake_run_tomac_module(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            workspace = tmp / "aq_workspace"
            workspace.mkdir()
            (workspace / "config.tomac.json").write_text(
                json.dumps(
                    {
                        "exchange": {"pair_whitelist": ["NQ/USD", "YM/USD"]},
                        "timeframe": "1m",
                    }
                ),
                encoding="utf-8",
            )
            strategies_dir = workspace / "user_data" / "strategies_external"
            strategies_dir.mkdir(parents=True)
            (strategies_dir / "BalancedWorkspaceStrategy.py").write_text("class BalancedWorkspaceStrategy: pass\n", encoding="utf-8")
            (workspace / "run_tomac.py").write_text(
                textwrap.dedent(
                    """
                    def run_backtest(strategy_name):
                        return {
                            "strategy": {
                                strategy_name: {
                                    "trades": [
                                        {
                                            "pair": "NQ/USD",
                                            "open_date": "2026-05-15 10:00:00+00:00",
                                            "close_date": "2026-05-15 10:10:00+00:00",
                                            "open_rate": 101.0,
                                            "close_rate": 103.0,
                                            "open_timestamp": 1778848800000,
                                            "close_timestamp": 1778849400000,
                                            "profit_abs": 22.0,
                                            "profit_ratio": 0.01980198019801982,
                                            "min_rate": 100.5,
                                            "max_rate": 103.5,
                                            "exit_reason": "roi",
                                            "enter_tag": "workspace-entry",
                                            "trade_duration": 10,
                                            "is_short": False,
                                        }
                                    ]
                                }
                            }
                        }
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            output_jsonl = tmp / "trades.jsonl"

            summary = exporter.export_workspace_trades(
                workspace_dir=workspace,
                output_jsonl=output_jsonl,
                strategy_mutation_id="balanced-workspace-factor-v1",
                auto_quant_run_id="workspace-run-1",
                symbol="TOMAC_BALANCED_TOD",
                provider="TOMAC",
                instrument="index_futures",
                timeframe="1m",
                branch_path="SessionRhythm -> TimeOfDaySeasonality -> BalancedAdaptiveSlotPortfolio -> factor_v1",
            )

            self.assertEqual(summary["rows"], 1)
            self.assertEqual(summary["strategy_name"], "BalancedWorkspaceStrategy")
            row = json.loads(output_jsonl.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(row["entry_signal"], "workspace-entry")
            self.assertEqual(row["pair"], "NQ/USD")
            self.assertEqual(row["realized_outcome"], "win")
            self.assertEqual(
                row["branch_path_segments"],
                [
                    "SessionRhythm",
                    "TimeOfDaySeasonality",
                    "BalancedAdaptiveSlotPortfolio",
                    "factor_v1",
                ],
            )


if __name__ == "__main__":
    unittest.main()
