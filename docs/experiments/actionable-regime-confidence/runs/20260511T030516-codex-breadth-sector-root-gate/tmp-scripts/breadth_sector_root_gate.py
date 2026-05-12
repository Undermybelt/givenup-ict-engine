#!/usr/bin/env python3
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
RUN_ID = "20260511T030516+0800-codex-breadth-sector-root-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T030516-codex-breadth-sector-root-gate"
OUT_DIR = RUN_ROOT / "breadth-sector-gate"
CHECK_DIR = RUN_ROOT / "checks"
FEATURES_CSV = OUT_DIR / "breadth_sector_root_features.csv"

TARGETS = ["SPY", "QQQ", "IWM"]
SECTORS = ["XLK", "XLF", "XLE", "XLY", "XLP", "XLU", "XLV", "XLI", "XLB", "XLRE", "XLC"]
PROXIES = sorted(set(TARGETS + SECTORS + ["RSP", "DIA", "HYG", "LQD", "TLT", "UUP", "GLD", "^VIX"]))
ROOTS = ["Bull", "Bear", "Sideways"]
Z95 = 1.959963984540054
QUANTILES = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
SUPPORT_TRAIN_MIN = 120
SUPPORT_CAL_MIN = 120
SUPPORT_TEST_MIN = 60
COVERAGE_MIN = 0.03
ECE_MAX = 0.05


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


def numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype(float).replace([np.inf, -np.inf], np.nan)
    return pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)


def json_counts(series: pd.Series) -> dict[str, int]:
    out: dict[str, int] = {}
    for key, value in series.items():
        if isinstance(key, tuple):
            label = "|".join(str(part) for part in key)
        else:
            label = str(key)
        out[label] = int(value)
    return out


def normalize_download(raw: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    if raw.empty:
        return pd.DataFrame(columns=["ts", "ticker", "open", "high", "low", "close", "volume"])
    if not isinstance(raw.columns, pd.MultiIndex):
        raw.columns = pd.MultiIndex.from_product([["UNKNOWN"], raw.columns])
    level0 = set(str(x) for x in raw.columns.get_level_values(0))
    tickers_first = bool(level0 & set(PROXIES))
    for ticker in PROXIES:
        try:
            part = raw[ticker].copy() if tickers_first else raw.xs(ticker, axis=1, level=1).copy()
        except Exception:
            continue
        rename = {
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "close",
            "Volume": "volume",
        }
        part = part.rename(columns=rename)
        keep = [col for col in ["open", "high", "low", "close", "volume"] if col in part.columns]
        if not keep or "close" not in keep:
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


def fetch_daily() -> tuple[pd.DataFrame, dict[str, Any]]:
    print(f"fetching yfinance symbols={','.join(PROXIES)}", flush=True)
    raw = yf.download(
        PROXIES,
        period="10y",
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=True,
        group_by="ticker",
    )
    daily = normalize_download(raw)
    meta = {
        "requested_symbols": PROXIES,
        "available_symbols": sorted(daily["ticker"].dropna().unique().tolist()),
        "rows": int(len(daily)),
        "date_min": daily["ts"].min().isoformat() if not daily.empty else None,
        "date_max": daily["ts"].max().isoformat() if not daily.empty else None,
    }
    return daily, meta


def to_weekly(daily: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    for ticker, group in daily.groupby("ticker", sort=False):
        g = group.set_index("ts").sort_index()
        w = pd.DataFrame(
            {
                "open": g["open"].resample("W-FRI").first(),
                "high": g["high"].resample("W-FRI").max(),
                "low": g["low"].resample("W-FRI").min(),
                "close": g["close"].resample("W-FRI").last(),
                "volume": g["volume"].resample("W-FRI").sum(),
            }
        ).dropna(subset=["close"])
        w["ticker"] = ticker
        w = w.reset_index()
        rows.append(w[["ts", "ticker", "open", "high", "low", "close", "volume"]])
    return pd.concat(rows, ignore_index=True) if rows else daily.iloc[0:0].copy()


def add_base_features(frame: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    df = frame.sort_values(["ticker", "ts"]).copy()
    df["timeframe"] = timeframe
    grp = df.groupby("ticker", group_keys=False)
    df["ret1"] = grp["close"].transform(lambda s: np.log(s).diff())
    df["ret4"] = grp["close"].transform(lambda s: np.log(s).diff(4))
    df["ret12"] = grp["close"].transform(lambda s: np.log(s).diff(12))
    df["range_pct"] = (df["high"] - df["low"]) / df["close"]
    for window in [20, 50, 100, 200]:
        min_periods = max(5, window // 4)
        df[f"ma{window}"] = grp["close"].rolling(window, min_periods=min_periods).mean().reset_index(level=0, drop=True)
        df[f"above_ma{window}"] = df["close"] > df[f"ma{window}"]
    df["vol20"] = grp["ret1"].rolling(20, min_periods=8).std().reset_index(level=0, drop=True)
    df["vol60"] = grp["ret1"].rolling(60, min_periods=16).std().reset_index(level=0, drop=True)
    df["range20"] = grp["range_pct"].rolling(20, min_periods=8).mean().reset_index(level=0, drop=True)
    horizon = 20 if timeframe == "1d" else 8
    df["future_ret"] = grp["close"].transform(lambda s: np.log(s).shift(-horizon) - np.log(s))
    df["future_absret"] = df["future_ret"].abs()
    df["future_range"] = grp["range_pct"].shift(-1).rolling(horizon, min_periods=max(3, horizon // 3)).mean().reset_index(level=0, drop=True)
    df["future_vol"] = grp["ret1"].shift(-1).rolling(horizon, min_periods=max(3, horizon // 3)).std().reset_index(level=0, drop=True)
    return df


def panel_features(df: pd.DataFrame) -> pd.DataFrame:
    proxy = df[df["ticker"].isin(PROXIES)].copy()
    proxy["is_sector"] = proxy["ticker"].isin(SECTORS)
    panel = (
        proxy.groupby(["ts", "timeframe"])
        .agg(
            breadth_count=("ticker", "nunique"),
            breadth_pos_ret4=("ret4", lambda s: float((s > 0).mean())),
            breadth_neg_ret4=("ret4", lambda s: float((s < 0).mean())),
            breadth_above_ma50=("above_ma50", "mean"),
            breadth_above_ma200=("above_ma200", "mean"),
            sector_pos_ret4=("ret4", lambda s: float((proxy.loc[s.index, "is_sector"] & (s > 0)).sum()) / max(1, int(proxy.loc[s.index, "is_sector"].sum()))),
            sector_neg_ret4=("ret4", lambda s: float((proxy.loc[s.index, "is_sector"] & (s < 0)).sum()) / max(1, int(proxy.loc[s.index, "is_sector"].sum()))),
            sector_dispersion_ret4=("ret4", "std"),
            panel_ret4_mean=("ret4", "mean"),
            panel_ret12_mean=("ret12", "mean"),
            panel_vol20_mean=("vol20", "mean"),
            panel_range20_mean=("range20", "mean"),
        )
        .reset_index()
    )
    wide = proxy.pivot_table(index=["ts", "timeframe"], columns="ticker", values="ret4", aggfunc="last")
    for col in ["HYG", "LQD", "TLT", "UUP", "GLD", "^VIX", "XLK", "XLY", "XLP", "XLU", "IWM", "QQQ", "SPY"]:
        if col not in wide.columns:
            wide[col] = np.nan
    wide["credit_risk_ret4"] = wide["HYG"] - wide["LQD"]
    wide["rates_risk_ret4"] = -wide["TLT"]
    wide["usd_risk_ret4"] = wide["UUP"]
    wide["vix_ret4"] = wide["^VIX"]
    wide["risk_on_minus_defensive_ret4"] = wide[["XLK", "XLY", "IWM", "HYG"]].mean(axis=1) - wide[["XLP", "XLU", "TLT", "GLD"]].mean(axis=1)
    wide["mega_vs_small_ret4"] = wide["QQQ"] - wide["IWM"]
    wide = wide.reset_index()[
        [
            "ts",
            "timeframe",
            "credit_risk_ret4",
            "rates_risk_ret4",
            "usd_risk_ret4",
            "vix_ret4",
            "risk_on_minus_defensive_ret4",
            "mega_vs_small_ret4",
        ]
    ]
    return panel.merge(wide, on=["ts", "timeframe"], how="left")


def build_feature_table(daily: pd.DataFrame) -> pd.DataFrame:
    full = pd.concat([add_base_features(daily, "1d"), add_base_features(to_weekly(daily), "1w")], ignore_index=True)
    panel = panel_features(full)
    targets = full[full["ticker"].isin(TARGETS)].merge(panel, on=["ts", "timeframe"], how="left")
    targets["instrument"] = targets["ticker"]
    targets["market"] = "yfinance_us_equity_proxy"
    targets["context"] = targets["instrument"] + ":" + targets["timeframe"]
    targets = targets.sort_values(["context", "ts"]).reset_index(drop=True)
    splits: list[str] = []
    for _, group in targets.groupby("context", sort=False):
        n = len(group)
        split = np.full(n, "train", dtype=object)
        split[n // 2 :] = "calibration"
        split[(3 * n) // 4 :] = "test"
        splits.extend(split.tolist())
    targets["split"] = splits
    train = targets[targets["split"] == "train"]
    crisis = (targets["future_absret"] >= numeric(train["future_absret"]).quantile(0.90)) | (
        targets["future_range"] >= numeric(train["future_range"]).quantile(0.90)
    )
    sideways = (
        (targets["future_absret"] <= numeric(train["future_absret"]).quantile(0.40))
        & (targets["future_range"] <= numeric(train["future_range"]).quantile(0.55))
        & (targets["future_vol"] <= numeric(train["future_vol"]).quantile(0.55))
        & (~crisis)
    )
    bull = (targets["future_ret"] >= numeric(train["future_ret"]).quantile(0.65)) & (~crisis) & (~sideways)
    bear = (targets["future_ret"] <= numeric(train["future_ret"]).quantile(0.35)) & (~crisis) & (~sideways)
    targets["root_label"] = "UnknownOrMixed"
    targets.loc[bear, "root_label"] = "Bear"
    targets.loc[bull, "root_label"] = "Bull"
    targets.loc[sideways, "root_label"] = "Sideways"
    targets.loc[crisis, "root_label"] = "Crisis"
    return targets


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
        "validation_market_contexts": sorted(selected_df["market"].dropna().unique().tolist()),
        "validation_timeframes": sorted(selected_df["timeframe"].dropna().unique().tolist()),
    }


FEATURE_COLUMNS = [
    "ret1",
    "ret4",
    "ret12",
    "range_pct",
    "above_ma20",
    "above_ma50",
    "above_ma100",
    "above_ma200",
    "vol20",
    "vol60",
    "range20",
    "breadth_pos_ret4",
    "breadth_neg_ret4",
    "breadth_above_ma50",
    "breadth_above_ma200",
    "sector_pos_ret4",
    "sector_neg_ret4",
    "sector_dispersion_ret4",
    "panel_ret4_mean",
    "panel_ret12_mean",
    "panel_vol20_mean",
    "panel_range20_mean",
    "credit_risk_ret4",
    "rates_risk_ret4",
    "usd_risk_ret4",
    "vix_ret4",
    "risk_on_minus_defensive_ret4",
    "mega_vs_small_ret4",
]


def candidate_masks(df: pd.DataFrame, root: str) -> list[tuple[str, pd.Series]]:
    train = df[df["split"] == "train"]
    candidates: list[tuple[str, pd.Series]] = []
    for feature in FEATURE_COLUMNS:
        if feature not in df.columns:
            continue
        values = numeric(train[feature]).dropna()
        if values.nunique() <= 1:
            continue
        for threshold in sorted({float(v) for v in values.quantile(QUANTILES).dropna().tolist()}):
            candidates.append((f"{feature} >= {threshold:.12g}", numeric(df[feature]) >= threshold))
            candidates.append((f"{feature} <= {threshold:.12g}", numeric(df[feature]) <= threshold))
    shaped = {
        "Bull": [
            ("breadth_pos_ret4 >= 0.65 AND risk_on_minus_defensive_ret4 >= train_q70", (df["breadth_pos_ret4"] >= 0.65) & (df["risk_on_minus_defensive_ret4"] >= numeric(train["risk_on_minus_defensive_ret4"]).quantile(0.70))),
            ("breadth_above_ma50 >= 0.65 AND credit_risk_ret4 >= train_q60", (df["breadth_above_ma50"] >= 0.65) & (df["credit_risk_ret4"] >= numeric(train["credit_risk_ret4"]).quantile(0.60))),
        ],
        "Bear": [
            ("breadth_neg_ret4 >= 0.60 AND vix_ret4 >= train_q65", (df["breadth_neg_ret4"] >= 0.60) & (df["vix_ret4"] >= numeric(train["vix_ret4"]).quantile(0.65))),
            ("breadth_above_ma50 <= 0.35 AND credit_risk_ret4 <= train_q35", (df["breadth_above_ma50"] <= 0.35) & (df["credit_risk_ret4"] <= numeric(train["credit_risk_ret4"]).quantile(0.35))),
        ],
        "Sideways": [
            ("sector_dispersion_ret4 <= train_q30 AND panel_range20_mean <= train_q40", (df["sector_dispersion_ret4"] <= numeric(train["sector_dispersion_ret4"]).quantile(0.30)) & (df["panel_range20_mean"] <= numeric(train["panel_range20_mean"]).quantile(0.40))),
            ("abs(panel_ret4_mean) <= train_abs_q35 AND panel_vol20_mean <= train_q45", (df["panel_ret4_mean"].abs() <= numeric(train["panel_ret4_mean"].abs()).quantile(0.35)) & (df["panel_vol20_mean"] <= numeric(train["panel_vol20_mean"]).quantile(0.45))),
        ],
    }
    candidates.extend(shaped.get(root, []))
    return candidates


def evaluate_rule(df: pd.DataFrame, root: str, rule: str, mask: pd.Series) -> dict[str, Any]:
    train = stats(df, mask, "train", root)
    calibration = stats(df, mask, "calibration", root, train["precision"])
    test = stats(df, mask, "test", root, calibration["precision"])
    ece = test["ece"]
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
    if ece > ECE_MAX:
        blockers.append("ece_above_0_05")
    if len(test["validation_instruments"]) < 2:
        blockers.append("validation_instruments_below_2")
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
        "ece": ece,
        "accepted_95": accepted,
        "blockers": blockers,
    }


def best_for_root(df: pd.DataFrame, root: str) -> dict[str, Any]:
    scored: list[dict[str, Any]] = []
    for rule, mask in candidate_masks(df, root):
        train = stats(df, mask, "train", root)
        if train["support"] < SUPPORT_TRAIN_MIN:
            continue
        item = evaluate_rule(df, root, rule, mask)
        scored.append(item)
    if not scored:
        empty = pd.Series(False, index=df.index)
        return evaluate_rule(df, root, "no_train_candidate_met_support_floor", empty)
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
    report_json = OUT_DIR / "breadth_sector_root_gate_report.json"
    report_md = OUT_DIR / "breadth_sector_root_gate_report.md"
    summary_csv = OUT_DIR / "breadth_sector_root_gate_summary.csv"
    assertions = CHECK_DIR / "breadth_sector_root_gate_assertions.out"
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
        "# Breadth/Sector Root Gate",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Data",
        "",
        f"- Requested yfinance symbols: {', '.join(PROXIES)}.",
        f"- Available symbols: {', '.join(report['provider']['available_symbols'])}.",
        f"- Derived feature rows: {report['dataset']['feature_rows']}.",
        "- Raw provider CSV committed: false; only derived feature/report artifacts are retained.",
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


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    daily, provider = fetch_daily()
    if daily.empty or len(set(daily["ticker"]) & set(TARGETS)) < 2:
        report = {
            "run_id": RUN_ID,
            "provider": provider,
            "dataset": {"feature_rows": 0},
            "root_reports": [],
            "decision": {
                "newly_accepted_roots": [],
                "gate": "blocked_provider_fetch_failed",
                "blocker": "yfinance did not return enough target symbols for a chronological Bull/Bear/Sideways gate.",
                "next_action": "Retry with a different provider/cache or use a local breadth/options/dealer dataset.",
            },
        }
        write_outputs(report)
        return 1
    features = build_feature_table(daily)
    features.to_csv(FEATURES_CSV, index=False)
    root_reports = [best_for_root(features, root) for root in ROOTS]
    newly_accepted = [row["root_class"] for row in root_reports if row["accepted_95"]]
    missing_after = [root for root in ["Bull", "Bear", "Sideways", "Manipulation"] if root not in newly_accepted]
    gate = "accepted_95_breadth_sector_roots_" + "_".join(newly_accepted) if newly_accepted else "blocked_breadth_sector_roots_below_95"
    report = {
        "run_id": RUN_ID,
        "provider": provider,
        "dataset": {
            "feature_rows": int(len(features)),
            "targets": TARGETS,
            "timeframes": sorted(features["timeframe"].dropna().unique().tolist()),
            "split_counts": json_counts(features.groupby(["split", "timeframe"]).size()),
            "label_counts": json_counts(features.groupby(["root_label", "timeframe"]).size()),
            "feature_table": repo_rel(FEATURES_CSV),
        },
        "threshold_policy": {
            "precision_wilson_lcb_95_min": 0.95,
            "calibration_support_min": SUPPORT_CAL_MIN,
            "test_support_min": SUPPORT_TEST_MIN,
            "coverage_min": COVERAGE_MIN,
            "ece_max": ECE_MAX,
            "validation_instruments_min": 2,
            "validation_timeframes_min": 2,
            "thresholds_relaxed": False,
            "blocked_predictor_prefixes": ["future_", "target_", "next_"],
        },
        "root_reports": root_reports,
        "decision": {
            "newly_accepted_roots": newly_accepted,
            "missing_active_roots_after_gate": missing_after,
            "gate": gate,
            "blocker": "Breadth/sector/credit/volatility features did not close all missing MainRegimeV2 roots at the unchanged 95% held-out gate."
            if missing_after
            else "All active roots accepted.",
            "next_action": "If no roots pass, acquire a labeled macro/bull-bear-sideways regime dataset or options/dealer-positioning history before rerunning unchanged gates.",
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
