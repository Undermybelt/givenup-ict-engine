#!/usr/bin/env python3
"""Board B root-transition triad RC-SPA readback.

Run-local additive experiment. It consumes existing local Auto-Quant feather
panels, attaches the accepted Board A MainRegimeV2 source-root schedule, and
scores one non-Tomac/non-VRP root-aware recipe with the Board B RC-SPA gates.
"""

from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T193803+0800-codex-board-b-root-transition-triad-clean-v1"
SCHEMA_VERSION = "board-b-root-transition-triad/v1"
RECIPE_ID = "RootTransitionTriadV1"
SOURCE_TICKER = "^IXIC"
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
REQUIRED_PATHS = ["Bull", "Bear", "Sideways", "Crisis", "Manipulation(scoped)"]

DATA_DIR = Path("/Users/thrill3r/Auto-Quant/user_data/data")
SOURCE_REGIME_CSV = Path(
    "/Users/thrill3r/Downloads/stock-market-regimes-20002026/"
    "stock_market_regimes_2000_2026.csv"
)

START = pd.Timestamp("2011-01-01", tz="UTC")
END = pd.Timestamp("2026-01-31", tz="UTC")

TARGET_EDGE = 0.001
TARGET_DSR = 1.0
DRAWDOWN_BUDGET = 0.25
TAIL_LOSS_BUDGET = 0.05
MIN_TOTAL_TRADES = 100
MIN_TEST_FOLDS = 4
MIN_TRADES_PER_TEST_FOLD = 10
FOLD_POSITIVE_RATE_MIN = 0.75

PANELS = [
    ("NQ/USD", "1h", DATA_DIR / "NQ_USD-1h.feather"),
    ("NQ/USD", "4h", DATA_DIR / "NQ_USD-4h.feather"),
    ("NQ/USD", "1d", DATA_DIR / "NQ_USD-1d.feather"),
    ("BTC/USDT", "4h", DATA_DIR / "BTC_USDT-4h.feather"),
    ("BTC/USDT", "1d", DATA_DIR / "BTC_USDT-1d.feather"),
    ("ETH/USDT", "4h", DATA_DIR / "ETH_USDT-4h.feather"),
    ("ETH/USDT", "1d", DATA_DIR / "ETH_USDT-1d.feather"),
    ("BNB/USDT", "4h", DATA_DIR / "BNB_USDT-4h.feather"),
    ("SOL/USDT", "4h", DATA_DIR / "SOL_USDT-4h.feather"),
    ("AVAX/USDT", "4h", DATA_DIR / "AVAX_USDT-4h.feather"),
    ("SPY/USD", "1d", DATA_DIR / "SPY_USD-1d.feather"),
    ("ES/USD", "1d", DATA_DIR / "ES_USD-1d.feather"),
    ("AAPL/USD", "1d", DATA_DIR / "AAPL_USD-1d.feather"),
    ("GLD/USD", "1h", DATA_DIR / "GLD_USD-1h.feather"),
    ("GLD/USD", "4h", DATA_DIR / "GLD_USD-4h.feather"),
]

VARIANTS: list[dict[str, Any]] = [
    {
        "variant_id": "trend_follow_fast",
        "mode": "trend",
        "lookback": 5,
        "ema": 20,
        "z": 1.1,
        "hold": {"1h": 8, "4h": 5, "1d": 5},
    },
    {
        "variant_id": "trend_follow_slow",
        "mode": "trend",
        "lookback": 20,
        "ema": 50,
        "z": 1.3,
        "hold": {"1h": 16, "4h": 8, "1d": 10},
    },
    {
        "variant_id": "range_reversion_dense",
        "mode": "reversion",
        "lookback": 5,
        "ema": 20,
        "z": 0.85,
        "hold": {"1h": 6, "4h": 4, "1d": 4},
    },
    {
        "variant_id": "tail_breakdown_short",
        "mode": "tail_short",
        "lookback": 3,
        "ema": 20,
        "z": 1.0,
        "hold": {"1h": 10, "4h": 6, "1d": 6},
    },
    {
        "variant_id": "defensive_rotation",
        "mode": "defensive",
        "lookback": 10,
        "ema": 20,
        "z": 1.0,
        "hold": {"1h": 12, "4h": 6, "1d": 8},
    },
]


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot find repo root from {start}")


RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = find_repo_root(Path(__file__).resolve())
BOARD_A_CONSUMER_MAP = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/"
    "regime_factor_consumer_map_v1.csv"
)

OUT_DIR = RUN_ROOT / "branch-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"
FAIL_CLOSED_DIR = RUN_ROOT / "ict-engine-fail-closed"

ALL_ROWS_CSV = OUT_DIR / "root_transition_triad_variant_rows_v1.csv"
SELECTED_ROWS_CSV = OUT_DIR / "root_transition_triad_selected_rows_v1.csv"
SUMMARY_CSV = OUT_DIR / "root_transition_triad_branch_summary_v1.csv"
PANEL_SUMMARY_CSV = OUT_DIR / "root_transition_triad_panel_summary_v1.csv"
REPORT_JSON = OUT_DIR / "root_transition_triad_rc_spa_report_v1.json"
REPORT_MD = OUT_DIR / "root_transition_triad_rc_spa_report_v1.md"
ASSERTIONS = CHECK_DIR / "root_transition_triad_v1_assertions.out"
FAIL_CLOSED_MD = FAIL_CLOSED_DIR / "root_transition_triad_fail_closed_summary_v1.md"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def git_ref(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def load_root_floors() -> dict[str, float]:
    floors: dict[str, float] = {}
    with BOARD_A_CONSUMER_MAP.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            regime = row["regime"]
            if regime in {"Bull", "Bear", "Sideways", "Crisis", "Manipulation"}:
                floors[regime] = float(row["confidence_floor"])
    return floors


def load_source_roots() -> pd.DataFrame:
    df = pd.read_csv(
        SOURCE_REGIME_CSV,
        usecols=["date", "ticker", "regime_label", "regime_confidence", "vix"],
        parse_dates=["date"],
    )
    df = df[df["ticker"] == SOURCE_TICKER].copy()
    if df.empty:
        raise RuntimeError(f"no source rows for {SOURCE_TICKER}")
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    df["parent_regime_root"] = df["regime_label"].map(lambda v: v if v in ROOTS else "Crisis")
    df["regime_confidence"] = pd.to_numeric(df["regime_confidence"], errors="coerce").fillna(0.0)
    df["vix"] = pd.to_numeric(df["vix"], errors="coerce").fillna(0.0)
    return df.sort_values("date").reset_index(drop=True)


class RootLookup:
    def __init__(self, source: pd.DataFrame, root_floors: dict[str, float]) -> None:
        self.dates = source["date"].to_numpy(dtype="datetime64[ns]")
        self.roots = source["parent_regime_root"].to_numpy()
        self.conf = source["regime_confidence"].to_numpy(dtype=float)
        self.vix = source["vix"].to_numpy(dtype=float)
        self.root_floors = root_floors

    def lookup(self, value: Any) -> dict[str, Any]:
        date = pd.Timestamp(value).tz_localize(None).normalize().to_datetime64()
        pos = int(np.searchsorted(self.dates, date, side="right") - 1)
        if pos < 0:
            return {
                "parent_regime_root": "Unlabeled",
                "parent_regime_confidence_floor": 0.0,
                "source_ticker_confidence": 0.0,
                "source_ticker_vix": 0.0,
                "root_lookup_status": "missing_before_source_panel",
            }
        root = str(self.roots[pos])
        return {
            "parent_regime_root": root,
            "parent_regime_confidence_floor": self.root_floors.get(root, 0.0),
            "source_ticker_confidence": float(self.conf[pos]),
            "source_ticker_vix": float(self.vix[pos]),
            "root_lookup_status": "source_panel_daily_asof",
        }


def branch_path(root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"{root} -> TrendExpansion -> TransitionContinuation -> {RECIPE_ID}:{variant_id}"
    if root == "Bear":
        return f"{root} -> BearMarketDrawdown -> DirectionalShortContinuation -> {RECIPE_ID}:{variant_id}"
    if root == "Sideways":
        return f"{root} -> RangeConsolidation -> BandMeanReversion -> {RECIPE_ID}:{variant_id}"
    if root == "Crisis":
        return f"{root} -> ExtremeStress -> TailRiskShortContinuation -> {RECIPE_ID}:{variant_id}"
    return "Manipulation(scoped) -> DirectEventOverlayMissing -> no_direct_event_rows -> suppress_or_abstain"


def branch_fields(root: str) -> dict[str, str]:
    if root == "Bull":
        return {
            "sub_regime_tags": "TrendExpansion",
            "sub_sub_regime_or_profit_factor": "TransitionContinuation",
            "profit_factor_family": "root_transition_directional",
            "allowed_action": "long_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bull_transition_branch_rc_spa_fails",
        }
    if root == "Bear":
        return {
            "sub_regime_tags": "BearMarketDrawdown",
            "sub_sub_regime_or_profit_factor": "DirectionalShortContinuation",
            "profit_factor_family": "root_transition_directional",
            "allowed_action": "short_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_bear_transition_branch_rc_spa_fails",
        }
    if root == "Sideways":
        return {
            "sub_regime_tags": "RangeConsolidation",
            "sub_sub_regime_or_profit_factor": "BandMeanReversion",
            "profit_factor_family": "root_range_reversion",
            "allowed_action": "long_short_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "suppress_if_sideways_range_branch_rc_spa_fails",
        }
    if root == "Crisis":
        return {
            "sub_regime_tags": "ExtremeStress",
            "sub_sub_regime_or_profit_factor": "TailRiskShortContinuation",
            "profit_factor_family": "tail_risk_directional",
            "allowed_action": "short_or_defensive_research_only_until_branch_rc_spa_passes",
            "suppression_rule": "tail_guard_blocks_crisis_transition_if_rc_spa_fails",
        }
    return {
        "sub_regime_tags": "DirectEventOverlayMissing",
        "sub_sub_regime_or_profit_factor": "no_direct_event_rows",
        "profit_factor_family": "direct_manipulation_overlay",
        "allowed_action": "suppress_or_abstain",
        "suppression_rule": "no_direct_manipulation_profit_rows",
    }


def roundtrip_cost(market: str, timeframe: str) -> float:
    if "USDT" in market:
        return 0.0015
    if timeframe == "1d":
        return 0.0006
    return 0.0008


def load_panel(path: Path, market: str, timeframe: str, lookup: RootLookup) -> pd.DataFrame:
    df = pd.read_feather(path)
    df["date"] = pd.to_datetime(df["date"], unit="ms", utc=True)
    df = df[(df["date"] >= START) & (df["date"] <= END)].copy()
    if df.empty:
        return df
    df = df.sort_values("date").reset_index(drop=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"]).reset_index(drop=True)
    df["session_date"] = df["date"].dt.tz_convert(None).dt.normalize()
    root_rows = [lookup.lookup(value) for value in df["session_date"]]
    root_df = pd.DataFrame(root_rows)
    df = pd.concat([df, root_df], axis=1)
    df["market"] = market
    df["timeframe"] = timeframe
    df["ret1"] = df["close"].pct_change().fillna(0.0)
    df["ret3"] = df["close"].pct_change(3).fillna(0.0)
    df["ret5"] = df["close"].pct_change(5).fillna(0.0)
    df["ret10"] = df["close"].pct_change(10).fillna(0.0)
    df["ret20"] = df["close"].pct_change(20).fillna(0.0)
    high_low = (df["high"] - df["low"]).abs()
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr20"] = tr.rolling(20, min_periods=5).mean().bfill()
    df["atr_pct"] = (df["atr20"] / df["close"]).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    mean20 = df["close"].rolling(20, min_periods=10).mean()
    std20 = df["close"].rolling(20, min_periods=10).std()
    df["z20"] = ((df["close"] - mean20) / std20.replace(0, np.nan)).fillna(0.0)
    df["high20_prev"] = df["high"].rolling(20, min_periods=10).max().shift(1)
    df["low20_prev"] = df["low"].rolling(20, min_periods=10).min().shift(1)
    df["ema20_slope"] = df["ema20"].pct_change(5).fillna(0.0)
    return df


def is_defensive_market(market: str) -> bool:
    return market.startswith("GLD")


def signal_direction(row: pd.Series, variant: dict[str, Any]) -> int:
    root = str(row["parent_regime_root"])
    market = str(row["market"])
    mode = str(variant["mode"])
    lookback = int(variant["lookback"])
    ema_col = f"ema{int(variant['ema'])}"
    trend = float(row.get(f"ret{lookback}", row["ret5"]))
    z_value = float(row["z20"])
    close = float(row["close"])
    ema_value = float(row[ema_col])
    vix = float(row["source_ticker_vix"])
    atr_pct = float(row["atr_pct"])
    z_threshold = float(variant["z"])

    if root == "Bull":
        if mode == "reversion":
            return 1 if z_value < -z_threshold and close > float(row["ema50"]) else 0
        if mode == "defensive" and is_defensive_market(market):
            return 0
        return 1 if trend > 0 and close > ema_value else 0

    if root == "Bear":
        if mode == "reversion":
            return -1 if z_value > z_threshold and close < float(row["ema50"]) else 0
        if mode == "defensive" and is_defensive_market(market):
            return 1 if trend > 0 and close > ema_value else 0
        return -1 if trend < 0 and close < ema_value else 0

    if root == "Sideways":
        low_slope = abs(float(row["ema20_slope"])) < max(0.004, atr_pct * 0.35)
        if not low_slope and mode != "reversion":
            return 0
        if z_value >= z_threshold:
            return -1
        if z_value <= -z_threshold:
            return 1
        return 0

    if root == "Crisis":
        if mode == "defensive" and is_defensive_market(market):
            return 1 if trend > 0 and close > ema_value else 0
        if mode == "reversion":
            return 1 if z_value < -1.8 and float(row["ret1"]) > 0 and vix < 35 else 0
        if mode == "tail_short":
            return -1 if (trend < 0 or float(row["ret3"]) < 0) and (close < ema_value or vix >= 28) else 0
        return -1 if trend < 0 and close < ema_value else 0

    return 0


def build_trade_rows(df: pd.DataFrame, variant: dict[str, Any]) -> list[dict[str, Any]]:
    if df.empty:
        return []
    variant_id = str(variant["variant_id"])
    timeframe = str(df["timeframe"].iloc[0])
    market = str(df["market"].iloc[0])
    hold = int(variant["hold"].get(timeframe, 5))
    cost = roundtrip_cost(market, timeframe)
    rows: list[dict[str, Any]] = []
    next_allowed = 0
    for idx, row in df.iterrows():
        if idx < next_allowed or idx + hold >= len(df):
            continue
        root = str(row["parent_regime_root"])
        if root not in ROOTS:
            continue
        direction = signal_direction(row, variant)
        if direction == 0:
            continue
        exit_idx = idx + hold
        exit_row = df.iloc[exit_idx]
        entry = float(row["close"])
        exit_price = float(exit_row["close"])
        if entry <= 0 or exit_price <= 0:
            continue
        gross = direction * (exit_price / entry - 1.0)
        pnl = gross - cost
        fields = branch_fields(root)
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": RUN_ID,
                "recipe_id": RECIPE_ID,
                "variant_id": variant_id,
                "market": market,
                "timeframe": timeframe,
                "trade_id": f"{RECIPE_ID}:{variant_id}:{market}:{timeframe}:{idx}",
                "open_date": row["date"].isoformat(),
                "close_date": exit_row["date"].isoformat(),
                "open_session_date": pd.Timestamp(row["session_date"]).date().isoformat(),
                "source_anchor": SOURCE_TICKER,
                "parent_regime_root": root,
                "parent_regime_confidence_floor": float(row["parent_regime_confidence_floor"]),
                "source_ticker_confidence": float(row["source_ticker_confidence"]),
                "source_ticker_vix": float(row["source_ticker_vix"]),
                "manipulation_overlay_state": "not_consumed_no_direct_event_rows",
                "sub_regime_tags": fields["sub_regime_tags"],
                "sub_sub_regime_or_profit_factor": fields["sub_sub_regime_or_profit_factor"],
                "profit_factor_family": fields["profit_factor_family"],
                "profit_factor_leaf": f"{RECIPE_ID}:{variant_id}",
                "regime_profit_branch_path": branch_path(root, variant_id),
                "regime_profit_branch_path_version": SCHEMA_VERSION,
                "trade_or_bar_horizon": f"{timeframe}_hold_{hold}",
                "allowed_action": fields["allowed_action"],
                "suppression_rule": fields["suppression_rule"],
                "direction": "long" if direction > 0 else "short",
                "direction_sign": direction,
                "entry_close": entry,
                "exit_close": exit_price,
                "gross_return": gross,
                "roundtrip_cost": cost,
                "profit_ratio_net": pnl,
                "year_fold": int(pd.Timestamp(row["date"]).year),
                "root_lookup_status": row["root_lookup_status"],
            }
        )
        next_allowed = exit_idx + 1
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bootstrap_lcb(values: np.ndarray, seed: int = 42) -> float:
    if len(values) == 0:
        return 0.0
    rng = np.random.default_rng(seed)
    sample_count = 400
    means = np.empty(sample_count)
    for i in range(sample_count):
        means[i] = rng.choice(values, size=len(values), replace=True).mean()
    return float(np.percentile(means, 5))


def max_drawdown(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    equity = np.cumsum(values)
    peaks = np.maximum.accumulate(equity)
    return float(np.max(peaks - equity))


def pbo_for_root(root: str, all_rows: list[dict[str, Any]]) -> tuple[float, str]:
    root_rows = [r for r in all_rows if r["parent_regime_root"] == root]
    folds = sorted({int(r["year_fold"]) for r in root_rows})
    variants = sorted({str(r["variant_id"]) for r in root_rows})
    if len(folds) < MIN_TEST_FOLDS or len(variants) < 3:
        return 1.0, "not_identifiable_lt4_folds_or_lt3_variants"
    bad = 0
    cases = 0
    for test_fold in folds:
        train_scores: dict[str, float] = {}
        test_scores: dict[str, float] = {}
        for variant in variants:
            train = [
                float(r["profit_ratio_net"])
                for r in root_rows
                if str(r["variant_id"]) == variant and int(r["year_fold"]) != test_fold
            ]
            test = [
                float(r["profit_ratio_net"])
                for r in root_rows
                if str(r["variant_id"]) == variant and int(r["year_fold"]) == test_fold
            ]
            if len(train) >= 20 and len(test) >= 5:
                train_scores[variant] = float(np.mean(train))
                test_scores[variant] = float(np.mean(test))
        if len(train_scores) < 3 or len(test_scores) < 3:
            continue
        selected = max(train_scores, key=train_scores.get)
        median_test = float(np.median(list(test_scores.values())))
        if test_scores.get(selected, -999.0) < median_test:
            bad += 1
        cases += 1
    if cases == 0:
        return 1.0, "not_identifiable_insufficient_variant_fold_matrix"
    return bad / cases, "simple_cscv_variant_year_fold_proxy"


def summarize_rows(
    *,
    root: str,
    variant_id: str,
    rows: list[dict[str, Any]],
    all_rows: list[dict[str, Any]],
    pbo: float,
    pbo_method: str,
) -> dict[str, Any]:
    values = np.array([float(r["profit_ratio_net"]) for r in rows], dtype=float)
    costs = np.array([float(r["roundtrip_cost"]) for r in rows], dtype=float)
    total = int(len(values))
    folds = sorted({int(r["year_fold"]) for r in rows})
    fold_returns = [
        float(np.sum([float(r["profit_ratio_net"]) for r in rows if int(r["year_fold"]) == fold]))
        for fold in folds
    ]
    fold_counts = [
        int(sum(1 for r in rows if int(r["year_fold"]) == fold))
        for fold in folds
    ]
    fold_positive_rate = (
        float(sum(1 for value in fold_returns if value > 0) / len(fold_returns))
        if fold_returns
        else 0.0
    )
    min_fold_trades = min(fold_counts) if fold_counts else 0
    mean = float(np.mean(values)) if total else 0.0
    std = float(np.std(values, ddof=1)) if total > 1 else 0.0
    dsr = float(mean / std * math.sqrt(total)) if std > 0 and total > 1 else 0.0
    lcb = bootstrap_lcb(values, seed=42 + len(root) + len(variant_id))
    stressed = values - costs if total else values
    stressed_lcb = bootstrap_lcb(stressed, seed=142 + len(root) + len(variant_id))
    tail_loss = float(max(0.0, -np.percentile(values, 5))) if total else 0.0
    outside = np.array(
        [
            float(r["profit_ratio_net"])
            for r in all_rows
            if r["parent_regime_root"] != root and str(r["variant_id"]) == variant_id
        ],
        dtype=float,
    )
    outside_mean = float(np.mean(outside)) if len(outside) else 0.0
    if mean <= 0:
        specificity = 0.0
    elif outside_mean <= 0:
        specificity = 999.0
    else:
        specificity = float(mean / max(outside_mean, 1e-9))

    edge_score = max(0.0, min(lcb / TARGET_EDGE, 1.0))
    fold_score = fold_positive_rate
    depth_score = max(0.0, min(total / MIN_TOTAL_TRADES, 1.0))
    dsr_score = max(0.0, min(dsr / TARGET_DSR, 1.0))
    pbo_score = 1.0 - max(0.0, min(pbo / 0.25, 1.0))
    cost_score = 1.0 if stressed_lcb > 0 else 0.0
    drawdown_score = 1.0 - max(0.0, min(max_drawdown(values) / DRAWDOWN_BUDGET, 1.0))
    specificity_score = max(0.0, min((specificity - 1.0) / 0.5, 1.0))
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
    if total < MIN_TOTAL_TRADES:
        failures.append("reject_thin_trades")
    if len(folds) < MIN_TEST_FOLDS:
        failures.append("reject_insufficient_test_folds")
    if min_fold_trades < MIN_TRADES_PER_TEST_FOLD:
        failures.append("reject_fold_trade_depth")
    if fold_positive_rate < FOLD_POSITIVE_RATE_MIN:
        failures.append("reject_fold_inconsistency")
    if lcb <= 0:
        failures.append("reject_no_positive_edge")
    if stressed_lcb <= 0:
        failures.append("reject_cost_fragile")
    if pbo > 0.25:
        failures.append("reject_overfit_risk")
    if dsr <= 0:
        failures.append("reject_dsr_nonpositive")
    if tail_loss > TAIL_LOSS_BUDGET:
        failures.append("reject_tail_risk")
    if specificity < 1.20:
        failures.append("reject_no_regime_specificity")
    if rc_spa < 60:
        failures.append("reject_rc_spa_below_60")
    hard_gate = "pass" if not failures else "fail:" + "|".join(failures)
    return {
        "recipe_id": RECIPE_ID,
        "parent_regime_root": root,
        "selected_variant_id": variant_id,
        "regime_profit_branch_path": branch_path(root, variant_id),
        "total_trades": total,
        "test_folds": len(folds),
        "folds": ",".join(str(fold) for fold in folds),
        "min_trades_per_test_fold": min_fold_trades,
        "fold_positive_rate": fold_positive_rate,
        "win_rate": float(np.mean(values > 0)) if total else 0.0,
        "mean_profit_ratio_net": mean,
        "net_return_R": float(np.sum(values)) if total else 0.0,
        "bootstrap_edge_lcb_5pct": lcb,
        "bootstrap_edge_lcb_5pct_stressed_2x_cost": stressed_lcb,
        "pbo": pbo,
        "pbo_method": pbo_method,
        "dsr": dsr,
        "dsr_method": "trade_return_sharpe_proxy_not_full_deflated_sharpe",
        "cost_stress_result": "pass" if stressed_lcb > 0 else "fail",
        "tail_loss_p95": tail_loss,
        "max_drawdown_trade_equity_proxy": max_drawdown(values),
        "regime_specificity_ratio": specificity,
        "outside_mean_profit_ratio_net": outside_mean,
        "rc_spa": rc_spa,
        "promotion_level": "reject" if hard_gate != "pass" or rc_spa < 60 else "stable_candidate",
        "hard_gate_result": hard_gate,
        "downstream_consumption_status": "not_started:blocked_by_branch_rc_spa_hard_gates",
    }


def summarize_root(root: str, all_rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if root == "Manipulation(scoped)":
        row = summarize_rows(
            root=root,
            variant_id="no_direct_event_rows",
            rows=[],
            all_rows=all_rows,
            pbo=1.0,
            pbo_method="no_direct_event_rows",
        )
        row["regime_profit_branch_path"] = branch_path(root, "no_direct_event_rows")
        return row, [row]
    pbo, pbo_method = pbo_for_root(root, all_rows)
    summaries: list[dict[str, Any]] = []
    for variant in [str(v["variant_id"]) for v in VARIANTS]:
        rows = [
            r
            for r in all_rows
            if r["parent_regime_root"] == root and str(r["variant_id"]) == variant
        ]
        summaries.append(
            summarize_rows(
                root=root,
                variant_id=variant,
                rows=rows,
                all_rows=all_rows,
                pbo=pbo,
                pbo_method=pbo_method,
            )
        )
    selected = max(summaries, key=lambda row: float(row["rc_spa"]))
    return selected, summaries


def write_report(report: dict[str, Any]) -> None:
    decision = report["decision"]
    panel_lines = [
        "| Market | TF | Variant | Trades | Mean | Win Rate | Net R |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for row in report["panel_summaries"]:
        panel_lines.append(
            f"| {row['market']} | {row['timeframe']} | `{row['variant_id']}` | "
            f"{row['trades']} | {row['mean_profit_ratio']:.6f} | "
            f"{row['win_rate']:.4f} | {row['net_return_R']:.6f} |"
        )
    branch_lines = [
        "| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["branch_summaries"]:
        branch_lines.append(
            f"| {row['parent_regime_root']} | `{row['selected_variant_id']}` | "
            f"{row['total_trades']} | {row['test_folds']} | "
            f"{row['min_trades_per_test_fold']} | {row['fold_positive_rate']:.4f} | "
            f"{row['bootstrap_edge_lcb_5pct']:.6f} | {row['pbo']:.3f} | "
            f"{row['dsr']:.4f} | {row['rc_spa']:.4f} | `{row['hard_gate_result']}` |"
        )
    lines = [
        "# Root Transition Triad RC-SPA v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{decision['gate_result']}`",
        f"- Stable profit score: `{decision['stable_profit_score']:.4f}`",
        f"- Variant rows: `{decision['variant_trade_rows']}`",
        f"- Selected rows: `{decision['selected_trade_rows']}`",
        f"- Branch paths evaluated: `{decision['branch_paths_evaluated']}`",
        f"- Branch paths passed: `{decision['branch_paths_passed']}`",
        f"- Selected root counts: `{decision['selected_root_trade_counts']}`",
        f"- Downstream consumption: `{decision['downstream_consumption']}`",
        f"- Primary blocker: {decision['primary_blocker']}",
        "",
        "## Panel / Variant Summary",
        "",
        *panel_lines,
        "",
        "## Selected Branch Summary",
        "",
        *branch_lines,
        "",
        "## Inputs",
        "",
        f"- Local Auto-Quant feathers: `{DATA_DIR}`",
        f"- Board A consumer map: `{rel(BOARD_A_CONSUMER_MAP)}`",
        f"- Source root schedule: `{SOURCE_REGIME_CSV}` / `{SOURCE_TICKER}`",
        "",
        "## Artifacts",
        "",
        f"- Report JSON: `{rel(REPORT_JSON)}`",
        f"- Selected rows: `{rel(SELECTED_ROWS_CSV)}`",
        f"- Variant rows: `{rel(ALL_ROWS_CSV)}`",
        f"- Branch summary: `{rel(SUMMARY_CSV)}`",
        f"- Panel summary: `{rel(PANEL_SUMMARY_CSV)}`",
        f"- Fail-closed downstream summary: `{rel(FAIL_CLOSED_MD)}`",
        f"- Assertions: `{rel(ASSERTIONS)}`",
        "",
        "## Next",
        "",
        f"- {decision['next_action']}",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    for path in [OUT_DIR, CHECK_DIR, FAIL_CLOSED_DIR]:
        path.mkdir(parents=True, exist_ok=True)
    required_inputs = [SOURCE_REGIME_CSV, BOARD_A_CONSUMER_MAP]
    missing = [str(path) for path in required_inputs if not path.exists() or path.stat().st_size == 0]
    missing += [str(path) for _, _, path in PANELS if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise RuntimeError("missing required inputs: " + ", ".join(missing))

    floors = load_root_floors()
    source = load_source_roots()
    lookup = RootLookup(source, floors)
    all_rows: list[dict[str, Any]] = []
    panel_summaries: list[dict[str, Any]] = []
    for market, timeframe, path in PANELS:
        panel = load_panel(path, market, timeframe, lookup)
        for variant in VARIANTS:
            rows = build_trade_rows(panel, variant)
            all_rows.extend(rows)
            values = np.array([float(r["profit_ratio_net"]) for r in rows], dtype=float)
            panel_summaries.append(
                {
                    "market": market,
                    "timeframe": timeframe,
                    "variant_id": variant["variant_id"],
                    "bars": int(len(panel)),
                    "trades": int(len(rows)),
                    "mean_profit_ratio": float(np.mean(values)) if len(values) else 0.0,
                    "win_rate": float(np.mean(values > 0)) if len(values) else 0.0,
                    "net_return_R": float(np.sum(values)) if len(values) else 0.0,
                }
            )

    branch_summaries: list[dict[str, Any]] = []
    variant_summaries: list[dict[str, Any]] = []
    selected_rows: list[dict[str, Any]] = []
    for root in REQUIRED_PATHS:
        selected, variants = summarize_root(root, all_rows)
        branch_summaries.append(selected)
        variant_summaries.extend(variants)
        selected_variant = str(selected["selected_variant_id"])
        selected_rows.extend(
            [
                r
                for r in all_rows
                if r["parent_regime_root"] == root and str(r["variant_id"]) == selected_variant
            ]
        )

    passed = [row for row in branch_summaries if row["hard_gate_result"] == "pass"]
    max_score = max(float(row["rc_spa"]) for row in branch_summaries) if branch_summaries else 0.0
    selected_counts = {root: 0 for root in REQUIRED_PATHS}
    for row in selected_rows:
        selected_counts[row["parent_regime_root"]] = selected_counts.get(row["parent_regime_root"], 0) + 1
    selected_counts["Manipulation(scoped)"] = 0
    matrix_counts = {root: 0 for root in REQUIRED_PATHS}
    for row in all_rows:
        matrix_counts[row["parent_regime_root"]] = matrix_counts.get(row["parent_regime_root"], 0) + 1
    matrix_counts["Manipulation(scoped)"] = 0

    root_failures = [
        f"{row['parent_regime_root']}={row['hard_gate_result']}"
        for row in branch_summaries
        if row["hard_gate_result"] != "pass"
    ]
    all_required_pass = len(passed) == len(REQUIRED_PATHS)
    gate_result = "pass" if all_required_pass else "fail:required_root_branch_hard_gates_failed"
    downstream = (
        "eligible_for_pre_bayes_bbn_catboost_execution_tree_probe"
        if all_required_pass
        else "not_started:blocked_by_branch_rc_spa_hard_gates"
    )
    primary_blocker = "all required branch hard gates passed" if all_required_pass else "; ".join(root_failures)
    next_action = (
        "B5: run Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree branch consumption."
        if all_required_pass
        else "B2R-repeat: keep RootTransitionTriad as fail-closed evidence; direct Manipulation still needs trade/PnL rows, and failed roots need a different family or provider panel without relaxing RC-SPA."
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "run_root": rel(RUN_ROOT),
        "repo_git_ref": git_ref(REPO_ROOT),
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "accepted_regime_artifact": rel(BOARD_A_CONSUMER_MAP),
        "recipe_id": RECIPE_ID,
        "inputs": {
            "data_dir": str(DATA_DIR),
            "source_regime_csv": str(SOURCE_REGIME_CSV),
            "source_ticker": SOURCE_TICKER,
            "board_a_consumer_map": rel(BOARD_A_CONSUMER_MAP),
        },
        "decision": {
            "gate_result": gate_result,
            "stable_profit_score": max_score,
            "variant_trade_rows": len(all_rows),
            "selected_trade_rows": len(selected_rows),
            "branch_paths_evaluated": len(branch_summaries),
            "branch_paths_passed": len(passed),
            "selected_root_trade_counts": selected_counts,
            "matrix_root_trade_counts": matrix_counts,
            "downstream_consumption": downstream,
            "primary_blocker": primary_blocker,
            "next_action": next_action,
        },
        "branch_summaries": branch_summaries,
        "variant_summaries": variant_summaries,
        "panel_summaries": panel_summaries,
        "artifacts": {
            "report_json": rel(REPORT_JSON),
            "report_md": rel(REPORT_MD),
            "selected_rows_csv": rel(SELECTED_ROWS_CSV),
            "all_rows_csv": rel(ALL_ROWS_CSV),
            "summary_csv": rel(SUMMARY_CSV),
            "panel_summary_csv": rel(PANEL_SUMMARY_CSV),
            "assertions": rel(ASSERTIONS),
            "fail_closed_summary": rel(FAIL_CLOSED_MD),
        },
        "completion": {
            "runtime_code_changed": False,
            "auto_quant_checkout_changed": False,
            "raw_auto_quant_data_committed": False,
            "thresholds_relaxed_after_scoring": False,
            "downstream_runtime_consumed_branch_path": all_required_pass,
        },
    }

    write_csv(ALL_ROWS_CSV, all_rows)
    write_csv(SELECTED_ROWS_CSV, selected_rows)
    write_csv(SUMMARY_CSV, branch_summaries)
    write_csv(PANEL_SUMMARY_CSV, panel_summaries)
    write_json(REPORT_JSON, report)
    write_report(report)
    FAIL_CLOSED_MD.write_text(
        "\n".join(
            [
                "# Root Transition Triad ict-engine Fail-Closed Summary v1",
                "",
                f"Run id: `{RUN_ID}`.",
                "",
                f"- Branch RC-SPA gate: `{gate_result}`",
                f"- Downstream consumption: `{downstream}`",
                "- Pre-Bayes / BBN / CatBoost / execution-tree were not started unless every required branch hard gate passed.",
                "- This is a fail-closed readback, not a promoted profitability packet.",
                "",
                f"Primary blocker: {primary_blocker}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assertions = [
        f"run_id={RUN_ID}",
        f"variant_trade_rows={len(all_rows)}",
        f"selected_trade_rows={len(selected_rows)}",
        f"branch_paths_evaluated={len(branch_summaries)}",
        f"branch_paths_passed={len(passed)}",
        f"gate_result={gate_result}",
        f"downstream_consumption={downstream}",
        "artifacts_exist=true",
    ]
    if not all_rows:
        assertions.append("ASSERT_FAIL:no_variant_trade_rows")
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 1 if any(line.startswith("ASSERT_FAIL") for line in assertions) else 0


if __name__ == "__main__":
    raise SystemExit(main())
