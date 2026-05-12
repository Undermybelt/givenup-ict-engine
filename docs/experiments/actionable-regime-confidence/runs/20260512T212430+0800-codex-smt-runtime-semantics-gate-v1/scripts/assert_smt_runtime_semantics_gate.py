#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "materials/smt_runtime_semantics_gate_packet.json"


def main() -> int:
    packet = json.loads(PACKET.read_text())
    aggregate = packet["aggregate"]
    gate = packet["quality_gate"]

    assert packet["definition"].startswith("ICT SMT divergence is same-timeframe/session")
    assert aggregate["provider_pairs"] >= 7
    assert aggregate["smt_signal_rows"] >= 1
    assert aggregate["semantic_gate_passed_rows"] == aggregate["smt_signal_rows"]
    assert aggregate["actionable_rows"] == 0
    assert aggregate["entry_context_complete_count"] == 0
    assert gate["semantic_gate_passed"] is True
    assert gate["smt_as_confirmation_only"] is True
    assert gate["actionable_allowed"] is False
    assert gate["pre_bayes_filter_allowed"] is False
    assert gate["bbn_learning_allowed"] is False
    assert gate["catboost_path_ranker_allowed"] is False
    assert gate["execution_tree_branch_weight_update_allowed"] is False
    assert gate["feedback_update_learning_allowed"] is False
    assert gate["promotion_allowed"] is False
    assert gate["trade_usable"] is False

    for regime in ["trend", "range", "transition", "stress", "other"]:
        stat = packet["per_regime_statistics"][regime]
        assert "trade_count" in stat
        assert "win_rate" in stat
        assert "expectancy" in stat
        assert "confidence" in stat

    for surface in [
        "Structure",
        "Technicals",
        "SMT",
        "Regime posterior evidence",
        "Execution tree features",
        "Feedback/update learning fields",
    ]:
        assert surface in packet["field_mapping"]

    print(
        json.dumps(
            {
                "packet_assertion": "pass",
                "provider_pairs": aggregate["provider_pairs"],
                "smt_signal_rows": aggregate["smt_signal_rows"],
                "semantic_gate_passed_rows": aggregate["semantic_gate_passed_rows"],
                "entry_context_complete_count": aggregate["entry_context_complete_count"],
                "downstream_allowed": gate["pre_bayes_filter_allowed"],
                "trade_usable": gate["trade_usable"],
                "fail_closed_reason": gate["fail_closed_reason"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
