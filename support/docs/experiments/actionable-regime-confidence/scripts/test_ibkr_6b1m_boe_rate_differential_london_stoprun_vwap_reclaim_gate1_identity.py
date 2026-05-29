#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SCRIPT = Path(__file__).with_name(
    "run_ibkr_6b1m_boe_rate_differential_london_stoprun_vwap_reclaim_gate1_v1.py"
)
SPEC = importlib.util.spec_from_file_location("ibkr_6b_boe_stoprun_gate1", SCRIPT)


class Ibkr6bBoeStoprunGate1IdentityTest(unittest.TestCase):
    def load_module(self):
        assert SPEC is not None and SPEC.loader is not None
        if str(SCRIPT.parent) not in sys.path:
            sys.path.insert(0, str(SCRIPT.parent))
        module = importlib.util.module_from_spec(SPEC)
        sys.modules[SPEC.name] = module
        SPEC.loader.exec_module(module)
        return module

    def test_branch_identity_is_6b_eth_full_retained_1m_origin(self) -> None:
        module = self.load_module()

        self.assertEqual(module.FACTOR_ID, "6b_eth_boe_rate_differential_london_stoprun_vwap_reclaim_v1")
        self.assertEqual(module.CONTRACT.symbol, "GBP")
        self.assertEqual(module.CONTRACT.human_root, "6B")
        self.assertEqual(module.CONTRACT.product, "fx_futures")
        self.assertEqual(module.CONTRACT.exchange, "CME")
        self.assertEqual(module.CONTRACT.multiplier, "62500")
        self.assertEqual(module.SESSION_SCOPE, "ETH/full_retained_session")
        self.assertFalse(module.RTH_FILTER_APPLIED)
        self.assertEqual([spec.timeframe for spec in module.SPECS], ["1m", "5m", "15m", "30m", "1h", "4h", "1d"])
        self.assertEqual(module.SPECS[0].role, "exact_training_origin")
        self.assertIn("BoE_FedRateDifferentialTransition", module.BRANCH_PATH)
        self.assertIn("LondonNYLiquidityStopRun", module.BRANCH_PATH)
        self.assertIn("AtrRiskManagedMtfContinuation", module.BRANCH_PATH)

    def test_fetch_args_use_ibkr_gbp_futures_without_rth_filter(self) -> None:
        module = self.load_module()

        args = [str(part) for part in module.fetch_args(module.SPECS[0], Path("/tmp/out.csv"), 911)]

        self.assertIn("--symbol", args)
        self.assertEqual(args[args.index("--symbol") + 1], "GBP")
        self.assertEqual(args[args.index("--sec-type") + 1], "FUT")
        self.assertEqual(args[args.index("--exchange") + 1], "CME")
        self.assertEqual(args[args.index("--currency") + 1], "USD")
        self.assertEqual(args[args.index("--last-trade-date") + 1], "202606")
        self.assertEqual(args[args.index("--multiplier") + 1], "62500")
        self.assertNotIn("--rth", args)

    def test_material_payload_carries_session_scope_and_6b_cost_model(self) -> None:
        module = self.load_module()

        material_path, material = module.build_material_payload(
            spec=module.SPECS[0],
            variant="balanced",
            strategy_path=Path("/tmp/Ibkr6bBoeRateDifferentialStoprunBalanced1MinV1.py"),
            normalized_data_path=Path("/tmp/ibkr_gbp_202606_1m_7d.csv"),
            strategy_class_name="Ibkr6bBoeRateDifferentialStoprunBalanced1MinV1",
        )

        self.assertEqual(
            material_path.name,
            "ibkr_6b_boe_rate_differential_london_stoprun_vwap_reclaim_balanced_1m_v1.material.json",
        )
        profile = material["consumer_evidence_profile"]
        self.assertEqual(profile["branch_path"], module.BRANCH_PATH)
        self.assertEqual(profile["root_symbol"], "6B")
        self.assertEqual(profile["broker_side_symbol"], "GBP")
        self.assertEqual(profile["session_scope"], "ETH/full_retained_session")
        self.assertFalse(profile["rth_filter_applied"])
        self.assertEqual(profile["context_timeframes"], ["5m", "15m", "30m", "1h", "4h", "1d"])
        self.assertEqual(profile["cost_model_status"], "verified_ibkr_broker_side_current_schedule_under_assumptions")
        self.assertEqual(profile["all_in_per_contract_per_side_usd"], 2.47)
        self.assertEqual(profile["all_in_round_turn_per_contract_usd"], 4.94)
        self.assertEqual(profile["tick_value_usd"], 6.25)
        self.assertFalse(profile["promotion_allowed"])
        self.assertFalse(profile["trade_usable"])
        self.assertFalse(profile["update_goal"])

    def test_strategy_source_contains_policy_stoprun_vwap_reclaim_contract(self) -> None:
        module = self.load_module()

        source = module.strategy_source(
            "Ibkr6bBoeRateDifferentialStoprunBalanced1MinV1",
            "1m",
            "balanced",
            module.VARIANTS["balanced"],
        )

        self.assertIn("london_ny_window", source)
        self.assertIn("asia_high", source)
        self.assertIn("asia_low", source)
        self.assertIn("stoprun_reclaim_long", source)
        self.assertIn("stoprun_reclaim_short", source)
        self.assertIn("policy_shock_proxy", source)
        self.assertIn("session_vwap", source)
        self.assertIn("htf_slope_proxy", source)

    def test_collision_guard_blocks_foreign_claims_and_allows_own_root(self) -> None:
        module = self.load_module()
        own = Path("/tmp/own-6b-root")
        foreign = Path("/tmp/foreign-root")
        audit = {
            "claims": [
                {"status": "active", "run_root": str(own), "scope": "own"},
                {"status": "active", "run_root": str(foreign), "scope": "foreign"},
                {"status": "active", "run_root": "/tmp/coord", "coordination_only": True},
            ],
            "live_factor_processes": [
                {"pid": 123, "run_root": str(foreign), "command_excerpt": "fetch_external.py ibkr-historical"}
            ],
        }

        guard = module.claim_collision_blockers(audit, allowed_roots={own})

        self.assertFalse(guard["pass"])
        self.assertEqual(len(guard["foreign_active_claims"]), 1)
        self.assertEqual(len(guard["foreign_live_processes"]), 1)

    def test_terminal_metrics_keep_practical_flags_false_without_exact_real_cost_survivor(self) -> None:
        module = self.load_module()

        metrics = module.build_terminal_metrics(
            commands=[{"name": "rank", "exit": 0}],
            rank_rows=[{"dummy": 1}],
            provider_rows=[{"symbol": "GBP", "timeframe": "1m", "rows": 1000}],
            branch_paths=[module.BRANCH_PATH],
            cost_rows=[
                {
                    "label": "6B/balanced/1m",
                    "trade_count": 8,
                    "real_cost_total_profit_pct": -0.12,
                    "survives_real_cost": False,
                }
            ],
        )

        self.assertEqual(metrics["session_scope"], "ETH/full_retained_session")
        self.assertFalse(metrics["rth_filter_applied"])
        self.assertEqual(metrics["exact_1m_real_cost_survivors"], [])
        self.assertFalse(metrics["downstream_allowed"])
        self.assertFalse(metrics["promotion_allowed"])
        self.assertFalse(metrics["trade_usable"])
        self.assertFalse(metrics["update_goal"])

    def test_terminal_metrics_classifies_gateway_zero_rows_as_provider_blocked(self) -> None:
        module = self.load_module()

        with TemporaryDirectory() as tmp:
            err = Path(tmp) / "fetch.err"
            err.write_text("ibkr-historical: no reachable local IBKR API port on 127.0.0.1\n", encoding="utf-8")
            metrics = module.build_terminal_metrics(
                commands=[{"name": "01_ibkr_fetch_6b_1m_7d", "exit": 1, "stderr_path": str(err)}],
                rank_rows=[],
                provider_rows=[{"symbol": "GBP", "timeframe": "1m", "rows": 0, "exit": 1}],
                branch_paths=[],
                cost_rows=[],
            )

        self.assertEqual(metrics["decision"], "provider_blocked_ibkr_gateway_unreachable")
        self.assertTrue(metrics["provider_blocked"])
        self.assertEqual(metrics["provider_blocker"], "ibkr_gateway_unreachable")
        self.assertFalse(metrics["downstream_allowed"])
        self.assertFalse(metrics["promotion_allowed"])
        self.assertFalse(metrics["trade_usable"])

    def test_write_terminal_metrics_outputs_json_and_markdown(self) -> None:
        module = self.load_module()

        with TemporaryDirectory() as tmp:
            module.ROOT = Path(tmp)
            module.write_terminal_metrics({"decision": "unit_test_decision"})

            data = json.loads((Path(tmp) / "checks/terminal_metrics.json").read_text())
            self.assertEqual(data["factor_id"], module.FACTOR_ID)
            self.assertEqual(data["session_scope"], "ETH/full_retained_session")
            self.assertFalse(data["promotion_allowed"])
            self.assertTrue((Path(tmp) / "summaries/terminal_decision_summary.md").exists())


if __name__ == "__main__":
    unittest.main()
