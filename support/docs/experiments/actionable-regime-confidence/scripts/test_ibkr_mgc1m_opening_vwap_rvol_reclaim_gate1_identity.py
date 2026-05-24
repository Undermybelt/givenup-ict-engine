#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("run_ibkr_mgc1m_opening_vwap_rvol_reclaim_7d_gate1_v1.py")
SPEC = importlib.util.spec_from_file_location("mgc_opening_vwap_gate1", SCRIPT)


class MgcOpeningVwapRvolGate1IdentityTest(unittest.TestCase):
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
            "RangeReversion -> OpeningVwapRvolReclaim -> ibkr_mgc1m_opening_vwap_rvol_reclaim_7d_gate1_v1",
        )
        branch_nodes = [part.strip() for part in module.BRANCH_PATH.split(" -> ")]
        self.assertEqual(branch_nodes[0], "RangeReversion")
        for label in ("FUTURES", "precious_metals", "MGC", "IBKR"):
            self.assertNotIn(label, branch_nodes)

        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('"branch_path": branch', source)
        self.assertIn('"regime_profit_branch_path": branch', source)
        self.assertIn('"provider": "IBKR"', source)
        self.assertIn('"market": "FUTURES"', source)
        self.assertIn('"product": contract.product', source)
        self.assertIn('"root_symbol": contract.symbol', source)
        self.assertIn('"root_timeframe": "1m"', source)

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
