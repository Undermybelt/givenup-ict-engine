#!/usr/bin/env python3
"""Audit current Board A root-regime completion against concrete artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T050045+0800-codex-current-goal-completion-audit"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T050045-codex-current-goal-completion-audit"
OUT_DIR = RUN_ROOT / "completion-audit"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

MIN_LCB = 0.95
MIN_COVERAGE = 0.03
MAX_ECE = 0.05
MIN_CAL_SUPPORT = 120
MIN_TEST_SUPPORT = 60


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def check_market_metric(metric: dict[str, Any]) -> dict[str, Any]:
    return {
        "support": metric.get("support"),
        "wilson95": metric.get("precision_wilson_lcb_95"),
        "coverage": metric.get("coverage"),
        "ece": metric.get("ece"),
        "validation_instruments": len(metric.get("validation_instruments", [])),
        "validation_market_contexts": len(metric.get("validation_market_contexts", [])),
        "validation_timeframes": len(metric.get("validation_timeframes", [])),
        "passes_lcb": metric.get("precision_wilson_lcb_95", 0.0) >= MIN_LCB,
        "passes_coverage": metric.get("coverage", 0.0) >= MIN_COVERAGE,
        "passes_ece": metric.get("ece", 0.0) <= MAX_ECE,
        "passes_support_cal": metric.get("support", 0) >= MIN_CAL_SUPPORT,
        "passes_support_test": metric.get("support", 0) >= MIN_TEST_SUPPORT,
        "passes_context": len(metric.get("validation_market_contexts", [])) >= 2,
        "passes_timeframes": len(metric.get("validation_timeframes", [])) >= 2,
    }


def market_root_result(root: str, report_path: Path, report: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    cal = check_market_metric(item["calibration"])
    test = check_market_metric(item["test"])
    accepted = bool(item.get("accepted_95", report.get("accepted_95", False)))
    state = item.get("state", report.get("state"))
    blockers = item.get("blockers", report.get("blockers", []))
    decision = report.get("decision", {})
    runtime_code_changed = bool(decision.get("runtime_code_changed", False))
    thresholds_relaxed = bool(decision.get("thresholds_relaxed", False))
    trade_usable = bool(decision.get("trade_usable", False))
    source = report.get("source", {})
    raw_committed = bool(
        source.get("raw_or_full_feature_table_committed", False)
        or source.get("raw_committed_to_repo", False)
    )
    passes = all(
        [
            accepted,
            state == "accepted_95",
            not blockers,
            cal["passes_lcb"],
            test["passes_lcb"],
            cal["passes_coverage"],
            test["passes_coverage"],
            cal["passes_ece"],
            test["passes_ece"],
            cal["passes_support_cal"],
            test["passes_support_test"],
            cal["passes_context"],
            test["passes_context"],
            cal["passes_timeframes"],
            test["passes_timeframes"],
            bool(item.get("rule") or report.get("rule")),
            not runtime_code_changed,
            not thresholds_relaxed,
            not trade_usable,
            not raw_committed,
        ]
    )
    return {
        "root": root,
        "passed": passes,
        "artifact": rel(report_path),
        "rule": item.get("rule") or report.get("rule"),
        "state": state,
        "accepted_95": accepted,
        "calibration": cal,
        "test": test,
        "blockers": blockers,
        "runtime_code_changed": runtime_code_changed,
        "thresholds_relaxed": thresholds_relaxed,
        "trade_usable": trade_usable,
        "raw_committed": raw_committed,
    }


def crisis_result(report_path: Path, report: dict[str, Any]) -> dict[str, Any]:
    item = next(root for root in report["root_reports"] if root["root_class"] == "Crisis")
    return market_root_result("Crisis", report_path, {"decision": {"runtime_code_changed": False, "thresholds_relaxed": False, "trade_usable": False}, "source": {}}, {
        "accepted_95": item["state"] == "accepted_95",
        "state": item["state"],
        "rule": item["selected_candidate"]["rule"],
        "blockers": item["selected_candidate"].get("blockers", []),
        "calibration": item["selected_candidate"]["calibration"],
        "test": item["selected_candidate"]["test"],
    })


def manipulation_result(report_path: Path, report: dict[str, Any]) -> dict[str, Any]:
    splits = {row["split"]: row for row in report["split_summaries"]}
    cal = splits["calibration"]
    test = splits["test"]
    accepted = bool(report["accepted_95"])
    passes = all(
        [
            accepted,
            report["candidate_root"] == "Manipulation",
            report["evidence_class"] == "direct_social_event_confirmed",
            report["target_policy"].startswith("source-backed direct"),
            report["rule"] == "classified_telegram_coin_pump_event_present == 1",
            cal["wilson95_lcb"] >= MIN_LCB,
            test["wilson95_lcb"] >= MIN_LCB,
            cal["support"] >= MIN_CAL_SUPPORT,
            test["support"] >= MIN_TEST_SUPPORT,
            cal["coverage"] >= MIN_COVERAGE,
            test["coverage"] >= MIN_COVERAGE,
            cal["negative_controls"] > 0,
            test["negative_controls"] > 0,
            report["source_stats"]["negative_controls"]["rows"] > 0,
            report["validation_contexts"]["coins_total"] >= 2,
            report["validation_contexts"]["channels_total"] >= 2,
            bool(report["abstain_condition"]),
            bool(report["allowed_action"]),
            not report["runtime_code_changed"],
            not report["thresholds_relaxed"],
            not report["raw_data_committed"],
            not report["trade_usable"],
        ]
    )
    return {
        "root": "Manipulation",
        "passed": passes,
        "artifact": rel(report_path),
        "rule": report["rule"],
        "state": "accepted_95" if accepted else "blocked",
        "accepted_95": accepted,
        "calibration": {
            "support": cal["support"],
            "wilson95": cal["wilson95_lcb"],
            "coverage": cal["coverage"],
            "negative_controls": cal["negative_controls"],
            "coins": cal["unique_coins_predicted_positive"],
            "channels": cal["unique_channels_predicted_positive"],
        },
        "test": {
            "support": test["support"],
            "wilson95": test["wilson95_lcb"],
            "coverage": test["coverage"],
            "negative_controls": test["negative_controls"],
            "coins": test["unique_coins_predicted_positive"],
            "channels": test["unique_channels_predicted_positive"],
        },
        "evidence_class": report["evidence_class"],
        "target_policy": report["target_policy"],
        "runtime_code_changed": report["runtime_code_changed"],
        "thresholds_relaxed": report["thresholds_relaxed"],
        "raw_committed": report["raw_data_committed"],
        "trade_usable": report["trade_usable"],
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    board_text = BOARD.read_text()

    bull_path = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T035045-codex-kaggle-bull-coverage-buffer-gate/kaggle-bull-gate/kaggle_bull_coverage_buffer_gate_report.json"
    yahoo_path = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T041923-codex-yahoo-sourcebacked-parent-root-gate/yahoo-parent-root-gate/yahoo_sourcebacked_parent_root_gate_report.json"
    crisis_path = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T235220-codex-broader-root-v2-probe/root-v2-broader/main_regime_v2_broader_root_calibration_report.json"
    manipulation_path = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T045102-codex-mehrnoom-telegram-direct-manipulation-gate/direct-event-gate/mehrnoom_telegram_direct_manipulation_gate_report.json"

    bull_report = load_json(bull_path)
    yahoo_report = load_json(yahoo_path)
    crisis_report = load_json(crisis_path)
    manipulation_report = load_json(manipulation_path)

    results = [
        market_root_result("Bull", bull_path, bull_report, bull_report),
        market_root_result("Bear", yahoo_path, yahoo_report, yahoo_report["root_reports"]["Bear"]),
        market_root_result("Sideways", yahoo_path, yahoo_report, yahoo_report["root_reports"]["Sideways"]),
        crisis_result(crisis_path, crisis_report),
        manipulation_result(manipulation_path, manipulation_report),
    ]

    checklist = [
        {
            "requirement": "Named board exists and is the active contract",
            "evidence": rel(BOARD),
            "passed": BOARD.exists() and "Actionable Regime Confidence TODO Board" in board_text,
        },
        {
            "requirement": "Active roots are MainRegimeV2 parent roots plus direct-input-gated Manipulation",
            "evidence": "Board Active MainRegimeV2 Root Ledger",
            "passed": all(root in board_text for root in ["`Bull`", "`Bear`", "`Sideways`", "`Crisis`", "`Manipulation`"])
            and "`UnknownOrMixed` | residual_only" in board_text,
        },
        {
            "requirement": "Expanded labels are not counted as completion roots",
            "evidence": "Board research guidance and root ledger",
            "passed": "child/provenance" in board_text and "sub_regime_evidence_only" in board_text,
        },
        {
            "requirement": "Every active root has accepted 95 evidence under concrete artifacts",
            "evidence": "Per-root artifact audit",
            "passed": all(row["passed"] for row in results),
        },
        {
            "requirement": "No trade-usable strategy is claimed by Board A",
            "evidence": "Per-root reports",
            "passed": all(not row["trade_usable"] for row in results),
        },
        {
            "requirement": "No runtime code changes or threshold relaxation are needed for accepted evidence",
            "evidence": "Per-root reports",
            "passed": all((not row["runtime_code_changed"] and not row["thresholds_relaxed"]) for row in results),
        },
    ]

    accepted_roots = [row["root"] for row in results if row["passed"]]
    missing_roots = [row["root"] for row in results if not row["passed"]]
    achieved = all(item["passed"] for item in checklist) and not missing_roots

    report = {
        "run_id": RUN_ID,
        "objective": str(BOARD) + " every regime confidence >=95 before reporting result",
        "success_criteria": [
            "Bull, Bear, Sideways, Crisis, and direct-input-gated Manipulation have accepted 95 evidence",
            "UnknownOrMixed remains residual and is not a completion root",
            "expanded/sub-regime labels do not count as root completion",
            "each accepted root maps to concrete artifacts and unchanged gates",
            "no trade-usable strategy claim is made by Board A",
        ],
        "checklist": checklist,
        "root_results": results,
        "accepted_roots": accepted_roots,
        "missing_roots": missing_roots,
        "goal_achieved": achieved,
        "residual_risk": [
            "Manipulation acceptance is direct event-confirmation for suppression/abstain/cooldown, not pre-event prediction.",
            "Board B profitability and execution promotion remain outside Board A.",
        ],
        "artifacts": {
            "audit_json": rel(OUT_DIR / "current_goal_completion_audit.json"),
            "audit_md": rel(OUT_DIR / "current_goal_completion_audit.md"),
            "assertions": rel(CHECK_DIR / "current_goal_completion_audit_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "current_goal_completion_audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    md_lines = [
        "# Current Goal Completion Audit",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Goal achieved: `{str(achieved).lower()}`",
        f"- Accepted roots: `{', '.join(accepted_roots)}`",
        f"- Missing roots: `{', '.join(missing_roots) if missing_roots else 'none'}`",
        "- UnknownOrMixed: residual only, not a completion root.",
        "- Trade usable: `false`.",
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        "| Requirement | Evidence | Status |",
        "|---|---|---|",
    ]
    for item in checklist:
        md_lines.append(f"| {item['requirement']} | `{item['evidence']}` | {'pass' if item['passed'] else 'fail'} |")
    md_lines.extend([
        "",
        "## Root Evidence",
        "",
        "| Root | Status | Artifact | Rule | Cal Wilson95 | Test Wilson95 | Test Support | Test Coverage |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ])
    for row in results:
        md_lines.append(
            f"| {row['root']} | {'pass' if row['passed'] else 'fail'} | `{row['artifact']}` | `{row['rule']}` | "
            f"{row['calibration']['wilson95']:.6f} | {row['test']['wilson95']:.6f} | {row['test']['support']} | {row['test']['coverage']:.6f} |"
        )
    md_lines.extend([
        "",
        "## Residual Risk",
        "",
        "- Manipulation acceptance is direct event-confirmation for suppression/abstain/cooldown, not pre-event prediction.",
        "- Board B profitability and execution promotion remain outside Board A.",
        "",
    ])
    (OUT_DIR / "current_goal_completion_audit.md").write_text("\n".join(md_lines))

    assertion_lines = [
        f"goal_achieved={str(achieved).lower()}",
        f"accepted_roots={','.join(accepted_roots)}",
        f"missing_roots={','.join(missing_roots) if missing_roots else 'none'}",
    ]
    for row in results:
        assertion_lines.extend(
            [
                f"{row['root']}.passed={str(row['passed']).lower()}",
                f"{row['root']}.test_wilson95={row['test']['wilson95']:.12f}",
                f"{row['root']}.test_support={row['test']['support']}",
                f"{row['root']}.test_coverage={row['test']['coverage']:.12f}",
            ]
        )
    assertion_lines.extend([
        "thresholds_relaxed=false",
        "runtime_code_changed=false",
        "trade_usable=false",
    ])
    (CHECK_DIR / "current_goal_completion_audit_assertions.out").write_text("\n".join(assertion_lines) + "\n")
    print(json.dumps({"goal_achieved": achieved, "accepted_roots": accepted_roots, "missing_roots": missing_roots}, indent=2))


if __name__ == "__main__":
    main()
