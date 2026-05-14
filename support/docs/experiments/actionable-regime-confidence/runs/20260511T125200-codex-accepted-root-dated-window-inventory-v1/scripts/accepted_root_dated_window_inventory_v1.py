#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[6]
RUN_ID = "20260511T125200+0800-codex-accepted-root-dated-window-inventory-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T125200-codex-accepted-root-dated-window-inventory-v1"
OUT_DIR = RUN_ROOT / "accepted-root-windows"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
BULL_FEATURE_TABLE = Path("/private/tmp/ict-regime-kaggle-regime-label-root/kaggle_regime_label_feature_table.csv")
YAHOO_CACHE_DIR = Path("/private/tmp/ict-regime-yahoo-sourcebacked-parent-root-gate")
SIDEWAYS_WINDOWS = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T123500-codex-sideways-dated-window-materialization-v1/sideways-windows/sideways_dated_windows_v1.csv"

BULL_GATE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T035045-codex-kaggle-bull-coverage-buffer-gate/kaggle-bull-gate/kaggle_bull_coverage_buffer_gate_report.json"
YAHOO_GATE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T041923-codex-yahoo-sourcebacked-parent-root-gate/yahoo-parent-root-gate/yahoo_sourcebacked_parent_root_gate_report.json"
CRISIS_GATE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T235220-codex-broader-root-v2-probe/root-v2-broader/main_regime_v2_broader_root_calibration_report.json"

BULL_DRAWDOWN_MIN = -0.0032047199531
BULL_VOL_MAX = 0.152179344579
BEAR_DRAWDOWN_RATIO_MIN = 1.0
BEAR_RETURN_RATIO_MIN = 1.0


FIELDS = [
    "window_id",
    "root",
    "source_gate_id",
    "provider",
    "instrument",
    "market_context",
    "timeframe",
    "start_date",
    "end_date",
    "row_count",
    "train_rows",
    "calibration_rows",
    "test_rows",
    "rule",
    "gate_calibration_lcb",
    "gate_test_lcb",
    "status",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_id(value: str) -> str:
    return value.replace("^", "idx").replace("=", "").replace("/", "-")


def read_json(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def root_report(report: dict, root: str) -> dict:
    reports = report["root_reports"]
    if isinstance(reports, dict):
        return reports[root]
    for item in reports:
        if item.get("root_class") == root or item.get("root") == root:
            return item
    raise KeyError(root)


def split_counts(group: pd.DataFrame) -> tuple[int, int, int]:
    counts = group["split"].value_counts().to_dict()
    return int(counts.get("train", 0)), int(counts.get("calibration", 0)), int(counts.get("test", 0))


def materialize_from_selected(df: pd.DataFrame, root: str, gate_id: str, provider: str, rule: str, cal_lcb: float, test_lcb: float) -> list[dict[str, str]]:
    windows: list[dict[str, str]] = []
    for (instrument, timeframe, market_context), group in df.sort_values("ts").groupby(["instrument", "timeframe", "market_context"]):
        group = group.reset_index(drop=True)
        start_idx = None
        for idx, row in group.iterrows():
            selected = bool(row["selected_positive"])
            if selected and start_idx is None:
                start_idx = idx
            if (not selected or idx == len(group) - 1) and start_idx is not None:
                end_idx = idx if selected and idx == len(group) - 1 else idx - 1
                window = group.loc[start_idx:end_idx]
                train_rows, cal_rows, test_rows = split_counts(window)
                start = pd.Timestamp(window.iloc[0]["ts"]).date()
                end = pd.Timestamp(window.iloc[-1]["ts"]).date()
                windows.append({
                    "window_id": f"{root.lower()}-{safe_id(str(instrument))}-{timeframe}-{start}-{end}",
                    "root": root,
                    "source_gate_id": gate_id,
                    "provider": provider,
                    "instrument": str(instrument),
                    "market_context": str(market_context),
                    "timeframe": str(timeframe),
                    "start_date": str(start),
                    "end_date": str(end),
                    "row_count": str(len(window)),
                    "train_rows": str(train_rows),
                    "calibration_rows": str(cal_rows),
                    "test_rows": str(test_rows),
                    "rule": rule,
                    "gate_calibration_lcb": f"{cal_lcb:.6f}",
                    "gate_test_lcb": f"{test_lcb:.6f}",
                    "status": "materialized_from_existing_accepted_95_gate",
                })
                start_idx = None
    return windows


def load_bull_windows(bull_report: dict) -> list[dict[str, str]]:
    if not BULL_FEATURE_TABLE.exists():
        return []
    usecols = [
        "date",
        "ticker",
        "timeframe",
        "market_context",
        "split",
        "regime_label",
        "close_drawdown60",
        "volatility",
    ]
    df = pd.read_csv(BULL_FEATURE_TABLE, usecols=usecols, parse_dates=["date"])
    df = df.rename(columns={"date": "ts", "ticker": "instrument"})
    df["selected_positive"] = (
        df["regime_label"].eq("Bull")
        & (pd.to_numeric(df["close_drawdown60"], errors="coerce") >= BULL_DRAWDOWN_MIN)
        & (pd.to_numeric(df["volatility"], errors="coerce") <= BULL_VOL_MAX)
    )
    return materialize_from_selected(
        df,
        "Bull",
        "bull_sourcebacked_drawdown_volatility_v1",
        "kaggle_stock_regime_feature_table",
        "close_drawdown60 >= -0.0032047199531 AND volatility <= 0.152179344579",
        float(bull_report["calibration"]["precision_wilson_lcb_95"]),
        float(bull_report["test"]["precision_wilson_lcb_95"]),
    )


def context_thresholds(market_context: str, timeframe: str) -> dict[str, float]:
    is_crypto = market_context == "crypto"
    if timeframe == "1d":
        return {
            "trend_window": 60,
            "long_window": 120,
            "bear_drawdown": 0.35 if is_crypto else 0.20,
            "bear_return": 0.10 if is_crypto else 0.04,
        }
    return {
        "trend_window": 26,
        "long_window": 52,
        "bear_drawdown": 0.45 if is_crypto else 0.20,
        "bear_return": 0.18 if is_crypto else 0.06,
    }


def build_bear_features(close: pd.Series, instrument: str, timeframe: str) -> pd.DataFrame:
    market_context = "crypto" if instrument.endswith("-USD") else "equity_etf"
    t = context_thresholds(market_context, timeframe)
    trend_window = int(t["trend_window"])
    long_window = int(t["long_window"])
    df = pd.DataFrame({"ts": close.index, "instrument": instrument, "close": close.to_numpy(dtype=float)})
    df["timeframe"] = timeframe
    df["market_context"] = market_context
    roll_max = df["close"].rolling(long_window).max()
    df["ret_trend"] = df["close"].pct_change(trend_window)
    df["drawdown_long"] = df["close"] / roll_max - 1.0
    df["bear_drawdown_ratio"] = -df["drawdown_long"] / float(t["bear_drawdown"])
    df["bear_return_ratio"] = -df["ret_trend"] / float(t["bear_return"])
    df = df.dropna(subset=["bear_drawdown_ratio", "bear_return_ratio"]).copy()
    df["selected_positive"] = (
        (df["bear_drawdown_ratio"] >= BEAR_DRAWDOWN_RATIO_MIN)
        & (df["bear_return_ratio"] >= BEAR_RETURN_RATIO_MIN)
    )
    return df


def add_splits(df: pd.DataFrame) -> pd.DataFrame:
    df["split"] = ""
    for _, idx in df.groupby(["instrument", "timeframe"]).groups.items():
        ordered = sorted(idx, key=lambda i: df.loc[i, "ts"])
        n = len(ordered)
        train_end = int(n * 0.60)
        calibration_end = int(n * 0.80)
        df.loc[ordered[:train_end], "split"] = "train"
        df.loc[ordered[train_end:calibration_end], "split"] = "calibration"
        df.loc[ordered[calibration_end:], "split"] = "test"
    return df[df["split"].isin(["train", "calibration", "test"])].reset_index(drop=True)


def load_bear_windows(yahoo_report: dict) -> list[dict[str, str]]:
    frames: list[pd.DataFrame] = []
    for interval, timeframe in [("1d", "1d"), ("1wk", "1w")]:
        path = YAHOO_CACHE_DIR / f"yahoo_close_{interval}.csv"
        if not path.exists():
            continue
        close = pd.read_csv(path, index_col=0, parse_dates=True)
        for instrument in close.columns:
            series = close[instrument].dropna().astype(float)
            if len(series) < 180:
                continue
            frames.append(build_bear_features(series, instrument, timeframe))
    if not frames:
        return []
    df = add_splits(pd.concat(frames, ignore_index=True))
    bear = yahoo_report["root_reports"]["Bear"]
    return materialize_from_selected(
        df,
        "Bear",
        "bear_sourcebacked_drawdown_return_ratio_v1",
        "yahoo_cached_public_market_data",
        "bear_drawdown_ratio >= 1 AND bear_return_ratio >= 1",
        float(bear["calibration"]["precision_wilson_lcb_95"]),
        float(bear["test"]["precision_wilson_lcb_95"]),
    )


def load_sideways_windows(yahoo_report: dict) -> list[dict[str, str]]:
    if not SIDEWAYS_WINDOWS.exists():
        return []
    side = yahoo_report["root_reports"]["Sideways"]
    rows: list[dict[str, str]] = []
    with SIDEWAYS_WINDOWS.open(newline="") as f:
        for row in csv.DictReader(f):
            rows.append({
                "window_id": row["source_window_id"],
                "root": "Sideways",
                "source_gate_id": "sideways_sourcebacked_abs_return_range_v1",
                "provider": row["provider"],
                "instrument": row["instrument"],
                "market_context": row["market_context"],
                "timeframe": row["timeframe"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "row_count": row["row_count"],
                "train_rows": row["train_rows"],
                "calibration_rows": row["calibration_rows"],
                "test_rows": row["test_rows"],
                "rule": row["rule"],
                "gate_calibration_lcb": f"{float(side['calibration']['precision_wilson_lcb_95']):.6f}",
                "gate_test_lcb": f"{float(side['test']['precision_wilson_lcb_95']):.6f}",
                "status": "materialized_from_existing_accepted_95_gate",
            })
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    bull_report = read_json(BULL_GATE)
    yahoo_report = read_json(YAHOO_GATE)
    crisis_report = read_json(CRISIS_GATE)

    bull_windows = load_bull_windows(bull_report)
    bear_windows = load_bear_windows(yahoo_report)
    sideways_windows = load_sideways_windows(yahoo_report)
    all_windows = bull_windows + bear_windows + sideways_windows

    windows_csv = OUT_DIR / "accepted_root_dated_windows_v1.csv"
    write_csv(windows_csv, all_windows)

    rows_by_root = Counter()
    windows_by_root = Counter()
    contexts_by_root: dict[str, set[str]] = {"Bull": set(), "Bear": set(), "Sideways": set()}
    timeframes_by_root: dict[str, set[str]] = {"Bull": set(), "Bear": set(), "Sideways": set()}
    for row in all_windows:
        root = row["root"]
        windows_by_root[root] += 1
        rows_by_root[root] += int(row["row_count"])
        contexts_by_root.setdefault(root, set()).add(row["market_context"])
        timeframes_by_root.setdefault(root, set()).add(row["timeframe"])

    crisis_summary = root_report(crisis_report, "Crisis")["selected_candidate"]
    package = {
        "run_id": RUN_ID,
        "artifact_type": "accepted_root_dated_window_inventory_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "board": str(BOARD.relative_to(REPO)),
            "board_sha256_at_run": sha256(BOARD),
            "bull_gate": str(BULL_GATE.relative_to(REPO)),
            "bull_gate_sha256": sha256(BULL_GATE),
            "yahoo_gate": str(YAHOO_GATE.relative_to(REPO)),
            "yahoo_gate_sha256": sha256(YAHOO_GATE),
            "crisis_gate": str(CRISIS_GATE.relative_to(REPO)),
            "crisis_gate_sha256": sha256(CRISIS_GATE),
            "bull_feature_table_local": str(BULL_FEATURE_TABLE),
            "yahoo_cache_dir": str(YAHOO_CACHE_DIR),
        },
        "materialized_inventory": {
            "csv": str(windows_csv.relative_to(REPO)),
            "total_windows": len(all_windows),
            "windows_by_root": dict(sorted(windows_by_root.items())),
            "selected_rows_by_root": dict(sorted(rows_by_root.items())),
            "contexts_by_root": {k: sorted(v) for k, v in contexts_by_root.items()},
            "timeframes_by_root": {k: sorted(v) for k, v in timeframes_by_root.items()},
        },
        "accepted_gate_references": {
            "Bull": {
                "gate_id": "bull_sourcebacked_drawdown_volatility_v1",
                "calibration_wilson95_lcb": round(float(bull_report["calibration"]["precision_wilson_lcb_95"]), 6),
                "test_wilson95_lcb": round(float(bull_report["test"]["precision_wilson_lcb_95"]), 6),
            },
            "Bear": {
                "gate_id": "bear_sourcebacked_drawdown_return_ratio_v1",
                "calibration_wilson95_lcb": round(float(yahoo_report["root_reports"]["Bear"]["calibration"]["precision_wilson_lcb_95"]), 6),
                "test_wilson95_lcb": round(float(yahoo_report["root_reports"]["Bear"]["test"]["precision_wilson_lcb_95"]), 6),
            },
            "Sideways": {
                "gate_id": "sideways_sourcebacked_abs_return_range_v1",
                "calibration_wilson95_lcb": round(float(yahoo_report["root_reports"]["Sideways"]["calibration"]["precision_wilson_lcb_95"]), 6),
                "test_wilson95_lcb": round(float(yahoo_report["root_reports"]["Sideways"]["test"]["precision_wilson_lcb_95"]), 6),
            },
            "Crisis": {
                "gate_id": "crisis_range_ratio_intraday_v1",
                "calibration_wilson95_lcb": round(float(crisis_summary["calibration"]["precision_wilson_lcb_95"]), 6),
                "test_wilson95_lcb": round(float(crisis_summary["test"]["precision_wilson_lcb_95"]), 6),
                "dated_windows_materialized": False,
                "reason": "The supporting cross-timeframe raw feature table was pruned; keep report-backed accepted gate but do not invent dated windows.",
            },
        },
        "decision": {
            "materialized_roots": sorted(windows_by_root),
            "report_backed_only_roots": ["Crisis"],
            "confidence_gate_claimed": False,
            "full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "next_action": "Use Bull/Bear/Sideways dated accepted-window inventory for downstream source-label joins; reacquire or regenerate Crisis feature rows before materializing Crisis dated windows.",
        },
        "guardrails": {
            "used_existing_local_tables_only": True,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
            "shared_board_modified": False,
        },
    }

    json_path = OUT_DIR / "accepted_root_dated_window_inventory_v1.json"
    json_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")

    md = [
        "# Accepted Root Dated Window Inventory v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Materialized accepted-root dated windows: `{len(all_windows)}`.",
        f"- Windows by root: `{dict(sorted(windows_by_root.items()))}`.",
        f"- Selected rows by root: `{dict(sorted(rows_by_root.items()))}`.",
        "- Crisis remains report-backed only; dated windows were not invented after the raw feature table was pruned.",
        "- Full objective gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.",
        "",
        "## Gate References",
        "",
        f"- Bull LCB calibration/test: `{package['accepted_gate_references']['Bull']['calibration_wilson95_lcb']}` / `{package['accepted_gate_references']['Bull']['test_wilson95_lcb']}`.",
        f"- Bear LCB calibration/test: `{package['accepted_gate_references']['Bear']['calibration_wilson95_lcb']}` / `{package['accepted_gate_references']['Bear']['test_wilson95_lcb']}`.",
        f"- Sideways LCB calibration/test: `{package['accepted_gate_references']['Sideways']['calibration_wilson95_lcb']}` / `{package['accepted_gate_references']['Sideways']['test_wilson95_lcb']}`.",
        f"- Crisis LCB calibration/test: `{package['accepted_gate_references']['Crisis']['calibration_wilson95_lcb']}` / `{package['accepted_gate_references']['Crisis']['test_wilson95_lcb']}` report-backed only.",
        "",
        "## Guardrails",
        "",
        "- Existing local tables/cache only.",
        "- No runtime code change.",
        "- No threshold relaxation.",
        "- No raw feature table committed.",
        "- No trade usability claimed.",
        "",
        "## Artifacts",
        "",
        "- `accepted_root_dated_window_inventory_v1.json`",
        "- `accepted_root_dated_windows_v1.csv`",
        "- `../checks/accepted_root_dated_window_inventory_v1_assertions.out`",
        "",
    ]
    (OUT_DIR / "accepted_root_dated_window_inventory_v1.md").write_text("\n".join(md))

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={package['inputs']['board_sha256_at_run']}",
        f"total_windows={len(all_windows)}",
        f"windows_by_root={dict(sorted(windows_by_root.items()))}",
        f"selected_rows_by_root={dict(sorted(rows_by_root.items()))}",
        f"materialized_roots={','.join(package['decision']['materialized_roots'])}",
        "crisis_dated_windows_materialized=false",
        "confidence_gate_claimed=false",
        "full_objective_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "trade_usable=false",
        "assertion_status=PASS",
    ]
    (CHECK_DIR / "accepted_root_dated_window_inventory_v1_assertions.out").write_text("\n".join(assertions) + "\n")

    assert windows_by_root["Bull"] > 0
    assert windows_by_root["Bear"] > 0
    assert windows_by_root["Sideways"] > 0
    assert package["accepted_gate_references"]["Crisis"]["dated_windows_materialized"] is False


if __name__ == "__main__":
    main()
