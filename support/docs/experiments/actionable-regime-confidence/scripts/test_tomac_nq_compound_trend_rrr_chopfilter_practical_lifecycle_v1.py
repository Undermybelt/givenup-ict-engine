#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name(
    "run_tomac_nq_compound_trend_rrr_chopfilter_practical_lifecycle_v1.py"
)
EXPECTED_BRANCH = (
    "US index futures -> NQ -> 1m -> HtfTrendRegime -> ChopFilter(ER>=0.35,n40) "
    "-> MomentumResonance -> {ThrustEntry | DonchianBreakout(60/120/240) | PullbackReclaim} "
    "-> FixedRrrBracket -> PracticalLifecycleContinuation"
)


def practical_command_results() -> list[dict]:
    return [
        {"stage": "provider_data", "name": "01_provider_data_fetch", "exit": 0, "timed_out": False},
        {"stage": "pre_bayes", "name": "05_pre_bayes_status", "exit": 0, "timed_out": False},
        {"stage": "bbn_workflow", "name": "04_workflow_status_bbn", "exit": 0, "timed_out": False},
        {"stage": "path_ranker", "name": "11_train_catboost_path_ranker", "exit": 0, "timed_out": False},
        {"stage": "execution_tree", "name": "16_analyze_after_ranker_execution_tree", "exit": 0, "timed_out": False},
        {"stage": "feedback_update", "name": "08_ingest_simulated_trade_feedback", "exit": 0, "timed_out": False},
        {"stage": "policy_training", "name": "19_policy_training_status", "exit": 0, "timed_out": False},
    ]


def load_module():
    spec = importlib.util.spec_from_file_location("nq_compound_practical_lifecycle", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load wrapper: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_full_lifecycle_state(module, root: Path) -> None:
    state = root / "state"
    symbol_dir = state / module.SYMBOL
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
        "live_trade_status": "ready",
        "promotion_allowed": True,
        "trade_usable": True,
        "update_goal": True,
    }
    write_json(symbol_dir / "workflow_snapshot.json", {"closed_loop_branch_admission": closed_loop})
    write_json(
        symbol_dir / "execution_candidate.json",
        {
            "path_id": EXPECTED_BRANCH,
            "actionable": True,
            "candidate_status": "execution_ready",
            "execution_readiness": 0.71,
        },
    )
    write_json(
        symbol_dir / "execution_tree_trace.json",
        {
            "closed_loop_branch_admission": closed_loop,
            "output": {
                "path_id": EXPECTED_BRANCH,
                "gate_status": "ready",
                "branch": "fill_viable",
                "actionable": True,
                "candidate_status": "execution_ready",
                "execution_readiness": 0.71,
                "path_ranker_score_visible_to_execution_tree": True,
                "path_ranker_score_used_by_execution_tree": True,
                "ranker_validation_ready": True,
                "split_reason_lineage": [
                    "path_ranker=Ranker runtime raw_scored_mature=220/30 production_validation=220/30 observation_validation=32/30"
                ],
            },
        },
    )
    write_json(symbol_dir / "policy_training/structural_path_ranking_target_summary.json", lifecycle)


class NqCompoundTrendRrrChopfilterPracticalLifecycleTests(unittest.TestCase):
    def test_constants_keep_same_tree_identity(self) -> None:
        module = load_module()

        self.assertEqual(module.FACTOR_ID, "nq_compound_trend_rrr_chopfilter_v1")
        self.assertEqual(module.BRANCH_PATH, EXPECTED_BRANCH)
        self.assertIn("NQ_COMPOUND", module.SYMBOL)

    def test_write_summary_does_not_emit_closure_without_full_lifecycle(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            state = root / "state"
            symbol_dir = state / module.SYMBOL
            write_json(
                symbol_dir / "workflow_snapshot.json",
                {
                    "closed_loop_branch_admission": {
                        "path_id": EXPECTED_BRANCH,
                        "actionable": True,
                        "candidate_status": "trade_candidate",
                    }
                },
            )
            write_json(
                symbol_dir / "execution_candidate.json",
                {
                    "path_id": EXPECTED_BRANCH,
                    "actionable": True,
                    "candidate_status": "trade_candidate",
                    "execution_readiness": 0.71,
                },
            )
            write_json(
                symbol_dir / "execution_tree_trace.json",
                {
                    "output": {
                        "path_id": EXPECTED_BRANCH,
                        "gate_status": "ready",
                        "branch": "fill_viable",
                        "actionable": True,
                        "candidate_status": "trade_candidate",
                        "execution_readiness": 0.71,
                        "path_ranker_score_visible_to_execution_tree": True,
                        "path_ranker_score_used_by_execution_tree": True,
                        "ranker_validation_ready": True,
                        "split_reason_lineage": [
                            "path_ranker=Ranker runtime raw_scored_mature=220/30 production_validation=220/30 observation_validation=0/30"
                        ],
                    }
                },
            )
            write_json(symbol_dir / "policy_training/structural_path_ranking_target_summary.json", {"rows": 220})

            module.configure_paths(root)
            module.write_summary(
                command_results=practical_command_results(),
                data_summary=module.market_data_provenance(),
                trade_summary={"rows": 220, "wins": 122, "losses": 98, "breakevens": 0},
            )

            self.assertTrue((root / "checks/terminal_metrics.json").exists())
            self.assertFalse((root / "summaries/same_tree_practical_closure.json").exists())

    def test_write_summary_emits_closure_only_when_full_chain_present(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            write_full_lifecycle_state(module, root)

            module.configure_paths(root)
            module.write_summary(
                command_results=practical_command_results(),
                data_summary=module.market_data_provenance(),
                trade_summary={"rows": 220, "wins": 122, "losses": 98, "breakevens": 0},
            )

            packet_path = root / "summaries/same_tree_practical_closure.json"
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            metrics = json.loads((root / "checks/terminal_metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(packet["status"], "pass")
            self.assertTrue(packet["promotion_allowed"])
            self.assertTrue(packet["trade_usable"])
            self.assertTrue(packet["deploy_ready"])
            self.assertFalse(packet["funded_live_fill_required"])
            self.assertEqual(packet["readiness_contract"], module.DEPLOY_READY_READINESS_CONTRACT)
            self.assertTrue(metrics["deploy_ready"])
            self.assertFalse(metrics["funded_live_fill_required"])
            self.assertEqual(metrics["readiness_contract"], module.DEPLOY_READY_READINESS_CONTRACT)

    def test_main_uses_full_staged_command_results_from_source_metrics(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            source = tmp_path / "source"
            source_metrics_path = source / "checks/terminal_metrics.json"
            write_full_lifecycle_state(module, root)
            write_json(
                source_metrics_path,
                {
                    "market_data_provenance": module.market_data_provenance(),
                    "command_results": practical_command_results(),
                },
            )

            original_source = module.SOURCE
            module.SOURCE = source
            try:
                rc = module.main(["--root", str(root)])
            finally:
                module.SOURCE = original_source

            metrics = json.loads((root / "checks/terminal_metrics.json").read_text(encoding="utf-8"))
            packet = json.loads(
                (root / "summaries/same_tree_practical_closure.json").read_text(encoding="utf-8")
            )
            self.assertEqual(rc, 0)
            self.assertEqual(
                {row["stage"] for row in metrics["command_results"]},
                {
                    "provider_data",
                    "pre_bayes",
                    "bbn_workflow",
                    "path_ranker",
                    "execution_tree",
                    "feedback_update",
                    "policy_training",
                },
            )
            self.assertEqual(packet["status"], "pass")

    def test_main_fails_closed_without_staged_command_results_even_when_lifecycle_flags_true(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            source = tmp_path / "source"
            write_full_lifecycle_state(module, root)
            write_json(
                source / "checks/terminal_metrics.json",
                {"market_data_provenance": module.market_data_provenance()},
            )

            original_source = module.SOURCE
            module.SOURCE = source
            try:
                rc = module.main(["--root", str(root)])
            finally:
                module.SOURCE = original_source

            metrics = json.loads((root / "checks/terminal_metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(rc, 2)
            self.assertEqual(metrics["command_results"], [])
            self.assertFalse(metrics["all_command_exits_zero"])
            self.assertFalse((root / "summaries/same_tree_practical_closure.json").exists())

    def test_write_summary_requires_explicit_non_timeout_command_proof(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            write_full_lifecycle_state(module, root)
            command_results = [
                {key: value for key, value in row.items() if key != "timed_out"}
                for row in practical_command_results()
            ]

            module.configure_paths(root)
            module.write_summary(
                command_results=command_results,
                data_summary=module.market_data_provenance(),
                trade_summary={"rows": 220, "wins": 122, "losses": 98, "breakevens": 0},
            )

            metrics = json.loads((root / "checks/terminal_metrics.json").read_text(encoding="utf-8"))
            self.assertFalse(metrics["all_command_exits_zero"])
            self.assertFalse((root / "summaries/same_tree_practical_closure.json").exists())


if __name__ == "__main__":
    unittest.main()
