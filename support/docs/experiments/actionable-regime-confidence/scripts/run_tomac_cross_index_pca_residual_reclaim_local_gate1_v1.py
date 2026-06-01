#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
BASE = REPO / "support/docs/experiments/actionable-regime-confidence"
RESEARCH_HELPERS = REPO / "support/scripts/research"
if str(RESEARCH_HELPERS) not in sys.path:
    sys.path.insert(0, str(RESEARCH_HELPERS))

import instrument_cost_model as cost_model  # noqa: E402

CLAIM_AUDIT = REPO / "support/scripts/factor_claim_terminalization_audit.py"
PARQUET_CACHE = Path("/Users/thrill3r/Downloads/Tomac/factor_training/cache")
FEATHER_CACHE = Path("/Users/thrill3r/Auto-Quant/user_data/data")
STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
DEFAULT_ROOT = Path("/tmp") / f"ict-engine-cross-index-pca-residual-reclaim-local-gate1-{STAMP}"
DEFAULT_COMPACT_ROOT = BASE / "runs" / f"{STAMP}-codex-cross-index-pca-residual-reclaim-local-gate1-v1"

FACTOR_ID = "cross_index_pca_residual_reclaim_v1"
BRANCH_PATH = (
    "TrendExpansion -> CrossIndexTrendBreadth -> ResidualMomentumBetaNeutralAdmission -> "
    "PCAResidualDislocation -> VwapReclaimOrFade -> cross_index_pca_residual_reclaim_v1"
)
SESSION_SCOPE = "ETH/full_retained_session"
RTH_FILTER_APPLIED = False
TIMEFRAMES = ("1m", "5m", "15m", "30m", "1h", "4h", "1d")
CONTEXT_RULES = {
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "1h",
    "4h": "4h",
    "1d": "1D",
}
@dataclass(frozen=True)
class PcaResidualVariant:
    slug: str
    side: int
    residual_z_abs_min: float
    min_residual_momentum_bps: float
    min_mtf_aligned: int
    max_mtf_opposed: int
    stop_atr: float
    target_atr: float
    max_hold_bars: int
    signal_interval_minutes: int

    @property
    def branch_path(self) -> str:
        side_name = "Long" if self.side == 1 else "Short"
        return f"{BRANCH_PATH} -> {side_name}{self.slug}"


def variants() -> list[PcaResidualVariant]:
    return [
        PcaResidualVariant("DenseResidualReclaimMtf2", 1, 1.00, 0.35, 2, 3, 0.75, 1.10, 90, 15),
        PcaResidualVariant("QualityResidualReclaimMtf3", 1, 1.35, 0.55, 3, 2, 0.85, 1.40, 120, 30),
        PcaResidualVariant("DeepResidualSnapback", 1, 1.80, 0.80, 3, 2, 0.95, 1.75, 150, 30),
        PcaResidualVariant("DenseResidualFadeMtf2", -1, 1.00, 0.35, 2, 3, 0.75, 1.10, 90, 15),
        PcaResidualVariant("QualityResidualFadeMtf3", -1, 1.35, 0.55, 3, 2, 0.85, 1.40, 120, 30),
        PcaResidualVariant("DeepResidualSnapback", -1, 1.80, 0.80, 3, 2, 0.95, 1.75, 150, 30),
    ]


def factor_id(symbol: str, variant: PcaResidualVariant) -> str:
    side = "long" if variant.side == 1 else "short"
    return f"tomac_{symbol.lower()}_cross_index_pca_residual_reclaim_{side}_{variant.slug.lower()}_local_gate1_v1"


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    time_column = next((name for name in ("timestamp", "datetime", "date") if name in out.columns), None)
    if time_column is None:
        out = out.reset_index()
        time_column = next((name for name in ("timestamp", "datetime", "date", "index") if name in out.columns), out.columns[0])
    out[time_column] = pd.to_datetime(out[time_column], utc=True)
    out = out.rename(columns={time_column: "timestamp"}).sort_values("timestamp")
    out = out.drop_duplicates("timestamp", keep="last").set_index("timestamp")
    for column in ("open", "high", "low", "close", "volume"):
        out[column] = pd.to_numeric(out[column], errors="coerce")
    out = out.dropna(subset=["open", "high", "low", "close"])
    out["volume"] = out["volume"].fillna(0.0)
    return out[["open", "high", "low", "close", "volume"]]


def read_frame(symbol: str, timeframe: str) -> pd.DataFrame:
    parquet = PARQUET_CACHE / f"{symbol}_{timeframe}.parquet"
    if parquet.exists():
        return normalize_ohlcv(pd.read_parquet(parquet))
    feather = FEATHER_CACHE / f"{symbol}_USD-{timeframe}.feather"
    if feather.exists():
        return normalize_ohlcv(pd.read_feather(feather))
    futures_feather = FEATHER_CACHE / "futures" / f"{symbol}_USD-{timeframe}-futures.feather"
    if futures_feather.exists():
        return normalize_ohlcv(pd.read_feather(futures_feather))
    raise FileNotFoundError(f"missing TOMAC local cache for {symbol} {timeframe}: {parquet} or {feather} or {futures_feather}")


def true_range(df: pd.DataFrame) -> pd.Series:
    previous_close = df["close"].shift(1)
    return pd.concat(
        [
            (df["high"] - df["low"]).abs(),
            (df["high"] - previous_close).abs(),
            (df["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def add_session_features(df: pd.DataFrame) -> pd.DataFrame:
    out = normalize_ohlcv(df)
    ny = out.index.tz_convert("America/New_York")
    out["session_date"] = ny.strftime("%Y-%m-%d")
    out["minute"] = out.index.hour * 60 + out.index.minute
    out["tr"] = true_range(out)
    out["atr14"] = out["tr"].rolling(14, min_periods=8).mean()
    typical = (out["high"] + out["low"] + out["close"]) / 3.0
    volume = out["volume"].clip(lower=0.0).replace(0.0, np.nan)
    tpv = (typical * volume).groupby(out["session_date"]).cumsum()
    cum_volume = volume.groupby(out["session_date"]).cumsum()
    out["session_vwap"] = tpv / cum_volume
    out["ema20"] = out["close"].ewm(span=20, adjust=False, min_periods=8).mean()
    return out


def _close_matrix(frames: dict[str, pd.DataFrame], symbols: list[str]) -> pd.DataFrame:
    columns: dict[str, pd.Series] = {}
    for symbol in symbols:
        columns[symbol] = normalize_ohlcv(frames[symbol])["close"]
    return pd.DataFrame(columns).sort_index().ffill().dropna()


def add_cross_index_pca_residual_features(
    frames: dict[str, pd.DataFrame],
    target: str,
    lookback: int = 120,
    z_window: int = 240,
) -> pd.DataFrame:
    symbols = [target] + sorted(symbol for symbol in frames if symbol != target)
    prices = _close_matrix(frames, symbols)
    returns = prices.pct_change()
    target_pos = symbols.index(target)
    residual_values = pd.Series(np.nan, index=prices.index, dtype="float64")
    common_values = pd.Series(np.nan, index=prices.index, dtype="float64")
    explained_values = pd.Series(np.nan, index=prices.index, dtype="float64")

    for idx in range(lookback + 1, len(returns)):
        window = returns.iloc[idx - lookback : idx].dropna()
        current = returns.iloc[idx]
        if len(window) < lookback or current.isna().any():
            continue
        matrix = window[symbols].to_numpy(dtype=float)
        mean = matrix.mean(axis=0)
        centered = matrix - mean
        try:
            _, singular_values, vt = np.linalg.svd(centered, full_matrices=False)
        except np.linalg.LinAlgError:
            continue
        if len(vt) == 0 or singular_values.sum() <= 0:
            continue
        component = vt[0]
        current_centered = current[symbols].to_numpy(dtype=float) - mean
        common_projection = float(current_centered @ component)
        reconstructed = common_projection * component
        residual = current_centered - reconstructed
        residual_values.iloc[idx] = float(residual[target_pos]) * 10000.0
        common_values.iloc[idx] = float(reconstructed[target_pos]) * 10000.0
        explained_values.iloc[idx] = float((singular_values[0] ** 2) / np.sum(singular_values**2))

    residual_mean = residual_values.rolling(z_window, min_periods=max(20, min(z_window, 40))).mean().shift(1)
    residual_std = residual_values.rolling(z_window, min_periods=max(20, min(z_window, 40))).std(ddof=0).shift(1).replace(0.0, np.nan)
    featured = add_session_features(frames[target]).reindex(prices.index).ffill()
    featured["pca_residual"] = residual_values
    featured["pca_common_component_bps"] = common_values
    featured["pca_common_explained_variance"] = explained_values
    featured["pca_residual_z"] = (residual_values - residual_mean) / residual_std
    featured["pca_residual_momentum_bps"] = residual_values.diff(3)
    return featured


def _context_features(context: pd.DataFrame, label: str) -> pd.DataFrame:
    ctx = normalize_ohlcv(context).dropna(subset=["close"]).copy()
    ctx[f"ctx_{label}_ema20"] = ctx["close"].ewm(span=20, adjust=False, min_periods=8).mean()
    ctx[f"ctx_{label}_ema50"] = ctx["close"].ewm(span=50, adjust=False, min_periods=15).mean()
    ctx[f"ctx_{label}_slope_bps"] = (ctx[f"ctx_{label}_ema20"] / ctx[f"ctx_{label}_ema20"].shift(3) - 1.0) * 10000.0
    columns = [f"ctx_{label}_ema20", f"ctx_{label}_ema50", f"ctx_{label}_slope_bps"]
    return ctx[columns].shift(1).reset_index().sort_values("timestamp")


def add_mtf_context(target: pd.DataFrame, context_frames: dict[str, pd.DataFrame] | None = None, contexts: list[str] | None = None) -> pd.DataFrame:
    base = target.reset_index().sort_values("timestamp")
    frames = context_frames or {}
    labels = contexts or list(CONTEXT_RULES)
    for label in labels:
        rule = CONTEXT_RULES[label]
        context = frames.get(label)
        if context is None:
            context = target[["open", "high", "low", "close", "volume"]].resample(rule, label="right", closed="right").agg(
                {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
            )
        ctx = _context_features(context, label)
        base = pd.merge_asof(base, ctx, on="timestamp", direction="backward")
    out = base.set_index("timestamp")
    long_align = pd.Series(0, index=out.index, dtype="int16")
    short_align = pd.Series(0, index=out.index, dtype="int16")
    checked = pd.Series(0, index=out.index, dtype="int16")
    for label in labels:
        valid = out[f"ctx_{label}_ema20"].notna() & out[f"ctx_{label}_ema50"].notna() & out[f"ctx_{label}_slope_bps"].notna()
        checked += valid.astype("int16")
        long_align += (
            valid & (out[f"ctx_{label}_ema20"] > out[f"ctx_{label}_ema50"]) & (out[f"ctx_{label}_slope_bps"] > 0)
        ).astype("int16")
        short_align += (
            valid & (out[f"ctx_{label}_ema20"] < out[f"ctx_{label}_ema50"]) & (out[f"ctx_{label}_slope_bps"] < 0)
        ).astype("int16")
    out["mtf_checked"] = checked
    out["mtf_long_aligned"] = long_align
    out["mtf_short_aligned"] = short_align
    return out


def build_signal(df: pd.DataFrame, variant: PcaResidualVariant) -> pd.Series:
    interval_ok = (df["minute"] % variant.signal_interval_minutes) == 0
    if variant.side == 1:
        dislocated = df["pca_residual_z"] <= -variant.residual_z_abs_min
        momentum = df["pca_residual_momentum_bps"] >= variant.min_residual_momentum_bps
        reclaim = (df["close"] > df["session_vwap"]) & (df["close"] > df["ema20"])
        mtf_ok = (df["mtf_long_aligned"] >= variant.min_mtf_aligned) & (df["mtf_short_aligned"] <= variant.max_mtf_opposed)
    else:
        dislocated = df["pca_residual_z"] >= variant.residual_z_abs_min
        momentum = df["pca_residual_momentum_bps"] <= -variant.min_residual_momentum_bps
        reclaim = (df["close"] < df["session_vwap"]) & (df["close"] < df["ema20"])
        mtf_ok = (df["mtf_short_aligned"] >= variant.min_mtf_aligned) & (df["mtf_long_aligned"] <= variant.max_mtf_opposed)
    return (dislocated & momentum & reclaim & mtf_ok & interval_ok).fillna(False)


def simulate_trades(symbol: str, df: pd.DataFrame, variant: PcaResidualVariant) -> list[dict[str, object]]:
    signal_idx = np.flatnonzero(build_signal(df, variant).to_numpy(dtype=bool))
    if len(signal_idx) == 0:
        return []
    open_values = df["open"].to_numpy(dtype=float)
    close_values = df["close"].to_numpy(dtype=float)
    high_values = df["high"].to_numpy(dtype=float)
    low_values = df["low"].to_numpy(dtype=float)
    atr_values = df["atr14"].to_numpy(dtype=float)
    sessions = df["session_date"].to_numpy(dtype=str)
    years = df.index.tz_convert("America/New_York").year.astype(int).to_numpy()
    timestamps = df.index.astype(str).to_numpy()
    trades: list[dict[str, object]] = []
    next_available = 0
    side = variant.side
    for idx in signal_idx:
        entry_idx = idx + 1
        if entry_idx <= next_available or entry_idx >= len(df):
            continue
        entry = open_values[entry_idx]
        atr_now = atr_values[idx]
        if not math.isfinite(entry) or not math.isfinite(atr_now) or entry <= 0 or atr_now <= 0:
            continue
        stop = entry - side * variant.stop_atr * atr_now
        target_price = entry + side * variant.target_atr * atr_now
        max_exit = min(entry_idx + variant.max_hold_bars, len(df) - 1)
        exit_idx = max_exit
        exit_price = close_values[max_exit]
        exit_reason = "timeout"
        for probe in range(entry_idx + 1, max_exit + 1):
            if side == 1:
                hit_stop = low_values[probe] <= stop
                hit_target = high_values[probe] >= target_price
            else:
                hit_stop = high_values[probe] >= stop
                hit_target = low_values[probe] <= target_price
            if hit_stop or hit_target:
                exit_idx = probe
                if hit_stop and hit_target:
                    exit_price = stop
                    exit_reason = "same_bar_stop_first"
                elif hit_stop:
                    exit_price = stop
                    exit_reason = "stop"
                else:
                    exit_price = target_price
                    exit_reason = "target"
                break
        raw_return = side * (exit_price / entry - 1.0)
        real_fee_return = cost_model.real_fee_round_turn_fraction(symbol, entry)
        trades.append(
            {
                "symbol": symbol,
                "factor_id": factor_id(symbol, variant),
                "branch_path": variant.branch_path,
                "entry_time": timestamps[entry_idx],
                "exit_time": timestamps[exit_idx],
                "entry_session": sessions[entry_idx],
                "year": int(years[entry_idx]),
                "side": "long" if side == 1 else "short",
                "entry": round(float(entry), 8),
                "exit": round(float(exit_price), 8),
                "raw_return": float(raw_return),
                "real_fee_round_turn_return": float(real_fee_return),
                "net_instrument_cost_return": float(raw_return - real_fee_return),
                "exit_reason": exit_reason,
            }
        )
        next_available = exit_idx
    return trades


def profit_factor(values: list[float]) -> float:
    gains = sum(item for item in values if item > 0)
    losses = -sum(item for item in values if item < 0)
    if losses == 0:
        return float("inf") if gains > 0 else 0.0
    return gains / losses


def split_net(trades: list[dict[str, object]], return_key: str) -> tuple[float, float, float]:
    if not trades:
        return 0.0, 0.0, 0.0
    n = len(trades)
    chunks = (trades[: n // 3], trades[n // 3 : 2 * n // 3], trades[2 * n // 3 :])
    return tuple(round(sum(float(row[return_key]) for row in chunk) * 100.0, 6) for chunk in chunks)  # type: ignore[return-value]


def score_trades(trades: list[dict[str, object]], sessions: int, symbol: str) -> dict[str, object]:
    raw_returns = [float(row["raw_return"]) for row in trades]
    instrument_returns = [float(row["net_instrument_cost_return"]) for row in trades]
    train, validation, test = split_net(trades, "net_instrument_cost_return")
    years = sorted({int(row["year"]) for row in trades})
    year_values: dict[str, float] = {}
    years_instrument_positive = 0
    for year in years:
        total = sum(float(row["net_instrument_cost_return"]) for row in trades if int(row["year"]) == year) * 100.0
        year_values[str(year)] = round(total, 6)
        if total > 0:
            years_instrument_positive += 1
    instrument_pf = profit_factor(instrument_returns)
    representative_price = (sum(float(row["entry"]) for row in trades) / len(trades)) if trades else None
    cost_packet = cost_model.cost_model_packet(symbol, representative_price)
    return {
        "trade_count": len(trades),
        "sessions": sessions,
        "trades_per_session": round(len(trades) / sessions, 6) if sessions else 0.0,
        "raw_total_profit_pct": round(sum(raw_returns) * 100.0, 6),
        "instrument_cost_total_profit_pct": round(sum(instrument_returns) * 100.0, 6),
        "instrument_cost_profit_factor": round(instrument_pf, 6) if math.isfinite(instrument_pf) else "inf",
        "win_rate_instrument_cost": round(sum(1 for item in instrument_returns if item > 0) / len(instrument_returns), 6) if instrument_returns else 0.0,
        "train_instrument_cost_total_profit_pct": train,
        "validation_instrument_cost_total_profit_pct": validation,
        "test_instrument_cost_total_profit_pct": test,
        "years_positive": years_instrument_positive,
        "years_instrument_cost_positive": years_instrument_positive,
        "year_count": len(years),
        "year_instrument_cost_total_profit_pct": year_values,
        "cost_model": cost_packet,
        "promotion_cost_verified": bool(cost_packet.get("verified_for_promotion")),
    }


def classify(row: dict[str, object]) -> dict[str, object]:
    trade_count = int(row.get("trade_count") or 0)
    trades_per_session = float(row.get("trades_per_session") or 0.0)
    net_cost = float(row.get("instrument_cost_total_profit_pct") or 0.0)
    pf_raw = row.get("instrument_cost_profit_factor")
    pf_cost = float("inf") if pf_raw == "inf" else float(pf_raw or 0.0)
    split_ok = all(
        float(row.get(key) or 0.0) > 0
        for key in (
            "train_instrument_cost_total_profit_pct",
            "validation_instrument_cost_total_profit_pct",
            "test_instrument_cost_total_profit_pct",
        )
    )
    cost_verified = bool(row.get("promotion_cost_verified"))
    density_ok = trade_count >= 60 and (1.0 / 3.0) <= trades_per_session <= 3.0
    cost_ok = net_cost > 0.0 and pf_cost >= 1.10
    instrument_cost_candidate = bool(density_ok and cost_verified and cost_ok and split_ok)
    if instrument_cost_candidate:
        decision = "local_instrument_cost_candidate_needs_exact_aq_downstream"
    elif trade_count <= 0:
        decision = "reject_zero_trades"
    elif not cost_verified:
        decision = "reject_cost_model_unverified"
    elif not density_ok:
        decision = "reject_density_outside_033_to_3_per_session"
    elif not cost_ok:
        decision = "reject_instrument_cost_economics"
    else:
        decision = "reject_chronological_split_instability"
    return {
        "density_target_033_to_3_per_session": density_ok,
        "cost_ok_instrument_cost_pf_gte_1_10": cost_ok,
        "split_instrument_cost_positive_all_thirds": split_ok,
        "instrument_cost_candidate": instrument_cost_candidate,
        "gate1_survivor": False,
        "decision": decision,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }


def retained_session_coverage(df: pd.DataFrame) -> dict[str, object]:
    ny = df.index.tz_convert("America/New_York")
    minutes = ny.hour * 60 + ny.minute
    rth = (minutes >= 9 * 60 + 30) & (minutes < 16 * 60)
    non_rth_rows = int((~rth).sum())
    return {
        "status": "pass" if non_rth_rows > 0 else "fail",
        "non_rth_rows": non_rth_rows,
        "total_rows": int(len(df)),
        "rth_window": "09:30-16:00 America/New_York",
    }


def cache_path_for_symbol(symbol: str, origin: str) -> Path:
    parquet = PARQUET_CACHE / f"{symbol}_{origin}.parquet"
    if parquet.exists():
        return parquet
    feather = FEATHER_CACHE / f"{symbol}_USD-{origin}.feather"
    if feather.exists():
        return feather
    futures_feather = FEATHER_CACHE / "futures" / f"{symbol}_USD-{origin}-futures.feather"
    if futures_feather.exists():
        return futures_feather
    return parquet


def load_symbol_frames(symbols: list[str], origin: str, start: str, end: str, max_screen_rows: int | None) -> tuple[dict[str, pd.DataFrame], dict[str, object]]:
    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
    frames: dict[str, pd.DataFrame] = {}
    stats: dict[str, object] = {}
    for symbol in symbols:
        frame = read_frame(symbol, origin)
        frame = frame.loc[(frame.index >= start_ts) & (frame.index < end_ts)].copy()
        if max_screen_rows is not None and len(frame) > max_screen_rows:
            frame = frame.iloc[-max_screen_rows:].copy()
        frames[symbol] = frame
        stats[symbol] = {
            "rows_1m": int(len(frame)),
            "first_timestamp": frame.index.min().isoformat() if len(frame) else None,
            "last_timestamp": frame.index.max().isoformat() if len(frame) else None,
            "retained_session_coverage": retained_session_coverage(frame) if len(frame) else {"status": "fail", "non_rth_rows": 0},
            "cache_path": str(cache_path_for_symbol(symbol, origin)),
        }
    return frames, stats


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        if not keys:
            handle.write("\n")
            return
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def sample_trades(trades: list[dict[str, object]], limit_each_side: int = 80) -> list[dict[str, object]]:
    if len(trades) <= limit_each_side * 2:
        return trades
    return trades[:limit_each_side] + trades[-limit_each_side:]


def candidate_record(symbol: str, variant: PcaResidualVariant, executed: bool) -> dict[str, object]:
    return {
        "symbol": symbol,
        "factor_id": factor_id(symbol, variant),
        "parent_factor_id": FACTOR_ID,
        "branch_path": variant.branch_path,
        "provider": "tomac_retained_local_cache" if executed else "prep_only_no_data_screen",
        "market": "futures",
        "product": "equity_index",
        "origin_timeframe": "1m",
        "context_timeframes": ",".join(CONTEXT_RULES.keys()),
        "side": "long" if variant.side == 1 else "short",
        "residual_z_abs_min": variant.residual_z_abs_min,
        "min_residual_momentum_bps": variant.min_residual_momentum_bps,
        "min_mtf_aligned": variant.min_mtf_aligned,
        "max_mtf_opposed": variant.max_mtf_opposed,
        "stop_atr": variant.stop_atr,
        "target_atr": variant.target_atr,
        "prep_only": not executed,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }


def prep_records(symbol: str, root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for variant in variants():
        row = candidate_record(symbol, variant, executed=False)
        row.update(score_trades([], 0, symbol))
        row.update(classify(row))
        row["decision"] = "prep_only_no_launch_runtime_blocked"
        records.append(row)
        material = root / "materials" / f"{row['factor_id']}.json"
        material.parent.mkdir(parents=True, exist_ok=True)
        material.write_text(json.dumps(row, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return records


def resample_frame(frame: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    if timeframe == "1m":
        return normalize_ohlcv(frame)
    rule = CONTEXT_RULES[timeframe]
    return normalize_ohlcv(frame).resample(rule, label="right", closed="right").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    ).dropna(subset=["open", "high", "low", "close"])


def screen_target(symbol: str, frames: dict[str, pd.DataFrame], root: Path, contexts: list[str]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    featured = add_cross_index_pca_residual_features(frames, symbol)
    context_frames = {timeframe: resample_frame(frames[symbol], timeframe) for timeframe in contexts}
    featured = add_mtf_context(featured, context_frames, contexts)
    sessions = int(featured["session_date"].nunique()) if len(featured) else 0
    for variant in variants():
        trades = simulate_trades(symbol, featured, variant)
        row = candidate_record(symbol, variant, executed=True)
        row.update(score_trades(trades, sessions, symbol))
        row.update(classify(row))
        records.append(row)
        material = root / "materials" / f"{row['factor_id']}.json"
        material.parent.mkdir(parents=True, exist_ok=True)
        material.write_text(json.dumps(row, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        write_csv(root / "materials" / f"{row['factor_id']}_trades_sample.csv", sample_trades(trades))
    return records


def load_claim_audit() -> dict[str, object]:
    proc = subprocess.run([sys.executable, str(CLAIM_AUDIT)], cwd=REPO, text=True, capture_output=True)
    if proc.returncode not in (0, 1):
        return {"audit_error": f"claim audit rc={proc.returncode}: {proc.stderr.strip()}"}
    try:
        payload = json.loads(proc.stdout)
        return payload if isinstance(payload, dict) else {"audit_error": "claim audit returned non-object json"}
    except json.JSONDecodeError as exc:
        return {"audit_error": f"claim audit invalid json: {exc}"}


def _same_root(candidate: object, current_root: Path) -> bool:
    if not isinstance(candidate, str) or not candidate.strip():
        return False
    path = Path(candidate).expanduser().resolve(strict=False)
    current = current_root.resolve(strict=False)
    return path == current or current in path.parents or path in current.parents


def collision_guard(audit: dict[str, object], current_root: Path) -> dict[str, object]:
    claims = audit.get("claims") if isinstance(audit.get("claims"), list) else []
    processes = audit.get("live_factor_processes") if isinstance(audit.get("live_factor_processes"), list) else []
    foreign_active_claims: list[str] = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        if claim.get("status") != "active" or claim.get("coordination_only"):
            continue
        root = claim.get("run_root") or claim.get("tmp_root")
        if _same_root(root, current_root):
            continue
        foreign_active_claims.append(str(claim.get("claim_file") or root or "unknown_claim"))
    foreign_live_roots: list[str] = []
    for process in processes:
        if not isinstance(process, dict):
            continue
        root = process.get("run_root")
        if _same_root(root, current_root):
            continue
        foreign_live_roots.append(str(root or process.get("pid") or "unknown_live_process"))
    return {
        "ready": not foreign_active_claims and not foreign_live_roots and not audit.get("audit_error"),
        "foreign_active_claims": foreign_active_claims,
        "foreign_live_roots": foreign_live_roots,
        "audit_error": audit.get("audit_error"),
    }


def render_summary(
    root: Path,
    records: list[dict[str, object]],
    data_stats: dict[str, object],
    execute_local_screen: bool,
    contexts: list[str],
    *,
    local_screen_executed: bool | None = None,
    decision_override: str | None = None,
    collision_guard_result: dict[str, object] | None = None,
) -> dict[str, object]:
    root.mkdir(parents=True, exist_ok=True)
    (root / "checks").mkdir(parents=True, exist_ok=True)
    (root / "summaries").mkdir(parents=True, exist_ok=True)
    candidates = [row for row in records if row.get("instrument_cost_candidate") is True]
    best = sorted(
        records,
        key=lambda row: (
            bool(row.get("instrument_cost_candidate")),
            float(row.get("instrument_cost_total_profit_pct") or -999999.0),
            float(row.get("trades_per_session") or 0.0),
        ),
        reverse=True,
    )
    if decision_override is not None:
        decision = decision_override
    elif not execute_local_screen:
        decision = "prep_only_no_launch_runtime_blocked"
    else:
        decision = "local_instrument_cost_candidate_needs_exact_aq_downstream" if candidates else "drop_local_screen_no_instrument_cost_candidate"
    if local_screen_executed is None:
        local_screen_executed = bool(execute_local_screen and decision_override is None)
    summary = {
        "schema_version": "tomac-cross-index-pca-residual-local-gate1/v1",
        "run_root": str(root),
        "factor_id": FACTOR_ID,
        "branch_path": BRANCH_PATH,
        "session_scope": SESSION_SCOPE,
        "rth_filter_applied": RTH_FILTER_APPLIED,
        "requested_timeframes": list(TIMEFRAMES),
        "origin_timeframe": "1m",
        "context_timeframes": contexts,
        "local_screen_only": True,
        "execute_local_screen": execute_local_screen,
        "local_screen_executed": local_screen_executed,
        "provider_attempted": False,
        "ibkr_historical_attempted": False,
        "autoquant_attempted": False,
        "paper_or_live_execution_attempted": False,
        "decision": decision,
        "candidate_count": len(records),
        "instrument_cost_candidate_count": len(candidates),
        "gate1_survivor_count": 0,
        "survivors": [],
        "instrument_cost_candidates": candidates,
        "top_by_instrument_cost": best[:10],
        "data_stats": data_stats,
        "collision_guard": collision_guard_result,
        "same_tree_practical_closure": None,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "next_gate": "rerun_claim_audit_then_execute_local_screen_or_exact_aq" if not execute_local_screen else "exact_aq_downstream_after_collision_audit_clear",
    }
    (root / "checks" / "terminal_metrics.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    write_csv(root / "summaries" / "screen_rows.csv", best)
    lines = [
        "# Cross-Index PCA Residual Reclaim Local Gate 1",
        "",
        f"Decision: `{decision}`",
        f"candidate_count: `{len(records)}`",
        f"instrument_cost_candidate_count: `{len(candidates)}`",
        "gate1_survivor_count: `0`",
        "promotion_allowed: `false`",
        "trade_usable: `false`",
        "update_goal: `false`",
        "provider_or_aq_launched: `false`",
        "",
        "| symbol | factor_id | trades | trades/session | raw net % | instrument cost net % | instrument PF | split | decision |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in best[:12]:
        split = "pass" if row.get("split_instrument_cost_positive_all_thirds") else "fail"
        lines.append(
            f"| {row['symbol']} | `{row['factor_id']}` | {row['trade_count']} | {row['trades_per_session']} | "
            f"{row.get('raw_total_profit_pct')} | {row.get('instrument_cost_total_profit_pct')} | "
            f"{row.get('instrument_cost_profit_factor')} | {split} | {row['decision']} |"
        )
    (root / "summaries" / "terminal_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def copy_terminal_outputs(root: Path, compact_root: Path) -> None:
    for relative in ("checks/terminal_metrics.json", "summaries/terminal_summary.md", "summaries/screen_rows.csv"):
        source = root / relative
        if source.exists():
            destination = compact_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


def parse_symbols(raw: list[str]) -> list[str]:
    symbols: list[str] = []
    for item in raw:
        for part in item.split(","):
            symbol = part.strip().upper()
            if symbol and symbol not in symbols:
                symbols.append(symbol)
    return symbols


def parse_contexts(raw: list[str]) -> list[str]:
    contexts: list[str] = []
    for item in raw:
        for part in item.split(","):
            timeframe = part.strip()
            if timeframe == "1m":
                continue
            if timeframe not in CONTEXT_RULES:
                raise ValueError(f"unsupported context timeframe {timeframe!r}; expected one of {sorted(CONTEXT_RULES)}")
            if timeframe not in contexts:
                contexts.append(timeframe)
    return contexts or list(CONTEXT_RULES)


def run(args: argparse.Namespace) -> dict[str, object]:
    root = Path(args.root).expanduser().resolve(strict=False)
    symbols = parse_symbols(args.symbols)
    contexts = parse_contexts(args.contexts)
    target = (args.target or symbols[-1]).upper()
    if target not in symbols:
        symbols.append(target)
    if args.origin != "1m":
        raise ValueError("cross-index PCA residual runner currently supports only 1m origin")
    if args.execute_local_screen:
        guard = collision_guard(load_claim_audit(), root)
        if not guard["ready"]:
            data_stats = {
                "status": "local_screen_blocked_before_data_load",
                "target": target,
                "symbols": symbols,
                "session_scope": SESSION_SCOPE,
                "rth_filter_applied": RTH_FILTER_APPLIED,
            }
            summary = render_summary(
                root,
                [],
                data_stats,
                args.execute_local_screen,
                contexts,
                local_screen_executed=False,
                decision_override="launch_blocked_by_collision_guard",
                collision_guard_result=guard,
            )
            summary["exit_code"] = 3
            if args.compact:
                compact_root = Path(args.compact_root)
                if not compact_root.is_absolute():
                    compact_root = (REPO / compact_root).resolve(strict=False)
                copy_terminal_outputs(root, compact_root)
                summary["compact_root"] = str(compact_root)
            return summary
        frames, stats = load_symbol_frames(symbols, args.origin, args.start, args.end, args.max_screen_rows)
        records = screen_target(target, frames, root, contexts)
        data_stats: dict[str, object] = {"symbols": stats, "target": target}
    else:
        records = prep_records(target, root)
        data_stats = {
            "status": "prep_only_no_data_loaded",
            "target": target,
            "symbols": symbols,
            "session_scope": SESSION_SCOPE,
            "rth_filter_applied": RTH_FILTER_APPLIED,
        }
    summary = render_summary(root, records, data_stats, args.execute_local_screen, contexts)
    if args.compact:
        compact_root = Path(args.compact_root)
        if not compact_root.is_absolute():
            compact_root = (REPO / compact_root).resolve(strict=False)
        copy_terminal_outputs(root, compact_root)
        summary["compact_root"] = str(compact_root)
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cross-index PCA residual reclaim Gate 1 prep/local screen; no provider, IBKR, AutoQuant, or paper/live launch."
    )
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    parser.add_argument("--compact-root", default=str(DEFAULT_COMPACT_ROOT))
    parser.add_argument("--symbols", nargs="+", default=["ES", "YM", "NQ"])
    parser.add_argument("--target", default="NQ")
    parser.add_argument("--origin", default="1m")
    parser.add_argument("--contexts", nargs="+", default=list(CONTEXT_RULES))
    parser.add_argument("--start", default="2021-01-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--max-screen-rows", type=int, default=None)
    parser.add_argument("--execute-local-screen", action="store_true")
    parser.add_argument("--compact", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    result = run(parse_args(argv))
    print(
        json.dumps(
            {
                "run_root": result["run_root"],
                "candidate_count": result["candidate_count"],
                "instrument_cost_candidate_count": result["instrument_cost_candidate_count"],
                "gate1_survivor_count": result["gate1_survivor_count"],
                "decision": result["decision"],
                "promotion_allowed": False,
                "trade_usable": False,
            },
            indent=2,
        )
    )
    return int(result.get("exit_code", 0) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
