#!/usr/bin/env python3
"""Self-contained Markov-style latent-state gate for MainRegimeV2 roots."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T031433+0800-codex-hmm-markov-root-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T031433-codex-hmm-markov-root-gate"
OUT_DIR = RUN_ROOT / "hmm-markov-gate"
CHECK_DIR = RUN_ROOT / "checks"
TMP_RAW_DIR = Path("/private/tmp/ict-regime-hmm-markov-root")

TARGETS = ["SPY", "QQQ", "IWM", "BTC-USD", "ETH-USD"]
PROXIES = ["TLT", "HYG", "LQD", "UUP", "GLD", "DBC", "^VIX", "^VIX3M"]
ROOTS = ["Bull", "Bear", "Sideways"]
Z95 = 1.959963984540054
STATE_COUNT = 6
SUPPORT_TRAIN_MIN = 120
SUPPORT_CAL_MIN = 120
SUPPORT_TEST_MIN = 60
COVERAGE_MIN = 0.03
ECE_MAX = 0.05
QUANTILES = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]

MARKET_CONTEXT = {
    "SPY": "us_large_cap_equity",
    "QQQ": "us_growth_equity",
    "IWM": "us_small_cap_equity",
    "BTC-USD": "crypto_btc",
    "ETH-USD": "crypto_eth",
}


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


def json_counts(series: pd.Series) -> dict[str, int]:
    out: dict[str, int] = {}
    for key, value in series.items():
        label = "|".join(str(part) for part in key) if isinstance(key, tuple) else str(key)
        out[label] = int(value)
    return out


def normalize_download(raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        level0 = set(str(x) for x in raw.columns.get_level_values(0))
        if "Close" in level0:
            close = raw["Close"].copy()
        else:
            cols = {}
            for ticker in tickers:
                if ticker in level0 and "Close" in raw[ticker].columns:
                    cols[ticker] = raw[ticker]["Close"]
            close = pd.DataFrame(cols)
    else:
        close = raw[["Close"]].copy()
        close.columns = tickers[:1]
    close.index = pd.to_datetime(close.index, utc=True).normalize()
    close = close.sort_index()
    close = close.dropna(axis=1, how="all")
    return close


def fetch_prices() -> tuple[pd.DataFrame, dict]:
    TMP_RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = TMP_RAW_DIR / "yfinance_cross_asset_daily_close.csv"
    tickers = sorted(set(TARGETS + PROXIES))
    if path.exists():
        close = pd.read_csv(path, index_col=0, parse_dates=True)
        close.index = pd.to_datetime(close.index, utc=True).normalize()
    else:
        raw = yf.download(tickers, period="15y", interval="1d", auto_adjust=True, progress=False, threads=True, group_by="ticker")
        close = normalize_download(raw, tickers)
        close.to_csv(path)
    status = {
        "provider": "yfinance",
        "requested": tickers,
        "available": sorted(close.columns.tolist()),
        "raw_cache": str(path),
        "rows": int(len(close)),
        "date_min": close.index.min().isoformat() if len(close) else None,
        "date_max": close.index.max().isoformat() if len(close) else None,
    }
    return close.ffill(limit=5), status


def resample_weekly(close: pd.DataFrame) -> pd.DataFrame:
    return close.resample("W-FRI").last().dropna(how="all")


def future_window_range(series: pd.Series, horizon: int) -> pd.Series:
    future_max = series.shift(-1).rolling(horizon, min_periods=max(3, horizon // 3)).max().shift(-(horizon - 1))
    future_min = series.shift(-1).rolling(horizon, min_periods=max(3, horizon // 3)).min().shift(-(horizon - 1))
    return (future_max - future_min) / series


def assign_root(price: pd.Series, timeframe: str) -> pd.DataFrame:
    horizon = 20 if timeframe == "1d" else 8
    future_ret = np.log(price.shift(-horizon)) - np.log(price)
    future_range = future_window_range(price, horizon)
    labels = pd.Series("UnknownOrMixed", index=price.index)
    labels[(future_ret >= 0.04) & (future_range <= 0.10)] = "Bull"
    labels[future_ret <= -0.04] = "Bear"
    labels[(future_ret.abs() <= 0.015) & (future_range <= 0.055)] = "Sideways"
    labels[(future_ret <= -0.08) | (future_range >= 0.13)] = "Crisis"
    return pd.DataFrame({"future_ret_label_only": future_ret, "future_range_label_only": future_range, "root_label": labels})


def relret(close: pd.DataFrame, lhs: str, rhs: str, periods: int) -> pd.Series:
    if lhs not in close.columns or rhs not in close.columns:
        return pd.Series(np.nan, index=close.index)
    return np.log(close[lhs] / close[rhs]).diff(periods)


def make_rows(close: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    ret = np.log(close).diff()
    for ticker in TARGETS:
        if ticker not in close.columns:
            continue
        price = close[ticker]
        frame = pd.DataFrame(index=close.index)
        frame["ts"] = close.index
        frame["instrument"] = ticker
        frame["timeframe"] = timeframe
        frame["market_context"] = MARKET_CONTEXT[ticker]
        frame["asset_ret_5"] = np.log(price).diff(5)
        frame["asset_ret_20"] = np.log(price).diff(20)
        frame["asset_ret_60"] = np.log(price).diff(60)
        frame["asset_vol_20"] = ret[ticker].rolling(20, min_periods=8).std()
        frame["asset_vol_60"] = ret[ticker].rolling(60, min_periods=16).std()
        rolling_max = price.rolling(60, min_periods=20).max()
        frame["asset_drawdown_60"] = price / rolling_max - 1.0
        frame["spy_ret_20"] = np.log(close["SPY"]).diff(20) if "SPY" in close.columns else np.nan
        frame["tlt_ret_20"] = np.log(close["TLT"]).diff(20) if "TLT" in close.columns else np.nan
        frame["uup_ret_20"] = np.log(close["UUP"]).diff(20) if "UUP" in close.columns else np.nan
        frame["gld_ret_20"] = np.log(close["GLD"]).diff(20) if "GLD" in close.columns else np.nan
        frame["dbc_ret_20"] = np.log(close["DBC"]).diff(20) if "DBC" in close.columns else np.nan
        frame["hyg_lqd_ratio_ret_20"] = relret(close, "HYG", "LQD", 20)
        frame["qqq_spy_ratio_ret_20"] = relret(close, "QQQ", "SPY", 20)
        frame["iwm_spy_ratio_ret_20"] = relret(close, "IWM", "SPY", 20)
        frame["eth_btc_ratio_ret_20"] = relret(close, "ETH-USD", "BTC-USD", 20)
        if "^VIX" in close.columns:
            frame["vix_level"] = close["^VIX"]
            frame["vix_chg_20"] = np.log(close["^VIX"]).diff(20)
        else:
            frame["vix_level"] = np.nan
            frame["vix_chg_20"] = np.nan
        if "^VIX" in close.columns and "^VIX3M" in close.columns:
            frame["vix3m_vix_ratio"] = close["^VIX3M"] / close["^VIX"]
        else:
            frame["vix3m_vix_ratio"] = np.nan
        labels = assign_root(price, timeframe)
        frame = frame.join(labels)
        rows.append(frame)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def build_features(close: pd.DataFrame) -> pd.DataFrame:
    daily = make_rows(close, "1d")
    weekly = make_rows(resample_weekly(close), "1w")
    data = pd.concat([daily, weekly], ignore_index=True)
    data = data.dropna(subset=["future_ret_label_only", "future_range_label_only", "root_label"])
    return data.sort_values(["ts", "instrument", "timeframe"]).reset_index(drop=True)


def split_by_time(data: pd.DataFrame) -> pd.DataFrame:
    dates = pd.Series(sorted(data["ts"].dropna().unique()))
    train_cut = dates.iloc[int(len(dates) * 0.60)]
    cal_cut = dates.iloc[int(len(dates) * 0.80)]
    out = data.copy()
    out["split"] = np.where(out["ts"] <= train_cut, "train", np.where(out["ts"] <= cal_cut, "calibration", "test"))
    return out


def standardize(train: pd.DataFrame, all_data: pd.DataFrame, cols: list[str]) -> tuple[np.ndarray, np.ndarray, pd.Series, pd.Series]:
    means = train[cols].apply(numeric).mean()
    stds = train[cols].apply(numeric).std().replace(0.0, np.nan).fillna(1.0)
    train_x = ((train[cols].apply(numeric).fillna(means) - means) / stds).to_numpy(float)
    all_x = ((all_data[cols].apply(numeric).fillna(means) - means) / stds).to_numpy(float)
    train_x = np.nan_to_num(train_x, nan=0.0, posinf=0.0, neginf=0.0)
    all_x = np.nan_to_num(all_x, nan=0.0, posinf=0.0, neginf=0.0)
    return train_x, all_x, means, stds


def fit_kmeans(train_x: np.ndarray, k: int = STATE_COUNT, iterations: int = 60) -> np.ndarray:
    if len(train_x) < k:
        raise RuntimeError("not enough rows for latent states")
    score = train_x[:, 0] if train_x.shape[1] else np.arange(len(train_x))
    order = np.argsort(score)
    init_idx = [order[int(i * (len(order) - 1) / max(1, k - 1))] for i in range(k)]
    centers = train_x[init_idx].copy()
    for _ in range(iterations):
        dist = ((train_x[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels = dist.argmin(axis=1)
        new_centers = centers.copy()
        for state in range(k):
            mask = labels == state
            if mask.any():
                new_centers[state] = train_x[mask].mean(axis=0)
        if np.allclose(new_centers, centers):
            break
        centers = new_centers
    return centers


def state_posteriors(all_x: np.ndarray, centers: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    dist = ((all_x[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
    states = dist.argmin(axis=1)
    scale = max(float(np.nanmedian(dist)), 1e-9)
    weights = np.exp(-dist / scale)
    weights = weights / weights.sum(axis=1, keepdims=True)
    return states, weights


def add_markov_state_features(data: pd.DataFrame, feature_cols: list[str]) -> tuple[pd.DataFrame, dict]:
    train = data[data["split"] == "train"].copy()
    train_x, all_x, means, stds = standardize(train, data, feature_cols)
    centers = fit_kmeans(train_x)
    states, posterior = state_posteriors(all_x, centers)
    out = data.copy()
    out["latent_state"] = states
    for state in range(STATE_COUNT):
        out[f"latent_state_{state}"] = (out["latent_state"] == state).astype(float)

    train_states = out[out["split"] == "train"]
    root_probs: dict[int, dict[str, float]] = {}
    for state in range(STATE_COUNT):
        state_rows = train_states[train_states["latent_state"] == state]
        denom = max(1, len(state_rows))
        root_probs[state] = {root: float((state_rows["root_label"] == root).sum() / denom) for root in ROOTS}
    for root in ROOTS:
        out[f"p_{root.lower()}"] = [root_probs[int(state)][root] for state in out["latent_state"]]
    p_matrix = out[[f"p_{root.lower()}" for root in ROOTS]].to_numpy(float)
    entropy_terms = np.zeros_like(p_matrix)
    positive = p_matrix > 0
    entropy_terms[positive] = p_matrix[positive] * np.log(p_matrix[positive])
    out["state_entropy"] = -np.nansum(entropy_terms, axis=1)
    out["state_confidence"] = np.nanmax(p_matrix, axis=1)
    out["posterior_confidence"] = posterior.max(axis=1)

    transition_counts = np.ones((STATE_COUNT, STATE_COUNT), dtype=float)
    for _, group in train_states.sort_values("ts").groupby(["instrument", "timeframe"], sort=False):
        values = group["latent_state"].to_numpy(int)
        for prev, nxt in zip(values[:-1], values[1:]):
            transition_counts[prev, nxt] += 1.0
    transition = transition_counts / transition_counts.sum(axis=1, keepdims=True)
    out["state_self_transition_prob"] = [float(transition[int(s), int(s)]) for s in out["latent_state"]]
    out["state_run_length"] = 1
    for _, idx in out.sort_values("ts").groupby(["instrument", "timeframe"], sort=False).groups.items():
        ordered = out.loc[list(idx)].sort_values("ts")
        run = []
        prev = None
        length = 0
        for state in ordered["latent_state"].to_numpy(int):
            length = length + 1 if prev == state else 1
            run.append(length)
            prev = state
        out.loc[ordered.index, "state_run_length"] = run
    meta = {
        "state_count": STATE_COUNT,
        "fit": "deterministic_kmeans_markov_surrogate_no_hmmlearn_installed",
        "train_feature_means": {k: float(v) for k, v in means.items()},
        "train_feature_stds": {k: float(v) for k, v in stds.items()},
        "state_root_probabilities": {str(k): v for k, v in root_probs.items()},
    }
    return out, meta


def candidate_feature_cols() -> list[str]:
    return (
        [f"p_{root.lower()}" for root in ROOTS]
        + ["state_entropy", "state_confidence", "posterior_confidence", "state_self_transition_prob", "state_run_length"]
        + [f"latent_state_{i}" for i in range(STATE_COUNT)]
    )


def rule_mask(df: pd.DataFrame, feature: str, op: str, threshold: float) -> pd.Series:
    values = numeric(df[feature])
    return values >= threshold if op == ">=" else values <= threshold


def split_eval(df: pd.DataFrame, root: str, feature: str, op: str, threshold: float) -> dict:
    mask = rule_mask(df, feature, op, threshold).fillna(False)
    y = df["root_label"] == root
    support = int(mask.sum())
    success = int((mask & y).sum())
    precision = success / support if support else 0.0
    p_col = f"p_{root.lower()}"
    ece = float(abs(numeric(df.loc[mask, p_col]).mean() - precision)) if support and p_col in df.columns else 1.0
    instruments = sorted(df.loc[mask, "instrument"].dropna().unique().tolist())
    contexts = sorted(df.loc[mask, "market_context"].dropna().unique().tolist())
    timeframes = sorted(df.loc[mask, "timeframe"].dropna().unique().tolist())
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lcb(success, support),
        "coverage": support / len(df) if len(df) else 0.0,
        "ece": ece,
        "validation_instruments": instruments,
        "validation_market_contexts": contexts,
        "validation_timeframes": timeframes,
    }


def evaluate_root(data: pd.DataFrame, root: str) -> dict:
    train = data[data["split"] == "train"]
    cal = data[data["split"] == "calibration"]
    test = data[data["split"] == "test"]
    candidates = []
    for feature in candidate_feature_cols():
        values = numeric(train[feature]).dropna()
        if len(values) < SUPPORT_TRAIN_MIN:
            continue
        thresholds = sorted(set(float(x) for x in np.quantile(values, QUANTILES)))
        for threshold in thresholds:
            for op in (">=", "<="):
                ev = split_eval(train, root, feature, op, threshold)
                if ev["support"] >= SUPPORT_TRAIN_MIN:
                    candidates.append({"feature": feature, "op": op, "threshold": threshold, "train": ev})
    if not candidates:
        raise RuntimeError(f"no candidates for {root}")
    selected = max(
        candidates,
        key=lambda c: (
            c["train"]["precision_wilson_lcb_95"],
            c["train"]["precision"],
            c["train"]["support"],
        ),
    )
    cal_ev = split_eval(cal, root, selected["feature"], selected["op"], selected["threshold"])
    test_ev = split_eval(test, root, selected["feature"], selected["op"], selected["threshold"])
    blockers = []
    if cal_ev["support"] < SUPPORT_CAL_MIN:
        blockers.append("calibration_support_below_120")
    if test_ev["support"] < SUPPORT_TEST_MIN:
        blockers.append("test_support_below_60")
    if cal_ev["precision_wilson_lcb_95"] < 0.95:
        blockers.append("calibration_wilson95_below_0_95")
    if test_ev["precision_wilson_lcb_95"] < 0.95:
        blockers.append("test_wilson95_below_0_95")
    if min(cal_ev["coverage"], test_ev["coverage"]) < COVERAGE_MIN:
        blockers.append("coverage_below_0_03")
    if max(cal_ev["ece"], test_ev["ece"]) > ECE_MAX:
        blockers.append("ece_above_0_05")
    if min(len(cal_ev["validation_instruments"]), len(test_ev["validation_instruments"])) < 2:
        blockers.append("validation_instruments_below_2")
    if min(len(cal_ev["validation_market_contexts"]), len(test_ev["validation_market_contexts"])) < 2:
        blockers.append("validation_market_contexts_below_2")
    if min(len(cal_ev["validation_timeframes"]), len(test_ev["validation_timeframes"])) < 2:
        blockers.append("validation_timeframes_below_2")
    return {
        "root_class": root,
        "rule": f"{selected['feature']} {selected['op']} {selected['threshold']:.12g}",
        "accepted_95": not blockers,
        "state": "accepted_95" if not blockers else "blocked",
        "blockers": blockers,
        "train": selected["train"],
        "calibration": cal_ev,
        "test": test_ev,
        "top_train_rules": sorted(
            [
                {
                    "rule": f"{c['feature']} {c['op']} {c['threshold']:.12g}",
                    "wilson95": c["train"]["precision_wilson_lcb_95"],
                    "precision": c["train"]["precision"],
                    "support": c["train"]["support"],
                }
                for c in candidates
            ],
            key=lambda x: (x["wilson95"], x["precision"], x["support"]),
            reverse=True,
        )[:10],
    }


def write_summary(path: Path, root_reports: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["root", "split", "rule", "support", "success", "precision", "wilson95_lcb", "coverage", "ece", "accepted_95", "blockers"],
        )
        writer.writeheader()
        for report in root_reports:
            for split in ["train", "calibration", "test"]:
                ev = report[split]
                writer.writerow(
                    {
                        "root": report["root_class"],
                        "split": split,
                        "rule": report["rule"],
                        "support": ev["support"],
                        "success": ev["success"],
                        "precision": f"{ev['precision']:.12f}",
                        "wilson95_lcb": f"{ev['precision_wilson_lcb_95']:.12f}",
                        "coverage": f"{ev['coverage']:.12f}",
                        "ece": f"{ev['ece']:.12f}",
                        "accepted_95": report["accepted_95"],
                        "blockers": "|".join(report["blockers"]),
                    }
                )


def write_report_md(path: Path, report: dict) -> None:
    lines = [
        "# HMM/Markov Root Gate",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Data",
        "",
        f"- yfinance symbols requested: {', '.join(report['provider']['requested'])}.",
        f"- yfinance symbols available: {', '.join(report['provider']['available'])}.",
        f"- Derived feature rows: {report['dataset']['feature_rows']}.",
        f"- Raw provider CSV committed: {str(report['decision']['raw_provider_csv_committed']).lower()}; cache path `{report['provider']['raw_cache']}`.",
        "- Latent-state fit: deterministic train-only k-means Markov surrogate because `hmmlearn` / `sklearn` are not installed.",
        "- Predictors blocked: `future_ret_label_only`, `future_range_label_only`, `root_label`, timestamps, identifiers, and label fields.",
        "",
        "## Gate Results",
        "",
    ]
    for item in report["root_reports"]:
        lines.append(
            f"- {item['root_class']}: accepted_95={item['accepted_95']}, rule=`{item['rule']}`, "
            f"cal_lcb={item['calibration']['precision_wilson_lcb_95']:.6f}, "
            f"test_lcb={item['test']['precision_wilson_lcb_95']:.6f}, "
            f"cal_support={item['calibration']['support']}, test_support={item['test']['support']}, "
            f"blockers={'|'.join(item['blockers']) if item['blockers'] else 'none'}"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Newly accepted active roots: {', '.join(report['decision']['newly_accepted_roots']) if report['decision']['newly_accepted_roots'] else 'none'}.",
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
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    close, provider = fetch_prices()
    feature_base = split_by_time(build_features(close))
    base_feature_cols = [
        "asset_ret_5",
        "asset_ret_20",
        "asset_ret_60",
        "asset_vol_20",
        "asset_vol_60",
        "asset_drawdown_60",
        "spy_ret_20",
        "tlt_ret_20",
        "uup_ret_20",
        "gld_ret_20",
        "dbc_ret_20",
        "hyg_lqd_ratio_ret_20",
        "qqq_spy_ratio_ret_20",
        "iwm_spy_ratio_ret_20",
        "eth_btc_ratio_ret_20",
        "vix_level",
        "vix_chg_20",
        "vix3m_vix_ratio",
    ]
    feature_base = feature_base.dropna(subset=["root_label"])
    feature_state, markov_meta = add_markov_state_features(feature_base, base_feature_cols)
    feature_path = OUT_DIR / "hmm_markov_root_feature_table.csv"
    sample_path = OUT_DIR / "hmm_markov_root_feature_sample.csv"
    feature_state.to_csv(feature_path, index=False)
    feature_state.tail(500).to_csv(sample_path, index=False)

    root_reports = [evaluate_root(feature_state, root) for root in ROOTS]
    accepted = [r["root_class"] for r in root_reports if r["accepted_95"]]
    report = {
        "run_id": RUN_ID,
        "active_axis": "MainRegimeV2",
        "candidate_roots": ROOTS,
        "provider": provider,
        "dataset": {
            "feature_rows": int(len(feature_state)),
            "feature_table": repo_rel(feature_path),
            "targets": TARGETS,
            "timeframes": ["1d", "1w"],
            "split_counts": json_counts(feature_state.groupby(["split", "timeframe"]).size()),
            "label_counts": json_counts(feature_state.groupby(["root_label", "timeframe"]).size()),
        },
        "markov_meta": markov_meta,
        "blocked_predictors": ["future_ret_label_only", "future_range_label_only", "root_label", "ts", "instrument", "timeframe", "market_context"],
        "root_reports": root_reports,
        "decision": {
            "gate": "accepted_95_partial" if accepted else "blocked_hmm_markov_root_gate_below_95",
            "newly_accepted_roots": accepted,
            "missing_active_roots_after_gate": [r for r in ["Bull", "Bear", "Sideways", "Manipulation"] if r not in accepted],
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "raw_provider_csv_committed": False,
            "trade_usable": False,
            "blocker": "Train-only latent-state root posteriors did not close all missing MainRegimeV2 roots at the unchanged 95% held-out gate.",
            "next_action": "Acquire labeled bull/bear/sideways regime-cycle data or true options/dealer-positioning history; avoid more proxy-only threshold scans, and keep Manipulation blocked until direct labels exist.",
        },
        "manipulation_handling": "not_evaluated_here_direct_input_required_accepted_false",
    }
    json_path = OUT_DIR / "hmm_markov_root_gate_report.json"
    md_path = OUT_DIR / "hmm_markov_root_gate_report.md"
    summary_path = OUT_DIR / "hmm_markov_root_gate_summary.csv"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_report_md(md_path, report)
    write_summary(summary_path, root_reports)

    assertions = [
        f"RUN_ID {RUN_ID}",
        "ACTIVE_AXIS MainRegimeV2",
        "CANDIDATE_ROOTS Bull,Bear,Sideways",
        f"FEATURE_ROWS {len(feature_state)}",
        f"NEWLY_ACCEPTED_ROOTS {','.join(accepted) if accepted else 'none'}",
        f"ACCEPTED_95 {str(bool(accepted)).lower()}",
        "MANIPULATION_ACCEPTED false",
        "THRESHOLDS_RELAXED false",
        "RUNTIME_CODE_CHANGED false",
        "RAW_PROVIDER_CSV_COMMITTED false",
        "TRADE_USABLE false",
        f"GATE {report['decision']['gate']}",
    ]
    for item in root_reports:
        assertions.append(f"{item['root_class']}_CAL_LCB {item['calibration']['precision_wilson_lcb_95']:.6f}")
        assertions.append(f"{item['root_class']}_TEST_LCB {item['test']['precision_wilson_lcb_95']:.6f}")
    (CHECK_DIR / "hmm_markov_root_gate_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    (RUN_ROOT / "README.md").write_text(
        "\n".join(
            [
                "# HMM/Markov Root Gate",
                "",
                f"- report: `{repo_rel(json_path)}`",
                f"- summary: `{repo_rel(summary_path)}`",
                f"- assertions: `{repo_rel(CHECK_DIR / 'hmm_markov_root_gate_assertions.out')}`",
                "- raw provider CSV committed: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
