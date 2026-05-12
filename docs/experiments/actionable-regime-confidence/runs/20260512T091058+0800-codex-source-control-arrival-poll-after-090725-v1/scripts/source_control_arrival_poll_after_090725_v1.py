#!/usr/bin/env python3
"""Read-only source/control arrival poll after the 090725 objective audit."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T091058+0800-codex-source-control-arrival-poll-after-090725-v1"
SLUG = "source-control-arrival-poll-after-090725-v1"
GATE = "source_control_arrival_poll_after_090725_v1=no_new_required_root_no_unlock"

SCRIPT = Path(__file__).resolve()
REPO = SCRIPT.parents[6]
BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_DIR = RUN_ROOT / SLUG
CHECK_DIR = RUN_ROOT / "checks"
PRIOR_090725 = (
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
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: Path, max_bytes: int | None = None) -> str | None:
    if not path.is_file():
        return None
    if max_bytes is not None and path.stat().st_size > max_bytes:
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"json_decode_error": True}


def count_top_files(path: Path) -> int:
    if not path.exists() or not path.is_dir():
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
        "required_files": required_files,
        "required_files_present": required_presence,
        "complete_required_file_set": bool(required_files) and all(required_presence.values()),
    }
    if name.startswith("r3_native_subhour"):
        provenance = load_json(path / "native_subhour_source_label_provenance.json")
        accepted_labels = provenance.get("accepted_mapping_confidence_95_labels", [])
        row["row_count"] = provenance.get("row_count", 0)
        row["accepted_mapping_confidence_95_labels"] = accepted_labels
        row["crisis_label_present"] = "Crisis" in accepted_labels
        row["unlocking"] = bool(row["complete_required_file_set"] and row["crisis_label_present"])
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
            depth = len(current_path.relative_to(root).parts) if current_path != root else 0
            if depth >= 3:
                dirs[:] = []
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "target", "__pycache__", ".venv", "Library"}]
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
                        "matched_terms": ";".join(matched),
                        "sha256_if_small": sha256(file_path, max_bytes=1_000_000) or "",
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

    cutoff_mtime = PRIOR_090725.stat().st_mtime if PRIOR_090725.exists() else 0.0
    target_rows = [inspect_target_root(name, path, required_files) for name, path, required_files in TARGET_ROOTS]
    dropzone_rows = recent_candidate_rows(cutoff_mtime)
    prior_assertions = [
        {
            "evidence": rel(BOARD_A),
            "sha256_before_artifact": sha256(BOARD_A),
            "gate_result": "board_a_current_state_reused_from_090725_audit",
        },
        {
            "evidence": rel(BOARD_B),
            "sha256_before_artifact": sha256(BOARD_B),
            "gate_result": "board_b_current_state_reused_from_090725_audit",
        },
    ]

    r3 = next(row for row in target_rows if row["name"] == "r3_native_subhour_tmp")
    r6_complete = any(row["complete_required_file_set"] for row in target_rows if row["name"].startswith("r6_owner_export"))
    r5_complete = any(row["complete_required_file_set"] for row in target_rows if row["name"].startswith("r5_recency"))

    summary = {
        "run_id": RUN_ID,
        "gate_result": GATE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "board_a_sha256_before_artifact": sha256(BOARD_A),
        "board_b_sha256_before_artifact": sha256(BOARD_B),
        "selected_history": False,
        "post_090725_dropzone_candidates": len(dropzone_rows),
        "current_r6_required_package_complete": r6_complete,
        "current_r5_recency_required_package_complete": r5_complete,
        "r3_native_subhour_required_file_set": bool(r3["complete_required_file_set"]),
        "r3_crisis_label_present": bool(r3.get("crisis_label_present", False)),
        "r3_native_subhour_unlock": bool(r3.get("unlocking", False)),
        "valid_required_root_unlock": bool(r6_complete and r5_complete and r3.get("unlocking", False)),
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "promotion_allowed": False,
        "update_goal": False,
    }

    (OUT_DIR / "source_control_arrival_poll_after_090725_v1.json").write_text(
        json.dumps({"summary": summary, "target_roots": target_rows, "dropzone_candidates": dropzone_rows, "prior_assertions": prior_assertions}, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    write_csv(
        OUT_DIR / "source_control_target_roots_after_090725_v1.csv",
        target_rows,
        [
            "name",
            "path",
            "exists",
            "is_dir",
            "file_count",
            "complete_required_file_set",
            "unlocking",
            "row_count",
            "crisis_label_present",
        ],
    )
    write_csv(
        OUT_DIR / "source_control_dropzone_candidates_after_090725_v1.csv",
        dropzone_rows,
        ["path", "root", "size", "mtime_utc", "matched_terms", "sha256_if_small"],
    )
    write_csv(
        OUT_DIR / "source_control_prior_assertions_after_090725_v1.csv",
        prior_assertions,
        ["evidence", "sha256_before_artifact", "gate_result"],
    )

    report = f"""# Source Control Arrival Poll After 090725 v1

Run id: `{RUN_ID}`

Gate result: `{GATE}`

## Readback

- Post-090725 dropzone candidates: `{len(dropzone_rows)}`
- Current R6 required package complete: `{r6_complete}`
- Current R5 recency required package complete: `{r5_complete}`
- R3 native-subhour required files present: `{bool(r3["complete_required_file_set"])}`
- R3 Crisis label present: `{bool(r3.get("crisis_label_present", False))}`
- R3 native-subhour unlock: `{bool(r3.get("unlocking", False))}`

## Decision

No new required root arrived after the 090725 audit. The source/control gate remains fail-closed.
Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false;
canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false;
promotion allowed false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/{SLUG}/source_control_arrival_poll_after_090725_v1.json`
- Target roots CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/{SLUG}/source_control_target_roots_after_090725_v1.csv`
- Dropzone candidates CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/{SLUG}/source_control_dropzone_candidates_after_090725_v1.csv`
- Prior assertions CSV: `docs/experiments/actionable-regime-confidence/runs/{RUN_ID}/{SLUG}/source_control_prior_assertions_after_090725_v1.csv`

## Next

Continue source/control acquisition only. Do not run selected-data AutoQuant or the ordered AutoQuant -> filter / Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree chain until both source/control and selected-history gates are satisfied.
"""
    (OUT_DIR / "source_control_arrival_poll_after_090725_v1.md").write_text(report, encoding="utf-8")

    assertions = [
        f"gate_result={GATE}",
        f"post_090725_dropzone_candidates={len(dropzone_rows)}",
        f"current_r6_required_package_complete={str(r6_complete).lower()}",
        f"current_r5_recency_required_package_complete={str(r5_complete).lower()}",
        f"r3_native_subhour_required_file_set={str(bool(r3['complete_required_file_set'])).lower()}",
        f"r3_crisis_label_present={str(bool(r3.get('crisis_label_present', False))).lower()}",
        f"r3_native_subhour_unlock={str(bool(r3.get('unlocking', False))).lower()}",
        "selected_history=false",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "promotion_allowed=false",
        "update_goal=false",
    ]
    (CHECK_DIR / "source_control_arrival_poll_after_090725_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
