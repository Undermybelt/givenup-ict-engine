#!/usr/bin/env python3
"""Assert the 220646 branch-admission gap packet stays fail-closed."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "materials/220646_prebayes_bbn_branch_admission_gap_packet.json"


def main() -> None:
    packet = json.loads(PACKET.read_text())
    gate = packet["gate"]
    assert packet["branch_feedback"]["feedback_rows"] == 48
    assert packet["branch_feedback"]["branch_path_count"] >= 4
    assert packet["pre_bayes_filter"]["nq_state"]["policy_present"] is True
    assert packet["pre_bayes_filter"]["src_root_state"]["policy_present"] is False
    assert packet["pre_bayes_filter"]["src_root_state"]["gate_status"] == "blocked"
    assert packet["bbn"]["applied_rows"] == 3
    assert packet["bbn"]["skipped_unsupported_label_rows"] == 1
    assert packet["execution_tree"]["candidate_present"] is True
    assert packet["execution_tree"]["execution_gate_status"] == "execution_blocked"
    assert packet["execution_tree"]["pre_bayes_gate_status"] == "blocked"
    assert gate["branch_path_preserved"] is True
    assert gate["catboost_path_ranker_satisfied"] is True
    assert gate["pre_bayes_filter_satisfied"] is False
    assert gate["bbn_learning_satisfied"] is False
    assert gate["execution_tree_admitted"] is False
    assert gate["promotion_allowed"] is False
    assert gate["trade_usable"] is False
    assert "pre_bayes_state_exists_for_NQ_not_SRC_ROOT" in gate["fail_closed_reasons"]
    assert "src_root_pre_bayes_gate_blocked" in gate["fail_closed_reasons"]
    print(
        "packet_assertion=pass "
        "branch_path=true catboost=true pre_bayes=false bbn=false execution=false trade_usable=false"
    )


if __name__ == "__main__":
    main()
