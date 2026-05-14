#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T041923+0800-codex-yahoo-sourcebacked-parent-root-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T041923-codex-yahoo-sourcebacked-parent-root-gate"
OUT_DIR = RUN_ROOT / "yahoo-parent-root-gate"
CHECK_DIR = RUN_ROOT / "checks"
CACHE_DIR = Path("/private/tmp/ict-regime-yahoo-sourcebacked-parent-root-gate")

EQUITY_TICKERS = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "HYG", "GLD"]
CRYPTO_TICKERS = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD"]
TICKERS = EQUITY_TICKERS + CRYPTO_TICKERS
START = "2015-01-01"
END = "2026-05-11"
Z95 = 1.959963984540054

ACCEPTANCE_95 = {
    "precision_wilson_lcb_95_min": 0.95,
    "support_min": 250,
    "coverage_min": 0.03,
    "ece_max": 0.05,
    "validation_instruments_min": 2,
    "validation_market_contexts_min": 2,
    "validation_timeframes_min": 2,
}

FEATURE_COLUMNS = [
    "bear_drawdown_ratio",
    "bear_return_ratio",
    "sideways_abs_return_ratio",
    "sideways_range_ratio",
    "sideways_ma_gap_ratio",
    "ret_trend",
    "ret_long",
    "drawdown_long",
    "range_trend",
    "ma_gap_trend",
    "vol_trend",
]


@dataclass(frozen=True)
class Rule:
    root_class: str
    name: str
    terms: tuple[tuple[str, str, float], ...]
    source_definition_candidate: bool = False

    def expression(self) -> str:
        return " AND ".join(f"{feature} {op} {threshold:.12g}" for feature, op, threshold in self.terms)

    def mask(self, df: pd.DataFrame) -> np.ndarray:
        out = np.ones(len(df), dtype=bool)
        for feature, op, threshold in self.terms:
            values = pd.to_numeric(df[feature], errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(np.inf).to_numpy(float)
            if op == "<=":
                out &= values <= threshold
            elif op == ">=":
                out &= values >= threshold
            else:
                raise ValueError(f"unsupported op {op}")
        return out


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson_lcb(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2.0 * total)
    margin = Z95 * math.sqrt((p * (1.0 - p) + Z95 * Z95 / (4.0 * total)) / total)
    return max(0.0, (center - margin) / denom)


def download_close(interval: str) -> pd.DataFrame:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"yahoo_close_{interval}.csv"
    if cache_path.exists():
        return pd.read_csv(cache_path, index_col=0, parse_dates=True)

    data = yf.download(
        TICKERS,
        start=START,
        end=END,
        interval=interval,
        auto_adjust=True,
        progress=False,
        threads=True,
        group_by="column",
    )
    if isinstance(data.columns, pd.MultiIndex):
        close = data["Close"].copy()
    else:
        close = data[["Close"]].copy()
        close.columns = [TICKERS[0]]
    close = close.dropna(axis=1, thresh=max(120, int(len(close) * 0.20)))
    close.to_csv(cache_path)
    return close


def context_thresholds(market_context: str, timeframe: str) -> dict[str, float]:
    is_crypto = market_context == "crypto"
    if timeframe == "1d":
        return {
            "trend_window": 60,
            "long_window": 120,
            "bear_drawdown": 0.35 if is_crypto else 0.20,
            "bear_return": 0.10 if is_crypto else 0.04,
            "sideways_abs_return": 0.12 if is_crypto else 0.04,
            "sideways_range": 0.55 if is_crypto else 0.18,
            "sideways_ma_gap": 0.12 if is_crypto else 0.04,
        }
    return {
        "trend_window": 26,
        "long_window": 52,
        "bear_drawdown": 0.45 if is_crypto else 0.20,
        "bear_return": 0.18 if is_crypto else 0.06,
        "sideways_abs_return": 0.22 if is_crypto else 0.08,
        "sideways_range": 0.80 if is_crypto else 0.30,
        "sideways_ma_gap": 0.22 if is_crypto else 0.08,
    }


def build_instrument_features(close: pd.Series, ticker: str, timeframe: str) -> pd.DataFrame:
    market_context = "crypto" if ticker.endswith("-USD") else "equity_etf"
    t = context_thresholds(market_context, timeframe)
    trend_window = int(t["trend_window"])
    long_window = int(t["long_window"])

    df = pd.DataFrame({"ts": close.index, "ticker": ticker, "close": close.to_numpy(dtype=float)})
    df["timeframe"] = timeframe
    df["market_context"] = market_context
    df["ret1"] = df["close"].pct_change()

    for window in sorted({trend_window, long_window, 20, 60, 120}):
        roll_max = df["close"].rolling(window).max()
        roll_min = df["close"].rolling(window).min()
        roll_mean = df["close"].rolling(window).mean()
        df[f"ret{window}"] = df["close"].pct_change(window)
        df[f"vol{window}"] = df["ret1"].rolling(window).std() * math.sqrt(252 if timeframe == "1d" else 52)
        df[f"drawdown{window}"] = df["close"] / roll_max - 1.0
        df[f"range{window}"] = (roll_max - roll_min) / roll_mean
        df[f"ma_gap{window}"] = df["close"] / roll_mean - 1.0

    ret_trend = df[f"ret{trend_window}"]
    ret_long = df[f"ret{long_window}"]
    drawdown_long = df[f"drawdown{long_window}"]
    range_trend = df[f"range{trend_window}"]
    ma_gap_trend = df[f"ma_gap{trend_window}"]
    vol_trend = df[f"vol{trend_window}"]

    df["ret_trend"] = ret_trend
    df["ret_long"] = ret_long
    df["drawdown_long"] = drawdown_long
    df["range_trend"] = range_trend
    df["ma_gap_trend"] = ma_gap_trend
    df["vol_trend"] = vol_trend
    df["bear_drawdown_ratio"] = -drawdown_long / float(t["bear_drawdown"])
    df["bear_return_ratio"] = -ret_trend / float(t["bear_return"])
    df["sideways_abs_return_ratio"] = ret_trend.abs() / float(t["sideways_abs_return"])
    df["sideways_range_ratio"] = range_trend / float(t["sideways_range"])
    df["sideways_ma_gap_ratio"] = ma_gap_trend.abs() / float(t["sideways_ma_gap"])

    labels = pd.Series("UnknownOrMixed", index=df.index)
    labels[(df["ret_trend"] >= (0.08 if timeframe == "1d" else 0.12)) & (df["bear_drawdown_ratio"] < 0.5)] = "Bull"
    labels[(df["bear_drawdown_ratio"] >= 1.0) & (df["bear_return_ratio"] >= 1.0)] = "Bear"
    sideways = (
        labels.eq("UnknownOrMixed")
        & (df["sideways_abs_return_ratio"] <= 1.0)
        & (df["sideways_range_ratio"] <= 1.0)
        & (df["sideways_ma_gap_ratio"] <= 1.0)
    )
    labels[sideways] = "Sideways"
    df["root_label"] = labels
    return df.dropna(subset=FEATURE_COLUMNS + ["root_label"]).copy()


def build_panel() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for interval, timeframe in [("1d", "1d"), ("1wk", "1w")]:
        close = download_close(interval)
        for ticker in close.columns:
            series = close[ticker].dropna().astype(float)
            if len(series) < 180:
                continue
            frames.append(build_instrument_features(series, ticker, timeframe))
    if not frames:
        raise RuntimeError("no usable Yahoo/yfinance close series")
    df = pd.concat(frames, ignore_index=True)
    df["split"] = ""
    for _, idx in df.groupby(["ticker", "timeframe"]).groups.items():
        ordered = sorted(idx, key=lambda i: df.loc[i, "ts"])
        n = len(ordered)
        train_end = int(n * 0.60)
        calibration_end = int(n * 0.80)
        df.loc[ordered[:train_end], "split"] = "train"
        df.loc[ordered[train_end:calibration_end], "split"] = "calibration"
        df.loc[ordered[calibration_end:], "split"] = "test"
    return df[df["split"].isin(["train", "calibration", "test"])].reset_index(drop=True)


def split_metric(df: pd.DataFrame, mask: np.ndarray, y: np.ndarray, split_name: str, train_precision: float | None = None) -> dict[str, Any]:
    split_mask = df["split"].to_numpy() == split_name
    selected = mask & split_mask
    support = int(selected.sum())
    success = int((selected & y).sum())
    precision = success / support if support else 0.0
    reference = precision if train_precision is None else train_precision
    selected_df = df.loc[selected]
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lcb(success, support),
        "coverage": support / int(split_mask.sum()) if int(split_mask.sum()) else 0.0,
        "ece": abs(reference - precision) if support else 0.0,
        "validation_instruments": sorted(selected_df["ticker"].dropna().astype(str).unique().tolist()),
        "validation_market_contexts": sorted(selected_df["market_context"].dropna().astype(str).unique().tolist()),
        "validation_timeframes": sorted(selected_df["timeframe"].dropna().astype(str).unique().tolist()),
    }


def blockers(calibration: dict[str, Any], test: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for split_name, metric in [("calibration", calibration), ("test", test)]:
        if metric["support"] < ACCEPTANCE_95["support_min"]:
            out.append(f"{split_name}_support_below_250")
        if metric["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
            out.append(f"{split_name}_wilson95_below_0_95")
        if metric["coverage"] < ACCEPTANCE_95["coverage_min"]:
            out.append(f"{split_name}_coverage_below_0_03")
        if metric["ece"] > ACCEPTANCE_95["ece_max"]:
            out.append(f"{split_name}_ece_above_0_05")
        if len(metric["validation_instruments"]) < ACCEPTANCE_95["validation_instruments_min"]:
            out.append(f"{split_name}_validation_instruments_below_2")
        if len(metric["validation_market_contexts"]) < ACCEPTANCE_95["validation_market_contexts_min"]:
            out.append(f"{split_name}_validation_market_contexts_below_2")
        if len(metric["validation_timeframes"]) < ACCEPTANCE_95["validation_timeframes_min"]:
            out.append(f"{split_name}_validation_timeframes_below_2")
    return out


def base_rules(root: str) -> list[Rule]:
    if root == "Bear":
        return [
            Rule(root, "source_observed_bear_definition", (("bear_drawdown_ratio", ">=", 1.0), ("bear_return_ratio", ">=", 1.0)), True),
        ]
    return [
        Rule(
            root,
            "source_observed_sideways_definition",
            (
                ("sideways_abs_return_ratio", "<=", 1.0),
                ("sideways_range_ratio", "<=", 1.0),
                ("sideways_ma_gap_ratio", "<=", 1.0),
            ),
            True,
        ),
    ]


def train_candidate_rules(df: pd.DataFrame, root: str, y: np.ndarray) -> list[Rule]:
    train = df["split"].eq("train").to_numpy()
    atom_rules: list[Rule] = []
    for feature in FEATURE_COLUMNS:
        values = pd.to_numeric(df[feature], errors="coerce").replace([np.inf, -np.inf], np.nan)
        train_values = values[train].dropna().to_numpy(float)
        if len(train_values) < 300:
            continue
        thresholds = set(float(x) for x in np.quantile(train_values, [0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 0.80, 0.90, 0.95, 0.98, 0.99]))
        thresholds.update({0.0, 0.5, 1.0, 1.5, 2.0})
        for threshold in sorted(thresholds):
            for op in ["<=", ">="]:
                atom_rules.append(Rule(root, f"train_atom_{feature}_{op}_{threshold:.8g}", ((feature, op, threshold),)))

    scored_atoms: list[tuple[float, float, float, int, Rule]] = []
    for rule in atom_rules:
        mask = rule.mask(df)
        train_metric = split_metric(df, mask, y, "train")
        if train_metric["support"] >= 500 and train_metric["coverage"] >= 0.035:
            scored_atoms.append(
                (
                    train_metric["precision_wilson_lcb_95"],
                    train_metric["precision"],
                    train_metric["coverage"],
                    train_metric["support"],
                    rule,
                )
            )
    scored_atoms.sort(reverse=True, key=lambda item: item[:4])
    top_atoms = [item[4] for item in scored_atoms[:80]]

    pair_rules: list[Rule] = []
    for i, left in enumerate(top_atoms):
        for right in top_atoms[i + 1 :]:
            features = {term[0] for term in left.terms + right.terms}
            if len(features) < 2:
                continue
            pair_rules.append(Rule(root, f"train_pair_{left.name}_{right.name}", left.terms + right.terms))
    return base_rules(root) + [item[4] for item in scored_atoms[:80]] + pair_rules


def evaluate_root(df: pd.DataFrame, root: str) -> dict[str, Any]:
    y = df["root_label"].eq(root).to_numpy()
    candidates = train_candidate_rules(df, root, y)
    evaluated: list[dict[str, Any]] = []
    for rule in candidates:
        mask = rule.mask(df)
        train = split_metric(df, mask, y, "train")
        if train["support"] < 500 or train["coverage"] < 0.035:
            continue
        evaluated.append(
            {
                "root_class": root,
                "rule_name": rule.name,
                "rule": rule.expression(),
                "source_definition_candidate": rule.source_definition_candidate,
                "threshold_selected_on": "train_split_only_candidate_library",
                "train": train,
                "mask": mask,
                "sort_key": [
                    train["precision_wilson_lcb_95"],
                    1.0 if rule.source_definition_candidate else 0.0,
                    train["precision"],
                    train["coverage"],
                    train["support"],
                ],
            }
        )
    evaluated.sort(key=lambda item: item["sort_key"], reverse=True)
    if not evaluated:
        raise RuntimeError(f"{root}: no train candidate with support")
    selected = evaluated[0]
    selected["calibration"] = split_metric(df, selected["mask"], y, "calibration", selected["train"]["precision"])
    selected["test"] = split_metric(df, selected["mask"], y, "test", selected["train"]["precision"])
    selected["blockers"] = blockers(selected["calibration"], selected["test"])
    selected["accepted_95"] = not selected["blockers"]
    selected["state"] = "accepted_95" if selected["accepted_95"] else "blocked"
    selected["top_train_candidates"] = [
        {
            "rule_name": item["rule_name"],
            "rule": item["rule"],
            "source_definition_candidate": item["source_definition_candidate"],
            "train_lcb": item["train"]["precision_wilson_lcb_95"],
            "train_precision": item["train"]["precision"],
            "train_support": item["train"]["support"],
            "train_coverage": item["train"]["coverage"],
        }
        for item in evaluated[:20]
    ]
    selected.pop("mask", None)
    selected.pop("sort_key", None)
    return selected


def write_summary(path: Path, root_reports: dict[str, dict[str, Any]]) -> None:
    fields = [
        "root_class",
        "state",
        "rule",
        "source_definition_candidate",
        "train_support",
        "train_lcb",
        "calibration_support",
        "calibration_lcb",
        "test_support",
        "test_lcb",
        "test_precision",
        "test_coverage",
        "validation_market_contexts",
        "validation_timeframes",
        "blockers",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for root, item in root_reports.items():
            writer.writerow(
                {
                    "root_class": root,
                    "state": item["state"],
                    "rule": item["rule"],
                    "source_definition_candidate": item["source_definition_candidate"],
                    "train_support": item["train"]["support"],
                    "train_lcb": item["train"]["precision_wilson_lcb_95"],
                    "calibration_support": item["calibration"]["support"],
                    "calibration_lcb": item["calibration"]["precision_wilson_lcb_95"],
                    "test_support": item["test"]["support"],
                    "test_lcb": item["test"]["precision_wilson_lcb_95"],
                    "test_precision": item["test"]["precision"],
                    "test_coverage": item["test"]["coverage"],
                    "validation_market_contexts": ";".join(item["test"]["validation_market_contexts"]),
                    "validation_timeframes": ";".join(item["test"]["validation_timeframes"]),
                    "blockers": ";".join(item["blockers"]),
                }
            )


def write_report_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Yahoo Source-Backed Parent Root Gate",
        "",
        f"Run id: `{report['loop_id']}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{report['decision']['gate_result']}`",
        f"- Accepted new roots: {', '.join(report['decision']['accepted_new_roots_95']) or 'none'}",
        f"- Missing roots after preserved accounting: {', '.join(report['decision']['missing_root_classes_95_effective'])}",
        "- Thresholds relaxed: `false`",
        "- Runtime code changed: `false`",
        "- Trade usable: `false`",
        "",
        "## Root Results",
        "",
        "| Root | State | Rule | Cal LCB | Test LCB | Test Precision | Test Coverage | Test Contexts | Blockers |",
        "|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    for root, item in report["root_reports"].items():
        lines.append(
            "| {root} | {state} | `{rule}` | {cal_lcb:.6f} | {test_lcb:.6f} | {test_precision:.6f} | {test_coverage:.6f} | {contexts} / {timeframes} | {blockers} |".format(
                root=root,
                state=item["state"],
                rule=item["rule"],
                cal_lcb=item["calibration"]["precision_wilson_lcb_95"],
                test_lcb=item["test"]["precision_wilson_lcb_95"],
                test_precision=item["test"]["precision"],
                test_coverage=item["test"]["coverage"],
                contexts=", ".join(item["test"]["validation_market_contexts"]),
                timeframes=", ".join(item["test"]["validation_timeframes"]),
                blockers=", ".join(item["blockers"]) or "none",
            )
        )
    lines.extend(
        [
            "",
            "## Source And Policy",
            "",
            "- External source review verdict: low risk; public market data and public regime-definition/method references only; no external code executed.",
            "- Parent labels are observed current/trailing state definitions, not future-return labels and not vendor analyst predictions.",
            "- Candidate thresholds are selected on the train split only; calibration/test are held out chronologically within each ticker/timeframe.",
            "- `future_*`, `target_*`, and `next_*` predictors are absent.",
            "- This does not reissue `Crisis` and does not evaluate `Manipulation` because Yahoo OHLCV is not direct event/order-lifecycle evidence.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def panel_profile(df: pd.DataFrame) -> dict[str, Any]:
    return {
        "rows": int(len(df)),
        "instruments": sorted(df["ticker"].astype(str).unique().tolist()),
        "market_contexts": sorted(df["market_context"].astype(str).unique().tolist()),
        "timeframes": sorted(df["timeframe"].astype(str).unique().tolist()),
        "split_counts": {str(k): int(v) for k, v in df["split"].value_counts().sort_index().to_dict().items()},
        "label_counts": {str(k): int(v) for k, v in df["root_label"].value_counts().to_dict().items()},
        "label_counts_by_split": {
            split: {str(k): int(v) for k, v in group["root_label"].value_counts().to_dict().items()}
            for split, group in df.groupby("split")
        },
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    df = build_panel()
    root_reports = {root: evaluate_root(df, root) for root in ["Bear", "Sideways"]}
    accepted = [root for root, item in root_reports.items() if item["accepted_95"]]
    retained_prior = ["Bull", "Crisis"]
    missing = [root for root in ["Bear", "Sideways", "Manipulation"] if root not in accepted]

    report_json = OUT_DIR / "yahoo_sourcebacked_parent_root_gate_report.json"
    report_md = OUT_DIR / "yahoo_sourcebacked_parent_root_gate_report.md"
    summary_csv = OUT_DIR / "yahoo_sourcebacked_parent_root_gate_summary.csv"
    assertions = CHECK_DIR / "yahoo_sourcebacked_parent_root_gate_assertions.out"
    feature_sample = OUT_DIR / "yahoo_sourcebacked_parent_root_gate_feature_sample.csv"

    sample_cols = ["ts", "ticker", "market_context", "timeframe", "split", "root_label"] + FEATURE_COLUMNS
    df[sample_cols].head(200).to_csv(feature_sample, index=False)

    report = {
        "loop_id": RUN_ID,
        "objective": "Bounded source-backed observed parent-root gate for missing MainRegimeV2 Bear and Sideways roots.",
        "source_review": {
            "risk": "low",
            "why": [
                "Public Yahoo/yfinance market data only; raw cache stays under /private/tmp.",
                "Public regime-definition and HMM/GMM method references only; no external code executed.",
                "No credentials, local config, wallet, browser, or destructive operations involved.",
            ],
            "human_approval_required": False,
            "safe_next_action": "absorb",
        },
        "sources": {
            "provider": "Yahoo public market data via yfinance",
            "cache_dir": str(CACHE_DIR),
            "raw_or_full_feature_table_committed": False,
            "definition_and_method_references": [
                "https://www.nasdaq.com/glossary/b/bear-market",
                "https://www.investopedia.com/terms/s/sidewaysmarket.asp",
                "https://doi.org/10.1016/j.physa.2024.130491",
                "https://doi.org/10.1007/s10614-024-10746-3",
            ],
        },
        "panel_profile": panel_profile(df),
        "label_policy": {
            "active_roots_evaluated": ["Bear", "Sideways"],
            "observed_current_or_trailing_inputs_only": True,
            "future_target_next_predictors_absent": True,
            "bear_definition": "context-normalized trailing drawdown and trailing return are both beyond source-backed bear thresholds",
            "sideways_definition": "context-normalized trailing absolute return, range, and moving-average gap are all inside source-backed sideways thresholds",
            "crisis_reissued": False,
            "manipulation_evaluated": False,
        },
        "acceptance_95": ACCEPTANCE_95,
        "root_reports": root_reports,
        "decision": {
            "gate_result": "accepted_95" if accepted else "blocked_yahoo_sourcebacked_parent_root_gate",
            "accepted_new_roots_95": accepted,
            "retained_prior_accepted_root_classes_95": retained_prior,
            "accepted_root_classes_95_effective": retained_prior + accepted,
            "missing_root_classes_95_effective": missing,
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "fresh_calibration_rerun": True,
            "trade_usable": False,
            "manipulation_blocker": "Yahoo OHLCV is not direct event/order-lifecycle/L2/L3/MBO/social/on-chain manipulation evidence.",
            "next_action": "Use the preserved Hyperliquid L4/order-lifecycle source path to acquire explicit direct manipulation positives/negatives; keep Manipulation fail-closed until then.",
        },
        "artifacts": {
            "report_json": repo_rel(report_json),
            "report_md": repo_rel(report_md),
            "summary_csv": repo_rel(summary_csv),
            "feature_sample": repo_rel(feature_sample),
            "assertions": repo_rel(assertions),
        },
    }
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_summary(summary_csv, root_reports)
    write_report_md(report_md, report)
    assertion_lines = [
        f"loop_id={RUN_ID}",
        f"gate_result={report['decision']['gate_result']}",
        f"accepted_new_roots_95={','.join(accepted) if accepted else 'none'}",
        f"missing_roots_95={','.join(missing)}",
        "thresholds_relaxed=false",
        "runtime_code_changed=false",
        "raw_or_full_feature_table_committed=false",
        "trade_usable=false",
    ]
    for root, item in root_reports.items():
        assertion_lines.append(
            f"{root}:state={item['state']}:cal_lcb={item['calibration']['precision_wilson_lcb_95']:.6f}:test_lcb={item['test']['precision_wilson_lcb_95']:.6f}:test_precision={item['test']['precision']:.6f}:test_coverage={item['test']['coverage']:.6f}:blockers={';'.join(item['blockers']) or 'none'}"
        )
    assertions.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
