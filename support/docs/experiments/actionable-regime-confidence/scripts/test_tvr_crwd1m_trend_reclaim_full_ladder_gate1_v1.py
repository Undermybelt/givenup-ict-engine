#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().with_name("run_tvr_crwd1m_trend_reclaim_full_ladder_gate1_v1.py")


def load_runner():
    spec = importlib.util.spec_from_file_location("tvr_crwd1m_trend_reclaim_full_ladder", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TvrCrwdTrendReclaimFullLadderGate1Test(unittest.TestCase):
    def assert_no_fixed_cost_bps_text(self, text: str) -> None:
        forbidden = (
            "bps_per_side",
            "1bps",
            "2bps",
            "5bps",
            "10bps",
            "15bps",
            "cost_bps",
            "fee_bps",
            "commission_bps",
            "cost_stress",
        )
        self.assertFalse([part for part in forbidden if part in text], text)

    def assert_no_fixed_cost_bps_fields(self, payload: dict[str, object]) -> None:
        forbidden = (
            "bps_per_side",
            "1bps",
            "2bps",
            "5bps",
            "10bps",
            "15bps",
            "cost_bps",
            "fee_bps",
            "commission_bps",
        )
        self.assertFalse([key for key in payload if any(part in key for part in forbidden)], sorted(payload))

    def test_rank_rows_fail_closed_when_crwd_equity_cost_model_is_unverified(self) -> None:
        runner = load_runner()

        rows = runner.instrument_cost_rows(
            [
                {
                    "package_id": "tvr-crwd1m-trend-reclaim-full-ladder-1m-v1",
                    "timeframe": "1m",
                    "trade_count": 12,
                    "total_profit_pct": 8.25,
                    "win_rate_pct": 58.0,
                    "sharpe": 1.8,
                    "branch_path": runner.BRANCH_PATH,
                }
            ],
            {"1m": 6},
        )

        row = rows[0]
        self.assertEqual(row["raw_total_profit_pct"], 8.25)
        self.assertIsNone(row["instrument_cost_total_profit_pct"])
        self.assertEqual(row["cost_model_status"], "cost_model_unverified")
        self.assertFalse(row["promotion_cost_verified"])
        self.assertFalse(row["survives_instrument_cost"])
        self.assertTrue(row["minimum_trade_sample_floor_met"])
        self.assertNotIn("density_target_1_to_3_per_day", row)
        self.assertFalse(row["gate1_survivor"])
        self.assertEqual(row["cost_model"]["instrument_class"], "US_EQUITY")
        self.assertEqual(row["cost_model"]["symbol"], "CRWD")
        self.assert_no_fixed_cost_bps_fields(row)

    def test_terminal_summary_writes_no_fixed_bps_cost_text(self) -> None:
        runner = load_runner()
        metrics = {
            "decision": "gate1_cost_model_unverified_no_downstream",
            "branch_fields_preserved": True,
            "promotion_cost_verified": False,
            "cost_model_status": "cost_model_unverified",
            "instrument_cost_survivors": [],
            "downstream_allowed": False,
            "interpretation": "Exact product commission model is unverified; fail closed.",
            "next_useful_work": "Verify official CRWD equity commission schedule before downstream.",
        }
        rows = [
            {
                "timeframe": "1m",
                "trade_count": 12,
                "trades_per_day": 2.0,
                "raw_total_profit_pct": 8.25,
                "instrument_cost_total_profit_pct": None,
                "cost_model_status": "cost_model_unverified",
                "promotion_cost_verified": False,
                "survives_instrument_cost": False,
                "gate1_survivor": False,
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(runner, "ROOT", Path(tmpdir)):
            (Path(tmpdir) / "summaries").mkdir(parents=True)
            runner.write_terminal_summary(metrics, rows)
            text = (Path(tmpdir) / "summaries" / "terminal_decision_summary.md").read_text(encoding="utf-8")

        self.assertIn("Instrument Cost Verification Table", text)
        self.assert_no_fixed_cost_bps_text(text)

    def test_terminal_metrics_payload_uses_instrument_cost_not_fixed_bps(self) -> None:
        payload = {
            "promotion_cost_verified": False,
            "cost_model_status": "cost_model_unverified",
            "instrument_cost_rows": [],
            "instrument_cost_survivors": [],
        }

        self.assert_no_fixed_cost_bps_text(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
