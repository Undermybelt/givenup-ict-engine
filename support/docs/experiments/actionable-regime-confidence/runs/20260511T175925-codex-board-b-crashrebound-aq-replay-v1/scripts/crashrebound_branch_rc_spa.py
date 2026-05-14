#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import csv
import importlib.util
import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
OPTIONAL_OVERLAY = "Manipulation"

FOLD_BRANCH_MAP = {
    "bull_2021": {
        "parent_regime_root": "Bull",
        "sub_regime_tags": "TrendExpansion; drawdown_pullback",
        "sub_sub_regime_or_profit_factor": "MomentumPersistenceDrawdownRebound",
        "profit_factor_family": "counter_trend_drawdown_rebound",
        "profit_factor_leaf": "CrashRebound",
        "allowed_action": "research_only_long_rebound",
        "suppression_rule": "suppress_if_board_a_root_not_bull_or_branch_path_missing",
        "branch_path_valid": True,
        "independent_test_fold": True,
    },
    "winter_2022": {
        "parent_regime_root": "Bear",
        "sub_regime_tags": "BearMarketDrawdown; capitulation_rebound",
        "sub_sub_regime_or_profit_factor": "MeanReversionAfterCapitulation",
        "profit_factor_family": "counter_trend_drawdown_rebound",
        "profit_factor_leaf": "CrashRebound",
        "allowed_action": "research_only_long_rebound",
        "suppression_rule": "suppress_if_board_a_root_not_bear_or_branch_path_missing",
        "branch_path_valid": True,
        "independent_test_fold": True,
    },
    "recovery_23_25": {
        "parent_regime_root": "UnacceptedRecoveryContext",
        "sub_regime_tags": "Recovery; mixed_bull_sideways_unverified",
        "sub_sub_regime_or_profit_factor": "DrawdownReboundWithoutAcceptedRoot",
        "profit_factor_family": "counter_trend_drawdown_rebound",
        "profit_factor_leaf": "CrashRebound",
        "allowed_action": "research_only_no_downstream_consumption",
        "suppression_rule": "suppress_until_board_a_maps_recovery_window_to_Bull_Sideways_or_Crisis",
        "branch_path_valid": False,
        "independent_test_fold": True,
    },
    "full_5y": {
        "parent_regime_root": "OverlappingMixedRoot",
        "sub_regime_tags": "Bull; Bear; Sideways_or_Crisis_unresolved",
        "sub_sub_regime_or_profit_factor": "AggregateNotAtomicBranch",
        "profit_factor_family": "counter_trend_drawdown_rebound",
        "profit_factor_leaf": "CrashRebound",
        "allowed_action": "diagnostic_only",
        "suppression_rule": "do_not_count_as_independent_fold_or_branch_path",
        "branch_path_valid": False,
        "independent_test_fold": False,
    },
}


def _jsonish(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _load_strategy_runner(autoquant_root: Path) -> Any:
    spec = importlib.util.spec_from_file_location("aq_run", autoquant_root / "run.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Auto-Quant runner from {autoquant_root / 'run.py'}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(autoquant_root))
    spec.loader.exec_module(module)
    return module


def _load_root_confidence(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    out: dict[str, float] = {}
    for row in rows:
        key = row.get("regime") or row.get("regime_root") or row.get("root") or row.get("factor_id") or ""
        if not key:
            # Current Board A CSV uses the first unnamed field as the root.
            key = next(iter(row.values()), "")
        try:
            out[str(key)] = float(row.get("confidence_floor") or row.get("confidence") or row.get("accepted_confidence") or row.get("score") or 0.0)
        except (TypeError, ValueError):
            out[str(key)] = 0.0
    return out


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _bootstrap_lcb(values: list[float], *, seed: int = 17, samples: int = 2000) -> float:
    if not values:
        return 0.0
    # Small deterministic LCG avoids adding numpy as a script dependency.
    state = seed & 0x7FFFFFFF
    means: list[float] = []
    n = len(values)
    for _ in range(samples):
        total = 0.0
        for _ in range(n):
            state = (1103515245 * state + 12345) & 0x7FFFFFFF
            total += values[state % n]
        means.append(total / n)
    means.sort()
    return means[int(0.05 * (len(means) - 1))]


def _profit_factor(values: list[float]) -> float:
    wins = sum(v for v in values if v > 0)
    losses = abs(sum(v for v in values if v < 0))
    if losses <= 1e-12:
        return 999.0 if wins > 0 else 0.0
    return wins / losses


def _fold_score(values: list[float]) -> dict[str, Any]:
    total = len(values)
    wins = sum(1 for value in values if value > 0)
    mean = statistics.fmean(values) if values else 0.0
    std = statistics.pstdev(values) if len(values) > 1 else 0.0
    sharpe_proxy = (mean / std * math.sqrt(total)) if std > 1e-12 else 0.0
    losses = sorted(abs(min(0.0, value)) for value in values)
    tail_loss_p95 = losses[int(0.95 * (len(losses) - 1))] if losses else 0.0
    return {
        "trades": total,
        "wins": wins,
        "win_rate": wins / total if total else 0.0,
        "mean_return": mean,
        "profit_factor": _profit_factor(values),
        "sharpe_proxy": sharpe_proxy,
        "bootstrap_edge_lcb_5pct": _bootstrap_lcb(values),
        "tail_loss_p95": tail_loss_p95,
        "sum_return": sum(values),
    }


def _path_parts(branch: dict[str, Any]) -> str:
    return (
        f"{branch['parent_regime_root']} -> {branch['sub_regime_tags'].split(';')[0].strip()} -> "
        f"{branch['sub_sub_regime_or_profit_factor']} -> {branch['profit_factor_leaf']}"
    )


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=False) + "\n")


def build(args: argparse.Namespace) -> dict[str, Any]:
    run_root = Path(args.run_root).resolve()
    autoquant_root = Path(args.autoquant_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    root_confidence = _load_root_confidence(Path(args.accepted_regime_artifact).resolve())
    runner = _load_strategy_runner(autoquant_root)
    pair_basket, timeranges = runner.get_strategy_overrides("CrashRebound")
    active_pairs = list(pair_basket or [])
    trade_rows: list[dict[str, Any]] = []
    fold_rows: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    replay_log = output_dir / "freqtrade_trade_extract.log"

    with replay_log.open("w", encoding="utf-8") as log_handle, contextlib.redirect_stdout(log_handle), contextlib.redirect_stderr(log_handle):
        for fold_label, timerange in timeranges:
            branch = dict(FOLD_BRANCH_MAP.get(fold_label, FOLD_BRANCH_MAP["full_5y"]))
            results = runner.run_backtest("CrashRebound", timerange, active_pairs)
            bundle = runner.extract_metrics(results, "CrashRebound", active_pairs)
            strat = results.get("strategy", {}).get("CrashRebound", {}) or {}
            trades = strat.get("trades") or []
            values: list[float] = []
            for idx, trade in enumerate(trades):
                fee_open = float(trade.get("fee_open") or 0.0)
                fee_close = float(trade.get("fee_close") or 0.0)
                profit_ratio = float(trade.get("profit_ratio") or 0.0)
                cost_stressed_profit_ratio = profit_ratio - fee_open - fee_close
                values.append(cost_stressed_profit_ratio)
                row = {
                    "accepted_regime_id": args.accepted_regime_id,
                    "recipe_id": "CrashRebound",
                    "fold_label": fold_label,
                    "timerange": timerange,
                    "independent_test_fold": branch["independent_test_fold"],
                    "branch_path_valid": branch["branch_path_valid"],
                    "parent_regime_root": branch["parent_regime_root"],
                    "parent_regime_confidence_floor": root_confidence.get(branch["parent_regime_root"], 0.0),
                    "manipulation_overlay_state": "absent_unverified",
                    "sub_regime_tags": branch["sub_regime_tags"],
                    "sub_sub_regime_or_profit_factor": branch["sub_sub_regime_or_profit_factor"],
                    "profit_factor_family": branch["profit_factor_family"],
                    "profit_factor_leaf": branch["profit_factor_leaf"],
                    "regime_profit_branch_path": _path_parts(branch),
                    "regime_profit_branch_path_version": "board-b-root-first-v1",
                    "allowed_action": branch["allowed_action"],
                    "suppression_rule": branch["suppression_rule"],
                    "pair": trade.get("pair"),
                    "trade_index": idx,
                    "open_date": _jsonish(trade.get("open_date")),
                    "close_date": _jsonish(trade.get("close_date")),
                    "profit_ratio": profit_ratio,
                    "profit_abs": float(trade.get("profit_abs") or 0.0),
                    "fee_open": fee_open,
                    "fee_close": fee_close,
                    "cost_stressed_profit_ratio": cost_stressed_profit_ratio,
                    "meta_label": 1 if cost_stressed_profit_ratio > 0 else 0,
                    "tail_loss": abs(min(0.0, cost_stressed_profit_ratio)),
                    "exit_reason": trade.get("exit_reason"),
                    "is_open": bool(trade.get("is_open")),
                    "stake_amount": float(trade.get("stake_amount") or 0.0),
                }
                trade_rows.append(row)
                labels.append(
                    {
                        "entry_index": len(labels),
                        "entry_timestamp": row["open_date"],
                        "side": 1,
                        "realized_R": cost_stressed_profit_ratio,
                        "mfe": _jsonish(trade.get("max_rate")),
                        "mae": -row["tail_loss"],
                        "time_to_hit": trade.get("trade_duration") or 0,
                        "meta_label": row["meta_label"],
                        "regime_confidence": row["parent_regime_confidence_floor"],
                        "slippage_R": fee_open + fee_close,
                    }
                )
            score = _fold_score(values)
            agg = bundle["aggregate"]
            fold_rows.append(
                {
                    "fold_label": fold_label,
                    "timerange": timerange,
                    "parent_regime_root": branch["parent_regime_root"],
                    "regime_profit_branch_path": _path_parts(branch),
                    "branch_path_valid": branch["branch_path_valid"],
                    "independent_test_fold": branch["independent_test_fold"],
                    "trades": score["trades"],
                    "win_rate": score["win_rate"],
                    "cost_stressed_mean_return": score["mean_return"],
                    "cost_stressed_sum_return": score["sum_return"],
                    "bootstrap_edge_lcb_5pct": score["bootstrap_edge_lcb_5pct"],
                    "profit_factor": score["profit_factor"],
                    "tail_loss_p95": score["tail_loss_p95"],
                    "sharpe_proxy": score["sharpe_proxy"],
                    "freqtrade_sharpe": agg.get("sharpe", 0.0),
                    "freqtrade_profit_pct": agg.get("total_profit_pct", 0.0),
                    "freqtrade_max_drawdown_pct": agg.get("max_drawdown_pct", 0.0),
                }
            )

    independent = [row for row in fold_rows if row["independent_test_fold"]]
    valid_independent = [row for row in independent if row["branch_path_valid"]]
    all_values = [float(row["cost_stressed_profit_ratio"]) for row in trade_rows if row["independent_test_fold"]]
    full_values = [float(row["cost_stressed_profit_ratio"]) for row in trade_rows if row["fold_label"] == "full_5y"]
    required_trades = 100
    target_edge = 0.005
    target_dsr = 1.0
    drawdown_budget = 0.20
    tail_loss_budget = 0.20
    total_score = _fold_score(all_values)
    full_score = _fold_score(full_values)
    positive_independent = sum(1 for row in independent if float(row["cost_stressed_sum_return"]) > 0.0)
    fold_positive_rate = positive_independent / len(independent) if independent else 0.0
    covered_roots = sorted({str(row["parent_regime_root"]) for row in valid_independent})
    missing_roots = [root for root in REQUIRED_ROOTS if root not in covered_roots]
    overlay_covered = any(row["parent_regime_root"] == OPTIONAL_OVERLAY for row in valid_independent)
    regime_specificity_ratio = 0.0
    valid_means = [float(row["cost_stressed_mean_return"]) for row in valid_independent]
    if valid_means and full_score["mean_return"] > 0:
        regime_specificity_ratio = max(valid_means) / full_score["mean_return"]
    pbo = 1.0 if len(valid_independent) < 4 or missing_roots else 0.25
    dsr_proxy = max(0.0, total_score["sharpe_proxy"] - math.sqrt(math.log(1.0 + 1.0)))
    hard_gate_failures: list[str] = []
    if not args.accepted_regime_id:
        hard_gate_failures.append("reject_missing_accepted_regime")
    if missing_roots or not overlay_covered:
        hard_gate_failures.append("reject_missing_branch_path")
    if len(all_values) < required_trades:
        hard_gate_failures.append("reject_thin_trades")
    if len(independent) < 4 or len(valid_independent) < 4:
        hard_gate_failures.append("reject_overfit_risk")
    if min((int(row["trades"]) for row in independent), default=0) < 10:
        hard_gate_failures.append("reject_thin_trades")
    if fold_positive_rate < 0.75 or total_score["bootstrap_edge_lcb_5pct"] <= 0.0:
        hard_gate_failures.append("reject_no_positive_edge")
    if any(float(row["cost_stressed_sum_return"]) <= 0.0 for row in independent):
        hard_gate_failures.append("reject_cost_fragile")
    if pbo > 0.25:
        hard_gate_failures.append("reject_overfit_risk")
    if dsr_proxy <= 0.0:
        hard_gate_failures.append("reject_no_positive_edge")
    if total_score["tail_loss_p95"] > tail_loss_budget:
        hard_gate_failures.append("reject_tail_risk")
    if regime_specificity_ratio < 1.20:
        hard_gate_failures.append("reject_no_regime_specificity")
    hard_gate_failures = sorted(set(hard_gate_failures))

    edge_score = _clamp(total_score["bootstrap_edge_lcb_5pct"] / target_edge)
    depth_score = _clamp(len(all_values) / required_trades)
    dsr_score = _clamp(dsr_proxy / target_dsr)
    pbo_score = 1.0 - _clamp(pbo / 0.25)
    cost_score = 0.0 if "reject_cost_fragile" in hard_gate_failures else 1.0
    drawdown_score = 1.0 - _clamp(total_score["tail_loss_p95"] / drawdown_budget)
    specificity_score = _clamp((regime_specificity_ratio - 1.0) / 0.5)
    raw_rc_spa = 100.0 * (
        0.20 * edge_score
        + 0.15 * fold_positive_rate
        + 0.15 * depth_score
        + 0.15 * dsr_score
        + 0.10 * pbo_score
        + 0.10 * cost_score
        + 0.10 * drawdown_score
        + 0.05 * specificity_score
    )
    rc_spa = 0.0 if hard_gate_failures else raw_rc_spa
    promotion_level = "reject"
    if not hard_gate_failures and rc_spa >= 85.0:
        promotion_level = "pilot_candidate"
    elif not hard_gate_failures and rc_spa >= 75.0:
        promotion_level = "stable_candidate"
    elif not hard_gate_failures and rc_spa >= 60.0:
        promotion_level = "research_watch"

    report = {
        "schema_version": "board-b-branch-path-rc-spa/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "accepted_regime_id": args.accepted_regime_id,
        "accepted_regime_artifact": str(Path(args.accepted_regime_artifact).resolve()),
        "recipe_id": "CrashRebound",
        "recipe_artifact_path": str(autoquant_root / "user_data/strategies/CrashRebound.py"),
        "backtest_artifact_path": str(run_root / "autoquant/crashrebound_replay.out"),
        "total_trades": len([row for row in trade_rows if row["fold_label"] == "full_5y"]),
        "independent_trade_rows": len(all_values),
        "test_folds": len(independent),
        "valid_branch_path_test_folds": len(valid_independent),
        "fold_positive_rate": fold_positive_rate,
        "bootstrap_edge_lcb_5pct": total_score["bootstrap_edge_lcb_5pct"],
        "pbo": pbo,
        "dsr": dsr_proxy,
        "cost_stress_result": "pass" if "reject_cost_fragile" not in hard_gate_failures else "fail",
        "tail_loss_p95": total_score["tail_loss_p95"],
        "tail_loss_budget": tail_loss_budget,
        "regime_specificity_ratio": regime_specificity_ratio,
        "covered_roots": covered_roots,
        "missing_roots": missing_roots,
        "manipulation_overlay_covered": overlay_covered,
        "hard_gate_result": "pass" if not hard_gate_failures else "fail:" + ",".join(hard_gate_failures),
        "hard_gate_failures": hard_gate_failures,
        "raw_rc_spa_before_hard_gate_zero": raw_rc_spa,
        "rc_spa": rc_spa,
        "promotion_level": promotion_level,
        "downstream_consumption_status": "not_eligible_fail_closed",
        "downstream_consumption": {
            "pre_bayes_filter": "fail_closed_before_bbn",
            "bbn": "failure_memory_only",
            "catboost_path_ranker": "not_run_no_target_rows",
            "execution_tree": "not_eligible_no_stable_or_pilot_candidate",
        },
        "notes": [
            "full_5y replay is overlapping diagnostic evidence and is not counted as an independent fold",
            "recovery_23_25 is not a Board A accepted root and is therefore marked branch_path_valid=false",
            "Manipulation overlay has no direct source-positive rows for this CrashRebound replay",
        ],
        "artifact_paths": {
            "trade_rows_csv": str(output_dir / "crashrebound_branch_trade_rows.csv"),
            "trade_rows_jsonl": str(output_dir / "crashrebound_branch_trade_rows.jsonl"),
            "folds_csv": str(output_dir / "crashrebound_branch_folds.csv"),
            "labels_jsonl": str(output_dir / "labels.jsonl"),
            "payoff_report_json": str(output_dir / "payoff_report.json"),
            "rc_spa_report_json": str(output_dir / "rc_spa_report.json"),
            "freqtrade_trade_extract_log": str(replay_log),
        },
    }
    payoff_report = {
        "candidate_id": "CrashRebound__branch_path_rc_spa",
        "promotion_gate": "reject" if promotion_level == "reject" else "probe",
        "dsr": dsr_proxy,
        "psr": max(0.0, min(1.0, fold_positive_rate)),
        "sharpe": full_score["sharpe_proxy"],
        "payoff_shape": "counter_trend_drawdown_rebound",
        "failure_tags": hard_gate_failures,
    }

    _write_csv(output_dir / "crashrebound_branch_trade_rows.csv", trade_rows)
    _write_jsonl(output_dir / "crashrebound_branch_trade_rows.jsonl", trade_rows)
    _write_csv(output_dir / "crashrebound_branch_folds.csv", fold_rows)
    _write_jsonl(output_dir / "labels.jsonl", labels)
    _write_json(output_dir / "payoff_report.json", payoff_report)
    _write_json(output_dir / "rc_spa_report.json", report)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    default_run_root = Path(__file__).resolve().parents[1]
    parser.add_argument("--run-root", default=str(default_run_root))
    parser.add_argument("--autoquant-root", default=str(default_run_root / "autoquant"))
    parser.add_argument("--output-dir", default=str(default_run_root / "branch-path-rc-spa"))
    parser.add_argument(
        "--accepted-regime-id",
        default="BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
    )
    parser.add_argument(
        "--accepted-regime-artifact",
        default=str(
            Path(__file__).resolve().parents[2]
            / "20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    report = build(parse_args(argv))
    print(json.dumps({
        "ok": True,
        "rc_spa": report["rc_spa"],
        "hard_gate_result": report["hard_gate_result"],
        "promotion_level": report["promotion_level"],
        "output": report["artifact_paths"]["rc_spa_report_json"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
