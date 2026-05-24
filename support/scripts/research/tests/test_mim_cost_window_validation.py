from __future__ import annotations

import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import mim_cost_window_validation as validation  # noqa: E402


class MimCostWindowValidationTests(unittest.TestCase):
    def _events(self) -> list[dict[str, object]]:
        start = date(2026, 5, 1)
        return [
            {
                "event_date": (start + timedelta(days=idx)).isoformat(),
                "branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_v1",
                "base_timeframe": "1m",
                "triple_barrier_label": 1 if idx % 3 == 0 else 0,
            }
            for idx in range(12)
        ]

    def test_purged_walk_forward_splits_remove_nearby_train_events(self) -> None:
        splits = validation.purged_walk_forward_splits(
            self._events(),
            n_splits=3,
            purge_days=1,
            embargo_days=1,
        )

        self.assertEqual([split.name for split in splits], ["fold_1", "fold_2", "fold_3"])
        for split in splits:
            self.assertTrue(split.test_indices)
            self.assertTrue(split.train_indices)
            self.assertFalse(set(split.train_indices) & set(split.test_indices))
            first_test = min(split.test_dates)
            last_test = max(split.test_dates)
            for train_date in split.train_dates:
                self.assertTrue(train_date < first_test - timedelta(days=1) or train_date > last_test + timedelta(days=1))

    def test_summary_preserves_no_promotion_flags_and_regime_root(self) -> None:
        splits = validation.purged_walk_forward_splits(self._events(), n_splits=2)
        summary = validation.build_validation_summary(
            splits,
            branch_path="TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_v1",
        )

        self.assertEqual(summary["branch_path"], "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_v1")
        self.assertEqual(summary["split_count"], 2)
        self.assertFalse(summary["promotion_allowed"])
        self.assertFalse(summary["trade_usable"])
        self.assertFalse(summary["downstream_allowed"])


if __name__ == "__main__":
    unittest.main()
