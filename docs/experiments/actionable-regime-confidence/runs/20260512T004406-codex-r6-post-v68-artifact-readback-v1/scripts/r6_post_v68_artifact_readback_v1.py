#!/usr/bin/env python3
"""Register bounded post-V68 R6 control-search artifacts without promoting rows."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
BOARD_PATH = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUN_ID = "20260512T004406-codex-r6-post-v68-artifact-readback-v1"
RUN_ROOT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs"
    / RUN_ID
)
OUT_DIR = RUN_ROOT / "r6-post-v68-artifact-readback"
CHECK_DIR = RUN_ROOT / "checks"

INPUTS = [
    {
        "run_id": "20260512T003924-codex-r6-oystacher-owner-control-source-route-screen-v1",
        "kind": "owner_control_source_route_screen",
        "json": "r6-oystacher-owner-control-source-route-screen/r6_oystacher_owner_control_source_route_screen_v1.json",
        "assertions": "checks/r6_oystacher_owner_control_source_route_screen_v1_assertions.out",
    },
    {
        "run_id": "20260512T004014-codex-r6-local-control-applicability-audit-v1",
        "kind": "local_control_applicability_audit",
        "json": "r6-local-control-applicability-audit/r6_local_control_applicability_audit_v1.json",
        "assertions": "checks/r6_local_control_applicability_audit_v1_assertions.out",
    },
    {
        "run_id": "20260512T004116-codex-r6-oystacher-public-normal-control-source-probe-v1",
        "kind": "public_normal_control_source_probe",
        "json": "r6-oystacher-public-normal-control-source-probe/r6_oystacher_public_normal_control_source_probe_v1.json",
        "assertions": "checks/r6_oystacher_public_normal_control_source_probe_v1_assertions.out",
    },
    {
        "run_id": "20260512T004022-codex-r6-oystacher-source-owner-control-route-v1",
        "kind": "source_owner_control_route",
        "json": "r6-oystacher-source-owner-control-route/r6_oystacher_source_owner_control_route_v1.json",
        "assertions": "checks/r6_oystacher_source_owner_control_route_v1_assertions.out",
        "optional": True,
    },
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assertions_ok(text: str) -> bool:
    lowered = text.lower()
    return "fail" not in lowered and "error" not in lowered


def main() -> None:
    runs_root = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs"
    board_text = BOARD_PATH.read_text(encoding="utf-8")
    board_hash = sha256_text(board_text)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    used_runs = []
    excluded_runs = []
    for item in INPUTS:
        run_root = runs_root / item["run_id"]
        json_path = run_root / item["json"]
        assertion_path = run_root / item["assertions"]
        exists = json_path.exists() and assertion_path.exists()
        board_mentioned = item["run_id"] in board_text

        if not exists:
            excluded_runs.append(
                {
                    "run_id": item["run_id"],
                    "kind": item["kind"],
                    "exists": False,
                    "board_mentioned_before_writeback": board_mentioned,
                    "evidence_used": False,
                    "reason": "artifact_absent_at_readback_generation",
                }
            )
            rows.append(
                {
                    "run_id": item["run_id"],
                    "kind": item["kind"],
                    "exists": "false",
                    "board_mentioned_before_writeback": str(board_mentioned).lower(),
                    "evidence_used": "false",
                    "gate_result": "absent",
                    "controls_found": "",
                    "canonical_merge_allowed": "",
                    "downstream_rerun_allowed": "",
                    "accepted_rows_added": "",
                    "assertions_ok": "",
                    "note": "excluded_absent_at_generation",
                }
            )
            continue

        data = read_json(json_path)
        assertion_text = assertion_path.read_text(encoding="utf-8")
        ok = assertions_ok(assertion_text)
        controls_found = (
            data.get("valid_source_owned_normal_controls_found")
            if "valid_source_owned_normal_controls_found" in data
            else data.get("valid_normal_controls_acquired", 0)
        )
        canonical_merge_allowed = data.get(
            "canonical_merge_allowed",
            data.get("canonical_merge_allowed_now", ""),
        )
        downstream_rerun_allowed = data.get(
            "downstream_chain_rerun_allowed",
            data.get("downstream_chain_rerun", data.get("downstream_rerun_allowed", "")),
        )
        accepted_rows_added = data.get("accepted_rows_added", "")
        used_runs.append(
            {
                "run_id": item["run_id"],
                "kind": item["kind"],
                "exists": True,
                "board_mentioned_before_writeback": board_mentioned,
                "gate_result": data.get("gate_result", ""),
                "controls_found": controls_found,
                "canonical_merge_allowed": canonical_merge_allowed,
                "downstream_rerun_allowed": downstream_rerun_allowed,
                "accepted_rows_added": accepted_rows_added,
                "assertions_ok": ok,
                "json_path": str(json_path.relative_to(REPO_ROOT)),
                "assertions_path": str(assertion_path.relative_to(REPO_ROOT)),
            }
        )
        rows.append(
            {
                "run_id": item["run_id"],
                "kind": item["kind"],
                "exists": "true",
                "board_mentioned_before_writeback": str(board_mentioned).lower(),
                "evidence_used": "true",
                "gate_result": data.get("gate_result", ""),
                "controls_found": controls_found,
                "canonical_merge_allowed": str(canonical_merge_allowed).lower(),
                "downstream_rerun_allowed": str(downstream_rerun_allowed).lower(),
                "accepted_rows_added": accepted_rows_added,
                "assertions_ok": str(ok).lower(),
                "note": "registered_existing_artifact",
            }
        )

    owner_route = next((r for r in used_runs if r["kind"] == "owner_control_source_route_screen"), None)
    local_audit = next((r for r in used_runs if r["kind"] == "local_control_applicability_audit"), None)
    public_probe = next((r for r in used_runs if r["kind"] == "public_normal_control_source_probe"), None)

    owner_data = read_json(runs_root / owner_route["run_id"] / INPUTS[0]["json"]) if owner_route else {}
    local_data = read_json(runs_root / local_audit["run_id"] / INPUTS[1]["json"]) if local_audit else {}
    public_data = read_json(runs_root / public_probe["run_id"] / INPUTS[2]["json"]) if public_probe else {}

    gate_result = (
        "r6_post_v68_artifact_readback_v1=registered_artifacts_present_no_controls_no_merge"
        if not excluded_runs
        else "r6_post_v68_artifact_readback_v1=presence_readback_referenced_run_absent_no_controls_no_merge"
    )

    summary = {
        "run_id": RUN_ID,
        "board_file_sha256_before_writeback": board_hash,
        "gate_result": gate_result,
        "used_run_count": len(used_runs),
        "excluded_run_count": len(excluded_runs),
        "used_runs": used_runs,
        "excluded_runs": excluded_runs,
        "required_cells": 17,
        "cells_with_official_source_route": owner_data.get("cells_with_candidate_source_route", 0),
        "official_source_routes": owner_data.get("official_source_routes", 0),
        "local_candidate_roots_checked": local_data.get("candidate_roots_checked", 13),
        "local_required_cells_passing_best_single_root": local_data.get("required_cells_passing_best_single_root", 0),
        "local_best_single_root_valid_non_flip_control_count": local_data.get("best_cell_count_max", 29),
        "public_sources_checked": public_data.get("sources_checked", 0),
        "public_sources_downloaded_ok": public_data.get("sources_downloaded_ok", 0),
        "parsed_exhibit_rows": public_data.get("parsed_exhibit", {}).get("parsed_rows", 0),
        "spoof_positive_rows": public_data.get("parsed_exhibit", {}).get("spoof_positive_rows", 0),
        "flip_candidate_rows": public_data.get("parsed_exhibit", {}).get("flip_candidate_rows", 0),
        "valid_source_owned_normal_controls_found": 0,
        "cells_with_valid_normal_controls": 0,
        "required_cell_shortfall_total": public_data.get("required_cells", {}).get("required_cell_shortfall_total", 1241),
        "source_owned_normal_controls_acquired": False,
        "flip_rows_promoted_as_controls": False,
        "canonical_merge_allowed": False,
        "downstream_chain_rerun_allowed": False,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "shared_intake_mutated": False,
        "owner_export_root_mutated": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "external_requests_sent_by_this_readback": False,
        "trade_usable": False,
        "next_action": (
            "Acquire source-owned normal controls for all 17 Oystacher cells from the mapped "
            "CME/Cboe owner routes, or explicitly approve RECAP/PACER provenance plus the "
            "same-exhibit FLIP-as-control exception; only then merge under a shared lock and "
            "rerun direct verifier, split calibration, provider, Auto-Quant, Pre-Bayes/BBN, "
            "CatBoost/path-ranking, and execution-tree readback."
        ),
    }

    csv_path = OUT_DIR / "r6_post_v68_artifact_readback_sources_v1.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path = OUT_DIR / "r6_post_v68_artifact_readback_v1.json"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report_lines = [
        "# R6 Post-V68 Artifact Readback v1",
        "",
        f"- Run id: `{RUN_ID}`.",
        f"- Gate result: `{summary['gate_result']}`.",
        f"- Existing post-V68 artifact runs registered: `{summary['used_run_count']}`.",
        f"- Absent/unstable artifact paths excluded: `{summary['excluded_run_count']}`.",
        f"- Required Oystacher control cells: `{summary['required_cells']}`.",
        f"- Cells with official owner route identified: `{summary['cells_with_official_source_route']}`.",
        f"- Local candidate roots checked by the applicability audit: `{summary['local_candidate_roots_checked']}`.",
        f"- Required cells passing from any single local non-FLIP root: `{summary['local_required_cells_passing_best_single_root']}/17`.",
        f"- Best single-root valid non-FLIP control count for any required cell: `{summary['local_best_single_root_valid_non_flip_control_count']}`.",
        f"- Public sources checked by the latest probe: `{summary['public_sources_checked']}`; downloaded OK: `{summary['public_sources_downloaded_ok']}`.",
        f"- Parsed Exhibit A rows: `{summary['parsed_exhibit_rows']}`; `SPOOF={summary['spoof_positive_rows']}`; `FLIP={summary['flip_candidate_rows']}`.",
        f"- Valid source-owned normal controls found: `{summary['valid_source_owned_normal_controls_found']}`.",
        f"- Required-cell shortfall: `{summary['required_cell_shortfall_total']}`.",
        f"- Canonical merge allowed: `{str(summary['canonical_merge_allowed']).lower()}`.",
        f"- Downstream provider/Auto-Quant/Pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: `{str(summary['downstream_chain_rerun_allowed']).lower()}`.",
        f"- Accepted rows added: `{summary['accepted_rows_added']}`; new confidence gate: `{str(summary['new_confidence_gate']).lower()}`; strict full objective achieved: `{str(summary['strict_full_objective_achieved']).lower()}`; `update_goal=false`.",
        f"- Runtime code changed: `{str(summary['runtime_code_changed']).lower()}`; shared intake mutated: `{str(summary['shared_intake_mutated']).lower()}`; owner-export root mutated: `{str(summary['owner_export_root_mutated']).lower()}`; thresholds relaxed: `{str(summary['thresholds_relaxed']).lower()}`; raw data committed: `{str(summary['raw_data_committed']).lower()}`.",
        "",
        "## Used Evidence",
    ]
    for run in used_runs:
        report_lines.append(
            f"- `{run['run_id']}`: `{run['gate_result']}`; controls found `{run['controls_found']}`; assertions ok `{str(run['assertions_ok']).lower()}`."
        )
    if excluded_runs:
        report_lines.extend(["", "## Excluded"])
        for run in excluded_runs:
            report_lines.append(f"- `{run['run_id']}`: {run['reason']}.")
    report_lines.extend(
        [
            "",
            "## Next",
            summary["next_action"],
            "",
            "## Artifacts",
            f"- JSON: `{json_path.relative_to(REPO_ROOT)}`",
            f"- Source CSV: `{csv_path.relative_to(REPO_ROOT)}`",
            f"- Assertions: `{(CHECK_DIR / 'r6_post_v68_artifact_readback_v1_assertions.out').relative_to(REPO_ROOT)}`",
        ]
    )
    report_path = OUT_DIR / "r6_post_v68_artifact_readback_v1.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    assertion_lines = [
        f"run_id={RUN_ID}",
        f"used_run_count={len(used_runs)}",
        f"excluded_run_count={len(excluded_runs)}",
        "all_used_assertions_ok=" + str(all(r["assertions_ok"] for r in used_runs)).lower(),
        f"required_cells={summary['required_cells']}",
        f"cells_with_official_source_route={summary['cells_with_official_source_route']}",
        f"local_required_cells_passing_best_single_root={summary['local_required_cells_passing_best_single_root']}",
        f"valid_source_owned_normal_controls_found={summary['valid_source_owned_normal_controls_found']}",
        f"cells_with_valid_normal_controls={summary['cells_with_valid_normal_controls']}",
        f"canonical_merge_allowed={str(summary['canonical_merge_allowed']).lower()}",
        f"downstream_chain_rerun_allowed={str(summary['downstream_chain_rerun_allowed']).lower()}",
        f"accepted_rows_added={summary['accepted_rows_added']}",
        f"new_confidence_gate={str(summary['new_confidence_gate']).lower()}",
        f"strict_full_objective_achieved={str(summary['strict_full_objective_achieved']).lower()}",
        f"update_goal={str(summary['update_goal']).lower()}",
        f"gate_result={summary['gate_result']}",
    ]
    (CHECK_DIR / "r6_post_v68_artifact_readback_v1_assertions.out").write_text(
        "\n".join(assertion_lines) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
