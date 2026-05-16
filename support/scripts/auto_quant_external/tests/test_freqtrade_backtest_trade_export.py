from __future__ import annotations

import json
import sys
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import freqtrade_backtest_trade_export as exporter  # noqa: E402


class FreqtradeBacktestTradeExportTests(unittest.TestCase):
    def test_export_backtest_zip_preserves_normalized_trade_fields(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            backtest_zip = tmp / "backtest.zip"
            output_jsonl = tmp / "trades.jsonl"
            payload = {
                "strategy": {
                    "DenseKlineUpbarReclaimLongV1": {
                        "trades": [
                            {
                                "pair": "QQQ/USD",
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
                                "enter_tag": "dense-entry",
                                "trade_duration": 10,
                                "is_short": False,
                            }
                        ]
                    }
                }
            }
            with zipfile.ZipFile(backtest_zip, "w") as zf:
                zf.writestr("backtest-result.json", json.dumps(payload))

            summary = exporter.export_backtest_trades(
                backtest_zip=backtest_zip,
                strategy_name="DenseKlineUpbarReclaimLongV1",
                output_jsonl=output_jsonl,
                strategy_mutation_id="dense-kline-upbar-reclaim-tvr-qqq-5m-v1",
                auto_quant_run_id="run-1",
                symbol="DENSE_KLINE_BRANCH",
                provider="TVR",
                instrument="QQQ",
                timeframe="5m",
                branch_path="TrendExpansion -> SessionLiquidity -> dense_kline_upbar_reclaim_tvr_5m -> dense_kline_upbar_reclaim_tvr_qqq_5m_v1",
            )

            self.assertEqual(summary["rows"], 1)
            row = json.loads(output_jsonl.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(row["trade_id"], "dense-kline-upbar-reclaim-tvr-qqq-5m-v1:1")
            self.assertEqual(row["realized_outcome"], "win")
            self.assertEqual(row["direction"], "Bull")
            self.assertAlmostEqual(row["open_rate"], 101.0)
            self.assertAlmostEqual(row["close_rate"], 103.0)
            self.assertAlmostEqual(row["profit_ratio"], 0.01980198019801982)
            self.assertAlmostEqual(row["profit_abs"], 22.0)
            self.assertEqual(row["entry_signal"], "dense-entry")


if __name__ == "__main__":
    unittest.main()
