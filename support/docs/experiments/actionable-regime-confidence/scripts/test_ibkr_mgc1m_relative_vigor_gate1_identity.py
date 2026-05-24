#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("run_ibkr_mgc1m_relative_vigor_reclaim_7d_gate1_v1.py")
EXPECTED_FACTOR_ID = "ibkr_mgc1m_relative_vigor_reclaim_7d_gate1_v1"
EXPECTED_BRANCH = (
    "RangeReversion -> RelativeVigorReclaim -> "
    f"RelativeVigorReclaim -> {EXPECTED_FACTOR_ID}"
)


class Mgc1mRelativeVigorGate1IdentityTest(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("mgc1m_relative_vigor_gate1", SCRIPT)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load wrapper: {SCRIPT}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_material_metadata_uses_regime_rooted_branch_not_provenance_prefix(self) -> None:
        module = self.load_module()

        self.assertEqual(module.base.BRANCH_PATH, EXPECTED_BRANCH)
        self.assertNotIn("FUTURES ->", module.base.BRANCH_PATH)
        self.assertNotIn("precious_metals", module.base.BRANCH_PATH)
        self.assertNotIn("MGC -> 1m", module.base.BRANCH_PATH)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_path = root / "mgc_1m.csv"
            data_path.write_text(
                "timestamp,open,high,low,close,volume\n"
                "2026-05-18T13:30:00+00:00,3200,3201,3199,3200.5,100\n",
                encoding="utf-8",
            )
            module.base.ROOT = root
            (root / "agent-material").mkdir()
            with patch.object(module.base, "timerange", return_value="20260518-20260518"):
                material_path = module.write_materials(data_path)[0]
            payload = json.loads(material_path.read_text(encoding="utf-8"))
            metadata = payload["consumer_evidence_profile"]

        self.assertEqual(metadata["branch_path"], EXPECTED_BRANCH)
        self.assertEqual(metadata["regime_profit_branch_path"], EXPECTED_BRANCH)
        self.assertEqual(metadata["main_regime"], "RangeReversion")
        self.assertEqual(metadata["sub_regime"], "RelativeVigorReclaim")
        self.assertEqual(metadata["sub_sub_regime_or_profit_factor"], "RelativeVigorReclaim")
        self.assertEqual(metadata["profit_factor"], EXPECTED_FACTOR_ID)
        self.assertEqual(metadata["profit_factor_id"], EXPECTED_FACTOR_ID)
        self.assertEqual(metadata["market"], "FUTURES")
        self.assertEqual(metadata["product"], "precious_metals")
        self.assertEqual(metadata["root_symbol"], "MGC")
        self.assertEqual(metadata["root_timeframe"], "1m")


if __name__ == "__main__":
    unittest.main()
