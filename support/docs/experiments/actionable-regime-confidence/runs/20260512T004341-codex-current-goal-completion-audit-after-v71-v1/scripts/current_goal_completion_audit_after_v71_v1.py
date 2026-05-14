#!/usr/bin/env python3
"""Audit the active Board A objective after the V71 R6 control screens."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


RUN_ID = "20260512T004341-codex-current-goal-completion-audit-after-v71-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "current-goal-completion-audit-after-v71"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

R6_SCREEN_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T003909-codex-r6-oystacher-independent-normal-control-screen-v1"
    / "r6-oystacher-independent-normal-control-screen"
    / "r6_oystacher_independent_normal_control_screen_v1.json"
)
R6_ROUTE_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T003924-codex-r6-oystacher-owner-control-source-route-screen-v1"
    / "r6-oystacher-owner-control-source-route-screen"
    / "r6_oystacher_owner_control_source_route_screen_v1.json"
)
R6_PUBLIC_NORMAL_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1"
    / "r6-oystacher-public-normal-control-source-probe"
    / "r6_oystacher_public_normal_control_source_probe_v1.json"
)
R6_EXTERNAL_CONTROL_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T004322-codex-r6-oystacher-external-control-source-scan-v1"
    / "r6-oystacher-external-control-source-scan"
    / "r6_oystacher_external_control_source_scan_v1.json"
)
R6_OFFICIAL_ROUTE_REPORT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T004410-codex-r6-official-route-date-fit-check-v1"
    / "r6-official-route-date-fit-check"
    / "r6_official_route_date_fit_check_v1.md"
)
R6_OFFICIAL_ROUTE_CELLS = R6_OFFICIAL_ROUTE_REPORT.with_name("r6_official_route_date_fit_cells_v1.csv")
R6_OFFICIAL_ROUTE_SOURCES = R6_OFFICIAL_ROUTE_REPORT.with_name("r6_official_route_date_fit_sources_v1.csv")
R6_OFFICIAL_ROUTE_ASSERTIONS = (
    R6_OFFICIAL_ROUTE_REPORT.parents[1]
    / "checks"
    / "r6_official_route_date_fit_check_v1_assertions.out"
)
LOCAL_CONTROL_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T003811-codex-r6-oystacher-local-control-path-disposition-v1"
    / "r6-oystacher-local-control-path-disposition"
    / "r6_oystacher_local_control_path_disposition_v1.json"
)
PROVIDER_AQ_JSON = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T003800-codex-v65-provider-autoquant-readonly-refresh-v1"
    / "v65-provider-autoquant-readonly-refresh"
    / "v65_provider_autoquant_readonly_refresh_v1.json"
)

R6_TARGET_ROOT = Path("/tmp/ict-engine-board-a-r6-owner-export-v1")
NON_R6_ROOTS = {
    "source_label_equivalence": Path("/tmp/ict-engine-source-label-equivalence-intake"),
    "native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "r5_source_panel_recency": Path("/tmp/ict-engine-source-panel-recency-extension"),
}
R6_REQUIRED_FILES = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
    "source_policy_approval.json",
    "control_policy_approval.json",
    "owner_approval_reference.md",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def cursor_value(board_text: str, field: str) -> str:
    pattern = rf"^\| {re.escape(field)} \| (.*?) \|"
    for line in board_text.splitlines():
        match = re.match(pattern, line)
        if match:
            return match.group(1)
    return ""


def root_state(root: Path, required_files: list[str] | None = None) -> dict[str, Any]:
    required_files = required_files or []
    return {
        "path": str(root),
        "exists": root.exists(),
        "required_files_present": {
            name: (root / name).exists() for name in required_files
        },
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text(encoding="utf-8")
    board_hash = sha256(BOARD)
    r6_screen = load_json(R6_SCREEN_JSON)
    r6_route = load_json(R6_ROUTE_JSON)
    r6_public_normal = load_json(R6_PUBLIC_NORMAL_JSON)
    r6_external_control = load_json(R6_EXTERNAL_CONTROL_JSON)
    r6_official_cells = read_csv(R6_OFFICIAL_ROUTE_CELLS)
    r6_official_sources = read_csv(R6_OFFICIAL_ROUTE_SOURCES)
    local_control = load_json(LOCAL_CONTROL_JSON)
    provider_aq = load_json(PROVIDER_AQ_JSON)

    r6_target_state = root_state(R6_TARGET_ROOT, R6_REQUIRED_FILES)
    non_r6_root_states = {name: root_state(path) for name, path in NON_R6_ROOTS.items()}

    current_cursor = {
        "board_state": cursor_value(board_text, "board_state"),
        "last_loop_id": cursor_value(board_text, "last_loop_id"),
        "current_run_root": cursor_value(board_text, "current_run_root"),
        "accepted_gate": cursor_value(board_text, "accepted_gate"),
        "blocker": cursor_value(board_text, "blocker"),
        "next_action": cursor_value(board_text, "next_action"),
    }

    checklist = [
        {
            "requirement": "Use the named Board A markdown as the authoritative shared board.",
            "status": "pass",
            "evidence": f"{BOARD.relative_to(REPO)} sha256={board_hash} cursor={current_cursor['last_loop_id']}",
            "gap": "",
        },
        {
            "requirement": "Every regime has a regime-specific 95% confidence packet.",
            "status": "blocked",
            "evidence": f"board_state={current_cursor['board_state']}; full_objective_gate remains none in accepted_gate",
            "gap": "Not every active regime/root has an accepted 95% packet.",
        },
        {
            "requirement": "Validate accepted confidence across other markets and periods/timeframes.",
            "status": "blocked",
            "evidence": "V71 R6 still lacks valid controls/canonical merge; R5/R3/source-label roots absent.",
            "gap": "Cross-axis validation cannot close until source/control evidence and non-R6 roots are present.",
        },
        {
            "requirement": "R6 direct Manipulation has accepted positives plus source-owned normal controls.",
            "status": "blocked",
            "evidence": (
                f"SPOOF positives={r6_screen['row_counts']['positive_spoof_candidates']}; "
                f"independent_normal_rows={r6_screen['row_counts']['independent_normal_rows']}; "
                f"valid_normal_controls_acquired={r6_route['valid_normal_controls_acquired']}; "
                f"public_source_owned_controls={r6_public_normal['valid_source_owned_normal_controls_found']}; "
                f"external_verifier_ready_controls={r6_external_control['verifier_ready_source_owned_normal_controls_found']}; "
                f"official_cells_controls_not_acquired={sum(1 for row in r6_official_cells if row['decision'] == 'controls_not_acquired')}"
            ),
            "gap": "FLIP controls are not approved and independent source-owned normal controls are absent.",
        },
        {
            "requirement": "Owner-export/canonical intake root is ready before downstream rerun.",
            "status": "blocked",
            "evidence": json.dumps(r6_target_state, sort_keys=True),
            "gap": "Target root lacks verifier-native files plus source/control approvals.",
        },
        {
            "requirement": "Provider awareness includes IBKR, TradingViewRemix/MCP, yfinance, and Kraken.",
            "status": "partial",
            "evidence": (
                f"provider-summary={provider_aq['provider_summary_line']}; "
                f"selected={provider_aq['selected_provider_status']}"
            ),
            "gap": "Read-only readiness was refreshed; it is not a post-canonical-merge downstream rerun.",
        },
        {
            "requirement": "Auto-Quant is operated as part of the real chain.",
            "status": "partial",
            "evidence": (
                f"auto_quant_status={provider_aq['auto_quant_status_value']}; "
                f"healthy={provider_aq['auto_quant_healthy']}; data_ready={provider_aq['auto_quant_data_ready']}"
            ),
            "gap": "Auto-Quant is ready/data-ready but no accepted canonical input exists for a fresh chain rerun.",
        },
        {
            "requirement": "Filter/pre-Bayes/BBN readback runs after accepted evidence.",
            "status": "deferred_blocked",
            "evidence": "No post-V71 canonical merge; downstream_chain_rerun=false in current artifacts.",
            "gap": "No accepted input to justify a non-proxy BBN/pre-Bayes rerun.",
        },
        {
            "requirement": "CatBoost/path-ranking readback runs after accepted evidence.",
            "status": "deferred_blocked",
            "evidence": "No post-V71 canonical merge; downstream_chain_rerun=false in current artifacts.",
            "gap": "No accepted input to justify a non-proxy CatBoost/path-ranking rerun.",
        },
        {
            "requirement": "Execution-tree readback runs after accepted evidence.",
            "status": "deferred_blocked",
            "evidence": "No post-V71 canonical merge; downstream_chain_rerun=false in current artifacts.",
            "gap": "No accepted input to justify a non-proxy execution-tree rerun.",
        },
        {
            "requirement": "Source-label confidence closes rather than staying 0/4.",
            "status": "blocked",
            "evidence": json.dumps(non_r6_root_states["source_label_equivalence"], sort_keys=True),
            "gap": "Source-label equivalence intake root is absent/incomplete.",
        },
        {
            "requirement": "R5 post-2026-01-30 source-panel rows are present.",
            "status": "blocked",
            "evidence": json.dumps(non_r6_root_states["r5_source_panel_recency"], sort_keys=True),
            "gap": "R5 recency source-panel intake root is absent/incomplete.",
        },
        {
            "requirement": "R3 native-subhour source-label root is present.",
            "status": "blocked",
            "evidence": json.dumps(non_r6_root_states["native_subhour"], sort_keys=True),
            "gap": "R3 native-subhour intake root is absent/incomplete.",
        },
        {
            "requirement": "Multi-agent work is preserved without overwriting concurrent artifacts.",
            "status": "pass",
            "evidence": "Audit is additive under a unique run root and does not edit other run dirs.",
            "gap": "",
        },
        {
            "requirement": "No proxy signal is accepted as completion.",
            "status": "pass",
            "evidence": "All proxy/deferred states remain blocked; trade_usable=false; update_goal=false.",
            "gap": "",
        },
    ]

    strict_full_objective_achieved = False
    gate_result = (
        "current_goal_completion_audit_after_v71_v1="
        "not_complete_r6_controls_canonical_downstream_source_label_r5_r3_blocked"
    )
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "board_path": str(BOARD.relative_to(REPO)),
        "board_sha256_at_start": board_hash,
        "current_cursor": current_cursor,
        "r6_independent_normal_control_screen": str(R6_SCREEN_JSON.relative_to(REPO)),
        "r6_owner_control_source_route_screen": str(R6_ROUTE_JSON.relative_to(REPO)),
        "r6_public_normal_control_source_probe": str(R6_PUBLIC_NORMAL_JSON.relative_to(REPO)),
        "r6_external_control_source_scan": str(R6_EXTERNAL_CONTROL_JSON.relative_to(REPO)),
        "r6_official_route_date_fit_check": str(R6_OFFICIAL_ROUTE_REPORT.relative_to(REPO)),
        "r6_local_control_disposition": str(LOCAL_CONTROL_JSON.relative_to(REPO)),
        "provider_autoquant_refresh": str(PROVIDER_AQ_JSON.relative_to(REPO)),
        "r6_target_state": r6_target_state,
        "non_r6_root_states": non_r6_root_states,
        "checklist_status_counts": {
            status: sum(1 for row in checklist if row["status"] == status)
            for status in sorted({row["status"] for row in checklist})
        },
        "r6_valid_source_owned_normal_controls_found": local_control["valid_source_owned_normal_controls_found"],
        "r6_required_cells_still_short": local_control["required_cells_still_short"],
        "r6_official_source_routes_identified": r6_route["cells_with_candidate_source_route"],
        "r6_valid_normal_controls_acquired": r6_route["valid_normal_controls_acquired"],
        "r6_public_sources_checked": r6_public_normal["sources_checked"],
        "r6_public_source_owned_normal_controls_found": r6_public_normal["valid_source_owned_normal_controls_found"],
        "r6_public_control_shortfall": r6_public_normal["required_cells"]["required_cell_shortfall_total"],
        "r6_external_sources_checked": r6_external_control["external_sources_checked"],
        "r6_external_raw_routes_identified": r6_external_control["raw_data_routes_identified"],
        "r6_external_verifier_ready_controls_found": r6_external_control["verifier_ready_source_owned_normal_controls_found"],
        "r6_official_route_sources_checked": len(r6_official_sources),
        "r6_official_route_cells_checked": len(r6_official_cells),
        "r6_official_route_controls_not_acquired_cells": sum(
            1 for row in r6_official_cells if row["decision"] == "controls_not_acquired"
        ),
        "r6_official_route_cfe_depth_gap_cells": sum(
            1 for row in r6_official_cells if "cboe_cfe" in row["official_route"]
        ),
        "downstream_chain_rerun": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": strict_full_objective_achieved,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "gate_result": gate_result,
        "next_action": current_cursor["next_action"],
    }

    json_path = OUT / "current_goal_completion_audit_after_v71_v1.json"
    report_path = OUT / "current_goal_completion_audit_after_v71_v1.md"
    checklist_path = OUT / "prompt_to_artifact_checklist_after_v71_v1.csv"
    assertions_path = CHECKS / "current_goal_completion_audit_after_v71_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_path, checklist, ["requirement", "status", "evidence", "gap"])
    report_path.write_text(
        "\n".join(
            [
                "# Current Goal Completion Audit After V71 v1",
                "",
                f"- Run id: `{RUN_ID}`.",
                f"- Board cursor observed: `{current_cursor['last_loop_id']}`.",
                f"- Board hash observed before artifact creation: `{board_hash}`.",
                f"- Gate result: `{gate_result}`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
                "",
                "## Objective Restatement",
                "",
                "The active objective requires every accepted regime to reach regime-specific 95% confidence, validate across other markets and periods/timeframes, and be backed by real provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readbacks. The same board markdown must remain the shared source of truth and concurrent agents' artifacts must not be overwritten.",
                "",
                "## Evidence Readback",
                "",
                f"- Current cursor remains blocked at `{current_cursor['last_loop_id']}`.",
                f"- R6 independent normal-control screen: independent normal rows `{r6_screen['row_counts']['independent_normal_rows']}`; public probes `{len(r6_screen['public_source_probes'])}`; gate `{r6_screen['decision']['gate_result']}`.",
                f"- R6 owner-control source routes: candidate routes for `{r6_route['cells_with_candidate_source_route']}` cells, valid controls acquired `{r6_route['valid_normal_controls_acquired']}`.",
                f"- R6 public normal-control source probe: sources checked `{r6_public_normal['sources_checked']}`, valid public source-owned normal controls `{r6_public_normal['valid_source_owned_normal_controls_found']}`, total shortfall `{r6_public_normal['required_cells']['required_cell_shortfall_total']}`.",
                f"- R6 external control source scan: external sources checked `{r6_external_control['external_sources_checked']}`, raw routes identified `{r6_external_control['raw_data_routes_identified']}`, verifier-ready source-owned normal controls `{r6_external_control['verifier_ready_source_owned_normal_controls_found']}`.",
                f"- R6 official route date-fit check: sources checked `{len(r6_official_sources)}`, cells checked `{len(r6_official_cells)}`, controls-not-acquired cells `{sum(1 for row in r6_official_cells if row['decision'] == 'controls_not_acquired')}`.",
                f"- Local control disposition: local paths checked `{local_control['local_paths_checked']}`, valid source-owned controls `{local_control['valid_source_owned_normal_controls_found']}`, required cells still short `{local_control['required_cells_still_short']}`.",
                f"- Provider/Auto-Quant read-only refresh: `{provider_aq['provider_summary_line']}`; Auto-Quant `{provider_aq['auto_quant_status_value']}`.",
                f"- R6 target root state: `{json.dumps(r6_target_state, sort_keys=True)}`.",
                f"- Non-R6 root states: `{json.dumps(non_r6_root_states, sort_keys=True)}`.",
                "",
                "## Audit Decision",
                "",
                "Do not call `update_goal`. V71 does not satisfy the objective: R6 still lacks accepted source-owned normal controls or explicit FLIP-control approval, the owner-export/canonical root is not ready, downstream chain rerun is deferred, source-label confidence is still blocked, and R5/R3 source roots are absent.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- Prompt-to-artifact checklist: `{checklist_path.relative_to(REPO)}`",
                f"- Assertions: `{assertions_path.relative_to(REPO)}`",
                "",
                "## Next",
                "",
                current_cursor["next_action"],
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = {
        "board_cursor_loaded": bool(current_cursor["last_loop_id"]),
        "r6_screen_loaded": R6_SCREEN_JSON.exists(),
        "r6_route_loaded": R6_ROUTE_JSON.exists(),
        "r6_public_normal_loaded": R6_PUBLIC_NORMAL_JSON.exists(),
        "r6_external_control_loaded": R6_EXTERNAL_CONTROL_JSON.exists(),
        "r6_official_route_loaded": R6_OFFICIAL_ROUTE_REPORT.exists(),
        "local_control_loaded": LOCAL_CONTROL_JSON.exists(),
        "provider_autoquant_loaded": PROVIDER_AQ_JSON.exists(),
        "r6_independent_normal_rows_zero": r6_screen["row_counts"]["independent_normal_rows"] == 0,
        "r6_valid_controls_zero": r6_route["valid_normal_controls_acquired"] == 0,
        "r6_public_source_owned_controls_zero": r6_public_normal["valid_source_owned_normal_controls_found"] == 0,
        "r6_external_verifier_ready_controls_zero": r6_external_control["verifier_ready_source_owned_normal_controls_found"] == 0,
        "r6_official_route_controls_not_acquired": all(
            row["decision"] == "controls_not_acquired" for row in r6_official_cells
        ),
        "r6_canonical_target_not_ready": not all(r6_target_state["required_files_present"].values()),
        "source_label_root_not_ready": not non_r6_root_states["source_label_equivalence"]["exists"],
        "r5_root_not_ready": not non_r6_root_states["r5_source_panel_recency"]["exists"],
        "r3_root_not_ready": not non_r6_root_states["native_subhour"]["exists"],
        "strict_full_objective_false": result["strict_full_objective_achieved"] is False,
        "update_goal_false": result["update_goal"] is False,
    }
    assertions_path.write_text(
        "\n".join(f"{key}={'PASS' if value else 'FAIL'}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"gate_result": gate_result, "update_goal": False}, sort_keys=True))
    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
