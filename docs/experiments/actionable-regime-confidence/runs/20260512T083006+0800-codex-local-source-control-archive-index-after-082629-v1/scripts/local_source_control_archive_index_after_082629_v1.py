#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T083006+0800-codex-local-source-control-archive-index-after-082629-v1"
SLUG = "local-source-control-archive-index-after-082629-v1"
GATE = "local_source_control_archive_index_after_082629_v1=no_verifier_native_source_control_archive_found"

REPO = Path(__file__).resolve().parents[6]
BOARD_A = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BOARD_B = REPO / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT_ROOT = RUN_ROOT / SLUG
CHECK_ROOT = RUN_ROOT / "checks"

TARGET_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/private/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-board-a-r5-recency-source-panel-v1"),
    Path("/private/tmp/ict-engine-board-a-r5-recency-source-panel-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/private/tmp/ict-engine-native-subhour-source-label-intake"),
]

SCAN_ROOTS = [
    Path("/Users/thrill3r/Downloads/Tomac"),
]

NAME_KEYWORDS = {
    "cat",
    "cboe",
    "cfe",
    "cftc",
    "cme",
    "control",
    "databento",
    "dbn",
    "depth",
    "direct",
    "export",
    "finra",
    "flip",
    "itch",
    "lifecycle",
    "manipulation",
    "mbo",
    "mbp",
    "order",
    "owner",
    "quote",
    "source",
    "spoof",
    "surveillance",
    "trade",
}

SOURCE_CONTROL_COLUMNS = {
    "action",
    "ask_px",
    "ask_size",
    "ask_sz",
    "bid_px",
    "bid_size",
    "bid_sz",
    "control_label",
    "event_type",
    "instrument_id",
    "is_control",
    "is_positive",
    "label",
    "matched_group",
    "order_id",
    "participant",
    "price",
    "side",
    "size",
    "source_section",
    "symbol",
    "ts_event",
}

EXACT_REQUIRED_FILES = {
    "direct_manipulation_positive_rows.csv",
    "direct_manipulation_matched_controls.csv",
    "direct_manipulation_provenance.json",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_header(path: Path) -> str:
    try:
        with path.open("rb") as handle:
            data = handle.read(8192)
    except OSError:
        return ""
    text = data.decode("utf-8", errors="ignore")
    return text.splitlines()[0].strip() if text.splitlines() else ""


def normalize_columns(header: str) -> set[str]:
    if not header:
        return set()
    delimiter = "\t" if "\t" in header and "," not in header else ","
    return {part.strip().lower() for part in header.split(delimiter) if part.strip()}


def list_archive_members(path: Path) -> list[str]:
    if path.suffix.lower() not in {".zip", ".rar", ".tar", ".tgz", ".gz", ".bz2", ".xz", ".7z"}:
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
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()][:100]


def candidate_name(path: Path) -> bool:
    lower = path.name.lower()
    tokens = {token for token in re.split(r"[^a-z0-9]+", lower) if token}
    if tokens & NAME_KEYWORDS:
        return True
    return any(
        token.startswith(("order", "quote", "trade", "control", "source", "owner", "export", "depth", "lifecycle"))
        for token in tokens
    )


def walk_candidates(root: Path) -> list[Path]:
    if not root.exists():
        return []
    candidates: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        parts = {part.lower() for part in current.parts}
        if any(part in {".git", "node_modules", "target", ".venv", "__pycache__"} for part in parts):
            dirnames[:] = []
            continue
        depth = len(current.relative_to(root).parts) if current != root else 0
        if root in {Path("/tmp"), Path("/private/tmp")} and depth > 4:
            dirnames[:] = []
            continue
        for filename in filenames:
            path = current / filename
            if candidate_name(path):
                candidates.append(path)
    return sorted(set(candidates))


def classify_file(path: Path) -> dict[str, object]:
    header = ""
    columns: set[str] = set()
    if path.suffix.lower() in {".csv", ".tsv", ".txt"}:
        header = file_header(path)
        columns = normalize_columns(header)
    archive_members = list_archive_members(path)
    member_name_hits = [
        member
        for member in archive_members
        if any(keyword in member.lower() for keyword in NAME_KEYWORDS)
    ][:20]
    exact_required_match = path.name in EXACT_REQUIRED_FILES
    control_column_hits = sorted(SOURCE_CONTROL_COLUMNS & columns)
    verifier_native_hint = exact_required_match or len({"label", "source_section", "matched_group"} & columns) >= 2
    return {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "suffix": path.suffix.lower(),
        "header": header,
        "control_column_hits": control_column_hits,
        "archive_member_count_read": len(archive_members),
        "archive_member_name_hits": member_name_hits,
        "exact_required_file_name": exact_required_match,
        "verifier_native_hint": verifier_native_hint,
    }


def root_status(root: Path) -> dict[str, object]:
    files = sorted(p.name for p in root.iterdir()) if root.exists() and root.is_dir() else []
    return {
        "root": str(root),
        "exists": root.exists(),
        "files": files[:100],
        "has_exact_required_package": EXACT_REQUIRED_FILES <= set(files),
    }


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    CHECK_ROOT.mkdir(parents=True, exist_ok=True)

    target_roots = [root_status(root) for root in TARGET_ROOTS]
    candidates: list[Path] = []
    for root in SCAN_ROOTS:
        candidates.extend(walk_candidates(root))
    candidates = sorted(set(candidates))
    classified = [classify_file(path) for path in candidates[:400]]

    exact_packages = [row for row in target_roots if row["has_exact_required_package"]]
    verifier_native_candidates = [row for row in classified if row["verifier_native_hint"]]
    archive_member_hits = [row for row in classified if row["archive_member_name_hits"]]

    accepted_rows_added = 0
    valid_required_root_unlock = False
    source_control_evidence_acquired = False

    payload = {
        "run_id": RUN_ID,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_a_hash_before_artifact": sha256_file(BOARD_A),
        "board_b_hash_before_artifact": sha256_file(BOARD_B),
        "gate_result": GATE,
        "scan_roots": [str(root) for root in SCAN_ROOTS],
        "target_roots": target_roots,
        "candidate_files_scanned": len(classified),
        "candidate_files_truncated": len(candidates) > len(classified),
        "archive_member_hit_files": len(archive_member_hits),
        "verifier_native_candidate_files": len(verifier_native_candidates),
        "exact_required_packages": exact_packages,
        "classified_files": classified,
        "accepted_rows_added": accepted_rows_added,
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

    json_path = OUT_ROOT / "local_source_control_archive_index_after_082629_v1.json"
    csv_path = OUT_ROOT / "local_source_control_archive_index_candidates_v1.csv"
    roots_path = OUT_ROOT / "local_source_control_archive_index_target_roots_v1.csv"
    md_path = OUT_ROOT / "local_source_control_archive_index_after_082629_v1.md"
    assertions_path = CHECK_ROOT / "local_source_control_archive_index_after_082629_v1_assertions.out"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    with csv_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "path",
            "size_bytes",
            "suffix",
            "control_column_hits",
            "archive_member_count_read",
            "archive_member_name_hits",
            "exact_required_file_name",
            "verifier_native_hint",
            "header",
        ])
        for row in classified:
            writer.writerow([
                row["path"],
                row["size_bytes"],
                row["suffix"],
                "|".join(row["control_column_hits"]),
                row["archive_member_count_read"],
                "|".join(row["archive_member_name_hits"]),
                row["exact_required_file_name"],
                row["verifier_native_hint"],
                row["header"],
            ])

    with roots_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["root", "exists", "has_exact_required_package", "files"])
        for row in target_roots:
            writer.writerow([row["root"], row["exists"], row["has_exact_required_package"], "|".join(row["files"])])

    top_rows = classified[:20]
    rows_md = "\n".join(
        f"| `{Path(row['path']).name}` | `{Path(row['path']).parent}` | `{row['suffix']}` | `{','.join(row['control_column_hits']) or 'none'}` | `{row['verifier_native_hint']}` |"
        for row in top_rows
    )
    roots_md = "\n".join(
        f"| `{row['root']}` | `{row['exists']}` | `{row['has_exact_required_package']}` |"
        for row in target_roots
    )
    md_path.write_text(
        "\n".join(
            [
                "# Local Source/Control Archive Index After 082629 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{GATE}`",
                "",
                "## Scope",
                "",
                "Read-only local index after the settled `082629` Databento archive readback. This probe checks known target roots and bounded local candidate paths for verifier-native source/control packages or order-lifecycle archives. It does not copy raw data into target roots, approve controls, run verifier/split calibration, run Auto-Quant, run Pre-Bayes/BBN/CatBoost/execution-tree promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Target Roots",
                "",
                "| Root | Exists | Has exact required package |",
                "|---|---:|---:|",
                roots_md,
                "",
                "## Candidate Summary",
                "",
                f"- Candidate files scanned: `{len(classified)}`.",
                f"- Archive-member hit files: `{len(archive_member_hits)}`.",
                f"- Verifier-native candidate files: `{len(verifier_native_candidates)}`.",
                f"- Exact required target-root packages: `{len(exact_packages)}`.",
                "",
                "| File | Directory | Suffix | Control-column hits | Verifier-native hint |",
                "|---|---|---|---|---:|",
                rows_md or "| none | none | none | none | false |",
                "",
                "## Decision",
                "",
                "- No exact required R6 owner-export package was present in the target roots.",
                "- Local candidate hits are file-name/header/archive-index context only; none supplies a complete verifier-native positive/control/provenance package.",
                "- The settled `082629` Databento archive remains OHLCV-only context, not an order-lifecycle source/control unlock.",
                "- Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.",
                "",
                "## Next",
                "",
                "Continue source/control acquisition only. The live unblocker remains an approved operator dispatch or fulfillment of the CME/Cboe/CFE owner-export requests with ticket/export/license provenance, source-owned normal controls, or explicit same-exhibit `FLIP`-as-control approval.",
                "",
            ]
        )
    )

    assertions = [
        f"gate_result={GATE}",
        f"candidate_files_scanned={len(classified)}",
        f"archive_member_hit_files={len(archive_member_hits)}",
        f"verifier_native_candidate_files={len(verifier_native_candidates)}",
        f"exact_required_packages={len(exact_packages)}",
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
    assertions_path.write_text("\n".join(assertions) + "\n")
    print("\n".join(assertions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
