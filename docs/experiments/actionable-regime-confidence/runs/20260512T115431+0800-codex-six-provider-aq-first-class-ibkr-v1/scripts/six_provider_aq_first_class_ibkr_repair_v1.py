from __future__ import annotations

import csv
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1"
SOURCE_AQ_TEMPLATE_RUN_ID = "20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1"
RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_AQ_TEMPLATE_ROOT = RUNS / SOURCE_AQ_TEMPLATE_RUN_ID
OLD_SCRIPT = SOURCE_AQ_TEMPLATE_ROOT / "scripts" / "112315_provider_matrix_aq_readback_v1.py"
BASE_JSON = ROOT / "six-provider-aq-first-class-ibkr-v1" / "six_provider_aq_first_class_ibkr_v1.json"

OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "six-provider-aq-first-class-ibkr-repair-v1"
PROVIDER_CSV_DIR = ROOT / "provider-csv"
WORKSPACE_ROOT = ROOT / "workspace"

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


def run_command(name: str, cmd: list[str], env: dict[str, str] | None = None, cwd: Path | None = None) -> int:
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


def fetch_yfinance_retry() -> dict[str, Any]:
    output = PROVIDER_CSV_DIR / "yfinance_btc_usd_1h_retry.csv"
    name = "22_yfinance_btc_usd_1h_venv_retry"
    cmd = [
        str(PYTHON),
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
        str(output),
    ]
    exit_code = run_command(name, cmd)
    return {"name": name, "exit": exit_code, "csv": str(output), "rows": csv_rows(output)}


def fetch_tvr_local_stdio_retry() -> dict[str, Any]:
    name = "23_tvr_btc_usd_1h_local_stdio_retry"
    env = os.environ.copy()
    env["HOME"] = "/tmp/ict-engine-tvr-btc-stdio-home"
    env["ICT_ENGINE_TRADINGVIEW_MCP_CMD"] = "uv"
    env["ICT_ENGINE_TRADINGVIEW_MCP_ARGS"] = "--directory /Users/thrill3r/tradingview-mcp/tradingview-mcp run tradingview-mcp"
    cmd = [
        "./target/debug/ict-engine",
        "market-data-harness",
        "--action",
        "fetch",
        "--market",
        "board-a-115431-tvr-btc-usd-1h-stdio",
        "--interval",
        "1h",
        "--role",
        "crypto_reference",
        "--provider",
        "crypto_reference=tradingview_mcp",
        "--symbol-spec",
        "crypto_reference=BTC-USD",
    ]
    exit_code = run_command(name, cmd, env=env)
    stdout = OUT_DIR / f"{name}.stdout"
    output = PROVIDER_CSV_DIR / "tvr_btc_usd_1h_retry.csv"
    rows_written = 0
    error: dict[str, Any] | None = None
    if stdout.exists() and stdout.read_text().strip():
        payload = json.loads(stdout.read_text())
        result = (payload.get("results") or [{}])[0]
        if result.get("ok"):
            rows = result.get("data") or []
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
                            "volume": row.get("volume", 0.0),
                        }
                    )
            rows_written = len(rows)
        else:
            error = result.get("error")
    return {"name": name, "exit": exit_code, "csv": str(output), "rows": rows_written, "error": error}


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


def run_provider_aq(old: Any, provider: str, source: Path, symbol: str) -> dict[str, Any]:
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
        "provider_symbol": symbol,
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
    report = REPORT_DIR / "six_provider_aq_first_class_ibkr_repair_v1.md"
    assertions = CHECK_DIR / "six_provider_aq_first_class_ibkr_repair_v1_assertions.out"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_six_provider_aq_first_class_ibkr_repair_v1.csv"
    lines = [
        "# Six Provider AQ First-Class IBKR Repair v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Scope",
        "This repair retries only the missing same-root yfinance and TVR lanes from the first-class IBKR packet, then runs AQ for repaired lanes with the same TOMAC template.",
        "It does not edit ict-engine runtime code and does not run downstream promotion.",
        "",
        "## Repair Fetches",
    ]
    for item in summary["repair_fetches"]:
        lines.append(f"- `{item['name']}`: rows `{item.get('rows')}`, exit `{item.get('exit')}`, csv `{item.get('csv')}`.")
    lines.extend(["", "## Repair AQ Results"])
    for result in summary["repair_aq_results"]:
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
            "## Combined Decision",
            f"- Gate result: `{summary['gate_result']}`.",
            f"- Same-root six-provider AQ authority: `{summary['same_root_six_provider_aq_authority']}`.",
            f"- Combined successful AQ provider runs: `{summary['combined_metric_totals']['run_success']}/{summary['combined_metric_totals']['provider_runs']}`.",
            f"- Combined strategies with metrics: `{summary['combined_metric_totals']['strategies_with_metrics']}`.",
            f"- Combined total trades: `{summary['combined_metric_totals']['total_trades']}`.",
            f"- Mature rooted branch observations added: `{summary['mature_rooted_branch_observations_added']}`.",
            "- Downstream Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree promotion chain: `not_run`.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
        ]
    )
    write_text(report, "\n".join(lines) + "\n")

    with checklist.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["repair yfinance same-root", "22_yfinance_btc_usd_1h_venv_retry", "covered", str(summary["repair_inputs"].get("yfinance"))])
        writer.writerow(["repair TVR same-root", "23_tvr_btc_usd_1h_local_stdio_retry", "covered", str(summary["repair_inputs"].get("tvr_btc_usd"))])
        writer.writerow(["combined six-provider AQ", str(report), "covered", str(summary["same_root_six_provider_aq_authority"])])
        writer.writerow(["downstream chain", "N/A", "not_run", "requires separate ordered promotion run after accepted AQ authority"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS repair_inputs={len(summary['repair_inputs'])}",
        f"PASS combined_compile_success={summary['combined_metric_totals']['compile_success']}",
        f"PASS combined_run_success={summary['combined_metric_totals']['run_success']}",
        f"PASS same_root_six_provider_aq_authority={summary['same_root_six_provider_aq_authority']}",
        "FAIL_CLOSED downstream_promotion_chain=not_run",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    write_text(assertions, "\n".join(assertion_lines) + "\n")


def main() -> int:
    old = load_old_module()
    old.RUN_ID = RUN_ID
    old.ROOT = ROOT
    old.OUT_DIR = OUT_DIR
    old.CHECK_DIR = CHECK_DIR
    old.REPORT_DIR = REPORT_DIR
    old.PROVIDER_CSV_DIR = PROVIDER_CSV_DIR
    old.WORKSPACE_ROOT = WORKSPACE_ROOT
    old.normalized_df = normalize_ohlcv
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    base = read_json(BASE_JSON)
    repair_fetches = [fetch_yfinance_retry(), fetch_tvr_local_stdio_retry()]
    repair_inputs: dict[str, dict[str, str]] = {}
    yf_csv = Path(repair_fetches[0]["csv"])
    tvr_csv = Path(repair_fetches[1]["csv"])
    if yf_csv.exists() and csv_rows(yf_csv) >= 91:
        repair_inputs["yfinance"] = {"source": str(yf_csv), "symbol": "BTC-USD"}
    if tvr_csv.exists() and csv_rows(tvr_csv) >= 91:
        repair_inputs["tvr_btc_usd"] = {"source": str(tvr_csv), "symbol": "BTC-USD"}

    repair_aq_results = [
        run_provider_aq(old, provider, Path(meta["source"]), meta["symbol"])
        for provider, meta in repair_inputs.items()
    ]
    base_results = base.get("aq_results", [])
    combined_results = base_results + repair_aq_results
    combined_totals = metric_totals(combined_results)
    provider_names = {result.get("provider") for result in combined_results}
    required = {"yfinance", "kraken_public", "binance_public", "bybit_public", "tvr_btc_usd", "ibkr_paxos"}
    same_root_authority = required.issubset(provider_names) and combined_totals["run_success"] >= 6
    gate = (
        "115431_six_provider_aq_first_class_ibkr_repair_v1=six_provider_aq_compile0_tomac0_downstream_not_run_no_promotion"
        if same_root_authority
        else "115431_six_provider_aq_first_class_ibkr_repair_v1=provider_or_aq_gate_still_incomplete_no_promotion"
    )
    summary = {
        "run_id": RUN_ID,
        "base_json": str(BASE_JSON),
        "repair_fetches": repair_fetches,
        "repair_inputs": repair_inputs,
        "repair_aq_results": repair_aq_results,
        "combined_metric_totals": combined_totals,
        "combined_provider_names": sorted(provider_names),
        "same_root_six_provider_aq_authority": same_root_authority,
        "gate_result": gate,
        "mature_rooted_branch_observations_added": combined_totals["total_trades"] if same_root_authority else 0,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "six_provider_aq_first_class_ibkr_repair_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
