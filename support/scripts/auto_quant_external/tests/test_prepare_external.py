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
