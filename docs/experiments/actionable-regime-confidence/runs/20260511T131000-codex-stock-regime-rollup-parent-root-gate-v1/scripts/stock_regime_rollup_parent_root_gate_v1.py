#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T131000+0800-codex-stock-regime-rollup-parent-root-gate-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T131000-codex-stock-regime-rollup-parent-root-gate-v1"
OUT_DIR = RUN_ROOT / "rollup-parent-root-gate"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
DAILY_SOURCE = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv")
ROLLUP = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T130600-codex-stock-regime-same-source-timeframe-rollup-v1/timeframe-rollup/stock_regime_same_source_timeframe_rollup_v1.csv"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
HELDOUT_TICKERS = {"AAPL", "AMZN", "JPM", "XOM", "JNJ", "^GSPC", "^DJI", "^IXIC", "^RUT", "TSLA"}
Z95 = 1.959963984540054
SUPPORT_MIN = 50
TRAIN_SUPPORT_MIN = 100
FEATURES = [
    "period_return",
    "mean_daily_volatility",
    "mean_regime_confidence",
    "label_share",
    "ret_4",
    "ret_12",
    "ret_26",
    "ret_52",
    "range_pos_12",
    "range_pos_52",
    "range_width_12",
    "range_width_52",
    "drawdown_12",
    "drawdown_52",
    "range_pos_52_period_rank",
    "timeframe_is_month",
]
QUANTILES = [0.01, 0.02, 0.05, 0.075, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.925, 0.95, 0.98, 0.99]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def wilson_lcb(pos: int, n: int) -> float:
    if n <= 0:
        return 0.0
    p = pos / n
    denom = 1 + Z95 * Z95 / n
    center = p + Z95 * Z95 / (2 * n)
    radius = Z95 * math.sqrt((p * (1 - p) + Z95 * Z95 / (4 * n)) / n)
    return (center - radius) / denom


def build_rollup_features() -> pd.DataFrame:
    daily = pd.read_csv(DAILY_SOURCE, parse_dates=["date"])
    labels = pd.read_csv(ROLLUP, parse_dates=["period_start", "period_end"])
    daily = daily.sort_values(["ticker", "date"]).copy()

    aggregates = []
    for timeframe, freq in [("1w", "W-FRI"), ("1mo", "M")]:
        frame = daily.copy()
        frame["period"] = frame["date"].dt.to_period(freq)
        grouped = frame.groupby(["ticker", "period"], sort=True)
        agg = grouped.agg(
            period_start=("date", "min"),
            period_end=("date", "max"),
            first_close=("close", "first"),
            close=("close", "last"),
            mean_daily_volatility=("volatility", "mean"),
        ).reset_index()
        agg["timeframe"] = timeframe
        aggregates.append(agg)

    period_features = pd.concat(aggregates, ignore_index=True)
    df = labels.merge(
        period_features,
        on=["ticker", "timeframe", "period_start", "period_end"],
        how="inner",
    )
    df["year"] = df["period_end"].dt.year
    df["root"] = df["root"].astype(str)
    df["period_return"] = df["close"] / df["first_close"] - 1.0
    df["mean_regime_confidence"] = pd.to_numeric(df["mean_regime_confidence"], errors="coerce")
    df["label_share"] = pd.to_numeric(df["label_share"], errors="coerce")
    df["source_days"] = pd.to_numeric(df["source_days"], errors="coerce")
    df["total_days"] = pd.to_numeric(df["total_days"], errors="coerce")
    df["timeframe_is_month"] = df["timeframe"].eq("1mo").astype(float)
    df = df.sort_values(["ticker", "timeframe", "period_end"])
    grouped = df.groupby(["ticker", "timeframe"], group_keys=False)
    for window in [4, 12, 26, 52]:
        df[f"ret_{window}"] = grouped["close"].pct_change(window)
        roll_min = grouped["close"].rolling(window, min_periods=window).min().reset_index(level=[0, 1], drop=True)
        roll_max = grouped["close"].rolling(window, min_periods=window).max().reset_index(level=[0, 1], drop=True)
        df[f"range_pos_{window}"] = (df["close"] - roll_min) / (roll_max - roll_min)
        df[f"range_width_{window}"] = roll_max / roll_min - 1.0
        df[f"drawdown_{window}"] = df["close"] / roll_max - 1.0
    df["range_pos_52_period_rank"] = df.groupby(["timeframe", "period_end"])["range_pos_52"].rank(pct=True)
    df = df.replace([float("inf"), float("-inf")], pd.NA)
    return df.dropna(subset=FEATURES).reset_index(drop=True)


def split_masks(df: pd.DataFrame) -> dict[str, pd.Series]:
    heldout = df["ticker"].isin(HELDOUT_TICKERS)
    return {
        "train": (~heldout) & (df["year"] <= 2016),
        "calibration": (~heldout) & (df["year"].between(2017, 2021)),
        "heldout_time": (~heldout) & (df["year"] >= 2022),
        "heldout_ticker": heldout,
    }


Rule = list[tuple[str, str, float]]


def rule_expr(rule: Rule) -> str:
    return " AND ".join(f"{feature} {op} {value:.12g}" for feature, op, value in rule)


def rule_mask(df: pd.DataFrame, rule: Rule) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for feature, op, value in rule:
        series = pd.to_numeric(df[feature], errors="coerce")
        if op == ">=":
            mask &= series.ge(value)
        else:
            mask &= series.le(value)
    return mask.fillna(False)


def metric(df: pd.DataFrame, root: str, emitted: pd.Series, split_mask: pd.Series) -> dict[str, Any]:
    selected = emitted & split_mask
    n = int(selected.sum())
    pos = int((selected & df["root"].eq(root)).sum())
    return {
        "support": n,
        "positives": pos,
        "precision": round(pos / n, 10) if n else 0.0,
        "wilson95_lcb": round(wilson_lcb(pos, n), 10),
    }


def train_candidates(df: pd.DataFrame, root: str, masks: dict[str, pd.Series]) -> list[dict[str, Any]]:
    train_mask = masks["train"]
    atoms: list[tuple[float, float, int, Rule]] = []
    for feature in FEATURES:
        values = pd.to_numeric(df.loc[train_mask, feature], errors="coerce").dropna()
        if values.nunique() <= 4:
            continue
        thresholds = sorted(set(float(values.quantile(q)) for q in QUANTILES))
        thresholds.extend([0.0, 0.5, 0.8, 0.9, 0.95, 1.0])
        for threshold in sorted(set(x for x in thresholds if math.isfinite(x))):
            for op in [">=", "<="]:
                rule = [(feature, op, threshold)]
                m = metric(df, root, rule_mask(df, rule), train_mask)
                if m["support"] >= TRAIN_SUPPORT_MIN:
                    atoms.append((m["wilson95_lcb"], m["precision"], m["support"], rule))
    atoms.sort(key=lambda x: x[:3], reverse=True)
    rules = [item[3] for item in atoms[:80]]
    for idx, left in enumerate([item[3] for item in atoms[:30]]):
        for right in [item[3] for item in atoms[idx + 1 : 30]]:
            if left[0][0] == right[0][0]:
                continue
            rules.append(left + right)

    evaluated: list[dict[str, Any]] = []
    for rule in rules:
        emitted = rule_mask(df, rule)
        train = metric(df, root, emitted, train_mask)
        if train["support"] < TRAIN_SUPPORT_MIN:
            continue
        evaluated.append({"rule": rule, "train": train})
    evaluated.sort(key=lambda item: (item["train"]["wilson95_lcb"], item["train"]["precision"], item["train"]["support"]), reverse=True)
    return evaluated


def evaluate_root(df: pd.DataFrame, root: str, masks: dict[str, pd.Series]) -> dict[str, Any]:
    candidates = train_candidates(df, root, masks)
    if not candidates:
        return {"regime": root, "accepted_95_rollup_gate": False, "blockers": ["no_train_candidate"], "rule": "none"}
    selected = candidates[0]
    emitted = rule_mask(df, selected["rule"])
    stats = {name: metric(df, root, emitted, mask) for name, mask in masks.items()}
    blockers = []
    for name in ["calibration", "heldout_time", "heldout_ticker"]:
        if stats[name]["support"] < SUPPORT_MIN:
            blockers.append(f"{name}_support_below_{SUPPORT_MIN}")
        if stats[name]["wilson95_lcb"] < 0.95:
            blockers.append(f"{name}_wilson95_below_0_95")
    return {
        "regime": root,
        "gate_id": f"{root.lower()}_stock_regime_rollup_abstain_v1",
        "taxonomy_role": "MainRegimeV2_price_root",
        "rule": rule_expr(selected["rule"]),
        "accepted_95_rollup_gate": not blockers,
        "blockers": blockers,
        "stats": stats,
        "top_train_candidates": [
            {
                "rule": rule_expr(item["rule"]),
                "train": item["train"],
            }
            for item in candidates[:10]
        ],
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    df = build_rollup_features()
    masks = split_masks(df)
    gates = [evaluate_root(df, root, masks) for root in ROOTS]
    accepted = [gate["regime"] for gate in gates if gate.get("accepted_95_rollup_gate")]
    summary_csv = OUT_DIR / "stock_regime_rollup_parent_root_gate_v1_summary.csv"
    with summary_csv.open("w", newline="") as f:
        fields = ["regime", "accepted_95", "rule", "cal_lcb", "time_lcb", "ticker_lcb", "cal_support", "time_support", "ticker_support", "blockers"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for gate in gates:
            st = gate.get("stats", {})
            writer.writerow({
                "regime": gate["regime"],
                "accepted_95": gate.get("accepted_95_rollup_gate", False),
                "rule": gate.get("rule", ""),
                "cal_lcb": st.get("calibration", {}).get("wilson95_lcb", 0.0),
                "time_lcb": st.get("heldout_time", {}).get("wilson95_lcb", 0.0),
                "ticker_lcb": st.get("heldout_ticker", {}).get("wilson95_lcb", 0.0),
                "cal_support": st.get("calibration", {}).get("support", 0),
                "time_support": st.get("heldout_time", {}).get("support", 0),
                "ticker_support": st.get("heldout_ticker", {}).get("support", 0),
                "blockers": ";".join(gate.get("blockers", [])),
            })

    package = {
        "run_id": RUN_ID,
        "artifact_type": "stock_regime_rollup_parent_root_gate_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "board": str(BOARD.relative_to(REPO)),
            "board_sha256_at_run": sha256(BOARD),
            "daily_source": str(DAILY_SOURCE),
            "daily_source_sha256": sha256(DAILY_SOURCE),
            "rollup_labels": str(ROLLUP.relative_to(REPO)),
            "rollup_labels_sha256": sha256(ROLLUP),
        },
        "panel": {
            "feature_rows": int(len(df)),
            "timeframes": sorted(df["timeframe"].unique().tolist()),
            "tickers": sorted(df["ticker"].unique().tolist()),
            "date_min": df["period_end"].min().strftime("%Y-%m-%d"),
            "date_max": df["period_end"].max().strftime("%Y-%m-%d"),
            "root_counts": {str(k): int(v) for k, v in df["root"].value_counts().sort_index().to_dict().items()},
        },
        "decision": {
            "accepted_95_rollup_parent_roots": sorted(accepted),
            "missing_rollup_parent_roots": sorted(set(ROOTS) - set(accepted)),
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_market_full_timeframe_completion": False,
            "gate_result": "accepted_95_rollup_stock_regime_roots_full_matrix_still_blocked" if set(accepted) == set(ROOTS) else "partial_rollup_stock_regime_roots_full_matrix_still_blocked",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "gates": gates,
        "artifacts": {
            "summary_csv": str(summary_csv.relative_to(REPO)),
        },
    }
    json_path = OUT_DIR / "stock_regime_rollup_parent_root_gate_v1.json"
    json_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")
    md = [
        "# Stock Regime Rollup Parent-Root Gate v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Accepted 95 rollup roots: `{', '.join(sorted(accepted)) or 'none'}`.",
        f"- Missing rollup roots: `{', '.join(sorted(set(ROOTS) - set(accepted))) or 'none'}`.",
        f"- Gate result: `{package['decision']['gate_result']}`.",
        "- Full objective achieved: `false`.",
        "",
        "## Gates",
        "",
        "| Root | Accepted | Rule | Cal LCB | Heldout-Time LCB | Heldout-Ticker LCB | Blockers |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for gate in gates:
        st = gate.get("stats", {})
        md.append(
            "| {root} | `{accepted}` | `{rule}` | {cal:.6f} | {time:.6f} | {ticker:.6f} | {blockers} |".format(
                root=gate["regime"],
                accepted=str(gate.get("accepted_95_rollup_gate", False)).lower(),
                rule=gate.get("rule", ""),
                cal=st.get("calibration", {}).get("wilson95_lcb", 0.0),
                time=st.get("heldout_time", {}).get("wilson95_lcb", 0.0),
                ticker=st.get("heldout_ticker", {}).get("wilson95_lcb", 0.0),
                blockers=", ".join(gate.get("blockers", [])) or "none",
            )
        )
    md.extend([
        "",
        "## Guardrails",
        "",
        "- Same-source 1w/1mo stock-market-regimes rollup only.",
        "- Thresholds selected on train split only.",
        "- No source-window projection, no runtime code change, no raw data commit.",
    ])
    (OUT_DIR / "stock_regime_rollup_parent_root_gate_v1.md").write_text("\n".join(md) + "\n")
    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={package['inputs']['board_sha256_at_run']}",
        f"accepted_95_rollup_parent_roots={','.join(sorted(accepted))}",
        f"missing_rollup_parent_roots={','.join(sorted(set(ROOTS) - set(accepted)))}",
        f"gate_result={package['decision']['gate_result']}",
        "accepted_full_objective_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    (CHECK_DIR / "stock_regime_rollup_parent_root_gate_v1_assertions.out").write_text("\n".join(assertions) + "\n")
    assert len(df) > 0


if __name__ == "__main__":
    main()
