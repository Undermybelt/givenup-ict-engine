#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name(
    "run_tomac_nq_compound_trend_rrr_chopfilter_practical_lifecycle_v1.py"
)
EXPECTED_BRANCH = (
    "US index futures -> NQ -> 1m -> HtfTrendRegime -> ChopFilter(ER>=0.35,n40) "
    "-> MomentumResonance -> {ThrustEntry | DonchianBreakout(60/120/240) | PullbackReclaim} "
    "-> FixedRrrBracket -> PracticalLifecycleContinuation"
)
ACCEPTED_FEEDBACK_SOURCE = "auto_quant_real_trades:paper_execution_feedback:nq_compound_fixture"


def practical_command_results() -> list[dict]:
    return [
        {"stage": "provider_data", "name": "01_provider_data_fetch", "exit": 0, "timed_out": False},
        {"stage": "pre_bayes", "name": "05_pre_bayes_status", "exit": 0, "timed_out": False},
        {"stage": "bbn_workflow", "name": "04_workflow_status_bbn", "exit": 0, "timed_out": False},
        {"stage": "path_ranker", "name": "11_train_catboost_path_ranker", "exit": 0, "timed_out": False},
        {"stage": "execution_tree", "name": "16_analyze_after_ranker_execution_tree", "exit": 0, "timed_out": False},
        {"stage": "feedback_update", "name": "08_ingest_paper_execution_feedback", "exit": 0, "timed_out": False},
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


def write_closure_evidence(module, path: Path) -> None:
    write_json(
        path,
        {
            "session_scope": "ETH/full_retained_session",
            "rth_filter_applied": False,
            "retained_session_coverage": {
                "status": "pass",
                "has_non_rth_rows": True,
                "evidence": "fixture retained tradable-session rows outside RTH",
            },
            "promotion_cost_verified": True,
            "cost_model": {
                "status": "pass",
                "instrument_class": "futures",
                "broker": "IBKR",
                "pricing_plan": "fixed_or_tiered_verified",
                "venue_routing": "exchange_verified",
                "currency": "USD",
                "unit_convention": "per_contract_round_turn",
                "fee_effective_date": "2026-05-30",
                "official_source_refs": [
                    {
                        "url": "https://www.interactivebrokers.com/en/pricing/commissions-futures.php",
                        "same_turn_readback": "official_source_http_200_rate_verified",
                    }
                ],
            },
        },
    )


def accepted_trade_summary() -> dict:
    return {
        "source": ACCEPTED_FEEDBACK_SOURCE,
        "feedback_source": ACCEPTED_FEEDBACK_SOURCE,
        "rows": 220,
        "accepted_rows": 220,
        "broker_fill_evidence_rows": 220,
        "broker_realized_rows": 220,
        "broker_fill_evidence": True,
        "broker_realized": True,
        "wins": 122,
        "losses": 98,
        "breakevens": 0,
    }


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
                closure_evidence=module.closure_evidence_fields(root / "materials/closure_evidence.json"),
            )

            self.assertTrue((root / "checks/terminal_metrics.json").exists())
            self.assertFalse((root / "summaries/same_tree_practical_closure.json").exists())

    def test_write_summary_emits_closure_only_when_full_chain_present(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            write_full_lifecycle_state(module, root)
            evidence = root / "materials/closure_evidence.json"
            write_closure_evidence(module, evidence)

            module.configure_paths(root)
            module.write_summary(
                command_results=practical_command_results(),
                data_summary=module.market_data_provenance(),
                trade_summary=accepted_trade_summary(),
                closure_evidence=module.closure_evidence_fields(evidence),
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

    def test_command_plan_preserves_accepted_paper_execution_feedback_source(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            feedback = tmp_path / "paper_feedback.jsonl"
            feedback.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "symbol": module.SYMBOL,
                        "trade_id": "paper-fill-0001",
                        "source": ACCEPTED_FEEDBACK_SOURCE,
                        "broker_realized": True,
                        "broker_fill_evidence": True,
                        "pnl": 1.25,
                        "realized_outcome": "win",
                        "regime_profit_branch_path": module.BRANCH_PATH,
                        "structural_feedback": {
                            "path_id": module.BRANCH_PATH,
                            "followed_path": True,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            module.configure_paths(root)
            plan = module.build_lifecycle_command_plan(
                strategy_library=tmp_path / "strategy_library.json",
                data_root=root / "data/provider/normalized",
                feedback_file=feedback,
            )
            feedback_step = next(step for step in plan if step["name"] == "08_feedback_update")
            argv = [str(item) for item in feedback_step["argv"]]

        self.assertEqual(argv[argv.index("--source") + 1], ACCEPTED_FEEDBACK_SOURCE)

    def test_command_plan_rejects_mixed_feedback_file_source_as_simulated(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            feedback = tmp_path / "mixed_feedback.jsonl"
            feedback.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "schema_version": "1.0",
                                "symbol": module.SYMBOL,
                                "trade_id": "paper-fill-0001",
                                "source": ACCEPTED_FEEDBACK_SOURCE,
                                "broker_realized": True,
                                "broker_fill_evidence": True,
                                "pnl": 1.25,
                                "realized_outcome": "win",
                            }
                        ),
                        json.dumps(
                            {
                                "schema_version": "1.0",
                                "symbol": module.SYMBOL,
                                "trade_id": "sim-row-0002",
                                "source": "retained_real_event_label_simulation",
                                "broker_realized": False,
                                "broker_fill_evidence": False,
                                "pnl": -0.75,
                                "realized_outcome": "loss",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            module.configure_paths(root)
            plan = module.build_lifecycle_command_plan(
                strategy_library=tmp_path / "strategy_library.json",
                data_root=root / "data/provider/normalized",
                feedback_file=feedback,
            )
            feedback_step = next(step for step in plan if step["name"] == "08_feedback_update")
            argv = [str(item) for item in feedback_step["argv"]]

        self.assertEqual(argv[argv.index("--source") + 1], module.TRADE_FEEDBACK_SOURCE)

    def test_main_uses_full_staged_command_results_from_source_metrics(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            source = tmp_path / "source"
            evidence = root / "materials/closure_evidence.json"
            source_metrics_path = source / "checks/terminal_metrics.json"
            write_full_lifecycle_state(module, root)
            write_closure_evidence(module, evidence)
            write_json(
                source_metrics_path,
                {
                    "market_data_provenance": module.market_data_provenance(),
                    "command_results": practical_command_results(),
                    "trade_summary": accepted_trade_summary(),
                },
            )

            original_source = module.SOURCE
            module.SOURCE = source
            try:
                rc = module.main(["--root", str(root), "--closure-evidence", str(evidence)])
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

    def test_main_keeps_closure_fail_closed_when_source_metrics_lack_accepted_feedback_source(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            source = tmp_path / "source"
            evidence = root / "materials/closure_evidence.json"
            write_full_lifecycle_state(module, root)
            write_closure_evidence(module, evidence)
            write_json(
                source / "checks/terminal_metrics.json",
                {
                    "market_data_provenance": module.market_data_provenance(),
                    "command_results": practical_command_results(),
                    "trade_summary": {"rows": 220, "wins": 122, "losses": 98},
                },
            )

            original_source = module.SOURCE
            module.SOURCE = source
            try:
                rc = module.main(["--root", str(root), "--closure-evidence", str(evidence)])
            finally:
                module.SOURCE = original_source

        self.assertEqual(rc, 2)
        self.assertFalse((root / "summaries/same_tree_practical_closure.json").exists())

    def test_main_resolves_default_paths_after_root_argument(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            write_full_lifecycle_state(module, root)
            plan = [{"stage": "provider_data", "name": "01_provider", "argv": ["provider"], "timeout": 1}]

            with patch.object(module, "prepare_local_data") as prepare_data, patch.object(
                module, "build_lifecycle_command_plan", return_value=plan
            ) as build_plan, patch.object(
                module,
                "run_lifecycle_driver",
                return_value=[{"stage": "provider_data", "name": "01_provider", "exit": 1, "timed_out": False}],
            ):
                module.main(["--root", str(root), "--execute-driver"])

        prepare_data.assert_called_once_with(root / "data/provider/normalized")
        _, kwargs = build_plan.call_args
        self.assertEqual(
            kwargs["strategy_library"],
            root / "materials/tomac_nq_compound_trend_rrr_chopfilter_strategy_library.json",
        )
        self.assertEqual(kwargs["data_root"], root / "data/provider/normalized")
        self.assertEqual(
            kwargs["feedback_file"],
            root / "feedback/tomac_nq_compound_trend_rrr_chopfilter_simulated_feedback.jsonl",
        )

    def test_explicit_data_root_skips_local_data_preparation(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            data_root = tmp_path / "explicit-data"
            write_full_lifecycle_state(module, root)
            plan = [{"stage": "provider_data", "name": "01_provider", "argv": ["provider"], "timeout": 1}]

            with patch.object(module, "prepare_local_data") as prepare_data, patch.object(
                module, "build_lifecycle_command_plan", return_value=plan
            ) as build_plan, patch.object(
                module,
                "run_lifecycle_driver",
                return_value=[{"stage": "provider_data", "name": "01_provider", "exit": 1, "timed_out": False}],
            ):
                module.main(["--root", str(root), "--data-root", str(data_root), "--execute-driver"])

        prepare_data.assert_not_called()
        _, kwargs = build_plan.call_args
        self.assertEqual(kwargs["data_root"], data_root)

    def test_execute_driver_prepares_explicit_run_root_data_root_when_cleaned_files_missing(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            data_root = root / "data/provider/normalized"
            write_full_lifecycle_state(module, root)
            plan = [{"stage": "provider_data", "name": "01_provider", "argv": ["provider"], "timeout": 1}]

            with patch.object(module, "prepare_local_data") as prepare_data, patch.object(
                module, "build_lifecycle_command_plan", return_value=plan
            ) as build_plan, patch.object(
                module,
                "run_lifecycle_driver",
                return_value=[{"stage": "provider_data", "name": "01_provider", "exit": 1, "timed_out": False}],
            ):
                module.main(["--root", str(root), "--data-root", str(data_root), "--execute-driver"])

        prepare_data.assert_called_once_with(data_root)
        _, kwargs = build_plan.call_args
        self.assertEqual(kwargs["data_root"], data_root)

    def test_reset_prior_init_state_removes_only_current_symbol_prior_artifacts(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            module.configure_paths(root)
            current = root / "state" / module.SYMBOL
            sibling = root / "state/auto-quant/OTHER_SYMBOL"
            write_json(current / "bbn_network.json", {"prior": True})
            write_json(current / "auto_quant_prior_init_history.json", {"history": True})
            write_json(current / "auto_quant_prior_init_old.json", {"artifact": True})
            write_json(current / "auto_quant_strategy_library.json", {"keep": True})
            write_json(
                current / "artifact_ledger.json",
                [
                    {
                        "artifact_kind": "auto_quant_prior_init_applied",
                        "artifact_id": "prior-old",
                        "status": "applied",
                        "decision_hint": "applied",
                    },
                    {
                        "artifact_kind": "auto_quant_strategy_library_validated",
                        "artifact_id": "library-current",
                        "status": "ready_for_prior_init",
                    },
                ],
            )
            write_json(sibling / "bbn_network.json", {"keep": True})

            removed = module.reset_prior_init_state()
            ledger = json.loads((current / "artifact_ledger.json").read_text(encoding="utf-8"))

            self.assertEqual(len(removed), 3)
            self.assertFalse((current / "bbn_network.json").exists())
            self.assertFalse((current / "auto_quant_prior_init_history.json").exists())
            self.assertFalse((current / "auto_quant_prior_init_old.json").exists())
            self.assertTrue((current / "auto_quant_strategy_library.json").exists())
            self.assertEqual(ledger[0]["status"], "rolled_back_before_lifecycle_rerun")
            self.assertEqual(ledger[1]["status"], "ready_for_prior_init")
            self.assertTrue((sibling / "bbn_network.json").exists())

    def test_reset_prior_init_state_removes_current_symbol_auto_quant_prior_artifacts(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            module.configure_paths(root)
            current = root / "state/auto-quant" / module.SYMBOL
            sibling = root / "state/auto-quant/OTHER_SYMBOL"
            write_json(current / "bbn_network.json", {"prior": True})
            write_json(current / "auto_quant_prior_init_history.json", {"history": True})
            write_json(current / "auto_quant_prior_init_old.json", {"artifact": True})
            write_json(current / "auto_quant_strategy_library.json", {"keep": True})
            write_json(
                current / "artifact_ledger.json",
                [
                    {
                        "artifact_kind": "auto_quant_prior_init_applied",
                        "artifact_id": "prior-old",
                        "status": "applied",
                        "decision_hint": "applied",
                    },
                    {
                        "artifact_kind": "auto_quant_strategy_library_validated",
                        "artifact_id": "library-current",
                        "status": "ready_for_prior_init",
                    },
                ],
            )
            write_json(sibling / "bbn_network.json", {"keep": True})

            removed = module.reset_prior_init_state()
            ledger = json.loads((current / "artifact_ledger.json").read_text(encoding="utf-8"))

            self.assertEqual(len(removed), 3)
            self.assertFalse((current / "bbn_network.json").exists())
            self.assertFalse((current / "auto_quant_prior_init_history.json").exists())
            self.assertFalse((current / "auto_quant_prior_init_old.json").exists())
            self.assertTrue((current / "auto_quant_strategy_library.json").exists())
            self.assertEqual(ledger[0]["status"], "rolled_back_before_lifecycle_rerun")
            self.assertEqual(ledger[1]["status"], "ready_for_prior_init")
            self.assertTrue((sibling / "bbn_network.json").exists())

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
                trade_summary=accepted_trade_summary(),
            )

            metrics = json.loads((root / "checks/terminal_metrics.json").read_text(encoding="utf-8"))
            self.assertFalse(metrics["all_command_exits_zero"])
            self.assertFalse((root / "summaries/same_tree_practical_closure.json").exists())

    def test_lifecycle_command_plan_covers_required_same_tree_stages(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            module.configure_paths(root)
            plan = module.build_lifecycle_command_plan(
                strategy_library=root / "materials/strategy_library.json",
                data_root=root / "data/provider/normalized",
                feedback_file=root / "feedback/simulated_feedback.jsonl",
            )

        stages = {step["stage"] for step in plan}
        names = {step["name"] for step in plan}
        self.assertTrue(set(module.REQUIRED_COMMAND_RESULT_STAGES).issubset(stages))
        self.assertIn("01_auto_quant_results_import", names)
        self.assertIn("08_feedback_update", names)
        self.assertTrue(any(name.endswith("policy_after_ranker") for name in names))

    def test_lifecycle_driver_stops_after_first_failed_stage(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            module.configure_paths(root)
            plan = [
                {"stage": "provider_data", "name": "01_provider", "argv": ["ok"], "timeout": 1},
                {"stage": "pre_bayes", "name": "02_prior", "argv": ["fail"], "timeout": 1},
                {"stage": "bbn_workflow", "name": "03_workflow", "argv": ["skip"], "timeout": 1},
            ]

            def fake_run_stage(stage: str, name: str, argv: list[object], timeout: int = 300) -> dict:
                return {"stage": stage, "name": name, "exit": 1 if name == "02_prior" else 0, "timed_out": False}

            with patch.object(module, "run_stage", side_effect=fake_run_stage):
                results = module.run_lifecycle_driver(plan)

        self.assertEqual([row["name"] for row in results], ["01_provider", "02_prior"])
        self.assertEqual(results[-1]["stage"], "pre_bayes")
        self.assertEqual(results[-1]["exit"], 1)

    def test_lifecycle_driver_reads_register_model_family_from_trainer_artifact(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            module.configure_paths(root)
            write_json(
                root / "path_ranker_model/trainer_artifact.json",
                {"model_family": "catboost", "trained_rows": 4, "calibration_rows": 4},
            )
            plan = [
                {
                    "stage": "path_ranker",
                    "name": "14_register_trainer",
                    "argv": [
                        "ict-engine",
                        "register-structural-path-ranking-trainer-artifact",
                        "--artifact-uri",
                        root / "path_ranker_model/trainer_artifact.json",
                        "--model-family",
                        "weighted_feature_sum_v1",
                        "--trained-rows",
                        "1",
                        "--calibration-rows",
                        "0",
                    ],
                    "timeout": 1,
                }
            ]

            seen_argv: list[str] = []

            def fake_run_stage(stage: str, name: str, argv: list[object], timeout: int = 300) -> dict:
                seen_argv.extend(str(item) for item in argv)
                return {"stage": stage, "name": name, "exit": 0, "timed_out": False}

            with patch.object(module, "run_stage", side_effect=fake_run_stage):
                results = module.run_lifecycle_driver(plan)

        self.assertEqual(results[-1]["exit"], 0)
        self.assertEqual(seen_argv[seen_argv.index("--model-family") + 1], "catboost")
        self.assertEqual(seen_argv[seen_argv.index("--trained-rows") + 1], "4")
        self.assertEqual(seen_argv[seen_argv.index("--calibration-rows") + 1], "4")

    def test_execute_driver_writes_serializable_command_plan(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            write_full_lifecycle_state(module, root)
            plan = [
                {"stage": "provider_data", "name": "01_provider", "argv": [root / "input.json"], "timeout": 1},
                {"stage": "pre_bayes", "name": "02_prior", "argv": ["prior"], "timeout": 1},
            ]

            with patch.object(module, "prepare_local_data"), patch.object(
                module, "reset_prior_init_state"
            ), patch.object(
                module, "staged_command_results", return_value=[]
            ), patch.object(
                module, "build_lifecycle_command_plan", return_value=plan
            ), patch.object(
                module,
                "run_lifecycle_driver",
                return_value=[{"stage": "provider_data", "name": "01_provider", "exit": 1, "timed_out": False}],
            ):
                rc = module.main(["--root", str(root), "--execute-driver"])

            plan_payload = json.loads((root / "checks/lifecycle_command_plan.json").read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertEqual(plan_payload["steps"][0]["argv"][0], str(root / "input.json"))

    def test_execute_driver_runs_even_when_staged_results_exist(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            write_full_lifecycle_state(module, root)
            plan = [
                {"stage": "provider_data", "name": "01_provider", "argv": ["provider"], "timeout": 1},
                {"stage": "pre_bayes", "name": "02_prior", "argv": ["prior"], "timeout": 1},
            ]
            driver_results = [
                {"stage": "provider_data", "name": "01_provider", "exit": 0, "timed_out": False},
                {"stage": "pre_bayes", "name": "02_prior", "exit": 1, "timed_out": False},
            ]

            with patch.object(module, "prepare_local_data"), patch.object(
                module, "reset_prior_init_state"
            ), patch.object(
                module, "staged_command_results", return_value=practical_command_results()
            ), patch.object(
                module, "build_lifecycle_command_plan", return_value=plan
            ), patch.object(module, "run_lifecycle_driver", return_value=driver_results) as run_driver:
                rc = module.main(["--root", str(root), "--execute-driver"])

            metrics = json.loads((root / "checks/terminal_metrics.json").read_text(encoding="utf-8"))

        run_driver.assert_called_once_with(plan)
        self.assertEqual(rc, 2)
        self.assertEqual(metrics["command_results"], driver_results)
        self.assertFalse((root / "summaries/same_tree_practical_closure.json").exists())

    def test_execute_driver_skips_lifecycle_when_explicit_feedback_file_has_no_accepted_rows(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            feedback = Path(tmp) / "accepted_feedback.jsonl"
            feedback.write_text("", encoding="utf-8")

            with patch.object(module, "prepare_local_data") as prepare_data, patch.object(
                module, "reset_prior_init_state"
            ) as reset_prior, patch.object(
                module, "build_lifecycle_command_plan"
            ) as build_plan, patch.object(module, "run_lifecycle_driver") as run_driver:
                rc = module.main(
                    [
                        "--root",
                        str(root),
                        "--execute-driver",
                        "--feedback-file",
                        str(feedback),
                    ]
                )

            preflight = json.loads((root / "checks/feedback_file_preflight.json").read_text(encoding="utf-8"))
            metrics = json.loads((root / "checks/terminal_metrics.json").read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertEqual(preflight["status"], "no_rows")
        self.assertFalse(preflight["accepted_execution_feedback_ready"])
        self.assertEqual(metrics["command_results"], [])
        self.assertFalse(metrics["all_command_exits_zero"])
        self.assertFalse((root / "summaries/same_tree_practical_closure.json").exists())
        prepare_data.assert_not_called()
        reset_prior.assert_not_called()
        build_plan.assert_not_called()
        run_driver.assert_not_called()

    def test_execute_driver_continues_when_explicit_feedback_file_has_accepted_rows(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            feedback = Path(tmp) / "accepted_feedback.jsonl"
            feedback.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "symbol": module.SYMBOL,
                        "trade_id": "paper-fill-0001",
                        "source": ACCEPTED_FEEDBACK_SOURCE,
                        "broker_realized": True,
                        "broker_fill_evidence": True,
                        "pnl": 1.25,
                        "realized_outcome": "win",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            plan = [{"stage": "provider_data", "name": "01_provider", "argv": ["provider"], "timeout": 1}]

            with patch.object(module, "prepare_local_data") as prepare_data, patch.object(
                module, "reset_prior_init_state"
            ) as reset_prior, patch.object(
                module, "build_lifecycle_command_plan", return_value=plan
            ) as build_plan, patch.object(
                module,
                "run_lifecycle_driver",
                return_value=[{"stage": "provider_data", "name": "01_provider", "exit": 1, "timed_out": False}],
            ) as run_driver:
                rc = module.main(
                    [
                        "--root",
                        str(root),
                        "--execute-driver",
                        "--feedback-file",
                        str(feedback),
                    ]
                )

            preflight = json.loads((root / "checks/feedback_file_preflight.json").read_text(encoding="utf-8"))

        self.assertEqual(rc, 2)
        self.assertEqual(preflight["status"], "ready")
        self.assertTrue(preflight["accepted_execution_feedback_ready"])
        self.assertEqual(preflight["accepted_rows"], 1)
        self.assertEqual(preflight["broker_fill_evidence_rows"], 1)
        self.assertEqual(preflight["broker_realized_rows"], 1)
        prepare_data.assert_called_once_with(root / "data/provider/normalized")
        reset_prior.assert_called_once()
        build_plan.assert_called_once()
        run_driver.assert_called_once_with(plan)

    def test_execute_driver_carries_current_accepted_feedback_summary_into_closure_metrics(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            feedback = tmp_path / "accepted_feedback.jsonl"
            evidence = root / "materials/closure_evidence.json"
            write_full_lifecycle_state(module, root)
            write_closure_evidence(module, evidence)
            feedback.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "symbol": module.SYMBOL,
                        "trade_id": "paper-fill-0001",
                        "source": ACCEPTED_FEEDBACK_SOURCE,
                        "broker_realized": True,
                        "broker_fill_evidence": True,
                        "pnl": 1.25,
                        "realized_outcome": "win",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            plan = [
                {"stage": row["stage"], "name": row["name"], "argv": [row["name"]], "timeout": 1}
                for row in practical_command_results()
            ]

            with patch.object(module, "prepare_local_data"), patch.object(
                module, "reset_prior_init_state"
            ), patch.object(
                module, "build_lifecycle_command_plan", return_value=plan
            ), patch.object(
                module,
                "run_lifecycle_driver",
                return_value=practical_command_results(),
            ):
                rc = module.main(
                    [
                        "--root",
                        str(root),
                        "--execute-driver",
                        "--feedback-file",
                        str(feedback),
                        "--closure-evidence",
                        str(evidence),
                    ]
                )

            metrics = json.loads((root / "checks/terminal_metrics.json").read_text(encoding="utf-8"))
            packet = json.loads((root / "summaries/same_tree_practical_closure.json").read_text(encoding="utf-8"))

        self.assertEqual(rc, 0)
        self.assertEqual(metrics["trade_summary"]["source"], ACCEPTED_FEEDBACK_SOURCE)
        self.assertEqual(metrics["trade_summary"]["accepted_rows"], 1)
        self.assertEqual(metrics["trade_summary"]["broker_fill_evidence_rows"], 1)
        self.assertEqual(metrics["trade_summary"]["broker_realized_rows"], 1)
        self.assertEqual(packet["status"], "pass")

    def test_execute_driver_normalizes_materialized_branch_identity(self) -> None:
        module = load_module()

        old_branch = module.BRANCH_PATH.replace(
            "PracticalLifecycleContinuation", "SimulatedOrPaperFeedbackPracticalClosure"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            library = root / "materials/tomac_nq_compound_trend_rrr_chopfilter_strategy_library.json"
            feedback = root / "feedback/tomac_nq_compound_trend_rrr_chopfilter_simulated_feedback.jsonl"
            write_json(
                library,
                {
                    "strategies": [
                        {
                            "metadata": {
                                "branch_path": old_branch,
                                "regime_profit_branch_path": old_branch,
                            }
                        }
                    ]
                },
            )
            feedback.parent.mkdir(parents=True, exist_ok=True)
            feedback.write_text(
                json.dumps({"branch_path": old_branch, "regime_profit_branch_path": old_branch}) + "\n",
                encoding="utf-8",
            )

            module.configure_paths(root)
            summary = module.normalize_materialized_branch_identity(library, feedback)

            library_payload = json.loads(library.read_text(encoding="utf-8"))
            feedback_row = json.loads(feedback.read_text(encoding="utf-8"))

        metadata = library_payload["strategies"][0]["metadata"]
        self.assertEqual(summary["strategy_rows_updated"], 1)
        self.assertEqual(summary["feedback_rows_updated"], 1)
        self.assertEqual(metadata["branch_path"], module.BRANCH_PATH)
        self.assertEqual(metadata["regime_profit_branch_path"], module.BRANCH_PATH)
        self.assertEqual(feedback_row["branch_path"], module.BRANCH_PATH)
        self.assertEqual(feedback_row["regime_profit_branch_path"], module.BRANCH_PATH)

    def test_failed_execute_driver_removes_stale_closure_packet(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            write_full_lifecycle_state(module, root)
            stale_packet = root / "summaries/same_tree_practical_closure.json"
            write_json(stale_packet, {"status": "pass", "stale": True})
            plan = [{"stage": "provider_data", "name": "01_provider", "argv": ["provider"], "timeout": 1}]

            with patch.object(module, "prepare_local_data"), patch.object(
                module, "reset_prior_init_state"
            ), patch.object(
                module, "build_lifecycle_command_plan", return_value=plan
            ), patch.object(
                module,
                "run_lifecycle_driver",
                return_value=[{"stage": "provider_data", "name": "01_provider", "exit": 1, "timed_out": False}],
            ):
                rc = module.main(["--root", str(root), "--execute-driver"])

        self.assertEqual(rc, 2)
        self.assertFalse(stale_packet.exists())


if __name__ == "__main__":
    unittest.main()
