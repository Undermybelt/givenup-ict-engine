#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T083450+0800-codex-tomac-local-schema-classifier-after-083108-v1"
SLUG = "tomac-local-schema-classifier-after-083108-v1"
GATE = "tomac_local_schema_classifier_after_083108_v1=no_verifier_native_source_control_schema_no_unlock"

REPO = Path(__file__).resolve().parents[6]
BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_ROOT = RUN_ROOT / SLUG
CHECK_ROOT = RUN_ROOT / "checks"

SCAN_ROOT = Path("/Users/thrill3r/Downloads/Tomac")

EXACT_REQUIRED_FILES = {
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
}

R6_TARGET_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
]

STRONG_ORDER_LIFECYCLE_COLUMNS = {
    "action",
    "aggressor_side",
    "ask_order_id",
    "ask_px",
    "ask_size",
    "ask_sz",
    "bid_order_id",
    "bid_px",
    "bid_size",
    "bid_sz",
    "book_level",
    "event_type",
    "order_id",
    "participant",
    "side",
}

SOURCE_CONTROL_COLUMNS = {
    "control_label",
    "event_window_id",
    "is_control",
    "is_positive",
    "label",
    "matched_control_id",
    "matched_group",
    "source_section",
}

OHLCV_COLUMNS = {"open", "high", "low", "close", "volume"}

SCAN_SUFFIXES = {
    ".csv",
    ".json",
    ".zip",
    ".rar",
    ".7z",
    ".gz",
    ".zst",
    ".parquet",
    ".dbn",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_header(path: Path) -> str:
    try:
        with path.open("rb") as handle:
            data = handle.read(16384)
    except OSError:
        return ""
    text = data.decode("utf-8", errors="ignore")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[0] if lines else ""


def normalize_columns(header: str) -> list[str]:
    if not header:
        return []
    delimiter = "\t" if "\t" in header and "," not in header else ","
    return [part.strip().lower().strip('"') for part in header.split(delimiter) if part.strip()]


def json_top_keys(path: Path) -> list[str]:
    try:
        with path.open("rb") as handle:
            data = handle.read(262144)
        loaded = json.loads(data.decode("utf-8", errors="ignore"))
    except Exception:
        return []
    if isinstance(loaded, dict):
        return sorted(str(key).lower() for key in loaded.keys())[:80]
    if isinstance(loaded, list) and loaded and isinstance(loaded[0], dict):
        return sorted(str(key).lower() for key in loaded[0].keys())[:80]
    return []


def archive_members(path: Path) -> list[str]:
    if path.suffix.lower() not in {".zip", ".rar", ".7z", ".tar", ".gz", ".zst"}:
        return []
    try:
        completed = subprocess.run(
            ["bsdtar", "-tf", str(path)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()][:200]


def classify_path(path: Path) -> dict[str, object]:
    suffix = path.suffix.lower()
    header = read_header(path) if suffix == ".csv" else ""
    columns = normalize_columns(header)
    key_set = set(json_top_keys(path)) if suffix == ".json" else set()
    col_set = set(columns) | key_set
    members = archive_members(path)
    member_lower = [member.lower() for member in members]

    strong_order_hits = sorted(STRONG_ORDER_LIFECYCLE_COLUMNS & col_set)
    source_control_hits = sorted(SOURCE_CONTROL_COLUMNS & col_set)
    ohlcv_hits = sorted(OHLCV_COLUMNS & col_set)
    exact_required_name = path.name in EXACT_REQUIRED_FILES
    archive_order_hits = [
        member
        for member in members
        if any(token in member.lower() for token in ["mbo", "mbp", "order", "book", "quote", "trade", "itch", "pitch"])
    ][:25]
    verifier_native_hint = exact_required_name or len(source_control_hits) >= 2
    strong_lifecycle_hint = bool(strong_order_hits) or bool(archive_order_hits)
    schema_class = "other"
    if exact_required_name or verifier_native_hint:
        schema_class = "verifier_native_hint"
    elif strong_lifecycle_hint:
        schema_class = "order_lifecycle_hint"
    elif OHLCV_COLUMNS <= set(ohlcv_hits) or ".ohlcv-" in path.name.lower():
        schema_class = "ohlcv_or_bar_context"
    elif any(token in path.name.lower() for token in ["backtest", "results", "summary", "perfect", "ultimate"]):
        schema_class = "backtest_or_performance_context"
    elif suffix == ".json" and any(token in key_set for token in ["bbn", "research_runs", "workflow_snapshot", "condition"]):
        schema_class = "runtime_or_strategy_context"

    return {
        "path": str(path),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "suffix": suffix,
        "schema_class": schema_class,
        "columns_or_keys": "|".join(columns[:40] if columns else sorted(key_set)[:40]),
        "strong_order_lifecycle_hits": "|".join(strong_order_hits),
        "source_control_hits": "|".join(source_control_hits),
        "ohlcv_hits": "|".join(ohlcv_hits),
        "archive_members_read": len(members),
        "archive_order_lifecycle_member_hits": "|".join(archive_order_hits),
        "exact_required_name": exact_required_name,
        "verifier_native_hint": verifier_native_hint,
        "strong_lifecycle_hint": strong_lifecycle_hint,
    }


def iter_scan_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    paths: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        parts = {part.lower() for part in current.parts}
        if any(part in {".git", "node_modules", "target", ".venv", "__pycache__"} for part in parts):
            dirnames[:] = []
            continue
        for name in filenames:
            path = current / name
            if path.suffix.lower() in SCAN_SUFFIXES:
                paths.append(path)
    return sorted(paths)


def target_root_status(root: Path) -> dict[str, object]:
    files = sorted(path.name for path in root.iterdir()) if root.exists() and root.is_dir() else []
    return {
        "root": str(root),
        "exists": root.exists(),
        "file_count": len(files),
        "has_exact_required_package": EXACT_REQUIRED_FILES <= set(files),
    }


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_ROOT.mkdir(parents=True, exist_ok=True)

    files = iter_scan_files(SCAN_ROOT)
    rows = [classify_path(path) for path in files]
    target_roots = [target_root_status(root) for root in R6_TARGET_ROOTS]

    exact_required_files_found = sum(1 for row in rows if row["exact_required_name"])
    verifier_native_hints = sum(1 for row in rows if row["verifier_native_hint"])
    strong_lifecycle_hints = sum(1 for row in rows if row["strong_lifecycle_hint"])
    order_lifecycle_schema_files = [
        row for row in rows if row["schema_class"] == "order_lifecycle_hint"
    ]
    exact_required_package_present = any(row["has_exact_required_package"] for row in target_roots)

    valid_required_root_unlock = False
    source_control_evidence_acquired = False

    payload = {
        "run_id": RUN_ID,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_a_hash_before_artifact": sha256_file(BOARD_A),
        "gate_result": GATE,
        "scan_root": str(SCAN_ROOT),
        "files_scanned": len(rows),
        "exact_required_files_found": exact_required_files_found,
        "exact_required_package_present": exact_required_package_present,
        "verifier_native_hint_files": verifier_native_hints,
        "strong_lifecycle_hint_files": strong_lifecycle_hints,
        "target_roots": target_roots,
        "accepted_rows_added": 0,
        "valid_required_root_unlock": valid_required_root_unlock,
        "source_control_evidence_acquired": source_control_evidence_acquired,
        "canonical_merge": False,
        "selected_data_autoquant_promotion": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "promotion_allowed": False,
        "update_goal": False,
    }

    json_path = OUT_ROOT / "tomac_local_schema_classifier_after_083108_v1.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    csv_path = OUT_ROOT / "tomac_local_schema_classifier_rows_v1.csv"
    fieldnames = [
        "path",
        "size_bytes",
        "suffix",
        "schema_class",
        "columns_or_keys",
        "strong_order_lifecycle_hits",
        "source_control_hits",
        "ohlcv_hits",
        "archive_members_read",
        "archive_order_lifecycle_member_hits",
        "exact_required_name",
        "verifier_native_hint",
        "strong_lifecycle_hint",
    ]
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    target_csv = OUT_ROOT / "tomac_local_schema_target_roots_v1.csv"
    with target_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["root", "exists", "file_count", "has_exact_required_package"])
        writer.writeheader()
        writer.writerows(target_roots)

    sample_order_rows = order_lifecycle_schema_files[:10]
    md_path = OUT_ROOT / "tomac_local_schema_classifier_after_083108_v1.md"
    lines = [
        "# Tomac Local Schema Classifier After 083108 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{GATE}`",
        "",
        "## Scope",
        "",
        "Read-only schema classification of local Tomac CSV/JSON/archive candidates after the settled `083108` arrival poll. This artifact reads headers and archive member names only. It does not copy files into target roots, approve Tomac strategy/backtest/bar files as source/control evidence, run verifier/split calibration, run canonical merge, run Auto-Quant, run Pre-Bayes/BBN/CatBoost/execution-tree promotion, make a trade claim, or call `update_goal`.",
        "",
        "## Summary",
        "",
        f"- Files scanned: `{len(rows)}`.",
        f"- Exact required source/control file names found: `{exact_required_files_found}`.",
        f"- Exact required package present in R6 target roots: `{str(exact_required_package_present).lower()}`.",
        f"- Verifier-native hint files: `{verifier_native_hints}`.",
        f"- Strong order-lifecycle hint files: `{strong_lifecycle_hints}`.",
        "",
        "## Target Roots",
        "",
        "| Root | Exists | File Count | Exact Required Package |",
        "|---|---:|---:|---:|",
    ]
    for row in target_roots:
        lines.append(
            f"| `{row['root']}` | `{row['exists']}` | `{row['file_count']}` | `{row['has_exact_required_package']}` |"
        )
    lines.extend([
        "",
        "## Order-Lifecycle-Like Samples",
        "",
    ])
    if sample_order_rows:
        lines.extend([
            "| File | Class | Strong Hits | Archive Hits |",
            "|---|---|---|---|",
        ])
        for row in sample_order_rows:
            lines.append(
                f"| `{row['path']}` | `{row['schema_class']}` | `{row['strong_order_lifecycle_hits'] or 'none'}` | `{row['archive_order_lifecycle_member_hits'] or 'none'}` |"
            )
    else:
        lines.append("- None.")
    lines.extend([
        "",
        "## Decision",
        "",
        "- No exact required R6 owner-export positive/control/provenance package was present in target roots.",
        "- Local Tomac files are classified as strategy/backtest/runtime context, OHLCV/bar context, or weak archive/member-name hints only; none is accepted as verifier-native source/control evidence.",
        "- Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.",
        "",
        "## Next",
        "",
        "Continue source/control acquisition only. The live unblocker remains owner-approved/authenticated FINRA, venue-surveillance, CAT-like, CME/Cboe/CFE order-lifecycle export with positives and matched normal controls, or explicit same-exhibit `FLIP`-as-control approval.",
        "",
    ])
    md_path.write_text("\n".join(lines))

    assertions = [
        f"gate_result={GATE}",
        f"files_scanned={len(rows)}",
        f"exact_required_files_found={exact_required_files_found}",
        f"exact_required_package_present={str(exact_required_package_present).lower()}",
        f"verifier_native_hint_files={verifier_native_hints}",
        f"strong_lifecycle_hint_files={strong_lifecycle_hints}",
        "accepted_rows_added=0",
        "valid_required_root_unlock=false",
        "source_control_evidence_acquired=false",
        "canonical_merge=false",
        "selected_data_autoquant_promotion=false",
        "downstream_promotion_rerun=false",
        "strict_full_objective=false",
        "trade_usable=false",
        "promotion_allowed=false",
        "update_goal=false",
    ]
    assertions_path = CHECK_ROOT / "tomac_local_schema_classifier_after_083108_v1_assertions.out"
    assertions_path.write_text("\n".join(assertions) + "\n")

    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
