#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "materials/smt_provider_observation_packet.json"
CSV_ROWS = ROOT / "materials/smt_provider_observation_rows.csv"
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
    "near_pd_array",
    "pd_array_type",
    "mss_or_cisd_confirmed",
    "displacement_confirmed",
    "confidence",
    "fail_closed_reason",
    "confirmation_role",
    "actionable",
}


def assert_true(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def main() -> int:
    packet = json.loads(PACKET.read_text())
    rows = packet["rows"]
    assert_true(packet.get("actionable") is False, "packet cannot be actionable")
    assert_true(packet.get("trade_usable") is False, "packet cannot be trade usable")
    assert_true(packet.get("promotion_allowed") is False, "packet cannot promote")
    if "standalone_actionable_allowed" in packet["quality_gate"]:
        assert_true(packet["quality_gate"]["standalone_actionable_allowed"] is False, "SMT cannot be standalone actionable")
    assert_true(packet["quality_gate"]["downstream_allowed"] is False, "downstream must remain blocked")
    assert_true(packet["quality_gate"]["quality_weight"] == 0.0, "quality weight must stay zero without outcomes")
    if "provider_request_readback" in packet:
        assert_true(packet["provider_request_readback"]["fetch_performed"] is False, "unexpected fetch in local-artifact packet")
        assert_true(packet["provider_request_readback"]["aligned_rows"] > 0, "BTC/ETH aligned provider rows missing")
    else:
        readbacks = packet["provider_readbacks"]
        assert_true(len(readbacks) >= 7, "required provider pair readbacks missing")
        assert_true(any(item["base_symbol"] == "NQ" and item["comparison_symbol"] == "ES" for item in readbacks), "NQ/ES readback missing")
        assert_true(any(item["base_symbol"] == "NQ" and item["comparison_symbol"] == "YM" for item in readbacks), "NQ/YM readback missing")
        assert_true(any(item["base_symbol"] == "EURUSD" and item["comparison_symbol"] == "GBPUSD" for item in readbacks), "EURUSD/GBPUSD readback missing")
        assert_true(any(item["base_symbol"] == "EURUSD" and item["comparison_symbol"] == "DXY" for item in readbacks), "EURUSD/DXY readback missing")
        assert_true(any(item["base_symbol"] == "XAUUSD" and item["comparison_symbol"] == "XAGUSD" for item in readbacks), "XAUUSD/XAGUSD readback missing")
        assert_true(any(item["base_symbol"] == "XAUUSD" and item["comparison_symbol"] == "DXY" for item in readbacks), "XAUUSD/DXY readback missing")
        assert_true(any(item["base_symbol"] == "BTC" and item["comparison_symbol"] == "ETH" for item in readbacks), "BTC/ETH readback missing")
    for regime in ["trend", "range", "transition", "stress", "other"]:
        stats = packet["per_regime_statistics"][regime]
        assert_true(stats["trade_count"] == 0, f"{regime} trade_count must fail closed")
        assert_true(stats["confidence"] == 0.0, f"{regime} confidence must fail closed")
    signals = [row for row in rows if row["smt_signal"] != "none"]
    for row in rows:
        missing = REQUIRED_FIELDS - set(row)
        assert_true(not missing, f"row missing required fields: {sorted(missing)}")
        assert_true(row["actionable"] is False, "SMT row cannot be actionable")
        assert_true(row["confirmation_role"] == "confirmation_only", "row must be confirmation-only")
        assert_true(row["fail_closed_reason"], "row missing fail_closed_reason")
        if row["smt_signal"] != "none":
            assert_true(row["base_level"] is not None, "signal missing base_level")
            assert_true(row["comparison_level"] is not None, "signal missing comparison_level")
            assert_true(row["same_event_window_confirmed"] is True, "signal missing same-event confirmation")
            assert_true(row["confidence"] >= 0.0, "signal confidence must be present")
            assert_true(row["mss_or_cisd_confirmed"] is False, "provider observation must not imply MSS/CISD")
            assert_true(row["displacement_confirmed"] is False, "provider observation must not imply displacement")
    with CSV_ROWS.open(newline="") as f:
        csv_rows = list(csv.DictReader(f))
    assert_true(len(csv_rows) == len(rows), "CSV and JSON row counts differ")
    aligned_rows = (
        packet["provider_request_readback"]["aligned_rows"]
        if "provider_request_readback" in packet
        else sum(item["aligned_rows"] for item in packet["provider_readbacks"])
    )
    print(
        json.dumps(
            {
                "packet_assertion": "pass",
                "rows": len(rows),
                "signals": len(signals),
                "aligned_rows": aligned_rows,
                "downstream_allowed": packet["quality_gate"]["downstream_allowed"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
