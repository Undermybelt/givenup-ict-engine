from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import purged_cv_backtest_guard as module  # noqa: E402


class PurgedCvBacktestGuardTests(unittest.TestCase):
    def test_cross_pair_local_indexes_do_not_count_as_overlap(self) -> None:
        labels = [
            {
                "pair": "NQ/USD",
                "entry_index": 0,
                "exit_index": 5,
                "open_ts_ms": 1_700_000_000_000,
                "close_ts_ms": 1_700_000_300_000,
                "realized_R": 1.0,
            },
            {
                "pair": "YM/USD",
                "entry_index": 0,
                "exit_index": 5,
                "open_ts_ms": 1_700_001_000_000,
                "close_ts_ms": 1_700_001_300_000,
                "realized_R": 0.5,
            },
        ]

        report = module.build_guard_report(labels=labels, nb_trials=1, embargo_bars=1, fold_count=2)

        self.assertNotIn("overlapping_labels", report["leakage_flags"])

    def test_same_pair_timestamp_overlap_is_still_flagged(self) -> None:
        labels = [
            {
                "pair": "NQ/USD",
                "entry_index": 0,
                "exit_index": 5,
                "open_ts_ms": 1_700_000_000_000,
                "close_ts_ms": 1_700_000_300_000,
                "realized_R": 1.0,
            },
            {
                "pair": "NQ/USD",
                "entry_index": 2,
                "exit_index": 7,
                "open_ts_ms": 1_700_000_120_000,
                "close_ts_ms": 1_700_000_420_000,
                "realized_R": -0.5,
            },
        ]

        report = module.build_guard_report(labels=labels, nb_trials=1, embargo_bars=1, fold_count=2)

        self.assertIn("overlapping_labels", report["leakage_flags"])


if __name__ == "__main__":
    unittest.main()
