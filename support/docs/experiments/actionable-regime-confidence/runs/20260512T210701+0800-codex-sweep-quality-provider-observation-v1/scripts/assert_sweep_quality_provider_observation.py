#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "materials/sweep_quality_provider_observation_packet.json"
ROWS = ROOT / "materials/sweep_quality_provider_observation_rows.csv"

REQUIRED_FIELDS = {
    "symbol",
    "timeframe",
    "session",
    "event_time",
    "sweep_type",
    "direction",
    "swept_side",
    "sweep_level",
    "reclaim_level",
    "invalidation_level",
    "continuation_trigger_level",
    "wick_body_ratio",
    "reclaim_speed_bars",
    "continuation_confirmed",
    "reversal_confirmed",
    "near_pd_array",
    "pd_array_type",
    "mss_or_cisd_confirmed",
    "displacement_confirmed",
    "regime_bucket",
    "provider_provenance",
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
    assert_true(packet["promotion_allowed"] is False, "promotion must remain blocked")
    assert_true(packet["trade_usable"] is False, "trade usable must remain blocked")
    assert_true(packet["actionable"] is False, "packet cannot be actionable")
    assert_true(packet["quality_gate"]["quality_weight"] == 0.0, "quality weight must be zero")
    assert_true(packet["quality_gate"]["downstream_allowed"] is False, "downstream must be blocked")
    assert_true(len(packet["provider_summary"]) >= 8, "provider summary coverage too small")
    assert_true(len(rows) > 0, "expected sweep observation rows")
    csv_rows = list(csv.DictReader(ROWS.open(newline="")))
    assert_true(len(csv_rows) == len(rows), "CSV row count mismatch")
    for row in rows:
        missing = REQUIRED_FIELDS - set(row)
        assert_true(not missing, f"row missing required fields: {sorted(missing)}")
        assert_true(row["sweep_type"] == "true_sweep", "provider row should be true_sweep")
        assert_true(row["sweep_level"] is not None, "missing sweep_level")
        assert_true(row["reclaim_level"] is not None, "missing reclaim_level")
        assert_true(row["invalidation_level"] is not None, "missing invalidation_level")
        assert_true(row["continuation_trigger_level"] is not None, "missing continuation_trigger_level")
        assert_true(row["confirmation_role"] == "confirmation_only", "row must be confirmation-only")
        assert_true(row["actionable"] is False, "row cannot be actionable")
        assert_true(row["mss_or_cisd_confirmed"] is False, "MSS/CISD cannot be invented")
        assert_true(row["displacement_confirmed"] is False, "displacement cannot be invented")
    for regime in ["trend", "range", "transition", "stress", "other"]:
        stats = packet["per_regime_statistics"][regime]
        assert_true(stats["trade_count"] == 0, f"{regime} trade count must be zero")
        assert_true(stats["win_rate"] is None, f"{regime} win rate must be null")
        assert_true(stats["expectancy"] is None, f"{regime} expectancy must be null")
        assert_true(stats["confidence"] == 0.0, f"{regime} confidence must be zero")
    print(
        json.dumps(
            {
                "packet_assertion": "pass",
                "provider_files": len(packet["provider_summary"]),
                "rows": len(rows),
                "downstream_allowed": packet["quality_gate"]["downstream_allowed"],
                "quality_weight": packet["quality_gate"]["quality_weight"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
