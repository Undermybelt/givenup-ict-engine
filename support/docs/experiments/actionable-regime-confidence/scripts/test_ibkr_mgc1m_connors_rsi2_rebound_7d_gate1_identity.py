#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("run_ibkr_mgc1m_connors_rsi2_rebound_7d_gate1_v1.py")
SPEC = importlib.util.spec_from_file_location("mgc_connors_rsi2_gate1", SCRIPT)


class MgcConnorsRsi2ReboundGate1IdentityTest(unittest.TestCase):
    def load_module(self):
        assert SPEC is not None and SPEC.loader is not None
        module = importlib.util.module_from_spec(SPEC)
        sys.modules[SPEC.name] = module
        SPEC.loader.exec_module(module)
        return module

    def test_branch_path_is_regime_root_first_and_profile_keeps_labels(self) -> None:
        module = self.load_module()

        self.assertEqual(
            module.BRANCH_PATH,
            "RangeReversion -> ConnorsRsi2Rebound -> ibkr_mgc1m_connors_rsi2_rebound_7d_gate1_v1",
        )
        branch_nodes = [part.strip() for part in module.BRANCH_PATH.split(" -> ")]
        self.assertEqual(branch_nodes[0], "RangeReversion")
        for label in ("FUTURES", "precious_metals", "MGC", "IBKR"):
            self.assertNotIn(label, branch_nodes)

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "run"
            (root / "agent-material").mkdir(parents=True, exist_ok=True)
            module.ROOT = root
            data_path = root / "data" / "provider" / "normalized" / "ibkr_mgc_1m.csv"
            data_path.parent.mkdir(parents=True, exist_ok=True)
            data_path.write_text(
                "timestamp,open,high,low,close,volume\n"
                "2026-05-19T13:30:00Z,1,2,0.5,1.5,100\n",
                encoding="utf-8",
            )

            materials = module.write_materials(data_path)

            payload = json.loads(materials[0].read_text(encoding="utf-8"))
            profile = payload["consumer_evidence_profile"]

            self.assertEqual(profile["branch_path"], module.BRANCH_PATH)
            self.assertEqual(profile["regime_profit_branch_path"], module.BRANCH_PATH)
            self.assertEqual(profile["main_regime"], "RangeReversion")
            self.assertEqual(profile["sub_regime"], "ConnorsRsi2Rebound")
            self.assertEqual(profile["sub_sub_regime_or_profit_factor"], module.FACTOR_ID)
            self.assertEqual(profile["profit_factor"], module.FACTOR_ID)
            self.assertEqual(profile["provider"], "IBKR")
            self.assertEqual(profile["market"], "FUTURES")
            self.assertEqual(profile["product"], "precious_metals")
            self.assertEqual(profile["root_symbol"], "MGC")
            self.assertEqual(profile["root_timeframe"], "1m")

    def test_gate1_downstream_predicate_uses_5bps_and_no_density_floor(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")

        self.assertIn(
            'record["survives_5bps_per_side"] = trades > 0 and record["5bps_per_side_total_profit_pct"] > 0',
            source,
        )
        self.assertIn("downstream = branch_ok and bool(survivors_5)", source)
        self.assertNotIn("downstream = branch_ok and bool(survivors_2)", source)
        self.assertNotIn('record["survives_5bps_per_side"] = trades >= 6', source)


if __name__ == "__main__":
    unittest.main()
