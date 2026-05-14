#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "materials" / "smt_relationship_resolver_sample_packet.json"
CSV_ROWS = ROOT / "materials" / "smt_relationship_resolver_rows.csv"
MAPPING = ROOT / "mappings" / "smt_relationship_resolver_field_mapping.json"
FACTOR = ROOT / "scripts" / "smt_relationship_resolver_factor.py"
FIXTURES = ROOT / "fixtures"


REQUIRED_ROW_FIELDS = {
    "base_symbol",
    "comparison_symbol",
    "relationship_type",
    "relationship_confidence",
    "timeframe",
    "session",
    "comparison_timeframe",
    "comparison_session",
    "timeframe_aligned",
    "session_overlap",
    "correlation_window_bars",
    "recent_correlation",
    "smt_signal",
    "base_swing_type",
    "base_event_time",
    "base_level",
    "comparison_swing_type",
    "comparison_event_time",
    "comparison_level",
    "event_window_bars",
    "event_time_delta_bars",
    "same_event_window_confirmed",
    "swept_side",
    "normalized_for_inverse_correlation",
    "raw_comparison_swing_type",
    "raw_comparison_level",
    "near_pd_array",
    "pd_array_type",
    "mss_or_cisd_confirmed",
    "displacement_confirmed",
    "provider_provenance",
    "evidence_source",
    "confidence",
    "fail_closed_reason",
    "confirmation_role",
    "actionable",
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    packet = json.loads(PACKET.read_text())
    mapping = json.loads(MAPPING.read_text())
    assert_true(packet["factor_name"] == "smt_relationship_resolver", "wrong factor_name")
    assert_true(packet["promotion_allowed"] is False, "promotion must stay false")
    assert_true(packet["trade_usable"] is False, "trade_usable must stay false")
    assert_true(packet["actionable"] is False, "SMT cannot be standalone actionable")
    assert_true(packet["quality_gate"]["quality_weight"] == 0.0, "preflight quality weight must be zero")
    assert_true(packet["quality_gate"]["downstream_allowed"] is False, "downstream must be blocked")
    assert_true(" -> " in packet["branch_path_contract"]["regime_profit_branch_path"], "branch path missing rooted delimiter")
    assert_true(len(packet["coverage_target"]) >= 4, "coverage target too small")
    for regime in ["trend", "range", "transition", "stress", "other"]:
        stats = packet["per_regime_statistics"][regime]
        assert_true(stats["trade_count"] == 0, f"{regime} trade_count must be zero in preflight")
        assert_true(stats["confidence"] == 0.0, f"{regime} confidence must be zero in preflight")
    for row in packet["rows"]:
        missing = REQUIRED_ROW_FIELDS - set(row)
        assert_true(not missing, f"row missing fields: {sorted(missing)}")
        assert_true(row["actionable"] is False, "row actionable must be false")
        assert_true(row["confirmation_role"] == "confirmation_only", "SMT row must be confirmation-only")
        assert_true(row["confidence"] == 0.0, "sample rows must fail closed with confidence 0")
        assert_true(row["fail_closed_reason"], "fail_closed_reason required")
        assert_true("base_level" in row and "comparison_level" in row, "price levels are required fields")
        assert_true(row["same_event_window_confirmed"] is False, "preflight rows cannot claim event alignment")
        if row["relationship_type"] == "negative":
            assert_true(row["normalized_for_inverse_correlation"] is True, "negative relation must normalize")
    with CSV_ROWS.open(newline="") as f:
        csv_rows = list(csv.DictReader(f))
    assert_true(len(csv_rows) == len(packet["rows"]), "CSV row count must match JSON packet")
    for surface in ["Structure", "Technicals", "SMT", "Regime posterior evidence", "Execution tree features", "Feedback/update learning fields"]:
        assert_true(surface in mapping["runtime_surface_mapping"], f"missing mapping surface {surface}")
    assert_true(FACTOR.exists(), "independent factor/training file missing")
    case_expectations = {
        "smt_bullish_positive_input.json": ("bullish_smt", False),
        "smt_bearish_negative_input.json": ("bearish_smt", True),
        "smt_timeframe_mismatch_input.json": ("none", False),
        "smt_session_mismatch_input.json": ("none", False),
    }
    executable_cases = {}
    for fixture_name, (expected_signal, expected_normalized) in case_expectations.items():
        fixture = FIXTURES / fixture_name
        assert_true(fixture.exists(), f"missing executable fixture {fixture_name}")
        output = subprocess.check_output([sys.executable, str(FACTOR), "--input", str(fixture), "--output", "-"], text=True)
        result = json.loads(output)
        rows = result["rows"]
        assert_true(rows, f"{fixture_name} produced no rows")
        row = rows[0]
        executable_cases[fixture_name] = {
            "smt_signal": row["smt_signal"],
            "fail_closed_reason": row["fail_closed_reason"],
            "base_level": row["base_level"],
            "comparison_level": row["comparison_level"],
            "normalized_for_inverse_correlation": row["normalized_for_inverse_correlation"],
            "raw_comparison_swing_type": row.get("raw_comparison_swing_type"),
            "confirmation_role": row.get("confirmation_role"),
            "same_event_window_confirmed": row.get("same_event_window_confirmed"),
        }
        assert_true(row["smt_signal"] == expected_signal, f"{fixture_name} wrong smt_signal")
        assert_true(row["actionable"] is False, f"{fixture_name} must remain confirmation-only")
        assert_true(row["confirmation_role"] == "confirmation_only", f"{fixture_name} must declare confirmation-only role")
        assert_true(row["normalized_for_inverse_correlation"] is expected_normalized, f"{fixture_name} normalization mismatch")
        if expected_signal != "none":
            assert_true(row["base_level"] is not None, f"{fixture_name} signal missing base_level")
            assert_true(row["comparison_level"] is not None, f"{fixture_name} signal missing comparison_level")
            assert_true(row["same_event_window_confirmed"] is True, f"{fixture_name} did not confirm same event window")
            assert_true(row["confidence"] > 0.0, f"{fixture_name} signal missing confidence")
        else:
            assert_true(row["confidence"] == 0.0, f"{fixture_name} fail-closed row must have zero confidence")
    print(
        json.dumps(
            {
                "packet_assertion": "pass",
                "rows": len(packet["rows"]),
                "coverage_target": packet["coverage_target"],
                "quality_weight": packet["quality_gate"]["quality_weight"],
                "downstream_allowed": packet["quality_gate"]["downstream_allowed"],
                "executable_cases": executable_cases,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"assert_smt_packet_failed: {exc}", file=sys.stderr)
        raise
