from __future__ import annotations

import math
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import instrument_cost_model as icm  # noqa: E402


class FuturesGeometryTests(unittest.TestCase):
    def test_nq_point_value_and_all_in(self) -> None:
        nq = icm.futures_cost_profile("NQ")
        assert nq is not None
        # tick_value / tick_size = 5.0 / 0.25 = $20 per point (E-mini Nasdaq multiplier).
        self.assertAlmostEqual(nq.point_value, 20.0)
        # 0.85 + 1.38 + 0.02 = 2.25 per side; round turn = 4.50.
        self.assertAlmostEqual(nq.all_in_per_contract_per_side, 2.25)
        self.assertAlmostEqual(nq.all_in_round_turn_per_contract, 4.50)
        self.assertAlmostEqual(nq.round_trip_fee_cash(), 4.50)

    def test_symbol_normalization_micro_before_full(self) -> None:
        self.assertEqual(icm.normalize_futures_root("NQ/USD"), "NQ")
        self.assertEqual(icm.normalize_futures_root("MNQ1!"), "MNQ")  # micro must win over NQ
        self.assertEqual(icm.normalize_futures_root("MES"), "MES")  # micro must win over ES
        self.assertEqual(icm.normalize_futures_root("MGC 202606"), "MGC")  # micro must win over GC
        self.assertEqual(icm.normalize_futures_root("nq future 2021-2025"), "NQ")


class RealCostConversionTests(unittest.TestCase):
    def test_nq_real_cost_uses_contract_notional(self) -> None:
        # The whole point: NQ commission is a per-contract dollar amount converted by notional.
        real = icm.real_fee_round_turn_fraction("NQ", 20000.0)
        # round-turn fee fraction = 4.50 / (price * multiplier) = 4.50 / (20000 * 20) = 1.125e-5
        self.assertAlmostEqual(real, 4.50 / (20000.0 * 20.0))
        self.assertAlmostEqual(real, 1.125e-5, places=10)
        self.assertFalse(hasattr(icm, "stress_round_turn_fraction"))
        self.assertFalse(hasattr(icm, "net_after_stress_bps"))

    def test_per_side_bps_order_of_magnitude(self) -> None:
        # Sanity vs the skill's MGC ~0.21 bps/side observation: NQ should be sub-bp per side.
        nq_bps = icm.futures_cost_profile("NQ").per_side_fee_bps(20000.0)
        self.assertLess(nq_bps, 0.1)
        self.assertGreater(nq_bps, 0.0)
        # MGC at ~2300: 0.97 / (2300 * 10) = ~0.42 bps/side (same order as the skill's 0.21 at higher px).
        mgc_bps = icm.futures_cost_profile("MGC").per_side_fee_bps(2300.0)
        self.assertLess(mgc_bps, 1.0)

    def test_positive_price_guard(self) -> None:
        with self.assertRaises(ValueError):
            icm.futures_cost_profile("NQ").round_trip_fee_pct(0.0)

    def test_net_after_real_fee_math(self) -> None:
        gross = 0.05  # 5% gross over 100 trades
        net_real = icm.net_after_real_fee(gross, 100, "NQ", 20000.0)
        self.assertAlmostEqual(net_real, 0.05 - 100 * 1.125e-5)  # 0.048875
        self.assertGreater(net_real, 0.0488)


class VerifiedSeedAndFailClosedTests(unittest.TestCase):
    def test_mnq_uses_skill_verified_not_old_default(self) -> None:
        # The prior inline table guessed MNQ comm 0.39 + exch 0.35 = 0.74 (no reg, unverified).
        # The skill verified MNQ all-in per side = 0.25 + 0.35 + 0.02 = 0.62.
        mnq = icm.futures_cost_profile("MNQ")
        self.assertAlmostEqual(mnq.all_in_per_contract_per_side, 0.62)
        self.assertTrue(mnq.verified_for_promotion)

    def test_unknown_symbol_fails_closed(self) -> None:
        self.assertIsNone(icm.futures_cost_profile("WHEATBERRY"))
        with self.assertRaises(icm.CostModelUnverified):
            icm.real_fee_round_turn_fraction("WHEATBERRY", 100.0)
        with self.assertRaises(icm.CostModelUnverified):
            icm.assert_verified_for_promotion("WHEATBERRY")

    def test_default_rows_block_promotion(self) -> None:
        # RTY and the XAU alias are not verified broker-side -> must fail closed for promotion.
        for sym in ("RTY", "XAU", "NG", "SIL"):
            prof = icm.futures_cost_profile(sym)
            self.assertIsNotNone(prof, sym)
            self.assertFalse(prof.verified_for_promotion, sym)
            with self.assertRaises(icm.CostModelUnverified):
                icm.assert_verified_for_promotion(sym)

    def test_verified_rows_carry_provenance(self) -> None:
        nq = icm.futures_cost_profile("NQ")
        self.assertTrue(nq.verified_for_promotion)
        self.assertTrue(nq.source_url.startswith("https://"))
        self.assertTrue(nq.fetched_at)


class CostPacketTests(unittest.TestCase):
    def test_packet_reports_real_verified_cost_only(self) -> None:
        packet = icm.cost_model_packet("NQ", 20000.0)
        self.assertEqual(packet["cost_model_status"], icm.STATUS_VERIFIED)
        self.assertEqual(packet["status"], icm.STATUS_VERIFIED)
        self.assertTrue(packet["verified_for_promotion"])
        self.assertEqual(packet["currency"], "USD")
        self.assertEqual(packet["fee_effective_date"], packet["cost_model_effective_date"])
        self.assertEqual(packet["unit_convention"], "per_contract_round_turn_usd")
        self.assertIn("IBKR", packet["venue_routing"])
        self.assertAlmostEqual(packet["contract_multiplier"], 20.0)
        self.assertAlmostEqual(packet["all_in_round_turn_per_contract"], 4.50)
        self.assertNotIn("legacy_stress_bps_per_side", packet)
        self.assertNotIn("legacy_stress_round_turn_pct", packet)
        self.assertNotIn("legacy_stress_role", packet)

    def test_fixed_bps_stress_api_is_not_exposed(self) -> None:
        self.assertFalse(hasattr(icm, "GATE1_STRESS_BPS_PER_SIDE"))
        self.assertFalse(hasattr(icm, "STRESS_TELEMETRY_BPS_PER_SIDE"))
        self.assertFalse(hasattr(icm, "stress_telemetry_packet"))

    def test_unknown_symbol_packet_is_unverified(self) -> None:
        packet = icm.cost_model_packet("WHEATBERRY", 100.0)
        self.assertEqual(packet["cost_model_status"], icm.STATUS_UNVERIFIED)

    def test_refresh_instructions_point_to_official_sources(self) -> None:
        instructions = icm.ibkr_refresh_instructions("NQ")
        self.assertEqual(instructions["symbol_root"], "NQ")
        self.assertIn("interactivebrokers.com", instructions["ibkr_main_pricing"])
        self.assertIn("CME", instructions["ibkr_exchange_fee_pages"])


class RankRowCostSummaryTests(unittest.TestCase):
    def test_representative_price_from_ohlcv_csv_uses_median_close(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ohlcv.csv"
            path.write_text("timestamp,close\n1,2300\n2,2310\n3,2320\n", encoding="utf-8")

            self.assertAlmostEqual(icm.representative_price_from_ohlcv_csv(path), 2310.0)

    def test_representative_price_from_provider_rows_uses_first_existing_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.csv"
            path = Path(tmp) / "ohlcv.csv"
            path.write_text("timestamp,close\n1,2290\n2,2300\n", encoding="utf-8")

            price = icm.representative_price_from_provider_rows([
                {"path": str(missing)},
                {"path": str(path)},
            ])

            self.assertAlmostEqual(price, 2295.0)

    def test_rank_rows_real_fee_summary_uses_verified_instrument_cost_only(self) -> None:
        rows = [
            {"package_id": "pkg-mgc-dense", "trade_count": 10, "total_profit_pct": 1.0, "win_rate_pct": 60, "branch_path": "B"},
            {"package_id": "pkg-mgc-flat", "trade_count": 0, "total_profit_pct": 0.0, "win_rate_pct": 0, "branch_path": "B"},
        ]

        summary = icm.rank_rows_real_fee_summary(
            rows,
            symbol="MGC",
            representative_price=2300.0,
            label_fn=lambda row: str(row["package_id"]),
        )

        self.assertTrue(summary["promotion_cost_verified"])
        self.assertEqual(summary["cost_model"]["cost_model_status"], icm.STATUS_VERIFIED)
        self.assertEqual(summary["survivors"], ["pkg-mgc-dense"])
        first = summary["rows"][0]
        self.assertEqual(first["label"], "pkg-mgc-dense")
        self.assertIn("instrument_cost_total_profit_pct", first)
        self.assertIn("survives_instrument_cost", first)
        self.assertNotIn("5bps_per_side_total_profit_pct", first)
        expected = 1.0 - 10 * icm.futures_cost_profile("MGC").round_trip_fee_pct(2300.0)
        self.assertAlmostEqual(first["instrument_cost_total_profit_pct"], round(expected, 6))

    def test_rank_rows_real_fee_output_helpers_have_no_fixed_bps_columns(self) -> None:
        rows = [
            {"package_id": "pkg-mgc-dense", "trade_count": 10, "total_profit_pct": 1.0, "win_rate_pct": 60, "branch_path": "B"},
        ]
        summary = icm.rank_rows_real_fee_summary(rows, symbol="MGC", representative_price=2300.0)

        self.assertNotIn("5bps", " ".join(icm.REAL_FEE_RANK_FIELDS))
        lines = icm.real_fee_rank_table_lines(
            decision="observe",
            title="Rows",
            rows=summary["rows"],
            branch_ok=True,
            survivors=summary["survivors"],
            downstream=True,
        )
        joined = "\n".join(lines)
        self.assertIn("instrument cost", joined)
        self.assertNotIn("5bps", joined)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rank_rows.csv"
            icm.write_real_fee_rank_rows_csv(path, summary["rows"])
            header = path.read_text(encoding="utf-8").splitlines()[0]
            self.assertIn("instrument_cost_total_profit_pct", header)
            self.assertNotIn("5bps", header)


if __name__ == "__main__":
    unittest.main()
