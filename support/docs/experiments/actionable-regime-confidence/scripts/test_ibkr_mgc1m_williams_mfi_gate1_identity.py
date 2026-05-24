#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("run_ibkr_mgc1m_williams_mfi_reclaim_7d_gate1_v1.py")
EXPECTED_FACTOR_ID = "ibkr_mgc1m_williams_mfi_reclaim_7d_gate1_v1"
EXPECTED_BRANCH = (
    "RangeReversion -> WilliamsMfiReclaim -> "
    f"WilliamsMfiReclaim -> {EXPECTED_FACTOR_ID}"
)


class Mgc1mWilliamsMfiGate1IdentityTest(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("mgc1m_williams_mfi_gate1", SCRIPT)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load wrapper: {SCRIPT}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_material_metadata_uses_regime_rooted_branch_not_provenance_prefix(self) -> None:
        module = self.load_module()

        self.assertEqual(module.BRANCH_PATH, EXPECTED_BRANCH)
        self.assertNotIn("FUTURES ->", module.BRANCH_PATH)
        self.assertNotIn("precious_metals", module.BRANCH_PATH)
        self.assertNotIn("MGC -> 1m", module.BRANCH_PATH)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            module.ROOT = root
            (root / "agent-material").mkdir(parents=True, exist_ok=True)
            data_path = root / "ibkr_mgc_202606_1m_7d.csv"
            data_path.write_text(
                "timestamp,open,high,low,close,volume\n"
                "2026-05-18T13:30:00+00:00,3000,3010,2990,3005,100\n",
                encoding="utf-8",
            )
            material = module.write_materials(data_path)[0]
            payload = json.loads(material.read_text(encoding="utf-8"))
            metadata = payload["consumer_evidence_profile"]

        self.assertEqual(metadata["branch_path"], EXPECTED_BRANCH)
        self.assertEqual(metadata["regime_profit_branch_path"], EXPECTED_BRANCH)
        self.assertEqual(metadata["main_regime"], "RangeReversion")
        self.assertEqual(metadata["sub_regime"], "WilliamsMfiReclaim")
        self.assertEqual(metadata["sub_sub_regime_or_profit_factor"], "WilliamsMfiReclaim")
        self.assertEqual(metadata["profit_factor_id"], EXPECTED_FACTOR_ID)
        self.assertEqual(metadata["market"], "FUTURES")
        self.assertEqual(metadata["product"], "precious_metals")
        self.assertEqual(metadata["root_symbol"], "MGC")
        self.assertEqual(metadata["root_timeframe"], "1m")

    def test_sparse_exact_1m_positive_5bps_is_not_density_blocked(self) -> None:
        module = self.load_module()

        rows, survivors_2, survivors_5, _paths, branch_ok, downstream = module.build_cost_summary(
            [
                {
                    "package_id": "ibkr-mgc-williams-mfi-reclaim-willmfi-balanced-1m-7d-v1",
                    "trade_count": 2,
                    "total_profit_pct": 0.45,
                    "win_rate_pct": 100.0,
                    "branch_path": module.BRANCH_PATH,
                }
            ]
        )

        self.assertEqual(rows[0]["5bps_per_side_total_profit_pct"], 0.25)
        self.assertEqual(survivors_2, ["MGC/willmfi_balanced/1m"])
        self.assertEqual(survivors_5, ["MGC/willmfi_balanced/1m"])
        self.assertTrue(branch_ok)
        self.assertTrue(downstream)

    def test_downstream_requires_exact_5bps_not_2bps_only(self) -> None:
        module = self.load_module()

        _rows, survivors_2, survivors_5, _paths, branch_ok, downstream = module.build_cost_summary(
            [
                {
                    "package_id": "ibkr-mgc-williams-mfi-reclaim-willmfi-dense-1m-7d-v1",
                    "trade_count": 2,
                    "total_profit_pct": 0.09,
                    "win_rate_pct": 50.0,
                    "branch_path": module.BRANCH_PATH,
                }
            ]
        )

        self.assertEqual(survivors_2, ["MGC/willmfi_dense/1m"])
        self.assertEqual(survivors_5, [])
        self.assertTrue(branch_ok)
        self.assertFalse(downstream)


if __name__ == "__main__":
    unittest.main()
