#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("run_board_a_positive_negative_feedback_ingress_v1.py")
SPEC = importlib.util.spec_from_file_location("board_a_feedback_ingress", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BoardAPositiveNegativeFeedbackIngressTest(unittest.TestCase):
    def test_unrooted_non_positive_rows_are_not_negative_boundary_samples(self) -> None:
        rows = [
            {
                "unit_label": "provider preflight without rooted factor",
                "trade_count": 0,
                "total_profit_pct": 0.0,
                "win_rate_pct": 0.0,
                "source_rank_file_index": 1,
                "source_rank_row_index": 1,
            },
            {
                "package_id": "rooted-trend-pullback-failure",
                "regime_profit_branch_path": "TrendExpansion -> PullbackSecondExpansion -> factor_v1",
                "trade_count": 3,
                "total_profit_pct": -0.42,
                "win_rate_pct": 33.3,
                "source_rank_file_index": 2,
                "source_rank_row_index": 1,
            },
        ]

        normalized = MODULE.normalize_target_rows(
            rows,
            symbol="BOARD_A_AGGREGATED_ROOTED_FEEDBACK_20260523",
            candidate_set_id="board-a-feedback-test",
        )

        self.assertEqual(normalized[0]["feedback_class"], "unrooted_observation_negative")
        self.assertEqual(normalized[0]["realized_outcome"], "blocked")
        self.assertEqual(normalized[0]["exit_reason"], "unrooted_observation_negative")
        self.assertNotIn("unknown", normalized[0]["path_id"])
        self.assertEqual(normalized[1]["feedback_class"], "negative_boundary_sample")
        self.assertEqual(normalized[1]["realized_outcome"], "loss")


if __name__ == "__main__":
    unittest.main()
