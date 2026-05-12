#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path


RUN_ID = "20260512T091346+0800-codex-source-control-selected-history-poll-after-090725-v1"
ARTIFACT_SLUG = "source-control-selected-history-poll-after-090725-v1"
GATE_RESULT = "source_control_selected_history_poll_after_090725_v1=no_owner_export_no_explicit_user_selected_history_no_unlock"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, header: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def walk_depth(root: Path, max_depth: int):
    if not root.exists():
        return
    root = root.resolve()
    base_depth = len(root.parts)
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        depth = len(current_path.parts) - base_depth
        if depth >= max_depth:
            dirs[:] = []
        yield current_path, files


def collect_direct_manipulation(root: Path, max_depth: int = 3):
    required = {
        "direct_manipulation_positive_rows.csv",
        "direct_manipulation_matched_controls.csv",
        "direct_manipulation_provenance.json",
    }
    found: dict[str, str] = {}
    if root.exists():
        for current_path, files in walk_depth(root, max_depth):
            for name in files:
                if name in required and name not in found:
                    found[name] = str(current_path / name)
    return found


def collect_selected_history_candidates(runs_root: Path, limit: int = 20):
    patterns = [
        "selected_data_path.txt",
        "*user-selected*",
        "*selected*historical*",
        "*agent_selected*",
        "*selected*history*",
    ]
    seen: set[str] = set()
    rows: list[dict[str, object]] = []
    for pattern in patterns:
        for path in runs_root.rglob(pattern):
            path_str = str(path)
            if path_str in seen:
                continue
            seen.add(path_str)
            reason = "agent-side candidate or historical-selection hint only"
            if path.name == "selected_data_path.txt":
                reason = "recorded path artifact, not an explicit user selection"
            elif "user-selected" in path_str.lower():
                reason = "user-selected naming appears in prior Board B artifacts, not current Board A proof"
            rows.append({"path": path_str, "kind": path.name, "reason": reason})
            if len(rows) >= limit:
                return rows
    return rows


def main() -> None:
    repo_root = Path(__file__).resolve().parents[6]
    board_path = repo_root / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
    run_root = repo_root / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
    artifact_dir = run_root / ARTIFACT_SLUG
    checks_dir = run_root / "checks"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    current_audit_json = (
        repo_root
        / "docs/experiments/actionable-regime-confidence/runs/20260512T090725+0800-codex-current-objective-audit-after-085908-v1/current-objective-audit-after-085908-v1/current_objective_audit_after_085908_v1.json"
    )

    owner_export_roots = [
        Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
    ]

    dropzone_rows: list[dict[str, object]] = []
    direct_manipulation_present = False
    for root in owner_export_roots:
        exists = root.exists()
        if exists:
            direct_found = collect_direct_manipulation(root)
            required_present = all(name in direct_found for name in (
                "direct_manipulation_positive_rows.csv",
                "direct_manipulation_matched_controls.csv",
                "direct_manipulation_provenance.json",
            ))
            direct_manipulation_present = direct_manipulation_present or required_present
        else:
            direct_found = {}
            required_present = False
        dropzone_rows.append(
            {
                "root": str(root),
                "exists": str(exists).lower(),
                "required_direct_manipulation_files_present": str(required_present).lower(),
                "found_files": ";".join(sorted(direct_found.values())) if direct_found else "",
            }
        )

    selected_history_candidates = collect_selected_history_candidates(
        repo_root / "docs/experiments/actionable-regime-confidence/runs"
    )
    explicit_user_selected_history = False
    source_control_evidence_acquired = direct_manipulation_present
    valid_required_root_unlock = False
    canonical_merge = False
    selected_data_autoquant_promotion = False
    downstream_promotion_rerun = False
    promotion_allowed = False
    update_goal = False

    checklist_rows = [
        {
            "requirement": "owner_export_dropzone_populated",
            "status": "blocked" if not direct_manipulation_present else "covered",
            "evidence": "no /tmp or /private/tmp owner-export root currently exposes all three required direct_manipulation files",
            "gap": "needs owner-approved source/export files in the documented dropzone",
        },
        {
            "requirement": "explicit_user_selected_history",
            "status": "blocked" if not explicit_user_selected_history else "covered",
            "evidence": "090725 audit keeps explicit selected-history false; only agent-side candidates exist",
            "gap": "need exactly one explicit user choice from HTF=1d, MTF=4h, or LTF=1h",
        },
        {
            "requirement": "source_control_unlock",
            "status": "blocked" if not valid_required_root_unlock else "covered",
            "evidence": GATE_RESULT,
            "gap": "needs owner export or FLIP control approval plus user-selected history",
        },
        {
            "requirement": "canonical_merge",
            "status": "blocked" if not canonical_merge else "covered",
            "evidence": "false by current ledger",
            "gap": "blocked until source/control and selected-history gates pass",
        },
        {
            "requirement": "selected_data_autoquant",
            "status": "not_run" if not selected_data_autoquant_promotion else "covered",
            "evidence": "false by current ledger",
            "gap": "blocked until source/control and selected-history gates pass",
        },
        {
            "requirement": "downstream_promotion",
            "status": "not_run" if not downstream_promotion_rerun else "covered",
            "evidence": "false by current ledger",
            "gap": "blocked until source/control and selected-history gates pass",
        },
        {
            "requirement": "completion_update_goal",
            "status": "blocked" if not update_goal else "covered",
            "evidence": "false by current ledger",
            "gap": "do not call update_goal",
        },
    ]

    board_hash = sha256_file(board_path)

    report_lines = [
        "# Source-Control Selected-History Poll After 090725 v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Gate result: `{GATE_RESULT}`",
        "",
        "## Readback",
        f"- Board hash before writeback: `{board_hash}`",
        f"- Source/control evidence acquired: `{str(source_control_evidence_acquired).lower()}`",
        f"- Valid required-root unlock: `{str(valid_required_root_unlock).lower()}`",
        f"- Explicit user-selected history: `{str(explicit_user_selected_history).lower()}`",
        f"- Canonical merge: `{str(canonical_merge).lower()}`",
        f"- Selected-data AutoQuant promotion: `{str(selected_data_autoquant_promotion).lower()}`",
        f"- Downstream promotion rerun: `{str(downstream_promotion_rerun).lower()}`",
        f"- Promotion allowed: `{str(promotion_allowed).lower()}`",
        f"- update_goal: `{str(update_goal).lower()}`",
        "",
        "## Dropzone",
    ]
    for row in dropzone_rows:
        report_lines.append(
            f"- {row['root']}: exists={row['exists']}, required_direct_manipulation_files_present={row['required_direct_manipulation_files_present']}"
            + (f", found={row['found_files']}" if row["found_files"] else "")
        )
    report_lines.extend([
        "",
        "## Selected History Candidates",
    ])
    if selected_history_candidates:
        for row in selected_history_candidates:
            report_lines.append(f"- {row['path']} ({row['reason']})")
    else:
        report_lines.append("- none found")
    report_lines.extend([
        "",
        "## Decision",
        "No owner-export dropzone with the required direct-manipulation files was found, and the latest current-objective audit keeps explicit selected history false.",
        "The objective remains fail-closed on source/control unlock and selected-history selection.",
    ])

    report_path = artifact_dir / "source_control_selected_history_poll_after_090725_v1.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    json_path = artifact_dir / "source_control_selected_history_poll_after_090725_v1.json"
    json_path.write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "gate_result": GATE_RESULT,
                "board_hash_before_writeback": board_hash,
                "source_control_evidence_acquired": source_control_evidence_acquired,
                "valid_required_root_unlock": valid_required_root_unlock,
                "explicit_user_selected_history": explicit_user_selected_history,
                "canonical_merge": canonical_merge,
                "selected_data_autoquant_promotion": selected_data_autoquant_promotion,
                "downstream_promotion_rerun": downstream_promotion_rerun,
                "promotion_allowed": promotion_allowed,
                "update_goal": update_goal,
                "dropzone": dropzone_rows,
                "selected_history_candidates": selected_history_candidates,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    checklist_path = artifact_dir / "prompt_to_artifact_checklist_after_090725_v1.csv"
    write_csv(
        checklist_path,
        ["requirement", "status", "evidence", "gap"],
        checklist_rows,
    )

    dropzone_csv = artifact_dir / "source_control_dropzone_readback_after_090725_v1.csv"
    write_csv(
        dropzone_csv,
        ["root", "exists", "required_direct_manipulation_files_present", "found_files"],
        dropzone_rows,
    )

    selected_history_csv = artifact_dir / "selected_history_candidates_after_090725_v1.csv"
    write_csv(
        selected_history_csv,
        ["path", "kind", "reason"],
        selected_history_candidates,
    )

    assertions_path = checks_dir / "source_control_selected_history_poll_after_090725_v1_assertions.out"
    assertions_lines = [
        f"gate_result={GATE_RESULT}",
        f"board_hash_before_writeback={board_hash}",
        f"source_control_evidence_acquired={str(source_control_evidence_acquired).lower()}",
        f"valid_required_root_unlock={str(valid_required_root_unlock).lower()}",
        f"explicit_user_selected_history={str(explicit_user_selected_history).lower()}",
        f"canonical_merge={str(canonical_merge).lower()}",
        f"selected_data_autoquant_promotion={str(selected_data_autoquant_promotion).lower()}",
        f"downstream_promotion_rerun={str(downstream_promotion_rerun).lower()}",
        f"promotion_allowed={str(promotion_allowed).lower()}",
        f"update_goal={str(update_goal).lower()}",
    ]
    assertions_path.write_text("\n".join(assertions_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
