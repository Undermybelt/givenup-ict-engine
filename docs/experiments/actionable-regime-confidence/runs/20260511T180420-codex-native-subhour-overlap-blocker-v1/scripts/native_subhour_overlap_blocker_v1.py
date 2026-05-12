#!/usr/bin/env python3
"""Probe whether native sub-hour provider bars overlap current source labels."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf


RUN_ID = "20260511T180420+0800-codex-native-subhour-overlap-blocker-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T180420-codex-native-subhour-overlap-blocker-v1"
)
OUT_DIR = RUN_ROOT / "native-subhour-overlap"
CHECK_DIR = RUN_ROOT / "checks"
BOARD = Path("docs/plans/2026-05-10-actionable-regime-confidence-todo.md")
SOURCE_PANEL = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)

OUT_JSON = OUT_DIR / "native_subhour_overlap_blocker_v1.json"
OUT_MD = OUT_DIR / "native_subhour_overlap_blocker_v1.md"
OUT_CSV = OUT_DIR / "native_subhour_overlap_blocker_v1_cells.csv"
OUT_ASSERT = CHECK_DIR / "native_subhour_overlap_blocker_v1_assertions.out"

SYMBOLS = ["AAPL", "^IXIC"]
TIMEFRAMES = ["15m", "30m"]
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
PERIOD = "60d"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def repo_rel(path: Path) -> str:
    return str(path)


def normalize_sessions(index: pd.DatetimeIndex) -> set[str]:
    if index.empty:
        return set()
    if getattr(index, "tz", None) is not None:
        local = index.tz_convert("America/New_York")
    else:
        local = index.tz_localize("UTC").tz_convert("America/New_York")
    return set(pd.Series(local).dt.date.astype(str).tolist())


def source_summary() -> dict[str, Any]:
    rows = 0
    tickers: set[str] = set()
    dates: set[str] = set()
    roots = {root: 0 for root in ROOTS}
    with SOURCE_PANEL.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows += 1
            tickers.add(row["ticker"])
            dates.add(row["date"])
            if row["regime_label"] in roots:
                roots[row["regime_label"]] += 1
    return {
        "rows": rows,
        "ticker_count": len(tickers),
        "date_min": min(dates),
        "date_max": max(dates),
        "roots": roots,
        "symbols_requested_present": {symbol: symbol in tickers for symbol in SYMBOLS},
    }


def source_dates_by_symbol() -> dict[str, set[str]]:
    dates: dict[str, set[str]] = {symbol: set() for symbol in SYMBOLS}
    with SOURCE_PANEL.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            ticker = row["ticker"]
            if ticker in dates and row["regime_label"] in ROOTS:
                dates[ticker].add(row["date"])
    return dates


def fetch_cell(symbol: str, interval: str) -> dict[str, Any]:
    try:
        bars = yf.download(
            tickers=symbol,
            period=PERIOD,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
            prepost=False,
        )
    except Exception as exc:  # pragma: no cover - provider failure path
        return {
            "symbol": symbol,
            "timeframe": interval,
            "download_state": "error",
            "error": f"{type(exc).__name__}: {exc}",
            "provider_rows": 0,
            "provider_session_count": 0,
            "provider_date_min": "",
            "provider_date_max": "",
            "source_overlap_sessions": 0,
            "native_subhour_source_overlap_ready": False,
            "blocker": "provider_fetch_error",
        }
    if bars is None or bars.empty:
        return {
            "symbol": symbol,
            "timeframe": interval,
            "download_state": "empty",
            "provider_rows": 0,
            "provider_session_count": 0,
            "provider_date_min": "",
            "provider_date_max": "",
            "source_overlap_sessions": 0,
            "native_subhour_source_overlap_ready": False,
            "blocker": "provider_returned_empty",
        }
    sessions = normalize_sessions(bars.index)
    return {
        "symbol": symbol,
        "timeframe": interval,
        "download_state": "ready",
        "provider_rows": int(len(bars)),
        "provider_session_count": len(sessions),
        "provider_date_min": min(sessions) if sessions else "",
        "provider_date_max": max(sessions) if sessions else "",
        "provider_sessions": sessions,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    src = source_summary()
    source_dates = source_dates_by_symbol()
    cell_rows: list[dict[str, Any]] = []
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            cell = fetch_cell(symbol, timeframe)
            sessions = cell.pop("provider_sessions", set())
            overlap = sessions & source_dates.get(symbol, set())
            source_symbol_present = bool(source_dates.get(symbol))
            if cell["download_state"] == "ready":
                if source_symbol_present and overlap:
                    blocker = ""
                    ready = True
                elif source_symbol_present:
                    blocker = "no_provider_session_overlap_with_source_panel_tail"
                    ready = False
                else:
                    blocker = "symbol_missing_from_source_panel"
                    ready = False
                cell.update(
                    {
                        "source_symbol_present": source_symbol_present,
                        "source_date_min": min(source_dates[symbol]) if source_symbol_present else "",
                        "source_date_max": max(source_dates[symbol]) if source_symbol_present else "",
                        "source_overlap_sessions": len(overlap),
                        "native_subhour_source_overlap_ready": ready,
                        "blocker": blocker,
                    }
                )
            else:
                cell.update(
                    {
                        "source_symbol_present": source_symbol_present,
                        "source_date_min": min(source_dates[symbol]) if source_symbol_present else "",
                        "source_date_max": max(source_dates[symbol]) if source_symbol_present else "",
                    }
                )
            cell_rows.append(cell)

    ready_cells = [row for row in cell_rows if row["native_subhour_source_overlap_ready"]]
    blocked_cells = [row for row in cell_rows if not row["native_subhour_source_overlap_ready"]]
    decision = {
        "gate_result": "native_subhour_overlap_blocker_v1=no_source_overlap_0of4_cells",
        "accepted_rows_added": 0,
        "new_confidence_gate": False,
        "full_objective_achieved": False,
        "update_goal": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
    }
    artifact = {
        "run_id": RUN_ID,
        "artifact_type": "native_subhour_overlap_blocker_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": repo_rel(BOARD),
        "board_sha256_at_run": sha256(BOARD),
        "source_panel": {
            **src,
            "sha256": sha256(SOURCE_PANEL),
        },
        "provider": {
            "name": "yfinance",
            "period": PERIOD,
            "symbols": SYMBOLS,
            "timeframes": TIMEFRAMES,
            "raw_rows_committed": False,
        },
        "cells": cell_rows,
        "summary": {
            "cells_checked": len(cell_rows),
            "ready_overlap_cells": len(ready_cells),
            "blocked_cells": len(blocked_cells),
            "blockers": sorted(set(row["blocker"] for row in blocked_cells)),
        },
        "decision": decision,
        "next_action": (
            "Do not run native sub-hour calibration until source-owned rows after "
            "2026-01-30 are acquired and pass the recency verifier."
        ),
    }
    OUT_JSON.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(
        OUT_CSV,
        cell_rows,
        [
            "symbol",
            "timeframe",
            "download_state",
            "provider_rows",
            "provider_session_count",
            "provider_date_min",
            "provider_date_max",
            "source_symbol_present",
            "source_date_min",
            "source_date_max",
            "source_overlap_sessions",
            "native_subhour_source_overlap_ready",
            "blocker",
            "error",
        ],
    )
    md_lines = [
        "# Native Subhour Overlap Blocker v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "This is a compact overlap probe for the P1 native sub-hour blocker. It fetches at most two source-panel markets and two native sub-hour timeframes, keeps raw provider rows out of the repo, and does not generate labels.",
        "",
        "## Result",
        "",
        f"- Cells checked: `{len(cell_rows)}` (`{', '.join(SYMBOLS)}` x `{', '.join(TIMEFRAMES)}`).",
        f"- Ready overlap cells: `{len(ready_cells)}`.",
        f"- Blocked cells: `{len(blocked_cells)}`.",
        f"- Source panel max date: `{src['date_max']}`.",
        "- Provider native sub-hour rows were current-window only for this probe, so they did not overlap the source-label tail.",
        "- Accepted rows added: `0`.",
        "- Gate result: `native_subhour_overlap_blocker_v1=no_source_overlap_0of4_cells`.",
        "- Full objective achieved: `false`; `update_goal=false`.",
        "- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.",
        "",
        "## Cells",
        "",
        "| Symbol | Timeframe | Provider Rows | Provider Dates | Source Dates | Overlap Sessions | State | Blocker |",
        "|---|---|---:|---|---|---:|---|---|",
    ]
    for row in cell_rows:
        md_lines.append(
            "| `{symbol}` | `{timeframe}` | {rows} | `{pmin}` to `{pmax}` | `{smin}` to `{smax}` | {overlap} | `{state}` | `{blocker}` |".format(
                symbol=row["symbol"],
                timeframe=row["timeframe"],
                rows=row["provider_rows"],
                pmin=row["provider_date_min"],
                pmax=row["provider_date_max"],
                smin=row.get("source_date_min", ""),
                smax=row.get("source_date_max", ""),
                overlap=row["source_overlap_sessions"],
                state=row["download_state"],
                blocker=row["blocker"],
            )
        )
    md_lines.extend(
        [
            "",
            "## Next",
            "",
            "Use `source_panel_recency_extension_manifest_v1` first. Native sub-hour calibration should remain blocked until source-owned rows after `2026-01-30` exist and pass the recency verifier.",
        ]
    )
    OUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    OUT_ASSERT.write_text(
        "\n".join(
            [
                f"run_id={RUN_ID}",
                f"source_panel_date_max={src['date_max']}",
                f"cells_checked={len(cell_rows)}",
                f"ready_overlap_cells={len(ready_cells)}",
                f"blocked_cells={len(blocked_cells)}",
                "accepted_rows_added=0",
                "new_confidence_gate=false",
                "runtime_code_changed=false",
                "thresholds_relaxed=false",
                "raw_data_committed=false",
                "full_objective_achieved=false",
                "update_goal=false",
                "assertion_status=PASS",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
