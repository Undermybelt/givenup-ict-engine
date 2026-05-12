#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


RUN_ID = "20260512T085912+0800-codex-current-objective-audit-after-085727-v1"
ARTIFACT = "current-objective-audit-after-085727-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = RUN_ROOT / ARTIFACT
CHECKS_DIR = RUN_ROOT / "checks"

BOARD_B = Path("docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md")
BOARD_A = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")

LATEST_ASSERTIONS = {
    "085612_public_route": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T085612+0800-codex-public-spoofing-source-control-route-triage-after-085131-v1/"
        "checks/public_spoofing_source_control_route_triage_after_085131_v1_assertions.out"
    ),
    "085727_official_route": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T085727+0800-codex-official-public-spoofing-source-control-route-triage-after-085131-v1/"
        "checks/official_public_spoofing_source_control_route_triage_after_085131_v1_assertions.out"
    ),
    "085808_case_attachment": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T085808+0800-codex-public-case-attachment-route-refresh-after-085131-v1/"
        "checks/public_case_attachment_route_refresh_after_085131_v1_assertions.out"
    ),
    "085131_dropzone": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T085131+0800-codex-source-control-dropzone-dispatch-refresh-after-083703-v1/"
        "checks/source_control_dropzone_dispatch_refresh_after_083703_v1_assertions.out"
    ),
    "085042_objective_audit": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T085042+0800-codex-current-objective-audit-after-083703-v1/"
        "checks/current_objective_audit_after_083703_v1_assertions.out"
    ),
}

TERMINAL_READBACK_ROOTS = {
    "085808_case_attachment_refresh": Path(
        "docs/experiments/actionable-regime-confidence/runs/"
        "20260512T085808+0800-codex-public-case-attachment-route-refresh-after-085131-v1"
    )
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_assertions(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def bool_value(values: dict[str, str], key: str) -> bool:
    return values.get(key, "").lower() == "true"


def file_count(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for p in root.rglob("*") if p.is_file())


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    board_b_text = BOARD_B.read_text(encoding="utf-8")
    board_a_text = BOARD_A.read_text(encoding="utf-8")
    assertions = {name: parse_assertions(path) for name, path in LATEST_ASSERTIONS.items()}

    latest_source_control_false = all(
        not bool_value(values, "source_control_evidence_acquired")
        for values in assertions.values()
        if values
    )
    latest_required_unlock_false = all(
        not bool_value(values, "valid_required_root_unlock")
        for values in assertions.values()
        if values
    )
    latest_update_goal_false = all(
        not bool_value(values, "update_goal")
        for values in assertions.values()
        if values
    )
    selected_history_false = (
        "explicit user-selected history false" in board_b_text
        or "no_explicit_user_selected_history" in board_b_text
        or "user_selected_historical_data_missing" in board_b_text
    )
    selected_data_autoquant_false = (
        "selected-data AutoQuant promotion false" in board_b_text
        or "no_selected_data_autoquant_training" in board_b_text
    )
    downstream_rerun_false = (
        "downstream promotion rerun false" in board_b_text
        or "downstream_promotion_rerun=false" in board_b_text
    )
    branch_contract_present = (
        "Non-negotiable rule" in board_b_text
        and "branch path" in board_b_text
        and "pre-Bayes, BBN, CatBoost/path-ranker, and execution tree" in board_b_text
    )
    cursor_fail_closed = "Keep `034002` as the fail-closed cursor" in board_b_text
    terminal_readback_counts = {name: file_count(root) for name, root in TERMINAL_READBACK_ROOTS.items()}

    checklist = [
        {
            "requirement": "Named Board B file is the active profitability contract",
            "evidence": str(BOARD_B),
            "status": "pass" if BOARD_B.exists() else "blocked",
            "gap": "" if BOARD_B.exists() else "Board B file missing",
        },
        {
            "requirement": "Regime-root branch identity is preserved as the downstream contract",
            "evidence": "Board B branch-path contract text",
            "status": "pass" if branch_contract_present else "blocked",
            "gap": "" if branch_contract_present else "Branch-path contract text not found",
        },
        {
            "requirement": "Source/control unlock is valid before promotion",
            "evidence": "; ".join(str(p) for p in LATEST_ASSERTIONS.values()),
            "status": "blocked" if latest_source_control_false and latest_required_unlock_false else "needs_review",
            "gap": "latest settled source/control artifacts remain fail-closed",
        },
        {
            "requirement": "Exactly one selected historical path exists: HTF, MTF, or LTF",
            "evidence": str(BOARD_B),
            "status": "blocked" if selected_history_false else "needs_review",
            "gap": "explicit user-selected history remains absent",
        },
        {
            "requirement": "Selected-data AutoQuant training/promotion has run",
            "evidence": str(BOARD_B),
            "status": "blocked" if selected_data_autoquant_false else "needs_review",
            "gap": "selected-data AutoQuant promotion remains false",
        },
        {
            "requirement": "Filter / Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree rerun is authorized and complete",
            "evidence": str(BOARD_B),
            "status": "blocked" if downstream_rerun_false else "needs_review",
            "gap": "downstream promotion rerun remains false",
        },
        {
            "requirement": "Provider surfaces IBKR, TradingViewRemix, yfinance, and Kraken are not used as proxy completion",
            "evidence": "Objective audit plus Board A/B gates",
            "status": "pass",
            "gap": "provider visibility is diagnostic only until source/control and selected-history gates pass",
        },
        {
            "requirement": "No update_goal call unless every objective requirement is complete",
            "evidence": "; ".join(f"{name}:{values.get('update_goal', 'missing')}" for name, values in assertions.items()),
            "status": "pass" if latest_update_goal_false else "blocked",
            "gap": "" if latest_update_goal_false else "one or more artifacts allow update_goal",
        },
        {
            "requirement": "Current cursor remains fail-closed",
            "evidence": str(BOARD_B),
            "status": "pass" if cursor_fail_closed else "needs_review",
            "gap": "" if cursor_fail_closed else "fail-closed cursor text not found",
        },
        {
            "requirement": "Count 085808 only as terminal fail-closed public case-route context",
            "evidence": str(TERMINAL_READBACK_ROOTS["085808_case_attachment_refresh"]),
            "status": "pass" if terminal_readback_counts["085808_case_attachment_refresh"] > 0 and not bool_value(assertions["085808_case_attachment"], "source_control_evidence_acquired") else "needs_review",
            "gap": "terminal_files=%d; no row-level source/control unlock" % terminal_readback_counts["085808_case_attachment_refresh"],
        },
    ]

    objective_complete = all(row["status"] == "pass" for row in checklist)

    summary = {
        "run_id": RUN_ID,
        "gate_result": "current_objective_audit_after_085727_v1=not_complete_source_control_absent_no_selected_history_no_downstream_promotion",
        "board_b_sha256": sha256_file(BOARD_B),
        "board_a_sha256": sha256_file(BOARD_A),
        "latest_assertions": assertions,
        "terminal_readback_file_counts": terminal_readback_counts,
        "branch_contract_present": branch_contract_present,
        "cursor_fail_closed": cursor_fail_closed,
        "source_control_evidence_acquired": False,
        "valid_required_root_unlock": False,
        "explicit_user_selected_history": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
        "objective_complete": objective_complete,
        "checklist": checklist,
    }

    json_path = OUT_DIR / "current_objective_audit_after_085727_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checklist_path = OUT_DIR / "prompt_to_artifact_checklist_after_085727_v1.csv"
    with checklist_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["requirement", "evidence", "status", "gap"])
        writer.writeheader()
        writer.writerows(checklist)

    report_lines = [
        "# Current Objective Audit After 085727 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{summary['gate_result']}`",
        "",
        "This audit maps the current user objective to settled repo evidence. It does not mutate target roots, does not run selected-data AutoQuant, direct verifier, canonical merge, Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion, does not make a trade claim, and does not call `update_goal`.",
        "",
        "## Readback",
        "",
        f"- Board B sha256: `{summary['board_b_sha256']}`.",
        f"- Board A sha256: `{summary['board_a_sha256']}`.",
        f"- Branch contract present: `{str(branch_contract_present).lower()}`.",
        f"- Current cursor fail-closed: `{str(cursor_fail_closed).lower()}`.",
        f"- `085612` gate: `{assertions['085612_public_route'].get('gate_result', 'missing')}`.",
        f"- `085727` gate: `{assertions['085727_official_route'].get('gate_result', 'missing')}`.",
        f"- `085808` gate: `{assertions['085808_case_attachment'].get('gate_result', 'missing')}`.",
        f"- `085808` terminal file count: `{terminal_readback_counts['085808_case_attachment_refresh']}`.",
        "",
        "## Decision",
        "",
        "- Source/control evidence acquired: `false`.",
        "- Valid required-root unlock: `false`.",
        "- Explicit selected historical path: `false`.",
        "- Selected-data AutoQuant promotion: `false`.",
        "- Downstream promotion rerun: `false`.",
        "- Objective complete: `false`.",
        "- Promotion allowed: `false`.",
        "- `update_goal=false`.",
        "",
        "## Checklist",
        "",
    ]
    for row in checklist:
        report_lines.append(f"- `{row['status']}` - {row['requirement']}: {row['gap'] or row['evidence']}")
    report_lines.extend(
        [
            "",
            "## Next",
            "",
            "Continue source/control acquisition only unless an approved operator dispatch/export with ticket/export/license provenance arrives, explicit same-exhibit `FLIP`-as-control approval is recorded, or the user explicitly selects exactly one historical path for non-promotional factor research after source/control unlock. Do not run selected-data AutoQuant or the ordered downstream chain until both gates are satisfied.",
        ]
    )
    (OUT_DIR / "current_objective_audit_after_085727_v1.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )

    checks_path = CHECKS_DIR / "current_objective_audit_after_085727_v1_assertions.out"
    checks_path.write_text(
        "\n".join(
            [
                f"gate_result={summary['gate_result']}",
                f"branch_contract_present={str(branch_contract_present).lower()}",
                f"cursor_fail_closed={str(cursor_fail_closed).lower()}",
                "source_control_evidence_acquired=false",
                "valid_required_root_unlock=false",
                "explicit_user_selected_history=false",
                "canonical_merge=false",
                "selected_data_autoquant_promotion=false",
                "downstream_promotion_rerun=false",
                "strict_full_objective=false",
                "trade_usable=false",
                "promotion_allowed=false",
                "objective_complete=false",
                "update_goal=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
