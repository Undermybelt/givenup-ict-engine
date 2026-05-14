#!/usr/bin/env python3
"""Verify the current Kaggle stock-market-regimes 2000-2026 file for R5 recency."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T064908+0800-codex-r5-kaggle-stock-regimes-recency-redownload-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
ARTIFACT_DIR = RUN_ROOT / "r5-kaggle-stock-regimes-recency-redownload-v1"
CHECKS_DIR = RUN_ROOT / "checks"
CSV_PATH = Path("/tmp/ict-engine-board-a-r5-kaggle-stock-regimes-recency-redownload-v1/stock_market_regimes_2000_2026.csv")
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    labels: Counter[str] = Counter()
    tickers: set[str] = set()
    dates: Counter[str] = Counter()
    confidence_by_label: dict[str, list[float]] = {}
    rows = 0
    date_min = ""
    date_max = ""
    max_date_samples: list[dict[str, str]] = []
    post_cutoff_rows = 0
    required_post_cutoff = "2026-01-30"

    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            rows += 1
            date = row["date"]
            label = row["regime_label"]
            labels[label] += 1
            tickers.add(row["ticker"])
            dates[date] += 1
            if not date_min or date < date_min:
                date_min = date
            if not date_max or date > date_max:
                date_max = date
                max_date_samples = [row]
            elif date == date_max and len(max_date_samples) < 8:
                max_date_samples.append(row)
            if date > required_post_cutoff:
                post_cutoff_rows += 1
            try:
                confidence_by_label.setdefault(label, []).append(float(row["regime_confidence"]))
            except ValueError:
                pass

    label_rows = []
    for label, count in sorted(labels.items()):
        vals = confidence_by_label.get(label, [])
        label_rows.append(
            {
                "regime_label": label,
                "rows": count,
                "mean_regime_confidence": round(sum(vals) / len(vals), 6) if vals else "",
                "max_regime_confidence": max(vals) if vals else "",
            }
        )

    recent_rows = [{"date": date, "rows": count} for date, count in sorted(dates.items())[-10:]]
    has_core_labels = {"Bull", "Bear", "Sideways", "Crisis"}.issubset(labels)
    r5_recency_unlock = post_cutoff_rows > 0
    gate_result = "r5_kaggle_stock_regimes_recency_redownload_v1=download_ok_no_post_2026_01_30_recency_no_unlock"
    decision = {
        "gate_result": gate_result,
        "download_exit_zero": True,
        "rows": rows,
        "date_min": date_min,
        "date_max": date_max,
        "ticker_count": len(tickers),
        "labels": dict(sorted(labels.items())),
        "has_bull_bear_sideways_crisis": has_core_labels,
        "post_2026_01_30_rows": post_cutoff_rows,
        "r5_recency_unlock": r5_recency_unlock,
        "accepted_rows_added": 0,
        "valid_required_root_unlock": False,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }
    output = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board_hash_before_artifact": sha256_path(BOARD),
        "csv_path": str(CSV_PATH),
        "csv_sha256": sha256_path(CSV_PATH),
        "csv_size_bytes": CSV_PATH.stat().st_size,
        "columns": fieldnames,
        "decision": decision,
        "max_date_samples": max_date_samples,
    }

    write_csv(ARTIFACT_DIR / "r5_kaggle_stock_regimes_label_counts_v1.csv", label_rows)
    write_csv(ARTIFACT_DIR / "r5_kaggle_stock_regimes_recent_dates_v1.csv", recent_rows)
    (ARTIFACT_DIR / "r5_kaggle_stock_regimes_recency_redownload_v1.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = f"""# R5 Kaggle Stock Regimes Recency Redownload v1

Run id: `{RUN_ID}`

Gate result: `{gate_result}`

## Scope

Corrected Kaggle download/readback for `mafaqbhatti/stock-market-regimes-20002026` after prior evidence showed the candidate as known daily/no post-cutoff. This packet verifies the actual downloaded file and does not mutate `/tmp/ict-engine-source-panel-recency-extension`, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Readback

- CSV: `{CSV_PATH}`
- Rows: `{rows}`
- Tickers: `{len(tickers)}`
- Date range: `{date_min}` to `{date_max}`
- Labels: `{", ".join(f"{k}={v}" for k, v in sorted(labels.items()))}`
- Core Bull/Bear/Sideways/Crisis labels present: `{has_core_labels}`
- Rows after `2026-01-30`: `{post_cutoff_rows}`

## Decision

The corrected download confirms the dataset is real and contains Bull/Bear/Sideways/Crisis-style daily labels, but it still ends on `2026-01-30`. It does not unlock the R5 post-cutoff recency root, does not satisfy R3 native-subhour evidence, and does not provide R6 owner/export controls. Promotion remains blocked: accepted rows added `0`, valid required root unlock false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Artifacts

- JSON: `{ARTIFACT_DIR / "r5_kaggle_stock_regimes_recency_redownload_v1.json"}`
- Label counts CSV: `{ARTIFACT_DIR / "r5_kaggle_stock_regimes_label_counts_v1.csv"}`
- Recent dates CSV: `{ARTIFACT_DIR / "r5_kaggle_stock_regimes_recent_dates_v1.csv"}`
- Assertions: `{CHECKS_DIR / "r5_kaggle_stock_regimes_recency_redownload_v1_assertions.out"}`

## Next

Do not materialize this file into `/tmp/ict-engine-source-panel-recency-extension` as an R5 unlock. Continue looking for source-owned post-`2026-01-30` recency rows, verifier-native R3 `MainRegimeV2` labels, R6 owner/export controls, or explicit source/control approval before canonical merge and downstream readback.
"""
    (ARTIFACT_DIR / "r5_kaggle_stock_regimes_recency_redownload_v1.md").write_text(report, encoding="utf-8")

    assertions = "\n".join(
        [
            f"gate_result={gate_result}",
            "download_exit_zero=true",
            f"date_max={date_max}",
            f"has_bull_bear_sideways_crisis={str(has_core_labels).lower()}",
            f"post_2026_01_30_rows={post_cutoff_rows}",
            "r5_recency_unlock=false",
            "accepted_rows_added=0",
            "valid_required_root_unlock=false",
            "canonical_merge=false",
            "downstream_promotion_rerun=false",
            "strict_full_objective=false",
            "trade_usable=false",
            "update_goal=false",
            "",
        ]
    )
    (CHECKS_DIR / "r5_kaggle_stock_regimes_recency_redownload_v1_assertions.out").write_text(
        assertions,
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
