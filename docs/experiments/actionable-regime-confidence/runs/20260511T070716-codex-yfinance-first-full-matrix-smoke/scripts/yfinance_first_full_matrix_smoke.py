#!/usr/bin/env python3
"""Fetch the yfinance-first full symbol/timeframe matrix from the manifest."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T070716+0800-codex-yfinance-first-full-matrix-smoke"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T070716-codex-yfinance-first-full-matrix-smoke"
OUT_DIR = RUN_ROOT / "matrix-smoke"
CHECK_DIR = RUN_ROOT / "checks"
MANIFEST = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T070440-codex-provider-universe-manifest-readback/provider-universe-manifest/provider_universe_manifest_readback.json"
BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"

PERIOD_BY_INTERVAL = {
    "1m": "5d",
    "5m": "60d",
    "15m": "60d",
    "30m": "60d",
    "1h": "730d",
    "4h": "730d",
    "1d": "5y",
    "1w": "10y",
    "1mo": "max",
}

YF_INTERVAL = {
    "1w": "1wk",
}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def load_json(path: Path) -> Any:
    with path.open() as handle:
        return json.load(handle)


def flatten_columns(frame: pd.DataFrame) -> pd.DataFrame:
    if isinstance(frame.columns, pd.MultiIndex):
        frame = frame.copy()
        frame.columns = ["_".join(str(part) for part in col if part) for col in frame.columns]
    return frame


def fetch_cell(symbol: str, interval: str) -> dict[str, Any]:
    yf_interval = YF_INTERVAL.get(interval, interval)
    period = PERIOD_BY_INTERVAL[interval]
    started = time.time()
    try:
        frame = yf.download(
            symbol,
            period=period,
            interval=yf_interval,
            progress=False,
            auto_adjust=False,
            threads=False,
        )
        elapsed = time.time() - started
        frame = flatten_columns(frame)
        rows = int(len(frame.index))
        if rows == 0:
            return {
                "symbol": symbol,
                "interval": interval,
                "yf_interval": yf_interval,
                "period": period,
                "status": "empty",
                "rows": 0,
                "elapsed_seconds": round(elapsed, 3),
            }
        return {
            "symbol": symbol,
            "interval": interval,
            "yf_interval": yf_interval,
            "period": period,
            "status": "ok",
            "rows": rows,
            "date_min": str(frame.index.min()),
            "date_max": str(frame.index.max()),
            "columns": list(frame.columns),
            "elapsed_seconds": round(elapsed, 3),
        }
    except Exception as exc:  # noqa: BLE001 - compact audit must preserve provider error text.
        elapsed = time.time() - started
        return {
            "symbol": symbol,
            "interval": interval,
            "yf_interval": yf_interval,
            "period": period,
            "status": "error",
            "rows": 0,
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
            "elapsed_seconds": round(elapsed, 3),
        }


def summarize(cells: list[dict[str, Any]]) -> dict[str, Any]:
    by_interval: dict[str, dict[str, int]] = {}
    by_symbol: dict[str, dict[str, int]] = {}
    for cell in cells:
        status = cell["status"]
        by_interval.setdefault(cell["interval"], {}).setdefault(status, 0)
        by_interval[cell["interval"]][status] += 1
        by_symbol.setdefault(cell["symbol"], {}).setdefault(status, 0)
        by_symbol[cell["symbol"]][status] += 1
    ok = sum(1 for cell in cells if cell["status"] == "ok")
    empty = sum(1 for cell in cells if cell["status"] == "empty")
    error = sum(1 for cell in cells if cell["status"] == "error")
    return {
        "total_cells": len(cells),
        "ok_cells": ok,
        "empty_cells": empty,
        "error_cells": error,
        "by_interval": by_interval,
        "by_symbol": by_symbol,
        "all_cells_ok": ok == len(cells),
    }


def write_report(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "yfinance_first_full_matrix_smoke.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    summary = report["summary"]
    lines = [
        "# YFinance-First Full Matrix Smoke",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Goal achieved: `{str(report['goal_achieved']).lower()}`",
        "",
        "## Matrix",
        "",
        f"- Symbols: `{len(report['symbols'])}`",
        f"- Intervals: `{', '.join(report['intervals'])}`",
        f"- Cells: `{summary['total_cells']}`",
        f"- OK / empty / error: `{summary['ok_cells']}` / `{summary['empty_cells']}` / `{summary['error_cells']}`",
        "",
        "## Interval Summary",
        "",
        "| Interval | OK | Empty | Error |",
        "|---|---:|---:|---:|",
    ]
    for interval in report["intervals"]:
        row = summary["by_interval"].get(interval, {})
        lines.append(f"| `{interval}` | {row.get('ok', 0)} | {row.get('empty', 0)} | {row.get('error', 0)} |")
    lines.extend([
        "",
        "## Failed / Empty Cells",
        "",
    ])
    failed = [cell for cell in report["cells"] if cell["status"] != "ok"]
    if failed:
        lines.extend(["| Symbol | Interval | Status | Detail |", "|---|---|---|---|"])
        for cell in failed:
            detail = cell.get("error") or "empty dataframe"
            lines.append(f"| `{cell['symbol']}` | `{cell['interval']}` | `{cell['status']}` | `{detail}` |")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "Result: this is a provider reachability/data-availability smoke matrix only. It does not calibrate root-regime confidence across the matrix.",
        "",
    ])
    (OUT_DIR / "yfinance_first_full_matrix_smoke.md").write_text("\n".join(lines))

    assertion_lines = [
        f"goal_achieved={str(report['goal_achieved']).lower()}",
        f"total_cells={summary['total_cells']}",
        f"ok_cells={summary['ok_cells']}",
        f"empty_cells={summary['empty_cells']}",
        f"error_cells={summary['error_cells']}",
        f"all_cells_ok={str(summary['all_cells_ok']).lower()}",
        "root_regime_calibration_executed=false",
    ]
    (CHECK_DIR / "yfinance_first_full_matrix_smoke_assertions.out").write_text("\n".join(assertion_lines) + "\n")


def main() -> None:
    manifest = load_json(MANIFEST)
    inputs = manifest["yfinance_first_matrix_inputs"]
    symbols = inputs["symbols"]
    intervals = inputs["timeframe_ladder"]
    cells = []
    for symbol in symbols:
        for interval in intervals:
            cells.append(fetch_cell(symbol, interval))
    summary = summarize(cells)
    report = {
        "run_id": RUN_ID,
        "objective": str(BOARD) + " yfinance-first full symbol/timeframe availability smoke",
        "source_manifest": rel(MANIFEST),
        "symbols": symbols,
        "intervals": intervals,
        "cells": cells,
        "summary": summary,
        "goal_achieved": False,
        "why_not_complete": [
            "This run only proves which yfinance cells are fetchable.",
            "Root-regime calibration has not yet been rerun across the matrix.",
            "Non-yfinance provider cells remain pending or blocked per provider-status.",
        ],
        "next_action": "Use the fetchable yfinance cells to build a root-regime calibration matrix for Bull/Bear/Sideways/Crisis; keep unavailable cells explicit.",
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "artifacts": {
            "matrix_json": rel(OUT_DIR / "yfinance_first_full_matrix_smoke.json"),
            "matrix_md": rel(OUT_DIR / "yfinance_first_full_matrix_smoke.md"),
            "assertions": rel(CHECK_DIR / "yfinance_first_full_matrix_smoke_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }
    write_report(report)
    print(json.dumps({"goal_achieved": False, "summary": summary}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
