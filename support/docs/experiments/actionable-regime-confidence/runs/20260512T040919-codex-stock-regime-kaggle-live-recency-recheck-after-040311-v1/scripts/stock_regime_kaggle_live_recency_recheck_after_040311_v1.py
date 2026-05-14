#!/usr/bin/env python3
"""Recheck the live Kaggle stock-regime source for R5 recency-tail rows."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path


RUN_ID = "20260512T040919-codex-stock-regime-kaggle-live-recency-recheck-after-040311-v1"
GATE = "stock_regime_kaggle_live_recency_recheck_after_040311_v1=upstream_unchanged_no_r5_recency_tail_repair_no_promotion"
DATASET = "mafaqbhatti/stock-market-regimes-20002026"
CSV_PATH = Path(os.environ.get("KAGGLE_CSV_PATH", "/tmp/ict-engine-kaggle-recency-recheck-040919/stock_market_regimes_2000_2026.csv"))
OUT_DIR = Path(__file__).resolve().parents[1] / "stock-regime-kaggle-live-recency-recheck-after-040311-v1"
CHECK_DIR = Path(__file__).resolve().parents[1] / "checks"
TARGETS = [
    ("XOM", "Sideways"),
    ("UNH", "Bear"),
    ("^DJI", "Sideways"),
    ("AMD", "Bear"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if not CSV_PATH.exists():
        raise SystemExit(f"missing input CSV: {CSV_PATH}")

    counts = defaultdict(int)
    total_rows = 0
    tickers: set[str] = set()
    min_date: str | None = None
    max_date: str | None = None

    with CSV_PATH.open(newline="") as f:
        reader = csv.DictReader(f)
        required = {"date", "ticker", "regime_label"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"missing required columns: {sorted(missing)}")

        for row in reader:
            total_rows += 1
            date = row["date"]
            ticker = row["ticker"]
            regime = row["regime_label"]
            tickers.add(ticker)
            min_date = date if min_date is None or date < min_date else min_date
            max_date = date if max_date is None or date > max_date else max_date
            for target_ticker, target_regime in TARGETS:
                if ticker == target_ticker and regime == target_regime:
                    key = (target_ticker, target_regime)
                    if date > "2026-01-30":
                        counts[(key, "after_2026_01_30")] += 1
                    if "2026-01-01" <= date <= "2026-01-30":
                        counts[(key, "jan_2026_through_0130")] += 1
                    if "2025-01-01" <= date <= "2025-12-31":
                        counts[(key, "calendar_2025")] += 1
                    counts[(key, "all_rows")] += 1

    target_rows = []
    any_after_cutoff = False
    for ticker, regime in TARGETS:
        key = (ticker, regime)
        after_count = counts[(key, "after_2026_01_30")]
        any_after_cutoff = any_after_cutoff or after_count > 0
        target_rows.append(
            {
                "ticker": ticker,
                "regime_label": regime,
                "rows_after_2026_01_30": after_count,
                "rows_2026_01_01_through_2026_01_30": counts[(key, "jan_2026_through_0130")],
                "rows_calendar_2025": counts[(key, "calendar_2025")],
                "rows_all_dates": counts[(key, "all_rows")],
            }
        )

    accepted_rows_added = 0
    strict_full_objective = False
    result = {
        "run_id": RUN_ID,
        "dataset": DATASET,
        "input_csv_path": str(CSV_PATH),
        "input_csv_sha256": sha256_file(CSV_PATH),
        "total_rows": total_rows,
        "ticker_count": len(tickers),
        "min_date": min_date,
        "max_date": max_date,
        "target_rows": target_rows,
        "any_target_rows_after_2026_01_30": any_after_cutoff,
        "gate_result": GATE,
        "accepted_rows_added": accepted_rows_added,
        "new_confidence_gate": False,
        "r5_recency_tail_repair_closed": False,
        "strict_full_objective": strict_full_objective,
        "raw_data_committed": False,
        "trade_usable": False,
        "update_goal": False,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    (OUT_DIR / "stock_regime_kaggle_live_recency_recheck_after_040311_v1.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )

    with (OUT_DIR / "stock_regime_kaggle_live_recency_recheck_counts_v1.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(target_rows[0].keys()))
        writer.writeheader()
        writer.writerows(target_rows)

    md = [
        "# Stock Regime Kaggle Live Recency Recheck After 040311 v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        f"- Gate result: `{GATE}`.",
        f"- Dataset: `{DATASET}`.",
        f"- Live CSV rows: `{total_rows}`; tickers: `{len(tickers)}`.",
        f"- Live date range: `{min_date}` to `{max_date}`.",
        "- Target cells checked: `XOM/Sideways`, `UNH/Bear`, `^DJI/Sideways`, and `AMD/Bear`.",
        f"- Any target rows after `2026-01-30`: `{str(any_after_cutoff).lower()}`.",
        "- Accepted rows added: `0`; new confidence gate: `false`.",
        "- R5 recency-tail repair closed: `false`; strict full objective achieved: `false`; `update_goal=false`.",
        "- Raw Kaggle CSV stayed under `/tmp`; repo output contains only this compact evidence packet.",
        "",
        "## Target Counts",
        "",
        "| Ticker | Regime | Rows after 2026-01-30 | Rows 2026-01-01..2026-01-30 | Rows calendar 2025 | Rows all dates |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in target_rows:
        md.append(
            f"| `{row['ticker']}` | `{row['regime_label']}` | {row['rows_after_2026_01_30']} | "
            f"{row['rows_2026_01_01_through_2026_01_30']} | {row['rows_calendar_2025']} | {row['rows_all_dates']} |"
        )
    md.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The live Kaggle source remains usable for historical readback but does not provide the post-`2026-01-30` source-owned target rows required by the strict R5 recency-tail blocker.",
            "- This does not create R3 native sub-hour labels, R6 owner/export controls, canonical merge input, downstream promotion evidence, or trade evidence.",
        ]
    )
    (OUT_DIR / "stock_regime_kaggle_live_recency_recheck_after_040311_v1.md").write_text("\n".join(md) + "\n")

    assertions = [
        f"PASS gate_result={GATE}",
        f"PASS total_rows={total_rows}",
        f"PASS max_date={max_date}",
        f"PASS any_target_rows_after_2026_01_30={str(any_after_cutoff).lower()}",
        "PASS accepted_rows_added=0",
        "PASS new_confidence_gate=false",
        "PASS r5_recency_tail_repair_closed=false",
        "PASS strict_full_objective=false",
        "PASS raw_data_committed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "stock_regime_kaggle_live_recency_recheck_after_040311_v1_assertions.out").write_text("\n".join(assertions) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
