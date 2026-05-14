#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "materials/smt_provider_window_event_alignment_expansion_packet.json"
ROWS = ROOT / "summaries/smt_provider_window_event_alignment_expansion_rows.csv"
PER_REGIME = ROOT / "summaries/smt_provider_window_event_alignment_expansion_per_regime.csv"
PAIR_SUMMARY = ROOT / "summaries/smt_provider_window_event_alignment_expansion_pair_summary.csv"


def main() -> int:
    packet = json.loads(PACKET.read_text())
    rows = list(csv.DictReader(ROWS.open(newline="")))
    per_regime = list(csv.DictReader(PER_REGIME.open(newline="")))
    pair_summary = list(csv.DictReader(PAIR_SUMMARY.open(newline="")))

    assert packet["factor_name"] == "smt_provider_window_event_alignment_expansion_v1"
    assert "not ordinary correlation" in packet["definition"]
    assert rows, "provider-window event rows required"
    assert len(per_regime) == 5, "per-regime trend/range/transition/stress/other rows required"
    assert len(pair_summary) == 7, "required pair summary rows required"
    assert all(row["actionable"] == "False" for row in rows)
    assert all(row["confirmation_role"] == "confirmation_only" for row in rows)
    assert all(row["base_level"] not in ("", "None", "null") for row in rows)
    assert all(row["comparison_level"] not in ("", "None", "null") for row in rows)
    inverse_rows = [row for row in rows if row["relationship_type"] == "negative"]
    assert all(row["normalized_for_inverse_correlation"] == "True" for row in inverse_rows)
    assert all(row["raw_comparison_swing_type"] for row in inverse_rows)

    gate = packet["quality_gate"]
    assert gate["smt_confirmation_only"] is True
    assert gate["standalone_actionable_allowed"] is False
    assert gate["actionable"] is False
    assert gate["pre_bayes_filter_allowed"] is False
    assert gate["bbn_learning_allowed"] is False
    assert gate["catboost_path_ranker_allowed"] is False
    assert gate["execution_tree_branch_weight_update_allowed"] is False
    assert gate["promotion_allowed"] is False
    assert gate["trade_usable"] is False
    assert packet["counts"]["strict_trade_count"] < gate["min_trade_count_for_learning"] or gate["per_regime_learning_floor_met"] is False

    print(json.dumps({
        "packet_assertion": "pass",
        "rows": packet["counts"]["rows"],
        "strict_trade_count": packet["counts"]["strict_trade_count"],
        "inverse_normalized_signal_rows": packet["counts"]["inverse_normalized_signal_rows"],
        "downstream_allowed": False,
        "fail_closed_reason": gate["fail_closed_reason"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
