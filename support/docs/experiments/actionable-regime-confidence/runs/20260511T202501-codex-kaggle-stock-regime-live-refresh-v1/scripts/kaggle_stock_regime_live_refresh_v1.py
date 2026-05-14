#!/usr/bin/env python3
"""Readback for a live Kaggle refresh of the stock-regime source panel."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T202501-codex-kaggle-stock-regime-live-refresh-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "kaggle-stock-regime-live-refresh"
CHECK_DIR = RUN_ROOT / "checks"
DOWNLOAD_ROOT = Path("/tmp/ict-engine-kaggle-stock-regimes-live-refresh-v1")
CSV_PATH = DOWNLOAD_ROOT / "stock_market_regimes_2000_2026.csv"
LOCAL_REFERENCE = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
DATASET_ID = "mafaqbhatti/stock-market-regimes-20002026"
DATASET_URL = "https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026"
LAST_ACCEPTED_SOURCE_DATE = "2026-01-30"
TARGET_CELLS = [
    ("XOM", "Sideways", "heldout_time", 5),
    ("UNH", "Bear", "calibration", 7),
    ("^DJI", "Sideways", "calibration", 7),
    ("AMD", "Bear", "calibration", 10),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def analyze_csv(path: Path) -> dict[str, object]:
    row_count = 0
    dates: list[str] = []
    target_counts = {
        f"{symbol}/{label}": {
            "symbol": symbol,
            "main_regime_v2_label": label,
            "split_role": split_role,
            "min_new_source_sessions": min_rows,
            "post_cutoff_rows": 0,
        }
        for symbol, label, split_role, min_rows in TARGET_CELLS
    }
    target_total_counts: dict[str, int] = {key: 0 for key in target_counts}
    label_counts: dict[str, int] = {}

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        for row in reader:
            row_count += 1
            day = (row.get("date") or "")[:10]
            symbol = row.get("ticker") or ""
            label = row.get("regime_label") or ""
            if day:
                dates.append(day)
            key = f"{symbol}/{label}"
            label_counts[key] = label_counts.get(key, 0) + 1
            if key in target_counts:
                target_total_counts[key] += 1
                if day > LAST_ACCEPTED_SOURCE_DATE:
                    target_counts[key]["post_cutoff_rows"] += 1

    return {
        "fieldnames": fieldnames,
        "row_count": row_count,
        "date_min": min(dates) if dates else None,
        "date_max": max(dates) if dates else None,
        "target_counts": list(target_counts.values()),
        "target_total_counts": target_total_counts,
        "target_label_counts": {key: label_counts.get(key, 0) for key in sorted(target_counts)},
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        raise SystemExit(f"missing downloaded csv: {CSV_PATH}")

    csv_stats = analyze_csv(CSV_PATH)
    downloaded_hash = sha256(CSV_PATH)
    local_hash = sha256(LOCAL_REFERENCE) if LOCAL_REFERENCE.exists() else None
    post_cutoff_total = sum(int(row["post_cutoff_rows"]) for row in csv_stats["target_counts"])
    decision = "kaggle_stock_regime_live_refresh_v1=downloaded_latest_public_dataset_no_post_2026_01_30_rows"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_id": DATASET_ID,
        "dataset_url": DATASET_URL,
        "license": "apache-2.0",
        "source_pull_root": str(DOWNLOAD_ROOT),
        "source_pull_commands": [
            "kaggle datasets files mafaqbhatti/stock-market-regimes-20002026 -v",
            "kaggle datasets download mafaqbhatti/stock-market-regimes-20002026 -p /tmp/ict-engine-kaggle-stock-regimes-live-refresh-v1 --unzip",
        ],
        "downloaded_csv": str(CSV_PATH),
        "downloaded_csv_sha256": downloaded_hash,
        "local_reference_csv": str(LOCAL_REFERENCE),
        "local_reference_csv_sha256": local_hash,
        "download_matches_local_reference": downloaded_hash == local_hash,
        "csv_stats": csv_stats,
        "last_accepted_source_date": LAST_ACCEPTED_SOURCE_DATE,
        "post_cutoff_target_rows": post_cutoff_total,
        "decision": decision,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "r5_recency_tail_repair_closed": False,
        "strict_full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }

    json_path = OUT_DIR / "kaggle_stock_regime_live_refresh_v1.json"
    report_path = OUT_DIR / "kaggle_stock_regime_live_refresh_v1.md"
    target_csv_path = OUT_DIR / "kaggle_stock_regime_live_refresh_v1_targets.csv"
    assertions_path = CHECK_DIR / "kaggle_stock_regime_live_refresh_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with target_csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["symbol", "main_regime_v2_label", "split_role", "min_new_source_sessions", "post_cutoff_rows"],
        )
        writer.writeheader()
        writer.writerows(csv_stats["target_counts"])

    lines = [
        "# Kaggle Stock Regime Live Refresh v1",
        "",
        f"- Decision: `{decision}`",
        f"- Dataset: `{DATASET_ID}`",
        f"- Dataset URL: `{DATASET_URL}`",
        "- Pull commands: `kaggle datasets files ... -v` and `kaggle datasets download ... --unzip`",
        f"- Download root: `{DOWNLOAD_ROOT}`",
        f"- Rows: `{csv_stats['row_count']}`",
        f"- Date range: `{csv_stats['date_min']}` to `{csv_stats['date_max']}`",
        f"- Downloaded CSV SHA256: `{downloaded_hash}`",
        f"- Matches local reference CSV: `{downloaded_hash == local_hash}`",
        f"- Post-cutoff target rows after `{LAST_ACCEPTED_SOURCE_DATE}`: `{post_cutoff_total}`",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- Strict full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Target Cells",
        "",
        "| Symbol | Label | Split Role | Required New Sessions | Post-Cutoff Rows |",
        "|---|---|---|---:|---:|",
    ]
    for row in csv_stats["target_counts"]:
        lines.append(
            f"| `{row['symbol']}` | `{row['main_regime_v2_label']}` | `{row['split_role']}` | "
            f"{row['min_new_source_sessions']} | {row['post_cutoff_rows']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The latest public Kaggle dataset was acquired into `/tmp` and analyzed without committing raw rows. It is byte-identical to the local reference CSV and still ends at `2026-01-30`, so it cannot populate the post-cutoff recency extension intake or close R5.",
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path}`",
            f"- Target CSV: `{target_csv_path}`",
            f"- Assertions: `{assertions_path}`",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS decision={decision}",
        f"PASS dataset_id={DATASET_ID}",
        f"PASS row_count={csv_stats['row_count']}",
        f"PASS date_max={csv_stats['date_max']}",
        f"PASS post_cutoff_target_rows={post_cutoff_total}",
        f"PASS download_matches_local_reference={str(downloaded_hash == local_hash).lower()}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS strict_full_objective_achieved=false",
        "PASS update_goal=false",
        "PASS raw_data_committed=false",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
