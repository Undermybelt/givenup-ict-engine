from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import same_tree_practical_closure as closure  # noqa: E402
import instrument_cost_model as instrument_cost  # noqa: E402


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


def practical_command_results_without_explicit_stages() -> list[dict]:
    return [{key: value for key, value in row.items() if key != "stage"} for row in practical_command_results()]


def valid_metrics() -> dict:
    return {
        "branch_path": "TrendExpansion -> Example -> factor_v1",
        "factor_id": "factor_v1",
        "promotion_allowed": True,
        "trade_usable": True,
        "update_goal": True,
        "all_command_exits_zero": True,
        "exact_branch_survived": True,
        "execution_candidate_actionable": True,
        "execution_candidate_status": "trade_candidate",
        "branch_local_admitted": True,
        "validation_ready": True,
        "path_ranker_used": True,
        "path_ranker_score_used_by_execution_tree": True,
        "validation_counters": {
            "raw_scored_mature": "1155/30",
            "production_validation": "1155/30",
            "observation_validation": "32/30",
        },
        "policy_training_summary": {
            "factor_profitability_lifecycle": {
                "learning_admitted_count": 1,
                "paper_ready_count": 1,
                "deploy_ready_count": 1,
                "live_ready_count": 1,
                "live_trade_usable_count": 1,
                "funded_live_fill_required": False,
                "readiness_contract": closure.DEPLOY_READY_READINESS_CONTRACT,
                "promotion_allowed": True,
                "trade_usable": True,
            }
        },
        "feedback_source": "auto_quant_real_trades:paper_execution_feedback:factor_v1",
        "runtime_trade_feedback_summary": {
            "source": "auto_quant_real_trades:paper_execution_feedback:factor_v1",
            "accepted_rows": 3,
            "broker_fill_evidence_rows": 3,
            "broker_realized_rows": 3,
        },
        "learning_admission_status": "admitted",
        "paper_admission_status": "ready",
        "deploy_ready": True,
        "live_trade_status": "ready",
        "funded_live_fill_required": False,
        "readiness_contract": closure.DEPLOY_READY_READINESS_CONTRACT,
        "market_data_provenance": {
            "status": "pass",
            "source_class": "roll_adjusted_clean_feather",
            "return_sanity": {
                "status": "pass",
                "extreme_abs_gross_gt_10pct_count": 0,
                "parse_bad_rows": 0,
                "max_abs_gross_return_pct": 4.2,
            },
        },
        "session_scope": "ETH/full_retained_session",
        "rth_filter_applied": False,
        "retained_session_coverage": {
            "status": "pass",
            "has_non_rth_rows": True,
            "non_rth_row_count": 384,
            "rth_window": "09:30-16:00",
            "timezone": "America/New_York",
            "evidence": "checks/retained_session_coverage.json",
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
        "command_results": practical_command_results(),
    }


class SameTreePracticalClosureTests(unittest.TestCase):
    def test_builds_pass_packet_from_full_practical_chain(self) -> None:
        packet = closure.build_same_tree_practical_closure_packet(valid_metrics())

        self.assertIsNotNone(packet)
        assert packet is not None
        self.assertEqual(packet["schema_version"], "same-tree-practical-closure/v1")
        self.assertEqual(packet["status"], "pass")
        self.assertTrue(packet["promotion_allowed"])
        self.assertTrue(packet["trade_usable"])
        self.assertTrue(packet["deploy_ready"])
        self.assertFalse(packet["funded_live_fill_required"])
        self.assertEqual(packet["readiness_contract"], closure.DEPLOY_READY_READINESS_CONTRACT)
        self.assertEqual(packet["provider_execution_feedback_chain"], "pass")
        self.assertTrue(packet["evidence_packet_validated"])

    def test_builds_pass_packet_from_full_chain_without_caller_preset_practical_flags(self) -> None:
        metrics = valid_metrics()
        metrics["promotion_allowed"] = False
        metrics["trade_usable"] = False
        metrics["update_goal"] = False

        packet = closure.build_same_tree_practical_closure_packet(metrics)

        self.assertIsNotNone(packet)
        assert packet is not None
        self.assertTrue(packet["promotion_allowed"])
        self.assertTrue(packet["trade_usable"])
        self.assertFalse(packet["update_goal"])

    def test_rejects_missing_lifecycle_tuple(self) -> None:
        metrics = valid_metrics()
        metrics["paper_admission_status"] = "not_evaluated"

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_funded_live_fill_requirement_semantic_drift(self) -> None:
        metrics = valid_metrics()
        metrics["funded_live_fill_required"] = True
        metrics["policy_training_summary"]["factor_profitability_lifecycle"][
            "funded_live_fill_required"
        ] = True

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_missing_deploy_ready_count(self) -> None:
        metrics = valid_metrics()
        del metrics["policy_training_summary"]["factor_profitability_lifecycle"][
            "deploy_ready_count"
        ]

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_policy_lifecycle_status_contradicting_top_level_tuple(self) -> None:
        metrics = valid_metrics()
        metrics["policy_training_summary"]["factor_profitability_lifecycle"].update(
            {
                "learning_admission_status": "not_evaluated",
                "paper_admission_status": "ready",
                "deploy_ready": True,
                "live_trade_status": "ready",
            }
        )

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_timed_out_command_result_even_when_exit_zero(self) -> None:
        metrics = valid_metrics()
        metrics["command_results"] = [{"name": "analyze", "exit": 0, "timed_out": True}]

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_command_result_without_explicit_non_timeout_proof(self) -> None:
        metrics = valid_metrics()
        metrics["command_results"] = [{"name": "analyze", "exit": 0}]

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_command_results_without_explicit_stage_proof(self) -> None:
        metrics = valid_metrics()
        metrics["command_results"] = practical_command_results_without_explicit_stages()

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_aggregate_command_result_without_step_coverage(self) -> None:
        metrics = valid_metrics()
        metrics["command_results"] = [{"name": "all", "exit": 0, "timed_out": False}]

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_single_command_name_spoofing_every_required_stage(self) -> None:
        metrics = valid_metrics()
        metrics["command_results"] = [
            {
                "name": "provider_pre_bayes_workflow_catboost_execution_tree_feedback_policy_training",
                "exit": 0,
                "timed_out": False,
            }
        ]

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_simulated_backtest_feedback_as_practical_closure_source(self) -> None:
        metrics = valid_metrics()
        metrics["feedback_source"] = "auto_quant_real_trades:simulated_backtest:rv_stress_gate"
        metrics["runtime_trade_feedback_summary"] = {
            "source": "auto_quant_real_trades:simulated_backtest:rv_stress_gate",
            "broker_fill_evidence": False,
            "broker_realized": False,
        }

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

        metrics = valid_metrics()
        metrics["command_results"] = [
            {
                **row,
                "name": "08_ingest_simulated_trade_feedback"
                if row["stage"] == "feedback_update"
                else row["name"],
            }
            for row in metrics["command_results"]
        ]

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_missing_accepted_execution_feedback_source(self) -> None:
        metrics = valid_metrics()
        metrics.pop("feedback_source")
        metrics.pop("runtime_trade_feedback_summary")

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_spoofed_accepted_execution_feedback_substring(self) -> None:
        metrics = valid_metrics()
        metrics["feedback_source"] = "audit:not_paper_execution_feedback:factor_v1"
        metrics["runtime_trade_feedback_summary"] = {
            "source": "audit:not_paper_execution_feedback:factor_v1",
            "accepted_rows": 3,
            "broker_fill_evidence_rows": 3,
            "broker_realized_rows": 3,
        }

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_negated_accepted_execution_feedback_token(self) -> None:
        metrics = valid_metrics()
        metrics["feedback_source"] = "audit:not-paper_execution_feedback:factor_v1"
        metrics["runtime_trade_feedback_summary"] = {
            "source": "audit:not paper_execution_feedback factor_v1",
            "accepted_rows": 3,
            "broker_fill_evidence_rows": 3,
            "broker_realized_rows": 3,
        }

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

        metrics = valid_metrics()
        metrics["feedback_source"] = "audit:without broker paper_execution_feedback:factor_v1"
        metrics["runtime_trade_feedback_summary"] = {
            "source": "audit:without-broker-paper_execution_feedback:factor_v1",
            "accepted_rows": 3,
            "broker_fill_evidence_rows": 3,
            "broker_realized_rows": 3,
        }

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_accepted_source_without_broker_execution_evidence(self) -> None:
        metrics = valid_metrics()
        metrics["runtime_trade_feedback_summary"] = {
            "source": "auto_quant_real_trades:paper_execution_feedback:factor_v1",
            "accepted_rows": 3,
        }

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_observe_only_execution_candidate_status(self) -> None:
        metrics = valid_metrics()
        metrics["execution_candidate_status"] = "execution_observe_only"

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_bad_market_data_provenance(self) -> None:
        metrics = valid_metrics()
        metrics["market_data_provenance"]["source_class"] = "raw_contract_stitching"

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_rth_only_or_unverified_session_scope(self) -> None:
        metrics = valid_metrics()
        metrics["session_scope"] = "RTH_comparison"

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

        metrics = valid_metrics()
        metrics["retained_session_coverage"]["has_non_rth_rows"] = False

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_session_scope_with_only_unstructured_non_rth_evidence_text(self) -> None:
        metrics = valid_metrics()
        metrics["retained_session_coverage"] = {
            "status": "pass",
            "has_non_rth_rows": True,
            "evidence": "verified retained tradable-session rows outside RTH",
        }

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_unverified_or_incomplete_cost_model(self) -> None:
        metrics = valid_metrics()
        metrics["promotion_cost_verified"] = False

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

        metrics = valid_metrics()
        metrics["cost_model"]["official_source_refs"] = []

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

        metrics = valid_metrics()
        metrics["cost_model"]["official_source_refs"] = [
            "https://www.interactivebrokers.com/en/pricing/commissions-futures.php"
        ]

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_accepts_verified_cost_model_status_with_structured_source_readback(self) -> None:
        metrics = valid_metrics()
        metrics["cost_model"]["status"] = "verified_ibkr_official"

        packet = closure.build_same_tree_practical_closure_packet(metrics)

        self.assertIsNotNone(packet)

    def test_accepts_exchange_field_as_cost_model_venue(self) -> None:
        metrics = valid_metrics()
        metrics["cost_model"].pop("venue_routing")
        metrics["cost_model"]["exchange"] = "CME"

        packet = closure.build_same_tree_practical_closure_packet(metrics)

        self.assertIsNotNone(packet)

    def test_accepts_canonical_futures_cost_packet_alias_fields(self) -> None:
        metrics = valid_metrics()
        cost_model = instrument_cost.cost_model_packet("NQ", 20000.0)
        cost_model["official_source_refs"] = [
            {
                "url": "https://www.interactivebrokers.com/en/pricing/commissions-futures.php",
                "same_turn_readback": "official_source_http_200_rate_verified",
            }
        ]
        metrics["cost_model"] = cost_model

        packet = closure.build_same_tree_practical_closure_packet(metrics)

        self.assertIsNotNone(packet)

    def test_write_removes_stale_packet_when_metrics_fail(self) -> None:
        metrics = valid_metrics()
        metrics["path_ranker_score_used_by_execution_tree"] = False
        with tempfile.TemporaryDirectory() as tmp:
            packet_path = Path(tmp) / "summaries/same_tree_practical_closure.json"
            packet_path.parent.mkdir(parents=True)
            packet_path.write_text(json.dumps({"status": "pass"}), encoding="utf-8")

            packet = closure.write_same_tree_practical_closure_packet(metrics, packet_path)

            self.assertIsNone(packet)
            self.assertFalse(packet_path.exists())


if __name__ == "__main__":
    unittest.main()
