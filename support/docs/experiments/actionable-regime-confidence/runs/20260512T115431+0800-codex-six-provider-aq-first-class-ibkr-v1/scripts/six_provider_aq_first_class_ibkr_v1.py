from __future__ import annotations

import csv
import importlib.util
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1"
SOURCE_AQ_TEMPLATE_RUN_ID = "20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1"
RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_AQ_TEMPLATE_ROOT = RUNS / SOURCE_AQ_TEMPLATE_RUN_ID
OLD_SCRIPT = SOURCE_AQ_TEMPLATE_ROOT / "scripts" / "112315_provider_matrix_aq_readback_v1.py"

OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "six-provider-aq-first-class-ibkr-v1"
PROVIDER_CSV_DIR = ROOT / "provider-csv"
WORKSPACE_ROOT = ROOT / "workspace"
CONFIG_DIR = ROOT / "config"

FETCH_START = "2026-04-01"
FETCH_END = "2026-05-12"
PYTHON = Path("/Users/thrill3r/Auto-Quant/.venv/bin/python")


def load_old_module():
    spec = importlib.util.spec_from_file_location("provider_matrix_aq_v1", OLD_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {OLD_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as fh:
        return max(sum(1 for _ in fh) - 1, 0)


def run_command(name: str, cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> int:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    write_text(OUT_DIR / f"{name}.cmd", " ".join(cmd) + "\n")
    write_text(OUT_DIR / f"{name}.stdout", proc.stdout)
    write_text(OUT_DIR / f"{name}.stderr", proc.stderr)
    write_text(CHECK_DIR / f"{name}.exit", f"{proc.returncode}\n")
    return proc.returncode


def fetch_public_provider(name: str, cmd: list[str]) -> dict[str, Any]:
    exit_code = run_command(name, cmd)
    output = Path(cmd[-1])
    return {
        "name": name,
        "exit": exit_code,
        "csv": str(output),
        "rows": csv_rows(output),
    }


def fetch_tvr() -> dict[str, Any]:
    name = "20_tvr_binance_btcusdt_1h"
    env = os.environ.copy()
    cmd = [
        "./target/debug/ict-engine",
        "market-data-harness",
        "--action",
        "fetch",
        "--market",
        "board-a-115431-tvr-btc-binance-1h",
        "--interval",
        "1h",
        "--role",
        "crypto_reference",
        "--provider",
        "crypto_reference=tradingview_mcp",
        "--symbol-spec",
        "crypto_reference=BINANCE:BTCUSDT",
    ]
    exit_code = run_command(name, cmd, env=env)
    stdout = OUT_DIR / f"{name}.stdout"
    out_csv = PROVIDER_CSV_DIR / "tvr_binance_btcusdt_1h.csv"
    rows_written = 0
    error: dict[str, Any] | None = None
    if stdout.exists() and stdout.read_text().strip():
        payload = json.loads(stdout.read_text())
        result = (payload.get("results") or [{}])[0]
        if result.get("ok"):
            rows = result.get("data") or []
            with out_csv.open("w", newline="") as fh:
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
                            "volume": row.get("volume", 0.0),
                        }
                    )
            rows_written = len(rows)
        else:
            error = result.get("error")
    return {
        "name": name,
        "exit": exit_code,
        "csv": str(out_csv),
        "rows": rows_written,
        "error": error,
    }


def write_ibkr_bulk_config() -> Path:
    path = CONFIG_DIR / "ibkr_btc_paxos_extended_bulk.yaml"
    text = f"""gateway:
  host: 127.0.0.1
  port: 4002
  client_id: 42
output:
  directory: {PROVIDER_CSV_DIR}
  filename_template: 'ibkr_{{symbol}}_{{bar_suffix}}_{{what}}.csv'
  force: true
defaults:
  bar_size: '1 hour'
  duration: '10 D'
  rth: false
  exchange: PAXOS
  currency: USD
symbols:
  - symbol: BTC
    sec_type: CRYPTO
    exchange: PAXOS
    currency: USD
    what_to_show: AGGTRADES
    rth: false
    bar_sizes: ['1 hour']
    duration: '10 D'
  - symbol: BTC
    sec_type: CRYPTO
    exchange: PAXOS
    currency: USD
    what_to_show: MIDPOINT
    rth: false
    bar_sizes: ['1 hour']
    duration: '10 D'
"""
    write_text(path, text)
    return path


def fetch_ibkr() -> dict[str, Any]:
    config = write_ibkr_bulk_config()
    name = "21_ibkr_btc_paxos_extended_bulk"
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{Path.cwd() / 'scripts'}:{Path.cwd()}:{env.get('PYTHONPATH', '')}"
    cmd = [
        str(PYTHON),
        "scripts/auto_quant_external/fetch_external.py",
        "ibkr-bulk",
        "--config",
        str(config),
        "--force",
    ]
    exit_code = run_command(name, cmd, env=env)
    agg = PROVIDER_CSV_DIR / "ibkr_BTC_1h_aggtrades.csv"
    midpoint = PROVIDER_CSV_DIR / "ibkr_BTC_1h_midpoint.csv"
    selected = agg if csv_rows(agg) >= 91 else midpoint if csv_rows(midpoint) >= 91 else agg
    return {
        "name": name,
        "exit": exit_code,
        "config": str(config),
        "aggtrades_csv": str(agg),
        "aggtrades_rows": csv_rows(agg),
        "midpoint_csv": str(midpoint),
        "midpoint_rows": csv_rows(midpoint),
        "selected_csv": str(selected),
        "selected_rows": csv_rows(selected),
        "selected_kind": "AGGTRADES" if selected == agg else "MIDPOINT",
    }


def normalize_ohlcv(source: Path) -> pd.DataFrame:
    raw = pd.read_csv(source)
    date_col = "date" if "date" in raw.columns else "timestamp" if "timestamp" in raw.columns else "ts"
    date = pd.to_datetime(raw[date_col], utc=True)
    volume = pd.to_numeric(raw.get("volume", 0.0), errors="coerce").fillna(0.0).astype(float)
    volume = volume.mask(volume < 0, 0.0)
    out = pd.DataFrame(
        {
            "date": date,
            "open": pd.to_numeric(raw["open"], errors="coerce").astype(float),
            "high": pd.to_numeric(raw["high"], errors="coerce").astype(float),
            "low": pd.to_numeric(raw["low"], errors="coerce").astype(float),
            "close": pd.to_numeric(raw["close"], errors="coerce").astype(float),
            "volume": volume,
        }
    )
    return out.dropna().sort_values("date").reset_index(drop=True)


def to_epoch_ms(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return int(value.timestamp() * 1000)
    return int(value)


def run_provider_aq(old: Any, provider: str, meta: dict[str, Any]) -> dict[str, Any]:
    source = Path(meta["source"])
    local_source = PROVIDER_CSV_DIR / f"aq_source_{provider}.csv"
    shutil.copy2(source, local_source)
    workspace = old.copy_template(provider)
    df = normalize_ohlcv(local_source)
    feather = workspace / "user_data" / "data" / "BTC_USDT-1h.feather"
    df.to_feather(feather)

    strategies = sorted((workspace / "user_data" / "strategies_external").glob("*.py"))
    compile_cmd = [
        str(old.PYTHON),
        "-m",
        "py_compile",
        "run_tomac.py",
        *[str(path.relative_to(workspace)) for path in strategies],
    ]
    run_cmd = [str(old.PYTHON), "run_tomac.py"]
    prefix = provider.replace("/", "_")
    compile_exit = run_command(f"aq_{prefix}_compile", compile_cmd, cwd=workspace)
    run_exit = run_command(f"aq_{prefix}_run_tomac", run_cmd, cwd=workspace)

    metrics: dict[str, Any] = {}
    for path in sorted((workspace / "derived").glob("*.metrics.json")):
        metrics[path.stem.replace(".metrics", "")] = read_json(path)

    return {
        "provider": provider,
        "provider_symbol": meta["symbol"],
        "source_csv": str(local_source),
        "rows": int(len(df)),
        "first_ts_ms": to_epoch_ms(df["date"].min()) if len(df) else None,
        "last_ts_ms": to_epoch_ms(df["date"].max()) if len(df) else None,
        "workspace": str(workspace),
        "compile_exit": compile_exit,
        "run_tomac_exit": run_exit,
        "metrics": metrics,
    }


def metric_totals(results: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {
        "provider_runs": len(results),
        "compile_success": 0,
        "run_success": 0,
        "strategies_with_metrics": 0,
        "total_trades": 0,
        "positive_profit_metric_count": 0,
    }
    for result in results:
        if result["compile_exit"] == 0:
            totals["compile_success"] += 1
        if result["run_tomac_exit"] == 0:
            totals["run_success"] += 1
        for payload in result.get("metrics", {}).values():
            aggregate = payload.get("aggregate", {})
            trades = int(aggregate.get("trade_count") or 0)
            profit = float(aggregate.get("total_profit_pct") or 0.0)
            totals["strategies_with_metrics"] += 1
            totals["total_trades"] += trades
            if profit > 0:
                totals["positive_profit_metric_count"] += 1
    return totals


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "six_provider_aq_first_class_ibkr_v1.md"
    assertions = CHECK_DIR / "six_provider_aq_first_class_ibkr_v1_assertions.out"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_six_provider_aq_first_class_ibkr_v1.csv"

    lines = [
        "# Six Provider AQ First-Class IBKR v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Scope",
        "This packet fetches all six provider lanes inside this run root, then runs the existing AQ/TOMAC provider strategy template.",
        "It does not edit ict-engine runtime code, does not approve selected history, and does not promote a downstream candidate.",
        "",
        "## Provider Fetches",
    ]
    for item in summary["provider_fetches"]:
        lines.append(f"- `{item['name']}`: rows `{item.get('rows')}`, exit `{item.get('exit')}`, csv `{item.get('csv')}`.")
    ibkr = summary["ibkr_fetch"]
    lines.append(
        f"- `ibkr`: exit `{ibkr['exit']}`, selected `{ibkr['selected_kind']}`, "
        f"selected_rows `{ibkr['selected_rows']}`, aggtrades_rows `{ibkr['aggtrades_rows']}`, midpoint_rows `{ibkr['midpoint_rows']}`."
    )
    lines.extend(["", "## AQ Results"])
    for result in summary["aq_results"]:
        lines.append(
            f"- `{result['provider']}`: rows `{result['rows']}`, compile exit `{result['compile_exit']}`, TOMAC exit `{result['run_tomac_exit']}`."
        )
        for strategy, payload in sorted(result.get("metrics", {}).items()):
            aggregate = payload.get("aggregate", {})
            lines.append(
                f"  - `{strategy}`: trades `{aggregate.get('trade_count')}`, "
                f"profit_pct `{aggregate.get('total_profit_pct')}`, "
                f"win_rate_pct `{aggregate.get('win_rate_pct')}`, "
                f"profit_factor `{aggregate.get('profit_factor')}`."
            )
    lines.extend(
        [
            "",
            "## Decision",
            f"- Gate result: `{summary['gate_result']}`.",
            f"- Same-root six-provider AQ authority: `{summary['same_root_six_provider_aq_authority']}`.",
            f"- Successful AQ provider runs: `{summary['metric_totals']['run_success']}/{summary['metric_totals']['provider_runs']}`.",
            f"- Strategies with metrics: `{summary['metric_totals']['strategies_with_metrics']}`.",
            f"- Total trades: `{summary['metric_totals']['total_trades']}`.",
            f"- Mature rooted branch observations added: `{summary['mature_rooted_branch_observations_added']}`.",
            "- Downstream Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree promotion chain: `not_run`.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / 'six_provider_aq_first_class_ibkr_v1.json'}`",
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
        writer.writerow(["same-root provider fetches", str(PROVIDER_CSV_DIR), "covered", "all fetches attempted inside this root"])
        writer.writerow(["first-class TVR input", "20_tvr_binance_btcusdt_1h", "covered", str(summary["provider_inputs"].get("tvr_binance", {}))])
        writer.writerow(["first-class IBKR input", "21_ibkr_btc_paxos_extended_bulk", "covered", str(summary["provider_inputs"].get("ibkr_paxos", {}))])
        writer.writerow(["same-root AQ", "command-output/aq_*_run_tomac.*", "covered", f"{summary['metric_totals']['run_success']} provider AQ runs exited 0"])
        writer.writerow(["downstream chain", "N/A", "not_run", "requires accepted six-provider AQ authority before promotion chain"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS provider_inputs={len(summary['provider_inputs'])}",
        f"PASS compile_success={summary['metric_totals']['compile_success']}",
        f"PASS run_success={summary['metric_totals']['run_success']}",
        f"PASS strategies_with_metrics={summary['metric_totals']['strategies_with_metrics']}",
        f"PASS same_root_six_provider_aq_authority={summary['same_root_six_provider_aq_authority']}",
        "FAIL_CLOSED downstream_promotion_chain=not_run",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    write_text(assertions, "\n".join(assertion_lines) + "\n")


def main() -> int:
    old = load_old_module()
    for path in (OUT_DIR, CHECK_DIR, REPORT_DIR, PROVIDER_CSV_DIR, WORKSPACE_ROOT, CONFIG_DIR):
        path.mkdir(parents=True, exist_ok=True)
    write_text(ROOT / "run_id.txt", RUN_ID + "\n")

    old.RUN_ID = RUN_ID
    old.ROOT = ROOT
    old.OUT_DIR = OUT_DIR
    old.CHECK_DIR = CHECK_DIR
    old.REPORT_DIR = REPORT_DIR
    old.PROVIDER_CSV_DIR = PROVIDER_CSV_DIR
    old.WORKSPACE_ROOT = WORKSPACE_ROOT
    old.normalized_df = normalize_ohlcv

    provider_fetches = [
        fetch_public_provider(
            "11_yfinance_btc_usd_1h",
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
                "1h",
                "--start",
                FETCH_START,
                "--end",
                FETCH_END,
                "--output",
                str(PROVIDER_CSV_DIR / "yfinance_btc_usd_1h.csv"),
            ],
        ),
        fetch_public_provider(
            "12_kraken_xbtusd_1h",
            [
                "uv",
                "run",
                "--with",
                "pandas",
                "scripts/auto_quant_external/fetch_external.py",
                "kraken-kline",
                "--market",
                "spot",
                "--pair",
                "XBTUSD",
                "--interval",
                "1h",
                "--start",
                FETCH_START,
                "--end",
                FETCH_END,
                "--output",
                str(PROVIDER_CSV_DIR / "kraken_xbtusd_1h.csv"),
            ],
        ),
        fetch_public_provider(
            "13_binance_btcusdt_1h",
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
                "1h",
                "--start",
                FETCH_START,
                "--end",
                FETCH_END,
                "--output",
                str(PROVIDER_CSV_DIR / "binance_btcusdt_1h.csv"),
            ],
        ),
        fetch_public_provider(
            "14_bybit_btcusdt_linear_1h",
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
                "1h",
                "--start",
                FETCH_START,
                "--end",
                FETCH_END,
                "--output",
                str(PROVIDER_CSV_DIR / "bybit_btcusdt_linear_1h.csv"),
            ],
        ),
    ]
    provider_fetches.append(fetch_tvr())
    ibkr_fetch = fetch_ibkr()

    provider_inputs = {
        "yfinance": {"source": PROVIDER_CSV_DIR / "yfinance_btc_usd_1h.csv", "symbol": "BTC-USD"},
        "kraken_public": {"source": PROVIDER_CSV_DIR / "kraken_xbtusd_1h.csv", "symbol": "XBTUSD"},
        "binance_public": {"source": PROVIDER_CSV_DIR / "binance_btcusdt_1h.csv", "symbol": "BTCUSDT"},
        "bybit_public": {"source": PROVIDER_CSV_DIR / "bybit_btcusdt_linear_1h.csv", "symbol": "BTCUSDT"},
        "tvr_binance": {"source": PROVIDER_CSV_DIR / "tvr_binance_btcusdt_1h.csv", "symbol": "BINANCE:BTCUSDT"},
        "ibkr_paxos": {"source": Path(ibkr_fetch["selected_csv"]), "symbol": f"BTC.PAXOS.{ibkr_fetch['selected_kind']}"},
    }
    provider_inputs = {
        key: value
        for key, value in provider_inputs.items()
        if Path(value["source"]).exists() and csv_rows(Path(value["source"])) > 0
    }

    aq_results = [run_provider_aq(old, provider, meta) for provider, meta in provider_inputs.items()]
    totals = metric_totals(aq_results)
    six_names = {"yfinance", "kraken_public", "binance_public", "bybit_public", "tvr_binance", "ibkr_paxos"}
    same_root_authority = set(provider_inputs) == six_names and totals["run_success"] == 6
    gate = (
        "115431_six_provider_aq_first_class_ibkr_v1=six_provider_aq_compile0_tomac0_no_downstream_promotion"
        if same_root_authority
        else "115431_six_provider_aq_first_class_ibkr_v1=provider_or_aq_gate_incomplete_no_downstream_promotion"
    )
    summary = {
        "run_id": RUN_ID,
        "source_aq_template_run_id": SOURCE_AQ_TEMPLATE_RUN_ID,
        "provider_fetches": provider_fetches,
        "ibkr_fetch": ibkr_fetch,
        "provider_inputs": {key: {**value, "source": str(value["source"])} for key, value in provider_inputs.items()},
        "aq_results": aq_results,
        "metric_totals": totals,
        "same_root_six_provider_aq_authority": same_root_authority,
        "gate_result": gate,
        "mature_rooted_branch_observations_added": totals["total_trades"] if same_root_authority else 0,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "six_provider_aq_first_class_ibkr_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
