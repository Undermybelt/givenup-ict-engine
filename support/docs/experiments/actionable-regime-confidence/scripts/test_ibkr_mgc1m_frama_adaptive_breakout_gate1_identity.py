#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name("run_ibkr_mgc1m_frama_adaptive_breakout_7d_gate1_v1.py")


def load_wrapper():
    spec = importlib.util.spec_from_file_location("ibkr_mgc_frama_gate1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class IbkrMgcFramaGate1IdentityTest(unittest.TestCase):
    def test_branch_path_is_regime_rooted_without_provider_labels(self) -> None:
        wrapper = load_wrapper()

        self.assertEqual(
            wrapper.base.BRANCH_PATH,
            "AdaptiveTrendExpansion -> FramaAdaptiveBreakout -> ibkr_mgc1m_frama_adaptive_breakout_7d_gate1_v1",
        )
        for label in ("FUTURES", "precious_metals", "MGC", "1m", "IBKR"):
            self.assertNotIn(label, wrapper.base.BRANCH_PATH.split(" -> "))

    def test_sparse_positive_exact_5bps_survives_without_density_floor(self) -> None:
        wrapper = load_wrapper()

        self.assertTrue(wrapper.base.cost_survives(2, 0.08))
        self.assertFalse(wrapper.base.cost_survives(0, 0.08))
        self.assertFalse(wrapper.base.cost_survives(2, 0.0))
        self.assertFalse(wrapper.base.cost_survives(2, -0.01))

    def test_downstream_requires_hard_5bps_survivor_not_2bps_only(self) -> None:
        wrapper = load_wrapper()

        self.assertFalse(wrapper.base.hard_gate_downstream_allowed(True, []))
        self.assertTrue(wrapper.base.hard_gate_downstream_allowed(True, ["MGC/frama_dense/1m"]))
        self.assertFalse(wrapper.base.hard_gate_downstream_allowed(False, ["MGC/frama_dense/1m"]))


if __name__ == "__main__":
    unittest.main()
