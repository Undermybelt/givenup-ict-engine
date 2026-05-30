#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name("run_tomac_index_hf_density_20_800_gate1_v1.py")


def load_runner():
    sys.path.insert(0, str(SCRIPT.parent))
    spec = importlib.util.spec_from_file_location("tomac_index_hf_density_20_800_gate1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TomacIndexHfDensityGate1Test(unittest.TestCase):
    def assert_no_cost_bps_fields(self, payload: dict[str, object]) -> None:
        forbidden = ("bps_per_side", "cost_bps", "fee_bps", "commission_bps", "net5bps", "top_by_5bps")
        self.assertFalse([key for key in payload if any(part in key for part in forbidden)], sorted(payload))

    def test_hf_density_accepts_20_to_800_trades_per_day(self) -> None:
        runner = load_runner()

        row = {
            "trade_count": 200,
            "trades_per_day": 25.0,
            "instrument_cost_total_profit_pct": 12.5,
            "instrument_cost_profit_factor": 1.35,
            "train_instrument_cost_total_profit_pct": 4.0,
            "validation_instrument_cost_total_profit_pct": 3.0,
            "test_instrument_cost_total_profit_pct": 5.0,
            "promotion_cost_verified": True,
        }

        classified = runner.classify_record(row)

        self.assertTrue(classified["density_target_20_to_800_per_day"])
        self.assertTrue(classified["gate1_survivor"])
        self.assertEqual(classified["decision"], "hf_gate1_instrument_cost_density_survivor_needs_downstream")
        self.assert_no_cost_bps_fields(classified)

    def test_hf_density_rejects_old_low_frequency_gate(self) -> None:
        runner = load_runner()

        row = {
            "trade_count": 200,
            "trades_per_day": 3.0,
            "instrument_cost_total_profit_pct": 12.5,
            "instrument_cost_profit_factor": 1.35,
            "train_instrument_cost_total_profit_pct": 4.0,
            "validation_instrument_cost_total_profit_pct": 3.0,
            "test_instrument_cost_total_profit_pct": 5.0,
            "promotion_cost_verified": True,
        }

        classified = runner.classify_record(row)

        self.assertFalse(classified["density_target_20_to_800_per_day"])
        self.assertFalse(classified["gate1_survivor"])
        self.assertEqual(classified["decision"], "reject_density_outside_20_to_800_per_day")

    def test_score_trades_uses_instrument_cost_not_fixed_bps_ladders(self) -> None:
        runner = load_runner()
        trades = [
            {"pnl_pct": 0.20, "entry": 20000.0},
            {"pnl_pct": -0.04, "entry": 20010.0},
            {"pnl_pct": 0.15, "entry": 20020.0},
        ]

        row = runner.score_trades(trades, sessions=1, symbol="MNQ")

        self.assertIn("raw_total_profit_pct", row)
        self.assertIn("instrument_cost_total_profit_pct", row)
        self.assertIn("train_instrument_cost_total_profit_pct", row)
        self.assertIn("promotion_cost_verified", row)
        self.assert_no_cost_bps_fields(row)

    def test_factor_ids_and_branches_are_regime_rooted(self) -> None:
        runner = load_runner()

        variant = runner.hf_variants()[0]

        self.assertEqual(runner.factor_id("ES", variant), "tomac_es_1m_hf_micro_vwap_reclaim_long_h2_20_to_800_gate1_v1")
        self.assertTrue(variant.branch_path.startswith("RangeReversion -> "))
        self.assertNotIn("ES", variant.branch_path)
        self.assertNotIn("futures", variant.branch_path.lower())


if __name__ == "__main__":
    unittest.main()
