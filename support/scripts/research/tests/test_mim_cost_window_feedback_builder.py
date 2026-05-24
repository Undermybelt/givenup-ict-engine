from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import mim_cost_window_feedback_builder as builder  # noqa: E402


class MimCostWindowFeedbackBuilderTests(unittest.TestCase):
    def test_build_feedback_rows_preserves_regime_root_and_mtf_resonance(self) -> None:
        events = [
            {
                "event_date": "2026-05-21",
                "event_ts": "2026-05-21T13:59:00+00:00",
                "symbol": "TEST",
                "provider": "retained-real",
                "branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_mim_v1",
                "main_regime": "TrendExpansion",
                "sub_regime": "IntradayMomentumCostWindow",
                "profit_factor": "test_mim_v1",
                "side": 1,
                "triple_barrier_label": 1,
                "mtf_trend_resonance": {
                    "enabled": True,
                    "aligned_timeframes": ["5m", "15m"],
                    "resonance_score": 0.5,
                    "promotion_allowed": False,
                },
            },
            {
                "event_date": "2026-05-22",
                "event_ts": "2026-05-22T13:59:00+00:00",
                "symbol": "TEST",
                "provider": "retained-real",
                "branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_mim_v1",
                "main_regime": "TrendExpansion",
                "sub_regime": "IntradayMomentumCostWindow",
                "profit_factor": "test_mim_v1",
                "side": 1,
                "triple_barrier_label": -1,
                "mtf_trend_resonance": {"enabled": False, "aligned_timeframes": [], "resonance_score": 0.0},
            },
        ]

        rows = builder.build_feedback_rows(
            events,
            factor_id="test_mim_v1",
            close_after_minutes=30,
            cost_bps_per_side=5.0,
        )

        self.assertEqual(len(rows), 2)
        first = rows[0]
        self.assertEqual(first["schema_version"], "1.0")
        self.assertEqual(first["trade_id"], "sim-mim-test_mim_v1-20260521-001")
        self.assertEqual(first["direction"], "long")
        self.assertEqual(first["realized_outcome"], "win")
        self.assertEqual(first["regime_profit_branch_path"], events[0]["branch_path"])
        self.assertEqual(first["main_regime"], "TrendExpansion")
        self.assertEqual(first["sub_regime"], "IntradayMomentumCostWindow")
        self.assertEqual(first["sub_sub_regime_or_profit_factor"], "mim_cost_window_regime_filter")
        self.assertEqual(first["profit_factor"], "test_mim_v1")
        self.assertEqual(first["structural_feedback"]["path_id"], events[0]["branch_path"])
        self.assertEqual(first["structural_feedback"]["exit_reason"], "triple_barrier_profit_take")
        self.assertEqual(first["factors_used"][0]["category"], "regime_profit_branch_path")
        self.assertEqual(first["mtf_trend_resonance"]["aligned_timeframes"], ["5m", "15m"])
        self.assertFalse(first["promotion_allowed"])
        self.assertFalse(first["trade_usable"])
        self.assertFalse(first["broker_fill_evidence"])
        self.assertEqual(rows[1]["realized_outcome"], "loss")

    def test_cli_writes_feedback_and_summary_without_promotion(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            events_path = tmp / "events.jsonl"
            output_path = tmp / "feedback.jsonl"
            summary_path = tmp / "summary.json"
            events_path.write_text(
                json.dumps(
                    {
                        "event_date": "2026-05-21",
                        "event_ts": "2026-05-21T13:59:00+00:00",
                        "symbol": "TEST",
                        "provider": "retained-real",
                        "branch_path": "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_mim_v1",
                        "side": 1,
                        "triple_barrier_label": 1,
                        "mtf_trend_resonance": {"enabled": True, "aligned_timeframes": ["5m"], "resonance_score": 0.25},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            exit_code = builder.main(
                [
                    "--events-jsonl",
                    str(events_path),
                    "--output-jsonl",
                    str(output_path),
                    "--summary-json",
                    str(summary_path),
                    "--factor-id",
                    "test_mim_v1",
                ]
            )

            self.assertEqual(exit_code, 0)
            row = json.loads(output_path.read_text(encoding="utf-8").splitlines()[0])
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(row["auto_quant_run_id"], "retained_real_mim_cost_window_feedback:test_mim_v1")
            self.assertFalse(row["promotion_allowed"])
            self.assertEqual(summary["feedback_rows"], 1)
            self.assertEqual(summary["wins"], 1)
            self.assertFalse(summary["promotion_allowed"])
            self.assertFalse(summary["provider_fetch_started"])
            self.assertFalse(summary["auto_quant_started"])


if __name__ == "__main__":
    unittest.main()
