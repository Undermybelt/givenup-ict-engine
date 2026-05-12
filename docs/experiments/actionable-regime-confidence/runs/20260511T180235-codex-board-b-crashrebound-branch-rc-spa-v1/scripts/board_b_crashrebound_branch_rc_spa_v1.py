#!/usr/bin/env python3
"""Run CrashRebound through Board B branch-path RC-SPA scoring.

This is an additive experiment artifact. It uses the local Auto-Quant checkout
and the frozen v0.4.1 CrashRebound strategy file, then emits trade-level rows
keyed by Board A market-regime context roots.
"""

from __future__ import annotations

import bisect
import contextlib
import csv
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import pandas as pd
from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting


RUN_ID = "20260511T180235+0800-codex-board-b-crashrebound-branch-rc-spa-v1"
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T180235-codex-board-b-crashrebound-branch-rc-spa-v1"
)
BOARD_B = Path("docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md")
BOARD_A_MAP = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T153637-codex-regime-factor-consumer-map-v1/"
    "regime-factor-map/regime_factor_consumer_map_v1.json"
)
BOARD_A_CONTEXT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T144838-codex-market-regime-context-packet-v1/"
    "market-regime-context/market_regime_context_packet_v1.json"
)
SOURCE_REGIME_CSV = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)
AUTO_QUANT_ROOT = Path("/Users/thrill3r/Auto-Quant")
AUTO_QUANT_STRATEGY_PATH = AUTO_QUANT_ROOT / "versions/0.4.1/strategies"
STRATEGY_FILE = AUTO_QUANT_STRATEGY_PATH / "CrashRebound.py"

OUT_DIR = RUN_ROOT / "branch-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"
LOG_DIR = RUN_ROOT / "logs"
TRADES_CSV = OUT_DIR / "crashrebound_branch_trades_v1.csv"
TRADES_JSONL = OUT_DIR / "crashrebound_branch_trades_v1.jsonl"
LABELS_JSONL = OUT_DIR / "crashrebound_purged_cv_labels_v1.jsonl"
SUMMARY_JSON = OUT_DIR / "crashrebound_branch_summary_v1.json"
RC_SPA_JSON = OUT_DIR / "crashrebound_rc_spa_report_v1.json"
PAYOFF_JSON = OUT_DIR / "crashrebound_payoff_shape_v1.json"
PURGED_JSON = OUT_DIR / "crashrebound_purged_cv_guard_v1.json"
PACKET_JSON = OUT_DIR / "crashrebound_regime_profitability_packet_v1.json"
IMPORT_MANIFEST = OUT_DIR / "crashrebound_strategy_library_for_import_v1.json"
REPORT_MD = OUT_DIR / "crashrebound_branch_rc_spa_v1.md"
ASSERTIONS = CHECK_DIR / "board_b_crashrebound_branch_rc_spa_v1_assertions.out"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
ROOT_TO_SUB_REGIME = {
    "Bull": "PullbackInUptrend",
    "Bear": "BearMarketCapitulationRebound",
    "Sideways": "RangeShockMeanReversion",
    "Crisis": "ExtremeStressReboundOrSuppression",
}
SUB_SUB_FACTOR = "DrawdownLt20RsiLt35VolumeConfirmDailyEmaSlopeUp"
PROFIT_FAMILY = "CounterTrendDrawdownRebound"
PROFIT_LEAF = "CrashRebound"
TIMERANGES = [
    ("bull_2021", "20210101-20211231"),
    ("winter_2022", "20220101-20221231"),
    ("recovery_23_25", "20230101-20251231"),
    ("full_5y", "20210101-20251231"),
]
PAIR_BASKET = ["SOL/USDT", "AVAX/USDT", "BNB/USDT"]
TAIL_LOSS_BUDGET = 0.10
TARGET_EDGE = 0.005
TARGET_DSR = 0.80
DRAWDOWN_BUDGET = 0.20
NB_TRIALS = 30


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False, default=str) + "\n", encoding="utf-8")


def _iso(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return default
        return out
    except (TypeError, ValueError):
        return default


def _pct(value: float) -> float:
    return round(value * 100.0, 6)


def _get_metric(entry: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        if key in entry:
            return _safe_float(entry[key], default)
    return default


def _validation_metrics(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "sharpe": round(_get_metric(entry, "sharpe", "sharpe_ratio"), 6),
        "sortino": round(_get_metric(entry, "sortino", "sortino_ratio"), 6),
        "calmar": round(_get_metric(entry, "calmar", "calmar_ratio"), 6),
        "total_profit_pct": round(_get_metric(entry, "profit_total_pct"), 6),
        "max_drawdown_pct": round(-abs(_get_metric(entry, "max_drawdown_account")) * 100.0, 6),
        "trade_count": int(_get_metric(entry, "trades", "total_trades")),
        "win_rate_pct": round(_get_metric(entry, "winrate") * 100.0, 6),
        "profit_factor": round(_get_metric(entry, "profit_factor"), 6),
    }


def _extract_metrics(results: dict[str, Any], strategy_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    strat = results.get("strategy", {}).get(strategy_name, {}) or {}
    aggregate: dict[str, Any] = _validation_metrics(strat)
    per_pair: dict[str, Any] = {}
    for entry in strat.get("results_per_pair", []) or []:
        key = entry.get("key", "")
        metrics = _validation_metrics(entry)
        if key == "TOTAL":
            aggregate = metrics
        elif key:
            per_pair[key] = metrics
    return aggregate, per_pair


def run_backtest(label: str, timerange: str) -> dict[str, Any]:
    args = {
        "config": [str(AUTO_QUANT_ROOT / "config.json")],
        "user_data_dir": str(AUTO_QUANT_ROOT / "user_data"),
        "datadir": str(AUTO_QUANT_ROOT / "user_data/data"),
        "strategy": "CrashRebound",
        "strategy_path": str(AUTO_QUANT_STRATEGY_PATH),
        "timerange": timerange,
        "export": "none",
        "exportfilename": None,
        "cache": "none",
    }
    config = Configuration(args, RunMode.BACKTEST).get_config()
    config["exchange"]["pair_whitelist"] = list(PAIR_BASKET)
    log_path = LOG_DIR / f"freqtrade_backtest_{label}.out"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        bt = Backtesting(config)
        bt.start()
    strat = bt.results.get("strategy", {}).get("CrashRebound", {}) or {}
    aggregate, per_pair = _extract_metrics(bt.results, "CrashRebound")
    return {
        "label": label,
        "timerange": timerange,
        "log_path": str(log_path),
        "aggregate_metrics": aggregate,
        "per_pair_metrics": per_pair,
        "trades": strat.get("trades", []) or [],
        "backtest_start": str(strat.get("backtest_start", "")),
        "backtest_end": str(strat.get("backtest_end", "")),
    }


class SourceRegimeLookup:
    def __init__(self, source_csv: Path) -> None:
        rows = pd.read_csv(source_csv, usecols=["date", "regime_label", "regime_confidence"])
        rows["date"] = pd.to_datetime(rows["date"]).dt.tz_localize(None)
        grouped = rows.groupby(["date", "regime_label"], observed=True).size().unstack(fill_value=0)
        confidence = rows.groupby(["date", "regime_label"], observed=True)["regime_confidence"].mean().unstack()
        daily: dict[pd.Timestamp, dict[str, Any]] = {}
        for date, counts in grouped.iterrows():
            total = int(counts.sum())
            root = str(counts.idxmax())
            support = int(counts[root])
            daily[pd.Timestamp(date)] = {
                "root": root,
                "support": support,
                "total": total,
                "panel_share": support / total if total else 0.0,
                "source_avg_confidence": _safe_float(confidence.loc[date, root]) if root in confidence.columns else 0.0,
            }
        self.daily = daily
        self.dates = sorted(daily)

    def lookup(self, value: Any) -> dict[str, Any]:
        ts = pd.Timestamp(value)
        if ts.tzinfo is not None:
            ts = ts.tz_convert("UTC").tz_localize(None)
        date = ts.normalize()
        if date in self.daily:
            out = dict(self.daily[date])
            out.update({"matched_source_date": date.date().isoformat(), "root_lookup_status": "exact_source_date"})
            return out
        pos = bisect.bisect_right(self.dates, date) - 1
        if pos >= 0:
            prev = self.dates[pos]
            gap_days = int((date - prev).days)
            if 0 <= gap_days <= 3:
                out = dict(self.daily[prev])
                out.update({
                    "matched_source_date": prev.date().isoformat(),
                    "root_lookup_status": f"previous_source_date_gap_{gap_days}d",
                })
                return out
        return {
            "root": "unknown",
            "support": 0,
            "total": 0,
            "panel_share": 0.0,
            "source_avg_confidence": 0.0,
            "matched_source_date": "",
            "root_lookup_status": "missing_source_date",
        }


def load_root_confidence() -> dict[str, float]:
    payload = json.loads(BOARD_A_CONTEXT.read_text(encoding="utf-8"))
    return {
        root: _safe_float(payload["root_packets"][root]["min_split_wilson95_lcb_floor"])
        for root in ROOTS
    }


def trade_to_row(trade: dict[str, Any], lookup: SourceRegimeLookup, root_confidence: dict[str, float]) -> dict[str, Any]:
    open_date = trade.get("open_date")
    close_date = trade.get("close_date")
    root_info = lookup.lookup(open_date)
    root = root_info["root"]
    sub_regime = ROOT_TO_SUB_REGIME.get(root, "UnknownRoot")
    branch_path = (
        f"{root} -> {sub_regime} -> {SUB_SUB_FACTOR} -> {PROFIT_LEAF}"
        if root in ROOTS
        else ""
    )
    fee_open = _safe_float(trade.get("fee_open"))
    fee_close = _safe_float(trade.get("fee_close"))
    cost_r = fee_open + fee_close
    realized_r = _safe_float(trade.get("profit_ratio"))
    stressed_r = realized_r - cost_r
    return {
        "run_id": RUN_ID,
        "recipe_id": PROFIT_LEAF,
        "pair": trade.get("pair", ""),
        "open_date": _iso(open_date),
        "close_date": _iso(close_date),
        "entry_index": int(_safe_float(trade.get("open_timestamp")) // 3_600_000),
        "exit_index": int(_safe_float(trade.get("close_timestamp")) // 3_600_000),
        "open_rate": _safe_float(trade.get("open_rate")),
        "close_rate": _safe_float(trade.get("close_rate")),
        "stake_amount": _safe_float(trade.get("stake_amount")),
        "profit_ratio": realized_r,
        "profit_abs": _safe_float(trade.get("profit_abs")),
        "gross_R": realized_r + cost_r,
        "cost_R": cost_r,
        "realized_R": realized_r,
        "stressed_2x_cost_R": stressed_r,
        "is_win": realized_r > 0.0,
        "exit_reason": trade.get("exit_reason", ""),
        "parent_regime_root": root if root in ROOTS else "",
        "parent_regime_confidence_floor": root_confidence.get(root, 0.0),
        "root_lookup_status": root_info["root_lookup_status"],
        "matched_source_date": root_info["matched_source_date"],
        "source_panel_support": root_info["support"],
        "source_panel_total": root_info["total"],
        "source_panel_share": root_info["panel_share"],
        "source_avg_confidence": root_info["source_avg_confidence"],
        "manipulation_overlay_state": "not_present_no_direct_source_match",
        "sub_regime_tags": sub_regime if root in ROOTS else "",
        "sub_sub_regime_or_profit_factor": SUB_SUB_FACTOR if root in ROOTS else "",
        "profit_factor_family": PROFIT_FAMILY if root in ROOTS else "",
        "profit_factor_leaf": PROFIT_LEAF if root in ROOTS else "",
        "regime_profit_branch_path": branch_path,
        "regime_profit_branch_path_version": "regime-profit-branch-path/v1",
        "trade_or_bar_horizon": "1h_entry_multi_day_exit",
        "allowed_action": "score_only_until_rc_spa_and_downstream_branch_consumption_pass",
        "suppression_rule": "suppress_if_direct_manipulation_overlay_present_or_crisis_tail_gate_fails",
    }


def _percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(math.floor((len(ordered) - 1) * ratio))))
    return ordered[idx]


def _max_drawdown(values: list[float]) -> float:
    running = 0.0
    peak = 0.0
    worst = 0.0
    for value in values:
        running += value
        peak = max(peak, running)
        worst = min(worst, running - peak)
    return abs(worst)


def _folds(rows: list[dict[str, Any]], fold_count: int = 4) -> list[list[dict[str, Any]]]:
    ordered = sorted(rows, key=lambda row: (row["entry_index"], row["exit_index"]))
    out: list[list[dict[str, Any]]] = []
    for idx in range(fold_count):
        start = round(len(ordered) * idx / fold_count)
        end = round(len(ordered) * (idx + 1) / fold_count)
        fold = ordered[start:end]
        if fold:
            out.append(fold)
    return out


def _bootstrap_lcb(values: list[float], samples: int = 2000) -> float:
    if not values:
        return 0.0
    # Deterministic linear congruential generator keeps this script dependency-light.
    state = 7
    means: list[float] = []
    n = len(values)
    for _ in range(samples):
        total = 0.0
        for _ in range(n):
            state = (1103515245 * state + 12345) % (2**31)
            total += values[state % n]
        means.append(total / n)
    return _percentile(means, 0.05)


def build_branch_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_root: dict[str, Any] = {}
    for root in ROOTS:
        root_rows = [row for row in rows if row["parent_regime_root"] == root]
        vals = [_safe_float(row["realized_R"]) for row in root_rows]
        stressed = [_safe_float(row["stressed_2x_cost_R"]) for row in root_rows]
        by_root[root] = {
            "trade_count": len(root_rows),
            "win_rate": sum(1 for value in vals if value > 0.0) / len(vals) if vals else 0.0,
            "net_return_R": sum(vals),
            "mean_R": mean(vals) if vals else 0.0,
            "bootstrap_edge_lcb_5pct": _bootstrap_lcb(vals) if vals else 0.0,
            "stressed_2x_cost_net_R": sum(stressed),
            "branch_path": root_rows[0]["regime_profit_branch_path"] if root_rows else "",
        }
    return by_root


def build_rc_spa(rows: list[dict[str, Any]], payoff: dict[str, Any], purged: dict[str, Any]) -> dict[str, Any]:
    values = [_safe_float(row["realized_R"]) for row in rows]
    stressed = [_safe_float(row["stressed_2x_cost_R"]) for row in rows]
    folds = _folds(rows, 4)
    fold_rows = []
    for index, fold in enumerate(folds):
        vals = [_safe_float(row["realized_R"]) for row in fold]
        stressed_vals = [_safe_float(row["stressed_2x_cost_R"]) for row in fold]
        fold_rows.append({
            "fold_index": index,
            "test_count": len(fold),
            "net_return_R": sum(vals),
            "positive": sum(vals) > 0.0,
            "stressed_2x_cost_net_R": sum(stressed_vals),
            "stressed_positive": sum(stressed_vals) > 0.0,
        })
    positive_rate = sum(1 for row in fold_rows if row["positive"]) / len(fold_rows) if fold_rows else 0.0
    min_trades_per_fold = min((row["test_count"] for row in fold_rows), default=0)
    edge_lcb = _bootstrap_lcb(values)
    cost_stress_survival = sum(stressed) > 0.0 and all(row["stressed_positive"] for row in fold_rows)
    pbo = _safe_float(purged.get("pbo"), 1.0)
    dsr = _safe_float(payoff.get("dsr"), 0.0)
    tail_loss = abs(_safe_float(payoff.get("tail_loss_p95"), 0.0))
    max_drawdown = _max_drawdown(values)
    branch_summary = build_branch_summary(rows)
    positive_branch_edges = [payload["mean_R"] for payload in branch_summary.values() if payload["trade_count"] > 0]
    best_edge = max(positive_branch_edges) if positive_branch_edges else 0.0
    other_edges = [edge for edge in positive_branch_edges if edge != best_edge]
    other_mean = mean(other_edges) if other_edges else 0.0
    if best_edge > 0.0 and other_mean <= 0.0:
        specificity_ratio = 999.0
    elif other_mean > 0.0:
        specificity_ratio = best_edge / other_mean
    else:
        specificity_ratio = 0.0

    hard_gates = {
        "accepted_regime_id_present": True,
        "branch_path_present": all(bool(row["regime_profit_branch_path"]) for row in rows),
        "root_lookup_coverage_full": all(row["parent_regime_root"] in ROOTS for row in rows),
        "min_total_trades": len(rows) >= 100,
        "min_test_folds": len(folds) >= 4,
        "min_trades_per_test_fold": min_trades_per_fold >= 10,
        "fold_positive_rate": positive_rate >= 0.75,
        "bootstrap_edge_lcb_5pct": edge_lcb > 0.0,
        "cost_stress_survival": cost_stress_survival,
        "pbo": pbo <= 0.25,
        "dsr": dsr > 0.0,
        "tail_loss_p95": tail_loss <= TAIL_LOSS_BUDGET,
        "regime_specificity_ratio": specificity_ratio >= 1.20,
    }
    branch_trade_depth_ok = all(
        payload["trade_count"] >= 100
        for payload in branch_summary.values()
        if payload["trade_count"] > 0
    )
    hard_gates["branch_min_total_trades_for_claimed_roots"] = branch_trade_depth_ok

    failure_reasons = [name for name, passed in hard_gates.items() if not passed]
    edge_score = max(0.0, min(1.0, edge_lcb / TARGET_EDGE))
    fold_score = positive_rate
    depth_score = max(0.0, min(1.0, len(rows) / 100.0))
    dsr_score = max(0.0, min(1.0, dsr / TARGET_DSR))
    pbo_score = 1.0 - max(0.0, min(1.0, pbo / 0.25))
    cost_score = 1.0 if cost_stress_survival else 0.0
    drawdown_score = 1.0 - max(0.0, min(1.0, max_drawdown / DRAWDOWN_BUDGET))
    specificity_score = max(0.0, min(1.0, (specificity_ratio - 1.0) / 0.5))
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
    if failure_reasons or rc_spa < 60.0:
        promotion = "reject"
    elif rc_spa < 75.0:
        promotion = "research_watch"
    elif rc_spa < 85.0:
        promotion = "stable_candidate"
    else:
        promotion = "pilot_candidate"
    return {
        "schema_version": "rc-spa/v1",
        "run_id": RUN_ID,
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "recipe_id": PROFIT_LEAF,
        "total_trades": len(rows),
        "test_folds": len(folds),
        "min_trades_per_test_fold": min_trades_per_fold,
        "fold_positive_rate": positive_rate,
        "bootstrap_edge_lcb_5pct": edge_lcb,
        "pbo": pbo,
        "dsr": dsr,
        "tail_loss_p95_abs": tail_loss,
        "tail_loss_budget_abs": TAIL_LOSS_BUDGET,
        "max_drawdown_R": max_drawdown,
        "regime_specificity_ratio": specificity_ratio,
        "cost_stress_survival": cost_stress_survival,
        "hard_gates": hard_gates,
        "failure_reasons": failure_reasons,
        "scores": {
            "edge_score": edge_score,
            "fold_score": fold_score,
            "depth_score": depth_score,
            "dsr_score": dsr_score,
            "pbo_score": pbo_score,
            "cost_score": cost_score,
            "drawdown_score": drawdown_score,
            "specificity_score": specificity_score,
        },
        "rc_spa": rc_spa,
        "promotion_level": promotion,
        "folds": fold_rows,
        "branch_summary": branch_summary,
    }


def write_rows(rows: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not rows:
        TRADES_CSV.write_text("", encoding="utf-8")
        TRADES_JSONL.write_text("", encoding="utf-8")
        LABELS_JSONL.write_text("", encoding="utf-8")
        return
    with TRADES_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with TRADES_JSONL.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=False) + "\n")
    with LABELS_JSONL.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps({
                "entry_index": row["entry_index"],
                "exit_index": row["exit_index"],
                "realized_R": row["realized_R"],
                "gross_R": row["gross_R"],
                "cost_R": row["cost_R"],
                "branch_path": row["regime_profit_branch_path"],
                "parent_regime_root": row["parent_regime_root"],
            }) + "\n")


def call_research_reports() -> tuple[dict[str, Any], dict[str, Any]]:
    payoff_cmd = [
        sys.executable,
        "scripts/research/factor_payoff_shape_report.py",
        "--candidate-id",
        PROFIT_LEAF,
        "--trades-jsonl",
        str(LABELS_JSONL),
        "--output-json",
        str(PAYOFF_JSON),
        "--nb-trials",
        str(NB_TRIALS),
        "--periods-per-year",
        "365",
    ]
    purged_cmd = [
        sys.executable,
        "scripts/research/purged_cv_backtest_guard.py",
        "--labels-jsonl",
        str(LABELS_JSONL),
        "--output-json",
        str(PURGED_JSON),
        "--nb-trials",
        str(NB_TRIALS),
        "--embargo-bars",
        "24",
        "--fold-count",
        "4",
    ]
    subprocess.run(payoff_cmd, check=True)
    subprocess.run(purged_cmd, check=True)
    return (
        json.loads(PAYOFF_JSON.read_text(encoding="utf-8")),
        json.loads(PURGED_JSON.read_text(encoding="utf-8")),
    )


def build_import_manifest(full_result: dict[str, Any]) -> dict[str, Any]:
    commit = subprocess.check_output(["git", "-C", str(AUTO_QUANT_ROOT), "rev-parse", "--short", "HEAD"], text=True).strip()
    return {
        "manifest_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "auto_quant_repo_url": str(AUTO_QUANT_ROOT),
        "auto_quant_pinned_ref": commit,
        "config_path": str(AUTO_QUANT_ROOT / "config.json"),
        "timeframe": "1h",
        "log_path": full_result["log_path"],
        "strategies": [
            {
                "name": PROFIT_LEAF,
                "file_path": str(STRATEGY_FILE),
                "metadata": {
                    "strategy": PROFIT_LEAF,
                    "mutation_id": "board-b-crashrebound-branch-rc-spa-v1",
                    "base_factor": "auto_quant_v0_4_1_crashrebound",
                    "hypothesis": "Counter-trend drawdown rebound after rolling drawdown, oversold confirmation, daily EMA slope-up, and volume confirmation.",
                    "paradigm": "counter-trend drawdown-rebound",
                    "expected_regime": "rooted_market_regime_context_then_drawdown_rebound_branch",
                    "factors_used": [
                        "market_regime_context.root",
                        "rolling_30d_drawdown",
                        "rsi14",
                        "ema200_1d_slope",
                        "volume_sma20",
                        "regime_profit_branch_path",
                    ],
                    "parent": "versions/0.4.1/CrashRebound",
                    "asset_class": "crypto_spot",
                    "status": "active",
                    "created": commit,
                },
                "status": "ok",
                "validation_metrics": full_result["aggregate_metrics"],
                "per_pair_metrics": full_result["per_pair_metrics"],
                "pairs": list(PAIR_BASKET),
                "timerange": "20210101-20251231",
                "commit": commit,
                "error": None,
            }
        ],
        "validation_errors": [],
    }


def write_report(summary: dict[str, Any], rc_spa: dict[str, Any], timerange_results: list[dict[str, Any]]) -> None:
    lines = [
        "# CrashRebound Branch RC-SPA v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Inputs",
        "",
        f"- Board B: `{BOARD_B}`",
        f"- Board A consumer map: `{BOARD_A_MAP}`",
        f"- Board A market context: `{BOARD_A_CONTEXT}`",
        f"- Auto-Quant root: `{AUTO_QUANT_ROOT}`",
        f"- Strategy file: `{STRATEGY_FILE}`",
        f"- Source regime CSV: `{SOURCE_REGIME_CSV}`",
        "",
        "## Auto-Quant Backtest Readback",
        "",
        "| Segment | Timerange | Trades | Win rate % | Profit % | Sharpe | Log |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for result in timerange_results:
        metrics = result["aggregate_metrics"]
        lines.append(
            f"| `{result['label']}` | `{result['timerange']}` | {metrics['trade_count']} | "
            f"{metrics['win_rate_pct']:.3f} | {metrics['total_profit_pct']:.3f} | "
            f"{metrics['sharpe']:.4f} | `{result['log_path']}` |"
        )
    lines.extend([
        "",
        "## Branch Summary",
        "",
        "| Root | Trades | Win rate % | Net R | Mean R | Edge LCB 5% | 2x cost net R | Branch path |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ])
    for root, payload in rc_spa["branch_summary"].items():
        lines.append(
            f"| `{root}` | {payload['trade_count']} | {_pct(payload['win_rate']):.3f} | "
            f"{payload['net_return_R']:.6f} | {payload['mean_R']:.6f} | "
            f"{payload['bootstrap_edge_lcb_5pct']:.6f} | {payload['stressed_2x_cost_net_R']:.6f} | "
            f"`{payload['branch_path']}` |"
        )
    lines.extend([
        "",
        "## RC-SPA Decision",
        "",
        f"- RC-SPA: `{rc_spa['rc_spa']:.3f}`",
        f"- Promotion level: `{rc_spa['promotion_level']}`",
        f"- Failure reasons: `{', '.join(rc_spa['failure_reasons']) if rc_spa['failure_reasons'] else 'none'}`",
        f"- Total trades: `{rc_spa['total_trades']}`",
        f"- Fold positive rate: `{rc_spa['fold_positive_rate']:.3f}`",
        f"- PBO: `{rc_spa['pbo']:.3f}`",
        f"- DSR: `{rc_spa['dsr']:.3f}`",
        f"- Tail loss abs p95: `{rc_spa['tail_loss_p95_abs']:.6f}` vs budget `{rc_spa['tail_loss_budget_abs']}`",
        "",
        "## Artifacts",
        "",
        f"- Trades CSV: `{TRADES_CSV}`",
        f"- Trades JSONL: `{TRADES_JSONL}`",
        f"- Labels JSONL: `{LABELS_JSONL}`",
        f"- Summary JSON: `{SUMMARY_JSON}`",
        f"- RC-SPA JSON: `{RC_SPA_JSON}`",
        f"- Payoff JSON: `{PAYOFF_JSON}`",
        f"- Purged CV JSON: `{PURGED_JSON}`",
        f"- Profitability packet: `{PACKET_JSON}`",
        f"- Import manifest: `{IMPORT_MANIFEST}`",
    ])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    for path in [OUT_DIR, CHECK_DIR, LOG_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    if not STRATEGY_FILE.exists():
        raise FileNotFoundError(STRATEGY_FILE)
    if not SOURCE_REGIME_CSV.exists():
        raise FileNotFoundError(SOURCE_REGIME_CSV)

    timerange_results = [run_backtest(label, timerange) for label, timerange in TIMERANGES]
    full_result = next(result for result in timerange_results if result["label"] == "full_5y")
    lookup = SourceRegimeLookup(SOURCE_REGIME_CSV)
    root_confidence = load_root_confidence()
    rows = [trade_to_row(trade, lookup, root_confidence) for trade in full_result["trades"]]
    write_rows(rows)
    payoff, purged = call_research_reports()
    rc_spa = build_rc_spa(rows, payoff, purged)

    summary = {
        "schema_version": "board-b-crashrebound-branch-summary/v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "board_b": str(BOARD_B),
            "board_a_map": str(BOARD_A_MAP),
            "board_a_context": str(BOARD_A_CONTEXT),
            "source_regime_csv": str(SOURCE_REGIME_CSV),
            "auto_quant_root": str(AUTO_QUANT_ROOT),
            "strategy_file": str(STRATEGY_FILE),
        },
        "timerange_results": [
            {k: v for k, v in result.items() if k != "trades"}
            for result in timerange_results
        ],
        "full_5y_trade_count": len(rows),
        "root_coverage": {
            root: sum(1 for row in rows if row["parent_regime_root"] == root)
            for root in ROOTS
        },
        "root_lookup_status_counts": pd.Series([row["root_lookup_status"] for row in rows]).value_counts().to_dict() if rows else {},
        "manipulation_overlay_state": "not_present_no_direct_source_match",
    }
    branch_packet = {
        "schema_version": "regime-profitability-packet/v1",
        "run_id": RUN_ID,
        "accepted_regime_id": rc_spa["accepted_regime_id"],
        "recipe_id": PROFIT_LEAF,
        "recipe_artifact_path": str(STRATEGY_FILE),
        "backtest_artifact_path": str(TRADES_CSV),
        "total_trades": rc_spa["total_trades"],
        "test_folds": rc_spa["test_folds"],
        "fold_positive_rate": rc_spa["fold_positive_rate"],
        "bootstrap_edge_lcb_5pct": rc_spa["bootstrap_edge_lcb_5pct"],
        "pbo": rc_spa["pbo"],
        "dsr": rc_spa["dsr"],
        "cost_stress_result": "pass" if rc_spa["cost_stress_survival"] else "fail",
        "tail_loss_p95": rc_spa["tail_loss_p95_abs"],
        "regime_specificity_ratio": rc_spa["regime_specificity_ratio"],
        "rc_spa": rc_spa["rc_spa"],
        "promotion_level": rc_spa["promotion_level"],
        "downstream_consumption_status": "not_started_rc_spa_rejected",
        "branch_summary": rc_spa["branch_summary"],
        "hard_gates": rc_spa["hard_gates"],
        "failure_reasons": rc_spa["failure_reasons"],
    }
    import_manifest = build_import_manifest(full_result)

    _write_json(SUMMARY_JSON, summary)
    _write_json(RC_SPA_JSON, rc_spa)
    _write_json(PACKET_JSON, branch_packet)
    _write_json(IMPORT_MANIFEST, import_manifest)
    write_report(summary, rc_spa, timerange_results)

    assertion_lines = [
        f"run_id={RUN_ID}",
        f"strategy=CrashRebound",
        f"auto_quant_backtest_full_5y_trades={len(rows)}",
        f"branch_path_present={rc_spa['hard_gates']['branch_path_present']}",
        f"root_lookup_coverage_full={rc_spa['hard_gates']['root_lookup_coverage_full']}",
        f"rc_spa={rc_spa['rc_spa']:.6f}",
        f"promotion_level={rc_spa['promotion_level']}",
        f"failure_reasons={','.join(rc_spa['failure_reasons'])}",
        f"trades_csv={TRADES_CSV}",
        f"packet_json={PACKET_JSON}",
        f"import_manifest={IMPORT_MANIFEST}",
    ]
    ASSERTIONS.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "run_id": RUN_ID,
        "trades": len(rows),
        "rc_spa": rc_spa["rc_spa"],
        "promotion_level": rc_spa["promotion_level"],
        "failure_reasons": rc_spa["failure_reasons"],
        "report": str(REPORT_MD),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
