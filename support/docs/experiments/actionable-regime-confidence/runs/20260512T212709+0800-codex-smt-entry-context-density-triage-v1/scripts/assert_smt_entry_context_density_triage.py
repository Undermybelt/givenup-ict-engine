#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "materials/smt_entry_context_density_triage_packet.json"
SUMMARY = ROOT / "summaries/smt_entry_context_density_triage_summary.csv"


def assert_true(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    packet = json.loads(PACKET.read_text())
    rows = list(csv.DictReader(SUMMARY.open(newline="")))
    gate = packet["quality_gate"]
    strict = packet["scenarios"]["strict_mss_displacement_pda"]["aggregate"]

    assert_true(gate["downstream_allowed"] is False, "triage must not unlock downstream")
    assert_true(gate["promotion_allowed"] is False, "triage must not unlock promotion")
    assert_true(gate["trade_usable"] is False, "triage must not be trade usable")
    assert_true(gate["quality_weight"] == 0.0, "triage quality weight must remain zero")
    assert_true(strict["trade_count"] == gate["strict_trade_count"], "strict count mismatch")
    assert_true(gate["strict_trade_count"] < gate["min_trade_count_for_learning"], "strict count unexpectedly passes floor")
    assert_true(packet["blocker_counts"]["signal_rows"] > 0, "expected SMT signal rows")
    assert_true(packet["blocker_counts"]["displacement_true"] < packet["blocker_counts"]["signal_rows"], "displacement should be identified as a bottleneck")
    assert_true(len(rows) == 42, "expected seven scenarios times six regime buckets")

    print(json.dumps({
        "packet_assertion": "pass",
        "strict_trade_count": gate["strict_trade_count"],
        "min_trade_count_for_learning": gate["min_trade_count_for_learning"],
        "best_relaxed_scenario": packet["best_relaxed_scenario"]["scenario"],
        "best_relaxed_trade_count": packet["best_relaxed_scenario"]["trade_count"],
        "downstream_allowed": gate["downstream_allowed"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
