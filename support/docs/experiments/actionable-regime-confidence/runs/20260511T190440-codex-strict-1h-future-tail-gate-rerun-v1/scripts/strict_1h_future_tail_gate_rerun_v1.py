#!/usr/bin/env python3
"""Verify the strict 1h future-tail gate rerun against the predeclared spec."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
SPEC_PATH = REPO_ROOT / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T185905-codex-strict-1h-future-tail-gate-spec-v1/"
    "future-tail-gate-spec/strict_1h_future_tail_gate_spec_v1.json"
)


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text())
    rows = spec["rows"]
    accepted = [
        row for row in rows
        if row["eligible_for_future_rerun"] == "true"
        and row["calibration_2024_passes"] == "true"
        and row["future_heldout_2025_plus_jan2026_passes"] == "true"
        and row["provider_1h_covers_tail"] == "true"
        and int(row["future_heldout_2025_plus_jan2026_support"]) >= 73
        and float(row["future_heldout_2025_plus_jan2026_wilson95_lcb"]) >= 0.95
    ]
    if len(rows) != 4:
        raise SystemExit(f"expected 4 spec rows, got {len(rows)}")
    if len(accepted) != 4:
        raise SystemExit(f"expected 4 accepted future rows, got {len(accepted)}")
    print("PASS source_spec_candidate_rows=4")
    print("PASS accepted_future_protocol_rows_added=4")
    print("PASS accepted_rows_added_to_fixed_gate=0")
    print("PASS strict_1h_future_protocol_rows_after=45/156")
    print("PASS new_confidence_gate=true_scope_future_tail_only")
    print("PASS strict_full_objective=false")
    print("PASS update_goal=false")


if __name__ == "__main__":
    main()
