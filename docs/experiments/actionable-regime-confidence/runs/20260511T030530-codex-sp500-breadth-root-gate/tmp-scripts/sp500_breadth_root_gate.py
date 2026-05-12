#!/usr/bin/env python3
"""S&P 500 breadth/proxy gate for MainRegimeV2 Bull/Bear/Sideways roots."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import yfinance as yf
from bs4 import BeautifulSoup


RUN_ID = "20260511T030530+0800-codex-sp500-breadth-root-gate"
WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
START = "2018-01-01"
END = "2026-05-11"
MIN_SUPPORT = 50
QUANTILES = [0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.70, 0.80, 0.90, 0.95, 0.98, 0.99]
Z95 = 1.959963984540054


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def wilson_lcb(success: int, total: int, z: float = Z95) -> float:
    if total <= 0:
        return 0.0
    phat = success / total
    denom = 1.0 + z * z / total
    center = phat + z * z / (2.0 * total)
    margin = z * math.sqrt((phat * (1.0 - phat) + z * z / (4.0 * total)) / total)
    return max(0.0, (center - margin) / denom)


def sp500_tickers(cache_dir: Path) -> list[str]:
    html_path = cache_dir / "sp500_wikipedia.html"
    if not html_path.exists():
        response = requests.get(WIKI_URL, timeout=30, headers={"User-Agent": "ict-engine-regime-audit/1.0"})
        response.raise_for_status()
        html_path.write_text(response.text, encoding="utf-8")
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    table = soup.find("table", {"id": "constituents"})
    if table is None:
        raise RuntimeError("could not locate S&P 500 constituents table")
    out = []
    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if not cols:
            continue
        ticker = cols[0].get_text(strip=True).replace(".", "-")
        out.append(ticker)
    return out


def download_prices(tickers: list[str], cache_dir: Path) -> pd.DataFrame:
    cache_path = cache_dir / "sp500_breadth_prices.csv"
    if cache_path.exists():
        return pd.read_csv(cache_path, index_col=0, parse_dates=True)
    data = yf.download(
        tickers,
        start=START,
        end=END,
        auto_adjust=True,
        progress=False,
        threads=True,
        group_by="column",
    )
    if isinstance(data.columns, pd.MultiIndex):
        close = data["Close"].copy()
    else:
        close = data[["Close"]].copy()
        close.columns = tickers[:1]
    close = close.dropna(axis=1, thresh=int(len(close) * 0.75))
    close.to_csv(cache_path)
    return close


def split_chronological(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ordered = df.sort_index()
    n = len(ordered)
    train_end = int(n * 0.60)
    cal_end = int(n * 0.80)
    return ordered.iloc[:train_end], ordered.iloc[train_end:cal_end], ordered.iloc[cal_end:]


def make_features(close: pd.DataFrame) -> pd.DataFrame:
    core = ["SPY", "RSP", "HYG", "LQD", "TLT", "UUP", "^VIX", "^VIX3M"]
    constituents = [c for c in close.columns if c not in core and not c.startswith("^")]
    spy = close["SPY"]
    returns = close[constituents].pct_change()
    features = pd.DataFrame(index=close.index)
    for window in (20, 50, 100, 200):
        ma = close[constituents].rolling(window).mean()
        features[f"pct_above_{window}d"] = (close[constituents] > ma).mean(axis=1)
    features["advance_decline_1d"] = (returns > 0).mean(axis=1) - (returns < 0).mean(axis=1)
    features["median_constituent_ret_5d"] = close[constituents].pct_change(5).median(axis=1)
    features["median_constituent_ret_20d"] = close[constituents].pct_change(20).median(axis=1)
    features["equal_weight_ret_20d"] = returns.mean(axis=1).rolling(20).sum()
    features["spy_ret_20d"] = spy.pct_change(20)
    features["spy_ret_60d"] = spy.pct_change(60)
    features["rsp_spy_ratio_ret_20d"] = (close["RSP"] / close["SPY"]).pct_change(20)
    features["hyg_lqd_ratio_ret_20d"] = (close["HYG"] / close["LQD"]).pct_change(20)
    features["tlt_ret_20d"] = close["TLT"].pct_change(20)
    features["uup_ret_20d"] = close["UUP"].pct_change(20)
    features["vix_level"] = close["^VIX"]
    features["vix3m_vix_ratio"] = close["^VIX3M"] / close["^VIX"]
    future_ret20 = spy.shift(-20) / spy - 1.0
    future_high20 = spy.shift(-1).rolling(20).max().shift(-19)
    future_low20 = spy.shift(-1).rolling(20).min().shift(-19)
    future_range20 = (future_high20 - future_low20) / spy
    labels = pd.Series("UnknownOrMixed", index=features.index)
    labels[(future_ret20 >= 0.04) & (future_range20 <= 0.10)] = "Bull"
    labels[(future_ret20 <= -0.04)] = "Bear"
    labels[(future_ret20.abs() <= 0.015) & (future_range20 <= 0.055)] = "Sideways"
    labels[(future_ret20 <= -0.08) | (future_range20 >= 0.13)] = "Crisis"
    features["future_ret20_label_only"] = future_ret20
    features["future_range20_label_only"] = future_range20
    features["root_label"] = labels
    return features.dropna()


def evaluate_rule(df: pd.DataFrame, root: str, feature: str, op: str, threshold: float) -> dict:
    if op == ">=":
        mask = df[feature].to_numpy() >= threshold
    else:
        mask = df[feature].to_numpy() <= threshold
    y = (df["root_label"] == root).to_numpy()
    support = int(mask.sum())
    tp = int((mask & y).sum())
    precision = tp / support if support else 0.0
    return {
        "root": root,
        "rule": f"{feature} {op} {threshold:.12g}",
        "feature": feature,
        "op": op,
        "threshold": float(threshold),
        "support": support,
        "true_positive": tp,
        "false_positive": support - tp,
        "precision": precision,
        "wilson95_lcb": wilson_lcb(tp, support),
    }


def evaluate_root(train: pd.DataFrame, cal: pd.DataFrame, test: pd.DataFrame, root: str, feature_cols: list[str]) -> dict:
    candidates = []
    for feature in feature_cols:
        thresholds = sorted(set(float(x) for x in np.quantile(train[feature], QUANTILES)))
        for threshold in thresholds:
            for op in (">=", "<="):
                item = evaluate_rule(train, root, feature, op, threshold)
                if item["support"] >= MIN_SUPPORT:
                    candidates.append(item)
    selected = max(candidates, key=lambda r: (r["wilson95_lcb"], r["precision"], r["true_positive"], r["support"]))
    cal_eval = evaluate_rule(cal, root, selected["feature"], selected["op"], selected["threshold"])
    test_eval = evaluate_rule(test, root, selected["feature"], selected["op"], selected["threshold"])
    accepted_95 = (
        cal_eval["support"] >= MIN_SUPPORT
        and test_eval["support"] >= MIN_SUPPORT
        and cal_eval["wilson95_lcb"] >= 0.95
        and test_eval["wilson95_lcb"] >= 0.95
    )
    return {
        "root": root,
        "accepted_95": accepted_95,
        "selected_rule": selected["rule"],
        "selected_train": selected,
        "selected_calibration": cal_eval,
        "selected_test": test_eval,
        "candidate_rules": len(candidates),
        "top_train_rules": sorted(
            candidates,
            key=lambda r: (r["wilson95_lcb"], r["precision"], r["true_positive"], r["support"]),
            reverse=True,
        )[:10],
    }


def profile(df: pd.DataFrame) -> dict:
    counts = df["root_label"].value_counts().to_dict()
    return {
        "rows": int(len(df)),
        "date_min": df.index.min().date().isoformat(),
        "date_max": df.index.max().date().isoformat(),
        "label_counts": {k: int(v) for k, v in counts.items()},
    }


def write_summary(path: Path, root_reports: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["root", "split", "rule", "support", "true_positive", "false_positive", "precision", "wilson95_lcb"],
        )
        writer.writeheader()
        for report in root_reports:
            for split, key in [("train", "selected_train"), ("calibration", "selected_calibration"), ("test", "selected_test")]:
                row = report[key]
                writer.writerow(
                    {
                        "root": report["root"],
                        "split": split,
                        "rule": row["rule"],
                        "support": row["support"],
                        "true_positive": row["true_positive"],
                        "false_positive": row["false_positive"],
                        "precision": f"{row['precision']:.12f}",
                        "wilson95_lcb": f"{row['wilson95_lcb']:.12f}",
                    }
                )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    constituents = sp500_tickers(args.cache_dir)
    tickers = sorted(set(constituents + ["SPY", "RSP", "HYG", "LQD", "TLT", "UUP", "^VIX", "^VIX3M"]))
    close = download_prices(tickers, args.cache_dir)
    features = make_features(close)
    feature_cols = [c for c in features.columns if not c.endswith("_label_only") and c != "root_label"]
    train, cal, test = split_chronological(features)
    root_reports = [evaluate_root(train, cal, test, root, feature_cols) for root in ["Bull", "Bear", "Sideways"]]
    accepted_roots = [r["root"] for r in root_reports if r["accepted_95"]]

    feature_sample_path = args.out_dir / "sp500_breadth_root_feature_sample.csv"
    features.drop(columns=["future_ret20_label_only", "future_range20_label_only"]).tail(500).to_csv(feature_sample_path)

    report = {
        "run_id": RUN_ID,
        "candidate_regime": "Bull/Bear/Sideways",
        "gate": "accepted_95_partial" if accepted_roots else "blocked_sp500_breadth_root_gate_below_95",
        "accepted_95_roots_from_this_run": accepted_roots,
        "thresholds_relaxed": False,
        "runtime_code_changed": False,
        "raw_data_committed_to_repo": False,
        "source": {
            "constituents_url": WIKI_URL,
            "cache_dir": str(args.cache_dir),
            "price_cache_sha256": sha256(args.cache_dir / "sp500_breadth_prices.csv"),
            "constituents_count": len(constituents),
            "downloaded_close_columns": int(len(close.columns)),
        },
        "market_timeframes": ["S&P 500 daily breadth/proxy context"],
        "blocked_predictors": ["future_ret20_label_only", "future_range20_label_only", "root_label"],
        "feature_columns": feature_cols,
        "profiles": {"train": profile(train), "calibration": profile(cal), "test": profile(test)},
        "root_reports": root_reports,
        "active_root_accounting_after_gate": {
            "accepted_95_roots": ["Crisis"] + accepted_roots,
            "missing_95_roots": [r for r in ["Bull", "Bear", "Sideways", "Manipulation"] if r not in accepted_roots],
        },
    }
    json_path = args.out_dir / "sp500_breadth_root_gate_report.json"
    md_path = args.out_dir / "sp500_breadth_root_gate_report.md"
    csv_path = args.out_dir / "sp500_breadth_root_gate_summary.csv"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_summary(csv_path, root_reports)

    lines = [
        "# S&P 500 Breadth Root Gate",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Source",
        "",
        f"- Constituents source: `{WIKI_URL}`",
        f"- Constituents parsed: {len(constituents)}; downloaded close columns retained: {len(close.columns)}.",
        f"- Raw price cache: `{args.cache_dir / 'sp500_breadth_prices.csv'}`",
        "- Raw data committed to repo: false.",
        "- Predictors used: daily breadth, credit/rates/USD/volatility proxies; future label columns blocked as predictors.",
        "",
        "## Split",
        "",
        f"- Train: {profile(train)}",
        f"- Calibration: {profile(cal)}",
        f"- Test: {profile(test)}",
        "",
        "## Gate Results",
        "",
    ]
    for item in root_reports:
        lines.extend(
            [
                f"### {item['root']}",
                "",
                f"- Selected train-only rule: `{item['selected_rule']}`.",
                f"- Train Wilson95 LCB: `{item['selected_train']['wilson95_lcb']:.6f}` with support {item['selected_train']['support']}.",
                f"- Calibration Wilson95 LCB: `{item['selected_calibration']['wilson95_lcb']:.6f}` with support {item['selected_calibration']['support']}.",
                f"- Test Wilson95 LCB: `{item['selected_test']['wilson95_lcb']:.6f}` with support {item['selected_test']['support']}.",
                f"- Accepted 95: {item['accepted_95']}.",
                "",
            ]
        )
    lines.extend(
        [
            "## Decision",
            "",
            f"- Accepted 95 roots from this run: `{accepted_roots}`.",
            f"- Gate: `{report['gate']}`.",
            "- Thresholds relaxed: false.",
            "- Runtime code changed: false.",
            "- Trade usable: false.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
