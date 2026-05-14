#!/usr/bin/env python3
"""Build a yfinance data-availability matrix for the expanded Board A scope.

This script writes compact summaries only. It does not commit raw OHLCV data
and does not claim regime-confidence completion.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T070440-codex-provider-universe-manifest-readback"
)
OUT_DIR = RUN_ROOT / "yfinance-full-matrix"
REPORT_JSON = OUT_DIR / "yfinance_full_universe_fetch_matrix.json"
REPORT_MD = OUT_DIR / "yfinance_full_universe_fetch_matrix.md"
SUMMARY_CSV = OUT_DIR / "yfinance_full_universe_fetch_matrix.csv"
ASSERTIONS = RUN_ROOT / "checks" / "yfinance_full_universe_fetch_matrix_assertions.out"

SYMBOLS = [
    "CL=F",
    "DIA",
    "ES=F",
    "GC=F",
    "GLD",
    "NQ=F",
    "QQQ",
    "SPY",
    "USO",
    "YM=F",
    "^DJI",
    "^GSPC",
    "^NDX",
    "^VIX",
]

FETCH_PLAN = [
    {"timeframe": "1m", "yf_interval": "1m", "period": "7d", "kind": "native"},
    {"timeframe": "5m", "yf_interval": "5m", "period": "60d", "kind": "native"},
    {"timeframe": "15m", "yf_interval": "15m", "period": "60d", "kind": "native"},
    {"timeframe": "30m", "yf_interval": "30m", "period": "60d", "kind": "native"},
    {"timeframe": "1h", "yf_interval": "1h", "period": "730d", "kind": "native"},
    {"timeframe": "1d", "yf_interval": "1d", "period": "10y", "kind": "native"},
    {"timeframe": "1w", "yf_interval": "1wk", "period": "10y", "kind": "native"},
    {"timeframe": "1mo", "yf_interval": "1mo", "period": "10y", "kind": "native"},
]


def close_frame(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        if "Close" in data.columns.get_level_values(-1):
            return data.xs("Close", axis=1, level=-1, drop_level=True)
        if "Close" in data.columns.get_level_values(0):
            return data.xs("Close", axis=1, level=0, drop_level=True)
    if "Close" in data.columns:
        return data[["Close"]].rename(columns={"Close": SYMBOLS[0]})
    return pd.DataFrame()


def summarize_native(plan: dict[str, str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    try:
        data = yf.download(
            tickers=SYMBOLS,
            period=plan["period"],
            interval=plan["yf_interval"],
            group_by="ticker",
            auto_adjust=False,
            progress=False,
            threads=True,
        )
        closes = close_frame(data)
    except Exception as exc:  # noqa: BLE001 - artifact records provider errors.
        for symbol in SYMBOLS:
            rows.append(
                {
                    "provider": "yfinance",
                    "symbol": symbol,
                    "timeframe": plan["timeframe"],
                    "yf_interval": plan["yf_interval"],
                    "period": plan["period"],
                    "status": "error",
                    "bars": 0,
                    "first_ts": "",
                    "last_ts": "",
                    "reason": type(exc).__name__ + ": " + str(exc)[:200],
                }
            )
        return rows

    for symbol in SYMBOLS:
        series = closes[symbol] if symbol in closes.columns else pd.Series(dtype=float)
        series = series.dropna()
        if len(series) > 0:
            status = "ok"
            first_ts = str(series.index.min())
            last_ts = str(series.index.max())
            reason = ""
        else:
            status = "no_data"
            first_ts = ""
            last_ts = ""
            reason = "empty_close_series"
        rows.append(
            {
                "provider": "yfinance",
                "symbol": symbol,
                "timeframe": plan["timeframe"],
                "yf_interval": plan["yf_interval"],
                "period": plan["period"],
                "status": status,
                "bars": int(len(series)),
                "first_ts": first_ts,
                "last_ts": last_ts,
                "reason": reason,
            }
        )
    return rows


def add_derived_4h(rows: list[dict[str, object]]) -> None:
    one_hour = {
        str(row["symbol"]): row
        for row in rows
        if row["provider"] == "yfinance" and row["timeframe"] == "1h"
    }
    for symbol in SYMBOLS:
        src = one_hour.get(symbol, {})
        bars = int(src.get("bars", 0) or 0)
        if src.get("status") == "ok" and bars >= 32:
            status = "derived_ok"
            reason = "derived_from_1h_summary_only"
        elif src.get("status") == "ok":
            status = "derived_insufficient_bars"
            reason = "1h_bars_below_32"
        else:
            status = "derived_blocked"
            reason = "1h_source_not_ok"
        rows.append(
            {
                "provider": "yfinance",
                "symbol": symbol,
                "timeframe": "4h",
                "yf_interval": "1h",
                "period": "730d",
                "status": status,
                "bars": bars // 4 if status == "derived_ok" else 0,
                "first_ts": src.get("first_ts", ""),
                "last_ts": src.get("last_ts", ""),
                "reason": reason,
            }
        )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ASSERTIONS.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for plan in FETCH_PLAN:
        rows.extend(summarize_native(plan))
    add_derived_4h(rows)

    ok_statuses = {"ok", "derived_ok"}
    ok_cells = [row for row in rows if row["status"] in ok_statuses]
    blocked_cells = [row for row in rows if row["status"] not in ok_statuses]
    by_timeframe = {}
    for timeframe in ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mo"]:
        subset = [row for row in rows if row["timeframe"] == timeframe]
        by_timeframe[timeframe] = {
            "ok": sum(1 for row in subset if row["status"] in ok_statuses),
            "total": len(subset),
        }

    report = {
        "run_id": "20260511T070440+0800-codex-yfinance-full-universe-fetch-matrix",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "goal_achieved": False,
        "provider": "yfinance",
        "symbols": SYMBOLS,
        "timeframes": ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1mo"],
        "raw_ohlcv_committed": False,
        "cell_count": len(rows),
        "ok_cell_count": len(ok_cells),
        "blocked_cell_count": len(blocked_cells),
        "coverage_by_timeframe": by_timeframe,
        "rows": rows,
        "gate_result": "yfinance_full_universe_fetch_matrix_built_root_confidence_pending",
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
    }

    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    with SUMMARY_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# YFinance Full-Universe Fetch Matrix",
        "",
        "Run id: `20260511T070440+0800-codex-yfinance-full-universe-fetch-matrix`",
        "",
        f"Cells: `{len(ok_cells)}` ok / `{len(rows)}` attempted.",
        "",
        "| Timeframe | OK Cells | Total Cells |",
        "|---|---:|---:|",
    ]
    for timeframe, item in by_timeframe.items():
        lines.append(f"| `{timeframe}` | {item['ok']} | {item['total']} |")
    lines.extend(
        [
            "",
            "This is a data-availability matrix only. It does not claim regime-confidence completion.",
            "",
            f"Gate result: `{report['gate_result']}`.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n")

    ASSERTIONS.write_text(
        "\n".join(
            [
                "goal_achieved=false",
                "provider=yfinance",
                f"cell_count={len(rows)}",
                f"ok_cell_count={len(ok_cells)}",
                f"blocked_cell_count={len(blocked_cells)}",
                f"all_timeframes_attempted={str(all(v['total'] == len(SYMBOLS) for v in by_timeframe.values())).lower()}",
                "raw_ohlcv_committed=false",
                f"gate_result={report['gate_result']}",
                "thresholds_relaxed=false",
                "runtime_code_changed=false",
                "trade_usable=false",
            ]
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
