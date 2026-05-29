from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import same_tree_practical_closure as closure  # noqa: E402


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
        "command_results": [{"name": "all", "exit": 0, "timed_out": False}],
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

    def test_rejects_timed_out_command_result_even_when_exit_zero(self) -> None:
        metrics = valid_metrics()
        metrics["command_results"] = [{"name": "analyze", "exit": 0, "timed_out": True}]

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

    def test_rejects_bad_market_data_provenance(self) -> None:
        metrics = valid_metrics()
        metrics["market_data_provenance"]["source_class"] = "raw_contract_stitching"

        self.assertIsNone(closure.build_same_tree_practical_closure_packet(metrics))

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
