from __future__ import annotations

import csv
import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T012949-codex-tomac-gc-nq-main-regime-v2-root-gate"
ROOT_DIR = RUN_ROOT / "root-gate"
CHECKS_DIR = RUN_ROOT / "checks"
GC_CSV = Path("/Users/thrill3r/Downloads/Tomac/gc future 2021-2025/gc_201101_202604.csv")
NQ_RAR = Path("/Users/thrill3r/Downloads/Tomac/gc future 2021-2025/databento.rar")
NQ_MEMBER = "nq_201101_202604.csv"

ROOTS = ["Bull", "Bear", "Sideways", "Crisis", "Manipulation", "UnknownOrMixed"]
EVALUATED_ROOTS = ["Bull", "Bear", "Sideways", "Crisis"]
BLOCKED_PREDICTOR_PREFIXES = ("future_", "target_")
ACCEPTANCE_95 = {
    "precision_wilson_lcb_95_min": 0.95,
    "calibration_support_min": 120,
    "test_support_min": 60,
    "ece_max": 0.05,
    "coverage_min": 0.03,
    "validation_instruments_min": 2,
    "validation_market_contexts_min": 2,
    "validation_timeframes_min": 2,
}


@dataclass(frozen=True)
class Condition:
    feature: str
    op: str
    threshold: float

    @property
    def text(self) -> str:
        return f"{self.feature} {self.op} {self.threshold:.12g}"

    def mask(self, values: np.ndarray) -> np.ndarray:
        return values >= self.threshold if self.op == ">=" else values <= self.threshold


@dataclass(frozen=True)
class Candidate:
    rule: str
    features: tuple[str, ...]
    mask: np.ndarray


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson(success: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    center = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return (center - margin) / denom


def bucket(ts: str, timeframe: str) -> str:
    # Source files are sorted continuous futures bars in exchange-local timestamps.
    # Local calendar buckets are enough for this readback and avoid per-row tz parsing.
    if timeframe == "1h":
        return f"{ts[:13]}:00:00"
    return ts[:10]


def push_bar(out: list[dict[str, Any]], bar: dict[str, Any] | None) -> None:
    if bar is not None:
        out.append(bar)


def iter_plain_csv(path: Path) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle)


def iter_rar_member(rar_path: Path, member: str) -> Iterable[dict[str, str]]:
    proc = subprocess.Popen(
        ["bsdtar", "-xOf", str(rar_path), member],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.stdout is not None
    try:
        yield from csv.DictReader(proc.stdout)
    finally:
        stderr = proc.stderr.read() if proc.stderr is not None else ""
        code = proc.wait()
        if code != 0:
            raise RuntimeError(f"bsdtar failed for {member}: {stderr[:500]}")


def aggregate_rows(rows: Iterable[dict[str, str]], instrument: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    current: dict[str, dict[str, Any] | None] = {"1h": None, "1d": None}
    for row in rows:
        try:
            op = float(row["open"])
            hi = float(row["high"])
            lo = float(row["low"])
            cl = float(row["close"])
            vol = float(row["volume"])
        except (KeyError, TypeError, ValueError):
            continue
        ts = row["ts_event"]
        for timeframe in ("1h", "1d"):
            b = bucket(ts, timeframe)
            bar = current[timeframe]
            if bar is None or bar["ts"] != b:
                push_bar(out, bar)
                current[timeframe] = {
                    "ts": b,
                    "instrument": instrument,
                    "market": "Tomac_Databento",
                    "timeframe": timeframe,
                    "context": f"{instrument}:Tomac_Databento:{timeframe}",
                    "open": op,
                    "high": hi,
                    "low": lo,
                    "close": cl,
                    "volume": vol,
                }
            else:
                bar["high"] = max(float(bar["high"]), hi)
                bar["low"] = min(float(bar["low"]), lo)
                bar["close"] = cl
                bar["volume"] = float(bar["volume"]) + vol
    for bar in current.values():
        push_bar(out, bar)
    return out


def safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    return a / b.replace(0, np.nan)


def add_features(frame: pd.DataFrame) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for context, group in frame.groupby("context", sort=False):
        g = group.sort_values("ts").copy()
        close = g["close"].astype(float)
        high = g["high"].astype(float)
        low = g["low"].astype(float)
        ret1 = close.pct_change()
        g["ret_1"] = ret1
        for window in (4, 8, 16, 32, 64):
            g[f"ret_{window}"] = close.pct_change(window)
        g["range_pct"] = safe_div(high - low, close)
        g["vol16"] = ret1.rolling(16, min_periods=8).std()
        g["vol64"] = ret1.rolling(64, min_periods=16).std()
        ma64 = close.rolling(64, min_periods=32).mean()
        g["ma64_slope16"] = safe_div(ma64 - ma64.shift(16), ma64.shift(16))
        g["drawdown64"] = safe_div(close, close.rolling(64, min_periods=32).max()) - 1.0
        g["rally64"] = safe_div(close, close.rolling(64, min_periods=32).min()) - 1.0
        g["abs_ret16"] = g["ret_16"].abs()
        dc_threshold = ret1.abs().rolling(64, min_periods=16).median()
        dc_event = (ret1.abs() > dc_threshold).astype(float)
        g["dc_event_rate16"] = dc_event.rolling(16, min_periods=8).mean()
        g["dc_signed_rate16"] = (np.sign(ret1).fillna(0.0) * dc_event).rolling(16, min_periods=8).mean()
        g["dc_overshoot16"] = (ret1.abs() - dc_threshold).clip(lower=0.0).rolling(16, min_periods=8).sum()
        horizon = 16 if str(g["timeframe"].iloc[0]) == "1h" else 8
        g["future_ret_h"] = safe_div(close.shift(-horizon), close) - 1.0
        g["future_absret_h"] = g["future_ret_h"].abs()
        g["future_range_h"] = safe_div(
            high.shift(-1).iloc[::-1].rolling(horizon, min_periods=horizon).max().iloc[::-1]
            - low.shift(-1).iloc[::-1].rolling(horizon, min_periods=horizon).min().iloc[::-1],
            close,
        )
        n = len(g)
        split = np.array(["test"] * n, dtype=object)
        split[: int(n * 0.50)] = "train"
        split[int(n * 0.50) : int(n * 0.75)] = "calibration"
        g["split"] = split
        parts.append(g)
    return pd.concat(parts, ignore_index=True)


def finite_quantile(series: pd.Series, q: float) -> float:
    clean = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    return float(clean.quantile(q)) if not clean.empty else math.nan


def assign_labels(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["root_label"] = "UnknownOrMixed"
    for _, group in out.groupby("context", sort=False):
        train = group[group["split"] == "train"]
        q = {
            "ret_hi": finite_quantile(train["future_ret_h"], 0.65),
            "ret_lo": finite_quantile(train["future_ret_h"], 0.35),
            "abs_hi": finite_quantile(train["future_absret_h"], 0.90),
            "abs_lo": finite_quantile(train["future_absret_h"], 0.40),
            "range_hi": finite_quantile(train["future_range_h"], 0.90),
            "range_lo": finite_quantile(train["future_range_h"], 0.45),
        }
        idx = group.index
        future_ret = pd.to_numeric(out.loc[idx, "future_ret_h"], errors="coerce")
        future_abs = pd.to_numeric(out.loc[idx, "future_absret_h"], errors="coerce")
        future_range = pd.to_numeric(out.loc[idx, "future_range_h"], errors="coerce")
        crisis = (future_abs >= q["abs_hi"]) | (future_range >= q["range_hi"])
        sideways = (~crisis) & (future_abs <= q["abs_lo"]) & (future_range <= q["range_lo"])
        bull = (~crisis) & (~sideways) & (future_ret >= q["ret_hi"])
        bear = (~crisis) & (~sideways) & (future_ret <= q["ret_lo"])
        labels = pd.Series("UnknownOrMixed", index=idx)
        labels.loc[crisis.fillna(False)] = "Crisis"
        labels.loc[sideways.fillna(False)] = "Sideways"
        labels.loc[bull.fillna(False)] = "Bull"
        labels.loc[bear.fillna(False)] = "Bear"
        out.loc[idx, "root_label"] = labels
    return out


def metric(mask: np.ndarray, root: str, split: str, frame: pd.DataFrame) -> dict[str, Any]:
    selected = frame[mask & frame["split"].eq(split).to_numpy()]
    support = int(len(selected))
    success = int((selected["root_label"] == root).sum()) if support else 0
    precision = success / support if support else 0.0
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson(success, support),
        "coverage": support / max(1, int(frame["split"].eq(split).sum())),
        "validation_instruments": sorted(selected["instrument"].dropna().astype(str).unique().tolist()) if support else [],
        "validation_market_contexts": sorted(selected["market"].dropna().astype(str).unique().tolist()) if support else [],
        "validation_timeframes": sorted(selected["timeframe"].dropna().astype(str).unique().tolist()) if support else [],
        "validation_contexts": sorted(selected["context"].dropna().astype(str).unique().tolist()) if support else [],
    }


def blockers(cal: dict[str, Any], test: dict[str, Any], ece: float) -> list[str]:
    out: list[str] = []
    if cal["support"] < ACCEPTANCE_95["calibration_support_min"]:
        out.append("calibration_support_below_120")
    if test["support"] < ACCEPTANCE_95["test_support_min"]:
        out.append("test_support_below_60")
    if cal["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        out.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        out.append("test_wilson95_below_0_95")
    if cal["coverage"] < ACCEPTANCE_95["coverage_min"]:
        out.append("calibration_coverage_below_0_03")
    if test["coverage"] < ACCEPTANCE_95["coverage_min"]:
        out.append("test_coverage_below_0_03")
    if ece > ACCEPTANCE_95["ece_max"]:
        out.append("ece_above_0_05")
    if len(test["validation_instruments"]) < ACCEPTANCE_95["validation_instruments_min"]:
        out.append("validation_instruments_below_2")
    if len(test["validation_market_contexts"]) < ACCEPTANCE_95["validation_market_contexts_min"]:
        out.append("validation_market_contexts_below_2")
    if len(test["validation_timeframes"]) < ACCEPTANCE_95["validation_timeframes_min"]:
        out.append("validation_timeframes_below_2")
    return out


def evaluate(candidate: Candidate, root: str, frame: pd.DataFrame) -> dict[str, Any]:
    train = metric(candidate.mask, root, "train", frame)
    cal = metric(candidate.mask, root, "calibration", frame)
    test = metric(candidate.mask, root, "test", frame)
    ece = abs(test["precision"] - cal["precision"]) if cal["support"] else 1.0
    b = blockers(cal, test, ece)
    return {
        "rule": candidate.rule,
        "features": list(candidate.features),
        "train": train,
        "calibration": cal,
        "test": test,
        "ece": ece,
        "accepted_95": not b,
        "blockers": b,
    }


def feature_pool(root: str) -> list[str]:
    shared = ["ret_4", "ret_8", "ret_16", "ret_32", "ma64_slope16", "drawdown64", "rally64", "dc_signed_rate16", "dc_event_rate16", "dc_overshoot16", "vol16", "vol64"]
    if root in {"Bull", "Bear"}:
        return shared
    if root == "Sideways":
        return ["abs_ret16", "range_pct", "vol16", "vol64", "ma64_slope16", "dc_event_rate16", "dc_overshoot16", "drawdown64", "rally64"]
    return ["abs_ret16", "range_pct", "vol16", "vol64", "drawdown64", "rally64", "dc_event_rate16", "dc_overshoot16"]


def candidate_pool(frame: pd.DataFrame, root: str) -> list[Candidate]:
    features = [f for f in feature_pool(root) if f in frame.columns]
    arrays = {f: pd.to_numeric(frame[f], errors="coerce").to_numpy(dtype=float) for f in features}
    train_mask = frame["split"].eq("train").to_numpy()
    atoms: list[Candidate] = []
    for feature, values in arrays.items():
        train_values = values[train_mask]
        train_values = train_values[np.isfinite(train_values)]
        for q in (0.10, 0.20, 0.35, 0.50, 0.65, 0.80, 0.90):
            if train_values.size == 0:
                continue
            cut = float(np.quantile(train_values, q))
            for op in (">=", "<="):
                cond = Condition(feature, op, cut)
                atoms.append(Candidate(cond.text, (feature,), cond.mask(values)))
    atom_scores = [(evaluate(atom, root, frame)["train"]["precision_wilson_lcb_95"], atom) for atom in atoms]
    top_atoms = [atom for _, atom in sorted(atom_scores, key=lambda item: item[0], reverse=True)[:40]]
    candidates = list(top_atoms)
    for i, left in enumerate(top_atoms):
        for right in top_atoms[i + 1 :]:
            if left.features == right.features:
                continue
            candidates.append(Candidate(f"{left.rule} AND {right.rule}", left.features + right.features, left.mask & right.mask))
    unique: dict[str, Candidate] = {}
    for candidate in candidates:
        if not any(f.startswith(BLOCKED_PREDICTOR_PREFIXES) for f in candidate.features):
            unique.setdefault(candidate.rule, candidate)
    return list(unique.values())


def probe_root(root: str, frame: pd.DataFrame) -> dict[str, Any]:
    candidates = [evaluate(c, root, frame) for c in candidate_pool(frame, root)]
    train_viable = [
        c
        for c in candidates
        if c["train"]["support"] >= ACCEPTANCE_95["calibration_support_min"]
        and c["train"]["coverage"] >= ACCEPTANCE_95["coverage_min"]
        and len(c["train"]["validation_instruments"]) >= ACCEPTANCE_95["validation_instruments_min"]
        and len(c["train"]["validation_timeframes"]) >= ACCEPTANCE_95["validation_timeframes_min"]
    ]
    pool = train_viable or candidates
    selected = max(pool, key=lambda c: (c["train"]["precision_wilson_lcb_95"], c["calibration"]["precision_wilson_lcb_95"], c["calibration"]["support"]))
    best_test = max(candidates, key=lambda c: (c["test"]["precision_wilson_lcb_95"], c["test"]["support"]))
    return {
        "root_class": root,
        "state": "accepted_95" if selected["accepted_95"] else "blocked",
        "selected_candidate": selected,
        "candidate_count": len(candidates),
        "train_viable_candidate_count": len(train_viable),
        "selection_policy": "bounded_train_viable_pool_ranked_by_train_then_calibration; test held out for acceptance audit",
        "best_test_observed_not_accepted": {
            "rule": best_test["rule"],
            "test_wilson95": best_test["test"]["precision_wilson_lcb_95"],
            "test_support": best_test["test"]["support"],
            "blockers": best_test["blockers"],
            "note": "Exploratory only; not an acceptance basis because it is test-selected.",
        },
    }


def write_summary(path: Path, reports: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["root_class", "state", "selected_rule", "calibration_support", "calibration_wilson95", "test_support", "test_wilson95", "test_coverage", "ece", "test_instruments", "test_market_contexts", "test_timeframes", "blockers"],
        )
        writer.writeheader()
        for report in reports:
            selected = report["selected_candidate"]
            writer.writerow(
                {
                    "root_class": report["root_class"],
                    "state": report["state"],
                    "selected_rule": selected["rule"],
                    "calibration_support": selected["calibration"]["support"],
                    "calibration_wilson95": selected["calibration"]["precision_wilson_lcb_95"],
                    "test_support": selected["test"]["support"],
                    "test_wilson95": selected["test"]["precision_wilson_lcb_95"],
                    "test_coverage": selected["test"]["coverage"],
                    "ece": selected["ece"],
                    "test_instruments": ";".join(selected["test"]["validation_instruments"]),
                    "test_market_contexts": ";".join(selected["test"]["validation_market_contexts"]),
                    "test_timeframes": ";".join(selected["test"]["validation_timeframes"]),
                    "blockers": ";".join(selected["blockers"]),
                }
            )


def main() -> int:
    ROOT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    bars = aggregate_rows(iter_plain_csv(GC_CSV), "GC")
    bars.extend(aggregate_rows(iter_rar_member(NQ_RAR, NQ_MEMBER), "NQ"))
    frame = pd.DataFrame(bars).sort_values(["context", "ts"]).reset_index(drop=True)
    usable = assign_labels(add_features(frame)).dropna(subset=["future_ret_h", "future_absret_h", "future_range_h"]).copy()
    reports = [probe_root(root, usable) for root in EVALUATED_ROOTS]
    manipulation = {
        "root_class": "Manipulation",
        "state": "missing_required_inputs",
        "selected_candidate": {
            "rule": "aligned_historical_direct_L2_L3_MBO_order_lifecycle_inputs_present == true",
            "features": [],
            "train": {"support": 0, "success": 0, "precision": 0.0, "precision_wilson_lcb_95": 0.0, "coverage": 0.0, "validation_instruments": [], "validation_market_contexts": [], "validation_timeframes": [], "validation_contexts": []},
            "calibration": {"support": 0, "success": 0, "precision": 0.0, "precision_wilson_lcb_95": 0.0, "coverage": 0.0, "validation_instruments": [], "validation_market_contexts": [], "validation_timeframes": [], "validation_contexts": []},
            "test": {"support": 0, "success": 0, "precision": 0.0, "precision_wilson_lcb_95": 0.0, "coverage": 0.0, "validation_instruments": [], "validation_market_contexts": [], "validation_timeframes": [], "validation_contexts": []},
            "ece": 1.0,
            "accepted_95": False,
            "blockers": ["missing_required_inputs", "ohlcv_panel_not_direct_manipulation_evidence"],
        },
    }
    reports.append(manipulation)
    accepted_this_run = [r["root_class"] for r in reports if r["state"] == "accepted_95"]
    prior_accepted = ["Crisis"]
    current_accepted = sorted(set(prior_accepted) | set(accepted_this_run))
    missing = [root for root in ["Bull", "Bear", "Sideways", "Manipulation"] if root not in current_accepted]
    report = {
        "schema_version": "tomac-gc-nq-main-regime-v2-root-gate/v2",
        "loop_id": "20260511T012949+0800-codex-tomac-gc-nq-main-regime-v2-root-gate",
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Use the Tomac Databento GC/NQ 1m OHLCV panel as signed-direction/sideways input and rerun MainRegimeV2 95 gates over 1h/1d contexts.",
        "input_files": {"GC": str(GC_CSV), "NQ": f"{NQ_RAR}:{NQ_MEMBER}"},
        "row_count_after_resample": int(len(frame)),
        "row_count_after_features": int(len(usable)),
        "contexts": sorted(usable["context"].dropna().astype(str).unique().tolist()),
        "target_counts_by_split": {split: usable[usable["split"].eq(split)]["root_label"].value_counts().to_dict() for split in ["train", "calibration", "test"]},
        "acceptance_95": ACCEPTANCE_95,
        "feature_policy": {
            "future_target_predictors_blocked": True,
            "future_columns_used_for_labels_only": ["future_ret_h", "future_absret_h", "future_range_h"],
            "derived_feature_families": ["rolling_return_volatility", "drawdown_rally", "directional_change_style_event_rate"],
            "runtime_code_changed": False,
        },
        "root_reports": reports,
        "accepted_root_classes_95_this_run": accepted_this_run,
        "accepted_root_classes_95_current_evidence": current_accepted,
        "missing_root_classes_95_current_evidence": missing,
        "decision": {
            "board_state": "blocked",
            "accepted_gate": "partial_for_MainRegimeV2_Crisis_prior_only" if current_accepted == ["Crisis"] else "partial_for_MainRegimeV2",
            "thresholds_relaxed": False,
            "blocked_future_target_predictors": True,
            "fresh_calibration_rerun": True,
            "runtime_code_changed": False,
            "trade_usable": False,
            "blocker": "missing_root_classes_95=" + ",".join(missing),
            "next_action": "Acquire calibration-grade direct L2/L3/MBO/order-lifecycle/event data for Manipulation and add materially stronger cross-provider signed-direction/sideways features before rerunning unchanged MainRegimeV2 gates.",
        },
    }
    report_path = ROOT_DIR / "tomac_gc_nq_main_regime_v2_root_gate_report.json"
    summary_path = ROOT_DIR / "tomac_gc_nq_main_regime_v2_root_gate_summary.csv"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_summary(summary_path, reports)
    (CHECKS_DIR / "tomac_gc_nq_main_regime_v2_root_gate_assertions.out").write_text(
        "\n".join(
            [
                f"report: {repo_rel(report_path)}",
                f"summary: {repo_rel(summary_path)}",
                "runtime_code_changed: False",
                "thresholds_relaxed: False",
                "blocked_future_target_predictors: True",
                "fresh_calibration_rerun: True",
                "trade_usable: False",
                "accepted_root_classes_95_this_run: " + ",".join(accepted_this_run),
                "accepted_root_classes_95_current_evidence: " + ",".join(current_accepted),
                "missing_root_classes_95_current_evidence: " + ",".join(missing),
                "manipulation_input_state: missing_required_inputs",
                "GATE " + ("accepted_all_required_roots" if not missing else "blocked"),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (RUN_ROOT / "README.md").write_text(
        "# Tomac GC/NQ MainRegimeV2 Root Gate\n\n"
        "This run streams the local Tomac Databento GC/NQ 1m OHLCV panel, resamples to 1h/1d, "
        "derives past-only signed/range features, and keeps future columns label-only.\n\n"
        f"Result: {report['decision']['accepted_gate']}; {report['decision']['blocker']}.\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
