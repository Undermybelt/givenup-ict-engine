from __future__ import annotations

import csv
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T195604+0800-codex-native-provider-cross-timeframe-acquisition-preflight-v1"
ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
CSV_DIR = ROOT / "provider-csv"
REPORT_DIR = ROOT / "native-provider-cross-timeframe-acquisition-preflight-v1"

PYTHON = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
FETCH_EXTERNAL = Path("scripts/auto_quant_external/fetch_external.py")

START = "2025-01-01"
END = "2026-05-12"


@dataclass(frozen=True)
class FetchSpec:
    provider: str
    provider_key: str
    market: str
    symbol: str
    timeframe: str
    command_kind: str
    requested_span: str = f"{START}..{END}"
    unsupported_reason: str | None = None


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def run_command(name: str, cmd: list[str], env: dict[str, str] | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    write_text(OUT_DIR / f"{name}.cmd", " ".join(cmd) + "\n")
    write_text(OUT_DIR / f"{name}.stdout", proc.stdout)
    write_text(OUT_DIR / f"{name}.stderr", proc.stderr)
    write_text(CHECK_DIR / f"{name}.exit", f"{proc.returncode}\n")
    return proc.returncode, proc.stdout, proc.stderr


def csv_path_for(spec: FetchSpec) -> Path:
    safe_provider = spec.provider_key.lower().replace("/", "_").replace("-", "_")
    safe_symbol = spec.symbol.lower().replace(":", "_").replace("/", "_").replace("-", "_").replace("^", "")
    return CSV_DIR / f"{safe_provider}_{safe_symbol}_{spec.timeframe}.csv"


def fetch_cmd(spec: FetchSpec, output: Path) -> list[str] | None:
    if spec.unsupported_reason:
        return None
    if spec.command_kind == "yahoo":
        return [
            str(PYTHON),
            str(FETCH_EXTERNAL),
            "yahoo",
            "--symbol",
            spec.symbol,
            "--interval",
            spec.timeframe,
            "--start",
            START,
            "--end",
            END,
            "--output",
            str(output),
        ]
    if spec.command_kind == "binance":
        return [
            str(PYTHON),
            str(FETCH_EXTERNAL),
            "binance-kline",
            "--symbol",
            spec.symbol,
            "--interval",
            spec.timeframe,
            "--start",
            START,
            "--end",
            END,
            "--output",
            str(output),
        ]
    if spec.command_kind == "bybit":
        return [
            str(PYTHON),
            str(FETCH_EXTERNAL),
            "bybit-kline",
            "--category",
            "linear",
            "--symbol",
            spec.symbol,
            "--interval",
            spec.timeframe,
            "--start",
            START,
            "--end",
            END,
            "--output",
            str(output),
        ]
    if spec.command_kind == "kraken":
        return [
            str(PYTHON),
            str(FETCH_EXTERNAL),
            "kraken-kline",
            "--market",
            "spot",
            "--pair",
            spec.symbol,
            "--interval",
            spec.timeframe,
            "--start",
            START,
            "--end",
            END,
            "--output",
            str(output),
        ]
    if spec.command_kind == "ibkr":
        bar_size = {"1h": "1 hour", "1d": "1 day"}[spec.timeframe]
        duration = "1 Y" if spec.timeframe == "1h" else "2 Y"
        return [
            str(PYTHON),
            str(FETCH_EXTERNAL),
            "ibkr-historical",
            "--symbol",
            spec.symbol,
            "--sec-type",
            "STK",
            "--exchange",
            "SMART",
            "--currency",
            "USD",
            "--primary-exchange",
            "ARCA",
            "--bar-size",
            bar_size,
            "--duration",
            duration,
            "--what-to-show",
            "TRADES",
            "--host",
            "127.0.0.1",
            "--port",
            "4002",
            "--client-id",
            "63",
            "--output",
            str(output),
        ]
    if spec.command_kind == "tvr_harness":
        request = {
            "market_key": f"board-a-195604-{spec.provider_key}-{spec.symbol}-{spec.timeframe}",
            "interval": spec.timeframe,
            "start": f"{START}T00:00:00Z",
            "end": f"{END}T00:00:00Z",
            "count": 12000,
            "related_roles": ["crypto_reference"],
            "provider_preferences": {"crypto_reference": "tradingview_mcp"},
            "symbol_overrides": {
                "crypto_reference": {
                    "display_symbol": spec.symbol,
                    "tradingview_mcp": spec.symbol,
                }
            },
        }
        request_path = ROOT / "requests" / f"tvr_{spec.symbol.replace(':', '_').lower()}_{spec.timeframe}.json"
        write_json(request_path, request)
        return [
            "./target/debug/ict-engine",
            "market-data-harness",
            "--action",
            "fetch",
            "--request-json",
            str(request_path),
        ]
    raise ValueError(f"unknown command kind: {spec.command_kind}")


def normalize_harness_stdout_to_csv(stdout: str, output: Path) -> int:
    if not stdout.strip():
        return 0
    payload = json.loads(stdout)
    results = payload.get("results") or []
    if not results or not results[0].get("ok"):
        return 0
    rows = results[0].get("data") or []
    with output.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["date", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "date": row.get("timestamp") or row.get("date"),
                    "open": row.get("open"),
                    "high": row.get("high"),
                    "low": row.get("low"),
                    "close": row.get("close"),
                    "volume": row.get("volume", 0),
                }
            )
    return len(rows)


def csv_stats(path: Path, timeframe: str) -> dict[str, Any]:
    if not path.exists():
        return {"rows": 0, "actual_start": None, "actual_end": None, "gap_count_gt_expected": None, "max_gap_hours": None}
    raw = pd.read_csv(path)
    if raw.empty:
        return {"rows": 0, "actual_start": None, "actual_end": None, "gap_count_gt_expected": None, "max_gap_hours": None}
    date_col = "date" if "date" in raw.columns else "timestamp" if "timestamp" in raw.columns else raw.columns[0]
    dates = pd.to_datetime(raw[date_col], utc=True, errors="coerce").dropna().sort_values()
    if dates.empty:
        return {"rows": len(raw), "actual_start": None, "actual_end": None, "gap_count_gt_expected": None, "max_gap_hours": None}
    diffs = dates.diff().dropna().dt.total_seconds() / 3600.0
    expected = {"1h": 1.0, "4h": 4.0, "1d": 24.0}.get(timeframe, 1.0)
    return {
        "rows": int(len(raw)),
        "actual_start": dates.iloc[0].isoformat(),
        "actual_end": dates.iloc[-1].isoformat(),
        "gap_count_gt_expected": int((diffs > expected * 1.5).sum()) if not diffs.empty else 0,
        "max_gap_hours": float(diffs.max()) if not diffs.empty else 0.0,
    }


def specs() -> list[FetchSpec]:
    out: list[FetchSpec] = []
    for tf in ["1h", "1d"]:
        out.append(FetchSpec("yfinance/YF", "yfinance", "equity", "SPY", tf, "yahoo"))
    out.append(FetchSpec("yfinance/YF", "yfinance", "equity", "SPY", "4h", "unsupported", unsupported_reason="fetch_external_yahoo_supports_1h_and_1d_not_native_4h"))
    for tf in ["1h", "1d"]:
        out.append(FetchSpec("IBKR", "ibkr", "equity", "SPY", tf, "ibkr"))
    out.append(FetchSpec("IBKR", "ibkr", "equity", "SPY", "4h", "unsupported", unsupported_reason="ibkr_fetch_external_declares_1_hour_and_1_day_bars_only_for_this_wrapper"))
    for provider, key, command in [
        ("Binance", "binance", "binance"),
        ("Bybit", "bybit", "bybit"),
        ("Kraken", "kraken", "kraken"),
    ]:
        symbol = "XBTUSD" if key == "kraken" else "BTCUSDT"
        for tf in ["1h", "4h", "1d"]:
            out.append(FetchSpec(provider, key, "crypto", symbol, tf, command))
    for tf in ["1h", "4h", "1d"]:
        out.append(FetchSpec("TradingViewRemix/TVR", "tvr", "crypto", "BINANCE:BTCUSDT", tf, "tvr_harness"))
    return out


def main() -> int:
    for path in [OUT_DIR, CHECK_DIR, CSV_DIR, REPORT_DIR, ROOT / "requests"]:
        path.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(specs(), start=1):
        output = csv_path_for(spec)
        name = f"{index:02d}_{spec.provider_key}_{spec.symbol.replace(':', '_').lower()}_{spec.timeframe}"
        cmd = fetch_cmd(spec, output)
        exit_code = None
        stdout = ""
        stderr = ""
        if cmd is None:
            write_text(CHECK_DIR / f"{name}.exit", "unsupported\n")
        else:
            exit_code, stdout, stderr = run_command(name, cmd)
            if spec.command_kind == "tvr_harness" and exit_code == 0:
                normalize_harness_stdout_to_csv(stdout, output)
        stats = csv_stats(output, spec.timeframe)
        rows.append(
            {
                "provider": spec.provider,
                "provider_key": spec.provider_key,
                "market": spec.market,
                "symbol": spec.symbol,
                "timeframe": spec.timeframe,
                "requested_span": spec.requested_span,
                "command_kind": spec.command_kind,
                "exit": exit_code,
                "unsupported_reason": spec.unsupported_reason,
                "csv": str(output) if output.exists() else None,
                "provider_direct_native": bool(output.exists() and stats["rows"] > 0 and not spec.unsupported_reason),
                "derived_from_other_timeframe": False,
                "stderr_tail": stderr[-500:] if stderr else "",
                **stats,
            }
        )
    csv_out = REPORT_DIR / "native_provider_cross_timeframe_matrix_v1.csv"
    with csv_out.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    provider_count = len({row["provider"] for row in rows})
    native_success = sum(1 for row in rows if row["provider_direct_native"])
    unsupported = sum(1 for row in rows if row["unsupported_reason"])
    failed = sum(1 for row in rows if row["exit"] not in (0, None) and not row["unsupported_reason"])
    payload = {
        "run_id": RUN_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider_count": provider_count,
        "timeframe_requests": len(rows),
        "provider_direct_native_successes": native_success,
        "unsupported_cells": unsupported,
        "failed_cells": failed,
        "providers": sorted({row["provider"] for row in rows}),
        "rows": rows,
        "promotion_allowed": False,
        "trade_usable": False,
        "accepted_95_contexts_added": 0,
    }
    write_json(REPORT_DIR / "native_provider_cross_timeframe_acquisition_preflight_v1.json", payload)
    md = [
        "# Native Provider Cross-Timeframe Acquisition Preflight v1",
        "",
        f"Providers: `{provider_count}`.",
        f"Timeframe requests: `{len(rows)}`.",
        f"Provider-direct native successes: `{native_success}`.",
        f"Unsupported cells: `{unsupported}`.",
        f"Failed cells: `{failed}`.",
        "",
        "This is acquisition/preflight evidence only. It does not add accepted >=95 contexts, does not train CatBoost, and does not unlock execution by itself.",
        "",
    ]
    write_text(REPORT_DIR / "native_provider_cross_timeframe_acquisition_preflight_v1.md", "\n".join(md))
    write_text(CHECK_DIR / "native_provider_cross_timeframe_acquisition_preflight_v1.exit", "0\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
