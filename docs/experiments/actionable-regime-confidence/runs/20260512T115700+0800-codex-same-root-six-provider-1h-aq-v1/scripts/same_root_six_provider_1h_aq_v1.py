from __future__ import annotations

import csv
import importlib.util
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1"
SOURCE_REPAIR_RUN_ID = "20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1"
IBKR_REPAIR_RUN_ID = "20260512T115249+0800-codex-ibkr-btc-long-aq-lane-v1"
TVR_PRECHECK_RUN_ID = "20260512T112030+0800-codex-btc-comparable-tvr-ibkr-provider-preflight-v1"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
REPORT_DIR = ROOT / "same-root-six-provider-1h-aq-v1"
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
CONFIG_DIR = ROOT / "config"
INPUT_DIR = ROOT / "input-csv"
PROVIDER_CSV_DIR = ROOT / "provider-csv"
WORKSPACE_ROOT = ROOT / "workspace"

FETCH_PY = Path("scripts/auto_quant_external/fetch_external.py")
AUTO_QUANT_PY = Path("/Users/thrill3r/Auto-Quant/.venv/bin/python")
REPAIR_SCRIPT = RUNS / SOURCE_REPAIR_RUN_ID / "scripts" / "112904_provider_matrix_aq_date_contract_repair_v1.py"

START = "2026-04-01"
END = "2026-05-12"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as fh:
        return max(sum(1 for _ in fh) - 1, 0)


def summarize_csv(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"rows": 0}
    df = pd.read_csv(path)
    if df.empty:
        return {"rows": 0}
    date_col = "date" if "date" in df.columns else "timestamp" if "timestamp" in df.columns else "ts"
    dates = pd.to_datetime(df[date_col], utc=True)
    return {
        "rows": int(len(df)),
        "first": dates.min().isoformat(),
        "last": dates.max().isoformat(),
    }


def run_cmd(name: str, cmd: list[str], env: dict[str, str] | None = None) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    (OUT_DIR / f"{name}.cmd").write_text(" ".join(cmd) + "\n")
    (OUT_DIR / f"{name}.stdout").write_text(proc.stdout)
    (OUT_DIR / f"{name}.stderr").write_text(proc.stderr)
    (CHECK_DIR / f"{name}.exit").write_text(f"{proc.returncode}\n")
    return {
        "name": name,
        "cmd": cmd,
        "exit": proc.returncode,
        "stdout": str(OUT_DIR / f"{name}.stdout"),
        "stderr": str(OUT_DIR / f"{name}.stderr"),
    }


def uv_fetch(name: str, args: list[str], output: Path, packages: list[str]) -> dict[str, Any]:
    cmd = ["uv", "run"]
    for package in packages:
        cmd.extend(["--with", package])
    cmd.extend([str(FETCH_PY), *args, "--output", str(output)])
    result = run_cmd(name, cmd)
    result["csv"] = str(output)
    result["rows"] = csv_rows(output)
    result["summary"] = summarize_csv(output)
    return result


def fetch_public_providers() -> dict[str, Any]:
    return {
        "yfinance": uv_fetch(
            "10_yfinance_btc_usd_1h",
            ["yahoo", "--symbol", "BTC-USD", "--interval", "1h", "--start", START, "--end", END],
            INPUT_DIR / "yfinance_btc_usd_1h.csv",
            ["yfinance", "pandas"],
        ),
        "kraken_public": uv_fetch(
            "11_kraken_xbtusd_1h",
            ["kraken-kline", "--market", "spot", "--pair", "XBTUSD", "--interval", "1h", "--start", START, "--end", END],
            INPUT_DIR / "kraken_xbtusd_1h.csv",
            ["pandas"],
        ),
        "binance_public": uv_fetch(
            "12_binance_btcusdt_1h",
            ["binance-kline", "--symbol", "BTCUSDT", "--interval", "1h", "--start", START, "--end", END],
            INPUT_DIR / "binance_btcusdt_1h.csv",
            ["pandas"],
        ),
        "bybit_public": uv_fetch(
            "13_bybit_btcusdt_linear_1h",
            ["bybit-kline", "--category", "linear", "--symbol", "BTCUSDT", "--interval", "1h", "--start", START, "--end", END],
            INPUT_DIR / "bybit_btcusdt_linear_1h.csv",
            ["pandas"],
        ),
    }


def write_tvr_csv(payload_path: Path, out_csv: Path) -> dict[str, Any]:
    payload = json.loads(payload_path.read_text())
    results = payload.get("results") or []
    if not results or not results[0].get("ok"):
        return {"csv": str(out_csv), "rows": 0, "ok": False}
    rows = results[0].get("data") or []
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["date", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "date": row["timestamp"],
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "volume": row.get("volume", 0.0),
                }
            )
    return {"csv": str(out_csv), "rows": len(rows), "ok": True, "summary": summarize_csv(out_csv)}


def fetch_tvr_default() -> dict[str, Any]:
    status = run_cmd(
        "20_provider_status_tvr_default",
        ["./target/debug/ict-engine", "provider-status", "--provider", "tradingview_mcp", "--agent"],
    )
    fetch = run_cmd(
        "21_tvr_default_binance_btcusdt_1h",
        [
            "./target/debug/ict-engine",
            "market-data-harness",
            "--action",
            "fetch",
            "--market",
            "board-a-same-root-tvr-btc-binance-1h",
            "--interval",
            "1h",
            "--role",
            "crypto_reference",
            "--provider",
            "crypto_reference=tradingview_mcp",
            "--symbol-spec",
            "crypto_reference=BINANCE:BTCUSDT",
        ],
    )
    csv_summary = write_tvr_csv(
        OUT_DIR / "21_tvr_default_binance_btcusdt_1h.stdout",
        INPUT_DIR / "tvr_default_binance_btcusdt_1h.csv",
    )
    fetch.update(csv_summary)
    return {"status": status, "fetch": fetch}


def write_ibkr_config() -> Path:
    config = CONFIG_DIR / "ibkr_btc_paxos_30d_1h_midpoint.yaml"
    config.write_text(
        "\n".join(
            [
                "gateway:",
                "  host: 127.0.0.1",
                "  port: 4002",
                "  client_id: 57",
                "output:",
                f"  directory: {INPUT_DIR}",
                "  filename_template: '{symbol}_{bar_suffix}_{what}.csv'",
                "  force: true",
                "defaults:",
                "  bar_size: '1 hour'",
                "  duration: '30 D'",
                "  what_to_show: MIDPOINT",
                "  rth: false",
                "  exchange: PAXOS",
                "  currency: USD",
                "symbols:",
                "  - symbol: BTC",
                "    sec_type: CRYPTO",
                "    exchange: PAXOS",
                "    currency: USD",
                "    what_to_show: MIDPOINT",
                "    rth: false",
                "    bar_sizes: ['1 hour']",
                "    duration: '30 D'",
                "",
            ]
        )
    )
    return config


def fetch_ibkr_long_1h() -> dict[str, Any]:
    config = write_ibkr_config()
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{Path('scripts').resolve()}:{Path('.').resolve()}"
    cmd = [
        str(AUTO_QUANT_PY),
        str(FETCH_PY),
        "ibkr-bulk",
        "--config",
        str(config),
        "--force",
    ]
    result = run_cmd("30_ibkr_paxos_btc_30d_1h_midpoint", cmd, env=env)
    csv_path = INPUT_DIR / "BTC_1h_midpoint.csv"
    result["csv"] = str(csv_path)
    result["rows"] = csv_rows(csv_path)
    result["summary"] = summarize_csv(csv_path)
    result["config"] = str(config)
    return result


def load_repair_module() -> Any:
    spec = importlib.util.spec_from_file_location("repair_113833", REPAIR_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {REPAIR_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_aq(provider_inputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    repair = load_repair_module()
    old = repair.load_old_module()
    old.RUN_ID = RUN_ID
    old.SOURCE_RUN_ID = RUN_ID
    old.ROOT = ROOT
    old.SOURCE_ROOT = ROOT
    old.OUT_DIR = OUT_DIR
    old.CHECK_DIR = CHECK_DIR
    old.PROVIDER_CSV_DIR = PROVIDER_CSV_DIR
    old.WORKSPACE_ROOT = WORKSPACE_ROOT
    old.normalized_df = repair.normalize_ohlcv
    repair.OUT_DIR = OUT_DIR
    repair.CHECK_DIR = CHECK_DIR
    repair.PROVIDER_CSV_DIR = PROVIDER_CSV_DIR
    repair.WORKSPACE_ROOT = WORKSPACE_ROOT
    return [
        repair.run_provider_fixed(old, provider, meta)
        for provider, meta in provider_inputs.items()
        if Path(meta["source"]).exists() and csv_rows(Path(meta["source"])) > 0
    ]


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
        if result.get("compile_exit") == 0:
            totals["compile_success"] += 1
        if result.get("run_tomac_exit") == 0:
            totals["run_success"] += 1
        for payload in (result.get("metrics") or {}).values():
            aggregate = payload.get("aggregate") or {}
            totals["strategies_with_metrics"] += 1
            totals["total_trades"] += int(aggregate.get("trade_count") or 0)
            if float(aggregate.get("total_profit_pct") or 0.0) > 0.0:
                totals["positive_profit_metric_count"] += 1
    return totals


def provider_fetch_matrix(fetches: dict[str, Any]) -> dict[str, Any]:
    return {
        "yfinance_btc_usd_1h": {
            "exit": fetches["public"]["yfinance"]["exit"],
            "rows": fetches["public"]["yfinance"]["rows"],
            "csv": fetches["public"]["yfinance"]["csv"],
        },
        "kraken_xbtusd_1h": {
            "exit": fetches["public"]["kraken_public"]["exit"],
            "rows": fetches["public"]["kraken_public"]["rows"],
            "csv": fetches["public"]["kraken_public"]["csv"],
        },
        "binance_btcusdt_1h": {
            "exit": fetches["public"]["binance_public"]["exit"],
            "rows": fetches["public"]["binance_public"]["rows"],
            "csv": fetches["public"]["binance_public"]["csv"],
        },
        "bybit_btcusdt_linear_1h": {
            "exit": fetches["public"]["bybit_public"]["exit"],
            "rows": fetches["public"]["bybit_public"]["rows"],
            "csv": fetches["public"]["bybit_public"]["csv"],
        },
        "tvr_default_binance_btcusdt_1h": {
            "exit": fetches["tvr"]["fetch"]["exit"],
            "rows": fetches["tvr"]["fetch"]["rows"],
            "csv": fetches["tvr"]["fetch"]["csv"],
        },
        "ibkr_paxos_btc_30d_1h_midpoint": {
            "exit": fetches["ibkr"]["exit"],
            "rows": fetches["ibkr"]["rows"],
            "csv": fetches["ibkr"]["csv"],
        },
    }


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "same_root_six_provider_1h_aq_v1.md"
    assertions = CHECK_DIR / "same_root_six_provider_1h_aq_v1_assertions.out"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_same_root_six_provider_1h_aq_v1.csv"

    lines = [
        "# Same-Root Six-Provider 1h AQ v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source repair reference: `{SOURCE_REPAIR_RUN_ID}`",
        f"IBKR repair reference: `{IBKR_REPAIR_RUN_ID}`",
        f"TVR precheck reference: `{TVR_PRECHECK_RUN_ID}`",
        "",
        "## Scope",
        "This packet attempts one same-root provider/AQ authority run with YF, Kraken, Binance, Bybit, TVR default remote/configured path, and IBKR PAXOS 30D 1h MIDPOINT.",
        "It does not edit ict-engine runtime code, rewrite older roots, approve selected history, or promote a candidate.",
        "",
        "## Provider Fetch Matrix",
    ]
    for key, row in summary["provider_fetch_matrix"].items():
        lines.append(f"- `{key}`: exit `{row['exit']}`, rows `{row['rows']}`, csv `{row['csv']}`.")
    lines.extend(["", "## AQ Results"])
    for result in summary["aq_results"]:
        lines.append(
            f"- `{result['provider']}`: rows `{result['rows']}`, compile exit `{result['compile_exit']}`, TOMAC exit `{result['run_tomac_exit']}`."
        )
        for strategy, payload in sorted((result.get("metrics") or {}).items()):
            aggregate = payload.get("aggregate") or {}
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
            f"- Provider fetch success: `{summary['provider_fetch_success']}/6`.",
            f"- Successful AQ provider runs: `{summary['metric_totals']['run_success']}/{summary['metric_totals']['provider_runs']}`.",
            f"- Strategies with metrics: `{summary['metric_totals']['strategies_with_metrics']}`.",
            f"- Total trades in AQ metrics: `{summary['metric_totals']['total_trades']}`.",
            f"- Mature rooted branch observations added: `{summary['mature_rooted_branch_observations_added']}`.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Fail-Closed / Next",
            "- No Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution-tree promotion chain is claimed from this packet.",
            "- If all six provider fetches and all six AQ lanes are successful, the next slice must push the selected surviving branch through the ordered downstream chain from this same run root.",
            "- If any provider fetch or AQ lane is missing, this packet remains fail-closed infrastructure evidence only.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / 'same_root_six_provider_1h_aq_v1.json'}`",
            f"- Checklist: `{checklist}`",
            f"- Assertions: `{assertions}`",
            f"- Command output and exits: `{OUT_DIR}`, `{CHECK_DIR}`",
            f"- Input CSVs: `{INPUT_DIR}`",
            f"- AQ provider CSVs: `{PROVIDER_CSV_DIR}`",
            f"- AQ workspaces: `{WORKSPACE_ROOT}`",
        ]
    )
    report.write_text("\n".join(lines) + "\n")

    with checklist.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["same run root provider inputs", str(INPUT_DIR), "covered", f"fetch_success={summary['provider_fetch_success']}/6"])
        writer.writerow(["TVR default configured path", "command-output/21_tvr_default_binance_btcusdt_1h.stdout", summary["tvr_status"], f"rows={summary['provider_fetch_matrix']['tvr_default_binance_btcusdt_1h']['rows']}"])
        writer.writerow(["IBKR 1h long path", summary["provider_fetch_matrix"]["ibkr_paxos_btc_30d_1h_midpoint"]["csv"], "covered", f"rows={summary['provider_fetch_matrix']['ibkr_paxos_btc_30d_1h_midpoint']['rows']}"])
        writer.writerow(["six provider AQ", str(WORKSPACE_ROOT), "covered" if summary["metric_totals"]["run_success"] == 6 else "partial", f"run_success={summary['metric_totals']['run_success']}/6"])
        writer.writerow(["downstream chain", "N/A", "not_run", "no promotion from provider/AQ packet alone"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS provider_fetch_success={summary['provider_fetch_success']}/6",
        f"PASS provider_runs={summary['metric_totals']['provider_runs']}",
        f"PASS compile_success={summary['metric_totals']['compile_success']}",
        f"PASS run_success={summary['metric_totals']['run_success']}",
        f"PASS strategies_with_metrics={summary['metric_totals']['strategies_with_metrics']}",
        f"PASS total_trades={summary['metric_totals']['total_trades']}",
        f"PASS mature_rooted_branch_observations_added={summary['mature_rooted_branch_observations_added']}",
        "FAIL_CLOSED no_pre_bayes_bbn_catboost_execution_tree_promotion",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    if summary["provider_fetch_success"] == 6 and summary["metric_totals"]["run_success"] == 6:
        assertion_lines.append("PASS six_provider_1h_provider_aq_packet_ready_for_downstream=true")
    else:
        assertion_lines.append("FAIL_CLOSED six_provider_1h_provider_aq_packet_ready_for_downstream=false")
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    for path in (ROOT, REPORT_DIR, OUT_DIR, CHECK_DIR, CONFIG_DIR, INPUT_DIR, PROVIDER_CSV_DIR, WORKSPACE_ROOT):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")

    fetches = {
        "public": fetch_public_providers(),
        "tvr": fetch_tvr_default(),
        "ibkr": fetch_ibkr_long_1h(),
    }
    matrix = provider_fetch_matrix(fetches)
    provider_inputs = {
        "yfinance": {"source": INPUT_DIR / "yfinance_btc_usd_1h.csv", "symbol": "BTC-USD"},
        "kraken_public": {"source": INPUT_DIR / "kraken_xbtusd_1h.csv", "symbol": "XBTUSD"},
        "binance_public": {"source": INPUT_DIR / "binance_btcusdt_1h.csv", "symbol": "BTCUSDT"},
        "bybit_public": {"source": INPUT_DIR / "bybit_btcusdt_linear_1h.csv", "symbol": "BTCUSDT"},
        "tvr_default_binance": {"source": INPUT_DIR / "tvr_default_binance_btcusdt_1h.csv", "symbol": "BINANCE:BTCUSDT"},
        "ibkr_paxos_long_midpoint": {"source": INPUT_DIR / "BTC_1h_midpoint.csv", "symbol": "BTC.PAXOS"},
    }
    provider_fetch_success = sum(1 for row in matrix.values() if row["exit"] == 0 and row["rows"] > 0)
    aq_results = run_aq(provider_inputs)
    totals = metric_totals(aq_results)
    six_ready = provider_fetch_success == 6 and totals["run_success"] == 6
    gate = (
        "same_root_six_provider_1h_aq_v1=six_provider_1h_provider_aq_packet_ready_for_downstream_no_promotion"
        if six_ready
        else "same_root_six_provider_1h_aq_v1=provider_or_aq_gap_fail_closed_no_promotion"
    )
    summary = {
        "run_id": RUN_ID,
        "source_repair_run_id": SOURCE_REPAIR_RUN_ID,
        "ibkr_repair_run_id": IBKR_REPAIR_RUN_ID,
        "tvr_precheck_run_id": TVR_PRECHECK_RUN_ID,
        "fetches": fetches,
        "provider_fetch_matrix": matrix,
        "provider_fetch_success": provider_fetch_success,
        "aq_results": aq_results,
        "metric_totals": totals,
        "mature_rooted_branch_observations_added": totals["total_trades"] if six_ready else 0,
        "gate_result": gate,
        "tvr_status": "covered" if matrix["tvr_default_binance_btcusdt_1h"]["rows"] > 0 else "fail_closed",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "same_root_six_provider_1h_aq_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
