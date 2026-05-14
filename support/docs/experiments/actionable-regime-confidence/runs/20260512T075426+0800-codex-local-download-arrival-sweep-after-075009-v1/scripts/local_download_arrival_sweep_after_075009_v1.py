#!/usr/bin/env python3
"""Bounded local/download arrival sweep after the 075009 source-control gate.

This is read-only against source roots. It classifies newly modified local files
that might be mistaken for Board A source/control unlocks, without promoting
OHLCV, public metadata, generated labels, or incomplete owner exports.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T075426+0800-codex-local-download-arrival-sweep-after-075009-v1"
GATE = "local_download_arrival_sweep_after_075009_v1=no_new_required_source_control_unlock"
CUTOFF = datetime(2026, 5, 12, 7, 50, 9, tzinfo=timezone(timedelta(hours=8)))

SCRIPT_PATH = Path(__file__).resolve()
RUN_ROOT = SCRIPT_PATH.parents[1]
ARTIFACT_DIR = RUN_ROOT / "local-download-arrival-sweep-after-075009-v1"
CHECKS_DIR = RUN_ROOT / "checks"
REPO_ROOT = RUN_ROOT.parents[4]
BOARD_A = REPO_ROOT / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

SCAN_ROOTS = [
    Path("/Users/thrill3r/Downloads"),
    Path("/tmp"),
    Path("/private/tmp"),
]

SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "target",
    "Library",
    "Caches",
    "Chrome",
    "Google",
    "com.apple",
}

TARGET_ROOTS = {
    "r6_owner_export": Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    "r5_recency": Path("/tmp/ict-engine-source-panel-recency-extension"),
    "r3_native_subhour": Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    "source_label_equivalence": Path("/tmp/ict-engine-source-label-equivalence-intake"),
}

R6_REQUIRED = {
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
}

FILENAME_TERMS = (
    "mainregimev2",
    "main_regime_v2",
    "source_label",
    "native_subhour",
    "regime",
    "crisis",
    "spoof",
    "layer",
    "manipulation",
    "matched_control",
    "matched_negative",
    "provenance",
    "databento",
    "ibkr",
    "tradingview",
    "kraken",
    "yfinance",
)

SOURCE_LABEL_COLUMNS = {
    "main_regime_v2",
    "mainregimev2",
    "main_regime_v2_label",
    "regime_label",
    "source_confidence",
    "qualifying_condition",
    "validation_instruments",
    "validation_periods",
    "validation_market_contexts",
}

ORDER_LIFECYCLE_COLUMNS = {
    "direct_label",
    "matched_negative_group_id",
    "order_id",
    "event_type",
    "side",
    "price",
    "quantity",
    "timestamp",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_mtime_local(path: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).astimezone(
            timezone(timedelta(hours=8))
        )
    except OSError:
        return None


def header_for(path: Path) -> list[str]:
    suffix = path.suffix.lower()
    try:
        if suffix in {".csv", ".tsv"}:
            with path.open(newline="", errors="replace") as f:
                sample = f.readline()
            delimiter = "\t" if suffix == ".tsv" else ","
            return [cell.strip().strip('"').lower() for cell in sample.split(delimiter)]
        if suffix in {".json", ".jsonl"}:
            with path.open(errors="replace") as f:
                text = f.readline() if suffix == ".jsonl" else f.read(65536)
            obj = json.loads(text)
            if isinstance(obj, dict):
                return [str(k).lower() for k in obj.keys()]
            if isinstance(obj, list) and obj and isinstance(obj[0], dict):
                return [str(k).lower() for k in obj[0].keys()]
    except Exception:
        return []
    return []


def classify_file(path: Path) -> dict[str, Any] | None:
    mtime = file_mtime_local(path)
    if mtime is None or mtime < CUTOFF:
        return None
    try:
        stat = path.stat()
    except OSError:
        return None
    if stat.st_size == 0 or stat.st_size > 300 * 1024 * 1024:
        return None

    lower_name = path.name.lower()
    header = header_for(path)
    header_set = set(header)
    filename_hit = any(term in lower_name for term in FILENAME_TERMS)
    source_label_hits = sorted(header_set & SOURCE_LABEL_COLUMNS)
    order_lifecycle_hits = sorted(header_set & ORDER_LIFECYCLE_COLUMNS)
    required_file_hit = path.name in R6_REQUIRED or "native_subhour_source_label" in lower_name

    if not (filename_hit or source_label_hits or order_lifecycle_hits or required_file_hit):
        return None

    return {
        "path": str(path),
        "filename": path.name,
        "mtime_local": mtime.isoformat(),
        "size": stat.st_size,
        "required_file_hit": required_file_hit,
        "filename_hit": filename_hit,
        "source_label_columns": "|".join(source_label_hits),
        "order_lifecycle_columns": "|".join(order_lifecycle_hits),
        "header_preview": "|".join(header[:24]),
    }


def iter_files(root: Path):
    if not root.exists():
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in SKIP_DIRS and not d.startswith(".") and "node_modules" not in d
        ]
        depth = len(Path(dirpath).relative_to(root).parts)
        if root in {Path("/tmp"), Path("/private/tmp")} and depth > 4:
            dirnames[:] = []
        if root == Path("/Users/thrill3r/Downloads") and depth > 6:
            dirnames[:] = []
        for filename in filenames:
            yield Path(dirpath) / filename


def root_status(name: str, root: Path) -> dict[str, Any]:
    files: list[str] = []
    if root.is_dir():
        files = sorted(p.name for p in root.iterdir() if p.is_file())
    return {
        "name": name,
        "root": str(root),
        "exists": root.exists(),
        "file_count": len(files),
        "files": files,
        "r6_required_complete": name == "r6_owner_export" and R6_REQUIRED.issubset(set(files)),
    }


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    scanned = 0
    for root in SCAN_ROOTS:
        for path in iter_files(root) or []:
            scanned += 1
            item = classify_file(path)
            if item is not None:
                rows.append(item)
            if scanned >= 200000:
                break

    rows.sort(key=lambda row: (row["mtime_local"], row["path"]))
    target_status = [root_status(name, path) for name, path in TARGET_ROOTS.items()]

    required_filename_hits = sum(1 for row in rows if row["required_file_hit"])
    source_label_schema_hits = sum(1 for row in rows if row["source_label_columns"])
    order_lifecycle_schema_hits = sum(1 for row in rows if row["order_lifecycle_columns"])
    r6_complete = any(row["r6_required_complete"] for row in target_status)
    r5_root_present = any(row["name"] == "r5_recency" and row["exists"] for row in target_status)
    r3_target_present = any(row["name"] == "r3_native_subhour" and row["exists"] for row in target_status)

    summary = {
        "run_id": RUN_ID,
        "gate_result": GATE,
        "cutoff_local": CUTOFF.isoformat(),
        "board_sha256": sha256(BOARD_A),
        "files_scanned": scanned,
        "candidate_rows": len(rows),
        "required_filename_hits": required_filename_hits,
        "source_label_schema_hits": source_label_schema_hits,
        "order_lifecycle_schema_hits": order_lifecycle_schema_hits,
        "target_roots": target_status,
        "accepted_rows_added": 0,
        "r6_owner_export_complete": r6_complete,
        "r5_recency_root_present": r5_root_present,
        "r3_native_subhour_root_present": r3_target_present,
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    csv_path = ARTIFACT_DIR / "local_download_arrival_sweep_after_075009_v1.csv"
    json_path = ARTIFACT_DIR / "local_download_arrival_sweep_after_075009_v1.json"
    report_path = ARTIFACT_DIR / "local_download_arrival_sweep_after_075009_v1.md"
    assertions_path = CHECKS_DIR / "local_download_arrival_sweep_after_075009_v1_assertions.out"

    fieldnames = [
        "path",
        "filename",
        "mtime_local",
        "size",
        "required_file_hit",
        "filename_hit",
        "source_label_columns",
        "order_lifecycle_columns",
        "header_preview",
    ]
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})

    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    report = [
        "# Local Download Arrival Sweep After 075009 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE}`",
        "",
        "## Scope",
        "",
        "Bounded read-only sweep of Downloads, `/tmp`, and `/private/tmp` for files modified after the `075009` source/control arrival poll. This does not mutate R3/R5/R6 target roots, derive labels, approve controls, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Readback",
        "",
        f"- Board hash: `{summary['board_sha256']}`.",
        f"- Files scanned: `{scanned}`.",
        f"- Candidate rows: `{len(rows)}`.",
        f"- Required filename hits: `{required_filename_hits}`.",
        f"- Source-label schema hits: `{source_label_schema_hits}`.",
        f"- Order-lifecycle schema hits: `{order_lifecycle_schema_hits}`.",
        f"- R6 owner/export complete: `{r6_complete}`.",
        f"- R5 recency root present: `{r5_root_present}`.",
        f"- R3 native-subhour root present: `{r3_target_present}`.",
        "",
        "## Decision",
        "",
        "No new valid required source/control root is unlocked by this sweep. Any candidate files are local inventory/readback evidence only unless a later manual review proves they are source-owned post-cutoff `MainRegimeV2` labels, verifier-native Crisis-capable R3 rows, or R6 owner-export positives with matched controls and provenance.",
        "",
        "Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.",
        "",
        "## Next",
        "",
        "Continue source/control acquisition only before any split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.",
        "",
    ]
    report_path.write_text("\n".join(report))

    assertions = [
        f"gate_result={GATE}",
        f"files_scanned={scanned}",
        f"candidate_rows={len(rows)}",
        f"required_filename_hits={required_filename_hits}",
        f"source_label_schema_hits={source_label_schema_hits}",
        f"order_lifecycle_schema_hits={order_lifecycle_schema_hits}",
        f"r6_owner_export_complete={str(r6_complete).lower()}",
        f"r5_recency_root_present={str(r5_root_present).lower()}",
        f"r3_native_subhour_root_present={str(r3_target_present).lower()}",
        "accepted_rows_added=0",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
