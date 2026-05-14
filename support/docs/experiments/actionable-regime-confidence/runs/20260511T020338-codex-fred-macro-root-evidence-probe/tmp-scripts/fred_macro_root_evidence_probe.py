from __future__ import annotations

import json
import math
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.request import urlopen

import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T020338-codex-fred-macro-root-evidence-probe"
)
OUT_DIR = RUN_ROOT / "root-macro"
CHECKS_DIR = RUN_ROOT / "checks"
LOOP_ID = "20260511T020338+0800-codex-fred-macro-root-evidence-probe"
SOURCE_TABLE = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T001642-cross-asset-root-evidence-yfinance/root-v2/"
    "cross_asset_root_feature_table.csv"
)

FRED_SERIES = {
    "T10Y2Y": "treasury_10y_2y_spread",
    "T10Y3M": "treasury_10y_3m_spread",
    "BAMLH0A0HYM2": "high_yield_oas",
    "BAMLC0A0CM": "corp_oas",
    "NFCI": "financial_conditions",
    "VIXCLS": "fred_vix_close",
}

ROOT_CLASSES = ("Bull", "Bear", "Sideways", "Crisis")
MIN_SUPPORT = 50


@dataclass(frozen=True)
class Condition:
    name: str
    feature: str
    op: str
    threshold: float


def repo_rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def wilson_lcb(successes: int, total: int, z: float = 1.96) -> float:
    if total <= 0:
        return 0.0
    p = successes / total
    denom = 1 + z * z / total
    centre = p + z * z / (2 * total)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total)
    return max(0.0, (centre - margin) / denom)


def fetch_fred_series(series_id: str, output_name: str) -> pd.DataFrame:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    with urlopen(url, timeout=30) as response:
        raw = response.read().decode("utf-8")
    df = pd.read_csv(StringIO(raw))
    date_column = df.columns[0]
    value_column = df.columns[1]
    df = df.rename(columns={date_column: "date", value_column: output_name})
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df[output_name] = pd.to_numeric(df[output_name].replace(".", pd.NA), errors="coerce")
    return df[["date", output_name]].dropna()


def build_macro_table() -> pd.DataFrame:
    merged: pd.DataFrame | None = None
    for series_id, output_name in FRED_SERIES.items():
        series = fetch_fred_series(series_id, output_name)
        merged = series if merged is None else merged.merge(series, on="date", how="outer")
    assert merged is not None
    merged = merged.sort_values("date")
    for column in list(FRED_SERIES.values()):
        merged[column] = merged[column].ffill()
        merged[f"{column}_chg5"] = merged[column].diff(5)
        merged[f"{column}_chg20"] = merged[column].diff(20)
        merged[f"{column}_rank252"] = merged[column].rolling(252, min_periods=80).rank(pct=True)
    return merged


def feature_table_with_macro() -> pd.DataFrame:
    source = pd.read_csv(SOURCE_TABLE)
    source["ts"] = pd.to_datetime(source["ts"], errors="coerce", utc=True)
    source["date"] = source["ts"].dt.date
    macro = build_macro_table()
    merged = source.merge(macro, on="date", how="left")
    macro_columns = [col for col in macro.columns if col != "date"]
    merged[macro_columns] = merged[macro_columns].ffill()
    return merged


def condition_mask(df: pd.DataFrame, condition: Condition) -> pd.Series:
    values = pd.to_numeric(df[condition.feature], errors="coerce")
    if condition.op == ">=":
        return values >= condition.threshold
    if condition.op == "<=":
        return values <= condition.threshold
    raise ValueError(condition.op)


def eval_mask(df: pd.DataFrame, mask: pd.Series, root_class: str) -> dict[str, Any]:
    selected = df[mask.fillna(False)]
    total = int(len(selected))
    positives = int((selected["root_label"] == root_class).sum()) if total else 0
    instruments = sorted(str(x) for x in selected.get("instrument", pd.Series(dtype=str)).dropna().unique())
    contexts = sorted(str(x) for x in selected.get("market", pd.Series(dtype=str)).dropna().unique())
    timeframes = sorted(str(x) for x in selected.get("timeframe", pd.Series(dtype=str)).dropna().unique())
    return {
        "support": total,
        "positives": positives,
        "precision": positives / total if total else 0.0,
        "wilson95_lcb": wilson_lcb(positives, total),
        "instruments": instruments,
        "market_contexts": contexts,
        "timeframes": timeframes,
    }


def candidate_conditions(train: pd.DataFrame, features: list[str]) -> list[Condition]:
    quantiles = (0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.7, 0.8, 0.9, 0.95, 0.98, 0.99)
    out: list[Condition] = []
    for feature in features:
        values = pd.to_numeric(train[feature], errors="coerce").dropna()
        if values.nunique() < 5:
            continue
        for q, threshold in values.quantile(quantiles).items():
            if not math.isfinite(float(threshold)):
                continue
            out.append(Condition(f"{feature} >= {threshold:.12g}", feature, ">=", float(threshold)))
            out.append(Condition(f"{feature} <= {threshold:.12g}", feature, "<=", float(threshold)))
    return out


def select_rule(df: pd.DataFrame, root_class: str, features: list[str]) -> dict[str, Any]:
    split = {name: df[df["split"] == name].copy() for name in ("train", "calibration", "test")}
    if split["calibration"].empty and "cal" in set(df["split"].dropna()):
        split["calibration"] = df[df["split"] == "cal"].copy()
    train = split["train"]
    cal = split["calibration"]
    test = split["test"]

    single_scores: list[tuple[float, float, int, Condition]] = []
    for condition in candidate_conditions(train, features):
        metrics = eval_mask(train, condition_mask(train, condition), root_class)
        if metrics["support"] >= MIN_SUPPORT:
            single_scores.append(
                (
                    metrics["wilson95_lcb"],
                    metrics["precision"],
                    metrics["support"],
                    condition,
                )
            )
    single_scores.sort(reverse=True, key=lambda item: (item[0], item[1], item[2]))
    top_conditions = [item[3] for item in single_scores[:30]]

    candidates: list[tuple[float, float, int, str, pd.Series]] = []
    for condition in top_conditions:
        mask = condition_mask(train, condition)
        metrics = eval_mask(train, mask, root_class)
        candidates.append((metrics["wilson95_lcb"], metrics["precision"], metrics["support"], condition.name, mask))

    for i, left in enumerate(top_conditions):
        left_mask = condition_mask(train, left)
        for right in top_conditions[i + 1 :]:
            if left.feature == right.feature:
                continue
            mask = left_mask & condition_mask(train, right)
            metrics = eval_mask(train, mask, root_class)
            if metrics["support"] >= MIN_SUPPORT:
                rule = f"{left.name} AND {right.name}"
                candidates.append((metrics["wilson95_lcb"], metrics["precision"], metrics["support"], rule, mask))

    if not candidates:
        return {
            "root_class": root_class,
            "state": "blocked",
            "rule": "no_train_candidate_with_min_support",
            "train": eval_mask(train, pd.Series(False, index=train.index), root_class),
            "calibration": eval_mask(cal, pd.Series(False, index=cal.index), root_class),
            "test": eval_mask(test, pd.Series(False, index=test.index), root_class),
            "blockers": ["no_train_candidate_with_min_support"],
        }

    candidates.sort(reverse=True, key=lambda item: (item[0], item[1], item[2]))
    _, _, _, selected_rule, _ = candidates[0]

    def apply_rule(frame: pd.DataFrame) -> pd.Series:
        parts = selected_rule.split(" AND ")
        mask = pd.Series(True, index=frame.index)
        for part in parts:
            if " >= " in part:
                feature, threshold = part.split(" >= ")
                mask &= condition_mask(frame, Condition(part, feature, ">=", float(threshold)))
            elif " <= " in part:
                feature, threshold = part.split(" <= ")
                mask &= condition_mask(frame, Condition(part, feature, "<=", float(threshold)))
            else:
                raise ValueError(part)
        return mask

    train_metrics = eval_mask(train, apply_rule(train), root_class)
    cal_metrics = eval_mask(cal, apply_rule(cal), root_class)
    test_metrics = eval_mask(test, apply_rule(test), root_class)
    blockers = []
    if cal_metrics["support"] < MIN_SUPPORT:
        blockers.append("calibration_support_below_50")
    if test_metrics["support"] < MIN_SUPPORT:
        blockers.append("test_support_below_50")
    if cal_metrics["wilson95_lcb"] < 0.95:
        blockers.append("calibration_wilson95_below_0_95")
    if test_metrics["wilson95_lcb"] < 0.95:
        blockers.append("test_wilson95_below_0_95")
    if len(test_metrics["instruments"]) < 2:
        blockers.append("test_instruments_below_2")
    if len(test_metrics["market_contexts"]) < 2:
        blockers.append("test_market_contexts_below_2")
    if len(test_metrics["timeframes"]) < 2:
        blockers.append("test_timeframes_below_2")

    return {
        "root_class": root_class,
        "state": "accepted_95" if not blockers else "blocked",
        "rule": selected_rule,
        "train": train_metrics,
        "calibration": cal_metrics,
        "test": test_metrics,
        "blockers": blockers,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    df = feature_table_with_macro()
    macro_features = [col for col in df.columns if col.startswith(tuple(FRED_SERIES.values()))]
    context_features = [
        "vix_level_rank252",
        "vix3m_vix_log_ratio",
        "vix_term_rank252",
        "cross_asset_risk_on_score16",
        "credit_breadth_score16",
        "crypto_risk_score16",
        "macro_stress_score16",
        "qqq_spy_rel16",
        "iwm_spy_rel16",
        "rsp_spy_rel16",
        "xly_xlp_rel16",
        "hyg_lqd_rel16",
        "eth_btc_rel16",
    ]
    features = [col for col in macro_features + context_features if col in df.columns]
    usable = df[df["root_label"].isin(ROOT_CLASSES)].copy()
    results = [select_rule(usable, root_class, features) for root_class in ROOT_CLASSES]
    accepted = [row["root_class"] for row in results if row["state"] == "accepted_95"]
    missing = [row["root_class"] for row in results if row["state"] != "accepted_95"]
    decision = {
        "board_state": "blocked",
        "active_axis": "MainRegimeV2",
        "candidate_regimes": list(ROOT_CLASSES),
        "accepted_95_root_classes_from_this_run": accepted,
        "missing_95_root_classes_from_this_run": missing,
        "accepted_gate": "partial_for_MainRegimeV2_Crisis_only_prior_evidence_preserved"
        if accepted == ["Crisis"]
        else "none_for_new_macro_roots"
        if not accepted
        else "partial_for_macro_root_probe",
        "thresholds_relaxed": False,
        "runtime_code_changed": False,
        "fresh_calibration_rerun": True,
        "blocked_future_target_predictors": True,
        "trade_usable": False,
        "blocker": (
            "FRED macro/credit/rates evidence did not close every missing active root at unchanged 95 gates; "
            "Manipulation still requires labeled direct data."
        ),
        "next_action": (
            "Add materially different signed-direction/sideways evidence such as breadth constituent counts, "
            "options/dealer positioning, or labeled macro regime datasets before rerunning Bull/Bear/Sideways gates."
        ),
    }
    report = {
        "schema_version": "fred-macro-root-evidence-probe/v1",
        "loop_id": LOOP_ID,
        "run_root": repo_rel(RUN_ROOT),
        "source_table": repo_rel(SOURCE_TABLE),
        "fred_series": FRED_SERIES,
        "rows": int(len(usable)),
        "features_used": features,
        "results": results,
        "decision": decision,
    }
    report_json = OUT_DIR / "fred_macro_root_evidence_probe_report.json"
    summary_csv = OUT_DIR / "fred_macro_root_evidence_probe_summary.csv"
    feature_csv = OUT_DIR / "fred_macro_root_feature_table_sample.csv"
    report_md = OUT_DIR / "fred_macro_root_evidence_probe_report.md"
    report_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(
        [
            {
                "root_class": row["root_class"],
                "state": row["state"],
                "rule": row["rule"],
                "cal_support": row["calibration"]["support"],
                "cal_lcb": row["calibration"]["wilson95_lcb"],
                "test_support": row["test"]["support"],
                "test_lcb": row["test"]["wilson95_lcb"],
                "test_instruments": ";".join(row["test"]["instruments"]),
                "test_market_contexts": ";".join(row["test"]["market_contexts"]),
                "test_timeframes": ";".join(row["test"]["timeframes"]),
                "blockers": ";".join(row["blockers"]),
            }
            for row in results
        ]
    ).to_csv(summary_csv, index=False)
    usable[["ts", "instrument", "market", "timeframe", "split", "root_label", *features]].head(2000).to_csv(
        feature_csv, index=False
    )
    lines = [
        "# FRED Macro Root Evidence Probe",
        "",
        f"Run id: `{LOOP_ID}`",
        "",
        "This probe joins public FRED rates/credit/financial-condition series to the existing cross-market root feature table and reruns unchanged train-selected root gates. It does not use `future_*` or `target_*` fields as predictors.",
        "",
        f"Rows evaluated: {len(usable)}.",
        f"Features used: {', '.join(features)}.",
        "",
        "| Root | State | Rule | Cal LCB | Test LCB | Test Support | Blockers |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for row in results:
        lines.append(
            "| {root} | {state} | `{rule}` | {cal:.6f} | {test:.6f} | {support} | {blockers} |".format(
                root=row["root_class"],
                state=row["state"],
                rule=row["rule"],
                cal=row["calibration"]["wilson95_lcb"],
                test=row["test"]["wilson95_lcb"],
                support=row["test"]["support"],
                blockers=", ".join(row["blockers"]) or "none",
            )
        )
    lines.extend(
        [
            "",
            f"Decision: `{decision['accepted_gate']}`.",
            f"Accepted from this run: {', '.join(accepted) or 'none'}.",
            f"Missing from this run: {', '.join(missing) or 'none'}.",
            "Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.",
        ]
    )
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (CHECKS_DIR / "fred_macro_root_evidence_probe_assertions.out").write_text(
        "\n".join(
            [
                f"RUN_ID {LOOP_ID}",
                f"REPORT {repo_rel(report_json)}",
                f"SUMMARY {repo_rel(summary_csv)}",
                f"ROWS {len(usable)}",
                f"ACCEPTED_FROM_THIS_RUN {','.join(accepted) or 'none'}",
                f"MISSING_FROM_THIS_RUN {','.join(missing) or 'none'}",
                "BLOCKED_FUTURE_TARGET_PREDICTORS true",
                "THRESHOLDS_RELAXED false",
                "RUNTIME_CODE_CHANGED false",
                "FRESH_CALIBRATION_RERUN true",
                "TRADE_USABLE false",
                f"GATE {decision['accepted_gate']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (RUN_ROOT / "README.md").write_text(
        "# FRED Macro Root Evidence Probe\n\n"
        "Public FRED macro/credit/rates sidecar for MainRegimeV2 Bull/Bear/Sideways/Crisis root gates.\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
