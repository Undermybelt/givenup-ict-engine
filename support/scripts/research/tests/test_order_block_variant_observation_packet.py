from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import order_block_variant_observation_packet as packet_builder  # noqa: E402


class OrderBlockVariantObservationPacketTests(unittest.TestCase):
    def test_classifies_bullish_order_block_breaker_from_candles(self) -> None:
        candles = [
            {"timestamp": "2026-05-01T08:00:00Z", "open": 100.0, "high": 101.0, "low": 99.5, "close": 100.5},
            {"timestamp": "2026-05-01T08:05:00Z", "open": 100.5, "high": 100.7, "low": 99.8, "close": 100.0},
            {"timestamp": "2026-05-01T08:10:00Z", "open": 100.0, "high": 102.0, "low": 99.9, "close": 101.5},
            {"timestamp": "2026-05-01T08:15:00Z", "open": 101.5, "high": 101.7, "low": 99.7, "close": 99.7},
        ]

        variant = packet_builder.classify_latest_order_block_variant(candles)

        self.assertEqual(variant["variant"], "breaker_block")
        self.assertEqual(variant["direction"], "bull")
        self.assertEqual(variant["high"], 100.7)
        self.assertEqual(variant["low"], 99.8)
        self.assertEqual(variant["midpoint"], 100.25)
        self.assertEqual(variant["validation_state"], "breaker_confirmed")
        self.assertTrue(variant["breaker_confirmed"])

    def test_build_packet_prefers_analyze_runtime_evidence_and_fails_closed(self) -> None:
        analyze_payload = {
            "report": {
                "symbol": "QQQ",
                "price_action": {
                    "order_block_variant": {
                        "factor_name": "order_block_variant_classifier",
                        "variant": "rejection_block",
                        "direction": "Bear",
                        "high": 429.5,
                        "low": 426.0,
                        "midpoint": 427.75,
                        "validation_state": "rejection_confirmed",
                        "mitigation_count": 2,
                        "breaker_confirmed": False,
                        "rejection_confirmed": True,
                        "confidence": 0.72,
                        "fail_closed_reason": None,
                    }
                },
                "trade_plan": {
                    "direction": "Bear",
                    "entry": 427.0,
                    "stop_loss": 430.0,
                    "take_profits": [424.0],
                },
                "multi_timeframe": {"entry_model_packets": {"sample": {"session_label": "new_york_am"}}},
            }
        }
        execution_candidate_payload = {
            "pre_bayes_evidence_filter": {
                "raw_market_regime_label": "range",
                "evidence_assignments": {"market_state_primary_regime": "RangeConsolidation"},
            }
        }
        candles = [
            {"timestamp": "2026-05-01T08:00:00Z", "open": 100.0, "high": 101.0, "low": 99.5, "close": 100.5},
            {"timestamp": "2026-05-01T08:05:00Z", "open": 100.5, "high": 100.7, "low": 99.8, "close": 100.0},
            {"timestamp": "2026-05-01T08:10:00Z", "open": 100.0, "high": 102.0, "low": 99.9, "close": 101.5},
        ]

        packet = packet_builder.build_observation_packet(
            analyze_payload=analyze_payload,
            execution_candidate_payload=execution_candidate_payload,
            candles=candles,
            provider="yfinance",
            timeframe="5m",
        )

        row = packet["rows"][0]
        self.assertEqual(packet["factor_name"], "order_block_variant_classifier")
        self.assertEqual(packet["branch_path_contract"]["main_regime"], "Range")
        self.assertEqual(row["variant"], "rejection_block")
        self.assertEqual(row["direction"], "bear")
        self.assertEqual(row["high"], 429.5)
        self.assertEqual(row["low"], 426.0)
        self.assertFalse(row["actionable"])
        self.assertEqual(packet["per_regime_statistics"]["range"]["trade_count"], 1)
        self.assertIn("single_observation_only_not_promotable", packet["quality_gate"]["fail_closed_reason"])
        self.assertEqual(
            packet["field_mapping"]["execution_tree_features"],
            [
                "high",
                "low",
                "midpoint",
                "validation_state",
                "mitigation_count",
                "breaker_confirmed",
                "rejection_confirmed",
            ],
        )

    def test_cli_writes_packet_and_csv(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            analyze_json = tmp / "analyze.json"
            execution_json = tmp / "execution.json"
            candles_json = tmp / "candles.json"
            output_json = tmp / "packet.json"
            output_csv = tmp / "packet.csv"
            analyze_json.write_text(
                json.dumps(
                    {
                        "report": {
                            "symbol": "BTC",
                            "price_action": {},
                            "trade_plan": {
                                "direction": "Bull",
                                "entry": 100.0,
                                "stop_loss": 99.0,
                                "take_profits": [101.0],
                            },
                            "multi_timeframe": {"entry_model_packets": {"sample": {"session_label": "crypto"}}},
                        }
                    }
                ),
                encoding="utf-8",
            )
            execution_json.write_text(
                json.dumps({"pre_bayes_evidence_filter": {"raw_market_regime_label": "transition", "evidence_assignments": {}}}),
                encoding="utf-8",
            )
            candles_json.write_text(
                json.dumps(
                    [
                        {"timestamp": "2026-05-01T08:00:00Z", "open": 100.0, "high": 101.0, "low": 99.5, "close": 100.5},
                        {"timestamp": "2026-05-01T08:05:00Z", "open": 100.5, "high": 100.7, "low": 99.8, "close": 100.0},
                        {"timestamp": "2026-05-01T08:10:00Z", "open": 100.0, "high": 102.0, "low": 99.9, "close": 101.5},
                    ]
                ),
                encoding="utf-8",
            )

            exit_code = packet_builder.main(
                [
                    "--analyze-json",
                    str(analyze_json),
                    "--execution-candidate-json",
                    str(execution_json),
                    "--candles-json",
                    str(candles_json),
                    "--provider",
                    "kraken",
                    "--timeframe",
                    "5m",
                    "--output-json",
                    str(output_json),
                    "--output-csv",
                    str(output_csv),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(output_json.read_text(encoding="utf-8"))["factor_name"], "order_block_variant_classifier")
            self.assertTrue(output_csv.exists())


if __name__ == "__main__":
    unittest.main()
