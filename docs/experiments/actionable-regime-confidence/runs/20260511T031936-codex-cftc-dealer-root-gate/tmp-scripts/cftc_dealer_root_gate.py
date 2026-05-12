#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import warnings
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from zipfile import ZipFile

import numpy as np
import pandas as pd
from pandas.errors import PerformanceWarning
import yfinance as yf


warnings.filterwarnings("ignore", category=PerformanceWarning)


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T031936+0800-codex-cftc-dealer-root-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T031936-codex-cftc-dealer-root-gate"
OUT_DIR = RUN_ROOT / "cftc-dealer-gate"
CHECK_DIR = RUN_ROOT / "checks"
TMP_RAW_DIR = Path("/private/tmp/ict-regime-cftc-dealer-root")

YEARS = list(range(2016, 2027))
CFTC_URL = "https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"
MARKET_ALIASES = {
    "SPY": [
        "S&P 500 Consolidated - CHICAGO MERCANTILE EXCHANGE",
        "E-MINI S&P 500 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE",
        "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE",
    ],
    "QQQ": [
        "NASDAQ-100 Consolidated - CHICAGO MERCANTILE EXCHANGE",
        "NASDAQ-100 STOCK INDEX (MINI) - CHICAGO MERCANTILE EXCHANGE",
        "NASDAQ MINI - CHICAGO MERCANTILE EXCHANGE",
    ],
    "IWM": [
        "RUSSELL E-MINI - CHICAGO MERCANTILE EXCHANGE",
        "E-MINI RUSSELL 2000 INDEX - CHICAGO MERCANTILE EXCHANGE",
        "RUSSELL 2000 MINI INDEX FUTURE - ICE FUTURES U.S.",
        "MICRO E-MINI RUSSELL 2000 INDX - CHICAGO MERCANTILE EXCHANGE",
    ],
}
MARKET_TO_ETF = {market: instrument for instrument, markets in MARKET_ALIASES.items() for market in markets}
MARKET_PRIORITY = {market: priority for instrument, markets in MARKET_ALIASES.items() for priority, market in enumerate(markets)}
ROOTS = ["Bull", "Bear", "Sideways"]
Z95 = 1.959963984540054
SUPPORT_TRAIN_MIN = 120
SUPPORT_CAL_MIN = 80
SUPPORT_TEST_MIN = 40
COVERAGE_MIN = 0.03
ECE_MAX = 0.05
QUANTILES = (0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95)


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)


def wilson_lcb(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2.0 * total)
    margin = Z95 * math.sqrt((p * (1.0 - p) + Z95 * Z95 / (4.0 * total)) / total)
    return max(0.0, (center - margin) / denom)


def fetch_cftc_year(year: int) -> tuple[pd.DataFrame, dict[str, Any]]:
    TMP_RAW_DIR.mkdir(parents=True, exist_ok=True)
    url = CFTC_URL.format(year=year)
    raw_path = TMP_RAW_DIR / f"fut_fin_txt_{year}.zip"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=60) as response:
        payload = response.read()
    raw_path.write_bytes(payload)
    with ZipFile(BytesIO(payload)) as zf:
        member = zf.namelist()[0]
        with zf.open(member) as fh:
            frame = pd.read_csv(fh)
    meta = {
        "year": year,
        "url": url,
        "raw_path": str(raw_path),
        "zip_bytes": len(payload),
        "zip_member": member,
        "rows": int(len(frame)),
    }
    return frame, meta


def fetch_cftc() -> tuple[pd.DataFrame, dict[str, Any]]:
    frames: list[pd.DataFrame] = []
    years: list[dict[str, Any]] = []
    for year in YEARS:
        try:
            frame, meta = fetch_cftc_year(year)
            frames.append(frame)
            years.append(meta | {"fetched": True})
        except Exception as exc:
            years.append({"year": year, "url": CFTC_URL.format(year=year), "fetched": False, "error": f"{type(exc).__name__}: {exc}"})
    if not frames:
        raise RuntimeError("no CFTC yearly files fetched")
    raw = pd.concat(frames, ignore_index=True)
    raw["report_date"] = pd.to_datetime(raw["Report_Date_as_YYYY-MM-DD"], utc=True, errors="coerce").dt.normalize()
    raw = raw[raw["Market_and_Exchange_Names"].isin(MARKET_TO_ETF)].copy()
    raw["instrument"] = raw["Market_and_Exchange_Names"].map(MARKET_TO_ETF)
    raw["market_priority"] = raw["Market_and_Exchange_Names"].map(MARKET_PRIORITY)
    raw["market_context"] = "cftc_traders_in_financial_futures"
    raw["timeframe"] = "1w"
    raw = raw.dropna(subset=["report_date", "instrument"]).sort_values(["instrument", "report_date"]).reset_index(drop=True)
    raw = (
        raw.sort_values(["instrument", "report_date", "market_priority"])
        .drop_duplicates(["instrument", "report_date"], keep="first")
        .reset_index(drop=True)
    )
    meta = {
        "provider": "CFTC",
        "source": "Traders in Financial Futures historical compressed futures-only text files",
        "years": years,
        "raw_dir": str(TMP_RAW_DIR),
        "selected_markets": MARKET_ALIASES,
        "selected_rows": int(len(raw)),
        "date_min": raw["report_date"].min().isoformat() if not raw.empty else None,
        "date_max": raw["report_date"].max().isoformat() if not raw.empty else None,
        "raw_committed_to_repo": False,
    }
    return raw, meta


def fetch_prices() -> tuple[pd.DataFrame, dict[str, Any]]:
    tickers = sorted(MARKET_ALIASES)
    raw = yf.download(tickers, period="15y", interval="1d", auto_adjust=True, progress=False, threads=True, group_by="ticker")
    rows: list[pd.DataFrame] = []
    if not isinstance(raw.columns, pd.MultiIndex):
        raw.columns = pd.MultiIndex.from_product([["UNKNOWN"], raw.columns])
    level0 = set(str(x) for x in raw.columns.get_level_values(0))
    tickers_first = bool(level0 & set(tickers))
    for ticker in tickers:
        try:
            part = raw[ticker].copy() if tickers_first else raw.xs(ticker, axis=1, level=1).copy()
        except Exception:
            continue
        part = part.rename(columns={"Close": "close", "Adj Close": "close"})
        if "close" not in part.columns:
            continue
        part = part[["close"]].reset_index().rename(columns={"Date": "date", "Datetime": "date"})
        part["date"] = pd.to_datetime(part["date"], utc=True, errors="coerce").dt.normalize()
        part["instrument"] = ticker
        part["close"] = numeric(part["close"])
        rows.append(part.dropna(subset=["date", "close"])[["date", "instrument", "close"]])
    prices = pd.concat(rows, ignore_index=True).sort_values(["instrument", "date"]) if rows else pd.DataFrame(columns=["date", "instrument", "close"])
    meta = {
        "provider": "yfinance",
        "requested_symbols": tickers,
        "available_symbols": sorted(prices["instrument"].dropna().unique().tolist()),
        "rows": int(len(prices)),
        "date_min": prices["date"].min().isoformat() if not prices.empty else None,
        "date_max": prices["date"].max().isoformat() if not prices.empty else None,
    }
    return prices, meta


def add_position_features(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    oi = numeric(df["Open_Interest_All"]).replace(0, np.nan)
    groups = {
        "dealer": ("Dealer_Positions_Long_All", "Dealer_Positions_Short_All", "Dealer_Positions_Spread_All"),
        "asset_mgr": ("Asset_Mgr_Positions_Long_All", "Asset_Mgr_Positions_Short_All", "Asset_Mgr_Positions_Spread_All"),
        "lev_money": ("Lev_Money_Positions_Long_All", "Lev_Money_Positions_Short_All", "Lev_Money_Positions_Spread_All"),
        "other_rept": ("Other_Rept_Positions_Long_All", "Other_Rept_Positions_Short_All", "Other_Rept_Positions_Spread_All"),
    }
    out = pd.DataFrame(
        {
            "ts": df["report_date"],
            "instrument": df["instrument"],
            "market_context": df["market_context"],
            "timeframe": df["timeframe"],
            "open_interest": oi,
        }
    )
    for name, (long_col, short_col, spread_col) in groups.items():
        long = numeric(df[long_col])
        short = numeric(df[short_col])
        spread = numeric(df[spread_col])
        out[f"{name}_long_oi"] = long / oi
        out[f"{name}_short_oi"] = short / oi
        out[f"{name}_spread_oi"] = spread / oi
        out[f"{name}_net_oi"] = (long - short) / oi
        out[f"{name}_gross_oi"] = (long + short + spread) / oi
        out[f"{name}_long_short_ratio"] = long / short.replace(0, np.nan)
    out = out.sort_values(["instrument", "ts"]).reset_index(drop=True)
    for col in [c for c in out.columns if c.endswith("_oi") or c.endswith("_ratio") or c == "open_interest"]:
        g = out.groupby("instrument", group_keys=False)[col]
        out[f"{col}_chg1"] = g.diff(1)
        out[f"{col}_chg4"] = g.diff(4)
        out[f"{col}_chg13"] = g.diff(13)
        mean52 = g.rolling(52, min_periods=20).mean().reset_index(level=0, drop=True)
        std52 = g.rolling(52, min_periods=20).std().reset_index(level=0, drop=True).replace(0, np.nan)
        out[f"{col}_z52"] = (out[col] - mean52) / std52
    out["dealer_vs_asset_mgr_net_oi"] = out["dealer_net_oi"] - out["asset_mgr_net_oi"]
    out["lev_money_vs_dealer_net_oi"] = out["lev_money_net_oi"] - out["dealer_net_oi"]
    out["asset_mgr_vs_lev_money_net_oi"] = out["asset_mgr_net_oi"] - out["lev_money_net_oi"]
    return out


def attach_prices(features: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for instrument, group in features.groupby("instrument", sort=False):
        p = prices[prices["instrument"] == instrument].sort_values("date")
        g = group.sort_values("ts")
        # Pandas asof-merge requires exactly matching datetime precision.
        p = p.copy()
        g = g.copy()
        p["date"] = pd.to_datetime(p["date"].dt.strftime("%Y-%m-%d"), utc=True)
        g["ts"] = pd.to_datetime(g["ts"].dt.strftime("%Y-%m-%d"), utc=True)
        joined = pd.merge_asof(g, p, left_on="ts", right_on="date", by="instrument", direction="backward")
        parts.append(joined)
    return pd.concat(parts, ignore_index=True).sort_values(["instrument", "ts"]).reset_index(drop=True)


def add_labels(frame: pd.DataFrame) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for _, group in frame.groupby("instrument", sort=False):
        g = group.sort_values("ts").copy()
        close = numeric(g["close"])
        g["ret1w"] = np.log(close).diff(1)
        g["ret4w"] = np.log(close).diff(4)
        g["ret13w"] = np.log(close).diff(13)
        g["vol13w"] = g["ret1w"].rolling(13, min_periods=6).std()
        g["future_ret8w"] = np.log(close.shift(-8)) - np.log(close)
        g["future_absret8w"] = g["future_ret8w"].abs()
        g["future_vol8w"] = g["ret1w"].shift(-1).rolling(8, min_periods=4).std()
        n = len(g)
        split = np.full(n, "train", dtype=object)
        split[int(n * 0.60) :] = "calibration"
        split[int(n * 0.80) :] = "test"
        g["split"] = split
        train = g[g["split"].eq("train")]
        future_ret = numeric(train["future_ret8w"])
        future_abs = numeric(train["future_absret8w"])
        future_vol = numeric(train["future_vol8w"])
        q_ret_hi = future_ret.quantile(0.65)
        q_ret_lo = future_ret.quantile(0.35)
        q_abs_hi = future_abs.quantile(0.90)
        q_abs_lo = future_abs.quantile(0.40)
        q_vol_hi = future_vol.quantile(0.90)
        q_vol_lo = future_vol.quantile(0.55)
        all_ret = numeric(g["future_ret8w"])
        all_abs = numeric(g["future_absret8w"])
        all_vol = numeric(g["future_vol8w"])
        crisis = (all_abs >= q_abs_hi) | (all_vol >= q_vol_hi)
        sideways = (~crisis) & (all_abs <= q_abs_lo) & (all_vol <= q_vol_lo)
        bull = (~crisis) & (~sideways) & (all_ret >= q_ret_hi)
        bear = (~crisis) & (~sideways) & (all_ret <= q_ret_lo)
        g["root_label"] = "UnknownOrMixed"
        g.loc[sideways.fillna(False), "root_label"] = "Sideways"
        g.loc[bull.fillna(False), "root_label"] = "Bull"
        g.loc[bear.fillna(False), "root_label"] = "Bear"
        g.loc[crisis.fillna(False), "root_label"] = "Crisis"
        parts.append(g)
    out = pd.concat(parts, ignore_index=True)
    out["context"] = out["instrument"] + ":" + out["timeframe"]
    return out.sort_values(["instrument", "ts"]).reset_index(drop=True)


def candidate_features(df: pd.DataFrame) -> list[str]:
    blocked = {
        "ts",
        "date",
        "instrument",
        "market_context",
        "timeframe",
        "context",
        "split",
        "root_label",
        "close",
        "future_ret8w",
        "future_absret8w",
        "future_vol8w",
    }
    features: list[str] = []
    for col in df.columns:
        if col in blocked or col.startswith("future_"):
            continue
        values = numeric(df[col])
        if int(values.notna().sum()) < 200 or values.dropna().nunique() <= 2:
            continue
        features.append(col)
    return sorted(features)


def metric(df: pd.DataFrame, mask: pd.Series, root: str, split: str) -> dict[str, Any]:
    split_mask = df["split"].eq(split)
    selected = df[split_mask & mask.fillna(False)]
    support = int(len(selected))
    success = int(selected["root_label"].eq(root).sum()) if support else 0
    precision = success / support if support else 0.0
    total_split = int(split_mask.sum())
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lcb(success, support),
        "coverage": support / total_split if total_split else 0.0,
        "validation_instruments": sorted(selected["instrument"].dropna().astype(str).unique().tolist()),
        "validation_market_contexts": sorted(selected["market_context"].dropna().astype(str).unique().tolist()),
        "validation_timeframes": sorted(selected["timeframe"].dropna().astype(str).unique().tolist()),
        "validation_contexts": sorted(selected["context"].dropna().astype(str).unique().tolist()),
    }


def blockers(calibration: dict[str, Any], test: dict[str, Any], ece: float) -> list[str]:
    out: list[str] = []
    if calibration["support"] < SUPPORT_CAL_MIN:
        out.append("calibration_support_below_80")
    if test["support"] < SUPPORT_TEST_MIN:
        out.append("test_support_below_40")
    if calibration["precision_wilson_lcb_95"] < 0.95:
        out.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < 0.95:
        out.append("test_wilson95_below_0_95")
    if calibration["coverage"] < COVERAGE_MIN:
        out.append("calibration_coverage_below_0_03")
    if test["coverage"] < COVERAGE_MIN:
        out.append("test_coverage_below_0_03")
    if ece > ECE_MAX:
        out.append("ece_above_0_05")
    if len(test["validation_instruments"]) < 2:
        out.append("validation_instruments_below_2")
    return out


def rule_mask(df: pd.DataFrame, rule: str) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for part in rule.split(" AND "):
        if " >= " in part:
            feature, value = part.split(" >= ")
            mask &= numeric(df[feature]) >= float(value)
        elif " <= " in part:
            feature, value = part.split(" <= ")
            mask &= numeric(df[feature]) <= float(value)
        else:
            raise ValueError(part)
    return mask


def train_candidate_rules(df: pd.DataFrame, root: str, features: list[str]) -> list[tuple[tuple[float, float, int], str]]:
    train = df[df["split"].eq("train")]
    candidates: list[tuple[tuple[float, float, int], str]] = []
    for feature in features:
        train_values = numeric(train[feature]).dropna()
        if train_values.nunique() <= 2:
            continue
        for q in QUANTILES:
            threshold = float(train_values.quantile(q))
            if not math.isfinite(threshold):
                continue
            for op in [">=", "<="]:
                rule = f"{feature} {op} {threshold:.12g}"
                m = metric(train, rule_mask(train, rule), root, "train")
                if m["support"] >= SUPPORT_TRAIN_MIN and m["coverage"] >= COVERAGE_MIN:
                    candidates.append(((m["precision_wilson_lcb_95"], m["precision"], m["support"]), rule))
    candidates.sort(key=lambda item: item[0], reverse=True)
    seeds = candidates[:30]
    for i, (_, left) in enumerate(seeds[:18]):
        left_feature = left.split(" ")[0]
        for _, right in seeds[i + 1 : 18]:
            right_feature = right.split(" ")[0]
            if left_feature == right_feature:
                continue
            rule = f"{left} AND {right}"
            m = metric(train, rule_mask(train, rule), root, "train")
            if m["support"] >= SUPPORT_TRAIN_MIN and m["coverage"] >= COVERAGE_MIN:
                candidates.append(((m["precision_wilson_lcb_95"], m["precision"], m["support"]), rule))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates


def run_root(df: pd.DataFrame, root: str, features: list[str]) -> dict[str, Any]:
    candidates = train_candidate_rules(df, root, features)
    if not candidates:
        false_mask = pd.Series(False, index=df.index)
        train = metric(df, false_mask, root, "train")
        calibration = metric(df, false_mask, root, "calibration")
        test = metric(df, false_mask, root, "test")
        return {
            "root_class": root,
            "state": "blocked",
            "rule": "no_train_candidate_with_min_support",
            "train": train,
            "calibration": calibration,
            "test": test,
            "ece": 1.0,
            "accepted_95": False,
            "blockers": ["no_train_candidate_with_min_support"],
        }
    _, selected_rule = candidates[0]
    mask = rule_mask(df, selected_rule)
    train = metric(df, mask, root, "train")
    calibration = metric(df, mask, root, "calibration")
    test = metric(df, mask, root, "test")
    ece = abs(test["precision"] - calibration["precision"]) if calibration["support"] else 1.0
    block = blockers(calibration, test, ece)
    return {
        "root_class": root,
        "state": "accepted_95" if not block else "blocked",
        "rule": selected_rule,
        "threshold_selected_on": "train_split_only",
        "train": train,
        "calibration": calibration,
        "test": test,
        "ece": ece,
        "accepted_95": not block,
        "blockers": block,
    }


def write_summary(path: Path, reports: list[dict[str, Any]]) -> None:
    fields = [
        "root_class",
        "state",
        "rule",
        "train_support",
        "train_lcb",
        "calibration_support",
        "calibration_lcb",
        "test_support",
        "test_lcb",
        "test_precision",
        "test_coverage",
        "ece",
        "test_instruments",
        "blockers",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for item in reports:
            writer.writerow(
                {
                    "root_class": item["root_class"],
                    "state": item["state"],
                    "rule": item["rule"],
                    "train_support": item["train"]["support"],
                    "train_lcb": item["train"]["precision_wilson_lcb_95"],
                    "calibration_support": item["calibration"]["support"],
                    "calibration_lcb": item["calibration"]["precision_wilson_lcb_95"],
                    "test_support": item["test"]["support"],
                    "test_lcb": item["test"]["precision_wilson_lcb_95"],
                    "test_precision": item["test"]["precision"],
                    "test_coverage": item["test"]["coverage"],
                    "ece": item["ece"],
                    "test_instruments": ";".join(item["test"]["validation_instruments"]),
                    "blockers": ";".join(item["blockers"]),
                }
            )


def write_report_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# CFTC Dealer Root Gate",
        "",
        f"Run id: `{report['loop_id']}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{report['decision']['gate_result']}`",
        f"- Accepted new roots: {', '.join(report['decision']['accepted_new_roots_95']) or 'none'}",
        f"- Missing roots: {', '.join(report['decision']['missing_root_classes_95_effective'])}",
        f"- Runtime code changed: `{str(report['decision']['runtime_code_changed']).lower()}`",
        f"- Thresholds relaxed: `{str(report['decision']['thresholds_relaxed']).lower()}`",
        "",
        "## Results",
        "",
        "| Root | State | Rule | Cal support | Cal LCB | Test support | Test LCB | Test precision | Blockers |",
        "|---|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for root in ROOTS:
        item = report["root_reports"][root]
        lines.append(
            "| {root} | {state} | `{rule}` | {cal_support} | {cal_lcb:.6f} | {test_support} | {test_lcb:.6f} | {test_precision:.6f} | {blockers} |".format(
                root=root,
                state=item["state"],
                rule=item["rule"],
                cal_support=item["calibration"]["support"],
                cal_lcb=item["calibration"]["precision_wilson_lcb_95"],
                test_support=item["test"]["support"],
                test_lcb=item["test"]["precision_wilson_lcb_95"],
                test_precision=item["test"]["precision"],
                blockers=", ".join(item["blockers"]) or "none",
            )
        )
    lines.extend(
        [
            "",
            "## Policy",
            "",
            "- Candidate roots are active MainRegimeV2 parent labels `Bull`, `Bear`, and `Sideways` only.",
            "- CFTC dealer, asset-manager, leveraged-money, and other-reportable positioning fields are predictors; future return label columns are blocked.",
            "- `Manipulation` is not evaluated because this source is weekly positioning, not direct event/order-lifecycle/L2 evidence.",
            "- Raw CFTC ZIPs stay under `/private/tmp` and are not committed to the repo.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    cftc_raw, cftc_meta = fetch_cftc()
    prices, price_meta = fetch_prices()
    feature_table = add_labels(attach_prices(add_position_features(cftc_raw), prices))
    feature_table = feature_table.dropna(subset=["close", "future_ret8w"]).copy()
    features = candidate_features(feature_table)
    root_reports = {root: run_root(feature_table, root, features) for root in ROOTS}
    accepted_new = [root for root, item in root_reports.items() if item["accepted_95"]]
    retained_prior = ["Crisis"]
    missing = [root for root in ["Bull", "Bear", "Sideways", "Manipulation"] if root not in accepted_new + retained_prior]

    feature_csv = OUT_DIR / "cftc_dealer_root_feature_table.csv"
    feature_sample_csv = OUT_DIR / "cftc_dealer_root_feature_sample.csv"
    summary_csv = OUT_DIR / "cftc_dealer_root_gate_summary.csv"
    report_json = OUT_DIR / "cftc_dealer_root_gate_report.json"
    report_md = OUT_DIR / "cftc_dealer_root_gate_report.md"
    assertions = CHECK_DIR / "cftc_dealer_root_gate_assertions.out"

    compact_cols = [
        "ts",
        "instrument",
        "market_context",
        "timeframe",
        "context",
        "split",
        "root_label",
        "close",
        "ret4w",
        "ret13w",
        "future_ret8w",
        "future_absret8w",
    ] + features
    feature_table[compact_cols].to_csv(feature_csv, index=False)
    feature_table[compact_cols].groupby(["instrument", "split"], group_keys=False).head(30).to_csv(feature_sample_csv, index=False)
    write_summary(summary_csv, list(root_reports.values()))

    report: dict[str, Any] = {
        "loop_id": RUN_ID,
        "objective": "CFTC dealer/asset-manager/leveraged-money positioning root gate for active MainRegimeV2 Bull/Bear/Sideways labels.",
        "sources": {
            "cftc": cftc_meta,
            "prices": price_meta,
            "cftc_url_pattern": CFTC_URL,
        },
        "feature_policy": {
            "candidate_feature_count": len(features),
            "candidate_features": features,
            "blocked_future_predictors": True,
            "target_columns_used_only_as_labels": True,
            "runtime_code_changed": False,
        },
        "split_counts": {split: int((feature_table["split"] == split).sum()) for split in ["train", "calibration", "test"]},
        "label_counts": {str(k): int(v) for k, v in feature_table["root_label"].value_counts(dropna=False).items()},
        "context_counts": {
            "instruments": sorted(feature_table["instrument"].astype(str).unique().tolist()),
            "market_contexts": sorted(feature_table["market_context"].astype(str).unique().tolist()),
            "timeframes": sorted(feature_table["timeframe"].astype(str).unique().tolist()),
            "contexts": sorted(feature_table["context"].astype(str).unique().tolist()),
        },
        "acceptance_95": {
            "precision_wilson_lcb_95_min": 0.95,
            "calibration_support_min": SUPPORT_CAL_MIN,
            "test_support_min": SUPPORT_TEST_MIN,
            "coverage_min": COVERAGE_MIN,
            "ece_max": ECE_MAX,
            "validation_instruments_min": 2,
        },
        "root_reports": root_reports,
        "decision": {
            "gate_result": "accepted_95" if accepted_new else "blocked_cftc_dealer_root_gate_below_95",
            "accepted_new_roots_95": accepted_new,
            "retained_prior_accepted_root_classes_95": retained_prior,
            "accepted_root_classes_95_effective": sorted(set(accepted_new + retained_prior), key=lambda item: ["Bull", "Bear", "Sideways", "Crisis", "Manipulation"].index(item)),
            "missing_root_classes_95_effective": missing,
            "manipulation_evaluated": False,
            "manipulation_blocker": "Weekly CFTC positioning is not direct event/order-lifecycle/L2 manipulation evidence.",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "fresh_calibration_rerun": True,
            "trade_usable": False,
            "next_action": "Acquire direct parent-labeled bull/bear/sideways regime-cycle data; CFTC positioning alone is still a proxy feature source.",
        },
        "artifacts": {
            "report_json": repo_rel(report_json),
            "report_md": repo_rel(report_md),
            "summary_csv": repo_rel(summary_csv),
            "feature_table": repo_rel(feature_csv),
            "feature_sample": repo_rel(feature_sample_csv),
            "assertions": repo_rel(assertions),
        },
    }
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_report_md(report_md, report)
    assertion_lines = [
        f"loop_id={RUN_ID}",
        f"rows={len(feature_table)}",
        f"raw_committed_to_repo={str(cftc_meta['raw_committed_to_repo']).lower()}",
        f"runtime_code_changed={str(report['decision']['runtime_code_changed']).lower()}",
        f"thresholds_relaxed={str(report['decision']['thresholds_relaxed']).lower()}",
        f"accepted_new_roots_95={','.join(accepted_new) if accepted_new else 'none'}",
        f"gate_result={report['decision']['gate_result']}",
    ]
    for root in ROOTS:
        item = root_reports[root]
        assertion_lines.append(
            f"{root}:cal_lcb={item['calibration']['precision_wilson_lcb_95']:.6f}:test_lcb={item['test']['precision_wilson_lcb_95']:.6f}:accepted={str(item['accepted_95']).lower()}"
        )
    assertions.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
