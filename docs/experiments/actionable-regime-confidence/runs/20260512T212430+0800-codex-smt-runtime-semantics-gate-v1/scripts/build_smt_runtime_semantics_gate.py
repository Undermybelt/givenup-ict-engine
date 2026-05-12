#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[4]
OBS_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T205906+0800-codex-smt-full-coverage-provider-observation-v2"
OBS_PACKET = OBS_ROOT / "materials/smt_provider_observation_packet.json"
OUTCOME_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T211032+0800-codex-smt-full-coverage-outcome-entry-context-v1"
OUTCOME_PACKET = OUTCOME_ROOT / "materials/smt_full_coverage_outcome_entry_context_packet.json"

REGIMES = ["trend", "range", "transition", "stress", "other"]
REQUIRED_RUNTIME_FIELDS = [
    "base_symbol",
    "comparison_symbol",
    "relationship_type",
    "relationship_confidence",
    "timeframe",
    "session",
    "smt_signal",
    "base_swing_type",
    "base_level",
    "comparison_swing_type",
    "comparison_level",
    "swept_side",
    "normalized_for_inverse_correlation",
    "near_pd_array",
    "pd_array_type",
    "mss_or_cisd_confirmed",
    "displacement_confirmed",
    "confidence",
    "fail_closed_reason",
]


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def valid_level(value: Any) -> bool:
    if value in (None, "", "n/a"):
        return False
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def row_semantics(row: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    signal = str(row.get("smt_signal") or "none")
    relationship = str(row.get("relationship_type") or "uncertain")

    if signal == "none":
        return False, ["no_same_event_smt_confirmation_failure"]

    missing = [field for field in REQUIRED_RUNTIME_FIELDS if field not in row]
    if missing:
        reasons.append("missing_required_fields:" + ",".join(missing))

    if not parse_bool(row.get("timeframe_aligned")):
        reasons.append("timeframe_not_aligned")
    if not parse_bool(row.get("session_overlap")):
        reasons.append("session_not_overlapped")
    if not parse_bool(row.get("same_event_window_confirmed")):
        reasons.append("same_event_window_not_confirmed")
    if not valid_level(row.get("base_level")):
        reasons.append("missing_base_level")
    if not valid_level(row.get("comparison_level")):
        reasons.append("missing_comparison_level")
    if parse_bool(row.get("actionable")):
        reasons.append("smt_must_not_be_actionable")
    if str(row.get("confirmation_role") or "") != "confirmation_only":
        reasons.append("smt_confirmation_role_not_locked")

    base_swing = str(row.get("base_swing_type") or "")
    comparison_swing = str(row.get("comparison_swing_type") or "")
    swept_side = str(row.get("swept_side") or "")
    if signal == "bullish_smt":
        if base_swing != "LL":
            reasons.append("bullish_smt_base_not_ll")
        if comparison_swing != "HL":
            reasons.append("bullish_smt_comparison_not_hl")
        if swept_side != "sell_side_liquidity":
            reasons.append("bullish_smt_missing_sell_side_sweep")
    elif signal == "bearish_smt":
        if base_swing != "HH":
            reasons.append("bearish_smt_base_not_hh")
        if comparison_swing != "LH":
            reasons.append("bearish_smt_comparison_not_lh")
        if swept_side != "buy_side_liquidity":
            reasons.append("bearish_smt_missing_buy_side_sweep")
    else:
        reasons.append("unsupported_smt_signal")

    if relationship == "negative":
        if not parse_bool(row.get("normalized_for_inverse_correlation")):
            reasons.append("inverse_relationship_not_normalized")
        if row.get("raw_comparison_swing_type") in (None, "", "n/a"):
            reasons.append("inverse_relationship_missing_raw_comparison_swing_type")
        if not valid_level(row.get("raw_comparison_level")):
            reasons.append("inverse_relationship_missing_raw_comparison_level")
    elif parse_bool(row.get("normalized_for_inverse_correlation")):
        reasons.append("positive_relationship_unexpected_inverse_normalization")

    return not reasons, reasons


def summarize_regimes(outcome_packet: dict[str, Any], semantic_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    outcome_stats = outcome_packet.get("per_regime_statistics", {})
    semantic_counts = Counter(row["regime_bucket"] for row in semantic_rows if row["semantic_gate_passed"])
    out: dict[str, dict[str, Any]] = {}
    for regime in REGIMES:
        stat = dict(outcome_stats.get(regime, {}))
        out[regime] = {
            "regime_bucket": regime,
            "semantic_event_count": semantic_counts.get(regime, 0),
            "event_count": stat.get("event_count", 0),
            "trade_count": stat.get("trade_count", 0) or 0,
            "win_rate": stat.get("win_rate"),
            "expectancy": stat.get("expectancy"),
            "candidate_win_rate_6h": stat.get("candidate_win_rate_6h"),
            "candidate_expectancy_6h": stat.get("candidate_expectancy_6h"),
            "confidence": min((stat.get("trade_count", 0) or 0) / 30.0, 1.0),
            "fail_closed_reason": stat.get("fail_closed_reason") or "missing_mss_cisd_displacement_pda_entry_context",
        }
    return out


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})


def main() -> int:
    obs = json.loads(OBS_PACKET.read_text())
    outcome = json.loads(OUTCOME_PACKET.read_text())

    semantic_rows: list[dict[str, Any]] = []
    for row in obs["rows"]:
        passed, reasons = row_semantics(row)
        semantic_rows.append(
            {
                "base_symbol": row.get("base_symbol"),
                "comparison_symbol": row.get("comparison_symbol"),
                "relationship_type": row.get("relationship_type"),
                "relationship_confidence": row.get("relationship_confidence"),
                "timeframe": row.get("timeframe"),
                "session": row.get("session"),
                "event_time": row.get("event_time"),
                "smt_signal": row.get("smt_signal"),
                "base_swing_type": row.get("base_swing_type"),
                "base_level": row.get("base_level"),
                "comparison_swing_type": row.get("comparison_swing_type"),
                "comparison_level": row.get("comparison_level"),
                "swept_side": row.get("swept_side"),
                "normalized_for_inverse_correlation": row.get("normalized_for_inverse_correlation"),
                "raw_comparison_swing_type": row.get("raw_comparison_swing_type"),
                "raw_comparison_level": row.get("raw_comparison_level"),
                "same_event_window_confirmed": row.get("same_event_window_confirmed"),
                "near_pd_array": row.get("near_pd_array"),
                "pd_array_type": row.get("pd_array_type"),
                "mss_or_cisd_confirmed": row.get("mss_or_cisd_confirmed"),
                "displacement_confirmed": row.get("displacement_confirmed"),
                "regime_bucket": row.get("regime_bucket") or "other",
                "actionable": row.get("actionable"),
                "semantic_gate_passed": passed,
                "semantic_fail_reason": "n/a" if passed else ";".join(reasons),
            }
        )

    passed_rows = [row for row in semantic_rows if row["semantic_gate_passed"]]
    signal_rows = [row for row in semantic_rows if row["smt_signal"] != "none"]
    inverse_signal_rows = [row for row in signal_rows if row["relationship_type"] == "negative"]
    per_regime = summarize_regimes(outcome, semantic_rows)
    relationship_rows = obs.get("provider_readbacks", [])

    field_mapping = {
        "Structure": ["base_swing_type", "comparison_swing_type", "swept_side", "base_level", "comparison_level"],
        "Technicals": ["same_event_window_confirmed", "near_pd_array", "pd_array_type", "displacement_confirmed"],
        "SMT": ["base_symbol", "comparison_symbol", "relationship_type", "normalized_for_inverse_correlation", "smt_signal"],
        "Regime posterior evidence": ["regime_bucket", "per_regime_statistics.confidence", "fail_closed_reason"],
        "Execution tree features": ["confirmation_role", "actionable", "mss_or_cisd_confirmed", "displacement_confirmed"],
        "Feedback/update learning fields": ["trade_count", "win_rate", "expectancy", "candidate_win_rate_6h", "candidate_expectancy_6h"],
    }

    packet = {
        "factor_name": "smt_runtime_semantics_gate",
        "factor_version": "2026-05-12.runtime-semantics.v1",
        "definition": "ICT SMT divergence is same-timeframe/session sibling-market swing confirmation failure around the same liquidity event; it is not generic correlation or relative strength.",
        "source_observation_packet": str(OBS_PACKET.relative_to(REPO)),
        "source_outcome_packet": str(OUTCOME_PACKET.relative_to(REPO)),
        "branch_path_contract": obs["branch_path_contract"],
        "dynamic_relationship_resolution": relationship_rows,
        "runtime_schema_required_fields": REQUIRED_RUNTIME_FIELDS,
        "aggregate": {
            "provider_pairs": len(relationship_rows),
            "rows": len(semantic_rows),
            "smt_signal_rows": len(signal_rows),
            "semantic_gate_passed_rows": len(passed_rows),
            "inverse_signal_rows": len(inverse_signal_rows),
            "actionable_rows": sum(1 for row in semantic_rows if parse_bool(row.get("actionable"))),
            "entry_context_complete_count": outcome.get("aggregate", {}).get("entry_context_complete_count", 0),
            "trade_count": sum((row.get("trade_count", 0) or 0) for row in per_regime.values()),
        },
        "per_regime_statistics": per_regime,
        "field_mapping": field_mapping,
        "quality_gate": {
            "semantic_gate_passed": len(passed_rows) == len(signal_rows) and len(signal_rows) > 0,
            "smt_as_confirmation_only": True,
            "actionable_allowed": False,
            "entry_context_complete": False,
            "learning_quality_weight": 0.0,
            "pre_bayes_filter_allowed": False,
            "bbn_learning_allowed": False,
            "catboost_path_ranker_allowed": False,
            "execution_tree_branch_weight_update_allowed": False,
            "feedback_update_learning_allowed": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "fail_closed_reason": "semantic_gate_passes_but_entry_context_and_per_regime_trade_counts_missing",
        },
    }

    write_csv(
        ROOT / "summaries/smt_runtime_semantics_gate_rows.csv",
        semantic_rows,
        [
            "base_symbol",
            "comparison_symbol",
            "relationship_type",
            "relationship_confidence",
            "timeframe",
            "session",
            "event_time",
            "smt_signal",
            "base_swing_type",
            "base_level",
            "comparison_swing_type",
            "comparison_level",
            "swept_side",
            "normalized_for_inverse_correlation",
            "raw_comparison_swing_type",
            "raw_comparison_level",
            "same_event_window_confirmed",
            "near_pd_array",
            "pd_array_type",
            "mss_or_cisd_confirmed",
            "displacement_confirmed",
            "regime_bucket",
            "actionable",
            "semantic_gate_passed",
            "semantic_fail_reason",
        ],
    )
    write_csv(
        ROOT / "summaries/smt_runtime_semantics_gate_per_regime.csv",
        list(per_regime.values()),
        [
            "regime_bucket",
            "semantic_event_count",
            "event_count",
            "trade_count",
            "win_rate",
            "expectancy",
            "candidate_win_rate_6h",
            "candidate_expectancy_6h",
            "confidence",
            "fail_closed_reason",
        ],
    )
    (ROOT / "materials/smt_runtime_semantics_gate_packet.json").write_text(json.dumps(packet, indent=2) + "\n")
    print(json.dumps(packet["aggregate"] | packet["quality_gate"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
