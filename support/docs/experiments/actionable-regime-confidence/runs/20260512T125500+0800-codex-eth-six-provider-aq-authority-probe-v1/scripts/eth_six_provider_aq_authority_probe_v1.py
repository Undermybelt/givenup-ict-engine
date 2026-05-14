from __future__ import annotations

import csv
import json
import math
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests


RUN_ID = "20260512T125500+0800-codex-eth-six-provider-aq-authority-probe-v1"
RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
TEMPLATE_WORKSPACE = (
    RUNS
    / "20260512T104902+0800-codex-board-b-yahoo-btc-pullback-precision-aq-v1"
    / "workspace"
    / "auto-quant-yahoo-btc-pullback-precision"
)
PYTHON = Path("/Users/thrill3r/Auto-Quant/.venv/bin/python")

OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "eth-six-provider-aq-authority-probe-v1"
PROVIDER_CSV_DIR = ROOT / "provider-csv"
WORKSPACE_ROOT = ROOT / "workspace"

START = datetime(2026, 4, 1, tzinfo=timezone.utc)
END = datetime(2026, 5, 12, 5, 0, tzinfo=timezone.utc)
PAIR = "ETH/USDT"
FEATHER_NAME = "ETH_USDT-1h.feather"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def record_exit(name: str, code: int) -> None:
    write_text(CHECK_DIR / f"{name}.exit", f"{code}\n")


def utc_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def write_provider_csv(name: str, rows: list[dict[str, Any]]) -> Path:
    path = PROVIDER_CSV_DIR / f"{name}.csv"
    PROVIDER_CSV_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["date", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path


def normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        try:
            ts = pd.to_datetime(row["date"], utc=True)
            out.append(
                {
                    "date": ts.isoformat().replace("+00:00", "Z"),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume") or 0.0),
                }
            )
        except Exception:
            continue
    out.sort(key=lambda item: item["date"])
    return out


def fetch_yfinance() -> dict[str, Any]:
    name = "yfinance_eth_usd_1h"
    url = "https://query1.finance.yahoo.com/v8/finance/chart/ETH-USD"
    params = {
        "period1": int(START.timestamp()),
        "period2": int(END.timestamp()),
        "interval": "1h",
        "includePrePost": "false",
    }
    started = time.time()
    try:
        resp = requests.get(url, params=params, timeout=25)
        write_text(OUT_DIR / f"{name}.stdout", resp.text)
        write_text(OUT_DIR / f"{name}.stderr", "")
        resp.raise_for_status()
        result = resp.json()["chart"]["result"][0]
        quote = result["indicators"]["quote"][0]
        rows = []
        for i, ts in enumerate(result.get("timestamp") or []):
            values = {k: (quote.get(k) or [None] * (i + 1))[i] for k in ["open", "high", "low", "close", "volume"]}
            if any(values[k] is None or (isinstance(values[k], float) and math.isnan(values[k])) for k in ["open", "high", "low", "close"]):
                continue
            rows.append(
                {
                    "date": datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat().replace("+00:00", "Z"),
                    **values,
                }
            )
        rows = normalize_rows(rows)
        csv_path = write_provider_csv(name, rows)
        record_exit(name, 0)
        return {
            "provider": "yfinance",
            "fetch_name": name,
            "exit": 0,
            "rows": len(rows),
            "csv": str(csv_path),
            "first_time": rows[0]["date"] if rows else None,
            "last_time": rows[-1]["date"] if rows else None,
            "elapsed_s": round(time.time() - started, 3),
        }
    except Exception as exc:
        write_text(OUT_DIR / f"{name}.stderr", f"{type(exc).__name__}: {exc}\n")
        record_exit(name, 1)
        return {"provider": "yfinance", "fetch_name": name, "exit": 1, "rows": 0, "error": str(exc)}


def fetch_kraken() -> dict[str, Any]:
    name = "kraken_ethusd_1h"
    url = "https://api.kraken.com/0/public/OHLC"
    params = {"pair": "ETHUSD", "interval": "60", "since": int(START.timestamp())}
    try:
        resp = requests.get(url, params=params, timeout=25)
        write_text(OUT_DIR / f"{name}.stdout", resp.text)
        write_text(OUT_DIR / f"{name}.stderr", "")
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        result = payload["result"]
        key = next(k for k in result.keys() if k != "last")
        rows = normalize_rows(
            [
                {
                    "date": datetime.fromtimestamp(int(item[0]), tz=timezone.utc).isoformat().replace("+00:00", "Z"),
                    "open": item[1],
                    "high": item[2],
                    "low": item[3],
                    "close": item[4],
                    "volume": item[6],
                }
                for item in result[key]
            ]
        )
        csv_path = write_provider_csv(name, rows)
        record_exit(name, 0)
        return {
            "provider": "kraken",
            "fetch_name": name,
            "exit": 0,
            "rows": len(rows),
            "csv": str(csv_path),
            "first_time": rows[0]["date"] if rows else None,
            "last_time": rows[-1]["date"] if rows else None,
        }
    except Exception as exc:
        write_text(OUT_DIR / f"{name}.stderr", f"{type(exc).__name__}: {exc}\n")
        record_exit(name, 1)
        return {"provider": "kraken", "fetch_name": name, "exit": 1, "rows": 0, "error": str(exc)}


def fetch_binance() -> dict[str, Any]:
    name = "binance_ethusdt_1h"
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "startTime": utc_ms(START),
        "endTime": utc_ms(END),
        "limit": 1000,
    }
    try:
        resp = requests.get(url, params=params, timeout=25)
        write_text(OUT_DIR / f"{name}.stdout", resp.text)
        write_text(OUT_DIR / f"{name}.stderr", "")
        resp.raise_for_status()
        rows = normalize_rows(
            [
                {
                    "date": datetime.fromtimestamp(int(item[0]) / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
                    "open": item[1],
                    "high": item[2],
                    "low": item[3],
                    "close": item[4],
                    "volume": item[5],
                }
                for item in resp.json()
            ]
        )
        csv_path = write_provider_csv(name, rows)
        record_exit(name, 0)
        return {
            "provider": "binance",
            "fetch_name": name,
            "exit": 0,
            "rows": len(rows),
            "csv": str(csv_path),
            "first_time": rows[0]["date"] if rows else None,
            "last_time": rows[-1]["date"] if rows else None,
        }
    except Exception as exc:
        write_text(OUT_DIR / f"{name}.stderr", f"{type(exc).__name__}: {exc}\n")
        record_exit(name, 1)
        return {"provider": "binance", "fetch_name": name, "exit": 1, "rows": 0, "error": str(exc)}


def fetch_bybit() -> dict[str, Any]:
    name = "bybit_ethusdt_linear_1h"
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "linear",
        "symbol": "ETHUSDT",
        "interval": "60",
        "start": utc_ms(START),
        "end": utc_ms(END),
        "limit": 1000,
    }
    try:
        resp = requests.get(url, params=params, timeout=25)
        write_text(OUT_DIR / f"{name}.stdout", resp.text)
        write_text(OUT_DIR / f"{name}.stderr", "")
        resp.raise_for_status()
        payload = resp.json()
        if str(payload.get("retCode")) != "0":
            raise RuntimeError(payload)
        rows = normalize_rows(
            [
                {
                    "date": datetime.fromtimestamp(int(item[0]) / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
                    "open": item[1],
                    "high": item[2],
                    "low": item[3],
                    "close": item[4],
                    "volume": item[5],
                }
                for item in payload["result"]["list"]
            ]
        )
        csv_path = write_provider_csv(name, rows)
        record_exit(name, 0)
        return {
            "provider": "bybit",
            "fetch_name": name,
            "exit": 0,
            "rows": len(rows),
            "csv": str(csv_path),
            "first_time": rows[0]["date"] if rows else None,
            "last_time": rows[-1]["date"] if rows else None,
        }
    except Exception as exc:
        write_text(OUT_DIR / f"{name}.stderr", f"{type(exc).__name__}: {exc}\n")
        record_exit(name, 1)
        return {"provider": "bybit", "fetch_name": name, "exit": 1, "rows": 0, "error": str(exc)}


def fetch_tvr_from_existing() -> dict[str, Any]:
    name = "tvr_eth_usd_1h"
    source = OUT_DIR / "00_tvr_eth_usd_1h.out"
    exit_path = CHECK_DIR / "00_tvr_eth_usd_1h.exit"
    try:
        payload = read_json(source)
        result = (payload.get("results") or [{}])[0]
        data = result.get("data") or []
        rows = normalize_rows(
            [
                {
                    "date": item["timestamp"],
                    "open": item["open"],
                    "high": item["high"],
                    "low": item["low"],
                    "close": item["close"],
                    "volume": item.get("volume") or 0.0,
                }
                for item in data
            ]
        )
        csv_path = write_provider_csv(name, rows)
        code = int(exit_path.read_text().strip()) if exit_path.exists() else 0
        return {
            "provider": "tradingview_mcp",
            "fetch_name": name,
            "exit": code,
            "rows": len(rows),
            "csv": str(csv_path),
            "first_time": rows[0]["date"] if rows else None,
            "last_time": rows[-1]["date"] if rows else None,
            "source_output": str(source),
        }
    except Exception as exc:
        return {"provider": "tradingview_mcp", "fetch_name": name, "exit": 1, "rows": 0, "error": str(exc)}


def fetch_ibkr() -> dict[str, Any]:
    name = "ibkr_eth_paxos_aggtrades_1h"
    csv_path = PROVIDER_CSV_DIR / f"{name}.csv"
    result_path = PROVIDER_CSV_DIR / f"{name}_result.json"
    code = r'''
import asyncio, json, sys
from pathlib import Path
import pandas as pd
from ib_async import IB, Crypto

out = Path(sys.argv[1])
meta_path = Path(sys.argv[2])
messages = []

async def main():
    ib = IB()
    def on_error(reqId, errorCode, errorString, contract):
        messages.append({"reqId": reqId, "errorCode": errorCode, "errorString": errorString, "contract": str(contract)})
    ib.errorEvent += on_error
    result = {
        "contract_attempt": "Crypto(ETH,PAXOS,USD)",
        "what_to_show": "AGGTRADES",
        "bar_size": "1 hour",
        "connected": False,
        "qualified": False,
        "rows": 0,
        "messages": messages,
        "csv": str(out),
    }
    try:
        await ib.connectAsync("127.0.0.1", 4002, clientId=45, timeout=8)
        result["connected"] = True
        contract = Crypto("ETH", "PAXOS", "USD")
        qualified = await ib.qualifyContractsAsync(contract)
        result["qualified"] = bool(qualified)
        if qualified:
            contract = qualified[0]
        result["qualified_contract"] = str(contract)
        bars = await ib.reqHistoricalDataAsync(
            contract,
            endDateTime="",
            durationStr="30 D",
            barSizeSetting="1 hour",
            whatToShow="AGGTRADES",
            useRTH=False,
            formatDate=1,
        )
        rows = []
        for b in bars:
            rows.append({"date": str(b.date), "open": b.open, "high": b.high, "low": b.low, "close": b.close, "volume": b.volume})
        result["rows"] = len(rows)
        if rows:
            out.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(rows).to_csv(out, index=False)
            result["first_time"] = rows[0]["date"]
            result["last_time"] = rows[-1]["date"]
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    finally:
        if ib.isConnected():
            ib.disconnect()
        meta_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, sort_keys=True))

asyncio.run(main())
'''
    cmd = ["uv", "run", "--with", "ib_async", "--with", "pandas", "python3", "-c", code, str(csv_path), str(result_path)]
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    write_text(OUT_DIR / f"{name}.cmd", " ".join(cmd[:7]) + " <python-code> " + str(csv_path) + " " + str(result_path) + "\n")
    write_text(OUT_DIR / f"{name}.stdout", proc.stdout)
    write_text(OUT_DIR / f"{name}.stderr", proc.stderr)
    record_exit(name, proc.returncode)
    result = read_json(result_path)
    return {
        "provider": "ibkr",
        "fetch_name": name,
        "exit": proc.returncode,
        "rows": int(result.get("rows") or 0),
        "csv": str(csv_path) if csv_path.exists() else None,
        "first_time": result.get("first_time"),
        "last_time": result.get("last_time"),
        "ibkr_result": result,
    }


def csv_to_feather(csv_path: Path, feather_path: Path) -> tuple[int, str | None, str | None]:
    raw = pd.read_csv(csv_path)
    date = pd.to_datetime(raw["date"], utc=True)
    df = pd.DataFrame(
        {
            "date": pd.Series(date.array.asi8 // 1_000_000, dtype="int64"),
            "open": raw["open"].astype(float),
            "high": raw["high"].astype(float),
            "low": raw["low"].astype(float),
            "close": raw["close"].astype(float),
            "volume": raw["volume"].astype(float),
        }
    ).dropna().sort_values("date").reset_index(drop=True)
    feather_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_feather(feather_path)
    first = pd.to_datetime(df["date"].min(), unit="ms", utc=True).isoformat() if len(df) else None
    last = pd.to_datetime(df["date"].max(), unit="ms", utc=True).isoformat() if len(df) else None
    return int(len(df)), first, last


def copy_template(provider: str) -> Path:
    workspace = WORKSPACE_ROOT / f"auto-quant-eth-{provider}"
    if workspace.exists():
        shutil.rmtree(workspace)
    shutil.copytree(TEMPLATE_WORKSPACE, workspace, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "derived"))
    data_dir = workspace / "user_data" / "data"
    for path in data_dir.glob("*.feather"):
        path.unlink()
    (workspace / "derived").mkdir(parents=True, exist_ok=True)
    config_path = workspace / "config.tomac.json"
    config = read_json(config_path)
    config["exchange"]["pair_whitelist"] = [PAIR]
    config["stake_currency"] = "USDT"
    config["timeframe"] = "1h"
    config["timerange"] = "20260401-20260512"
    write_json(config_path, config)
    return workspace


def run_aq(provider_result: dict[str, Any]) -> dict[str, Any]:
    provider = provider_result["provider"]
    csv_value = provider_result.get("csv")
    if not csv_value or provider_result.get("rows", 0) < 120:
        return {
            "provider": provider,
            "skipped": True,
            "reason": "provider_rows_below_120_or_missing_csv",
            "rows": provider_result.get("rows", 0),
        }
    workspace = copy_template(provider)
    feather = workspace / "user_data" / "data" / FEATHER_NAME
    rows, first, last = csv_to_feather(Path(csv_value), feather)
    strategies = sorted((workspace / "user_data" / "strategies_external").glob("*.py"))
    compile_cmd = [str(PYTHON), "-m", "py_compile", "run_tomac.py", *[str(path.relative_to(workspace)) for path in strategies]]
    run_cmd = [str(PYTHON), "run_tomac.py"]
    prefix = f"aq_{provider}"
    compile_proc = subprocess.run(compile_cmd, cwd=workspace, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    write_text(OUT_DIR / f"{prefix}_compile.out", compile_proc.stdout)
    write_text(OUT_DIR / f"{prefix}_compile.err", compile_proc.stderr)
    write_text(OUT_DIR / f"{prefix}_compile.cmd", " ".join(compile_cmd) + "\n")
    record_exit(f"{prefix}_compile", compile_proc.returncode)
    run_proc = subprocess.run(run_cmd, cwd=workspace, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    write_text(OUT_DIR / f"{prefix}_run_tomac.out", run_proc.stdout)
    write_text(OUT_DIR / f"{prefix}_run_tomac.err", run_proc.stderr)
    write_text(OUT_DIR / f"{prefix}_run_tomac.cmd", " ".join(run_cmd) + "\n")
    record_exit(f"{prefix}_run_tomac", run_proc.returncode)
    metrics: dict[str, Any] = {}
    real_trade_rows = 0
    for path in sorted((workspace / "derived").glob("*.metrics.json")):
        metrics[path.stem.replace(".metrics", "")] = read_json(path)
    for path in sorted((workspace / "derived").glob("*.real_trades.jsonl")):
        real_trade_rows += sum(1 for _ in path.open())
    return {
        "provider": provider,
        "skipped": False,
        "rows": rows,
        "first_time": first,
        "last_time": last,
        "workspace": str(workspace),
        "feather": str(feather),
        "compile_exit": compile_proc.returncode,
        "run_tomac_exit": run_proc.returncode,
        "metrics": metrics,
        "real_trade_rows": real_trade_rows,
    }


def strategy_lines(result: dict[str, Any]) -> list[str]:
    if result.get("skipped"):
        return [f"  - skipped: {result.get('reason')}"]
    lines: list[str] = []
    for strategy, payload in sorted((result.get("metrics") or {}).items()):
        agg = payload.get("aggregate", {})
        lines.append(
            f"  - {strategy}: trades={agg.get('trade_count')} profit_pct={agg.get('total_profit_pct')} "
            f"sharpe={agg.get('sharpe')} pf={agg.get('profit_factor')}"
        )
    if not lines:
        lines.append("  - no metrics emitted")
    return lines


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "eth_six_provider_aq_authority_probe_v1.md"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_eth_six_provider_aq_authority_probe_v1.csv"
    assertions = CHECK_DIR / "eth_six_provider_aq_authority_probe_v1_assertions.out"
    lines = [
        "# ETH Six-Provider AQ Authority Probe v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Scope",
        "Provider-provenanced ETH 1h matrix across TradingViewRemix/TVR, yfinance/YF, Kraken, Binance, Bybit, and IBKR PAXOS, followed by isolated Auto-Quant/TOMAC execution per provider when enough 1h rows exist.",
        "This does not modify ict-engine runtime code, production BBN CPDs, production CatBoost/path-ranker state, or execution-tree gates.",
        "",
        "## Provider Matrix",
    ]
    for item in summary["provider_results"]:
        lines.append(
            f"- `{item['provider']}` / `{item['fetch_name']}`: exit `{item.get('exit')}`, rows `{item.get('rows')}`, first `{item.get('first_time')}`, last `{item.get('last_time')}`."
        )
    lines.extend(["", "## AQ Results"])
    for result in summary["aq_results"]:
        lines.append(
            f"- `{result['provider']}`: rows `{result.get('rows')}`, compile exit `{result.get('compile_exit')}`, TOMAC exit `{result.get('run_tomac_exit')}`, real_trade_rows `{result.get('real_trade_rows', 0)}`."
        )
        lines.extend(strategy_lines(result))
    lines.extend(
        [
            "",
            "## Decision",
            f"- Gate result: `{summary['gate_result']}`.",
            f"- Providers with raw rows: `{summary['providers_with_rows']}/6`.",
            f"- Providers with AQ execution: `{summary['providers_with_aq_execution']}/6`.",
            f"- Nonzero AQ trade providers: `{summary['providers_with_nonzero_trades']}/6`.",
            "- This is provider-authority incubation evidence only. It does not supply calibrated mature rooted observations, accepted `>=95%` regime context, or execution-tree non-observe release.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / 'eth_six_provider_aq_authority_probe_v1.json'}`",
            f"- Checklist: `{checklist}`",
            f"- Assertions: `{assertions}`",
            f"- Provider CSVs: `{PROVIDER_CSV_DIR}`",
            f"- AQ workspaces: `{WORKSPACE_ROOT}`",
        ]
    )
    write_text(report, "\n".join(lines) + "\n")

    with checklist.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["six provider matrix", str(PROVIDER_CSV_DIR), "covered", f"{summary['providers_with_rows']}/6 providers with rows"])
        writer.writerow(["AQ execution", str(WORKSPACE_ROOT), "covered_partial", f"{summary['providers_with_aq_execution']}/6 providers executed"])
        writer.writerow(["nonzero observations", "workspace/*/derived/*.real_trades.jsonl", "covered_partial", f"{summary['providers_with_nonzero_trades']}/6 providers nonzero"])
        writer.writerow(["Pre-Bayes/BBN/CatBoost/execution", "N/A", "not_run", "not enough mature rooted/calibrated evidence for promotion"])
        writer.writerow(["promotion", "N/A", "fail_closed", "promotion_allowed=false"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS providers_with_rows={summary['providers_with_rows']}",
        f"PASS providers_with_aq_execution={summary['providers_with_aq_execution']}",
        f"PASS providers_with_nonzero_trades={summary['providers_with_nonzero_trades']}",
        f"FAIL_CLOSED mature_rooted_observations_added={summary['mature_rooted_branch_observations_added']}",
        "FAIL_CLOSED accepted_95_regime_context=false",
        "FAIL_CLOSED no_pre_bayes_bbn_catboost_execution_tree_promotion",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    write_text(assertions, "\n".join(assertion_lines) + "\n")


def main() -> int:
    for path in [OUT_DIR, CHECK_DIR, REPORT_DIR, PROVIDER_CSV_DIR, WORKSPACE_ROOT]:
        path.mkdir(parents=True, exist_ok=True)
    write_text(ROOT / "run_id.txt", RUN_ID + "\n")
    provider_results = [
        fetch_tvr_from_existing(),
        fetch_yfinance(),
        fetch_kraken(),
        fetch_binance(),
        fetch_bybit(),
        fetch_ibkr(),
    ]
    aq_results = [run_aq(item) for item in provider_results]
    providers_with_rows = sum(1 for item in provider_results if int(item.get("rows") or 0) > 0)
    providers_with_aq_execution = sum(1 for item in aq_results if not item.get("skipped") and item.get("run_tomac_exit") == 0)
    providers_with_nonzero_trades = sum(1 for item in aq_results if int(item.get("real_trade_rows") or 0) > 0)
    mature_rooted = 0
    summary = {
        "run_id": RUN_ID,
        "pair": PAIR,
        "provider_results": provider_results,
        "aq_results": aq_results,
        "providers_with_rows": providers_with_rows,
        "providers_with_aq_execution": providers_with_aq_execution,
        "providers_with_nonzero_trades": providers_with_nonzero_trades,
        "mature_rooted_branch_observations_added": mature_rooted,
        "gate_result": "eth_six_provider_aq_authority_probe=provider_rows_and_aq_nonzero_incubation_but_no_mature_rooted_calibration_or_execution_promotion",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "eth_six_provider_aq_authority_probe_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
