from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import liquidity_pool_texture_observation_packet as packet_builder  # noqa: E402


class LiquidityPoolTextureObservationPacketTests(unittest.TestCase):
    def test_resolve_observation_outcome_hits_take_profit_first(self) -> None:
        future_candles = [
            {"timestamp": "2026-05-01T08:00:00Z", "open": 100.0, "high": 100.8, "low": 99.8, "close": 100.6},
            {"timestamp": "2026-05-01T08:05:00Z", "open": 100.6, "high": 101.4, "low": 100.4, "close": 101.2},
        ]
        outcome = packet_builder.resolve_observation_outcome(
            direction="Bull",
            entry=100.0,
            stop_loss=99.0,
            take_profit=101.0,
            future_candles=future_candles,
        )

        self.assertEqual(outcome["outcome"], "win")
        self.assertEqual(outcome["exit_reason"], "take_profit_1")
        self.assertAlmostEqual(outcome["realized_r"], 1.0)

    def test_build_observation_packet_maps_range_sample(self) -> None:
        analyze_payload = {
            "report": {
                "symbol": "YF_QQQ_SAMPLE",
                "price_action": {
                    "nearest_liquidity_pool_level": 714.5,
                    "latest_liquidity_sweep_level": 714.5,
                    "liquidity_pool_texture": {
                        "factor_name": "liquidity_pool_texture",
                        "texture": "jagged",
                        "level": 714.5,
                        "high": 714.7,
                        "low": 714.3,
                        "touch_count": 8,
                        "spacing_consistency": 0.26,
                        "clean_sweep_likelihood": 0.64,
                        "confidence": 0.63,
                        "fail_closed_reason": None,
                    },
                },
                "trade_plan": {
                    "direction": "Bull",
                    "entry": 100.0,
                    "stop_loss": 99.0,
                    "take_profits": [101.0, 102.0, 103.0],
                },
                "multi_timeframe": {
                    "entry_model_packets": {
                        "sample": {"session_label": "dead_zone"}
                    }
                },
            }
        }
        execution_candidate_payload = {
            "pre_bayes_evidence_filter": {
                "raw_market_regime_label": "range",
                "evidence_assignments": {
                    "market_state_primary_regime": "RangeConsolidation",
                    "market_state_secondary_regime": "TightRange",
                },
            }
        }
        future_candles = [
            {"timestamp": "2026-05-01T08:00:00Z", "open": 100.0, "high": 100.5, "low": 99.6, "close": 100.2},
            {"timestamp": "2026-05-01T08:05:00Z", "open": 100.2, "high": 101.2, "low": 100.1, "close": 101.0},
        ]

        packet = packet_builder.build_observation_packet(
            analyze_payload=analyze_payload,
            execution_candidate_payload=execution_candidate_payload,
            future_candles=future_candles,
            provider="yfinance",
            timeframe="5m",
        )

        self.assertEqual(packet["branch_path_contract"]["main_regime"], "Range")
        self.assertEqual(packet["rows"][0]["provider"], "yfinance")
        self.assertEqual(packet["rows"][0]["observation_outcome"], "win")
        self.assertEqual(packet["per_regime_statistics"]["range"]["trade_count"], 1)
        self.assertFalse(packet["quality_gate"]["downstream_allowed"])

    def test_build_observation_packet_fail_closes_neutral_trade_plan(self) -> None:
        analyze_payload = {
            "report": {
                "symbol": "YF_QQQ_SAMPLE",
                "price_action": {
                    "nearest_liquidity_pool_level": 714.5,
                    "latest_liquidity_sweep_level": 714.5,
                    "liquidity_pool_texture": {
                        "factor_name": "liquidity_pool_texture",
                        "texture": "jagged",
                        "level": 714.5,
                        "high": 714.7,
                        "low": 714.3,
                        "touch_count": 8,
                        "spacing_consistency": 0.26,
                        "clean_sweep_likelihood": 0.64,
                        "confidence": 0.63,
                        "fail_closed_reason": None,
                    },
                },
                "trade_plan": {
                    "direction": "Neutral",
                    "entry": 100.0,
                    "stop_loss": 99.0,
                    "take_profits": [101.0, 102.0, 103.0],
                },
                "multi_timeframe": {
                    "entry_model_packets": {
                        "sample": {"session_label": "dead_zone"}
                    }
                },
            }
        }
        execution_candidate_payload = {
            "pre_bayes_evidence_filter": {
                "raw_market_regime_label": "range",
                "evidence_assignments": {
                    "market_state_primary_regime": "RangeConsolidation",
                    "market_state_secondary_regime": "TightRange",
                },
            }
        }
        future_candles = [
            {"timestamp": "2026-05-01T08:00:00Z", "open": 100.0, "high": 100.5, "low": 99.6, "close": 100.2},
            {"timestamp": "2026-05-01T08:05:00Z", "open": 100.2, "high": 101.2, "low": 100.1, "close": 101.0},
        ]

        packet = packet_builder.build_observation_packet(
            analyze_payload=analyze_payload,
            execution_candidate_payload=execution_candidate_payload,
            future_candles=future_candles,
            provider="yfinance",
            timeframe="5m",
        )

        self.assertEqual(packet["rows"][0]["selected_direction"], "Neutral")
        self.assertEqual(packet["rows"][0]["observation_outcome"], "no_trade")
        self.assertEqual(packet["per_regime_statistics"]["range"]["trade_count"], 0)
        self.assertEqual(
            packet["per_regime_statistics"]["range"]["fail_closed_reason"],
            "non_directional_trade_plan_not_eligible_for_realized_outcome",
        )

    def test_cli_writes_packet_and_csv(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            analyze_json = tmp / "analyze.json"
            execution_json = tmp / "execution.json"
            future_json = tmp / "future.json"
            output_json = tmp / "packet.json"
            output_csv = tmp / "packet.csv"

            analyze_json.write_text(
                json.dumps(
                    {
                        "report": {
                            "symbol": "YF_QQQ_SAMPLE",
                            "price_action": {
                                "nearest_liquidity_pool_level": 714.5,
                                "latest_liquidity_sweep_level": 714.5,
                                "liquidity_pool_texture": {
                                    "factor_name": "liquidity_pool_texture",
                                    "texture": "jagged",
                                    "level": 714.5,
                                    "high": 714.7,
                                    "low": 714.3,
                                    "touch_count": 8,
                                    "spacing_consistency": 0.26,
                                    "clean_sweep_likelihood": 0.64,
                                    "confidence": 0.63,
                                    "fail_closed_reason": None,
                                },
                            },
                            "trade_plan": {
                                "direction": "Bull",
                                "entry": 100.0,
                                "stop_loss": 99.0,
                                "take_profits": [101.0, 102.0, 103.0],
                            },
                            "multi_timeframe": {"entry_model_packets": {"sample": {"session_label": "dead_zone"}}},
                        }
                    }
                ),
                encoding="utf-8",
            )
            execution_json.write_text(
                json.dumps(
                    {
                        "pre_bayes_evidence_filter": {
                            "raw_market_regime_label": "range",
                            "evidence_assignments": {
                                "market_state_primary_regime": "RangeConsolidation",
                                "market_state_secondary_regime": "TightRange",
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )
            future_json.write_text(
                json.dumps(
                    [
                        {"timestamp": "2026-05-01T08:00:00Z", "open": 100.0, "high": 100.5, "low": 99.6, "close": 100.2},
                        {"timestamp": "2026-05-01T08:05:00Z", "open": 100.2, "high": 101.2, "low": 100.1, "close": 101.0},
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
                    "--future-ltf-json",
                    str(future_json),
                    "--provider",
                    "yfinance",
                    "--timeframe",
                    "5m",
                    "--output-json",
                    str(output_json),
                    "--output-csv",
                    str(output_csv),
                ]
            )

            self.assertEqual(exit_code, 0)
            packet = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(packet["factor_name"], "liquidity_pool_texture")
            self.assertTrue(output_csv.exists())


if __name__ == "__main__":
    unittest.main()
