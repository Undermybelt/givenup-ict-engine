from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import tomac_parquet_to_feather as bridge  # noqa: E402


class TomacParquetToFeatherTests(unittest.TestCase):
    def test_convert_single_timeframe_writes_futures_feather_with_freqtrade_schema(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            cache = root / "cache"
            cache.mkdir()
            source = cache / "NQ_15m.parquet"
            pd.DataFrame(
                {
                    "datetime": pd.date_range("2026-01-01", periods=3, freq="15min", tz="UTC"),
                    "open": [1.0, 2.0, 3.0],
                    "high": [1.5, 2.5, 3.5],
                    "low": [0.5, 1.5, 2.5],
                    "close": [1.1, 2.1, 3.1],
                    "volume": [10.0, 11.0, 12.0],
                    "ignored": ["a", "b", "c"],
                }
            ).to_parquet(source)

            out_dir = root / "aq" / "user_data" / "data"
            result = bridge.convert_cache(
                cache_root=cache,
                output_dir=out_dir,
                symbols=["NQ"],
                timeframes=["15m"],
                futures=True,
            )

            self.assertEqual(result["converted_count"], 1)
            target = out_dir / "futures" / "NQ_USD-15m-futures.feather"
            self.assertTrue(target.exists())
            restored = pd.read_feather(target)
            self.assertEqual(list(restored.columns), ["date", "open", "high", "low", "close", "volume"])
            self.assertEqual(len(restored), 3)
            self.assertEqual(str(restored.iloc[0]["date"]), "2026-01-01 00:00:00+00:00")
            self.assertEqual(result["outputs"][0]["rows"], 3)
            self.assertEqual(result["outputs"][0]["session_scope"], "ETH/full_retained_session")
            self.assertFalse(result["outputs"][0]["rth_filter_applied"])

    def test_legacy_xau_request_writes_gc_data_filename(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            cache = root / "cache"
            cache.mkdir()
            pd.DataFrame(
                {
                    "datetime": pd.date_range("2026-01-01", periods=3, freq="15min", tz="UTC"),
                    "open": [2300.0, 2301.0, 2302.0],
                    "high": [2301.0, 2302.0, 2303.0],
                    "low": [2299.0, 2300.0, 2301.0],
                    "close": [2300.5, 2301.5, 2302.5],
                    "volume": [10.0, 11.0, 12.0],
                }
            ).to_parquet(cache / "GC_15m.parquet")

            out_dir = root / "aq" / "user_data" / "data"
            result = bridge.convert_cache(
                cache_root=cache,
                output_dir=out_dir,
                symbols=["XAU"],
                timeframes=["15m"],
                futures=True,
            )

            target = out_dir / "futures" / "GC_USD-15m-futures.feather"
            self.assertTrue(target.exists())
            self.assertFalse((out_dir / "futures" / "XAU_USD-15m-futures.feather").exists())
            self.assertEqual(result["raw_requested_symbols"], ["XAU"])
            self.assertEqual(result["symbols"], ["GC"])
            self.assertEqual(result["symbol_aliases"], [{"requested": "XAU", "canonical": "GC"}])
            self.assertEqual(result["outputs"][0]["symbol"], "GC")
            self.assertEqual(result["outputs"][0]["raw_requested_symbol"], "XAU")
            self.assertEqual(result["outputs"][0]["legacy_symbol_alias"], "XAU")
            self.assertTrue(result["outputs"][0]["output"].endswith("GC_USD-15m-futures.feather"))

    def test_legacy_xau_cache_input_falls_back_but_output_still_uses_gc_filename(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            cache = root / "cache"
            cache.mkdir()
            pd.DataFrame(
                {
                    "date": pd.date_range("2026-01-01", periods=2, freq="1h", tz="UTC"),
                    "open": [2300.0, 2301.0],
                    "high": [2301.0, 2302.0],
                    "low": [2299.0, 2300.0],
                    "close": [2300.5, 2301.5],
                    "volume": [10.0, 11.0],
                }
            ).to_parquet(cache / "XAU_1h.parquet")

            out_dir = root / "aq" / "user_data" / "data"
            result = bridge.convert_cache(
                cache_root=cache,
                output_dir=out_dir,
                symbols=["XAU"],
                timeframes=["1h"],
                futures=True,
            )

            self.assertTrue((out_dir / "futures" / "GC_USD-1h-futures.feather").exists())
            self.assertFalse((out_dir / "futures" / "XAU_USD-1h-futures.feather").exists())
            self.assertTrue(result["outputs"][0]["source"].endswith("XAU_1h.parquet"))

    def test_main_writes_summary_json_for_multiple_timeframes(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            cache = root / "cache"
            cache.mkdir()
            for timeframe, freq in {"5m": "5min", "1h": "h"}.items():
                pd.DataFrame(
                    {
                        "date": pd.date_range("2026-01-01", periods=2, freq=freq, tz="UTC"),
                        "open": [1.0, 2.0],
                        "high": [1.5, 2.5],
                        "low": [0.5, 1.5],
                        "close": [1.1, 2.1],
                        "volume": [10.0, 11.0],
                    }
                ).to_parquet(cache / f"YM_{timeframe}.parquet")

            summary = root / "summary.json"
            exit_code = bridge.main(
                [
                    "--cache-root",
                    str(cache),
                    "--output-dir",
                    str(root / "aq" / "user_data" / "data"),
                    "--symbols",
                    "YM",
                    "--timeframes",
                    "5m,1h",
                    "--summary-json",
                    str(summary),
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(summary.read_text(encoding="utf-8"))
            self.assertEqual(payload["converted_count"], 2)
            self.assertEqual([row["timeframe"] for row in payload["outputs"]], ["5m", "1h"])


if __name__ == "__main__":
    unittest.main()
