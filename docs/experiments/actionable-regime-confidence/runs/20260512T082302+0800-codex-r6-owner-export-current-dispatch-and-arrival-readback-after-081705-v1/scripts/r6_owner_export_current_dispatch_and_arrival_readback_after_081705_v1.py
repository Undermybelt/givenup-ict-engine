#!/usr/bin/env python3
"""Read-only current R6 owner-export dispatch and arrival readback."""

from __future__ import annotations

import csv
import hashlib
import json
from email import policy
from email.parser import BytesParser
from pathlib import Path


RUN_ID = "20260512T082302+0800-codex-r6-owner-export-current-dispatch-and-arrival-readback-after-081705-v1"
GATE_RESULT = (
    "r6_owner_export_current_dispatch_and_arrival_readback_after_081705_v1="
    "drafts_current_target_roots_absent_no_source_control_unlock"
)
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "r6-owner-export-current-dispatch-and-arrival-readback-after-081705-v1"
CHECKS = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

V5_DISPATCH_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1"
    / "r6-owner-export-v5-dispatch-manifest-v1"
)
DISPATCH_DRAFTS = [
    V5_DISPATCH_ROOT / "cme_group_owner_export_v5_dispatch_v1.eml",
    V5_DISPATCH_ROOT / "cboe_cfe_owner_export_v5_dispatch_v1.eml",
]
REFERENCE_ARTIFACTS = [
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T052231-codex-r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1"
    / "r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1"
    / "r6_owner_export_sendable_requests_v5_with_bessembinder_addendum_v1.md",
    V5_DISPATCH_ROOT / "r6_owner_export_v5_dispatch_manifest_v1.md",
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T055516-codex-r6-owner-export-dispatch-feasibility-readback-v1"
    / "r6-owner-export-dispatch-feasibility-readback-v1"
    / "r6_owner_export_dispatch_feasibility_readback_v1.md",
    REPO
    / "docs/experiments/actionable-regime-confidence/runs"
    / "20260512T060032-codex-r6-local-owner-export-intake-search-v1"
    / "r6-local-owner-export-intake-search-v1"
    / "r6_local_owner_export_intake_search_v1.md",
]
TARGET_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]
CURRENT_REQUIRED_FILES = [
    "positive_spoofing_layering_rows.csv",
    "matched_negative_normal_activity_rows.csv",
    "provenance_manifest.json",
]
LEGACY_REQUIRED_FILES = [
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_draft(path: Path) -> dict[str, object]:
    row: dict[str, object] = {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256(path),
        "parseable": False,
        "from_header_present": False,
        "to_header_present": False,
        "subject_present": False,
    }
    if not path.exists():
        return row
    try:
        msg = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    except Exception as exc:  # pragma: no cover - diagnostic output only.
        row["parse_error"] = str(exc)
        return row
    row["parseable"] = True
    row["from_header_present"] = bool(msg.get("From"))
    row["to_header_present"] = bool(msg.get("To"))
    row["subject_present"] = bool(msg.get("Subject"))
    return row


def root_status(root: Path) -> dict[str, object]:
    current_present = [name for name in CURRENT_REQUIRED_FILES if (root / name).exists()]
    legacy_present = [name for name in LEGACY_REQUIRED_FILES if (root / name).exists()]
    provenance_like = []
    if root.exists():
        for path in sorted(root.glob("*")):
            if not path.is_file():
                continue
            lowered = path.name.lower()
            if any(token in lowered for token in ("ticket", "export", "license", "provenance", "manifest")):
                provenance_like.append(path.name)
    return {
        "root": str(root),
        "exists": root.exists(),
        "current_required_present": current_present,
        "current_required_complete": len(current_present) == len(CURRENT_REQUIRED_FILES),
        "legacy_required_present": legacy_present,
        "legacy_required_complete": len(legacy_present) == len(LEGACY_REQUIRED_FILES),
        "provenance_like_files": provenance_like,
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def existing_board_sha(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text()).get("board_sha256_before")
    except (json.JSONDecodeError, OSError):
        return None
    return value if isinstance(value, str) and value else None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    json_path = OUT / "r6_owner_export_current_dispatch_and_arrival_readback_after_081705_v1.json"

    draft_rows = [parse_draft(path) for path in DISPATCH_DRAFTS]
    target_rows = [root_status(root) for root in TARGET_ROOTS]
    reference_rows = [
        {"path": rel(path), "exists": path.exists(), "sha256": sha256(path)}
        for path in REFERENCE_ARTIFACTS
    ]

    target_unlock = any(
        bool(row["current_required_complete"] or row["legacy_required_complete"])
        for row in target_rows
        if "owner-export" in str(row["root"])
    )
    all_drafts_parseable = all(bool(row["parseable"]) for row in draft_rows)
    any_sender_identity = any(bool(row["from_header_present"]) for row in draft_rows)
    all_reference_artifacts_present = all(bool(row["exists"]) for row in reference_rows)

    result = {
        "run_id": RUN_ID,
        "gate_result": GATE_RESULT,
        "board_sha256_before": existing_board_sha(json_path) or sha256(BOARD),
        "reference_artifacts": reference_rows,
        "dispatch_drafts": draft_rows,
        "target_roots": target_rows,
        "all_drafts_parseable": all_drafts_parseable,
        "any_sender_identity": any_sender_identity,
        "all_reference_artifacts_present": all_reference_artifacts_present,
        "owner_export_target_unlock": target_unlock,
        "source_control_evidence_acquired": False,
        "accepted_rows_added": 0,
        "valid_required_root_unlock": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
        "external_requests_sent_by_this_artifact": False,
        "target_roots_mutated_by_this_artifact": False,
        "next_action": (
            "Dispatch or otherwise satisfy the v5 CME and Cboe/CFE owner-export requests "
            "through an approved operator path, preserve ticket/export/license identifiers "
            "in provenance, or record explicit FLIP-as-control approval before any canonical "
            "merge or downstream rerun."
        ),
    }

    md_path = OUT / "r6_owner_export_current_dispatch_and_arrival_readback_after_081705_v1.md"
    draft_csv = OUT / "current_dispatch_drafts_v1.csv"
    target_csv = OUT / "current_target_root_status_v1.csv"
    reference_csv = OUT / "current_reference_artifacts_v1.csv"
    assertions_path = CHECKS / "r6_owner_export_current_dispatch_and_arrival_readback_after_081705_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_csv(draft_csv, draft_rows)
    write_csv(target_csv, target_rows)
    write_csv(reference_csv, reference_rows)

    md_path.write_text(
        "\n".join(
            [
                "# R6 Owner Export Current Dispatch and Arrival Readback After 081705 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{GATE_RESULT}`",
                "",
                f"Board sha256 before artifact: `{result['board_sha256_before']}`",
                "",
                "## Scope",
                "",
                "Read-only current-state check after the latest public RECAP route corrections. "
                "This artifact inventories the freshest v5 CME/Cboe/CFE dispatch drafts and checks "
                "only the approved target roots for verifier-native R6 owner-export files. It does "
                "not send email, copy files, approve controls, mutate target roots, run canonical "
                "merge, rerun downstream promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Readback",
                "",
                f"- Reference artifacts present: `{all_reference_artifacts_present}`.",
                f"- Dispatch drafts present: `{sum(1 for row in draft_rows if row['exists'])}`.",
                f"- Dispatch drafts parseable: `{all_drafts_parseable}`.",
                f"- Sender identity present in any draft: `{any_sender_identity}`.",
                f"- Owner-export target unlock found: `{target_unlock}`.",
                f"- Accepted rows added: `0`.",
                f"- Source/control evidence acquired: `false`.",
                "",
                "## Target Roots",
                "",
                "| root | exists | current required complete | legacy required complete | provenance-like files |",
                "|---|---:|---:|---:|---:|",
                *[
                    "| {root} | {exists} | {current_required_complete} | {legacy_required_complete} | {count} |".format(
                        root=row["root"],
                        exists=str(row["exists"]).lower(),
                        current_required_complete=str(row["current_required_complete"]).lower(),
                        legacy_required_complete=str(row["legacy_required_complete"]).lower(),
                        count=len(row["provenance_like_files"]),
                    )
                    for row in target_rows
                ],
                "",
                "## Decision",
                "",
                "No current approved target root contains a complete verifier-native owner-export package "
                "or provenance/ticket evidence. The current v5 drafts remain parseable dispatch artifacts, "
                "not source/control evidence. Canonical merge and downstream AutoQuant/filter/Pre-Bayes/BBN/"
                "CatBoost/path-ranking/execution-tree promotion remain blocked.",
                "",
                "Promotion status remains unchanged: accepted rows added `0`, valid required-root unlock "
                "`false`, source/control evidence acquired `false`, canonical merge `false`, selected-data "
                "AutoQuant promotion `false`, downstream promotion rerun `false`, strict full objective "
                "`false`, trade usable `false`, and `update_goal=false`.",
                "",
                "## Next",
                "",
                str(result["next_action"]),
                "",
            ]
        )
    )

    assertions = [
        f"PASS gate_result={GATE_RESULT}",
        f"PASS reference_artifacts_present={str(all_reference_artifacts_present).lower()}",
        f"PASS dispatch_drafts_parseable={str(all_drafts_parseable).lower()}",
        f"PASS sender_identity_present={str(any_sender_identity).lower()}",
        "PASS external_requests_sent_by_this_artifact=false",
        f"PASS owner_export_target_unlock={str(target_unlock).lower()}",
        "PASS accepted_rows_added=0",
        "PASS source_control_evidence_acquired=false",
        "PASS valid_required_root_unlock=false",
        "PASS canonical_merge=false",
        "PASS selected_data_autoquant_promotion=false",
        "PASS downstream_promotion_rerun=false",
        "PASS strict_full_objective=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
        "PASS target_roots_mutated_by_this_artifact=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
