#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name("run_ibkr_mgc1m_adx_atr_short_fade_7d_gate1_v1.py")


def load_wrapper():
    spec = importlib.util.spec_from_file_location("ibkr_mgc_adx_atr_short_fade_gate1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class IbkrMgcAdxAtrShortFadeGate1IdentityTest(unittest.TestCase):
    def test_branch_path_is_regime_rooted_without_provider_labels(self) -> None:
        wrapper = load_wrapper()

        self.assertEqual(
            wrapper.BRANCH_PATH,
            "TrendReversal -> AdxAtrShortFade -> ibkr_mgc1m_adx_atr_short_fade_7d_gate1_v1",
        )
        for label in ("FUTURES", "precious_metals", "MGC", "1m", "IBKR"):
            self.assertNotIn(label, wrapper.BRANCH_PATH.split(" -> "))


if __name__ == "__main__":
    unittest.main()
