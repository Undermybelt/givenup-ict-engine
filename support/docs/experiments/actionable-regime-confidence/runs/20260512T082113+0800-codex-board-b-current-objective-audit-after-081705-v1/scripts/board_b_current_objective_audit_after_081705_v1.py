#!/usr/bin/env python3
"""Board B current-objective audit after 081705.

Reads current board state plus the latest route assertion files and writes a
prompt-to-artifact checklist. This is an audit artifact only; it does not run
AutoQuant, mutate state, or promote candidates.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260512T082113+0800-codex-board-b-current-objective-audit-after-081705-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / "board-b-current-objective-audit-after-081705-v1"
CHECK_DIR = RUN_ROOT / "checks"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"
BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

ROUTES = [
    {
        "id": "081025_r6_direct_intake_approval_gap",
        "assertions": REPO
        / "docs/experiments/actionable-regime-confidence/runs/20260512T081025+0800-codex-r6-direct-intake-approval-gap-readback-after-080950-v1/checks/r6_direct_intake_approval_gap_readback_after_080950_v1_assertions.out",
        "gate": "direct_intake_present_but_no_r6_owner_export_or_approval_unlock",
    },
    {
        "id": "081149_r6_public_docket_attachment_route",
        "assertions": REPO
        / "docs/experiments/actionable-regime-confidence/runs/20260512T081149+0800-codex-r6-public-docket-attachment-route-probe-after-080700-v1/checks/r6_public_docket_attachment_route_probe_after_080700_v1_assertions.out",
        "gate": "no_public_docket_attachment_control_unlock",
    },
    {
        "id": "081152_post_080906_source_control_consistency",
        "assertions": REPO
        / "docs/experiments/actionable-regime-confidence/runs/20260512T081152+0800-codex-post-080906-source-control-root-consistency-v1/checks/post_080906_source_control_root_consistency_v1_assertions.out",
        "gate": "no_required_source_control_unlock",
    },
    {
        "id": "081155_source_control_arrival_poll",
        "assertions": REPO
        / "docs/experiments/actionable-regime-confidence/runs/20260512T081155+0800-codex-source-control-arrival-poll-after-080837-v1/checks/source_control_arrival_poll_after_080837_v1_assertions.out",
        "gate": "no_new_required_root_no_unlock",
    },
    {
        "id": "081227_current_objective_audit_after_080906",
        "assertions": REPO
        / "docs/experiments/actionable-regime-confidence/runs/20260512T081227+0800-codex-current-objective-audit-after-080906-v1/checks/current_objective_audit_after_080906_v1_assertions.out",
        "gate": "not_complete_latest_public_routes_no_required_unlock_no_downstream_promotion",
    },
    {
        "id": "081323_courtlistener_recap_sibling_attachment",
        "assertions": REPO
        / "docs/experiments/actionable-regime-confidence/runs/20260512T081323+0800-codex-courtlistener-recap-sibling-attachment-probe-after-080906-v1/checks/courtlistener_recap_sibling_attachment_probe_after_080906_v1_assertions.out",
        "gate": "no_new_public_control_attachment_unlock",
    },
    {
        "id": "081522_r6_courtlistener_recap_control_route",
        "assertions": REPO
        / "docs/experiments/actionable-regime-confidence/runs/20260512T081522+0800-codex-r6-courtlistener-recap-control-route-after-080950-v1/checks/r6_courtlistener_recap_control_route_after_080950_v1_assertions.out",
        "gate": "public_recap_positive_and_context_only_no_source_owned_normal_controls",
    },
    {
        "id": "081705_courtlistener_recap_sibling_fast",
        "assertions": REPO
        / "docs/experiments/actionable-regime-confidence/runs/20260512T081705+0800-codex-courtlistener-recap-sibling-fast-probe-after-081323-v1/checks/courtlistener_recap_sibling_fast_probe_after_081323_v1_assertions.out",
        "gate": "no_new_public_control_attachment_unlock",
    },
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_assertions(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        out["missing"] = "true"
        return out
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip()
        elif line.startswith("PASS "):
            out["pass"] = line[5:].strip()
    return out


def yes_no(value: object) -> str:
    return str(value).lower()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    board_text = BOARD_B.read_text()
    route_rows = []
    missing_assertions = []
    for route in ROUTES:
        parsed = parse_assertions(route["assertions"])
        if parsed.get("missing") == "true":
            missing_assertions.append(route["id"])
        route_rows.append(
            {
                "route": route["id"],
                "gate": parsed.get("gate") or parsed.get("gate_result") or route["gate"],
                "valid_required_root_unlock": parsed.get("valid_required_root_unlock", "false"),
                "source_control_evidence_acquired": parsed.get("source_control_evidence_acquired", "false"),
                "accepted_rows_added": parsed.get("accepted_rows_added", "0"),
                "promotion_allowed": parsed.get("promotion_allowed", "false"),
                "update_goal": parsed.get("update_goal", "false"),
                "assertions": str(route["assertions"].relative_to(REPO)),
            }
        )

    required_markers = [
        "count_once:081323_courtlistener_recap_sibling_attachment_probe_after_080906",
        "count_once:081522_r6_courtlistener_recap_control_route_after_080950",
        "count_once:081705_courtlistener_recap_sibling_fast_probe_after_081323",
    ]
    missing_board_markers = [marker for marker in required_markers if marker not in board_text]
    explicit_user_selected_history = any(
        phrase in board_text
        for phrase in [
            "explicit_user_selected_history_present=true",
            "user_selected_history_present=true",
            "user selected exactly one historical path",
        ]
    )

    checklist = [
        {
            "requirement": "Board B markdown is the active contract",
            "status": "covered",
            "evidence": str(BOARD_B.relative_to(REPO)),
            "blocker": "",
        },
        {
            "requirement": "Profitability factors must be rooted in accepted regime-identification roots",
            "status": "blocked",
            "evidence": "081025/081149/081152/081155/081227/081323/081522/081705 assertion files all remain no-unlock or not-complete",
            "blocker": "valid_required_root_unlock=false; source_control_evidence_acquired=false",
        },
        {
            "requirement": "Preserve branch path main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor through filter/Pre-Bayes/BBN/CatBoost/execution tree",
            "status": "partial_fail_closed",
            "evidence": "Prior branch artifacts exist, but latest source/control gates forbid canonical merge and downstream rerun",
            "blocker": "canonical_merge=false; downstream_promotion_rerun=false",
        },
        {
            "requirement": "Operate AutoQuant and ict-engine through filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution tree on real artifacts",
            "status": "partial_fail_closed",
            "evidence": "Prior real-chain readbacks exist; selected-data AutoQuant promotion remains false in latest gates",
            "blocker": "selected_data_autoquant_promotion=false and downstream_promotion_rerun=false",
        },
        {
            "requirement": "Use IBKR, TradingViewRemix, yfinance, and Kraken visibly",
            "status": "partial_non_promoting",
            "evidence": "Prior provider/runtime readbacks cover provider surfaces diagnostically",
            "blocker": "provider diagnostics are not accepted source/control evidence",
        },
        {
            "requirement": "Continue source/control acquisition without promoting proxies",
            "status": "covered_fail_closed",
            "evidence": "Latest CourtListener/RECAP probes 081323, 081522, 081705 are counted as fail-closed",
            "blocker": "",
        },
        {
            "requirement": "Do not disturb concurrent multi-agent board work",
            "status": "covered",
            "evidence": "Audit is an additive run root; board markers are checked before mirroring",
            "blocker": "",
        },
        {
            "requirement": "Require exactly one explicit user-selected historical path HTF/MTF/LTF before selected-data factor research",
            "status": "blocked",
            "evidence": "No explicit user-selected history marker found in current Board B text",
            "blocker": "user_selected_historical_data_missing",
        },
        {
            "requirement": "Do not run selected-data AutoQuant or downstream promotion before both gates pass",
            "status": "blocked",
            "evidence": "Latest assertion files report selected_data_autoquant_promotion=false and downstream_promotion_rerun=false",
            "blocker": "source/control unlock and selected-history gates are both unsatisfied",
        },
        {
            "requirement": "Do not call update_goal before the objective is actually complete",
            "status": "blocked",
            "evidence": "Latest assertion files report strict_full_objective=false and update_goal=false",
            "blocker": "objective incomplete",
        },
    ]

    blocked = sum(1 for row in checklist if row["status"] == "blocked")
    partial = sum(1 for row in checklist if row["status"].startswith("partial"))
    covered = sum(1 for row in checklist if row["status"].startswith("covered"))
    gate_result = (
        "board_b_current_objective_audit_after_081705_v1="
        "not_complete_latest_recap_routes_no_required_unlock_no_selected_history_no_downstream_promotion"
    )
    decision = {
        "run_id": RUN_ID,
        "gate_result": gate_result,
        "board_b_hash": sha256(BOARD_B),
        "board_a_hash": sha256(BOARD_A),
        "blocked_requirements": blocked,
        "partial_requirements": partial,
        "covered_requirements": covered,
        "missing_assertion_files": missing_assertions,
        "missing_board_markers": missing_board_markers,
        "explicit_user_selected_history": explicit_user_selected_history,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
        "route_rows": route_rows,
        "checklist": checklist,
    }

    md = OUT_DIR / "board_b_current_objective_audit_after_081705_v1.md"
    js = OUT_DIR / "board_b_current_objective_audit_after_081705_v1.json"
    csv_path = OUT_DIR / "prompt_to_artifact_checklist_after_081705_v1.csv"
    assertions = CHECK_DIR / "board_b_current_objective_audit_after_081705_v1_assertions.out"

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["requirement", "status", "evidence", "blocker"])
        writer.writeheader()
        writer.writerows(checklist)

    js.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n")

    rows_md = "\n".join(
        f"| `{row['requirement']}` | `{row['status']}` | {row['evidence']} | {row['blocker']} |"
        for row in checklist
    )
    route_md = "\n".join(
        f"| `{row['route']}` | `{row['gate']}` | `{row['valid_required_root_unlock']}` | `{row['source_control_evidence_acquired']}` | `{row['accepted_rows_added']}` | `{row['update_goal']}` |"
        for row in route_rows
    )
    md.write_text(
        f"""# Board B Current Objective Audit After 081705 v1

Run id: `{RUN_ID}`

Gate result: `{gate_result}`

## Objective Restatement

Board B must train profitability factors inside accepted regime-identification
roots, preserve the branch path `main_regime -> sub_regime ->
sub_sub_regime_or_profit_factor -> profit_factor`, and only continue through
selected-data AutoQuant plus filter / Pre-Bayes -> BBN -> CatBoost/path-ranking
-> execution tree after both gates are satisfied: a valid source/control unlock
and exactly one explicit user-selected historical path (`HTF`, `MTF`, or `LTF`).

## Prompt-to-Artifact Checklist

| Requirement | Status | Evidence | Blocker |
|---|---|---|---|
{rows_md}

## Latest Route Readbacks

| Route | Gate | Valid root unlock | Source/control acquired | Accepted rows | update_goal |
|---|---|---|---|---|---|
{route_md}

## Decision

- Blocked requirements: `{blocked}`; partial requirements: `{partial}`; covered requirements: `{covered}`.
- Missing assertion files: `{','.join(missing_assertions) if missing_assertions else 'none'}`.
- Missing Board B count markers: `{','.join(missing_board_markers) if missing_board_markers else 'none'}`.
- Latest CourtListener/RECAP route probes through `081705` add `0` accepted rows and no required source/control unlock.
- R6 owner/export remains absent or incomplete, R5 post-cutoff recency remains absent, and R3 native-subhour Crisis remains absent.
- Explicit user-selected history remains absent; selected-data AutoQuant promotion and downstream rerun remain blocked.
- `valid_required_root_unlock=false`; `source_control_evidence_acquired=false`; `canonical_merge=false`; `selected_data_autoquant_promotion=false`; `downstream_promotion_rerun=false`; `strict_full_objective=false`; `trade_usable=false`; `promotion_allowed=false`; `update_goal=false`.

## Artifacts

- JSON: `{js.relative_to(REPO)}`
- Checklist CSV: `{csv_path.relative_to(REPO)}`
- Assertions: `{assertions.relative_to(REPO)}`

## Next

Continue source/control acquisition only, or obtain exactly one explicit
user-selected historical path (`HTF`, `MTF`, or `LTF`) for non-promotional
factor research. Do not run selected-data AutoQuant or the ordered filter /
Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree chain until both
the source/control unlock gate and selected-history gate are satisfied.
"""
    )
    assertions.write_text(
        "\n".join(
            [
                f"gate_result={gate_result}",
                f"blocked_requirements={blocked}",
                f"partial_requirements={partial}",
                f"covered_requirements={covered}",
                f"missing_assertion_files={','.join(missing_assertions) if missing_assertions else 'none'}",
                f"missing_board_markers={','.join(missing_board_markers) if missing_board_markers else 'none'}",
                f"explicit_user_selected_history={yes_no(explicit_user_selected_history)}",
                "accepted_rows_added=0",
                "valid_required_root_unlock=false",
                "source_control_evidence_acquired=false",
                "canonical_merge=false",
                "selected_data_autoquant_promotion=false",
                "downstream_promotion_rerun=false",
                "strict_full_objective=false",
                "trade_usable=false",
                "promotion_allowed=false",
                "update_goal=false",
                "",
            ]
        )
    )


if __name__ == "__main__":
    main()
