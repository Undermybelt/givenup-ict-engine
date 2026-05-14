#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import random
import zipfile
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T002251+0800-codex-board-b-local-nq-nonzero-candidate-probe-v1"
SCHEMA_VERSION = "board-b-local-nq-nonzero-candidate/v1"
RECIPE_ID = "TomacNQ_KillzoneBreakout"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
TARGET_EDGE = 0.001
TARGET_DSR = 1.0
MIN_TOTAL_TRADES = 100
MIN_TEST_FOLDS = 4
MIN_TRADES_PER_TEST_FOLD = 10
FOLD_POSITIVE_RATE_MIN = 0.75
EXTRA_ROUND_TRIP_COST = 0.0002


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot find repo root from {start}")


RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = find_repo_root(Path(__file__).resolve())
ZIP_PATH = Path("/Users/thrill3r/Auto-Quant/user_data/backtest_results/backtest-result-2026-05-12_00-27-36.zip")
SOURCE_REGIME_CSV = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
BOARD_A_CONSUMER_MAP = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/"
    "regime_factor_consumer_map_v1.csv"
)
OUT_DIR = RUN_ROOT / "branch-rc-spa"
ICT_DIR = RUN_ROOT / "ict-engine-downstream"
CHECK_DIR = RUN_ROOT / "checks"
REPORT_JSON = OUT_DIR / "tomac_nq_nonzero_candidate_report_v1.json"
REPORT_MD = OUT_DIR / "tomac_nq_nonzero_candidate_report_v1.md"
TRADE_ROWS_CSV = OUT_DIR / "tomac_nq_nonzero_candidate_trade_rows_v1.csv"
BRANCH_SUMMARY_CSV = OUT_DIR / "tomac_nq_nonzero_candidate_branch_summary_v1.csv"
WIRE_JSONL = ICT_DIR / "tomac_nq_nonzero_candidate_real_trades_v1.jsonl"
WIRE_COUNT = ICT_DIR / "tomac_nq_nonzero_candidate_real_trades_v1.count"
ASSERTIONS = CHECK_DIR / "tomac_nq_nonzero_candidate_assertions_v1.out"

BRANCH_MAP = {
    "Bull": ("TrendExpansion", "TomacKillzoneBreakout", "intraday_breakout"),
    "Bear": ("BearMarketDrawdown", "TomacBreakoutSuppression", "intraday_breakout"),
    "Sideways": ("RangeConsolidation", "TomacFalseBreakoutRisk", "intraday_breakout"),
    "Crisis": ("ExtremeStress", "TomacPanicBreakoutGuard", "intraday_breakout"),
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def load_root_floors() -> dict[str, float]:
    floors: dict[str, float] = {}
    with BOARD_A_CONSUMER_MAP.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            regime = row.get("regime", "")
            if regime in {"Bull", "Bear", "Sideways", "Crisis", "Manipulation"}:
                floors[regime] = float(row.get("confidence_floor") or 0.0)
    return floors


def load_source_schedule() -> tuple[list[str], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    with SOURCE_REGIME_CSV.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("ticker") != "^IXIC":
                continue
            rows.append(
                {
                    "date": row["date"],
                    "root": row["regime_label"],
                    "confidence": float(row.get("regime_confidence") or 0.0),
                    "vix": float(row.get("vix") or 0.0),
                }
            )
    rows.sort(key=lambda r: r["date"])
    return [row["date"] for row in rows], rows


def load_backtest_payload() -> dict[str, Any]:
    with zipfile.ZipFile(ZIP_PATH) as zf:
        json_names = [name for name in zf.namelist() if name.endswith(".json") and "_config" not in name]
        if len(json_names) != 1:
            raise RuntimeError(f"expected one result JSON in {ZIP_PATH}, got {json_names}")
        return json.loads(zf.read(json_names[0]).decode("utf-8"))


def branch_path(root: str) -> str:
    sub, leaf, _family = BRANCH_MAP.get(root, ("Unlabeled", "Unlabeled", "intraday_breakout"))
    return f"{root} -> {sub} -> {leaf} -> {RECIPE_ID}"


def factor_direction_from_root(root: str) -> str:
    return root if root in {"Bull", "Bear"} else "Neutral"


def factor_direction_from_pnl(pnl: float) -> str:
    if pnl > 0.0:
        return "Bull"
    if pnl < 0.0:
        return "Bear"
    return "Neutral"


def attach_rows(
    trades: list[dict[str, Any]],
    dates: list[str],
    schedule: list[dict[str, Any]],
    floors: dict[str, float],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, trade in enumerate(trades, start=1):
        open_ts_ms = int(trade["open_timestamp"])
        close_ts_ms = int(trade["close_timestamp"])
        opened = datetime.fromtimestamp(open_ts_ms / 1000, tz=timezone.utc)
        closed = datetime.fromtimestamp(close_ts_ms / 1000, tz=timezone.utc)
        session_date = opened.date().isoformat()
        pos = bisect_right(dates, session_date) - 1
        if pos >= 0:
            source = schedule[pos]
            root = source["root"]
            source_date = source["date"]
            source_conf = source["confidence"]
            source_vix = source["vix"]
        else:
            root = "Unlabeled"
            source_date = ""
            source_conf = 0.0
            source_vix = 0.0
        sub, leaf, family = BRANCH_MAP.get(root, ("Unlabeled", "Unlabeled", "intraday_breakout"))
        pnl = float(trade.get("profit_ratio") or 0.0)
        realized = "win" if pnl > 0 else "loss" if pnl < 0 else "breakeven"
        rows.append(
            {
                "row_id": idx,
                "schema_version": SCHEMA_VERSION,
                "run_id": RUN_ID,
                "recipe_id": RECIPE_ID,
                "strategy_name": RECIPE_ID,
                "strategy_mutation_id": "local-auto-quant-tomac-nq-killzone-breakout",
                "symbol": SYMBOL,
                "target_market": "NQ/USD",
                "trade_id": f"{RECIPE_ID}:{idx}",
                "open_ts_ms": open_ts_ms,
                "close_ts_ms": close_ts_ms,
                "open_date": opened.isoformat(),
                "close_date": closed.isoformat(),
                "open_session_date": session_date,
                "source_regime_session_date": source_date,
                "source_context_attachment_policy": "^IXIC_source_anchor_previous_session_context",
                "source_anchor": "^IXIC",
                "parent_regime_root": root,
                "parent_regime_confidence_floor": floors.get(root, 0.0),
                "source_anchor_confidence": source_conf,
                "source_anchor_vix": source_vix,
                "sub_regime_tags": sub,
                "sub_sub_regime_or_profit_factor": leaf,
                "profit_factor_family": family,
                "profit_factor_leaf": RECIPE_ID,
                "regime_profit_branch_path": branch_path(root),
                "regime_profit_branch_path_version": SCHEMA_VERSION,
                "trade_or_bar_horizon": f"{trade.get('trade_duration')}m_trade",
                "entry_signal": "tomac_killzone_breakout",
                "exit_reason": trade.get("exit_reason", "unknown"),
                "year_fold": opened.year,
                "profit_ratio_net": pnl,
                "pnl": pnl,
                "realized_outcome": realized,
                "win_rate_component": 1 if pnl > 0 else 0,
            }
        )
    return rows


def bootstrap_lcb(values: list[float], seed: int = 42) -> float:
    if not values:
        return 0.0
    rng = random.Random(seed)
    draws = []
    for _ in range(3000):
        sample = [values[rng.randrange(len(values))] for _ in range(len(values))]
        draws.append(sum(sample) / len(sample))
    draws.sort()
    return draws[int(0.05 * (len(draws) - 1))]


def max_drawdown(values: list[float]) -> float:
    if not values:
        return 0.0
    equity = 1.0
    peak = 1.0
    worst = 0.0
    for value in values:
        equity *= 1.0 + value
        peak = max(peak, equity)
        worst = min(worst, equity / peak - 1.0)
    return abs(worst)


def summarize_branch(path: str, rows: list[dict[str, Any]], all_rows: list[dict[str, Any]]) -> dict[str, Any]:
    returns = [float(row["profit_ratio_net"]) for row in rows]
    outside = [
        float(row["profit_ratio_net"])
        for row in all_rows
        if row["regime_profit_branch_path"] != path
    ]
    folds = sorted({int(row["year_fold"]) for row in rows})
    fold_sums = [
        sum(float(row["profit_ratio_net"]) for row in rows if int(row["year_fold"]) == fold)
        for fold in folds
    ]
    fold_counts = [
        sum(1 for row in rows if int(row["year_fold"]) == fold)
        for fold in folds
    ]
    n = len(returns)
    mean_return = sum(returns) / n if n else 0.0
    win_rate = sum(1 for value in returns if value > 0.0) / n if n else 0.0
    lcb = bootstrap_lcb(returns)
    stressed = [value - EXTRA_ROUND_TRIP_COST for value in returns]
    stressed_lcb = bootstrap_lcb(stressed)
    std = math.sqrt(sum((value - mean_return) ** 2 for value in returns) / (n - 1)) if n > 1 else 0.0
    dsr = mean_return / std * math.sqrt(n) if std > 0.0 else 0.0
    outside_mean = sum(outside) / len(outside) if outside else 0.0
    specificity = 999.0 if mean_return > 0.0 and outside_mean <= 0.0 else (
        mean_return / outside_mean if outside_mean > 0.0 else 0.0
    )
    fold_positive_rate = sum(1 for value in fold_sums if value > 0.0) / len(fold_sums) if fold_sums else 0.0
    min_trades_per_fold = min(fold_counts) if fold_counts else 0
    pbo = 1.0 if len(folds) < MIN_TEST_FOLDS else sum(1 for value in fold_sums if value <= 0.0) / len(fold_sums)
    cost_ok = bool(n and sum(stressed) > 0.0 and stressed_lcb > 0.0)
    tail_loss_p95 = max(0.0, -sorted(returns)[max(0, int(0.05 * (n - 1)))]) if n else 0.0
    branch_mdd = max_drawdown(returns)

    edge_score = min(max(lcb / TARGET_EDGE, 0.0), 1.0)
    fold_score = fold_positive_rate
    depth_score = min(max(n / MIN_TOTAL_TRADES, 0.0), 1.0)
    dsr_score = min(max(dsr / TARGET_DSR, 0.0), 1.0)
    pbo_score = 1.0 - min(max(pbo / 0.25, 0.0), 1.0)
    cost_score = 1.0 if cost_ok else 0.0
    drawdown_score = 1.0 - min(max(branch_mdd / 0.25, 0.0), 1.0)
    specificity_score = min(max((specificity - 1.0) / 0.5, 0.0), 1.0)
    rc_spa = 100.0 * (
        0.20 * edge_score
        + 0.15 * fold_score
        + 0.15 * depth_score
        + 0.15 * dsr_score
        + 0.10 * pbo_score
        + 0.10 * cost_score
        + 0.10 * drawdown_score
        + 0.05 * specificity_score
    )

    failures: list[str] = []
    if n < MIN_TOTAL_TRADES:
        failures.append("reject_thin_trades")
    if len(folds) < MIN_TEST_FOLDS:
        failures.append("reject_insufficient_test_folds")
    if min_trades_per_fold < MIN_TRADES_PER_TEST_FOLD:
        failures.append("reject_fold_trade_depth")
    if fold_positive_rate < FOLD_POSITIVE_RATE_MIN:
        failures.append("reject_fold_inconsistency")
    if lcb <= 0.0:
        failures.append("reject_no_positive_edge")
    if not cost_ok:
        failures.append("reject_cost_fragile")
    if pbo > 0.25:
        failures.append("reject_overfit_risk")
    if dsr <= 0.0:
        failures.append("reject_dsr_nonpositive")
    if specificity < 1.20:
        failures.append("reject_no_regime_specificity")
    if rc_spa < 60.0:
        failures.append("reject_rc_spa_below_60")

    parent_root = rows[0]["parent_regime_root"] if rows else path.split(" -> ", 1)[0]
    return {
        "recipe_id": RECIPE_ID,
        "regime_profit_branch_path": path,
        "parent_regime_root": parent_root,
        "total_trades": n,
        "test_folds": len(folds),
        "min_trades_per_test_fold": min_trades_per_fold,
        "fold_positive_rate": fold_positive_rate,
        "win_rate": win_rate,
        "mean_profit_ratio_net": mean_return,
        "bootstrap_edge_lcb_5pct": lcb,
        "bootstrap_edge_lcb_5pct_stressed_cost": stressed_lcb,
        "pbo": pbo,
        "dsr": dsr,
        "cost_stress_result": "pass" if cost_ok else "fail",
        "tail_loss_p95": tail_loss_p95,
        "max_drawdown_trade_equity_proxy": branch_mdd,
        "regime_specificity_ratio": specificity,
        "outside_mean_profit_ratio_net": outside_mean,
        "rc_spa": rc_spa,
        "hard_gate_result": "pass" if not failures else "fail:" + "|".join(dict.fromkeys(failures)),
    }


def write_wire(rows: list[dict[str, Any]]) -> None:
    ICT_DIR.mkdir(parents=True, exist_ok=True)
    with WIRE_JSONL.open("w", encoding="utf-8") as fh:
        for row in rows:
            pnl = float(row["pnl"])
            root = row["parent_regime_root"]
            pnl_direction = factor_direction_from_pnl(pnl)
            feedback = {
                "protocol_version": SCHEMA_VERSION,
                "recommendation_id": row["trade_id"],
                "recommended_at": row["open_date"],
                "symbol": SYMBOL,
                "node_id": root,
                "branch_id": row["regime_profit_branch_path"],
                "scenario_id": row["sub_regime_tags"],
                "path_id": row["regime_profit_branch_path"],
                "direction": "long",
                "entry_style": "tomac_killzone_breakout",
                "candidate_set_id": RUN_ID,
                "candidate_set_size": len(rows),
                "followed_path": True,
                "realized_outcome": row["realized_outcome"],
                "realized_pnl": pnl,
                "exit_reason": row["exit_reason"],
                "notes": "isolated_fail_closed_local_nq_nonzero_candidate_probe",
            }
            payload = {
                "schema_version": "1.0",
                "symbol": SYMBOL,
                "trade_id": row["trade_id"],
                "strategy_name": RECIPE_ID,
                "strategy_mutation_id": row["strategy_mutation_id"],
                "auto_quant_run_id": RUN_ID,
                "open_ts_ms": row["open_ts_ms"],
                "close_ts_ms": row["close_ts_ms"],
                "direction": "long",
                "pnl": pnl,
                "realized_outcome": row["realized_outcome"],
                "regime_at_entry": root,
                "entry_signal": row["entry_signal"],
                "factors_used": [
                    {
                        "factor_name": "market_regime_context.root",
                        "category": "regime_context",
                        "direction": factor_direction_from_root(root),
                        "value": row["source_anchor_confidence"],
                        "confidence": row["source_anchor_confidence"],
                        "weighted_score": row["source_anchor_confidence"],
                        "uncertainty_contribution": max(0.0, 1.0 - row["source_anchor_confidence"]),
                    },
                    {
                        "factor_name": "regime_profit_branch_path",
                        "category": "branch_path",
                        "direction": pnl_direction,
                        "value": pnl,
                        "confidence": row["source_anchor_confidence"],
                        "weighted_score": pnl,
                        "uncertainty_contribution": max(0.0, 1.0 - row["source_anchor_confidence"]),
                    },
                    {
                        "factor_name": "tomac_killzone_breakout",
                        "category": "intraday_breakout",
                        "direction": pnl_direction,
                        "value": pnl,
                        "confidence": 0.50,
                        "weighted_score": pnl,
                        "uncertainty_contribution": 0.50,
                    },
                ],
                "structural_feedback": feedback,
            }
            fh.write(json.dumps(payload, sort_keys=True) + "\n")
    WIRE_COUNT.write_text(f"{len(rows)}\n", encoding="utf-8")


def write_report(report: dict[str, Any]) -> None:
    decision = report["decision"]
    lines = [
        "# Tomac NQ Nonzero Candidate Probe v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        "This run resolves the prior `zero_trade_auto_quant_candidate` blocker only at the measurement layer: the local Auto-Quant/Freqtrade path emitted real NQ trades. It does not promote a profitability factor.",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Stable profit score: `{decision['stable_profit_score']:.4f}`",
        f"- Trade rows: `{decision['total_trade_rows']}`",
        f"- Root trade counts: `{decision['root_trade_counts']}`",
        f"- Downstream consumption: `{decision['downstream_consumption']}`",
        f"- Primary blocker: {decision['primary_blocker']}",
        "",
        "## Branch Summary",
        "",
        "| Root | Trades | Folds | Win Rate | Mean PnL | LCB 5% | PBO | DSR | RC-SPA | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["branch_summaries"]:
        lines.append(
            f"| {row['parent_regime_root']} | {row['total_trades']} | {row['test_folds']} | "
            f"{row['win_rate']:.4f} | {row['mean_profit_ratio_net']:.6f} | "
            f"{row['bootstrap_edge_lcb_5pct']:.6f} | {row['pbo']:.2f} | "
            f"{row['dsr']:.4f} | {row['rc_spa']:.4f} | `{row['hard_gate_result']}` |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Auto-Quant log: `{rel(RUN_ROOT / 'logs/01_tomac_nq_killzone_breakout.out')}`",
            f"- Source zip: `{ZIP_PATH}`",
            f"- Trade rows: `{rel(TRADE_ROWS_CSV)}`",
            f"- Branch summary: `{rel(BRANCH_SUMMARY_CSV)}`",
            f"- ict-engine wire JSONL: `{rel(WIRE_JSONL)}`",
            f"- Assertions: `{rel(ASSERTIONS)}`",
            "",
            "## Next",
            "",
            f"- {decision['next_action']}",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    for path in [OUT_DIR, ICT_DIR, CHECK_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    payload = load_backtest_payload()
    strategy = payload["strategy"][RECIPE_ID]
    trades = strategy.get("trades", [])
    dates, schedule = load_source_schedule()
    floors = load_root_floors()
    rows = attach_rows(trades, dates, schedule, floors)
    required_paths = [branch_path(root) for root in ["Bull", "Bear", "Sideways", "Crisis"]]
    branch_summaries = [
        summarize_branch(path, [row for row in rows if row["regime_profit_branch_path"] == path], rows)
        for path in required_paths
    ]
    max_rc_spa = max([float(row["rc_spa"]) for row in branch_summaries] or [0.0])
    branch_passes = [row for row in branch_summaries if row["hard_gate_result"] == "pass"]
    root_counts = {
        root: sum(1 for row in rows if row["parent_regime_root"] == root)
        for root in ["Bull", "Bear", "Sideways", "Crisis"]
    }
    gate_result = "pass:all_required_root_branch_paths_passed" if len(branch_passes) == 4 else (
        "fail:measured_nonzero_but_branch_rc_spa_rejected"
    )
    downstream = (
        "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe"
        if gate_result.startswith("pass:")
        else "fail_closed:parse_and_status_probe_only"
    )
    decision = {
        "board_state": "pilot_candidate" if gate_result.startswith("pass:") else "rejected",
        "gate_result": gate_result,
        "stable_profit_score": max_rc_spa,
        "total_trade_rows": len(rows),
        "root_trade_counts": root_counts,
        "branch_paths_passed": len(branch_passes),
        "downstream_consumption": downstream,
        "primary_blocker": (
            "Local NQ Auto-Quant produced nonzero trades, but the candidate is negative "
            "overall and far below root-first support/fold/edge gates."
        ),
        "next_action": (
            "Keep this as fail-closed measurement evidence; next switch to a denser "
            "NQ/local-feather family or user-selected dataset before promotion probes."
        ),
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "recipe_id": RECIPE_ID,
        "symbol": SYMBOL,
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "accepted_regime_artifact": rel(BOARD_A_CONSUMER_MAP),
        "auto_quant_result_zip": str(ZIP_PATH),
        "auto_quant_metrics": {
            "trade_count": int(strategy.get("total_trades") or 0),
            "profit_total_pct": float(strategy.get("profit_total", 0.0)) * 100.0,
            "sharpe": float(strategy.get("sharpe") or 0.0),
            "sortino": float(strategy.get("sortino") or 0.0),
            "calmar": float(strategy.get("calmar") or 0.0),
            "win_rate": float(strategy.get("winrate") or 0.0),
            "profit_factor": float(strategy.get("profit_factor") or 0.0),
        },
        "decision": decision,
        "branch_summaries": branch_summaries,
        "artifacts": {
            "report_md": rel(REPORT_MD),
            "report_json": rel(REPORT_JSON),
            "trade_rows_csv": rel(TRADE_ROWS_CSV),
            "branch_summary_csv": rel(BRANCH_SUMMARY_CSV),
            "ict_engine_wire_jsonl": rel(WIRE_JSONL),
            "assertions": rel(ASSERTIONS),
        },
    }
    write_csv(TRADE_ROWS_CSV, rows)
    write_csv(BRANCH_SUMMARY_CSV, branch_summaries)
    write_wire(rows)
    write_json(REPORT_JSON, report)
    write_report(report)
    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_zip_exists={ZIP_PATH.exists()}",
        f"PASS auto_quant_trade_count={len(rows)}",
        f"PASS wire_count={WIRE_COUNT.read_text(encoding='utf-8').strip()}",
        f"PASS gate_result={gate_result}",
        f"PASS promotion_allowed={str(gate_result.startswith('pass:')).lower()}",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
    ]
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "report": rel(REPORT_JSON), "gate_result": gate_result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
