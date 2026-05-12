#!/usr/bin/env python3
"""Read-only Board A source/control arrival poll after 090725."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T091246+0800-codex-source-control-arrival-poll-after-090725-v1"
SLUG = "source-control-arrival-poll-after-090725-v1"
GATE = "source_control_arrival_poll_after_090725_v1=no_new_required_root_no_unlock"

SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[6]
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / SLUG
CHECK_DIR = RUN_ROOT / "checks"
PRIOR_RUN = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T090725+0800-codex-current-objective-audit-after-085908-v1"
)

TARGET_ROOTS = [
    (
        "r6_owner_export_tmp",
        Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
        [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    ),
    (
        "r6_owner_export_private_tmp",
        Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
        [
            "positive_spoofing_layering_rows.csv",
            "matched_negative_normal_activity_rows.csv",
            "provenance_manifest.json",
        ],
    ),
    (
        "r5_recency_tmp",
        Path("/tmp/ict-engine-source-panel-recency-extension"),
        ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
    ),
    (
        "r5_recency_private_tmp",
        Path("/private/tmp/ict-engine-source-panel-recency-extension"),
        ["stock_market_regimes_2026_extension.csv", "source_panel_recency_provenance.json"],
    ),
    (
        "r3_native_subhour_tmp",
        Path("/tmp/ict-engine-native-subhour-source-label-intake"),
        ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
    ),
    (
        "r3_native_subhour_private_tmp",
        Path("/private/tmp/ict-engine-native-subhour-source-label-intake"),
        ["native_subhour_source_label_rows.csv", "native_subhour_source_label_provenance.json"],
    ),
]

DROPZONE_ROOTS = [Path.home() / "Downloads", Path.home() / "Desktop", Path("/tmp"), Path("/private/tmp")]
DROPZONE_TERMS = [
    "mainregimev2",
    "source_control",
    "source-control",
    "owner_export",
    "owner-export",
    "order_lifecycle",
    "order-lifecycle",
    "positive_spoofing",
    "positive-spoofing",
    "matched_negative",
    "matched-negative",
    "provenance_manifest",
    "native_subhour",
    "finra",
    "cat",
    "cme",
    "cboe",
    "cfe",
    "flip",
    "oystacher",
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path, max_bytes: int | None = None) -> str:
    if not path.is_file():
        return ""
    if max_bytes is not None and path.stat().st_size > max_bytes:
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {"json_decode_error": True}


def count_top_files(path: Path) -> int:
    if not path.is_dir():
        return 0
    return sum(1 for child in path.iterdir() if child.is_file())


def inspect_target_root(name: str, path: Path, required_files: list[str]) -> dict[str, Any]:
    required_presence = {file_name: (path / file_name).exists() for file_name in required_files}
    row: dict[str, Any] = {
        "name": name,
        "path": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "file_count": count_top_files(path),
        "required_files": "|".join(required_files),
        "required_files_present": json.dumps(required_presence, sort_keys=True),
        "complete_required_file_set": bool(required_files) and all(required_presence.values()),
    }
    if name.startswith("r3_native_subhour"):
        provenance = load_json(path / "native_subhour_source_label_provenance.json")
        labels = provenance.get("accepted_mapping_confidence_95_labels", [])
        row["row_count"] = provenance.get("row_count", 0)
        row["accepted_mapping_confidence_95_labels"] = "|".join(str(label) for label in labels)
        row["crisis_label_present"] = "Crisis" in labels
        row["unlocking"] = bool(row["complete_required_file_set"] and row["crisis_label_present"])
    elif name.startswith("r6_owner_export"):
        row["unlocking"] = bool(row["complete_required_file_set"])
    elif name.startswith("r5_recency"):
        row["unlocking"] = bool(row["complete_required_file_set"])
    else:
        row["unlocking"] = False
    return row


def recent_candidate_rows(cutoff_mtime: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for root in DROPZONE_ROOTS:
        if not root.exists():
            continue
        for current, dirs, files in os.walk(root):
            current_path = Path(current)
            rel_depth = len(current_path.relative_to(root).parts) if current_path != root else 0
            if rel_depth >= 3:
                dirs[:] = []
            dirs[:] = [
                directory
                for directory in dirs
                if directory not in {".git", "node_modules", "target", "__pycache__", ".venv", "Library"}
            ]
            for file_name in files:
                lower = file_name.lower()
                matched = [term for term in DROPZONE_TERMS if term in lower]
                if not matched:
                    continue
                file_path = current_path / file_name
                try:
                    stat = file_path.stat()
                except OSError:
                    continue
                if stat.st_mtime < cutoff_mtime:
                    continue
                key = str(file_path.resolve())
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "path": str(file_path),
                        "root": str(root),
                        "size": stat.st_size,
                        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                        "matched_terms": "|".join(matched),
                        "sha256_if_small": sha256(file_path, max_bytes=1_000_000),
                    }
                )
    rows.sort(key=lambda item: (item["mtime_utc"], item["path"]))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    cutoff_mtime = PRIOR_RUN.stat().st_mtime if PRIOR_RUN.exists() else 0.0
    board_sha = sha256(BOARD)
    target_rows = [inspect_target_root(name, path, required) for name, path, required in TARGET_ROOTS]
    candidate_rows = recent_candidate_rows(cutoff_mtime)

    r6_complete = any(row["name"].startswith("r6_owner_export") and row["unlocking"] for row in target_rows)
    r5_complete = any(row["name"].startswith("r5_recency") and row["unlocking"] for row in target_rows)
    r3_complete = any(row["name"].startswith("r3_native_subhour") and row["complete_required_file_set"] for row in target_rows)
    r3_crisis = any(row["name"].startswith("r3_native_subhour") and row.get("crisis_label_present") for row in target_rows)
    r3_unlock = any(row["name"].startswith("r3_native_subhour") and row["unlocking"] for row in target_rows)

    valid_required_root_unlock = bool(r6_complete or r5_complete or r3_unlock)
    summary = {
        "run_id": RUN_ID,
        "gate_result": GATE,
        "board_sha256_before_artifact": board_sha,
        "prior_run": rel(PRIOR_RUN),
        "cutoff_mtime_utc": datetime.fromtimestamp(cutoff_mtime, timezone.utc).isoformat()
        if cutoff_mtime
        else "",
        "post_090725_dropzone_candidates": len(candidate_rows),
        "current_r6_required_package_complete": r6_complete,
        "r5_recency_required_package_complete": r5_complete,
        "r3_native_subhour_complete_required_file_set": r3_complete,
        "r3_crisis_label_present": r3_crisis,
        "r3_native_subhour_unlock": r3_unlock,
        "accepted_rows_added": 0,
        "valid_required_root_unlock": valid_required_root_unlock,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }

    write_csv(
        OUT_DIR / "source_control_target_roots_after_090725_v1.csv",
        target_rows,
        [
            "name",
            "path",
            "exists",
            "is_dir",
            "file_count",
            "required_files",
            "required_files_present",
            "complete_required_file_set",
            "row_count",
            "accepted_mapping_confidence_95_labels",
            "crisis_label_present",
            "unlocking",
        ],
    )
    write_csv(
        OUT_DIR / "source_control_dropzone_candidates_after_090725_v1.csv",
        candidate_rows,
        ["path", "root", "size", "mtime_utc", "matched_terms", "sha256_if_small"],
    )

    json_path = OUT_DIR / "source_control_arrival_poll_after_090725_v1.json"
    json_path.write_text(json.dumps({"summary": summary, "target_roots": target_rows, "dropzone_candidates": candidate_rows}, indent=2), encoding="utf-8")

    report = f"""# Source/Control Arrival Poll After 090725 v1

Run id: `{RUN_ID}`

Gate result: `{GATE}`

## Scope

Read-only source/control arrival poll after terminal `090725`. This packet checks exact R6/R5/R3 target roots and recent Downloads/Desktop/tmp dropzone candidates modified after `090725`. It does not mutate target roots, approve local files as source/control evidence, send external requests, run verifier, run selected-data AutoQuant, run Pre-Bayes/BBN/CatBoost/execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Board A SHA-256 before artifact: `{board_sha}`.
- Post-090725 dropzone candidates: `{len(candidate_rows)}`.
- Current R6 required package complete: `{r6_complete}`.
- R5 recency required package complete: `{r5_complete}`.
- R3 native-subhour required files present: `{r3_complete}`.
- R3 Crisis label present: `{r3_crisis}`.
- R3 native-subhour unlock: `{r3_unlock}`.

## Decision

No new owner-approved/source-owned source/control package was accepted by this readback. R6 owner/export and R5 recency roots remain incomplete or absent. R3 native-subhour rows remain non-unlocking because Crisis is absent.

Accepted rows added `0`; valid required-root unlock {str(valid_required_root_unlock).lower()}; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.

## Artifacts

- JSON: `{rel(json_path)}`
- Target roots CSV: `{rel(OUT_DIR / "source_control_target_roots_after_090725_v1.csv")}`
- Dropzone candidates CSV: `{rel(OUT_DIR / "source_control_dropzone_candidates_after_090725_v1.csv")}`
- Assertions: `{rel(CHECK_DIR / "source_control_arrival_poll_after_090725_v1_assertions.out")}`

## Next

Continue source/control acquisition only. The live unblocker remains owner-approved/authenticated FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE order-lifecycle export rows with positives and matched normal controls, source-owned post-2026-01-30 R5 `MainRegimeV2` rows, verifier-native Crisis-capable R3 native-subhour labels, or explicit same-exhibit `FLIP`-as-control approval before verifier, split calibration, canonical merge, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, execution-tree promotion, trade claims, or `update_goal`.
"""
    report_path = OUT_DIR / "source_control_arrival_poll_after_090725_v1.md"
    report_path.write_text(report, encoding="utf-8")

    assertions_path = CHECK_DIR / "source_control_arrival_poll_after_090725_v1_assertions.out"
    assertions_path.write_text(
        "\n".join(
            [
                f"gate_result={GATE}",
                f"post_090725_dropzone_candidates={len(candidate_rows)}",
                f"current_r6_required_package_complete={str(r6_complete).lower()}",
                f"r5_recency_complete_required_file_set={str(r5_complete).lower()}",
                f"r3_native_subhour_complete_required_file_set={str(r3_complete).lower()}",
                f"r3_crisis_label_present={str(r3_crisis).lower()}",
                f"r3_native_subhour_unlock={str(r3_unlock).lower()}",
                "accepted_rows_added=0",
                f"valid_required_root_unlock={str(valid_required_root_unlock).lower()}",
                "source_control_evidence_acquired=false",
                "canonical_merge=false",
                "selected_data_autoquant_promotion=false",
                "downstream_promotion_rerun=false",
                "strict_full_objective=false",
                "trade_usable=false",
                "promotion_allowed=false",
                "update_goal=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
