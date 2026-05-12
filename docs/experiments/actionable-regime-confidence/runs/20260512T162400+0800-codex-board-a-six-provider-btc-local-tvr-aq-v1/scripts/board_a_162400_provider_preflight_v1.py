from __future__ import annotations

import csv
import json
import os
import shlex
import subprocess
from pathlib import Path

import pandas as pd


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1"
)
FETCH = "scripts/auto_quant_external/fetch_external.py"
PY_FETCH_PREFIX = [
    "uv",
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
    FETCH,
]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def command_line(args: list[str]) -> str:
    return " ".join(shlex.quote(arg) for arg in args) + "\n"


def run_cmd(label: str, args: list[str], timeout: int = 420) -> int:
    write_text(RUN_ROOT / f"command-output/{label}.cmd", command_line(args))
    out_path = RUN_ROOT / f"command-output/{label}.out"
    err_path = RUN_ROOT / f"command-output/{label}.err"
    exit_path = RUN_ROOT / f"checks/{label}.exit"
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        write_text(out_path, proc.stdout)
        write_text(err_path, proc.stderr)
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        write_text(out_path, exc.stdout or "")
        write_text(err_path, (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n")
        code = 124
    write_text(exit_path, f"{code}\n")
    return code


def normalize_csv(src: Path, dst: Path) -> dict:
    df = pd.read_csv(src)
    if "date" not in df.columns and "ts" in df.columns:
        df = df.rename(columns={"ts": "date"})
    if "date" not in df.columns and "timestamp" in df.columns:
        df = df.rename(columns={"timestamp": "date"})
    required = ["date", "open", "high", "low", "close", "volume"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{src} missing required columns {missing}")
    out = df[required].copy()
    out["date"] = pd.to_datetime(out["date"], utc=True, errors="coerce")
    for col in ["open", "high", "low", "close", "volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["date", "open", "high", "low", "close"])
    out["volume"] = out["volume"].fillna(0).clip(lower=0)
    out = out.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
    out["date"] = out["date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dst, index=False)
    return {
        "rows": int(len(out)),
        "first": str(out["date"].iloc[0]) if not out.empty else "",
        "last": str(out["date"].iloc[-1]) if not out.empty else "",
        "normalized_path": str(dst),
    }


def normalize_tvr_json(src: Path, dst: Path) -> dict:
    payload = json.loads(src.read_text())
    result = payload.get("results", [{}])[0]
    rows = result.get("data") or []
    df = pd.DataFrame(rows)
    if df.empty:
        dst.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(dst, index=False)
        return {"rows": 0, "first": "", "last": "", "normalized_path": str(dst)}
    if "timestamp" not in df.columns:
        raise ValueError(f"{src} missing timestamp in TVR result")
    df = df.rename(columns={"timestamp": "date"})
    tmp = RUN_ROOT / "data/raw/tvr_btc_usd_1h.raw.csv"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(tmp, index=False)
    return normalize_csv(tmp, dst)


def provider_row(
    provider: str,
    label: str,
    exit_code: int,
    normalized: dict | None,
    blocker: str,
) -> dict:
    acquired = exit_code == 0 and bool(normalized) and int(normalized.get("rows", 0)) > 0
    return {
        "provider": provider,
        "provider_requested": True,
        "provider_data_acquired": acquired,
        "provider_unreachable": not acquired,
        "command_label": label,
        "exit": exit_code,
        "rows": int(normalized.get("rows", 0)) if normalized else 0,
        "first": normalized.get("first", "") if normalized else "",
        "last": normalized.get("last", "") if normalized else "",
        "source_or_blocker": normalized.get("normalized_path", blocker) if normalized else blocker,
        "status": "current_row_ready" if acquired else "fail_closed_provider_row_missing",
        "failure_reason": "" if acquired else blocker,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    write_text(RUN_ROOT / "run_root.txt", str(RUN_ROOT) + "\n")
    raw = RUN_ROOT / "data/raw"
    norm = RUN_ROOT / "data/normalized"
    start = "2026-02-12"
    end = "2026-05-12"

    jobs = [
        (
            "01_fetch_yfinance_btc_usd_1h",
            "yfinance/YF",
            PY_FETCH_PREFIX
            + [
                "yahoo",
                "--symbol",
                "BTC-USD",
                "--interval",
                "1h",
                "--start",
                start,
                "--end",
                end,
                "--output",
                str(raw / "yfinance_btc_usd_1h.csv"),
            ],
            raw / "yfinance_btc_usd_1h.csv",
            norm / "yfinance_btc_usd_1h.normalized.csv",
            "yfinance_btc_usd_1h_fetch_failed",
            420,
            "csv",
        ),
        (
            "02_fetch_binance_btcusdt_1h",
            "Binance",
            PY_FETCH_PREFIX
            + [
                "binance-kline",
                "--symbol",
                "BTCUSDT",
                "--interval",
                "1h",
                "--start",
                start,
                "--end",
                end,
                "--output",
                str(raw / "binance_btcusdt_1h.csv"),
            ],
            raw / "binance_btcusdt_1h.csv",
            norm / "binance_btcusdt_1h.normalized.csv",
            "binance_btcusdt_1h_fetch_failed",
            420,
            "csv",
        ),
        (
            "03_fetch_bybit_linear_btcusdt_1h",
            "Bybit",
            PY_FETCH_PREFIX
            + [
                "bybit-kline",
                "--category",
                "linear",
                "--symbol",
                "BTCUSDT",
                "--interval",
                "1h",
                "--start",
                start,
                "--end",
                end,
                "--output",
                str(raw / "bybit_linear_btcusdt_1h.csv"),
            ],
            raw / "bybit_linear_btcusdt_1h.csv",
            norm / "bybit_linear_btcusdt_1h.normalized.csv",
            "bybit_linear_btcusdt_1h_fetch_failed",
            420,
            "csv",
        ),
        (
            "04_fetch_kraken_futures_pfxbtusd_1h",
            "Kraken",
            PY_FETCH_PREFIX
            + [
                "kraken-kline",
                "--market",
                "futures",
                "--pair",
                "PF_XBTUSD",
                "--interval",
                "1h",
                "--start",
                start,
                "--end",
                end,
                "--output",
                str(raw / "kraken_futures_pfxbtusd_1h.csv"),
            ],
            raw / "kraken_futures_pfxbtusd_1h.csv",
            norm / "kraken_futures_pfxbtusd_1h.normalized.csv",
            "kraken_futures_pfxbtusd_1h_fetch_failed",
            420,
            "csv",
        ),
        (
            "05_fetch_ibkr_paxos_btc_1h",
            "IBKR",
            PY_FETCH_PREFIX
            + [
                "ibkr-historical",
                "--symbol",
                "BTC",
                "--sec-type",
                "CASH",
                "--exchange",
                "PAXOS",
                "--currency",
                "USD",
                "--bar-size",
                "1 hour",
                "--duration",
                "30 D",
                "--what-to-show",
                "TRADES",
                "--port",
                "4002",
                "--client-id",
                "64",
                "--output",
                str(raw / "ibkr_paxos_btc_1h.csv"),
            ],
            raw / "ibkr_paxos_btc_1h.csv",
            norm / "ibkr_paxos_btc_1h.normalized.csv",
            "ibkr_paxos_btc_1h_fetch_failed",
            300,
            "csv",
        ),
        (
            "06_fetch_tvr_local_stdio_btc_usd_1h",
            "TradingViewRemix/TVR",
            [
                "env",
                f"HOME=/tmp/ict-engine-162400-tvr-home-{os.getpid()}",
                "ICT_ENGINE_TVREMIX_MCP_URL=",
                "ICT_ENGINE_TVREMIX_MCP_API_KEY=",
                "ICT_ENGINE_TRADINGVIEW_MCP_CMD=uv",
                "ICT_ENGINE_TRADINGVIEW_MCP_ARGS=--directory /Users/thrill3r/tradingview-mcp/tradingview-mcp run tradingview-mcp",
                "./target/debug/ict-engine",
                "market-data-harness",
                "--action",
                "fetch",
                "--market",
                "board-a-162400-tvr-btc-usd-1h",
                "--interval",
                "1h",
                "--role",
                "crypto_reference",
                "--provider",
                "crypto_reference=tradingview_mcp",
                "--symbol-spec",
                "crypto_reference=BTC-USD",
            ],
            RUN_ROOT / "command-output/06_fetch_tvr_local_stdio_btc_usd_1h.out",
            norm / "tvr_btc_usd_1h.normalized.csv",
            "tvr_local_stdio_btc_usd_1h_fetch_failed",
            240,
            "tvr_json",
        ),
    ]

    provider_rows: list[dict] = []
    fetch_rows: list[dict] = []
    for label, provider, args, raw_path, norm_path, blocker, timeout, mode in jobs:
        code = run_cmd(label, args, timeout=timeout)
        normalized: dict | None = None
        if code == 0:
            try:
                if mode == "tvr_json":
                    normalized = normalize_tvr_json(raw_path, norm_path)
                elif raw_path.exists():
                    normalized = normalize_csv(raw_path, norm_path)
            except Exception as exc:  # noqa: BLE001
                blocker = f"{blocker}:normalize_error:{exc}"
        row = provider_row(provider, label, code, normalized, blocker)
        provider_rows.append(row)
        fetch_rows.append({"label": label, "provider": provider, **row})

    provider_order = {
        "IBKR": 0,
        "TradingViewRemix/TVR": 1,
        "yfinance/YF": 2,
        "Kraken": 3,
        "Binance": 4,
        "Bybit": 5,
    }
    provider_rows = sorted(provider_rows, key=lambda row: provider_order[row["provider"]])
    write_csv(RUN_ROOT / "summaries/provider_authority_matrix.csv", provider_rows)

    all_ready = all(row["provider_data_acquired"] for row in provider_rows)
    summary = {
        "run_root": str(RUN_ROOT),
        "provider_rows": provider_rows,
        "same_root_six_provider_authority": all_ready,
        "auto_quant_ran": False,
        "pre_bayes_bbn_catboost_execution_tree_ran": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_text(RUN_ROOT / "summaries/board_a_162400_provider_preflight_v1.json", json.dumps(summary, indent=2) + "\n")

    lines = [
        "# Board A 162400 Provider Preflight v1",
        "",
        f"Run root: `{RUN_ROOT}`",
        "",
        "Provider rows:",
    ]
    for row in provider_rows:
        lines.append(
            f"- {row['provider']}: acquired={row['provider_data_acquired']} "
            f"exit={row['exit']} rows={row['rows']} first={row['first']} last={row['last']} "
            f"source_or_blocker=`{row['source_or_blocker']}`"
        )
    lines += [
        "",
        "Decision:",
        f"- same_root_six_provider_authority={str(all_ready).lower()}",
        "- auto_quant_ran=false",
        "- pre_bayes_bbn_catboost_execution_tree_ran=false",
        "- promotion_allowed=false",
        "- trade_usable=false",
        "- update_goal=false",
    ]
    write_text(RUN_ROOT / "board_a_162400_provider_preflight_v1.md", "\n".join(lines) + "\n")

    assertion_lines = [
        f"{'PASS' if len(provider_rows) == 6 else 'FAIL'} provider_rows={len(provider_rows)}",
        f"{'PASS' if any(row['provider'] == 'TradingViewRemix/TVR' for row in provider_rows) else 'FAIL'} tvr_row_present=True",
        f"{'PASS' if all_ready else 'FAIL'} same_root_six_provider_authority={all_ready}",
        "PASS auto_quant_ran_false=True",
        "PASS promotion_allowed_false=True",
        "PASS update_goal_false=True",
    ]
    write_text(RUN_ROOT / "checks/board_a_162400_provider_preflight_v1_assertions.out", "\n".join(assertion_lines) + "\n")
    return 0 if all_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
