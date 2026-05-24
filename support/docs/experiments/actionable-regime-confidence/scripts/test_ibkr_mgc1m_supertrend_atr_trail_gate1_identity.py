#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name("run_ibkr_mgc1m_supertrend_atr_trail_7d_gate1_v1.py")


def load_wrapper():
    spec = importlib.util.spec_from_file_location("ibkr_mgc_supertrend_atr_gate1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class IbkrMgcSuperTrendAtrGate1IdentityTest(unittest.TestCase):
    def test_branch_path_is_regime_rooted_without_provider_labels(self) -> None:
        wrapper = load_wrapper()

        self.assertEqual(
            wrapper.BRANCH_PATH,
            "TrendExpansion -> SuperTrendAtrTrail -> ibkr_mgc1m_supertrend_atr_trail_7d_gate1_v1",
        )
        for label in ("FUTURES", "precious_metals", "MGC", "1m", "IBKR"):
            self.assertNotIn(label, wrapper.BRANCH_PATH.split(" -> "))

    def test_sparse_positive_exact_5bps_survives_without_density_floor(self) -> None:
        wrapper = load_wrapper()

        self.assertTrue(wrapper.cost_survives(2, 0.08))
        self.assertFalse(wrapper.cost_survives(0, 0.08))
        self.assertFalse(wrapper.cost_survives(2, 0.0))
        self.assertFalse(wrapper.cost_survives(2, -0.01))

    def test_downstream_requires_hard_5bps_survivor_not_2bps_only(self) -> None:
        wrapper = load_wrapper()

        self.assertFalse(wrapper.hard_gate_downstream_allowed(True, []))
        self.assertTrue(wrapper.hard_gate_downstream_allowed(True, ["MGC/st_dense/1m"]))
        self.assertFalse(wrapper.hard_gate_downstream_allowed(False, ["MGC/st_dense/1m"]))


if __name__ == "__main__":
    unittest.main()
