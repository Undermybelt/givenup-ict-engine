#!/usr/bin/env python3
"""Attempt Binance and Bybit public crypto matrices under the uv wrapper."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T073000+0800-codex-binance-bybit-public-matrix"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T073000-codex-binance-bybit-public-matrix"
OUT_DIR = RUN_ROOT / "public-crypto-matrix"
CHECK_DIR = RUN_ROOT / "checks"
RAW_ROOT = Path("/private/tmp/ict-regime-binance-bybit-public-matrix-20260511T073000")
FETCH_EXTERNAL = REPO / "scripts/auto_quant_external/fetch_external.py"

SYMBOLS = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "SOL": "SOLUSDT",
}
TIMEFRAME_WINDOWS = {
    "1m": ("2026-05-03", "2026-05-10", "1m"),
    "5m": ("2026-04-10", "2026-05-10", "5m"),
    "15m": ("2026-04-01", "2026-05-10", "15m"),
    "30m": ("2026-04-01", "2026-05-10", "30m"),
    "1h": ("2026-04-01", "2026-05-10", "1h"),
    "4h": ("2025-05-10", "2026-05-10", "4h"),
    "1d": ("2024-05-10", "2026-05-10", "1d"),
    "1w": ("2021-05-10", "2026-05-10", "1w"),
    "1mo": ("2021-05-10", "2026-05-10", "1M"),
}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def run_cmd(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def read_csv_summary(path: Path) -> dict[str, Any]:
    df = pd.read_csv(path)
    if df.empty:
        return {"rows": 0, "first_ts": "", "last_ts": ""}
    ts_col = "date" if "date" in df.columns else df.columns[0]
    return {
        "rows": int(len(df)),
        "first_ts": str(pd.to_datetime(df[ts_col]).min()),
        "last_ts": str(pd.to_datetime(df[ts_col]).max()),
    }


def fetch_cell(provider: str, symbol_name: str, exchange_symbol: str, timeframe: str, exchange_interval: str, start: str, end: str) -> dict[str, Any]:
    raw_path = RAW_ROOT / provider / f"{exchange_symbol}_{timeframe}.csv"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    if provider == "binance_public":
        cmd = [
            sys.executable,
            str(FETCH_EXTERNAL),
            "binance-kline",
            "--symbol",
            exchange_symbol,
            "--interval",
            exchange_interval,
            "--start",
            start,
            "--end",
            end,
            "--output",
            str(raw_path),
        ]
    elif provider == "bybit_public":
        cmd = [
            sys.executable,
            str(FETCH_EXTERNAL),
            "bybit-kline",
            "--category",
            "linear",
            "--symbol",
            exchange_symbol,
            "--interval",
            exchange_interval,
            "--start",
            start,
            "--end",
            end,
            "--output",
            str(raw_path),
        ]
    else:
        raise ValueError(provider)
    proc = run_cmd(cmd)
    row: dict[str, Any] = {
        "provider": provider,
        "symbol": symbol_name,
        "exchange_symbol": exchange_symbol,
        "timeframe": timeframe,
        "exchange_interval": exchange_interval,
        "start": start,
        "end": end,
        "raw_csv": str(raw_path),
        "raw_committed": False,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip()[-500:],
        "stderr": proc.stderr.strip()[-500:],
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
    }
    if proc.returncode != 0:
        row.update({"status": "fetch_failed", "reason": f"returncode={proc.returncode}", "rows": 0, "first_ts": "", "last_ts": ""})
    elif not raw_path.exists():
        row.update({"status": "fetch_failed", "reason": "fetch_returned_success_but_output_missing", "rows": 0, "first_ts": "", "last_ts": ""})
    else:
        summary = read_csv_summary(raw_path)
        row.update({"status": "ok" if summary["rows"] > 0 else "empty", "reason": "", **summary})
    return row


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    RAW_ROOT.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for provider in ["binance_public", "bybit_public"]:
        for symbol_name, exchange_symbol in SYMBOLS.items():
            for timeframe, (start, end, exchange_interval) in TIMEFRAME_WINDOWS.items():
                rows.append(fetch_cell(provider, symbol_name, exchange_symbol, timeframe, exchange_interval, start, end))

    ok_rows = [row for row in rows if row["status"] == "ok"]
    failed_rows = [row for row in rows if row["status"] == "fetch_failed"]
    empty_rows = [row for row in rows if row["status"] == "empty"]

    report = {
        "run_id": RUN_ID,
        "goal_achieved": False,
        "objective": "Attempt Binance and Bybit public crypto data matrices for BTC/ETH/SOL across the Board A timeframe ladder.",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "providers": ["binance_public", "bybit_public"],
        "symbols": sorted(SYMBOLS),
        "timeframes": list(TIMEFRAME_WINDOWS),
        "cell_count": len(rows),
        "ok_cell_count": len(ok_rows),
        "failed_cell_count": len(failed_rows),
        "empty_cell_count": len(empty_rows),
        "raw_root": str(RAW_ROOT),
        "raw_ohlcv_committed": False,
        "rows": rows,
        "completion_accounting": {
            "actual_data_fetch_attempted": True,
            "accepted_full_cycle_full_universe": False,
            "why_not_accepted": [
                "Binance/Bybit public data availability is not independent MainRegimeV2 root-label calibration.",
                "Fetched bars still need independent source-backed root labels or unsupported-label disposition.",
                "TradingViewRemix and non-public/operator lanes remain separate from this public crypto matrix.",
            ],
        },
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "gate_result": "binance_bybit_public_matrix_built_root_confidence_pending",
        "next_action": "Refresh the full coverage disposition matrix with Binance/Bybit public data cells before attempting IBKR or a completion audit.",
        "artifacts": {
            "summary_json": rel(OUT_DIR / "binance_bybit_public_matrix.json"),
            "summary_md": rel(OUT_DIR / "binance_bybit_public_matrix.md"),
            "summary_csv": rel(OUT_DIR / "binance_bybit_public_matrix.csv"),
            "assertions": rel(CHECK_DIR / "binance_bybit_public_matrix_assertions.out"),
            "script": rel(Path(__file__)),
        },
    }

    (OUT_DIR / "binance_bybit_public_matrix.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    with (OUT_DIR / "binance_bybit_public_matrix.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    by_provider = {provider: sum(1 for row in rows if row["provider"] == provider and row["status"] == "ok") for provider in ["binance_public", "bybit_public"]}
    lines = [
        "# Binance + Bybit Public Matrix",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "Goal achieved: `false`",
        "",
        f"- Cells attempted: `{len(rows)}`",
        f"- OK cells: `{len(ok_rows)}`",
        f"- Failed cells: `{len(failed_rows)}`",
        f"- Empty cells: `{len(empty_rows)}`",
        f"- Binance OK cells: `{by_provider['binance_public']}`",
        f"- Bybit OK cells: `{by_provider['bybit_public']}`",
        "- Raw OHLCV committed: `false`",
        "",
        "Gate result: `binance_bybit_public_matrix_built_root_confidence_pending`",
        "",
        "Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
    ]
    (OUT_DIR / "binance_bybit_public_matrix.md").write_text("\n".join(lines) + "\n")

    assertion_lines = [
        "goal_achieved=false",
        f"cell_count={len(rows)}",
        f"ok_cell_count={len(ok_rows)}",
        f"failed_cell_count={len(failed_rows)}",
        f"empty_cell_count={len(empty_rows)}",
        f"binance.ok_cell_count={by_provider['binance_public']}",
        f"bybit.ok_cell_count={by_provider['bybit_public']}",
        "actual_data_fetch_attempted=true",
        "accepted_full_cycle_full_universe=false",
        "raw_ohlcv_committed=false",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "trade_usable=false",
        "gate_result=binance_bybit_public_matrix_built_root_confidence_pending",
    ]
    (CHECK_DIR / "binance_bybit_public_matrix_assertions.out").write_text("\n".join(assertion_lines) + "\n")
    print(rel(OUT_DIR / "binance_bybit_public_matrix.json"))


if __name__ == "__main__":
    main()
