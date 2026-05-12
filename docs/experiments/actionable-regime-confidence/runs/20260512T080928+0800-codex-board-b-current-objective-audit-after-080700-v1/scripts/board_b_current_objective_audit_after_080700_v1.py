#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T080928+0800-codex-board-b-current-objective-audit-after-080700-v1"
SLUG = "board-b-current-objective-audit-after-080700-v1"
GATE_RESULT = (
    "board_b_current_objective_audit_after_080700_v1="
    "not_complete_no_source_control_unlock_no_selected_history_no_downstream_promotion"
)

REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_ROOT = RUN_ROOT / SLUG
CHECK_ROOT = RUN_ROOT / "checks"
BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"

EVIDENCE = {
    "080054": "docs/experiments/actionable-regime-confidence/runs/20260512T080054+0800-codex-current-objective-audit-after-075828-v1/checks/current_objective_audit_after_075828_v1_assertions.out",
    "080333": "docs/experiments/actionable-regime-confidence/runs/20260512T080333+0800-codex-openml-dataverse-source-route-probe-after-075932-v1/checks/openml_dataverse_source_route_probe_after_075932_v1_assertions.out",
    "080336": "docs/experiments/actionable-regime-confidence/runs/20260512T080336+0800-codex-source-control-arrival-poll-after-080054-v1/checks/source_control_arrival_poll_after_080054_v1_assertions.out",
    "080411": "docs/experiments/actionable-regime-confidence/runs/20260512T080411+0800-codex-r6-regulator-exchange-source-route-probe-after-080054-v1/checks/r6_regulator_exchange_source_route_probe_after_080054_v1_assertions.out",
    "080425": "docs/experiments/actionable-regime-confidence/runs/20260512T080425+0800-codex-target-root-approval-readback-after-075925-v1/checks/target_root_approval_readback_after_075925_v1_assertions.out",
    "080446": "docs/experiments/actionable-regime-confidence/runs/20260512T080446+0800-codex-required-root-arrival-poll-after-080054-v1/checks/required_root_arrival_poll_after_080054_v1_assertions.out",
    "080452": "docs/experiments/actionable-regime-confidence/runs/20260512T080452+0800-codex-dryad-source-route-probe-after-080054-v1/checks/dryad_source_route_probe_after_080054_v1_assertions.out",
    "080700": "docs/experiments/actionable-regime-confidence/runs/20260512T080700+0800-codex-openml-dryad-mendeley-exact-web-search-after-080054-v1/checks/openml_dryad_mendeley_exact_web_search_after_080054_v1_assertions.out",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_assertions(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_ROOT.mkdir(parents=True, exist_ok=True)

    evidence_values = {
        key: read_assertions(REPO / rel_path)
        for key, rel_path in EVIDENCE.items()
    }

    checklist = [
        {
            "requirement": "Use Board B markdown as active contract",
            "status": "covered",
            "evidence": str(BOARD_B),
            "blocker": "",
        },
        {
            "requirement": "Profitability-factor training rooted in accepted regime-identification roots",
            "status": "blocked",
            "evidence": "080054/080336/080425/080446 all report valid_required_root_unlock=false",
            "blocker": "No valid R3/R5/R6 source-control root or approval unlock",
        },
        {
            "requirement": "Preserve branch path through filter, BBN, CatBoost/path-ranking, and execution tree",
            "status": "partial_fail_closed",
            "evidence": "Prior 075108/080413 readbacks preserved branch labels but downstream stayed blocked/observe-only",
            "blocker": "Downstream promotion forbidden until source/control and selected-history gates pass",
        },
        {
            "requirement": "Personally operate AutoQuant and ict-engine chain on real artifacts",
            "status": "partial_fail_closed",
            "evidence": "Prior readbacks exercised provider/AutoQuant/pre-Bayes/workflow/path-ranking surfaces",
            "blocker": "Selected-data AutoQuant and promotion rerun remain blocked",
        },
        {
            "requirement": "Use IBKR, TradingViewRemix, yfinance, and Kraken visibly",
            "status": "partial_non_promoting",
            "evidence": "Prior 075108/075420 provider/cache readbacks covered these surfaces diagnostically",
            "blocker": "Provider visibility did not produce accepted source/control evidence",
        },
        {
            "requirement": "Continue source/control acquisition without promoting proxies",
            "status": "covered_fail_closed",
            "evidence": "080333/080411/080452/080700 route probes all no_unlock",
            "blocker": "",
        },
        {
            "requirement": "Explicit user-selected historical path before selected-data factor research",
            "status": "blocked",
            "evidence": "No explicit HTF/MTF/LTF selection found in latest Board B tail",
            "blocker": "user_selected_historical_data_missing",
        },
        {
            "requirement": "Canonical merge / selected-data AutoQuant / downstream promotion",
            "status": "blocked",
            "evidence": "080425 approval_present=false; canonical_merge_allowed_now=false; downstream_rerun_allowed_now=false",
            "blocker": "source_control_unlock_absent",
        },
    ]

    blocked = sum(1 for row in checklist if row["status"] == "blocked")
    partial = sum(1 for row in checklist if row["status"].startswith("partial"))
    decision = {
        "accepted_rows_added": 0,
        "blocked_requirements": blocked,
        "partial_requirements": partial,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "explicit_user_selected_history_present": False,
        "gate_result": GATE_RESULT,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_allowed": False,
        "selected_data_autoquant_run": False,
        "selected_data_autoquant_promotion": False,
        "source_control_evidence_acquired": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
        "valid_required_root_unlock": False,
    }
    payload = {
        "run_id": RUN_ID,
        "board_hash_before_artifact": {
            "board_a": sha256_file(BOARD_A),
            "board_b": sha256_file(BOARD_B),
        },
        "evidence_assertions": evidence_values,
        "checklist": checklist,
        "decision": decision,
    }

    json_path = OUT_ROOT / "board_b_current_objective_audit_after_080700_v1.json"
    csv_path = OUT_ROOT / "prompt_to_artifact_checklist_after_080700_v1.csv"
    md_path = OUT_ROOT / "board_b_current_objective_audit_after_080700_v1.md"
    assertions_path = CHECK_ROOT / "board_b_current_objective_audit_after_080700_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["requirement", "status", "evidence", "blocker"])
        writer.writeheader()
        writer.writerows(checklist)

    md_lines = [
        "# Board B Current Objective Audit After 080700 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE_RESULT}`",
        "",
        "## Objective Restatement",
        "",
        "Board B must train and evaluate profitability factors inside accepted Board A regime roots, preserve the branch path `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`, and only continue through selected-data AutoQuant plus filter / Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree when source/control and selected-history gates are satisfied.",
        "",
        "## Prompt-to-Artifact Checklist",
        "",
        "| Requirement | Status | Evidence | Blocker |",
        "|---|---|---|---|",
    ]
    for row in checklist:
        md_lines.append(
            f"| {row['requirement']} | {row['status']} | {row['evidence']} | {row['blocker']} |"
        )
    md_lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Blocked requirements: `{blocked}`; partial requirements: `{partial}`.",
            "- Latest post-080054 source/control route probes and root-readbacks add no accepted rows and do not unlock R3/R5/R6.",
            "- Explicit user-selected history remains absent, so selected-data factor research and promotion remain blocked.",
            "- `valid_required_root_unlock=false`; `source_control_evidence_acquired=false`; `canonical_merge=false`; `selected_data_autoquant_promotion=false`; `downstream_promotion_rerun=false`; `trade_usable=false`; `update_goal=false`.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Checklist CSV: `{csv_path}`",
            f"- Assertions: `{assertions_path}`",
            "",
            "## Next",
            "",
            "Continue source/control acquisition only unless the user explicitly selects exactly one historical path, `HTF`, `MTF`, or `LTF`, for non-promotional factor research. Do not run selected-data AutoQuant or downstream promotion until both gates are satisfied.",
            "",
        ]
    )
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    assertions = [
        f"gate_result={GATE_RESULT}",
        f"blocked_requirements={blocked}",
        f"partial_requirements={partial}",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "explicit_user_selected_history_present=false",
        "selected_data_autoquant_run=false",
        "selected_data_autoquant_promotion=false",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "promotion_allowed=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
