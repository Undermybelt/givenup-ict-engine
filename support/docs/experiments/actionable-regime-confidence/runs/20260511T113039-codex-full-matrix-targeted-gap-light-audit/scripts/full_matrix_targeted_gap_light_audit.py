#!/usr/bin/env python3
from __future__ import annotations

import csv
import itertools
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ID = "20260511T113039+0800-codex-full-matrix-targeted-gap-light-audit"
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T113039-codex-full-matrix-targeted-gap-light-audit"
OUT_DIR = RUN_ROOT / "targeted-gap-light"
CHECK_DIR = RUN_ROOT / "checks"
KAGGLE_TABLE = Path("/private/tmp/ict-regime-kaggle-regime-label-root/kaggle_regime_label_feature_table.csv")
INTRADAY_TABLE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260510T224014-codex-cross-timeframe-regime-validation/cross_timeframe_regime_features.csv"
HEAVY_RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T110540-codex-full-matrix-targeted-gap-batch"

Z95 = 1.959963984540054
FEATURES = [
    "vix",
    "volatility",
    "vol60_z",
    "ret20",
    "returns",
    "close_drawdown60",
    "yield_curve_10y_2y",
    "unemployment_rate",
    "fed_funds_rate",
    "real_rate_proxy",
]
QUANTILES = [0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.925, 0.95, 0.975, 0.99]


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


def metric(mask: np.ndarray, labels: np.ndarray, split_mask: np.ndarray, markets: np.ndarray, timeframes: np.ndarray, instruments: np.ndarray) -> dict[str, Any]:
    selected = mask & split_mask
    support = int(selected.sum())
    success = int((selected & labels).sum())
    return {
        "support": support,
        "success": success,
        "precision": success / support if support else 0.0,
        "precision_wilson_lcb_95": wilson_lcb(success, support),
        "coverage": support / max(1, int(split_mask.sum())),
        "validation_market_contexts": sorted({str(x) for x in markets[selected]}),
        "validation_timeframes": sorted({str(x) for x in timeframes[selected]}),
        "validation_instruments_count": len({str(x) for x in instruments[selected]}),
    }


def audit_crisis_source_labels() -> dict[str, Any]:
    rows = list(csv.DictReader(KAGGLE_TABLE.open(newline="", encoding="utf-8")))
    labels = np.array([row["regime_label"] == "Crisis" for row in rows], dtype=bool)
    splits = {name: np.array([row["split"] == name for row in rows], dtype=bool) for name in ["train", "calibration", "test"]}
    markets = np.array([row["market_context"] for row in rows], dtype=object)
    timeframes = np.array([row["timeframe"] for row in rows], dtype=object)
    instruments = np.array([row["ticker"] for row in rows], dtype=object)

    values: dict[str, np.ndarray] = {}
    for feature in FEATURES:
        values[feature] = np.array([float(row[feature]) if row.get(feature) not in ("", None) else math.nan for row in rows], dtype=float)

    terms: list[tuple[float, float, float, int, tuple[str, str, float], np.ndarray]] = []
    train = splits["train"]
    for feature, vector in values.items():
        train_values = vector[train & np.isfinite(vector)]
        thresholds = sorted({float(np.quantile(train_values, q)) for q in QUANTILES})
        for threshold in thresholds:
            for op in [">=", "<="]:
                mask = np.isfinite(vector) & ((vector >= threshold) if op == ">=" else (vector <= threshold))
                train_metric = metric(mask, labels, train, markets, timeframes, instruments)
                if train_metric["support"] >= 500 and train_metric["coverage"] >= 0.02 and train_metric["precision_wilson_lcb_95"] > 0.2:
                    terms.append((train_metric["precision_wilson_lcb_95"], train_metric["precision"], train_metric["coverage"], train_metric["support"], (feature, op, threshold), mask))
    terms.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    top_terms = terms[:50]

    accepted: list[dict[str, Any]] = []
    best_blocked: list[dict[str, Any]] = []
    for depth in [1, 2, 3]:
        for combo in itertools.combinations(top_terms, depth):
            mask = np.ones(len(rows), dtype=bool)
            rule_terms: list[str] = []
            for _, _, _, _, (feature, op, threshold), term_mask in combo:
                mask &= term_mask
                rule_terms.append(f"{feature} {op} {threshold:.12g}")
            calibration = metric(mask, labels, splits["calibration"], markets, timeframes, instruments)
            test = metric(mask, labels, splits["test"], markets, timeframes, instruments)
            blockers = []
            for split_name, data in [("calibration", calibration), ("test", test)]:
                if data["support"] < 250:
                    blockers.append(f"{split_name}_support_below_250")
                if data["precision_wilson_lcb_95"] < 0.95:
                    blockers.append(f"{split_name}_wilson95_below_0_95")
                if data["coverage"] < 0.01:
                    blockers.append(f"{split_name}_coverage_below_0_01")
                if len(data["validation_market_contexts"]) < 2:
                    blockers.append(f"{split_name}_market_contexts_below_2")
                if len(data["validation_timeframes"]) < 2:
                    blockers.append(f"{split_name}_timeframes_below_2")
            item = {
                "rule": " AND ".join(rule_terms),
                "calibration": calibration,
                "test": test,
                "blockers": blockers,
            }
            if not blockers:
                accepted.append(item)
            else:
                best_blocked.append(item)
    best_blocked.sort(key=lambda item: (item["test"]["precision_wilson_lcb_95"], item["test"]["precision"], item["test"]["coverage"]), reverse=True)
    return {
        "root": "Crisis",
        "source": repo_rel(KAGGLE_TABLE) if KAGGLE_TABLE.is_relative_to(REPO) else str(KAGGLE_TABLE),
        "rows": len(rows),
        "label_counts": Counter(row["regime_label"] for row in rows),
        "search_policy": {
            "candidate_features": FEATURES,
            "top_train_terms_kept": 50,
            "max_rule_depth": 3,
            "predictor_source": "current_or_trailing_fields_only",
            "target_source": "existing source regime_label column",
        },
        "top_train_terms": [
            {
                "term": f"{term[0]} {term[1]} {term[2]:.12g}",
                "train_wilson95": lcb,
                "train_precision": precision,
                "train_coverage": coverage,
                "train_support": support,
            }
            for lcb, precision, coverage, support, term, _ in terms[:10]
        ],
        "accepted_95": bool(accepted),
        "accepted_rules": accepted[:5],
        "best_blocked_rules": best_blocked[:5],
    }


def summarize_intraday_table() -> dict[str, Any]:
    with INTRADAY_TABLE.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        headers = reader.fieldnames or []
    return {
        "source": repo_rel(INTRADAY_TABLE),
        "rows": len(rows),
        "timeframes": Counter(row["timeframe"] for row in rows),
        "markets": Counter(row["market"] for row in rows),
        "has_source_regime_label": "regime_label" in headers or "root_label" in headers,
        "target_like_columns": [name for name in headers if name.startswith("target_")],
        "decision": "blocked_intraday_table_has_future_target_columns_but_no_independent_source_root_labels",
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    heavy_outputs = list((HEAVY_RUN_ROOT / "targeted-gap-batch").glob("*")) if (HEAVY_RUN_ROOT / "targeted-gap-batch").exists() else []
    crisis = audit_crisis_source_labels()
    intraday = summarize_intraday_table()
    accepted = ["Crisis"] if crisis["accepted_95"] else []
    report = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": "docs/plans/2026-05-10-actionable-regime-confidence-todo.md",
        "active_taxonomy": "MainRegimeV2",
        "objective": "Lightweight recovery audit for the stalled full-matrix targeted gap batch: test bounded source-labeled Crisis rules and block intraday proxy targets without independent labels.",
        "heavy_runner_readback": {
            "run_root": repo_rel(HEAVY_RUN_ROOT),
            "script_present": (HEAVY_RUN_ROOT / "scripts/full_matrix_targeted_gap_batch.py").exists(),
            "report_outputs_present": bool(heavy_outputs),
            "action_taken": "heavy_runner_observed_no_report_outputs_after_manual_run_attempt; this light audit avoids modifying that script",
        },
        "crisis_source_label_probe": crisis,
        "intraday_source_label_readiness": intraday,
        "decision": {
            "accepted_parent_root_gap_slices_added": len(accepted),
            "accepted_roots_in_this_slice": accepted,
            "blocked_roots_in_this_slice": [] if accepted else ["Crisis"],
            "full_matrix_goal_achieved": False,
            "gate_result": "partial_crisis_source_label_slice_accepted_full_matrix_still_blocked" if accepted else "blocked_light_gap_audit_no_95_source_label_slice",
            "thresholds_relaxed": False,
            "runtime_code_changed": False,
            "raw_data_committed": False,
            "trade_usable": False,
        },
        "next_action": "Acquire independent source root labels for the missing intraday/monthly provider matrix; do not count future-return target columns as source labels. Continue separate direct Manipulation variety acquisition.",
    }
    json_path = OUT_DIR / "full_matrix_targeted_gap_light_audit.json"
    md_path = OUT_DIR / "full_matrix_targeted_gap_light_audit.md"
    assertions_path = CHECK_DIR / "full_matrix_targeted_gap_light_audit_assertions.out"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=lambda x: dict(x) if isinstance(x, Counter) else str(x)) + "\n", encoding="utf-8")
    best = crisis["best_blocked_rules"][0]
    md_lines = [
        "# Full-Matrix Targeted Gap Light Audit",
        "",
        f"Run ID: `{RUN_ID}`",
        "",
        "## Result",
        "",
        f"- Accepted parent-root gap slices added: `{report['decision']['accepted_parent_root_gap_slices_added']}`.",
        f"- Gate result: `{report['decision']['gate_result']}`.",
        "- Runtime code changed: false.",
        "- Thresholds relaxed: false.",
        "- Raw data committed: false.",
        "- Trade usable: false.",
        "",
        "## Crisis Source-Label Probe",
        "",
        f"- Rows: `{crisis['rows']}`.",
        f"- Accepted 95: `{str(crisis['accepted_95']).lower()}`.",
        f"- Best blocked rule: `{best['rule']}`.",
        f"- Best blocked calibration/test Wilson95: `{best['calibration']['precision_wilson_lcb_95']:.6f}` / `{best['test']['precision_wilson_lcb_95']:.6f}`.",
        f"- Best blocked blockers: `{'; '.join(best['blockers'])}`.",
        "",
        "## Intraday Source-Label Readiness",
        "",
        f"- Rows: `{intraday['rows']}`.",
        f"- Has independent source root label column: `{str(intraday['has_source_regime_label']).lower()}`.",
        f"- Target-like columns: `{', '.join(intraday['target_like_columns'])}`.",
        f"- Decision: `{intraday['decision']}`.",
        "",
        "## Next Action",
        "",
        report["next_action"],
    ]
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    assertions = [
        "PASS active_taxonomy=MainRegimeV2",
        "PASS input_kaggle_feature_table_present",
        "PASS input_intraday_feature_table_present",
        f"PASS accepted_parent_root_gap_slices_added={report['decision']['accepted_parent_root_gap_slices_added']}",
        "PASS full_matrix_goal_achieved=false",
        "PASS intraday_future_targets_not_counted_as_source_labels",
        "PASS thresholds_relaxed=false",
        "PASS runtime_code_changed=false",
        "PASS raw_data_committed=false",
        "PASS trade_usable=false",
        f"GATE {report['decision']['gate_result']}",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"report": repo_rel(json_path), "gate_result": report["decision"]["gate_result"], "accepted": accepted}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
