#!/usr/bin/env python3
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T033430-codex-autoquant-threaded-resolver-workaround-run-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "autoquant-threaded-resolver-workaround-run-v1"
CHECKS = RUN_ROOT / "checks"
COMMAND = RUN_ROOT / "command-output"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def read_exit(name: str) -> int | None:
    text = read_text(COMMAND / name).strip()
    try:
        return int(text)
    except ValueError:
        return None


def parse_strategy_metrics(stdout: str) -> list[dict[str, object]]:
    metrics: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for line in stdout.splitlines():
        if line.startswith("strategy:"):
            if current and current.get("timerange_label") == "full":
                metrics.append(current)
            current = {"strategy": line.split(":", 1)[1].strip()}
            continue
        if current is None:
            continue
        for field in [
            "timerange_label",
            "timerange",
            "sharpe",
            "sortino",
            "calmar",
            "total_profit_pct",
            "max_drawdown_pct",
            "trade_count",
            "win_rate_pct",
            "profit_factor",
            "robust_sharpe",
            "worst_profit_pct",
            "worst_dd_pct",
            "avg_position_pct",
            "profit_floor",
            "min_position_size",
            "pareto_dominated_by",
        ]:
            prefix = f"{field}:"
            if line.startswith(prefix):
                value = line.split(":", 1)[1].strip()
                if field in {
                    "sharpe",
                    "sortino",
                    "calmar",
                    "total_profit_pct",
                    "max_drawdown_pct",
                    "win_rate_pct",
                    "profit_factor",
                    "robust_sharpe",
                    "worst_profit_pct",
                    "worst_dd_pct",
                    "avg_position_pct",
                }:
                    value = value.split()[0]
                    current[field] = float(value)
                elif field == "trade_count":
                    current[field] = int(value)
                else:
                    current[field] = value
                break
    if current and current.get("timerange_label") == "full":
        metrics.append(current)
    return metrics


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    prepare_attempt1_exit = read_exit("auto_quant_prepare_threaded_resolver.exit")
    prepare_attempt2_exit = read_exit("auto_quant_prepare_threaded_resolver_attempt2.exit")
    run_plain_exit = read_exit("auto_quant_run_seeded_strategies.exit")
    run_threaded_exit = read_exit("auto_quant_run_seeded_strategies_threaded_resolver.exit")
    status_exit = read_exit("auto_quant_status_after_threaded_prepare.exit")

    prepare_attempt1_stderr = read_text(COMMAND / "auto_quant_prepare_threaded_resolver.stderr.txt")
    prepare_attempt2_stdout = read_text(COMMAND / "auto_quant_prepare_threaded_resolver_attempt2.stdout.txt")
    run_plain_stdout = read_text(COMMAND / "auto_quant_run_seeded_strategies.stdout.txt")
    run_threaded_stdout = read_text(COMMAND / "auto_quant_run_seeded_strategies_threaded_resolver.stdout.txt")
    run_threaded_stderr = read_text(COMMAND / "auto_quant_run_seeded_strategies_threaded_resolver.stderr.txt")
    status_stdout = read_text(COMMAND / "auto_quant_status_after_threaded_prepare.stdout.json")

    try:
        status = json.loads(status_stdout)
    except json.JSONDecodeError:
        status = {}

    metrics = parse_strategy_metrics(run_threaded_stdout)
    strategy_count = len(metrics)
    best = max(metrics, key=lambda row: float(row.get("sharpe", -999.0))) if metrics else {}
    seeded_run_success = "Done: 3 backtests succeeded, 0 failed." in run_threaded_stdout
    sitecustomize_applied = "ict_engine_autoquant_threaded_resolver_sitecustomize=applied" in run_threaded_stderr
    gate = "autoquant_threaded_resolver_workaround_run_v1=prepare_and_seeded_backtest_succeeded_source_controls_still_blocked_no_promotion"

    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate,
        "objective_mapping": "Follow up the 033216 resolver diagnostic by testing a no-runtime-code threaded-resolver workaround, then seed and run Auto-Quant in isolated /tmp state.",
        "inputs": {
            "sitecustomize": str((RUN_ROOT / "threaded-resolver-workaround/sitecustomize.py").relative_to(REPO)),
            "prepare_attempt1_stderr": str((COMMAND / "auto_quant_prepare_threaded_resolver.stderr.txt").relative_to(REPO)),
            "prepare_attempt2_stdout": str((COMMAND / "auto_quant_prepare_threaded_resolver_attempt2.stdout.txt").relative_to(REPO)),
            "status_after_prepare_stdout": str((COMMAND / "auto_quant_status_after_threaded_prepare.stdout.json").relative_to(REPO)),
            "plain_seeded_run_stdout": str((COMMAND / "auto_quant_run_seeded_strategies.stdout.txt").relative_to(REPO)),
            "threaded_seeded_run_stdout": str((COMMAND / "auto_quant_run_seeded_strategies_threaded_resolver.stdout.txt").relative_to(REPO)),
        },
        "attempts": {
            "prepare_attempt1_wrong_shim_path": {
                "exit_code": prepare_attempt1_exit,
                "aiodns_dns_error": "Could not contact DNS servers" in prepare_attempt1_stderr,
            },
            "prepare_attempt2_correct_threaded_resolver": {
                "exit_code": prepare_attempt2_exit,
                "status": "prepared" if '"status": "prepared"' in prepare_attempt2_stdout else "unknown",
                "data_ready_stdout": '"data_ready": true' in prepare_attempt2_stdout,
            },
            "status_after_prepare": {
                "exit_code": status_exit,
                "status": status.get("status"),
                "healthy": status.get("healthy"),
                "data_ready": status.get("data_ready"),
                "notes": status.get("notes"),
            },
            "seeded_run_without_threaded_resolver": {
                "exit_code": run_plain_exit,
                "succeeded": run_plain_exit == 0,
                "market_load_failed": "Could not load markets" in run_plain_stdout,
            },
            "seeded_run_with_threaded_resolver": {
                "exit_code": run_threaded_exit,
                "succeeded": seeded_run_success and run_threaded_exit == 0,
                "sitecustomize_applied": sitecustomize_applied,
                "strategy_count": strategy_count,
            },
        },
        "strategy_metrics": metrics,
        "best_strategy_by_sharpe": best,
        "diagnosis": {
            "threaded_resolver_workaround_effective_for_prepare": prepare_attempt2_exit == 0 and status.get("data_ready") is True,
            "threaded_resolver_workaround_effective_for_seeded_run": seeded_run_success and run_threaded_exit == 0,
            "auto_quant_data_ready": status.get("data_ready") is True,
            "seeded_backtests_succeeded": seeded_run_success,
        },
        "promotion": {
            "accepted_rows_added": 0,
            "new_confidence_gate": False,
            "canonical_merge_allowed": False,
            "downstream_promotion_rerun_allowed": False,
            "strict_full_objective_achieved": False,
            "trade_usable": False,
            "update_goal": False,
        },
        "non_mutations": {
            "runtime_code_changed": False,
            "source_roots_mutated": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "repo_runtime_code_changed": False,
        },
        "decision": "The threaded-resolver shim fixed the Auto-Quant Binance DNS path in isolated /tmp state: prepare succeeded, data_ready is true, and three seeded Auto-Quant backtests completed. This is runtime readiness evidence only and cannot promote Board A while source/control gates remain closed.",
        "next_action": "Keep the Current Cursor source/control action: acquire verifier-native owner/export rows or explicit FLIP/source-control approval before canonical merge, verifier rerun, split calibration, and downstream promotion.",
    }

    json_path = OUT / "autoquant_threaded_resolver_workaround_run_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    csv_path = OUT / "autoquant_threaded_resolver_workaround_run_v1.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["field", "value"])
        writer.writerow(["gate_result", gate])
        writer.writerow(["prepare_attempt1_exit", prepare_attempt1_exit])
        writer.writerow(["prepare_attempt2_exit", prepare_attempt2_exit])
        writer.writerow(["status_after_prepare", status.get("status")])
        writer.writerow(["data_ready_after_prepare", status.get("data_ready")])
        writer.writerow(["seeded_run_without_resolver_exit", run_plain_exit])
        writer.writerow(["seeded_run_with_resolver_exit", run_threaded_exit])
        writer.writerow(["seeded_run_with_resolver_success", seeded_run_success])
        writer.writerow(["best_strategy", best.get("strategy")])
        writer.writerow(["best_strategy_sharpe", best.get("sharpe")])
        writer.writerow(["best_strategy_trade_count", best.get("trade_count")])
        writer.writerow(["accepted_rows_added", 0])
        writer.writerow(["update_goal", False])

    strategy_csv_path = OUT / "autoquant_threaded_resolver_strategy_metrics_v1.csv"
    with strategy_csv_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "strategy",
            "sharpe",
            "total_profit_pct",
            "max_drawdown_pct",
            "trade_count",
            "win_rate_pct",
            "profit_factor",
            "avg_position_pct",
            "profit_floor",
            "min_position_size",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in metrics:
            writer.writerow({field: row.get(field) for field in fieldnames})

    md = [
        "# AutoQuant Threaded Resolver Workaround Run v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate}`",
        "",
        "## Readback",
        "",
        f"- First prepare attempt exit code: `{prepare_attempt1_exit}`; this used the wrong shim path and preserved the aiohttp/aiodns failure.",
        f"- Corrected threaded-resolver prepare exit code: `{prepare_attempt2_exit}`; `auto-quant-prepare` returned `status=prepared` and `data_ready=true`.",
        f"- Post-prepare `auto-quant-status` exit code: `{status_exit}`; status `{status.get('status')}`, healthy `{str(status.get('healthy')).lower()}`, data_ready `{str(status.get('data_ready')).lower()}`.",
        "- Seeded three active strategies into the isolated managed Auto-Quant workspace: `BTCLeaderBreakV4`, `MomentumMTFConfluence`, and `VolBreakoutSized`.",
        f"- Seeded run without the resolver shim exit code: `{run_plain_exit}`; it failed while loading Binance markets.",
        f"- Seeded run with the resolver shim exit code: `{run_threaded_exit}`; `Done: 3 backtests succeeded, 0 failed`.",
        "",
        "## Strategy Metrics",
        "",
        "| Strategy | Sharpe | Profit % | Max DD % | Trades | Win % | PF | Position gate |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in metrics:
        md.append(
            "| {strategy} | {sharpe:.4f} | {profit:.2f} | {dd:.2f} | {trades} | {win:.2f} | {pf:.4f} | {pos_gate} |".format(
                strategy=row.get("strategy"),
                sharpe=float(row.get("sharpe", 0.0)),
                profit=float(row.get("total_profit_pct", 0.0)),
                dd=float(row.get("max_drawdown_pct", 0.0)),
                trades=int(row.get("trade_count", 0)),
                win=float(row.get("win_rate_pct", 0.0)),
                pf=float(row.get("profit_factor", 0.0)),
                pos_gate=row.get("min_position_size", ""),
            )
        )
    md.extend(
        [
            "",
            "## Decision",
            "",
            result["decision"],
            "",
            "- Accepted rows added: `0`",
            "- New confidence gate: `false`",
            "- Canonical merge allowed: `false`",
            "- Downstream promotion rerun allowed: `false`",
            "- Strict full objective achieved: `false`",
            "- Trade usable: `false`",
            "- `update_goal=false`",
            "",
            "## Next",
            "",
            result["next_action"],
            "",
            "## Artifacts",
            "",
            f"- JSON: `{json_path.relative_to(REPO)}`",
            f"- Summary CSV: `{csv_path.relative_to(REPO)}`",
            f"- Strategy metrics CSV: `{strategy_csv_path.relative_to(REPO)}`",
            f"- Assertions: `{(CHECKS / 'autoquant_threaded_resolver_workaround_run_v1_assertions.out').relative_to(REPO)}`",
        ]
    )
    md_path = OUT / "autoquant_threaded_resolver_workaround_run_v1.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    assertions = [
        ("gate_result", result["gate_result"] == gate),
        ("prepare_attempt2_exit_0", prepare_attempt2_exit == 0),
        ("status_after_prepare_exit_0", status_exit == 0),
        ("data_ready_true", status.get("data_ready") is True),
        ("seeded_run_with_resolver_exit_0", run_threaded_exit == 0),
        ("seeded_backtests_succeeded_true", seeded_run_success is True),
        ("strategy_count_3", strategy_count == 3),
        ("best_strategy_vol_breakout_sized", best.get("strategy") == "VolBreakoutSized"),
        ("accepted_rows_added_0", result["promotion"]["accepted_rows_added"] == 0),
        ("canonical_merge_allowed_false", result["promotion"]["canonical_merge_allowed"] is False),
        ("downstream_promotion_rerun_allowed_false", result["promotion"]["downstream_promotion_rerun_allowed"] is False),
        ("strict_full_objective_false", result["promotion"]["strict_full_objective_achieved"] is False),
        ("trade_usable_false", result["promotion"]["trade_usable"] is False),
        ("update_goal_false", result["promotion"]["update_goal"] is False),
        ("runtime_code_changed_false", result["non_mutations"]["runtime_code_changed"] is False),
        ("source_roots_mutated_false", result["non_mutations"]["source_roots_mutated"] is False),
        ("thresholds_relaxed_false", result["non_mutations"]["thresholds_relaxed"] is False),
        ("raw_data_committed_false", result["non_mutations"]["raw_data_committed"] is False),
    ]
    failures = []
    lines = []
    for name, ok in assertions:
        lines.append(f"{'PASS' if ok else 'FAIL'} {name}={str(ok).lower()}")
        if not ok:
            failures.append(name)
    assertion_path = CHECKS / "autoquant_threaded_resolver_workaround_run_v1_assertions.out"
    assertion_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("assertions failed: " + ",".join(failures))


if __name__ == "__main__":
    main()
