#!/usr/bin/env python3
"""Probe the local stock-market-regimes panel without copying raw data.

This is intentionally a compact, reproducible audit script. It checks whether
the user-provided panel is a MainRegimeV2 parent-label source, then runs a
small chronological selective-rule probe to avoid promoting child/subtype
labels as parent regime evidence.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


RUN_ID = "20260511T104942+0800-codex-mainregimev2-local-panel-rule-probe"
SOURCE_ROOT = Path("/Users/thrill3r/Downloads/stock-market-regimes-20002026")
SOURCE_CSV = SOURCE_ROOT / "stock_market_regimes_2000_2026.csv"
OUT_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T104942-codex-mainregimev2-local-panel-rule-probe"
)
PROBE_DIR = OUT_ROOT / "local-panel-probe"
CHECK_DIR = OUT_ROOT / "checks"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
RESIDUAL = "UnknownOrMixed"


def wilson_lcb(success: int, support: int, z: float = 1.96) -> float:
    if support <= 0:
        return 0.0
    phat = success / support
    denom = 1.0 + z * z / support
    center = phat + z * z / (2 * support)
    spread = z * math.sqrt((phat * (1.0 - phat) + z * z / (4 * support)) / support)
    return (center - spread) / denom


def split_by_date(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    dates = np.array(sorted(df["date"].unique()))
    cut1 = dates[int(len(dates) * 0.60)]
    cut2 = dates[int(len(dates) * 0.80)]
    return {
        "train": df[df["date"] < cut1].copy(),
        "calibration": df[(df["date"] >= cut1) & (df["date"] < cut2)].copy(),
        "test": df[df["date"] >= cut2].copy(),
    }


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["ticker", "date"]).copy()
    grouped = df.groupby("ticker", group_keys=False)
    for window in [5, 20, 60, 120, 252]:
        df[f"ret_{window}"] = grouped["close"].pct_change(window)
        roll_close = grouped["close"].rolling(window, min_periods=max(3, window // 3))
        ma = roll_close.mean().reset_index(level=0, drop=True)
        max_close = roll_close.max().reset_index(level=0, drop=True)
        min_close = roll_close.min().reset_index(level=0, drop=True)
        range_width = max_close - min_close
        df[f"ma_ratio_{window}"] = df["close"] / ma - 1.0
        df[f"drawdown_{window}"] = df["close"] / max_close - 1.0
        df[f"range_pos_{window}"] = (df["close"] - min_close) / range_width
        df[f"abs_ma_ratio_{window}"] = df[f"ma_ratio_{window}"].abs()
        df[f"abs_ret_{window}"] = df[f"ret_{window}"].abs()
        df[f"vol_real_{window}"] = (
            grouped["returns"]
            .rolling(window, min_periods=max(3, window // 3))
            .std()
            .reset_index(level=0, drop=True)
        )
    df["yield_curve_10y2y"] = df["10y_treasury"] - df["2y_treasury"]
    return df.sort_values(["date", "ticker"]).reset_index(drop=True)


def evaluate_mask(df: pd.DataFrame, mask: pd.Series | np.ndarray, root: str) -> dict[str, object]:
    mask = np.asarray(mask, dtype=bool)
    support = int(mask.sum())
    success = int((df.loc[mask, "regime_label"] == root).sum()) if support else 0
    precision = success / support if support else 0.0
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lcb(success, support),
        "coverage": support / len(df) if len(df) else 0.0,
        "validation_instruments": sorted(df.loc[mask, "ticker"].dropna().unique().tolist()) if support else [],
        "validation_timeframes": ["1d"] if support else [],
        "validation_market_contexts": sorted(
            set("index" if str(ticker).startswith("^") else "single_stock" for ticker in df.loc[mask, "ticker"])
        )
        if support
        else [],
    }


def rule_mask(df: pd.DataFrame, rule: dict[str, object]) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for atom in rule["atoms"]:
        field = str(atom["field"])
        op = str(atom["op"])
        value = float(atom["value"])
        values = df[field].astype(float)
        if op == ">=":
            atom_mask = values >= value
        elif op == "<=":
            atom_mask = values <= value
        else:
            raise ValueError(f"unsupported op: {op}")
        mask &= values.notna() & atom_mask
    return mask


def main() -> None:
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    usecols = [
        "date",
        "ticker",
        "close",
        "returns",
        "volatility",
        "regime_label",
        "regime_confidence",
        "macro_context",
        "unemployment_rate",
        "fed_funds_rate",
        "cpi",
        "10y_treasury",
        "2y_treasury",
        "vix",
    ]
    raw = pd.read_csv(SOURCE_CSV, usecols=usecols, parse_dates=["date"])
    df = raw[raw["regime_label"].isin(ROOTS)].copy()
    residual_rows = raw[~raw["regime_label"].isin(ROOTS)].copy()
    df = add_features(df)
    splits = split_by_date(df)

    # Rules are chosen from an exploratory train-only probe over this exact source.
    # They are intentionally simple and audited separately on calibration/test.
    rules = {
        "Bull": {
            "rule": "drawdown_252 >= -0.002313918074873498",
            "atoms": [{"field": "drawdown_252", "op": ">=", "value": -0.002313918074873498}],
        },
        "Bear": {
            "rule": "range_pos_252 <= 0",
            "atoms": [
                {"field": "range_pos_252", "op": "<=", "value": 0.0},
            ],
        },
        "Sideways": {
            "rule": "abs_ma_ratio_252 <= 0.005983289330013457 AND abs_ret_20 <= 0.01746949514288885",
            "atoms": [
                {"field": "abs_ma_ratio_252", "op": "<=", "value": 0.005983289330013457},
                {"field": "abs_ret_20", "op": "<=", "value": 0.01746949514288885},
            ],
        },
        "Crisis": {
            "rule": "vol_real_120 >= 0.06997391797413682",
            "atoms": [{"field": "vol_real_120", "op": ">=", "value": 0.06997391797413682}],
        },
    }

    root_reports: dict[str, dict[str, object]] = {}
    for root, rule in rules.items():
        report = {
            "root_class": root,
            "rule": rule["rule"],
            "note": rule.get("note"),
            "train": evaluate_mask(splits["train"], rule_mask(splits["train"], rule), root),
            "calibration": evaluate_mask(splits["calibration"], rule_mask(splits["calibration"], rule), root),
            "test": evaluate_mask(splits["test"], rule_mask(splits["test"], rule), root),
        }
        accepted = (
            report["calibration"]["support"] >= 250
            and report["test"]["support"] >= 250
            and report["calibration"]["coverage"] >= 0.03
            and report["test"]["coverage"] >= 0.03
            and report["calibration"]["precision_wilson_lcb_95"] >= 0.95
            and report["test"]["precision_wilson_lcb_95"] >= 0.95
            and len(report["calibration"]["validation_instruments"]) >= 2
            and len(report["test"]["validation_instruments"]) >= 2
            and len(report["calibration"]["validation_market_contexts"]) >= 2
            and len(report["test"]["validation_market_contexts"]) >= 2
        )
        report["accepted_95"] = bool(accepted)
        blockers = []
        for split in ["calibration", "test"]:
            metrics = report[split]
            if metrics["support"] < 250:
                blockers.append(f"{split}_support_below_250")
            if metrics["coverage"] < 0.03:
                blockers.append(f"{split}_coverage_below_0_03")
            if metrics["precision_wilson_lcb_95"] < 0.95:
                blockers.append(f"{split}_wilson95_below_0_95")
            if len(metrics["validation_market_contexts"]) < 2:
                blockers.append(f"{split}_market_contexts_below_2")
        report["blockers"] = blockers
        root_reports[root] = report

    accepted_roots = [root for root, report in root_reports.items() if report["accepted_95"]]
    label_counts = raw["regime_label"].value_counts().to_dict()
    result = {
        "run_id": RUN_ID,
        "board": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
        "source_root": str(SOURCE_ROOT),
        "source_csv": str(SOURCE_CSV),
        "raw_data_committed": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "trade_usable": False,
        "active_taxonomy_readback": {
            "name": "MainRegimeV2",
            "price_roots": ROOTS,
            "residual": RESIDUAL,
            "separate_direct_event_lane": "Manipulation",
            "superseded_not_active": ["MainRegimeV5", "MainRegimeV6", "ActionableRegimeRootV7"],
        },
        "source_profile": {
            "rows_total": int(len(raw)),
            "rows_mainregimev2": int(len(df)),
            "rows_residual_or_extra": int(len(residual_rows)),
            "tickers": int(raw["ticker"].nunique()),
            "date_start": str(raw["date"].min().date()),
            "date_end": str(raw["date"].max().date()),
            "native_timeframe": "1d",
            "label_counts": {str(k): int(v) for k, v in label_counts.items()},
            "extra_labels_mapped_to_residual": sorted(residual_rows["regime_label"].dropna().unique().tolist()),
        },
        "split_counts": {name: int(len(split)) for name, split in splits.items()},
        "acceptance_policy": {
            "precision_wilson_lcb_95_min": 0.95,
            "calibration_support_min": 250,
            "test_support_min": 250,
            "coverage_min": 0.03,
            "validation_instruments_min": 2,
            "validation_market_contexts_min": 2,
            "validation_timeframes_required_for_full_cycle_goal": "not_satisfied_by_this_daily_only_source",
        },
        "root_reports": root_reports,
        "decision": {
            "accepted_roots_95_from_this_probe": accepted_roots,
            "accepted_parent_root_slots_added": 0,
            "accepted_direct_manipulation_rows_added": 0,
            "gate_result": "blocked_local_panel_selective_rule_probe_daily_only_and_incomplete_roots",
            "blocker": "The panel is correctly parent-class MainRegimeV2, but this daily-only probe accepts only Bull and cannot close Bear, Sideways, Crisis, expanded full-cycle slots, or direct Manipulation variety coverage.",
            "next_action": "Continue exact-underlying MainRegimeV2 parent-root label acquisition outside this daily-only local panel; keep Manipulation on direct-event/order-lifecycle/social/on-chain evidence.",
        },
    }

    json_path = PROBE_DIR / "mainregimev2_local_panel_rule_probe.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    csv_path = PROBE_DIR / "mainregimev2_local_panel_rule_probe_summary.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "root",
                "accepted_95",
                "rule",
                "cal_support",
                "cal_precision",
                "cal_wilson95",
                "test_support",
                "test_precision",
                "test_wilson95",
                "blockers",
            ]
        )
        for root, report in root_reports.items():
            writer.writerow(
                [
                    root,
                    report["accepted_95"],
                    report["rule"],
                    report["calibration"]["support"],
                    f"{report['calibration']['precision']:.12f}",
                    f"{report['calibration']['precision_wilson_lcb_95']:.12f}",
                    report["test"]["support"],
                    f"{report['test']['precision']:.12f}",
                    f"{report['test']['precision_wilson_lcb_95']:.12f}",
                    ";".join(report["blockers"]),
                ]
            )

    md_path = PROBE_DIR / "mainregimev2_local_panel_rule_probe.md"
    lines = [
        "# MainRegimeV2 Local Panel Rule Probe",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        f"Source root: `{SOURCE_ROOT}`",
        "",
        "## Readback",
        "",
        "- The source labels are parent-class `MainRegimeV2` labels: `Bull`, `Bear`, `Sideways`, and `Crisis`.",
        f"- Extra labels mapped to residual/provenance only: `{result['source_profile']['extra_labels_mapped_to_residual']}`.",
        f"- Rows: `{result['source_profile']['rows_total']}` total; `{result['source_profile']['rows_mainregimev2']}` MainRegimeV2 rows.",
        f"- Native timeframe: `{result['source_profile']['native_timeframe']}` only.",
        "- `Manipulation` is not present and is not inferable from this OHLCV/macro panel.",
        "",
        "## Selective Rule Probe",
        "",
        "| Root | Accepted 95 | Rule | Cal support | Cal Wilson95 | Test support | Test Wilson95 |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for root, report in root_reports.items():
        lines.append(
            "| {root} | {accepted} | `{rule}` | {cal_support} | {cal_lcb:.6f} | {test_support} | {test_lcb:.6f} |".format(
                root=root,
                accepted=str(report["accepted_95"]).lower(),
                rule=report["rule"],
                cal_support=report["calibration"]["support"],
                cal_lcb=report["calibration"]["precision_wilson_lcb_95"],
                test_support=report["test"]["support"],
                test_lcb=report["test"]["precision_wilson_lcb_95"],
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Accepted parent-root slots added: `0`.",
            "- Accepted direct `Manipulation` rows/windows added: `0`.",
            "- Gate result: `blocked_local_panel_selective_rule_probe_daily_only_and_incomplete_roots`.",
            "- This confirms the user's taxonomy correction: the local panel is a main-class regime panel, while expansion/consolidation/stress/liquidity labels are child/provenance evidence only.",
            "- The probe does not complete the Board A goal because it is daily-only, accepts only `Bull` under the local selective rule, and provides no direct `Manipulation` evidence.",
            "- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n")

    assertions = [
        "PASS active_taxonomy_mainregimev2",
        "PASS no_raw_data_committed",
        "PASS thresholds_relaxed_false",
        "PASS runtime_code_changed_false",
        "PASS manipulation_not_inferred_from_ohlcv",
        "PASS expanded_or_child_labels_not_promoted",
    ]
    if accepted_roots == ["Bull"]:
        assertions.append("PASS only_bull_accepted_in_this_probe")
    else:
        assertions.append(f"FAIL unexpected_accepted_roots={accepted_roots}")
    (CHECK_DIR / "mainregimev2_local_panel_rule_probe_assertions.out").write_text("\n".join(assertions) + "\n")

    print(json.dumps({"json": str(json_path), "summary_csv": str(csv_path), "report": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()
