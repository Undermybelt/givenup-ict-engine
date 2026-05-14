#!/usr/bin/env python3
"""Board B Tomac NQ branch RC-SPA readback.

This is an additive experiment artifact. It uses the existing Auto-Quant
Tomac NQ strategy and synthetic-pair runner, attaches Board A source-root
labels from the local source panel, and writes branch-path evidence without
modifying ict-engine runtime code or the Auto-Quant checkout.
"""

from __future__ import annotations

import contextlib
import csv
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting


RUN_ID = "20260511T183756+0800-codex-board-b-tomac-nq-branch-rc-spa-v1"
SCHEMA_VERSION = "board-b-tomac-nq-branch-rc-spa/v1"
STRATEGY_NAME = "TomacNQ_KillzoneBreakout"
PAIR = "NQ/USD"
SOURCE_TICKER = "^IXIC"
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
TIMERANGES = [
    ("full_2011_2025", "20110101-20251231"),
    ("fold_2011_2014", "20110101-20141231"),
    ("fold_2015_2018", "20150101-20181231"),
    ("fold_2019_2021", "20190101-20211231"),
    ("fold_2022_2023", "20220101-20231231"),
    ("fold_2024_2025", "20240101-20251231"),
]

EXTRA_ROUND_TRIP_COST = 0.002
MIN_TOTAL_TRADES = 100
MIN_TEST_FOLDS = 4
MIN_TRADES_PER_FOLD = 10
FOLD_POSITIVE_RATE_MIN = 0.75
TARGET_DSR = 1.0


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot find repo root from {start}")


RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = find_repo_root(Path(__file__).resolve())
AUTO_QUANT_ROOT = Path("/Users/thrill3r/Auto-Quant")
AUTO_QUANT_USER_DATA = AUTO_QUANT_ROOT / "user_data"
AUTO_QUANT_DATA = AUTO_QUANT_USER_DATA / "data"
AUTO_QUANT_CONFIG = AUTO_QUANT_ROOT / "config.tomac.json"
AUTO_QUANT_STRATEGIES = AUTO_QUANT_USER_DATA / "strategies_external"
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
BOARD_B = REPO_ROOT / "docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md"

OUT_DIR = RUN_ROOT / "branch-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"
LOG_DIR = RUN_ROOT / "logs"
TRADES_CSV = OUT_DIR / "tomac_nq_branch_trades_v1.csv"
SUMMARY_CSV = OUT_DIR / "tomac_nq_branch_rc_spa_summary_v1.csv"
TIMERANGE_CSV = OUT_DIR / "tomac_nq_timerange_summaries_v1.csv"
REPORT_JSON = OUT_DIR / "tomac_nq_branch_rc_spa_report_v1.json"
REPORT_MD = OUT_DIR / "tomac_nq_branch_rc_spa_report_v1.md"
ASSERTIONS = CHECK_DIR / "tomac_nq_branch_rc_spa_v1_assertions.out"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def setup_imports() -> None:
    sys.path.insert(0, str(AUTO_QUANT_ROOT))


def load_tomac_runner():
    setup_imports()
    import run_tomac  # type: ignore

    return run_tomac


def build_config(timerange: str) -> dict[str, Any]:
    base = json.loads(AUTO_QUANT_CONFIG.read_text(encoding="utf-8"))
    base["exchange"]["pair_whitelist"] = [PAIR]
    base["exchange"]["skip_pair_validation"] = True
    base["stake_currency"] = "USD"
    base["timerange"] = timerange
    base["max_open_trades"] = 1
    args = {
        "config": [str(AUTO_QUANT_CONFIG)],
        "user_data_dir": str(AUTO_QUANT_USER_DATA),
        "datadir": str(AUTO_QUANT_DATA),
        "strategy": STRATEGY_NAME,
        "strategy_path": str(AUTO_QUANT_STRATEGIES),
        "timerange": timerange,
        "export": "none",
        "exportfilename": None,
        "cache": "none",
    }
    config = Configuration(args, RunMode.BACKTEST).get_config()
    for key, value in base.items():
        if key != "exchange":
            config[key] = value
    config["exchange"].update(base["exchange"])
    config["pairlists"] = [{"method": "StaticPairList"}]
    return config


def run_backtest(label: str, timerange: str) -> dict[str, Any]:
    run_tomac = load_tomac_runner()
    config = build_config(timerange)
    log_path = LOG_DIR / f"freqtrade_backtest_{label}.out"
    err_path = LOG_DIR / f"freqtrade_backtest_{label}.err"
    with log_path.open("w", encoding="utf-8") as out, err_path.open("w", encoding="utf-8") as err:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            exchange = run_tomac._build_exchange_with_synthetic_pairs(config)
            bt = Backtesting(config, exchange=exchange)
            bt.start()
    strategy_result = bt.results.get("strategy", {}).get(STRATEGY_NAME, {}) or {}
    metrics = run_tomac.extract_metrics(bt.results, STRATEGY_NAME)
    return {
        "label": label,
        "timerange": timerange,
        "log_path": rel(log_path),
        "stderr_path": rel(err_path),
        "aggregate_metrics": metrics["aggregate"],
        "per_pair_metrics": metrics["per_pair"],
        "trades": strategy_result.get("trades", []) or [],
        "backtest_start": str(strategy_result.get("backtest_start", "")),
        "backtest_end": str(strategy_result.get("backtest_end", "")),
    }


def load_source_roots() -> pd.DataFrame:
    df = pd.read_csv(
        SOURCE_REGIME_CSV,
        usecols=["date", "ticker", "regime_label", "regime_confidence"],
        parse_dates=["date"],
    )
    df = df[df["ticker"] == SOURCE_TICKER].copy()
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    df["parent_regime_root"] = df["regime_label"].map(
        lambda value: value if value in ROOTS else "Crisis"
    )
    return df.sort_values("date").reset_index(drop=True)


class RootLookup:
    def __init__(self, source: pd.DataFrame) -> None:
        self.dates = source["date"].to_numpy(dtype="datetime64[ns]")
        self.roots = source["parent_regime_root"].to_numpy()
        self.confidence = source["regime_confidence"].to_numpy()

    def lookup(self, value: Any) -> dict[str, Any]:
        date = pd.Timestamp(value).tz_localize(None).normalize().to_datetime64()
        pos = int(np.searchsorted(self.dates, date, side="right") - 1)
        if pos < 0:
            return {
                "parent_regime_root": "Unlabeled",
                "parent_regime_confidence_floor": 0.0,
                "root_lookup_status": "missing_before_source_panel",
            }
        return {
            "parent_regime_root": str(self.roots[pos]),
            "parent_regime_confidence_floor": float(self.confidence[pos]),
            "root_lookup_status": "source_ticker_asof_daily",
        }


def branch_path(root: str) -> str:
    if root == "Bull":
        return f"{root} -> TrendExpansion -> TomacKillzoneBreakout -> {STRATEGY_NAME}"
    if root == "Bear":
        return f"{root} -> BearMarketDrawdown -> TomacKillzoneBreakout -> {STRATEGY_NAME}"
    if root == "Sideways":
        return f"{root} -> RangeConsolidation -> TomacKillzoneBreakout -> {STRATEGY_NAME}"
    if root == "Crisis":
        return f"{root} -> ExtremeStress -> TomacKillzoneBreakout -> {STRATEGY_NAME}"
    return "Manipulation(scoped) -> DirectEventOverlayMissing -> no_direct_event_rows -> suppress_or_abstain"


def clean_trade(trade: dict[str, Any], lookup: RootLookup) -> dict[str, Any]:
    open_date = pd.Timestamp(trade["open_date"])
    close_date = pd.Timestamp(trade["close_date"])
    root = lookup.lookup(open_date)
    profit_ratio = float(trade.get("profit_ratio", 0.0) or 0.0)
    parent_root = root["parent_regime_root"]
    return {
        "run_id": RUN_ID,
        "recipe_id": STRATEGY_NAME,
        "pair": str(trade.get("pair", "")),
        "open_date": open_date.isoformat(),
        "close_date": close_date.isoformat(),
        "profit_ratio": profit_ratio,
        "net_return_R": profit_ratio,
        "win": profit_ratio > 0,
        "exit_reason": str(trade.get("exit_reason", "")),
        "trade_duration_min": float(trade.get("trade_duration", 0.0) or 0.0),
        "parent_regime_root": parent_root,
        "parent_regime_confidence_floor": root["parent_regime_confidence_floor"],
        "root_lookup_status": root["root_lookup_status"],
        "regime_profit_branch_path": branch_path(parent_root),
        "regime_profit_branch_path_version": "board-b/v1",
        "source_ticker": SOURCE_TICKER,
        "allowed_action": "research_only_until_rc_spa_and_variant_matrix_pass",
        "suppression_rule": "suppress_if_branch_rc_spa_fails",
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def bootstrap_lcb(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    rng = np.random.default_rng(183756)
    means = [float(rng.choice(values, size=len(values), replace=True).mean()) for _ in range(1000)]
    return float(np.quantile(means, 0.05))


def fold_stats(values: np.ndarray) -> dict[str, Any]:
    if len(values) == 0:
        return {
            "test_folds": 0,
            "min_trades_per_test_fold": 0,
            "fold_positive_rate": 0.0,
            "fold_net_returns": [],
        }
    chunks = [chunk for chunk in np.array_split(values, min(5, len(values))) if len(chunk)]
    nets = [float(chunk.sum()) for chunk in chunks]
    return {
        "test_folds": len(chunks),
        "min_trades_per_test_fold": min(len(chunk) for chunk in chunks),
        "fold_positive_rate": sum(1 for net in nets if net > 0.0) / len(nets),
        "fold_net_returns": nets,
    }


def dsr(values: np.ndarray) -> float:
    if len(values) < 2:
        return 0.0
    std = float(values.std(ddof=1))
    if std <= 1e-12:
        return 0.0
    return float(values.mean() / std * math.sqrt(len(values)))


def branch_summary_for(root: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    branch_rows = [row for row in rows if row["parent_regime_root"] == root]
    values = np.array([float(row["net_return_R"]) for row in branch_rows], dtype=float)
    folds = fold_stats(values)
    total = int(len(values))
    net = float(values.sum()) if total else 0.0
    mean = float(values.mean()) if total else 0.0
    lcb = bootstrap_lcb(values)
    stressed = net - EXTRA_ROUND_TRIP_COST * total
    d = dsr(values)
    win_rate = float((values > 0.0).mean()) if total else 0.0
    pbo = 1.0
    failures: list[str] = []
    if total < MIN_TOTAL_TRADES:
        failures.append("reject_thin_trades")
    if folds["test_folds"] < MIN_TEST_FOLDS:
        failures.append("reject_insufficient_test_folds")
    if folds["min_trades_per_test_fold"] < MIN_TRADES_PER_FOLD:
        failures.append("reject_fold_trade_depth")
    if folds["fold_positive_rate"] < FOLD_POSITIVE_RATE_MIN:
        failures.append("reject_fold_inconsistency")
    if lcb <= 0.0:
        failures.append("reject_no_positive_edge")
    if stressed <= 0.0:
        failures.append("reject_cost_fragile")
    failures.append("reject_pbo_not_estimated_single_existing_recipe")
    if d <= 0.0:
        failures.append("reject_dsr_nonpositive")
    elif d < TARGET_DSR:
        failures.append("reject_dsr_below_target")

    score = 10.0
    score += 20.0 if total >= MIN_TOTAL_TRADES else max(0.0, 20.0 * total / MIN_TOTAL_TRADES)
    score += 20.0 if lcb > 0.0 else 0.0
    score += 20.0 * folds["fold_positive_rate"]
    score += 15.0 if stressed > 0.0 else 0.0
    score += min(10.0, max(0.0, d / TARGET_DSR * 10.0))
    score = min(100.0, score)
    if score < 60.0:
        failures.append("reject_rc_spa_below_60")

    return {
        "parent_regime_root": root,
        "regime_profit_branch_path": branch_path(root),
        "total_trades": total,
        "win_rate": win_rate,
        "net_return_R": net,
        "mean_R": mean,
        "bootstrap_edge_lcb_5pct": lcb,
        "stressed_2x_cost_net_R": stressed,
        "test_folds": folds["test_folds"],
        "min_trades_per_test_fold": folds["min_trades_per_test_fold"],
        "fold_positive_rate": folds["fold_positive_rate"],
        "fold_net_returns": folds["fold_net_returns"],
        "pbo": pbo,
        "dsr": d,
        "rc_spa": score,
        "hard_gate_result": "pass" if not failures else "fail:" + "|".join(failures),
        "failure_reasons": failures,
    }


def summarize(rows: list[dict[str, Any]], timerange_results: list[dict[str, Any]]) -> dict[str, Any]:
    branch_summaries = [branch_summary_for(root, rows) for root in ROOTS]
    manipulation = branch_summary_for("Manipulation(scoped)", rows)
    manipulation["parent_regime_root"] = "Manipulation(scoped)"
    manipulation["regime_profit_branch_path"] = branch_path("Manipulation(scoped)")
    branch_summaries.append(manipulation)
    passes = [row for row in branch_summaries if row["hard_gate_result"] == "pass"]
    max_score = max((row["rc_spa"] for row in branch_summaries), default=0.0)
    root_counts = {row["parent_regime_root"]: row["total_trades"] for row in branch_summaries}
    decision = {
        "board_state": "rejected",
        "gate_result": "fail:all_branch_paths_failed_rc_spa_hard_gates"
        if not passes
        else "pass:branch_paths_available_for_downstream",
        "stable_profit_score": max_score,
        "branch_paths_evaluated": len(branch_summaries),
        "branch_paths_passed": len(passes),
        "total_trade_rows": len(rows),
        "root_trade_counts": root_counts,
        "downstream_consumption": "not_started:blocked_by_branch_rc_spa_hard_gates"
        if not passes
        else "not_started:rc_spa_candidate",
        "primary_blocker": (
            "TomacNQ_KillzoneBreakout proves the synthetic NQ/USD Auto-Quant path can add a "
            "broader 2011-2025 crisis-capable panel, but this existing single recipe has no "
            "variant/PBO matrix and does not pass all branch hard gates."
        ),
        "next_action": (
            "B2R-repeat: synthesize a root-aware NQ variant matrix from this Tomac path, "
            "or extend the source panel so Crisis and scoped Manipulation have enough direct rows."
        ),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_root": rel(RUN_ROOT),
        "board_b": rel(BOARD_B),
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "accepted_regime_artifact": rel(BOARD_A_CONSUMER_MAP),
        "recipe_id": STRATEGY_NAME,
        "pair": PAIR,
        "source_ticker": SOURCE_TICKER,
        "auto_quant": {
            "root": str(AUTO_QUANT_ROOT),
            "config": str(AUTO_QUANT_CONFIG),
            "strategy_path": str(AUTO_QUANT_STRATEGIES / f"{STRATEGY_NAME}.py"),
            "data_path": str(AUTO_QUANT_DATA / "NQ_USD-1h.feather"),
        },
        "timerange_results": [{k: v for k, v in result.items() if k != "trades"} for result in timerange_results],
        "branch_summaries": branch_summaries,
        "decision": decision,
        "completion": {
            "runtime_code_changed": False,
            "auto_quant_checkout_changed": False,
            "raw_auto_quant_data_committed": False,
            "thresholds_relaxed": False,
            "downstream_runtime_consumed_branch_path": decision["gate_result"].startswith("pass:"),
        },
    }


def write_report(report: dict[str, Any]) -> None:
    timer_rows = []
    for result in report["timerange_results"]:
        metrics = result["aggregate_metrics"]
        timer_rows.append({
            "label": result["label"],
            "timerange": result["timerange"],
            "trade_count": int(metrics.get("trade_count", 0)),
            "win_rate_pct": float(metrics.get("win_rate_pct", 0.0)),
            "total_profit_pct": float(metrics.get("total_profit_pct", 0.0)),
            "sharpe": float(metrics.get("sharpe", 0.0)),
            "log_path": result["log_path"],
        })
    write_csv(TIMERANGE_CSV, timer_rows)
    summary_rows = [
        {
            "parent_regime_root": row["parent_regime_root"],
            "total_trades": row["total_trades"],
            "folds": row["test_folds"],
            "min_fold_trades": row["min_trades_per_test_fold"],
            "fold_positive_rate": row["fold_positive_rate"],
            "edge_lcb_5pct": row["bootstrap_edge_lcb_5pct"],
            "pbo": row["pbo"],
            "dsr": row["dsr"],
            "rc_spa": row["rc_spa"],
            "hard_gate_result": row["hard_gate_result"],
            "branch_path": row["regime_profit_branch_path"],
        }
        for row in report["branch_summaries"]
    ]
    write_csv(SUMMARY_CSV, summary_rows)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Tomac NQ Branch RC-SPA v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{report['decision']['gate_result']}`",
        f"- Stable profit score: `{report['decision']['stable_profit_score']:.4f}`",
        f"- Total trade rows: `{report['decision']['total_trade_rows']}`",
        f"- Branch paths evaluated: `{report['decision']['branch_paths_evaluated']}`",
        f"- Branch paths passed: `{report['decision']['branch_paths_passed']}`",
        f"- Root trade counts: `{report['decision']['root_trade_counts']}`",
        f"- Downstream consumption: `{report['decision']['downstream_consumption']}`",
        f"- Primary blocker: {report['decision']['primary_blocker']}",
        "",
        "## Auto-Quant / Freqtrade Readback",
        "",
        "| Segment | Timerange | Trades | Win rate % | Profit % | Sharpe | Log |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in timer_rows:
        lines.append(
            f"| `{row['label']}` | `{row['timerange']}` | {row['trade_count']} | "
            f"{row['win_rate_pct']:.3f} | {row['total_profit_pct']:.3f} | "
            f"{row['sharpe']:.4f} | `{row['log_path']}` |"
        )
    lines.extend([
        "",
        "## Branch Summary",
        "",
        "| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ])
    for row in report["branch_summaries"]:
        lines.append(
            f"| {row['parent_regime_root']} | {row['total_trades']} | {row['test_folds']} | "
            f"{row['min_trades_per_test_fold']} | {row['fold_positive_rate']:.4f} | "
            f"{row['bootstrap_edge_lcb_5pct']:.6f} | {row['pbo']:.2f} | "
            f"{row['dsr']:.4f} | {row['rc_spa']:.4f} | `{row['hard_gate_result']}` |"
        )
    lines.extend([
        "",
        "## Artifacts",
        "",
        f"- Report JSON: `{rel(REPORT_JSON)}`",
        f"- Trade rows: `{rel(TRADES_CSV)}`",
        f"- Branch summary: `{rel(SUMMARY_CSV)}`",
        f"- Timerange summary: `{rel(TIMERANGE_CSV)}`",
        f"- Assertions: `{rel(ASSERTIONS)}`",
        "",
        "## Next",
        "",
        f"- {report['decision']['next_action']}",
    ])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def git_ref() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(AUTO_QUANT_ROOT), "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def main() -> int:
    for path in [OUT_DIR, CHECK_DIR, LOG_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    timerange_results = [run_backtest(label, timerange) for label, timerange in TIMERANGES]
    full = next(result for result in timerange_results if result["label"] == "full_2011_2025")
    lookup = RootLookup(load_source_roots())
    rows = [clean_trade(trade, lookup) for trade in full["trades"]]
    write_csv(TRADES_CSV, rows)
    report = summarize(rows, timerange_results)
    report["auto_quant"]["pinned_ref"] = git_ref()
    write_report(report)
    assertions = [
        f"run_id={RUN_ID}",
        f"strategy={STRATEGY_NAME}",
        f"pair={PAIR}",
        f"full_trade_rows={len(rows)}",
        f"gate_result={report['decision']['gate_result']}",
        f"stable_profit_score={report['decision']['stable_profit_score']:.6f}",
        f"branch_paths_passed={report['decision']['branch_paths_passed']}",
        f"root_trade_counts={report['decision']['root_trade_counts']}",
        f"report_json={rel(REPORT_JSON)}",
    ]
    if not rows:
        assertions.append("ASSERT_FAIL:no_trade_rows")
    if report["decision"]["gate_result"].startswith("pass:"):
        assertions.append("ASSERT_FAIL:unexpected_pass_without_variant_pbo_matrix")
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "run_id": RUN_ID,
        "strategy": STRATEGY_NAME,
        "pair": PAIR,
        "trades": len(rows),
        "stable_profit_score": report["decision"]["stable_profit_score"],
        "gate_result": report["decision"]["gate_result"],
        "report": rel(REPORT_MD),
    }, indent=2))
    return 0 if not any(line.startswith("ASSERT_FAIL") for line in assertions) else 1


if __name__ == "__main__":
    raise SystemExit(main())
