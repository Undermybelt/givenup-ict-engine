#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "materials" / "smt_confirmation_failure_packet.json"
CSV_ROWS = ROOT / "materials" / "smt_confirmation_failure_rows.csv"
MAPPING = ROOT / "mappings" / "smt_confirmation_failure_field_mapping.json"


REQUIRED_ROW_FIELDS = {
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
    "actionable",
    "raw_comparison_swing_type",
    "raw_comparison_level",
}


def assert_true(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    packet = json.loads(PACKET.read_text())
    mapping = json.loads(MAPPING.read_text())
    assert_true(packet["factor_name"] == "smt_confirmation_failure_v1", "wrong factor")
    assert_true(packet["actionable"] is False, "SMT must not be standalone actionable")
    assert_true(packet["trade_usable"] is False, "fixture material must not be trade usable")
    assert_true(packet["promotion_allowed"] is False, "fixture material must not be promotable")
    assert_true(packet["quality_gate"]["downstream_allowed"] is False, "downstream must fail closed")
    assert_true(set(packet["per_regime_statistics"]) == {"trend", "range", "transition", "stress", "other"}, "missing regime stats")

    rows = packet["rows"]
    assert_true(rows, "missing rows")
    seen_pairs = {(row["base_symbol"], row["comparison_symbol"]) for row in rows}
    for required in [("NQ", "ES"), ("NQ", "YM"), ("EURUSD", "GBPUSD"), ("EURUSD", "DXY"), ("XAUUSD", "XAGUSD"), ("XAUUSD", "DXY"), ("BTC", "ETH")]:
        assert_true(required in seen_pairs, f"missing required pair {required}")
    for row in rows:
        assert_true(REQUIRED_ROW_FIELDS.issubset(row), f"row missing fields: {row}")
        assert_true(row["actionable"] is False, "row actionable must be false")
        if row["relationship_type"] == "negative":
            assert_true(row["normalized_for_inverse_correlation"] is True, "negative relationship must be normalized")
            assert_true(row["raw_comparison_swing_type"] is not None or row["fail_closed_reason"], "negative row needs raw comparison event")
        if row["smt_signal"] != "none":
            assert_true(row["base_level"] is not None, "signal missing base_level")
            assert_true(row["comparison_level"] is not None, "signal missing comparison_level")
            assert_true(row["swept_side"] in {"buy_side_liquidity", "sell_side_liquidity"}, "signal missing swept side")
            assert_true(row["fail_closed_reason"] is not None, "signal must remain confirmation-only without full entry model")

    with CSV_ROWS.open() as handle:
        csv_rows = list(csv.DictReader(handle))
    assert_true(len(csv_rows) == len(rows), "csv/json row mismatch")

    for surface in ["Structure", "Technicals", "SMT", "Regime posterior evidence", "Execution tree features", "Feedback/update learning fields"]:
        assert_true(surface in mapping["ict_engine_surface_mapping"], f"missing mapping {surface}")
    assert_true(mapping["gates"]["smt_confirmation_only"] is True, "mapping must lock confirmation-only")
    assert_true(mapping["gates"]["standalone_actionable_allowed"] is False, "standalone actionable must be blocked")

    print(
        json.dumps(
            {
                "packet_assertion": "pass",
                "rows": len(rows),
                "signals": sum(1 for row in rows if row["smt_signal"] != "none"),
                "negative_normalized_rows": sum(1 for row in rows if row["relationship_type"] == "negative" and row["normalized_for_inverse_correlation"]),
                "quality_weight": packet["quality_gate"]["quality_weight"],
                "downstream_allowed": packet["quality_gate"]["downstream_allowed"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"assert_smt_confirmation_packet_failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
