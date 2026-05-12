#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT = RUN_ROOT / "command-output"
CHECKS = RUN_ROOT / "checks"
DATA = RUN_ROOT / "data"
REPORT = RUN_ROOT / "native-provider-timeframe-fetch-probe-v1"
FETCH = REPO / "scripts/auto_quant_external/fetch_external.py"
ENGINE = REPO / "target/debug/ict-engine"
UV = Path.home() / ".local/bin/uv"

START = "2024-05-13"
END = "2026-05-12"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_step(name: str, argv: list[str], timeout: int = 240) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.cmd").write_text(" ".join(argv) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(
            argv,
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        rc = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        rc = 124
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n"
        timed_out = True
    (OUT / f"{name}.out").write_text(stdout, encoding="utf-8")
    (OUT / f"{name}.err").write_text(stderr, encoding="utf-8")
    (CHECKS / f"{name}.exit").write_text(f"{rc}\n", encoding="utf-8")
    return {"name": name, "exit": rc, "timed_out": timed_out, "argv": argv}


def csv_summary(path: Path) -> dict[str, Any]:
    if not path.exists() or path.stat().st_size == 0:
        return {"rows": 0, "first_ts": None, "last_ts": None}
    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            ts = row.get("date") or row.get("timestamp") or row.get("ts")
            if ts:
                rows.append(ts)
    rows.sort()
    return {
        "rows": len(rows),
        "first_ts": rows[0] if rows else None,
        "last_ts": rows[-1] if rows else None,
    }


def write_skip(name: str, reason: str) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.cmd").write_text(f"SKIP {reason}\n", encoding="utf-8")
    (OUT / f"{name}.out").write_text("", encoding="utf-8")
    (OUT / f"{name}.err").write_text(reason + "\n", encoding="utf-8")
    (CHECKS / f"{name}.exit").write_text("125\n", encoding="utf-8")
    return {"name": name, "exit": 125, "timed_out": False, "argv": ["SKIP", reason]}


def fetch_public_tasks() -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    specs = [
        ("yfinance_YF", "yahoo", "SPY", ["1h", "1d"]),
        ("Binance", "binance-kline", "BTCUSDT", ["1h", "4h", "1d"]),
        ("Bybit", "bybit-kline", "BTCUSDT", ["1h", "4h", "1d"]),
        ("Kraken", "kraken-kline", "PF_XBTUSD", ["1h", "4h", "1d"]),
    ]
    for provider, command, symbol, intervals in specs:
        for interval in ["1h", "4h", "1d"]:
            slug = f"{provider}_{symbol}_{interval}".lower().replace("/", "_")
            output = DATA / provider / f"{symbol}_{interval}.csv"
            if interval not in intervals:
                step = write_skip(slug, f"{provider} native {interval} unsupported by fetch_external.py")
            elif command == "yahoo":
                step = run_step(
                    slug,
                    [
                        "python3",
                        str(FETCH),
                        "yahoo",
                        "--symbol",
                        symbol,
                        "--interval",
                        interval,
                        "--start",
                        START,
                        "--end",
                        END,
                        "--output",
                        str(output),
                    ],
                    timeout=300,
                )
            elif command == "binance-kline":
                step = run_step(
                    slug,
                    [
                        "python3",
                        str(FETCH),
                        "binance-kline",
                        "--symbol",
                        symbol,
                        "--interval",
                        interval,
                        "--start",
                        START,
                        "--end",
                        END,
                        "--output",
                        str(output),
                    ],
                    timeout=300,
                )
            elif command == "bybit-kline":
                step = run_step(
                    slug,
                    [
                        "python3",
                        str(FETCH),
                        "bybit-kline",
                        "--category",
                        "linear",
                        "--symbol",
                        symbol,
                        "--interval",
                        interval,
                        "--start",
                        START,
                        "--end",
                        END,
                        "--output",
                        str(output),
                    ],
                    timeout=300,
                )
            else:
                step = run_step(
                    slug,
                    [
                        "python3",
                        str(FETCH),
                        "kraken-kline",
                        "--market",
                        "futures",
                        "--pair",
                        symbol,
                        "--interval",
                        interval,
                        "--start",
                        START,
                        "--end",
                        END,
                        "--output",
                        str(output),
                    ],
                    timeout=300,
                )
            tasks.append(
                {
                    "provider": provider,
                    "symbol": symbol,
                    "interval": interval,
                    "native_fetch_attempted": interval in intervals,
                    "output": rel(output),
                    "step": step,
                    **csv_summary(output),
                }
            )
    return tasks


def fetch_ibkr_tasks() -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    bar_sizes = {"1h": "1 hour", "1d": "1 day"}
    for interval in ["1h", "4h", "1d"]:
        name = f"ibkr_spy_{interval}"
        output = DATA / "IBKR" / f"SPY_{interval}.csv"
        if interval not in bar_sizes:
            step = write_skip(name, "IBKR historical native 4h bar size is not exposed by fetch_external.py")
        else:
            base = [str(UV), "run", "--with", "pandas", "--with", "requests", "--with", "redis", "--with", "ib_async"]
            if not UV.exists():
                base = ["python3"]
            step = run_step(
                name,
                base
                + [
                    str(FETCH),
                    "ibkr-historical",
                    "--symbol",
                    "SPY",
                    "--sec-type",
                    "STK",
                    "--exchange",
                    "SMART",
                    "--currency",
                    "USD",
                    "--primary-exchange",
                    "ARCA",
                    "--bar-size",
                    bar_sizes[interval],
                    "--duration",
                    "1 Y" if interval == "1h" else "2 Y",
                    "--what-to-show",
                    "TRADES",
                    "--port",
                    "4002",
                    "--output",
                    str(output),
                ],
                timeout=300,
            )
        tasks.append(
            {
                "provider": "IBKR",
                "symbol": "SPY",
                "interval": interval,
                "native_fetch_attempted": interval in bar_sizes,
                "output": rel(output),
                "step": step,
                **csv_summary(output),
            }
        )
    return tasks


def fetch_tvr_tasks() -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for interval in ["1h", "4h", "1d"]:
        name = f"tvr_btcusd_{interval}"
        request = {
            "market_key": "board-a-tvr-native-timeframe-probe",
            "interval": interval,
            "start": f"{START}T00:00:00Z",
            "end": f"{END}T00:00:00Z",
            "related_roles": ["reference"],
            "provider_preferences": {"reference": "tradingview_mcp"},
            "symbol_overrides": {
                "reference": {
                    "display_symbol": "BTCUSD",
                    "tradingview_mcp": "BITSTAMP:BTCUSD",
                }
            },
        }
        request_path = DATA / "TradingViewRemix_TVR" / f"request_{interval}.json"
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        step = run_step(
            name,
            [
                str(ENGINE),
                "market-data-harness",
                "--action",
                "fetch",
                "--request-json",
                rel(request_path),
            ],
            timeout=180,
        )
        rows = 0
        first_ts = None
        last_ts = None
        try:
            payload = json.loads((OUT / f"{name}.out").read_text(encoding="utf-8"))
            candles = (((payload.get("results") or [{}])[0].get("data") or {}).get("candles") or [])
            rows = len(candles)
            stamps = sorted(str(c.get("timestamp") or c.get("time") or "") for c in candles if c)
            first_ts = stamps[0] if stamps else None
            last_ts = stamps[-1] if stamps else None
        except Exception:
            pass
        tasks.append(
            {
                "provider": "TradingViewRemix/TVR",
                "symbol": "BITSTAMP:BTCUSD",
                "interval": interval,
                "native_fetch_attempted": True,
                "request": rel(request_path),
                "step": step,
                "rows": rows,
                "first_ts": first_ts,
                "last_ts": last_ts,
            }
        )
    return tasks


def main() -> int:
    REPORT.mkdir(parents=True, exist_ok=True)
    tasks = fetch_public_tasks() + fetch_ibkr_tasks() + fetch_tvr_tasks()
    providers = sorted({item["provider"] for item in tasks})
    intervals = ["1h", "4h", "1d"]
    complete_native = []
    for provider in providers:
        rows_by_interval = {
            item["interval"]: item["rows"]
            for item in tasks
            if item["provider"] == provider and item["step"]["exit"] == 0
        }
        if all(rows_by_interval.get(interval, 0) > 0 for interval in intervals):
            complete_native.append(provider)
    report = {
        "schema_version": "board-a-native-provider-timeframe-fetch-probe-v1",
        "generated_at": now_z(),
        "run_root": rel(RUN_ROOT),
        "requested_start": START,
        "requested_end": END,
        "providers_required": [
            "IBKR",
            "TradingViewRemix/TVR",
            "yfinance/YF",
            "Kraken",
            "Binance",
            "Bybit",
        ],
        "intervals_required": intervals,
        "tasks_total": len(tasks),
        "tasks_exit_zero": sum(1 for item in tasks if item["step"]["exit"] == 0),
        "providers_with_complete_native_1h_4h_1d": complete_native,
        "complete_native_provider_count": len(complete_native),
        "accepted_95_contexts_added": 0,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "tasks": tasks,
    }
    (REPORT / "native_provider_timeframe_fetch_probe_v1.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    rows = [
        [
            "provider",
            "symbol",
            "interval",
            "exit",
            "rows",
            "first_ts",
            "last_ts",
            "native_fetch_attempted",
            "output_or_request",
        ]
    ]
    for item in tasks:
        rows.append(
            [
                item["provider"],
                item["symbol"],
                item["interval"],
                str(item["step"]["exit"]),
                str(item["rows"]),
                str(item["first_ts"]),
                str(item["last_ts"]),
                str(item["native_fetch_attempted"]),
                item.get("output") or item.get("request") or "",
            ]
        )
    with (REPORT / "native_provider_timeframe_fetch_probe_v1.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)
    (REPORT / "native_provider_timeframe_fetch_probe_v1.md").write_text(
        "# Native Provider Timeframe Fetch Probe v1\n\n"
        f"Requested window: `{START}` to `{END}`.\n\n"
        f"Command exits: `{report['tasks_exit_zero']}/{report['tasks_total']}`.\n\n"
        f"Providers with complete native 1h/4h/1d rows: `{len(complete_native)}/6` "
        f"({', '.join(complete_native) if complete_native else 'none'}).\n\n"
        "Gate: fail-closed for Board A unless all required provider/timeframe rows can feed the full chain and later produce per-regime calibrated >=95 plus execution admission.\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
