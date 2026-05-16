from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import smt_observation_packet as packet_builder  # noqa: E402


class SmtObservationPacketTests(unittest.TestCase):
    def test_resolve_observation_outcome_hits_take_profit_first(self) -> None:
        future_candles = [
            {"timestamp": "2026-05-01T08:00:00Z", "open": 100.0, "high": 100.5, "low": 99.7, "close": 100.2},
            {"timestamp": "2026-05-01T08:05:00Z", "open": 100.2, "high": 101.4, "low": 100.1, "close": 101.1},
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

    def test_build_observation_packet_maps_smt_fields_and_fail_closed_gate(self) -> None:
        analyze_payload = {
            "report": {
                "symbol": "NQ",
                "smt_correlation": {
                    "paired_market_available": True,
                    "spot_symbol": "ES",
                    "timeframe": "5m",
                    "comparison_timeframe": "5m",
                    "session": "new_york_am",
                    "relationship_type": "positive",
                    "relationship_confidence": 0.84,
                    "primary_related_symbols": ["ES", "YM", "RTY"],
                    "futures_peers": ["ES", "YM", "RTY", "DXY", "VIX"],
                    "cfd_proxies": ["NAS100", "US500", "US30"],
                    "etf_proxies": ["QQQ", "SPY", "DIA", "IWM"],
                    "sector_or_industry_peers": [],
                    "currency_macro_drivers": ["DXY", "VIX"],
                    "session_leaders": ["NQ", "ES"],
                    "resolver_relationship_type": "index_peer",
                    "resolver_confidence": 0.90,
                    "resolver_evidence_source": "builtin_symbol_relationship_seed",
                    "smt_signal": "bearish_smt",
                    "base_swing_type": "HH_sweep",
                    "base_level": 18550.25,
                    "comparison_swing_type": "LH",
                    "comparison_level": 5320.75,
                    "raw_comparison_swing_type": "LH",
                    "raw_comparison_level": 5320.75,
                    "swept_side": "buy_side_liquidity",
                    "same_liquidity_event_confirmed": True,
                    "normalized_for_inverse_correlation": False,
                    "near_pd_array": True,
                    "pd_array_type": "FVG",
                    "mss_or_cisd_confirmed": True,
                    "displacement_confirmed": True,
                    "trade_use": "confirmation_only",
                    "fail_closed_reason": None,
                    "related_futures_symbols": ["ES", "YM", "RTY"],
                    "related_etf_symbols": ["QQQ", "SPY"],
                    "related_options_symbols": ["QQQ"],
                    "related_cfd_symbols": ["NAS100", "US500"],
                    "related_crypto_symbols": [],
                },
                "trade_plan": {
                    "direction": "Bear",
                    "entry": 100.0,
                    "stop_loss": 101.0,
                    "take_profits": [99.0, 98.0, 97.0],
                },
                "multi_timeframe": {
                    "entry_model_packets": {"sample": {"session_label": "new_york_am"}}
                },
            }
        }
        execution_candidate_payload = {
            "pre_bayes_evidence_filter": {
                "raw_market_regime_label": "transition",
                "evidence_assignments": {
                    "market_state_primary_regime": "TransitionCompression"
                },
            }
        }
        future_candles = [
            {"timestamp": "2026-05-01T08:00:00Z", "open": 100.0, "high": 100.2, "low": 99.5, "close": 99.7},
            {"timestamp": "2026-05-01T08:05:00Z", "open": 99.7, "high": 99.9, "low": 98.8, "close": 99.0},
        ]

        packet = packet_builder.build_observation_packet(
            analyze_payload=analyze_payload,
            execution_candidate_payload=execution_candidate_payload,
            future_candles=future_candles,
            provider="yfinance",
            timeframe="5m",
            comparison_symbol="ES",
            comparison_session="new_york_am",
        )

        row = packet["rows"][0]
        self.assertEqual(packet["branch_path_contract"]["main_regime"], "Transition")
        self.assertEqual(row["comparison_symbol"], "ES")
        self.assertTrue(row["timeframe_aligned"])
        self.assertTrue(row["same_liquidity_event_confirmed"])
        self.assertEqual(row["base_level"], 18550.25)
        self.assertEqual(row["comparison_level"], 5320.75)
        self.assertTrue(row["near_pd_array"])
        self.assertEqual(row["pd_array_type"], "FVG")
        self.assertTrue(row["mss_or_cisd_confirmed"])
        self.assertTrue(row["displacement_confirmed"])
        self.assertEqual(row["resolver_relationship_type"], "index_peer")
        self.assertEqual(row["resolver_confidence"], 0.90)
        self.assertEqual(
            packet["relationship_resolver"]["primary_related_symbols"],
            ["ES", "YM", "RTY"],
        )
        self.assertEqual(
            packet["relationship_resolver"]["session_leaders"],
            ["NQ", "ES"],
        )
        self.assertFalse(packet["quality_gate"]["downstream_allowed"])
        self.assertEqual(packet["per_regime_statistics"]["transition"]["trade_count"], 1)
        self.assertEqual(
            packet["field_mapping"]["smt"],
            [
                "smt_signal",
                "trade_use",
                "near_pd_array",
                "pd_array_type",
                "mss_or_cisd_confirmed",
                "displacement_confirmed",
                "fail_closed_reason",
            ],
        )

    def test_build_observation_packet_fails_closed_when_session_or_relationship_unstable(self) -> None:
        analyze_payload = {
            "report": {
                "symbol": "EURUSD",
                "smt_correlation": {
                    "paired_market_available": True,
                    "spot_symbol": "DXY",
                    "relationship_type": "uncertain",
                    "relationship_confidence": 0.18,
                    "smt_signal": None,
                    "base_swing_type": None,
                    "base_level": None,
                    "comparison_swing_type": None,
                    "comparison_level": None,
                    "raw_comparison_swing_type": None,
                    "raw_comparison_level": None,
                    "swept_side": None,
                    "normalized_for_inverse_correlation": False,
                    "trade_use": "confirmation_only",
                    "fail_closed_reason": "relationship_uncertain",
                    "related_futures_symbols": ["6E", "DX"],
                    "related_etf_symbols": ["FXE", "UUP"],
                    "related_options_symbols": [],
                    "related_cfd_symbols": ["GBPUSD"],
                    "related_crypto_symbols": [],
                },
                "trade_plan": {
                    "direction": "Bull",
                    "entry": 1.08,
                    "stop_loss": 1.07,
                    "take_profits": [1.09, 1.10, 1.11],
                },
                "multi_timeframe": {
                    "entry_model_packets": {"sample": {"session_label": "london"}}
                },
            }
        }
        execution_candidate_payload = {
            "pre_bayes_evidence_filter": {"raw_market_regime_label": "range", "evidence_assignments": {}}
        }
        future_candles = [
            {"timestamp": "2026-05-01T08:00:00Z", "open": 1.08, "high": 1.081, "low": 1.075, "close": 1.076},
            {"timestamp": "2026-05-01T08:05:00Z", "open": 1.076, "high": 1.078, "low": 1.072, "close": 1.074},
        ]

        packet = packet_builder.build_observation_packet(
            analyze_payload=analyze_payload,
            execution_candidate_payload=execution_candidate_payload,
            future_candles=future_candles,
            provider="yfinance",
            timeframe="5m",
            comparison_symbol="DXY",
            comparison_session="new_york_am",
        )

        reason = packet["quality_gate"]["fail_closed_reason"]
        self.assertIn("recent_correlation_unstable", reason)
        self.assertIn("session_not_overlapping", reason)
        self.assertIn("missing_required_structure_levels", reason)

    def test_build_observation_packet_fails_closed_when_smt_signal_lacks_entry_context(self) -> None:
        analyze_payload = {
            "report": {
                "symbol": "XAUUSD",
                "smt_correlation": {
                    "paired_market_available": True,
                    "spot_symbol": "XAGUSD",
                    "timeframe": "15m",
                    "comparison_timeframe": "5m",
                    "session": "new_york_am",
                    "relationship_type": "positive",
                    "relationship_confidence": 0.76,
                    "smt_signal": "bullish_smt",
                    "base_swing_type": "LL_sweep",
                    "base_level": 2335.1,
                    "comparison_swing_type": "HL",
                    "comparison_level": 28.42,
                    "raw_comparison_swing_type": "HL",
                    "raw_comparison_level": 28.42,
                    "swept_side": "sell_side_liquidity",
                    "same_liquidity_event_confirmed": False,
                    "normalized_for_inverse_correlation": False,
                    "near_pd_array": False,
                    "pd_array_type": "none",
                    "mss_or_cisd_confirmed": False,
                    "displacement_confirmed": False,
                    "trade_use": "confirmation_only",
                    "fail_closed_reason": None,
                    "related_futures_symbols": ["GC", "SI"],
                    "related_etf_symbols": ["GDX"],
                    "related_options_symbols": [],
                    "related_cfd_symbols": ["XAUUSD", "XAGUSD"],
                    "related_crypto_symbols": [],
                },
                "trade_plan": {
                    "direction": "Bull",
                    "entry": 100.0,
                    "stop_loss": 99.0,
                    "take_profits": [101.0],
                },
                "multi_timeframe": {"entry_model_packets": {"sample": {"session_label": "new_york_am"}}},
            }
        }
        execution_candidate_payload = {
            "pre_bayes_evidence_filter": {"raw_market_regime_label": "stress", "evidence_assignments": {}}
        }
        future_candles = [
            {"timestamp": "2026-05-01T08:00:00Z", "open": 100.0, "high": 100.4, "low": 99.7, "close": 100.2},
            {"timestamp": "2026-05-01T08:15:00Z", "open": 100.2, "high": 100.6, "low": 99.8, "close": 100.1},
        ]

        packet = packet_builder.build_observation_packet(
            analyze_payload=analyze_payload,
            execution_candidate_payload=execution_candidate_payload,
            future_candles=future_candles,
            provider="yfinance",
            timeframe="15m",
            comparison_symbol="XAGUSD",
            comparison_session="new_york_am",
        )

        reason = packet["quality_gate"]["fail_closed_reason"]
        self.assertIn("timeframe_not_aligned", reason)
        self.assertIn("same_liquidity_event_not_confirmed", reason)
        self.assertIn("missing_mss_or_cisd_confirmation", reason)
        self.assertIn("missing_displacement_confirmation", reason)
        self.assertIn("missing_pd_array_entry_context", reason)
        self.assertFalse(packet["quality_gate"]["downstream_allowed"])

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
                            "symbol": "BTC",
                            "smt_correlation": {
                                "paired_market_available": True,
                                "spot_symbol": "ETH",
                                "timeframe": "5m",
                                "comparison_timeframe": "5m",
                                "session": "london",
                                "relationship_type": "positive",
                                "relationship_confidence": 0.7,
                                "primary_related_symbols": ["ETH", "SOL", "DXY"],
                                "futures_peers": ["BTC", "ETH"],
                                "cfd_proxies": ["BTCUSD", "ETHUSD"],
                                "etf_proxies": ["IBIT", "ETHA", "QQQ"],
                                "sector_or_industry_peers": [],
                                "currency_macro_drivers": ["DXY", "QQQ"],
                                "session_leaders": ["BTC", "ETH"],
                                "resolver_relationship_type": "crypto_beta",
                                "resolver_confidence": 0.78,
                                "resolver_evidence_source": "builtin_symbol_relationship_seed",
                                "smt_signal": "bullish_smt",
                                "base_swing_type": "LL_sweep",
                                "base_level": 61250.0,
                                "comparison_swing_type": "HL",
                                "comparison_level": 3045.0,
                                "raw_comparison_swing_type": "HL",
                                "raw_comparison_level": 3045.0,
                                "swept_side": "sell_side_liquidity",
                                "same_liquidity_event_confirmed": True,
                                "normalized_for_inverse_correlation": False,
                                "near_pd_array": False,
                                "pd_array_type": "none",
                                "mss_or_cisd_confirmed": False,
                                "displacement_confirmed": False,
                                "trade_use": "confirmation_only",
                                "fail_closed_reason": None,
                                "related_futures_symbols": ["BTC", "ETH"],
                                "related_etf_symbols": ["IBIT", "ETHA", "QQQ"],
                                "related_options_symbols": [],
                                "related_cfd_symbols": ["BTCUSD", "ETHUSD"],
                                "related_crypto_symbols": ["SOL"],
                            },
                            "trade_plan": {
                                "direction": "Bull",
                                "entry": 100.0,
                                "stop_loss": 99.0,
                                "take_profits": [101.0, 102.0, 103.0],
                            },
                            "multi_timeframe": {"entry_model_packets": {"sample": {"session_label": "london"}}},
                        }
                    }
                ),
                encoding="utf-8",
            )
            execution_json.write_text(
                json.dumps(
                    {
                        "pre_bayes_evidence_filter": {
                            "raw_market_regime_label": "trend",
                            "evidence_assignments": {
                                "market_state_primary_regime": "TrendExpansion"
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )
            future_json.write_text(
                json.dumps(
                    [
                        {"timestamp": "2026-05-01T08:00:00Z", "open": 100.0, "high": 100.6, "low": 99.8, "close": 100.4},
                        {"timestamp": "2026-05-01T08:05:00Z", "open": 100.4, "high": 101.3, "low": 100.3, "close": 101.0},
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
                    "kraken",
                    "--timeframe",
                    "5m",
                    "--comparison-symbol",
                    "ETH",
                    "--comparison-session",
                    "london",
                    "--output-json",
                    str(output_json),
                    "--output-csv",
                    str(output_csv),
                ]
            )

            self.assertEqual(exit_code, 0)
            packet = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(packet["factor_name"], "smt_relationship_resolver")
            self.assertTrue(output_csv.exists())


if __name__ == "__main__":
    unittest.main()
