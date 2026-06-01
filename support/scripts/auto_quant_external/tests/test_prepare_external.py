from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import prepare_external as prepare  # noqa: E402


class PrepareExternalFeatherTests(unittest.TestCase):
    def test_resample_supports_three_minute_timeframe(self) -> None:
        frame = pd.DataFrame(
            {
                "date": pd.date_range("2026-01-01", periods=6, freq="1min", tz="UTC"),
                "open": [10.0, 11.0, 12.0, 20.0, 21.0, 22.0],
                "high": [10.5, 11.5, 12.5, 20.5, 21.5, 22.5],
                "low": [9.5, 10.5, 11.5, 19.5, 20.5, 21.5],
                "close": [10.2, 11.2, 12.2, 20.2, 21.2, 22.2],
                "volume": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            }
        )

        resampled = prepare.resample_ohlcv(frame, "3m")

        self.assertEqual(len(resampled), 2)
        self.assertEqual(resampled.iloc[0]["open"], 10.0)
        self.assertEqual(resampled.iloc[0]["high"], 12.5)
        self.assertEqual(resampled.iloc[0]["low"], 9.5)
        self.assertEqual(resampled.iloc[0]["close"], 12.2)
        self.assertEqual(resampled.iloc[0]["volume"], 6.0)
        self.assertEqual(str(resampled.iloc[1]["date"]), "2026-01-01 00:03:00+00:00")

    def test_write_feather_preserves_datetimelike_date_column(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            frame = pd.DataFrame(
                {
                    "date": pd.date_range("2026-01-01", periods=3, freq="1h", tz="UTC"),
                    "open": [1.0, 2.0, 3.0],
                    "high": [1.5, 2.5, 3.5],
                    "low": [0.5, 1.5, 2.5],
                    "close": [1.1, 2.1, 3.1],
                    "volume": [10.0, 11.0, 12.0],
                }
            )

            feather = prepare.write_feather(frame, root, "BTCUSDT/USD", "1h")
            restored = pd.read_feather(feather)

            self.assertTrue(pd.api.types.is_datetime64_any_dtype(restored["date"]))
            self.assertEqual(str(restored.iloc[0]["date"]), "2026-01-01 00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
