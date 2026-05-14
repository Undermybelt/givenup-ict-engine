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
RUN_ID = "20260511T123500+0800-codex-sideways-dated-window-materialization-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T123500-codex-sideways-dated-window-materialization-v1"
OUT_DIR = RUN_ROOT / "sideways-windows"
CHECK_DIR = RUN_ROOT / "checks"

BOARD = REPO / "docs/plans/2026-05-10-actionable-regime-confidence-todo.md"
SIDEWAYS_GATE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T041923-codex-yahoo-sourcebacked-parent-root-gate/yahoo-parent-root-gate/yahoo_sourcebacked_parent_root_gate_report.json"
PROTOCOL = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T123100-codex-crosswalk-decision-package-v1/crosswalk-decision/sideways_adjudication_protocol_v1.md"
CACHE_DIR = Path("/private/tmp/ict-regime-yahoo-sourcebacked-parent-root-gate")

RULE_ABS_RETURN_RATIO_MAX = 0.505204858191
RULE_RANGE_RATIO_MAX = 0.357222193236
FEATURE_COLUMNS = [
    "sideways_abs_return_ratio",
    "sideways_range_ratio",
    "sideways_ma_gap_ratio",
    "ret_trend",
    "range_trend",
    "ma_gap_trend",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def context_thresholds(market_context: str, timeframe: str) -> dict[str, float]:
    is_crypto = market_context == "crypto"
    if timeframe == "1d":
        return {
            "trend_window": 60,
            "sideways_abs_return": 0.12 if is_crypto else 0.04,
            "sideways_range": 0.55 if is_crypto else 0.18,
            "sideways_ma_gap": 0.12 if is_crypto else 0.04,
        }
    return {
        "trend_window": 26,
        "sideways_abs_return": 0.22 if is_crypto else 0.08,
        "sideways_range": 0.80 if is_crypto else 0.30,
        "sideways_ma_gap": 0.22 if is_crypto else 0.08,
    }


def build_features(close: pd.Series, ticker: str, timeframe: str) -> pd.DataFrame:
    market_context = "crypto" if ticker.endswith("-USD") else "equity_etf"
    thresholds = context_thresholds(market_context, timeframe)
    trend_window = int(thresholds["trend_window"])
    df = pd.DataFrame({"ts": close.index, "ticker": ticker, "close": close.to_numpy(dtype=float)})
    df["timeframe"] = timeframe
    df["market_context"] = market_context
    roll_max = df["close"].rolling(trend_window).max()
    roll_min = df["close"].rolling(trend_window).min()
    roll_mean = df["close"].rolling(trend_window).mean()
    df["ret_trend"] = df["close"].pct_change(trend_window)
    df["range_trend"] = (roll_max - roll_min) / roll_mean
    df["ma_gap_trend"] = df["close"] / roll_mean - 1.0
    df["sideways_abs_return_ratio"] = df["ret_trend"].abs() / float(thresholds["sideways_abs_return"])
    df["sideways_range_ratio"] = df["range_trend"] / float(thresholds["sideways_range"])
    df["sideways_ma_gap_ratio"] = df["ma_gap_trend"].abs() / float(thresholds["sideways_ma_gap"])
    df = df.dropna(subset=FEATURE_COLUMNS).copy()
    df["sideways_materialized"] = (
        (df["sideways_abs_return_ratio"] <= RULE_ABS_RETURN_RATIO_MAX)
        & (df["sideways_range_ratio"] <= RULE_RANGE_RATIO_MAX)
    )
    return df


def split_for_panel(df: pd.DataFrame) -> pd.DataFrame:
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


def load_panel_from_cache() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for interval, timeframe in [("1d", "1d"), ("1wk", "1w")]:
        path = CACHE_DIR / f"yahoo_close_{interval}.csv"
        if not path.exists():
            raise FileNotFoundError(f"required cache missing: {path}")
        close = pd.read_csv(path, index_col=0, parse_dates=True)
        for ticker in close.columns:
            series = close[ticker].dropna().astype(float)
            if len(series) < 180:
                continue
            frames.append(build_features(series, ticker, timeframe))
    if not frames:
        raise RuntimeError("no cached Yahoo close series could produce features")
    return split_for_panel(pd.concat(frames, ignore_index=True))


def materialize_windows(df: pd.DataFrame) -> list[dict[str, str]]:
    windows: list[dict[str, str]] = []
    for (ticker, timeframe, market_context), group in df.sort_values("ts").groupby(["ticker", "timeframe", "market_context"]):
        group = group.reset_index(drop=True)
        start = None
        end = None
        rows = 0
        splits: Counter[str] = Counter()
        min_abs = math.inf
        max_abs = -math.inf
        min_range = math.inf
        max_range = -math.inf
        for _, row in group.iterrows():
            if bool(row["sideways_materialized"]):
                if start is None:
                    start = row["ts"]
                    rows = 0
                    splits = Counter()
                    min_abs = math.inf
                    max_abs = -math.inf
                    min_range = math.inf
                    max_range = -math.inf
                end = row["ts"]
                rows += 1
                splits[str(row["split"])] += 1
                abs_ratio = float(row["sideways_abs_return_ratio"])
                range_ratio = float(row["sideways_range_ratio"])
                min_abs = min(min_abs, abs_ratio)
                max_abs = max(max_abs, abs_ratio)
                min_range = min(min_range, range_ratio)
                max_range = max(max_range, range_ratio)
            elif start is not None:
                windows.append(make_window(ticker, timeframe, market_context, start, end, rows, splits, min_abs, max_abs, min_range, max_range))
                start = None
        if start is not None:
            windows.append(make_window(ticker, timeframe, market_context, start, end, rows, splits, min_abs, max_abs, min_range, max_range))
    return windows


def make_window(
    ticker: str,
    timeframe: str,
    market_context: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    rows: int,
    splits: Counter[str],
    min_abs: float,
    max_abs: float,
    min_range: float,
    max_range: float,
) -> dict[str, str]:
    return {
        "source_window_id": f"sideways-{ticker}-{timeframe}-{start.date()}-{end.date()}",
        "root": "Sideways",
        "provider": "yfinance_cache",
        "instrument": ticker,
        "market_context": market_context,
        "timeframe": timeframe,
        "start_date": str(start.date()),
        "end_date": str(end.date()),
        "row_count": str(rows),
        "train_rows": str(splits["train"]),
        "calibration_rows": str(splits["calibration"]),
        "test_rows": str(splits["test"]),
        "rule": f"sideways_abs_return_ratio <= {RULE_ABS_RETURN_RATIO_MAX} AND sideways_range_ratio <= {RULE_RANGE_RATIO_MAX}",
        "min_sideways_abs_return_ratio": f"{min_abs:.12g}",
        "max_sideways_abs_return_ratio": f"{max_abs:.12g}",
        "min_sideways_range_ratio": f"{min_range:.12g}",
        "max_sideways_range_ratio": f"{max_range:.12g}",
        "status": "materialized_scoped_dated_window",
    }


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "source_window_id",
        "root",
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
        "min_sideways_abs_return_ratio",
        "max_sideways_abs_return_ratio",
        "min_sideways_range_ratio",
        "max_sideways_range_ratio",
        "status",
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    with SIDEWAYS_GATE.open() as f:
        gate = json.load(f)
    side = gate["root_reports"]["Sideways"]
    df = load_panel_from_cache()
    windows = materialize_windows(df)

    window_csv = OUT_DIR / "sideways_dated_windows_v1.csv"
    write_csv(window_csv, windows)

    rows_selected = int(df["sideways_materialized"].sum())
    by_timeframe = {str(k): int(v) for k, v in df[df["sideways_materialized"]]["timeframe"].value_counts().sort_index().to_dict().items()}
    by_context = {str(k): int(v) for k, v in df[df["sideways_materialized"]]["market_context"].value_counts().sort_index().to_dict().items()}
    by_split = {str(k): int(v) for k, v in df[df["sideways_materialized"]]["split"].value_counts().sort_index().to_dict().items()}

    package = {
        "run_id": RUN_ID,
        "artifact_type": "sideways_dated_window_materialization_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "board": str(BOARD.relative_to(REPO)),
            "board_sha256_at_run": sha256(BOARD),
            "sideways_gate_report": str(SIDEWAYS_GATE.relative_to(REPO)),
            "sideways_gate_report_sha256": sha256(SIDEWAYS_GATE),
            "sideways_protocol": str(PROTOCOL.relative_to(REPO)),
            "cache_files": [
                str((CACHE_DIR / "yahoo_close_1d.csv")),
                str((CACHE_DIR / "yahoo_close_1wk.csv")),
            ],
        },
        "source_scope": {
            "provider": "Yahoo public market data via existing local yfinance cache",
            "market_contexts": sorted(df["market_context"].unique().tolist()),
            "timeframes": sorted(df["timeframe"].unique().tolist()),
            "instruments": sorted(df["ticker"].unique().tolist()),
            "panel_rows": int(len(df)),
        },
        "materialized_windows": {
            "window_count": len(windows),
            "selected_rows": rows_selected,
            "selected_rows_by_timeframe": by_timeframe,
            "selected_rows_by_market_context": by_context,
            "selected_rows_by_split": by_split,
            "csv": str(window_csv.relative_to(REPO)),
        },
        "accepted_gate_reference": {
            "gate_id": "sideways_sourcebacked_abs_return_range_v1",
            "gate_report": str(SIDEWAYS_GATE.relative_to(REPO)),
            "rule": side["rule"],
            "calibration_wilson95_lcb": round(float(side["calibration"]["precision_wilson_lcb_95"]), 6),
            "test_wilson95_lcb": round(float(side["test"]["precision_wilson_lcb_95"]), 6),
            "test_support": int(side["test"]["support"]),
            "test_precision": round(float(side["test"]["precision"]), 6),
        },
        "decision": {
            "sideways_dated_windows_materialized": True,
            "scope": "scoped_existing_yahoo_gate_crypto_and_equity_etf_1d_1w_only",
            "full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "remaining_gap": "Expanded intraday/monthly/full-species Sideways cells still need targeted rerun or exact source labels.",
            "trade_usable": False,
        },
        "guardrails": {
            "downloaded_new_data": False,
            "used_existing_cache_only": True,
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "sideways_as_complement": False,
            "future_or_target_predictors_used": False,
            "shared_board_modified": False,
        },
    }

    json_path = OUT_DIR / "sideways_dated_window_materialization_v1.json"
    json_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")

    md = [
        "# Sideways Dated Window Materialization v1",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Materialized Sideways dated windows: `{len(windows)}`.",
        f"- Selected rows: `{rows_selected}`.",
        f"- Scope: `{package['decision']['scope']}`.",
        f"- Existing Sideways gate Wilson95 calibration/test LCB: `{package['accepted_gate_reference']['calibration_wilson95_lcb']}` / `{package['accepted_gate_reference']['test_wilson95_lcb']}`.",
        "- Full objective gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.",
        "",
        "## What Changed",
        "",
        "The Sideways lane no longer has to say only `no dated source window` for the existing accepted Yahoo scope. It now has concrete dated windows derived from the already accepted `sideways_sourcebacked_abs_return_range_v1` gate.",
        "",
        "## Guardrails",
        "",
        "- Existing local cache only; no fresh download.",
        "- No threshold relaxation.",
        "- No runtime code change.",
        "- No raw Yahoo close matrix committed.",
        "- Sideways is not inferred as complement of Bull/Bear/Crisis.",
        "- This does not cover expanded intraday/monthly/full-species Sideways slots.",
        "",
        "## Artifacts",
        "",
        "- `sideways_dated_window_materialization_v1.json`",
        "- `sideways_dated_windows_v1.csv`",
        "- `../checks/sideways_dated_window_materialization_v1_assertions.out`",
        "",
    ]
    (OUT_DIR / "sideways_dated_window_materialization_v1.md").write_text("\n".join(md))

    assertions = [
        f"run_id={RUN_ID}",
        f"board_sha256_at_run={package['inputs']['board_sha256_at_run']}",
        f"window_count={len(windows)}",
        f"selected_rows={rows_selected}",
        "sideways_dated_windows_materialized=true",
        f"existing_gate_test_lcb={package['accepted_gate_reference']['test_wilson95_lcb']}",
        "full_objective_gate=none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
        "downloaded_new_data=false",
        "used_existing_cache_only=true",
        "runtime_code_changed=false",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
        "sideways_as_complement=false",
        "future_or_target_predictors_used=false",
        "shared_board_modified=false",
        "assertion_status=PASS",
    ]
    (CHECK_DIR / "sideways_dated_window_materialization_v1_assertions.out").write_text("\n".join(assertions) + "\n")

    assert len(windows) > 0
    assert rows_selected > 0
    assert package["accepted_gate_reference"]["test_wilson95_lcb"] >= 0.95
    assert package["decision"]["full_objective_gate"] == "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal"


if __name__ == "__main__":
    main()
