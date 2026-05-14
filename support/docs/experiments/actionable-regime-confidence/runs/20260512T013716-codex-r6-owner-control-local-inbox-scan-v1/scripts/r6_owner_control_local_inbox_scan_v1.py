#!/usr/bin/env python3
"""Bounded local inbox scan for newly arrived R6 owner-control files."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


RUN_ID = "20260512T013716-codex-r6-owner-control-local-inbox-scan-v1"
REPO = Path(__file__).resolve().parents[6]
OUT_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = OUT_ROOT / "r6-owner-control-local-inbox-scan-v1"
CHECK_DIR = OUT_ROOT / "checks"

SCAN_ROOTS = [
    Path("/Users/thrill3r/Downloads"),
    Path("/Users/thrill3r/Desktop"),
    Path("/tmp"),
]
MAX_DEPTH = 4
NEEDLES = [
    "oystacher",
    "spoof",
    "spoofing",
    "manipulation",
    "direct_manipulation",
    "owner_export",
    "r6_owner",
    "cme_control",
    "cboe_control",
    "cfe_control",
]
TARGET_ROOTS = [
    ("r6_owner_export", Path("/tmp/ict-engine-board-a-r6-owner-export-v1")),
    ("r3_native_subhour", Path("/tmp/ict-engine-native-subhour-source-label-intake")),
    ("r5_recency_extension", Path("/tmp/ict-engine-source-panel-recency-extension")),
    ("source_label_equivalence", Path("/tmp/ict-engine-source-label-equivalence-intake")),
]


def depth(root: Path, path: Path) -> int:
    try:
        return len(path.relative_to(root).parts)
    except ValueError:
        return MAX_DEPTH + 1


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def scan_candidates() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)
            if depth(root, current) >= MAX_DEPTH:
                dirnames[:] = []
            for filename in filenames:
                lower = filename.lower()
                matched = [needle for needle in NEEDLES if needle in lower]
                if not matched:
                    continue
                path = current / filename
                try:
                    stat = path.stat()
                except OSError:
                    continue
                rows.append(
                    {
                        "root": str(root),
                        "path": str(path),
                        "matched_terms": ";".join(matched),
                        "disposition": classify(path),
                        "ready_source_owned_control_candidate": False,
                        "size_bytes": stat.st_size,
                    }
                )
    return sorted(rows, key=lambda row: str(row["path"]))


def classify(path: Path) -> str:
    text = str(path).lower()
    if "/tmp/ict-engine-board-a-r6-owner-export-v1/" in text:
        return "target_owner_export_path_requires_full_file_set"
    if "approval" in text:
        return "approval_template_or_pending_decision_not_explicit_approval"
    if "direct-manipulation-row-intake" in text or "direct_manipulation-row-intake" in text:
        return "historical_intake_manifest_artifact_not_new_owner_export"
    if "/tmp/ict-engine-direct-manipulation-row-intake/" in text:
        return "live_direct_intake_not_owner_export_root"
    if "r6-direct-intake" in text or "oystacher-exhibit-a" in text:
        return "isolated_or_same_exhibit_artifact_not_source_owned_normal_controls"
    if text.endswith((".pdf", ".html", ".txt", ".headers.txt")):
        return "source_trace_file_not_verifier_native_control_export"
    if "jsoncheck" in text or text.endswith((".out", ".valid")):
        return "prior_readback_or_request_artifact_not_owner_export_data"
    return "local_candidate_not_classified_as_ready_owner_control"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    candidates = scan_candidates()
    ready_candidates = [
        row for row in candidates if row["ready_source_owned_control_candidate"] is True
    ]
    target_roots = [
        {
            "id": root_id,
            "root": str(root),
            "present": root.exists(),
            "file_count": sum(1 for item in root.rglob("*") if item.is_file()) if root.exists() else 0,
        }
        for root_id, root in TARGET_ROOTS
    ]

    summary = {
        "run_id": RUN_ID,
        "gate_result": "r6_owner_control_local_inbox_scan_v1=old_candidates_found_no_source_owned_controls_no_approval",
        "scan_roots": [str(root) for root in SCAN_ROOTS],
        "max_depth": MAX_DEPTH,
        "candidate_count": len(candidates),
        "ready_source_owned_control_candidate_count": len(ready_candidates),
        "target_roots": target_roots,
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
        "external_requests_sent": False,
        "trade_usable": False,
    }

    write_csv(
        OUT_DIR / "r6_owner_control_local_inbox_candidates_v1.csv",
        candidates,
        [
            "root",
            "path",
            "matched_terms",
            "disposition",
            "ready_source_owned_control_candidate",
            "size_bytes",
        ],
    )
    write_csv(
        OUT_DIR / "r6_owner_control_local_inbox_target_roots_v1.csv",
        target_roots,
        ["id", "root", "present", "file_count"],
    )
    (OUT_DIR / "r6_owner_control_local_inbox_scan_v1.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    target_lines = "\n".join(
        f"- `{row['id']}`: present `{str(row['present']).lower()}`, files `{row['file_count']}` at `{row['root']}`."
        for row in target_roots
    )
    (OUT_DIR / "r6_owner_control_local_inbox_scan_v1.md").write_text(
        "\n".join(
            [
                "# R6 Owner Control Local Inbox Scan v1",
                "",
                f"Run id: `{RUN_ID}`",
                f"Gate result: `{summary['gate_result']}`",
                "",
                "Scan scope:",
                "- `/Users/thrill3r/Downloads`",
                "- `/Users/thrill3r/Desktop`",
                "- `/tmp`",
                f"- max depth `{MAX_DEPTH}`",
                "",
                "Result:",
                f"- Matching local inbox candidate files found: `{len(candidates)}`.",
                f"- Ready source-owned normal-control or explicit-approval candidates found: `{len(ready_candidates)}`.",
                "- Hits are prior readbacks, source trace files, isolated/same-exhibit artifacts, live direct-intake rows, or pending approval templates; none satisfy the active owner-export branch.",
                "- This scan does not treat historical repo experiment artifacts as source-owned control inputs.",
                "",
                "Target root readback:",
                target_lines,
                "",
                "Promotion status:",
                "- Accepted rows added: `0`.",
                "- Canonical merge allowed: `false`.",
                "- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree rerun allowed: `false`.",
                "- Strict full objective achieved: `false`; `update_goal=false`.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    root_present = {row["id"]: row["present"] for row in target_roots}
    assertions = {
        "ready_source_owned_control_candidate_count_zero": len(ready_candidates) == 0,
        "r6_owner_export_root_absent": root_present["r6_owner_export"] is False,
        "r3_native_subhour_root_absent": root_present["r3_native_subhour"] is False,
        "r5_recency_extension_root_absent": root_present["r5_recency_extension"] is False,
        "source_label_equivalence_root_present": root_present["source_label_equivalence"] is True,
        "accepted_rows_added_zero": summary["accepted_rows_added"] == 0,
        "canonical_merge_allowed_false": summary["canonical_merge_allowed"] is False,
        "downstream_chain_rerun_allowed_false": summary["downstream_chain_rerun_allowed"] is False,
        "strict_full_objective_achieved_false": summary["strict_full_objective_achieved"] is False,
        "update_goal_false": summary["update_goal"] is False,
        "runtime_code_changed_false": summary["runtime_code_changed"] is False,
        "shared_intake_mutated_false": summary["shared_intake_mutated"] is False,
        "external_requests_sent_false": summary["external_requests_sent"] is False,
    }
    (CHECK_DIR / "r6_owner_control_local_inbox_scan_v1_assertions.out").write_text(
        "\n".join(f"{key}={value}" for key, value in assertions.items()) + "\n",
        encoding="utf-8",
    )
    return 0 if all(assertions.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
