#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T124107+0800-codex-source-window-slot-calibration-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T124107-codex-source-window-slot-calibration-v1"
OUT_DIR = RUN_ROOT / "source-window-slot-calibration"
CHECK_DIR = RUN_ROOT / "checks"
CACHE_DIR = Path("/private/tmp/ict-regime-source-window-slot-calibration-v1")

UNIFIED_PANEL = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T124000-codex-unified-source-label-panel-v1/unified-panel/unified_source_label_panel_v1.csv"
SIDEWAYS_JSON = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T123500-codex-sideways-dated-window-materialization-v1/sideways-windows/sideways_dated_window_materialization_v1.json"

SUPPORTED_INTERVALS = {
    "1d": "1d",
    "1w": "1wk",
    "1mo": "1mo",
}
UNSUPPORTED_TIMEFRAME_REASON = "no_long_historical_yfinance_bar_overlap_for_intraday_slot"
Z95 = 1.959963984540054

ACCEPTANCE = {
    "precision_wilson_lcb_95_min": 0.95,
    "support_min": 60,
    "ece_max": 0.05,
}


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def wilson_lcb(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2.0 * total)
    margin = Z95 * math.sqrt((p * (1.0 - p) + Z95 * Z95 / (4.0 * total)) / total)
    return max(0.0, (center - margin) / denom)


def normalize_date(value: str, granularity: str, is_end: bool) -> pd.Timestamp | None:
    if not value:
        return None
    if granularity == "month" and len(value) == 7:
        ts = pd.Timestamp(value + "-01")
        if is_end:
            return ts + pd.offsets.MonthEnd(0)
        return ts
    return pd.Timestamp(value)


def split_for_date(ts: pd.Timestamp) -> str:
    if ts < pd.Timestamp("2015-01-01"):
        return "train"
    if ts < pd.Timestamp("2021-01-01"):
        return "calibration"
    return "test"


def download_close(tickers: list[str], timeframe: str) -> pd.DataFrame:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    interval = SUPPORTED_INTERVALS[timeframe]
    cache_path = CACHE_DIR / f"close_{timeframe}.csv"
    if cache_path.exists():
        return pd.read_csv(cache_path, index_col=0, parse_dates=True)
    raw = yf.download(
        sorted(tickers),
        start="1999-01-01",
        end="2026-05-11",
        interval=interval,
        auto_adjust=True,
        progress=False,
        threads=True,
        group_by="column",
    )
    if not isinstance(raw.columns, pd.MultiIndex):
        raise RuntimeError(f"unexpected yfinance output for {timeframe}")
    close = raw["Close"].dropna(axis=1, thresh=30).copy()
    close.to_csv(cache_path)
    return close


def build_feature_rows(close: pd.Series, ticker: str, timeframe: str) -> pd.DataFrame:
    annualizer = math.sqrt({"1d": 252, "1w": 52, "1mo": 12}[timeframe])
    df = pd.DataFrame({"ts": close.index, "instrument": ticker, "timeframe": timeframe, "close": close.to_numpy(float)})
    df["ret1"] = df["close"].pct_change()
    for window in [20, 32, 60, 120, 128, 200]:
        rolling_max = df["close"].rolling(window).max()
        rolling_min = df["close"].rolling(window).min()
        rolling_mean = df["close"].rolling(window).mean()
        df[f"ret{window}"] = df["close"].pct_change(window)
        df[f"vol{window}"] = df["ret1"].rolling(window).std() * annualizer
        df[f"dd{window}"] = df["close"] / rolling_max - 1.0
        df[f"range{window}"] = (rolling_max - rolling_min) / rolling_mean
        df[f"ma_gap{window}"] = df["close"] / rolling_mean - 1.0
    df["bear_drawdown_ratio"] = -df["dd120"] / 0.20
    df["bear_return_ratio"] = -df["ret60"] / 0.04
    df["range_ratio32_128"] = df["range32"] / df["range128"]
    return df.replace([np.inf, -np.inf], np.nan)


def source_windows_by_slot(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    out: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["source_type"] != "source_window_crosswalk":
            continue
        if row["timeframe"] not in SUPPORTED_INTERVALS:
            continue
        if row["root"] not in {"Bull", "Bear", "Crisis"}:
            continue
        end = normalize_date(row["end_date"], row["date_granularity"], True)
        if end is None:
            continue
        start = normalize_date(row["start_date"], row["date_granularity"], False)
        assert start is not None
        out[(row["instrument"], row["timeframe"])].append(
            {
                "root": row["root"],
                "start": start,
                "end": end,
                "label_window_id": row["label_window_id"],
                "scope_tier": row["scope_tier"],
            }
        )
    return out


def attach_labels(df: pd.DataFrame, windows: list[dict[str, Any]]) -> pd.DataFrame:
    root_sets: list[set[str]] = []
    window_sets: list[set[str]] = []
    for ts in df["ts"]:
        roots: set[str] = set()
        ids: set[str] = set()
        stamp = pd.Timestamp(ts)
        for window in windows:
            if window["start"] <= stamp <= window["end"]:
                roots.add(str(window["root"]))
                ids.add(str(window["label_window_id"]))
        root_sets.append(roots)
        window_sets.append(ids)
    out = df.copy()
    out["source_roots"] = [";".join(sorted(x)) for x in root_sets]
    out["source_window_ids"] = [";".join(sorted(x)) for x in window_sets]
    out["has_source_label"] = [bool(x) for x in root_sets]
    out["split"] = out["ts"].map(split_for_date)
    return out[out["has_source_label"]].reset_index(drop=True)


def rule_mask(df: pd.DataFrame, root: str) -> tuple[str, np.ndarray]:
    if root == "Bull":
        return "dd60 >= -0.0032047199531 AND vol60 <= 0.152179344579", (
            (df["dd60"] >= -0.0032047199531) & (df["vol60"] <= 0.152179344579)
        ).fillna(False).to_numpy(bool)
    if root == "Bear":
        return "bear_drawdown_ratio >= 1 AND bear_return_ratio >= 1", (
            (df["bear_drawdown_ratio"] >= 1.0) & (df["bear_return_ratio"] >= 1.0)
        ).fillna(False).to_numpy(bool)
    if root == "Crisis":
        return "range_ratio32_128 >= 1.43116959912", (
            df["range_ratio32_128"] >= 1.43116959912
        ).fillna(False).to_numpy(bool)
    raise ValueError(root)


def metric(df: pd.DataFrame, root: str, mask: np.ndarray, split: str, train_precision: float | None = None) -> dict[str, Any]:
    split_mask = df["split"].eq(split).to_numpy()
    selected = mask & split_mask
    support = int(selected.sum())
    labels = df["source_roots"].astype(str).str.split(";").apply(lambda xs: root in xs).to_numpy(bool)
    success = int((selected & labels).sum())
    precision = success / support if support else 0.0
    reference = precision if train_precision is None else train_precision
    selected_df = df.loc[selected]
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lcb(success, support),
        "ece": abs(reference - precision) if support else 0.0,
        "source_window_count": len(set(";".join(selected_df["source_window_ids"].dropna().astype(str)).split(";")) - {""}),
    }


def blockers(calibration: dict[str, Any], test: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for split_name, data in [("calibration", calibration), ("test", test)]:
        if data["support"] < ACCEPTANCE["support_min"]:
            out.append(f"{split_name}_support_below_60")
        if data["precision_wilson_lcb_95"] < ACCEPTANCE["precision_wilson_lcb_95_min"]:
            out.append(f"{split_name}_wilson95_below_0_95")
        if data["ece"] > ACCEPTANCE["ece_max"]:
            out.append(f"{split_name}_ece_above_0_05")
    return out


def evaluate_slot(df: pd.DataFrame, root: str) -> dict[str, Any]:
    expression, mask = rule_mask(df, root)
    train = metric(df, root, mask, "train")
    calibration = metric(df, root, mask, "calibration", train["precision"])
    test = metric(df, root, mask, "test", train["precision"])
    blocked_by = blockers(calibration, test)
    return {
        "root": root,
        "rule": expression,
        "train": train,
        "calibration": calibration,
        "test": test,
        "accepted_95": not blocked_by,
        "blockers": blocked_by,
    }


def summarize_sideways() -> dict[str, Any]:
    data = json.loads(SIDEWAYS_JSON.read_text())
    return {
        "root": "Sideways",
        "status": "carried_forward_scoped_existing_gate",
        "accepted_95": True,
        "calibration_wilson95_lcb": 0.988647,
        "test_wilson95_lcb": 0.995568,
        "scope": "Yahoo crypto/equity_etf 1d/1w only",
        "window_count": data.get("windows", {}).get("total", 608) if isinstance(data.get("windows"), dict) else 608,
        "guardrail": "not expanded to intraday/monthly/full-species cells",
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    panel_rows = read_csv(UNIFIED_PANEL)
    windows = source_windows_by_slot(panel_rows)
    instruments_by_timeframe: dict[str, list[str]] = defaultdict(list)
    for instrument, timeframe in windows:
        instruments_by_timeframe[timeframe].append(instrument)

    unsupported_counts = Counter(
        row["timeframe"]
        for row in panel_rows
        if row["source_type"] == "source_window_crosswalk" and row["timeframe"] not in SUPPORTED_INTERVALS
    )

    slot_reports: list[dict[str, Any]] = []
    row_counts: Counter[str] = Counter()
    for timeframe, instruments in sorted(instruments_by_timeframe.items()):
        close = download_close(sorted(set(instruments)), timeframe)
        for instrument in sorted(set(instruments)):
            if instrument not in close.columns:
                slot_reports.append({
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "status": "abstain_no_bar_data",
                    "reason": "downloaded_close_missing_instrument",
                })
                continue
            feature_df = build_feature_rows(close[instrument].dropna().astype(float), instrument, timeframe)
            labeled = attach_labels(feature_df, windows[(instrument, timeframe)])
            row_counts[f"{instrument}:{timeframe}"] = len(labeled)
            root_reports = [evaluate_slot(labeled, root) for root in ["Bull", "Bear", "Crisis"]]
            slot_reports.append({
                "instrument": instrument,
                "timeframe": timeframe,
                "status": "calibrated_on_supported_bar_overlap",
                "labeled_rows": int(len(labeled)),
                "source_root_counts": dict(Counter(root for roots in labeled["source_roots"].astype(str) for root in roots.split(";") if root)),
                "root_reports": root_reports,
            })

    accepted_by_root: dict[str, list[str]] = defaultdict(list)
    blocked_by_root: dict[str, list[str]] = defaultdict(list)
    for slot in slot_reports:
        if slot["status"] != "calibrated_on_supported_bar_overlap":
            continue
        slot_id = f"{slot['instrument']}:{slot['timeframe']}"
        for root_report in slot["root_reports"]:
            if root_report["accepted_95"]:
                accepted_by_root[root_report["root"]].append(slot_id)
            else:
                blocked_by_root[root_report["root"]].append(slot_id)

    sideways = summarize_sideways()
    report = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "source_window_slot_calibration_v1",
        "inputs": {
            "unified_panel": repo_rel(UNIFIED_PANEL),
            "sideways_materialization": repo_rel(SIDEWAYS_JSON),
        },
        "acceptance": ACCEPTANCE,
        "supported_timeframes": sorted(SUPPORTED_INTERVALS),
        "unsupported_crosswalk_timeframes": dict(sorted(unsupported_counts.items())),
        "unsupported_timeframe_reason": UNSUPPORTED_TIMEFRAME_REASON,
        "slot_reports": slot_reports,
        "sideways_carried_forward": sideways,
        "decision": {
            "accepted_crosswalk_slots_by_root": {root: sorted(slots) for root, slots in accepted_by_root.items()},
            "blocked_crosswalk_slots_by_root": {root: sorted(slots) for root, slots in blocked_by_root.items()},
            "sideways_scoped_accepted": sideways["accepted_95"],
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "gate_result": "partial_supported_bar_overlap_calibrated_full_matrix_still_blocked",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": "Do not broaden source-window projections. Use only accepted slots downstream; acquire exact/direct labels for blocked Bear/Crisis cells and direct Manipulation varieties.",
    }

    json_path = OUT_DIR / "source_window_slot_calibration_v1.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    summary_csv = OUT_DIR / "source_window_slot_calibration_v1_summary.csv"
    with summary_csv.open("w", newline="") as f:
        fields = ["instrument", "timeframe", "root", "accepted_95", "cal_lcb", "test_lcb", "cal_support", "test_support", "blockers"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for slot in slot_reports:
            if slot["status"] != "calibrated_on_supported_bar_overlap":
                continue
            for root_report in slot["root_reports"]:
                writer.writerow({
                    "instrument": slot["instrument"],
                    "timeframe": slot["timeframe"],
                    "root": root_report["root"],
                    "accepted_95": root_report["accepted_95"],
                    "cal_lcb": f"{root_report['calibration']['precision_wilson_lcb_95']:.6f}",
                    "test_lcb": f"{root_report['test']['precision_wilson_lcb_95']:.6f}",
                    "cal_support": root_report["calibration"]["support"],
                    "test_support": root_report["test"]["support"],
                    "blockers": ";".join(root_report["blockers"]),
                })

    accepted_flat = [
        f"{root}:{slot}"
        for root, slots in sorted(accepted_by_root.items())
        for slot in sorted(slots)
    ]
    md = [
        "# Source-Window Slot Calibration v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Supported bar-overlap slots calibrated: `{sum(1 for s in slot_reports if s['status'] == 'calibrated_on_supported_bar_overlap')}`.",
        f"- Unsupported crosswalk timeframe slots abstained: `{dict(sorted(unsupported_counts.items()))}`.",
        f"- Accepted 95 crosswalk slots: `{accepted_flat}`.",
        f"- Sideways carried forward as scoped accepted gate: `{sideways['calibration_wilson95_lcb']}` / `{sideways['test_wilson95_lcb']}`.",
        "- Full objective achieved: `false`.",
        "",
        "## Boundary",
        "",
        "- Bull/Bear/Crisis source-window rows were calibrated only where yfinance historical bars overlap `1d`, `1w`, or `1mo`.",
        "- Intraday crosswalk slots remain abstained because long historical yfinance intraday bars are unavailable for those source windows.",
        "- Sideways remains scoped to Yahoo crypto/equity ETF `1d`/`1w`; no intraday/monthly/full-species projection was made.",
        "- Manipulation is not part of this price-root panel and still requires direct event/order-flow/order-lifecycle rows.",
        "",
        "## Artifacts",
        "",
        f"- `{repo_rel(json_path)}`",
        f"- `{repo_rel(summary_csv)}`",
        f"- `{repo_rel(CHECK_DIR / 'source_window_slot_calibration_v1_assertions.out')}`",
        "",
    ]
    (OUT_DIR / "source_window_slot_calibration_v1.md").write_text("\n".join(md))

    assertions = {
        "run_id": RUN_ID,
        "json": repo_rel(json_path),
        "summary_csv": repo_rel(summary_csv),
        "accepted_full_objective_gate": report["decision"]["accepted_full_objective_gate"],
        "full_objective_achieved": False,
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "trade_usable": False,
        "unsupported_timeframes_abstained": bool(unsupported_counts),
    }
    (CHECK_DIR / "source_window_slot_calibration_v1_assertions.out").write_text(
        json.dumps(assertions, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
