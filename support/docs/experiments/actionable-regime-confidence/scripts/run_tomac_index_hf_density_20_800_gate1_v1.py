#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from run_tomac_index_futures_local_gate1_v1 import normalize_source_csv, source_universe

import sys


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
BASE = REPO / "support/docs/experiments/actionable-regime-confidence"
STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
DEFAULT_ROOT = Path("/tmp") / f"ict-engine-tomac-index-hf-density-20-800-local-gate1-{STAMP}"
DEFAULT_COMPACT_ROOT = BASE / "runs" / f"{STAMP}-codex-tomac-index-hf-density-20-800-local-gate1-v1"
DEFAULT_START = "2024-01-01"
DEFAULT_END = "2025-12-31"
TIMEFRAMES = ("1m", "5m", "15m", "30m", "1h", "4h", "1d")
RESEARCH_HELPERS = REPO / "support/scripts/research"
if str(RESEARCH_HELPERS) not in sys.path:
    sys.path.insert(0, str(RESEARCH_HELPERS))

import instrument_cost_model as cost_model  # noqa: E402


@dataclass(frozen=True)
class HfVariant:
    slug: str
    branch_path: str
    side: int
    hold_bars: int
    stop_atr: float
    target_atr: float
    signal_family: str
    min_mtf_aligned: int = 0
    max_mtf_opposed: int = 6
    min_rvol: float = 0.0
    params: dict[str, float] = field(default_factory=dict)


def hf_variants() -> list[HfVariant]:
    return [
        HfVariant(
            slug="micro_vwap_reclaim_long_h2",
            branch_path="RangeReversion -> MeanReclaim -> VwapProxyReversionDensity -> HfMicroVwapReclaim",
            side=1,
            hold_bars=2,
            stop_atr=0.22,
            target_atr=0.28,
            signal_family="vwap_reclaim",
            max_mtf_opposed=4,
            min_rvol=0.25,
            params={"min_dislocation_atr": -1.20, "max_dislocation_atr": -0.05},
        ),
        HfVariant(
            slug="micro_vwap_reclaim_short_h2",
            branch_path="RangeReversion -> MeanReclaim -> VwapProxyReversionDensity -> HfMicroVwapReclaim",
            side=-1,
            hold_bars=2,
            stop_atr=0.22,
            target_atr=0.28,
            signal_family="vwap_reclaim",
            max_mtf_opposed=4,
            min_rvol=0.25,
            params={"min_dislocation_atr": 0.05, "max_dislocation_atr": 1.20},
        ),
        HfVariant(
            slug="dense_ema_pullback_long_h3",
            branch_path="TrendExpansion -> MicroTrendPullback -> EmaStackContinuation -> HfDensePullback",
            side=1,
            hold_bars=3,
            stop_atr=0.25,
            target_atr=0.34,
            signal_family="ema_pullback",
            min_mtf_aligned=2,
            max_mtf_opposed=3,
            min_rvol=0.20,
            params={"max_pullback_atr": 0.45},
        ),
        HfVariant(
            slug="dense_ema_pullback_short_h3",
            branch_path="TrendExpansion -> MicroTrendPullback -> EmaStackContinuation -> HfDensePullback",
            side=-1,
            hold_bars=3,
            stop_atr=0.25,
            target_atr=0.34,
            signal_family="ema_pullback",
            min_mtf_aligned=2,
            max_mtf_opposed=3,
            min_rvol=0.20,
            params={"max_pullback_atr": 0.45},
        ),
        HfVariant(
            slug="micro_donchian_breakout_long_h4",
            branch_path="TrendExpansion -> MicroBreakout -> DonchianImpulseContinuation -> HfBreakoutScalp",
            side=1,
            hold_bars=4,
            stop_atr=0.30,
            target_atr=0.42,
            signal_family="donchian_breakout",
            min_mtf_aligned=2,
            max_mtf_opposed=3,
            min_rvol=0.35,
            params={"lookback": 18.0, "min_body_atr": 0.10},
        ),
        HfVariant(
            slug="micro_donchian_breakout_short_h4",
            branch_path="TrendExpansion -> MicroBreakout -> DonchianImpulseContinuation -> HfBreakoutScalp",
            side=-1,
            hold_bars=4,
            stop_atr=0.30,
            target_atr=0.42,
            signal_family="donchian_breakout",
            min_mtf_aligned=2,
            max_mtf_opposed=3,
            min_rvol=0.35,
            params={"lookback": 18.0, "min_body_atr": 0.10},
        ),
        HfVariant(
            slug="ema_cross_dense_long_h1",
            branch_path="TrendExpansion -> MicroMomentum -> FastEmaCrossParticipation -> HfOneMinuteContinuation",
            side=1,
            hold_bars=1,
            stop_atr=0.18,
            target_atr=0.22,
            signal_family="fast_ema_cross",
            min_mtf_aligned=1,
            max_mtf_opposed=4,
            min_rvol=0.10,
        ),
        HfVariant(
            slug="ema_cross_dense_short_h1",
            branch_path="TrendExpansion -> MicroMomentum -> FastEmaCrossParticipation -> HfOneMinuteContinuation",
            side=-1,
            hold_bars=1,
            stop_atr=0.18,
            target_atr=0.22,
            signal_family="fast_ema_cross",
            min_mtf_aligned=1,
            max_mtf_opposed=4,
            min_rvol=0.10,
        ),
    ]


def factor_id(symbol: str, variant: HfVariant) -> str:
    return f"tomac_{symbol.lower()}_1m_hf_{variant.slug}_20_to_800_gate1_v1"


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df["close"].shift(1)
    return pd.concat(
        [(df["high"] - df["low"]).abs(), (df["high"] - prev_close).abs(), (df["low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)


def load_features(normalized_csv: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    df = pd.read_csv(normalized_csv)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    df = df.set_index("timestamp")
    for column in ("open", "high", "low", "close", "volume"):
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"])
    df["volume"] = df["volume"].fillna(0.0)
    df["date"] = df.index.date.astype(str)
    df["minute"] = df.index.hour * 60 + df.index.minute
    df["regular_session"] = (df["minute"] >= 13 * 60 + 30) & (df["minute"] <= 20 * 60 + 55)
    df["atr14"] = true_range(df).rolling(14, min_periods=8).mean()
    df["ema3"] = df["close"].ewm(span=3, adjust=False, min_periods=3).mean()
    df["ema8"] = df["close"].ewm(span=8, adjust=False, min_periods=6).mean()
    df["ema21"] = df["close"].ewm(span=21, adjust=False, min_periods=12).mean()
    df["ema55"] = df["close"].ewm(span=55, adjust=False, min_periods=28).mean()
    df["body_atr"] = ((df["close"] - df["open"]).abs() / df["atr14"].replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
    df["rvol60"] = df["volume"] / df["volume"].rolling(60, min_periods=20).median().replace(0, np.nan)
    typical = (df["high"] + df["low"] + df["close"]) / 3.0
    volume = df["volume"].replace(0, np.nan)
    grouped = df.groupby("date", sort=False)
    df["session_vwap"] = (typical * volume).groupby(df["date"]).cumsum() / volume.groupby(df["date"]).cumsum()
    df["vwap_dislocation_atr"] = (df["close"] - df["session_vwap"]) / df["atr14"].replace(0, np.nan)
    df["donchian_high18"] = df["high"].rolling(18, min_periods=10).max().shift(1)
    df["donchian_low18"] = df["low"].rolling(18, min_periods=10).min().shift(1)

    base = df.reset_index().sort_values("timestamp")
    for label, rule in {"5m": "5min", "15m": "15min", "30m": "30min", "1h": "1h", "4h": "4h", "1d": "1D"}.items():
        tf = df[["open", "high", "low", "close", "volume"]].resample(rule, label="right", closed="right").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
        ).dropna()
        tf[f"ema20_{label}"] = tf["close"].ewm(span=20, adjust=False, min_periods=8).mean()
        tf[f"ema50_{label}"] = tf["close"].ewm(span=50, adjust=False, min_periods=15).mean()
        tf[f"slope_{label}"] = tf[f"ema20_{label}"] - tf[f"ema20_{label}"].shift(3)
        ctx = tf[[f"ema20_{label}", f"ema50_{label}", f"slope_{label}"]].reset_index().sort_values("timestamp")
        base = pd.merge_asof(base, ctx, on="timestamp", direction="backward")

    df = base.set_index("timestamp")
    long_align = pd.Series(0, index=df.index, dtype="int16")
    short_align = pd.Series(0, index=df.index, dtype="int16")
    checked = pd.Series(0, index=df.index, dtype="int16")
    for label in ("5m", "15m", "30m", "1h", "4h", "1d"):
        valid = df[f"ema20_{label}"].notna() & df[f"ema50_{label}"].notna() & df[f"slope_{label}"].notna()
        checked += valid.astype("int16")
        long_align += (valid & (df[f"ema20_{label}"] > df[f"ema50_{label}"]) & (df[f"slope_{label}"] > 0)).astype("int16")
        short_align += (valid & (df[f"ema20_{label}"] < df[f"ema50_{label}"]) & (df[f"slope_{label}"] < 0)).astype("int16")
    df["mtf_checked"] = checked
    df["mtf_long_aligned"] = long_align
    df["mtf_short_aligned"] = short_align
    summary = {
        "normalized_csv": str(normalized_csv),
        "rows": int(len(df)),
        "first_timestamp": df.index.min().isoformat() if len(df) else None,
        "last_timestamp": df.index.max().isoformat() if len(df) else None,
        "trading_sessions": int(df["date"].nunique()) if len(df) else 0,
        "timeframes_requested": list(TIMEFRAMES),
    }
    return df, summary


def build_signal(df: pd.DataFrame, variant: HfVariant) -> pd.Series:
    side = variant.side
    atr_ok = df["atr14"].notna() & (df["atr14"] > 0)
    rvol_ok = df["rvol60"].fillna(0.0) >= variant.min_rvol
    if side == 1:
        mtf_ok = (df["mtf_long_aligned"] >= variant.min_mtf_aligned) & (df["mtf_short_aligned"] <= variant.max_mtf_opposed)
    else:
        mtf_ok = (df["mtf_short_aligned"] >= variant.min_mtf_aligned) & (df["mtf_long_aligned"] <= variant.max_mtf_opposed)

    if variant.signal_family == "vwap_reclaim":
        dislocation = df["vwap_dislocation_atr"]
        if side == 1:
            raw = (
                dislocation.between(variant.params["min_dislocation_atr"], variant.params["max_dislocation_atr"])
                & (df["close"] > df["open"])
                & (df["close"] >= df["ema3"])
            )
        else:
            raw = (
                dislocation.between(variant.params["min_dislocation_atr"], variant.params["max_dislocation_atr"])
                & (df["close"] < df["open"])
                & (df["close"] <= df["ema3"])
            )
    elif variant.signal_family == "ema_pullback":
        band = variant.params["max_pullback_atr"] * df["atr14"]
        if side == 1:
            raw = (
                (df["ema8"] > df["ema21"])
                & (df["ema21"] > df["ema55"])
                & (df["low"] <= df["ema8"] + band)
                & (df["close"] > df["ema8"])
                & (df["close"] > df["open"])
            )
        else:
            raw = (
                (df["ema8"] < df["ema21"])
                & (df["ema21"] < df["ema55"])
                & (df["high"] >= df["ema8"] - band)
                & (df["close"] < df["ema8"])
                & (df["close"] < df["open"])
            )
    elif variant.signal_family == "donchian_breakout":
        min_body = variant.params["min_body_atr"]
        if side == 1:
            raw = (df["close"] > df["donchian_high18"]) & (df["body_atr"] >= min_body) & (df["close"] > df["open"])
        else:
            raw = (df["close"] < df["donchian_low18"]) & (df["body_atr"] >= min_body) & (df["close"] < df["open"])
    elif variant.signal_family == "fast_ema_cross":
        if side == 1:
            raw = (df["ema3"] > df["ema8"]) & (df["ema3"].shift(1) <= df["ema8"].shift(1)) & (df["close"] > df["open"])
        else:
            raw = (df["ema3"] < df["ema8"]) & (df["ema3"].shift(1) >= df["ema8"].shift(1)) & (df["close"] < df["open"])
    else:
        raise ValueError(f"unsupported signal_family: {variant.signal_family}")
    return (raw & atr_ok & rvol_ok & mtf_ok).fillna(False)


def simulate_trades(symbol: str, df: pd.DataFrame, variant: HfVariant, *, max_trades: int | None = None) -> list[dict[str, object]]:
    signal = build_signal(df, variant)
    signal_idx = np.flatnonzero(signal.to_numpy(dtype=bool))
    close = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    atr_values = df["atr14"].to_numpy(dtype=float)
    timestamps = df.index.astype(str).to_numpy()
    trades: list[dict[str, object]] = []
    last_exit = -1
    side = variant.side
    fid = factor_id(symbol, variant)
    for idx in signal_idx:
        if idx <= last_exit or idx >= len(df) - 1:
            continue
        entry = close[idx]
        atr_now = atr_values[idx]
        if not math.isfinite(entry) or not math.isfinite(atr_now) or entry <= 0 or atr_now <= 0:
            continue
        max_exit = min(idx + variant.hold_bars, len(df) - 1)
        stop = entry - side * variant.stop_atr * atr_now
        target = entry + side * variant.target_atr * atr_now
        exit_idx = max_exit
        exit_price = close[max_exit]
        reason = "timeout"
        for probe in range(idx + 1, max_exit + 1):
            if side == 1:
                hit_stop = low[probe] <= stop
                hit_target = high[probe] >= target
            else:
                hit_stop = high[probe] >= stop
                hit_target = low[probe] <= target
            if hit_stop or hit_target:
                exit_idx = probe
                if hit_stop and hit_target:
                    exit_price = stop
                    reason = "same_bar_stop_first"
                elif hit_stop:
                    exit_price = stop
                    reason = "stop"
                else:
                    exit_price = target
                    reason = "target"
                break
        pnl_pct = side * (exit_price - entry) / entry * 100.0
        trades.append(
            {
                "symbol": symbol,
                "factor_id": fid,
                "branch_path": variant.branch_path,
                "entry_timestamp": timestamps[idx],
                "exit_timestamp": timestamps[exit_idx],
                "side": "long" if side == 1 else "short",
                "entry": round(float(entry), 10),
                "exit": round(float(exit_price), 10),
                "pnl_pct": round(float(pnl_pct), 8),
                "hold_bars": int(exit_idx - idx),
                "exit_reason": reason,
            }
        )
        last_exit = exit_idx
        if max_trades is not None and len(trades) >= max_trades:
            break
    return trades


def profit_factor(net_pnls: list[float]) -> float:
    gains = sum(item for item in net_pnls if item > 0)
    losses = -sum(item for item in net_pnls if item < 0)
    if losses == 0:
        return float("inf") if gains > 0 else 0.0
    return gains / losses


def split_net(trades: list[dict[str, object]], return_key: str) -> tuple[float, float, float]:
    if not trades:
        return 0.0, 0.0, 0.0
    n = len(trades)
    chunks = (trades[: n // 3], trades[n // 3 : 2 * n // 3], trades[2 * n // 3 :])
    return tuple(round(sum(float(t[return_key]) for t in chunk), 6) for chunk in chunks)  # type: ignore[return-value]


def score_trades(trades: list[dict[str, object]], *, sessions: int, symbol: str) -> dict[str, object]:
    count = len(trades)
    raw_pnls = [float(t["pnl_pct"]) for t in trades]
    net_instrument_pnls: list[float] = []
    for trade in trades:
        entry = float(trade.get("entry") or 0.0)
        fee_pct = cost_model.real_fee_round_turn_fraction(symbol, entry) * 100.0 if entry > 0 else 0.0
        trade["instrument_cost_return_pct"] = round(float(trade["pnl_pct"]) - fee_pct, 8)
        net_instrument_pnls.append(float(trade["instrument_cost_return_pct"]))
    total = sum(raw_pnls)
    instrument_total = sum(net_instrument_pnls)
    wins = sum(1 for item in net_instrument_pnls if item > 0)
    losses = sum(1 for item in net_instrument_pnls if item < 0)
    train_cost, validation_cost, test_cost = split_net(trades, "instrument_cost_return_pct")
    representative_price = (sum(float(t.get("entry") or 0.0) for t in trades) / count) if count else None
    cost_packet = cost_model.cost_model_packet(symbol, representative_price)
    result: dict[str, object] = {
        "trade_count": count,
        "trading_sessions": sessions,
        "trades_per_day": round(count / sessions, 6) if sessions else 0.0,
        "win_rate": round(wins / count, 6) if count else 0.0,
        "wins": wins,
        "losses": losses,
        "raw_total_profit_pct": round(total, 6),
        "instrument_cost_total_profit_pct": round(instrument_total, 6),
        "instrument_cost_profit_factor": round(profit_factor(net_instrument_pnls), 6) if math.isfinite(profit_factor(net_instrument_pnls)) else "inf",
        "train_instrument_cost_total_profit_pct": train_cost,
        "validation_instrument_cost_total_profit_pct": validation_cost,
        "test_instrument_cost_total_profit_pct": test_cost,
        "cost_model": cost_packet,
        "promotion_cost_verified": bool(cost_packet.get("verified_for_promotion")),
    }
    return result


def classify_record(record: dict[str, object]) -> dict[str, object]:
    trades_per_day = float(record.get("trades_per_day") or 0.0)
    trade_count = int(record.get("trade_count") or 0)
    density_ok = 20.0 <= trades_per_day <= 800.0 and trade_count >= 60
    net_cost = float(record.get("instrument_cost_total_profit_pct") or 0.0)
    pf_raw = record.get("instrument_cost_profit_factor")
    pf_cost = float("inf") if pf_raw == "inf" else float(pf_raw or 0.0)
    split_cost_ok = all(float(record.get(key) or 0.0) > 0 for key in ("train_instrument_cost_total_profit_pct", "validation_instrument_cost_total_profit_pct", "test_instrument_cost_total_profit_pct"))
    cost_verified = bool(record.get("promotion_cost_verified"))
    cost_ok = cost_verified and net_cost > 0 and pf_cost >= 1.10
    gate1_survivor = bool(density_ok and cost_ok and split_cost_ok)
    if gate1_survivor:
        decision = "hf_gate1_instrument_cost_density_survivor_needs_downstream"
    elif not density_ok:
        decision = "reject_density_outside_20_to_800_per_day"
    elif not cost_ok:
        decision = "reject_instrument_cost_economics"
    else:
        decision = "reject_chronological_split_instability"
    return {
        "density_target_20_to_800_per_day": density_ok,
        "split_instrument_cost_positive_all_thirds": split_cost_ok,
        "cost_ok_instrument_cost_pf_gte_1_10": cost_ok,
        "gate1_survivor": gate1_survivor,
        "decision": decision,
    }


def sample_trades(trades: list[dict[str, object]], limit_each_side: int = 100) -> list[dict[str, object]]:
    if len(trades) <= limit_each_side * 2:
        return trades
    return trades[:limit_each_side] + trades[-limit_each_side:]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def screen_symbol(symbol: str, normalized_csv: Path, root: Path, *, max_screen_rows: int | None, max_trades_per_variant: int | None) -> tuple[list[dict[str, object]], dict[str, object]]:
    df, data_summary = load_features(normalized_csv)
    if max_screen_rows is not None and len(df) > max_screen_rows:
        df = df.iloc[-max_screen_rows:].copy()
        data_summary["screen_rows_used"] = int(len(df))
        data_summary["screen_first_timestamp"] = df.index.min().isoformat() if len(df) else None
    else:
        data_summary["screen_rows_used"] = int(len(df))
    sessions = int(df["date"].nunique()) if len(df) else 0
    records: list[dict[str, object]] = []
    for variant in hf_variants():
        trades = simulate_trades(symbol, df, variant, max_trades=max_trades_per_variant)
        record: dict[str, object] = {
            "symbol": symbol,
            "factor_id": factor_id(symbol, variant),
            "branch_path": variant.branch_path,
            "provider": "tomac_databento_local",
            "market": "futures",
            "product": "equity_index",
            "origin_timeframe": "1m",
            "context_timeframes": ",".join(TIMEFRAMES[1:]),
            "side": "long" if variant.side == 1 else "short",
            "hold_bars": variant.hold_bars,
            "stop_atr": variant.stop_atr,
            "target_atr": variant.target_atr,
            "signal_family": variant.signal_family,
            "min_mtf_aligned": variant.min_mtf_aligned,
            "max_mtf_opposed": variant.max_mtf_opposed,
            "min_rvol": variant.min_rvol,
        }
        record.update(score_trades(trades, sessions=sessions, symbol=symbol))
        record.update(classify_record(record))
        records.append(record)
        material = root / "materials" / f"{record['factor_id']}.json"
        material.parent.mkdir(parents=True, exist_ok=True)
        material.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        write_csv(root / "materials" / f"{record['factor_id']}_trades_sample.csv", sample_trades(trades))
    return records, data_summary


def render_summary(root: Path, records: list[dict[str, object]], source_stats: list[dict[str, object]]) -> dict[str, object]:
    survivors = [row for row in records if row.get("gate1_survivor") is True]
    density_hits = [row for row in records if row.get("density_target_20_to_800_per_day") is True]
    best = sorted(records, key=lambda row: float(row.get("instrument_cost_total_profit_pct") or -999999.0), reverse=True)[:12]
    near = sorted(density_hits, key=lambda row: float(row.get("instrument_cost_total_profit_pct") or -999999.0), reverse=True)[:12]
    summary = {
        "run_root": str(root),
        "candidate_count": len(records),
        "density_20_to_800_count": len(density_hits),
        "gate1_survivor_count": len(survivors),
        "survivors": survivors,
        "top_by_instrument_cost": best,
        "top_density_hits_by_instrument_cost": near,
        "source_stats": source_stats,
        "hard_retention_rule": {
            "density": "20 <= trades_per_day <= 800, 1m origin",
            "cost": "verified instrument-cost net positive and PF >= 1.10",
            "split": "chronological train/validation/test thirds positive after instrument cost",
            "promotion": "downstream provider/AQ/Pre-Bayes/BBN/CatBoost/execution-feedback chain not run in this local screen",
        },
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "decision": "hf_gate1_survivor_needs_downstream" if survivors else "terminalized_reject_no_hf_instrument_cost_density_survivor",
    }
    (root / "checks").mkdir(parents=True, exist_ok=True)
    (root / "checks/terminal_metrics.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# TOMAC Index HF Density 20-800 Gate 1",
        "",
        f"- Candidate rows: `{len(records)}`.",
        f"- Density hits 20-800/day: `{len(density_hits)}`.",
        f"- Gate 1 instrument-cost survivors: `{len(survivors)}`.",
        "- Origin timeframe: `1m`.",
        "- Context ladder: `5m,15m,30m,1h,4h,1d`.",
        "- Downstream provider/AQ/paper trade was not run by this local screen.",
        "",
        "## Top Density Hits By Instrument Cost",
        "",
        "| symbol | factor_id | trades/day | trades | raw % | instrument cost % | instrument PF | split | decision |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in near:
        split = "pass" if row.get("split_instrument_cost_positive_all_thirds") else "fail"
        lines.append(
            f"| {row['symbol']} | `{row['factor_id']}` | {row['trades_per_day']} | {row['trade_count']} | "
            f"{row['raw_total_profit_pct']} | {row['instrument_cost_total_profit_pct']} | {row['instrument_cost_profit_factor']} | {split} | {row['decision']} |"
        )
    lines.extend(["", "## Top Rows By Instrument Cost", "", "| symbol | factor_id | trades/day | trades | instrument cost % | decision |", "|---|---|---:|---:|---:|---|"])
    for row in best:
        lines.append(
            f"| {row['symbol']} | `{row['factor_id']}` | {row['trades_per_day']} | {row['trade_count']} | "
            f"{row['instrument_cost_total_profit_pct']} | {row['decision']} |"
        )
    (root / "summaries").mkdir(parents=True, exist_ok=True)
    (root / "summaries/terminal_decision_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def run(args: argparse.Namespace) -> dict[str, object]:
    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    wanted = {item.strip().upper() for item in args.symbols.split(",") if item.strip()}
    records: list[dict[str, object]] = []
    source_stats: list[dict[str, object]] = []
    for source in source_universe():
        if source.symbol not in wanted:
            continue
        normalized = root / "data/provider/normalized" / f"tomac_{source.symbol.lower()}_1m_{args.start}_{args.end}.csv"
        clean_stats = normalize_source_csv(source, normalized, start=args.start, end=args.end, max_rows=args.max_normalize_rows)
        symbol_records, feature_stats = screen_symbol(
            source.symbol,
            normalized,
            root,
            max_screen_rows=args.max_screen_rows,
            max_trades_per_variant=args.max_trades_per_variant,
        )
        source_stats.append({**clean_stats, **feature_stats})
        records.extend(symbol_records)
    write_csv(root / "summaries/hf_screen_rows.csv", records)
    summary = render_summary(root, records, source_stats)
    if args.compact:
        compact_root = Path(args.compact_root)
        for rel in ("checks/terminal_metrics.json", "summaries/terminal_decision_summary.md", "summaries/hf_screen_rows.csv"):
            src = root / rel
            dst = compact_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
        summary["compact_root"] = str(compact_root)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local TOMAC ES/YM/NQ 1m high-frequency 20-800 trades/day Gate 1 screen.")
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    parser.add_argument("--compact-root", default=str(DEFAULT_COMPACT_ROOT))
    parser.add_argument("--symbols", default="ES,YM,NQ")
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--max-normalize-rows", type=int, default=None)
    parser.add_argument("--max-screen-rows", type=int, default=None)
    parser.add_argument("--max-trades-per-variant", type=int, default=None)
    parser.add_argument("--compact", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    result = run(parse_args())
    print(json.dumps({"run_root": result["run_root"], "gate1_survivor_count": result["gate1_survivor_count"], "density_20_to_800_count": result["density_20_to_800_count"]}, indent=2))
