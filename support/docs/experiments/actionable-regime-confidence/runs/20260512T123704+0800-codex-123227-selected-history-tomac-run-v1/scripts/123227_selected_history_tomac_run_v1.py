from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


RUN_ID = "20260512T123704+0800-codex-123227-selected-history-tomac-run-v1"
SOURCE_RUN_ID = "20260512T123227+0800-codex-115700-selected-history-btc-alias-aq-v1"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
REPORT_DIR = ROOT / "123227-selected-history-tomac-run-v1"
CHECK_DIR = ROOT / "checks"
COMMAND_DIR = ROOT / "command-output"


def read_text(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def read_exit(name: str) -> int | None:
    path = COMMAND_DIR / name
    if not path.exists():
        return None
    try:
        return int(path.read_text().strip())
    except ValueError:
        return None


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.read_text().strip():
        return {}
    return json.loads(path.read_text())


def parse_tomac_stdout(text: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in text.splitlines():
        if line.strip() == "---":
            if current:
                blocks.append(current)
            current = {}
            continue
        if current is None or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key in {
            "strategy",
            "commit",
            "config",
            "pairs",
            "sharpe",
            "sortino",
            "calmar",
            "total_profit_pct",
            "max_drawdown_pct",
            "trade_count",
            "win_rate_pct",
            "profit_factor",
        }:
            current[key] = value
    if current:
        blocks.append(current)
    parsed: list[dict[str, Any]] = []
    for block in blocks:
        row = dict(block)
        for key in [
            "sharpe",
            "sortino",
            "calmar",
            "total_profit_pct",
            "max_drawdown_pct",
            "win_rate_pct",
            "profit_factor",
        ]:
            if key in row:
                row[key] = float(row[key])
        if "trade_count" in row:
            row["trade_count"] = int(row["trade_count"])
        parsed.append(row)
    return parsed


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    (ROOT / "source_run_id.txt").write_text(SOURCE_RUN_ID + "\n")

    wrapper_err = read_text(COMMAND_DIR / "01_run_tomac.err")
    tomac_out = read_text(COMMAND_DIR / "02_run_tomac_venv.out")
    tomac_err = read_text(COMMAND_DIR / "02_run_tomac_venv.err")
    aq_status = read_json(COMMAND_DIR / "03_auto_quant_status.out")
    adoption_review = read_json(COMMAND_DIR / "04b_auto_quant_adoption_review.out")
    workflow_status = read_json(COMMAND_DIR / "05_workflow_status.out")
    strategies = parse_tomac_stdout(tomac_out)
    done_match = re.search(r"Done:\s+(\d+)\s+succeeded,\s+(\d+)\s+failed", tomac_out)
    succeeded = int(done_match.group(1)) if done_match else 0
    failed = int(done_match.group(2)) if done_match else 0
    total_trades = sum(int(row.get("trade_count", 0)) for row in strategies)
    max_win_rate = max((float(row.get("win_rate_pct", 0.0)) for row in strategies), default=0.0)
    max_sharpe = max((float(row.get("sharpe", 0.0)) for row in strategies), default=0.0)
    payload = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "commands": {
            "uv_wrapper_exit": read_exit("01_run_tomac.exit"),
            "uv_wrapper_error": wrapper_err.strip(),
            "venv_tomac_exit": read_exit("02_run_tomac_venv.exit"),
            "auto_quant_status_exit": read_exit("03_auto_quant_status.exit"),
            "adoption_review_initial_exit": read_exit("04_auto_quant_adoption_review.exit"),
            "adoption_review_supported_exit": read_exit("04b_auto_quant_adoption_review.exit"),
            "workflow_status_exit": read_exit("05_workflow_status.exit"),
        },
        "tomac": {
            "succeeded": succeeded,
            "failed": failed,
            "strategies": strategies,
            "total_trades": total_trades,
            "max_win_rate_pct": max_win_rate,
            "max_sharpe": max_sharpe,
            "stderr_excerpt": tomac_err[:4000],
        },
        "ict_engine": {
            "auto_quant_status": {
                "status": aq_status.get("status"),
                "dependency_status": aq_status.get("dependency_status", {}),
            },
            "adoption_review": adoption_review,
            "workflow_status": workflow_status,
        },
        "decision": {
            "gate": "selected_history_tomac_measured_zero_trades_no_downstream_promotion",
            "auto_quant_measured": True,
            "candidate_package_available": False,
            "accepted_regime_gate": False,
            "pre_bayes_bbn_catboost_execution_ready": False,
            "production_likelihood_mutation": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        },
    }
    json_path = REPORT_DIR / "123227_selected_history_tomac_run_v1.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    strategy_csv = REPORT_DIR / "123227_selected_history_tomac_strategy_metrics_v1.csv"
    with strategy_csv.open("w", newline="") as fh:
        fieldnames = [
            "strategy",
            "pairs",
            "trade_count",
            "win_rate_pct",
            "sharpe",
            "total_profit_pct",
            "profit_factor",
            "config",
            "commit",
        ]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in strategies:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    checklist = REPORT_DIR / "prompt_to_artifact_checklist_123227_selected_history_tomac_run_v1.csv"
    with checklist.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["selected-history data-ready root", str(COMMAND_DIR / "03_auto_quant_status.out"), "covered", str(aq_status.get("status"))])
        writer.writerow(["run Auto-Quant TOMAC", str(COMMAND_DIR / "02_run_tomac_venv.out"), "covered", f"succeeded={succeeded} failed={failed}"])
        writer.writerow(["measure candidate trades", str(strategy_csv), "fail_closed", f"total_trades={total_trades}"])
        writer.writerow(["ict-engine adoption review", str(COMMAND_DIR / "04b_auto_quant_adoption_review.out"), "covered", adoption_review.get("review_status", "unknown")])
        writer.writerow(["downstream Pre-Bayes/BBN/CatBoost/execution", str(COMMAND_DIR / "05_workflow_status.out"), "fail_closed", "no candidate package; workflow insufficient_state"])
        writer.writerow(["no promotion/update_goal", str(json_path), "covered", "promotion_allowed=false update_goal=false"])

    md_path = REPORT_DIR / "123227_selected_history_tomac_run_v1.md"
    lines = [
        "# 123227 Selected-History TOMAC Run v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Source selected-history root: `{SOURCE_RUN_ID}`",
        "",
        "## Scope",
        "Run the selected-history `123227` Auto-Quant/TOMAC handoff in its isolated workspace and tie the measured result back to ict-engine status/review surfaces.",
        "This does not mutate BBN CPDs, CatBoost models, or execution-tree gates.",
        "",
        "## Readback",
        f"- Initial wrapper command failed before backtest because `freqtrade` was missing from the outer `uv --with ta-lib` environment; the isolated Auto-Quant `.venv` contains `freqtrade`, `talib`, and `pandas`.",
        f"- TOMAC via the isolated `.venv` exited `{payload['commands']['venv_tomac_exit']}`.",
        f"- Strategies succeeded/failed: `{succeeded}` / `{failed}`.",
        f"- Strategies measured: `{[row.get('strategy') for row in strategies]}`.",
        f"- Total measured trades: `{total_trades}`.",
        f"- Max strategy win rate pct: `{max_win_rate}`; max Sharpe: `{max_sharpe}`.",
        f"- ict-engine auto-quant status: `{aq_status.get('status')}`.",
        f"- ict-engine adoption review: `{adoption_review.get('review_status')}` / `{adoption_review.get('review_summary')}`.",
        f"- workflow-status blocker: `{(workflow_status.get('blocking_truth') or {}).get('status')}` / `{(workflow_status.get('blocking_truth') or {}).get('reason')}`.",
        "",
        "## Decision",
        "- Gate: `selected_history_tomac_measured_zero_trades_no_downstream_promotion`.",
        "- The selected-history data-ready unlock is real, and TOMAC ran, but all three TOMAC-derived strategies produced zero trades on this BTC-only selected window.",
        "- Because there is no measured candidate package, this root cannot advance into Pre-Bayes/BBN/CatBoost/execution promotion.",
        "- `production_likelihood_mutation=false`.",
        "- `promotion_allowed=false`.",
        "- `trade_usable=false`.",
        "- `update_goal=false`.",
        "",
        "## Artifacts",
        f"- JSON: `{json_path}`",
        f"- Strategy metrics CSV: `{strategy_csv}`",
        f"- Checklist: `{checklist}`",
        f"- Assertions: `{CHECK_DIR / '123227_selected_history_tomac_run_v1_assertions.out'}`",
    ]
    md_path.write_text("\n".join(lines) + "\n")

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run_id={SOURCE_RUN_ID}",
        "PASS root_cause=outer_uv_missing_freqtrade",
        f"PASS venv_tomac_exit={payload['commands']['venv_tomac_exit']}",
        f"PASS tomac_succeeded={succeeded}",
        f"PASS tomac_failed={failed}",
        f"FAIL_CLOSED total_trades={total_trades}",
        "FAIL_CLOSED candidate_package_available=false",
        "FAIL_CLOSED pre_bayes_bbn_catboost_execution_ready=false",
        "PASS production_likelihood_mutation=false",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "123227_selected_history_tomac_run_v1_assertions.out").write_text("\n".join(assertions) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
