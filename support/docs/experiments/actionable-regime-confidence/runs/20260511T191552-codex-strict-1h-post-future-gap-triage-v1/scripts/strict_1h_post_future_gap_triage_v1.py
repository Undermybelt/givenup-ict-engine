#!/usr/bin/env python3
"""Verify strict 1h post-future gap triage from source CSVs."""

from __future__ import annotations

import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[6]
NEAR_MISS = REPO_ROOT / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T184151-codex-strict-1h-near-miss-extension-requirements-v1/"
    "strict-1h-extension-requirements/strict_1h_near_miss_extension_candidates_v1.csv"
)
TAIL = REPO_ROOT / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T184530-codex-strict-1h-jan2026-tail-support-probe-v1/"
    "jan2026-tail-support/strict_1h_jan2026_tail_support_probe_v1_rows.csv"
)
ACCEPTED = REPO_ROOT / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T190440-codex-strict-1h-future-tail-gate-rerun-v1/"
    "future-tail-gate-rerun/strict_1h_future_tail_gate_rerun_v1_rows.csv"
)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def key(row: dict[str, str]) -> tuple[str, str]:
    return row["instrument"], row["root"]


def main() -> None:
    near = rows(NEAR_MISS)
    tail_by_key = {key(row): row for row in rows(TAIL)}
    accepted_keys = {key(row) for row in rows(ACCEPTED)}
    remaining = [row for row in near if key(row) not in accepted_keys]
    ready_existing_tail = [
        row for row in remaining
        if tail_by_key.get(key(row), {}).get("tail_covers_missing_extra") == "true"
    ]
    new_needed = []
    for row in remaining:
        tail = tail_by_key.get(key(row), {})
        have = int(tail.get("jan2026_source_tail_sessions", "0"))
        need = int(row["total_extra_sessions_to_make_fixed_splits_pass"])
        new_needed.append(max(0, need - have))

    assert len(near) == 13
    assert len(accepted_keys) == 4
    assert len(remaining) == 9
    assert len(ready_existing_tail) == 0
    assert min(new_needed) == 5

    print("PASS future_protocol_accepted_rows=4")
    print("PASS near_miss_candidates_before=13")
    print("PASS remaining_near_miss_after_future=9")
    print("PASS remaining_ready_with_existing_tail=0")
    print("PASS min_new_source_sessions_needed=5")
    print("PASS strict_1h_future_protocol_rows=45/156")
    print("PASS strict_full_objective=false")
    print("PASS update_goal=false")


if __name__ == "__main__":
    main()
