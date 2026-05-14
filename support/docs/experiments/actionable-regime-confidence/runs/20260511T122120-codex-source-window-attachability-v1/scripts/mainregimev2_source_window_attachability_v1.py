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
RUN_ID = "20260511T122120+0800-codex-source-window-attachability-v1"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T122120-codex-source-window-attachability-v1"
OUT_DIR = RUN_ROOT / "source-window-attachability"
CHECK_DIR = RUN_ROOT / "checks"
CACHE_DIR = Path("/private/tmp/ict-regime-source-window-attachability-v1")
SEED_CSV = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T120900-codex-exportable-source-scan/source-scan/source_window_seed_v1.csv"

TICKERS = ["^GSPC", "SPY", "QQQ", "IWM", "ES=F"]
START = "1999-01-01"
END = "2026-05-11"
Z95 = 1.959963984540054

NATIVE_ACCEPTANCE = {
    "precision_wilson_lcb_95_min": 0.95,
    "support_min": 60,
    "coverage_min": 0.01,
    "ece_max": 0.05,
}

FEATURES = [
    "ret5",
    "ret10",
    "ret20",
    "ret40",
    "ret60",
    "ret80",
    "ret120",
    "ret160",
    "ret200",
    "vol20",
    "vol60",
    "vol120",
    "vol200",
    "dd20",
    "dd60",
    "dd120",
    "dd200",
    "dd252",
    "range20",
    "range60",
    "range120",
    "range200",
    "ma_gap20",
    "ma_gap60",
    "ma_gap120",
    "ma_gap200",
    "bear_drawdown_ratio",
    "bear_return_ratio",
]


@dataclass(frozen=True)
class SourceWindow:
    source_id: str
    root: str
    native_scope: str
    start_date: pd.Timestamp
    end_date: pd.Timestamp | None
    projection_status: str
    notes: str

    @property
    def is_closed_yardeni_sp500(self) -> bool:
        return (
            self.source_id == "yardeni_sp500_bull_bear_tables_2024"
            and self.native_scope == "S&P 500"
            and self.root in {"Bull", "Bear"}
            and self.end_date is not None
        )

    @property
    def window_id(self) -> str:
        end = self.end_date.date().isoformat() if self.end_date is not None else "open"
        return f"{self.source_id}:{self.root}:{self.start_date.date().isoformat()}:{end}"


@dataclass(frozen=True)
class Rule:
    name: str
    terms: tuple[tuple[str, str, float], ...]
    selected_on: str

    def expression(self) -> str:
        return " AND ".join(f"{feature} {op} {threshold:.12g}" for feature, op, threshold in self.terms)

    def mask(self, df: pd.DataFrame) -> np.ndarray:
        selected = np.ones(len(df), dtype=bool)
        for feature, op, threshold in self.terms:
            values = pd.to_numeric(df[feature], errors="coerce").replace([np.inf, -np.inf], np.nan).to_numpy(float)
            if op == "<=":
                selected &= values <= threshold
            elif op == ">=":
                selected &= values >= threshold
            else:
                raise ValueError(op)
        return selected


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


def load_source_windows() -> list[SourceWindow]:
    windows: list[SourceWindow] = []
    with SEED_CSV.open() as fh:
        for row in csv.DictReader(fh):
            start = pd.Timestamp(row["start_date"])
            end = pd.Timestamp(row["end_date"]) if row["end_date"] else None
            windows.append(
                SourceWindow(
                    source_id=row["source_id"],
                    root=row["root"],
                    native_scope=row["native_scope"],
                    start_date=start,
                    end_date=end,
                    projection_status=row["projection_status"],
                    notes=row["notes"],
                )
            )
    return windows


def closed_yardeni_windows(windows: list[SourceWindow]) -> list[SourceWindow]:
    return sorted([w for w in windows if w.is_closed_yardeni_sp500], key=lambda w: w.start_date)


def source_label_for_date(ts: pd.Timestamp, windows: list[SourceWindow]) -> tuple[str, str | None]:
    for window in windows:
        assert window.end_date is not None
        if window.start_date <= ts <= window.end_date:
            return window.root, window.window_id
    return "UnknownOrMixed", None


def download_close(interval: str) -> pd.DataFrame:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"close_{interval}.csv"
    if cache_path.exists():
        return pd.read_csv(cache_path, index_col=0, parse_dates=True)

    raw = yf.download(
        TICKERS,
        start=START,
        end=END,
        interval=interval,
        auto_adjust=True,
        progress=False,
        threads=True,
        group_by="column",
    )
    if not isinstance(raw.columns, pd.MultiIndex):
        raise RuntimeError(f"unexpected yfinance shape for interval {interval}")
    close = raw["Close"].dropna(axis=1, thresh=120).copy()
    close.to_csv(cache_path)
    return close


def split_for_date(ts: pd.Timestamp) -> str:
    if ts < pd.Timestamp("2015-01-01"):
        return "train"
    if ts < pd.Timestamp("2021-01-01"):
        return "calibration"
    return "test"


def build_features(close: pd.Series, ticker: str, timeframe: str, windows: list[SourceWindow]) -> pd.DataFrame:
    annualizer = math.sqrt(252 if timeframe == "1d" else 52)
    df = pd.DataFrame({"ts": close.index, "ticker": ticker, "close": close.to_numpy(float)})
    df["timeframe"] = timeframe
    df["ret1"] = df["close"].pct_change()
    for window in [5, 10, 20, 40, 60, 80, 120, 160, 200, 252]:
        roll_max = df["close"].rolling(window).max()
        roll_min = df["close"].rolling(window).min()
        roll_mean = df["close"].rolling(window).mean()
        if window != 252:
            df[f"ret{window}"] = df["close"].pct_change(window)
            df[f"vol{window}"] = df["ret1"].rolling(window).std() * annualizer
            df[f"range{window}"] = (roll_max - roll_min) / roll_mean
            df[f"ma_gap{window}"] = df["close"] / roll_mean - 1.0
        df[f"dd{window}"] = df["close"] / roll_max - 1.0

    df["bear_drawdown_ratio"] = -df["dd120"] / 0.20
    df["bear_return_ratio"] = -df["ret60"] / 0.04
    labels = [source_label_for_date(pd.Timestamp(ts), windows) for ts in df["ts"]]
    df["source_root_label"] = [item[0] for item in labels]
    df["source_window_id"] = [item[1] for item in labels]
    df["split"] = df["ts"].map(split_for_date)
    df["native_exact_source_slot"] = ticker == "^GSPC" and timeframe == "1d"
    df["projection_status"] = np.where(
        df["native_exact_source_slot"],
        "native_exact_sp500_daily",
        "requires_owner_crosswalk",
    )
    last_closed_end = max(w.end_date for w in windows if w.end_date is not None)
    df = df[df["ts"] <= last_closed_end].copy()
    return df.dropna(subset=FEATURES + ["source_root_label", "split"]).reset_index(drop=True)


def build_panel(windows: list[SourceWindow]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for interval, timeframe in [("1d", "1d"), ("1wk", "1w")]:
        close = download_close(interval)
        for ticker in close.columns:
            series = close[ticker].dropna().astype(float)
            if len(series) < 300:
                continue
            frames.append(build_features(series, str(ticker), timeframe, windows))
    if not frames:
        raise RuntimeError("no source-window feature rows built")
    return pd.concat(frames, ignore_index=True)


def metric(df: pd.DataFrame, mask: np.ndarray, root: str, split: str, train_precision: float | None = None) -> dict[str, Any]:
    split_mask = df["split"].eq(split).to_numpy()
    selected = mask & split_mask
    support = int(selected.sum())
    success = int((selected & df["source_root_label"].eq(root).to_numpy()).sum())
    precision = success / support if support else 0.0
    ref = precision if train_precision is None else train_precision
    selected_df = df.loc[selected]
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lcb(success, support),
        "coverage": support / int(split_mask.sum()) if int(split_mask.sum()) else 0.0,
        "ece": abs(ref - precision) if support else 0.0,
        "tickers": sorted(selected_df["ticker"].dropna().astype(str).unique().tolist()),
        "timeframes": sorted(selected_df["timeframe"].dropna().astype(str).unique().tolist()),
        "source_windows": sorted(selected_df["source_window_id"].dropna().astype(str).unique().tolist()),
    }


def blockers(calibration: dict[str, Any], test: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for split, data in [("calibration", calibration), ("test", test)]:
        if data["support"] < NATIVE_ACCEPTANCE["support_min"]:
            out.append(f"{split}_support_below_{NATIVE_ACCEPTANCE['support_min']}")
        if data["precision_wilson_lcb_95"] < NATIVE_ACCEPTANCE["precision_wilson_lcb_95_min"]:
            out.append(f"{split}_wilson95_below_0_95")
        if data["coverage"] < NATIVE_ACCEPTANCE["coverage_min"]:
            out.append(f"{split}_coverage_below_0_01")
        if data["ece"] > NATIVE_ACCEPTANCE["ece_max"]:
            out.append(f"{split}_ece_above_0_05")
    return out


def existing_rule(root: str) -> Rule:
    if root == "Bull":
        return Rule(
            "existing_scoped_bull_factor_rule",
            (("dd60", ">=", -0.0032047199531), ("vol60", "<=", 0.152179344579)),
            "prior_accepted_factor_supply_map",
        )
    if root == "Bear":
        return Rule(
            "existing_scoped_bear_factor_rule",
            (("bear_drawdown_ratio", ">=", 1.0), ("bear_return_ratio", ">=", 1.0)),
            "prior_accepted_factor_supply_map",
        )
    raise ValueError(root)


def calibration_selected_rule(df: pd.DataFrame, root: str) -> Rule:
    train_mask = df["split"].eq("train").to_numpy()
    atoms: list[tuple[float, float, int, Rule, np.ndarray]] = []
    for feature in FEATURES:
        train_values = pd.to_numeric(df.loc[train_mask, feature], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if train_values.nunique() < 10:
            continue
        thresholds = sorted(
            set(
                float(train_values.quantile(q))
                for q in [0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30, 0.50, 0.70, 0.80, 0.90, 0.95, 0.98, 0.99]
            )
        )
        for threshold in thresholds:
            if not math.isfinite(threshold):
                continue
            for op in ["<=", ">="]:
                rule = Rule(
                    f"train_atom_{feature}_{op}_{threshold:.8g}",
                    ((feature, op, threshold),),
                    "train_candidate_library_then_calibration_split",
                )
                mask = rule.mask(df)
                train_metric = metric(df, mask, root, "train")
                if train_metric["support"] >= 60 and train_metric["coverage"] >= 0.01:
                    atoms.append(
                        (
                            train_metric["precision_wilson_lcb_95"],
                            train_metric["precision"],
                            train_metric["support"],
                            rule,
                            mask,
                        )
                    )
    atoms.sort(key=lambda item: item[:3], reverse=True)
    candidates: list[tuple[Rule, np.ndarray]] = [(item[3], item[4]) for item in atoms[:80]]
    for i, left in enumerate(atoms[:60]):
        for right in atoms[i + 1 : 60]:
            left_rule = left[3]
            right_rule = right[3]
            if {term[0] for term in left_rule.terms} & {term[0] for term in right_rule.terms}:
                continue
            terms = left_rule.terms + right_rule.terms
            rule = Rule(
                "train_pair_" + "_AND_".join(f"{feature}_{op}_{threshold:.8g}" for feature, op, threshold in terms),
                terms,
                "train_candidate_library_then_calibration_split",
            )
            candidates.append((rule, left[4] & right[4]))

    scored: list[tuple[float, float, int, float, Rule]] = []
    for rule, mask in candidates:
        train_metric = metric(df, mask, root, "train")
        if train_metric["support"] < 60 or train_metric["coverage"] < 0.01:
            continue
        calibration_metric = metric(df, mask, root, "calibration", train_metric["precision"])
        if calibration_metric["support"] < 10:
            continue
        scored.append(
            (
                calibration_metric["precision_wilson_lcb_95"],
                calibration_metric["precision"],
                calibration_metric["support"],
                train_metric["precision_wilson_lcb_95"],
                rule,
            )
        )
    if not scored:
        raise RuntimeError(f"no calibration-selected rule for {root}")
    scored.sort(key=lambda item: item[:4], reverse=True)
    return scored[0][4]


def evaluate_rule(df: pd.DataFrame, root: str, rule: Rule) -> dict[str, Any]:
    mask = rule.mask(df)
    train = metric(df, mask, root, "train")
    calibration = metric(df, mask, root, "calibration", train["precision"])
    test = metric(df, mask, root, "test", train["precision"])
    blocked_by = blockers(calibration, test)
    return {
        "root": root,
        "rule_name": rule.name,
        "rule": rule.expression(),
        "selected_on": rule.selected_on,
        "train": train,
        "calibration": calibration,
        "test": test,
        "accepted_95_source_window_gate": not blocked_by,
        "blockers": blocked_by,
    }


def source_label_slots(panel: pd.DataFrame, windows: list[SourceWindow]) -> list[dict[str, Any]]:
    native = panel[panel["native_exact_source_slot"]]
    slots: list[dict[str, Any]] = []
    for root in ["Bull", "Bear"]:
        rows = native[native["source_root_label"].eq(root)]
        slots.append(
            {
                "root": root,
                "provider": "yfinance",
                "instrument": "^GSPC",
                "timeframe": "1d",
                "source_id": "yardeni_sp500_bull_bear_tables_2024",
                "projection_status": "native_exact_sp500_daily_closed_windows",
                "accepted_source_label_target_slot": len(rows) > 0,
                "rows": int(len(rows)),
                "source_windows": sorted(rows["source_window_id"].dropna().astype(str).unique().tolist()),
                "note": "Closed Yardeni S&P 500 windows only; the open-ended 2022-10-12 bull window is excluded until refreshed.",
            }
        )
    slots.append(
        {
            "root": "Crisis",
            "provider": "n/a",
            "instrument": "US macro/business cycle",
            "timeframe": "month",
            "source_id": "nber_business_cycle_dates",
            "projection_status": "requires_owner_crosswalk_before_instrument_attachment",
            "accepted_source_label_target_slot": False,
            "rows": 0,
            "source_windows": [w.window_id for w in windows if w.source_id == "nber_business_cycle_dates"],
            "note": "NBER windows are primary macro dates, not instrument-specific price-root labels.",
        }
    )
    slots.append(
        {
            "root": "Sideways",
            "provider": "n/a",
            "instrument": "n/a",
            "timeframe": "n/a",
            "source_id": "none",
            "projection_status": "missing_dated_source_or_owner_approved_adjudication_protocol",
            "accepted_source_label_target_slot": False,
            "rows": 0,
            "source_windows": [],
            "note": "Sideways still needs a dated source or adjudication protocol; do not infer it from Bull/Bear residuals.",
        }
    )
    return slots


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "mainregimev2_source_window_attachability_v1.json"
    md_path = OUT_DIR / "mainregimev2_source_window_attachability_v1.md"
    csv_path = OUT_DIR / "mainregimev2_source_window_attachability_v1_summary.csv"
    checks_path = CHECK_DIR / "mainregimev2_source_window_attachability_v1_assertions.out"

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "root",
                "rule_name",
                "scope",
                "calibration_lcb",
                "test_lcb",
                "calibration_support",
                "test_support",
                "accepted_95_source_window_gate",
            ],
        )
        writer.writeheader()
        for scope, root_reports in report["calibrated_gate_reports"].items():
            for item in root_reports:
                writer.writerow(
                    {
                        "root": item["root"],
                        "rule_name": item["rule_name"],
                        "scope": scope,
                        "calibration_lcb": f"{item['calibration']['precision_wilson_lcb_95']:.6f}",
                        "test_lcb": f"{item['test']['precision_wilson_lcb_95']:.6f}",
                        "calibration_support": item["calibration"]["support"],
                        "test_support": item["test"]["support"],
                        "accepted_95_source_window_gate": item["accepted_95_source_window_gate"],
                    }
                )

    native_slots = [slot for slot in report["source_label_slots"] if slot["accepted_source_label_target_slot"]]
    native_bull = next(item for item in report["calibrated_gate_reports"]["native_gspc_1d"] if item["root"] == "Bull" and item["rule_name"].startswith("train_"))
    native_bear = next(item for item in report["calibrated_gate_reports"]["native_gspc_1d"] if item["root"] == "Bear" and item["rule_name"].startswith("train_"))

    md = f"""# MainRegimeV2 Source-Window Attachability v1

Run ID: `{RUN_ID}`

## Purpose

This run converts the positive source-window pivot into an attachability check. It separates three things that were getting conflated:

- source-label target slots;
- calibrated abstaining factor gates;
- full-market/full-timeframe completion.

## Source-Label Slots

Accepted native source-label target slots added: `{len(native_slots)}`.

| Root | Provider | Instrument | Timeframe | Rows | Status |
|---|---|---|---|---:|---|
"""
    for slot in report["source_label_slots"]:
        md += (
            f"| `{slot['root']}` | `{slot['provider']}` | `{slot['instrument']}` | "
            f"`{slot['timeframe']}` | `{slot['rows']}` | `{slot['projection_status']}` |\n"
        )

    md += f"""
## Native `^GSPC` Daily Gate

| Root | Rule | Calibration Wilson95 | Test Wilson95 | Calibration Support | Test Support | Accepted |
|---|---|---:|---:|---:|---:|---:|
| `Bull` | `{native_bull['rule']}` | `{native_bull['calibration']['precision_wilson_lcb_95']:.6f}` | `{native_bull['test']['precision_wilson_lcb_95']:.6f}` | `{native_bull['calibration']['support']}` | `{native_bull['test']['support']}` | `{native_bull['accepted_95_source_window_gate']}` |
| `Bear` | `{native_bear['rule']}` | `{native_bear['calibration']['precision_wilson_lcb_95']:.6f}` | `{native_bear['test']['precision_wilson_lcb_95']:.6f}` | `{native_bear['calibration']['support']}` | `{native_bear['test']['support']}` | `{native_bear['accepted_95_source_window_gate']}` |

## Decision

- Source-label target slots added: `{report['decision']['accepted_source_label_target_slots_added']}` for native `^GSPC` daily `Bull`/`Bear` closed Yardeni windows.
- Calibrated source-window gates accepted: `{', '.join(report['decision']['accepted_95_source_window_gates']) if report['decision']['accepted_95_source_window_gates'] else 'none'}`.
- Full objective achieved: `false`.
- Gate result: `{report['decision']['gate_result']}`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw yfinance cache committed: false.

## Next

Use the accepted `Bull` source-window gate as a positive bridge from source labels to a calibrated factor. Do not retry generic source scans. The next productive closure is either:

1. get an explicit owner-approved crosswalk for S&P 500 source windows to SPY/ES/timeframe projections, then rerun this same attachability check; or
2. define a dated `Sideways` adjudication protocol, because residual-from-Bull/Bear is still not a source label.
"""
    md_path.write_text(md)

    failed = []
    if report["decision"]["accepted_source_label_target_slots_added"] < 2:
        failed.append("expected_two_native_source_label_slots")
    if "Bull" not in report["decision"]["accepted_95_source_window_gates"]:
        failed.append("expected_bull_source_window_gate")
    checks = {
        "failed_assertions": failed,
        "json": repo_rel(json_path),
        "markdown": repo_rel(md_path),
        "summary_csv": repo_rel(csv_path),
        "raw_cache_dir": str(CACHE_DIR),
    }
    checks_path.write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n")
    if failed:
        raise AssertionError(failed)


def main() -> None:
    windows = load_source_windows()
    closed_windows = closed_yardeni_windows(windows)
    panel = build_panel(closed_windows)
    native = panel[panel["native_exact_source_slot"]].reset_index(drop=True)
    stress_1d = panel[panel["timeframe"].eq("1d")].reset_index(drop=True)

    reports: dict[str, list[dict[str, Any]]] = {
        "native_gspc_1d": [],
        "nonaccepted_1d_crosswalk_stress": [],
    }
    for root in ["Bull", "Bear"]:
        selected_native_rule = calibration_selected_rule(native, root)
        for rule in [existing_rule(root), selected_native_rule]:
            reports["native_gspc_1d"].append(evaluate_rule(native, root, rule))
        for rule in [existing_rule(root), selected_native_rule]:
            reports["nonaccepted_1d_crosswalk_stress"].append(evaluate_rule(stress_1d, root, rule))

    accepted_native_gates = sorted(
        {
            item["root"]
            for item in reports["native_gspc_1d"]
            if item["accepted_95_source_window_gate"] and item["rule_name"].startswith("train_")
        }
    )
    slots = source_label_slots(panel, windows)
    accepted_slots = [slot for slot in slots if slot["accepted_source_label_target_slot"]]

    report = {
        "run_id": RUN_ID,
        "board": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
        "purpose": "Attach positive source-window seeds to native yfinance ^GSPC daily slots and test train-only abstaining gates against closed Yardeni Bull/Bear windows.",
        "taxonomy": {
            "name": "MainRegimeV2",
            "price_roots": ["Bull", "Bear", "Sideways", "Crisis"],
            "direct_overlay_or_class": ["Manipulation"],
        },
        "source_policy": {
            "closed_yardeni_windows_used_for_native_acceptance": [w.window_id for w in closed_windows],
            "open_ended_yardeni_window_excluded_until_refresh": True,
            "crosswalks_not_owner_approved": ["SPY", "QQQ", "IWM", "ES=F", "1w"],
            "sideways_fail_closed": True,
            "nber_crisis_requires_owner_crosswalk_before_instrument_attachment": True,
        },
        "acceptance_source_window_95": NATIVE_ACCEPTANCE,
        "panel_profile": {
            "rows": int(len(panel)),
            "native_rows": int(len(native)),
            "tickers": sorted(panel["ticker"].dropna().astype(str).unique().tolist()),
            "timeframes": sorted(panel["timeframe"].dropna().astype(str).unique().tolist()),
            "closed_source_label_counts_native": native["source_root_label"].value_counts().sort_index().to_dict(),
            "split_counts_native": native["split"].value_counts().sort_index().to_dict(),
            "raw_cache_dir": str(CACHE_DIR),
        },
        "source_label_slots": slots,
        "calibrated_gate_reports": reports,
        "decision": {
            "accepted_source_label_target_slots_added": len(accepted_slots),
            "accepted_95_source_window_gates": accepted_native_gates,
            "accepted_full_objective_gate": "none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal",
            "full_objective_achieved": False,
            "gate_result": "accepted_native_bull_source_window_gate_and_two_sp500_source_label_slots_full_matrix_still_open",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
    }
    write_outputs(report)


if __name__ == "__main__":
    main()
