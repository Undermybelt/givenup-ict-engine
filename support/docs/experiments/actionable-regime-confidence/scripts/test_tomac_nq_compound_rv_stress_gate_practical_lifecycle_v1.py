#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name(
    "run_tomac_nq_compound_rv_stress_gate_practical_lifecycle_v1.py"
)
EXPECTED_BRANCH = (
    "US index futures -> NQ -> ETH/full_retained_session -> 1m parent execution + shifted 5m/15m/30m/1h/4h/1d context "
    "-> HtfTrendRegime -> ChopFilter(ER>=0.35,n40) -> MomentumResonance -> CompoundTrendRrrBreadth "
    "-> FixedRrrBracket -> RealizedVolatilityStressGate(30m_abs_ret16_max <= 0.04174409724) "
    "-> PracticalLifecycleContinuation"
)


def load_module():
    spec = importlib.util.spec_from_file_location("nq_compound_rv_lifecycle", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load wrapper: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def practical_command_results() -> list[dict]:
    return [
        {"stage": "provider_data", "name": "01_provider_data", "exit": 0, "timed_out": False},
        {"stage": "pre_bayes", "name": "02_pre_bayes", "exit": 0, "timed_out": False},
        {"stage": "bbn_workflow", "name": "03_bbn_workflow", "exit": 0, "timed_out": False},
        {"stage": "path_ranker", "name": "04_path_ranker", "exit": 0, "timed_out": False},
        {"stage": "execution_tree", "name": "05_execution_tree", "exit": 0, "timed_out": False},
        {"stage": "feedback_update", "name": "06_feedback_update", "exit": 0, "timed_out": False},
        {"stage": "policy_training", "name": "07_policy_training", "exit": 0, "timed_out": False},
    ]


def write_materialization(
    root: Path,
    command_results: list[dict] | None = None,
    market_data_provenance: dict | None = None,
    retained_session_coverage: dict | None = None,
    cost_model: dict | None = None,
    promotion_cost_verified: bool = False,
) -> None:
    payload = {
        "status": "child_gate_simulated_feedback_materialized_fail_closed",
        "factor_id": "nq_compound_trend_rrr_chopfilter_rv_stress_gate_rescore_v1",
        "parent_factor_id": "nq_compound_trend_rrr_chopfilter_v1",
        "branch_path": EXPECTED_BRANCH.replace("PracticalLifecycleContinuation", "SimulatedFeedbackMaterialization"),
        "feedback_rows": 535,
        "best_gate": "30m_abs_ret16_max",
        "best_threshold": 0.04174409724,
        "child_full_trades_per_session": 0.343830334,
        "child_oos_trades_per_session": 0.344,
        "child_full_net5bps_total_ret_pct": 160.467967,
        "child_oos_net5bps_total_ret_pct": 52.662845,
        "session_scope": "ETH/full_retained_session",
        "rth_filter_applied": False,
        "promotion_allowed": False,
        "trade_usable": False,
    }
    if market_data_provenance is not None:
        payload["market_data_provenance"] = market_data_provenance
    if retained_session_coverage is not None:
        payload["retained_session_coverage"] = retained_session_coverage
    if cost_model is not None:
        payload["cost_model"] = cost_model
    payload["promotion_cost_verified"] = promotion_cost_verified
    if command_results is not None:
        payload["command_results"] = command_results
    write_json(root / "checks/terminal_metrics.json", payload)


def explicit_market_data_provenance() -> dict:
    return {
        "status": "pass",
        "source_class": "roll_adjusted_clean_feather",
        "source": "fixture-clean-feather",
        "return_sanity": {
            "status": "pass",
            "extreme_abs_gross_gt_10pct_count": 0,
            "parse_bad_rows": 0,
            "max_abs_gross_return_pct": 2.0,
        },
    }


def explicit_retained_session_coverage() -> dict:
    return {
        "status": "pass",
        "has_non_rth_rows": True,
        "evidence": "fixture retained NQ rows include timestamps outside 09:30-16:00 America/New_York",
    }


def explicit_verified_cost_model() -> dict:
    return {
        "status": "verified",
        "instrument_class": "futures",
        "broker": "IBKR",
        "pricing_plan": "US futures unbundled",
        "exchange": "CME",
        "currency": "USD",
        "unit_convention": "per_contract_per_side",
        "fee_effective_date": "2026-05-30",
        "source_refs": {
            "commission": {
                "url": "https://www.interactivebrokers.com/en/pricing/commissions-futures.php",
                "http_status": 200,
                "rate_verified": True,
            },
            "exchange_fee": {
                "url": "https://www.interactivebrokers.com/en/accounts/fees/futuresFees.php",
                "http_status": 200,
                "rate_verified": True,
            },
        },
    }


def write_full_lifecycle_state(module, root: Path) -> None:
    symbol_dir = root / "state" / module.SYMBOL
    lifecycle = {
        "factor_profitability_lifecycle": {
            "learning_admitted_count": 1,
            "paper_ready_count": 1,
            "deploy_ready_count": 1,
            "live_ready_count": 1,
            "live_trade_usable_count": 1,
            "funded_live_fill_required": False,
            "readiness_contract": module.DEPLOY_READY_READINESS_CONTRACT,
            "promotion_allowed": True,
            "trade_usable": True,
        },
        "learning_admission_status": "admitted",
        "paper_admission_status": "ready",
        "live_trade_status": "ready",
    }
    closed_loop = {
        "path_id": EXPECTED_BRANCH,
        "status": "admitted",
        "ready": True,
        "actionable": True,
        "candidate_status": "execution_ready",
        "promotion_allowed": True,
        "trade_usable": True,
        "update_goal": True,
    }
    write_json(symbol_dir / "workflow_snapshot.json", {"closed_loop_branch_admission": closed_loop})
    write_json(symbol_dir / "execution_candidate.json", {"path_id": EXPECTED_BRANCH, "actionable": True, "candidate_status": "execution_ready"})
    write_json(
        symbol_dir / "execution_tree_trace.json",
        {
            "closed_loop_branch_admission": closed_loop,
            "output": {
                "path_id": EXPECTED_BRANCH,
                "actionable": True,
                "candidate_status": "execution_ready",
                "path_ranker_score_used_by_execution_tree": True,
                "path_ranker_score_visible_to_execution_tree": True,
                "ranker_validation_ready": True,
                "split_reason_lineage": [
                    "path_ranker=Ranker runtime raw_scored_mature=535/30 production_validation=535/30 observation_validation=535/30"
                ],
            },
        },
    )
    write_json(symbol_dir / "policy_training/structural_path_ranking_target_summary.json", lifecycle)


class NqCompoundRvStressPracticalLifecycleTests(unittest.TestCase):
    def test_constants_are_child_gate_identity(self) -> None:
        module = load_module()

        self.assertEqual(module.FACTOR_ID, "nq_compound_trend_rrr_chopfilter_rv_stress_gate_rescore_v1")
        self.assertEqual(module.PARENT_FACTOR_ID, "nq_compound_trend_rrr_chopfilter_v1")
        self.assertEqual(module.BRANCH_PATH, EXPECTED_BRANCH)
        self.assertIn("RV_STRESS", module.SYMBOL)

    def test_main_fails_closed_without_staged_command_results(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            material = tmp_path / "material"
            write_materialization(material)
            write_full_lifecycle_state(module, root)

            rc = module.main(["--root", str(root), "--materialization-root", str(material)])
            metrics = json.loads((root / "checks/terminal_metrics.json").read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertEqual(metrics["status"], "practical_lifecycle_fail_closed")
        self.assertEqual(metrics["command_results"], [])
        self.assertFalse(metrics["all_command_exits_zero"])
        self.assertFalse(metrics["promotion_allowed"])
        self.assertFalse(metrics["trade_usable"])

    def test_write_summary_stays_fail_closed_without_validated_extension_complete(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            material = tmp_path / "material"
            write_materialization(
                material,
                practical_command_results(),
                explicit_market_data_provenance(),
                explicit_retained_session_coverage(),
                explicit_verified_cost_model(),
                promotion_cost_verified=True,
            )
            write_full_lifecycle_state(module, root)

            module.configure_paths(root)
            metrics = module.write_summary(
                module.staged_command_results(material),
                module.market_data_provenance(material),
                material,
            )

        self.assertEqual(metrics["status"], "practical_lifecycle_fail_closed")
        self.assertTrue(metrics["all_command_exits_zero"])
        self.assertEqual(metrics["market_data_provenance"]["status"], "pass")
        self.assertEqual(metrics["retained_session_coverage"]["status"], "pass")
        self.assertTrue(metrics["promotion_cost_verified"])
        self.assertEqual(metrics["cost_model"]["status"], "verified")
        self.assertFalse(metrics["promotion_allowed"])
        self.assertFalse(metrics["trade_usable"])
        self.assertFalse((root / "summaries/same_tree_practical_closure.json").exists())

    def test_market_data_provenance_must_be_explicit_for_closure(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            material = tmp_path / "material"
            write_materialization(material, practical_command_results())
            write_full_lifecycle_state(module, root)

            module.configure_paths(root)
            metrics = module.write_summary(
                module.staged_command_results(material),
                module.market_data_provenance(material),
                material,
            )

        self.assertEqual(metrics["status"], "practical_lifecycle_fail_closed")
        self.assertNotEqual(metrics["market_data_provenance"].get("status"), "pass")
        self.assertFalse(metrics["promotion_allowed"])
        self.assertFalse(metrics["trade_usable"])
        self.assertFalse((root / "summaries/same_tree_practical_closure.json").exists())

    def test_return_sanity_must_be_explicit_for_closure(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            material = tmp_path / "material"
            write_materialization(
                material,
                practical_command_results(),
                {"status": "pass", "source_class": "roll_adjusted_clean_feather"},
            )
            write_full_lifecycle_state(module, root)

            module.configure_paths(root)
            metrics = module.write_summary(
                module.staged_command_results(material),
                module.market_data_provenance(material),
                material,
            )

        self.assertEqual(metrics["status"], "practical_lifecycle_fail_closed")
        self.assertNotEqual(metrics["market_data_provenance"].get("return_sanity", {}).get("status"), "pass")
        self.assertFalse(metrics["promotion_allowed"])
        self.assertFalse(metrics["trade_usable"])
        self.assertFalse((root / "summaries/same_tree_practical_closure.json").exists())

    def test_command_result_stage_validation_requires_all_stages(self) -> None:
        module = load_module()

        partial = practical_command_results()[:-1]
        self.assertFalse(module.command_results_cover_practical_stages(partial))
        self.assertTrue(module.command_results_cover_practical_stages(practical_command_results()))

    def test_market_data_provenance_inherits_child_rescore_readback(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            material = tmp_path / "material"
            child = tmp_path / "child_rescore"
            write_json(
                material / "checks/terminal_metrics.json",
                {
                    "child_rescore_root": str(child),
                    "feedback_jsonl": str(material / "feedback/events.jsonl"),
                    "session_scope": "ETH/full_retained_session",
                    "rth_filter_applied": False,
                },
            )
            write_json(
                child / "checks/terminal_metrics.json",
                {"market_data_provenance": explicit_market_data_provenance()},
            )

            provenance = module.market_data_provenance(material)

        self.assertEqual(provenance["status"], "pass")
        self.assertEqual(provenance["return_sanity"]["status"], "pass")
        self.assertIn("child_rescore", provenance["source_payload"])

    def test_source_packet_supplies_session_coverage_and_cost_model(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            material = tmp_path / "material"
            source_packet_path = tmp_path / "source_packet.json"
            source_packet = {
                "session_scope": "ETH/full_retained_session",
                "rth_filter_applied": False,
                "retained_session_coverage": explicit_retained_session_coverage(),
                "promotion_cost_verified": True,
                "cost_model": explicit_verified_cost_model(),
            }
            write_json(source_packet_path, source_packet)
            write_materialization(material)

            module.configure_paths(root)
            metrics = module.write_summary(
                module.staged_command_results(material),
                module.market_data_provenance(material),
                material,
                source_packet,
                source_packet_path,
            )

        self.assertEqual(metrics["status"], "practical_lifecycle_fail_closed")
        self.assertEqual(metrics["source_cost_coverage_packet"], str(source_packet_path))
        self.assertEqual(metrics["retained_session_coverage"]["status"], "pass")
        self.assertTrue(metrics["retained_session_coverage"]["has_non_rth_rows"])
        self.assertTrue(metrics["promotion_cost_verified"])
        self.assertEqual(metrics["cost_model"]["status"], "verified")
        self.assertFalse(metrics["promotion_allowed"])
        self.assertFalse(metrics["trade_usable"])

    def test_execute_driver_plan_is_json_safe_and_uses_configured_root_data_dir(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            module.configure_paths(root)

            plan = module.build_lifecycle_command_plan(
                strategy_library=tmp_path / "strategy.json",
                data_root=module.resolve_data_root(""),
                feedback_file=tmp_path / "feedback.jsonl",
            )
            payload = {"steps": plan}

            json.dumps(payload)
            analyze_steps = [step for step in plan if step["name"] in {"03_analyze_seed", "16_analyze_after_ranker"}]

        self.assertEqual(len(analyze_steps), 2)
        for step in analyze_steps:
            argv = step["argv"]
            self.assertIn(str(root / "data/provider/normalized"), argv)


if __name__ == "__main__":
    unittest.main()
