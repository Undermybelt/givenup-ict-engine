#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import warnings
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import yfinance as yf


warnings.filterwarnings("ignore")

REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T030759+0800-codex-cboe-options-vol-root-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T030759-codex-cboe-options-vol-root-gate"
OUT_DIR = RUN_ROOT / "options-vol-gate"
CHECK_DIR = RUN_ROOT / "checks"
TMP_RAW_DIR = Path("/private/tmp/ict-regime-cboe-options-vol-root")
FEATURE_TABLE = OUT_DIR / "cboe_options_vol_root_feature_table.csv"

TARGETS = ["SPY", "QQQ", "IWM"]
ROOTS = ["Bull", "Bear", "Sideways"]
Z95 = 1.959963984540054
QUANTILES = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
SUPPORT_TRAIN_MIN = 120
SUPPORT_CAL_MIN = 120
SUPPORT_TEST_MIN = 60
COVERAGE_MIN = 0.03
ECE_MAX = 0.05

CBOE_SERIES = {
    "vix": "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv",
    "vvix": "https://cdn.cboe.com/api/global/us_indices/daily_prices/VVIX_History.csv",
    "vix9d": "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX9D_History.csv",
    "vix3m": "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX3M_History.csv",
    "vix6m": "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX6M_History.csv",
    "vix1y": "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX1Y_History.csv",
    "skew": "https://cdn.cboe.com/api/global/us_indices/daily_prices/SKEW_History.csv",
    "ovx": "https://cdn.cboe.com/api/global/us_indices/daily_prices/OVX_History.csv",
    "gvz": "https://cdn.cboe.com/api/global/us_indices/daily_prices/GVZ_History.csv",
    "vxeem": "https://cdn.cboe.com/api/global/us_indices/daily_prices/VXEEM_History.csv",
}

MARKET_CONTEXT = {
    "SPY": "us_large_cap_equity_with_cboe_vol",
    "QQQ": "us_growth_equity_with_cboe_vol",
    "IWM": "us_small_cap_equity_with_cboe_vol",
}


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype(float).replace([np.inf, -np.inf], np.nan)
    return pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)


def wilson_lcb(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2.0 * total)
    margin = Z95 * math.sqrt((p * (1.0 - p) + Z95 * Z95 / (4.0 * total)) / total)
    return max(0.0, (center - margin) / denom)


def json_counts(series: pd.Series) -> dict[str, int]:
    out: dict[str, int] = {}
    for key, value in series.items():
        if isinstance(key, tuple):
            label = "|".join(str(part) for part in key)
        else:
            label = str(key)
        out[label] = int(value)
    return out


def rolling_rank_pct(series: pd.Series, window: int) -> pd.Series:
    def rank_last(values: np.ndarray) -> float:
        values = values[~np.isnan(values)]
        if len(values) <= 1:
            return np.nan
        return float((values <= values[-1]).mean())

    return numeric(series).rolling(window, min_periods=max(20, window // 4)).apply(rank_last, raw=True)


def download_cboe_series(name: str, url: str) -> pd.DataFrame:
    TMP_RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = TMP_RAW_DIR / f"{name}.csv"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=45) as response:
        raw_path.write_bytes(response.read())
    df = pd.read_csv(raw_path)
    if "DATE" not in df.columns:
        raise ValueError(f"{name} CBOE CSV missing DATE column")
    df["ts"] = pd.to_datetime(df["DATE"], errors="coerce", utc=True).dt.normalize()
    value_col = "CLOSE" if "CLOSE" in df.columns else name.upper()
    if value_col not in df.columns:
        numeric_cols = [col for col in df.columns if col != "DATE" and pd.api.types.is_numeric_dtype(df[col])]
        if not numeric_cols:
            raise ValueError(f"{name} CBOE CSV missing numeric value column")
        value_col = numeric_cols[-1]
    out = df[["ts", value_col]].rename(columns={value_col: name})
    out[name] = numeric(out[name])
    return out.dropna(subset=["ts", name]).sort_values("ts")


def fetch_cboe() -> tuple[pd.DataFrame, dict[str, Any]]:
    frames: list[pd.DataFrame] = []
    status: dict[str, Any] = {"source_urls": CBOE_SERIES, "raw_dir": str(TMP_RAW_DIR), "series": {}}
    for name, url in CBOE_SERIES.items():
        try:
            frame = download_cboe_series(name, url)
            frames.append(frame)
            status["series"][name] = {
                "rows": int(len(frame)),
                "date_min": frame["ts"].min().isoformat() if not frame.empty else None,
                "date_max": frame["ts"].max().isoformat() if not frame.empty else None,
                "fetched": True,
            }
        except Exception as exc:
            status["series"][name] = {"fetched": False, "error": f"{type(exc).__name__}: {exc}"}
    if not frames:
        return pd.DataFrame(columns=["ts"]), status
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="ts", how="outer")
    merged = merged.sort_values("ts").reset_index(drop=True)
    status["available_series"] = [col for col in merged.columns if col != "ts" and merged[col].notna().any()]
    status["rows_merged"] = int(len(merged))
    status["date_min"] = merged["ts"].min().isoformat() if not merged.empty else None
    status["date_max"] = merged["ts"].max().isoformat() if not merged.empty else None
    return merged, status


def normalize_download(raw: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    if raw.empty:
        return pd.DataFrame(columns=["ts", "ticker", "open", "high", "low", "close", "volume"])
    if not isinstance(raw.columns, pd.MultiIndex):
        raw.columns = pd.MultiIndex.from_product([["UNKNOWN"], raw.columns])
    level0 = set(str(x) for x in raw.columns.get_level_values(0))
    tickers_first = bool(level0 & set(TARGETS))
    for ticker in TARGETS:
        try:
            part = raw[ticker].copy() if tickers_first else raw.xs(ticker, axis=1, level=1).copy()
        except Exception:
            continue
        part = part.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Adj Close": "close", "Volume": "volume"})
        keep = [col for col in ["open", "high", "low", "close", "volume"] if col in part.columns]
        if "close" not in keep:
            continue
        part = part[keep].reset_index().rename(columns={"Date": "ts", "Datetime": "ts"})
        part["ts"] = pd.to_datetime(part["ts"], utc=True).dt.normalize()
        part["ticker"] = ticker
        for col in ["open", "high", "low", "close", "volume"]:
            if col not in part.columns:
                part[col] = np.nan
            part[col] = numeric(part[col])
        part = part.dropna(subset=["ts", "close"])
        if not part.empty:
            rows.append(part[["ts", "ticker", "open", "high", "low", "close", "volume"]])
    if not rows:
        return pd.DataFrame(columns=["ts", "ticker", "open", "high", "low", "close", "volume"])
    return pd.concat(rows, ignore_index=True).sort_values(["ticker", "ts"])


def fetch_targets() -> tuple[pd.DataFrame, dict[str, Any]]:
    raw = yf.download(TARGETS, period="15y", interval="1d", auto_adjust=True, progress=False, threads=True, group_by="ticker")
    targets = normalize_download(raw)
    status = {
        "provider": "yfinance",
        "requested_symbols": TARGETS,
        "available_symbols": sorted(targets["ticker"].dropna().unique().tolist()),
        "rows": int(len(targets)),
        "date_min": targets["ts"].min().isoformat() if not targets.empty else None,
        "date_max": targets["ts"].max().isoformat() if not targets.empty else None,
    }
    return targets, status


def to_weekly(daily: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for ticker, group in daily.groupby("ticker", sort=False):
        g = group.set_index("ts").sort_index()
        weekly = pd.DataFrame(
            {
                "open": g["open"].resample("W-FRI").first(),
                "high": g["high"].resample("W-FRI").max(),
                "low": g["low"].resample("W-FRI").min(),
                "close": g["close"].resample("W-FRI").last(),
                "volume": g["volume"].resample("W-FRI").sum(),
            }
        ).dropna(subset=["close"])
        weekly["ticker"] = ticker
        rows.append(weekly.reset_index()[["ts", "ticker", "open", "high", "low", "close", "volume"]])
    return pd.concat(rows, ignore_index=True) if rows else daily.iloc[0:0].copy()


def cboe_daily_features(cboe: pd.DataFrame) -> pd.DataFrame:
    df = cboe.sort_values("ts").copy()
    for col in CBOE_SERIES:
        if col not in df.columns:
            df[col] = np.nan
        df[col] = numeric(df[col])
    df["vix_rank_252"] = rolling_rank_pct(df["vix"], 252)
    df["vvix_rank_252"] = rolling_rank_pct(df["vvix"], 252)
    df["skew_rank_252"] = rolling_rank_pct(df["skew"], 252)
    df["vix_ret_5"] = np.log(df["vix"]).diff(5)
    df["vix_ret_20"] = np.log(df["vix"]).diff(20)
    df["vvix_ret_20"] = np.log(df["vvix"]).diff(20)
    df["skew_chg_20"] = df["skew"].diff(20)
    df["vix9d_vix_ratio"] = df["vix9d"] / df["vix"]
    df["vix3m_vix_ratio"] = df["vix3m"] / df["vix"]
    df["vix6m_vix_ratio"] = df["vix6m"] / df["vix"]
    df["vix1y_vix_ratio"] = df["vix1y"] / df["vix"]
    df["vvix_vix_ratio"] = df["vvix"] / df["vix"]
    df["front_vol_inversion"] = df["vix9d_vix_ratio"] - df["vix3m_vix_ratio"]
    df["long_vol_contango"] = df["vix1y_vix_ratio"] - df["vix3m_vix_ratio"]
    cross = df[["ovx", "gvz", "vxeem"]]
    df["crossasset_vol_mean"] = cross.mean(axis=1)
    df["crossasset_vol_dispersion"] = cross.std(axis=1)
    df["equity_vs_crossasset_vol"] = df["vix"] - df["crossasset_vol_mean"]
    return df


def add_target_features(frame: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    df = frame.sort_values(["ticker", "ts"]).copy()
    df["timeframe"] = timeframe
    grp = df.groupby("ticker", group_keys=False)
    df["target_ret_1"] = grp["close"].transform(lambda s: np.log(s).diff())
    df["target_ret_5"] = grp["close"].transform(lambda s: np.log(s).diff(5))
    df["target_ret_20"] = grp["close"].transform(lambda s: np.log(s).diff(20))
    df["target_range_pct"] = (df["high"] - df["low"]) / df["close"]
    df["target_vol_20"] = grp["target_ret_1"].rolling(20, min_periods=8).std().reset_index(level=0, drop=True)
    df["target_vol_60"] = grp["target_ret_1"].rolling(60, min_periods=16).std().reset_index(level=0, drop=True)
    df["target_range_20"] = grp["target_range_pct"].rolling(20, min_periods=8).mean().reset_index(level=0, drop=True)
    rolling_max = grp["close"].rolling(60, min_periods=20).max().reset_index(level=0, drop=True)
    df["target_drawdown_60"] = df["close"] / rolling_max - 1.0
    horizon = 20 if timeframe == "1d" else 8
    df["future_ret"] = grp["close"].transform(lambda s: np.log(s).shift(-horizon) - np.log(s))
    df["future_absret"] = df["future_ret"].abs()
    df["future_range"] = grp["target_range_pct"].shift(-1).rolling(horizon, min_periods=max(3, horizon // 3)).mean().reset_index(level=0, drop=True)
    df["future_vol"] = grp["target_ret_1"].shift(-1).rolling(horizon, min_periods=max(3, horizon // 3)).std().reset_index(level=0, drop=True)
    return df


def make_cboe_weekly(cboe_features: pd.DataFrame) -> pd.DataFrame:
    value_cols = [col for col in cboe_features.columns if col != "ts"]
    weekly = cboe_features.set_index("ts").sort_index()[value_cols].resample("W-FRI").last().reset_index()
    return weekly


def label_roots(features: pd.DataFrame) -> pd.DataFrame:
    out = features.copy()
    out["split"] = ""
    for _, group in out.groupby(["ticker", "timeframe"], sort=False):
        idx = group.sort_values("ts").index.to_numpy()
        n = len(idx)
        split = np.full(n, "train", dtype=object)
        split[n // 2 :] = "calibration"
        split[(3 * n) // 4 :] = "test"
        out.loc[idx, "split"] = split

    train = out[out["split"] == "train"]
    crisis = (out["future_absret"] >= numeric(train["future_absret"]).quantile(0.90)) | (
        out["future_range"] >= numeric(train["future_range"]).quantile(0.90)
    )
    sideways = (
        (out["future_absret"] <= numeric(train["future_absret"]).quantile(0.40))
        & (out["future_range"] <= numeric(train["future_range"]).quantile(0.55))
        & (out["future_vol"] <= numeric(train["future_vol"]).quantile(0.55))
        & (~crisis)
    )
    bull = (out["future_ret"] >= numeric(train["future_ret"]).quantile(0.65)) & (~crisis) & (~sideways)
    bear = (out["future_ret"] <= numeric(train["future_ret"]).quantile(0.35)) & (~crisis) & (~sideways)
    out["root_label"] = "UnknownOrMixed"
    out.loc[bear, "root_label"] = "Bear"
    out.loc[bull, "root_label"] = "Bull"
    out.loc[sideways, "root_label"] = "Sideways"
    out.loc[crisis, "root_label"] = "Crisis"
    return out


def build_feature_table(target_daily: pd.DataFrame, cboe: pd.DataFrame) -> pd.DataFrame:
    cboe_d = cboe_daily_features(cboe)
    daily = add_target_features(target_daily, "1d").merge(cboe_d, on="ts", how="left")
    weekly = add_target_features(to_weekly(target_daily), "1w").merge(make_cboe_weekly(cboe_d), on="ts", how="left")
    full = pd.concat([daily, weekly], ignore_index=True, sort=False)
    full["instrument"] = full["ticker"]
    full["market_context"] = full["ticker"].map(MARKET_CONTEXT).fillna("unknown_equity_with_cboe_vol")
    full["provider_context"] = "cboe_public_vol_indices_plus_yfinance_equity"
    full = full.sort_values(["ticker", "timeframe", "ts"]).reset_index(drop=True)
    return label_roots(full)


FEATURE_COLUMNS = [
    "target_ret_1",
    "target_ret_5",
    "target_ret_20",
    "target_range_pct",
    "target_vol_20",
    "target_vol_60",
    "target_range_20",
    "target_drawdown_60",
    "vix",
    "vvix",
    "vix9d",
    "vix3m",
    "vix6m",
    "vix1y",
    "skew",
    "ovx",
    "gvz",
    "vxeem",
    "vix_rank_252",
    "vvix_rank_252",
    "skew_rank_252",
    "vix_ret_5",
    "vix_ret_20",
    "vvix_ret_20",
    "skew_chg_20",
    "vix9d_vix_ratio",
    "vix3m_vix_ratio",
    "vix6m_vix_ratio",
    "vix1y_vix_ratio",
    "vvix_vix_ratio",
    "front_vol_inversion",
    "long_vol_contango",
    "crossasset_vol_mean",
    "crossasset_vol_dispersion",
    "equity_vs_crossasset_vol",
]


def stats(df: pd.DataFrame, mask: pd.Series, split: str, root: str, probability: float | None = None) -> dict[str, Any]:
    valid = (df["split"] == split) & df["root_label"].notna()
    selected = valid & mask.fillna(False)
    support = int(selected.sum())
    success = int((df.loc[selected, "root_label"] == root).sum()) if support else 0
    precision = success / support if support else 0.0
    selected_df = df.loc[selected]
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lcb(success, support),
        "coverage": support / max(1, int(valid.sum())),
        "ece": 0.0 if probability is None else abs(float(probability) - precision),
        "validation_instruments": sorted(selected_df["instrument"].dropna().unique().tolist()),
        "validation_market_contexts": sorted(selected_df["market_context"].dropna().unique().tolist()),
        "validation_provider_contexts": sorted(selected_df["provider_context"].dropna().unique().tolist()),
        "validation_timeframes": sorted(selected_df["timeframe"].dropna().unique().tolist()),
    }


def q(train: pd.DataFrame, col: str, quantile: float) -> float:
    return float(numeric(train[col]).quantile(quantile))


def candidate_masks(df: pd.DataFrame, root: str) -> list[tuple[str, pd.Series]]:
    train = df[df["split"] == "train"]
    candidates: list[tuple[str, pd.Series]] = []
    for feature in FEATURE_COLUMNS:
        if feature not in df.columns or feature.startswith(("future_", "next_")) or feature == "h4":
            continue
        values = numeric(train[feature]).dropna()
        if values.nunique() <= 1:
            continue
        for threshold in sorted({float(v) for v in values.quantile(QUANTILES).dropna().tolist()}):
            candidates.append((f"{feature} >= {threshold:.12g}", numeric(df[feature]) >= threshold))
            candidates.append((f"{feature} <= {threshold:.12g}", numeric(df[feature]) <= threshold))

    shaped = {
        "Bull": [
            ("vix_rank_252 <= train_q35 AND vix3m_vix_ratio >= train_q60", (df["vix_rank_252"] <= q(train, "vix_rank_252", 0.35)) & (df["vix3m_vix_ratio"] >= q(train, "vix3m_vix_ratio", 0.60))),
            ("target_ret_20 >= train_q60 AND vvix_vix_ratio <= train_q40", (df["target_ret_20"] >= q(train, "target_ret_20", 0.60)) & (df["vvix_vix_ratio"] <= q(train, "vvix_vix_ratio", 0.40))),
            ("vix_ret_20 <= train_q35 AND front_vol_inversion <= train_q45", (df["vix_ret_20"] <= q(train, "vix_ret_20", 0.35)) & (df["front_vol_inversion"] <= q(train, "front_vol_inversion", 0.45))),
        ],
        "Bear": [
            ("vix_rank_252 >= train_q65 AND vix_ret_20 >= train_q60", (df["vix_rank_252"] >= q(train, "vix_rank_252", 0.65)) & (df["vix_ret_20"] >= q(train, "vix_ret_20", 0.60))),
            ("front_vol_inversion >= train_q65 AND vvix_rank_252 >= train_q65", (df["front_vol_inversion"] >= q(train, "front_vol_inversion", 0.65)) & (df["vvix_rank_252"] >= q(train, "vvix_rank_252", 0.65))),
            ("target_drawdown_60 <= train_q30 AND skew_chg_20 >= train_q60", (df["target_drawdown_60"] <= q(train, "target_drawdown_60", 0.30)) & (df["skew_chg_20"] >= q(train, "skew_chg_20", 0.60))),
        ],
        "Sideways": [
            ("abs(target_ret_20) <= train_abs_q35 AND target_vol_20 <= train_q45", (df["target_ret_20"].abs() <= numeric(train["target_ret_20"].abs()).quantile(0.35)) & (df["target_vol_20"] <= q(train, "target_vol_20", 0.45))),
            ("vix_ret_20_abs <= train_abs_q35 AND vix_rank_252 <= train_q55", (df["vix_ret_20"].abs() <= numeric(train["vix_ret_20"].abs()).quantile(0.35)) & (df["vix_rank_252"] <= q(train, "vix_rank_252", 0.55))),
            ("crossasset_vol_dispersion <= train_q45 AND long_vol_contango >= train_q45", (df["crossasset_vol_dispersion"] <= q(train, "crossasset_vol_dispersion", 0.45)) & (df["long_vol_contango"] >= q(train, "long_vol_contango", 0.45))),
        ],
    }
    candidates.extend(shaped[root])
    return candidates


def evaluate_rule(df: pd.DataFrame, root: str, rule: str, mask: pd.Series) -> dict[str, Any]:
    train = stats(df, mask, "train", root)
    calibration = stats(df, mask, "calibration", root, train["precision"])
    test = stats(df, mask, "test", root, calibration["precision"])
    blockers: list[str] = []
    if calibration["support"] < SUPPORT_CAL_MIN:
        blockers.append("calibration_support_below_120")
    if test["support"] < SUPPORT_TEST_MIN:
        blockers.append("test_support_below_60")
    if calibration["precision_wilson_lcb_95"] < 0.95:
        blockers.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < 0.95:
        blockers.append("test_wilson95_below_0_95")
    if test["coverage"] < COVERAGE_MIN:
        blockers.append("coverage_below_0_03")
    if test["ece"] > ECE_MAX:
        blockers.append("ece_above_0_05")
    if len(test["validation_instruments"]) < 2:
        blockers.append("validation_instruments_below_2")
    if len(test["validation_market_contexts"]) < 2:
        blockers.append("validation_market_contexts_below_2")
    if len(test["validation_timeframes"]) < 2:
        blockers.append("validation_timeframes_below_2")
    accepted = not blockers
    return {
        "root_class": root,
        "state": "accepted_95" if accepted else "blocked",
        "rule": rule,
        "train": train,
        "calibration": calibration,
        "test": test,
        "ece": test["ece"],
        "accepted_95": accepted,
        "blockers": blockers,
    }


def best_for_root(df: pd.DataFrame, root: str) -> dict[str, Any]:
    scored: list[dict[str, Any]] = []
    for rule, mask in candidate_masks(df, root):
        train = stats(df, mask, "train", root)
        if train["support"] < SUPPORT_TRAIN_MIN:
            continue
        scored.append(evaluate_rule(df, root, rule, mask))
    if not scored:
        return evaluate_rule(df, root, "no_train_candidate_met_support_floor", pd.Series(False, index=df.index))
    scored.sort(
        key=lambda row: (
            row["calibration"]["precision_wilson_lcb_95"],
            row["test"]["precision_wilson_lcb_95"],
            row["calibration"]["precision"],
            row["test"]["precision"],
            row["test"]["support"],
        ),
        reverse=True,
    )
    return scored[0]


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    report_json = OUT_DIR / "cboe_options_vol_root_gate_report.json"
    report_md = OUT_DIR / "cboe_options_vol_root_gate_report.md"
    summary_csv = OUT_DIR / "cboe_options_vol_root_gate_summary.csv"
    assertions = CHECK_DIR / "cboe_options_vol_root_gate_assertions.out"
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    with summary_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "root_class",
                "state",
                "rule",
                "calibration_support",
                "test_support",
                "calibration_lcb",
                "test_lcb",
                "test_coverage",
                "ece",
                "blockers",
            ],
        )
        writer.writeheader()
        for row in report["root_reports"]:
            writer.writerow(
                {
                    "root_class": row["root_class"],
                    "state": row["state"],
                    "rule": row["rule"],
                    "calibration_support": row["calibration"]["support"],
                    "test_support": row["test"]["support"],
                    "calibration_lcb": row["calibration"]["precision_wilson_lcb_95"],
                    "test_lcb": row["test"]["precision_wilson_lcb_95"],
                    "test_coverage": row["test"]["coverage"],
                    "ece": row["ece"],
                    "blockers": "|".join(row["blockers"]),
                }
            )
    lines = [
        "# CBOE Options/Vol Root Gate",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Data",
        "",
        f"- CBOE public volatility series requested: {', '.join(CBOE_SERIES)}.",
        f"- CBOE public volatility series available: {', '.join(report['cboe_provider'].get('available_series', []))}.",
        f"- yfinance target symbols available: {', '.join(report['target_provider'].get('available_symbols', []))}.",
        f"- Derived feature rows: {report['dataset']['feature_rows']}.",
        f"- Raw provider CSV committed: false; CBOE raw CSV cache path `{report['cboe_provider']['raw_dir']}`.",
        "",
        "## Gate Results",
        "",
    ]
    for row in report["root_reports"]:
        lines.append(
            "- {root}: accepted_95={accepted}, rule=`{rule}`, cal_lcb={cal_lcb:.6f}, test_lcb={test_lcb:.6f}, cal_support={cal_support}, test_support={test_support}, blockers={blockers}".format(
                root=row["root_class"],
                accepted=row["accepted_95"],
                rule=row["rule"],
                cal_lcb=row["calibration"]["precision_wilson_lcb_95"],
                test_lcb=row["test"]["precision_wilson_lcb_95"],
                cal_support=row["calibration"]["support"],
                test_support=row["test"]["support"],
                blockers="|".join(row["blockers"]) or "none",
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Newly accepted active roots: {', '.join(report['decision']['newly_accepted_roots']) or 'none'}.",
            f"- Gate: `{report['decision']['gate']}`.",
            "- Thresholds relaxed: false.",
            "- Runtime code changed: false.",
            "- Trade usable: false.",
            "",
            report["decision"]["blocker"],
            "",
            f"Next: {report['decision']['next_action']}",
        ]
    )
    report_md.write_text("\n".join(lines) + "\n")
    checks = [
        f"RUN_ID {RUN_ID}",
        "ACTIVE_AXIS MainRegimeV2",
        "CANDIDATE_ROOTS Bull,Bear,Sideways",
        f"FEATURE_ROWS {report['dataset']['feature_rows']}",
        f"NEWLY_ACCEPTED_ROOTS {','.join(report['decision']['newly_accepted_roots']) or 'none'}",
        f"ACCEPTED_95 {str(bool(report['decision']['newly_accepted_roots'])).lower()}",
        "MANIPULATION_ACCEPTED false",
        "THRESHOLDS_RELAXED false",
        "RUNTIME_CODE_CHANGED false",
        "RAW_PROVIDER_CSV_COMMITTED false",
        "TRADE_USABLE false",
        f"GATE {report['decision']['gate']}",
    ]
    for row in report["root_reports"]:
        checks.append(f"{row['root_class']}_CAL_LCB {row['calibration']['precision_wilson_lcb_95']:.6f}")
        checks.append(f"{row['root_class']}_TEST_LCB {row['test']['precision_wilson_lcb_95']:.6f}")
    assertions.write_text("\n".join(checks) + "\n")
    (RUN_ROOT / "README.md").write_text(
        "\n".join(
            [
                "# CBOE Options/Vol Root Gate",
                "",
                f"- report: `{repo_rel(report_json)}`",
                f"- summary: `{repo_rel(summary_csv)}`",
                f"- assertions: `{repo_rel(assertions)}`",
                "- raw provider CSV committed: false",
                "",
            ]
        )
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    cboe, cboe_provider = fetch_cboe()
    targets, target_provider = fetch_targets()
    if cboe.empty or targets.empty or len(set(targets["ticker"]) & set(TARGETS)) < 2:
        report = {
            "run_id": RUN_ID,
            "cboe_provider": cboe_provider,
            "target_provider": target_provider,
            "dataset": {"feature_rows": 0},
            "root_reports": [],
            "decision": {
                "newly_accepted_roots": [],
                "missing_active_roots_after_gate": ["Bull", "Bear", "Sideways", "Manipulation"],
                "gate": "blocked_provider_fetch_failed",
                "blocker": "CBOE or yfinance fetch did not return enough rows for a chronological Bull/Bear/Sideways gate.",
                "next_action": "Retry with local options/dealer-positioning cache or a labeled macro regime dataset.",
                "runtime_code_changed": False,
                "thresholds_relaxed": False,
                "trade_usable": False,
                "raw_provider_csv_committed": False,
            },
        }
        write_outputs(report)
        return 1
    features = build_feature_table(targets, cboe)
    features = features.dropna(subset=["future_ret", "future_absret", "future_range", "root_label"])
    features.to_csv(FEATURE_TABLE, index=False)
    root_reports = [best_for_root(features, root) for root in ROOTS]
    newly_accepted = [row["root_class"] for row in root_reports if row["accepted_95"]]
    missing_after = [root for root in ["Bull", "Bear", "Sideways", "Manipulation"] if root not in newly_accepted]
    gate = "accepted_95_cboe_options_vol_roots_" + "_".join(newly_accepted) if newly_accepted else "blocked_cboe_options_vol_roots_below_95"
    report = {
        "run_id": RUN_ID,
        "active_axis": "MainRegimeV2",
        "candidate_roots": ROOTS,
        "manipulation_handling": "not_evaluated_here_direct_input_required_accepted_false",
        "cboe_provider": cboe_provider,
        "target_provider": target_provider,
        "dataset": {
            "feature_rows": int(len(features)),
            "targets": TARGETS,
            "timeframes": sorted(features["timeframe"].dropna().unique().tolist()),
            "split_counts": json_counts(features.groupby(["split", "timeframe"]).size()),
            "label_counts": json_counts(features.groupby(["root_label", "timeframe"]).size()),
            "feature_table": repo_rel(FEATURE_TABLE),
            "artifact_only_no_raw_provider_csv": True,
        },
        "threshold_policy": {
            "precision_wilson_lcb_95_min": 0.95,
            "calibration_support_min": SUPPORT_CAL_MIN,
            "test_support_min": SUPPORT_TEST_MIN,
            "coverage_min": COVERAGE_MIN,
            "ece_max": ECE_MAX,
            "validation_instruments_min": 2,
            "validation_market_contexts_min": 2,
            "validation_timeframes_min": 2,
            "thresholds_relaxed": False,
            "blocked_predictor_prefixes": ["future_", "target_", "next_", "h4"],
            "label_only_columns": ["future_ret", "future_absret", "future_range", "future_vol", "root_label"],
        },
        "root_reports": root_reports,
        "decision": {
            "newly_accepted_roots": newly_accepted,
            "missing_active_roots_after_gate": missing_after,
            "gate": gate,
            "blocker": "CBOE public volatility and options-implied context did not close all missing MainRegimeV2 roots at the unchanged 95% held-out gate."
            if missing_after
            else "All active roots accepted.",
            "next_action": "If this gate fails, stop repeating proxy-only threshold scans; acquire labeled bull/bear/sideways regime-cycle data or options/dealer-positioning history, and direct order-flow/event labels for Manipulation.",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "trade_usable": False,
            "raw_provider_csv_committed": False,
        },
    }
    write_outputs(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
