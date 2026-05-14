#!/usr/bin/env python3
"""Fail-closed verifier for source-panel recency extension rows."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path


REQUIRED_COLUMNS = ['date', 'ticker', 'close', 'returns', 'volatility', 'regime_label', 'regime_confidence', 'macro_context', 'unemployment_rate', 'fed_funds_rate', 'cpi', '10y_treasury', '2y_treasury', 'vix']
EXPECTED_TICKERS = set(['AAPL', 'ABBV', 'AMD', 'AMZN', 'BA', 'BAC', 'CAT', 'COP', 'CSCO', 'CVX', 'DIS', 'GE', 'GOOGL', 'GS', 'HD', 'INTC', 'JNJ', 'JPM', 'MCD', 'META', 'MS', 'MSFT', 'NFLX', 'NKE', 'NVDA', 'PFE', 'SBUX', 'T', 'TMO', 'TSLA', 'UNH', 'VZ', 'WFC', 'WMT', 'XOM', '^DJI', '^GSPC', '^IXIC', '^RUT'])
ROOTS = ['Bear', 'Bull', 'Crisis', 'Sideways']
LAST_SOURCE_DATE = datetime.strptime('2026-01-30', "%Y-%m-%d").date()
REQUIRED_FILES = {
    "extension_rows": "stock_market_regimes_2026_extension.csv",
    "provenance_manifest": "source_panel_recency_provenance.json",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intake-root", required=True)
    args = parser.parse_args()
    root = Path(args.intake_root)
    rows_path = root / REQUIRED_FILES["extension_rows"]
    provenance_path = root / REQUIRED_FILES["provenance_manifest"]
    missing = [str(path) for path in [rows_path, provenance_path] if not path.exists()]
    if missing:
        print(json.dumps({"status": "blocked", "reason": "missing_required_files", "missing_files": missing}, indent=2))
        return 2

    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    with rows_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in (reader.fieldnames or [])]
        if missing_cols:
            print(json.dumps({"status": "blocked", "reason": "missing_columns", "missing_columns": missing_cols}, indent=2))
            return 2
        rows = list(reader)
    if not rows:
        print(json.dumps({"status": "blocked", "reason": "empty_extension_rows"}, indent=2))
        return 2
    bad_dates = []
    bad_labels = []
    seen = set()
    duplicates = 0
    tickers = set()
    for row in rows:
        key = (row["date"], row["ticker"])
        if key in seen:
            duplicates += 1
        seen.add(key)
        tickers.add(row["ticker"])
        day = datetime.strptime(row["date"], "%Y-%m-%d").date()
        if day <= LAST_SOURCE_DATE:
            bad_dates.append(row["date"])
        if row["regime_label"] not in ROOTS:
            bad_labels.append(row["regime_label"])
    unknown_tickers = sorted(tickers - EXPECTED_TICKERS)
    if bad_dates or bad_labels or duplicates or unknown_tickers:
        print(json.dumps({
            "status": "blocked",
            "reason": "extension_rows_failed_guardrails",
            "bad_dates_sample": bad_dates[:10],
            "bad_labels_sample": sorted(set(bad_labels))[:10],
            "duplicates": duplicates,
            "unknown_tickers": unknown_tickers[:20],
        }, indent=2))
        return 2
    print(json.dumps({
        "status": "schema_ready_unscored",
        "extension_rows": len(rows),
        "ticker_count": len(tickers),
        "date_min": min(row["date"] for row in rows),
        "date_max": max(row["date"] for row in rows),
        "provenance_keys": sorted(provenance.keys()),
        "next": "append to source panel in /tmp and rerun daily/weekly/monthly/1h source gates"
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
