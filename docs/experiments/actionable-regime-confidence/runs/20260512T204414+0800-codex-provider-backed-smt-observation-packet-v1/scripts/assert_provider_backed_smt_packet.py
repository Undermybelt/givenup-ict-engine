#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "materials" / "smt_provider_observation_packet.json"
FETCH = ROOT / "materials" / "provider_fetch_summary.json"


def main() -> int:
    packet = json.loads(PACKET.read_text())
    fetch = json.loads(FETCH.read_text())
    assert packet["factor_name"] == "smt_relationship_resolver"
    assert packet["promotion_allowed"] is False
    assert packet["trade_usable"] is False
    assert packet["actionable"] is False
    assert packet["quality_gate"]["quality_weight"] == 0.0
    assert packet["quality_gate"]["downstream_allowed"] is False
    assert len(packet["rows"]) >= 4
    assert any(r["base_symbol"] == "NQ" and r["comparison_symbol"] in {"ES", "YM"} for r in packet["rows"])
    assert any(r["base_symbol"] == "EURUSD" and r["comparison_symbol"] in {"GBPUSD", "DXY"} for r in packet["rows"])
    assert any(r["base_symbol"] == "XAUUSD" and r["comparison_symbol"] in {"XAGUSD", "DXY"} for r in packet["rows"])
    assert any(r["base_symbol"] == "BTC" and r["comparison_symbol"] == "ETH" for r in packet["rows"])
    assert any(r["normalized_for_inverse_correlation"] for r in packet["rows"])
    for row in packet["rows"]:
        assert row["actionable"] is False
        assert row["regime_profit_branch_path"].count("->") == 3
        if row["confidence"] > 0:
            assert row["base_level"] is not None
            assert row["comparison_level"] is not None
        else:
            assert row["fail_closed_reason"]
    for stats in packet["per_regime_statistics"].values():
        assert stats["trade_count"] == 0
        assert stats["confidence"] == 0.0
        assert stats["fail_closed_reason"]
    successful = sum(1 for m in fetch if m.get("returned_rows", 0) > 0)
    print(json.dumps({
        "provider_backed_smt_assertion": "pass",
        "rows": len(packet["rows"]),
        "successful_provider_symbols": successful,
        "smt_signal_counts": {s: sum(1 for r in packet["rows"] if r["smt_signal"] == s) for s in ["bullish_smt", "bearish_smt", "none"]},
        "downstream_allowed": packet["quality_gate"]["downstream_allowed"]
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
