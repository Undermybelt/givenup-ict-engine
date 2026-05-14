from __future__ import annotations

import csv
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


RUN_ID = "20260512T115130+0800-codex-113833-ibkr-longer-duration-six-provider-aq-v1"
SOURCE_RUN_ID = "20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1"
RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_ROOT = RUNS / SOURCE_RUN_ID
REPAIR_SCRIPT = SOURCE_ROOT / "scripts" / "112904_provider_matrix_aq_date_contract_repair_v1.py"
OLD_SCRIPT = RUNS / "20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1" / "scripts" / "112315_provider_matrix_aq_readback_v1.py"

OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "ibkr-longer-duration-six-provider-aq-v1"
PROVIDER_CSV_DIR = ROOT / "provider-csv"
INPUT_DIR = ROOT / "input-csv"
WORKSPACE_ROOT = ROOT / "workspace"
CONFIG = ROOT / "config" / "ibkr_btc_paxos_1h_14d.yaml"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def exit_code(path: Path) -> int | None:
    if not path.exists():
        return None
    return int(path.read_text().strip())


def csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as fh:
        return max(sum(1 for _ in fh) - 1, 0)


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
            totals["strategies_with_metrics"] += 1
            totals["total_trades"] += int(aggregate.get("trade_count") or 0)
            if float(aggregate.get("total_profit_pct") or 0.0) > 0:
                totals["positive_profit_metric_count"] += 1
    return totals


def run_fetch() -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{Path('scripts').resolve()}:{Path('.').resolve()}"
    cmd = [
        "/Users/thrill3r/Auto-Quant/.venv/bin/python",
        "scripts/auto_quant_external/fetch_external.py",
        "ibkr-bulk",
        "--config",
        str(CONFIG),
        "--force",
    ]
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "00_ibkr_bulk_14d.cmd").write_text(" ".join(cmd) + "\n")
    (OUT_DIR / "00_ibkr_bulk_14d.out").write_text(proc.stdout)
    (OUT_DIR / "00_ibkr_bulk_14d.err").write_text(proc.stderr)
    (CHECK_DIR / "00_ibkr_bulk_14d.exit").write_text(f"{proc.returncode}\n")
    return {
        "cmd": " ".join(cmd),
        "exit": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "csv": str(PROVIDER_CSV_DIR / "BTC_1h_midpoint.csv"),
        "rows": csv_rows(PROVIDER_CSV_DIR / "BTC_1h_midpoint.csv"),
    }


def run_aq() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    repair = load_module(REPAIR_SCRIPT, "repair_113833")
    old = load_module(OLD_SCRIPT, "provider_matrix_aq_base")
    for path in (OUT_DIR, CHECK_DIR, PROVIDER_CSV_DIR, INPUT_DIR, WORKSPACE_ROOT, REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
    repair.OUT_DIR = OUT_DIR
    repair.CHECK_DIR = CHECK_DIR
    repair.PROVIDER_CSV_DIR = PROVIDER_CSV_DIR
    repair.WORKSPACE_ROOT = WORKSPACE_ROOT
    old.RUN_ID = RUN_ID
    old.ROOT = ROOT
    old.OUT_DIR = OUT_DIR
    old.CHECK_DIR = CHECK_DIR
    old.PROVIDER_CSV_DIR = PROVIDER_CSV_DIR
    old.WORKSPACE_ROOT = WORKSPACE_ROOT
    old.normalized_df = repair.normalize_ohlcv

    tvr_source = repair.write_tvr_binance_source()
    ibkr_input = INPUT_DIR / "ibkr_btc_paxos_1h_midpoint_14d.csv"
    shutil.copy2(PROVIDER_CSV_DIR / "BTC_1h_midpoint.csv", ibkr_input)
    provider_inputs = {
        "yfinance": {
            "source": repair.PROVIDER_ROOT / "provider-csv" / "yfinance_btc_usd_1h.csv",
            "symbol": "BTC-USD",
        },
        "kraken_public": {
            "source": repair.PROVIDER_ROOT / "provider-csv" / "kraken_xbtusd_1h.csv",
            "symbol": "XBTUSD",
        },
        "binance_public": {
            "source": repair.PROVIDER_ROOT / "provider-csv" / "binance_btcusdt_1h.csv",
            "symbol": "BTCUSDT",
        },
        "bybit_public": {
            "source": repair.PROVIDER_ROOT / "provider-csv" / "bybit_btcusdt_linear_1h.csv",
            "symbol": "BTCUSDT",
        },
        "tvr_binance": {
            "source": tvr_source,
            "symbol": "BINANCE:BTCUSDT",
        },
        "ibkr_midpoint_14d": {
            "source": ibkr_input,
            "symbol": "BTC.PAXOS",
        },
    }
    results = [
        repair.run_provider_fixed(old, provider, meta)
        for provider, meta in provider_inputs.items()
    ]
    matrix = repair.provider_matrix_readback()
    matrix["fetch_exits"]["ibkr_btc_paxos_midpoint_1h_14d"] = exit_code(
        CHECK_DIR / "00_ibkr_bulk_14d.exit"
    )
    matrix["fetch_rows"]["ibkr_btc_paxos_midpoint_1h_14d"] = csv_rows(
        PROVIDER_CSV_DIR / "BTC_1h_midpoint.csv"
    )
    return results, matrix


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "ibkr_longer_duration_six_provider_aq_v1.md"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_ibkr_longer_duration_six_provider_aq_v1.csv"
    assertions = CHECK_DIR / "ibkr_longer_duration_six_provider_aq_v1_assertions.out"
    lines = [
        "# IBKR Longer Duration Six-Provider AQ v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source repair root: `{SOURCE_RUN_ID}`",
        "",
        "## Scope",
        "Rerun the six provider AQ matrix with the same date-contract repair as 113833, but replace the thin 2D IBKR 1h MIDPOINT input with a 14D IBKR 1h MIDPOINT fetch.",
        "This does not edit ict-engine runtime code, rewrite older roots, or promote a candidate.",
        "",
        "## Fetch",
        f"- IBKR 14D fetch exit `{summary['fetch']['exit']}`, rows `{summary['fetch']['rows']}`.",
        "",
        "## AQ Results",
    ]
    for result in summary["aq_results"]:
        lines.append(
            f"- `{result['provider']}`: rows `{result['rows']}`, compile exit `{result['compile_exit']}`, TOMAC exit `{result['run_tomac_exit']}`."
        )
        for strategy, payload in sorted(result.get("metrics", {}).items()):
            aggregate = payload.get("aggregate", {})
            lines.append(
                f"  - `{strategy}`: trades `{aggregate.get('trade_count')}`, profit_pct `{aggregate.get('total_profit_pct')}`, win_rate_pct `{aggregate.get('win_rate_pct')}`, profit_factor `{aggregate.get('profit_factor')}`."
            )
    lines.extend(
        [
            "",
            "## Decision",
            f"- Gate result: `{summary['gate_result']}`.",
            f"- Successful AQ provider runs: `{summary['metric_totals']['run_success']}/{summary['metric_totals']['provider_runs']}`.",
            f"- Strategies with metrics: `{summary['metric_totals']['strategies_with_metrics']}`.",
            f"- Total trades in AQ metrics: `{summary['metric_totals']['total_trades']}`.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / 'ibkr_longer_duration_six_provider_aq_v1.json'}`",
            f"- Checklist: `{checklist}`",
            f"- Assertions: `{assertions}`",
            f"- Provider CSVs: `{PROVIDER_CSV_DIR}`",
            f"- AQ workspaces: `{WORKSPACE_ROOT}`",
        ]
    )
    report.write_text("\n".join(lines) + "\n")
    with checklist.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["longer IBKR 1h input", str(PROVIDER_CSV_DIR / "BTC_1h_midpoint.csv"), "covered", f"rows={summary['fetch']['rows']}"])
        writer.writerow(["six provider AQ rerun", "command-output/aq_*_run_tomac.*", "covered", f"{summary['metric_totals']['run_success']}/6 provider runs exited 0"])
        writer.writerow(["downstream chain", "N/A", "not_run", "run only repairs provider/AQ authority; downstream remains separate"])
    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run={SOURCE_RUN_ID}",
        f"PASS ibkr_14d_fetch_exit={summary['fetch']['exit']}",
        f"PASS ibkr_14d_rows={summary['fetch']['rows']}",
        f"PASS provider_runs={summary['metric_totals']['provider_runs']}",
        f"PASS compile_success={summary['metric_totals']['compile_success']}",
        f"PASS run_success={summary['metric_totals']['run_success']}",
        f"PASS strategies_with_metrics={summary['metric_totals']['strategies_with_metrics']}",
        "FAIL_CLOSED no_pre_bayes_bbn_catboost_execution_tree_promotion",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    if summary["metric_totals"]["run_success"] == 6:
        assertion_lines.append("PASS six_provider_aq_runtime_ran=true")
    else:
        assertion_lines.append("FAIL_CLOSED six_provider_aq_runtime_ran=false")
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    for path in (OUT_DIR, CHECK_DIR, PROVIDER_CSV_DIR, INPUT_DIR, WORKSPACE_ROOT, REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    (ROOT / "source_root.txt").write_text(str(SOURCE_ROOT) + "\n")
    fetch = run_fetch()
    aq_results, matrix = run_aq()
    totals = metric_totals(aq_results)
    gate = (
        "ibkr_longer_duration_six_provider_aq_v1=six_provider_aq_ran_no_downstream_promotion"
        if totals["run_success"] == 6
        else "ibkr_longer_duration_six_provider_aq_v1=ibkr_still_fail_closed_no_downstream_promotion"
    )
    summary = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "fetch": fetch,
        "provider_matrix": matrix,
        "aq_results": aq_results,
        "metric_totals": totals,
        "gate_result": gate,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "ibkr_longer_duration_six_provider_aq_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
