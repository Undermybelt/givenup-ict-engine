#!/usr/bin/env python3
"""Board A source/control arrival poll after the 074116 R3 settlement.

This script is intentionally read-only for repo and temp roots. It records
whether a valid R3/R5/R6 source-control unlock has arrived since the latest
manual settlement, without running verifier, calibration, canonical merge, or
downstream promotion.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


RUN_ID = "20260512T074408+0800-codex-source-control-arrival-poll-after-074116-v1"
GATE = "source_control_arrival_poll_after_074116_v1=no_new_required_source_control_unlock"
CUTOFF = datetime(2026, 5, 12, 7, 41, 16, tzinfo=timezone(timedelta(hours=8)))

SCRIPT_PATH = Path(__file__).resolve()
RUN_ROOT = SCRIPT_PATH.parents[1]
ARTIFACT_DIR = RUN_ROOT / "source-control-arrival-poll-after-074116-v1"
CHECKS_DIR = RUN_ROOT / "checks"
REPO_ROOT = RUN_ROOT.parents[4]
BOARD = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

R6_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
]
R5_ROOTS = [
    Path("/tmp/ict-engine-source-panel-recency-extension"),
    Path("/private/tmp/ict-engine-source-panel-recency-extension"),
]
R3_ROOTS = [
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/private/tmp/ict-engine-native-subhour-source-label-intake"),
]
EQUIV_ROOTS = [
    Path("/tmp/ict-engine-source-label-equivalence-intake"),
    Path("/private/tmp/ict-engine-source-label-equivalence-intake"),
]

APPROVAL_PACKAGES = [
    Path("/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid"),
    Path("/tmp/r6_oystacher_approval_decision_package_v1.json.valid"),
]

R6_REQUIRED = [
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
]

RECENT_FILENAME_SIGNALS = {
    "direct_manipulation_positive_rows.csv": "r6_positive_rows",
    "direct_manipulation_matched_controls.csv": "r6_matched_controls",
    "direct_manipulation_provenance.json": "r6_provenance",
    "native_subhour_source_label_rows.csv": "r3_native_subhour_rows",
    "native_subhour_source_label_provenance.json": "r3_native_subhour_provenance",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        with path.open() as f:
            obj = json.load(f)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def root_status(root: Path, required: list[str]) -> dict[str, Any]:
    status: dict[str, Any] = {
        "root": str(root),
        "exists": root.exists(),
        "is_dir": root.is_dir(),
        "required_files": required,
        "present_required_files": [],
        "missing_required_files": required[:],
        "file_count": 0,
    }
    if not root.is_dir():
        return status

    files = [p for p in root.iterdir() if p.is_file()]
    status["file_count"] = len(files)
    present = sorted(name for name in required if (root / name).is_file())
    status["present_required_files"] = present
    status["missing_required_files"] = sorted(set(required) - set(present))
    return status


def r3_crisis_status(root: Path) -> dict[str, Any]:
    provenance = root / "native_subhour_source_label_provenance.json"
    obj = read_json(provenance) if provenance.exists() else None
    text = json.dumps(obj or {}, sort_keys=True)
    return {
        "root": str(root),
        "exists": root.exists(),
        "provenance_exists": provenance.exists(),
        "crisis_string_present": "Crisis" in text,
        "known_tsie_dataset": "sujinwo/tsie-market-regime-dataset" in text,
        "accepted_mapping_labels": (obj or {}).get("accepted_mapping_confidence_95_labels", []),
        "limitations": (obj or {}).get("limitations", []),
    }


def approval_status(path: Path) -> dict[str, Any]:
    obj = read_json(path) if path.exists() else None
    assertions = (obj or {}).get("assertions", {})
    row_counts = (obj or {}).get("row_counts", {})
    return {
        "path": str(path),
        "exists": path.exists(),
        "approval_present": bool((obj or {}).get("approval_present") or assertions.get("approval_present")),
        "canonical_merge_allowed_now": bool(
            (obj or {}).get("canonical_merge_allowed_now")
            or assertions.get("canonical_merge_allowed_now")
        ),
        "downstream_rerun_allowed_now": bool(
            (obj or {}).get("downstream_rerun_allowed_now")
            or assertions.get("downstream_rerun_allowed_now")
        ),
        "flip_controls_accepted_under_current_contract": bool(
            (obj or {}).get("flip_controls_accepted_under_current_contract")
            or assertions.get("flip_controls_accepted_under_current_contract")
        ),
        "positive_spoof_rows": (obj or {}).get("positive_spoof_rows") or row_counts.get("positive_spoof_rows"),
        "flip_rows": (obj or {}).get("flip_rows") or row_counts.get("flip_rows"),
        "matched_groups": (obj or {}).get("matched_groups") or row_counts.get("matched_groups"),
    }


def board_after_marker() -> dict[str, Any]:
    text = BOARD.read_text()
    marker = "## 2026-05-12 Supplemental 074116 R3 Possible File Manual Review After 073755 v1"
    idx = text.rfind(marker)
    after = text[idx:] if idx >= 0 else ""
    positive_tokens = [
        "approval_present=true",
        "canonical_merge_allowed_now=true",
        "downstream_rerun_allowed_now=true",
        "valid required-root unlock true",
        "valid_required_root_unlock=true",
        "source/control evidence acquired true",
        "source_control_evidence_acquired=true",
    ]
    return {
        "marker_found": idx >= 0,
        "post_marker_bytes": len(after),
        "positive_approval_or_unlock_tokens": [token for token in positive_tokens if token in after],
        "board_sha256": sha256(BOARD),
    }


def recent_file_signals() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    search_roots = [
        Path("/tmp"),
        Path("/private/tmp"),
        REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs",
    ]
    seen: set[str] = set()
    for search_root in search_roots:
        if not search_root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(search_root):
            dirnames[:] = [
                d
                for d in dirnames
                if d not in {".git", "target", "node_modules", "__pycache__", ".venv"}
            ]
            for filename in filenames:
                reason = RECENT_FILENAME_SIGNALS.get(filename)
                lower = filename.lower()
                if reason is None and "mainregimev2" not in lower:
                    continue
                path = Path(dirpath) / filename
                key = str(path)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    stat = path.stat()
                except OSError:
                    continue
                mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).astimezone(
                    timezone(timedelta(hours=8))
                )
                if mtime < CUTOFF:
                    continue
                rows.append(
                    {
                        "path": str(path),
                        "filename": filename,
                        "signal": reason or "mainregimev2_filename",
                        "mtime": mtime.isoformat(),
                        "size": stat.st_size,
                    }
                )
    rows.sort(key=lambda row: (row["mtime"], row["path"]))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    board = board_after_marker()
    r6 = [root_status(root, R6_REQUIRED) for root in R6_ROOTS]
    r5 = [root_status(root, []) for root in R5_ROOTS]
    r3 = [r3_crisis_status(root) for root in R3_ROOTS]
    equiv = [root_status(root, []) for root in EQUIV_ROOTS]
    approvals = [approval_status(path) for path in APPROVAL_PACKAGES]
    recent = recent_file_signals()

    approval_present = any(item["approval_present"] for item in approvals) or bool(
        board["positive_approval_or_unlock_tokens"]
    )
    canonical_merge_allowed_now = any(item["canonical_merge_allowed_now"] for item in approvals)
    downstream_rerun_allowed_now = any(item["downstream_rerun_allowed_now"] for item in approvals)
    r6_owner_export_unlock = any(
        item["exists"] and not item["missing_required_files"] for item in r6
    ) and approval_present
    r5_recency_unlock = any(item["exists"] and item["file_count"] > 0 for item in r5)
    r3_native_subhour_unlock = any(
        item["exists"] and item["provenance_exists"] and item["crisis_string_present"] and not item["known_tsie_dataset"]
        for item in r3
    )
    valid_required_root_unlock = (
        r6_owner_export_unlock or r5_recency_unlock or r3_native_subhour_unlock
    )

    summary: dict[str, Any] = {
        "run_id": RUN_ID,
        "gate_result": GATE,
        "cutoff_local": CUTOFF.isoformat(),
        "board": board,
        "r6_roots": r6,
        "r5_roots": r5,
        "r3_roots": r3,
        "source_label_equivalence_roots": equiv,
        "approval_packages": approvals,
        "recent_signal_count": len(recent),
        "recent_required_filename_count": sum(
            1 for row in recent if row["signal"] in set(RECENT_FILENAME_SIGNALS.values())
        ),
        "recent_mainregimev2_filename_count": sum(
            1 for row in recent if row["signal"] == "mainregimev2_filename"
        ),
        "approval_present": approval_present,
        "canonical_merge_allowed_now": canonical_merge_allowed_now,
        "downstream_rerun_allowed_now": downstream_rerun_allowed_now,
        "accepted_rows_added": 0,
        "r6_owner_export_unlock": r6_owner_export_unlock,
        "r5_recency_unlock": r5_recency_unlock,
        "r3_native_subhour_unlock": r3_native_subhour_unlock,
        "valid_required_root_unlock": valid_required_root_unlock,
        "source_control_evidence_acquired": valid_required_root_unlock,
        "direct_verifier_run": False,
        "split_calibration_run": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    if valid_required_root_unlock:
        summary["gate_result"] = "source_control_arrival_poll_after_074116_v1=unexpected_unlock_requires_manual_gate_review"

    json_path = ARTIFACT_DIR / "source_control_arrival_poll_after_074116_v1.json"
    report_path = ARTIFACT_DIR / "source_control_arrival_poll_after_074116_v1.md"
    csv_path = ARTIFACT_DIR / "source_control_arrival_poll_after_074116_v1.csv"
    assertions_path = CHECKS_DIR / "source_control_arrival_poll_after_074116_v1_assertions.out"

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_csv(csv_path, recent, ["path", "filename", "signal", "mtime", "size"])

    report = [
        "# Source/Control Arrival Poll After 074116 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{summary['gate_result']}`",
        "",
        "## Scope",
        "",
        "Read-only poll for explicit R6 approval, source-owned R6 controls, post-cutoff R5 rows, verifier-native Crisis-capable R3 labels, or a new accepted `MainRegimeV2` source export after the `074116` manual R3 settlement.",
        "This packet does not mutate target roots, run direct verifier, run split calibration, run canonical merge, run selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Readback",
        "",
        f"- Board hash: `{board['board_sha256']}`.",
        f"- Board post-`074116` positive approval/unlock tokens: `{len(board['positive_approval_or_unlock_tokens'])}`.",
        f"- R6 owner/export roots complete and approved: `{r6_owner_export_unlock}`.",
        f"- R5 recency root unlock: `{r5_recency_unlock}`.",
        f"- R3 native-subhour Crisis-capable unlock: `{r3_native_subhour_unlock}`.",
        f"- Recent filename signals after cutoff: `{len(recent)}`.",
        f"- Recent required filename signals after cutoff: `{summary['recent_required_filename_count']}`.",
        f"- Recent `MainRegimeV2` filename signals after cutoff: `{summary['recent_mainregimev2_filename_count']}`.",
        f"- Approval package approval present: `{approval_present}`.",
        f"- Canonical merge allowed now: `{canonical_merge_allowed_now}`.",
        f"- Downstream rerun allowed now: `{downstream_rerun_allowed_now}`.",
        "",
        "## Decision",
        "",
        "No new required source/control unlock arrived in the checked local roots or post-`074116` board tail. R6 owner/export remains absent or not approved, R5 recency root remains absent, and the R3 native-subhour root remains TSIE-derived/non-promoting rather than verifier-native Crisis-capable evidence.",
        "",
        "Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; direct verifier run false; split calibration run false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
        "",
        "## Next",
        "",
        "Continue source/control acquisition only. Do not run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion until explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export exists.",
        "",
    ]
    report_path.write_text("\n".join(report))

    assertions = [
        f"gate_result={summary['gate_result']}",
        f"approval_present={str(approval_present).lower()}",
        f"canonical_merge_allowed_now={str(canonical_merge_allowed_now).lower()}",
        f"downstream_rerun_allowed_now={str(downstream_rerun_allowed_now).lower()}",
        f"recent_signal_count={len(recent)}",
        f"recent_required_filename_count={summary['recent_required_filename_count']}",
        f"recent_mainregimev2_filename_count={summary['recent_mainregimev2_filename_count']}",
        f"accepted_rows_added={summary['accepted_rows_added']}",
        f"r6_owner_export_unlock={str(r6_owner_export_unlock).lower()}",
        f"r5_recency_unlock={str(r5_recency_unlock).lower()}",
        f"r3_native_subhour_unlock={str(r3_native_subhour_unlock).lower()}",
        f"valid_required_root_unlock={str(valid_required_root_unlock).lower()}",
        f"source_control_evidence_acquired={str(valid_required_root_unlock).lower()}",
        "direct_verifier_run=false",
        "split_calibration_run=false",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if not valid_required_root_unlock else 2


if __name__ == "__main__":
    raise SystemExit(main())
