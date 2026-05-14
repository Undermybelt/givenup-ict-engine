from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T165415+0800-codex-board-a-provider-max-window-capability-probe-v1"
ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
CSV_DIR = ROOT / "provider-csv"
SUMMARY_DIR = ROOT / "summaries"
CONFIG_DIR = ROOT / "config"

REQUESTED_START = "2021-01-01"
REQUESTED_END = "2026-05-12"
TIMEFRAME = "1h"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def run_cmd(label: str, cmd: list[str], *, env: dict[str, str] | None = None, timeout: int = 1200) -> int:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    write_text(OUT_DIR / f"{label}.cmd", " ".join(cmd) + "\n")
    proc = subprocess.run(
        cmd,
        cwd=Path.cwd(),
        env=merged_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    write_text(OUT_DIR / f"{label}.stdout", proc.stdout)
    write_text(OUT_DIR / f"{label}.stderr", proc.stderr)
    write_text(CHECK_DIR / f"{label}.exit", f"{proc.returncode}\n")
    return proc.returncode


def csv_profile(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"rows": 0, "first": None, "last": None, "columns": []}
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        columns = reader.fieldnames or []
        time_key = next(
            (key for key in ("timestamp", "date", "datetime", "open_time", "time") if key in columns),
            columns[0] if columns else None,
        )
        first = None
        last = None
        rows = 0
        for row in reader:
            rows += 1
            value = row.get(time_key, "") if time_key else ""
            if rows == 1:
                first = value
            last = value
    return {"rows": rows, "first": first, "last": last, "columns": columns}


def tvr_profile(stdout_path: Path, csv_path: Path) -> dict[str, Any]:
    if not stdout_path.exists():
        return {"rows": 0, "first": None, "last": None, "columns": []}
    try:
        payload = json.loads(stdout_path.read_text())
    except json.JSONDecodeError:
        return {"rows": 0, "first": None, "last": None, "columns": []}
    rows: list[dict[str, Any]] = []
    for result in payload.get("results", []):
        rows.extend(result.get("data") or [])
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "timestamp": row.get("timestamp"),
                    "open": row.get("open"),
                    "high": row.get("high"),
                    "low": row.get("low"),
                    "close": row.get("close"),
                    "volume": row.get("volume", 0),
                }
            )
    return csv_profile(csv_path)


def write_ibkr_config() -> Path:
    config_path = CONFIG_DIR / "ibkr_btc_paxos_aggtrades_1y.yaml"
    write_text(
        config_path,
        "\n".join(
            [
                "gateway:",
                "  host: 127.0.0.1",
                "  port: 4002",
                "  client_id: 44",
                "output:",
                f"  directory: {CSV_DIR}",
                "  filename_template: '{symbol}_{bar_suffix}_{what}.csv'",
                "  force: true",
                "defaults:",
                "  bar_size: '1 hour'",
                "  duration: '1 Y'",
                "  what_to_show: AGGTRADES",
                "  rth: false",
                "  exchange: PAXOS",
                "  currency: USD",
                "symbols:",
                "  - symbol: BTC",
                "    sec_type: CRYPTO",
                "    exchange: PAXOS",
                "    currency: USD",
                "    what_to_show: AGGTRADES",
                "    rth: false",
                "    bar_sizes: ['1 hour']",
                "    duration: '1 Y'",
                "",
            ]
        ),
    )
    return config_path


def main() -> int:
    for path in (OUT_DIR, CHECK_DIR, CSV_DIR, SUMMARY_DIR, CONFIG_DIR):
        path.mkdir(parents=True, exist_ok=True)
    write_text(ROOT / "run_id.txt", RUN_ID + "\n")

    commands = [
        (
            "01_yfinance_btc_usd_1h_20210101_20260512",
            [
                "uv",
                "run",
                "--with",
                "yfinance",
                "--with",
                "pandas",
                "scripts/auto_quant_external/fetch_external.py",
                "yahoo",
                "--symbol",
                "BTC-USD",
                "--interval",
                TIMEFRAME,
                "--start",
                REQUESTED_START,
                "--end",
                REQUESTED_END,
                "--output",
                str(CSV_DIR / "yfinance_btc_usd_1h_20210101_20260512.csv"),
            ],
            {},
        ),
        (
            "02_kraken_xbtusd_1h_20210101_20260512",
            [
                "uv",
                "run",
                "--with",
                "pandas",
                "scripts/auto_quant_external/fetch_external.py",
                "kraken-kline",
                "--market",
                "futures",
                "--pair",
                "PF_XBTUSD",
                "--interval",
                TIMEFRAME,
                "--start",
                REQUESTED_START,
                "--end",
                REQUESTED_END,
                "--output",
                str(CSV_DIR / "kraken_pfxbtusd_1h_20210101_20260512.csv"),
            ],
            {},
        ),
        (
            "03_binance_btcusdt_1h_20210101_20260512",
            [
                "uv",
                "run",
                "--with",
                "pandas",
                "scripts/auto_quant_external/fetch_external.py",
                "binance-kline",
                "--symbol",
                "BTCUSDT",
                "--interval",
                TIMEFRAME,
                "--start",
                REQUESTED_START,
                "--end",
                REQUESTED_END,
                "--output",
                str(CSV_DIR / "binance_btcusdt_1h_20210101_20260512.csv"),
            ],
            {},
        ),
        (
            "04_bybit_btcusdt_linear_1h_20210101_20260512",
            [
                "uv",
                "run",
                "--with",
                "pandas",
                "scripts/auto_quant_external/fetch_external.py",
                "bybit-kline",
                "--category",
                "linear",
                "--symbol",
                "BTCUSDT",
                "--interval",
                TIMEFRAME,
                "--start",
                REQUESTED_START,
                "--end",
                REQUESTED_END,
                "--output",
                str(CSV_DIR / "bybit_btcusdt_linear_1h_20210101_20260512.csv"),
            ],
            {},
        ),
        (
            "05_tvr_btc_usd_1h_local_stdio_default_window",
            [
                "./target/debug/ict-engine",
                "market-data-harness",
                "--action",
                "fetch",
                "--market",
                "board-a-165415-btc-tvr-local-stdio-1h",
                "--interval",
                TIMEFRAME,
                "--role",
                "crypto_reference",
                "--provider",
                "crypto_reference=tradingview_mcp",
                "--symbol-spec",
                "crypto_reference=BTC-USD",
            ],
            {
                "HOME": "/tmp/ict-engine-tvr-local-stdio-165415-home",
                "ICT_ENGINE_TVREMIX_MCP_URL": "",
                "ICT_ENGINE_TVREMIX_MCP_API_KEY": "",
                "ICT_ENGINE_TRADINGVIEW_MCP_CMD": "uv",
                "ICT_ENGINE_TRADINGVIEW_MCP_ARGS": "--directory /Users/thrill3r/tradingview-mcp/tradingview-mcp run tradingview-mcp",
            },
        ),
    ]

    rows: list[dict[str, Any]] = []
    output_paths = {
        "01_yfinance_btc_usd_1h_20210101_20260512": CSV_DIR / "yfinance_btc_usd_1h_20210101_20260512.csv",
        "02_kraken_xbtusd_1h_20210101_20260512": CSV_DIR / "kraken_pfxbtusd_1h_20210101_20260512.csv",
        "03_binance_btcusdt_1h_20210101_20260512": CSV_DIR / "binance_btcusdt_1h_20210101_20260512.csv",
        "04_bybit_btcusdt_linear_1h_20210101_20260512": CSV_DIR / "bybit_btcusdt_linear_1h_20210101_20260512.csv",
    }
    providers = {
        "01_yfinance_btc_usd_1h_20210101_20260512": "yfinance/YF",
        "02_kraken_xbtusd_1h_20210101_20260512": "Kraken",
        "03_binance_btcusdt_1h_20210101_20260512": "Binance",
        "04_bybit_btcusdt_linear_1h_20210101_20260512": "Bybit",
        "05_tvr_btc_usd_1h_local_stdio_default_window": "TradingViewRemix/TVR",
    }

    for label, cmd, env in commands:
        exit_code = run_cmd(label, cmd, env=env)
        if label.startswith("05_tvr"):
            profile = tvr_profile(OUT_DIR / f"{label}.stdout", CSV_DIR / "tvr_btc_usd_1h_local_stdio_default_window.csv")
            requested_span = "provider_default_local_stdio_no_explicit_range"
        else:
            profile = csv_profile(output_paths[label])
            requested_span = f"{REQUESTED_START}_to_{REQUESTED_END}"
        rows.append(
            {
                "provider": providers[label],
                "label": label,
                "requested_history_span": requested_span,
                "returned_first": profile["first"],
                "returned_last": profile["last"],
                "timeframe": TIMEFRAME,
                "kline_rows": profile["rows"],
                "exit": exit_code,
                "portable_to_consumer": providers[label] != "IBKR",
                "local_file_runtime_dependency": False,
                "status": "current_row_ready" if exit_code == 0 and profile["rows"] > 0 else "fail_closed",
            }
        )

    ibkr_config = write_ibkr_config()
    ibkr_label = "06_ibkr_btc_paxos_aggtrades_1h_1y_duration"
    ibkr_exit = run_cmd(
        ibkr_label,
        [
            "/Users/thrill3r/Auto-Quant/.venv/bin/python",
            "scripts/auto_quant_external/fetch_external.py",
            "ibkr-bulk",
            "--config",
            str(ibkr_config),
            "--force",
        ],
        env={"PYTHONPATH": f"{Path.cwd() / 'scripts'}:{Path.cwd()}"},
        timeout=1200,
    )
    ibkr_csv = CSV_DIR / "BTC_1h_AGGTRADES.csv"
    if not ibkr_csv.exists():
        alternatives = sorted(CSV_DIR.glob("BTC_*AGGTRADES*.csv"))
        ibkr_csv = alternatives[0] if alternatives else ibkr_csv
    ibkr_profile = csv_profile(ibkr_csv)
    rows.append(
        {
            "provider": "IBKR",
            "label": ibkr_label,
            "requested_history_span": "1Y_duration_via_ibkr_bulk",
            "returned_first": ibkr_profile["first"],
            "returned_last": ibkr_profile["last"],
            "timeframe": TIMEFRAME,
            "kline_rows": ibkr_profile["rows"],
            "exit": ibkr_exit,
            "portable_to_consumer": True,
            "local_file_runtime_dependency": False,
            "status": "current_row_ready" if ibkr_exit == 0 and ibkr_profile["rows"] > 0 else "fail_closed",
        }
    )

    summary = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_start": REQUESTED_START,
        "requested_end": REQUESTED_END,
        "timeframe": TIMEFRAME,
        "rows": rows,
        "provider_rows_ready": sum(1 for row in rows if row["status"] == "current_row_ready"),
        "provider_rows_total": len(rows),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_text(SUMMARY_DIR / "provider_max_window_capability_probe_v1.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")

    matrix_path = SUMMARY_DIR / "provider_max_window_capability_matrix.csv"
    with matrix_path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "provider",
                "label",
                "requested_history_span",
                "returned_first",
                "returned_last",
                "timeframe",
                "kline_rows",
                "exit",
                "portable_to_consumer",
                "local_file_runtime_dependency",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Board A Provider Max-Window Capability Probe v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "This probe requests the broadest feasible BTC 1h history from provider interfaces and does not run Auto-Quant or downstream ict-engine gates.",
        "",
        "## Matrix",
    ]
    for row in rows:
        lines.append(
            f"- {row['provider']}: requested `{row['requested_history_span']}`, rows `{row['kline_rows']}`, "
            f"first `{row['returned_first']}`, last `{row['returned_last']}`, exit `{row['exit']}`, status `{row['status']}`."
        )
    lines.extend(
        [
            "",
            "## Gate",
            f"- provider_rows_ready={summary['provider_rows_ready']}/{summary['provider_rows_total']}.",
            "- sample_adequacy=capability_probe_only.",
            "- auto_quant_started=false.",
            "- downstream_started=false.",
            "- promotion_allowed=false.",
            "- trade_usable=false.",
            "- update_goal=false.",
        ]
    )
    write_text(ROOT / "provider_max_window_capability_probe_v1.md", "\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
