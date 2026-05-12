#!/usr/bin/env python3
"""Run-local Board B branch direction rescue probe.

This diagnostic consumes existing real branch rows and tests whether failed
branches are a simple direction/sign problem. It is not a promoted Auto-Quant
recipe because inverse variants are post-hoc probes and Manipulation shorting
would require borrow/perp execution evidence.
"""

from __future__ import annotations

import csv
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T194754+0800-codex-board-b-branch-direction-rescue-probe-v1"
SCHEMA_VERSION = "board-b-branch-direction-rescue-probe/v1"
ACCEPTED_REGIME_ID = "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation"
ROOTS = ["Bull", "Bear", "Sideways", "Crisis", "Manipulation(scoped)"]

TARGET_EDGE = 0.001
TARGET_DSR = 1.0
DRAWDOWN_BUDGET = 0.25
TAIL_LOSS_BUDGET = 0.05
MIN_TOTAL_TRADES = 100
MIN_TEST_FOLDS = 4
MIN_TRADES_PER_TEST_FOLD = 10
FOLD_POSITIVE_RATE_MIN = 0.75

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())

ROOT_VARIANT_ROWS = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T193803-codex-board-b-root-transition-triad-clean-v1/branch-rc-spa/"
    "root_transition_triad_variant_rows_v1.csv"
)
MANIP_ROWS = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T194035-codex-board-b-mehrnoom-binance-intraday-pnl-v1/"
    "mehrnoom-binance-intraday-pnl/mehrnoom_binance_intraday_pnl_rows_v1.csv"
)
BASELINE_REPORT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/branch-rc-spa/"
    "root_plus_manip_bridge_rc_spa_report_v1.json"
)

OUT_DIR = RUN_ROOT / "branch-direction-rescue-probe"
CHECK_DIR = RUN_ROOT / "checks"
SUMMARY_CSV = OUT_DIR / "branch_direction_rescue_summary_v1.csv"
REPORT_JSON = OUT_DIR / "branch_direction_rescue_probe_v1.json"
REPORT_MD = OUT_DIR / "branch_direction_rescue_probe_v1.md"
ASSERTIONS = CHECK_DIR / "branch_direction_rescue_probe_v1_assertions.out"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def git_ref() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def bootstrap_lcb(values: np.ndarray, seed: int) -> float:
    if len(values) == 0:
        return 0.0
    rng = np.random.default_rng(seed)
    means = np.empty(400)
    for idx in range(len(means)):
        means[idx] = rng.choice(values, size=len(values), replace=True).mean()
    return float(np.percentile(means, 5))


def max_drawdown(values: np.ndarray) -> float:
    if len(values) == 0:
        return 0.0
    equity = np.cumsum(values)
    peaks = np.maximum.accumulate(equity)
    return float(np.max(peaks - equity))


def pbo_for_root(rows: list[dict[str, Any]], root: str) -> tuple[float, str]:
    root_rows = [row for row in rows if row["parent_regime_root"] == root]
    folds = sorted({str(row["fold_id"]) for row in root_rows})
    variants = sorted({str(row["variant_id"]) for row in root_rows})
    if len(folds) < MIN_TEST_FOLDS or len(variants) < 3:
        return 1.0, "not_identifiable_lt4_folds_or_lt3_variants"
    bad = 0
    cases = 0
    for test_fold in folds:
        train_scores: dict[str, float] = {}
        test_scores: dict[str, float] = {}
        for variant in variants:
            train = [
                float(row["profit_ratio_net"])
                for row in root_rows
                if str(row["variant_id"]) == variant and str(row["fold_id"]) != test_fold
            ]
            test = [
                float(row["profit_ratio_net"])
                for row in root_rows
                if str(row["variant_id"]) == variant and str(row["fold_id"]) == test_fold
            ]
            if len(train) >= 20 and len(test) >= 5:
                train_scores[variant] = float(np.mean(train))
                test_scores[variant] = float(np.mean(test))
        if len(train_scores) < 3 or len(test_scores) < 3:
            continue
        selected = max(train_scores, key=train_scores.get)
        median_test = float(np.median(list(test_scores.values())))
        if test_scores.get(selected, -999.0) < median_test:
            bad += 1
        cases += 1
    if cases == 0:
        return 1.0, "not_identifiable_insufficient_variant_fold_matrix"
    return bad / cases, "simple_cscv_variant_fold_proxy_with_direction_probe"


def score_rows(
    *,
    root: str,
    variant_id: str,
    rows: list[dict[str, Any]],
    all_rows: list[dict[str, Any]],
    pbo: float,
    pbo_method: str,
    extra_blockers: list[str] | None = None,
) -> dict[str, Any]:
    values = np.array([float(row["profit_ratio_net"]) for row in rows], dtype=float)
    costs = np.array([float(row["roundtrip_cost"]) for row in rows], dtype=float)
    total = int(len(values))
    folds = sorted({str(row["fold_id"]) for row in rows})
    fold_returns = [
        float(sum(float(row["profit_ratio_net"]) for row in rows if str(row["fold_id"]) == fold))
        for fold in folds
    ]
    fold_counts = [
        int(sum(1 for row in rows if str(row["fold_id"]) == fold))
        for fold in folds
    ]
    fold_positive_rate = (
        float(sum(1 for value in fold_returns if value > 0) / len(fold_returns))
        if fold_returns
        else 0.0
    )
    min_fold_trades = min(fold_counts) if fold_counts else 0
    mean = float(np.mean(values)) if total else 0.0
    std = float(np.std(values, ddof=1)) if total > 1 else 0.0
    dsr = float(mean / std * math.sqrt(total)) if std > 0 and total > 1 else 0.0
    seed_base = sum(ord(ch) for ch in f"{root}:{variant_id}") % 10_000
    lcb = bootstrap_lcb(values, seed=1000 + seed_base)
    stressed_lcb = bootstrap_lcb(values - costs, seed=2000 + seed_base) if total else 0.0
    tail_loss = float(max(0.0, -np.percentile(values, 5))) if total else 0.0
    outside = np.array(
        [
            float(row["profit_ratio_net"])
            for row in all_rows
            if row["parent_regime_root"] != root and row["variant_id"] == variant_id
        ],
        dtype=float,
    )
    outside_mean = float(np.mean(outside)) if len(outside) else 0.0
    if mean <= 0:
        specificity = 0.0
    elif outside_mean <= 0:
        specificity = 999.0
    else:
        specificity = float(mean / max(outside_mean, 1e-9))

    edge_score = max(0.0, min(lcb / TARGET_EDGE, 1.0))
    fold_score = fold_positive_rate
    depth_score = max(0.0, min(total / MIN_TOTAL_TRADES, 1.0))
    dsr_score = max(0.0, min(dsr / TARGET_DSR, 1.0))
    pbo_score = 1.0 - max(0.0, min(pbo / 0.25, 1.0))
    cost_score = 1.0 if stressed_lcb > 0 else 0.0
    drawdown_score = 1.0 - max(0.0, min(max_drawdown(values) / DRAWDOWN_BUDGET, 1.0))
    specificity_score = max(0.0, min((specificity - 1.0) / 0.5, 1.0))
    rc_spa = 100.0 * (
        0.20 * edge_score
        + 0.15 * fold_score
        + 0.15 * depth_score
        + 0.15 * dsr_score
        + 0.10 * pbo_score
        + 0.10 * cost_score
        + 0.10 * drawdown_score
        + 0.05 * specificity_score
    )

    failures: list[str] = []
    if total < MIN_TOTAL_TRADES:
        failures.append("reject_thin_trades")
    if len(folds) < MIN_TEST_FOLDS:
        failures.append("reject_insufficient_test_folds")
    if min_fold_trades < MIN_TRADES_PER_TEST_FOLD:
        failures.append("reject_fold_trade_depth")
    if fold_positive_rate < FOLD_POSITIVE_RATE_MIN:
        failures.append("reject_fold_inconsistency")
    if lcb <= 0:
        failures.append("reject_no_positive_edge")
    if stressed_lcb <= 0:
        failures.append("reject_cost_fragile")
    if pbo > 0.25:
        failures.append("reject_overfit_risk")
    if dsr <= 0:
        failures.append("reject_dsr_nonpositive")
    if tail_loss > TAIL_LOSS_BUDGET:
        failures.append("reject_tail_risk")
    if specificity < 1.20:
        failures.append("reject_no_regime_specificity")
    if rc_spa < 60:
        failures.append("reject_rc_spa_below_60")
    failures.extend(extra_blockers or [])
    hard_gate = "pass" if not failures else "fail:" + "|".join(failures)
    return {
        "parent_regime_root": root,
        "selected_variant_id": variant_id,
        "total_trades": total,
        "test_folds": len(folds),
        "folds": ",".join(folds),
        "min_trades_per_test_fold": min_fold_trades,
        "fold_positive_rate": fold_positive_rate,
        "win_rate": float(np.mean(values > 0)) if total else 0.0,
        "mean_profit_ratio_net": mean,
        "net_return_R": float(np.sum(values)) if total else 0.0,
        "bootstrap_edge_lcb_5pct": lcb,
        "bootstrap_edge_lcb_5pct_stressed_2x_cost": stressed_lcb,
        "pbo": pbo,
        "pbo_method": pbo_method,
        "dsr": dsr,
        "cost_stress_result": "pass" if stressed_lcb > 0 else "fail",
        "tail_loss_p95": tail_loss,
        "max_drawdown_trade_equity_proxy": max_drawdown(values),
        "regime_specificity_ratio": specificity,
        "outside_mean_profit_ratio_net": outside_mean,
        "rc_spa": rc_spa,
        "hard_gate_result": hard_gate,
        "promotion_level": "diagnostic_only",
        "downstream_consumption_status": "not_started:direction_probe_not_promotion_grade",
    }


def root_branch_path(root: str, variant_id: str) -> str:
    if root == "Bull":
        return f"Bull -> TrendExpansion -> TransitionContinuation -> DirectionRescueProbe:{variant_id}"
    if root == "Bear":
        return f"Bear -> BearMarketDrawdown -> DirectionalShortContinuation -> DirectionRescueProbe:{variant_id}"
    if root == "Sideways":
        return f"Sideways -> RangeConsolidation -> BandMeanReversion -> DirectionRescueProbe:{variant_id}"
    if root == "Crisis":
        return f"Crisis -> ExtremeStress -> TailRiskShortContinuation -> DirectionRescueProbe:{variant_id}"
    return "Manipulation(scoped) -> TelegramPumpEvent -> DirectionRescueProbe -> provider_reconstructed_pnl"


def load_root_probe_rows() -> list[dict[str, Any]]:
    source = pd.read_csv(ROOT_VARIANT_ROWS)
    rows: list[dict[str, Any]] = []
    for record in source.to_dict("records"):
        root = str(record["parent_regime_root"])
        base_variant = str(record["variant_id"])
        cost = float(record["roundtrip_cost"])
        gross = float(record["gross_return"])
        common = {
            "source_artifact": rel(ROOT_VARIANT_ROWS),
            "parent_regime_root": root,
            "roundtrip_cost": cost,
            "fold_id": str(int(record["year_fold"])),
        }
        rows.append(
            {
                **common,
                "variant_id": f"{base_variant}__as_recorded",
                "profit_ratio_net": float(record["profit_ratio_net"]),
                "probe_mode": "as_recorded",
                "regime_profit_branch_path": root_branch_path(root, f"{base_variant}__as_recorded"),
            }
        )
        rows.append(
            {
                **common,
                "variant_id": f"{base_variant}__inverse_direction_probe",
                "profit_ratio_net": -gross - cost,
                "probe_mode": "inverse_direction_probe",
                "regime_profit_branch_path": root_branch_path(root, f"{base_variant}__inverse_direction_probe"),
            }
        )
    return rows


def load_manipulation_probe_rows() -> list[dict[str, Any]]:
    source = pd.read_csv(MANIP_ROWS)
    positives = source[source["is_manipulation_positive"].astype(bool)].copy()
    rows: list[dict[str, Any]] = []
    for record in positives.to_dict("records"):
        fold = str(pd.Timestamp(record["entry_ts"]).to_period("M"))
        gross_6h = float(record["return_6h"])
        gross_24h = float(record["return_24h"])
        cost = 0.0015
        common = {
            "source_artifact": rel(MANIP_ROWS),
            "parent_regime_root": "Manipulation(scoped)",
            "roundtrip_cost": cost,
            "fold_id": fold,
            "regime_profit_branch_path": root_branch_path("Manipulation(scoped)", "event"),
        }
        rows.append(
            {
                **common,
                "variant_id": "manipulation_event_long_6h",
                "profit_ratio_net": gross_6h - cost,
                "probe_mode": "event_long_6h",
            }
        )
        rows.append(
            {
                **common,
                "variant_id": "manipulation_event_short_6h_borrow_unverified",
                "profit_ratio_net": -gross_6h - cost,
                "probe_mode": "event_short_6h_borrow_unverified",
            }
        )
        rows.append(
            {
                **common,
                "variant_id": "manipulation_event_long_24h",
                "profit_ratio_net": gross_24h - cost,
                "probe_mode": "event_long_24h",
            }
        )
        rows.append(
            {
                **common,
                "variant_id": "manipulation_event_short_24h_borrow_unverified",
                "profit_ratio_net": -gross_24h - cost,
                "probe_mode": "event_short_24h_borrow_unverified",
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    with BASELINE_REPORT.open(encoding="utf-8") as fh:
        baseline = json.load(fh)

    all_rows = load_root_probe_rows() + load_manipulation_probe_rows()
    summary_rows: list[dict[str, Any]] = []
    all_candidate_summaries: list[dict[str, Any]] = []
    for root in ROOTS:
        root_rows = [row for row in all_rows if row["parent_regime_root"] == root]
        pbo, pbo_method = pbo_for_root(all_rows, root)
        variants = sorted({row["variant_id"] for row in root_rows})
        candidates: list[dict[str, Any]] = []
        for variant in variants:
            rows = [row for row in root_rows if row["variant_id"] == variant]
            extra: list[str] = []
            if "inverse_direction_probe" in variant:
                extra.append("reject_posthoc_inverse_direction_probe_not_predeclared_recipe")
            if "borrow_unverified" in variant:
                extra.append("reject_short_execution_borrow_or_perp_unverified")
            scored = score_rows(
                root=root,
                variant_id=variant,
                rows=rows,
                all_rows=all_rows,
                pbo=pbo,
                pbo_method=pbo_method,
                extra_blockers=extra,
            )
            scored["regime_profit_branch_path"] = root_branch_path(root, variant)
            candidates.append(scored)
            all_candidate_summaries.append(scored)
        selected = max(candidates, key=lambda row: float(row["rc_spa"])) if candidates else score_rows(
            root=root,
            variant_id="no_rows",
            rows=[],
            all_rows=all_rows,
            pbo=1.0,
            pbo_method="no_rows",
        )
        summary_rows.append(selected)

    formal_passes = [row for row in summary_rows if row["hard_gate_result"] == "pass"]
    numeric_passes_before_diagnostic_blockers = [
        row
        for row in all_candidate_summaries
        if row["rc_spa"] >= 60
        and row["bootstrap_edge_lcb_5pct"] > 0
        and row["bootstrap_edge_lcb_5pct_stressed_2x_cost"] > 0
        and row["fold_positive_rate"] >= FOLD_POSITIVE_RATE_MIN
        and row["pbo"] <= 0.25
        and row["total_trades"] >= MIN_TOTAL_TRADES
        and row["min_trades_per_test_fold"] >= MIN_TRADES_PER_TEST_FOLD
    ]
    max_score = max(float(row["rc_spa"]) for row in summary_rows) if summary_rows else 0.0
    gate_result = (
        "pass"
        if len(formal_passes) == len(ROOTS)
        else "fail:direction_rescue_probe_not_promotion_grade"
    )
    primary_blocker = "; ".join(
        f"{row['parent_regime_root']}={row['hard_gate_result']}" for row in summary_rows
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "repo_git_ref": git_ref(),
        "accepted_regime_id": ACCEPTED_REGIME_ID,
        "run_root": rel(RUN_ROOT),
        "inputs": {
            "baseline_report": rel(BASELINE_REPORT),
            "root_variant_rows": rel(ROOT_VARIANT_ROWS),
            "manipulation_rows": rel(MANIP_ROWS),
        },
        "decision": {
            "gate_result": gate_result,
            "stable_profit_score": max_score,
            "branch_paths_evaluated": len(summary_rows),
            "branch_paths_passed": len(formal_passes),
            "numeric_candidates_before_diagnostic_blockers": len(numeric_passes_before_diagnostic_blockers),
            "baseline_gate_result": baseline["decision"]["gate_result"],
            "downstream_consumption": "not_started:direction_probe_not_promotion_grade",
            "primary_blocker": primary_blocker,
            "next_action": (
                "Do not promote direction probes. If a sign-flip branch looks promising, rerun it as a "
                "predeclared Auto-Quant recipe with execution feasibility and then repeat RC-SPA."
            ),
        },
        "selected_branch_summaries": summary_rows,
        "artifacts": {
            "report_json": rel(REPORT_JSON),
            "report_md": rel(REPORT_MD),
            "summary_csv": rel(SUMMARY_CSV),
            "assertions": rel(ASSERTIONS),
        },
    }
    write_csv(SUMMARY_CSV, summary_rows)
    write_json(REPORT_JSON, report)

    lines = [
        "# Branch Direction Rescue Probe v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        f"- Gate result: `{gate_result}`",
        f"- Stable profit score: `{max_score:.4f}`",
        f"- Branch paths passed: `{len(formal_passes)}/{len(ROOTS)}`",
        f"- Numeric candidates before diagnostic blockers: `{len(numeric_passes_before_diagnostic_blockers)}`",
        f"- Downstream consumption: `not_started:direction_probe_not_promotion_grade`",
        "",
        "## Selected Branch Summary",
        "",
        "| Root | Variant | Trades | Folds | Min Fold Trades | LCB 5% | PBO | DSR | RC-SPA | Gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary_rows:
        lines.append(
            "| {parent_regime_root} | `{selected_variant_id}` | {total_trades} | {test_folds} | "
            "{min_trades_per_test_fold} | {bootstrap_edge_lcb_5pct:.6f} | {pbo:.3f} | "
            "{dsr:.4f} | {rc_spa:.4f} | `{hard_gate_result}` |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is a diagnostic-only post-hoc direction/sign probe, not a promoted Auto-Quant recipe.",
            "- Inverse-direction candidates remain blocked unless re-authored as predeclared recipes and rerun through RC-SPA.",
            "- Short Manipulation probes remain blocked without borrow/perp execution evidence.",
            "",
            "## Artifacts",
            "",
            f"- Report JSON: `{rel(REPORT_JSON)}`",
            f"- Summary CSV: `{rel(SUMMARY_CSV)}`",
            f"- Assertions: `{rel(ASSERTIONS)}`",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

    ASSERTIONS.write_text(
        "\n".join(
            [
                f"branch_paths_evaluated={len(summary_rows)}",
                f"branch_paths_passed={len(formal_passes)}",
                f"gate_result={gate_result}",
                "downstream_consumption=not_started:direction_probe_not_promotion_grade",
                f"numeric_candidates_before_diagnostic_blockers={len(numeric_passes_before_diagnostic_blockers)}",
                f"artifacts_exist={REPORT_JSON.exists() and REPORT_MD.exists() and SUMMARY_CSV.exists()}".lower(),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
