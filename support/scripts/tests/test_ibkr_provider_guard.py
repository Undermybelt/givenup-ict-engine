import unittest

from support.scripts.auto_quant_external.ibkr_provider_guard import (
    classify_ibkr_ladder_state,
)


class IbkrProviderGuardTest(unittest.TestCase):
    def test_provider_status_ready_but_all_fetches_empty_blocks_aq(self) -> None:
        verdict = classify_ibkr_ladder_state(
            provider_status_exit=0,
            fetch_exits={"1m_7d": 3, "5m_1m": 3, "1d_1y": 3},
            row_counts={"1m": 0, "5m": 0, "1d": 0},
            material_count=0,
            ranked_row_count=0,
        )

        self.assertEqual(verdict.decision, "provider_blocked_no_rows_no_materials")
        self.assertFalse(verdict.provider_rows_ready)
        self.assertFalse(verdict.allow_material_build)
        self.assertFalse(verdict.allow_auto_quant)
        self.assertFalse(verdict.factor_verdict)
        self.assertFalse(verdict.cooldown_recommended)
        self.assertIn("provider-status", verdict.reason)

    def test_repeated_zero_row_ladders_recommend_provider_cooldown(self) -> None:
        verdict = classify_ibkr_ladder_state(
            provider_status_exit=0,
            fetch_exits={"1m_7d": 3, "5m_1m": 3, "1d_1y": 3},
            row_counts={"1m": 0, "5m": 0, "1d": 0},
            material_count=0,
            ranked_row_count=0,
            recent_blocked_ladders=3,
        )

        self.assertEqual(verdict.decision, "provider_cooldown_after_repeated_no_rows")
        self.assertTrue(verdict.cooldown_recommended)
        self.assertFalse(verdict.allow_material_build)
        self.assertFalse(verdict.allow_auto_quant)
        self.assertFalse(verdict.factor_verdict)
        self.assertIn("recent blocked IBKR ladders=3", verdict.reason)

    def test_any_real_rows_allows_material_stage(self) -> None:
        verdict = classify_ibkr_ladder_state(
            provider_status_exit=0,
            fetch_exits={"1m_7d": 0, "5m_1m": 3},
            row_counts={"1m": 1200, "5m": 0},
            material_count=0,
            ranked_row_count=0,
        )

        self.assertEqual(verdict.decision, "provider_rows_ready")
        self.assertTrue(verdict.provider_rows_ready)
        self.assertTrue(verdict.allow_material_build)
        self.assertFalse(verdict.cooldown_recommended)
        self.assertFalse(verdict.factor_verdict)


if __name__ == "__main__":
    unittest.main()
