#!/usr/bin/env python3
"""Board A 162440 same-root provider preflight.

This script gathers current provider rows under one owned run root. It does not
run Auto-Quant or downstream promotion checks; the output decides whether those
steps are justified.
"""

from __future__ import annotations

import csv
import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any


RUN_ID = "20260512T162440+0800-codex-board-a-six-provider-localstdio-aq-packet-v1"
REPO = Path(".").resolve()
ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = ROOT / "command-output"
CHECKS = ROOT / "checks"
DATA = ROOT / "data"
SUMMARIES = ROOT / "summaries"
REQUESTS = ROOT / "requests"
REPORT = ROOT / "board-a-six-provider-localstdio-aq-packet-v1"
FETCH = REPO / "scripts/auto_quant_external/fetch_external.py"
ICT = REPO / "target/debug/ict-engine"
UV = "/Users/thrill3r/.local/bin/uv"
BASE_FETCH = [
    UV,
    "run",
    "--with",
    "pandas",
    "--with",
    "requests",
    "--with",
    "ib_async",
    "--with",
    "redis",
    "--with",
    "pyyaml",
    "python",
    str(FETCH),
]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def run_command(
    label: str,
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout: int = 240,
) -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)
    out_path = OUT / f"{label}.out"
    err_path = OUT / f"{label}.err"
    exit_path = CHECKS / f"{label}.exit"
    if exit_path.exists() and out_path.exists() and err_path.exists():
        stdout = out_path.read_text()
        stderr = err_path.read_text()
        try:
            code = int(exit_path.read_text().strip())
        except ValueError:
            code = 125
        parsed = None
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            pass
        return {"label": label, "exit": code, "stdout": stdout, "stderr": stderr, "parsed": parsed}
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    (OUT / f"{label}.cmd").write_text(" ".join(shlex.quote(part) for part in cmd) + "\n")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO),
            env=merged_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n"
        code = 124
    except FileNotFoundError as exc:
        stdout = ""
        stderr = f"SPAWN_FAILED FileNotFoundError: {exc}\n"
        code = 127
    if isinstance(stdout, bytes):
        stdout = stdout.decode(errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode(errors="replace")
    (OUT / f"{label}.out").write_text(stdout)
    (OUT / f"{label}.err").write_text(stderr)
    (CHECKS / f"{label}.exit").write_text(f"{code}\n")
    parsed = None
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        pass
    return {"label": label, "exit": code, "stdout": stdout, "stderr": stderr, "parsed": parsed}


def csv_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "exists": False, "rows": 0, "first_timestamp": None, "last_timestamp": None}
    first = None
    last = None
    rows = 0
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows += 1
            ts = row.get("date") or row.get("ts") or row.get("timestamp")
            if first is None:
                first = ts
            last = ts
    return {"path": str(path), "exists": True, "rows": rows, "first_timestamp": first, "last_timestamp": last}


def harness_summary(result: dict[str, Any], data_path: Path) -> dict[str, Any]:
    parsed = result.get("parsed")
    rows = 0
    first = None
    last = None
    ok = False
    if isinstance(parsed, dict):
        results = parsed.get("results") or []
        for envelope in results:
            if envelope.get("ok") and isinstance(envelope.get("data"), list):
                ok = True
                records = envelope["data"]
                rows = len(records)
                if records:
                    first = records[0].get("timestamp")
                    last = records[-1].get("timestamp")
                write_json(data_path, records)
                break
    return {"path": str(data_path), "exists": data_path.exists(), "ok": ok, "rows": rows, "first_timestamp": first, "last_timestamp": last}


def provider_status_reason(parsed: Any, provider_id: str) -> dict[str, Any]:
    if not isinstance(parsed, dict):
        return {"ready": None, "status": None, "reason": None}
    for item in parsed.get("providers", []):
        if item.get("provider_id") == provider_id:
            return {
                "ready": item.get("ready"),
                "status": item.get("status"),
                "reason": item.get("reason"),
            }
    return {"ready": None, "status": None, "reason": None}


def main() -> int:
    for path in [OUT, CHECKS, DATA, SUMMARIES, REQUESTS, REPORT]:
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")

    env_limits = {
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
    }
    tvr_env = {
        **env_limits,
        "HOME": "/tmp/ict-engine-tvr-stdio-162440-home",
        "ICT_ENGINE_TVREMIX_MCP_URL": "",
        "ICT_ENGINE_TVREMIX_MCP_API_KEY": "",
        "ICT_ENGINE_TRADINGVIEW_MCP_CMD": "uv",
        "ICT_ENGINE_TRADINGVIEW_MCP_ARGS": "--directory /Users/thrill3r/tradingview-mcp/tradingview-mcp run tradingview-mcp",
    }

    commands: list[dict[str, Any]] = []
    commands.append(
        run_command(
            "00_provider_status_agent_localstdio",
            [str(ICT), "provider-status", "--agent"],
            env=tvr_env,
            timeout=120,
        )
    )

    output_paths = {
        "yfinance": DATA / "yfinance_btc_usd_1h_20260501_20260512.csv",
        "binance": DATA / "binance_btcusdt_1h_20260501_20260512.csv",
        "bybit": DATA / "bybit_linear_btcusdt_1h_20260501_20260512.csv",
        "kraken": DATA / "kraken_futures_pfxbtusd_1h_20260501_20260512.csv",
        "ibkr": DATA / "ibkr_spy_1h_2d.csv",
        "tvr": DATA / "tradingview_mcp_btc_usd_1h.json",
    }
    commands.append(
        run_command(
            "01_yfinance_btc_usd_1h",
            [*BASE_FETCH, "yahoo", "--symbol", "BTC-USD", "--interval", "1h", "--start", "2026-05-01", "--end", "2026-05-12", "--output", str(output_paths["yfinance"])],
            env=env_limits,
            timeout=240,
        )
    )
    commands.append(
        run_command(
            "02_binance_btcusdt_1h",
            [*BASE_FETCH, "binance-kline", "--symbol", "BTCUSDT", "--interval", "1h", "--start", "2026-05-01", "--end", "2026-05-12", "--output", str(output_paths["binance"])],
            env=env_limits,
            timeout=240,
        )
    )
    commands.append(
        run_command(
            "03_bybit_linear_btcusdt_1h",
            [*BASE_FETCH, "bybit-kline", "--category", "linear", "--symbol", "BTCUSDT", "--interval", "1h", "--start", "2026-05-01", "--end", "2026-05-12", "--output", str(output_paths["bybit"])],
            env=env_limits,
            timeout=240,
        )
    )
    commands.append(
        run_command(
            "04_kraken_futures_pfxbtusd_1h",
            [*BASE_FETCH, "kraken-kline", "--market", "futures", "--pair", "PF_XBTUSD", "--interval", "1h", "--start", "2026-05-01", "--end", "2026-05-12", "--output", str(output_paths["kraken"])],
            env=env_limits,
            timeout=240,
        )
    )
    commands.append(
        run_command(
            "05_ibkr_spy_1h",
            [
                *BASE_FETCH,
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
                "1 hour",
                "--duration",
                "2 D",
                "--what-to-show",
                "TRADES",
                "--port",
                "4002",
                "--client-id",
                "64",
                "--output",
                str(output_paths["ibkr"]),
            ],
            env=env_limits,
            timeout=180,
        )
    )
    commands.append(
        run_command(
            "06_tvr_btc_usd_1h_localstdio",
            [
                str(ICT),
                "market-data-harness",
                "--action",
                "fetch",
                "--market",
                "board-a-162440-tvr-stdio-btc-usd-1h",
                "--interval",
                "1h",
                "--role",
                "crypto_reference",
                "--provider",
                "crypto_reference=tradingview_mcp",
                "--symbol-spec",
                "crypto_reference=BTC-USD",
            ],
            env=tvr_env,
            timeout=180,
        )
    )

    exits = {item["label"]: item["exit"] for item in commands}
    provider_status = commands[0].get("parsed")
    rows = [
        {
            "provider": "IBKR",
            "provider_symbol": "SPY STK SMART/ARCA",
            "timeframe": "1h",
            "exit": exits["05_ibkr_spy_1h"],
            "data": csv_summary(output_paths["ibkr"]),
            "same_symbol_as_crypto_packet": False,
            "usable_for_current_aq_authority": False,
            "notes": "Current reachable IBKR row is SPY context, not BTC/crypto same-symbol AQ input.",
        },
        {
            "provider": "TradingViewRemix/TVR",
            "provider_symbol": "BTC-USD",
            "timeframe": "1h",
            "exit": exits["06_tvr_btc_usd_1h_localstdio"],
            "data": harness_summary(commands[-1], output_paths["tvr"]),
            "same_symbol_as_crypto_packet": True,
            "usable_for_current_aq_authority": exits["06_tvr_btc_usd_1h_localstdio"] == 0,
            "notes": "Local-stdio tradingview_mcp route; remote HTTP API key path intentionally unset.",
        },
        {
            "provider": "yfinance/YF",
            "provider_symbol": "BTC-USD",
            "timeframe": "1h",
            "exit": exits["01_yfinance_btc_usd_1h"],
            "data": csv_summary(output_paths["yfinance"]),
            "same_symbol_as_crypto_packet": True,
            "usable_for_current_aq_authority": exits["01_yfinance_btc_usd_1h"] == 0,
            "notes": "Public Yahoo HTTP OHLCV.",
        },
        {
            "provider": "Kraken",
            "provider_symbol": "PF_XBTUSD",
            "timeframe": "1h",
            "exit": exits["04_kraken_futures_pfxbtusd_1h"],
            "data": csv_summary(output_paths["kraken"]),
            "same_symbol_as_crypto_packet": False,
            "usable_for_current_aq_authority": exits["04_kraken_futures_pfxbtusd_1h"] == 0,
            "notes": "Kraken futures BTC-perp public OHLCV; related instrument, not exact spot BTCUSDT.",
        },
        {
            "provider": "Binance",
            "provider_symbol": "BTCUSDT",
            "timeframe": "1h",
            "exit": exits["02_binance_btcusdt_1h"],
            "data": csv_summary(output_paths["binance"]),
            "same_symbol_as_crypto_packet": True,
            "usable_for_current_aq_authority": exits["02_binance_btcusdt_1h"] == 0,
            "notes": "Public Binance spot OHLCV.",
        },
        {
            "provider": "Bybit",
            "provider_symbol": "BTCUSDT linear",
            "timeframe": "1h",
            "exit": exits["03_bybit_linear_btcusdt_1h"],
            "data": csv_summary(output_paths["bybit"]),
            "same_symbol_as_crypto_packet": False,
            "usable_for_current_aq_authority": exits["03_bybit_linear_btcusdt_1h"] == 0,
            "notes": "Public Bybit linear-perp OHLCV; related instrument, not exact spot BTCUSDT.",
        },
    ]
    all_exit_zero = all(row["exit"] == 0 for row in rows)
    all_have_rows = all((row["data"].get("rows") or 0) > 0 for row in rows)
    same_symbol_failures = [row["provider"] for row in rows if not row["same_symbol_as_crypto_packet"]]
    six_provider_current_rows = all_exit_zero and all_have_rows
    same_root_current_aq_authority = six_provider_current_rows and not same_symbol_failures
    decision = {
        "six_provider_current_rows": six_provider_current_rows,
        "same_root_current_aq_authority": same_root_current_aq_authority,
        "blockers": [],
        "auto_quant_should_start": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    if not all_exit_zero:
        decision["blockers"].append("one_or_more_provider_fetch_exits_nonzero")
    if not all_have_rows:
        decision["blockers"].append("one_or_more_provider_rows_empty")
    if same_symbol_failures:
        decision["blockers"].append("provider_rows_not_same_symbol_or_same_market_context:" + ",".join(same_symbol_failures))
    if six_provider_current_rows and not same_symbol_failures:
        decision["auto_quant_should_start"] = True

    summary = {
        "run_id": RUN_ID,
        "scope": "board_a_six_provider_localstdio_preflight",
        "command_exits": exits,
        "provider_status_reasons": {
            "ibkr": provider_status_reason(provider_status, "ibkr"),
            "yfinance": provider_status_reason(provider_status, "yfinance"),
            "tradingview_mcp": provider_status_reason(provider_status, "tradingview_mcp"),
        },
        "provider_rows": rows,
        "decision": decision,
    }
    write_json(SUMMARIES / "provider_preflight_162440_summary.json", summary)

    matrix_path = SUMMARIES / "provider_preflight_162440_matrix.csv"
    with matrix_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "provider",
            "provider_symbol",
            "timeframe",
            "exit",
            "rows",
            "first_timestamp",
            "last_timestamp",
            "same_symbol_as_crypto_packet",
            "usable_for_current_aq_authority",
            "notes",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "provider": row["provider"],
                    "provider_symbol": row["provider_symbol"],
                    "timeframe": row["timeframe"],
                    "exit": row["exit"],
                    "rows": row["data"].get("rows"),
                    "first_timestamp": row["data"].get("first_timestamp"),
                    "last_timestamp": row["data"].get("last_timestamp"),
                    "same_symbol_as_crypto_packet": row["same_symbol_as_crypto_packet"],
                    "usable_for_current_aq_authority": row["usable_for_current_aq_authority"],
                    "notes": row["notes"],
                }
            )

    lines = [
        "# Board A Six-Provider Local-Stdio AQ Packet Preflight v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Provider Rows",
        "",
    ]
    for row in rows:
        lines.append(
            f"- {row['provider']}: exit `{row['exit']}`, rows `{row['data'].get('rows')}`, "
            f"symbol `{row['provider_symbol']}`, same-symbol `{row['same_symbol_as_crypto_packet']}`."
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- six_provider_current_rows: `{six_provider_current_rows}`",
            f"- same_root_current_aq_authority: `{same_root_current_aq_authority}`",
            f"- auto_quant_should_start: `{decision['auto_quant_should_start']}`",
            f"- blockers: `{decision['blockers']}`",
            "- promotion_allowed: `false`",
            "- trade_usable: `false`",
            "- update_goal: `false`",
        ]
    )
    (REPORT / "provider_preflight_162440.md").write_text("\n".join(lines) + "\n")
    (CHECKS / "provider_preflight_162440_assertions.out").write_text(
        "\n".join(
            [
                f"six_provider_current_rows={six_provider_current_rows}",
                f"same_root_current_aq_authority={same_root_current_aq_authority}",
                f"auto_quant_should_start={decision['auto_quant_should_start']}",
                f"blockers={';'.join(decision['blockers'])}",
                "promotion_allowed=false",
                "trade_usable=false",
                "update_goal=false",
            ]
        )
        + "\n"
    )
    print(SUMMARIES / "provider_preflight_162440_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
