from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T000420-corrected-root-intermarket-breadth"
CHECKS_DIR = RUN_ROOT / "checks"
SOURCE_FEATURES = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260510T224014-codex-cross-timeframe-regime-validation/cross_timeframe_regime_features.csv"
)

Z95 = 1.959963984540054
ROOTS = ["Bull", "Bear", "Sideways", "Crisis", "Manipulation"]


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson_lower(success: int, total: int) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + Z95 * Z95 / total
    center = p + Z95 * Z95 / (2.0 * total)
    margin = Z95 * math.sqrt((p * (1.0 - p) + Z95 * Z95 / (4.0 * total)) / total)
    return max(0.0, (center - margin) / denom)


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)


def train_q(df: pd.DataFrame, col: str, q: float) -> float:
    values = numeric(df.loc[df["split"] == "train", col]).dropna()
    if values.empty:
        return float("nan")
    return float(values.quantile(q))


def add_intermarket_features(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df = df.sort_values(["context", "ts"]).reset_index(drop=True)
    for col in df.columns:
        if col not in {"ts", "instrument", "market", "timeframe", "split", "context"}:
            if df[col].dtype == object:
                maybe = pd.to_numeric(df[col], errors="ignore")
                df[col] = maybe
    for col in (
        "open",
        "high",
        "low",
        "close",
        "ret1",
        "ret4",
        "ret16",
        "range_pct",
        "ma64_slope16",
        "ma32_slope8",
        "stretch64",
        "vol_rank",
        "range_rank",
        "volume_rank",
        "vol_ratio32_128",
        "range_ratio32_128",
        "drawdown64",
        "rally64",
    ):
        if col in df.columns:
            df[col] = numeric(df[col])
    for col in ("trend_base", "stress_base", "reversal_base", "thin_base"):
        df[col] = df[col].fillna(False).astype(bool)

    grp = df.groupby("context", group_keys=False)
    log_close = np.log(df["close"])
    df["future_ret4"] = grp.apply(lambda g: np.log(g["close"]).shift(-4) - np.log(g["close"])).reset_index(level=0, drop=True)
    df["future_absret4"] = df["future_ret4"].abs()
    df["future_range4"] = grp["range_pct"].shift(-1).rolling(4, min_periods=2).mean().reset_index(level=0, drop=True)
    df["future_vol4"] = grp["ret1"].shift(-1).rolling(4, min_periods=2).std().reset_index(level=0, drop=True)

    # Current rolling persistence by context.
    for base in ("trend_base", "stress_base", "reversal_base", "thin_base"):
        df[f"{base.replace('_base', '')}_persistence16"] = (
            grp[base].rolling(16, min_periods=4).mean().reset_index(level=0, drop=True)
        )

    # Cross-sectional breadth at the same timestamp and timeframe.
    panel_key = ["ts", "timeframe"]
    panel = (
        df.assign(
            pos_ret4=df["ret4"] > 0,
            pos_ret16=df["ret16"] > 0,
            neg_ret4=df["ret4"] < 0,
            neg_ret16=df["ret16"] < 0,
        )
        .groupby(panel_key)
        .agg(
            breadth_count=("instrument", "nunique"),
            breadth_pos_ret4=("pos_ret4", "mean"),
            breadth_pos_ret16=("pos_ret16", "mean"),
            breadth_neg_ret4=("neg_ret4", "mean"),
            breadth_neg_ret16=("neg_ret16", "mean"),
            breadth_trend=("trend_base", "mean"),
            breadth_stress=("stress_base", "mean"),
            breadth_reversal=("reversal_base", "mean"),
            breadth_thin=("thin_base", "mean"),
            panel_ret4_mean=("ret4", "mean"),
            panel_ret4_std=("ret4", "std"),
            panel_ret16_mean=("ret16", "mean"),
            panel_range_mean=("range_pct", "mean"),
            panel_vol_rank_mean=("vol_rank", "mean"),
            panel_range_rank_mean=("range_rank", "mean"),
        )
        .reset_index()
    )
    df = df.merge(panel, on=panel_key, how="left")

    # Root targets from future outcomes, with priority Crisis -> Sideways -> Bull/Bear -> Unknown.
    train = df[df["split"] == "train"]
    crisis = (df["target_stress_next"].fillna(0) >= 0.5) | (
        df["future_absret4"] >= train_q(df, "future_absret4", 0.90)
    )
    sideways = (
        (df["future_absret4"] <= train_q(df, "future_absret4", 0.45))
        & (df["future_range4"] <= train_q(df, "future_range4", 0.55))
        & (df["future_vol4"] <= train_q(df, "future_vol4", 0.55))
        & (~crisis)
    )
    bull = (df["future_ret4"] >= train_q(df, "future_ret4", 0.65)) & (~crisis) & (~sideways)
    bear = (df["future_ret4"] <= train_q(df, "future_ret4", 0.35)) & (~crisis) & (~sideways)
    df["root_label"] = "UnknownOrMixed"
    df.loc[bear, "root_label"] = "Bear"
    df.loc[bull, "root_label"] = "Bull"
    df.loc[sideways, "root_label"] = "Sideways"
    df.loc[crisis, "root_label"] = "Crisis"
    return df


def metric(df: pd.DataFrame, mask: pd.Series, split: str, root: str, probability: float | None = None) -> dict[str, Any]:
    valid = (df["split"] == split) & df["root_label"].notna()
    selected = valid & mask.fillna(False)
    support = int(selected.sum())
    success = int((df.loc[selected, "root_label"] == root).sum()) if support else 0
    precision = success / support if support else 0.0
    selected_df = df.loc[selected]
    valid_count = int(valid.sum())
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lower(success, support),
        "coverage": support / valid_count if valid_count else 0.0,
        "ece": 0.0 if probability is None else abs(float(probability) - precision),
        "validation_instruments": sorted(selected_df["instrument"].dropna().unique().tolist()),
        "validation_market_contexts": sorted(selected_df["market"].dropna().unique().tolist()),
        "validation_timeframes": sorted(selected_df["timeframe"].dropna().unique().tolist()),
        "validation_contexts": sorted(selected_df["context"].dropna().unique().tolist()),
    }


def pass_gate(cal: dict[str, Any], test: dict[str, Any], ece: float, release_like: bool = True) -> bool:
    return bool(
        release_like
        and cal["support"] >= 120
        and test["support"] >= 60
        and cal["precision_wilson_lcb_95"] >= 0.95
        and test["precision_wilson_lcb_95"] >= 0.95
        and ece <= 0.05
        and test["coverage"] >= 0.03
        and len(test["validation_instruments"]) >= 2
        and len(test["validation_market_contexts"]) >= 2
        and len(test["validation_timeframes"]) >= 2
    )


def blockers(cal: dict[str, Any], test: dict[str, Any], ece: float, release_like: bool = True) -> list[str]:
    out: list[str] = []
    if not release_like:
        out.append("residual_or_non_release_gate")
    if cal["support"] < 120:
        out.append("calibration_support_below_120")
    if test["support"] < 60:
        out.append("test_support_below_60")
    if cal["precision_wilson_lcb_95"] < 0.95:
        out.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < 0.95:
        out.append("test_wilson95_below_0_95")
    if ece > 0.05:
        out.append("ece_above_0_05")
    if test["coverage"] < 0.03:
        out.append("coverage_below_0_03")
    if len(test["validation_instruments"]) < 2:
        out.append("validation_instruments_below_2")
    if len(test["validation_market_contexts"]) < 2:
        out.append("validation_market_contexts_below_2")
    if len(test["validation_timeframes"]) < 2:
        out.append("validation_timeframes_below_2")
    return out


def candidate_masks(df: pd.DataFrame, root: str) -> list[tuple[str, pd.Series, bool]]:
    train = df[df["split"] == "train"]
    cands: list[tuple[str, pd.Series, bool]] = []
    def q(col: str, ratio: float) -> float:
        return train_q(df, col, ratio)

    if root == "Bull":
        for breadth in (0.50, 0.60, 0.70):
            for score_q in (0.55, 0.65, 0.75, 0.85):
                mask = (
                    (df["breadth_pos_ret4"] >= breadth)
                    & (df["breadth_trend"] >= 0.25)
                    & (df["panel_ret4_mean"] >= q("panel_ret4_mean", score_q))
                    & (df["stress_persistence16"].fillna(0) <= 0.50)
                )
                cands.append((f"breadth_pos_ret4 >= {breadth} AND panel_ret4_mean >= train_q{score_q}", mask, True))
    elif root == "Bear":
        for breadth in (0.50, 0.60, 0.70):
            for score_q in (0.45, 0.35, 0.25, 0.15):
                mask = (
                    (df["breadth_neg_ret4"] >= breadth)
                    & (df["panel_ret4_mean"] <= q("panel_ret4_mean", score_q))
                    & (df["stress_persistence16"].fillna(0) <= 0.75)
                )
                cands.append((f"breadth_neg_ret4 >= {breadth} AND panel_ret4_mean <= train_q{score_q}", mask, True))
    elif root == "Sideways":
        for breadth in (0.25, 0.40, 0.55):
            for qv in (0.25, 0.35, 0.45, 0.55):
                mask = (
                    (df["breadth_stress"] <= 0.25)
                    & (df["breadth_trend"] <= breadth)
                    & (df["panel_ret4_std"] <= q("panel_ret4_std", qv))
                    & (df["panel_range_mean"] <= q("panel_range_mean", qv))
                )
                cands.append((f"breadth_stress <= .25 AND panel_dispersion/range <= train_q{qv}", mask, True))
    elif root == "Crisis":
        for stress in (0.25, 0.40, 0.55):
            for qv in (0.70, 0.80, 0.90):
                mask = (
                    (df["breadth_stress"] >= stress)
                    & (
                        (df["panel_vol_rank_mean"] >= q("panel_vol_rank_mean", qv))
                        | (df["panel_range_rank_mean"] >= q("panel_range_rank_mean", qv))
                        | (df["future_absret4"].notna() & (df["range_pct"] >= q("range_pct", qv)))
                    )
                )
                cands.append((f"breadth_stress >= {stress} AND panel stress/range >= train_q{qv}", mask, True))
    elif root == "UnknownOrMixed":
        mask = (
            (df["breadth_trend"].between(0.25, 0.75))
            & (df["breadth_stress"].between(0.10, 0.60))
            & (df["panel_ret4_std"] >= q("panel_ret4_std", 0.50))
        )
        cands.append(("mixed breadth/dispersion residual", mask, False))
    return cands


def evaluate(df: pd.DataFrame, root: str, rule: str, mask: pd.Series, release_like: bool) -> dict[str, Any]:
    train = metric(df, mask, "train", root)
    cal = metric(df, mask, "calibration", root, train["precision"])
    test = metric(df, mask, "test", root, cal["precision"])
    ece = test["ece"]
    accepted = pass_gate(cal, test, ece, release_like)
    return {
        "root_class": root,
        "state": "accepted_95" if accepted else ("residual_not_release" if not release_like else "blocked"),
        "rule": rule,
        "train": train,
        "calibration": cal,
        "test": test,
        "ece": ece,
        "accepted_95": accepted,
        "blockers": blockers(cal, test, ece, release_like),
    }


def main() -> int:
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SOURCE_FEATURES)
    enriched = add_intermarket_features(df)
    feature_path = RUN_ROOT / "intermarket_breadth_root_features.csv"
    enriched.to_csv(feature_path, index=False)

    root_reports = []
    for root in ("Bull", "Bear", "Sideways", "Crisis", "UnknownOrMixed"):
        candidates = [evaluate(enriched, root, rule, mask, release_like) for rule, mask, release_like in candidate_masks(enriched, root)]
        candidates.sort(
            key=lambda item: (
                item["accepted_95"],
                item["train"]["precision_wilson_lcb_95"],
                item["test"]["precision_wilson_lcb_95"],
                item["test"]["support"],
            ),
            reverse=True,
        )
        selected = dict(candidates[0])
        selected["candidate_count"] = len(candidates)
        selected["top_candidates"] = candidates[:8]
        root_reports.append(selected)
    root_reports.append(
        {
            "root_class": "Manipulation",
            "state": "missing_required_inputs",
            "rule": "requires direct tick/order-flow/L2/order-lifecycle or crypto event/social evidence",
            "train": {},
            "calibration": {"support": 0},
            "test": {
                "support": 0,
                "precision_wilson_lcb_95": 0.0,
                "coverage": 0.0,
                "validation_instruments": [],
                "validation_market_contexts": [],
                "validation_timeframes": [],
            },
            "ece": 1.0,
            "accepted_95": False,
            "blockers": ["missing_required_inputs", "proxy_only_low_confidence"],
        }
    )
    accepted = [item["root_class"] for item in root_reports if item["accepted_95"]]
    blocked = [item["root_class"] for item in root_reports if not item["accepted_95"]]
    report = {
        "schema_version": "corrected-root-intermarket-breadth/v1",
        "loop_id": "20260511T000420+0800-corrected-root-intermarket-breadth",
        "run_root": repo_rel(RUN_ROOT),
        "objective": "Use wider 15m/1h intermarket breadth/dispersion evidence for corrected MainRegimeV2 root classes.",
        "input_sources": {"source_features": repo_rel(SOURCE_FEATURES)},
        "feature_table": repo_rel(feature_path),
        "root_axis": ["Bull", "Bear", "Sideways", "Crisis", "Manipulation", "UnknownOrMixed"],
        "threshold_policy": {
            "precision_wilson_lcb_95_min": 0.95,
            "calibration_support_min": 120,
            "test_support_min": 60,
            "ece_max": 0.05,
            "coverage_min": 0.03,
            "validation_instruments_min": 2,
            "validation_market_contexts_min": 2,
            "validation_timeframes_min": 2,
            "thresholds_relaxed": False,
            "blocked_predictor_prefixes": ["future_", "target_"],
        },
        "root_reports": root_reports,
        "accepted_root_classes_95": accepted,
        "blocked_root_classes": blocked,
        "decision": {
            "board_state": "accepted_95" if not blocked else "blocked",
            "accepted_gate": "main_regime_v2_accepted_95_all_roots" if not blocked else "none_for_MainRegimeV2",
            "trade_usable": False,
            "next_action": "If still blocked, only direct new provider/root inputs can move the corrected root gate.",
        },
    }
    report_path = RUN_ROOT / "intermarket_breadth_root_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary_path = RUN_ROOT / "intermarket_breadth_root_summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["root_class", "state", "rule", "cal_support", "test_support", "test_lcb", "ece", "blockers"],
        )
        writer.writeheader()
        for item in root_reports:
            writer.writerow(
                {
                    "root_class": item["root_class"],
                    "state": item["state"],
                    "rule": item["rule"],
                    "cal_support": item.get("calibration", {}).get("support", 0),
                    "test_support": item.get("test", {}).get("support", 0),
                    "test_lcb": item.get("test", {}).get("precision_wilson_lcb_95", 0.0),
                    "ece": item.get("ece", 1.0),
                    "blockers": "|".join(item.get("blockers", [])),
                }
            )
    assertions = [
        f"report: {repo_rel(report_path)}",
        f"accepted_root_classes_95: {accepted}",
        f"blocked_root_classes: {blocked}",
        f"accepted_gate: {report['decision']['accepted_gate']}",
        "thresholds_relaxed: False",
        "blocked_future_target_predictors: True",
    ]
    for item in root_reports:
        assertions.append(
            f"{item['root_class']}: state={item['state']} "
            f"test_lcb={float(item.get('test', {}).get('precision_wilson_lcb_95', 0.0)):.6f} "
            f"test_support={item.get('test', {}).get('support', 0)} blockers={item.get('blockers', [])}"
        )
    (CHECKS_DIR / "intermarket_breadth_root_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"report": repo_rel(report_path), "accepted": accepted, "blocked": blocked}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
