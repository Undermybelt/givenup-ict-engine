from __future__ import annotations

import csv
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T001642-cross-asset-root-evidence-yfinance"
ROOT_DIR = RUN_ROOT / "root-v2"
CHECKS_DIR = RUN_ROOT / "checks"

SYMBOLS = [
    "QQQ",
    "SPY",
    "IWM",
    "TLT",
    "HYG",
    "LQD",
    "UUP",
    "RSP",
    "XLY",
    "XLP",
    "^VIX",
    "^VIX3M",
    "BTC-USD",
    "ETH-USD",
]
TARGETS = ["QQQ", "BTC-USD"]
DOWNLOADS = {
    "1h": {"period": "730d", "horizon_bars": 8, "market_hours_note": "hourly yfinance; crypto rows may carry stale macro proxies over closed equity sessions"},
    "1d": {"period": "10y", "horizon_bars": 5, "market_hours_note": "daily yfinance"},
}
ROOT_CLASSES = ["Bull", "Bear", "Sideways", "Crisis", "Manipulation", "UnknownOrMixed"]
BLOCKED_PREDICTOR_PREFIXES = ("future_", "target_")
ACCEPTANCE_95 = {
    "precision_wilson_lcb_95_min": 0.95,
    "calibration_support_min": 120,
    "test_support_min": 60,
    "ece_max": 0.05,
    "coverage_min": 0.03,
    "validation_instruments_min": 2,
    "validation_market_contexts_min": 2,
    "validation_timeframes_min": 2,
}
HIGH_SIGNAL_FEATURES = {
    "ret_1",
    "ret_4",
    "ret_8",
    "ret_16",
    "range_pct",
    "vol16",
    "vol64",
    "stretch32",
    "ma64_slope16",
    "drawdown64",
    "rally64",
    "vol_rank252",
    "range_rank252",
    "volume_rank252",
    "abs_ret16_rank252",
    "QQQ_ret4",
    "QQQ_ret16",
    "SPY_ret16",
    "IWM_ret16",
    "TLT_ret16",
    "HYG_ret16",
    "LQD_ret16",
    "UUP_ret16",
    "VIX_ret4",
    "VIX_ret16",
    "BTC_USD_ret16",
    "ETH_USD_ret16",
    "qqq_spy_rel16",
    "iwm_spy_rel16",
    "rsp_spy_rel16",
    "xly_xlp_rel16",
    "hyg_lqd_rel16",
    "eth_btc_rel16",
    "vix_level_rank252",
    "vix3m_vix_log_ratio",
    "vix_term_rank252",
    "cross_asset_risk_on_score16",
    "credit_breadth_score16",
    "crypto_risk_score16",
    "macro_stress_score16",
    "bull_root_score",
    "bear_root_score",
    "sideways_root_score",
    "crisis_root_score",
}


@dataclass(frozen=True)
class Rule:
    description: str
    feature_names: tuple[str, ...]
    clauses: tuple[tuple[str, str, float], ...]

    def select(self, rows: pd.DataFrame) -> pd.Series:
        mask = pd.Series(True, index=rows.index)
        for feature, op, cut in self.clauses:
            values = pd.to_numeric(rows[feature], errors="coerce")
            if op == ">=":
                mask &= values >= cut
            elif op == "<=":
                mask &= values <= cut
            else:
                raise ValueError(f"unsupported operator {op}")
        return mask.fillna(False)


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson(success: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    center = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return (center - margin) / denom


def rolling_rank(series: pd.Series, window: int) -> pd.Series:
    min_periods = max(20, min(window, 60))

    def rank_last(values: np.ndarray) -> float:
        clean = values[np.isfinite(values)]
        if len(clean) == 0:
            return np.nan
        return float((clean <= clean[-1]).sum() / len(clean))

    return series.rolling(window=window, min_periods=min_periods).apply(rank_last, raw=True)


def log_return(series: pd.Series, periods: int) -> pd.Series:
    return np.log(series / series.shift(periods)).replace([np.inf, -np.inf], np.nan)


def finite_quantile(series: pd.Series, q: float) -> float:
    values = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if values.empty:
        return math.nan
    return float(values.quantile(q))


def download_prices(interval: str, period: str) -> dict[str, pd.DataFrame]:
    data = yf.download(
        SYMBOLS,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=True,
        group_by="ticker",
    )
    raw_path = RUN_ROOT / f"downloaded_prices_{interval}.csv"
    data.to_csv(raw_path)
    if not isinstance(data.columns, pd.MultiIndex):
        raise RuntimeError(f"expected MultiIndex yfinance data for {interval}")

    panels: dict[str, pd.DataFrame] = {}
    for field in ["Open", "High", "Low", "Close", "Volume"]:
        frame = pd.DataFrame(index=data.index)
        for symbol in SYMBOLS:
            if (symbol, field) in data.columns:
                frame[symbol] = pd.to_numeric(data[(symbol, field)], errors="coerce")
        panels[field.lower()] = frame.sort_index()
    return panels


def add_proxy_features(frame: pd.DataFrame, close_ffill: pd.DataFrame, interval: str) -> pd.DataFrame:
    close = close_ffill
    proxy_returns = {}
    for symbol in SYMBOLS:
        if symbol in close:
            proxy_returns[f"{clean_symbol(symbol)}_ret4"] = log_return(close[symbol], 4)
            proxy_returns[f"{clean_symbol(symbol)}_ret16"] = log_return(close[symbol], 16)

    out = frame.copy()
    for name, values in proxy_returns.items():
        out[name] = values.reindex(out.index)

    def col(name: str) -> pd.Series:
        return pd.to_numeric(out.get(name, pd.Series(np.nan, index=out.index)), errors="coerce")

    out["qqq_spy_rel16"] = col("QQQ_ret16") - col("SPY_ret16")
    out["iwm_spy_rel16"] = col("IWM_ret16") - col("SPY_ret16")
    out["rsp_spy_rel16"] = col("RSP_ret16") - col("SPY_ret16")
    out["xly_xlp_rel16"] = col("XLY_ret16") - col("XLP_ret16")
    out["hyg_lqd_rel16"] = col("HYG_ret16") - col("LQD_ret16")
    out["eth_btc_rel16"] = col("ETH_USD_ret16") - col("BTC_USD_ret16")
    vix = close["^VIX"].reindex(out.index) if "^VIX" in close else pd.Series(np.nan, index=out.index)
    vix3m = close["^VIX3M"].reindex(out.index) if "^VIX3M" in close else pd.Series(np.nan, index=out.index)
    out["vix_level_rank252"] = rolling_rank(vix, 252).reindex(out.index)
    out["vix3m_vix_log_ratio"] = np.log(vix3m / vix).replace([np.inf, -np.inf], np.nan).reindex(out.index)
    out["vix_term_rank252"] = rolling_rank(out["vix3m_vix_log_ratio"], 252)

    risk_cols = [
        "SPY_ret16",
        "QQQ_ret16",
        "iwm_spy_rel16",
        "rsp_spy_rel16",
        "xly_xlp_rel16",
        "hyg_lqd_rel16",
    ]
    risk_on = pd.concat([col(name) for name in risk_cols], axis=1).mean(axis=1)
    risk_off = pd.concat([col("TLT_ret16"), col("UUP_ret16"), col("VIX_ret4")], axis=1).mean(axis=1)
    crypto_on = pd.concat([col("BTC_USD_ret16"), col("ETH_USD_ret16"), col("eth_btc_rel16")], axis=1).mean(axis=1)
    out["cross_asset_risk_on_score16"] = risk_on - risk_off
    out["credit_breadth_score16"] = pd.concat(
        [col("hyg_lqd_rel16"), col("rsp_spy_rel16"), col("xly_xlp_rel16")], axis=1
    ).mean(axis=1)
    out["crypto_risk_score16"] = crypto_on - 0.5 * col("UUP_ret16") - 0.5 * col("VIX_ret4")
    out["macro_stress_score16"] = (
        col("VIX_ret4")
        + col("UUP_ret16")
        - col("hyg_lqd_rel16")
        - col("rsp_spy_rel16")
        + out["vix_level_rank252"].fillna(0.5) * 0.01
    )
    out["input_interval"] = interval
    return out


def clean_symbol(symbol: str) -> str:
    return symbol.replace("^", "").replace("-", "_")


def build_context_rows(interval: str, panels: dict[str, pd.DataFrame], horizon_bars: int) -> pd.DataFrame:
    close = panels["close"]
    ffill_limit = 72 if interval == "1h" else 7
    close_ffill = close.ffill(limit=ffill_limit)
    rows: list[pd.DataFrame] = []
    for target in TARGETS:
        target_close = close[target].dropna()
        if target_close.empty:
            continue
        frame = pd.DataFrame(index=target_close.index)
        frame["ts"] = frame.index.astype(str)
        frame["instrument"] = target
        frame["market"] = "yfinance_US_ETF" if target == "QQQ" else "yfinance_crypto"
        frame["timeframe"] = interval
        frame["timeframe_minutes"] = 60 if interval == "1h" else 1440
        for field, panel in panels.items():
            if target in panel:
                frame[field] = panel[target].reindex(frame.index)
        frame["ret_1"] = log_return(frame["close"], 1)
        frame["ret_4"] = log_return(frame["close"], 4)
        frame["ret_8"] = log_return(frame["close"], 8)
        frame["ret_16"] = log_return(frame["close"], 16)
        frame["range_pct"] = ((frame["high"] - frame["low"]) / frame["close"]).replace([np.inf, -np.inf], np.nan)
        frame["vol16"] = frame["ret_1"].rolling(16, min_periods=8).std()
        frame["vol64"] = frame["ret_1"].rolling(64, min_periods=20).std()
        ma32 = frame["close"].rolling(32, min_periods=16).mean()
        ma64 = frame["close"].rolling(64, min_periods=32).mean()
        frame["stretch32"] = (frame["close"] / ma32 - 1.0).replace([np.inf, -np.inf], np.nan)
        frame["ma64_slope16"] = (ma64 / ma64.shift(16) - 1.0).replace([np.inf, -np.inf], np.nan)
        frame["drawdown64"] = (frame["close"] / frame["close"].rolling(64, min_periods=20).max() - 1.0).replace(
            [np.inf, -np.inf], np.nan
        )
        frame["rally64"] = (frame["close"] / frame["close"].rolling(64, min_periods=20).min() - 1.0).replace(
            [np.inf, -np.inf], np.nan
        )
        frame["vol_rank252"] = rolling_rank(frame["vol16"], 252)
        frame["range_rank252"] = rolling_rank(frame["range_pct"], 252)
        frame["volume_rank252"] = rolling_rank(frame["volume"], 252)
        frame["abs_ret16_rank252"] = rolling_rank(frame["ret_16"].abs(), 252)
        frame = add_proxy_features(frame, close_ffill, interval)
        if target == "BTC-USD":
            frame["bull_root_score"] = (
                frame["ret_16"] + frame["crypto_risk_score16"] + 0.5 * frame["cross_asset_risk_on_score16"]
            )
            frame["bear_root_score"] = (
                -frame["ret_16"] - frame["crypto_risk_score16"] - 0.25 * frame["credit_breadth_score16"]
            )
        else:
            frame["bull_root_score"] = (
                frame["ret_16"] + frame["cross_asset_risk_on_score16"] + 0.25 * frame["crypto_risk_score16"]
            )
            frame["bear_root_score"] = (
                -frame["ret_16"] - frame["cross_asset_risk_on_score16"] + 0.5 * frame["macro_stress_score16"]
            )
        frame["sideways_root_score"] = (
            -frame["ret_16"].abs()
            -frame["ret_4"].abs()
            -frame["vol_rank252"].fillna(0.5) * 0.01
            -frame["range_rank252"].fillna(0.5) * 0.01
        )
        frame["crisis_root_score"] = (
            frame["vol_rank252"].fillna(0.5) * 0.02
            + frame["range_rank252"].fillna(0.5) * 0.02
            + frame["ret_4"].abs()
            + frame["macro_stress_score16"].fillna(0.0)
        )
        frame["future_ret_h"] = log_return(frame["close"], horizon_bars).shift(-horizon_bars)
        frame["future_absret_h"] = frame["future_ret_h"].abs()
        frame["future_range_h"] = (
            (frame["high"].rolling(horizon_bars, min_periods=horizon_bars).max().shift(-horizon_bars + 1)
            - frame["low"].rolling(horizon_bars, min_periods=horizon_bars).min().shift(-horizon_bars + 1))
            / frame["close"]
        ).replace([np.inf, -np.inf], np.nan)
        rows.append(frame)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, axis=0, ignore_index=False).sort_index()


def assign_splits(rows: pd.DataFrame) -> pd.DataFrame:
    out = rows.copy()
    out["context"] = out["instrument"].astype(str) + ":" + out["market"].astype(str) + ":" + out["timeframe"].astype(str)
    out["split"] = ""
    for _, idx in out.groupby("context", sort=False).groups.items():
        ordered = out.loc[idx].sort_index()
        n = len(ordered)
        train_end = int(n * 0.50)
        calibration_end = int(n * 0.75)
        out.loc[ordered.index[:train_end], "split"] = "train"
        out.loc[ordered.index[train_end:calibration_end], "split"] = "calibration"
        out.loc[ordered.index[calibration_end:], "split"] = "test"
    return out


def assign_root_labels(rows: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    out = rows.copy()
    thresholds: dict[str, Any] = {}
    out["root_label"] = "UnknownOrMixed"
    for context, group in out.groupby("context", sort=False):
        train = group[group["split"] == "train"]
        ctx_thresholds = {
            "bull_future_ret_q65": finite_quantile(train["future_ret_h"], 0.65),
            "bear_future_ret_q35": finite_quantile(train["future_ret_h"], 0.35),
            "crisis_future_absret_q90": finite_quantile(train["future_absret_h"], 0.90),
            "sideways_future_absret_q40": finite_quantile(train["future_absret_h"], 0.40),
        }
        thresholds[context] = ctx_thresholds
        idx = group.index
        future_ret = pd.to_numeric(out.loc[idx, "future_ret_h"], errors="coerce")
        future_absret = pd.to_numeric(out.loc[idx, "future_absret_h"], errors="coerce")
        crisis = future_absret >= ctx_thresholds["crisis_future_absret_q90"]
        sideways = (future_absret <= ctx_thresholds["sideways_future_absret_q40"]) & ~crisis
        bull = (future_ret >= ctx_thresholds["bull_future_ret_q65"]) & ~crisis & ~sideways
        bear = (future_ret <= ctx_thresholds["bear_future_ret_q35"]) & ~crisis & ~sideways
        labels = pd.Series("UnknownOrMixed", index=idx)
        labels.loc[crisis.fillna(False)] = "Crisis"
        labels.loc[sideways.fillna(False)] = "Sideways"
        labels.loc[bull.fillna(False)] = "Bull"
        labels.loc[bear.fillna(False)] = "Bear"
        out.loc[idx, "root_label"] = labels
    return out, thresholds


def candidate_features(rows: pd.DataFrame) -> list[str]:
    blocked = {
        "open",
        "high",
        "low",
        "close",
        "volume",
        "timeframe_minutes",
    }
    id_cols = {"ts", "instrument", "market", "timeframe", "context", "split", "root_label", "input_interval"}
    features = []
    for column in rows.columns:
        if column in blocked or column in id_cols:
            continue
        if column.startswith(BLOCKED_PREDICTOR_PREFIXES):
            continue
        if not pd.api.types.is_numeric_dtype(rows[column]):
            continue
        if column in HIGH_SIGNAL_FEATURES:
            features.append(column)
    return sorted(features)


def build_rules(rows: pd.DataFrame, features: list[str]) -> list[Rule]:
    train = rows[rows["split"] == "train"]
    quantiles = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
    rules: list[Rule] = []
    seen: set[str] = set()
    feature_cuts: dict[str, dict[float, float]] = {}
    for feature in features:
        cuts = {}
        for q in quantiles:
            cut = finite_quantile(train[feature], q)
            if math.isfinite(cut):
                cuts[q] = cut
        feature_cuts[feature] = cuts
        for cut in sorted(set(cuts.values())):
            for op in [">=", "<="]:
                desc = f"{feature} {op} {cut:.12g}"
                if desc not in seen:
                    seen.add(desc)
                    rules.append(Rule(desc, (feature,), ((feature, op, cut),)))

    combo_features = [
        feature
        for feature in [
            "bull_root_score",
            "bear_root_score",
            "sideways_root_score",
            "crisis_root_score",
            "cross_asset_risk_on_score16",
            "credit_breadth_score16",
            "crypto_risk_score16",
            "macro_stress_score16",
            "vix_level_rank252",
            "hyg_lqd_rel16",
            "eth_btc_rel16",
            "vol_rank252",
            "range_rank252",
            "ret_16",
        ]
        if feature in features
    ]
    for left, right in itertools.combinations(combo_features, 2):
        left_cuts = feature_cuts.get(left, {})
        right_cuts = feature_cuts.get(right, {})
        for left_q, left_op in [(0.80, ">="), (0.20, "<=")]:
            for right_q, right_op in [(0.80, ">="), (0.20, "<=")]:
                if left_q not in left_cuts or right_q not in right_cuts:
                    continue
                clauses = ((left, left_op, left_cuts[left_q]), (right, right_op, right_cuts[right_q]))
                desc = " AND ".join(f"{name} {op} {cut:.12g}" for name, op, cut in clauses)
                if desc not in seen:
                    seen.add(desc)
                    rules.append(Rule(desc, (left, right), clauses))
    return rules


def metric(label: str, selected: pd.DataFrame, split_total: int) -> dict[str, Any]:
    support = int(len(selected))
    success = int((selected["root_label"] == label).sum()) if support else 0
    precision = success / support if support else 0.0
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson(success, support),
        "coverage": support / max(1, split_total),
        "validation_instruments": sorted(selected["instrument"].dropna().astype(str).unique().tolist()) if support else [],
        "validation_market_contexts": sorted(selected["market"].dropna().astype(str).unique().tolist()) if support else [],
        "validation_timeframes": sorted(selected["timeframe"].dropna().astype(str).unique().tolist()) if support else [],
        "validation_contexts": sorted(selected["context"].dropna().astype(str).unique().tolist()) if support else [],
    }


def passes_gate(calibration: dict[str, Any], test: dict[str, Any], ece: float) -> bool:
    return (
        calibration["support"] >= ACCEPTANCE_95["calibration_support_min"]
        and test["support"] >= ACCEPTANCE_95["test_support_min"]
        and calibration["precision_wilson_lcb_95"] >= ACCEPTANCE_95["precision_wilson_lcb_95_min"]
        and test["precision_wilson_lcb_95"] >= ACCEPTANCE_95["precision_wilson_lcb_95_min"]
        and ece <= ACCEPTANCE_95["ece_max"]
        and test["coverage"] >= ACCEPTANCE_95["coverage_min"]
        and len(test["validation_instruments"]) >= ACCEPTANCE_95["validation_instruments_min"]
        and len(test["validation_market_contexts"]) >= ACCEPTANCE_95["validation_market_contexts_min"]
        and len(test["validation_timeframes"]) >= ACCEPTANCE_95["validation_timeframes_min"]
    )


def blockers(calibration: dict[str, Any], test: dict[str, Any], ece: float) -> list[str]:
    out: list[str] = []
    if calibration["support"] < ACCEPTANCE_95["calibration_support_min"]:
        out.append("calibration_support_below_120")
    if test["support"] < ACCEPTANCE_95["test_support_min"]:
        out.append("test_support_below_60")
    if calibration["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        out.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        out.append("test_wilson95_below_0_95")
    if ece > ACCEPTANCE_95["ece_max"]:
        out.append("ece_above_0_05")
    if test["coverage"] < ACCEPTANCE_95["coverage_min"]:
        out.append("coverage_below_0_03")
    if len(test["validation_instruments"]) < ACCEPTANCE_95["validation_instruments_min"]:
        out.append("validation_instruments_below_2")
    if len(test["validation_market_contexts"]) < ACCEPTANCE_95["validation_market_contexts_min"]:
        out.append("validation_market_contexts_below_2")
    if len(test["validation_timeframes"]) < ACCEPTANCE_95["validation_timeframes_min"]:
        out.append("validation_timeframes_below_2")
    return out


def evaluate_rule(label: str, rule: Rule, rows: pd.DataFrame) -> dict[str, Any]:
    selected_mask = rule.select(rows)
    train = rows[rows["split"] == "train"]
    calibration = rows[rows["split"] == "calibration"]
    test = rows[rows["split"] == "test"]
    train_metric = metric(label, rows[selected_mask & (rows["split"] == "train")], len(train))
    calibration_metric = metric(label, rows[selected_mask & (rows["split"] == "calibration")], len(calibration))
    test_metric = metric(label, rows[selected_mask & (rows["split"] == "test")], len(test))
    ece = abs(test_metric["precision"] - calibration_metric["precision"]) if calibration_metric["support"] else 1.0
    accepted = passes_gate(calibration_metric, test_metric, ece)
    return {
        "rule": rule.description,
        "features": list(rule.feature_names),
        "train": train_metric,
        "calibration": calibration_metric,
        "test": test_metric,
        "ece": ece,
        "accepted_95": accepted,
        "blockers": blockers(calibration_metric, test_metric, ece),
    }


def train_select_label(label: str, rules: list[Rule], rows: pd.DataFrame) -> dict[str, Any]:
    evaluated = [evaluate_rule(label, rule, rows) for rule in rules]
    train_viable = [
        item
        for item in evaluated
        if item["train"]["support"] >= ACCEPTANCE_95["calibration_support_min"]
        and item["train"]["coverage"] >= ACCEPTANCE_95["coverage_min"]
        and len(item["train"]["validation_instruments"]) >= ACCEPTANCE_95["validation_instruments_min"]
        and len(item["train"]["validation_market_contexts"]) >= ACCEPTANCE_95["validation_market_contexts_min"]
        and len(item["train"]["validation_timeframes"]) >= ACCEPTANCE_95["validation_timeframes_min"]
    ]
    pool = train_viable if train_viable else evaluated
    pool.sort(
        key=lambda item: (
            item["train"]["precision_wilson_lcb_95"],
            item["train"]["support"],
            -len(item["rule"]),
        ),
        reverse=True,
    )
    selected = pool[0] if pool else None
    best_test = max(evaluated, key=lambda item: item["test"]["precision_wilson_lcb_95"]) if evaluated else None
    return {
        "root_class": label,
        "state": "accepted_95" if selected and selected["accepted_95"] else "blocked",
        "selected_candidate": selected,
        "candidate_count": len(evaluated),
        "train_viable_candidate_count": len(train_viable),
        "selection_policy": "train_only_rank_by_train_wilson_lcb_then_support; calibration/test are held-out checks",
        "best_test_observed_not_accepted": {
            "rule": best_test["rule"] if best_test else "",
            "test_wilson95": best_test["test"]["precision_wilson_lcb_95"] if best_test else 0.0,
            "calibration_support": best_test["calibration"]["support"] if best_test else 0,
            "test_support": best_test["test"]["support"] if best_test else 0,
            "test_timeframes": best_test["test"]["validation_timeframes"] if best_test else [],
            "blockers": best_test["blockers"] if best_test else [],
            "note": "Exploratory only; not an acceptance basis because it is test-selected.",
        },
    }


def write_summary_csv(path: Path, reports: list[dict[str, Any]]) -> None:
    fields = [
        "root_class",
        "state",
        "selected_rule",
        "calibration_support",
        "calibration_wilson95",
        "test_support",
        "test_wilson95",
        "test_coverage",
        "ece",
        "test_instruments",
        "test_market_contexts",
        "test_timeframes",
        "blockers",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for report in reports:
            selected = report.get("selected_candidate") or {}
            calibration = selected.get("calibration", {})
            test = selected.get("test", {})
            writer.writerow(
                {
                    "root_class": report["root_class"],
                    "state": report["state"],
                    "selected_rule": selected.get("rule", ""),
                    "calibration_support": calibration.get("support", 0),
                    "calibration_wilson95": calibration.get("precision_wilson_lcb_95", 0.0),
                    "test_support": test.get("support", 0),
                    "test_wilson95": test.get("precision_wilson_lcb_95", 0.0),
                    "test_coverage": test.get("coverage", 0.0),
                    "ece": selected.get("ece", 1.0),
                    "test_instruments": ";".join(test.get("validation_instruments", [])),
                    "test_market_contexts": ";".join(test.get("validation_market_contexts", [])),
                    "test_timeframes": ";".join(test.get("validation_timeframes", [])),
                    "blockers": ";".join(selected.get("blockers", [])),
                }
            )


def main() -> int:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    ROOT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    context_frames: list[pd.DataFrame] = []
    download_status: dict[str, Any] = {}
    for interval, config in DOWNLOADS.items():
        panels = download_prices(interval, str(config["period"]))
        present = sorted(set().union(*[set(panel.columns) for panel in panels.values()]))
        download_status[interval] = {
            "period": config["period"],
            "present_symbols": present,
            "start": str(panels["close"].index.min()),
            "end": str(panels["close"].index.max()),
            "rows": int(len(panels["close"])),
            "market_hours_note": config["market_hours_note"],
        }
        context_frames.append(build_context_rows(interval, panels, int(config["horizon_bars"])))

    rows = pd.concat(context_frames, axis=0, ignore_index=True)
    rows = rows.replace([np.inf, -np.inf], np.nan)
    rows = rows.dropna(subset=["close", "future_ret_h", "future_absret_h"])
    rows = assign_splits(rows)
    rows, thresholds = assign_root_labels(rows)
    feature_names = candidate_features(rows)
    rules = build_rules(rows, feature_names)
    reports = [train_select_label(label, rules, rows) for label in ["Bull", "Bear", "Sideways", "Crisis"]]
    manipulation_report = {
        "root_class": "Manipulation",
        "state": "missing_required_inputs",
        "selected_candidate": {
            "rule": "",
            "features": [],
            "train": {"support": 0, "precision_wilson_lcb_95": 0.0},
            "calibration": {"support": 0, "precision_wilson_lcb_95": 0.0},
            "test": {
                "support": 0,
                "precision_wilson_lcb_95": 0.0,
                "coverage": 0.0,
                "validation_instruments": [],
                "validation_market_contexts": [],
                "validation_timeframes": [],
            },
            "ece": 1.0,
            "accepted_95": False,
            "blockers": ["missing_required_inputs", "proxy_only_low_confidence"],
        },
        "selection_policy": "fail_closed_required_inputs_missing",
        "direct_input_inventory": {
            "tick_data": False,
            "order_flow": False,
            "l2_order_book": False,
            "order_lifecycle": False,
            "crypto_event_social": False,
            "note": "This yfinance run is OHLCV plus cross-asset proxy evidence only; it is not a manipulation evidence source.",
        },
    }
    reports.append(manipulation_report)
    accepted = [item["root_class"] for item in reports if item["state"] == "accepted_95"]
    missing = [item["root_class"] for item in reports if item["state"] != "accepted_95"]

    feature_table = ROOT_DIR / "cross_asset_root_feature_table.csv"
    rows.to_csv(feature_table, index=False)
    report = {
        "schema_version": "main-regime-v2-cross-asset-yfinance-root-evidence/v1",
        "loop_id": "20260511T001642+0800-cross-asset-root-evidence-yfinance",
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Ingest higher-signal cross-asset root inputs for Bull/Bear/Sideways/Crisis and rerun the unchanged chronological MainRegimeV2 95% gate.",
        "active_market_set": ["QQQ yfinance_US_ETF", "BTC-USD yfinance_crypto"],
        "active_timeframes": ["1h", "1d"],
        "download_status": download_status,
        "target_schema": {
            "root_axis": ["Bull", "Bear", "Sideways", "Crisis"],
            "manipulation_treatment": "fifth_main_class_or_overlay_fail_closed",
            "residual_bucket": "UnknownOrMixed",
            "chronological_split": "per instrument:market:timeframe context, 50% train / 25% calibration / 25% test",
            "target_definitions": {
                "Crisis": "future_absret_h >= per-context train q90, evaluated first",
                "Sideways": "future_absret_h <= per-context train q40 AND NOT Crisis",
                "Bull": "future_ret_h >= per-context train q65 AND NOT Crisis AND NOT Sideways",
                "Bear": "future_ret_h <= per-context train q35 AND NOT Crisis AND NOT Sideways",
                "Manipulation": "not materialized from yfinance; requires direct tick/order-flow/L2/order-lifecycle or crypto event/social evidence",
                "UnknownOrMixed": "residual bucket after Crisis/Sideways/Bull/Bear",
            },
            "per_context_train_thresholds": thresholds,
            "acceptance_95": ACCEPTANCE_95,
        },
        "feature_families": {
            "target_price_state": ["ret_1", "ret_4", "ret_8", "ret_16", "vol_rank252", "range_rank252", "ma64_slope16", "drawdown64", "rally64"],
            "cross_asset": ["cross_asset_risk_on_score16", "credit_breadth_score16", "crypto_risk_score16", "macro_stress_score16"],
            "volatility_term": ["vix_level_rank252", "vix3m_vix_log_ratio", "vix_term_rank252"],
            "breadth_credit_sector": ["rsp_spy_rel16", "hyg_lqd_rel16", "xly_xlp_rel16"],
            "crypto_relative": ["eth_btc_rel16"],
        },
        "blocked_predictor_prefixes": list(BLOCKED_PREDICTOR_PREFIXES),
        "predictor_features_used": feature_names,
        "candidate_rule_count": len(rules),
        "row_counts_by_split_and_root": {
            split: rows[rows["split"] == split]["root_label"].value_counts().reindex(ROOT_CLASSES, fill_value=0).to_dict()
            for split in ["train", "calibration", "test"]
        },
        "root_reports": reports,
        "decision": {
            "board_state": "accepted_95" if not missing else "blocked",
            "accepted_root_classes_95": accepted,
            "missing_root_classes_95": missing,
            "accepted_gate": "main_regime_v2_accepted_95_all_root_classes" if not missing else "none_for_MainRegimeV2",
            "thresholds_relaxed": False,
            "blocked_future_target_predictors": True,
            "trade_usable": False,
            "blocker": "missing_root_classes_95=" + ",".join(missing),
            "next_action": "Do not repeat proxy-only OHLCV/cross-asset threshold search; add direct microstructure/order-flow/order-lifecycle or a stronger supervised root-state model with the same chronological gate.",
        },
    }
    report_path = ROOT_DIR / "cross_asset_root_evidence_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_summary_csv(ROOT_DIR / "cross_asset_root_evidence_summary.csv", reports)
    (RUN_ROOT / "README.md").write_text(
        "# Cross-Asset MainRegimeV2 Root Evidence - yfinance\n\n"
        "This run downloads yfinance QQQ and BTC-USD target rows on 1h/1d and adds cross-asset "
        "risk, credit, breadth, sector, volatility-term, dollar, and crypto-relative features. "
        "The unchanged 95% gate is applied with chronological train/calibration/test splits. "
        "Manipulation remains fail-closed because yfinance does not provide direct tick/order-flow/L2/order-lifecycle evidence.\n",
        encoding="utf-8",
    )
    assertions = [
        f"report: {repo_rel(report_path)}",
        f"feature_table: {repo_rel(feature_table)}",
        f"accepted_root_classes_95: {accepted}",
        f"missing_root_classes_95: {missing}",
        f"accepted_gate: {report['decision']['accepted_gate']}",
        "thresholds_relaxed: False",
        "blocked_future_target_predictors: True",
        "trade_usable: False",
    ]
    for item in reports:
        selected = item.get("selected_candidate") or {}
        test = selected.get("test", {})
        assertions.append(
            f"{item['root_class']}: state={item['state']} "
            f"test_lcb={float(test.get('precision_wilson_lcb_95', 0.0)):.6f} "
            f"cal={selected.get('calibration', {}).get('support', 0)} "
            f"test={test.get('support', 0)} blockers={','.join(selected.get('blockers', []))}"
        )
    (CHECKS_DIR / "cross_asset_root_evidence_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"report": repo_rel(report_path), "accepted": accepted, "missing": missing}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
