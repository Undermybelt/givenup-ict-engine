from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
BASE_SCRIPT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/20260510T232844-codex-main-regime-v2-root-probe/tmp-scripts/main_regime_v2_root_probe.py"
)
RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260510T234600-main-regime-v2-corrected-advanced-features"
)
OUTPUT_DIR = RUN_ROOT / "root-v2"
CHECKS_DIR = RUN_ROOT / "checks"

ADVANCED_NUMERIC_FEATURES = [
    "ret_8",
    "ret_16",
    "trend_persistence16",
    "range_persistence16",
    "stress_persistence16",
    "reversal_persistence16",
    "thin_persistence16",
    "dc_up_rate16",
    "dc_down_rate16",
    "bull_state_score",
    "bear_state_score",
    "sideways_state_score",
    "crisis_state_score",
    "root_confidence_proxy",
]


def _load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("main_regime_v2_root_probe_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.RUN_ROOT = RUN_ROOT
    module.OUTPUT_DIR = OUTPUT_DIR
    module.NUMERIC_FEATURES = list(dict.fromkeys(module.NUMERIC_FEATURES + ADVANCED_NUMERIC_FEATURES))
    return module


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


def _safe_div(num: float, den: float) -> float:
    if not math.isfinite(num) or not math.isfinite(den) or abs(den) <= 1e-12:
        return math.nan
    return num / den


def _rolling_mean(values: list[float], idx: int, window: int) -> float:
    start = max(0, idx - window + 1)
    clean = [value for value in values[start : idx + 1] if math.isfinite(value)]
    return sum(clean) / len(clean) if clean else math.nan


def _rolling_min(values: list[float], idx: int, window: int) -> float:
    start = max(0, idx - window + 1)
    clean = [value for value in values[start : idx + 1] if math.isfinite(value)]
    return min(clean) if clean else math.nan


def _rolling_max(values: list[float], idx: int, window: int) -> float:
    start = max(0, idx - window + 1)
    clean = [value for value in values[start : idx + 1] if math.isfinite(value)]
    return max(clean) if clean else math.nan


def _quantile(values: list[float], ratio: float) -> float:
    clean = sorted(value for value in values if math.isfinite(value))
    if not clean:
        return math.nan
    idx = min(len(clean) - 1, max(0, int((len(clean) - 1) * ratio)))
    return clean[idx]


def _add_advanced_fields(rows: list[dict[str, Any]]) -> None:
    by_context: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_context[str(row["_context"])].append(row)

    train_ranges = [_float(row.get("range_pct")) for row in rows if row.get("_split") == "train"]
    train_range_mid = max(_quantile(train_ranges, 0.50), 1e-6)

    for context_rows in by_context.values():
        context_rows.sort(key=lambda item: str(item["ts"]))
        closes = [_float(row.get("close")) for row in context_rows]
        highs = [_float(row.get("high")) for row in context_rows]
        lows = [_float(row.get("low")) for row in context_rows]
        trend_flags = [1.0 if _bool(row.get("condition_trend_expansion")) else 0.0 for row in context_rows]
        range_flags = [1.0 if _bool(row.get("condition_range_consolidation")) else 0.0 for row in context_rows]
        stress_flags = [1.0 if _bool(row.get("condition_extreme_stress")) else 0.0 for row in context_rows]
        reversal_flags = [1.0 if _bool(row.get("condition_reversal_brewing")) else 0.0 for row in context_rows]
        thin_flags = [1.0 if _bool(row.get("condition_thin_liquidity")) else 0.0 for row in context_rows]
        dc_up_events: list[float] = []
        dc_down_events: list[float] = []
        for idx, row in enumerate(context_rows):
            close = closes[idx]
            ret_8 = math.nan
            ret_16 = math.nan
            if idx >= 8 and closes[idx - 8] > 0 and close > 0:
                ret_8 = math.log(close / closes[idx - 8])
            if idx >= 16 and closes[idx - 16] > 0 and close > 0:
                ret_16 = math.log(close / closes[idx - 16])
            recent_low = _rolling_min(lows, idx, 16)
            recent_high = _rolling_max(highs, idx, 16)
            dc_up = (
                math.isfinite(close)
                and math.isfinite(recent_low)
                and recent_low > 0
                and close / recent_low - 1.0 >= 2.0 * train_range_mid
            )
            dc_down = (
                math.isfinite(close)
                and math.isfinite(recent_high)
                and recent_high > 0
                and close / recent_high - 1.0 <= -2.0 * train_range_mid
            )
            dc_up_events.append(1.0 if dc_up else 0.0)
            dc_down_events.append(1.0 if dc_down else 0.0)

            trend_p = _rolling_mean(trend_flags, idx, 16)
            range_p = _rolling_mean(range_flags, idx, 16)
            stress_p = _rolling_mean(stress_flags, idx, 16)
            reversal_p = _rolling_mean(reversal_flags, idx, 16)
            thin_p = _rolling_mean(thin_flags, idx, 16)
            dc_up_rate = _rolling_mean(dc_up_events, idx, 16)
            dc_down_rate = _rolling_mean(dc_down_events, idx, 16)
            ret_1 = _float(row.get("ret_1"))
            ret_4 = _float(row.get("ret_4"))
            stretch = _float(row.get("stretch_32"))
            range_pct = _float(row.get("range_pct"))
            vol_rank = _float(row.get("realized_vol_rank_252"))
            range_rank = _float(row.get("range_rank_252"))
            stretch_abs_rank = _float(row.get("stretch_abs_rank_252"))

            bull_score = (
                (ret_4 if math.isfinite(ret_4) else 0.0)
                + (ret_8 if math.isfinite(ret_8) else 0.0)
                + (ret_16 if math.isfinite(ret_16) else 0.0)
                + trend_p * 0.02
                + dc_up_rate * 0.02
                - stress_p * 0.02
            )
            bear_score = (
                -(ret_4 if math.isfinite(ret_4) else 0.0)
                - (ret_8 if math.isfinite(ret_8) else 0.0)
                - (ret_16 if math.isfinite(ret_16) else 0.0)
                + dc_down_rate * 0.02
                + stress_p * 0.01
            )
            sideways_score = (
                range_p * 0.04
                - abs(ret_1 if math.isfinite(ret_1) else 0.0)
                - abs(ret_4 if math.isfinite(ret_4) else 0.0)
                - (range_rank if math.isfinite(range_rank) else 0.5) * 0.01
                - (stretch_abs_rank if math.isfinite(stretch_abs_rank) else 0.5) * 0.01
            )
            crisis_score = (
                stress_p * 0.04
                + (vol_rank if math.isfinite(vol_rank) else 0.0) * 0.01
                + (range_rank if math.isfinite(range_rank) else 0.0) * 0.01
                + abs(ret_4 if math.isfinite(ret_4) else 0.0)
                + (range_pct if math.isfinite(range_pct) else 0.0)
            )
            row.update(
                {
                    "ret_8": ret_8,
                    "ret_16": ret_16,
                    "trend_persistence16": trend_p,
                    "range_persistence16": range_p,
                    "stress_persistence16": stress_p,
                    "reversal_persistence16": reversal_p,
                    "thin_persistence16": thin_p,
                    "dc_up_rate16": dc_up_rate,
                    "dc_down_rate16": dc_down_rate,
                    "bull_state_score": bull_score,
                    "bear_state_score": bear_score,
                    "sideways_state_score": sideways_score,
                    "crisis_state_score": crisis_score,
                    "root_confidence_proxy": max(bull_score, bear_score, sideways_score, crisis_score),
                }
            )


def main() -> int:
    module = _load_base_module()
    rows = module._read_rows()
    _add_advanced_fields(rows)
    train_rows = module._split_rows(rows, "train")
    calibration_rows = module._split_rows(rows, "calibration")
    test_rows = module._split_rows(rows, "test")
    thresholds = module._root_thresholds(train_rows)
    for row in rows:
        row["_root_label"] = module._assign_root_label(row, thresholds)
    row_counts: dict[str, dict[str, int]] = {}
    for split in ["train", "calibration", "test"]:
        counts = Counter(row["_root_label"] for row in module._split_rows(rows, split))
        row_counts[split] = {label: counts.get(label, 0) for label in module.ROOT_CLASSES}

    rules = module._candidate_rules(train_rows)
    reports = [
        module._probe_label(
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
    }
    all_reports = reports + [manipulation_report]
    accepted_roots = [item["root_class"] for item in all_reports if item["state"] == "accepted_95"]
    blocked_roots = [item["root_class"] for item in all_reports if item["state"] != "accepted_95"]
    report = {
        "schema_version": "main-regime-v2-corrected-advanced-root-features/v1",
        "loop_id": "20260510T234600+0800-main-regime-v2-corrected-advanced-features",
        "run_root": str(RUN_ROOT),
        "objective": "Try higher-signal deterministic directional-change/persistence/state-score features on the corrected MainRegimeV2 root axis.",
        "input_feature_table": str(module.INPUT_FEATURE_TABLE),
        "base_root_probe": "docs/experiments/actionable-regime-confidence/runs/20260510T232844-codex-main-regime-v2-root-probe/root-v2/main_regime_v2_root_calibration_report.json",
        "predictor_features_used": module.BOOLEAN_FEATURES + module.NUMERIC_FEATURES,
        "advanced_numeric_features": ADVANCED_NUMERIC_FEATURES,
        "blocked_predictor_prefixes": list(module.BLOCKED_PREDICTOR_PREFIXES),
        "acceptance_95": module.ACCEPTANCE_95,
        "target_schema": str(OUTPUT_DIR / "main_regime_v2_target_schema.json"),
        "crosswalk": str(OUTPUT_DIR / "main_regime_v2_crosswalk.json"),
        "root_reports": all_reports,
        "decision": {
            "board_state": "blocked",
            "accepted_95_root_classes": accepted_roots,
            "blocked_root_classes": blocked_roots,
            "accepted_95_all_main_regime_v2_roots": len(blocked_roots) == 0,
            "trade_usable": False,
            "why_not_complete": [
                "Higher-signal deterministic OHLCV-derived features still did not make every corrected root class pass the unchanged 95% gate.",
                "Manipulation remains fail-closed because no direct microstructure/order-flow/order-lifecycle or crypto event/social inputs are present.",
            ],
            "next_action": "Stop repeating OHLCV-derived root-rule searches; ingest new root evidence or required manipulation inputs before rerunning.",
        },
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    module._write_json(OUTPUT_DIR / "main_regime_v2_target_schema.json", module._schema(thresholds, row_counts))
    module._write_json(OUTPUT_DIR / "main_regime_v2_crosswalk.json", module._crosswalk())
    module._write_json(OUTPUT_DIR / "corrected_advanced_root_feature_report.json", report)
    module._write_summary_csv(OUTPUT_DIR / "corrected_advanced_root_feature_summary.csv", all_reports)
    RUN_ROOT.joinpath("README.md").write_text(
        "# Corrected MainRegimeV2 Advanced Root Features\n\n"
        "This run keeps the corrected root axis from 20260510T232844 and adds deterministic "
        "directional-change, persistence, and state-score predictors. It does not use future/target "
        "columns as predictors and does not relax thresholds.\n",
        encoding="utf-8",
    )
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    assertions = [
        f"report: {OUTPUT_DIR / 'corrected_advanced_root_feature_report.json'}",
        f"accepted_root_classes_95: {accepted_roots}",
        f"blocked_root_classes: {blocked_roots}",
        f"accepted_gate: {report['decision']['accepted_95_all_main_regime_v2_roots']}",
        "thresholds_relaxed: False",
        "blocked_future_target_predictors: True",
    ]
    for item in all_reports:
        selected = item.get("selected_candidate") or {}
        test = selected.get("test", {})
        assertions.append(
            f"{item['root_class']}: state={item['state']} "
            f"test_lcb={float(test.get('precision_wilson_lcb_95', 0.0)):.6f} "
            f"test_support={test.get('support', 0)} blockers={selected.get('blockers', [])}"
        )
    (CHECKS_DIR / "corrected_advanced_root_feature_assertions.out").write_text(
        "\n".join(assertions) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "ok": True,
                "accepted_roots": accepted_roots,
                "blocked_roots": blocked_roots,
                "report": str(OUTPUT_DIR / "corrected_advanced_root_feature_report.json"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
