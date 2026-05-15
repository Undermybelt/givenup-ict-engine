from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import normalize_external_ohlcv as normalizer  # noqa: E402


class NormalizeExternalOhlcvTests(unittest.TestCase):
    def test_main_normalizes_csv_rows_into_wrapped_candle_json(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            raw = root / "nq.csv"
            output = root / "nq.json"
            raw.write_text(
                "timestamp,open,high,low,close,volume\n"
                "2026-01-02T00:00:00Z,2,3,1,2.5,11\n"
                "2026-01-01T00:00:00Z,1,2,0.5,1.5,10\n",
                encoding="utf-8",
            )

            exit_code = normalizer.main(
                [
                    "--input",
                    str(raw),
                    "--output",
                    str(output),
                    "--symbol",
                    "NQ",
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["symbol"], "NQ")
            self.assertEqual(payload["candles"][0]["timestamp"], "2026-01-01T00:00:00Z")
            self.assertEqual(payload["candles"][1]["close"], 2.5)

    def test_normalize_rows_sorts_and_deduplicates_json_series(self) -> None:
        rows = normalizer.normalize_rows(
            [
                {
                    "timestamp": "2026-01-02T00:00:00Z",
                    "open": 2,
                    "high": 3,
                    "low": 1,
                    "close": 2.5,
                    "volume": 11,
                },
                {
                    "timestamp": "2026-01-01T00:00:00Z",
                    "open": 1,
                    "high": 2,
                    "low": 0.5,
                    "close": 1.5,
                    "volume": 10,
                },
                {
                    "timestamp": "2026-01-01T00:00:00Z",
                    "open": 1.1,
                    "high": 2.1,
                    "low": 0.6,
                    "close": 1.6,
                    "volume": 12,
                },
            ]
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["timestamp"].isoformat(), "2026-01-01T00:00:00+00:00")
        self.assertEqual(rows[0]["close"], 1.6)

    def test_main_accepts_wrapped_json_payload(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            raw = root / "qqq.json"
            output = root / "qqq.normalized.json"
            raw.write_text(
                json.dumps(
                    {
                        "symbol": "QQQ",
                        "candles": [
                            {
                                "time": 1735689600000,
                                "open": "1",
                                "high": "2",
                                "low": "0.5",
                                "close": "1.5",
                                "volume": "9",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            exit_code = normalizer.main(
                [
                    "--input",
                    str(raw),
                    "--output",
                    str(output),
                    "--symbol",
                    "QQQ",
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["symbol"], "QQQ")
            self.assertEqual(payload["candles"][0]["open"], 1.0)


if __name__ == "__main__":
    unittest.main()
