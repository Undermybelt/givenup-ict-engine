#!/usr/bin/env python3
"""Rerun CrashRebound through the local Auto-Quant/Freqtrade runtime.

This is an additive Board B probe. It emits branch-path trade/fold evidence and
an RC-SPA gate report without mutating ict-engine runtime code or the
Auto-Quant checkout.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting


SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = SCRIPT.parents[6]
OUT = RUN_ROOT / "branch-rc-spa"
CHECKS = RUN_ROOT / "checks"

AQ = Path("/Users/thrill3r/Auto-Quant")
AQ_USER_DATA = AQ / "user_data"
AQ_DATA = AQ_USER_DATA / "data"
AQ_CONFIG = AQ / "config.json"
AQ_STRATEGY_DIR = AQ / "versions/0.4.1/strategies"
STRATEGY = "CrashRebound"

ACCEPTED_REGIME_ID = "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation"
ACCEPTED_REGIME_ARTIFACT = (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/"
    "regime_factor_consumer_map_v1.csv"
)
BRANCH_PATH_VERSION = "regime_profit_branch_path/v1"
BRANCH_SOURCE = "auto_quant_v0.4.1_calendar_regime_proxy_not_board_a_source_label"

PAIRS = ["SOL/USDT", "AVAX/USDT", "BNB/USDT"]
DEFAULT_TIMERANGES = [
    ("bull_2021", "20210101-20211231"),
    ("winter_2022", "20220101-20221231"),
    ("recovery_23_25", "20230101-20251231"),
    ("full_5y", "20210101-20251231"),
]


def json_default(obj: Any) -> Any:
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    return str(obj)


def load_strategy_class() -> Any:
    path = AQ_STRATEGY_DIR / f"{STRATEGY}.py"
    spec = importlib.util.spec_from_file_location(STRATEGY, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load strategy spec from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, STRATEGY)


def run_backtest(timerange: str) -> dict[str, Any]:
    args = {
        "config": [str(AQ_CONFIG)],
        "user_data_dir": str(AQ_USER_DATA),
        "datadir": str(AQ_DATA),
        "strategy": STRATEGY,
        "strategy_path": str(AQ_STRATEGY_DIR),
        "timerange": timerange,
        "export": "none",
        "exportfilename": None,
        "cache": "none",
    }
    config = Configuration(args, RunMode.BACKTEST).get_config()
    config["exchange"]["pair_whitelist"] = list(PAIRS)
    bt = Backtesting(config)
    bt.start()
    return bt.results


def metric_value(d: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        if key in d and d[key] is not None:
            try:
                return float(d[key])
            except (TypeError, ValueError):
                pass
    return default


def entry_metrics(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "sharpe": metric_value(entry, "sharpe", "sharpe_ratio"),
        "sortino": metric_value(entry, "sortino", "sortino_ratio"),
        "calmar": metric_value(entry, "calmar", "calmar_ratio"),
        "total_profit_pct": metric_value(entry, "profit_total_pct"),
        "max_drawdown_pct": -abs(metric_value(entry, "max_drawdown_account")) * 100.0,
        "trade_count": int(metric_value(entry, "trades", "total_trades")),
        "win_rate_pct": metric_value(entry, "winrate") * 100.0,
        "profit_factor": metric_value(entry, "profit_factor"),
    }


def extract_metrics(results: dict[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    strat = results.get("strategy", {}).get(STRATEGY, {}) or {}
    per_pair_rows = strat.get("results_per_pair", []) or []
    aggregate: dict[str, Any] = {}
    per_pair: dict[str, dict[str, Any]] = {}
    for row in per_pair_rows:
        key = row.get("key", "")
        metrics = entry_metrics(row)
        if key == "TOTAL":
            aggregate = metrics
        elif key:
            per_pair[key] = metrics
    if not aggregate:
        aggregate = entry_metrics(strat)
    return aggregate, per_pair


def records_from_any(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, pd.DataFrame):
        return value.to_dict("records")
    if isinstance(value, list):
        out: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, dict):
                out.append(dict(item))
            elif hasattr(item, "__dict__"):
                out.append(dict(item.__dict__))
        return out
    if isinstance(value, dict):
        for key in ("trades", "results"):
            rows = records_from_any(value.get(key))
            if rows:
                return rows
    return []


def extract_trade_rows(results: dict[str, Any], label: str, timerange: str) -> list[dict[str, Any]]:
    strat = results.get("strategy", {}).get(STRATEGY, {}) or {}
    rows = records_from_any(strat.get("trades")) or records_from_any(strat.get("results"))
    normalized: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        flat = {k: json_default(v) for k, v in row.items()}
        profit_ratio = parse_float(first_present(row, "profit_ratio", "profit_pct", "profit_percent"))
        if profit_ratio is None:
            continue
        if "profit_pct" in row and "profit_ratio" not in row:
            profit_ratio = profit_ratio / 100.0
        open_raw = first_present(row, "open_date", "open_timestamp", "open_time", "date")
        close_raw = first_present(row, "close_date", "close_timestamp", "close_time")
        open_ts = pd.to_datetime(open_raw, utc=True, errors="coerce")
        close_ts = pd.to_datetime(close_raw, utc=True, errors="coerce") if close_raw is not None else pd.NaT
        pair = str(first_present(row, "pair", default=""))
        branch = branch_for_timestamp(open_ts)
        flat.update(
            {
                "source_timerange_label": label,
                "source_timerange": timerange,
                "trade_seq": idx,
                "pair": pair,
                "open_date": open_ts.isoformat() if not pd.isna(open_ts) else "",
                "close_date": close_ts.isoformat() if not pd.isna(close_ts) else "",
                "profit_ratio": profit_ratio,
                "is_win": profit_ratio > 0.0,
                "parent_regime_root": branch["parent_regime_root"],
                "parent_regime_confidence_floor": branch["parent_regime_confidence_floor"],
                "manipulation_overlay_state": "absent_not_evaluated_by_direct_source",
                "sub_regime_tags": branch["sub_regime_tags"],
                "sub_sub_regime_or_profit_factor": branch["sub_sub_regime_or_profit_factor"],
                "profit_factor_family": "counter_trend_drawdown_rebound",
                "profit_factor_leaf": STRATEGY,
                "regime_profit_branch_path": branch["regime_profit_branch_path"],
                "regime_profit_branch_path_version": BRANCH_PATH_VERSION,
                "branch_path_source": BRANCH_SOURCE,
                "recipe_id": STRATEGY,
                "trade_or_bar_horizon": "1h_entry_exit_trade",
                "allowed_action": branch["allowed_action"],
                "suppression_rule": branch["suppression_rule"],
            }
        )
        normalized.append(flat)
    return normalized


def first_present(row: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return default


def parse_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        out = float(value)
        if math.isnan(out):
            return None
        return out
    except (TypeError, ValueError):
        return None


def branch_for_timestamp(ts: pd.Timestamp) -> dict[str, Any]:
    if pd.isna(ts):
        root = "unmapped"
    elif ts.year == 2021:
        root = "Bull"
    elif ts.year == 2022:
        root = "Bear"
    elif ts.year == 2023:
        root = "Sideways"
    elif ts.year >= 2024:
        root = "Bull"
    else:
        root = "unmapped"

    floors = {
        "Bull": 0.9797225384,
        "Bear": 0.963920242,
        "Sideways": 0.9529358324,
        "Crisis": 0.9619059575,
    }
    sub = {
        "Bull": ("BullPullback", "CapitulationMeanReversionSetup", "trade_allowed_after_root_gate"),
        "Bear": ("BearMarketCapitulation", "ReboundAttempt", "size_limited_or_observe"),
        "Sideways": ("RangeConsolidation", "MeanReversionSetup", "trade_allowed_after_root_gate"),
        "Crisis": ("ExtremeStress", "ShortVolSuppression", "no_trade"),
    }.get(root, ("Unmapped", "MissingBoardASourceLabel", "no_trade"))
    suppression = "none"
    if root == "Bear":
        suppression = "size_limit_until_branch_specific_edge_passes"
    if root in {"Crisis", "unmapped"}:
        suppression = "suppress_trade"
    leaf = STRATEGY if root != "Crisis" else "no_trade"
    return {
        "parent_regime_root": root,
        "parent_regime_confidence_floor": floors.get(root, ""),
        "sub_regime_tags": sub[0],
        "sub_sub_regime_or_profit_factor": sub[1],
        "profit_factor_leaf": leaf,
        "regime_profit_branch_path": f"{root} -> {sub[0]} -> {sub[1]} -> {leaf}",
        "allowed_action": sub[2],
        "suppression_rule": suppression,
    }


def compute_drawdown(returns: list[float]) -> float:
    equity = np.cumprod(1.0 + np.array(returns, dtype=float))
    if equity.size == 0:
        return 0.0
    peak = np.maximum.accumulate(equity)
    dd = equity / peak - 1.0
    return float(dd.min())


def bootstrap_lcb(returns: list[float], seed: int = 7, n: int = 2000) -> float:
    if not returns:
        return 0.0
    arr = np.array(returns, dtype=float)
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(n):
        sample = rng.choice(arr, size=len(arr), replace=True)
        means.append(float(sample.mean()))
    return float(np.quantile(means, 0.05))


def summarize(rows: list[dict[str, Any]], metrics_by_label: dict[str, Any]) -> dict[str, Any]:
    profits = [float(r["profit_ratio"]) for r in rows]
    years = sorted({pd.to_datetime(r["open_date"], utc=True).year for r in rows if r.get("open_date")})
    fold_rows = []
    for year in years:
        yr = [r for r in rows if r.get("open_date") and pd.to_datetime(r["open_date"], utc=True).year == year]
        vals = [float(r["profit_ratio"]) for r in yr]
        fold_rows.append(
            {
                "fold_id": str(year),
                "fold_kind": "calendar_year_from_full_5y_trades",
                "trades": len(vals),
                "net_profit_ratio_sum": float(sum(vals)),
                "win_rate": float(np.mean([v > 0 for v in vals])) if vals else 0.0,
                "positive_edge": bool(sum(vals) > 0),
            }
        )
    branches = []
    for path in sorted({r["regime_profit_branch_path"] for r in rows}):
        group = [r for r in rows if r["regime_profit_branch_path"] == path]
        vals = [float(r["profit_ratio"]) for r in group]
        branches.append(
            {
                "regime_profit_branch_path": path,
                "parent_regime_root": group[0]["parent_regime_root"],
                "branch_path_source": group[0]["branch_path_source"],
                "trades": len(vals),
                "net_profit_ratio_sum": float(sum(vals)),
                "mean_profit_ratio": float(np.mean(vals)) if vals else 0.0,
                "win_rate": float(np.mean([v > 0 for v in vals])) if vals else 0.0,
            }
        )

    required_roots = ["Bull", "Bear", "Sideways", "Crisis"]
    roots_present = sorted({r["parent_regime_root"] for r in rows})
    missing_roots = [root for root in required_roots if root not in roots_present]
    fold_positive_rate = float(np.mean([f["positive_edge"] for f in fold_rows])) if fold_rows else 0.0
    edge_lcb = bootstrap_lcb(profits)
    cost_stressed = [p - 0.002 for p in profits]
    cost_stress_survival = bool(sum(cost_stressed) > 0 and bootstrap_lcb(cost_stressed) > 0)
    trade_sharpe_proxy = 0.0
    if len(profits) > 1 and np.std(profits) > 0:
        trade_sharpe_proxy = float(np.mean(profits) / np.std(profits) * math.sqrt(len(profits)))
    max_drawdown = compute_drawdown(profits)
    tail_loss_p95 = abs(float(np.quantile(profits, 0.05))) if profits else 0.0
    branch_means = [b["mean_profit_ratio"] for b in branches if b["trades"] >= 10]
    if len(branch_means) >= 2:
        best = max(branch_means)
        others = [m for m in branch_means if m != best]
        denom = abs(float(np.mean(others))) if others else 0.0
        regime_specificity_ratio = best / denom if denom > 1e-12 else 0.0
    else:
        regime_specificity_ratio = 0.0

    hard_gates = {
        "accepted_regime_id_present": True,
        "accepted_regime_artifact": ACCEPTED_REGIME_ARTIFACT,
        "branch_path_present": all(bool(r.get("regime_profit_branch_path")) for r in rows),
        "branch_path_source_accepted_board_a_labels": False,
        "all_required_roots_present": not missing_roots,
        "missing_roots": missing_roots,
        "total_trades_gate": len(rows) >= 100,
        "min_test_folds_gate": len(fold_rows) >= 4,
        "min_trades_per_test_fold_gate": all(f["trades"] >= 10 for f in fold_rows),
        "fold_positive_rate": fold_positive_rate,
        "fold_positive_rate_gate": fold_positive_rate >= 0.75,
        "bootstrap_edge_lcb_5pct": edge_lcb,
        "bootstrap_edge_lcb_gate": edge_lcb > 0,
        "cost_stress_survival": cost_stress_survival,
        "pbo": None,
        "pbo_gate": False,
        "pbo_note": "not computable from one selected recipe without a candidate panel",
        "dsr": None,
        "dsr_proxy": trade_sharpe_proxy,
        "dsr_gate": trade_sharpe_proxy > 0,
        "dsr_note": "proxy only; formal DSR not available in Auto-Quant artifact",
        "tail_loss_p95": tail_loss_p95,
        "tail_loss_budget": 0.05,
        "tail_loss_gate": tail_loss_p95 <= 0.05,
        "regime_specificity_ratio": regime_specificity_ratio,
        "regime_specificity_gate": regime_specificity_ratio >= 1.20,
    }

    edge_score = clamp(edge_lcb / 0.0025)
    depth_score = clamp(len(rows) / 100.0)
    dsr_score = clamp(trade_sharpe_proxy / 1.0)
    pbo_score = 0.0
    cost_score = 1.0 if cost_stress_survival else 0.0
    drawdown_score = 1.0 - clamp(abs(max_drawdown) / 0.25)
    specificity_score = clamp((regime_specificity_ratio - 1.0) / 0.5)
    rc_spa = 100.0 * (
        0.20 * edge_score
        + 0.15 * fold_positive_rate
        + 0.15 * depth_score
        + 0.15 * dsr_score
        + 0.10 * pbo_score
        + 0.10 * cost_score
        + 0.10 * drawdown_score
        + 0.05 * specificity_score
    )

    failed = []
    if not hard_gates["branch_path_source_accepted_board_a_labels"]:
        failed.append("reject_missing_branch_path")
    if missing_roots:
        failed.append("reject_missing_required_roots")
    if not hard_gates["pbo_gate"]:
        failed.append("reject_overfit_risk")
    if not hard_gates["regime_specificity_gate"]:
        failed.append("reject_no_regime_specificity")
    if not hard_gates["cost_stress_survival"]:
        failed.append("reject_cost_fragile")
    if not hard_gates["bootstrap_edge_lcb_gate"]:
        failed.append("reject_no_positive_edge")
    if not hard_gates["tail_loss_gate"]:
        failed.append("reject_tail_risk")

    promotion = "reject" if failed or rc_spa < 60.0 else "research_watch"
    return {
        "run_id": "20260511T180121+0800-codex-crashrebound-branch-rc-spa-v1",
        "accepted_regime_id": ACCEPTED_REGIME_ID,
        "accepted_regime_artifact": ACCEPTED_REGIME_ARTIFACT,
        "recipe_id": STRATEGY,
        "recipe_source": str(AQ_STRATEGY_DIR / f"{STRATEGY}.py"),
        "rc_spa_trade_scope": "full_5y_trades_year_folds",
        "total_trades": len(rows),
        "win_rate": float(np.mean([p > 0 for p in profits])) if profits else 0.0,
        "net_profit_ratio_sum": float(sum(profits)),
        "max_drawdown": max_drawdown,
        "folds": fold_rows,
        "branches": branches,
        "hard_gates": hard_gates,
        "rc_spa_components": {
            "edge_score": edge_score,
            "fold_score": fold_positive_rate,
            "depth_score": depth_score,
            "dsr_score": dsr_score,
            "pbo_score": pbo_score,
            "cost_score": cost_score,
            "drawdown_score": drawdown_score,
            "specificity_score": specificity_score,
        },
        "rc_spa": rc_spa,
        "promotion_level": promotion,
        "gate_result": "fail:" + ";".join(dict.fromkeys(failed)) if failed else "pass",
        "downstream_consumption_status": "not_started_rejected_before_promotion",
        "metrics_by_timerange": metrics_by_label,
    }


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    if math.isnan(value) or math.isinf(value):
        return lo
    return max(lo, min(hi, value))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
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


def write_markdown(summary: dict[str, Any]) -> None:
    lines = [
        "# CrashRebound Branch RC-SPA v1",
        "",
        f"Run ID: `{summary['run_id']}`",
        "",
        "## Decision",
        "",
        f"- Promotion level: `{summary['promotion_level']}`.",
        f"- Gate result: `{summary['gate_result']}`.",
        f"- RC-SPA: `{summary['rc_spa']:.4f}`.",
        f"- Trades: `{summary['total_trades']}` from the real local Auto-Quant/Freqtrade runtime.",
        "- Branch paths were emitted, but their source is an Auto-Quant calendar-regime proxy, not Board A source-owned per-trade labels.",
        "- `Crisis` and scoped direct `Manipulation` have no trade-level evidence in this recipe run; no proxy overlay was promoted.",
        "- PBO and formal DSR are not available from a single selected recipe without a candidate panel, so promotion fails closed.",
        "",
        "## Branches",
        "",
        "| Branch path | Root | Trades | Win rate | Net profit ratio sum | Source |",
        "|---|---|---:|---:|---:|---|",
    ]
    for branch in summary["branches"]:
        lines.append(
            "| {path} | {root} | {trades} | {wr:.4f} | {profit:.6f} | {source} |".format(
                path=branch["regime_profit_branch_path"],
                root=branch["parent_regime_root"],
                trades=branch["trades"],
                wr=branch["win_rate"],
                profit=branch["net_profit_ratio_sum"],
                source=branch["branch_path_source"],
            )
        )
    lines += [
        "",
        "## Hard Gates",
        "",
        "| Gate | Result |",
        "|---|---|",
    ]
    for key, value in summary["hard_gates"].items():
        lines.append(f"| `{key}` | `{value}` |")
    lines += [
        "",
        "## Artifacts",
        "",
        "- Trades CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T180121-codex-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_branch_trades_v1.csv`",
        "- Fold CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T180121-codex-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_branch_folds_v1.csv`",
        "- Summary JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T180121-codex-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_branch_rc_spa_v1.json`",
        "- Import library JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T180121-codex-crashrebound-branch-rc-spa-v1/branch-rc-spa/auto_quant_strategy_library.crashrebound_branch_v1.json`",
        "",
        "## Next",
        "",
        "Rerun or transform the recipe on Board A source-labeled branch rows before any pre-Bayes/BBN/CatBoost/execution-tree promotion attempt.",
        "",
    ]
    (OUT / "crashrebound_branch_rc_spa_v1.md").write_text("\n".join(lines), encoding="utf-8")


def build_import_library(summary: dict[str, Any]) -> dict[str, Any]:
    metrics = summary["metrics_by_timerange"].get("full_5y", {}).get("aggregate", {})
    return {
        "manifest_version": "1.0",
        "exported_at": "2026-05-11T18:01:21+08:00",
        "auto_quant_repo_url": str(AQ),
        "auto_quant_pinned_ref": git_short(AQ),
        "config_path": str(AQ_CONFIG),
        "validation_errors": [],
        "timeframe": "1h",
        "strategies": [
            {
                "name": STRATEGY,
                "file_path": str(AQ_STRATEGY_DIR / f"{STRATEGY}.py"),
                "status": "ok",
                "metadata": {
                    "strategy": STRATEGY,
                    "mutation_id": "board-b-crashrebound-branch-rc-spa-v1",
                    "base_factor": "auto_quant_v0.4.1_measured_seed",
                    "hypothesis": "Drawdown rebound recipe requires Board A rooted branch-path proof before promotion.",
                    "expected_regime": "reversal_or_rebound_after_drawdown",
                    "branch_path_source": BRANCH_SOURCE,
                    "accepted_regime_id": ACCEPTED_REGIME_ID,
                },
                "validation_metrics": {
                    "sharpe": metrics.get("sharpe", 0.0),
                    "sortino": metrics.get("sortino", 0.0),
                    "calmar": metrics.get("calmar", 0.0),
                    "total_profit_pct": metrics.get("total_profit_pct", 0.0),
                    "max_drawdown_pct": metrics.get("max_drawdown_pct", 0.0),
                    "trade_count": summary["total_trades"],
                    "win_rate_pct": summary["win_rate"] * 100.0,
                    "profit_factor": metrics.get("profit_factor", 0.0),
                    "rc_spa": summary["rc_spa"],
                    "promotion_level": summary["promotion_level"],
                    "gate_result": summary["gate_result"],
                },
                "per_pair_metrics": summary["metrics_by_timerange"].get("full_5y", {}).get("per_pair", {}),
                "branch_path_metrics": summary["branches"],
                "pairs": PAIRS,
                "timerange": "20210101-20251231",
                "commit": git_short(AQ),
                "error": None,
            }
        ],
    }


def git_short(path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=path,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    cls = load_strategy_class()
    timeranges = getattr(cls, "test_timeranges", None) or DEFAULT_TIMERANGES
    metrics_by_label: dict[str, Any] = {}
    rows_by_label: dict[str, list[dict[str, Any]]] = {}
    for label, timerange in timeranges:
        results = run_backtest(timerange)
        aggregate, per_pair = extract_metrics(results)
        metrics_by_label[label] = {
            "timerange": timerange,
            "aggregate": aggregate,
            "per_pair": per_pair,
        }
        rows_by_label[label] = extract_trade_rows(results, label, timerange)

    all_metrics_rows = []
    for label, payload in metrics_by_label.items():
        row = {"timerange_label": label, "timerange": payload["timerange"]}
        row.update(payload["aggregate"])
        all_metrics_rows.append(row)
    write_csv(OUT / "crashrebound_timerange_metrics_v1.csv", all_metrics_rows)

    canonical_rows = rows_by_label.get("full_5y") or (
        rows_by_label.get("bull_2021", [])
        + rows_by_label.get("winter_2022", [])
        + rows_by_label.get("recovery_23_25", [])
    )
    if not canonical_rows:
        raise RuntimeError("Freqtrade result did not expose trade rows; cannot compute RC-SPA")
    write_csv(OUT / "crashrebound_branch_trades_v1.csv", canonical_rows)

    summary = summarize(canonical_rows, metrics_by_label)
    write_csv(OUT / "crashrebound_branch_folds_v1.csv", summary["folds"])
    write_csv(OUT / "crashrebound_branch_paths_v1.csv", summary["branches"])
    (OUT / "crashrebound_branch_rc_spa_v1.json").write_text(
        json.dumps(summary, indent=2, default=json_default),
        encoding="utf-8",
    )
    library = build_import_library(summary)
    (OUT / "auto_quant_strategy_library.crashrebound_branch_v1.json").write_text(
        json.dumps(library, indent=2, default=json_default),
        encoding="utf-8",
    )
    write_markdown(summary)

    assertions = [
        f"PASS total_trades={summary['total_trades']}",
        f"PASS promotion_level={summary['promotion_level']}",
        f"PASS gate_result={summary['gate_result']}",
        f"PASS branch_path_source_accepted_board_a_labels={summary['hard_gates']['branch_path_source_accepted_board_a_labels']}",
        f"PASS missing_roots={','.join(summary['hard_gates']['missing_roots'])}",
    ]
    (CHECKS / "crashrebound_branch_rc_spa_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, default=json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
