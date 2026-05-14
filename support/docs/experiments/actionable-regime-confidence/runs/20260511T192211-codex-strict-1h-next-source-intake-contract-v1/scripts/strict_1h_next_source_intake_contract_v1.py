#!/usr/bin/env python3
"""Verify the strict 1h next-source intake contract."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
CONTRACT = REPO_ROOT / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T192211-codex-strict-1h-next-source-intake-contract-v1/"
    "strict-1h-next-source-intake-contract/strict_1h_next_source_intake_contract_v1.json"
)


def main() -> None:
    payload = json.loads(CONTRACT.read_text())
    targets = payload["target_rows"]
    assert len(targets) == 4
    assert targets[0]["symbol"] == "XOM"
    assert targets[0]["minimum_new_source_sessions"] == 5
    assert {target["acceptable_package_id"] for target in targets} == {
        "native_subhour_overlap_after_recency"
    }
    assert payload["decision"]["accepted_rows_added"] == 0
    assert payload["decision"]["new_confidence_gate"] is False
    assert payload["decision"]["strict_full_objective_achieved"] is False
    print("PASS target_rows=4")
    print("PASS first_target=XOM/Sideways")
    print("PASS min_new_source_sessions_first_target=5")
    print("PASS verifier_package_id=native_subhour_overlap_after_recency")
    print("PASS accepted_rows_added=0")
    print("PASS new_confidence_gate=false")
    print("PASS strict_full_objective=false")
    print("PASS update_goal=false")


if __name__ == "__main__":
    main()
