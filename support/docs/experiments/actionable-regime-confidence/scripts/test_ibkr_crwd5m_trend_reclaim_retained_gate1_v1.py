#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().with_name("run_ibkr_crwd5m_trend_reclaim_retained_gate1_v1.py")


def load_runner():
    spec = importlib.util.spec_from_file_location("ibkr_crwd5m_trend_reclaim_retained_gate1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class IbkrCrwd5mTrendReclaimRetainedGate1Test(unittest.TestCase):
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
                    "package_id": "ibkr-crwd5m-trend-reclaim-retained-5m-v1",
                    "timeframe": "5m",
                    "trade_count": 35,
                    "total_profit_pct": 12.5,
                    "win_rate_pct": 57.0,
                    "sharpe": 1.35,
                }
            ],
            {"5m": 20},
        )

        row = rows[0]
        self.assertEqual(row["raw_total_profit_pct"], 12.5)
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

    def test_material_payload_uses_instrument_cost_verification_not_fixed_bps_priority(self) -> None:
        runner = load_runner()

        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(runner, "ROOT", Path(tmpdir)):
            normalized = Path(tmpdir) / "data" / "ibkr_crwd_5m_3m.csv"
            normalized.parent.mkdir(parents=True)
            (Path(tmpdir) / "agent-material").mkdir(parents=True)
            normalized.write_text(
                "timestamp,open,high,low,close,volume\n"
                "2024-01-02 09:30:00,100,101,99,100.5,1000\n",
                encoding="utf-8",
            )

            material_path = runner.write_material_for_spec(runner.SPECS[0], normalized)
            payload = json.loads(material_path.read_text(encoding="utf-8"))

        self.assertIn("instrument_cost_verification", payload["evaluation_priority"])
        self.assertFalse(payload["consumer_evidence_profile"]["promotion_cost_verified"])
        self.assertEqual(payload["consumer_evidence_profile"]["cost_model_status"], "cost_model_unverified")
        self.assert_no_fixed_cost_bps_text(json.dumps(payload, sort_keys=True))

    def test_terminal_summary_writes_no_fixed_bps_cost_text(self) -> None:
        runner = load_runner()
        metrics = {
            "decision": "gate1_cost_model_unverified_no_downstream",
            "interpretation": "Exact product commission model is unverified; fail closed.",
            "next_useful_work": "Verify official IBKR equity commission schedule before downstream.",
        }
        rows = [
            {
                "timeframe": "5m",
                "trade_count": 35,
                "trades_per_day": 1.75,
                "raw_total_profit_pct": 12.5,
                "instrument_cost_total_profit_pct": None,
                "cost_model_status": "cost_model_unverified",
                "promotion_cost_verified": False,
                "survives_instrument_cost": False,
                "minimum_trade_sample_floor_met": True,
                "gate1_survivor": False,
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(runner, "ROOT", Path(tmpdir)):
            (Path(tmpdir) / "summaries").mkdir(parents=True)
            runner.write_terminal_summary(metrics, rows)
            text = (Path(tmpdir) / "summaries" / "terminal_decision_summary.md").read_text(encoding="utf-8")

        self.assertIn("Instrument Cost Verification Table", text)
        self.assert_no_fixed_cost_bps_text(text)


if __name__ == "__main__":
    unittest.main()
