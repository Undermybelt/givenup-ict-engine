#!/usr/bin/env python3
"""Reconcile Board A after the active V71 official route/date-fit cursor."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


RUN_ID = "20260512T005039-codex-current-objective-reconciliation-after-v71-v1"
REPO = Path(__file__).resolve().parents[6]
RUNS = REPO / "docs/experiments/actionable-regime-confidence/runs"
RUN_ROOT = RUNS / RUN_ID
OUT = RUN_ROOT / "current-objective-reconciliation-after-v71"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

ARTIFACTS = {
    "public_normal_probe": RUNS
    / "20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1"
    / "r6-oystacher-public-normal-control-source-probe"
    / "r6_oystacher_public_normal_control_source_probe_v1.json",
    "external_control_scan": RUNS
    / "20260512T004322-codex-r6-oystacher-external-control-source-scan-v1"
    / "r6-oystacher-external-control-source-scan"
    / "r6_oystacher_external_control_source_scan_v1.json",
    "owner_market_data_access": RUNS
    / "20260512T004507-codex-r6-oystacher-owner-market-data-access-preflight-v1"
    / "r6-oystacher-owner-market-data-access-preflight"
    / "r6_oystacher_owner_market_data_access_preflight_v1.json",
    "artifact_integrity": RUNS
    / "20260512T004552-codex-r6-board-artifact-integrity-repair-v1"
    / "r6-board-artifact-integrity-repair"
    / "r6_board_artifact_integrity_repair_v1.json",
    "owner_export_presence": RUNS
    / "20260512T004713-codex-r6-source-owner-export-presence-sweep-v1"
    / "r6-source-owner-export-presence-sweep"
    / "r6_source_owner_export_presence_sweep_v1.json",
    "non_r6_readback": RUNS
    / "20260512T004822-codex-non-r6-source-intake-current-readback-v2"
    / "non-r6-source-intake-current-readback"
    / "non_r6_source_intake_current_readback_v2.json",
}
OFFICIAL_ROUTE_ASSERTIONS = (
    RUNS
    / "20260512T004410-codex-r6-official-route-date-fit-check-v1"
    / "checks/r6_official_route_date_fit_check_v1_assertions.out"
)

ROOTS = {
    "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "source_label_equivalence": Path("/tmp/ict-engine-source-label-equivalence-intake"),
    "r5_source_panel_recency": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
}
R6_REQUIRED = [
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


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_assertions(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        if "=" in raw:
            key, value = raw.split("=", 1)
            values[key.strip()] = value.strip()
        elif raw.startswith("PASS "):
            key, _, value = raw[5:].partition("=")
            values[key.strip()] = value.strip()
    return values


def cursor_value(board_text: str, field: str) -> str:
    pattern = rf"^\| {re.escape(field)} \| (.*?) \|"
    for line in board_text.splitlines():
        match = re.match(pattern, line)
        if match:
            return match.group(1)
    return ""


def root_state(root: Path, required: list[str] | None = None) -> dict[str, Any]:
    required = required or []
    return {
        "path": str(root),
        "exists": root.exists(),
        "required_files_present": {name: (root / name).exists() for name in required},
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def recent_board_reference_rows(board_text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    pattern = re.compile(r"docs/experiments/actionable-regime-confidence/runs/(20260512T00[4-9][0-9]{3}-[^/`\s]+)")
    for match in pattern.finditer(board_text):
        run_id = match.group(1)
        if run_id in seen:
            continue
        seen.add(run_id)
        root = RUNS / run_id
        file_count = sum(1 for item in root.rglob("*") if item.is_file()) if root.exists() else 0
        rows.append(
            {
                "run_id": run_id,
                "root_exists": root.exists(),
                "file_count": file_count,
                "status": "present" if root.exists() and file_count else "missing_or_empty",
            }
        )
    return rows


def artifact_presence_rows(board_text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, path in ARTIFACTS.items():
        run_id = next(part for part in path.parts if part.startswith("20260512T"))
        rows.append(
            {
                "artifact": name,
                "run_id": run_id,
                "path": rel(path),
                "exists": path.exists(),
                "board_mentioned": run_id in board_text,
            }
        )
    current_v71 = RUNS / "20260512T004341-codex-current-goal-completion-audit-after-v71-v1"
    superseded_v70 = RUNS / "20260512T004827-codex-current-goal-completion-audit-after-v70-v1"
    rows.extend(
        [
            {
                "artifact": "board_referenced_v71_completion_root",
                "run_id": current_v71.name,
                "path": rel(current_v71),
                "exists": current_v71.exists(),
                "board_mentioned": current_v71.name in board_text,
            },
            {
                "artifact": "superseded_v70_command_only_root",
                "run_id": superseded_v70.name,
                "path": rel(superseded_v70),
                "exists": superseded_v70.exists(),
                "board_mentioned": superseded_v70.name in board_text,
            },
        ]
    )
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    board_text = BOARD.read_text(encoding="utf-8")
    board_hash = sha256(BOARD)
    cursor = {
        "board_state": cursor_value(board_text, "board_state"),
        "last_loop_id": cursor_value(board_text, "last_loop_id"),
        "current_run_root": cursor_value(board_text, "current_run_root"),
        "accepted_gate": cursor_value(board_text, "accepted_gate"),
        "blocker": cursor_value(board_text, "blocker"),
        "next_action": cursor_value(board_text, "next_action"),
    }

    data = {name: load_json(path) for name, path in ARTIFACTS.items()}
    official = parse_assertions(OFFICIAL_ROUTE_ASSERTIONS)
    roots = {
        name: root_state(path, R6_REQUIRED if name == "r6_owner_export" else [])
        for name, path in ROOTS.items()
    }
    board_refs = recent_board_reference_rows(board_text)
    artifact_rows = artifact_presence_rows(board_text)

    broken_board_refs = [row for row in board_refs if row["status"] == "missing_or_empty"]
    recent_board_refs_all_present = not broken_board_refs

    gate_result = (
        "current_objective_reconciliation_after_v71_v1="
        "blocked_controls_absent_non_r6_absent_no_merge"
    )
    checklist = [
        {
            "requirement": "Current cursor is V71 official route date-fit.",
            "status": "pass" if "20260512T004410" in cursor["last_loop_id"] else "blocked",
            "evidence": cursor["last_loop_id"],
            "gap": "",
        },
        {
            "requirement": "R6 source-owned normal controls are acquired.",
            "status": "blocked",
            "evidence": (
                f"public={data['public_normal_probe']['valid_source_owned_normal_controls_found']}; "
                f"external={data['external_control_scan']['verifier_ready_source_owned_normal_controls_found']}; "
                f"owner_presence={data['owner_export_presence']['strictly_usable_source_owned_controls_found']}; "
                f"official_controls_not_acquired={official.get('controls_not_acquired')}"
            ),
            "gap": "No verifier-ready source-owned normal controls and no FLIP-control approval.",
        },
        {
            "requirement": "Owner-market-data access can fetch usable controls locally.",
            "status": "blocked",
            "evidence": (
                f"source_owned_controls={data['owner_market_data_access']['source_owned_normal_controls_acquired']}; "
                f"cells_with_valid_controls={data['owner_market_data_access']['cells_with_valid_controls']}"
            ),
            "gap": "Local Databento/CME/Cboe access did not acquire verifier-ready rows.",
        },
        {
            "requirement": "Owner export root is verifier-native and complete.",
            "status": "blocked",
            "evidence": json.dumps(roots["r6_owner_export"], sort_keys=True),
            "gap": "Owner-export root files and approval artifacts are absent.",
        },
        {
            "requirement": "Non-R6 source roots are ready.",
            "status": "blocked",
            "evidence": (
                f"ready_roots={data['non_r6_readback']['ready_roots']}/"
                f"{data['non_r6_readback']['roots_checked']}; "
                f"required_files_present={data['non_r6_readback']['required_files_present']}/"
                f"{data['non_r6_readback']['required_files_total']}"
            ),
            "gap": "Source-label equivalence, R5 recency, and R3 native-subhour roots remain absent/incomplete.",
        },
        {
            "requirement": "Board artifact references are all present.",
            "status": "pass" if recent_board_refs_all_present else "partial",
            "evidence": f"broken_or_empty_recent_refs={len(broken_board_refs)}",
            "gap": "Some recent board-referenced artifact roots are missing or empty." if broken_board_refs else "",
        },
        {
            "requirement": "Downstream provider/Auto-Quant/BBN/CatBoost/execution-tree rerun is justified.",
            "status": "deferred_blocked",
            "evidence": (
                f"canonical_merge_allowed={data['owner_export_presence']['canonical_merge_allowed']}; "
                f"downstream_allowed={data['owner_export_presence']['downstream_chain_rerun_allowed']}"
            ),
            "gap": "No accepted source/control input exists for a non-proxy downstream rerun.",
        },
        {
            "requirement": "Do not claim strict objective completion.",
            "status": "pass",
            "evidence": "strict_full_objective_achieved=false; update_goal=false",
            "gap": "",
        },
    ]

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "board_path": rel(BOARD),
        "board_sha256_at_start": board_hash,
        "cursor": cursor,
        "gate_result": gate_result,
        "artifact_inputs": {name: rel(path) for name, path in ARTIFACTS.items()},
        "official_route_assertions": official,
        "root_states": roots,
        "recent_board_reference_status": board_refs,
        "artifact_presence": artifact_rows,
        "broken_board_reference_count": len(broken_board_refs),
        "recent_board_refs_all_present": recent_board_refs_all_present,
        "r6_public_source_owned_normal_controls_found": data["public_normal_probe"]["valid_source_owned_normal_controls_found"],
        "r6_external_verifier_ready_controls_found": data["external_control_scan"]["verifier_ready_source_owned_normal_controls_found"],
        "r6_owner_access_source_owned_controls_acquired": data["owner_market_data_access"]["source_owned_normal_controls_acquired"],
        "r6_owner_presence_strictly_usable_controls_found": data["owner_export_presence"]["strictly_usable_source_owned_controls_found"],
        "non_r6_ready_roots": data["non_r6_readback"]["ready_roots"],
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "next_action": cursor["next_action"],
    }

    json_path = OUT / "current_objective_reconciliation_after_v71_v1.json"
    report_path = OUT / "current_objective_reconciliation_after_v71_v1.md"
    checklist_path = OUT / "prompt_to_artifact_checklist_after_v71_v1.csv"
    board_refs_path = OUT / "recent_board_reference_status_v1.csv"
    artifact_path = OUT / "artifact_presence_v1.csv"
    assertions_path = CHECKS / "current_objective_reconciliation_after_v71_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(checklist_path, checklist, ["requirement", "status", "evidence", "gap"])
    write_csv(board_refs_path, board_refs, ["run_id", "root_exists", "file_count", "status"])
    write_csv(artifact_path, artifact_rows, ["artifact", "run_id", "path", "exists", "board_mentioned"])

    lines = [
        "# Current Objective Reconciliation After V71 v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Board cursor observed: `{cursor['last_loop_id']}`.",
        f"- Board hash observed before artifact creation: `{board_hash}`.",
        f"- Gate result: `{gate_result}`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Readback",
        "",
        f"- R6 controls: public `{result['r6_public_source_owned_normal_controls_found']}`, external verifier-ready `{result['r6_external_verifier_ready_controls_found']}`, owner-access acquired `{result['r6_owner_access_source_owned_controls_acquired']}`, owner-presence usable `{result['r6_owner_presence_strictly_usable_controls_found']}`.",
        f"- Official route assertions: controls_not_acquired `{official.get('controls_not_acquired')}`, downstream_rerun_false `{official.get('downstream_rerun_false')}`.",
        f"- Owner-export root: `{json.dumps(roots['r6_owner_export'], sort_keys=True)}`.",
        f"- Non-R6 readiness: ready roots `{data['non_r6_readback']['ready_roots']}/{data['non_r6_readback']['roots_checked']}`, required files `{data['non_r6_readback']['required_files_present']}/{data['non_r6_readback']['required_files_total']}`.",
        f"- Recent board reference integrity: broken_or_empty `{len(broken_board_refs)}`; all recent references present `{recent_board_refs_all_present}`.",
        "",
        "## Decision",
        "",
        "Do not call `update_goal`. V71 still has no source-owned normal controls, no same-exhibit `FLIP` control approval, no verifier-native owner-export root, no non-R6 source roots, and no accepted input that justifies rerunning the downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree chain.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{rel(json_path)}`",
        f"- Checklist CSV: `{rel(checklist_path)}`",
        f"- Board reference CSV: `{rel(board_refs_path)}`",
        f"- Artifact presence CSV: `{rel(artifact_path)}`",
        f"- Assertions: `{rel(assertions_path)}`",
        "",
        "## Next",
        "",
        cursor["next_action"],
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")

    assertions = {
        "cursor_is_v71_official_route": "20260512T004410" in cursor["last_loop_id"],
        "public_controls_zero": result["r6_public_source_owned_normal_controls_found"] == 0,
        "external_controls_zero": result["r6_external_verifier_ready_controls_found"] == 0,
        "owner_access_controls_zero": result["r6_owner_access_source_owned_controls_acquired"] == 0,
        "owner_presence_controls_zero": result["r6_owner_presence_strictly_usable_controls_found"] == 0,
        "owner_export_root_incomplete": not all(roots["r6_owner_export"]["required_files_present"].values()),
        "non_r6_ready_roots_zero": result["non_r6_ready_roots"] == 0,
        "recent_board_refs_all_present": recent_board_refs_all_present,
        "no_downstream_rerun": result["downstream_chain_rerun_allowed"] is False,
        "strict_objective_false": result["strict_full_objective_achieved"] is False,
        "update_goal_false": result["update_goal"] is False,
    }
    assertions_path.write_text(
        "\n".join(f"{key}={'PASS' if value else 'FAIL'}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"gate_result": gate_result, "assertions_passed": all(assertions.values())}, sort_keys=True))
    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
