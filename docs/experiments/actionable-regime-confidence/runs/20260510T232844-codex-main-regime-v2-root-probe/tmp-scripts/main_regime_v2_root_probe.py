from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260510T232844-codex-main-regime-v2-root-probe"
)
INPUT_FEATURE_TABLE = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260510T202359-hermes-cross-market-regime-validation/cross-market/"
    "cross_market_regime_features_and_labels.csv"
)
OUTPUT_DIR = RUN_ROOT / "root-v2"

NUMERIC_FEATURES = [
    "ret_1",
    "ret_4",
    "stretch_32",
    "range_pct",
    "realized_vol_rank_252",
    "range_rank_252",
    "volume_rank_252",
    "stretch_abs_rank_252",
]
BOOLEAN_FEATURES = [
    "condition_trend_expansion",
    "condition_range_consolidation",
    "condition_extreme_stress",
    "condition_reversal_brewing",
    "condition_thin_liquidity",
]
BLOCKED_PREDICTOR_PREFIXES = ("future_", "target_")
ROOT_CLASSES = ["Bull", "Bear", "Sideways", "Crisis", "Manipulation", "UnknownOrMixed"]
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


def _float(value: Any) -> float:
    try:
        if value in ("", None):
            return math.nan
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def _bool(value: Any) -> bool:
    text = str(value).strip().lower()
    if text in {"true", "yes"}:
        return True
    number = _float(value)
    return math.isfinite(number) and number >= 0.5


def _quantile(values: list[float], ratio: float) -> float:
    clean = sorted(value for value in values if math.isfinite(value))
    if not clean:
        return math.nan
    idx = min(len(clean) - 1, max(0, int((len(clean) - 1) * ratio)))
    return clean[idx]


def _wilson(success: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        return 0.0
    p = success / total
    denom = 1.0 + z * z / total
    center = p + z * z / (2.0 * total)
    margin = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * total)) / total)
    return (center - margin) / denom


def _read_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with INPUT_FEATURE_TABLE.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            row["_context"] = f"{row['instrument']}:{row['market']}:{row['timeframe']}"
            rows.append(row)
    by_context: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_context[str(row["_context"])].append(row)
    for context_rows in by_context.values():
        context_rows.sort(key=lambda item: str(item["ts"]))
        n = len(context_rows)
        for idx, row in enumerate(context_rows):
            if idx < n * 0.50:
                split = "train"
            elif idx < n * 0.75:
                split = "calibration"
            else:
                split = "test"
            row["_split"] = split
    return rows


def _root_thresholds(train_rows: list[dict[str, Any]]) -> dict[str, float]:
    future_returns = [_float(row.get("future_ret_h8h")) for row in train_rows]
    future_abs_returns = [_float(row.get("future_absret_h8h")) for row in train_rows]
    return {
        "bull_future_ret_h8h_train_q65": _quantile(future_returns, 0.65),
        "bear_future_ret_h8h_train_q35": _quantile(future_returns, 0.35),
        "crisis_future_absret_h8h_train_q90": _quantile(future_abs_returns, 0.90),
    }


def _assign_root_label(row: dict[str, Any], thresholds: dict[str, float]) -> str:
    future_ret = _float(row.get("future_ret_h8h"))
    future_absret = _float(row.get("future_absret_h8h"))
    crisis = _bool(row.get("target_extreme_stress")) or (
        math.isfinite(future_absret)
        and future_absret >= thresholds["crisis_future_absret_h8h_train_q90"]
    )
    sideways = _bool(row.get("target_range_consolidation")) and not crisis
    bull = (
        math.isfinite(future_ret)
        and future_ret >= thresholds["bull_future_ret_h8h_train_q65"]
        and not crisis
        and not sideways
    )
    bear = (
        math.isfinite(future_ret)
        and future_ret <= thresholds["bear_future_ret_h8h_train_q35"]
        and not crisis
        and not sideways
    )
    if crisis:
        return "Crisis"
    if sideways:
        return "Sideways"
    if bull:
        return "Bull"
    if bear:
        return "Bear"
    return "UnknownOrMixed"


def _split_rows(rows: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("_split") == split]


def _metric(label: str, selected: list[dict[str, Any]], split_total: int) -> dict[str, Any]:
    support = len(selected)
    success = sum(1 for row in selected if row.get("_root_label") == label)
    precision = success / support if support else 0.0
    return {
        "support": support,
        "success": success,
        "precision": precision,
        "precision_wilson_lcb_95": _wilson(success, support),
        "coverage": support / max(1, split_total),
        "validation_instruments": sorted({str(row.get("instrument", "")) for row in selected}),
        "validation_market_contexts": sorted({str(row.get("market", "")) for row in selected}),
        "validation_timeframes": sorted({str(row.get("timeframe", "")) for row in selected}),
        "validation_contexts": sorted({str(row.get("_context", "")) for row in selected}),
    }


class Rule:
    def __init__(self, description: str, predicate: Callable[[dict[str, Any]], bool]) -> None:
        self.description = description
        self.predicate = predicate

    def select(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [row for row in rows if self.predicate(row)]


def _candidate_rules(train_rows: list[dict[str, Any]]) -> list[Rule]:
    rules: list[Rule] = []
    for name in BOOLEAN_FEATURES:
        rules.append(Rule(name, lambda row, name=name: _bool(row.get(name))))
        rules.append(Rule(f"NOT {name}", lambda row, name=name: not _bool(row.get(name))))
    for name in NUMERIC_FEATURES:
        values = [_float(row.get(name)) for row in train_rows]
        cuts = sorted(
            {
                _quantile(values, ratio)
                for ratio in [
                    0.05,
                    0.10,
                    0.15,
                    0.20,
                    0.25,
                    0.30,
                    0.35,
                    0.40,
                    0.45,
                    0.50,
                    0.55,
                    0.60,
                    0.65,
                    0.70,
                    0.75,
                    0.80,
                    0.85,
                    0.90,
                    0.95,
                ]
                if math.isfinite(_quantile(values, ratio))
            }
        )
        for cut in cuts:
            rules.append(
                Rule(
                    f"{name} >= {cut:.12g}",
                    lambda row, name=name, cut=cut: math.isfinite(_float(row.get(name)))
                    and _float(row.get(name)) >= cut,
                )
            )
            rules.append(
                Rule(
                    f"{name} <= {cut:.12g}",
                    lambda row, name=name, cut=cut: math.isfinite(_float(row.get(name)))
                    and _float(row.get(name)) <= cut,
                )
            )
    for bool_name in BOOLEAN_FEATURES:
        for num_name in NUMERIC_FEATURES:
            values = [_float(row.get(num_name)) for row in train_rows]
            for ratio in [0.10, 0.20, 0.30, 0.70, 0.80, 0.90]:
                cut = _quantile(values, ratio)
                if not math.isfinite(cut):
                    continue
                rules.append(
                    Rule(
                        f"{bool_name} AND {num_name} >= {cut:.12g}",
                        lambda row, bool_name=bool_name, num_name=num_name, cut=cut: _bool(
                            row.get(bool_name)
                        )
                        and math.isfinite(_float(row.get(num_name)))
                        and _float(row.get(num_name)) >= cut,
                    )
                )
                rules.append(
                    Rule(
                        f"{bool_name} AND {num_name} <= {cut:.12g}",
                        lambda row, bool_name=bool_name, num_name=num_name, cut=cut: _bool(
                            row.get(bool_name)
                        )
                        and math.isfinite(_float(row.get(num_name)))
                        and _float(row.get(num_name)) <= cut,
                    )
                )
                rules.append(
                    Rule(
                        f"NOT {bool_name} AND {num_name} >= {cut:.12g}",
                        lambda row, bool_name=bool_name, num_name=num_name, cut=cut: (
                            not _bool(row.get(bool_name))
                        )
                        and math.isfinite(_float(row.get(num_name)))
                        and _float(row.get(num_name)) >= cut,
                    )
                )
                rules.append(
                    Rule(
                        f"NOT {bool_name} AND {num_name} <= {cut:.12g}",
                        lambda row, bool_name=bool_name, num_name=num_name, cut=cut: (
                            not _bool(row.get(bool_name))
                        )
                        and math.isfinite(_float(row.get(num_name)))
                        and _float(row.get(num_name)) <= cut,
                    )
                )
    return rules


def _passes_gate(calibration: dict[str, Any], test: dict[str, Any], ece: float) -> bool:
    return (
        calibration["support"] >= ACCEPTANCE_95["calibration_support_min"]
        and test["support"] >= ACCEPTANCE_95["test_support_min"]
        and calibration["precision_wilson_lcb_95"]
        >= ACCEPTANCE_95["precision_wilson_lcb_95_min"]
        and test["precision_wilson_lcb_95"] >= ACCEPTANCE_95["precision_wilson_lcb_95_min"]
        and ece <= ACCEPTANCE_95["ece_max"]
        and test["coverage"] >= ACCEPTANCE_95["coverage_min"]
        and len(test["validation_instruments"]) >= ACCEPTANCE_95["validation_instruments_min"]
        and len(test["validation_market_contexts"])
        >= ACCEPTANCE_95["validation_market_contexts_min"]
        and len(test["validation_timeframes"]) >= ACCEPTANCE_95["validation_timeframes_min"]
    )


def _blockers(calibration: dict[str, Any], test: dict[str, Any], ece: float) -> list[str]:
    blockers: list[str] = []
    if calibration["support"] < ACCEPTANCE_95["calibration_support_min"]:
        blockers.append("calibration_support_below_120")
    if test["support"] < ACCEPTANCE_95["test_support_min"]:
        blockers.append("test_support_below_60")
    if calibration["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        blockers.append("calibration_wilson95_below_0_95")
    if test["precision_wilson_lcb_95"] < ACCEPTANCE_95["precision_wilson_lcb_95_min"]:
        blockers.append("test_wilson95_below_0_95")
    if ece > ACCEPTANCE_95["ece_max"]:
        blockers.append("ece_above_0_05")
    if test["coverage"] < ACCEPTANCE_95["coverage_min"]:
        blockers.append("coverage_below_0_03")
    if len(test["validation_instruments"]) < ACCEPTANCE_95["validation_instruments_min"]:
        blockers.append("validation_instruments_below_2")
    if len(test["validation_market_contexts"]) < ACCEPTANCE_95["validation_market_contexts_min"]:
        blockers.append("validation_market_contexts_below_2")
    if len(test["validation_timeframes"]) < ACCEPTANCE_95["validation_timeframes_min"]:
        blockers.append("validation_timeframes_below_2")
    return blockers


def _probe_label(
    *,
    label: str,
    rules: list[Rule],
    train_rows: list[dict[str, Any]],
    calibration_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for rule in rules:
        train = _metric(label, rule.select(train_rows), len(train_rows))
        if train["support"] < 120 or train["coverage"] < 0.03:
            continue
        calibration = _metric(label, rule.select(calibration_rows), len(calibration_rows))
        test = _metric(label, rule.select(test_rows), len(test_rows))
        ece = abs(test["precision"] - calibration["precision"]) if calibration["support"] else 1.0
        candidates.append(
            {
                "rule": rule.description,
                "train": train,
                "calibration": calibration,
                "test": test,
                "ece": ece,
                "accepted_95": _passes_gate(calibration, test, ece),
                "blockers": _blockers(calibration, test, ece),
            }
        )
    candidates.sort(
        key=lambda item: (
            item["accepted_95"],
            item["test"]["precision_wilson_lcb_95"],
            item["calibration"]["precision_wilson_lcb_95"],
            item["test"]["support"],
        ),
        reverse=True,
    )
    best = candidates[0] if candidates else None
    accepted = [item for item in candidates if item["accepted_95"]]
    return {
        "root_class": label,
        "state": "accepted_95" if accepted else "blocked",
        "accepted_candidate_count": len(accepted),
        "selected_candidate": accepted[0] if accepted else best,
        "top_candidates": candidates[:10],
    }


def _schema(thresholds: dict[str, float], row_counts: dict[str, dict[str, int]]) -> dict[str, Any]:
    return {
        "schema_version": "main-regime-v2-target-schema/v1",
        "root_axis": ["Bull", "Bear", "Sideways", "Crisis"],
        "manipulation_treatment": "fifth_main_class_or_overlay_fail_closed",
        "residual_bucket": "UnknownOrMixed",
        "input_feature_table": str(INPUT_FEATURE_TABLE),
        "chronological_split": "per instrument:market:timeframe context, 50% train / 25% calibration / 25% test",
        "blocked_predictor_prefixes": list(BLOCKED_PREDICTOR_PREFIXES),
        "target_definitions": {
            "Crisis": (
                "target_extreme_stress == true OR future_absret_h8h >= "
                "train_context_pool_q90; evaluated before Bull/Bear/Sideways"
            ),
            "Sideways": "target_range_consolidation == true AND NOT Crisis",
            "Bull": (
                "future_ret_h8h >= train_context_pool_q65 AND NOT Crisis AND NOT Sideways"
            ),
            "Bear": (
                "future_ret_h8h <= train_context_pool_q35 AND NOT Crisis AND NOT Sideways"
            ),
            "Manipulation": (
                "not materialized from this OHLCV-derived table; requires direct tick/order-flow/"
                "L2/order-lifecycle or crypto event/social evidence"
            ),
            "UnknownOrMixed": "residual bucket after Crisis/Sideways/Bull/Bear",
        },
        "train_thresholds": thresholds,
        "row_counts_by_split_and_root": row_counts,
        "acceptance_95": ACCEPTANCE_95,
    }


def _crosswalk() -> dict[str, Any]:
    return {
        "schema_version": "main-regime-v2-crosswalk/v1",
        "rule": "sub-regime packets are evidence only and cannot promote a root class without this root gate",
        "crosswalk": {
            "Bull": {
                "sub_regime_evidence": ["TrendExpansion"],
                "promotion_requirement": "signed positive drift/persistence root packet",
            },
            "Bear": {
                "sub_regime_evidence": ["TrendExpansion", "ExtremeStress"],
                "promotion_requirement": "signed negative drift/persistence root packet, separate from Crisis",
            },
            "Sideways": {
                "sub_regime_evidence": ["RangeConsolidation"],
                "promotion_requirement": "range/chop/compression root packet plus residual bucket",
            },
            "Crisis": {
                "sub_regime_evidence": ["ExtremeStress"],
                "promotion_requirement": "tail/stress/liquidity-cliff root packet, separate from ordinary Bear",
            },
            "Manipulation": {
                "sub_regime_evidence": [],
                "blocked_context_only": ["ThinLiquidity", "SessionLiquidityCoreViable"],
                "promotion_requirement": "direct non-OHLCV manipulation inputs",
                "failure_state": "missing_required_inputs",
            },
            "UnknownOrMixed": {
                "sub_regime_evidence": [],
                "promotion_requirement": "explicit residual bucket, not a tradable accepted class",
            },
        },
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _write_summary_csv(path: Path, reports: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "root_class",
        "state",
        "accepted_candidate_count",
        "selected_rule",
        "calibration_support",
        "calibration_wilson95",
        "test_support",
        "test_wilson95",
        "test_coverage",
        "ece",
        "test_instruments",
        "test_market_contexts",
        "test_timeframes",
        "blockers",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for report in reports:
            selected = report.get("selected_candidate") or {}
            calibration = selected.get("calibration", {})
            test = selected.get("test", {})
            writer.writerow(
                {
                    "root_class": report["root_class"],
                    "state": report["state"],
                    "accepted_candidate_count": report["accepted_candidate_count"],
                    "selected_rule": selected.get("rule", ""),
                    "calibration_support": calibration.get("support", 0),
                    "calibration_wilson95": calibration.get("precision_wilson_lcb_95", 0.0),
                    "test_support": test.get("support", 0),
                    "test_wilson95": test.get("precision_wilson_lcb_95", 0.0),
                    "test_coverage": test.get("coverage", 0.0),
                    "ece": selected.get("ece", 1.0),
                    "test_instruments": ";".join(test.get("validation_instruments", [])),
                    "test_market_contexts": ";".join(test.get("validation_market_contexts", [])),
                    "test_timeframes": ";".join(test.get("validation_timeframes", [])),
                    "blockers": ";".join(selected.get("blockers", [])),
                }
            )


def main() -> int:
    rows = _read_rows()
    train_rows = _split_rows(rows, "train")
    calibration_rows = _split_rows(rows, "calibration")
    test_rows = _split_rows(rows, "test")
    thresholds = _root_thresholds(train_rows)
    for row in rows:
        row["_root_label"] = _assign_root_label(row, thresholds)
    row_counts: dict[str, dict[str, int]] = {}
    for split in ["train", "calibration", "test"]:
        counts = Counter(row["_root_label"] for row in _split_rows(rows, split))
        row_counts[split] = {label: counts.get(label, 0) for label in ROOT_CLASSES}

    rules = _candidate_rules(train_rows)
    reports = [
        _probe_label(
            label=label,
            rules=rules,
            train_rows=train_rows,
            calibration_rows=calibration_rows,
            test_rows=test_rows,
        )
        for label in ["Bull", "Bear", "Sideways", "Crisis"]
    ]
    manipulation_report = {
        "root_class": "Manipulation",
        "state": "missing_required_inputs",
        "accepted_candidate_count": 0,
        "selected_candidate": {
            "rule": "",
            "calibration": {"support": 0, "precision_wilson_lcb_95": 0.0},
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
        },
        "required_inputs": [
            "tick/trade tape with aggressor side or enough fields to infer order-flow imbalance",
            "bid/ask quotes or L2 depth snapshots",
            "order lifecycle anomalies",
            "venue/liquidity-taking behavior",
            "crypto event/social/mempool evidence when applicable",
        ],
        "explicit_non_evidence": [
            "ThinLiquidity",
            "SessionLiquidityCoreViable",
            "volume ratios",
            "daily range compression",
            "sweep-like OHLCV shapes",
        ],
    }
    all_reports = reports + [manipulation_report]
    accepted_roots = [item["root_class"] for item in all_reports if item["state"] == "accepted_95"]
    blocked_roots = [item["root_class"] for item in all_reports if item["state"] != "accepted_95"]

    calibration_report = {
        "schema_version": "main-regime-v2-root-calibration/v1",
        "loop_id": "20260510T232844+0800-codex-main-regime-v2-root-probe",
        "run_root": str(RUN_ROOT),
        "objective": "Build MainRegimeV2 target schema/crosswalk and rerun unchanged 95% root-class gates.",
        "input_feature_table": str(INPUT_FEATURE_TABLE),
        "blocked_predictor_prefixes": list(BLOCKED_PREDICTOR_PREFIXES),
        "predictor_features_used": BOOLEAN_FEATURES + NUMERIC_FEATURES,
        "target_schema": str(OUTPUT_DIR / "main_regime_v2_target_schema.json"),
        "crosswalk": str(OUTPUT_DIR / "main_regime_v2_crosswalk.json"),
        "acceptance_95": ACCEPTANCE_95,
        "root_reports": all_reports,
        "decision": {
            "board_state": "blocked",
            "accepted_95_root_classes": accepted_roots,
            "blocked_root_classes": blocked_roots,
            "accepted_95_all_main_regime_v2_roots": len(blocked_roots) == 0,
            "trade_usable": False,
            "why_not_complete": [
                "No root class passed the unchanged MainRegimeV2 95% gate in this probe."
                if not accepted_roots
                else "Not every MainRegimeV2 root class passed the unchanged 95% gate.",
                "Manipulation remains fail-closed because the source table has OHLCV-derived context only and no direct microstructure/order-flow/order-lifecycle inputs.",
            ],
            "next_action": (
                "Add higher-signal root-class features and direct Manipulation inputs, then rerun "
                "the same chronological root gate without promoting sub-regime packets."
            ),
        },
    }

    _write_json(OUTPUT_DIR / "main_regime_v2_target_schema.json", _schema(thresholds, row_counts))
    _write_json(OUTPUT_DIR / "main_regime_v2_crosswalk.json", _crosswalk())
    _write_json(OUTPUT_DIR / "main_regime_v2_root_calibration_report.json", calibration_report)
    _write_summary_csv(OUTPUT_DIR / "main_regime_v2_root_probe_summary.csv", all_reports)
    (RUN_ROOT / "README.md").write_text(
        "# MainRegimeV2 Root Probe\n\n"
        "This run materializes the MainRegimeV2 target schema/crosswalk and evaluates "
        "root-level 95% gates without promoting existing sub-regime packets.\n\n"
        f"- input feature table: `{INPUT_FEATURE_TABLE}`\n"
        f"- schema: `{OUTPUT_DIR / 'main_regime_v2_target_schema.json'}`\n"
        f"- crosswalk: `{OUTPUT_DIR / 'main_regime_v2_crosswalk.json'}`\n"
        f"- calibration report: `{OUTPUT_DIR / 'main_regime_v2_root_calibration_report.json'}`\n"
        f"- summary CSV: `{OUTPUT_DIR / 'main_regime_v2_root_probe_summary.csv'}`\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": True,
                "accepted_roots": accepted_roots,
                "blocked_roots": blocked_roots,
                "report": str(OUTPUT_DIR / "main_regime_v2_root_calibration_report.json"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
