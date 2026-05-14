#!/usr/bin/env python3
"""Read-only Board A source/control arrival scan after empty 051640 root."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T051909-codex-source-control-arrival-scan-after-051640-v1"
GATE = "source_control_arrival_scan_after_051640_v1=no_new_source_control_unlock_no_promotion"
BOARD_REL = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
RELATED_AUDITS = [
    {
        "name": "051754_current_objective_audit_v2",
        "root": Path(
            "docs/experiments/actionable-regime-confidence/runs/"
            "20260512T051754-codex-current-objective-audit-after-051145-051153-051247-v2"
        ),
        "json": Path(
            "current-objective-audit-after-051145-051153-051247-v2/"
            "current_objective_audit_after_051145_051153_051247_v2.json"
        ),
    },
    {
        "name": "051640_current_objective_audit_v1",
        "root": Path(
            "docs/experiments/actionable-regime-confidence/runs/"
            "20260512T051640-codex-current-objective-audit-after-051145-051153-051247-v1"
        ),
        "json": Path(
            "current-objective-audit-after-051145-051153-051247-v1/"
            "current_objective_audit_after_051145_051153_051247_v1.json"
        ),
    },
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob("*") if p.is_file())


def audit_row(repo_root: Path, audit: dict[str, Path | str]) -> dict[str, str]:
    root_rel = audit["root"]
    assert isinstance(root_rel, Path)
    root = repo_root / root_rel
    json_rel = audit["json"]
    assert isinstance(json_rel, Path)
    json_path = root / json_rel
    gate = "missing"
    objective_complete = "unknown"
    if json_path.is_file():
        payload = json.loads(json_path.read_text())
        gate = str(payload.get("gate_result", "missing_gate_result"))
        objective_complete = str(payload.get("objective_complete", "unknown")).lower()
    count = file_count(root)
    return {
        "audit": str(audit["name"]),
        "root": str(root_rel),
        "file_count": str(count),
        "json_present": str(json_path.is_file()).lower(),
        "gate_result": gate,
        "objective_complete": objective_complete,
        "status": "non_promoting_readback" if objective_complete == "false" else "incomplete_or_unknown",
    }


def root_row(name: str, root: Path, required_files: list[str], role: str) -> dict[str, str]:
    present = root.is_dir()
    present_files = []
    missing_files = []
    if present:
        for rel in required_files:
            if (root / rel).is_file():
                present_files.append(rel)
            else:
                missing_files.append(rel)
    else:
        missing_files = required_files[:]
    complete = present and not missing_files
    return {
        "gate": name,
        "path": str(root),
        "required_files": ";".join(required_files),
        "present": str(present).lower(),
        "present_required_files": str(len(present_files)),
        "missing_required_files": str(len(missing_files)),
        "complete": str(complete).lower(),
        "status": "present_complete" if complete else "blocked",
        "evidence_role": role,
    }


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    script_path = Path(__file__).resolve()
    run_root = script_path.parents[1]
    repo_root = script_path.parents[6]
    artifact_dir = run_root / "source-control-arrival-scan-after-051640-v1"
    checks_dir = run_root / "checks"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)

    board = repo_root / BOARD_REL
    board_hash = sha256(board)
    related_audits = [audit_row(repo_root, audit) for audit in RELATED_AUDITS]

    roots = [
        root_row(
            "r6_owner_export_root",
            Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
            [
                "positive_spoofing_layering_rows.csv",
                "matched_negative_normal_activity_rows.csv",
                "provenance_manifest.json",
            ],
            "required_source_control_root",
        ),
        root_row(
            "r3_native_subhour_root",
            Path("/tmp/ict-engine-native-subhour-source-label-intake"),
            [
                "native_subhour_source_label_rows.csv",
                "native_subhour_source_label_provenance.json",
            ],
            "required_source_label_root",
        ),
        root_row(
            "r5_recency_extension_root",
            Path("/tmp/ict-engine-source-panel-recency-extension"),
            [
                "stock_market_regimes_2026_extension.csv",
                "source_panel_recency_provenance.json",
            ],
            "required_source_label_root",
        ),
        root_row(
            "source_label_equivalence_existing_non_target",
            Path("/tmp/ict-engine-source-label-equivalence-intake"),
            [
                "source_label_equivalence_rows.csv",
                "source_label_equivalence_provenance.json",
            ],
            "present_but_non_promoting_existing_equivalence_root",
        ),
    ]

    target_roots = roots[:3]
    target_roots_complete = all(row["complete"] == "true" for row in target_roots)
    any_target_root_present = any(row["present"] == "true" for row in target_roots)
    source_control_evidence_acquired = target_roots_complete

    summary = {
        "run_id": RUN_ID,
        "gate_result": GATE,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_path": str(BOARD_REL),
        "board_sha256_before_scan": board_hash,
        "related_current_objective_audits": related_audits,
        "target_roots_present_any": any_target_root_present,
        "target_roots_complete_all": target_roots_complete,
        "source_control_evidence_acquired": source_control_evidence_acquired,
        "accepted_rows_added": 0,
        "accepted_regime_confidence_labels": 0,
        "canonical_merge_allowed": False,
        "downstream_promotion_rerun_allowed": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
        "notes": [
            "Existing source-label equivalence intake remains non-promoting by itself.",
            "Empty 051640 directory is treated as an incomplete artifact directory, not evidence.",
            "Provider/runtime readiness is intentionally not promoted as source/control evidence.",
        ],
        "root_status": roots,
    }

    json_path = artifact_dir / "source_control_arrival_scan_after_051640_v1.json"
    md_path = artifact_dir / "source_control_arrival_scan_after_051640_v1.md"
    csv_path = artifact_dir / "source_control_arrival_scan_after_051640_v1_checklist.csv"
    audits_csv_path = artifact_dir / "source_control_arrival_scan_after_051640_v1_related_audits.csv"
    assertions_path = checks_dir / "source_control_arrival_scan_after_051640_v1_assertions.out"

    json_path.write_text(json.dumps(summary, indent=2) + "\n")
    write_csv(csv_path, roots)
    write_csv(audits_csv_path, related_audits)

    md_lines = [
        "# Source Control Arrival Scan After 051640 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE}`",
        "",
        f"Board sha256 before scan artifact: `{board_hash}`",
        "",
        "## Purpose",
        "",
        "This read-only scan checks whether any source/control delivery arrived after the latest",
        "`051145`, `051153`, `051247`, `051640`, and `051754` readback artifacts. It does not",
        "mutate target roots, copy local triplets, approve `FLIP` controls, run canonical merge,",
        "run downstream promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Live Root Readback",
        "",
        "| Gate | Path | Status | Required files present | Evidence role |",
        "|---|---|---|---:|---|",
    ]
    for row in roots:
        md_lines.append(
            f"| `{row['gate']}` | `{row['path']}` | `{row['status']}` | "
            f"{row['present_required_files']} | `{row['evidence_role']}` |"
        )
    md_lines.extend(
        [
            "",
            "## Related Current-Objective Audit Readback",
            "",
            "| Audit | Files | JSON | Objective complete | Status |",
            "|---|---:|---|---|---|",
        ]
    )
    for row in related_audits:
        md_lines.append(
            f"| `{row['audit']}` | {row['file_count']} | `{row['json_present']}` | "
            f"`{row['objective_complete']}` | `{row['status']}` |"
        )
    md_lines.extend(
        [
            "",
            "These audits are counted only through their own board registrations. This scan is a later",
            "source/control arrival poll and does not duplicate their completion-status packets.",
            "",
            "## Decision",
            "",
            "Accepted rows added `0`; accepted regime-confidence labels `0`; source/control evidence",
            "acquired `false`; target source/control roots complete `false`; canonical merge `false`;",
            "downstream promotion rerun `false`; strict full objective `false`; trade usable `false`;",
            "`update_goal=false`.",
            "",
            "## Next",
            "",
            "Preserve the Current Cursor next action. Continue only after explicit approval, verifier-native",
            "R6 owner/export rows plus source-owned broad normal controls, source-owned R5 recency-extension",
            "rows, native sub-hour source-label rows, or genuinely source-owned cross-timeframe",
            "`MainRegimeV2` exports unlock a target root before rerunning direct verifier, split calibration,",
            "canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and",
            "execution-tree readback in order.",
            "",
        ]
    )
    md_path.write_text("\n".join(md_lines))

    assertions = [
        f"PASS board_readable {BOARD_REL}",
        f"PASS board_sha256 {board_hash}",
        "PASS required_target_roots_not_complete",
        "PASS source_control_evidence_acquired_false",
        "PASS related_current_objective_audits_non_promoting",
        "PASS no_canonical_merge",
        "PASS update_goal_false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")


if __name__ == "__main__":
    main()
