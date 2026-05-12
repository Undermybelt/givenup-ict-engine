#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "materials/smt_provider_observation_packet.json"
ROWS = ROOT / "materials/smt_provider_observation_rows.csv"

REQUIRED_COVERAGE = {
    "NQ/ES/YM": {("NQ", "ES"), ("NQ", "YM")},
    "EURUSD/GBPUSD/DXY": {("EURUSD", "GBPUSD"), ("EURUSD", "DXY")},
    "XAUUSD/XAGUSD/DXY": {("XAUUSD", "XAGUSD"), ("XAUUSD", "DXY")},
    "BTC/ETH": {("BTC", "ETH")},
}

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
    "recent_correlation",
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
    "regime_bucket",
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
    readbacks = packet["provider_readbacks"]
    quality = packet["quality_gate"]

    assert_true(packet["promotion_allowed"] is False, "promotion must remain blocked")
    assert_true(packet["trade_usable"] is False, "trade usability must remain blocked")
    assert_true(packet["actionable"] is False, "packet must not be actionable")
    assert_true(quality["quality_weight"] == 0.0, "quality weight must be zero without outcomes")
    assert_true(quality["downstream_allowed"] is False, "downstream must remain blocked")
    assert_true("no_mss_cisd_displacement_pda" in quality["fail_closed_reason"], "missing downstream fail-closed reason")

    observed_pairs = {(item["base_symbol"], item["comparison_symbol"]) for item in readbacks}
    for family, pairs in REQUIRED_COVERAGE.items():
        assert_true(pairs.issubset(observed_pairs), f"missing provider pairs for {family}: {sorted(pairs - observed_pairs)}")

    assert_true(len(readbacks) == 7, "expected seven provider pair readbacks")
    assert_true(all(item["provider_data_acquired"] for item in readbacks), "all provider lanes must have acquired data")
    assert_true(all(item["aligned_rows"] >= 40 for item in readbacks), "all provider lanes need aligned rows")
    assert_true(len(rows) > 0, "expected provider observation rows")

    csv_rows = list(csv.DictReader(ROWS.open(newline="")))
    assert_true(len(csv_rows) == len(rows), "CSV row count differs from JSON row count")

    for row in rows:
        missing = REQUIRED_ROW_FIELDS - set(row)
        assert_true(not missing, f"row missing required fields: {sorted(missing)}")
        assert_true(row["confirmation_role"] == "confirmation_only", "SMT row must be confirmation-only")
        assert_true(row["actionable"] is False, "SMT row must not be actionable")
        assert_true(row["timeframe_aligned"] is True, "timeframe must align")
        assert_true(row["session_overlap"] is True, "session must overlap")
        if row["smt_signal"] != "none":
            assert_true(row["same_event_window_confirmed"] is True, "SMT event must be same-window")
            assert_true(row["base_level"] is not None, "signal missing base_level")
            assert_true(row["comparison_level"] is not None, "signal missing comparison_level")
        else:
            assert_true(row["fail_closed_reason"], "fail-closed row must explain why no SMT signal emitted")
        assert_true(row["mss_or_cisd_confirmed"] is False, "MSS/CISD must not be invented")
        assert_true(row["displacement_confirmed"] is False, "displacement must not be invented")
        if row["relationship_type"] == "negative":
            assert_true(row["normalized_for_inverse_correlation"] is True, "negative rows must be normalized")
            if row["smt_signal"] != "none":
                assert_true(row["raw_comparison_swing_type"] is not None, "negative rows must preserve raw comparison swing")
        else:
            assert_true(row["normalized_for_inverse_correlation"] is False, "positive rows must not be inverse-normalized")

    for regime in ["trend", "range", "transition", "stress", "other"]:
        stats = packet["per_regime_statistics"][regime]
        assert_true(stats["trade_count"] == 0, f"{regime} trade count must be zero")
        assert_true(stats["win_rate"] is None, f"{regime} win rate must be null")
        assert_true(stats["expectancy"] is None, f"{regime} expectancy must be null")
        assert_true(stats["confidence"] == 0.0, f"{regime} confidence must remain zero")

    print(
        json.dumps(
            {
                "packet_assertion": "pass",
                "provider_pairs": len(readbacks),
                "rows": len(rows),
                "smt_event_count": sum(item["smt_event_count"] for item in readbacks),
                "downstream_allowed": quality["downstream_allowed"],
                "quality_weight": quality["quality_weight"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
