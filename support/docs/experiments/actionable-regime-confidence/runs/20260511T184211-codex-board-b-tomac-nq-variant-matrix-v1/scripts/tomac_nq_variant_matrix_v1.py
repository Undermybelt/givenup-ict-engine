#!/usr/bin/env python3
"""Board B Tomac NQ root-aware variant matrix.

Additive experiment only: writes run-local Freqtrade strategy variants, runs
them through the local Auto-Quant Tomac synthetic-pair path, attaches Board A
root labels, estimates branch PBO from a variant/fold matrix, and emits
fail-closed Board B evidence without changing ict-engine runtime code or the
Auto-Quant checkout.
"""

from __future__ import annotations

import contextlib
import csv
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting


RUN_ID = "20260511T184211+0800-codex-board-b-tomac-nq-variant-matrix-v1"
SCHEMA_VERSION = "board-b-tomac-nq-variant-matrix/v1"
PAIR = "NQ/USD"
SOURCE_TICKER = "^IXIC"
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
ALL_ROOTS = [*ROOTS, "Manipulation(scoped)"]
TIMERANGES = [
    ("full_2011_2025", "20110101-20251231"),
    ("fold_2011_2014", "20110101-20141231"),
    ("fold_2015_2018", "20150101-20181231"),
    ("fold_2019_2021", "20190101-20211231"),
    ("fold_2022_2023", "20220101-20231231"),
    ("fold_2024_2025", "20240101-20251231"),
]
FOLD_LABELS = [label for label, _ in TIMERANGES if label.startswith("fold_")]

EXTRA_ROUND_TRIP_COST = 0.002
MIN_TOTAL_TRADES = 100
MIN_TEST_FOLDS = 4
MIN_TRADES_PER_FOLD = 10
FOLD_POSITIVE_RATE_MIN = 0.75
TARGET_DSR = 1.0
TAIL_LOSS_BUDGET = 0.04
REQUIRED_PBO_MAX = 0.25


@dataclass(frozen=True)
class Variant:
    class_name: str
    high_window: int
    low_window: int
    hour_start: int
    hour_end: int
    trend_filter: bool
    ema_fast: int
    ema_slow: int
    stoploss: float
    trail_positive: float
    trail_offset: float


VARIANTS = [
    Variant("TomacNQ_VM_Base24_AM13_15", 24, 24, 13, 15, True, 21, 89, -0.020, 0.005, 0.010),
    Variant("TomacNQ_VM_Fast18_AM13_16", 18, 24, 13, 16, True, 13, 55, -0.020, 0.004, 0.009),
    Variant("TomacNQ_VM_Tight12_AM13_15", 12, 18, 13, 15, True, 13, 55, -0.018, 0.004, 0.008),
    Variant("TomacNQ_VM_Wide36_AM14_15", 36, 36, 14, 15, True, 21, 89, -0.015, 0.006, 0.012),
    Variant("TomacNQ_VM_NoTrend24_AM13_15", 24, 24, 13, 15, False, 21, 89, -0.020, 0.005, 0.010),
    Variant("TomacNQ_VM_CrisisWide12_AM12_16", 12, 24, 12, 16, False, 13, 55, -0.025, 0.004, 0.010),
    Variant("TomacNQ_VM_Sideways18_AM12_15", 18, 18, 12, 15, False, 21, 89, -0.018, 0.006, 0.012),
    Variant("TomacNQ_VM_Conservative48_AM13_14", 48, 48, 13, 14, True, 34, 144, -0.015, 0.007, 0.014),
]


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
LOCAL_STRATEGY_DIR = RUN_ROOT / "strategies"
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

OUT_DIR = RUN_ROOT / "variant-matrix"
CHECK_DIR = RUN_ROOT / "checks"
LOG_DIR = RUN_ROOT / "logs"
TRADES_CSV = OUT_DIR / "tomac_nq_variant_matrix_trades_v1.csv"
VARIANT_SUMMARY_CSV = OUT_DIR / "tomac_nq_variant_matrix_variant_summary_v1.csv"
ROOT_SUMMARY_CSV = OUT_DIR / "tomac_nq_variant_matrix_root_summary_v1.csv"
FOLD_MATRIX_CSV = OUT_DIR / "tomac_nq_variant_matrix_fold_matrix_v1.csv"
REPORT_JSON = OUT_DIR / "tomac_nq_variant_matrix_report_v1.json"
REPORT_MD = OUT_DIR / "tomac_nq_variant_matrix_report_v1.md"
ASSERTIONS = CHECK_DIR / "tomac_nq_variant_matrix_v1_assertions.out"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def setup_imports() -> None:
    sys.path.insert(0, str(AUTO_QUANT_ROOT))


def load_tomac_runner():
    setup_imports()
    import run_tomac  # type: ignore

    return run_tomac


def variant_source(variant: Variant) -> str:
    trend_line = (
        '        trend_4h = dataframe["ema_fast_4h"] > dataframe["ema_slow_4h"]\n'
        "        entry = am_killzone & breakout & trend_4h\n"
        if variant.trend_filter
        else "        entry = am_killzone & breakout\n"
    )
    return f'''from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy, informative
from pandas import DataFrame


class {variant.class_name}(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {{"0": 100}}
    stoploss = {variant.stoploss}

    trailing_stop = True
    trailing_stop_positive = {variant.trail_positive}
    trailing_stop_positive_offset = {variant.trail_offset}
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 260

    @informative("4h")
    def populate_indicators_4h(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod={variant.ema_fast})
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod={variant.ema_slow})
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["high_window"] = dataframe["high"].rolling({variant.high_window}).max().shift(1)
        dataframe["low_window"] = dataframe["low"].rolling({variant.low_window}).min().shift(1)
        dataframe["hour_utc"] = dataframe["date"].dt.hour
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        am_killzone = (dataframe["hour_utc"] >= {variant.hour_start}) & (dataframe["hour_utc"] <= {variant.hour_end})
        breakout = dataframe["close"] > dataframe["high_window"]
{trend_line}        dataframe.loc[entry, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        breakdown = dataframe["close"] < dataframe["low_window"]
        trend_break_4h = dataframe["ema_fast_4h"] < dataframe["ema_slow_4h"]
        dataframe.loc[breakdown | trend_break_4h, "exit_long"] = 1
        return dataframe
'''


def write_variant_strategies() -> None:
    LOCAL_STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    for variant in VARIANTS:
        (LOCAL_STRATEGY_DIR / f"{variant.class_name}.py").write_text(
            variant_source(variant),
            encoding="utf-8",
        )


def build_config(strategy_name: str, timerange: str) -> dict[str, Any]:
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
        "strategy": strategy_name,
        "strategy_path": str(LOCAL_STRATEGY_DIR),
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


def run_backtest(variant: Variant, label: str, timerange: str) -> dict[str, Any]:
    run_tomac = load_tomac_runner()
    config = build_config(variant.class_name, timerange)
    log_path = LOG_DIR / f"freqtrade_{variant.class_name}_{label}.out"
    err_path = LOG_DIR / f"freqtrade_{variant.class_name}_{label}.err"
    with log_path.open("w", encoding="utf-8") as out, err_path.open("w", encoding="utf-8") as err:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            exchange = run_tomac._build_exchange_with_synthetic_pairs(config)
            bt = Backtesting(config, exchange=exchange)
            bt.start()
    strategy_result = bt.results.get("strategy", {}).get(variant.class_name, {}) or {}
    metrics = run_tomac.extract_metrics(bt.results, variant.class_name)
    return {
        "variant_id": variant.class_name,
        "label": label,
        "timerange": timerange,
        "log_path": rel(log_path),
        "stderr_path": rel(err_path),
        "aggregate_metrics": metrics["aggregate"],
        "per_pair_metrics": metrics["per_pair"],
        "trades": strategy_result.get("trades", []) or [],
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


def branch_path(root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"{root} -> TrendExpansion -> TomacNQVariantMatrix -> {variant_id}"
    if root == "Bear":
        return f"{root} -> BearMarketDrawdown -> TomacNQVariantMatrix -> {variant_id}"
    if root == "Sideways":
        return f"{root} -> RangeConsolidation -> TomacNQVariantMatrix -> {variant_id}"
    if root == "Crisis":
        return f"{root} -> ExtremeStress -> TomacNQVariantMatrix -> {variant_id}"
    return "Manipulation(scoped) -> DirectEventOverlayMissing -> no_direct_event_rows -> suppress_or_abstain"


def clean_trade(trade: dict[str, Any], variant: Variant, label: str, lookup: RootLookup) -> dict[str, Any]:
    open_date = pd.Timestamp(trade["open_date"])
    close_date = pd.Timestamp(trade["close_date"])
    root = lookup.lookup(open_date)
    profit_ratio = float(trade.get("profit_ratio", 0.0) or 0.0)
    parent_root = root["parent_regime_root"]
    return {
        "run_id": RUN_ID,
        "recipe_id": "TomacNQVariantMatrixV1",
        "variant_id": variant.class_name,
        "pair": str(trade.get("pair", "")),
        "segment": label,
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
        "regime_profit_branch_path": branch_path(parent_root, variant.class_name),
        "regime_profit_branch_path_version": "board-b/v1",
        "source_ticker": SOURCE_TICKER,
        "allowed_action": "research_only_until_rc_spa_variant_matrix_and_required_roots_pass",
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


def bootstrap_lcb(values: np.ndarray, seed: int) -> float:
    if len(values) == 0:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    rng = np.random.default_rng(seed)
    means = [float(rng.choice(values, size=len(values), replace=True).mean()) for _ in range(1000)]
    return float(np.quantile(means, 0.05))


def dsr(values: np.ndarray) -> float:
    if len(values) < 2:
        return 0.0
    std = float(values.std(ddof=1))
    if std <= 1e-12:
        return 0.0
    return float(values.mean() / std * math.sqrt(len(values)))


def fold_values(
    fold_rows: list[dict[str, Any]],
    variant_id: str,
    root: str,
) -> list[float]:
    values = []
    for label in FOLD_LABELS:
        net = sum(
            float(row["net_return_R"])
            for row in fold_rows
            if row["variant_id"] == variant_id
            and row["parent_regime_root"] == root
            and row["segment"] == label
        )
        values.append(float(net))
    return values


def fold_trade_counts(
    fold_rows: list[dict[str, Any]],
    variant_id: str,
    root: str,
) -> list[int]:
    counts = []
    for label in FOLD_LABELS:
        counts.append(
            sum(
                1
                for row in fold_rows
                if row["variant_id"] == variant_id
                and row["parent_regime_root"] == root
                and row["segment"] == label
            )
        )
    return counts


def estimate_pbo(fold_matrix: dict[tuple[str, str], list[float]], root: str) -> float:
    candidate_ids = [variant.class_name for variant in VARIANTS]
    events = 0
    below_median = 0
    for idx in range(len(FOLD_LABELS)):
        train_scores = {
            variant_id: sum(
                value
                for pos, value in enumerate(fold_matrix[(variant_id, root)])
                if pos != idx
            )
            for variant_id in candidate_ids
        }
        best_variant = max(train_scores, key=train_scores.get)
        test_values = [fold_matrix[(variant_id, root)][idx] for variant_id in candidate_ids]
        if not any(value != 0.0 for value in test_values):
            continue
        events += 1
        if fold_matrix[(best_variant, root)][idx] < float(np.median(test_values)):
            below_median += 1
    if events == 0:
        return 1.0
    return below_median / events


def tail_loss_p95(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    return float(np.quantile(np.maximum(-values, 0.0), 0.95))


def specificity_ratio(full_rows: list[dict[str, Any]], variant_id: str, root: str) -> float:
    root_values = [
        float(row["net_return_R"])
        for row in full_rows
        if row["variant_id"] == variant_id and row["parent_regime_root"] == root
    ]
    other_values = [
        float(row["net_return_R"])
        for row in full_rows
        if row["variant_id"] == variant_id and row["parent_regime_root"] != root
    ]
    if not root_values or not other_values:
        return 0.0
    root_mean = float(np.mean(root_values))
    other_mean = float(np.mean(other_values))
    if root_mean <= 0.0:
        return 0.0
    if other_mean <= 0.0:
        return 3.0
    return root_mean / max(other_mean, 1e-12)


def score_branch(
    full_rows: list[dict[str, Any]],
    fold_rows: list[dict[str, Any]],
    fold_matrix: dict[tuple[str, str], list[float]],
    variant_id: str,
    root: str,
    pbo: float,
) -> dict[str, Any]:
    branch_rows = [
        row
        for row in full_rows
        if row["variant_id"] == variant_id and row["parent_regime_root"] == root
    ]
    values = np.array([float(row["net_return_R"]) for row in branch_rows], dtype=float)
    total = int(len(values))
    counts = fold_trade_counts(fold_rows, variant_id, root)
    fold_nets = fold_matrix[(variant_id, root)]
    fold_positive_rate = sum(1 for net in fold_nets if net > 0.0) / len(fold_nets)
    min_fold_trades = min(counts) if counts else 0
    net = float(values.sum()) if total else 0.0
    lcb = bootstrap_lcb(values, seed=184211 + abs(hash((variant_id, root))) % 10000)
    stressed = net - EXTRA_ROUND_TRIP_COST * total
    d = dsr(values)
    win_rate = float((values > 0.0).mean()) if total else 0.0
    tail = tail_loss_p95(values)
    specificity = specificity_ratio(full_rows, variant_id, root)
    failures: list[str] = []
    if total < MIN_TOTAL_TRADES:
        failures.append("reject_thin_trades")
    if len(FOLD_LABELS) < MIN_TEST_FOLDS:
        failures.append("reject_insufficient_test_folds")
    if min_fold_trades < MIN_TRADES_PER_FOLD:
        failures.append("reject_fold_trade_depth")
    if fold_positive_rate < FOLD_POSITIVE_RATE_MIN:
        failures.append("reject_fold_inconsistency")
    if lcb <= 0.0:
        failures.append("reject_no_positive_edge")
    if stressed <= 0.0:
        failures.append("reject_cost_fragile")
    if pbo > REQUIRED_PBO_MAX:
        failures.append("reject_overfit_risk")
    if d <= 0.0:
        failures.append("reject_dsr_nonpositive")
    elif d < TARGET_DSR:
        failures.append("reject_dsr_below_target")
    if tail > TAIL_LOSS_BUDGET:
        failures.append("reject_tail_risk")
    if specificity < 1.20:
        failures.append("reject_no_regime_specificity")

    edge_score = min(1.0, max(0.0, lcb / 0.0005))
    fold_score = fold_positive_rate
    depth_score = min(1.0, total / MIN_TOTAL_TRADES)
    dsr_score = min(1.0, max(0.0, d / TARGET_DSR))
    pbo_score = 1.0 - min(1.0, max(0.0, pbo / REQUIRED_PBO_MAX))
    cost_score = 1.0 if stressed > 0.0 else 0.0
    drawdown_score = 1.0 - min(1.0, max(0.0, tail / TAIL_LOSS_BUDGET))
    specificity_score = min(1.0, max(0.0, (specificity - 1.0) / 0.5))
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
    if rc_spa < 60.0 and "reject_rc_spa_below_60" not in failures:
        failures.append("reject_rc_spa_below_60")

    return {
        "parent_regime_root": root,
        "selected_variant": variant_id,
        "regime_profit_branch_path": branch_path(root, variant_id),
        "total_trades": total,
        "win_rate": win_rate,
        "net_return_R": net,
        "bootstrap_edge_lcb_5pct": lcb,
        "stressed_2x_cost_net_R": stressed,
        "test_folds": len(FOLD_LABELS),
        "min_trades_per_test_fold": min_fold_trades,
        "fold_trade_counts": counts,
        "fold_net_returns": fold_nets,
        "fold_positive_rate": fold_positive_rate,
        "pbo": pbo,
        "dsr": d,
        "tail_loss_p95": tail,
        "regime_specificity_ratio": specificity,
        "rc_spa": rc_spa,
        "hard_gate_result": "pass" if not failures else "fail:" + "|".join(failures),
        "failure_reasons": failures,
    }


def summarize(all_results: list[dict[str, Any]], full_rows: list[dict[str, Any]], fold_rows: list[dict[str, Any]]) -> dict[str, Any]:
    fold_matrix: dict[tuple[str, str], list[float]] = {}
    fold_matrix_rows: list[dict[str, Any]] = []
    variant_summary_rows: list[dict[str, Any]] = []
    for variant in VARIANTS:
        full_variant_rows = [row for row in full_rows if row["variant_id"] == variant.class_name]
        values = np.array([float(row["net_return_R"]) for row in full_variant_rows], dtype=float)
        by_root = {
            root: sum(1 for row in full_variant_rows if row["parent_regime_root"] == root)
            for root in ALL_ROOTS
        }
        variant_summary_rows.append({
            "variant_id": variant.class_name,
            "full_trades": len(full_variant_rows),
            "full_net_return_R": float(values.sum()) if len(values) else 0.0,
            "full_win_rate": float((values > 0.0).mean()) if len(values) else 0.0,
            "root_trade_counts": by_root,
            "params": {
                "high_window": variant.high_window,
                "low_window": variant.low_window,
                "hour_start": variant.hour_start,
                "hour_end": variant.hour_end,
                "trend_filter": variant.trend_filter,
                "ema_fast": variant.ema_fast,
                "ema_slow": variant.ema_slow,
                "stoploss": variant.stoploss,
                "trail_positive": variant.trail_positive,
                "trail_offset": variant.trail_offset,
            },
        })
        for root in ALL_ROOTS:
            nets = fold_values(fold_rows, variant.class_name, root)
            fold_matrix[(variant.class_name, root)] = nets
            counts = fold_trade_counts(fold_rows, variant.class_name, root)
            for label, net, count in zip(FOLD_LABELS, nets, counts):
                fold_matrix_rows.append({
                    "variant_id": variant.class_name,
                    "parent_regime_root": root,
                    "fold": label,
                    "fold_net_return_R": net,
                    "fold_trades": count,
                })

    root_summaries: list[dict[str, Any]] = []
    for root in ALL_ROOTS:
        pbo = estimate_pbo(fold_matrix, root)
        candidates = [
            score_branch(full_rows, fold_rows, fold_matrix, variant.class_name, root, pbo)
            for variant in VARIANTS
        ]
        selected = max(
            candidates,
            key=lambda row: (
                row["rc_spa"],
                row["total_trades"],
                row["net_return_R"],
            ),
        )
        selected["pbo_matrix_variant_count"] = len(VARIANTS)
        root_summaries.append(selected)

    passes = [row for row in root_summaries if row["hard_gate_result"] == "pass"]
    max_score = max((row["rc_spa"] for row in root_summaries), default=0.0)
    required_failed = [
        row["parent_regime_root"]
        for row in root_summaries
        if row["parent_regime_root"] in ["Bear", "Sideways", "Crisis", "Manipulation(scoped)"]
        and row["hard_gate_result"] != "pass"
    ]
    if not passes:
        gate = "fail:all_branch_paths_failed_rc_spa_hard_gates"
    elif required_failed:
        gate = "fail:required_branch_paths_failed_rc_spa_hard_gates"
    else:
        gate = "pass:branch_paths_available_for_downstream"

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_root": rel(RUN_ROOT),
        "board_b": rel(BOARD_B),
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "accepted_regime_artifact": rel(BOARD_A_CONSUMER_MAP),
        "recipe_id": "TomacNQVariantMatrixV1",
        "pair": PAIR,
        "source_ticker": SOURCE_TICKER,
        "auto_quant": {
            "root": str(AUTO_QUANT_ROOT),
            "config": str(AUTO_QUANT_CONFIG),
            "strategy_path": rel(LOCAL_STRATEGY_DIR),
            "data_path": str(AUTO_QUANT_DATA / "NQ_USD-1h.feather"),
            "pinned_ref": git_ref(AUTO_QUANT_ROOT),
        },
        "variant_count": len(VARIANTS),
        "timerange_results": [{k: v for k, v in result.items() if k != "trades"} for result in all_results],
        "variant_summaries": variant_summary_rows,
        "fold_matrix": fold_matrix_rows,
        "root_summaries": root_summaries,
        "decision": {
            "board_state": "rejected" if not gate.startswith("pass:") else "research_watch",
            "gate_result": gate,
            "stable_profit_score": max_score,
            "branch_paths_evaluated": len(root_summaries),
            "branch_paths_passed": len(passes),
            "required_failed_roots": required_failed,
            "total_trade_rows_full_matrix": len(full_rows),
            "root_trade_counts_selected": {
                row["parent_regime_root"]: row["total_trades"] for row in root_summaries
            },
            "downstream_consumption": (
                "not_started:blocked_by_required_branch_rc_spa_hard_gates"
                if not gate.startswith("pass:")
                else "not_started:rc_spa_candidate_needs_downstream"
            ),
            "primary_blocker": (
                "TomacNQVariantMatrixV1 estimates PBO from 8 variants x 5 folds, but required "
                "Bear/Sideways/Crisis/Manipulation branch paths still do not all satisfy RC-SPA."
            ),
            "next_action": (
                "B2R-repeat: extend direct crisis/manipulation rows or synthesize a branch-specific "
                "recipe that increases Bear/Sideways/Crisis fold depth without losing edge."
            ),
        },
        "completion": {
            "runtime_code_changed": False,
            "auto_quant_checkout_changed": False,
            "run_local_strategy_variants_written": True,
            "raw_auto_quant_data_committed": False,
            "thresholds_relaxed": False,
            "downstream_runtime_consumed_branch_path": gate.startswith("pass:"),
        },
    }


def write_report(report: dict[str, Any]) -> None:
    variant_csv_rows = []
    for row in report["variant_summaries"]:
        out = {k: v for k, v in row.items() if k not in {"root_trade_counts", "params"}}
        out["root_trade_counts_json"] = json.dumps(row["root_trade_counts"], sort_keys=True)
        out["params_json"] = json.dumps(row["params"], sort_keys=True)
        variant_csv_rows.append(out)
    write_csv(VARIANT_SUMMARY_CSV, variant_csv_rows)
    write_csv(FOLD_MATRIX_CSV, report["fold_matrix"])
    root_rows = [
        {
            "parent_regime_root": row["parent_regime_root"],
            "selected_variant": row["selected_variant"],
            "total_trades": row["total_trades"],
            "test_folds": row["test_folds"],
            "min_trades_per_test_fold": row["min_trades_per_test_fold"],
            "fold_positive_rate": row["fold_positive_rate"],
            "edge_lcb_5pct": row["bootstrap_edge_lcb_5pct"],
            "pbo": row["pbo"],
            "dsr": row["dsr"],
            "tail_loss_p95": row["tail_loss_p95"],
            "regime_specificity_ratio": row["regime_specificity_ratio"],
            "rc_spa": row["rc_spa"],
            "hard_gate_result": row["hard_gate_result"],
            "branch_path": row["regime_profit_branch_path"],
        }
        for row in report["root_summaries"]
    ]
    write_csv(ROOT_SUMMARY_CSV, root_rows)
    REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Tomac NQ Variant Matrix v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{report['decision']['gate_result']}`",
        f"- Stable profit score: `{report['decision']['stable_profit_score']:.4f}`",
        f"- Variant matrix: `{report['variant_count']}` variants x `{len(FOLD_LABELS)}` folds",
        f"- Full-matrix trade rows: `{report['decision']['total_trade_rows_full_matrix']}`",
        f"- Branch paths passed: `{report['decision']['branch_paths_passed']}` / `{report['decision']['branch_paths_evaluated']}`",
        f"- Selected root trade counts: `{report['decision']['root_trade_counts_selected']}`",
        f"- Required failed roots: `{report['decision']['required_failed_roots']}`",
        f"- Downstream consumption: `{report['decision']['downstream_consumption']}`",
        f"- Primary blocker: {report['decision']['primary_blocker']}",
        "",
        "## Selected Branch Summary",
        "",
        "| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | Tail p95 | Specificity | RC-SPA | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["root_summaries"]:
        lines.append(
            f"| {row['parent_regime_root']} | `{row['selected_variant']}` | {row['total_trades']} | "
            f"{row['test_folds']} | {row['min_trades_per_test_fold']} | "
            f"{row['fold_positive_rate']:.4f} | {row['bootstrap_edge_lcb_5pct']:.6f} | "
            f"{row['pbo']:.2f} | {row['dsr']:.4f} | {row['tail_loss_p95']:.4f} | "
            f"{row['regime_specificity_ratio']:.4f} | {row['rc_spa']:.4f} | "
            f"`{row['hard_gate_result']}` |"
        )
    lines.extend([
        "",
        "## Variant Full-Window Readback",
        "",
        "| Variant | Trades | Net R | Win Rate | Root Counts |",
        "|---|---:|---:|---:|---|",
    ])
    for row in report["variant_summaries"]:
        lines.append(
            f"| `{row['variant_id']}` | {row['full_trades']} | {row['full_net_return_R']:.6f} | "
            f"{row['full_win_rate']:.4f} | `{row['root_trade_counts']}` |"
        )
    lines.extend([
        "",
        "## Artifacts",
        "",
        f"- Report JSON: `{rel(REPORT_JSON)}`",
        f"- Full trade rows: `{rel(TRADES_CSV)}`",
        f"- Selected branch summary: `{rel(ROOT_SUMMARY_CSV)}`",
        f"- Variant summary: `{rel(VARIANT_SUMMARY_CSV)}`",
        f"- Fold matrix: `{rel(FOLD_MATRIX_CSV)}`",
        f"- Run-local strategies: `{rel(LOCAL_STRATEGY_DIR)}`",
        f"- Assertions: `{rel(ASSERTIONS)}`",
        "",
        "## Next",
        "",
        f"- {report['decision']['next_action']}",
    ])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def git_ref(path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def main() -> int:
    for path in [OUT_DIR, CHECK_DIR, LOG_DIR, LOCAL_STRATEGY_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    write_variant_strategies()
    lookup = RootLookup(load_source_roots())
    all_results: list[dict[str, Any]] = []
    full_rows: list[dict[str, Any]] = []
    fold_rows: list[dict[str, Any]] = []
    for variant in VARIANTS:
        for label, timerange in TIMERANGES:
            result = run_backtest(variant, label, timerange)
            all_results.append(result)
            rows = [clean_trade(trade, variant, label, lookup) for trade in result["trades"]]
            if label == "full_2011_2025":
                full_rows.extend(rows)
            else:
                fold_rows.extend(rows)
    write_csv(TRADES_CSV, full_rows)
    report = summarize(all_results, full_rows, fold_rows)
    write_report(report)
    assertions = [
        f"run_id={RUN_ID}",
        "recipe=TomacNQVariantMatrixV1",
        f"pair={PAIR}",
        f"variant_count={len(VARIANTS)}",
        f"full_matrix_trade_rows={len(full_rows)}",
        f"gate_result={report['decision']['gate_result']}",
        f"stable_profit_score={report['decision']['stable_profit_score']:.6f}",
        f"branch_paths_passed={report['decision']['branch_paths_passed']}",
        f"required_failed_roots={report['decision']['required_failed_roots']}",
        f"report_json={rel(REPORT_JSON)}",
    ]
    if not full_rows:
        assertions.append("ASSERT_FAIL:no_full_trade_rows")
    if report["decision"]["gate_result"].startswith("pass:"):
        assertions.append("ASSERT_FAIL:unexpected_full_required_root_pass_without_downstream")
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "run_id": RUN_ID,
        "recipe": "TomacNQVariantMatrixV1",
        "variants": len(VARIANTS),
        "full_trade_rows": len(full_rows),
        "stable_profit_score": report["decision"]["stable_profit_score"],
        "gate_result": report["decision"]["gate_result"],
        "report": rel(REPORT_MD),
    }, indent=2))
    return 0 if not any(line.startswith("ASSERT_FAIL") for line in assertions) else 1


if __name__ == "__main__":
    raise SystemExit(main())
