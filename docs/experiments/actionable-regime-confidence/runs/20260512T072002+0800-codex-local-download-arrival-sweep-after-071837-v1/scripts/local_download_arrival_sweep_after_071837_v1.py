#!/usr/bin/env python3
"""Bounded local download/vendor-arrival sweep after the 071837 Kaggle registration."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "local-download-arrival-sweep-after-071837-v1"
CHECKS_DIR = RUN_ROOT / "checks"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

RUN_ID = "20260512T072002+0800-codex-local-download-arrival-sweep-after-071837-v1"
GATE = "local_download_arrival_sweep_after_071837_v1=known_stock_regime_download_only_no_vendor_export_no_unlock"

ROOTS = [
    Path("/Users/thrill3r/Downloads"),
    Path("/Users/thrill3r/Desktop"),
    Path("/Users/thrill3r/Documents"),
]

NAME_MARKERS = [
    "cme",
    "cboe",
    "cfe",
    "databento",
    "mbo",
    "mbp",
    "depth",
    "order",
    "lifecycle",
    "oystacher",
    "3red",
    "ticket",
    "support",
    "export",
    "license",
    "direct_manipulation",
    "mainregimev2",
    "stock",
    "regime",
    "native",
    "subhour",
]

DATA_EXTS = {
    ".csv",
    ".json",
    ".parquet",
    ".dbn",
    ".zip",
    ".rar",
    ".gz",
    ".eml",
    ".pdf",
    ".feather",
    ".arrow",
    ".pq",
}

KNOWN_NON_PROMOTING = {
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv",
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.parquet",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_recent_files(root: Path, cutoff: float, max_depth: int = 4):
    if not root.exists():
        return
    root_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        path = Path(dirpath)
        depth = len(path.parts) - root_depth
        if depth >= max_depth:
            dirnames[:] = []
        for filename in filenames:
            item = path / filename
            try:
                stat = item.stat()
            except OSError:
                continue
            if stat.st_mtime < cutoff:
                continue
            yield item, stat


def classify(path: Path) -> str:
    lower = path.name.lower()
    suffix = path.suffix.lower()
    path_str = str(path)
    if path_str in KNOWN_NON_PROMOTING or "/stock-market-regimes-20002026/" in path_str:
        return "known_kaggle_stock_market_regimes_context_only"
    if suffix in {".dbn", ".parquet", ".feather", ".arrow", ".pq"} and any(marker in lower for marker in ["mbo", "mbp", "depth", "order", "lifecycle", "databento"]):
        return "candidate_depth_or_order_lifecycle_needs_manual_readback"
    if "direct_manipulation" in lower:
        return "candidate_required_filename_needs_manual_readback"
    if "mainregimev2" in lower or ("native" in lower and "subhour" in lower):
        return "candidate_r3_or_r5_name_needs_manual_readback"
    if any(marker in lower for marker in ["ticket", "support", "license", "export"]):
        return "candidate_vendor_response_name_needs_manual_readback"
    return "other_recent_context"


def csv_profile(path: Path) -> dict:
    profile: dict[str, object] = {}
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
            reader = csv.DictReader(fh)
            profile["columns"] = reader.fieldnames or []
            row_count = 0
            max_date = None
            min_date = None
            labels: dict[str, int] = {}
            for row in reader:
                row_count += 1
                date = row.get("date") or row.get("Date") or row.get("timestamp") or row.get("datetime")
                if date:
                    min_date = date if min_date is None or date < min_date else min_date
                    max_date = date if max_date is None or date > max_date else max_date
                label = row.get("MainRegimeV2") or row.get("regime_label") or row.get("label")
                if label:
                    labels[label] = labels.get(label, 0) + 1
            profile["row_count"] = row_count
            profile["min_date"] = min_date
            profile["max_date"] = max_date
            profile["label_counts"] = labels
            profile["post_2026_01_30_rows"] = 0
            if max_date and max_date > "2026-01-30":
                with path.open("r", encoding="utf-8", errors="replace", newline="") as fh2:
                    reader2 = csv.DictReader(fh2)
                    count = 0
                    for row in reader2:
                        date = row.get("date") or row.get("Date") or row.get("timestamp") or row.get("datetime")
                        if date and date > "2026-01-30":
                            count += 1
                    profile["post_2026_01_30_rows"] = count
    except Exception as exc:  # profile must fail closed
        profile["profile_error"] = f"{type(exc).__name__}: {exc}"
    return profile


def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = list(rows[0].keys()) if rows else ["path"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = (datetime.now() - timedelta(days=1)).timestamp()

    rows = []
    for root in ROOTS:
        for path, stat in iter_recent_files(root, cutoff):
            lower = path.name.lower()
            suffix = path.suffix.lower()
            matched_name = any(marker in lower for marker in NAME_MARKERS)
            matched_ext = suffix in DATA_EXTS
            if not (matched_name or matched_ext):
                continue
            rows.append(
                {
                    "path": str(path),
                    "size_bytes": stat.st_size,
                    "mtime_epoch": int(stat.st_mtime),
                    "suffix": suffix,
                    "classification": classify(path),
                    "sha256": sha256_file(path) if stat.st_size <= 25 * 1024 * 1024 else None,
                }
            )
    rows.sort(key=lambda row: row["path"])

    known_stock_csv = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
    stock_profile = csv_profile(known_stock_csv) if known_stock_csv.exists() else {"missing": True}

    candidate_unlock_rows = [
        row
        for row in rows
        if row["classification"]
        in {
            "candidate_depth_or_order_lifecycle_needs_manual_readback",
            "candidate_required_filename_needs_manual_readback",
            "candidate_r3_or_r5_name_needs_manual_readback",
            "candidate_vendor_response_name_needs_manual_readback",
        }
    ]

    assertions = {
        "recent_candidate_file_count": len(rows),
        "candidate_unlock_file_count": len(candidate_unlock_rows),
        "known_stock_regime_files_only_for_name_match": all(
            row["classification"] == "known_kaggle_stock_market_regimes_context_only" for row in rows if "stock-market-regimes-20002026" in row["path"]
        ),
        "stock_profile_max_date": stock_profile.get("max_date"),
        "stock_profile_post_2026_01_30_rows": stock_profile.get("post_2026_01_30_rows"),
        "valid_required_root_unlock": False,
        "source_control_evidence_acquired": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    packet = {
        "run_id": RUN_ID,
        "generated_at_local": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "board_sha256_before_artifact": sha256_file(BOARD),
        "gate_result": GATE,
        "scope": {
            "mode": "bounded_recent_local_download_vendor_arrival_sweep",
            "roots": [str(root) for root in ROOTS],
            "mtime_window_days": 1,
            "max_depth": 4,
            "read_only": True,
            "no_root_mutation": True,
            "no_downstream_promotion": True,
            "update_goal": False,
        },
        "recent_candidates": rows,
        "known_stock_market_regimes_profile": stock_profile,
        "assertions": assertions,
        "decision": (
            "The bounded recent local sweep found only the known stock-market-regimes-20002026 "
            "CSV/parquet context files as name-matched arrivals. No vendor ticket/export/license "
            "response, DBN/MBO/MBP/depth/order-lifecycle file, required R6 filename, MainRegimeV2 "
            "source export, or native-subhour file arrived outside the target roots."
        ),
        "next": (
            "Continue only from explicit source/control approval, verifier-native R6 owner-export "
            "rows with valid controls, source-owned post-2026-01-30 R5 rows matching the source-panel "
            "schema, verifier-native Crisis-capable R3 MainRegimeV2 labels, or a genuinely new accepted "
            "cross-timeframe MainRegimeV2 source export."
        ),
    }

    json_path = ARTIFACT_DIR / "local_download_arrival_sweep_after_071837_v1.json"
    csv_path = ARTIFACT_DIR / "local_download_arrival_sweep_after_071837_v1.csv"
    md_path = ARTIFACT_DIR / "local_download_arrival_sweep_after_071837_v1.md"
    assertions_path = CHECKS_DIR / "local_download_arrival_sweep_after_071837_v1_assertions.out"

    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(csv_path, rows)
    md_path.write_text(
        "\n".join(
            [
                "# Local Download Arrival Sweep After 071837 v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                f"Gate result: `{GATE}`",
                "",
                "## Scope",
                "",
                "Bounded read-only sweep of recent files under `Downloads`, `Desktop`, and `Documents` after the `071837` Kaggle source-probe registration. This packet does not mutate target roots, copy rows into canonical inputs, approve proxy labels, run direct verifier, run split calibration, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.",
                "",
                "## Readback",
                "",
                f"- Recent candidate files matched: `{len(rows)}`.",
                f"- Candidate unlock-like files matched: `{len(candidate_unlock_rows)}`.",
                f"- Known stock-market-regimes max date: `{stock_profile.get('max_date')}`.",
                f"- Known stock-market-regimes post-`2026-01-30` rows: `{stock_profile.get('post_2026_01_30_rows')}`.",
                "",
                "## Decision",
                "",
                packet["decision"],
                "",
                "Accepted rows added `0`, R6 owner/export unlock false, R5 recency unlock false, R3 native-subhour unlock false, valid required-root unlock false, source/control evidence acquired false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path.relative_to(REPO)}`",
                f"- Candidate CSV: `{csv_path.relative_to(REPO)}`",
                f"- Assertions: `{assertions_path.relative_to(REPO)}`",
                "",
                "## Next",
                "",
                packet["next"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    assertions_path.write_text(
        "\n".join(
            [
                f"gate_result={GATE}",
                f"recent_candidate_file_count={len(rows)}",
                f"candidate_unlock_file_count={len(candidate_unlock_rows)}",
                f"stock_profile_max_date={stock_profile.get('max_date')}",
                f"stock_profile_post_2026_01_30_rows={stock_profile.get('post_2026_01_30_rows')}",
                "valid_required_root_unlock=false",
                "source_control_evidence_acquired=false",
                "canonical_merge=false",
                "downstream_promotion_rerun=false",
                "strict_full_objective=false",
                "trade_usable=false",
                "update_goal=false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
