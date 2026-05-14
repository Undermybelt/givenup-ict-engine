#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "materials/smt_full_coverage_outcome_entry_context_packet.json"
ROWS = ROOT / "summaries/smt_full_coverage_outcome_entry_context_rows.csv"
REGIME = ROOT / "summaries/smt_full_coverage_outcome_entry_context_regime_summary.csv"


def assert_true(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    packet = json.loads(PACKET.read_text())
    rows = list(csv.DictReader(ROWS.open()))
    regimes = list(csv.DictReader(REGIME.open()))
    required_row_fields = {
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
    }
    assert_true(packet["factor_name"] == "smt_full_coverage_outcome_entry_context_v1", "wrong factor")
    assert_true(len(rows) == packet["aggregate"]["event_count"], "row count mismatch")
    assert_true(packet["aggregate"]["event_count"] >= 40, "insufficient full-coverage SMT events")
    assert_true(packet["aggregate"]["outcome_6h_count"] > 0, "missing 6h outcomes")
    assert_true(packet["aggregate"]["entry_context_complete_count"] == 0, "entry context should remain incomplete")
    assert_true(packet["aggregate"]["required_provider_pair_count"] >= 7, "missing required provider pair coverage")
    assert_true(packet["aggregate"]["required_provider_pairs_without_smt_event"] >= 3, "missing fail-closed no-SMT pair readback")
    assert_true(packet["aggregate"]["inverse_relationship_event_count"] == 0, "inverse rows should not become events without same-event confirmation")
    assert_true(set(packet["per_regime_statistics"]) == {"trend", "range", "transition", "stress", "other"}, "missing regime buckets")
    covered_pairs = {(row["base_symbol"], row["comparison_symbol"]) for row in packet["provider_pair_readback"]}
    for pair in [("NQ", "ES"), ("NQ", "YM"), ("EURUSD", "GBPUSD"), ("EURUSD", "DXY"), ("XAUUSD", "XAGUSD"), ("XAUUSD", "DXY"), ("BTC", "ETH")]:
        assert_true(pair in covered_pairs, f"missing required provider pair {pair}")
    assert_true(packet["quality_gate"]["learning_quality_weight"] == 0.0, "learning quality must fail closed")
    for key in ["auto_quant_dispatch_allowed", "pre_bayes_filter_allowed", "bbn_learning_allowed", "catboost_learning_allowed", "execution_tree_branch_weight_update_allowed", "promotion_allowed", "trade_usable"]:
        assert_true(packet["quality_gate"][key] is False, f"{key} must be false")
    assert_true(required_row_fields.issubset(set(rows[0])), "missing required SMT schema fields")
    for row in rows:
        assert_true(row["actionable"] == "False", "SMT outcome row must not become actionable")
        assert_true(row["confirmation_role"] == "confirmation_only", "SMT rows must be confirmation-only")
        assert_true(row["relationship_type"] in {"positive", "negative", "uncertain"}, "invalid relationship_type")
        assert_true(row["smt_signal"] in {"bullish_smt", "bearish_smt"}, "labelled rows should be non-null SMT events")
        assert_true(row["base_swing_type"] in {"HH", "LH", "LL", "HL", "equal_high", "equal_low"}, "invalid base_swing_type")
        assert_true(row["comparison_swing_type"] in {"HH", "LH", "LL", "HL", "equal_high", "equal_low"}, "invalid comparison_swing_type")
        assert_true(row["base_level"] not in {"", "None"}, "labelled row missing base_level")
        assert_true(row["comparison_level"] not in {"", "None"}, "labelled row missing comparison_level")
        assert_true(row["relationship_confidence"] not in {"", "None"}, "labelled row missing relationship_confidence")
        assert_true(row["confidence"] not in {"", "None"}, "labelled row missing confidence")
        assert_true(row["mss_or_cisd_confirmed"] == "False", "MSS/CISD should remain unconfirmed in this label packet")
        assert_true(row["displacement_confirmed"] == "False", "displacement should remain unconfirmed in this label packet")
        assert_true(row["fail_closed_reason"] == "missing_mss_cisd_displacement_pda_entry_context", "row must fail closed on entry context")
    for row in regimes:
        assert_true(row["trade_count"] == "0", "regime trade_count must stay zero without entry context")
        assert_true(row["fail_closed_reason"] == "missing_mss_cisd_displacement_pda_entry_context", "regime must fail closed")
    print(
        json.dumps(
            {
                "packet_assertion": "pass",
                "rows": len(rows),
                "outcome_6h_count": packet["aggregate"]["outcome_6h_count"],
                "outcome_12h_count": packet["aggregate"]["outcome_12h_count"],
                "entry_context_complete_count": packet["aggregate"]["entry_context_complete_count"],
                "learning_quality_weight": packet["quality_gate"]["learning_quality_weight"],
                "downstream_allowed": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
