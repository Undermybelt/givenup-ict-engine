#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("run_ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1.py")


def load_module():
    spec = importlib.util.spec_from_file_location("ibkr_qqq_micro_trend_density", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class IbkrQqqMicroTrendDensityTests(unittest.TestCase):
    def test_run_root_override_keeps_generated_state_out_of_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {"ICT_ENGINE_RUN_ROOT_OVERRIDE": tmpdir}, clear=False):
                module = load_module()

            self.assertEqual(module.ROOT, Path(tmpdir))
            self.assertNotIn("support/docs/experiments", str(module.ROOT))

    def test_branch_identity_contains_full_regime_root(self) -> None:
        module = load_module()

        self.assertEqual(module.PARTS[:4], ["US", "equity_etf", "QQQ", "1m"])
        self.assertEqual(module.PARTS[4], "Trend")
        self.assertEqual(module.PARTS[5], "SessionLiquidity")
        self.assertEqual(module.PARTS[-1], module.FACTOR_ID)

    def test_zero_provider_rows_with_fetch_failure_is_not_gate1_factor_drop(self) -> None:
        module = load_module()

        provider_rows = [
            {"timeframe": "1m", "rows": 0, "exit": 1},
            {"timeframe": "5m", "rows": 0, "exit": 1},
        ]

        decision, status = module.classify_decision(provider_rows, downstream_allowed=False)

        self.assertEqual(decision, "provider_acquisition_blocked_no_gate1_verdict")
        self.assertEqual(status, "blocked_no_provider_rows_fetch_failed")

    def test_zero_provider_rows_with_successful_empty_fetch_still_blocks_gate1(self) -> None:
        module = load_module()

        decision, status = module.classify_decision([{"rows": 0, "exit": 0}], downstream_allowed=False)

        self.assertEqual(decision, "provider_acquisition_blocked_no_gate1_verdict")
        self.assertEqual(status, "blocked_no_provider_rows")

    def test_provider_rows_allow_factor_verdict_classification(self) -> None:
        module = load_module()

        provider_rows = [{"timeframe": "1m", "rows": 25, "exit": 0}]

        passed, passed_status = module.classify_decision(provider_rows, downstream_allowed=True)
        failed, failed_status = module.classify_decision(provider_rows, downstream_allowed=False)

        self.assertEqual(passed, "gate1_ibkr_native_candidate_downstream_allowed")
        self.assertEqual(failed, "drop_gate1_no_ibkr_cost_density")
        self.assertEqual(passed_status, "nonzero_rows_acquired")
        self.assertEqual(failed_status, "nonzero_rows_acquired")


if __name__ == "__main__":
    unittest.main()
