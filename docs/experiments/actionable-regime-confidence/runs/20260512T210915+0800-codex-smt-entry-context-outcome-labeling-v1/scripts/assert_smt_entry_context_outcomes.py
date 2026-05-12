#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "materials/smt_entry_context_outcome_packet.json"
ROWS = ROOT / "materials/smt_entry_context_outcome_rows.csv"

REQUIRED_FIELDS = {
    "base_symbol",
    "comparison_symbol",
    "relationship_type",
    "timeframe",
    "session",
    "smt_signal",
    "base_level",
    "comparison_level",
    "swept_side",
    "normalized_for_inverse_correlation",
    "raw_comparison_swing_type",
    "mss_or_cisd_confirmed",
    "displacement_confirmed",
    "near_pd_array",
    "pd_array_type",
    "forward_return",
    "outcome_hit",
    "entry_context_complete",
    "branch_path",
    "confirmation_role",
    "actionable",
}


def assert_true(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    packet = json.loads(PACKET.read_text())
    rows = packet["rows"]
    stats = packet["per_regime_statistics"]
    gate = packet["quality_gate"]
    csv_rows = list(csv.DictReader(ROWS.open(newline="")))

    assert_true(packet["promotion_allowed"] is False, "promotion must remain blocked")
    assert_true(packet["trade_usable"] is False, "trade usable must remain blocked")
    assert_true(packet["actionable"] is False, "packet must not be actionable")
    assert_true(gate["quality_weight"] == 0.0, "quality must remain zero until support passes")
    assert_true(gate["downstream_allowed"] is False, "downstream must remain blocked")
    assert_true(len(rows) == len(csv_rows), "CSV and JSON row count mismatch")
    assert_true(len(rows) > 0, "expected labeled SMT rows")

    for row in rows:
        missing = REQUIRED_FIELDS - set(row)
        assert_true(not missing, f"row missing required fields: {sorted(missing)}")
        assert_true(row["confirmation_role"] == "confirmation_only", "SMT must remain confirmation-only")
        assert_true(row["actionable"] is False, "SMT row must not be actionable")
        if row["smt_signal"] != "none":
            assert_true(row["base_level"] is not None, "signal row missing base_level")
            assert_true(row["comparison_level"] is not None, "signal row missing comparison_level")
            assert_true(row["forward_return"] is not None, "signal row missing forward outcome")
            assert_true(row["outcome_hit"] is not None, "signal row missing outcome hit")
        if row["entry_context_complete"]:
            assert_true(row["mss_or_cisd_confirmed"] is True, "complete row missing MSS/CISD")
            assert_true(row["displacement_confirmed"] is True, "complete row missing displacement")
            assert_true(row["near_pd_array"] is True, "complete row missing PDA")

    for regime in ["trend", "range", "transition", "stress", "other"]:
        assert_true(regime in stats, f"missing regime stats for {regime}")
        item = stats[regime]
        assert_true("trade_count" in item, f"{regime} missing trade_count")
        assert_true("win_rate" in item, f"{regime} missing win_rate")
        assert_true("expectancy" in item, f"{regime} missing expectancy")
        assert_true("confidence" in item, f"{regime} missing confidence")

    print(json.dumps({
        "packet_assertion": "pass",
        "rows": len(rows),
        "entry_context_trade_count": sum(item["trade_count"] for item in stats.values()),
        "downstream_allowed": gate["downstream_allowed"],
        "quality_weight": gate["quality_weight"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
