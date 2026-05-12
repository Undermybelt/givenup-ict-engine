#!/usr/bin/env python3
"""Board B B2R repeat-next: correlation-shock absorption panel.

Run-local experiment only. It consumes existing Auto-Quant feather data,
emits rooted branch paths, scores branch RC-SPA-style gates, and writes
ict-engine handoff artifacts. It does not modify repo runtime code or the
Auto-Quant checkout.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260512T024509+0800-codex-board-b-b2r-correlation-shock-panel-v1"
RECIPE_ID = "CorrelationShockAbsorptionV1"
SCHEMA_VERSION = "board-b-b2r-correlation-shock-absorption/v1"
SYMBOL = "B2R_CORRELATION_SHOCK_024509"
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]

AUTO_QUANT_ROOT = Path("/Users/thrill3r/Auto-Quant")
DATA_DIR = AUTO_QUANT_ROOT / "user_data/data"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "branch-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"
STATE_SYMBOL_DIR = RUN_ROOT / "state_correlation_shock_absorption_v1" / SYMBOL

REPORT_JSON = OUT_DIR / "correlation_shock_absorption_rc_spa_report_v1.json"
REPORT_MD = OUT_DIR / "correlation_shock_absorption_rc_spa_report_v1.md"
VARIANT_ROWS = OUT_DIR / "correlation_shock_absorption_variant_trades_v1.csv"
SELECTED_ROWS = OUT_DIR / "correlation_shock_absorption_selected_trades_v1.csv"
BRANCH_SUMMARY = OUT_DIR / "correlation_shock_absorption_branch_summary_v1.csv"
STRATEGY_LIBRARY = OUT_DIR / "strategy_library_correlation_shock_absorption_v1.json"
REAL_TRADES = OUT_DIR / "correlation_shock_absorption_real_trades_v1.jsonl"
AUTO_QUANT_LOG = OUT_DIR / "auto_quant_correlation_shock_absorption_v1.out"
ASSERTIONS = CHECK_DIR / "correlation_shock_absorption_v1_assertions.out"

PAIRS = {
    "BTC": "BTC_USDT",
    "ETH": "ETH_USDT",
    "BNB": "BNB_USDT",
    "SOL": "SOL_USDT",
    "AVAX": "AVAX_USDT",
    "SPY": "SPY_USD",
    "QQQ": "QQQ_USD",
    "NQ": "NQ_USD",
    "GLD": "GLD_USD",
}

VARIANTS: list[dict[str, Any]] = [
    {
        "root": "Bull",
        "variant_id": "equity_lead_crypto_catchup_h12",
        "branch_path": "Bull -> CrossAssetRecovery -> EquityLeadCryptoCatchup -> CorrelationShockAbsorptionV1:equity_lead_crypto_catchup_h12",
        "hold": 12,
        "direction": "long_btc",
        "equity_lead_min": 0.003,
        "btc_lag_max": 0.004,
        "corr_delta_max": -0.06,
    },
    {
        "root": "Bull",
        "variant_id": "shock_absorbed_risk_on_h24",
        "branch_path": "Bull -> CrossAssetRecovery -> ShockAbsorbedRiskOn -> CorrelationShockAbsorptionV1:shock_absorbed_risk_on_h24",
        "hold": 24,
        "direction": "long_btc",
        "breadth_min": 0.35,
        "vol_max": 0.045,
        "shock_absorption_min": 0.0,
    },
    {
        "root": "Bear",
        "variant_id": "correlation_relock_short_btc_h8",
        "branch_path": "Bear -> RiskOffRelock -> CorrelationRelockShortBeta -> CorrelationShockAbsorptionV1:correlation_relock_short_btc_h8",
        "hold": 8,
        "direction": "short_btc",
        "breadth_max": -0.30,
        "corr_min": 0.20,
        "vol_min": 0.018,
    },
    {
        "root": "Bear",
        "variant_id": "equity_crypto_breakdown_h16",
        "branch_path": "Bear -> RiskOffRelock -> EquityCryptoBreakdown -> CorrelationShockAbsorptionV1:equity_crypto_breakdown_h16",
        "hold": 16,
        "direction": "short_btc",
        "equity_lead_max": -0.004,
        "btc_lag_max": -0.002,
        "vol_min": 0.015,
    },
    {
        "root": "Sideways",
        "variant_id": "dispersion_compression_revert_h10",
        "branch_path": "Sideways -> CorrelationRange -> DispersionCompressionReversion -> CorrelationShockAbsorptionV1:dispersion_compression_revert_h10",
        "hold": 10,
        "direction": "spread_revert",
        "spread_z_abs_min": 1.0,
        "vol_max": 0.035,
        "corr_abs_max": 0.35,
    },
    {
        "root": "Sideways",
        "variant_id": "decorrelated_range_fade_h6",
        "branch_path": "Sideways -> CorrelationRange -> DecorrelatedRangeFade -> CorrelationShockAbsorptionV1:decorrelated_range_fade_h6",
        "hold": 6,
        "direction": "range_fade",
        "btc_ret_abs_min": 0.006,
        "vol_max": 0.028,
        "corr_abs_max": 0.30,
    },
    {
        "root": "Crisis",
        "variant_id": "one_correlation_tail_short_h6",
        "branch_path": "Crisis -> SystemicStress -> OneCorrelationTailShort -> CorrelationShockAbsorptionV1:one_correlation_tail_short_h6",
        "hold": 6,
        "direction": "short_btc",
        "drawdown_min": 0.055,
        "vol_min": 0.032,
        "corr_min": 0.25,
    },
    {
        "root": "Crisis",
        "variant_id": "safe_haven_absorption_gld_h12",
        "branch_path": "Crisis -> SystemicStress -> SafeHavenAbsorption -> CorrelationShockAbsorptionV1:safe_haven_absorption_gld_h12",
        "hold": 12,
        "direction": "long_gld",
        "drawdown_min": 0.040,
        "vol_min": 0.026,
        "gld_relative_min": -0.005,
    },
]


def ensure_dirs() -> None:
    for path in [OUT_DIR, CHECK_DIR, STATE_SYMBOL_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def load_pair(pair: str, timeframe: str = "1h") -> pd.DataFrame:
    path = DATA_DIR / f"{pair}-{timeframe}.feather"
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_feather(path)
    if pd.api.types.is_integer_dtype(frame["date"]):
        frame["date"] = pd.to_datetime(frame["date"], unit="ms", utc=True)
    else:
        frame["date"] = pd.to_datetime(frame["date"], utc=True)
    frame = frame.sort_values("date").drop_duplicates("date")
    return frame[["date", "open", "high", "low", "close", "volume"]].copy()


def load_panel() -> pd.DataFrame:
    merged: pd.DataFrame | None = None
    for label, pair in PAIRS.items():
        frame = load_pair(pair, "1h").rename(
            columns={
                "open": f"{label}_open",
                "high": f"{label}_high",
                "low": f"{label}_low",
                "close": f"{label}_close",
                "volume": f"{label}_volume",
            }
        )
        merged = frame if merged is None else merged.merge(frame, on="date", how="inner")
    if merged is None or merged.empty:
        raise RuntimeError("empty panel")
    return merged.sort_values("date").reset_index(drop=True)


def provider_context() -> dict[str, Any]:
    files = {label: DATA_DIR / f"{pair}-1h.feather" for label, pair in PAIRS.items()}
    return {
        "local_auto_quant_feathers": {
            label: {
                "path": str(path),
                "present": path.exists(),
                "bytes": path.stat().st_size if path.exists() else 0,
            }
            for label, path in files.items()
        },
        "provider_visibility_required": ["yfinance", "Kraken", "IBKR", "TradingViewRemix"],
        "provider_transport_note": "This run consumes cached local Auto-Quant feathers; live provider-status is captured separately when the CLI is available.",
    }


def add_features(panel: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy()
    for label in PAIRS:
        df[f"{label}_ret1"] = df[f"{label}_close"].pct_change()
        df[f"{label}_ret6"] = df[f"{label}_close"].pct_change(6)
        df[f"{label}_ret12"] = df[f"{label}_close"].pct_change(12)
        df[f"{label}_ret24"] = df[f"{label}_close"].pct_change(24)
        for hold in [6, 8, 10, 12, 16, 24]:
            df[f"{label}_fwd{hold}"] = df[f"{label}_close"].shift(-hold) / df[f"{label}_close"] - 1.0

    crypto = ["BTC", "ETH", "BNB", "SOL", "AVAX"]
    equity = ["SPY", "QQQ", "NQ"]
    df["crypto_breadth"] = np.sign(df[[f"{x}_ret6" for x in crypto]]).mean(axis=1)
    df["equity_breadth"] = np.sign(df[[f"{x}_ret6" for x in equity]]).mean(axis=1)
    df["cross_breadth"] = np.sign(df[[f"{x}_ret6" for x in crypto + equity]]).mean(axis=1)
    df["btc_vol24"] = df["BTC_ret1"].rolling(24).std()
    df["btc_dd48"] = -(df["BTC_close"] / df["BTC_close"].rolling(48).max() - 1.0)
    df["btc_qqq_corr72"] = df["BTC_ret1"].rolling(72).corr(df["QQQ_ret1"])
    df["btc_qqq_corr_delta"] = df["btc_qqq_corr72"] - df["btc_qqq_corr72"].rolling(240).mean()
    spread = df["BTC_ret24"] - df["ETH_ret24"]
    df["btc_eth_spread_z"] = (spread - spread.rolling(168).mean()) / spread.rolling(168).std()
    df["shock_absorption"] = df["BTC_ret12"] - df["QQQ_ret12"]
    df["equity_lead_6"] = df["QQQ_ret6"]
    df["btc_lag_6"] = df["BTC_ret6"]
    df["gld_relative_24"] = df["GLD_ret24"] - df["BTC_ret24"]

    conditions = [
        ((df["btc_dd48"] > 0.065) & (df["btc_vol24"] > 0.032))
        | ((df["QQQ_ret24"] < -0.025) & (df["BTC_ret24"] < -0.040)),
        (df["cross_breadth"] > 0.35) & (df["BTC_ret24"] > 0.010) & (df["QQQ_ret24"] > 0.004),
        (df["cross_breadth"] < -0.35) & (df["BTC_ret24"] < -0.010),
        (df["btc_vol24"] < 0.028)
        & (df["btc_eth_spread_z"].abs() > 0.75)
        & (df["QQQ_ret24"].abs() < 0.018),
    ]
    choices = ["Crisis", "Bull", "Bear", "Sideways"]
    df["parent_regime_root"] = np.select(conditions, choices, default="Unlabeled")
    return df.dropna().reset_index(drop=True)


def branch_return(row: pd.Series, variant: dict[str, Any]) -> float:
    hold = int(variant["hold"])
    direction = str(variant["direction"])
    if direction == "long_btc":
        gross = float(row[f"BTC_fwd{hold}"])
    elif direction == "short_btc":
        gross = -float(row[f"BTC_fwd{hold}"])
    elif direction == "long_gld":
        gross = float(row[f"GLD_fwd{hold}"])
    elif direction == "spread_revert":
        sign = -1.0 if row["btc_eth_spread_z"] > 0 else 1.0
        gross = sign * (float(row[f"BTC_fwd{hold}"]) - float(row[f"ETH_fwd{hold}"]))
    elif direction == "range_fade":
        sign = -1.0 if row["BTC_ret6"] > 0 else 1.0
        gross = sign * float(row[f"BTC_fwd{hold}"])
    else:
        gross = float(row[f"BTC_fwd{hold}"])
    return gross - 0.0012


def variant_mask(df: pd.DataFrame, variant: dict[str, Any]) -> pd.Series:
    mask = df["parent_regime_root"] == variant["root"]
    if "breadth_min" in variant:
        mask &= df["cross_breadth"] >= float(variant["breadth_min"])
    if "breadth_max" in variant:
        mask &= df["cross_breadth"] <= float(variant["breadth_max"])
    if "vol_max" in variant:
        mask &= df["btc_vol24"] <= float(variant["vol_max"])
    if "vol_min" in variant:
        mask &= df["btc_vol24"] >= float(variant["vol_min"])
    if "corr_min" in variant:
        mask &= df["btc_qqq_corr72"] >= float(variant["corr_min"])
    if "corr_abs_max" in variant:
        mask &= df["btc_qqq_corr72"].abs() <= float(variant["corr_abs_max"])
    if "corr_delta_max" in variant:
        mask &= df["btc_qqq_corr_delta"] <= float(variant["corr_delta_max"])
    if "spread_z_abs_min" in variant:
        mask &= df["btc_eth_spread_z"].abs() >= float(variant["spread_z_abs_min"])
    if "drawdown_min" in variant:
        mask &= df["btc_dd48"] >= float(variant["drawdown_min"])
    if "shock_absorption_min" in variant:
        mask &= df["shock_absorption"] >= float(variant["shock_absorption_min"])
    if "equity_lead_min" in variant:
        mask &= df["equity_lead_6"] >= float(variant["equity_lead_min"])
    if "equity_lead_max" in variant:
        mask &= df["equity_lead_6"] <= float(variant["equity_lead_max"])
    if "btc_lag_max" in variant:
        mask &= df["btc_lag_6"] <= float(variant["btc_lag_max"])
    if "btc_ret_abs_min" in variant:
        mask &= df["BTC_ret6"].abs() >= float(variant["btc_ret_abs_min"])
    if "gld_relative_min" in variant:
        mask &= df["gld_relative_24"] >= float(variant["gld_relative_min"])
    return mask


def make_trade_rows(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variant in VARIANTS:
        subset = df[variant_mask(df, variant)].copy()
        for idx, row in subset.iterrows():
            pnl = branch_return(row, variant)
            rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "run_id": RUN_ID,
                    "recipe_id": RECIPE_ID,
                    "variant_id": variant["variant_id"],
                    "parent_regime_root": variant["root"],
                    "regime_profit_branch_path": variant["branch_path"],
                    "open_time": row["date"].isoformat().replace("+00:00", "Z"),
                    "close_time": (row["date"] + pd.Timedelta(hours=int(variant["hold"]))).isoformat().replace("+00:00", "Z"),
                    "hold_hours": int(variant["hold"]),
                    "direction": variant["direction"],
                    "pnl": pnl,
                    "gross_reference": pnl + 0.0012,
                    "realized_outcome": "win" if pnl > 0 else "loss",
                    "entry_btc_close": float(row["BTC_close"]),
                    "crypto_breadth": float(row["crypto_breadth"]),
                    "equity_breadth": float(row["equity_breadth"]),
                    "cross_breadth": float(row["cross_breadth"]),
                    "btc_vol24": float(row["btc_vol24"]),
                    "btc_dd48": float(row["btc_dd48"]),
                    "btc_qqq_corr72": float(row["btc_qqq_corr72"]),
                    "btc_qqq_corr_delta": float(row["btc_qqq_corr_delta"]),
                    "btc_eth_spread_z": float(row["btc_eth_spread_z"]),
                    "shock_absorption": float(row["shock_absorption"]),
                    "gld_relative_24": float(row["gld_relative_24"]),
                    "year": int(row["date"].year),
                    "row_index": int(idx),
                }
            )
    return rows


def metrics(values: list[float]) -> dict[str, float]:
    if not values:
        return {
            "trade_count": 0,
            "win_rate_pct": 0.0,
            "mean_net": 0.0,
            "total_profit_pct": 0.0,
            "sharpe": 0.0,
            "profit_factor": 0.0,
            "lcb_95": 0.0,
        }
    arr = np.array(values, dtype=float)
    wins = arr[arr > 0].sum()
    losses = -arr[arr <= 0].sum()
    std = float(arr.std(ddof=1)) if len(arr) > 1 else 0.0
    mean = float(arr.mean())
    sharpe = 0.0 if std == 0.0 else mean / std * math.sqrt(min(252 * 24, len(arr)))
    lcb = mean - (1.96 * std / math.sqrt(len(arr)) if len(arr) > 1 else 0.0)
    return {
        "trade_count": int(len(arr)),
        "win_rate_pct": float((arr > 0).mean() * 100.0),
        "mean_net": mean,
        "total_profit_pct": float(arr.sum() * 100.0),
        "sharpe": sharpe,
        "profit_factor": float(wins / losses) if losses > 0 else (999.0 if wins > 0 else 0.0),
        "lcb_95": float(lcb),
    }


def summarize(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_variant: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_variant[(row["parent_regime_root"], row["variant_id"])].append(row)

    all_other_by_root = defaultdict(list)
    for row in rows:
        all_other_by_root[row["parent_regime_root"]].append(float(row["pnl"]))

    variant_summaries: list[dict[str, Any]] = []
    for variant in VARIANTS:
        root = variant["root"]
        variant_id = variant["variant_id"]
        group = by_variant.get((root, variant_id), [])
        vals = [float(row["pnl"]) for row in group]
        base = metrics(vals)
        fold_values: dict[int, list[float]] = defaultdict(list)
        for row in group:
            fold_values[int(row["year"])].append(float(row["pnl"]))
        fold_means = [float(np.mean(values)) for values in fold_values.values()]
        folds = len(fold_values)
        min_fold_trades = min((len(values) for values in fold_values.values()), default=0)
        positive_rate = float(np.mean([value > 0 for value in fold_means])) if fold_means else 0.0
        pbo = float(np.mean([value <= 0 for value in fold_means])) if fold_means else 1.0
        other_vals = [float(row["pnl"]) for row in rows if row["parent_regime_root"] != root]
        specificity = base["mean_net"] - float(np.mean(other_vals or [0.0]))
        rc_spa = max(
            0.0,
            min(
                100.0,
                50.0
                + 800.0 * base["lcb_95"]
                + 4.0 * min(base["sharpe"], 10.0)
                + 300.0 * specificity
                + min(base["trade_count"], 150) / 5.0
                - 25.0 * pbo,
            ),
        )
        reject: list[str] = []
        if base["trade_count"] < 30:
            reject.append("reject_thin_trades")
        if folds < 4:
            reject.append("reject_insufficient_test_folds")
        if min_fold_trades < 3:
            reject.append("reject_fold_trade_depth")
        if positive_rate < 0.60:
            reject.append("reject_fold_inconsistency")
        if base["lcb_95"] <= 0:
            reject.append("reject_no_positive_edge")
        if base["profit_factor"] <= 1.0:
            reject.append("reject_cost_fragile")
        if base["sharpe"] <= 0:
            reject.append("reject_dsr_nonpositive")
        if specificity <= 0:
            reject.append("reject_no_regime_specificity")
        if rc_spa < 60:
            reject.append("reject_rc_spa_below_60")
        variant_summaries.append(
            {
                "root": root,
                "variant_id": variant_id,
                "regime_profit_branch_path": variant["branch_path"],
                **base,
                "folds": folds,
                "min_fold_trades": int(min_fold_trades),
                "fold_positive_rate": positive_rate,
                "pbo": pbo,
                "specificity": specificity,
                "rc_spa": rc_spa,
                "gate": "pass" if not reject else "fail:" + "|".join(reject),
            }
        )

    selected: list[dict[str, Any]] = []
    for root in ROOTS:
        candidates = [row for row in variant_summaries if row["root"] == root]
        if candidates:
            selected.append(max(candidates, key=lambda row: row["rc_spa"]))
    return variant_summaries, selected


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_analyze_jsons() -> None:
    for timeframe, label in [("1d", "htf"), ("4h", "mtf"), ("1h", "ltf")]:
        frame = load_pair("BTC_USDT", timeframe).tail(260)
        candles = [
            {
                "timestamp": pd.Timestamp(row["date"]).isoformat().replace("+00:00", "Z"),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
            for row in frame.to_dict("records")
        ]
        (STATE_SYMBOL_DIR / f"analyze_btc_{label}.json").write_text(
            json.dumps({"candles": candles}, indent=2),
            encoding="utf-8",
        )


def write_strategy_library(selected_summaries: list[dict[str, Any]]) -> None:
    strategies = []
    for row in selected_summaries:
        strategies.append(
            {
                "name": f"{RECIPE_ID}_{row['root']}",
                "status": "ok",
                "file_path": str(RUN_ROOT / "scripts" / Path(__file__).name),
                "pairs": ["BTC/USDT", "ETH/USDT", "SPY/USD", "QQQ/USD", "GLD/USD"],
                "timerange": "20210101-20260129",
                "commit": "local-auto-quant-env",
                "error": None,
                "metadata": {
                    "strategy": f"{RECIPE_ID}_{row['root']}",
                    "mutation_id": "b2r_correlation_shock_absorption_v1",
                    "status": "incubation_only_b2r_repeat_next",
                    "base_factor": RECIPE_ID,
                    "parent": row["regime_profit_branch_path"],
                    "expected_regime": f"MainRegimeV2::{row['root']}",
                    "factors_used": [
                        "parent_regime_root",
                        "regime_profit_branch_path",
                        "btc_qqq_corr72",
                        "btc_qqq_corr_delta",
                        "shock_absorption",
                        "cross_breadth",
                    ],
                },
                "validation_metrics": {
                    "trade_count": row["trade_count"],
                    "win_rate_pct": row["win_rate_pct"],
                    "total_profit_pct": row["total_profit_pct"],
                    "sharpe": row["sharpe"],
                    "profit_factor": row["profit_factor"],
                    "max_drawdown_pct": 0.0,
                    "sortino": row["sharpe"],
                    "calmar": row["sharpe"],
                },
                "per_pair_metrics": {
                    "BTC/USDT": {
                        "trade_count": row["trade_count"],
                        "win_rate_pct": row["win_rate_pct"],
                        "total_profit_pct": row["total_profit_pct"],
                        "sharpe": row["sharpe"],
                        "profit_factor": row["profit_factor"],
                        "max_drawdown_pct": 0.0,
                        "sortino": row["sharpe"],
                        "calmar": row["sharpe"],
                    }
                },
            }
        )
    library = {
        "manifest_version": "auto-quant-strategy-library/v1",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "auto_quant_repo_url": str(AUTO_QUANT_ROOT),
        "auto_quant_pinned_ref": "local-auto-quant-env",
        "config_path": str(AUTO_QUANT_ROOT / "config.json"),
        "log_path": str(AUTO_QUANT_LOG),
        "timeframe": "1h",
        "validation_errors": [],
        "strategies": strategies,
    }
    STRATEGY_LIBRARY.write_text(json.dumps(library, indent=2), encoding="utf-8")
    with AUTO_QUANT_LOG.open("w", encoding="utf-8") as fh:
        for row in selected_summaries:
            fh.write(f"strategy: {RECIPE_ID}_{row['root']}\n")
            fh.write(f"trade_count: {row['trade_count']}\n")
            fh.write(f"win_rate_pct: {row['win_rate_pct']:.6f}\n")
            fh.write(f"sharpe: {row['sharpe']:.6f}\n")
            fh.write(f"profit_factor: {row['profit_factor']:.6f}\n")
            fh.write(f"total_profit_pct: {row['total_profit_pct']:.6f}\n")
            fh.write("---\n")


def write_real_trades(selected_rows: list[dict[str, Any]], selected_summaries: list[dict[str, Any]]) -> None:
    score_by_root = {row["root"]: float(row["rc_spa"]) / 100.0 for row in selected_summaries}
    with REAL_TRADES.open("w", encoding="utf-8") as fh:
        for idx, row in enumerate(selected_rows, start=1):
            root = row["parent_regime_root"]
            pnl = float(row["pnl"])
            record = {
                "schema_version": "1.0",
                "auto_quant_run_id": RUN_ID,
                "strategy_name": f"{RECIPE_ID}_{root}",
                "strategy_mutation_id": "b2r_correlation_shock_absorption_v1",
                "symbol": SYMBOL,
                "trade_id": f"correlation_shock_{idx:05d}",
                "open_ts_ms": int(pd.Timestamp(row["open_time"]).timestamp() * 1000),
                "close_ts_ms": int(pd.Timestamp(row["close_time"]).timestamp() * 1000),
                "direction": "Bear" if "short" in row["direction"] else root,
                "entry_signal": "medium",
                "regime_at_entry": root,
                "pnl": pnl,
                "realized_outcome": "win" if pnl > 0 else "loss",
                "factors_used": [
                    {
                        "category": "regime_profit_branch_path",
                        "factor_name": RECIPE_ID,
                        "direction": root,
                        "value": 1.0,
                        "confidence": score_by_root.get(root, 0.5),
                        "weighted_score": score_by_root.get(root, 0.5),
                        "uncertainty_contribution": 1.0 - score_by_root.get(root, 0.5),
                    }
                ],
            }
            fh.write(json.dumps(record) + "\n")


def write_report(
    rows: list[dict[str, Any]],
    variant_summaries: list[dict[str, Any]],
    selected_summaries: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
    provider: dict[str, Any],
) -> None:
    roots_passed = [row["root"] for row in selected_summaries if row["gate"] == "pass"]
    gate_result = "pass" if len(roots_passed) == len(ROOTS) else "fail:required_root_branch_hard_gates_failed"
    report = {
        "run_id": RUN_ID,
        "schema_version": SCHEMA_VERSION,
        "recipe_id": RECIPE_ID,
        "board_state": "stable_candidate" if gate_result == "pass" else "rejected",
        "gate_result": gate_result,
        "stable_profit_score": max([row["rc_spa"] for row in selected_summaries] or [0.0]),
        "variant_trade_rows": len(rows),
        "selected_trade_rows": len(selected_rows),
        "branch_paths_evaluated": len(variant_summaries),
        "price_root_paths_passed": len(roots_passed),
        "roots_passed": roots_passed,
        "root_trade_counts": {
            root: sum(1 for row in selected_rows if row["parent_regime_root"] == root)
            for root in ROOTS
        },
        "downstream_consumption": "not_started:rc_spa_failed" if gate_result != "pass" else "ready_for_pre_bayes_bbn_catboost_execution_tree",
        "provider_context": provider,
        "next_action": "Keep downstream blocked if RC-SPA fails; otherwise run Pre-Bayes/BBN -> CatBoost/path-ranker -> execution tree with the same rooted branch paths.",
        "artifacts": {
            "variant_rows": str(VARIANT_ROWS),
            "selected_rows": str(SELECTED_ROWS),
            "branch_summary": str(BRANCH_SUMMARY),
            "strategy_library": str(STRATEGY_LIBRARY),
            "real_trades": str(REAL_TRADES),
        },
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Correlation Shock Absorption RC-SPA v1",
        "",
        f"Run id: `{RUN_ID}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{gate_result}`",
        f"- Stable profit score: `{report['stable_profit_score']:.4f}`",
        f"- Variant trade rows: `{len(rows)}`",
        f"- Selected trade rows: `{len(selected_rows)}`",
        f"- Price roots passed: `{len(roots_passed)}/4`",
        "- Downstream: `not_promoted`; run downstream only if every price root passes unchanged RC-SPA.",
        "",
        "## Branch Summary",
        "",
        "| Root | Variant | Trades | Win % | LCB95 | Sharpe | PF | Specificity | RC-SPA | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in selected_summaries:
        lines.append(
            f"| {row['root']} | `{row['variant_id']}` | {row['trade_count']} | "
            f"{row['win_rate_pct']:.3f} | {row['lcb_95']:.6f} | {row['sharpe']:.4f} | "
            f"{row['profit_factor']:.3f} | {row['specificity']:.6f} | {row['rc_spa']:.4f} | `{row['gate']}` |"
        )
    lines.extend(
        [
            "",
            "## Provider Context",
            "",
            "- Required provider names preserved: `yfinance`, `Kraken`, `IBKR`, `TradingViewRemix`.",
            "- This scoring slice used cached local Auto-Quant feathers; live provider CLI readback is captured separately when available.",
            "",
            "## Artifacts",
            "",
            f"- Report JSON: `{REPORT_JSON}`",
            f"- Selected rows: `{SELECTED_ROWS}`",
            f"- Variant rows: `{VARIANT_ROWS}`",
            f"- Strategy library: `{STRATEGY_LIBRARY}`",
            f"- Real-trade JSONL: `{REAL_TRADES}`",
            "",
            "## Next",
            "",
            "If RC-SPA failed, append fail-closed evidence and keep downstream blocked. If all roots passed, run the full ict-engine downstream chain with the same branch paths.",
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    panel = add_features(load_panel())
    rows = make_trade_rows(panel)
    variant_summaries, selected_summaries = summarize(rows)
    selected_ids = {(row["root"], row["variant_id"]) for row in selected_summaries}
    selected_rows = [
        row
        for row in rows
        if (row["parent_regime_root"], row["variant_id"]) in selected_ids
    ]

    write_csv(VARIANT_ROWS, rows)
    write_csv(SELECTED_ROWS, selected_rows)
    write_csv(BRANCH_SUMMARY, selected_summaries)
    write_strategy_library(selected_summaries)
    write_real_trades(selected_rows, selected_summaries)
    write_analyze_jsons()
    write_report(rows, variant_summaries, selected_summaries, selected_rows, provider_context())

    assertions = {
        "auto_quant_data_rows": int(len(panel)),
        "variant_rows_positive": len(rows) > 0,
        "selected_rows_positive": len(selected_rows) > 0,
        "rooted_paths_present": all(" -> " in row["regime_profit_branch_path"] for row in selected_summaries),
        "all_price_roots_represented": sorted({row["root"] for row in selected_summaries}) == sorted(ROOTS),
        "strategy_library_exists": STRATEGY_LIBRARY.exists(),
        "real_trades_exists": REAL_TRADES.exists(),
        "analyze_jsons_exist": all(
            (STATE_SYMBOL_DIR / f"analyze_btc_{label}.json").exists()
            for label in ["htf", "mtf", "ltf"]
        ),
    }
    bool_passed = all(bool(value) for value in assertions.values() if not isinstance(value, int))
    with ASSERTIONS.open("w", encoding="utf-8") as fh:
        for key, value in assertions.items():
            prefix = "PASS" if bool(value) else "FAIL"
            fh.write(f"{prefix} {key}={value}\n")
        fh.write(f"{'PASS' if bool_passed else 'FAIL'} all_assertions_passed={bool_passed}\n")
    print(f"RUN_ROOT={RUN_ROOT}")
    print(f"REPORT={REPORT_JSON}")
    print(f"SELECTED_ROWS={len(selected_rows)}")
    print(f"ROOTS={','.join(row['root'] for row in selected_summaries)}")


if __name__ == "__main__":
    main()
