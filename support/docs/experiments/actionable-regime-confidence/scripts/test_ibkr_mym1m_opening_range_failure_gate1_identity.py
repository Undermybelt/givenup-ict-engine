#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("run_ibkr_mym1m_opening_range_failure_reclaim_7d_gate1_v1.py")
EXPECTED_FACTOR_ID = "ibkr_mym1m_opening_range_failure_reclaim_7d_gate1_v1"
EXPECTED_BRANCH = (
    "RangeReversion -> OpeningRangeFailureReclaim -> "
    f"OpeningRangeFailureReclaim -> {EXPECTED_FACTOR_ID}"
)


class Mym1mOpeningRangeFailureGate1IdentityTest(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("mym1m_opening_range_failure_gate1", SCRIPT)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load wrapper: {SCRIPT}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_material_metadata_uses_regime_rooted_branch_not_provenance_prefix(self) -> None:
        module = self.load_module()
        contract = module.CONTRACTS[0]

        branch_path = getattr(module, "BRANCH_PATH", None)
        self.assertEqual(branch_path, EXPECTED_BRANCH)
        self.assertNotIn("FUTURES ->", branch_path)
        self.assertNotIn("equity_index", branch_path)
        self.assertNotIn("MYM -> 1m", branch_path)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            module.ROOT = root
            (root / "agent-material").mkdir(parents=True, exist_ok=True)
            data_path = root / "ibkr_mym_202606_1m_7d.csv"
            data_path.write_text(
                "timestamp,open,high,low,close,volume\n"
                "2026-05-18T13:30:00+00:00,42000,42010,41990,42005,100\n",
                encoding="utf-8",
            )
            material = module.write_materials(contract, data_path)[0]
            payload = json.loads(material.read_text(encoding="utf-8"))
            metadata = payload["consumer_evidence_profile"]

        self.assertEqual(metadata["branch_path"], EXPECTED_BRANCH)
        self.assertEqual(metadata["regime_profit_branch_path"], EXPECTED_BRANCH)
        self.assertEqual(metadata["main_regime"], "RangeReversion")
        self.assertEqual(metadata["sub_regime"], "OpeningRangeFailureReclaim")
        self.assertEqual(metadata["sub_sub_regime_or_profit_factor"], "OpeningRangeFailureReclaim")
        self.assertEqual(metadata["profit_factor_id"], EXPECTED_FACTOR_ID)
        self.assertEqual(metadata["market"], "FUTURES")
        self.assertEqual(metadata["product"], "equity_index")
        self.assertEqual(metadata["root_symbol"], "MYM")
        self.assertEqual(metadata["root_timeframe"], "1m")

    def test_sparse_positive_instrument_cost_survives_without_density_floor(self) -> None:
        module = self.load_module()

        rows, survivors, branch_ok = module.build_cost_summary(
            [
                {
                    "package_id": "ibkr-mym-opening-range-failure-reclaim-dense-1m-7d-v1",
                    "trade_count": 2,
                    "total_profit_pct": 0.45,
                    "win_rate_pct": 100.0,
                    "branch_path": EXPECTED_BRANCH,
                }
            ],
            representative_price=42000.0,
        )

        self.assertIn("instrument_cost_total_profit_pct", rows[0])
        self.assertIn("survives_instrument_cost", rows[0])
        self.assertNotIn("5bps_per_side_total_profit_pct", rows[0])
        self.assertTrue(rows[0]["survives_instrument_cost"])
        self.assertEqual(survivors, ["MYM/dense/1m"])
        self.assertTrue(branch_ok)

    def test_downstream_requires_verified_instrument_cost_survivor(self) -> None:
        module = self.load_module()

        self.assertFalse(module.hard_gate_downstream_allowed(True, []))
        self.assertTrue(module.hard_gate_downstream_allowed(True, ["MYM/dense/1m"]))
        self.assertFalse(module.hard_gate_downstream_allowed(False, ["MYM/dense/1m"]))


if __name__ == "__main__":
    unittest.main()
