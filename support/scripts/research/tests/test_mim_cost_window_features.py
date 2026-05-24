from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import mim_cost_window_features as mim  # noqa: E402


class MimCostWindowFeatureTests(unittest.TestCase):
    def _bars(self) -> list[mim.Bar]:
        start = datetime(2026, 5, 22, 13, 30, tzinfo=timezone.utc)
        bars: list[mim.Bar] = []
        price = 100.0
        for idx in range(90):
            drift = 0.035 if idx < 30 else 0.012
            open_ = price
            close = price + drift
            high = close + 0.025
            low = open_ - 0.020
            volume = 1000 + idx * 8 + (500 if idx < 30 else 0)
            bars.append(mim.Bar(start + timedelta(minutes=idx), open_, high, low, close, volume))
            price = close
        return bars

    def test_source_backed_feature_contract_flags_low_cost_momentum_window(self) -> None:
        features = mim.mim_cost_window_features(self._bars())

        self.assertGreater(features.first_window_return, 0.009)
        self.assertGreater(features.first_window_realized_variance, 0.0)
        self.assertGreater(features.first_window_amihud, 0.0)
        self.assertGreaterEqual(features.corwin_schultz_spread, 0.0)
        self.assertLess(features.corwin_schultz_spread, 0.0065)
        self.assertLess(features.basic_high_low_spread, 0.0065)
        self.assertGreater(features.rvol, 1.0)
        self.assertGreaterEqual(features.momentum_state_prob, 0.58)
        self.assertLessEqual(features.posterior_entropy_proxy, 0.92)
        self.assertTrue(features.eligible_long)

    def test_triple_barrier_adapter_labels_primary_event_without_new_dependency(self) -> None:
        bars = self._bars()

        self.assertEqual(
            mim.triple_barrier_label(bars, 0, profit_take=0.004, stop_loss=0.020, horizon=40),
            1,
        )
        stopped = [
            mim.Bar(bar.ts, bar.open, bar.high, min(bar.low, bar.close - 2.0), bar.close, bar.volume)
            if idx == 2
            else bar
            for idx, bar in enumerate(bars)
        ]
        self.assertEqual(
            mim.triple_barrier_label(stopped, 0, profit_take=0.050, stop_loss=0.010, horizon=10),
            -1,
        )

    def test_reader_accepts_ibkr_ts_column(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bars.csv"
            path.write_text(
                "ts,open,high,low,close,volume\n"
                "2026-05-22T13:30:00Z,100,100.2,99.9,100.1,1000\n"
                "2026-05-22T13:31:00Z,100.1,100.3,100.0,100.2,1100\n",
                encoding="utf-8",
            )
            rows = mim.read_bars(path)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].close, 100.1)


if __name__ == "__main__":
    unittest.main()
