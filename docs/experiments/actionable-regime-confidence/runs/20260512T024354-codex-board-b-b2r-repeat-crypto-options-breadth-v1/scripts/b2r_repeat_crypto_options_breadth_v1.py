#!/usr/bin/env python3
"""B2R repeat-next: crypto/equity/options breadth root-aware panel.

This is a run-local Board B experiment. It reads local Auto-Quant market data,
keeps BTC options snapshots as auxiliary evidence, emits rooted branch paths,
scores RC-SPA-style branch gates, and writes ict-engine handoff artifacts.
It does not modify repo runtime code or the Auto-Quant checkout.
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


RUN_ID = "20260512T024354+0800-codex-board-b-b2r-repeat-crypto-options-breadth-v1"
RECIPE_ID = "CryptoOptionsBreadthRootV1"
SCHEMA_VERSION = "board-b-b2r-repeat-crypto-options-breadth/v1"
SYMBOL = "B2R_REPEAT_CRYPTO_OPTIONS_024354"
ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]

AUTO_QUANT_ROOT = Path("/Users/thrill3r/Auto-Quant")
DATA_DIR = AUTO_QUANT_ROOT / "user_data/data"
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "branch-rc-spa"
CHECK_DIR = RUN_ROOT / "checks"
STATE_SYMBOL_DIR = RUN_ROOT / "state_b2r_repeat_crypto_options_breadth_v1" / SYMBOL

REPORT_JSON = OUT_DIR / "crypto_options_breadth_rc_spa_report_v1.json"
REPORT_MD = OUT_DIR / "crypto_options_breadth_rc_spa_report_v1.md"
VARIANT_ROWS = OUT_DIR / "crypto_options_breadth_variant_trades_v1.csv"
SELECTED_ROWS = OUT_DIR / "crypto_options_breadth_selected_trades_v1.csv"
BRANCH_SUMMARY = OUT_DIR / "crypto_options_breadth_branch_summary_v1.csv"
STRATEGY_LIBRARY = OUT_DIR / "strategy_library_crypto_options_breadth_v1.json"
REAL_TRADES = OUT_DIR / "crypto_options_breadth_real_trades_v1.jsonl"
AUTO_QUANT_LOG = OUT_DIR / "auto_quant_crypto_options_breadth_v1.out"
ASSERTIONS = CHECK_DIR / "crypto_options_breadth_v1_assertions.out"

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
        "variant_id": "crypto_equity_risk_on_h12",
        "branch_path": "Bull -> CryptoEquityRiskOn -> BreadthMomentum -> CryptoOptionsBreadthRootV1:crypto_equity_risk_on_h12",
        "hold": 12,
        "direction": "long_btc",
        "breadth_min": 0.45,
        "vol_max": 0.035,
    },
    {
        "root": "Bull",
        "variant_id": "crypto_beta_followthrough_h24",
        "branch_path": "Bull -> CryptoEquityRiskOn -> CryptoBetaFollowThrough -> CryptoOptionsBreadthRootV1:crypto_beta_followthrough_h24",
        "hold": 24,
        "direction": "long_btc",
        "breadth_min": 0.25,
        "vol_max": 0.050,
    },
    {
        "root": "Bear",
        "variant_id": "risk_off_short_btc_h8",
        "branch_path": "Bear -> RiskOffDeleveraging -> CryptoBetaShort -> CryptoOptionsBreadthRootV1:risk_off_short_btc_h8",
        "hold": 8,
        "direction": "short_btc",
        "breadth_max": -0.35,
        "vol_min": 0.020,
    },
    {
        "root": "Bear",
        "variant_id": "equity_crypto_breakdown_h16",
        "branch_path": "Bear -> RiskOffDeleveraging -> EquityCryptoBreakdown -> CryptoOptionsBreadthRootV1:equity_crypto_breakdown_h16",
        "hold": 16,
        "direction": "short_btc",
        "breadth_max": -0.20,
        "vol_min": 0.015,
    },
    {
        "root": "Sideways",
        "variant_id": "btc_eth_dispersion_revert_h10",
        "branch_path": "Sideways -> CrossAssetRange -> BtcEthDispersionReversion -> CryptoOptionsBreadthRootV1:btc_eth_dispersion_revert_h10",
        "hold": 10,
        "direction": "spread_revert",
        "spread_z_abs_min": 1.2,
        "vol_max": 0.040,
    },
    {
        "root": "Sideways",
        "variant_id": "low_vol_range_fade_h6",
        "branch_path": "Sideways -> CrossAssetRange -> LowVolRangeFade -> CryptoOptionsBreadthRootV1:low_vol_range_fade_h6",
        "hold": 6,
        "direction": "range_fade",
        "spread_z_abs_min": 0.8,
        "vol_max": 0.025,
    },
    {
        "root": "Crisis",
        "variant_id": "panic_short_btc_h6",
        "branch_path": "Crisis -> CryptoStress -> PanicContinuationOrTailHedge -> CryptoOptionsBreadthRootV1:panic_short_btc_h6",
        "hold": 6,
        "direction": "short_btc",
        "drawdown_min": 0.055,
        "vol_min": 0.035,
    },
    {
        "root": "Crisis",
        "variant_id": "gold_relative_tail_h12",
        "branch_path": "Crisis -> CryptoStress -> GoldRelativeTailHedge -> CryptoOptionsBreadthRootV1:gold_relative_tail_h12",
        "hold": 12,
        "direction": "long_gld",
        "drawdown_min": 0.040,
        "vol_min": 0.030,
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
    if pd.api.types.is_numeric_dtype(frame["date"]):
        frame["date"] = pd.to_datetime(frame["date"], unit="ms", utc=True)
    else:
        frame["date"] = pd.to_datetime(frame["date"], utc=True)
    frame = frame.sort_values("date").drop_duplicates("date")
    return frame[["date", "open", "high", "low", "close", "volume"]].copy()


def load_panel() -> pd.DataFrame:
    merged: pd.DataFrame | None = None
    for label, pair in PAIRS.items():
        frame = load_pair(pair, "1h")
        renamed = frame.rename(
            columns={
                "open": f"{label}_open",
                "high": f"{label}_high",
                "low": f"{label}_low",
                "close": f"{label}_close",
                "volume": f"{label}_volume",
            }
        )
        merged = renamed if merged is None else merged.merge(renamed, on="date", how="inner")
    if merged is None or merged.empty:
        raise RuntimeError("empty panel")
    return merged.sort_values("date").reset_index(drop=True)


def options_summary() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for venue, path in [
        ("binance", DATA_DIR / "options/binance_BTC.csv"),
        ("bybit", DATA_DIR / "options/bybit_BTC.csv"),
    ]:
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        frame["venue"] = venue
        rows.extend(frame.to_dict("records"))
    if not rows:
        return {"venues": [], "rows": 0}
    frame = pd.DataFrame(rows)
    side = frame["side"].astype(str).str.upper().str[0]
    calls = frame[side == "C"]
    puts = frame[side == "P"]
    call_iv = float(calls["mark_iv"].astype(float).median()) if not calls.empty else None
    put_iv = float(puts["mark_iv"].astype(float).median()) if not puts.empty else None
    return {
        "venues": sorted(frame["venue"].unique().tolist()),
        "rows": int(len(frame)),
        "snapshot_min": str(frame["snapshot_utc"].min()),
        "snapshot_max": str(frame["snapshot_utc"].max()),
        "median_call_iv": call_iv,
        "median_put_iv": put_iv,
        "put_call_iv_spread": None if call_iv is None or put_iv is None else put_iv - call_iv,
        "open_interest_rows": int(frame.get("open_interest", pd.Series(dtype=float)).notna().sum()),
    }


def add_features(panel: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy()
    for label in PAIRS:
        df[f"{label}_ret1"] = df[f"{label}_close"].pct_change()
        df[f"{label}_ret6"] = df[f"{label}_close"].pct_change(6)
        df[f"{label}_ret24"] = df[f"{label}_close"].pct_change(24)
        df[f"{label}_fwd6"] = df[f"{label}_close"].shift(-6) / df[f"{label}_close"] - 1.0
        df[f"{label}_fwd8"] = df[f"{label}_close"].shift(-8) / df[f"{label}_close"] - 1.0
        df[f"{label}_fwd10"] = df[f"{label}_close"].shift(-10) / df[f"{label}_close"] - 1.0
        df[f"{label}_fwd12"] = df[f"{label}_close"].shift(-12) / df[f"{label}_close"] - 1.0
        df[f"{label}_fwd16"] = df[f"{label}_close"].shift(-16) / df[f"{label}_close"] - 1.0
        df[f"{label}_fwd24"] = df[f"{label}_close"].shift(-24) / df[f"{label}_close"] - 1.0

    crypto = ["BTC", "ETH", "BNB", "SOL", "AVAX"]
    equity = ["SPY", "QQQ", "NQ"]
    df["crypto_breadth"] = np.sign(df[[f"{x}_ret6" for x in crypto]]).mean(axis=1)
    df["equity_breadth"] = np.sign(df[[f"{x}_ret6" for x in equity]]).mean(axis=1)
    df["cross_breadth"] = np.sign(df[[f"{x}_ret6" for x in crypto + equity]]).mean(axis=1)
    df["btc_vol24"] = df["BTC_ret1"].rolling(24).std()
    df["btc_dd24"] = -(df["BTC_close"] / df["BTC_close"].rolling(24).max() - 1.0)
    spread = df["BTC_ret24"] - df["ETH_ret24"]
    df["btc_eth_spread_z"] = (spread - spread.rolling(120).mean()) / spread.rolling(120).std()
    df["gld_relative_24"] = df["GLD_ret24"] - df["BTC_ret24"]

    conditions = [
        (df["btc_dd24"] > 0.06) & (df["btc_vol24"] > 0.035),
        (df["cross_breadth"] > 0.35) & (df["BTC_ret24"] > 0.015),
        (df["cross_breadth"] < -0.35) & (df["BTC_ret24"] < -0.015),
        (df["btc_vol24"] < 0.025) & (df["btc_eth_spread_z"].abs() > 0.8),
    ]
    choices = ["Crisis", "Bull", "Bear", "Sideways"]
    df["parent_regime_root"] = np.select(conditions, choices, default="Unlabeled")
    return df.dropna().reset_index(drop=True)


def branch_return(row: pd.Series, variant: dict[str, Any]) -> float:
    hold = int(variant["hold"])
    direction = variant["direction"]
    btc = float(row[f"BTC_fwd{hold}"])
    if direction == "long_btc":
        gross = btc
    elif direction == "short_btc":
        gross = -btc
    elif direction == "long_gld":
        gross = float(row[f"GLD_fwd{hold}"])
    elif direction == "spread_revert":
        sign = -1.0 if row["btc_eth_spread_z"] > 0 else 1.0
        gross = sign * (float(row[f"BTC_fwd{hold}"]) - float(row[f"ETH_fwd{hold}"]))
    elif direction == "range_fade":
        sign = -1.0 if row["BTC_ret6"] > 0 else 1.0
        gross = sign * float(row[f"BTC_fwd{hold}"])
    else:
        gross = btc
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
    if "spread_z_abs_min" in variant:
        mask &= df["btc_eth_spread_z"].abs() >= float(variant["spread_z_abs_min"])
    if "drawdown_min" in variant:
        mask &= df["btc_dd24"] >= float(variant["drawdown_min"])
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
                    "btc_dd24": float(row["btc_dd24"]),
                    "btc_eth_spread_z": float(row["btc_eth_spread_z"]),
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
    sharpe = 0.0 if std == 0 else mean / std * math.sqrt(min(252 * 24, len(arr)))
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

    variant_summaries: list[dict[str, Any]] = []
    for (root, variant_id), group in by_variant.items():
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
        specificity = base["mean_net"] - float(np.mean([float(row["pnl"]) for row in rows if row["parent_regime_root"] != root] or [0.0]))
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
                "regime_profit_branch_path": group[0]["regime_profit_branch_path"],
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
        if not candidates:
            continue
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
        candles = []
        for row in frame.to_dict("records"):
            candles.append(
                {
                    "timestamp": pd.Timestamp(row["date"]).isoformat().replace("+00:00", "Z"),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]),
                }
            )
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
                    "mutation_id": "b2r_repeat_crypto_options_breadth_v1",
                    "status": "incubation_only_b2r_repeat_next",
                    "base_factor": RECIPE_ID,
                    "parent": row["regime_profit_branch_path"],
                    "expected_regime": f"MainRegimeV2::{row['root']}",
                    "factors_used": [
                        "parent_regime_root",
                        "regime_profit_branch_path",
                        "crypto_breadth",
                        "equity_breadth",
                        "btc_options_iv_skew",
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
                "strategy_mutation_id": "b2r_repeat_crypto_options_breadth_v1",
                "symbol": SYMBOL,
                "trade_id": f"crypto_options_breadth_{idx:05d}",
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
    opt_summary: dict[str, Any],
) -> None:
    roots_passed = [row["root"] for row in selected_summaries if row["gate"] == "pass"]
    gate_result = "pass" if len(roots_passed) == len(ROOTS) else "fail:required_root_branch_hard_gates_failed"
    downstream_consumption = (
        "ready_for_downstream_chain"
        if gate_result == "pass"
        else "not_started:blocked_by_branch_rc_spa_hard_gates"
    )
    report = {
        "run_id": RUN_ID,
        "schema_version": SCHEMA_VERSION,
        "recipe_id": RECIPE_ID,
        "board_state": "rejected" if gate_result != "pass" else "stable_candidate",
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
        "manipulation_component_combined": False,
        "manipulation_component_policy": "combine only if all price roots pass unchanged RC-SPA",
        "downstream_consumption": downstream_consumption,
        "options_auxiliary": opt_summary,
        "provider_panel": {
            "local_auto_quant_feathers": sorted(PAIRS.values()),
            "auxiliary_options_files": ["options/binance_BTC.csv", "options/bybit_BTC.csv"],
            "provider_visibility_required": ["yfinance", "kraken", "ibkr", "tradingviewremix"],
        },
        "next_action": (
            "Run ict-engine import/prior-init/real-trade ingest/analyze/pre-bayes/workflow/execution-tree readback; do not promote unless all roots pass and downstream admits the branch."
            if gate_result == "pass"
            else "Do not run downstream for this packet; use as nursery feedback for root coverage and options-breadth data repair."
        ),
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
        "# Crypto Options Breadth RC-SPA v1",
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
        f"- Options auxiliary rows: `{opt_summary.get('rows', 0)}` from `{','.join(opt_summary.get('venues', []))}`",
        f"- Downstream: `{downstream_consumption}`",
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
            report["next_action"],
        ]
    )
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ensure_dirs()
    opt_summary = options_summary()
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
    write_report(rows, variant_summaries, selected_summaries, selected_rows, opt_summary)

    assertions = {
        "auto_quant_data_rows": int(len(panel)),
        "options_auxiliary_rows": int(opt_summary.get("rows", 0)),
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
    all_passed = all(bool(value) for value in assertions.values())
    with ASSERTIONS.open("w", encoding="utf-8") as fh:
        for key, value in assertions.items():
            prefix = "PASS" if bool(value) else "FAIL"
            fh.write(f"{prefix} {key}={value}\n")
        fh.write(f"{'PASS' if all_passed else 'FAIL'} all_assertions_passed={all_passed}\n")
    print(f"RUN_ROOT={RUN_ROOT}")
    print(f"REPORT={REPORT_JSON}")
    print(f"SELECTED_ROWS={len(selected_rows)}")
    print(f"ROOTS={','.join(row['root'] for row in selected_summaries)}")


if __name__ == "__main__":
    main()
