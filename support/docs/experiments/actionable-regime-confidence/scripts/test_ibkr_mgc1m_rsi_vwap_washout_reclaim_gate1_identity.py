#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("run_ibkr_mgc1m_rsi_vwap_washout_reclaim_gate1_v1.py")
SPEC = importlib.util.spec_from_file_location("mgc_rsi_vwap_gate1", SCRIPT)


class MgcRsiVwapWashoutGate1IdentityTest(unittest.TestCase):
    def load_module(self):
        assert SPEC is not None and SPEC.loader is not None
        module = importlib.util.module_from_spec(SPEC)
        sys.modules[SPEC.name] = module
        SPEC.loader.exec_module(module)
        return module

    def test_branch_template_is_regime_root_first_without_provider_labels(self) -> None:
        module = self.load_module()

        self.assertEqual(
            module.BRANCH_TEMPLATE,
            "RangeReversion -> RsiVwapWashoutReclaim -> ibkr_mgc1m_rsi_vwap_washout_reclaim_gate1_v1",
        )
        branch_nodes = [part.strip() for part in module.BRANCH_TEMPLATE.split(" -> ")]
        self.assertEqual(branch_nodes[0], "RangeReversion")
        for label in ("FUTURES", "precious_metals", "MGC", "1m", "IBKR"):
            self.assertNotIn(label, branch_nodes)

    def test_downstream_requires_hard_5bps_survivor_not_2bps_only(self) -> None:
        module = self.load_module()

        self.assertFalse(module.hard_gate_downstream_allowed(True, []))
        self.assertTrue(module.hard_gate_downstream_allowed(True, ["MGC/dense/1m"]))
        self.assertFalse(module.hard_gate_downstream_allowed(False, ["MGC/dense/1m"]))

    def test_sparse_positive_exact_5bps_survives_without_density_floor(self) -> None:
        module = self.load_module()

        self.assertTrue(module.cost_survives(2, 0.13))
        self.assertFalse(module.cost_survives(0, 0.13))
        self.assertFalse(module.cost_survives(2, 0.0))
        self.assertFalse(module.cost_survives(2, -0.01))


if __name__ == "__main__":
    unittest.main()
