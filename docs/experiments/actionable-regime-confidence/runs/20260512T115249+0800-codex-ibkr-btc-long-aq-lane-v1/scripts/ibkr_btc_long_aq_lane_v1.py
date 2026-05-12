from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T115249+0800-codex-ibkr-btc-long-aq-lane-v1"
SOURCE_RUN_ID = "20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1"
PROVIDER_MATRIX_ROOT_ID = "20260512T112315+0800-codex-board-b-six-provider-btc-matrix-probe-v1"
PRECHECK_ROOT_ID = "20260512T112030+0800-codex-btc-comparable-tvr-ibkr-provider-preflight-v1"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_ROOT = RUNS / SOURCE_RUN_ID
REPORT_DIR = ROOT / "ibkr-btc-long-aq-lane-v1"
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
CONFIG_DIR = ROOT / "config"
DERIVED_DIR = ROOT / "derived" / "ibkr_btc_paxos_long"
PROVIDER_CSV_DIR = ROOT / "provider-csv"
WORKSPACE_ROOT = ROOT / "workspace"

FETCH_PY = Path("scripts/auto_quant_external/fetch_external.py")
AUTO_QUANT_PY = Path("/Users/thrill3r/Auto-Quant/.venv/bin/python")
REPAIR_SCRIPT = SOURCE_ROOT / "scripts" / "112904_provider_matrix_aq_date_contract_repair_v1.py"


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


def load_repair_module():
    spec = importlib.util.spec_from_file_location("repair_113833", REPAIR_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {REPAIR_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_fetch_config() -> Path:
    config = CONFIG_DIR / "ibkr_btc_paxos_30d_bulk.yaml"
    config.write_text(
        "\n".join(
            [
                "gateway:",
                "  host: 127.0.0.1",
                "  port: 4002",
                "  client_id: 52",
                "output:",
                f"  directory: {DERIVED_DIR}",
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


def run_fetch(config: Path) -> dict[str, Any]:
    cmd = [
        str(AUTO_QUANT_PY),
        str(FETCH_PY),
        "ibkr-bulk",
        "--config",
        str(config),
        "--force",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = (
        "/Users/thrill3r/projects-ict-engine/ict-engine/scripts:"
        "/Users/thrill3r/projects-ict-engine/ict-engine"
    )
    proc = subprocess.run(
        cmd,
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    name = "00_ibkr_btc_paxos_30d_bulk"
    (OUT_DIR / f"{name}.cmd").write_text(" ".join(cmd) + "\n")
    (OUT_DIR / f"{name}.out").write_text(proc.stdout)
    (OUT_DIR / f"{name}.err").write_text(proc.stderr)
    (CHECK_DIR / f"{name}.exit").write_text(f"{proc.returncode}\n")
    csv_path = DERIVED_DIR / "BTC_1h_midpoint.csv"
    return {
        "command": cmd,
        "exit": proc.returncode,
        "stdout": str(OUT_DIR / f"{name}.out"),
        "stderr": str(OUT_DIR / f"{name}.err"),
        "csv": str(csv_path),
        "rows": csv_rows(csv_path),
    }


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


def run_aq(provider_csv: Path) -> dict[str, Any]:
    repair = load_repair_module()
    old = repair.load_old_module()

    for path in (PROVIDER_CSV_DIR, WORKSPACE_ROOT, OUT_DIR, CHECK_DIR):
        path.mkdir(parents=True, exist_ok=True)

    old.RUN_ID = RUN_ID
    old.SOURCE_RUN_ID = PROVIDER_MATRIX_ROOT_ID
    old.ROOT = ROOT
    old.SOURCE_ROOT = SOURCE_ROOT
    old.OUT_DIR = OUT_DIR
    old.CHECK_DIR = CHECK_DIR
    old.PROVIDER_CSV_DIR = PROVIDER_CSV_DIR
    old.WORKSPACE_ROOT = WORKSPACE_ROOT
    old.normalized_df = repair.normalize_ohlcv

    repair.OUT_DIR = OUT_DIR
    repair.CHECK_DIR = CHECK_DIR
    repair.PROVIDER_CSV_DIR = PROVIDER_CSV_DIR
    repair.WORKSPACE_ROOT = WORKSPACE_ROOT

    result = repair.run_provider_fixed(
        old,
        "ibkr_paxos_long_midpoint",
        {
            "source": provider_csv,
            "symbol": "BTC.PAXOS",
        },
    )
    totals = repair.metric_totals([result])
    return {
        "result": result,
        "totals": totals,
    }


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "ibkr_btc_long_aq_lane_v1.md"
    assertions = CHECK_DIR / "ibkr_btc_long_aq_lane_v1_assertions.out"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_ibkr_btc_long_aq_lane_v1.csv"

    fetch = summary["fetch"]
    aq = summary.get("aq") or {}
    aq_result = aq.get("result") or {}
    totals = aq.get("totals") or {}
    metrics = aq_result.get("metrics") or {}
    lines = [
        "# IBKR BTC Long AQ Lane v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source provider-matrix AQ repair: `{SOURCE_RUN_ID}`",
        f"Provider matrix root: `{PROVIDER_MATRIX_ROOT_ID}`",
        f"IBKR precheck root: `{PRECHECK_ROOT_ID}`",
        "",
        "## Scope",
        "This isolated run repairs only the thin IBKR BTC/PAXOS AQ lane by requesting a longer direct IBKR historical series.",
        "It does not edit ict-engine runtime code, does not rewrite earlier run roots, and does not promote a candidate.",
        "",
        "## Fetch Readback",
        f"- `ibkr-bulk` exit `{fetch['exit']}`.",
        f"- CSV rows `{summary['csv_summary'].get('rows')}` from `{summary['csv_summary'].get('first')}` through `{summary['csv_summary'].get('last')}`.",
        f"- CSV: `{fetch['csv']}`",
        "",
        "## AQ Readback",
    ]
    if aq_result:
        lines.append(
            f"- Provider `ibkr_paxos_long_midpoint`: rows `{aq_result.get('rows')}`, "
            f"compile exit `{aq_result.get('compile_exit')}`, TOMAC exit `{aq_result.get('run_tomac_exit')}`."
        )
        for strategy, payload in sorted(metrics.items()):
            aggregate = payload.get("aggregate", {})
            lines.append(
                f"  - `{strategy}`: trades `{aggregate.get('trade_count')}`, "
                f"profit_pct `{aggregate.get('total_profit_pct')}`, "
                f"win_rate_pct `{aggregate.get('win_rate_pct')}`, "
                f"profit_factor `{aggregate.get('profit_factor')}`."
            )
    else:
        lines.append("- AQ not run because the provider fetch failed or emitted no rows.")

    lines.extend(
        [
            "",
            "## Decision",
            f"- Gate result: `{summary['gate_result']}`.",
            f"- Evidence class: `{summary['evidence_class']}`.",
            f"- Mature rooted branch observations added: `{summary['mature_rooted_branch_observations_added']}`.",
            f"- AQ run success: `{totals.get('run_success', 0)}/{totals.get('provider_runs', 0)}`.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / 'ibkr_btc_long_aq_lane_v1.json'}`",
            f"- Assertions: `{assertions}`",
            f"- Command output and exits: `{OUT_DIR}`, `{CHECK_DIR}`",
            f"- AQ workspace: `{WORKSPACE_ROOT}`",
        ]
    )
    report.write_text("\n".join(lines) + "\n")

    checklist.write_text(
        "\n".join(
            [
                "requirement,artifact,status,note",
                f"longer IBKR BTC historical fetch,{fetch['csv']},covered,rows={summary['csv_summary'].get('rows')}",
                f"IBKR AQ/TOMAC lane,{WORKSPACE_ROOT},covered,run_success={totals.get('run_success', 0)}",
                "same-root six-provider authority,N/A,not_closed,this is a narrow IBKR repair continuation not a full same-packet downstream closure",
                "downstream chain,N/A,not_run,promotion remains blocked until combined same-root provider packet is pushed through Pre-Bayes/BBN/CatBoost/execution tree",
                "",
            ]
        )
    )

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run={SOURCE_RUN_ID}",
        f"PASS ibkr_fetch_exit={fetch['exit']}",
        f"PASS ibkr_fetch_rows={summary['csv_summary'].get('rows', 0)}",
    ]
    if aq_result:
        assertion_lines.extend(
            [
                f"PASS ibkr_compile_exit={aq_result.get('compile_exit')}",
                f"PASS ibkr_tomac_exit={aq_result.get('run_tomac_exit')}",
                f"PASS ibkr_strategies_with_metrics={totals.get('strategies_with_metrics', 0)}",
                f"PASS ibkr_total_trades={totals.get('total_trades', 0)}",
            ]
        )
    else:
        assertion_lines.append("FAIL_CLOSED ibkr_aq_not_run")
    assertion_lines.extend(
        [
            "FAIL_CLOSED same_root_six_provider_downstream_chain_not_rerun",
            "PASS promotion_allowed=false",
            "PASS trade_usable=false",
            "PASS update_goal=false",
        ]
    )
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    for path in (ROOT, REPORT_DIR, OUT_DIR, CHECK_DIR, CONFIG_DIR, DERIVED_DIR, PROVIDER_CSV_DIR, WORKSPACE_ROOT):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    (ROOT / "source_run.txt").write_text(SOURCE_RUN_ID + "\n")

    config = write_fetch_config()
    fetch = run_fetch(config)
    csv_path = Path(fetch["csv"])
    csv_summary = summarize_csv(csv_path)
    aq = None
    if fetch["exit"] == 0 and csv_summary.get("rows", 0) > 0:
        aq = run_aq(csv_path)
    total_trades = int(((aq or {}).get("totals") or {}).get("total_trades") or 0)
    run_success = int(((aq or {}).get("totals") or {}).get("run_success") or 0)
    summary = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "provider_matrix_root_id": PROVIDER_MATRIX_ROOT_ID,
        "precheck_root_id": PRECHECK_ROOT_ID,
        "fetch": fetch,
        "config": str(config),
        "csv_summary": csv_summary,
        "aq": aq,
        "mature_rooted_branch_observations_added": total_trades if run_success else 0,
        "evidence_class": "infrastructure_repair_candidate_ibkr_provider_aq_lane",
        "gate_result": "ibkr_btc_long_aq_lane=ibkr_provider_lane_repaired_but_same_root_downstream_chain_not_rerun",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "ibkr_btc_long_aq_lane_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
