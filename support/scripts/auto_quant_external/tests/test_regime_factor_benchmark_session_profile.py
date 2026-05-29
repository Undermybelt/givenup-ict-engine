from __future__ import annotations

import math
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import regime_factor_benchmark as benchmark  # noqa: E402


def candle(ts: str, open_: float, high: float, low: float, close: float, volume: float) -> benchmark.Candle:
    return benchmark.Candle(
        timestamp=datetime.fromisoformat(ts).astimezone(timezone.utc),
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )


class RegimeFactorBenchmarkSessionProfileTests(unittest.TestCase):
    def test_needs_scalar_vectors_includes_hazard_and_bocpd_families(self) -> None:
        self.assertTrue(benchmark.needs_scalar_vectors_for_feature_sets(["hazard"]))
        self.assertTrue(benchmark.needs_scalar_vectors_for_feature_sets(["bocpd_lite"]))
        self.assertTrue(benchmark.needs_scalar_vectors_for_feature_sets(["ms_regime"]))
        self.assertFalse(benchmark.needs_scalar_vectors_for_feature_sets(["session_profile"]))

    def test_session_profile_snapshot_matches_market_profile_formulas(self) -> None:
        session = [
            candle("2026-05-26T13:30:00+00:00", 100.0, 101.0, 99.5, 100.5, 10),
            candle("2026-05-26T13:35:00+00:00", 100.5, 102.0, 100.2, 101.0, 30),
            candle("2026-05-26T13:40:00+00:00", 101.0, 102.5, 100.8, 101.0, 40),
            candle("2026-05-26T14:00:00+00:00", 101.0, 103.0, 100.9, 102.0, 25),
            candle("2026-05-26T14:15:00+00:00", 102.0, 103.5, 101.8, 103.0, 20),
            candle("2026-05-26T14:30:00+00:00", 103.0, 104.0, 102.7, 103.0, 20),
            candle("2026-05-26T14:35:00+00:00", 103.0, 105.0, 102.9, 104.5, 50),
        ]

        snapshot = benchmark.session_profile_snapshot(session, row_size=0.5)

        self.assertEqual((99.5, 102.5), snapshot["open_range"])
        self.assertEqual((99.5, 104.0), snapshot["initial_balance"])
        self.assertEqual(101.0, snapshot["poc_price"])
        self.assertEqual((101.0, 104.5), snapshot["value_area"])
        self.assertEqual(97.5, snapshot["balanced_target"])

    def test_opening_drive_session_profile_factor_detects_continuation_acceptance(self) -> None:
        candles = []
        price = 100.0
        start = datetime(2026, 5, 26, 13, 30, tzinfo=timezone.utc)
        for minute in range(80):
            ts = start + timedelta(minutes=minute)
            if minute < 10:
                open_ = price
                close = price + 0.04
                high = close + 0.10
                low = open_ - 0.05
                volume = 120 + minute
            elif minute < 60:
                open_ = price
                close = price + 0.08
                high = close + 0.10
                low = open_ - 0.04
                volume = 150 + minute
            else:
                open_ = price
                close = price + 0.18
                high = close + 0.12
                low = open_ - 0.03
                volume = 260 + minute * 2
            candles.append(
                benchmark.Candle(
                    timestamp=ts,
                    open=open_,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                )
            )
            price = close

        features = benchmark.build_features(candles)
        features.update(benchmark.session_profile_feature_vectors(candles, features))
        factor = benchmark.build_factor_functions(candles, features)["opening_drive_session_profile_v1"]

        pred = factor(len(candles) - 1)

        self.assertEqual("trend_continuation", pred.label)
        self.assertTrue(math.isfinite(pred.score))
        self.assertGreater(pred.score, 0.0)


if __name__ == "__main__":
    unittest.main()
