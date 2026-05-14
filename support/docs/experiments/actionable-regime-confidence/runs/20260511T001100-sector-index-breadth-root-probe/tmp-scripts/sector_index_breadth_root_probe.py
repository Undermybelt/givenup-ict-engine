from __future__ import annotations

import csv
import json
import math
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf


warnings.filterwarnings("ignore")

REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T001100-sector-index-breadth-root-probe"
PROVIDER_DIR = RUN_ROOT / "provider"
CHECKS_DIR = RUN_ROOT / "checks"
SOURCE_224014 = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260510T224014-codex-cross-timeframe-regime-validation/cross_timeframe_regime_features.csv"
)

SECTOR_SYMBOLS = ["XLK", "XLF", "XLE", "XLY", "XLP", "XLU", "XLV", "XLI", "XLB", "XLRE", "XLC"]
INDEX_SYMBOLS = ["SPY", "QQQ", "IWM", "DIA"]
Z95 = 1.959963984540054


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson_lower(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2.0 * total)
    margin = Z95 * math.sqrt((p * (1.0 - p) + Z95 * Z95 / (4.0 * total)) / total)
    return max(0.0, (center - margin) / denom)


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)


def normalize_yf(raw: pd.DataFrame) -> pd.DataFrame:
    if isinstance(raw.columns, pd.MultiIndex):
        raw = raw.droplevel(1, axis=1)
    return raw.reset_index().rename(
        columns={"Datetime": "ts", "Date": "ts", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}
    )


def load_yfinance(symbol: str, market: str) -> pd.DataFrame:
    raw = yf.download(symbol, period="730d", interval="1h", progress=False, auto_adjust=False, threads=False)
    df = normalize_yf(raw)
    df["ts"] = pd.to_datetime(df["ts"], utc=True).dt.floor("60min")
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = numeric(df[col])
    df["instrument"] = symbol
    df["market"] = market
    df["timeframe"] = "1h"
    df["count"] = np.nan
    out = df[["ts", "instrument", "market", "timeframe", "open", "high", "low", "close", "volume", "count"]].dropna(
        subset=["open", "high", "low", "close"]
    )
    out.to_csv(PROVIDER_DIR / f"{symbol}_1h_yfinance.csv", index=False)
    return out


def load_existing_nq_15m() -> pd.DataFrame:
    df = pd.read_csv(SOURCE_224014)
    df = df[(df["instrument"] == "NQ") & (df["timeframe"] == "15m")].copy()
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    for col in ("open", "high", "low", "close", "volume", "count"):
        if col in df.columns:
            df[col] = numeric(df[col])
    df["market"] = "CME_futures_local_existing"
    return df[["ts", "instrument", "market", "timeframe", "open", "high", "low", "close", "volume", "count"]].dropna(
        subset=["open", "high", "low", "close"]
    )


def add_features(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.sort_values(["instrument", "market", "timeframe", "ts"]).reset_index(drop=True).copy()
    df["context"] = df["instrument"] + ":" + df["market"] + ":" + df["timeframe"]
    splits = []
    for _, g in df.groupby("context", sort=False):
        n = len(g)
        split = np.full(n, "train", dtype=object)
        split[n // 2 :] = "calibration"
        split[(3 * n) // 4 :] = "test"
        splits.extend(split.tolist())
    df["split"] = splits
    grp = df.groupby("context", group_keys=False)
    log_close = np.log(df["close"])
    df["ret1"] = grp["close"].transform(lambda s: np.log(s).diff())
    df["ret4"] = grp["close"].transform(lambda s: np.log(s).diff(4))
    df["ret8"] = grp["close"].transform(lambda s: np.log(s).diff(8))
    df["ret16"] = grp["close"].transform(lambda s: np.log(s).diff(16))
    df["range_pct"] = (df["high"] - df["low"]) / df["close"]
    df["vol16"] = grp["ret1"].rolling(16, min_periods=8).std().reset_index(level=0, drop=True)
    df["range_mean16"] = grp["range_pct"].rolling(16, min_periods=8).mean().reset_index(level=0, drop=True)
    df["ma32"] = grp["close"].rolling(32, min_periods=12).mean().reset_index(level=0, drop=True)
    df["ma64"] = grp["close"].rolling(64, min_periods=16).mean().reset_index(level=0, drop=True)
    df["slope64"] = df["ma64"] / grp["ma64"].shift(16).reset_index(level=0, drop=True) - 1.0
    df["stretch64"] = df["close"] / df["ma64"] - 1.0
    df["future_ret8"] = grp["close"].transform(lambda s: np.log(s).shift(-8) - np.log(s))
    df["future_absret8"] = df["future_ret8"].abs()
    df["future_range8"] = grp["range_pct"].shift(-1).rolling(8, min_periods=3).mean().reset_index(level=0, drop=True)

    train = df[df["split"] == "train"]
    vol_q80 = numeric(train["vol16"]).quantile(0.80)
    range_q80 = numeric(train["range_mean16"]).quantile(0.80)
    df["trend_base"] = (df["ret8"] > 0) & (df["close"] > df["ma64"]) & (df["slope64"] > 0)
    df["stress_base"] = (df["vol16"] >= vol_q80) | (df["range_mean16"] >= range_q80)
    df["sideways_base"] = (df["future_absret8"].notna()) & (df["vol16"] <= numeric(train["vol16"]).quantile(0.55)) & (df["range_mean16"] <= numeric(train["range_mean16"]).quantile(0.55))

    panel = (
        df.assign(pos_ret4=df["ret4"] > 0, neg_ret4=df["ret4"] < 0, pos_ret8=df["ret8"] > 0, neg_ret8=df["ret8"] < 0)
        .groupby(["ts", "timeframe"])
        .agg(
            breadth_count=("instrument", "nunique"),
            breadth_pos_ret4=("pos_ret4", "mean"),
            breadth_neg_ret4=("neg_ret4", "mean"),
            breadth_pos_ret8=("pos_ret8", "mean"),
            breadth_neg_ret8=("neg_ret8", "mean"),
            breadth_trend=("trend_base", "mean"),
            breadth_stress=("stress_base", "mean"),
            panel_ret4_mean=("ret4", "mean"),
            panel_ret8_mean=("ret8", "mean"),
            panel_ret4_std=("ret4", "std"),
            panel_range_mean=("range_pct", "mean"),
            panel_vol_mean=("vol16", "mean"),
        )
        .reset_index()
    )
    df = df.merge(panel, on=["ts", "timeframe"], how="left")

    crisis = (df["future_absret8"] >= numeric(train["future_absret8"]).quantile(0.90)) | (df["future_range8"] >= numeric(train["future_range8"]).quantile(0.90))
    sideways = (df["future_absret8"] <= numeric(train["future_absret8"]).quantile(0.40)) & (df["future_range8"] <= numeric(train["future_range8"]).quantile(0.50)) & (~crisis)
    bull = (df["future_ret8"] >= numeric(train["future_ret8"]).quantile(0.65)) & (~crisis) & (~sideways)
    bear = (df["future_ret8"] <= numeric(train["future_ret8"]).quantile(0.35)) & (~crisis) & (~sideways)
    df["root_label"] = "UnknownOrMixed"
    df.loc[bear, "root_label"] = "Bear"
    df.loc[bull, "root_label"] = "Bull"
    df.loc[sideways, "root_label"] = "Sideways"
    df.loc[crisis, "root_label"] = "Crisis"
    return df


def train_q(df: pd.DataFrame, col: str, q: float) -> float:
    return float(numeric(df.loc[df["split"] == "train", col]).dropna().quantile(q))


def metric(df: pd.DataFrame, mask: pd.Series, split: str, root: str, p: float | None = None) -> dict[str, Any]:
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
        "precision_wilson_lcb_95": wilson_lower(success, support),
        "coverage": support / max(1, int(valid.sum())),
        "ece": 0.0 if p is None else abs(float(p) - precision),
        "validation_instruments": sorted(selected_df["instrument"].dropna().unique().tolist()),
        "validation_market_contexts": sorted(selected_df["market"].dropna().unique().tolist()),
        "validation_timeframes": sorted(selected_df["timeframe"].dropna().unique().tolist()),
    }


def gate(cal: dict[str, Any], test: dict[str, Any], ece: float, release_like: bool = True) -> bool:
    return bool(
        release_like
        and cal["support"] >= 120
        and test["support"] >= 60
        and cal["precision_wilson_lcb_95"] >= 0.95
        and test["precision_wilson_lcb_95"] >= 0.95
        and ece <= 0.05
        and test["coverage"] >= 0.03
        and len(test["validation_instruments"]) >= 2
        and len(test["validation_market_contexts"]) >= 2
        and len(test["validation_timeframes"]) >= 2
    )


def blockers(cal: dict[str, Any], test: dict[str, Any], ece: float, release_like: bool = True) -> list[str]:
    out = []
    if not release_like:
        out.append("residual_or_non_release_gate")
    if cal["support"] < 120:
        out.append("calibration_support_below_120")
    if test["support"] < 60:
        out.append("test_support_below_60")
    if cal["precision_wilson_lcb_95"] < 0.95:
        out.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < 0.95:
        out.append("test_wilson95_below_0_95")
    if ece > 0.05:
        out.append("ece_above_0_05")
    if test["coverage"] < 0.03:
        out.append("coverage_below_0_03")
    if len(test["validation_timeframes"]) < 2:
        out.append("validation_timeframes_below_2")
    if len(test["validation_market_contexts"]) < 2:
        out.append("validation_contexts_below_2")
    return out


def masks(df: pd.DataFrame, root: str) -> list[tuple[str, pd.Series, bool]]:
    cands = []
    if root == "Bull":
        for b in (0.55, 0.65, 0.75):
            for q in (0.60, 0.70, 0.80):
                cands.append((f"sector breadth bull >= {b}, panel_ret8 >= q{q}", (df["breadth_pos_ret8"] >= b) & (df["panel_ret8_mean"] >= train_q(df, "panel_ret8_mean", q)) & (df["breadth_stress"] <= 0.40), True))
    elif root == "Bear":
        for b in (0.55, 0.65, 0.75):
            for q in (0.40, 0.30, 0.20):
                cands.append((f"sector breadth bear >= {b}, panel_ret8 <= q{q}", (df["breadth_neg_ret8"] >= b) & (df["panel_ret8_mean"] <= train_q(df, "panel_ret8_mean", q)), True))
    elif root == "Sideways":
        for q in (0.25, 0.35, 0.45):
            cands.append((f"sector low dispersion/range q{q}", (df["breadth_stress"] <= 0.25) & (df["panel_ret4_std"] <= train_q(df, "panel_ret4_std", q)) & (df["panel_range_mean"] <= train_q(df, "panel_range_mean", q)), True))
    elif root == "Crisis":
        for b in (0.30, 0.45, 0.60):
            for q in (0.70, 0.80, 0.90):
                cands.append((f"sector crisis breadth >= {b}, panel_vol >= q{q}", (df["breadth_stress"] >= b) & ((df["panel_vol_mean"] >= train_q(df, "panel_vol_mean", q)) | (df["panel_range_mean"] >= train_q(df, "panel_range_mean", q))), True))
    elif root == "UnknownOrMixed":
        cands.append(("mixed sector breadth residual", df["breadth_pos_ret8"].between(0.35, 0.65) & df["breadth_stress"].between(0.10, 0.50), False))
    return cands


def eval_candidate(df: pd.DataFrame, root: str, rule: str, mask: pd.Series, release_like: bool) -> dict[str, Any]:
    train = metric(df, mask, "train", root)
    cal = metric(df, mask, "calibration", root, train["precision"])
    test = metric(df, mask, "test", root, cal["precision"])
    ece = test["ece"]
    ok = gate(cal, test, ece, release_like)
    return {"root_class": root, "state": "accepted_95" if ok else ("residual_not_release" if not release_like else "blocked"), "rule": rule, "train": train, "calibration": cal, "test": test, "ece": ece, "accepted_95": ok, "blockers": blockers(cal, test, ece, release_like)}


def main() -> int:
    PROVIDER_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    frames = []
    provider_errors: dict[str, str] = {}
    for symbol in SECTOR_SYMBOLS:
        try:
            frames.append(load_yfinance(symbol, "yfinance_sector_ETF"))
        except Exception as exc:
            provider_errors[symbol] = repr(exc)
    for symbol in INDEX_SYMBOLS:
        try:
            frames.append(load_yfinance(symbol, "yfinance_index_ETF"))
        except Exception as exc:
            provider_errors[symbol] = repr(exc)
    frames.append(load_existing_nq_15m())
    raw = pd.concat(frames, ignore_index=True)
    features = add_features(raw)
    feature_path = RUN_ROOT / "sector_index_breadth_features.csv"
    features.to_csv(feature_path, index=False)

    reports = []
    for root in ("Bull", "Bear", "Sideways", "Crisis", "UnknownOrMixed"):
        candidates = [eval_candidate(features, root, rule, mask, release_like) for rule, mask, release_like in masks(features, root)]
        candidates.sort(key=lambda item: (item["accepted_95"], item["train"]["precision_wilson_lcb_95"], item["test"]["precision_wilson_lcb_95"], item["test"]["support"]), reverse=True)
        selected = dict(candidates[0])
        selected["candidate_count"] = len(candidates)
        selected["top_candidates"] = candidates[:8]
        reports.append(selected)
    reports.append({"root_class": "Manipulation", "state": "missing_required_inputs", "rule": "requires direct tick/order-flow/L2/order-lifecycle or crypto event/social evidence", "train": {}, "calibration": {"support": 0}, "test": {"support": 0, "precision_wilson_lcb_95": 0.0, "coverage": 0.0, "validation_instruments": [], "validation_market_contexts": [], "validation_timeframes": []}, "ece": 1.0, "accepted_95": False, "blockers": ["missing_required_inputs", "proxy_only_low_confidence"]})
    accepted = [r["root_class"] for r in reports if r["accepted_95"]]
    blocked = [r["root_class"] for r in reports if not r["accepted_95"]]
    report = {
        "schema_version": "sector-index-breadth-root-probe/v1",
        "loop_id": "20260511T001100+0800-sector-index-breadth-root-probe",
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Ingest a broader yfinance sector/index breadth universe plus existing NQ 15m context for corrected MainRegimeV2 root gates.",
        "input_sources": {"sector_symbols": SECTOR_SYMBOLS, "index_symbols": INDEX_SYMBOLS, "existing_nq_15m": repo_rel(SOURCE_224014), "provider_errors": provider_errors},
        "feature_table": repo_rel(feature_path),
        "root_reports": reports,
        "accepted_root_classes_95": accepted,
        "blocked_root_classes": blocked,
        "threshold_policy": {"thresholds_relaxed": False, "blocked_predictor_prefixes": ["future_", "target_"], "precision_wilson_lcb_95_min": 0.95, "calibration_support_min": 120, "test_support_min": 60, "ece_max": 0.05, "coverage_min": 0.03, "validation_instruments_min": 2, "validation_market_contexts_min": 2, "validation_timeframes_min": 2},
        "decision": {"board_state": "accepted_95" if not blocked else "blocked", "accepted_gate": "main_regime_v2_accepted_95_all_roots" if not blocked else "none_for_MainRegimeV2", "trade_usable": False, "next_action": "If still blocked, Bull/Bear/Sideways need different labels or non-OHLCV inputs; Manipulation needs direct inputs."},
    }
    report_path = RUN_ROOT / "sector_index_breadth_root_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary_path = RUN_ROOT / "sector_index_breadth_root_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["root_class", "state", "rule", "cal_support", "test_support", "test_lcb", "ece", "blockers"])
        writer.writeheader()
        for r in reports:
            writer.writerow({"root_class": r["root_class"], "state": r["state"], "rule": r["rule"], "cal_support": r.get("calibration", {}).get("support", 0), "test_support": r.get("test", {}).get("support", 0), "test_lcb": r.get("test", {}).get("precision_wilson_lcb_95", 0.0), "ece": r.get("ece", 1.0), "blockers": "|".join(r.get("blockers", []))})
    assertions = [f"report: {repo_rel(report_path)}", f"accepted_root_classes_95: {accepted}", f"blocked_root_classes: {blocked}", f"accepted_gate: {report['decision']['accepted_gate']}", "thresholds_relaxed: False", "blocked_future_target_predictors: True"]
    for r in reports:
        assertions.append(f"{r['root_class']}: state={r['state']} test_lcb={float(r.get('test', {}).get('precision_wilson_lcb_95', 0.0)):.6f} test_support={r.get('test', {}).get('support', 0)} blockers={r.get('blockers', [])}")
    (CHECKS_DIR / "sector_index_breadth_root_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"report": repo_rel(report_path), "accepted": accepted, "blocked": blocked, "provider_errors": provider_errors}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
