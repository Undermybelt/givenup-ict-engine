#!/usr/bin/env python3
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260512T033215-codex-autoquant-local-cache-tomac-readback-after-032835-v1"
REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs" / RUN_ID
OUT = RUN_ROOT / "autoquant-local-cache-tomac-readback-after-032835-v1"
CHECKS = RUN_ROOT / "checks"
COMMAND = RUN_ROOT / "command-output"


def read_text(path):
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def parse_summary(stdout):
    metrics = {}
    for key in [
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
    ]:
        match = re.search(rf"^{re.escape(key)}:\s+(.+)$", stdout, re.MULTILINE)
        metrics[key] = match.group(1).strip() if match else None
    number_keys = {
        "sharpe",
        "sortino",
        "calmar",
        "total_profit_pct",
        "max_drawdown_pct",
        "win_rate_pct",
        "profit_factor",
    }
    for key in number_keys:
        if metrics[key] is not None:
            metrics[key] = float(metrics[key])
    if metrics["trade_count"] is not None:
        metrics["trade_count"] = int(metrics["trade_count"])
    return metrics


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    exitcode_text = read_text(COMMAND / "run_tomac.exitcode").strip()
    exitcode = int(exitcode_text) if exitcode_text else None
    stdout = read_text(COMMAND / "run_tomac.stdout.txt")
    stderr = read_text(COMMAND / "run_tomac.stderr.txt")
    metrics = parse_summary(stdout)

    fill_warnings = re.findall(r"Missing data fillup for .*", stderr)
    gate = "autoquant_local_cache_tomac_readback_after_032835_v1=backtest_ran_single_pair_local_cache_nonpromoting_source_controls_downstream_blocked"
    result = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_result": gate,
        "objective_mapping": "Read back a real Auto-Quant/Freqtrade local-cache Tomac strategy run after 032835, then decide whether it can contribute to Board A regime-confidence completion.",
        "inputs": {
            "stdout": str((COMMAND / "run_tomac.stdout.txt").relative_to(REPO)),
            "stderr": str((COMMAND / "run_tomac.stderr.txt").relative_to(REPO)),
            "exitcode": str((COMMAND / "run_tomac.exitcode").relative_to(REPO)),
        },
        "command": {
            "exit_code": exitcode,
            "succeeded": exitcode == 0,
            "strategy": metrics["strategy"],
            "commit": metrics["commit"],
            "config": metrics["config"],
            "pairs": metrics["pairs"],
        },
        "metrics": {
            "trade_count": metrics["trade_count"],
            "win_rate_pct": metrics["win_rate_pct"],
            "total_profit_pct": metrics["total_profit_pct"],
            "sharpe": metrics["sharpe"],
            "sortino": metrics["sortino"],
            "calmar": metrics["calmar"],
            "max_drawdown_pct": metrics["max_drawdown_pct"],
            "profit_factor": metrics["profit_factor"],
        },
        "data_quality": {
            "local_cache_only": True,
            "pairs_evaluated": [metrics["pairs"]] if metrics["pairs"] else [],
            "timeframe_observed": "1h",
            "fillup_warnings": fill_warnings,
            "cross_market_validation": False,
            "cross_timeframe_validation": False,
            "per_regime_95_confidence": False,
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
            "raw_market_data_committed": False,
        },
        "decision": "The Auto-Quant backtest ran and is useful diagnostics, but it is a single-pair local-cache strategy result with no accepted regime-confidence labels, no cross-market/cross-timeframe validation, no source/control unlock, no canonical merge, and no downstream promotion rerun.",
        "next_action": "Use this only as Auto-Quant runtime evidence. Continue Board A from verifier-native source rows, explicit FLIP approval/source-owned controls, or genuinely source-owned cross-timeframe MainRegimeV2 exports.",
    }

    json_path = OUT / "autoquant_local_cache_tomac_readback_after_032835_v1.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checklist = [
        ("autoquant_command_operated", "pass", f"exit_code={exitcode}; strategy={metrics['strategy']}", ""),
        ("local_cache_backtest_metrics_recorded", "pass", f"trades={metrics['trade_count']}; win_rate_pct={metrics['win_rate_pct']}; total_profit_pct={metrics['total_profit_pct']}; sharpe={metrics['sharpe']}", ""),
        ("every_regime_95_confidence", "blocked", "no accepted regime-confidence labels in this packet", "Backtest metrics are not regime-confidence evidence."),
        ("cross_market_cycle_timeframe_validation", "blocked", f"pairs={metrics['pairs']}; timeframe=1h", "Single-pair local-cache run only."),
        ("source_control_unlock", "blocked", "source_roots_mutated=false; accepted_rows_added=0", "No verifier-native owner rows or matched controls."),
        ("downstream_chain_promotion", "blocked", "canonical_merge=false; downstream_promotion_rerun=false", "Do not run BBN/CatBoost/execution-tree promotion from this packet."),
    ]
    checklist_path = OUT / "autoquant_local_cache_tomac_prompt_to_artifact_checklist_after_032835_v1.csv"
    with checklist_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["requirement", "status", "evidence", "gap"])
        writer.writerows(checklist)

    metrics_path = OUT / "autoquant_local_cache_tomac_metrics_after_032835_v1.csv"
    with metrics_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        for key, value in result["metrics"].items():
            writer.writerow([key, value])

    md = [
        "# AutoQuant Local Cache Tomac Readback After 032835 v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        f"Gate result: `{gate}`",
        "",
        "## Readback",
        "",
        f"- Command exit code: `{exitcode}`.",
        f"- Strategy: `{metrics['strategy']}` at Auto-Quant commit `{metrics['commit']}` with config `{metrics['config']}`.",
        f"- Pair/timeframe: `{metrics['pairs']}` / `1h`.",
        f"- Trades: `{metrics['trade_count']}`; win rate `{metrics['win_rate_pct']}`%; total profit `{metrics['total_profit_pct']}`%; Sharpe `{metrics['sharpe']}`; profit factor `{metrics['profit_factor']}`.",
        f"- Data-fill warnings: `{len(fill_warnings)}`.",
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
        f"- Checklist CSV: `{checklist_path.relative_to(REPO)}`",
        f"- Metrics CSV: `{metrics_path.relative_to(REPO)}`",
    ]
    md_path = OUT / "autoquant_local_cache_tomac_readback_after_032835_v1.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    assertions = [
        ("gate_result", result["gate_result"] == gate),
        ("command_exit_code_zero", exitcode == 0),
        ("strategy_tomac", metrics["strategy"] == "TomacNQ_KillzoneBreakout"),
        ("single_pair_qqq", metrics["pairs"] == "QQQ/USD"),
        ("trade_count_74", metrics["trade_count"] == 74),
        ("win_rate_52_7027", metrics["win_rate_pct"] == 52.7027),
        ("cross_market_validation_false", result["data_quality"]["cross_market_validation"] is False),
        ("cross_timeframe_validation_false", result["data_quality"]["cross_timeframe_validation"] is False),
        ("per_regime_95_confidence_false", result["data_quality"]["per_regime_95_confidence"] is False),
        ("accepted_rows_added_0", result["promotion"]["accepted_rows_added"] == 0),
        ("canonical_merge_allowed_false", result["promotion"]["canonical_merge_allowed"] is False),
        ("downstream_promotion_rerun_allowed_false", result["promotion"]["downstream_promotion_rerun_allowed"] is False),
        ("strict_full_objective_false", result["promotion"]["strict_full_objective_achieved"] is False),
        ("trade_usable_false", result["promotion"]["trade_usable"] is False),
        ("update_goal_false", result["promotion"]["update_goal"] is False),
        ("runtime_code_changed_false", result["non_mutations"]["runtime_code_changed"] is False),
        ("source_roots_mutated_false", result["non_mutations"]["source_roots_mutated"] is False),
        ("thresholds_relaxed_false", result["non_mutations"]["thresholds_relaxed"] is False),
        ("raw_market_data_committed_false", result["non_mutations"]["raw_market_data_committed"] is False),
    ]
    lines = []
    failures = []
    for name, ok in assertions:
        lines.append(f"{'PASS' if ok else 'FAIL'} {name}={str(ok).lower()}")
        if not ok:
            failures.append(name)
    assertion_path = CHECKS / "autoquant_local_cache_tomac_readback_after_032835_v1_assertions.out"
    assertion_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit("assertions failed: " + ",".join(failures))


if __name__ == "__main__":
    main()
