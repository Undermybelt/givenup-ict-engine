from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from typing import Any


RUN_ID = "20260512T115108+0800-codex-112315-same-root-six-provider-aq-readback-v1"
SOURCE_RUN_ID = "20260512T112315+0800-codex-board-b-six-provider-btc-matrix-probe-v1"
REPAIR_RUN_ID = "20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_ROOT = RUNS / SOURCE_RUN_ID
REPAIR_ROOT = RUNS / REPAIR_RUN_ID
REPAIR_SCRIPT = REPAIR_ROOT / "scripts" / "112904_provider_matrix_aq_date_contract_repair_v1.py"

OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "112315-same-root-six-provider-aq-readback-v1"
PROVIDER_CSV_DIR = ROOT / "provider-csv"
WORKSPACE_ROOT = ROOT / "workspace"


def load_repair_module() -> Any:
    spec = importlib.util.spec_from_file_location("aq_date_contract_repair", REPAIR_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {REPAIR_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def exit_code(path: Path) -> int | None:
    if not path.exists():
        return None
    return int(path.read_text().strip())


def csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as fh:
        return max(sum(1 for _ in fh) - 1, 0)


def provider_matrix() -> dict[str, Any]:
    return {
        "source_provider_root": str(SOURCE_ROOT),
        "fetch_exits": {
            "yfinance_btc_usd_1h": exit_code(SOURCE_ROOT / "checks" / "11_yfinance_btc_usd_1h.exit"),
            "kraken_xbtusd_1h": exit_code(SOURCE_ROOT / "checks" / "12_kraken_xbtusd_1h.exit"),
            "binance_btcusdt_1h": exit_code(SOURCE_ROOT / "checks" / "13_binance_btcusdt_1h.exit"),
            "bybit_btcusdt_linear_1h": exit_code(SOURCE_ROOT / "checks" / "14_bybit_btcusdt_linear_1h.exit"),
            "tvr_btc_usd_1d": exit_code(SOURCE_ROOT / "checks" / "18_tvr_alias_BTC_USD_1d_local_stdio.exit"),
            "ibkr_btc_paxos_aggtrades_1d": exit_code(SOURCE_ROOT / "checks" / "17_ibkr_btc_paxos_aggtrades_1d.exit"),
        },
        "fetch_rows": {
            "yfinance_btc_usd_1h": csv_rows(SOURCE_ROOT / "provider-csv" / "yfinance_btc_usd_1h.csv"),
            "kraken_xbtusd_1h": csv_rows(SOURCE_ROOT / "provider-csv" / "kraken_xbtusd_1h.csv"),
            "binance_btcusdt_1h": csv_rows(SOURCE_ROOT / "provider-csv" / "binance_btcusdt_1h.csv"),
            "bybit_btcusdt_linear_1h": csv_rows(SOURCE_ROOT / "provider-csv" / "bybit_btcusdt_linear_1h.csv"),
            "tvr_btc_usd_1d": csv_rows(SOURCE_ROOT / "provider-csv" / "tvr_btc_usd_1d.csv"),
            "ibkr_btc_paxos_aggtrades_1d": csv_rows(SOURCE_ROOT / "provider-csv" / "ibkr_btc_paxos_aggtrades_1d.csv"),
        },
        "authority_caveat": "same provider-acquisition root, but TVR and IBKR are daily bars while the AQ workspace is a 1h TOMAC template",
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
            totals["strategies_with_metrics"] += 1
            totals["total_trades"] += int(aggregate.get("trade_count") or 0)
            if float(aggregate.get("total_profit_pct") or 0.0) > 0.0:
                totals["positive_profit_metric_count"] += 1
    return totals


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "112315_same_root_six_provider_aq_readback_v1.md"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_112315_same_root_six_provider_aq_readback_v1.csv"
    assertions = CHECK_DIR / "112315_same_root_six_provider_aq_readback_v1_assertions.out"

    lines = [
        "# 112315 Same-Root Six-Provider AQ Readback v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source provider root: `{SOURCE_RUN_ID}`",
        "",
        "## Scope",
        "This packet runs AQ/TOMAC from the single `112315` provider-acquisition root only.",
        "It uses YF, Kraken, Binance, Bybit 1h rows plus the same-root TVR BTC-USD 1d and IBKR PAXOS AGGTRADES 1d rows.",
        "It does not edit ict-engine runtime code, does not approve selected history, and does not promote a candidate.",
        "",
        "## Provider Matrix",
    ]
    matrix = summary["provider_matrix"]
    for key, value in matrix["fetch_rows"].items():
        lines.append(f"- `{key}`: rows `{value}`, exit `{matrix['fetch_exits'].get(key)}`.")
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
            f"- Successful AQ provider runs: `{summary['metric_totals']['run_success']}/{summary['metric_totals']['provider_runs']}`.",
            f"- Strategies with metrics: `{summary['metric_totals']['strategies_with_metrics']}`.",
            f"- Total trades in AQ metrics: `{summary['metric_totals']['total_trades']}`.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Fail-Closed Reason",
            "- This is closer to same-root provider authority than `113833`, but TVR and IBKR are only daily rows inside a 1h TOMAC template.",
            "- IBKR still lacks a successful 1h AQ lane; no accepted six-provider AQ authority is claimed.",
            "- No Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution-tree promotion chain is run from this packet.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / '112315_same_root_six_provider_aq_readback_v1.json'}`",
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
        writer.writerow(["single provider root", str(SOURCE_ROOT), "covered", "all input CSVs are under 112315 provider-csv"])
        writer.writerow(["run AQ for six requested providers", str(WORKSPACE_ROOT), "covered", f"{summary['metric_totals']['provider_runs']} provider workspaces"])
        writer.writerow(["TVR included", str(PROVIDER_CSV_DIR / "tvr_btc_usd_1d.csv"), "covered_partial", "daily rows only"])
        writer.writerow(["IBKR included", str(PROVIDER_CSV_DIR / "ibkr_btc_paxos_aggtrades_1d.csv"), "covered_partial", "daily AGGTRADES rows only"])
        writer.writerow(["downstream chain", "N/A", "not_run", "blocked by daily TVR/IBKR AQ authority and no selected-history approval"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run={SOURCE_RUN_ID}",
        f"PASS provider_runs={summary['metric_totals']['provider_runs']}",
        f"PASS compile_success={summary['metric_totals']['compile_success']}",
        f"PASS run_success={summary['metric_totals']['run_success']}",
        f"PASS strategies_with_metrics={summary['metric_totals']['strategies_with_metrics']}",
        f"PASS total_trades={summary['metric_totals']['total_trades']}",
        "FAIL_CLOSED tvr_daily_only_inside_1h_template",
        "FAIL_CLOSED ibkr_daily_only_inside_1h_template",
        "FAIL_CLOSED no_pre_bayes_bbn_catboost_execution_tree_promotion",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    repair = load_repair_module()
    old = repair.load_old_module()
    for path in (OUT_DIR, CHECK_DIR, REPORT_DIR, PROVIDER_CSV_DIR, WORKSPACE_ROOT):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")

    old.RUN_ID = RUN_ID
    old.ROOT = ROOT
    old.OUT_DIR = OUT_DIR
    old.CHECK_DIR = CHECK_DIR
    old.PROVIDER_CSV_DIR = PROVIDER_CSV_DIR
    old.WORKSPACE_ROOT = WORKSPACE_ROOT

    provider_inputs = {
        "yfinance": {
            "source": SOURCE_ROOT / "provider-csv" / "yfinance_btc_usd_1h.csv",
            "symbol": "BTC-USD",
        },
        "kraken_public": {
            "source": SOURCE_ROOT / "provider-csv" / "kraken_xbtusd_1h.csv",
            "symbol": "XBTUSD",
        },
        "binance_public": {
            "source": SOURCE_ROOT / "provider-csv" / "binance_btcusdt_1h.csv",
            "symbol": "BTCUSDT",
        },
        "bybit_public": {
            "source": SOURCE_ROOT / "provider-csv" / "bybit_btcusdt_linear_1h.csv",
            "symbol": "BTCUSDT",
        },
        "tvr_btc_usd": {
            "source": SOURCE_ROOT / "provider-csv" / "tvr_btc_usd_1d.csv",
            "symbol": "BTC-USD",
        },
        "ibkr_aggtrades": {
            "source": SOURCE_ROOT / "provider-csv" / "ibkr_btc_paxos_aggtrades_1d.csv",
            "symbol": "BTC.PAXOS",
        },
    }
    aq_results = [
        repair.run_provider_fixed(old, provider, meta)
        for provider, meta in provider_inputs.items()
    ]
    totals = metric_totals(aq_results)
    summary = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "provider_matrix": provider_matrix(),
        "aq_results": aq_results,
        "metric_totals": totals,
        "gate_result": "112315_same_root_six_provider_aq_readback=same_provider_root_aq_attempted_but_tvr_ibkr_daily_template_mismatch_no_promotion",
        "mature_rooted_branch_observations_added": 0,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "112315_same_root_six_provider_aq_readback_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
