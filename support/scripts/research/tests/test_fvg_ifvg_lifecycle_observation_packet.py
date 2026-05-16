from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import fvg_ifvg_lifecycle_observation_packet as packet_builder  # noqa: E402


class FvgIfvgLifecycleObservationPacketTests(unittest.TestCase):
    def test_classifies_filled_then_inverted_bullish_fvg(self) -> None:
        candles = [
            {"timestamp": "2026-05-01T08:00:00Z", "open": 100.0, "high": 100.5, "low": 99.8, "close": 100.2},
            {"timestamp": "2026-05-01T08:05:00Z", "open": 100.2, "high": 101.2, "low": 100.1, "close": 101.0},
            {"timestamp": "2026-05-01T08:10:00Z", "open": 102.0, "high": 102.4, "low": 102.0, "close": 102.2},
            {"timestamp": "2026-05-01T08:15:00Z", "open": 102.2, "high": 102.3, "low": 100.4, "close": 100.7},
            {"timestamp": "2026-05-01T08:20:00Z", "open": 100.7, "high": 100.8, "low": 99.4, "close": 99.8},
        ]

        lifecycle = packet_builder.classify_latest_fvg_lifecycle(candles)

        self.assertEqual(lifecycle["fvg_type"], "IFVG")
        self.assertEqual(lifecycle["direction"], "bear")
        self.assertEqual(lifecycle["original_direction"], "bull")
        self.assertEqual(lifecycle["top"], 102.0)
        self.assertEqual(lifecycle["bottom"], 100.5)
        self.assertEqual(lifecycle["fill_ratio"], 1.0)
        self.assertTrue(lifecycle["inverted"])
        self.assertEqual(lifecycle["validation_state"], "inverted")

    def test_build_packet_maps_fields_and_fails_closed_single_observation(self) -> None:
        analyze_payload = {
            "report": {
                "symbol": "SPY",
                "price_action": {
                    "open_fvgs": 1,
                    "nearest_open_fvg_top": 102.0,
                    "nearest_open_fvg_bottom": 100.5,
                },
                "trade_plan": {
                    "direction": "Bear",
                    "entry": 100.0,
                    "stop_loss": 101.0,
                    "take_profits": [99.0],
                },
                "multi_timeframe": {"entry_model_packets": {"sample": {"session_label": "new_york_am"}}},
            }
        }
        execution_candidate_payload = {
            "pre_bayes_evidence_filter": {
                "raw_market_regime_label": "transition",
                "evidence_assignments": {"market_state_primary_regime": "TransitionCompression"},
            }
        }
        candles = [
            {"timestamp": "2026-05-01T08:00:00Z", "open": 100.0, "high": 100.5, "low": 99.8, "close": 100.2},
            {"timestamp": "2026-05-01T08:05:00Z", "open": 100.2, "high": 101.2, "low": 100.1, "close": 101.0},
            {"timestamp": "2026-05-01T08:10:00Z", "open": 102.0, "high": 102.4, "low": 102.0, "close": 102.2},
            {"timestamp": "2026-05-01T08:15:00Z", "open": 102.2, "high": 102.3, "low": 100.4, "close": 100.7},
            {"timestamp": "2026-05-01T08:20:00Z", "open": 100.7, "high": 100.8, "low": 99.4, "close": 99.8},
        ]

        packet = packet_builder.build_observation_packet(
            analyze_payload=analyze_payload,
            execution_candidate_payload=execution_candidate_payload,
            candles=candles,
            provider="yfinance",
            timeframe="5m",
        )

        row = packet["rows"][0]
        self.assertEqual(packet["factor_name"], "fvg_ifvg_lifecycle")
        self.assertEqual(packet["branch_path_contract"]["main_regime"], "Transition")
        self.assertEqual(row["fvg_type"], "IFVG")
        self.assertEqual(row["direction"], "bear")
        self.assertEqual(row["top"], 102.0)
        self.assertEqual(row["bottom"], 100.5)
        self.assertEqual(row["midpoint"], 101.25)
        self.assertEqual(row["fill_ratio"], 1.0)
        self.assertTrue(row["inverted"])
        self.assertFalse(row["actionable"])
        self.assertEqual(packet["per_regime_statistics"]["transition"]["trade_count"], 1)
        self.assertIn("single_observation_only_not_promotable", packet["quality_gate"]["fail_closed_reason"])
        self.assertEqual(
            packet["field_mapping"]["technicals"],
            ["fvg_type", "direction", "top", "bottom", "midpoint", "fill_ratio", "inverted", "respected"],
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
                            "trade_plan": {"direction": "Bull", "entry": 100.0, "stop_loss": 99.0, "take_profits": [101.0]},
                            "multi_timeframe": {"entry_model_packets": {"sample": {"session_label": "crypto"}}},
                        }
                    }
                ),
                encoding="utf-8",
            )
            execution_json.write_text(
                json.dumps({"pre_bayes_evidence_filter": {"raw_market_regime_label": "range", "evidence_assignments": {}}}),
                encoding="utf-8",
            )
            candles_json.write_text(
                json.dumps(
                    [
                        {"timestamp": "2026-05-01T08:00:00Z", "open": 100.0, "high": 100.5, "low": 99.8, "close": 100.2},
                        {"timestamp": "2026-05-01T08:05:00Z", "open": 100.2, "high": 101.2, "low": 100.1, "close": 101.0},
                        {"timestamp": "2026-05-01T08:10:00Z", "open": 102.0, "high": 102.4, "low": 102.0, "close": 102.2},
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
            self.assertEqual(json.loads(output_json.read_text(encoding="utf-8"))["factor_name"], "fvg_ifvg_lifecycle")
            self.assertTrue(output_csv.exists())


if __name__ == "__main__":
    unittest.main()
