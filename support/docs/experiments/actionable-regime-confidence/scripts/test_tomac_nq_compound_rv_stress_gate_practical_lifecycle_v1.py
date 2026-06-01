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
    "run_tomac_nq_compound_rv_stress_gate_practical_lifecycle_v1.py"
)
EXPECTED_BRANCH = (
    "US index futures -> NQ -> ETH/full_retained_session -> 1m parent execution + shifted 5m/15m/30m/1h/4h/1d context "
    "-> HtfTrendRegime -> ChopFilter(ER>=0.35,n40) -> MomentumResonance -> CompoundTrendRrrBreadth "
    "-> FixedRrrBracket -> RealizedVolatilityStressGate(30m_abs_ret16_max <= 0.04174409724) "
    "-> PracticalLifecycleContinuation"
)
ACCEPTED_FEEDBACK_SOURCE = "auto_quant_real_trades:paper_execution_feedback:nq_compound_rv_stress_fixture"


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


def write_accepted_runtime_feedback_summary(root: Path) -> None:
    write_json(
        root / "checks/runtime_trade_feedback_summary.json",
        {
            "source": ACCEPTED_FEEDBACK_SOURCE,
            "broker_realized": True,
            "broker_fill_evidence": True,
            "rows": 535,
        },
    )


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
        "non_rth_row_count": 535,
        "rth_window": "09:30-16:00",
        "timezone": "America/New_York",
        "evidence": "fixtures/nq_retained_session_coverage.json",
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


def write_live_plane_ready_state_with_stale_candidate(module, root: Path) -> None:
    symbol_dir = root / "state" / module.SYMBOL
    closed_loop = {
        "path_id": EXPECTED_BRANCH,
        "path_label": EXPECTED_BRANCH,
        "status": "fail_closed",
        "reason": "execution_plane_ready_but_lifecycle_tuple_missing",
        "ready": True,
        "actionable": True,
        "candidate_status": "execution_ready",
        "pre_bayes_gate_status": "pass_neutralized",
        "execution_gate_status": "execution_ready",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(symbol_dir / "workflow_snapshot.json", {})
    write_json(
        symbol_dir / "execution_candidate.json",
        {
            "candidate_status": "execution_observe_only",
            "actionable": False,
        },
    )
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
    write_json(
        symbol_dir / "policy_training/structural_path_ranking_target_summary.json",
        {
            "factor_profitability_lifecycle": {
                "learning_admitted_count": 4,
                "paper_ready_count": 4,
                "deploy_ready_count": 0,
                "live_ready_count": 0,
                "live_trade_usable_count": 0,
                "funded_live_fill_required": False,
                "readiness_contract": module.DEPLOY_READY_READINESS_CONTRACT,
                "promotion_allowed": False,
                "trade_usable": False,
            }
        },
    )


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

    def test_write_summary_emits_canonical_closure_from_complete_lifecycle_evidence(self) -> None:
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
            write_accepted_runtime_feedback_summary(root)
            metrics = module.write_summary(
                module.staged_command_results(material),
                module.market_data_provenance(material),
                material,
            )

            packet = json.loads(
                (root / "summaries/same_tree_practical_closure.json").read_text(encoding="utf-8")
            )
            summary = json.loads((root / "summaries/terminal_summary.json").read_text(encoding="utf-8"))

        self.assertEqual(metrics["status"], "practical_closure_pass")
        self.assertTrue(metrics["all_command_exits_zero"])
        self.assertEqual(metrics["market_data_provenance"]["status"], "pass")
        self.assertEqual(metrics["retained_session_coverage"]["status"], "pass")
        self.assertTrue(metrics["promotion_cost_verified"])
        self.assertEqual(metrics["cost_model"]["status"], "verified")
        self.assertEqual(packet["status"], "pass")
        self.assertTrue(packet["promotion_allowed"])
        self.assertTrue(packet["trade_usable"])
        self.assertFalse(metrics["promotion_allowed"])
        self.assertFalse(metrics["trade_usable"])
        self.assertFalse(metrics["update_goal"])
        self.assertFalse(metrics["extension_complete"])
        self.assertEqual(metrics["same_tree_practical_closure"], str(root / "summaries/same_tree_practical_closure.json"))
        self.assertFalse(summary["promotion_allowed"])
        self.assertFalse(summary["trade_usable"])
        self.assertFalse(summary["update_goal"])
        self.assertEqual(summary["same_tree_practical_closure"], str(root / "summaries/same_tree_practical_closure.json"))

    def test_write_summary_emits_canonical_closure_with_validated_extension_packet(self) -> None:
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
                "validated_extension_complete": True,
                "validated_extension_evidence": "same-tree lifecycle command rows plus policy lifecycle tuple",
            }
            write_json(source_packet_path, source_packet)
            write_materialization(
                material,
                practical_command_results(),
                explicit_market_data_provenance(),
            )
            write_full_lifecycle_state(module, root)

            module.configure_paths(root)
            write_accepted_runtime_feedback_summary(root)
            metrics = module.write_summary(
                module.staged_command_results(material),
                module.market_data_provenance(material),
                material,
                source_packet,
                source_packet_path,
            )

            packet = json.loads(
                (root / "summaries/same_tree_practical_closure.json").read_text(encoding="utf-8")
            )
            summary = json.loads((root / "summaries/terminal_summary.json").read_text(encoding="utf-8"))

        self.assertEqual(metrics["status"], "practical_closure_pass")
        self.assertFalse(metrics["promotion_allowed"])
        self.assertFalse(metrics["trade_usable"])
        self.assertFalse(metrics["update_goal"])
        self.assertFalse(metrics["extension_complete"])
        self.assertEqual(metrics["same_tree_practical_closure"], str(root / "summaries/same_tree_practical_closure.json"))
        self.assertFalse(summary["promotion_allowed"])
        self.assertFalse(summary["trade_usable"])
        self.assertFalse(summary["update_goal"])
        self.assertEqual(summary["same_tree_practical_closure"], str(root / "summaries/same_tree_practical_closure.json"))
        self.assertEqual(packet["status"], "pass")
        self.assertTrue(packet["promotion_allowed"])
        self.assertTrue(packet["trade_usable"])

    def test_write_summary_reads_factor_lifecycle_from_policy_training_stdout(self) -> None:
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
            write_json(
                root
                / "state"
                / module.SYMBOL
                / "policy_training/structural_path_ranking_target_summary.json",
                {"summary_line": "structural_path_ranking_target raw summary without lifecycle"},
            )
            module.configure_paths(root)
            write_json(
                root / "command-output/19_policy_after_ranker.out",
                {
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
                },
            )

            write_accepted_runtime_feedback_summary(root)
            metrics = module.write_summary(
                module.staged_command_results(material),
                module.market_data_provenance(material),
                material,
            )

        self.assertEqual(metrics["status"], "practical_closure_pass")
        self.assertEqual(
            metrics["policy_training_summary"]["factor_profitability_lifecycle"][
                "live_trade_usable_count"
            ],
            1,
        )
        self.assertEqual(metrics["live_trade_status"], "ready")
        self.assertEqual(
            metrics["readiness_contract"], module.DEPLOY_READY_READINESS_CONTRACT
        )

    def test_write_summary_rejects_simulated_runtime_feedback_summary(self) -> None:
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
            write_json(
                root / "checks/runtime_trade_feedback_summary.json",
                {
                    "source": module.TRADE_FEEDBACK_SOURCE,
                    "broker_realized": False,
                    "broker_fill_evidence": False,
                    "rows": 535,
                },
            )
            metrics = module.write_summary(
                module.staged_command_results(material),
                module.market_data_provenance(material),
                material,
            )

            closure_path = root / "summaries/same_tree_practical_closure.json"

        self.assertEqual(metrics["status"], "practical_lifecycle_fail_closed")
        self.assertEqual(metrics["feedback_source"], module.TRADE_FEEDBACK_SOURCE)
        self.assertFalse(closure_path.exists())

    def test_write_summary_prefers_closed_loop_candidate_status_over_stale_candidate_file(
        self,
    ) -> None:
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
            write_live_plane_ready_state_with_stale_candidate(module, root)

            module.configure_paths(root)
            metrics = module.write_summary(
                module.staged_command_results(material),
                module.market_data_provenance(material),
                material,
            )

        self.assertEqual(metrics["execution_candidate_status"], "execution_ready")
        self.assertTrue(metrics["execution_candidate_actionable"])
        self.assertTrue(metrics["branch_local_admitted"])
        self.assertEqual(metrics["status"], "practical_lifecycle_fail_closed")
        self.assertFalse(metrics["promotion_allowed"])
        self.assertFalse(metrics["trade_usable"])

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

    def test_prepares_runtime_strategy_library_from_materialization_library(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            source_library = tmp_path / "source_strategy_library.json"
            write_json(
                source_library,
                {
                    "schema_version": "tomac-nq-compound-rv-stress-gate-strategy-library/v1",
                    "factor_id": module.FACTOR_ID,
                    "parent_factor_id": module.PARENT_FACTOR_ID,
                    "symbol": "TOMAC_NQ_COMPOUND_RV_STRESS_GATE_FEEDBACK_MATERIALIZATION_V1",
                    "timeframe": "1m",
                    "strategies": [
                        {
                            "name": module.FACTOR_ID,
                            "symbol": "TOMAC_NQ_COMPOUND_RV_STRESS_GATE_FEEDBACK_MATERIALIZATION_V1",
                            "timeframe": "1m",
                            "metadata": {
                                "factor_id": module.FACTOR_ID,
                                "parent_factor_id": module.PARENT_FACTOR_ID,
                                "branch_path": EXPECTED_BRANCH.replace(
                                    "PracticalLifecycleContinuation", "SimulatedFeedbackMaterialization"
                                ),
                                "child_full_trade_count": 535,
                                "child_full_net5bps_total_ret_pct": 160.467967,
                                "child_oos_trade_count": 215,
                                "child_oos_net5bps_total_ret_pct": 52.662845,
                                "session_scope": "ETH/full_retained_session",
                                "rth_filter_applied": False,
                            },
                        }
                    ],
                },
            )

            module.configure_paths(root)
            prepared = module.prepare_runtime_strategy_library(source_library)
            payload = json.loads(prepared.read_text(encoding="utf-8"))

        self.assertEqual(payload["manifest_version"], "1.0")
        self.assertEqual(payload["auto_quant_repo_url"], "tomac_nq_compound_rv_stress_gate_practical_lifecycle_v1")
        self.assertEqual(payload["timeframe"], "1m")
        self.assertEqual(payload["strategies"][0]["status"], "ok")
        self.assertIsNone(payload["strategies"][0]["error"])
        self.assertEqual(payload["strategies"][0]["validation_metrics"]["trade_count"], 535)
        self.assertEqual(payload["strategies"][0]["validation_metrics"]["total_profit_pct"], 160.467967)
        self.assertEqual(payload["strategies"][0]["metadata"]["regime_profit_branch_path"], EXPECTED_BRANCH)
        self.assertFalse(payload["strategies"][0]["metadata"]["promotion_allowed"])
        self.assertFalse(payload["strategies"][0]["metadata"]["trade_usable"])

    def test_prepare_runtime_trade_feedback_adapts_materialization_jsonl_to_ingest_schema(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            feedback = tmp_path / "materialized_feedback.jsonl"
            feedback.write_text(
                json.dumps(
                    {
                        "row_index": 7,
                        "symbol": "TOMAC_NQ_COMPOUND_RV_STRESS_GATE_FEEDBACK_MATERIALIZATION_V1",
                        "stream_label": "pullback_sl12_rrr3_reson",
                        "event_ts": "2021-01-20 02:39:00+00:00",
                        "open_ts": "2021-01-20 02:39:00+00:00",
                        "bars_held": 4120,
                        "direction": 1,
                        "net5bps_return": 0.030651884980088785,
                        "gross_return": 0.031651884980088786,
                        "exit_reason": "tp",
                        "regime_profit_branch_path": EXPECTED_BRANCH.replace(
                            "PracticalLifecycleContinuation", "SimulatedFeedbackMaterialization"
                        ),
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            module.configure_paths(root)
            prepared, summary = module.prepare_runtime_trade_feedback(feedback)
            record = json.loads(prepared.read_text(encoding="utf-8"))

        self.assertEqual(summary["rows"], 1)
        self.assertEqual(record["schema_version"], "1.0")
        self.assertEqual(record["symbol"], module.SYMBOL)
        self.assertEqual(record["strategy_name"], "pullback_sl12_rrr3_reson")
        self.assertEqual(record["strategy_mutation_id"], module.FACTOR_ID)
        self.assertEqual(record["direction"], "Bull")
        self.assertEqual(record["pnl"], 0.030651884980088785)
        self.assertEqual(record["realized_outcome"], "win")
        self.assertEqual(record["regime_profit_branch_path"], EXPECTED_BRANCH)
        self.assertEqual(record["structural_feedback"]["path_id"], EXPECTED_BRANCH)
        self.assertGreater(record["close_ts_ms"], record["open_ts_ms"])

    def test_execute_driver_uses_prepared_runtime_trade_feedback(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            material = tmp_path / "material"
            source_library = tmp_path / "source_strategy_library.json"
            source_feedback = tmp_path / "feedback.jsonl"
            prepared_feedback = tmp_path / "prepared_real_trades.jsonl"
            write_json(source_library, {"strategies": []})
            source_feedback.write_text("{}\n", encoding="utf-8")
            prepared_feedback.write_text("", encoding="utf-8")
            plan = [{"stage": "feedback_update", "name": "08_feedback_update", "argv": ["feedback"], "timeout": 1}]

            with patch.object(module, "prepare_local_data"), patch.object(
                module, "prepare_runtime_trade_feedback", return_value=(prepared_feedback, {"rows": 1})
            ) as prepare_feedback, patch.object(
                module, "build_lifecycle_command_plan", return_value=plan
            ) as build_plan, patch.object(
                module,
                "run_lifecycle_driver",
                return_value=[{"stage": "feedback_update", "name": "08_feedback_update", "exit": 1, "timed_out": False}],
            ):
                module.main(
                    [
                        "--root",
                        str(root),
                        "--materialization-root",
                        str(material),
                        "--strategy-library",
                        str(source_library),
                        "--feedback-file",
                        str(source_feedback),
                        "--execute-driver",
                    ]
                )

        prepare_feedback.assert_called_once_with(source_feedback)
        _, kwargs = build_plan.call_args
        self.assertEqual(kwargs["feedback_file"], prepared_feedback)

    def test_lifecycle_command_plan_registers_catboost_trainer_artifact(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            module.configure_paths(root)
            plan = module.build_lifecycle_command_plan(
                strategy_library=tmp_path / "strategy_library.json",
                data_root=tmp_path / "data",
                feedback_file=tmp_path / "feedback.jsonl",
            )

        register = next(row for row in plan if row["name"] == "14_register_trainer")
        argv = register["argv"]
        model_family_index = argv.index("--model-family") + 1
        self.assertEqual(argv[model_family_index], "catboost")

    def test_reset_prior_init_state_removes_auto_quant_symbol_prior_artifacts_only(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            module.configure_paths(root)
            current = root / "state" / "auto-quant" / module.SYMBOL
            sibling = root / "state" / "auto-quant" / "OTHER_SYMBOL"
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

            self.assertEqual(len(removed["removed"]), 3)
            self.assertFalse((current / "bbn_network.json").exists())
            self.assertFalse((current / "auto_quant_prior_init_history.json").exists())
            self.assertFalse((current / "auto_quant_prior_init_old.json").exists())
            self.assertTrue((current / "auto_quant_strategy_library.json").exists())
            self.assertEqual(ledger[0]["status"], "rolled_back_before_lifecycle_rerun")
            self.assertEqual(ledger[1]["status"], "ready_for_prior_init")
            self.assertTrue((sibling / "bbn_network.json").exists())

    def test_prepares_runtime_trade_feedback_from_materialization_feedback(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            source_feedback = tmp_path / "materialized_feedback.jsonl"
            materialized_branch = EXPECTED_BRANCH.replace(
                "PracticalLifecycleContinuation", "SimulatedFeedbackMaterialization"
            )
            rows = [
                {
                    "row_index": 0,
                    "event_ts": "2021-01-10 23:17:00+00:00",
                    "open_ts": "2021-01-10 23:17:00+00:00",
                    "bars_held": 120,
                    "direction": 1,
                    "net5bps_return": 0.031,
                    "stream_label": "breakout_don60_sl8_rrr15",
                    "exit_reason": "tp",
                    "child_gate": "30m_abs_ret16_max",
                    "child_threshold": 0.04174409724,
                    "factor_id": module.FACTOR_ID,
                    "branch_path": materialized_branch,
                    "regime_profit_branch_path": materialized_branch,
                    "session_scope": "ETH/full_retained_session",
                    "rth_filter_applied": False,
                },
                {
                    "row_index": 1,
                    "event_ts": "2021-01-11 01:23:00+00:00",
                    "open_ts": "2021-01-11 01:23:00+00:00",
                    "bars_held": 60,
                    "direction": -1,
                    "net5bps_return": -0.012,
                    "stream_label": "pullback_sl12_rrr3_reson",
                    "exit_reason": "sl",
                    "child_gate": "30m_abs_ret16_max",
                    "child_threshold": 0.04174409724,
                    "factor_id": module.FACTOR_ID,
                    "branch_path": materialized_branch,
                    "regime_profit_branch_path": materialized_branch,
                    "session_scope": "ETH/full_retained_session",
                    "rth_filter_applied": False,
                },
            ]
            source_feedback.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

            module.configure_paths(root)
            runtime_feedback, summary = module.prepare_runtime_trade_feedback(source_feedback)
            payloads = [json.loads(line) for line in runtime_feedback.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(summary["rows"], 2)
        self.assertEqual(summary["wins"], 1)
        self.assertEqual(summary["losses"], 1)
        self.assertEqual(summary["target_schema"], "auto_quant_real_trades_jsonl/v1")
        self.assertEqual(payloads[0]["schema_version"], "1.0")
        self.assertEqual(payloads[0]["symbol"], module.SYMBOL)
        self.assertEqual(payloads[0]["direction"], "Bull")
        self.assertEqual(payloads[1]["direction"], "Bear")
        self.assertEqual(payloads[0]["realized_outcome"], "win")
        self.assertEqual(payloads[1]["realized_outcome"], "loss")
        self.assertEqual(payloads[0]["regime_profit_branch_path"], EXPECTED_BRANCH)
        self.assertEqual(payloads[0]["structural_feedback"]["path_id"], EXPECTED_BRANCH)
        self.assertTrue(payloads[0]["structural_feedback"]["followed_path"])
        self.assertIn("not broker fill", payloads[0]["structural_feedback"]["notes"])
        self.assertNotIn("trade_usable", payloads[0])

    def test_prepare_real_trade_feedback_preserves_accepted_execution_feedback_jsonl(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            source_feedback = tmp_path / "paper_feedback.jsonl"
            accepted_record = {
                "schema_version": "1.0",
                "symbol": module.SYMBOL,
                "trade_id": "paper-fill-0001",
                "strategy_name": module.FACTOR_ID,
                "strategy_mutation_id": module.FACTOR_ID,
                "source": ACCEPTED_FEEDBACK_SOURCE,
                "open_ts_ms": 1609714800000,
                "close_ts_ms": 1609718400000,
                "direction": "Bull",
                "pnl": 1.25,
                "realized_outcome": "win",
                "broker_realized": True,
                "broker_fill_evidence": True,
                "model_probabilities_before_trade": {
                    "selected_direction": "Bull",
                    "selected_probability": 0.72,
                    "long_score": 0.72,
                    "short_score": 0.28,
                    "win_prob_long": 0.72,
                    "win_prob_short": 0.28,
                    "uncertainty": 0.56,
                },
                "structural_feedback": {
                    "protocol_version": "structural-feedback-v1",
                    "recommendation_id": "paper-fill-0001",
                    "recommended_at": "2021-01-03T23:00:00Z",
                    "node_id": "US index futures",
                    "branch_id": "US index futures -> NQ",
                    "scenario_id": "US index futures -> NQ -> ETH/full_retained_session",
                    "path_id": EXPECTED_BRANCH,
                    "followed_path": True,
                    "exit_reason": "paper_fill_win",
                },
                "regime_profit_branch_path": EXPECTED_BRANCH,
                "main_regime": "US index futures",
                "sub_regime": "NQ",
                "sub_sub_regime_or_profit_factor": "ETH/full_retained_session",
                "profit_factor": module.FACTOR_ID,
            }
            source_feedback.write_text(json.dumps(accepted_record) + "\n", encoding="utf-8")

            module.configure_paths(root)
            runtime_feedback = module.prepare_real_trade_feedback(source_feedback)
            summary = json.loads((root / "checks/runtime_trade_feedback_summary.json").read_text(encoding="utf-8"))
            payloads = [json.loads(line) for line in runtime_feedback.read_text(encoding="utf-8").splitlines()]
            plan = module.build_lifecycle_command_plan(
                strategy_library=tmp_path / "strategy_library.json",
                data_root=root / "data/provider/normalized",
                feedback_file=runtime_feedback,
            )
            feedback_step = next(step for step in plan if step["name"] == "08_feedback_update")

        self.assertEqual(runtime_feedback, source_feedback)
        self.assertEqual(summary["source"], ACCEPTED_FEEDBACK_SOURCE)
        self.assertTrue(summary["broker_realized"])
        self.assertTrue(summary["broker_fill_evidence"])
        self.assertEqual(summary["rows"], 1)
        self.assertEqual(payloads[0]["source"], ACCEPTED_FEEDBACK_SOURCE)
        self.assertTrue(payloads[0]["broker_realized"])
        self.assertTrue(payloads[0]["broker_fill_evidence"])
        self.assertEqual(payloads[0]["structural_feedback"]["path_id"], EXPECTED_BRANCH)
        source_arg_index = feedback_step["argv"].index("--source") + 1
        self.assertEqual(feedback_step["argv"][source_arg_index], ACCEPTED_FEEDBACK_SOURCE)

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
            feedback_step = next(step for step in plan if step["name"] == "08_feedback_update")

        self.assertEqual(len(analyze_steps), 2)
        for step in analyze_steps:
            argv = step["argv"]
            self.assertIn(str(root / "data/provider/normalized"), argv)
        self.assertIn("auto_quant_real_trades:simulated_backtest:tomac_nq_compound_rv_stress_gate_v1", feedback_step["argv"])

    def test_run_lifecycle_driver_reads_register_model_family_from_trainer_artifact(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            artifact = root / "path_ranker_model/trainer_artifact.json"
            write_json(artifact, {"model_family": "catboost", "trained_rows": 4, "calibration_rows": 4})
            module.configure_paths(root)
            plan = [
                {
                    "stage": "path_ranker",
                    "name": "14_register_trainer",
                    "argv": [
                        module.ICT,
                        "register-structural-path-ranking-trainer-artifact",
                        "--artifact-uri",
                        artifact,
                        "--model-family",
                        "weighted_feature_sum_v1",
                    ],
                    "timeout": 1,
                }
            ]

            captured: list[list[str]] = []

            def fake_run_stage(stage: str, name: str, argv: list[object], timeout: int) -> dict:
                captured.append([str(item) for item in argv])
                return {"stage": stage, "name": name, "exit": 0, "timed_out": False}

            with patch.object(module, "run_stage", side_effect=fake_run_stage):
                results = module.run_lifecycle_driver(plan)

        self.assertEqual(results[0]["exit"], 0)
        model_family_index = captured[0].index("--model-family") + 1
        self.assertEqual(captured[0][model_family_index], "catboost")

    def test_main_prepares_default_data_root_before_execute_driver(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            material = tmp_path / "material"
            source_library = tmp_path / "source_strategy_library.json"
            write_json(source_library, {"strategies": []})
            plan = [{"stage": "provider_data", "name": "01_provider", "argv": ["provider"], "timeout": 1}]

            runtime_feedback = root / "feedback/tomac_nq_compound_rv_stress_runtime_real_trades.jsonl"

            with patch.object(module, "prepare_local_data") as prepare_data, patch.object(
                module, "prepare_real_trade_feedback", return_value=runtime_feedback
            ) as prepare_feedback, patch.object(
                module, "build_lifecycle_command_plan", return_value=plan
            ) as build_plan, patch.object(
                module,
                "run_lifecycle_driver",
                return_value=[{"stage": "provider_data", "name": "01_provider", "exit": 1, "timed_out": False}],
            ):
                module.main(
                    [
                        "--root",
                        str(root),
                        "--materialization-root",
                        str(material),
                        "--strategy-library",
                        str(source_library),
                        "--execute-driver",
                    ]
                )

        prepare_data.assert_called_once_with(root / "data/provider/normalized")
        prepare_feedback.assert_called_once_with(
            module.DEFAULT_MATERIALIZATION_ROOT
            / "feedback/tomac_nq_compound_rv_stress_gate_simulated_feedback.jsonl"
        )
        _, kwargs = build_plan.call_args
        self.assertEqual(kwargs["data_root"], root / "data/provider/normalized")
        self.assertEqual(kwargs["feedback_file"], root / "feedback/tomac_nq_compound_rv_stress_runtime_real_trades.jsonl")

    def test_main_converts_materialized_feedback_before_execute_driver(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            material = tmp_path / "material"
            source_library = tmp_path / "source_strategy_library.json"
            source_feedback = tmp_path / "materialized_feedback.jsonl"
            runtime_feedback = root / "feedback/tomac_nq_compound_rv_stress_runtime_real_trades.jsonl"
            write_json(source_library, {"strategies": []})
            source_feedback.write_text(json.dumps({"open_ts": "2021-01-10T23:17:00+00:00"}) + "\n", encoding="utf-8")
            plan = [{"stage": "provider_data", "name": "01_provider", "argv": ["provider"], "timeout": 1}]

            with patch.object(module, "prepare_local_data"), patch.object(
                module,
                "prepare_runtime_trade_feedback",
                return_value=(runtime_feedback, {"rows": 1, "target_schema": "auto_quant_real_trades_jsonl/v1"}),
            ) as prepare_feedback, patch.object(
                module, "build_lifecycle_command_plan", return_value=plan
            ) as build_plan, patch.object(
                module,
                "run_lifecycle_driver",
                return_value=[{"stage": "provider_data", "name": "01_provider", "exit": 1, "timed_out": False}],
            ):
                module.main(
                    [
                        "--root",
                        str(root),
                        "--materialization-root",
                        str(material),
                        "--strategy-library",
                        str(source_library),
                        "--feedback-file",
                        str(source_feedback),
                        "--execute-driver",
                    ]
                )

        prepare_feedback.assert_called_once_with(source_feedback)
        _, kwargs = build_plan.call_args
        self.assertEqual(kwargs["feedback_file"], runtime_feedback)

    def test_execute_driver_prepares_default_run_root_data_when_cleaned_files_missing(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            material = tmp_path / "material"
            strategy_library = tmp_path / "strategy_library.json"
            feedback_file = tmp_path / "feedback.jsonl"
            write_materialization(material)
            write_json(
                strategy_library,
                {
                    "timeframe": "1m",
                    "strategies": [
                        {
                            "name": module.FACTOR_ID,
                            "metadata": {
                                "factor_id": module.FACTOR_ID,
                                "child_full_trade_count": 535,
                                "child_full_net5bps_total_ret_pct": 160.467967,
                            },
                        }
                    ],
                },
            )
            feedback_file.write_text("", encoding="utf-8")
            plan = [
                {
                    "stage": "execution_tree",
                    "name": "03_analyze_seed",
                    "argv": ["analyze"],
                    "timeout": 1,
                }
            ]

            with patch.object(module, "prepare_local_data") as prepare_data, patch.object(
                module, "build_lifecycle_command_plan", return_value=plan
            ), patch.object(
                module,
                "run_lifecycle_driver",
                return_value=[{"stage": "execution_tree", "name": "03_analyze_seed", "exit": 1, "timed_out": False}],
            ):
                rc = module.main(
                    [
                        "--root",
                        str(root),
                        "--materialization-root",
                        str(material),
                        "--strategy-library",
                        str(strategy_library),
                        "--feedback-file",
                        str(feedback_file),
                        "--execute-driver",
                    ]
                )

        self.assertEqual(rc, 2)
        prepare_data.assert_called_once_with(root / "data/provider/normalized")

    def test_execute_driver_prepares_default_run_root_data_root_when_cleaned_files_missing(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            material = tmp_path / "material"
            data_root = root / "data/provider/normalized"
            source_feather = tmp_path / "NQ_USD-1m.feather"
            source_feather.write_text("fixture", encoding="utf-8")
            source_library = tmp_path / "source_strategy_library.json"
            feedback_file = tmp_path / "feedback.jsonl"
            feedback_file.write_text("", encoding="utf-8")
            write_materialization(material)
            write_json(
                source_library,
                {
                    "timeframe": "1m",
                    "strategies": [
                        {
                            "name": module.FACTOR_ID,
                            "metadata": {
                                "factor_id": module.FACTOR_ID,
                                "child_full_trade_count": 535,
                                "child_full_net5bps_total_ret_pct": 160.467967,
                            },
                        }
                    ],
                },
            )
            plan = [{"stage": "provider_data", "name": "01_provider", "argv": ["provider"], "timeout": 1}]

            def write_cleaned(_source_csv: Path, target_json: Path) -> int:
                target_json.parent.mkdir(parents=True, exist_ok=True)
                target_json.write_text(json.dumps({"candles": [1, 2, 3]}), encoding="utf-8")
                return 3

            with patch.object(module, "source_feather_path", return_value=source_feather, create=True), patch.object(
                module, "feather_to_csv", return_value=100, create=True
            ), patch.object(module, "trim_csv_rows", return_value=10, create=True), patch.object(
                module, "trimmed_csv_to_cleaned_json", side_effect=write_cleaned, create=True
            ), patch.object(module, "build_lifecycle_command_plan", return_value=plan) as build_plan, patch.object(
                module,
                "run_lifecycle_driver",
                return_value=[{"stage": "provider_data", "name": "01_provider", "exit": 1, "timed_out": False}],
            ):
                module.main(
                    [
                        "--root",
                        str(root),
                        "--materialization-root",
                        str(material),
                        "--strategy-library",
                        str(source_library),
                        "--feedback-file",
                        str(feedback_file),
                        "--execute-driver",
                    ]
                )

            cleaned_1m = data_root / "cleaned-1m" / f"{module.SYMBOL.lower()}.continuous-1m.json"
            self.assertTrue(cleaned_1m.exists())
            _, kwargs = build_plan.call_args
            self.assertEqual(kwargs["data_root"], data_root)

    def test_execute_driver_prepares_explicit_run_root_data_root_when_cleaned_files_missing(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            root = tmp_path / "root"
            material = tmp_path / "material"
            data_root = root / "data/provider/normalized"
            source_feather = tmp_path / "NQ_USD-1m.feather"
            source_feather.write_text("fixture", encoding="utf-8")
            source_library = tmp_path / "source_strategy_library.json"
            feedback_file = tmp_path / "feedback.jsonl"
            feedback_file.write_text("", encoding="utf-8")
            write_materialization(material)
            write_json(
                source_library,
                {
                    "timeframe": "1m",
                    "strategies": [
                        {
                            "name": module.FACTOR_ID,
                            "metadata": {
                                "factor_id": module.FACTOR_ID,
                                "child_full_trade_count": 535,
                                "child_full_net5bps_total_ret_pct": 160.467967,
                            },
                        }
                    ],
                },
            )
            plan = [{"stage": "provider_data", "name": "01_provider", "argv": ["provider"], "timeout": 1}]

            def write_cleaned(_source_csv: Path, target_json: Path) -> int:
                target_json.parent.mkdir(parents=True, exist_ok=True)
                target_json.write_text(json.dumps({"candles": [1, 2, 3]}), encoding="utf-8")
                return 3

            with patch.object(module, "source_feather_path", return_value=source_feather), patch.object(
                module, "feather_to_csv", return_value=100
            ), patch.object(module, "trim_csv_rows", return_value=10), patch.object(
                module, "trimmed_csv_to_cleaned_json", side_effect=write_cleaned
            ), patch.object(module, "build_lifecycle_command_plan", return_value=plan) as build_plan, patch.object(
                module,
                "run_lifecycle_driver",
                return_value=[{"stage": "provider_data", "name": "01_provider", "exit": 1, "timed_out": False}],
            ):
                module.main(
                    [
                        "--root",
                        str(root),
                        "--materialization-root",
                        str(material),
                        "--strategy-library",
                        str(source_library),
                        "--feedback-file",
                        str(feedback_file),
                        "--data-root",
                        str(data_root),
                        "--execute-driver",
                    ]
                )

            cleaned_1m = data_root / "cleaned-1m" / f"{module.SYMBOL.lower()}.continuous-1m.json"
            self.assertTrue(cleaned_1m.exists())
            _, kwargs = build_plan.call_args
            self.assertEqual(kwargs["data_root"], data_root)


if __name__ == "__main__":
    unittest.main()
