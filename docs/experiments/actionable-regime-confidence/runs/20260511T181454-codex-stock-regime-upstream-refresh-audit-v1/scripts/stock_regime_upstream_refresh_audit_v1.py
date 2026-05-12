#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pandas as pd


RUN_ID = "20260511T181454+0800-codex-stock-regime-upstream-refresh-audit-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs/20260511T181454-codex-stock-regime-upstream-refresh-audit-v1")
OUT_DIR = RUN_ROOT / "upstream-refresh"
CHECK_DIR = RUN_ROOT / "checks"
TMP_ROOT = Path("/tmp/ict-engine-kaggle-stock-regime-upstream-refresh")
DATASET = "mafaqbhatti/stock-market-regimes-20002026"
LOCAL_ROOT = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026")
LOCAL_CSV = LOCAL_ROOT / "stock_market_regimes_2000_2026.csv"
LOCAL_PARQUET = LOCAL_ROOT / "stock_market_regimes_2000_2026.parquet"


def run_cmd(args: list[str]) -> str:
    result = subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result.stdout


def parse_kaggle_files(text: str) -> list[dict]:
    rows: list[dict] = []
    for line in text.splitlines():
        line = line.rstrip()
        if not line or line.startswith("name") or set(line.strip()) <= {"-", " "}:
            continue
        match = re.match(r"^(?P<name>\S+)\s+(?P<size>\d+)\s+(?P<creation>.+?)\s*$", line)
        if not match:
            continue
        rows.append(
            {
                "name": match.group("name"),
                "size": int(match.group("size")),
                "creationDate": match.group("creation"),
            }
        )
    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)

    metadata_stdout = run_cmd(["kaggle", "datasets", "metadata", DATASET, "-p", str(TMP_ROOT)])
    metadata_path = TMP_ROOT / "dataset-metadata.json"
    metadata_raw = metadata_path.read_text()
    try:
        metadata = json.loads(metadata_raw)
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
    except Exception:
        metadata = {"raw": metadata_raw}

    files_stdout = run_cmd(["kaggle", "datasets", "files", DATASET])
    files = parse_kaggle_files(files_stdout)

    source = pd.read_csv(LOCAL_CSV, usecols=["date", "ticker", "regime_label"])
    local_summary = {
        "csv_size": LOCAL_CSV.stat().st_size,
        "parquet_size": LOCAL_PARQUET.stat().st_size,
        "rows": int(len(source)),
        "tickers": int(source["ticker"].nunique()),
        "date_min": str(source["date"].min()),
        "date_max": str(source["date"].max()),
        "regime_counts": {str(k): int(v) for k, v in source["regime_label"].value_counts().to_dict().items()},
    }

    csv_file = next((row for row in files if row["name"] == LOCAL_CSV.name), None)
    parquet_file = next((row for row in files if row["name"] == LOCAL_PARQUET.name), None)
    upstream_same_csv_size = bool(csv_file and csv_file["size"] == local_summary["csv_size"])
    upstream_same_parquet_size = bool(parquet_file and parquet_file["size"] == local_summary["parquet_size"])
    source_tail_closed = local_summary["date_max"] == "2026-01-30"
    no_recency_extension = upstream_same_csv_size and upstream_same_parquet_size and source_tail_closed

    result = {
        "run_id": RUN_ID,
        "dataset": DATASET,
        "dataset_url": f"https://www.kaggle.com/datasets/{DATASET}",
        "purpose": "Check whether the upstream stock-market-regimes source package has newer source-owned labels that can satisfy Board A recency extension.",
        "metadata_stdout": metadata_stdout.strip(),
        "metadata": metadata,
        "kaggle_files": files,
        "local_summary": local_summary,
        "upstream_same_csv_size": upstream_same_csv_size,
        "upstream_same_parquet_size": upstream_same_parquet_size,
        "source_tail_closed": source_tail_closed,
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "gate_result": "stock_regime_upstream_refresh_audit_v1=no_new_upstream_recency_extension",
        "decision": "blocked_no_new_upstream_source_rows" if no_recency_extension else "needs_manual_review",
        "reason": "Kaggle upstream file listing matches the local CSV/parquet sizes and the local source labels still end at 2026-01-30; no source-owned recency extension is available from this upstream package.",
        "next_action": "Keep source-panel recency extension blocked until a source owner publishes post-2026-01-30 labels or the required /tmp intake files are supplied.",
    }

    json_path = OUT_DIR / "stock_regime_upstream_refresh_audit_v1.json"
    report_path = OUT_DIR / "stock_regime_upstream_refresh_audit_v1.md"
    files_path = OUT_DIR / "stock_regime_upstream_refresh_audit_v1_files.txt"
    metadata_copy = OUT_DIR / "dataset-metadata.json"
    checks_path = CHECK_DIR / "stock_regime_upstream_refresh_audit_v1_assertions.out"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    files_path.write_text(files_stdout)
    metadata_copy.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")

    report = f"""# Stock Regime Upstream Refresh Audit v1

Run ID: `{RUN_ID}`

This audit checks the upstream Kaggle source package for source-owned labels newer than the local stock-market-regimes panel. It records metadata and file listings only; it does not download or commit raw source rows.

## Decision

`stock_regime_upstream_refresh_audit_v1=no_new_upstream_recency_extension`

- Dataset: `{DATASET}`
- Dataset URL: `https://www.kaggle.com/datasets/{DATASET}`
- Local source max date: `{local_summary['date_max']}`.
- Local rows / tickers: `{local_summary['rows']}` / `{local_summary['tickers']}`.
- Upstream CSV size matches local: `{str(upstream_same_csv_size).lower()}`.
- Upstream parquet size matches local: `{str(upstream_same_parquet_size).lower()}`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Full objective achieved: `false`.
- `update_goal`: `false`.

## Why It Blocks

The upstream file listing does not expose a newer source-panel revision. The local CSV size is `{local_summary['csv_size']}` bytes and the upstream CSV listing is `{csv_file['size'] if csv_file else 'missing'}` bytes. The local parquet size is `{local_summary['parquet_size']}` bytes and the upstream parquet listing is `{parquet_file['size'] if parquet_file else 'missing'}` bytes.

The source labels still end at `2026-01-30`, so the `2026-01-30` recency blocker remains live. Provider candles after that date cannot be promoted into source labels.

## Artifacts

- JSON: `{json_path}`
- Kaggle file listing: `{files_path}`
- Metadata JSON: `{metadata_copy}`
- Assertions: `{checks_path}`

## Next

Keep `source_panel_recency_extension_manifest_v1` fail-closed until a source owner publishes post-`2026-01-30` rows or the required `/tmp/ict-engine-source-panel-recency-extension` intake files are supplied.
"""
    report_path.write_text(report)

    assertions = [
        ("kaggle_files_seen", len(files) >= 5),
        ("local_source_tail_2026_01_30", source_tail_closed),
        ("upstream_csv_size_matches_local", upstream_same_csv_size),
        ("upstream_parquet_size_matches_local", upstream_same_parquet_size),
        ("accepted_rows_added_zero", result["accepted_rows_added"] == 0),
        ("new_confidence_gate_false", result["new_confidence_gate"] is False),
        ("full_objective_false", result["full_objective_achieved"] is False),
        ("no_raw_data_commit", result["raw_data_committed"] is False),
    ]
    lines = [f"PASS {name}" if ok else f"FAIL {name}" for name, ok in assertions]
    failed = [name for name, ok in assertions if not ok]
    if failed:
        lines.append(f"FAILED_ASSERTIONS {','.join(failed)}")
        checks_path.write_text("\n".join(lines) + "\n")
        raise SystemExit(1)
    lines.append("ALL_ASSERTIONS_PASS")
    checks_path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
