#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name(
    "run_tomac_rachev_tail_reward_risk_admission_prep_v1.py"
)


def load_runner():
    spec = importlib.util.spec_from_file_location("rachev_tail_reward_prep", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RachevTailRewardRiskAdmissionPrepTests(unittest.TestCase):
    def test_plan_is_eth_full_session_no_launch_and_independent_timeframes(self) -> None:
        runner = load_runner()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            compact = Path(tmp) / "compact"
            plan = runner.build_plan(root, compact)

        self.assertEqual(plan.factor_family, "rachev_tail_reward_risk_admission_filter")
        self.assertEqual(plan.session_scope, "ETH/full_retained_session")
        self.assertFalse(plan.rth_filter_applied)
        self.assertEqual(plan.target_timeframes, ["5m", "15m", "30m", "1h", "4h", "1d"])
        self.assertEqual(
            [spec.factor_id for spec in plan.strategy_specs],
            [
                "tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_5m_v1",
                "tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_15m_v1",
                "tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_30m_v1",
                "tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_1h_v1",
                "tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_4h_v1",
                "tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_1d_v1",
            ],
        )
        self.assertTrue(plan.coordination_only)
        self.assertTrue(plan.no_provider_fetch)
        self.assertTrue(plan.no_ibkr_historical)
        self.assertTrue(plan.no_autoquant_or_freqtrade_launch)
        self.assertTrue(plan.no_local_backtest_launch)
        self.assertTrue(plan.no_paper_sim_live)
        self.assertTrue(plan.no_downstream_lifecycle)
        self.assertFalse(plan.provider_attempted)
        self.assertFalse(plan.ibkr_attempted)
        self.assertFalse(plan.autoquant_attempted)
        self.assertFalse(plan.local_backtest_attempted)
        self.assertFalse(plan.paper_or_live_attempted)
        self.assertFalse(plan.downstream_lifecycle_attempted)
        self.assertFalse(plan.promotion_allowed)
        self.assertFalse(plan.trade_usable)
        self.assertFalse(plan.update_goal)
        self.assertIsNone(plan.same_tree_practical_closure)
        self.assertIn("RachevExpectedTailGainLoss", plan.branch_path)

    def test_strategy_source_uses_shifted_rachev_state_and_no_future_payoff(self) -> None:
        runner = load_runner()
        spec = runner.build_strategy_specs()[1]

        source = runner.strategy_source(spec)

        self.assertIn("factor_id: tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_15m_v1", source)
        self.assertIn("RachevExpectedTailGainLoss", source)
        self.assertIn("rolling_rachev_ratio", source)
        self.assertIn("upper_tail_gain", source)
        self.assertIn("lower_tail_loss", source)
        self.assertIn("rachev_ratio_raw.shift(1)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)
        self.assertNotIn("future", source.lower())

    def test_main_writes_material_strategy_claim_and_summaries_without_runtime_launch(self) -> None:
        runner = load_runner()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            compact = Path(tmp) / "compact"
            claim = Path(tmp) / "claim.json"
            repo_doc = Path(tmp) / "repo-doc.md"

            code = runner.main(
                [
                    "--root",
                    str(root),
                    "--compact-root",
                    str(compact),
                    "--claim",
                    str(claim),
                    "--repo-doc",
                    str(repo_doc),
                    "--stamp",
                    "20260531T080000+0800",
                ]
            )

            self.assertEqual(code, 0)
            workdoc = root / "workdoc.md"
            summary = json.loads((root / "summaries" / "prep_summary.json").read_text(encoding="utf-8"))
            compact_summary = json.loads((compact / "summaries" / "prep_summary.json").read_text(encoding="utf-8"))
            launch_plan = json.loads((root / "summaries" / "launch_plan.json").read_text(encoding="utf-8"))
            claim_payload = json.loads(claim.read_text(encoding="utf-8"))
            strategy_files = sorted((root / "materials").glob("Tomac*RachevTailRewardRiskAdmission*.py"))

            self.assertTrue(workdoc.exists())
            self.assertTrue(repo_doc.exists())
            self.assertNotIn(str(Path.home()), repo_doc.read_text(encoding="utf-8"))
            self.assertEqual(summary, compact_summary)
            self.assertEqual(len(strategy_files), 6)
            self.assertEqual(summary["status"], "terminalized_training_prep_no_launch")
            self.assertEqual(summary["decision"], "prep_packet_complete_no_launch_runtime_blocked")
            self.assertTrue(summary["coordination_only"])
            self.assertFalse(summary["provider_attempted"])
            self.assertFalse(summary["ibkr_attempted"])
            self.assertFalse(summary["autoquant_attempted"])
            self.assertFalse(summary["local_backtest_attempted"])
            self.assertFalse(summary["paper_or_live_attempted"])
            self.assertFalse(summary["downstream_lifecycle_attempted"])
            self.assertFalse(summary["promotion_allowed"])
            self.assertFalse(summary["trade_usable"])
            self.assertEqual(len(launch_plan["commands_when_clear"]), 6)
            self.assertIn("run_tomac_one.py", launch_plan["commands_when_clear"][0])
            self.assertEqual(claim_payload["status"], "terminalized_training_prep_no_launch")
            self.assertTrue(claim_payload["coordination_only"])
            self.assertIn("No AutoQuant, Freqtrade, or TOMAC runtime launch", claim_payload["non_goals"])
            self.assertFalse(claim_payload["promotion_allowed"])
            self.assertFalse(claim_payload["trade_usable"])


if __name__ == "__main__":
    unittest.main()
