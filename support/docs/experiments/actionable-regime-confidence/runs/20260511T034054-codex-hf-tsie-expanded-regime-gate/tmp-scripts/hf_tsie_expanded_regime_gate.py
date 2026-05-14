#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

sys.path.insert(0, "/private/tmp/ict_py39_polars")

import numpy as np
import polars as pl


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T034054+0800-codex-hf-tsie-expanded-regime-gate"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T034054-codex-hf-tsie-expanded-regime-gate"
OUT_DIR = RUN_ROOT / "hf-tsie-expanded-gate"
CHECK_DIR = RUN_ROOT / "checks"
TMP_RAW_DIR = Path("/private/tmp/ict-regime-hf-tsie")
TMP_POLARS_TARGET = Path("/private/tmp/ict_py39_polars")

DATASET_ID = "sujinwo/tsie-market-regime-dataset"
DATASET_PAGE = f"https://huggingface.co/datasets/{DATASET_ID}"
PARQUET_URL = f"{DATASET_PAGE}/resolve/main/tft_dataset_labeled.parquet"
PARQUET_PATH = TMP_RAW_DIR / "tft_dataset_labeled.parquet"
README_URL = f"{DATASET_PAGE}/resolve/main/README.md"

ROOTS = ["BullExpansion", "BearExpansion", "SidewaysConsolidation"]
ACTIVE_TIMEFRAME_SUFFIXES = {"240", "1D"}
BOUNDED_ROW_STRIDE = 1
LABEL_MAP = {
    6: "BullExpansion",  # STRONG BUY
    0: "BearExpansion",  # STRONG SELL
    3: "SidewaysConsolidation",  # FLAT / NOISE
}
RAW_LABEL_NAMES = {
    0: "STRONG SELL",
    1: "WEAK SELL",
    2: "BEAR TRAP",
    3: "FLAT / NOISE",
    4: "BULL TRAP",
    5: "WEAK BUY",
    6: "STRONG BUY",
}
FEATURES = [
    "log_return",
    "price_norm",
    "volume_norm",
    "volatility",
    "momentum_3",
    "momentum_10",
    "macd_norm",
    "atr_norm",
    "bb_pos",
    "is_opening",
    "is_closing",
    "is_session_1",
    "is_session_2",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
]
BLOCKED_COLUMNS = ["future_volatility", "trend_return", "target_return", "regime_label"]
Z95 = 1.959963984540054
SUPPORT_TRAIN_MIN = 500
SUPPORT_CAL_MIN = 120
SUPPORT_TEST_MIN = 60
COVERAGE_MIN = 0.03
ECE_MAX = 0.05


@dataclass(frozen=True)
class Candidate:
    method: str
    rule: str
    mask: np.ndarray


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


def ensure_parquet() -> dict[str, Any]:
    TMP_RAW_DIR.mkdir(parents=True, exist_ok=True)
    if not PARQUET_PATH.exists() or PARQUET_PATH.stat().st_size < 500_000_000:
        req = Request(PARQUET_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=120) as response:
            PARQUET_PATH.write_bytes(response.read())
    return {
        "dataset_id": DATASET_ID,
        "dataset_page": DATASET_PAGE,
        "parquet_url": PARQUET_URL,
        "parquet_path": str(PARQUET_PATH),
        "parquet_bytes": PARQUET_PATH.stat().st_size,
        "raw_committed_to_repo": False,
        "polars_target": str(TMP_POLARS_TARGET),
    }


def fetch_readme_excerpt() -> str:
    try:
        req = Request(README_URL, headers={"User-Agent": "Mozilla/5.0"})
        text = urlopen(req, timeout=30).read().decode("utf-8", errors="replace")
    except Exception as exc:
        return f"README fetch failed: {type(exc).__name__}: {exc}"
    keep: list[str] = []
    for line in text.splitlines():
        if "STRONG SELL" in line or "FLAT / NOISE" in line or "STRONG BUY" in line:
            keep.append(line.strip())
        if "not future-leakage" in line.lower():
            keep.append(line.strip())
    return " | ".join(keep[:8])


def load_frame() -> pl.DataFrame:
    cols = [
        "group_id",
        "time_idx",
        "time",
        "regime_label",
    ] + FEATURES + BLOCKED_COLUMNS[:-1]
    df = pl.read_parquet(PARQUET_PATH, columns=cols)
    label_expr = pl.lit("UnknownOrMixed")
    for raw, mapped in LABEL_MAP.items():
        label_expr = pl.when(pl.col("regime_label") == raw).then(pl.lit(mapped)).otherwise(label_expr)
    df = (
        df.sort(["group_id", "time_idx"])
        .with_columns(
            [
                pl.len().over("group_id").alias("_group_n"),
                (pl.col("time_idx").rank("ordinal").over("group_id") - 1).alias("_group_i"),
                pl.col("group_id").str.extract(r"_(\d+|1D)$", 1).alias("_timeframe_suffix"),
                label_expr.alias("root_label"),
            ]
        )
        .with_columns(
            pl.when(pl.col("_timeframe_suffix") == "1D")
            .then(pl.lit(1440))
            .otherwise(pl.col("_timeframe_suffix").cast(pl.Int64, strict=False))
            .alias("timeframe_minutes")
        )
        .filter(pl.col("_timeframe_suffix").is_in(sorted(ACTIVE_TIMEFRAME_SUFFIXES)))
        .filter((pl.col("_group_i") % BOUNDED_ROW_STRIDE) == 0)
        .with_columns(
            [
                pl.when(pl.col("_group_i") < (pl.col("_group_n") * 0.60))
                .then(pl.lit("train"))
                .when(pl.col("_group_i") < (pl.col("_group_n") * 0.80))
                .then(pl.lit("calibration"))
                .otherwise(pl.lit("test"))
                .alias("split"),
                pl.concat_str([pl.lit("IDX:"), pl.col("group_id")]).alias("instrument"),
                pl.lit("huggingface_tsie_idx").alias("market_context"),
                pl.when(pl.col("_timeframe_suffix") == "1D")
                .then(pl.lit("1d"))
                .otherwise(pl.concat_str([pl.col("timeframe_minutes").cast(pl.Utf8), pl.lit("m")]))
                .alias("timeframe"),
            ]
        )
        .with_columns(
            pl.concat_str([pl.col("instrument"), pl.lit(":"), pl.col("timeframe")]).alias("context")
        )
    )
    return df


def to_arrays(df: pl.DataFrame) -> dict[str, Any]:
    arrays: dict[str, Any] = {
        "split": df.get_column("split").to_numpy(),
        "root_label": df.get_column("root_label").to_numpy(),
        "instrument": df.get_column("instrument").to_numpy(),
        "market_context": df.get_column("market_context").to_numpy(),
        "timeframe": df.get_column("timeframe").to_numpy(),
        "context": df.get_column("context").to_numpy(),
    }
    for feature in FEATURES:
        arrays[feature] = df.get_column(feature).cast(pl.Float64).to_numpy()
    return arrays


def split_metric(arrays: dict[str, Any], selected: np.ndarray, root: str, split: str) -> dict[str, Any]:
    split_mask = arrays["split"] == split
    chosen = selected & split_mask
    support = int(chosen.sum())
    success = int(((arrays["root_label"] == root) & chosen).sum()) if support else 0
    precision = success / support if support else 0.0
    split_total = int(split_mask.sum())
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": wilson_lcb(success, support),
        "coverage": support / split_total if split_total else 0.0,
        "validation_instruments": sorted(np.unique(arrays["instrument"][chosen]).tolist()) if support else [],
        "validation_market_contexts": sorted(np.unique(arrays["market_context"][chosen]).tolist()) if support else [],
        "validation_timeframes": sorted(np.unique(arrays["timeframe"][chosen]).tolist()) if support else [],
        "validation_contexts": sorted(np.unique(arrays["context"][chosen]).tolist()) if support else [],
    }


def train_key(arrays: dict[str, Any], selected: np.ndarray, root: str) -> tuple[float, float, int, float]:
    train_mask = arrays["split"] == "train"
    chosen = selected & train_mask
    support = int(chosen.sum())
    if support <= 0:
        return (0.0, 0.0, 0, 0.0)
    success = int(((arrays["root_label"] == root) & chosen).sum())
    precision = success / support
    coverage = support / max(1, int(train_mask.sum()))
    return (wilson_lcb(success, support), precision, support, coverage)


def blockers(cal: dict[str, Any], test: dict[str, Any], ece: float) -> list[str]:
    out: list[str] = []
    if cal["support"] < SUPPORT_CAL_MIN:
        out.append("calibration_support_below_120")
    if test["support"] < SUPPORT_TEST_MIN:
        out.append("test_support_below_60")
    if cal["precision_wilson_lcb_95"] < 0.95:
        out.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < 0.95:
        out.append("test_wilson95_below_0_95")
    if cal["coverage"] < COVERAGE_MIN:
        out.append("calibration_coverage_below_0_03")
    if test["coverage"] < COVERAGE_MIN:
        out.append("test_coverage_below_0_03")
    if ece > ECE_MAX:
        out.append("ece_above_0_05")
    if len(test["validation_instruments"]) < 2:
        out.append("validation_instruments_below_2")
    if len(test["validation_market_contexts"]) < 2:
        out.append("validation_market_contexts_below_2")
    if len(test["validation_timeframes"]) < 2:
        out.append("validation_timeframes_below_2")
    if BOUNDED_ROW_STRIDE > 1:
        out.append("bounded_sample_not_completion_eligible")
    return out


def atom_candidates(arrays: dict[str, Any], root: str) -> list[Candidate]:
    train = arrays["split"] == "train"
    atoms: list[tuple[tuple[float, float, int], Candidate]] = []
    keep_top = 80
    for feature in FEATURES:
        values = arrays[feature].astype(float)
        finite_values = np.isfinite(values)
        train_values = values[train & np.isfinite(values)]
        if len(train_values) < SUPPORT_TRAIN_MIN or len(np.unique(train_values[: min(len(train_values), 5000)])) <= 2:
            quantiles = [0.5]
        else:
            quantiles = [0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.98, 0.99]
        for q in quantiles:
            threshold = float(np.nanquantile(train_values, q))
            if not math.isfinite(threshold):
                continue
            for op in [">=", "<="]:
                mask = finite_values & ((values >= threshold) if op == ">=" else (values <= threshold))
                key = train_key(arrays, mask, root)
                if key[2] < SUPPORT_TRAIN_MIN or key[3] < COVERAGE_MIN:
                    continue
                atoms.append((key[:3], Candidate("rule_atom", f"{feature} {op} {threshold:.12g}", mask)))
                if len(atoms) > keep_top * 2:
                    atoms.sort(key=lambda item: item[0], reverse=True)
                    atoms = atoms[:keep_top]
    atoms.sort(key=lambda item: item[0], reverse=True)
    return [candidate for _, candidate in atoms[:keep_top]]


def run_root(arrays: dict[str, Any], root: str) -> dict[str, Any]:
    atoms = atom_candidates(arrays, root)
    best: tuple[tuple[float, float, int], Candidate] | None = None

    def consider(candidate: Candidate) -> None:
        nonlocal best
        key_full = train_key(arrays, candidate.mask, root)
        if key_full[2] < SUPPORT_TRAIN_MIN or key_full[3] < COVERAGE_MIN:
            return
        key = key_full[:3]
        if best is None or key > best[0]:
            best = (key, candidate)

    for candidate in atoms[:50]:
        consider(candidate)
    for i, left in enumerate(atoms[:24]):
        for right in atoms[i + 1 : 24]:
            if left.rule.split()[0] == right.rule.split()[0]:
                continue
            consider(Candidate("rule_pair", f"{left.rule} AND {right.rule}", left.mask & right.mask))
    for i, left in enumerate(atoms[:10]):
        for j, mid in enumerate(atoms[i + 1 : 10], start=i + 1):
            for right in atoms[j + 1 : 10]:
                features = {left.rule.split()[0], mid.rule.split()[0], right.rule.split()[0]}
                if len(features) < 3:
                    continue
                consider(Candidate("rule_triple", f"{left.rule} AND {mid.rule} AND {right.rule}", left.mask & mid.mask & right.mask))

    if best is None:
        selected = np.zeros(len(arrays["split"]), dtype=bool)
        candidate = Candidate("none", "no_train_candidate_with_min_support", selected)
    else:
        candidate = best[1]
    train = split_metric(arrays, candidate.mask, root, "train")
    cal = split_metric(arrays, candidate.mask, root, "calibration")
    test = split_metric(arrays, candidate.mask, root, "test")
    ece = abs(test["precision"] - cal["precision"]) if cal["support"] else 1.0
    block = blockers(cal, test, ece)
    return {
        "root_class": root,
        "state": "accepted_95" if not block else "blocked",
        "method": candidate.method,
        "rule": candidate.rule,
        "train": train,
        "calibration": cal,
        "test": test,
        "ece": ece,
        "accepted_95": not block,
        "blockers": block,
    }


def write_summary(path: Path, reports: list[dict[str, Any]]) -> None:
    fields = [
        "root_class",
        "state",
        "method",
        "rule",
        "train_support",
        "train_lcb",
        "cal_support",
        "cal_lcb",
        "test_support",
        "test_lcb",
        "test_precision",
        "test_coverage",
        "ece",
        "test_instruments",
        "test_market_contexts",
        "test_timeframes",
        "blockers",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for item in reports:
            writer.writerow(
                {
                    "root_class": item["root_class"],
                    "state": item["state"],
                    "method": item["method"],
                    "rule": item["rule"],
                    "train_support": item["train"]["support"],
                    "train_lcb": item["train"]["precision_wilson_lcb_95"],
                    "cal_support": item["calibration"]["support"],
                    "cal_lcb": item["calibration"]["precision_wilson_lcb_95"],
                    "test_support": item["test"]["support"],
                    "test_lcb": item["test"]["precision_wilson_lcb_95"],
                    "test_precision": item["test"]["precision"],
                    "test_coverage": item["test"]["coverage"],
                    "ece": item["ece"],
                    "test_instruments": ";".join(item["test"]["validation_instruments"][:20]),
                    "test_market_contexts": ";".join(item["test"]["validation_market_contexts"]),
                    "test_timeframes": ";".join(item["test"]["validation_timeframes"]),
                    "blockers": ";".join(item["blockers"]),
                }
            )


def write_md(path: Path, report: dict[str, Any]) -> None:
    if BOUNDED_ROW_STRIDE > 1:
        row_scope = (
            f"- This loop is bounded to timeframe suffixes `{', '.join(sorted(ACTIVE_TIMEFRAME_SUFFIXES))}` "
            f"and every `{BOUNDED_ROW_STRIDE}`th row per source group; it is fail-closed and not completion-eligible."
        )
    else:
        row_scope = (
            f"- This loop uses all rows for timeframe suffixes `{', '.join(sorted(ACTIVE_TIMEFRAME_SUFFIXES))}`; "
            "it is completion-eligible for this source but still must pass the unchanged cross-context and 95 LCB gates."
        )
    lines = [
        "# Hugging Face TSIE Expanded Regime Gate",
        "",
        f"Run id: `{report['loop_id']}`.",
        "",
        "## Decision",
        "",
        f"- Gate result: `{report['decision']['gate_result']}`",
        f"- Accepted roots in this source: {', '.join(report['decision']['accepted_new_roots_95']) or 'none'}",
        f"- Missing active expanded roots after this source: {', '.join(report['decision']['missing_root_classes_95_effective'])}",
        f"- Runtime code changed: `{str(report['decision']['runtime_code_changed']).lower()}`",
        f"- Thresholds relaxed: `{str(report['decision']['thresholds_relaxed']).lower()}`",
        "",
        "## Results",
        "",
        "| Root | State | Rule | Cal support | Cal LCB | Test support | Test LCB | Test precision | Blockers |",
        "|---|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for root in ROOTS:
        item = report["root_reports"][root]
        lines.append(
            "| {root} | {state} | `{rule}` | {cal_support} | {cal_lcb:.6f} | {test_support} | {test_lcb:.6f} | {test_precision:.6f} | {blockers} |".format(
                root=root,
                state=item["state"],
                rule=item["rule"],
                cal_support=item["calibration"]["support"],
                cal_lcb=item["calibration"]["precision_wilson_lcb_95"],
                test_support=item["test"]["support"],
                test_lcb=item["test"]["precision_wilson_lcb_95"],
                test_precision=item["test"]["precision"],
                blockers=", ".join(item["blockers"]) or "none",
            )
        )
    lines.extend(
        [
            "",
            "## Source Policy",
            "",
            "- Source is external direct-labeled TSIE IDX market-regime data from Hugging Face.",
            "- Mapping: `STRONG BUY` -> `BullExpansion`; `STRONG SELL` -> `BearExpansion`; `FLAT / NOISE` -> `SidewaysConsolidation`; weak/trap labels remain `UnknownOrMixed`.",
            "- Blocked as predictors: `future_volatility`, `trend_return`, `target_return`, and `regime_label`.",
            row_scope,
            "- Raw 564MB parquet stays under `/private/tmp`; repo artifacts are compact summaries/samples only.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    source_meta = ensure_parquet()
    readme_excerpt = fetch_readme_excerpt()
    df = load_frame()
    arrays = to_arrays(df)
    root_reports = {root: run_root(arrays, root) for root in ROOTS}
    accepted_new = [root for root, item in root_reports.items() if item["accepted_95"]]
    active_roots = ["BullExpansion", "BearExpansion", "SidewaysConsolidation", "CrisisCrash", "Manipulation"]
    effective = sorted(set(accepted_new + ["CrisisCrash"]), key=active_roots.index)
    missing = [root for root in active_roots if root not in effective]

    sample_csv = OUT_DIR / "hf_tsie_expanded_regime_sample.csv"
    summary_csv = OUT_DIR / "hf_tsie_expanded_regime_summary.csv"
    report_json = OUT_DIR / "hf_tsie_expanded_regime_report.json"
    report_md = OUT_DIR / "hf_tsie_expanded_regime_report.md"
    assertions = CHECK_DIR / "hf_tsie_expanded_regime_assertions.out"

    sample = (
        df.select(["time", "instrument", "timeframe", "split", "regime_label", "root_label"] + FEATURES)
        .group_by(["root_label", "split"], maintain_order=True)
        .head(20)
    )
    sample.write_csv(sample_csv)
    write_summary(summary_csv, list(root_reports.values()))

    split_counts = {row["split"]: row["len"] for row in df.group_by("split").len().to_dicts()}
    label_counts = {row["root_label"]: row["len"] for row in df.group_by("root_label").len().to_dicts()}
    raw_label_counts = {RAW_LABEL_NAMES.get(row["regime_label"], str(row["regime_label"])): row["len"] for row in df.group_by("regime_label").len().to_dicts()}
    report: dict[str, Any] = {
        "loop_id": RUN_ID,
        "objective": "Evaluate external direct-labeled TSIE IDX strong buy/sell/flat labels as expanded root evidence under unchanged 95 gates.",
        "source": source_meta | {"readme_excerpt": readme_excerpt},
        "feature_policy": {
            "predictor_features": FEATURES,
            "blocked_predictor_columns": BLOCKED_COLUMNS,
            "label_mapping": {RAW_LABEL_NAMES[k]: v for k, v in LABEL_MAP.items()},
            "weak_or_trap_labels": "WEAK SELL, BEAR TRAP, BULL TRAP, and WEAK BUY remain UnknownOrMixed for this active expanded-root gate.",
            "active_timeframe_suffixes": sorted(ACTIVE_TIMEFRAME_SUFFIXES),
            "bounded_row_stride": BOUNDED_ROW_STRIDE,
            "completion_eligible": BOUNDED_ROW_STRIDE == 1,
            "raw_committed_to_repo": False,
        },
        "threshold_policy": {
            "precision_wilson_lcb_95_min": 0.95,
            "calibration_support_min": SUPPORT_CAL_MIN,
            "test_support_min": SUPPORT_TEST_MIN,
            "coverage_min": COVERAGE_MIN,
            "ece_max": ECE_MAX,
            "validation_instruments_min": 2,
            "validation_market_contexts_min": 2,
            "validation_timeframes_min": 2,
        },
        "row_count": int(df.height),
        "split_counts": split_counts,
        "label_counts": label_counts,
        "raw_label_counts": raw_label_counts,
        "context_counts": {
            "instruments": int(df.select(pl.col("instrument").n_unique()).item()),
            "market_contexts": sorted(df.select("market_context").unique().get_column("market_context").to_list()),
            "timeframes": sorted(df.select("timeframe").unique().get_column("timeframe").to_list()),
            "contexts": int(df.select(pl.col("context").n_unique()).item()),
        },
        "root_reports": root_reports,
        "decision": {
            "gate_result": "accepted_95" if accepted_new else "blocked_hf_tsie_expanded_regime_gate_below_95_or_validation_scope",
            "accepted_new_roots_95": accepted_new,
            "retained_prior_accepted_root_classes_95": ["CrisisCrash"],
            "accepted_root_classes_95_effective": effective,
            "missing_root_classes_95_effective": missing,
            "manipulation_evaluated": False,
            "manipulation_blocker": "TSIE is labeled buy/sell/flat regime data, not direct event/order-lifecycle/L2 manipulation evidence.",
            "runtime_code_changed": False,
            "thresholds_relaxed": False,
            "fresh_calibration_rerun": True,
            "trade_usable": False,
            "next_action": "Run a completion-eligible full-data MainRegimeV3Candidate gate or switch to a smaller direct-labeled cross-market source, and acquire direct manipulation event/order-lifecycle labels.",
        },
        "artifacts": {
            "report_json": repo_rel(report_json),
            "report_md": repo_rel(report_md),
            "summary_csv": repo_rel(summary_csv),
            "sample_csv": repo_rel(sample_csv),
            "assertions": repo_rel(assertions),
        },
    }
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_md(report_md, report)

    lines = [
        f"loop_id={RUN_ID}",
        f"rows={df.height}",
        f"raw_committed_to_repo=false",
        f"runtime_code_changed={str(report['decision']['runtime_code_changed']).lower()}",
        f"thresholds_relaxed={str(report['decision']['thresholds_relaxed']).lower()}",
        f"bounded_row_stride={BOUNDED_ROW_STRIDE}",
        f"completion_eligible={str(BOUNDED_ROW_STRIDE == 1).lower()}",
        f"accepted_new_roots_95={','.join(accepted_new) if accepted_new else 'none'}",
        f"gate_result={report['decision']['gate_result']}",
    ]
    for root in ROOTS:
        item = root_reports[root]
        lines.append(
            f"{root}:cal_lcb={item['calibration']['precision_wilson_lcb_95']:.6f}:test_lcb={item['test']['precision_wilson_lcb_95']:.6f}:accepted={str(item['accepted_95']).lower()}:blockers={','.join(item['blockers'])}"
        )
    assertions.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
