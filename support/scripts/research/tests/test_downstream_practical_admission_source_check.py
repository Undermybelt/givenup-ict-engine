from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import downstream_practical_admission_source_check as checker  # noqa: E402


class DownstreamPracticalAdmissionSourceCheckTests(unittest.TestCase):
    def write_source(self, source: str) -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        path = Path(tmpdir.name) / "run_example_downstream_v1.py"
        path.write_text(source, encoding="utf-8")
        return path

    def test_flags_branch_local_admission_as_practical_assignment(self) -> None:
        path = self.write_source(
            """
def build_metrics(pass_exec):
    return {
        "branch_local_admitted": pass_exec,
        "promotion_allowed": pass_exec,
        "trade_usable": pass_exec,
        "update_goal": pass_exec,
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(report["decision"], "practical_admission_source_violation")
        self.assertEqual(
            sorted(hit["key"] for hit in report["violations"]),
            ["promotion_allowed", "trade_usable", "update_goal"],
        )

    def test_allows_practical_admission_flags_helper_routing(self) -> None:
        path = self.write_source(
            """
def practical_admission_flags(branch_local_admitted, extension_complete=False):
    practical_allowed = bool(branch_local_admitted and extension_complete)
    return {
        "branch_local_admitted": bool(branch_local_admitted),
        "extension_complete": bool(extension_complete),
        "promotion_allowed": practical_allowed,
        "trade_usable": practical_allowed,
        "update_goal": practical_allowed,
    }

def build_metrics(pass_exec):
    practical = practical_admission_flags(pass_exec)
    return {
        "branch_local_admitted": practical["branch_local_admitted"],
        "extension_complete": practical["extension_complete"],
        "promotion_allowed": practical["promotion_allowed"],
        "trade_usable": practical["trade_usable"],
        "update_goal": practical["update_goal"],
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_flags_hardcoded_true_extension_complete_helper_call(self) -> None:
        path = self.write_source(
            """
def practical_admission_flags(branch_local_admitted, extension_complete=False):
    practical_allowed = bool(branch_local_admitted and extension_complete)
    return {
        "branch_local_admitted": bool(branch_local_admitted),
        "extension_complete": bool(extension_complete),
        "promotion_allowed": practical_allowed,
        "trade_usable": practical_allowed,
        "update_goal": practical_allowed,
    }

def build_metrics(pass_exec):
    practical = practical_admission_flags(pass_exec, extension_complete=True)
    return {
        "branch_local_admitted": practical["branch_local_admitted"],
        "extension_complete": practical["extension_complete"],
        "promotion_allowed": practical["promotion_allowed"],
        "trade_usable": practical["trade_usable"],
        "update_goal": practical["update_goal"],
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"][0]["violation"],
            "extension_complete_without_validated_practical_closure_source",
        )
        self.assertEqual(report["violations"][0]["key"], "extension_complete")

    def test_flags_metrics_extension_complete_readback_helper_call(self) -> None:
        path = self.write_source(
            """
def practical_admission_flags(branch_local_admitted, extension_complete=False):
    practical_allowed = bool(branch_local_admitted and extension_complete)
    return {
        "branch_local_admitted": bool(branch_local_admitted),
        "extension_complete": bool(extension_complete),
        "promotion_allowed": practical_allowed,
        "trade_usable": practical_allowed,
        "update_goal": practical_allowed,
    }

def rewrite_metrics(metrics):
    practical = practical_admission_flags(
        bool(metrics.get("branch_local_admitted")),
        extension_complete=bool(metrics.get("extension_complete")),
    )
    metrics["promotion_allowed"] = practical["promotion_allowed"]
    metrics["trade_usable"] = practical["trade_usable"]
    metrics["update_goal"] = practical["update_goal"]
    return metrics
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"][0]["violation"],
            "extension_complete_without_validated_practical_closure_source",
        )
        self.assertEqual(report["violations"][0]["key"], "extension_complete")

    def test_flags_returned_true_extension_complete_helper_call(self) -> None:
        path = self.write_source(
            """
def practical_admission_flags(branch_local_admitted, extension_complete=False):
    practical_allowed = bool(branch_local_admitted and extension_complete)
    return {
        "branch_local_admitted": bool(branch_local_admitted),
        "extension_complete": bool(extension_complete),
        "promotion_allowed": practical_allowed,
        "trade_usable": practical_allowed,
        "update_goal": practical_allowed,
    }

def build_metrics(pass_exec):
    return practical_admission_flags(pass_exec, extension_complete=True)
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"][0]["violation"],
            "extension_complete_without_validated_practical_closure_source",
        )
        self.assertEqual(report["violations"][0]["key"], "extension_complete")

    def test_allows_unrelated_extension_complete_keyword_call(self) -> None:
        path = self.write_source(
            """
def build_report(extension_complete=False):
    return {"extension_complete": bool(extension_complete)}

def build_metrics(pass_exec):
    report = build_report(extension_complete=True)
    return {
        "extension_complete": report["extension_complete"],
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_flags_practical_helper_that_ignores_extension_complete(self) -> None:
        path = self.write_source(
            """
def practical_admission_flags(branch_local_admitted, extension_complete=False):
    practical_allowed = bool(branch_local_admitted)
    return {
        "branch_local_admitted": bool(branch_local_admitted),
        "extension_complete": bool(extension_complete),
        "promotion_allowed": practical_allowed,
        "trade_usable": practical_allowed,
        "update_goal": practical_allowed,
    }

def build_metrics(pass_exec):
    practical = practical_admission_flags(pass_exec)
    return {
        "promotion_allowed": practical["promotion_allowed"],
        "trade_usable": practical["trade_usable"],
        "update_goal": practical["update_goal"],
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(
            sorted(hit["key"] for hit in report["violations"]),
            ["promotion_allowed", "promotion_allowed", "trade_usable", "trade_usable", "update_goal", "update_goal"],
        )

    def test_flags_practical_helper_that_ors_extension_complete(self) -> None:
        path = self.write_source(
            """
def practical_admission_flags(branch_local_admitted, extension_complete=False):
    practical_allowed = bool(branch_local_admitted or extension_complete)
    return {
        "branch_local_admitted": bool(branch_local_admitted),
        "extension_complete": bool(extension_complete),
        "promotion_allowed": practical_allowed,
        "trade_usable": practical_allowed,
        "update_goal": practical_allowed,
    }

def build_metrics(pass_exec):
    practical = practical_admission_flags(pass_exec)
    return {
        "promotion_allowed": practical["promotion_allowed"],
        "trade_usable": practical["trade_usable"],
        "update_goal": practical["update_goal"],
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(
            sorted(hit["key"] for hit in report["violations"]),
            ["promotion_allowed", "promotion_allowed", "trade_usable", "trade_usable", "update_goal", "update_goal"],
        )

    def test_flags_pda_as_branch_local_hard_gate_before_helper(self) -> None:
        path = self.write_source(
            """
def practical_admission_flags(branch_local_admitted, extension_complete=False):
    practical_allowed = bool(branch_local_admitted and extension_complete)
    return {
        "branch_local_admitted": bool(branch_local_admitted),
        "extension_complete": bool(extension_complete),
        "promotion_allowed": practical_allowed,
        "trade_usable": practical_allowed,
        "update_goal": practical_allowed,
    }

def build_metrics(all_ok, exact_branch_survived, actionable, hazard, pda, readiness):
    pass_exec = all_ok and exact_branch_survived and actionable and hazard < 0.60 and pda and readiness >= 0.45
    practical = practical_admission_flags(pass_exec)
    return {
        "branch_local_admitted": practical["branch_local_admitted"],
        "promotion_allowed": practical["promotion_allowed"],
        "trade_usable": practical["trade_usable"],
        "update_goal": practical["update_goal"],
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(report["violations"][0]["violation"], "branch_local_admission_uses_pda_hard_gate")

    def test_flags_transition_hazard_as_branch_local_hard_gate(self) -> None:
        path = self.write_source(
            """
def practical_admission_flags(branch_local_admitted, extension_complete=False):
    practical_allowed = bool(branch_local_admitted and extension_complete)
    return {
        "branch_local_admitted": bool(branch_local_admitted),
        "extension_complete": bool(extension_complete),
        "promotion_allowed": practical_allowed,
        "trade_usable": practical_allowed,
        "update_goal": practical_allowed,
    }

def build_metrics(all_ok, exact_branch_survived, actionable, hazard, pda, readiness):
    pass_exec = all_ok and exact_branch_survived and actionable and hazard < 0.60 and readiness >= 0.45
    practical = practical_admission_flags(pass_exec)
    return {
        "pda_hybrid_alignment": pda,
        "pda_required": False,
        "branch_local_admitted": practical["branch_local_admitted"],
        "promotion_allowed": practical["promotion_allowed"],
        "trade_usable": practical["trade_usable"],
        "update_goal": practical["update_goal"],
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(report["violations"][0]["violation"], "branch_local_admission_uses_transition_hard_gate")

    def test_flags_transition_hazard_taint_through_intermediate_guard(self) -> None:
        path = self.write_source(
            """
def practical_admission_flags(branch_local_admitted, extension_complete=False):
    practical_allowed = bool(branch_local_admitted and extension_complete)
    return {
        "branch_local_admitted": bool(branch_local_admitted),
        "extension_complete": bool(extension_complete),
        "promotion_allowed": practical_allowed,
        "trade_usable": practical_allowed,
        "update_goal": practical_allowed,
    }

def build_metrics(branch_ok, transition_hazard, readiness):
    hazard_ok = transition_hazard < 0.60
    pass_exec = branch_ok and hazard_ok and readiness >= 0.45
    practical = practical_admission_flags(pass_exec)
    return {
        "transition_hazard": transition_hazard,
        "branch_local_admitted": practical["branch_local_admitted"],
        "promotion_allowed": practical["promotion_allowed"],
        "trade_usable": practical["trade_usable"],
        "update_goal": practical["update_goal"],
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(report["violations"][0]["violation"], "branch_local_admission_uses_transition_hard_gate")
        self.assertEqual(report["violations"][0]["key"], "branch_local_admitted")

    def test_allows_pda_and_transition_telemetry_not_in_branch_local_hard_gate(self) -> None:
        path = self.write_source(
            """
def practical_admission_flags(branch_local_admitted, extension_complete=False):
    practical_allowed = bool(branch_local_admitted and extension_complete)
    return {
        "branch_local_admitted": bool(branch_local_admitted),
        "extension_complete": bool(extension_complete),
        "promotion_allowed": practical_allowed,
        "trade_usable": practical_allowed,
        "update_goal": practical_allowed,
    }

def build_metrics(all_ok, exact_branch_survived, actionable, hazard, pda, readiness):
    pass_exec = all_ok and exact_branch_survived and actionable and readiness >= 0.45
    practical = practical_admission_flags(pass_exec)
    return {
        "pda_required": False,
        "transition_hazard_required": False,
        "branch_local_admitted": practical["branch_local_admitted"],
        "promotion_allowed": practical["promotion_allowed"],
        "trade_usable": practical["trade_usable"],
        "update_goal": practical["update_goal"],
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_flags_retired_pda_or_transition_policy_templates(self) -> None:
        path = self.write_source(
            """
DEFAULT_PERSONAL_PROFILE = {
    "strict_gate_policy": {
        "transition_hazard_lt": 0.60,
        "pda_hybrid_alignment": True,
        "execution_readiness_min": 0.45,
    }
}
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(
            sorted(hit["key"] for hit in report["violations"]),
            ["pda_hybrid_alignment", "transition_hazard_lt"],
        )
        self.assertEqual(
            {hit["violation"] for hit in report["violations"]},
            {"retired_field_used_as_practical_gate_template"},
        )

    def test_allows_false_retired_gate_telemetry_in_dict_call(self) -> None:
        path = self.write_source(
            """
def build_metrics():
    return dict(
        pda_required=False,
        transition_hazard_required=False,
        promotion_allowed=False,
        trade_usable=False,
        update_goal=False,
    )
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_allows_explicit_false_observation_metrics(self) -> None:
        path = self.write_source(
            """
def build_metrics():
    return {
        "extension_complete": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_allows_learning_admission_without_practical_flags(self) -> None:
        path = self.write_source(
            """
def build_metrics(branch_ok):
    return {
        "learning_admission_status": "admitted" if branch_ok else "blocked",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_flags_learning_admission_reused_as_trade_usable(self) -> None:
        path = self.write_source(
            """
def build_metrics(branch_ok):
    lifecycle = {"learning_allowed": branch_ok}
    learning_allowed = lifecycle["learning_allowed"]
    return {
        "learning_allowed": learning_allowed,
        "trade_usable": learning_allowed,
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"][0]["violation"],
            "learning_admission_reused_as_practical_flag",
        )
        self.assertEqual(report["violations"][0]["key"], "trade_usable")

    def test_flags_lifecycle_live_trade_assignment_without_local_helper_contract(self) -> None:
        path = self.write_source(
            """
def lifecycle_decision():
    lifecycle = {
        "learning_admission": {"status": "admitted"},
        "live_trade": {
            "promotion_allowed": False,
            "trade_usable": False,
        },
    }
    return lifecycle

def build_report():
    lifecycle = lifecycle_decision()
    report = {}
    report["promotion_allowed"] = lifecycle["live_trade"]["promotion_allowed"]
    report["trade_usable"] = lifecycle["live_trade"]["trade_usable"]
    return report
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(
            sorted(hit["key"] for hit in report["violations"]),
            ["promotion_allowed", "trade_usable"],
        )

    def test_allows_passive_lifecycle_readback_view(self) -> None:
        path = self.write_source(
            """
def closed_loop_consumption_view(lifecycle):
    live_trade = (lifecycle or {}).get("live_trade") or {}
    promotion_allowed = bool(live_trade.get("promotion_allowed", False))
    trade_usable = bool(live_trade.get("trade_usable", False))
    return {
        "closed_loop_consumption_status": "promotion_ready" if promotion_allowed and trade_usable else "inspection_only",
        "promotion_allowed": promotion_allowed,
        "trade_usable": trade_usable,
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_allows_passive_claim_readback_view(self) -> None:
        path = self.write_source(
            """
def claim_readback(claim):
    return {
        "claim_file": claim.get("claim_file"),
        "promotion_allowed": claim.get("promotion_allowed"),
        "trade_usable": claim.get("trade_usable"),
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_allows_passive_serialized_claim_bool_extraction(self) -> None:
        path = self.write_source(
            """
def parse_claim(fields, serialized):
    if not isinstance(fields.get("promotion_allowed"), bool):
        fields["promotion_allowed"] = _extract_bool("promotion_allowed", serialized)
    if not isinstance(fields.get("trade_usable"), bool):
        fields["trade_usable"] = _extract_bool("trade_usable", serialized)
    return fields
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_allows_explicit_false_name_aliases(self) -> None:
        path = self.write_source(
            """
def build_report():
    promotion_allowed = False
    trade_usable = False
    update_goal = False
    return {
        "promotion_allowed": promotion_allowed,
        "trade_usable": trade_usable,
        "update_goal": update_goal,
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_allows_module_level_false_default_aliases(self) -> None:
        path = self.write_source(
            """
PROMOTION_ALLOWED_DEFAULT = False
TRADE_USABLE_DEFAULT = False

def build_report():
    return {
        "promotion_allowed": PROMOTION_ALLOWED_DEFAULT,
        "trade_usable": TRADE_USABLE_DEFAULT,
        "update_goal": False,
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_does_not_trust_module_level_false_default_after_reassignment(self) -> None:
        path = self.write_source(
            """
PROMOTION_ALLOWED_DEFAULT = False
PROMOTION_ALLOWED_DEFAULT = compute_runtime_flag()

def build_report():
    return {"promotion_allowed": PROMOTION_ALLOWED_DEFAULT}
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(report["violations"][0]["key"], "promotion_allowed")

    def test_does_not_trust_false_name_alias_after_reassignment(self) -> None:
        path = self.write_source(
            """
def build_report(pass_exec):
    promotion_allowed = False
    promotion_allowed = pass_exec
    return {"promotion_allowed": promotion_allowed}
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(report["violations"][0]["key"], "promotion_allowed")

    def test_allows_passive_report_subscript_readback(self) -> None:
        path = self.write_source(
            """
def print_summary(report):
    return {
        "promotion_allowed": report["promotion_allowed"],
        "trade_usable": report["trade_usable"],
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_allows_diagnostic_allowed_targets_context(self) -> None:
        path = self.write_source(
            """
def build_report(allowed):
    return {
        "decision": "diagnostic_only",
        "allowed_targets": {
            "promotion_allowed": allowed,
            "trade_usable": allowed,
        },
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_does_not_trust_practical_dict_without_helper_call(self) -> None:
        path = self.write_source(
            """
def build_metrics(pass_exec):
    practical = {
        "promotion_allowed": pass_exec,
        "trade_usable": pass_exec,
        "update_goal": pass_exec,
    }
    return {
        "promotion_allowed": practical["promotion_allowed"],
        "trade_usable": practical["trade_usable"],
        "update_goal": practical["update_goal"],
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(
            sorted(hit["key"] for hit in report["violations"]),
            ["promotion_allowed", "promotion_allowed", "trade_usable", "trade_usable", "update_goal", "update_goal"],
        )

    def test_flags_decision_string_practical_assignment_without_extension_contract(self) -> None:
        path = self.write_source(
            """
def build_metrics(decision):
    return {
        "promotion_allowed": decision == "downstream_execution_actionable",
        "trade_usable": decision == "downstream_execution_actionable",
        "update_goal": decision == "downstream_execution_actionable",
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(
            sorted(hit["value"] for hit in report["violations"]),
            [
                'decision == "downstream_execution_actionable"',
                'decision == "downstream_execution_actionable"',
                'decision == "downstream_execution_actionable"',
            ],
        )

    def test_flags_post_dict_practical_subscript_assignment_without_extension_contract(self) -> None:
        path = self.write_source(
            """
def build_metrics(downstream_allowed):
    metrics = {}
    metrics["promotion_allowed"] = downstream_allowed
    metrics["trade_usable"] = downstream_allowed
    metrics["update_goal"] = downstream_allowed
    return metrics
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(
            sorted(hit["key"] for hit in report["violations"]),
            ["promotion_allowed", "trade_usable", "update_goal"],
        )

    def test_allows_post_dict_practical_subscript_assignment_from_helper(self) -> None:
        path = self.write_source(
            """
def practical_admission_flags(branch_local_admitted, extension_complete=False):
    practical_allowed = bool(branch_local_admitted and extension_complete)
    return {
        "branch_local_admitted": bool(branch_local_admitted),
        "extension_complete": bool(extension_complete),
        "promotion_allowed": practical_allowed,
        "trade_usable": practical_allowed,
        "update_goal": practical_allowed,
    }

def build_metrics(pass_exec):
    practical = practical_admission_flags(pass_exec)
    metrics = {}
    metrics["promotion_allowed"] = practical["promotion_allowed"]
    metrics["trade_usable"] = practical["trade_usable"]
    metrics["update_goal"] = practical["update_goal"]
    return metrics
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_flags_dict_call_practical_keywords_without_extension_contract(self) -> None:
        path = self.write_source(
            """
def build_metrics(downstream_allowed):
    return dict(
        promotion_allowed=downstream_allowed,
        trade_usable=downstream_allowed,
        update_goal=downstream_allowed,
    )
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(
            sorted(hit["key"] for hit in report["violations"]),
            ["promotion_allowed", "trade_usable", "update_goal"],
        )

    def test_allows_dict_call_practical_keywords_from_helper(self) -> None:
        path = self.write_source(
            """
def practical_admission_flags(branch_local_admitted, extension_complete=False):
    practical_allowed = bool(branch_local_admitted and extension_complete)
    return {
        "branch_local_admitted": bool(branch_local_admitted),
        "extension_complete": bool(extension_complete),
        "promotion_allowed": practical_allowed,
        "trade_usable": practical_allowed,
        "update_goal": practical_allowed,
    }

def build_metrics(pass_exec):
    practical = practical_admission_flags(pass_exec)
    return dict(
        promotion_allowed=practical["promotion_allowed"],
        trade_usable=practical["trade_usable"],
        update_goal=practical["update_goal"],
    )
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])

    def test_flags_downstream_admission_from_2bps_survivors(self) -> None:
        path = self.write_source(
            """
def build_metrics(branch_ok, survivors_2, survivors_5):
    downstream = branch_ok and bool(survivors_2)
    return {
        "exact_1m_survivors_2bps": survivors_2,
        "exact_1m_survivors_5bps": survivors_5,
        "downstream_allowed": downstream,
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"][0]["violation"],
            "downstream_admission_uses_2bps_survivor_gate",
        )

    def test_flags_5bps_survival_trade_count_floor(self) -> None:
        path = self.write_source(
            """
def score(row):
    trades = int(row.get("trade_count") or 0)
    row["survives_5bps_per_side"] = trades >= 6 and row["5bps_per_side_total_profit_pct"] > 0
    return row
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(
            report["violations"][0]["violation"],
            "five_bps_survival_uses_trade_density_floor",
        )

    def test_allows_5bps_survival_trade_count_positive_and_downstream_from_5bps(self) -> None:
        path = self.write_source(
            """
def build_metrics(branch_ok, survivors_5):
    row = {}
    trades = 1
    row["survives_5bps_per_side"] = trades > 0 and row["5bps_per_side_total_profit_pct"] > 0
    downstream = branch_ok and bool(survivors_5)
    return {
        "exact_1m_survivors_5bps": survivors_5,
        "downstream_allowed": downstream,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"])
        self.assertEqual(report["violations"], [])


if __name__ == "__main__":
    unittest.main()
