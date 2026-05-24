from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "support" / "scripts" / "research"
sys.path.insert(0, str(SCRIPTS))

import mim_cost_window_gate_report as report  # noqa: E402


class MimCostWindowGateReportTests(unittest.TestCase):
    def _write_events(self, rows: list[dict[str, object]]) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "events.jsonl"
        path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )
        return path

    def test_positive_triple_barrier_events_prepare_gate1_without_downstream(self) -> None:
        branch = "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> alpha_v1"
        events = self._write_events(
            [
                {
                    "branch_path": branch,
                    "event_ts": "2026-05-18T14:00:00+00:00",
                    "side": 1,
                    "eligible_long": True,
                    "triple_barrier_label": 1,
                    "mtf_trend_resonance": {"enabled": True, "resonance_score": 0.8, "aligned_timeframes": ["5m"]},
                },
                {
                    "branch_path": branch,
                    "event_ts": "2026-05-20T14:00:00+00:00",
                    "side": 1,
                    "eligible_long": True,
                    "triple_barrier_label": 0,
                    "mtf_trend_resonance": {"enabled": True, "resonance_score": 0.4, "aligned_timeframes": []},
                },
            ]
        )

        result = report.build_gate_report(events, branch_path=branch, factor_id="alpha_v1")

        self.assertEqual(result["classification"], "retained_real_gate1_candidate")
        self.assertEqual(result["event_count"], 2)
        self.assertEqual(result["positive_triple_barrier_count"], 1)
        self.assertTrue(result["frequency"]["ok"])
        self.assertTrue(result["auto_quant_gate1_ready"])
        self.assertFalse(result["downstream_allowed"])
        self.assertFalse(result["promotion_allowed"])
        self.assertFalse(result["trade_usable"])

    def test_branch_path_drift_rejects_candidate(self) -> None:
        branch = "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> alpha_v1"
        events = self._write_events(
            [
                {
                    "branch_path": "RangeReversion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> alpha_v1",
                    "event_ts": "2026-05-18T14:00:00+00:00",
                    "side": 1,
                    "eligible_long": True,
                    "triple_barrier_label": 1,
                }
            ]
        )

        result = report.build_gate_report(events, branch_path=branch, factor_id="alpha_v1")

        self.assertEqual(result["classification"], "reject_branch_path_mismatch")
        self.assertFalse(result["auto_quant_gate1_ready"])
        self.assertIn("branch_path_mismatch", result["blockers"])

    def test_regime_profit_branch_path_drift_rejects_candidate(self) -> None:
        branch = "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> alpha_v1"
        events = self._write_events(
            [
                {
                    "branch_path": branch,
                    "regime_profit_branch_path": (
                        "RangeReversion -> IntradayMomentumCostWindow -> "
                        "mim_cost_window_regime_filter -> alpha_v1"
                    ),
                    "event_ts": "2026-05-18T14:00:00+00:00",
                    "side": 1,
                    "eligible_long": True,
                    "triple_barrier_label": 1,
                }
            ]
        )

        result = report.build_gate_report(events, branch_path=branch, factor_id="alpha_v1")

        self.assertEqual(result["classification"], "reject_branch_path_mismatch")
        self.assertFalse(result["auto_quant_gate1_ready"])
        self.assertIn("branch_path_mismatch", result["blockers"])

    def test_frequency_window_blocks_gate1_readiness(self) -> None:
        branch = "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> alpha_v1"
        events = self._write_events(
            [
                {
                    "branch_path": branch,
                    "event_ts": "2026-05-18T14:00:00+00:00",
                    "side": 1,
                    "eligible_long": True,
                    "triple_barrier_label": 1,
                },
                {
                    "branch_path": branch,
                    "event_ts": "2026-05-18T14:05:00+00:00",
                    "side": 1,
                    "eligible_long": True,
                    "triple_barrier_label": 1,
                },
                {
                    "branch_path": branch,
                    "event_ts": "2026-05-18T14:10:00+00:00",
                    "side": 1,
                    "eligible_long": True,
                    "triple_barrier_label": 1,
                },
                {
                    "branch_path": branch,
                    "event_ts": "2026-05-18T14:15:00+00:00",
                    "side": 1,
                    "eligible_long": True,
                    "triple_barrier_label": 1,
                },
                {
                    "branch_path": branch,
                    "event_ts": "2026-05-24T14:00:00+00:00",
                    "side": 1,
                    "eligible_long": True,
                    "triple_barrier_label": 1,
                },
            ]
        )

        result = report.build_gate_report(events, branch_path=branch, factor_id="alpha_v1")

        self.assertEqual(result["classification"], "retain_observation_only")
        self.assertFalse(result["frequency"]["ok"])
        self.assertIn("trades_per_day_gt_max", result["blockers"])
        self.assertIn("max_gap_days_gt_allowed", result["blockers"])
        self.assertFalse(result["auto_quant_gate1_ready"])


if __name__ == "__main__":
    unittest.main()
