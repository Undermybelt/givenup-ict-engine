from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import options_dealer_context_observation_packet as packet_builder  # noqa: E402


class OptionsDealerContextObservationPacketTests(unittest.TestCase):
    def test_derives_gamma_put_call_walls_from_option_rows(self) -> None:
        rows = [
            {"option_type": "call", "strike": 100.0, "openInterest": 100, "volume": 10, "impliedVolatility": 0.25, "days_to_expiry": 7},
            {"option_type": "call", "strike": 105.0, "openInterest": 800, "volume": 30, "impliedVolatility": 0.27, "days_to_expiry": 7},
            {"option_type": "put", "strike": 95.0, "openInterest": 700, "volume": 25, "impliedVolatility": 0.31, "days_to_expiry": 7},
            {"option_type": "put", "strike": 90.0, "openInterest": 150, "volume": 8, "impliedVolatility": 0.35, "days_to_expiry": 7},
        ]

        context = packet_builder.classify_options_dealer_context(rows, spot_price=100.0)

        self.assertEqual(context["gamma_wall"], 105.0)
        self.assertEqual(context["call_wall"], 105.0)
        self.assertEqual(context["put_wall"], 95.0)
        self.assertEqual(context["dealer_gamma_regime"], "positive_gamma_pin_risk")
        self.assertEqual(context["expected_pin_or_acceleration"], "pin_between_put_call_walls")
        self.assertGreater(context["skew_stress"], 0.0)
        self.assertGreater(context["confidence"], 0.0)

    def test_build_packet_maps_fields_and_fails_closed_single_snapshot(self) -> None:
        rows = [
            {"option_type": "call", "strike": 100.0, "openInterest": 100, "volume": 10, "impliedVolatility": 0.25, "days_to_expiry": 7},
            {"option_type": "call", "strike": 105.0, "openInterest": 800, "volume": 30, "impliedVolatility": 0.27, "days_to_expiry": 7},
            {"option_type": "put", "strike": 95.0, "openInterest": 700, "volume": 25, "impliedVolatility": 0.31, "days_to_expiry": 7},
        ]

        packet = packet_builder.build_observation_packet(
            symbol="QQQ",
            provider="yfinance",
            spot_price=100.0,
            option_rows=rows,
            snapshot_time="2026-05-16T20:56:58+08:00",
        )

        row = packet["rows"][0]
        self.assertEqual(packet["factor_name"], "options_dealer_context")
        self.assertEqual(packet["branch_path_contract"]["main_regime"], "RangeConsolidation")
        self.assertEqual(row["gamma_wall"], 105.0)
        self.assertEqual(row["put_wall"], 95.0)
        self.assertEqual(row["call_wall"], 105.0)
        self.assertFalse(row["actionable"])
        self.assertFalse(packet["quality_gate"]["downstream_allowed"])
        self.assertEqual(packet["per_regime_statistics"]["range"]["trade_count"], 0)
        self.assertIn("single_snapshot_observation_only", packet["quality_gate"]["fail_closed_reason"])
        self.assertEqual(
            packet["field_mapping"]["execution_tree_features"],
            ["gamma_wall", "put_wall", "call_wall", "dealer_gamma_regime", "expected_pin_or_acceleration", "skew_stress"],
        )

    def test_cli_writes_packet_and_csv(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            option_rows = tmp / "option_rows.json"
            output_json = tmp / "packet.json"
            output_csv = tmp / "packet.csv"
            option_rows.write_text(
                json.dumps(
                    [
                        {"option_type": "call", "strike": 100.0, "openInterest": 100, "volume": 10, "impliedVolatility": 0.25, "days_to_expiry": 7},
                        {"option_type": "call", "strike": 105.0, "openInterest": 800, "volume": 30, "impliedVolatility": 0.27, "days_to_expiry": 7},
                        {"option_type": "put", "strike": 95.0, "openInterest": 700, "volume": 25, "impliedVolatility": 0.31, "days_to_expiry": 7},
                    ]
                ),
                encoding="utf-8",
            )

            exit_code = packet_builder.main(
                [
                    "--symbol",
                    "QQQ",
                    "--provider",
                    "yfinance",
                    "--spot-price",
                    "100.0",
                    "--snapshot-time",
                    "2026-05-16T20:56:58+08:00",
                    "--option-rows-json",
                    str(option_rows),
                    "--output-json",
                    str(output_json),
                    "--output-csv",
                    str(output_csv),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(output_json.read_text(encoding="utf-8"))["factor_name"], "options_dealer_context")
            self.assertTrue(output_csv.exists())


if __name__ == "__main__":
    unittest.main()
