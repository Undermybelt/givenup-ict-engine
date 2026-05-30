from __future__ import annotations

import math
import sys
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
    def test_nq_real_cost_is_far_below_5bps_stress(self) -> None:
        # The whole point: the real NQ round-turn fee is ~0.001% of notional, not 0.1%.
        real = icm.real_fee_round_turn_fraction("NQ", 20000.0)
        # round-turn fee fraction = 4.50 / (price * multiplier) = 4.50 / (20000 * 20) = 1.125e-5
        # i.e. ~0.11 bps round-turn of notional (not the flat 10 bps the old code subtracted).
        self.assertAlmostEqual(real, 4.50 / (20000.0 * 20.0))
        self.assertAlmostEqual(real, 1.125e-5, places=10)

        stress = icm.stress_round_turn_fraction()  # legacy 5 bps/side telemetry -> 10 bps round turn = 1e-3.
        self.assertAlmostEqual(stress, 1e-3)

        # The flat 5bps/side stress over-charges NQ by ~89x at px 20000 (and ~67x at px 15000,
        # which is exactly the "~67x" the user observed: 10bps round-turn vs ~0.15bps real).
        self.assertGreater(stress / real, 80.0)
        real_15k = icm.real_fee_round_turn_fraction("NQ", 15000.0)
        self.assertAlmostEqual(stress / real_15k, 1e-3 / (4.50 / (15000.0 * 20.0)))
        self.assertAlmostEqual(stress / real_15k, 66.6667, places=3)

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

    def test_net_after_real_fee_and_stress_math(self) -> None:
        gross = 0.05  # 5% gross over 100 trades
        net_real = icm.net_after_real_fee(gross, 100, "NQ", 20000.0)
        net_stress = icm.net_after_stress_bps(gross, 100, 5.0)
        self.assertAlmostEqual(net_real, 0.05 - 100 * 1.125e-5)  # 0.048875
        self.assertAlmostEqual(net_stress, 0.05 - 100 * 1e-3)  # = -0.05
        # Real cost barely dents gross (loses ~0.0011 on 0.05); the 5bps stress flips it negative.
        self.assertGreater(net_real, 0.0488)
        self.assertLess(net_stress, 0.0)


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
    def test_packet_separates_real_from_stress(self) -> None:
        packet = icm.cost_model_packet("NQ", 20000.0)
        self.assertEqual(packet["cost_model_status"], icm.STATUS_VERIFIED)
        self.assertTrue(packet["verified_for_promotion"])
        self.assertAlmostEqual(packet["contract_multiplier"], 20.0)
        self.assertAlmostEqual(packet["all_in_round_turn_per_contract"], 4.50)
        # Stress telemetry must be present, labeled, and clearly separate from the real cost.
        self.assertEqual(packet["legacy_stress_bps_per_side"], 5.0)
        self.assertEqual(packet["legacy_stress_role"], "telemetry_not_futures_commission_model_not_candidate_gate")
        self.assertGreater(packet["legacy_stress_round_turn_pct"], packet["real_fee_round_turn_pct"] * 50)

    def test_unknown_symbol_packet_is_unverified(self) -> None:
        packet = icm.cost_model_packet("WHEATBERRY", 100.0)
        self.assertEqual(packet["cost_model_status"], icm.STATUS_UNVERIFIED)

    def test_refresh_instructions_point_to_official_sources(self) -> None:
        instructions = icm.ibkr_refresh_instructions("NQ")
        self.assertEqual(instructions["symbol_root"], "NQ")
        self.assertIn("interactivebrokers.com", instructions["ibkr_main_pricing"])
        self.assertIn("CME", instructions["ibkr_exchange_fee_pages"])


if __name__ == "__main__":
    unittest.main()
