from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import mtf_trend_resonance as resonance  # noqa: E402


class MtfTrendResonanceTests(unittest.TestCase):
    def _write_context_csv(self, path: Path, *, start_price: float, drift: float) -> None:
        start = datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc)
        rows = ["ts,open,high,low,close,volume"]
        price = start_price
        for idx in range(8):
            open_ = price
            close = price + drift
            high = max(open_, close) + 0.08
            low = min(open_, close) - 0.08
            ts = (start + timedelta(minutes=5 * idx)).isoformat().replace("+00:00", "Z")
            rows.append(f"{ts},{open_:.6f},{high:.6f},{low:.6f},{close:.6f},{1000 + idx:.2f}")
            price = close
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    def test_long_resonance_aligns_uptrend_context_and_rejects_downtrend(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            five = tmp / "five.csv"
            fifteen = tmp / "fifteen.csv"
            self._write_context_csv(five, start_price=100.0, drift=0.40)
            self._write_context_csv(fifteen, start_price=100.0, drift=-0.35)

            summary = resonance.build_mtf_trend_resonance(
                {"5m": five, "15m": fifteen},
                event_ts="2026-05-21T12:35:00+00:00",
                side=1,
                required_timeframes=("5m", "15m"),
                min_aligned=1,
            )

        self.assertTrue(summary["enabled"])
        self.assertEqual(summary["aligned_timeframes"], ["5m"])
        self.assertEqual(summary["rejected_timeframes"], ["15m"])
        self.assertGreater(summary["resonance_score"], 0.0)
        self.assertFalse(summary["promotion_allowed"])
        self.assertFalse(summary["trade_usable"])

    def test_missing_context_is_explicitly_disabled(self) -> None:
        summary = resonance.build_mtf_trend_resonance({}, event_ts="2026-05-21T12:35:00+00:00", side=1)

        self.assertFalse(summary["enabled"])
        self.assertEqual(summary["min_aligned"], 3)
        self.assertEqual(summary["min_slope_bps"], 10.0)
        self.assertEqual(summary["resonance_score"], 0.0)
        self.assertEqual(summary["aligned_timeframes"], [])
        self.assertEqual(summary["by_timeframe"], {})

    def test_weak_positive_slope_below_cost_floor_is_rejected(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            weak = tmp / "weak.csv"
            self._write_context_csv(weak, start_price=100.0, drift=0.005)

            summary = resonance.build_mtf_trend_resonance(
                {"5m": weak},
                event_ts="2026-05-21T12:35:00+00:00",
                side=1,
                required_timeframes=("5m",),
                min_aligned=1,
            )

        self.assertFalse(summary["aligned"])
        self.assertEqual(summary["aligned_timeframes"], [])
        self.assertEqual(summary["by_timeframe"]["5m"]["reason"], "slope_bps_lt_min")
        self.assertLess(summary["by_timeframe"]["5m"]["directional_slope_bps"], 10.0)

    def test_no_trade_side_never_counts_as_resonance(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            strong = tmp / "strong.csv"
            self._write_context_csv(strong, start_price=100.0, drift=0.40)

            summary = resonance.build_mtf_trend_resonance(
                {"5m": strong},
                event_ts="2026-05-21T12:35:00+00:00",
                side=0,
                required_timeframes=("5m",),
                min_aligned=1,
            )

        self.assertFalse(summary["aligned"])
        self.assertEqual(summary["rejected_timeframes"], ["5m"])
        self.assertEqual(summary["by_timeframe"]["5m"]["reason"], "no_trade_side")

    def test_default_requires_three_aligned_context_frames(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            aligned_a = tmp / "aligned_a.csv"
            aligned_b = tmp / "aligned_b.csv"
            rejected = tmp / "rejected.csv"
            self._write_context_csv(aligned_a, start_price=100.0, drift=0.40)
            self._write_context_csv(aligned_b, start_price=100.0, drift=0.35)
            self._write_context_csv(rejected, start_price=100.0, drift=-0.30)

            summary = resonance.build_mtf_trend_resonance(
                {"5m": aligned_a, "15m": aligned_b, "30m": rejected},
                event_ts="2026-05-21T12:35:00+00:00",
                side=1,
                required_timeframes=("5m", "15m", "30m"),
            )

        self.assertEqual(summary["min_aligned"], 3)
        self.assertEqual(summary["aligned_timeframes"], ["5m", "15m"])
        self.assertFalse(summary["aligned"])


if __name__ == "__main__":
    unittest.main()
