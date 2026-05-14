#!/usr/bin/env python3
import csv
import json
from pathlib import Path

RUN_ROOT = Path(__file__).resolve().parents[1]
PACKET = RUN_ROOT / "materials/smt_training_matrix_readiness_packet.json"
ROWS = RUN_ROOT / "summaries/smt_training_matrix_rows.csv"

REQUIRED_FIELDS = {
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
    "raw_comparison_swing_type",
    "raw_comparison_level",
    "near_pd_array",
    "pd_array_type",
    "mss_or_cisd_confirmed",
    "displacement_confirmed",
    "training_row_eligible",
    "training_blockers",
}


def truthy(value):
    return str(value).strip().lower() in {"true", "1", "yes"}


def main():
    packet = json.loads(PACKET.read_text())
    rows = list(csv.DictReader(ROWS.open()))
    missing = REQUIRED_FIELDS - set(rows[0])
    if missing:
        raise AssertionError(f"missing required fields: {sorted(missing)}")

    if any(truthy(row["actionable"]) for row in rows):
        raise AssertionError("SMT training rows must not be standalone actionable")
    if any(row["confirmation_role"] != "confirmation_only" for row in rows):
        raise AssertionError("SMT rows must remain confirmation_only")
    if any(not row["base_level"] or not row["comparison_level"] for row in rows):
        raise AssertionError("every row must carry base_level and comparison_level")

    inverse_rows = [row for row in rows if truthy(row["normalized_for_inverse_correlation"])]
    if not inverse_rows:
        raise AssertionError("expected inverse-normalized rows for negative relationship lanes")
    if any(not row["raw_comparison_swing_type"] or not row["raw_comparison_level"] for row in inverse_rows):
        raise AssertionError("inverse-normalized rows must preserve raw comparison structure")

    for pair in ["NQ/ES", "NQ/YM", "EURUSD/GBPUSD", "EURUSD/DXY", "XAUUSD/XAGUSD", "XAUUSD/DXY", "BTC/ETH"]:
        if pair not in packet["required_pair_summary"]:
            raise AssertionError(f"missing required pair summary: {pair}")
    for regime in ["trend", "range", "transition", "stress", "other"]:
        if regime not in packet["per_regime_statistics"]:
            raise AssertionError(f"missing regime summary: {regime}")

    if packet["quality_gate"]["downstream_allowed"]:
        raise AssertionError("current SMT matrix should fail closed until pair and per-regime floors are met")

    print(json.dumps({
        "packet_assertion": "pass",
        "rows": len(rows),
        "training_row_eligible": packet["counts"]["training_row_eligible"],
        "inverse_normalized_rows": packet["counts"]["inverse_normalized_rows"],
        "downstream_allowed": packet["quality_gate"]["downstream_allowed"],
        "fail_closed_reason": packet["quality_gate"]["fail_closed_reason"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
