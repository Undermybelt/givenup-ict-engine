from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import factor_formula_library as library  # noqa: E402


class FactorFormulaLibraryTests(unittest.TestCase):
    def test_zero_config_library_contains_hotplug_seed_pool(self) -> None:
        result = library.build_formula_library()

        self.assertEqual(result["schema_version"], "factor-formula-library/v1")
        self.assertGreaterEqual(result["seed_count"], 6)
        seed_ids = {seed["seed_id"] for seed in result["seeds"]}
        self.assertIn("qlib_alpha158_momentum_roc", seed_ids)
        self.assertIn("alpha101_rank_decay_reversion", seed_ids)
        self.assertIn("vrp_compression_regime", seed_ids)
        self.assertIn("mtf_trend_resonance_breakout_v1", seed_ids)
        self.assertIn("mim_cost_window_regime_filter_v1", seed_ids)
        first = result["seeds"][0]
        self.assertIn("expression", first)
        self.assertIn("required_fields", first)
        self.assertIn("mutation_hints", first)
        self.assertTrue(first["hotplug_ready"])

    def test_mim_cost_window_seed_is_regime_rooted_and_aq_ready(self) -> None:
        result = library.build_formula_library(families=["intraday_momentum_cost_window"])
        self.assertEqual(result["seed_count"], 1)
        seed = result["seeds"][0]

        self.assertEqual(seed["seed_id"], "mim_cost_window_regime_filter_v1")
        self.assertEqual(seed["allowed_regimes"][0], "TrendExpansion")
        self.assertIn("first_window_return", seed["required_fields"])
        self.assertIn("corwin_schultz_spread", seed["required_fields"])
        self.assertIn("momentum_state_prob", seed["required_fields"])
        self.assertIn("mtf_trend_resonance", seed["required_fields"])
        self.assertEqual(seed["default_params"]["base_timeframe"], "1m")
        self.assertEqual(seed["default_params"]["context_timeframes"], ["5m", "15m", "30m", "1h", "4h", "1d"])
        self.assertEqual(seed["default_params"]["candidate_policy"], "trend_following_only")
        self.assertGreaterEqual(seed["default_params"]["min_mtf_aligned"], 2)
        self.assertTrue(seed["hotplug_ready"])

    def test_cost_aware_triple_barrier_meta_gate_seed_requires_verified_instrument_cost(self) -> None:
        result = library.build_formula_library(families=["cost_aware_event_labeling"])
        self.assertEqual(result["seed_count"], 1)
        seed = result["seeds"][0]

        self.assertEqual(seed["seed_id"], "cost_aware_triple_barrier_meta_gate_v1")
        self.assertEqual(seed["allowed_regimes"], ["TrendExpansion"])
        self.assertIn("primary_side", seed["required_fields"])
        self.assertIn("target_volatility", seed["required_fields"])
        self.assertIn("instrument_cost_model", seed["required_fields"])
        self.assertGreaterEqual(seed["default_params"]["min_ret_bps"], 10.0)
        self.assertEqual(seed["default_params"]["cost_model_status"], "cost_model_unverified")
        self.assertFalse(seed["default_params"]["promotion_cost_verified"])
        self.assertIn("verified_instrument_cost_model", seed["default_params"]["promotion_requires"])
        self.assertIn("meta_label_probability_gate", seed["expression"])
        self.assertIn("verified_instrument_cost_edge_floor", seed["expression"])
        self.assertNotIn("round_trip_cost_bps", seed["expression"])
        self.assertNotIn("slippage_buffer_bps", seed["expression"])
        self.assertIn("FinMLKit", seed["source"])
        self.assertTrue(seed["hotplug_ready"])

    def test_mtf_trend_resonance_seed_preserves_regime_root_and_hard_gates(self) -> None:
        result = library.build_formula_library(families=["mtf_trend_resonance"])
        self.assertEqual(result["seed_count"], 1)
        seed = result["seeds"][0]

        self.assertEqual(seed["seed_id"], "mtf_trend_resonance_breakout_v1")
        self.assertEqual(seed["allowed_regimes"], ["TrendExpansion"])
        self.assertEqual(seed["default_params"]["candidate_policy"], "trend_following_only")
        self.assertEqual(seed["default_params"]["base_timeframe"], "1m")
        self.assertEqual(seed["default_params"]["context_timeframes"], ["5m", "15m", "30m", "1h", "4h", "1d"])
        self.assertGreaterEqual(seed["default_params"]["min_mtf_aligned"], 3)
        self.assertIn("TrendExpansion -> MTFTrendContinuationOrPullback", seed["default_params"]["branch_path_template"])
        self.assertEqual(seed["default_params"]["cost_model_status"], "cost_model_unverified")
        self.assertFalse(seed["default_params"]["promotion_cost_verified"])
        self.assertIn("verified_instrument_cost_model", seed["default_params"]["promotion_requires"])
        self.assertIn("triple_barrier_meta_label_only_after_primary_event_survives_cost", seed["overlay_policy"])
        self.assertEqual(seed["artifact_policy"], "provider_rows_required_no_simulated_promotion")

    def test_formula_library_source_has_no_fixed_bps_cost_authority(self) -> None:
        import fixed_bps_cost_model_source_check as checker

        report = checker.check_source_file(SCRIPT_ROOT / "factor_formula_library.py")

        self.assertTrue(report["ok"], report["violations"])

    def test_family_filter_returns_only_requested_factor_family(self) -> None:
        result = library.build_formula_library(families=["mean_reversion"])

        self.assertGreaterEqual(result["seed_count"], 1)
        self.assertEqual({seed["family"] for seed in result["seeds"]}, {"mean_reversion"})

    def test_cli_writes_json_and_jsonl_artifacts(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            output_json = tmp / "formula_library.json"
            output_jsonl = tmp / "formula_library.jsonl"

            exit_code = library.main(
                [
                    "--output-json",
                    str(output_json),
                    "--output-jsonl",
                    str(output_jsonl),
                    "--family",
                    "momentum",
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertGreaterEqual(payload["seed_count"], 1)
            self.assertIn('"family": "momentum"', output_jsonl.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
