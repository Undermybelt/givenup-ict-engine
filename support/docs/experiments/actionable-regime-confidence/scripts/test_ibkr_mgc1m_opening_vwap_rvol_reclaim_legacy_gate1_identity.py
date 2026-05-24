#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name("run_ibkr_mgc1m_opening_vwap_rvol_reclaim_gate1_v1.py")


def load_wrapper():
    spec = importlib.util.spec_from_file_location("ibkr_mgc_opening_vwap_rvol_legacy_gate1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class IbkrMgcOpeningVwapRvolLegacyGate1IdentityTest(unittest.TestCase):
    def test_branch_template_is_regime_rooted_without_provider_labels(self) -> None:
        wrapper = load_wrapper()

        self.assertEqual(
            wrapper.BRANCH_TEMPLATE,
            "RangeReversion -> OpeningVwapRvolReclaim -> ibkr_mgc1m_opening_vwap_rvol_reclaim_gate1_v1",
        )
        for label in ("FUTURES", "precious_metals", "MGC", "1m", "IBKR"):
            self.assertNotIn(label, wrapper.BRANCH_TEMPLATE.split(" -> "))

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
