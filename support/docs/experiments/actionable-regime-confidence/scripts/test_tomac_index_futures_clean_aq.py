#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import argparse
from subprocess import TimeoutExpired
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd


SCRIPT = Path(__file__).with_name("run_tomac_index_futures_clean_aq_v1.py")
SPEC = importlib.util.spec_from_file_location("tomac_index_futures_clean_aq", SCRIPT)


class TomacIndexFuturesCleanAqTest(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        assert SPEC is not None and SPEC.loader is not None
        sys.modules[SPEC.name] = module
        SPEC.loader.exec_module(module)
        return module

    def test_pyarrow_missing_reexecs_through_auto_quant_python(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            preferred_python = Path(tmpdir) / "aq-python"
            preferred_python.write_text("", encoding="utf-8")

            argv = ["runner.py", "--root", "/tmp/run", "--symbols", "ES"]
            reexec_argv = module.pyarrow_runtime_reexec_argv(
                current_executable=Path("/usr/bin/python3"),
                preferred_python=preferred_python,
                argv=argv,
                pyarrow_available=False,
                script_path=Path("/repo/run_tomac_index_futures_clean_aq_v1.py"),
            )

            self.assertEqual(
                reexec_argv,
                [
                    str(preferred_python),
                    "/repo/run_tomac_index_futures_clean_aq_v1.py",
                    "--root",
                    "/tmp/run",
                    "--symbols",
                    "ES",
                ],
            )

    def test_ssa_spectral_trend_denoise_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["ssa_spectral_trend_denoise_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "SsaSpectralTrendDenoiseFilter")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> SpectralDenoiseTrendQuality -> SsaLowRankSignalFilter -> ParentSignalAdmission",
        )
        self.assertEqual(
            spec.factor_id("1m"),
            "tomac_idxfut_clean_ssa_spectral_trend_denoise_filter_1m_v1",
        )

    def test_ssa_spectral_trend_denoise_strategy_source_uses_shifted_low_rank_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["ssa_spectral_trend_denoise_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn("factor_id: tomac_idxfut_clean_ssa_spectral_trend_denoise_filter_1m_v1", source)
        self.assertIn("SpectralDenoiseTrendQuality", source)
        self.assertIn("low_rank_trend = dataframe[\"close\"].rolling(55).mean()", source)
        self.assertIn("ssa_residual_energy_ratio", source)
        self.assertIn("ssa_low_rank_signal_filter_long.fillna(False)", source)
        self.assertIn("ssa_low_rank_signal_filter_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)

    def test_vmd_intrinsic_mode_trend_rejoin_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["vmd_intrinsic_mode_trend_rejoin_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "VmdIntrinsicModeTrendRejoinFilter")
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> AdaptiveSignalDecomposition -> VariationalModeIntrinsicTrend -> ModeEnergyConcentration",
        )
        timeframes = ("1m", "5m", "15m", "30m", "1h", "4h", "1d")
        self.assertTrue(all(spec.supports(symbol="NQ", timeframe=timeframe) for timeframe in timeframes))
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in timeframes],
            [
                "tomac_idxfut_clean_vmd_intrinsic_mode_trend_rejoin_filter_1m_v1",
                "tomac_idxfut_clean_vmd_intrinsic_mode_trend_rejoin_filter_5m_v1",
                "tomac_idxfut_clean_vmd_intrinsic_mode_trend_rejoin_filter_15m_v1",
                "tomac_idxfut_clean_vmd_intrinsic_mode_trend_rejoin_filter_30m_v1",
                "tomac_idxfut_clean_vmd_intrinsic_mode_trend_rejoin_filter_1h_v1",
                "tomac_idxfut_clean_vmd_intrinsic_mode_trend_rejoin_filter_4h_v1",
                "tomac_idxfut_clean_vmd_intrinsic_mode_trend_rejoin_filter_1d_v1",
            ],
        )

    def test_vmd_intrinsic_mode_trend_rejoin_strategy_source_uses_shifted_mode_energy_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["vmd_intrinsic_mode_trend_rejoin_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn("factor_id: tomac_idxfut_clean_vmd_intrinsic_mode_trend_rejoin_filter_1m_v1", source)
        self.assertIn("VariationalModeIntrinsicTrend", source)
        self.assertIn("vmd_low_frequency_mode_proxy", source)
        self.assertIn("vmd_high_frequency_residual", source)
        self.assertIn("vmd_low_mode_slope_bps_shifted", source)
        self.assertIn("vmd_high_mode_energy_ratio_shifted", source)
        self.assertIn("vmd_intrinsic_mode_trend_long.fillna(False)", source)
        self.assertIn("vmd_intrinsic_mode_trend_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "vmd_intrinsic_mode_trend_rejoin_filter" == "vmd_intrinsic_mode_trend_rejoin_filter":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        vmd_block = source[branch_start:next_branch]
        self.assertNotIn("shift(-", vmd_block)

    def test_trend_expansion_retest_hold_quality_family_is_registered_for_nq_15m(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["trend_expansion_only_regime_transition_retest_hold_quality"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "TrendExpansionOnlyRetestHoldQuality")
        self.assertEqual(spec.direction, "long")
        self.assertEqual(
            spec.branch_path,
            "RegimeTransition -> TrendExpansionOnly -> CompressionBreakoutStateShift -> RetestHoldQuality",
        )
        self.assertTrue(spec.supports(symbol="NQ", timeframe="15m"))
        self.assertFalse(spec.supports(symbol="NQ", timeframe="5m"))
        self.assertFalse(spec.supports(symbol="ES", timeframe="15m"))
        self.assertEqual(
            spec.factor_id("15m"),
            "tomac_nq_15m_trend_expansion_only_regime_transition_long_retest_hold_quality_exact_aq_v1",
        )

    def test_trend_expansion_retest_hold_quality_strategy_source_is_closed_bar_only(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["trend_expansion_only_regime_transition_retest_hold_quality"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn(
            "factor_id: tomac_nq_15m_trend_expansion_only_regime_transition_long_retest_hold_quality_exact_aq_v1",
            source,
        )
        self.assertIn("RetestHoldQuality", source)
        self.assertIn("state_shift_retest_hold_long", source)
        self.assertIn("other_regimes_reference_veto_only", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "trend_expansion_only_regime_transition_retest_hold_quality" == "trend_expansion_only_regime_transition_retest_hold_quality":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        retest_block = source[branch_start:next_branch]
        self.assertNotIn("shift(-", retest_block)

    def test_ehlers_autocorr_periodogram_cycle_gate_family_is_registered_for_eth_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["ehlers_autocorr_periodogram_cycle_regime_gate"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "EhlersAutocorrPeriodogramCycleRegimeGate")
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.branch_path,
            "CycleRegime -> AutocorrelationPeriodogram -> DominantCycleStability -> ParentSignalAdmissionFilter",
        )
        self.assertFalse(spec.supports(symbol="NQ", timeframe="1m"))
        timeframes = ("5m", "15m", "30m", "1h", "4h", "1d")
        self.assertTrue(all(spec.supports(symbol="NQ", timeframe=timeframe) for timeframe in timeframes))
        self.assertFalse(spec.supports(symbol="ES", timeframe="30m"))
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in timeframes],
            [
                "tomac_nq_5m_ehlers_autocorr_periodogram_cycle_regime_gate_v1",
                "tomac_nq_15m_ehlers_autocorr_periodogram_cycle_regime_gate_v1",
                "tomac_nq_30m_ehlers_autocorr_periodogram_cycle_regime_gate_v1",
                "tomac_nq_1h_ehlers_autocorr_periodogram_cycle_regime_gate_v1",
                "tomac_nq_4h_ehlers_autocorr_periodogram_cycle_regime_gate_v1",
                "tomac_nq_1d_ehlers_autocorr_periodogram_cycle_regime_gate_v1",
            ],
        )

    def test_ehlers_autocorr_periodogram_cycle_gate_source_is_closed_bar_only(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["ehlers_autocorr_periodogram_cycle_regime_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("factor_id: tomac_nq_30m_ehlers_autocorr_periodogram_cycle_regime_gate_v1", source)
        self.assertIn("AutocorrelationPeriodogram", source)
        self.assertIn("ehlers_dominant_cycle_period_shifted", source)
        self.assertIn("ehlers_cycle_concentration_shifted", source)
        self.assertIn("ehlers_cycle_stability_shifted", source)
        self.assertIn("ehlers_autocorr_cycle_gate_long.fillna(False)", source)
        self.assertIn("ehlers_autocorr_cycle_gate_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertGreaterEqual(
            source.count(
                'elif "ehlers_autocorr_periodogram_cycle_regime_gate" == "ehlers_autocorr_periodogram_cycle_regime_gate":'
            ),
            2,
        )
        self.assertIn("ehlers_cycle_instability_exit", source)
        self.assertIn("ehlers_long_cycle_failure", source)
        self.assertIn("ehlers_short_cycle_failure", source)
        self.assertIn("exit_signal = exit_raw.shift(1).fillna(False)", source)
        self.assertIn("short_exit_signal = short_exit_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "ehlers_autocorr_periodogram_cycle_regime_gate" == "ehlers_autocorr_periodogram_cycle_regime_gate":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        ehlers_block = source[branch_start:next_branch]
        self.assertNotIn("shift(-", ehlers_block)

    def test_hilbert_analytic_phase_trend_admission_family_is_registered_for_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["hilbert_analytic_phase_trend_admission"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "HilbertAnalyticPhaseTrendAdmission")
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> CyclePhaseState -> HilbertAnalyticPhaseSlope -> PhaseCoherentTrendAdmission -> FrictionAwareRrrBracket",
        )
        self.assertFalse(spec.supports(symbol="NQ", timeframe="1m"))
        timeframes = ("5m", "15m", "30m", "1h", "4h", "1d")
        self.assertTrue(all(spec.supports(symbol="NQ", timeframe=timeframe) for timeframe in timeframes))
        self.assertFalse(spec.supports(symbol="ES", timeframe="30m"))
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in timeframes],
            [
                "tomac_nq_5m_hilbert_analytic_phase_trend_admission_v1",
                "tomac_nq_15m_hilbert_analytic_phase_trend_admission_v1",
                "tomac_nq_30m_hilbert_analytic_phase_trend_admission_v1",
                "tomac_nq_1h_hilbert_analytic_phase_trend_admission_v1",
                "tomac_nq_4h_hilbert_analytic_phase_trend_admission_v1",
                "tomac_nq_1d_hilbert_analytic_phase_trend_admission_v1",
            ],
        )

    def test_hilbert_analytic_phase_trend_admission_source_is_closed_bar_only(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["hilbert_analytic_phase_trend_admission"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("factor_id: tomac_nq_30m_hilbert_analytic_phase_trend_admission_v1", source)
        self.assertIn("HilbertAnalyticPhaseSlope", source)
        self.assertIn("hilbert_phase_shifted", source)
        self.assertIn("hilbert_phase_slope_shifted", source)
        self.assertIn("hilbert_phase_accel_shifted", source)
        self.assertIn("phase_coherence_score_shifted", source)
        self.assertIn("hilbert_analytic_phase_trend_long.fillna(False)", source)
        self.assertIn("hilbert_analytic_phase_trend_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertIn("hilbert_phase_decoherence_exit", source)
        self.assertIn("hilbert_long_phase_failure", source)
        self.assertIn("hilbert_short_phase_failure", source)
        self.assertIn("exit_signal = exit_raw.shift(1).fillna(False)", source)
        self.assertIn("short_exit_signal = short_exit_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "hilbert_analytic_phase_trend_admission" == "hilbert_analytic_phase_trend_admission":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        hilbert_block = source[branch_start:next_branch]
        self.assertNotIn("shift(-", hilbert_block)

    def test_trend_ote_ks_distribution_stability_family_is_registered_for_eth_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["trend_ote_ks_distribution_stability_reacceleration"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "TrendOteKsDistributionStabilityReacceleration")
        self.assertEqual(spec.direction, "long")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> OtePullbackContinuation -> ReturnShapeStability -> KsDistributionDriftGuard -> ReaccelerationEntry",
        )
        self.assertFalse(spec.supports(symbol="NQ", timeframe="1m"))
        timeframes = ("5m", "15m", "30m", "1h", "4h", "1d")
        self.assertTrue(all(spec.supports(symbol="NQ", timeframe=timeframe) for timeframe in timeframes))
        self.assertFalse(spec.supports(symbol="ES", timeframe="15m"))
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in timeframes],
            [
                "tomac_nq_5m_eth_ote_ks_stability_reacceleration_long_v1",
                "tomac_nq_15m_eth_ote_ks_stability_reacceleration_long_v1",
                "tomac_nq_30m_eth_ote_ks_stability_reacceleration_long_v1",
                "tomac_nq_1h_eth_ote_ks_stability_reacceleration_long_v1",
                "tomac_nq_4h_eth_ote_ks_stability_reacceleration_long_v1",
                "tomac_nq_1d_eth_ote_ks_stability_reacceleration_long_v1",
            ],
        )

    def test_trend_ote_ks_distribution_stability_strategy_source_is_closed_bar_only(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["trend_ote_ks_distribution_stability_reacceleration"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_nq_15m_eth_ote_ks_stability_reacceleration_long_v1", source)
        self.assertIn("KsDistributionDriftGuard", source)
        self.assertIn("ote_ks_distribution_distance", source)
        self.assertIn("ote_ks_stability_gate", source)
        self.assertIn("ote_ks_reacceleration_long.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "trend_ote_ks_distribution_stability_reacceleration" == "trend_ote_ks_distribution_stability_reacceleration":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        ote_ks_block = source[branch_start:next_branch]
        self.assertNotIn("shift(-", ote_ks_block)

    def test_heikin_ashi_kama_quality_30m_family_is_registered_with_exact_nq_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["heikin_ashi_kama_trend_pullback_rejoin_long_quality_30m"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "HeikinAshiKamaTrendPullbackRejoinLongQuality")
        self.assertEqual(spec.direction, "long")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> HeikinAshiTrendState -> KamaEfficiencyPullback -> RejoinReacceleration -> MtfSlopeResonance",
        )
        self.assertTrue(spec.supports(symbol="NQ", timeframe="30m"))
        self.assertFalse(spec.supports(symbol="YM", timeframe="30m"))
        self.assertFalse(spec.supports(symbol="NQ", timeframe="15m"))
        self.assertEqual(
            spec.factor_id("30m"),
            "tomac_nq_30m_heikin_ashi_kama_trend_pullback_rejoin_long_qualityrejoin_v1",
        )

    def test_heikin_ashi_kama_quality_30m_strategy_source_uses_shifted_rejoin_gate(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["heikin_ashi_kama_trend_pullback_rejoin_long_quality_30m"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("factor_id: tomac_nq_30m_heikin_ashi_kama_trend_pullback_rejoin_long_qualityrejoin_v1", source)
        self.assertIn("HeikinAshiTrendState", source)
        self.assertIn("ha_trend_shifted", source)
        self.assertIn("heikin_kama_efficiency_shifted", source)
        self.assertIn("heikin_kama_pullback_low_prev", source)
        self.assertIn("heikin_kama_quality_rejoin_long.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_wavelet_coherence_lead_lag_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["wavelet_coherence_lead_lag_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "WaveletCoherenceLeadLagFilter")
        self.assertEqual(
            spec.branch_path,
            "CrossMarketConfirmation -> WaveletCoherenceLeadLag -> ScaleLocalizedLeaderConfirmation -> ParentTrendAdmission",
        )
        self.assertEqual(
            spec.factor_id("1m"),
            "tomac_idxfut_clean_wavelet_coherence_lead_lag_filter_1m_v1",
        )

    def test_wavelet_coherence_lead_lag_strategy_source_uses_shifted_coherence_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["wavelet_coherence_lead_lag_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn("factor_id: tomac_idxfut_clean_wavelet_coherence_lead_lag_filter_1m_v1", source)
        self.assertIn("WaveletCoherenceLeadLag", source)
        self.assertIn("scale_localized_coherence", source)
        self.assertIn("coherence_lead_lag_impulse", source)
        self.assertIn("leader_confirmation_long.fillna(False)", source)
        self.assertIn("leader_confirmation_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)

    def test_dynamic_lead_lag_breadth_family_is_registered_with_exact_1h_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["dynamic_lead_lag_breadth_gate"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "DynamicLeadLagBreadthGate")
        self.assertEqual(
            spec.branch_path,
            "CrossMarketStructure -> DynamicLeadLagBreadth -> PairSpecificLagAdmissionFilter -> NqTrendParentRescore",
        )
        self.assertEqual(
            spec.factor_id("1h"),
            "tomac_nq_dynamic_lead_lag_breadth_gate_1h_long_lb64_cw128_h24_v1",
        )
        self.assertTrue(spec.supports(symbol="NQ", timeframe="1h"))
        self.assertFalse(spec.supports(symbol="YM", timeframe="1h"))
        self.assertFalse(spec.supports(symbol="NQ", timeframe="15m"))

    def test_dynamic_lead_lag_breadth_strategy_source_uses_shifted_sidecar_gate(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["dynamic_lead_lag_breadth_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="1h")

        self.assertIn("factor_id: tomac_nq_dynamic_lead_lag_breadth_gate_1h_long_lb64_cw128_h24_v1", source)
        self.assertIn("CrossMarketStructure -> DynamicLeadLagBreadth", source)
        self.assertIn("dll_leadlag_score_bps", source)
        self.assertIn("dll_leadlag_agreement_long", source)
        self.assertIn("dll_nq_momentum_bps", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_dynamic_lead_lag_breadth_sidecar_materializes_completed_bar_features(self) -> None:
        module = self.load_module()
        if not module.has_pyarrow():
            self.skipTest("pyarrow unavailable")

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            dates = pd.date_range("2021-01-01", periods=220, freq="1h", tz="UTC")
            for symbol, offset in (("NQ", 0.0), ("YM", 1.5), ("GC", -2.0)):
                out_dir = root / "clean" / symbol
                out_dir.mkdir(parents=True)
                close = [100.0 + offset + idx * 0.15 for idx in range(len(dates))]
                pd.DataFrame({"date": dates, "close": close}).to_feather(
                    out_dir / f"{symbol}_USD-1h.feather"
                )
            frame = pd.DataFrame({"date": dates, "close": [100.0 + idx * 0.15 for idx in range(len(dates))]})

            merged, stats = module.merge_dynamic_lead_lag_breadth_sidecar(
                frame,
                root,
                symbol="NQ",
                timeframe="1h",
            )

        self.assertEqual(stats["status"], "materialized")
        self.assertEqual(stats["future_lookahead"], False)
        self.assertIn("dll_leadlag_score_bps", merged.columns)
        self.assertIn("dll_nq_momentum_bps", merged.columns)
        self.assertIn("dll_gc_score_bps", merged.columns)
        self.assertNotIn("dll_xau_score_bps", merged.columns)
        self.assertGreater(int(merged["dll_leadlag_score_bps"].notna().sum()), 0)

    def test_dynamic_lead_lag_breadth_staging_keeps_aq_ohlcv_six_columns(self) -> None:
        module = self.load_module()
        if not module.has_pyarrow():
            self.skipTest("pyarrow unavailable")
        if not (module.AQ_REPO / "run_tomac.py").exists() or not (module.AQ_REPO / "config.tomac.json").exists():
            self.skipTest("Auto-Quant workspace unavailable")

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            dates = pd.date_range("2021-01-01", periods=220, freq="1h", tz="UTC")
            for symbol, offset in (("NQ", 0.0), ("YM", 1.5), ("GC", -2.0)):
                out_dir = root / "clean" / symbol
                out_dir.mkdir(parents=True)
                close = [100.0 + offset + idx * 0.15 for idx in range(len(dates))]
                frame = pd.DataFrame(
                    {
                        "date": dates,
                        "open": close,
                        "high": [value + 0.2 for value in close],
                        "low": [value - 0.2 for value in close],
                        "close": close,
                        "volume": [1000.0 for _ in close],
                    }
                )
                frame.to_feather(out_dir / f"{symbol}_USD-1h.feather")

            staging = module.stage_aq_inputs(
                root,
                symbols=["NQ"],
                timeframe="1h",
                start="2021-01-01",
                end="2021-01-10",
                families=["dynamic_lead_lag_breadth_gate"],
            )

            aq_frame = pd.read_feather(staging["data"][0])
            sidecar_path = staging["dynamic_lead_lag_sidecars"][0]["strategy_sidecar_feather"]
            sidecar_frame = pd.read_feather(sidecar_path)

        self.assertEqual(list(aq_frame.columns), ["date", "open", "high", "low", "close", "volume"])
        self.assertIn("dll_leadlag_score_bps", sidecar_frame.columns)
        self.assertIn("dll_gc_score_bps", sidecar_frame.columns)
        self.assertNotIn("dll_xau_score_bps", sidecar_frame.columns)

    def test_residual_momentum_beta_neutral_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["residual_momentum_beta_neutral_parent_admission"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "ResidualMomentumBetaNeutralParentAdmission")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> ResidualMomentum -> BetaNeutralMarketModeRemoval -> ParentSignalAdmission",
        )
        self.assertEqual(
            spec.factor_id("1h"),
            "tomac_idxfut_clean_residual_momentum_beta_neutral_parent_admission_1h_v1",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_residual_momentum_beta_neutral_parent_admission_5m_v1",
                "tomac_idxfut_clean_residual_momentum_beta_neutral_parent_admission_15m_v1",
                "tomac_idxfut_clean_residual_momentum_beta_neutral_parent_admission_30m_v1",
                "tomac_idxfut_clean_residual_momentum_beta_neutral_parent_admission_1h_v1",
                "tomac_idxfut_clean_residual_momentum_beta_neutral_parent_admission_4h_v1",
                "tomac_idxfut_clean_residual_momentum_beta_neutral_parent_admission_1d_v1",
            ],
        )

    def test_residual_momentum_beta_neutral_source_uses_shifted_residual_admission(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["residual_momentum_beta_neutral_parent_admission"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="1h")

        self.assertIn("factor_id: tomac_idxfut_clean_residual_momentum_beta_neutral_parent_admission_1h_v1", source)
        self.assertIn("BetaNeutralMarketModeRemoval", source)
        self.assertIn("market_mode_return =", source)
        self.assertIn("rolling_beta_to_market_mode", source)
        self.assertIn("beta_neutral_residual_return", source)
        self.assertIn("residual_momentum_parent_admission_long.fillna(False)", source)
        self.assertIn("residual_momentum_parent_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_bocpd_runlength_transition_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["bocpd_runlength_transition_acceptance"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "BocpdRunlengthTransitionAcceptance")
        self.assertEqual(
            spec.branch_path,
            "RegimeRoot -> BayesianRunLengthState -> TransitionAcceptance -> TrendExpansionParentAdmission",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h")],
            [
                "tomac_idxfut_clean_bocpd_runlength_transition_acceptance_5m_v1",
                "tomac_idxfut_clean_bocpd_runlength_transition_acceptance_15m_v1",
                "tomac_idxfut_clean_bocpd_runlength_transition_acceptance_30m_v1",
                "tomac_idxfut_clean_bocpd_runlength_transition_acceptance_1h_v1",
            ],
        )

    def test_bocpd_runlength_transition_source_uses_shifted_runlength_admission(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["bocpd_runlength_transition_acceptance"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_idxfut_clean_bocpd_runlength_transition_acceptance_15m_v1", source)
        self.assertIn("BayesianRunLengthState", source)
        self.assertIn("bocpd_return_surprise", source)
        self.assertIn("bocpd_run_length_proxy", source)
        self.assertIn("bocpd_transition_probability_shifted", source)
        self.assertIn("bocpd_transition_parent_admission_long", source)
        self.assertIn("bocpd_transition_parent_admission_short", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_filtered_markov_trendexpansion_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["filtered_markov_trendexpansion_posterior_gate"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "FilteredMarkovTrendExpansionPosteriorGate")
        self.assertEqual(
            spec.branch_path,
            "RegimeTransition -> TrendExpansionOnly -> FilteredMarkovPosterior -> NextSegmentTrendExpansion",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("30m", "1h", "15m", "5m")],
            [
                "tomac_idxfut_clean_filtered_markov_trendexpansion_posterior_gate_30m_v1",
                "tomac_idxfut_clean_filtered_markov_trendexpansion_posterior_gate_1h_v1",
                "tomac_idxfut_clean_filtered_markov_trendexpansion_posterior_gate_15m_v1",
                "tomac_idxfut_clean_filtered_markov_trendexpansion_posterior_gate_5m_v1",
            ],
        )

    def test_filtered_markov_trendexpansion_source_uses_filtered_shifted_posterior(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["filtered_markov_trendexpansion_posterior_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("factor_id: tomac_idxfut_clean_filtered_markov_trendexpansion_posterior_gate_30m_v1", source)
        self.assertIn("FilteredMarkovPosterior", source)
        self.assertIn("markov_filtered_trend_probability", source)
        self.assertIn("markov_filtered_probability_shifted", source)
        self.assertIn("markov_next_segment_trendexpansion_long", source)
        self.assertIn("markov_next_segment_trendexpansion_short", source)
        self.assertNotIn("markov_smoothed", source.lower())
        self.assertNotIn("markov_backfilled", source.lower())
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_terminal_packet_preserves_staged_strategy_identity_without_survivor_rows(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "run"
            compact_root = Path(tmpdir) / "compact"
            summary = {
                "symbols": ["NQ"],
                "timeframes": ["5m", "15m", "30m", "1h"],
                "families": ["bocpd_runlength_transition_acceptance"],
                "future_leakage_policy": {"uses_shift_negative": False},
                "aq_staging": [
                    {
                        "strategy_specs": [
                            {
                                "class_name": "TomacNQBocpdRunlengthTransitionAcceptanceFifteenMinCleanV1",
                                "symbol": "NQ",
                                "timeframe": "15m",
                                "factor_id": "tomac_idxfut_clean_bocpd_runlength_transition_acceptance_15m_v1",
                                "branch_path": (
                                    "RegimeRoot -> BayesianRunLengthState -> TransitionAcceptance -> "
                                    "TrendExpansionParentAdmission -> "
                                    "tomac_idxfut_clean_bocpd_runlength_transition_acceptance_15m_v1"
                                ),
                                "family": "bocpd_runlength_transition_acceptance",
                                "direction": "long_short",
                            }
                        ]
                    }
                ],
                "aq_gate_summaries": [
                    {
                        "timeframe": "15m",
                        "decision": "observation_no_autoquant_survivor_yet",
                        "rank_rows": 2,
                        "survivors_instrument_cost": [],
                        "raw_survivors_before_session_scope": [],
                        "command": {"exit": 0, "timed_out": False},
                        "session_scope": "ETH/full_retained_session",
                        "rth_filter_applied": False,
                        "eth_full_retained_session_evidence": True,
                        "data_provenance": {},
                    }
                ],
            }

            module.write_terminal_regime_feedback_packets(root, compact_root, summary)

            terminal = json.loads((root / "summaries" / "terminal_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(
                terminal["factor_id"],
                "tomac_idxfut_clean_bocpd_runlength_transition_acceptance_15m_v1",
            )
            self.assertEqual(
                terminal["branch_path"],
                "RegimeRoot -> BayesianRunLengthState -> TransitionAcceptance -> "
                "TrendExpansionParentAdmission -> tomac_idxfut_clean_bocpd_runlength_transition_acceptance_15m_v1",
            )
            self.assertEqual(terminal["factor_family"], "bocpd_runlength_transition_acceptance")
            self.assertEqual(terminal["aq_result"]["representative_row"]["direction"], "long_short")

    def test_elder_thermometer_heat_rejoin_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["elder_thermometer_heat_rejoin"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "ElderThermometerHeatRejoin")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> MarketThermometerHeat -> HeatNormalizedTrendRejoin",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_elder_thermometer_heat_rejoin_5m_v1",
                "tomac_idxfut_clean_elder_thermometer_heat_rejoin_15m_v1",
                "tomac_idxfut_clean_elder_thermometer_heat_rejoin_30m_v1",
                "tomac_idxfut_clean_elder_thermometer_heat_rejoin_1h_v1",
                "tomac_idxfut_clean_elder_thermometer_heat_rejoin_4h_v1",
                "tomac_idxfut_clean_elder_thermometer_heat_rejoin_1d_v1",
            ],
        )

    def test_elder_thermometer_heat_rejoin_source_uses_shifted_heat_admission(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["elder_thermometer_heat_rejoin"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_idxfut_clean_elder_thermometer_heat_rejoin_15m_v1", source)
        self.assertIn("MarketThermometerHeat", source)
        self.assertIn("elder_thermometer_heat", source)
        self.assertIn("elder_thermometer_heat_ratio_shifted", source)
        self.assertIn("heat_normalized_rejoin_long.fillna(False)", source)
        self.assertIn("heat_normalized_rejoin_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_pgo_atr_trend_rejoin_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["pgo_atr_trend_rejoin"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "PgoAtrTrendRejoin")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> AtrNormalizedDeviationState -> PrettyGoodOscillatorTrendRejoin -> MtfSlopeResonanceGuard",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_pgo_atr_trend_rejoin_5m_v1",
                "tomac_idxfut_clean_pgo_atr_trend_rejoin_15m_v1",
                "tomac_idxfut_clean_pgo_atr_trend_rejoin_30m_v1",
                "tomac_idxfut_clean_pgo_atr_trend_rejoin_1h_v1",
                "tomac_idxfut_clean_pgo_atr_trend_rejoin_4h_v1",
                "tomac_idxfut_clean_pgo_atr_trend_rejoin_1d_v1",
            ],
        )

    def test_pgo_atr_trend_rejoin_source_uses_shifted_pgo_admission(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["pgo_atr_trend_rejoin"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("factor_id: tomac_idxfut_clean_pgo_atr_trend_rejoin_30m_v1", source)
        self.assertIn("AtrNormalizedDeviationState", source)
        self.assertIn("pgo_atr_deviation", source)
        self.assertIn("pgo_rejoin_impulse_shifted", source)
        self.assertIn("pgo_atr_trend_rejoin_long.fillna(False)", source)
        self.assertIn("pgo_atr_trend_rejoin_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_gann_hilo_atr_trend_rejoin_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["gann_hilo_atr_trend_rejoin_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "GannHiLoAtrTrendRejoinFilter")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> GannHiLoActivatorState -> AtrTrendRejoin -> MtfTrendResonance",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_gann_hilo_atr_trend_rejoin_filter_5m_v1",
                "tomac_idxfut_clean_gann_hilo_atr_trend_rejoin_filter_15m_v1",
                "tomac_idxfut_clean_gann_hilo_atr_trend_rejoin_filter_30m_v1",
                "tomac_idxfut_clean_gann_hilo_atr_trend_rejoin_filter_1h_v1",
                "tomac_idxfut_clean_gann_hilo_atr_trend_rejoin_filter_4h_v1",
                "tomac_idxfut_clean_gann_hilo_atr_trend_rejoin_filter_1d_v1",
            ],
        )

    def test_gann_hilo_atr_trend_rejoin_source_uses_shifted_hilo_admission(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["gann_hilo_atr_trend_rejoin_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_idxfut_clean_gann_hilo_atr_trend_rejoin_filter_15m_v1", source)
        self.assertIn("GannHiLoActivatorState", source)
        self.assertIn("gann_hilo_high_shifted", source)
        self.assertIn("gann_hilo_low_shifted", source)
        self.assertIn("gann_hilo_activator_state", source)
        self.assertIn("gann_hilo_atr_rejoin_long.fillna(False)", source)
        self.assertIn("gann_hilo_atr_rejoin_short.fillna(False)", source)
        self.assertIn("mtf_gann_hilo_rejoin_long.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_jolts_labor_tightness_regime_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["jolts_labor_tightness_regime_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "JoltsLaborTightnessRegimeFilter")
        self.assertEqual(
            spec.branch_path,
            "MacroLaborRegime -> JoltsLaborTightness -> RiskOnOffAdmissionFilter",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_jolts_labor_tightness_regime_filter_5m_v1",
                "tomac_idxfut_clean_jolts_labor_tightness_regime_filter_15m_v1",
                "tomac_idxfut_clean_jolts_labor_tightness_regime_filter_30m_v1",
                "tomac_idxfut_clean_jolts_labor_tightness_regime_filter_1h_v1",
                "tomac_idxfut_clean_jolts_labor_tightness_regime_filter_4h_v1",
                "tomac_idxfut_clean_jolts_labor_tightness_regime_filter_1d_v1",
            ],
        )

    def test_jolts_labor_tightness_regime_source_uses_shifted_macro_admission(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["jolts_labor_tightness_regime_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("factor_id: tomac_idxfut_clean_jolts_labor_tightness_regime_filter_30m_v1", source)
        self.assertIn("JoltsLaborTightness", source)
        self.assertIn("job_openings_to_unemployed_proxy", source)
        self.assertIn("jolts_labor_tightness_release_lag_ok", source)
        self.assertIn("labor_tightness_risk_on_admission_long.fillna(False)", source)
        self.assertIn("labor_tightness_risk_off_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_jdk_relative_rotation_regime_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["jdk_relative_rotation_regime_gate"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "JdkRelativeRotationRegimeGate")
        self.assertEqual(
            spec.branch_path,
            "CrossMarketStructure -> RelativeRotationGraph -> RSRatioRSMomentumQuadrant -> LeadershipTransitionGate",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_jdk_relative_rotation_regime_gate_5m_v1",
                "tomac_idxfut_clean_jdk_relative_rotation_regime_gate_15m_v1",
                "tomac_idxfut_clean_jdk_relative_rotation_regime_gate_30m_v1",
                "tomac_idxfut_clean_jdk_relative_rotation_regime_gate_1h_v1",
                "tomac_idxfut_clean_jdk_relative_rotation_regime_gate_4h_v1",
                "tomac_idxfut_clean_jdk_relative_rotation_regime_gate_1d_v1",
            ],
        )

    def test_jdk_relative_rotation_regime_source_uses_shifted_cross_market_sidecar(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["jdk_relative_rotation_regime_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_idxfut_clean_jdk_relative_rotation_regime_gate_15m_v1", source)
        self.assertIn("RelativeRotationGraph", source)
        self.assertIn("jdk_leadership_constructive", source)
        self.assertIn("jdk_leadership_defensive", source)
        self.assertIn("jdk_rs_ratio", source)
        self.assertIn("jdk_rs_momentum", source)
        self.assertIn("relative_rotation_rejoin_long.fillna(False)", source)
        self.assertIn("relative_rotation_rejoin_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_jdk_relative_rotation_sidecar_materializes_cross_market_columns(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dates = pd.date_range("2025-01-01T00:00:00Z", periods=220, freq="15min")
            close_shapes = {
                "NQ": [100.0 + index * 0.08 for index in range(len(dates))],
                "YM": [100.0 + index * 0.03 for index in range(len(dates))],
                "GC": [100.0 - index * 0.01 for index in range(len(dates))],
            }
            for symbol, closes in close_shapes.items():
                clean_dir = root / "clean" / symbol
                clean_dir.mkdir(parents=True)
                pd.DataFrame(
                    {
                        "date": dates,
                        "open": closes,
                        "high": [value + 0.5 for value in closes],
                        "low": [value - 0.5 for value in closes],
                        "close": closes,
                        "volume": [100.0 + index for index in range(len(dates))],
                    }
                ).to_feather(clean_dir / f"{symbol}_USD-15m.feather")

            frame = pd.read_feather(root / "clean" / "NQ" / "NQ_USD-15m.feather")
            merged, stats = module.merge_jdk_relative_rotation_sidecar(
                frame,
                root,
                symbol="NQ",
                timeframe="15m",
                symbols=["NQ", "YM", "GC"],
            )

            self.assertEqual(stats["status"], "materialized")
            self.assertFalse(stats["future_lookahead"])
            self.assertGreater(stats["non_null_rs_ratio_rows"], 0)
            for column in (
                "jdk_rs_ratio",
                "jdk_rs_momentum",
                "jdk_relative_leading",
                "jdk_relative_improving",
                "jdk_relative_weakening",
                "jdk_relative_lagging",
                "jdk_leadership_constructive",
                "jdk_leadership_defensive",
                "jdk_rotation_persistence",
            ):
                self.assertIn(column, merged.columns)
            self.assertEqual(merged["jdk_rotation_sidecar_symbol"].dropna().unique().tolist(), ["NQ"])
            self.assertEqual(merged["jdk_rotation_sidecar_timeframe"].dropna().unique().tolist(), ["15m"])
            self.assertEqual(merged["jdk_rotation_sidecar_symbols"].dropna().unique().tolist(), ["NQ,YM,GC"])

    def test_stage_aq_inputs_materializes_jdk_relative_rotation_sidecar_for_family(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dates = pd.date_range("2025-01-01T00:00:00Z", periods=220, freq="15min")
            for offset, symbol in enumerate(("NQ", "YM", "GC")):
                clean_dir = root / "clean" / symbol
                clean_dir.mkdir(parents=True)
                closes = [100.0 + offset + index * (0.08 - offset * 0.03) for index in range(len(dates))]
                pd.DataFrame(
                    {
                        "date": dates,
                        "open": closes,
                        "high": [value + 0.5 for value in closes],
                        "low": [value - 0.5 for value in closes],
                        "close": closes,
                        "volume": [100.0 + index for index in range(len(dates))],
                    }
                ).to_feather(clean_dir / f"{symbol}_USD-15m.feather")

            staged = module.stage_aq_inputs(
                root,
                symbols=["NQ", "YM", "GC"],
                timeframe="15m",
                start="2025-01-01",
                end="2025-01-03",
                families=["jdk_relative_rotation_regime_gate"],
            )

            staged_frame = pd.read_feather(staged["data"][0])
            self.assertIn("jdk_rs_ratio", staged_frame.columns)
            self.assertIn("jdk_leadership_constructive", staged_frame.columns)
            self.assertEqual(len(staged["jdk_relative_rotation_sidecars"]), 3)
            self.assertTrue(all(item["status"] == "materialized" for item in staged["jdk_relative_rotation_sidecars"]))
            self.assertEqual(staged["strategy_specs"][0]["family"], "jdk_relative_rotation_regime_gate")

    def test_macd_cross_regime_trigger_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["macd_cross_regime_trigger"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "MacdCrossRegimeTrigger")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> MacdCrossRegimeTrigger -> GoldDeadCrossStateSwitch",
        )
        self.assertEqual(
            spec.factor_id("15m"),
            "tomac_idxfut_clean_macd_cross_regime_trigger_15m_v1",
        )
        self.assertEqual(
            spec.factor_id("1d"),
            "tomac_idxfut_clean_macd_cross_regime_trigger_1d_v1",
        )

    def test_macd_cross_regime_trigger_strategy_uses_cross_state_not_divergence(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["macd_cross_regime_trigger"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_idxfut_clean_macd_cross_regime_trigger_15m_v1", source)
        self.assertIn("GoldDeadCrossStateSwitch", source)
        self.assertIn("golden_cross", source)
        self.assertIn("death_cross", source)
        self.assertIn("trend_expansion_long", source)
        self.assertIn("trend_breakdown_short", source)
        self.assertIn("compression_release_long", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "macd_cross_regime_trigger" == "macd_cross_regime_trigger":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        macd_cross_block = source[branch_start:next_branch]
        self.assertNotIn("macd_divergence", macd_cross_block)
        self.assertNotIn("midnight_open", macd_cross_block)

    def test_macd_failed_cross_trap_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["macd_failed_cross_trap_reversal"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "MacdFailedCrossTrapReversal")
        self.assertEqual(
            spec.branch_path,
            "RangeTransition -> MacdFailedCrossTrap -> FailedGoldDeadCrossTrapReversal",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_macd_failed_cross_trap_reversal_5m_v1",
                "tomac_idxfut_clean_macd_failed_cross_trap_reversal_15m_v1",
                "tomac_idxfut_clean_macd_failed_cross_trap_reversal_30m_v1",
                "tomac_idxfut_clean_macd_failed_cross_trap_reversal_1h_v1",
                "tomac_idxfut_clean_macd_failed_cross_trap_reversal_4h_v1",
                "tomac_idxfut_clean_macd_failed_cross_trap_reversal_1d_v1",
            ],
        )

    def test_macd_failed_cross_trap_strategy_uses_failed_cross_windows(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["macd_failed_cross_trap_reversal"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("factor_id: tomac_idxfut_clean_macd_failed_cross_trap_reversal_30m_v1", source)
        self.assertIn("FailedGoldDeadCrossTrapReversal", source)
        self.assertIn("failed_death_cross_window", source)
        self.assertIn("failed_golden_cross_window", source)
        self.assertIn("death_cross_trap_reclaim", source)
        self.assertIn("golden_cross_trap_breakdown", source)
        self.assertIn("higher_timeframe_hist_not_bearish", source)
        self.assertIn("higher_timeframe_hist_not_bullish", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "macd_failed_cross_trap_reversal" == "macd_failed_cross_trap_reversal":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        failed_cross_block = source[branch_start:next_branch]
        self.assertNotIn("macd_divergence", failed_cross_block)
        self.assertNotIn("midnight_open", failed_cross_block)
        self.assertNotIn("compression_release_long", failed_cross_block)

    def test_macd_failed_cross_trap_mtf_resonance_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["macd_failed_cross_trap_mtf_resonance"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "MacdFailedCrossTrapMtfResonance")
        self.assertEqual(
            spec.branch_path,
            "RangeTransition -> MacdFailedCrossTrap -> FailedGoldDeadCrossTrapReversal -> MtfHistogramSlopeResonance",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_macd_failed_cross_trap_mtf_resonance_5m_v1",
                "tomac_idxfut_clean_macd_failed_cross_trap_mtf_resonance_15m_v1",
                "tomac_idxfut_clean_macd_failed_cross_trap_mtf_resonance_30m_v1",
                "tomac_idxfut_clean_macd_failed_cross_trap_mtf_resonance_1h_v1",
                "tomac_idxfut_clean_macd_failed_cross_trap_mtf_resonance_4h_v1",
                "tomac_idxfut_clean_macd_failed_cross_trap_mtf_resonance_1d_v1",
            ],
        )

    def test_macd_failed_cross_trap_mtf_resonance_strategy_uses_mtf_histogram_slope_resonance(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["macd_failed_cross_trap_mtf_resonance"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="1h")

        self.assertIn("factor_id: tomac_idxfut_clean_macd_failed_cross_trap_mtf_resonance_1h_v1", source)
        self.assertIn("MtfHistogramSlopeResonance", source)
        self.assertIn("failed_death_cross_window", source)
        self.assertIn("failed_golden_cross_window", source)
        self.assertIn("mtf_histogram_slope_resonance_long", source)
        self.assertIn("mtf_histogram_slope_resonance_short", source)
        self.assertIn("macd_hist_acceleration", source)
        self.assertIn("slope_4h", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "macd_failed_cross_trap_mtf_resonance" == "macd_failed_cross_trap_mtf_resonance":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        mtf_resonance_block = source[branch_start:next_branch]
        self.assertNotIn("macd_divergence", mtf_resonance_block)
        self.assertNotIn("midnight_open", mtf_resonance_block)
        self.assertNotIn("compression_release_long", mtf_resonance_block)

    def test_matrix_profile_motif_discord_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["matrix_profile_motif_discord_admission_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "MatrixProfileMotifDiscordAdmissionFilter")
        self.assertEqual(
            spec.branch_path,
            "ValidationMaturity -> MatrixProfileMotifDiscord -> ParentSignalSimilarityAdmission -> DiscordVetoTrendAdmission",
        )
        self.assertEqual(
            spec.factor_id("1m"),
            "tomac_idxfut_clean_matrix_profile_motif_discord_admission_filter_1m_v1",
        )

    def test_matrix_profile_motif_discord_strategy_source_uses_shifted_discord_veto(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["matrix_profile_motif_discord_admission_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_matrix_profile_motif_discord_admission_filter_1m_v1",
            source,
        )
        self.assertIn("MatrixProfileMotifDiscord", source)
        self.assertIn("rolling_subsequence_return", source)
        self.assertIn("matrix_profile_distance_z", source)
        self.assertIn("motif_similarity_admission_long.fillna(False)", source)
        self.assertIn("discord_veto", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)

    def test_sax_symbolic_aggregate_word_shift_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["sax_symbolic_aggregate_word_shift_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "SaxSymbolicAggregateWordShiftFilter")
        self.assertEqual(
            spec.branch_path,
            "RangeTransition -> SymbolicWordShift -> SaxMotifDiscordAdmissionFilter -> ParentSignalAdmissionFilter",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_sax_symbolic_aggregate_word_shift_filter_5m_v1",
                "tomac_idxfut_clean_sax_symbolic_aggregate_word_shift_filter_15m_v1",
                "tomac_idxfut_clean_sax_symbolic_aggregate_word_shift_filter_30m_v1",
                "tomac_idxfut_clean_sax_symbolic_aggregate_word_shift_filter_1h_v1",
                "tomac_idxfut_clean_sax_symbolic_aggregate_word_shift_filter_4h_v1",
                "tomac_idxfut_clean_sax_symbolic_aggregate_word_shift_filter_1d_v1",
            ],
        )

    def test_sax_symbolic_aggregate_word_shift_strategy_source_uses_shifted_word_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["sax_symbolic_aggregate_word_shift_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_idxfut_clean_sax_symbolic_aggregate_word_shift_filter_15m_v1", source)
        self.assertIn("SymbolicWordShift", source)
        self.assertIn("sax_return_symbol_shifted", source)
        self.assertIn("sax_range_symbol_shifted", source)
        self.assertIn("sax_word_code", source)
        self.assertIn("sax_word_rarity", source)
        self.assertIn("sax_motif_churn", source)
        self.assertIn("sax_directional_word_transition", source)
        self.assertIn("sax_symbolic_word_admission_long.fillna(False)", source)
        self.assertIn("sax_symbolic_word_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_chande_forecast_oscillator_half_life_reversion_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["chande_forecast_oscillator_half_life_reversion_gate"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "ChandeForecastOscillatorHalfLifeReversionGate")
        self.assertEqual(
            spec.branch_path,
            "MeanReversion -> ForecastErrorOscillator -> ChandeForecastDeviation -> HalfLifeReversionAdmission",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_chande_forecast_oscillator_half_life_reversion_gate_5m_v1",
                "tomac_idxfut_clean_chande_forecast_oscillator_half_life_reversion_gate_15m_v1",
                "tomac_idxfut_clean_chande_forecast_oscillator_half_life_reversion_gate_30m_v1",
                "tomac_idxfut_clean_chande_forecast_oscillator_half_life_reversion_gate_1h_v1",
                "tomac_idxfut_clean_chande_forecast_oscillator_half_life_reversion_gate_4h_v1",
                "tomac_idxfut_clean_chande_forecast_oscillator_half_life_reversion_gate_1d_v1",
            ],
        )

    def test_chande_forecast_oscillator_half_life_reversion_strategy_source_uses_shifted_forecast_error(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["chande_forecast_oscillator_half_life_reversion_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_chande_forecast_oscillator_half_life_reversion_gate_30m_v1",
            source,
        )
        self.assertIn("ForecastErrorOscillator", source)
        self.assertIn("chande_forecast_endpoint", source)
        self.assertIn("chande_forecast_oscillator", source)
        self.assertIn("chande_forecast_error_half_life", source)
        self.assertIn("forecast_error_reversion_pressure", source)
        self.assertIn("chande_forecast_half_life_reversion_long.fillna(False)", source)
        self.assertIn("chande_forecast_half_life_reversion_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_score_driven_gas_state_admission_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["score_driven_gas_state_admission_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "ScoreDrivenGasStateAdmissionFilter")
        self.assertEqual(
            spec.branch_path,
            "ValidationMaturity -> ObservationDrivenState -> ScoreDrivenGASFilter -> ParentSignalAdmissionFilter",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_score_driven_gas_state_admission_filter_5m_v1",
                "tomac_idxfut_clean_score_driven_gas_state_admission_filter_15m_v1",
                "tomac_idxfut_clean_score_driven_gas_state_admission_filter_30m_v1",
                "tomac_idxfut_clean_score_driven_gas_state_admission_filter_1h_v1",
                "tomac_idxfut_clean_score_driven_gas_state_admission_filter_4h_v1",
                "tomac_idxfut_clean_score_driven_gas_state_admission_filter_1d_v1",
            ],
        )

    def test_score_driven_gas_state_admission_strategy_source_uses_shifted_gas_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["score_driven_gas_state_admission_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_score_driven_gas_state_admission_filter_15m_v1",
            source,
        )
        self.assertIn("ObservationDrivenState", source)
        self.assertIn("gas_location_score", source)
        self.assertIn("gas_scale_state", source)
        self.assertIn("gas_tail_pressure", source)
        self.assertIn("score_driven_parent_admission_long.fillna(False)", source)
        self.assertIn("score_driven_parent_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "score_driven_gas_state_admission_filter" == "score_driven_gas_state_admission_filter":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        gas_block = source[branch_start:next_branch]
        self.assertNotIn("shift(-", gas_block)
        self.assertNotIn("bps_per_side", gas_block)
        self.assertNotIn("cost_bps", gas_block)

    def test_trend_intensity_index_reacceleration_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["trend_intensity_index_reacceleration_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "TrendIntensityIndexReaccelerationFilter")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> TrendIntensityIndex -> ReaccelerationAfterPullback -> ParentTrendAdmissionFilter",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_trend_intensity_index_reacceleration_filter_5m_v1",
                "tomac_idxfut_clean_trend_intensity_index_reacceleration_filter_15m_v1",
                "tomac_idxfut_clean_trend_intensity_index_reacceleration_filter_30m_v1",
                "tomac_idxfut_clean_trend_intensity_index_reacceleration_filter_1h_v1",
                "tomac_idxfut_clean_trend_intensity_index_reacceleration_filter_4h_v1",
                "tomac_idxfut_clean_trend_intensity_index_reacceleration_filter_1d_v1",
            ],
        )

    def test_trend_intensity_index_reacceleration_strategy_source_uses_shifted_tii_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["trend_intensity_index_reacceleration_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_trend_intensity_index_reacceleration_filter_15m_v1",
            source,
        )
        self.assertIn("TrendIntensityIndex", source)
        self.assertIn("trend_intensity_index_value", source)
        self.assertIn("trend_intensity_reacceleration_long.fillna(False)", source)
        self.assertIn("trend_intensity_reacceleration_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "trend_intensity_index_reacceleration_filter" == "trend_intensity_index_reacceleration_filter":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        tii_block = source[branch_start:next_branch]
        self.assertNotIn("shift(-", tii_block)
        self.assertNotIn("bps_per_side", tii_block)
        self.assertNotIn("cost_bps", tii_block)

    def test_tsmom_vol_scaled_low_turnover_rrr_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["tsmom_vol_scaled_low_turnover_rrr"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "TsmomVolScaledLowTurnoverRrr")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> TimeSeriesMomentum -> VolScaledLowTurnoverHold -> FixedRrrContinuation -> SourceBackedMopHurstPedersen",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_tsmom_vol_scaled_low_turnover_rrr_5m_v1",
                "tomac_idxfut_clean_tsmom_vol_scaled_low_turnover_rrr_15m_v1",
                "tomac_idxfut_clean_tsmom_vol_scaled_low_turnover_rrr_30m_v1",
                "tomac_idxfut_clean_tsmom_vol_scaled_low_turnover_rrr_1h_v1",
                "tomac_idxfut_clean_tsmom_vol_scaled_low_turnover_rrr_4h_v1",
                "tomac_idxfut_clean_tsmom_vol_scaled_low_turnover_rrr_1d_v1",
            ],
        )

    def test_tsmom_vol_scaled_low_turnover_rrr_strategy_source_uses_shifted_source_backed_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["tsmom_vol_scaled_low_turnover_rrr"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="1h")

        self.assertIn("factor_id: tomac_idxfut_clean_tsmom_vol_scaled_low_turnover_rrr_1h_v1", source)
        self.assertIn("TimeSeriesMomentum", source)
        self.assertIn("tsmom_return_55_shifted", source)
        self.assertIn("tsmom_return_144_shifted", source)
        self.assertIn("tsmom_vol_scaled_score", source)
        self.assertIn("tsmom_low_turnover_hold_state", source)
        self.assertIn("tsmom_low_turnover_friction_window.fillna(False)", source)
        self.assertIn("tsmom_trend_decay_long.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "tsmom_vol_scaled_low_turnover_rrr" == "tsmom_vol_scaled_low_turnover_rrr":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        tsmom_block = source[branch_start:next_branch]
        self.assertNotIn("shift(-", tsmom_block)
        self.assertNotIn("bps_per_side", tsmom_block)
        self.assertNotIn("cost_bps", tsmom_block)

    def test_dss_bressert_reacceleration_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["dss_bressert_reacceleration_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "DssBressertReaccelerationFilter")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> DoubleSmoothedStochasticState -> PullbackReacceleration -> MtfTrendResonance -> FrictionAwareAtrHold",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_dss_bressert_reacceleration_filter_5m_v1",
                "tomac_idxfut_clean_dss_bressert_reacceleration_filter_15m_v1",
                "tomac_idxfut_clean_dss_bressert_reacceleration_filter_30m_v1",
                "tomac_idxfut_clean_dss_bressert_reacceleration_filter_1h_v1",
                "tomac_idxfut_clean_dss_bressert_reacceleration_filter_4h_v1",
                "tomac_idxfut_clean_dss_bressert_reacceleration_filter_1d_v1",
            ],
        )

    def test_dss_bressert_reacceleration_strategy_source_uses_shifted_dss_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["dss_bressert_reacceleration_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_dss_bressert_reacceleration_filter_15m_v1",
            source,
        )
        self.assertIn("DoubleSmoothedStochasticState", source)
        self.assertIn("dss_bressert_value_shifted", source)
        self.assertIn("dss_bressert_reacceleration_long.fillna(False)", source)
        self.assertIn("dss_bressert_reacceleration_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "dss_bressert_reacceleration_filter" == "dss_bressert_reacceleration_filter":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        dss_block = source[branch_start:next_branch]
        self.assertNotIn("shift(-", dss_block)
        self.assertNotIn("bps_per_side", dss_block)
        self.assertNotIn("cost_bps", dss_block)

    def test_local_polynomial_curvature_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["local_polynomial_curvature_acceleration_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "LocalPolynomialCurvatureAccelerationFilter")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> LocalPolynomialTrendGeometry -> CurvatureAccelerationState -> ParentTrendAdmission",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_local_polynomial_curvature_acceleration_filter_5m_v1",
                "tomac_idxfut_clean_local_polynomial_curvature_acceleration_filter_15m_v1",
                "tomac_idxfut_clean_local_polynomial_curvature_acceleration_filter_30m_v1",
                "tomac_idxfut_clean_local_polynomial_curvature_acceleration_filter_1h_v1",
                "tomac_idxfut_clean_local_polynomial_curvature_acceleration_filter_4h_v1",
                "tomac_idxfut_clean_local_polynomial_curvature_acceleration_filter_1d_v1",
            ],
        )

    def test_local_polynomial_curvature_strategy_source_uses_shifted_curvature_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["local_polynomial_curvature_acceleration_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_local_polynomial_curvature_acceleration_filter_30m_v1",
            source,
        )
        self.assertIn("LocalPolynomialTrendGeometry", source)
        self.assertIn("local_poly_slope_bps_55", source)
        self.assertIn("local_poly_curvature_bps_55", source)
        self.assertIn("curvature_acceleration_state_long.fillna(False)", source)
        self.assertIn("curvature_acceleration_state_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "local_polynomial_curvature_acceleration_filter" == "local_polynomial_curvature_acceleration_filter":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        curvature_block = source[branch_start:next_branch]
        self.assertNotIn("shift(-", curvature_block)

    def test_qqe_rsi_trend_quality_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["qqe_rsi_trend_quality_reacceleration_gate"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "QqeRsiTrendQualityReaccelerationGate")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> MomentumSmoothing -> QQERSITrendQuality -> ReaccelerationAfterPullback -> MtfSlopeResonance -> FrictionAwareAtrHold",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_qqe_rsi_trend_quality_reacceleration_gate_5m_v1",
                "tomac_idxfut_clean_qqe_rsi_trend_quality_reacceleration_gate_15m_v1",
                "tomac_idxfut_clean_qqe_rsi_trend_quality_reacceleration_gate_30m_v1",
                "tomac_idxfut_clean_qqe_rsi_trend_quality_reacceleration_gate_1h_v1",
                "tomac_idxfut_clean_qqe_rsi_trend_quality_reacceleration_gate_4h_v1",
                "tomac_idxfut_clean_qqe_rsi_trend_quality_reacceleration_gate_1d_v1",
            ],
        )

    def test_qqe_rsi_trend_quality_strategy_source_uses_shifted_reacceleration_gate(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["qqe_rsi_trend_quality_reacceleration_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="1h")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_qqe_rsi_trend_quality_reacceleration_gate_1h_v1",
            source,
        )
        self.assertIn("QQERSITrendQuality", source)
        self.assertIn("qqe_fast_trailing_band", source)
        self.assertIn("qqe_slow_trailing_band", source)
        self.assertIn("qqe_reacceleration_after_pullback_long.fillna(False)", source)
        self.assertIn("qqe_reacceleration_after_pullback_short.fillna(False)", source)
        self.assertIn("mtf_slope_resonance_long.fillna(False)", source)
        self.assertIn("mtf_slope_resonance_short.fillna(False)", source)
        self.assertIn("friction_aware_atr_hold.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "qqe_rsi_trend_quality_reacceleration_gate" == "qqe_rsi_trend_quality_reacceleration_gate":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        qqe_block = source[branch_start:next_branch]
        self.assertNotIn("shift(-", qqe_block)

    def test_visibility_graph_trend_persistence_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["visibility_graph_trend_persistence_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "VisibilityGraphTrendPersistenceFilter")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> SequenceTopology -> VisibilityGraphTrendPersistence -> ParentSignalAdmissionFilter",
        )
        self.assertEqual(
            spec.factor_id("1m"),
            "tomac_idxfut_clean_visibility_graph_trend_persistence_filter_1m_v1",
        )

    def test_visibility_graph_trend_persistence_strategy_source_uses_shifted_graph_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["visibility_graph_trend_persistence_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn("factor_id: tomac_idxfut_clean_visibility_graph_trend_persistence_filter_1m_v1", source)
        self.assertIn("VisibilityGraphTrendPersistence", source)
        self.assertIn("visibility_graph_degree_asymmetry", source)
        self.assertIn("visibility_graph_persistence_ratio", source)
        self.assertIn("graph_persistence_admission_long.fillna(False)", source)
        self.assertIn("graph_noise_veto", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)

    def test_correlation_network_centrality_risk_gate_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["correlation_network_centrality_risk_gate"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "CorrelationNetworkCentralityRiskGate")
        self.assertEqual(spec.direction, "long_short")
        self.assertFalse(spec.supports(symbol="NQ", timeframe="1m"))
        self.assertTrue(spec.supports(symbol="NQ", timeframe="5m"))
        self.assertEqual(
            spec.branch_path,
            "CrossMarketStructure -> CorrelationNetworkTopology -> MstCentralityCrowdingState -> ParentTrendAdmissionFilter",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_correlation_network_centrality_risk_gate_5m_v1",
                "tomac_idxfut_clean_correlation_network_centrality_risk_gate_15m_v1",
                "tomac_idxfut_clean_correlation_network_centrality_risk_gate_30m_v1",
                "tomac_idxfut_clean_correlation_network_centrality_risk_gate_1h_v1",
                "tomac_idxfut_clean_correlation_network_centrality_risk_gate_4h_v1",
                "tomac_idxfut_clean_correlation_network_centrality_risk_gate_1d_v1",
            ],
        )

    def test_correlation_network_centrality_risk_gate_strategy_source_uses_shifted_completed_bar_network_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["correlation_network_centrality_risk_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_idxfut_clean_correlation_network_centrality_risk_gate_15m_v1", source)
        self.assertIn("CorrelationNetworkTopology", source)
        self.assertIn("MstCentralityCrowdingState", source)
        self.assertIn("correlation_network_distance_proxy", source)
        self.assertIn("mst_centrality_crowding_state_shifted", source)
        self.assertIn("market_mode_compression_shifted", source)
        self.assertIn("correlation_network_parent_trend_admission_long", source)
        self.assertIn("correlation_network_parent_trend_admission_short", source)
        self.assertIn("network_crowding_veto", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "correlation_network_centrality_risk_gate" == "correlation_network_centrality_risk_gate":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        correlation_network_block = source[branch_start:next_branch]
        self.assertNotIn("shift(-", correlation_network_block)

    def test_sprt_sequential_likelihood_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["sprt_sequential_likelihood_trend_confirmation_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "SprtSequentialLikelihoodTrendConfirmationFilter")
        self.assertEqual(
            spec.branch_path,
            "ValidationMaturity -> SequentialEvidence -> SprtLikelihoodTrendConfirmation -> ParentSignalAdmissionFilter",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_sprt_sequential_likelihood_trend_confirmation_filter_5m_v1",
                "tomac_idxfut_clean_sprt_sequential_likelihood_trend_confirmation_filter_15m_v1",
                "tomac_idxfut_clean_sprt_sequential_likelihood_trend_confirmation_filter_30m_v1",
                "tomac_idxfut_clean_sprt_sequential_likelihood_trend_confirmation_filter_1h_v1",
                "tomac_idxfut_clean_sprt_sequential_likelihood_trend_confirmation_filter_4h_v1",
                "tomac_idxfut_clean_sprt_sequential_likelihood_trend_confirmation_filter_1d_v1",
            ],
        )

    def test_sprt_sequential_likelihood_strategy_source_uses_shifted_llr_admission(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["sprt_sequential_likelihood_trend_confirmation_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_sprt_sequential_likelihood_trend_confirmation_filter_15m_v1",
            source,
        )
        self.assertIn("SprtLikelihoodTrendConfirmation", source)
        self.assertIn("sprt_completed_bar_evidence", source)
        self.assertIn("sprt_log_likelihood_ratio", source)
        self.assertIn("sprt_accept_boundary", source)
        self.assertIn("sprt_reject_boundary", source)
        self.assertIn("sprt_parent_signal_admission_long.fillna(False)", source)
        self.assertIn("sprt_parent_signal_admission_short.fillna(False)", source)
        self.assertIn("sprt_cooldown_veto", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "sprt_sequential_likelihood_trend_confirmation_filter" == "sprt_sequential_likelihood_trend_confirmation_filter":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        sprt_block = source[branch_start:next_branch]
        self.assertNotIn("shift(-", sprt_block)

    def test_shiryaev_roberts_quickest_change_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["shiryaev_roberts_quickest_change_persistence_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "ShiryaevRobertsQuickestChangePersistenceFilter")
        self.assertEqual(
            spec.branch_path,
            "ValidationMaturity -> QuickestChangeDetection -> ShiryaevRobertsPersistence -> ParentSignalAdmissionFilter",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertFalse(spec.supports(symbol="NQ", timeframe="1m"))
        self.assertTrue(spec.supports(symbol="NQ", timeframe="5m"))
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_shiryaev_roberts_quickest_change_persistence_filter_5m_v1",
                "tomac_idxfut_clean_shiryaev_roberts_quickest_change_persistence_filter_15m_v1",
                "tomac_idxfut_clean_shiryaev_roberts_quickest_change_persistence_filter_30m_v1",
                "tomac_idxfut_clean_shiryaev_roberts_quickest_change_persistence_filter_1h_v1",
                "tomac_idxfut_clean_shiryaev_roberts_quickest_change_persistence_filter_4h_v1",
                "tomac_idxfut_clean_shiryaev_roberts_quickest_change_persistence_filter_1d_v1",
            ],
        )

    def test_shiryaev_roberts_quickest_change_strategy_source_uses_shifted_persistence_stat(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["shiryaev_roberts_quickest_change_persistence_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_shiryaev_roberts_quickest_change_persistence_filter_15m_v1",
            source,
        )
        self.assertIn("ShiryaevRobertsPersistence", source)
        self.assertIn("shiryaev_roberts_stat", source)
        self.assertIn("shiryaev_roberts_stat_shifted", source)
        self.assertIn("shiryaev_roberts_parent_admission_long.fillna(False)", source)
        self.assertIn("shiryaev_roberts_parent_admission_short.fillna(False)", source)
        self.assertIn("shiryaev_roberts_collapse_veto", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "shiryaev_roberts_quickest_change_persistence_filter" == "shiryaev_roberts_quickest_change_persistence_filter":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        sr_block = source[branch_start:next_branch]
        self.assertNotIn("shift(-", sr_block)
        self.assertNotIn("bps_per_side", sr_block)
        self.assertNotIn("cost_bps", sr_block)

    def test_l1_trend_filter_slope_stability_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["l1_trend_filter_slope_stability_gate"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "L1TrendFilterSlopeStabilityGate")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> SparseTrendDenoising -> L1TrendFilterSlopeStability -> ParentSignalAdmissionFilter",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.factor_id("5m"),
            "tomac_idxfut_clean_l1_trend_filter_slope_stability_gate_5m_v1",
        )

    def test_l1_trend_filter_slope_stability_strategy_source_uses_shifted_sparse_trend_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["l1_trend_filter_slope_stability_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="5m")

        self.assertIn("factor_id: tomac_idxfut_clean_l1_trend_filter_slope_stability_gate_5m_v1", source)
        self.assertIn("L1TrendFilterSlopeStability", source)
        self.assertIn("sparse_trend_proxy = dataframe[\"close\"].ewm(span=89", source)
        self.assertIn("l1_trend_slope_bps", source)
        self.assertIn("l1_kink_density", source)
        self.assertIn("l1_slope_stability_long.fillna(False)", source)
        self.assertIn("l1_slope_stability_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_hawkes_intensity_cluster_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["hawkes_intensity_cluster_admission_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "HawkesIntensityClusterAdmissionFilter")
        self.assertEqual(
            spec.branch_path,
            "ValidationMaturity -> EventClusterIntensity -> HawkesSelfExcitingActivityState -> ParentSignalAdmissionFilter",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.factor_id("5m"),
            "tomac_idxfut_clean_hawkes_intensity_cluster_admission_filter_5m_v1",
        )

    def test_hawkes_intensity_cluster_strategy_source_uses_shifted_cluster_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["hawkes_intensity_cluster_admission_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="5m")

        self.assertIn("factor_id: tomac_idxfut_clean_hawkes_intensity_cluster_admission_filter_5m_v1", source)
        self.assertIn("HawkesSelfExcitingActivityState", source)
        self.assertIn("hawkes_up_event_intensity", source)
        self.assertIn("hawkes_down_event_intensity", source)
        self.assertIn("hawkes_directional_excitation_ratio", source)
        self.assertIn("hawkes_two_sided_noise_ratio", source)
        self.assertIn("hawkes_cluster_admission_long.fillna(False)", source)
        self.assertIn("hawkes_cluster_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_beveridge_nelson_cycle_trend_filter_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["beveridge_nelson_cycle_trend_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "BeveridgeNelsonCycleTrendFilter")
        self.assertEqual(
            spec.branch_path,
            "RegimeRoot -> StochasticTrendCycleDecomposition -> BeveridgeNelsonPermanentSlope -> TransitoryGapMeanReversion -> ParentSignalAdmissionFilter",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.factor_id("5m"),
            "tomac_idxfut_clean_beveridge_nelson_cycle_trend_filter_5m_v1",
        )
        self.assertTrue(spec.supports(symbol="NQ", timeframe="1h"))
        self.assertFalse(spec.supports(symbol="NQ", timeframe="1m"))

    def test_beveridge_nelson_cycle_trend_filter_strategy_source_uses_shifted_bn_proxy(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["beveridge_nelson_cycle_trend_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="5m")

        self.assertIn("factor_id: tomac_idxfut_clean_beveridge_nelson_cycle_trend_filter_5m_v1", source)
        self.assertIn("BeveridgeNelsonPermanentSlope", source)
        self.assertIn("bn_permanent_trend_proxy", source)
        self.assertIn("bn_permanent_slope_bps", source)
        self.assertIn("bn_transitory_gap_bps", source)
        self.assertIn("bn_transitory_gap_z", source)
        self.assertIn("bn_cycle_contraction", source)
        self.assertIn("bn_trend_cycle_admission_long.fillna(False)", source)
        self.assertIn("bn_trend_cycle_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_bds_nonlinear_dependence_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["bds_nonlinear_dependence_admission_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "BdsNonlinearDependenceAdmissionFilter")
        self.assertEqual(
            spec.branch_path,
            "TransitionRisk -> NonlinearDependence -> BdsCorrelationDimensionGate -> ParentSignalAdmissionFilter",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.factor_id("15m"),
            "tomac_idxfut_clean_bds_nonlinear_dependence_admission_filter_15m_v1",
        )

    def test_bds_nonlinear_dependence_strategy_source_uses_shifted_residual_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["bds_nonlinear_dependence_admission_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_bds_nonlinear_dependence_admission_filter_15m_v1",
            source,
        )
        self.assertIn("BdsCorrelationDimensionGate", source)
        self.assertIn("bds_residual_return", source)
        self.assertIn("bds_embedding_dimension_2", source)
        self.assertIn("bds_embedding_dimension_3", source)
        self.assertIn("bds_epsilon_scale_075", source)
        self.assertIn("bds_epsilon_scale_150", source)
        self.assertIn("bds_nonlinear_dependence_score", source)
        self.assertIn("bds_parent_signal_admission_long.fillna(False)", source)
        self.assertIn("bds_parent_signal_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_rqa_determinism_trend_persistence_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["rqa_determinism_trend_persistence_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "RqaDeterminismTrendPersistenceFilter")
        self.assertEqual(
            spec.branch_path,
            "SpectralRhythm -> PhaseSpaceRecurrence -> RqaDeterminismLaminarity -> ParentTrendAdmissionFilter",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.factor_id("5m"),
            "tomac_idxfut_clean_rqa_determinism_trend_persistence_filter_5m_v1",
        )

    def test_rqa_determinism_trend_persistence_strategy_source_uses_shifted_rqa_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["rqa_determinism_trend_persistence_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="5m")

        self.assertIn("factor_id: tomac_idxfut_clean_rqa_determinism_trend_persistence_filter_5m_v1", source)
        self.assertIn("RqaDeterminismLaminarity", source)
        self.assertIn("rqa_embedding_return", source)
        self.assertIn("rqa_recurrence_rate", source)
        self.assertIn("rqa_determinism", source)
        self.assertIn("rqa_laminarity", source)
        self.assertIn("rqa_trapping_time", source)
        self.assertIn("rqa_parent_trend_admission_long.fillna(False)", source)
        self.assertIn("rqa_parent_trend_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_jump_activity_index_finite_infinite_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["jump_activity_index_finite_infinite_state_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "JumpActivityIndexFiniteInfiniteStateFilter")
        self.assertEqual(
            spec.branch_path,
            "TransitionRisk -> JumpActivityRegime -> FiniteInfiniteActivityState -> ParentTrendOrReclaimAdmissionFilter",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.factor_id("15m"),
            "tomac_idxfut_clean_jump_activity_index_finite_infinite_state_filter_15m_v1",
        )

    def test_jump_activity_index_finite_infinite_strategy_source_uses_shifted_activity_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["jump_activity_index_finite_infinite_state_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_jump_activity_index_finite_infinite_state_filter_15m_v1",
            source,
        )
        self.assertIn("JumpActivityRegime", source)
        self.assertIn("jump_activity_return_power_1", source)
        self.assertIn("jump_activity_return_power_2", source)
        self.assertIn("jump_activity_power_ratio", source)
        self.assertIn("jump_activity_index_proxy", source)
        self.assertIn("finite_infinite_activity_state", source)
        self.assertIn("jump_activity_parent_admission_long.fillna(False)", source)
        self.assertIn("jump_activity_parent_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_quantile_regression_trend_asymmetry_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["quantile_regression_trend_asymmetry_gate"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "QuantileRegressionTrendAsymmetryGate")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> DistributionalSlope -> RollingQuantileRegression -> UpperLowerTailSlopeAsymmetry -> FrictionAwareAtrHold",
        )
        self.assertEqual(spec.direction, "long")
        self.assertEqual(
            spec.factor_id("30m"),
            "tomac_idxfut_clean_quantile_regression_trend_asymmetry_gate_30m_v1",
        )

    def test_quantile_regression_trend_asymmetry_strategy_source_uses_shifted_tail_slope_gate(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["quantile_regression_trend_asymmetry_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("factor_id: tomac_idxfut_clean_quantile_regression_trend_asymmetry_gate_30m_v1", source)
        self.assertIn("RollingQuantileRegression", source)
        self.assertIn("quantile_lower_slope_bps", source)
        self.assertIn("quantile_median_slope_bps", source)
        self.assertIn("quantile_upper_slope_bps", source)
        self.assertIn("quantile_tail_slope_asymmetry", source)
        self.assertIn("quantile_regression_trend_asymmetry_long.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_median_price_envelope_reacceleration_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["median_price_envelope_reacceleration_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "MedianPriceEnvelopeReaccelerationFilter")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> MedianPriceEnvelope -> PullbackAcceptance -> ReaccelerationFilter -> FrictionAwareAtrHold",
        )
        self.assertEqual(spec.direction, "long")
        self.assertEqual(
            spec.factor_id("4h"),
            "tomac_idxfut_clean_median_price_envelope_reacceleration_filter_4h_v1",
        )

    def test_median_price_envelope_reacceleration_strategy_source_uses_shifted_median_envelope(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["median_price_envelope_reacceleration_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="4h")

        self.assertIn("factor_id: tomac_idxfut_clean_median_price_envelope_reacceleration_filter_4h_v1", source)
        self.assertIn("MedianPriceEnvelope", source)
        self.assertIn("median_price_envelope_center", source)
        self.assertIn("median_price_envelope_width", source)
        self.assertIn("median_price_envelope_displacement", source)
        self.assertIn("median_price_envelope_reacceleration", source)
        self.assertIn("median_price_envelope_reacceleration_long.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_swing_leg_duration_amplitude_asymmetry_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["swing_leg_duration_amplitude_asymmetry_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "SwingLegDurationAmplitudeAsymmetryFilter")
        self.assertEqual(
            spec.branch_path,
            "RegimeRoot -> SwingStructureRegime -> ConfirmedPivotLegAsymmetry -> DurationAmplitudeContinuation",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_swing_leg_duration_amplitude_asymmetry_filter_5m_v1",
                "tomac_idxfut_clean_swing_leg_duration_amplitude_asymmetry_filter_15m_v1",
                "tomac_idxfut_clean_swing_leg_duration_amplitude_asymmetry_filter_30m_v1",
                "tomac_idxfut_clean_swing_leg_duration_amplitude_asymmetry_filter_1h_v1",
                "tomac_idxfut_clean_swing_leg_duration_amplitude_asymmetry_filter_4h_v1",
                "tomac_idxfut_clean_swing_leg_duration_amplitude_asymmetry_filter_1d_v1",
            ],
        )

    def test_swing_leg_duration_amplitude_asymmetry_strategy_source_uses_lagged_confirmed_pivots(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["swing_leg_duration_amplitude_asymmetry_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_idxfut_clean_swing_leg_duration_amplitude_asymmetry_filter_15m_v1", source)
        self.assertIn("ConfirmedPivotLegAsymmetry", source)
        self.assertIn("confirmed_pivot_high", source)
        self.assertIn("confirmed_pivot_low", source)
        self.assertIn("swing_leg_duration_ratio", source)
        self.assertIn("swing_leg_amplitude_ratio", source)
        self.assertIn("swing_leg_duration_amplitude_asymmetry_long.fillna(False)", source)
        self.assertIn("swing_leg_duration_amplitude_asymmetry_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_vhf_chop_trend_reacceleration_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["vhf_chop_trend_reacceleration"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "VhfChopTrendReacceleration")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> DirectionalEfficiency -> VhfChopCompressionRelease -> MtfTrendReacceleration",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h")],
            [
                "tomac_idxfut_clean_vhf_chop_trend_reacceleration_5m_v1",
                "tomac_idxfut_clean_vhf_chop_trend_reacceleration_15m_v1",
                "tomac_idxfut_clean_vhf_chop_trend_reacceleration_30m_v1",
                "tomac_idxfut_clean_vhf_chop_trend_reacceleration_1h_v1",
            ],
        )

    def test_vhf_chop_trend_reacceleration_strategy_source_uses_shifted_efficiency_release(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["vhf_chop_trend_reacceleration"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("factor_id: tomac_idxfut_clean_vhf_chop_trend_reacceleration_30m_v1", source)
        self.assertIn("VhfChopCompressionRelease", source)
        self.assertIn("vhf_34_shifted", source)
        self.assertIn("chop_34_shifted", source)
        self.assertIn("vhf_reacceleration_shifted", source)
        self.assertIn("vhf_chop_reacceleration_long.fillna(False)", source)
        self.assertIn("vhf_chop_reacceleration_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_trendexpansion_bocpd_dynmom_vhfchop_family_is_registered_for_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["trendexpansion_bocpd_dynmom_vhfchop"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "TrendExpansionBocpdDynmomVhfChop")
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> RegimeChangeAdmission -> BocpdRunLengthReset -> "
            "DynamicMomentumConsensus -> VhfChopNoTrendVeto -> ExpansionTrendOnlyEntry",
        )
        timeframes = ("5m", "15m", "30m", "1h", "4h", "1d")
        self.assertTrue(all(spec.supports(symbol="NQ", timeframe=timeframe) for timeframe in timeframes))
        self.assertFalse(spec.supports(symbol="NQ", timeframe="1m"))
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in timeframes],
            [
                "tomac_nq_5m_trendexpansion_bocpd_dynmom_vhfchop_mtf_v1",
                "tomac_nq_15m_trendexpansion_bocpd_dynmom_vhfchop_mtf_v1",
                "tomac_nq_30m_trendexpansion_bocpd_dynmom_vhfchop_mtf_v1",
                "tomac_nq_1h_trendexpansion_bocpd_dynmom_vhfchop_mtf_v1",
                "tomac_nq_4h_trendexpansion_bocpd_dynmom_vhfchop_mtf_v1",
                "tomac_nq_1d_trendexpansion_bocpd_dynmom_vhfchop_mtf_v1",
            ],
        )

    def test_trendexpansion_bocpd_dynmom_vhfchop_source_is_closed_bar_trendexpansion_only(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["trendexpansion_bocpd_dynmom_vhfchop"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_nq_15m_trendexpansion_bocpd_dynmom_vhfchop_mtf_v1", source)
        self.assertIn("RegimeChangeAdmission", source)
        self.assertIn("bocpd_run_length_reset_shifted", source)
        self.assertIn("bocpd_hazard_proxy_shifted", source)
        self.assertIn("dynmom_consensus_shifted", source)
        self.assertIn("vhf_chop_no_trend_veto_shifted", source)
        self.assertIn("trendexpansion_only_long.fillna(False)", source)
        self.assertIn("trendexpansion_only_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertIn("other_regimes_reference_veto_only", source)
        self.assertNotIn("shift(-", source)

    def test_trendexpansion_only_clean_state_shift_15m_family_is_registered(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(
            families=["trend_expansion_only_regime_transition_clean_state_shift"]
        )

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "TrendExpansionOnlyCleanStateShift")
        self.assertEqual(spec.direction, "long")
        self.assertEqual(
            spec.branch_path,
            "RegimeTransition -> TrendExpansionOnly -> CompressionBreakoutStateShift",
        )
        self.assertTrue(spec.supports(symbol="NQ", timeframe="15m"))
        self.assertFalse(spec.supports(symbol="NQ", timeframe="5m"))
        self.assertFalse(spec.supports(symbol="YM", timeframe="15m"))
        self.assertEqual(
            spec.factor_id("15m"),
            "tomac_nq_15m_trend_expansion_only_regime_transition_long_clean_state_shift_exact_aq_v1",
        )

    def test_trendexpansion_only_clean_state_shift_source_is_closed_bar_long_only(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(
            families=["trend_expansion_only_regime_transition_clean_state_shift"]
        )[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn(
            "factor_id: tomac_nq_15m_trend_expansion_only_regime_transition_long_clean_state_shift_exact_aq_v1",
            source,
        )
        self.assertIn("RegimeTransition", source)
        self.assertIn("TrendExpansionOnly", source)
        self.assertIn("CompressionBreakoutStateShift", source)
        self.assertIn("state_shift_clean_transition_long", source)
        self.assertIn("other_regimes_reference_veto_only", source)
        self.assertIn("state_shift_friction_window", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("can_short = False", source)
        self.assertNotIn("state_shift_clean_transition_short", source)
        self.assertNotIn("shift(-", source)

    def test_trendexpansion_only_strict_state_shift_5m_family_is_registered(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(
            families=["trend_expansion_only_regime_transition_strict_state_shift"]
        )

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "TrendExpansionOnlyStrictStateShift")
        self.assertEqual(spec.direction, "long")
        self.assertEqual(
            spec.branch_path,
            "RegimeTransition -> TrendExpansionOnly -> CompressionBreakoutStateShift -> StrictStateShift",
        )
        self.assertTrue(spec.supports(symbol="NQ", timeframe="5m"))
        self.assertFalse(spec.supports(symbol="NQ", timeframe="15m"))
        self.assertFalse(spec.supports(symbol="YM", timeframe="5m"))
        self.assertEqual(
            spec.factor_id("5m"),
            "tomac_nq_5m_trend_expansion_only_regime_transition_long_strict_state_shift_exact_aq_v1",
        )

    def test_trendexpansion_only_strict_state_shift_source_is_closed_bar_long_only(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(
            families=["trend_expansion_only_regime_transition_strict_state_shift"]
        )[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="5m")

        self.assertIn(
            "factor_id: tomac_nq_5m_trend_expansion_only_regime_transition_long_strict_state_shift_exact_aq_v1",
            source,
        )
        self.assertIn("RegimeTransition", source)
        self.assertIn("TrendExpansionOnly", source)
        self.assertIn("CompressionBreakoutStateShift", source)
        self.assertIn("StrictStateShift", source)
        self.assertIn("state_shift_strict_transition_long", source)
        self.assertIn("other_regimes_reference_veto_only", source)
        self.assertIn('dataframe["state_shift_chop_shifted"].gt(50.0)', source)
        self.assertIn('dataframe["state_shift_vhf_shifted"].ge(0.36)', source)
        self.assertIn('dataframe["state_shift_vhf_rise_shifted"].gt(0.008)', source)
        self.assertIn('dataframe["state_shift_adx_rise_shifted"].gt(0.40)', source)
        self.assertIn('dataframe["state_shift_momentum_bps_shifted"].gt(0.7975)', source)
        self.assertIn(").ge(3)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("can_short = False", source)
        self.assertNotIn("state_shift_strict_transition_short", source)
        self.assertNotIn("shift(-", source)

    def test_directional_sign_entropy_release_reacceleration_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["directional_sign_entropy_release_reacceleration"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "DirectionalSignEntropyReleaseReacceleration")
        self.assertEqual(
            spec.branch_path,
            "RegimeRoot -> TrendExpansion -> DirectionalSignEntropyCompression -> EntropyReleaseReacceleration -> MtfResonance",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_directional_sign_entropy_release_reacceleration_5m_v1",
                "tomac_idxfut_clean_directional_sign_entropy_release_reacceleration_15m_v1",
                "tomac_idxfut_clean_directional_sign_entropy_release_reacceleration_30m_v1",
                "tomac_idxfut_clean_directional_sign_entropy_release_reacceleration_1h_v1",
                "tomac_idxfut_clean_directional_sign_entropy_release_reacceleration_4h_v1",
                "tomac_idxfut_clean_directional_sign_entropy_release_reacceleration_1d_v1",
            ],
        )

    def test_directional_sign_entropy_release_reacceleration_strategy_source_uses_shifted_entropy_release(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["directional_sign_entropy_release_reacceleration"])[0]

        source = module.strategy_source(spec, symbol="YM", timeframe="1d")

        self.assertIn("factor_id: tomac_idxfut_clean_directional_sign_entropy_release_reacceleration_1d_v1", source)
        self.assertIn("DirectionalSignEntropyCompression", source)
        self.assertIn("directional_sign_entropy", source)
        self.assertIn("directional_sign_entropy_release", source)
        self.assertIn("signed_return_reacceleration", source)
        self.assertIn("entropy_release_reacceleration_long.fillna(False)", source)
        self.assertIn("entropy_release_reacceleration_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_pesaran_timmermann_directional_accuracy_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["pesaran_timmermann_directional_accuracy_admission_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "PesaranTimmermannDirectionalAccuracyAdmissionFilter")
        self.assertEqual(
            spec.branch_path,
            "RegimeRoot -> TrendExpansion -> DirectionalForecastSkill -> PesaranTimmermannDirectionalAccuracy -> ParentTrendAdmission",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_pesaran_timmermann_directional_accuracy_admission_filter_5m_v1",
                "tomac_idxfut_clean_pesaran_timmermann_directional_accuracy_admission_filter_15m_v1",
                "tomac_idxfut_clean_pesaran_timmermann_directional_accuracy_admission_filter_30m_v1",
                "tomac_idxfut_clean_pesaran_timmermann_directional_accuracy_admission_filter_1h_v1",
                "tomac_idxfut_clean_pesaran_timmermann_directional_accuracy_admission_filter_4h_v1",
                "tomac_idxfut_clean_pesaran_timmermann_directional_accuracy_admission_filter_1d_v1",
            ],
        )

    def test_pesaran_timmermann_directional_accuracy_strategy_source_uses_shifted_directional_skill_gate(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["pesaran_timmermann_directional_accuracy_admission_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_pesaran_timmermann_directional_accuracy_admission_filter_30m_v1",
            source,
        )
        self.assertIn("PesaranTimmermannDirectionalAccuracy", source)
        self.assertIn("pt_forecast_direction_shifted", source)
        self.assertIn("pt_realized_direction_shifted", source)
        self.assertIn("pt_directional_accuracy_score", source)
        self.assertIn("pt_directional_skill_long.fillna(False)", source)
        self.assertIn("pt_directional_skill_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_ultimate_williams_reacceleration_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["ultimate_williams_reacceleration"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "UltimateWilliamsReacceleration")
        self.assertEqual(
            spec.branch_path,
            "RegimeRoot -> OscillatorReacceleration -> UltimateWilliamsReclaim -> TrendContinuationFilter",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_ultimate_williams_reacceleration_5m_v1",
                "tomac_idxfut_clean_ultimate_williams_reacceleration_15m_v1",
                "tomac_idxfut_clean_ultimate_williams_reacceleration_30m_v1",
                "tomac_idxfut_clean_ultimate_williams_reacceleration_1h_v1",
                "tomac_idxfut_clean_ultimate_williams_reacceleration_4h_v1",
                "tomac_idxfut_clean_ultimate_williams_reacceleration_1d_v1",
            ],
        )

    def test_ultimate_williams_strategy_source_uses_shifted_completed_oscillator_reclaim(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["ultimate_williams_reacceleration"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_idxfut_clean_ultimate_williams_reacceleration_15m_v1", source)
        self.assertIn("UltimateWilliamsReclaim", source)
        self.assertIn("ultimate_oscillator_shifted", source)
        self.assertIn("williams_r_prev_min3", source)
        self.assertIn("ultimate_williams_reacceleration_long.fillna(False)", source)
        self.assertIn("ultimate_williams_reacceleration_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_medrv_minrv_noise_robust_vol_state_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["medrv_minrv_noise_robust_vol_state_gate"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "MedrvMinrvNoiseRobustVolStateGate")
        self.assertEqual(
            spec.branch_path,
            "VolatilityState -> JumpRobustRealizedVolatility -> MedrvMinrvNoiseRobustState -> ParentTrendOrReclaimAdmission",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_medrv_minrv_noise_robust_vol_state_gate_5m_v1",
                "tomac_idxfut_clean_medrv_minrv_noise_robust_vol_state_gate_15m_v1",
                "tomac_idxfut_clean_medrv_minrv_noise_robust_vol_state_gate_30m_v1",
                "tomac_idxfut_clean_medrv_minrv_noise_robust_vol_state_gate_1h_v1",
                "tomac_idxfut_clean_medrv_minrv_noise_robust_vol_state_gate_4h_v1",
                "tomac_idxfut_clean_medrv_minrv_noise_robust_vol_state_gate_1d_v1",
            ],
        )

    def test_medrv_minrv_strategy_source_uses_shifted_noise_robust_vol_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["medrv_minrv_noise_robust_vol_state_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("factor_id: tomac_idxfut_clean_medrv_minrv_noise_robust_vol_state_gate_30m_v1", source)
        self.assertIn("MedrvMinrvNoiseRobustState", source)
        self.assertIn("medrv_like", source)
        self.assertIn("minrv_like", source)
        self.assertIn("rv_medrv_disagreement_shifted", source)
        self.assertIn("robust_vol_state_z_shifted", source)
        self.assertIn("medrv_minrv_noise_robust_state_long.fillna(False)", source)
        self.assertIn("medrv_minrv_noise_robust_state_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_emd_imf_trend_residual_gate_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["emd_imf_trend_residual_gate"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "EmdImfTrendResidualGate")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> AdaptiveModeDecomposition -> ImfTrendResidualAgreement -> MtfResidualEnergyVeto -> FrictionAwareAtrHold",
        )
        self.assertEqual(spec.direction, "long")
        self.assertEqual(
            spec.factor_id("1h"),
            "tomac_idxfut_clean_emd_imf_trend_residual_gate_1h_v1",
        )

    def test_emd_imf_trend_residual_gate_strategy_source_uses_shifted_imf_residual_gate(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["emd_imf_trend_residual_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="1h")

        self.assertIn("factor_id: tomac_idxfut_clean_emd_imf_trend_residual_gate_1h_v1", source)
        self.assertIn("AdaptiveModeDecomposition", source)
        self.assertIn("emd_imf_fast_energy_proxy", source)
        self.assertIn("emd_imf_slow_residual_proxy", source)
        self.assertIn("emd_imf_residual_slope_bps", source)
        self.assertIn("emd_imf_energy_ratio", source)
        self.assertIn("emd_imf_trend_residual_agreement", source)
        self.assertIn("emd_imf_trend_residual_agreement.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_market_turbulence_mahalanobis_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["market_turbulence_mahalanobis_state_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "MarketTurbulenceMahalanobisStateFilter")
        self.assertEqual(
            spec.branch_path,
            "RiskState -> MarketTurbulence -> RollingMahalanobisDistance -> ParentSignalAdmissionFilter",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.factor_id("15m"),
            "tomac_idxfut_clean_market_turbulence_mahalanobis_state_filter_15m_v1",
        )

    def test_market_turbulence_mahalanobis_strategy_source_uses_shifted_stress_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["market_turbulence_mahalanobis_state_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_idxfut_clean_market_turbulence_mahalanobis_state_filter_15m_v1", source)
        self.assertIn("MarketTurbulence", source)
        self.assertIn("mahalanobis_return_vector", source)
        self.assertIn("market_turbulence_distance", source)
        self.assertIn("market_turbulence_percentile", source)
        self.assertIn("turbulence_parent_signal_admission_long.fillna(False)", source)
        self.assertIn("turbulence_parent_signal_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_rough_volatility_local_roughness_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["rough_volatility_local_roughness_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "RoughVolatilityLocalRoughnessFilter")
        self.assertEqual(
            spec.branch_path,
            "VolatilityState -> RoughVolatility -> LocalRoughnessPersistence -> ParentSignalAdmissionFilter",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.factor_id("1h"),
            "tomac_idxfut_clean_rough_volatility_local_roughness_filter_1h_v1",
        )

    def test_rough_volatility_local_roughness_strategy_source_uses_shifted_roughness_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["rough_volatility_local_roughness_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="1h")

        self.assertIn("factor_id: tomac_idxfut_clean_rough_volatility_local_roughness_filter_1h_v1", source)
        self.assertIn("RoughVolatility", source)
        self.assertIn("rough_volatility_return", source)
        self.assertIn("realized_volatility_acceleration", source)
        self.assertIn("local_roughness_persistence", source)
        self.assertIn("roughness_parent_signal_admission_long.fillna(False)", source)
        self.assertIn("roughness_parent_signal_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_structural_break_variance_shift_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["structural_break_variance_shift_admission_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "StructuralBreakVarianceShiftAdmissionFilter")
        self.assertEqual(
            spec.branch_path,
            "ValidationMaturity -> StructuralBreakStability -> VarianceShiftAndParameterBreak -> ParentSignalAdmissionFilter",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.factor_id("5m"),
            "tomac_idxfut_clean_structural_break_variance_shift_admission_filter_5m_v1",
        )

    def test_structural_break_variance_shift_strategy_source_uses_shifted_break_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["structural_break_variance_shift_admission_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="5m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_structural_break_variance_shift_admission_filter_5m_v1",
            source,
        )
        self.assertIn("StructuralBreakStability", source)
        self.assertIn("structural_break_score", source)
        self.assertIn("variance_shift_score", source)
        self.assertIn("stable_parameter_state", source)
        self.assertIn("variance_shift_veto", source)
        self.assertIn("break_state_parent_admission_long.fillna(False)", source)
        self.assertIn("break_state_parent_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_htf_range_edge_cisd_mss_displacement_family_is_registered_as_transition_predictor(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["htf_range_edge_cisd_mss_displacement_te"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "HtfRangeEdgeCisdMssDisplacementTe")
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.branch_path,
            "RegimeTransition -> TrendExpansionOnly -> HtfRangeEdgeCisdMssDisplacement -> NextSegmentTrendExpansionPosterior",
        )
        self.assertTrue(spec.supports(symbol="NQ", timeframe="3m"))
        self.assertTrue(spec.supports(symbol="YM", timeframe="5m"))
        self.assertFalse(spec.supports(symbol="ES", timeframe="3m"))
        self.assertEqual(
            spec.factor_id("3m"),
            "tomac_idxfut_clean_htf_range_edge_cisd_mss_displacement_te_3m_v1",
        )

    def test_htf_range_edge_cisd_mss_displacement_source_is_closed_bar_predictive(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["htf_range_edge_cisd_mss_displacement_te"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="3m")

        self.assertIn("factor_id: tomac_idxfut_clean_htf_range_edge_cisd_mss_displacement_te_3m_v1", source)
        self.assertIn("RegimeTransition", source)
        self.assertIn("TrendExpansionOnly", source)
        self.assertIn("htf_range_bottom_sweep", source)
        self.assertIn("bull_cisd_delivery_flip", source)
        self.assertIn("bull_displacement_impulse", source)
        self.assertIn("range_prior_long.fillna(False)", source)
        self.assertIn("ltf_structure_long.fillna(False)", source)
        self.assertIn("expansion_impulse_long.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertIn("posterior_decay_long", source)
        self.assertNotIn("shift(-", source)

    def test_htf_range_breakout_retest_te_selective_family_is_registered(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["htf_range_breakout_retest_te_selective"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "HtfRangeBreakoutRetestTeSelective")
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.branch_path,
            "RegimeTransition -> TrendExpansionOnly -> HtfRangeBreakoutRetestAcceptance -> SelectivePosteriorV1",
        )
        self.assertTrue(spec.supports(symbol="NQ", timeframe="1m"))
        self.assertTrue(spec.supports(symbol="YM", timeframe="15m"))
        self.assertFalse(spec.supports(symbol="ES", timeframe="5m"))
        self.assertEqual(
            spec.factor_id("5m"),
            "tomac_idxfut_clean_htf_range_breakout_retest_te_selective_5m_v1",
        )

    def test_htf_range_breakout_retest_te_selective_source_is_closed_bar_retest_predictive(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["htf_range_breakout_retest_te_selective"])[0]

        source = module.strategy_source(spec, symbol="YM", timeframe="5m")

        self.assertIn("factor_id: tomac_idxfut_clean_htf_range_breakout_retest_te_selective_5m_v1", source)
        self.assertIn("HtfRangeBreakoutRetestAcceptance", source)
        self.assertIn("htf_range_top_breakout_recent", source)
        self.assertIn("htf_range_top_retest_hold", source)
        self.assertIn("htf_range_bottom_retest_hold", source)
        self.assertIn("selective_breakout_decay_long", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertIn("exit_signal = exit_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_pettitt_rank_shift_breakout_reliability_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["pettitt_rank_shift_breakout_reliability_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "PettittRankShiftBreakoutReliabilityFilter")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> NonparametricChangePoint -> PettittRankShift -> BreakoutReliabilityGate",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_pettitt_rank_shift_breakout_reliability_filter_5m_v1",
                "tomac_idxfut_clean_pettitt_rank_shift_breakout_reliability_filter_15m_v1",
                "tomac_idxfut_clean_pettitt_rank_shift_breakout_reliability_filter_30m_v1",
                "tomac_idxfut_clean_pettitt_rank_shift_breakout_reliability_filter_1h_v1",
                "tomac_idxfut_clean_pettitt_rank_shift_breakout_reliability_filter_4h_v1",
                "tomac_idxfut_clean_pettitt_rank_shift_breakout_reliability_filter_1d_v1",
            ],
        )

    def test_pettitt_rank_shift_breakout_reliability_strategy_source_uses_shifted_rank_gate(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["pettitt_rank_shift_breakout_reliability_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_pettitt_rank_shift_breakout_reliability_filter_15m_v1",
            source,
        )
        self.assertIn("NonparametricChangePoint", source)
        self.assertIn("pettitt_rank_statistic", source)
        self.assertIn("pettitt_location_balance", source)
        self.assertIn("pettitt_breakout_reliability_long.fillna(False)", source)
        self.assertIn("pettitt_breakout_reliability_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_high_low_spread_amihud_liquidity_shock_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["high_low_spread_amihud_liquidity_shock_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "HighLowSpreadAmihudLiquidityShockFilter")
        self.assertEqual(
            spec.branch_path,
            "LiquidityState -> HighLowSpreadEstimator -> AmihudPriceImpactShock -> ParentTrendAdmissionFilter",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.factor_id("5m"),
            "tomac_idxfut_clean_high_low_spread_amihud_liquidity_shock_filter_5m_v1",
        )
        self.assertEqual(
            spec.factor_id("1d"),
            "tomac_idxfut_clean_high_low_spread_amihud_liquidity_shock_filter_1d_v1",
        )

    def test_high_low_spread_amihud_liquidity_shock_strategy_source_uses_shifted_liquidity_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["high_low_spread_amihud_liquidity_shock_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="5m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_high_low_spread_amihud_liquidity_shock_filter_5m_v1",
            source,
        )
        self.assertIn("HighLowSpreadEstimator", source)
        self.assertIn("corwin_schultz_spread_proxy", source)
        self.assertIn("amihud_price_impact_shock", source)
        self.assertIn("liquidity_shock_percentile", source)
        self.assertIn("liquidity_parent_admission_long.fillna(False)", source)
        self.assertIn("liquidity_parent_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_kyle_lambda_impact_resilience_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["kyle_lambda_impact_resilience_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "KyleLambdaImpactResilienceFilter")
        self.assertEqual(
            spec.branch_path,
            "LiquidityStress -> SignedVolumePriceImpact -> KyleLambdaImpactState -> ImpactResilienceAdmissionFilter",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.factor_id("5m"),
            "tomac_idxfut_clean_kyle_lambda_impact_resilience_filter_5m_v1",
        )
        self.assertEqual(
            spec.factor_id("1d"),
            "tomac_idxfut_clean_kyle_lambda_impact_resilience_filter_1d_v1",
        )

    def test_kyle_lambda_impact_resilience_strategy_source_uses_shifted_impact_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["kyle_lambda_impact_resilience_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_kyle_lambda_impact_resilience_filter_15m_v1",
            source,
        )
        self.assertIn("SignedVolumePriceImpact", source)
        self.assertIn("KyleLambdaImpactState", source)
        self.assertIn("impact_signed_volume_proxy_shifted", source)
        self.assertIn("kyle_lambda_impact_proxy", source)
        self.assertIn("impact_resilience_state", source)
        self.assertIn("lambda_impact_parent_admission_long.fillna(False)", source)
        self.assertIn("lambda_impact_parent_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_signed_return_impact_absorption_reversal_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["signed_return_impact_absorption_reversal_gate"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "SignedReturnImpactAbsorptionReversalGate")
        self.assertEqual(
            spec.branch_path,
            "MicrostructureProxy -> SignedReturnImpact -> AbsorptionFailureReversal -> MtfMeanReversionAdmission",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_signed_return_impact_absorption_reversal_gate_5m_v1",
                "tomac_idxfut_clean_signed_return_impact_absorption_reversal_gate_15m_v1",
                "tomac_idxfut_clean_signed_return_impact_absorption_reversal_gate_30m_v1",
                "tomac_idxfut_clean_signed_return_impact_absorption_reversal_gate_1h_v1",
                "tomac_idxfut_clean_signed_return_impact_absorption_reversal_gate_4h_v1",
                "tomac_idxfut_clean_signed_return_impact_absorption_reversal_gate_1d_v1",
            ],
        )

    def test_signed_return_impact_absorption_reversal_strategy_source_uses_shifted_absorption_gate(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["signed_return_impact_absorption_reversal_gate"])[0]

        source = module.strategy_source(spec, symbol="YM", timeframe="30m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_signed_return_impact_absorption_reversal_gate_30m_v1",
            source,
        )
        self.assertIn("SignedReturnImpact", source)
        self.assertIn("signed_return_impact_proxy", source)
        self.assertIn("impact_absorption_state", source)
        self.assertIn("absorption_reversal_long.fillna(False)", source)
        self.assertIn("absorption_reversal_short.fillna(False)", source)
        self.assertIn("impact_absorption_decay_long.fillna(False)", source)
        self.assertIn("impact_absorption_decay_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_dcca_cross_correlation_trend_admission_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["dcca_cross_correlation_trend_admission_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "DccaCrossCorrelationTrendAdmissionFilter")
        self.assertEqual(
            spec.branch_path,
            "CrossMarketStructure -> DetrendedCrossCorrelation -> DccaTrendCoherenceGate -> ParentSignalAdmissionFilter",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.factor_id("5m"),
            "tomac_idxfut_clean_dcca_cross_correlation_trend_admission_filter_5m_v1",
        )

    def test_dcca_cross_correlation_trend_admission_strategy_source_uses_shifted_coherence_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["dcca_cross_correlation_trend_admission_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="5m")

        self.assertIn("factor_id: tomac_idxfut_clean_dcca_cross_correlation_trend_admission_filter_5m_v1", source)
        self.assertIn("DetrendedCrossCorrelation", source)
        self.assertIn("dcca_parent_return", source)
        self.assertIn("dcca_peer_coherence", source)
        self.assertIn("dcca_trend_coherence_score", source)
        self.assertIn("dcca_parent_signal_admission_long.fillna(False)", source)
        self.assertIn("dcca_parent_signal_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_covar_systemic_tail_risk_admission_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["covar_systemic_tail_risk_admission_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "CovarSystemicTailRiskAdmissionFilter")
        self.assertEqual(
            spec.branch_path,
            "RiskState -> ConditionalTailSystemicRisk -> DeltaCoVaRStressState -> ParentSignalAdmissionFilter",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.factor_id("1h"),
            "tomac_idxfut_clean_covar_systemic_tail_risk_admission_filter_1h_v1",
        )

    def test_covar_systemic_tail_risk_strategy_source_uses_shifted_tail_risk_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["covar_systemic_tail_risk_admission_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="1h")

        self.assertIn("factor_id: tomac_idxfut_clean_covar_systemic_tail_risk_admission_filter_1h_v1", source)
        self.assertIn("ConditionalTailSystemicRisk", source)
        self.assertIn("covar_parent_return", source)
        self.assertIn("covar_peer_system_return", source)
        self.assertIn("conditional_system_var", source)
        self.assertIn("delta_covar_stress_state", source)
        self.assertIn("covar_parent_signal_admission_long.fillna(False)", source)
        self.assertIn("covar_parent_signal_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_unit_root_stationarity_mode_switch_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["unit_root_stationarity_mode_switch_gate"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "UnitRootStationarityModeSwitchGate")
        self.assertEqual(
            spec.branch_path,
            "ValidationMaturity -> UnitRootStationarityMode -> ParentContinuationOrReversionAdmission",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.factor_id("30m"),
            "tomac_idxfut_clean_unit_root_stationarity_mode_switch_gate_30m_v1",
        )

    def test_unit_root_stationarity_mode_switch_strategy_source_uses_shifted_stationarity_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["unit_root_stationarity_mode_switch_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("factor_id: tomac_idxfut_clean_unit_root_stationarity_mode_switch_gate_30m_v1", source)
        self.assertIn("UnitRootStationarityMode", source)
        self.assertIn("unit_root_return", source)
        self.assertIn("pp_adf_unit_root_proxy", source)
        self.assertIn("kpss_stationarity_proxy", source)
        self.assertIn("df_gls_detrended_slope", source)
        self.assertIn("stationarity_mode_parent_admission_long.fillna(False)", source)
        self.assertIn("stationarity_mode_parent_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_event_duration_liquidity_clock_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["event_duration_liquidity_clock_trend_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "EventDurationLiquidityClockTrendFilter")
        self.assertEqual(
            spec.branch_path,
            "SessionLiquidity -> EventDurationLiquidityClock -> ACDStyleDurationThrottle -> ParentTrendAdmission",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_event_duration_liquidity_clock_trend_filter_5m_v1",
                "tomac_idxfut_clean_event_duration_liquidity_clock_trend_filter_15m_v1",
                "tomac_idxfut_clean_event_duration_liquidity_clock_trend_filter_30m_v1",
                "tomac_idxfut_clean_event_duration_liquidity_clock_trend_filter_1h_v1",
                "tomac_idxfut_clean_event_duration_liquidity_clock_trend_filter_4h_v1",
                "tomac_idxfut_clean_event_duration_liquidity_clock_trend_filter_1d_v1",
            ],
        )

    def test_event_duration_liquidity_clock_strategy_source_uses_shifted_event_clock(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["event_duration_liquidity_clock_trend_filter"])[0]

        source = module.strategy_source(spec, symbol="YM", timeframe="15m")

        self.assertIn("factor_id: tomac_idxfut_clean_event_duration_liquidity_clock_trend_filter_15m_v1", source)
        self.assertIn("EventDurationLiquidityClock", source)
        self.assertIn("event_duration_liquidity_clock", source)
        self.assertIn("event_clock_compression_ratio", source)
        self.assertIn("event_duration_parent_admission_long.fillna(False)", source)
        self.assertIn("event_duration_parent_admission_short.fillna(False)", source)
        self.assertIn("event_duration_decay_long.fillna(False)", source)
        self.assertIn("event_duration_decay_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_renko_price_brick_reacceleration_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["renko_price_brick_reacceleration_filter"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "RenkoPriceBrickReaccelerationFilter")
        self.assertEqual(
            spec.branch_path,
            "RegimeRoot -> EventCompressedTrend -> RenkoPriceBrickState -> BrickReaccelerationAdmission",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_renko_price_brick_reacceleration_filter_5m_v1",
                "tomac_idxfut_clean_renko_price_brick_reacceleration_filter_15m_v1",
                "tomac_idxfut_clean_renko_price_brick_reacceleration_filter_30m_v1",
                "tomac_idxfut_clean_renko_price_brick_reacceleration_filter_1h_v1",
                "tomac_idxfut_clean_renko_price_brick_reacceleration_filter_4h_v1",
                "tomac_idxfut_clean_renko_price_brick_reacceleration_filter_1d_v1",
            ],
        )

    def test_renko_price_brick_reacceleration_strategy_source_uses_shifted_brick_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["renko_price_brick_reacceleration_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        compile(source, "renko_price_brick_reacceleration_strategy.py", "exec")
        self.assertIn("factor_id: tomac_idxfut_clean_renko_price_brick_reacceleration_filter_30m_v1", source)
        self.assertIn("EventCompressedTrend", source)
        self.assertIn("RenkoPriceBrickState", source)
        self.assertIn("renko_completed_brick_size_shifted", source)
        self.assertIn("renko_price_brick_state", source)
        self.assertIn("renko_brick_reacceleration_long", source)
        self.assertIn("renko_brick_reacceleration_short", source)
        self.assertIn("renko_brick_churn_veto", source)
        self.assertIn("renko_parent_admission_long.fillna(False)", source)
        self.assertIn("renko_parent_admission_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_candlestick_pattern_context_reliability_family_is_registered_with_rooted_branch(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["candlestick_pattern_context_reliability_gate"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "CandlestickPatternContextReliabilityGate")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> PriceActionPatternReliability -> CandlestickContextFilter -> ParentSignalAdmissionGate",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_candlestick_pattern_context_reliability_gate_5m_v1",
                "tomac_idxfut_clean_candlestick_pattern_context_reliability_gate_15m_v1",
                "tomac_idxfut_clean_candlestick_pattern_context_reliability_gate_30m_v1",
                "tomac_idxfut_clean_candlestick_pattern_context_reliability_gate_1h_v1",
                "tomac_idxfut_clean_candlestick_pattern_context_reliability_gate_4h_v1",
                "tomac_idxfut_clean_candlestick_pattern_context_reliability_gate_1d_v1",
            ],
        )

    def test_candlestick_pattern_context_reliability_strategy_source_uses_shifted_patterns(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["candlestick_pattern_context_reliability_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        compile(source, "candlestick_pattern_context_reliability_strategy.py", "exec")
        self.assertIn(
            "factor_id: tomac_idxfut_clean_candlestick_pattern_context_reliability_gate_15m_v1",
            source,
        )
        self.assertIn("PriceActionPatternReliability", source)
        self.assertIn("bullish_engulfing_shifted", source)
        self.assertIn("bearish_engulfing_shifted", source)
        self.assertIn("bullish_marubozu_shifted", source)
        self.assertIn("bearish_marubozu_shifted", source)
        self.assertIn("candlestick_context_reliability_long", source)
        self.assertIn("candlestick_context_reliability_short", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_outright_filter_rejects_calendar_spreads(self) -> None:
        module = self.load_module()

        self.assertTrue(module.is_outright_contract("ESM5", "ES"))
        self.assertTrue(module.is_outright_contract("YMU25", "YM"))
        self.assertTrue(module.is_outright_contract("NQH6", "NQ"))
        self.assertTrue(module.is_outright_contract("GCG1", "XAU"))
        self.assertFalse(module.is_outright_contract("ESM1-ESU1", "ES"))
        self.assertFalse(module.is_outright_contract("ESM5/ESU5", "ES"))
        self.assertFalse(module.is_outright_contract("MESH5", "ES"))
        self.assertFalse(module.is_outright_contract("GCG1-GCJ1", "XAU"))

    def test_selects_current_highest_volume_outright_per_timestamp(self) -> None:
        module = self.load_module()
        frame = pd.DataFrame(
            [
                {
                    "date": "2025-03-17T13:30:00Z",
                    "symbol": "ESH5",
                    "open": 5200,
                    "high": 5201,
                    "low": 5199,
                    "close": 5200.5,
                    "volume": 10,
                },
                {
                    "date": "2025-03-17T13:30:00Z",
                    "symbol": "ESM5",
                    "open": 5210,
                    "high": 5211,
                    "low": 5209,
                    "close": 5210.5,
                    "volume": 300,
                },
                {
                    "date": "2025-03-17T13:30:00Z",
                    "symbol": "ESH5-ESM5",
                    "open": 10,
                    "high": 11,
                    "low": 9,
                    "close": 10.5,
                    "volume": 9999,
                },
                {
                    "date": "2025-03-17T13:31:00Z",
                    "symbol": "ESH5",
                    "open": 5200.5,
                    "high": 5202,
                    "low": 5200,
                    "close": 5201.5,
                    "volume": 400,
                },
                {
                    "date": "2025-03-17T13:31:00Z",
                    "symbol": "ESM5",
                    "open": 5210.5,
                    "high": 5212,
                    "low": 5210,
                    "close": 5211.5,
                    "volume": 200,
                },
            ]
        )

        selected, stats = module.select_front_outright_rows(frame, "ES")

        self.assertEqual(list(selected["contract"]), ["ESM5", "ESH5"])
        self.assertEqual(stats["spread_rows_dropped"], 1)
        self.assertEqual(stats["duplicate_timestamp_rows_dropped"], 2)

    def test_selects_xau_gc_outrights_instead_of_dropping_every_row(self) -> None:
        module = self.load_module()
        frame = pd.DataFrame(
            [
                {
                    "date": "2025-03-17T13:30:00Z",
                    "symbol": "GCG5",
                    "open": 2300.0,
                    "high": 2301.0,
                    "low": 2299.0,
                    "close": 2300.5,
                    "volume": 120,
                },
                {
                    "date": "2025-03-17T13:30:00Z",
                    "symbol": "GCG5-GCJ5",
                    "open": 1.0,
                    "high": 1.2,
                    "low": 0.8,
                    "close": 1.1,
                    "volume": 9999,
                },
                {
                    "date": "2025-03-17T13:31:00Z",
                    "symbol": "GCJ5",
                    "open": 2301.0,
                    "high": 2302.0,
                    "low": 2300.0,
                    "close": 2301.5,
                    "volume": 200,
                },
            ]
        )

        selected, stats = module.select_front_outright_rows(frame, "XAU")

        self.assertEqual(list(selected["contract"]), ["GCG5", "GCJ5"])
        self.assertEqual(stats["spread_rows_dropped"], 1)
        self.assertEqual(stats["duplicate_timestamp_rows_dropped"], 0)

    def test_back_adjust_uses_only_boundary_prices_and_writes_ledger(self) -> None:
        module = self.load_module()
        frame = pd.DataFrame(
            [
                {
                    "date": "2025-03-17T13:30:00Z",
                    "contract": "ESH5",
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0,
                    "volume": 10,
                },
                {
                    "date": "2025-03-17T13:31:00Z",
                    "contract": "ESM5",
                    "open": 110.0,
                    "high": 111.0,
                    "low": 109.0,
                    "close": 110.5,
                    "volume": 20,
                },
                {
                    "date": "2025-03-17T13:32:00Z",
                    "contract": "ESM5",
                    "open": 110.5,
                    "high": 112.0,
                    "low": 110.0,
                    "close": 111.0,
                    "volume": 25,
                },
            ]
        )

        adjusted, ledger = module.back_adjust_rolls(frame, symbol="ES")

        self.assertEqual(len(ledger), 1)
        self.assertEqual(ledger[0]["old_contract"], "ESH5")
        self.assertEqual(ledger[0]["new_contract"], "ESM5")
        self.assertEqual(ledger[0]["prev_raw_close"], 100.0)
        self.assertEqual(ledger[0]["new_raw_open"], 110.0)
        self.assertEqual(ledger[0]["adjustment_delta"], -10.0)
        self.assertEqual(float(adjusted.iloc[1]["open"]), 100.0)
        self.assertEqual(float(adjusted.iloc[1]["close"]), 100.5)
        self.assertEqual(float(adjusted.iloc[2]["close"]), 101.0)

    def test_resample_timeframes_from_clean_one_minute(self) -> None:
        module = self.load_module()
        frame = pd.DataFrame(
            {
                "date": pd.date_range("2025-03-17T13:30:00Z", periods=5, freq="1min"),
                "open": [1, 2, 3, 4, 5],
                "high": [2, 3, 4, 5, 6],
                "low": [0, 1, 2, 3, 4],
                "close": [1.5, 2.5, 3.5, 4.5, 5.5],
                "volume": [10, 20, 30, 40, 50],
            }
        )

        resampled = module.resample_clean_ohlcv(frame, "5m")

        self.assertEqual(len(resampled), 1)
        self.assertEqual(float(resampled.iloc[0]["open"]), 1.0)
        self.assertEqual(float(resampled.iloc[0]["high"]), 6.0)
        self.assertEqual(float(resampled.iloc[0]["low"]), 0.0)
        self.assertEqual(float(resampled.iloc[0]["close"]), 5.5)
        self.assertEqual(float(resampled.iloc[0]["volume"]), 150.0)

    def test_dense_calendar_for_aq_fills_only_from_past_close(self) -> None:
        module = self.load_module()
        frame = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    ["2025-03-17T13:30:00Z", "2025-03-17T13:40:00Z"],
                    utc=True,
                ),
                "open": [100.0, 103.0],
                "high": [101.0, 104.0],
                "low": [99.0, 102.0],
                "close": [100.5, 103.5],
                "volume": [10.0, 20.0],
            }
        )

        dense, stats = module.dense_calendar_for_aq(frame, "5m")

        self.assertEqual(list(dense["date"].dt.strftime("%H:%M")), ["13:30", "13:35", "13:40"])
        fill_row = dense.iloc[1]
        self.assertEqual(float(fill_row["open"]), 100.5)
        self.assertEqual(float(fill_row["high"]), 100.5)
        self.assertEqual(float(fill_row["low"]), 100.5)
        self.assertEqual(float(fill_row["close"]), 100.5)
        self.assertEqual(float(fill_row["volume"]), 0.0)
        self.assertEqual(stats["filled_rows"], 1)
        self.assertFalse(stats["future_lookahead"])

    def test_clean_source_to_1m_records_eth_full_session_coverage(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "es.csv"
            pd.DataFrame(
                [
                    {
                        "ts_event": "2025-03-17T08:00:00.000000000Z",
                        "open": 100.0,
                        "high": 101.0,
                        "low": 99.0,
                        "close": 100.5,
                        "volume": 10,
                        "symbol": "ESH5",
                    },
                    {
                        "ts_event": "2025-03-17T13:30:00.000000000Z",
                        "open": 101.0,
                        "high": 102.0,
                        "low": 100.0,
                        "close": 101.5,
                        "volume": 20,
                        "symbol": "ESH5",
                    },
                    {
                        "ts_event": "2025-03-17T21:30:00.000000000Z",
                        "open": 102.0,
                        "high": 103.0,
                        "low": 101.0,
                        "close": 102.5,
                        "volume": 30,
                        "symbol": "ESH5",
                    },
                ]
            ).to_csv(csv_path, index=False)

            _, _, stats = module.clean_source_to_1m(
                module.TomacSource(symbol="ES", source_csv=csv_path),
                start="2025-03-17",
                end="2025-03-17",
                chunksize=2,
            )

        self.assertEqual(stats["session_scope"], "ETH/full_retained_session")
        self.assertFalse(stats["rth_filter_applied"])
        self.assertTrue(stats["eth_full_retained_session_evidence"])
        self.assertEqual(stats["eth_full_retained_coverage_status"], "verified_retained_rows_outside_rth")
        self.assertEqual(stats["outside_rth_1m_rows"], 2)
        self.assertEqual(stats["rth_1m_rows"], 1)
        self.assertIn("outside CME/CBOT equity-index RTH", stats["session_coverage_evidence"])

    def test_generated_strategy_shifts_entry_and_exit_signals(self) -> None:
        module = self.load_module()

        source = module.strategy_source(module.candidate_specs()[0], symbol="ES", timeframe="5m")

        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("exit_raw.shift(1)", source)
        self.assertIn('metadata.get("pair") != "ES/USD"', source)
        self.assertIn("factor_id: tomac_idxfut_clean_opening_drive_rvol_vwap_continuation_5m_v1", source)
        self.assertIn(
            "branch_path: TrendExpansion -> SessionLiquidity -> "
            "OpeningDriveRvolVwapContinuation -> "
            "tomac_idxfut_clean_opening_drive_rvol_vwap_continuation_5m_v1",
            source,
        )
        self.assertNotIn("shift(-", source)

    def test_sanitize_aq_subprocess_env_disables_user_site_and_path_injection(self) -> None:
        module = self.load_module()

        env = {
            "PATH": "/usr/bin:/bin",
            "PYTHONPATH": "/tmp/bad/site-packages",
            "PYTHONHOME": "/tmp/bad/home",
            "PYTHONUSERBASE": "/tmp/bad/userbase",
        }

        sanitized = module.sanitize_aq_subprocess_env(env)

        self.assertEqual(sanitized["PATH"], "/usr/bin:/bin")
        self.assertEqual(sanitized["PYTHONNOUSERSITE"], "1")
        self.assertNotIn("PYTHONPATH", sanitized)
        self.assertNotIn("PYTHONHOME", sanitized)
        self.assertNotIn("PYTHONUSERBASE", sanitized)

    def test_run_stages_aq_only_for_symbols_with_cleaned_sources(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "root"
            compact = Path(tmpdir) / "compact"
            source = module.TomacSource(symbol="NQ", source_csv=Path("/tmp/nq.csv"))
            staged_symbols = []

            module.source_universe = lambda: [source]
            module.write_clean_bundle = lambda *args, **kwargs: {"symbol": source.symbol}

            def fake_stage_aq_inputs(*args, **kwargs):
                staged_symbols.extend(kwargs["symbols"])
                return {"workspace": str(root / "aq_workspace"), "strategy_specs": []}

            module.stage_aq_inputs = fake_stage_aq_inputs

            args = argparse.Namespace(
                root=str(root),
                compact_root=str(compact),
                symbols="NQ,XAU",
                start="2021-01-01",
                end="2021-01-02",
                timeframes="1m",
                families=None,
                max_rows=None,
                chunksize=10,
                reuse_clean=False,
                aq_smoke_timeframe="1m",
                aq_symbol_limit=2,
                clean_only=True,
                timeout=1,
            )

            summary = module.run(args)

            self.assertEqual(staged_symbols, ["NQ"])
            self.assertEqual(summary["raw_requested_symbols"], ["NQ", "XAU"])
            self.assertEqual(summary["requested_symbols"], ["NQ", "GC"])
            self.assertEqual(summary["symbol_aliases"], [{"requested": "XAU", "canonical": "GC"}])
            self.assertEqual(summary["symbols"], ["NQ"])
            self.assertEqual(summary["skipped_symbols"], ["GC"])

    def test_run_stages_gc_when_legacy_xau_is_requested_and_supported_by_default_source_universe(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "root"
            compact = Path(tmpdir) / "compact"
            staged_symbols = []

            module.write_clean_bundle = lambda source, **kwargs: {"symbol": source.symbol}

            def fake_stage_aq_inputs(*args, **kwargs):
                staged_symbols.extend(kwargs["symbols"])
                return {"workspace": str(root / "aq_workspace"), "strategy_specs": []}

            module.stage_aq_inputs = fake_stage_aq_inputs

            args = argparse.Namespace(
                root=str(root),
                compact_root=str(compact),
                symbols="NQ,XAU",
                start="2021-01-01",
                end="2021-01-02",
                timeframes="1m",
                families=None,
                max_rows=None,
                chunksize=10,
                reuse_clean=False,
                aq_smoke_timeframe="1m",
                aq_symbol_limit=2,
                clean_only=True,
                timeout=1,
            )

            summary = module.run(args)

            self.assertEqual(staged_symbols, ["NQ", "GC"])
            self.assertEqual(summary["raw_requested_symbols"], ["NQ", "XAU"])
            self.assertEqual(summary["requested_symbols"], ["NQ", "GC"])
            self.assertEqual(summary["symbol_aliases"], [{"requested": "XAU", "canonical": "GC"}])
            self.assertEqual(summary["symbols"], ["NQ", "GC"])
            self.assertEqual(summary["skipped_symbols"], [])

    def test_run_cmd_timeout_normalizes_bytes_from_timeout_expired(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "root"
            root.mkdir(parents=True, exist_ok=True)
            with patch.object(
                module.subprocess,
                "run",
                side_effect=TimeoutExpired(["fake"], timeout=1, output=b"raw-out", stderr=b"raw-err"),
            ):
                result = module.run_cmd(root, "timeout_bytes_object", ["fake"], root, timeout=1)

            self.assertEqual(result["exit"], 124)
            self.assertTrue(result["timed_out"])
            self.assertIn("raw-err", (root / "command-output/timeout_bytes_object.err").read_text())
            self.assertIn("raw-out", (root / "command-output/timeout_bytes_object.out").read_text())

    def test_claim_collision_guard_blocks_foreign_active_claim_before_aq(self) -> None:
        module = self.load_module()

        audit = {
            "claims": [
                {
                    "claim_file": "foreign.claim",
                    "status": "active",
                    "coordination_only": False,
                    "run_root": "/tmp/foreign-root",
                    "tmp_root": "/tmp/foreign-root",
                    "scope": "foreign Board B lane",
                },
                {
                    "claim_file": "own.claim",
                    "status": "active",
                    "coordination_only": False,
                    "run_root": "/tmp/own-root",
                    "tmp_root": "/tmp/own-root",
                    "scope": "own Board B lane",
                },
            ],
            "live_factor_processes": [
                {"pid": 123, "run_root": "/tmp/foreign-live", "command_excerpt": "run_tomac.py"}
            ],
        }

        guard = module.claim_collision_blockers(audit, allowed_roots={Path("/tmp/own-root")})

        self.assertFalse(guard["pass"])
        self.assertEqual([item["claim_file"] for item in guard["foreign_active_claims"]], ["foreign.claim"])
        self.assertEqual([item["pid"] for item in guard["foreign_live_processes"]], [123])

    def test_claim_collision_guard_allows_own_active_claim(self) -> None:
        module = self.load_module()

        audit = {
            "claims": [
                {
                    "claim_file": "own.claim",
                    "status": "active",
                    "coordination_only": False,
                    "run_root": "/tmp/own-root",
                    "tmp_root": "/tmp/own-root",
                    "scope": "own Board B lane",
                }
            ],
            "live_factor_processes": [],
        }

        guard = module.claim_collision_blockers(audit, allowed_roots={Path("/tmp/own-root")})

        self.assertTrue(guard["pass"])
        self.assertEqual(guard["foreign_active_claims"], [])
        self.assertEqual(guard["foreign_live_processes"], [])

    def test_claim_collision_guard_allows_parent_claim_root_for_child_aq_root(self) -> None:
        module = self.load_module()

        audit = {
            "claims": [
                {
                    "claim_file": "own-parent.claim",
                    "status": "active",
                    "coordination_only": False,
                    "run_root": "/tmp/own-root",
                    "tmp_root": "/tmp/own-root",
                    "scope": "own Board B parent lane",
                }
            ],
            "live_factor_processes": [],
        }

        roots = module.allowed_collision_roots(Path("/tmp/own-root/aq"), Path("/repo/runs/own"))
        guard = module.claim_collision_blockers(audit, allowed_roots=roots)

        self.assertTrue(guard["pass"])
        self.assertEqual(guard["foreign_active_claims"], [])

    def test_claim_collision_guard_allows_parent_process_root_for_child_run_root(self) -> None:
        module = self.load_module()

        audit = {
            "claims": [],
            "live_factor_processes": [
                {
                    "pid": 456,
                    "run_root": "/tmp/own-root",
                    "command_excerpt": "run_tomac_index_futures_clean_aq_v1.py --root /tmp/own-root/run",
                }
            ],
        }

        roots = module.allowed_collision_roots(Path("/tmp/own-root/run"), Path("/repo/runs/own"))
        guard = module.claim_collision_blockers(audit, allowed_roots=roots)

        self.assertTrue(guard["pass"])
        self.assertEqual(guard["foreign_live_processes"], [])

    def test_run_blocks_foreign_claim_before_cleaning_or_staging_when_aq_enabled(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "root"
            compact = Path(tmpdir) / "compact"
            source = module.TomacSource(symbol="ES", source_csv=Path("/tmp/es.csv"))
            calls = {"clean": 0, "stage": 0}

            module.source_universe = lambda: [source]

            def fake_write_clean_bundle(*args, **kwargs):
                calls["clean"] += 1
                return {"symbol": source.symbol}

            def fake_stage_aq_inputs(*args, **kwargs):
                calls["stage"] += 1
                return {"workspace": str(root / "aq_workspace"), "strategy_specs": []}

            def fake_guard(*args, **kwargs):
                self.assertEqual(args[:2], (root, compact))
                self.assertEqual(kwargs["allowed_roots"], module.allowed_collision_roots(root, compact))
                return {
                    "pass": False,
                    "decision": "launch_blocked_by_foreign_claim_or_runtime",
                    "foreign_active_claims": [{"claim_file": "foreign.claim"}],
                    "foreign_live_processes": [],
                }

            module.write_clean_bundle = fake_write_clean_bundle
            module.stage_aq_inputs = fake_stage_aq_inputs
            module.run_claim_collision_audit = fake_guard

            args = argparse.Namespace(
                root=str(root),
                compact_root=str(compact),
                symbols="ES",
                start="2021-01-01",
                end="2021-01-02",
                timeframes="1m",
                families=None,
                max_rows=None,
                chunksize=10,
                reuse_clean=False,
                aq_smoke_timeframe="1m",
                aq_symbol_limit=1,
                clean_only=False,
                timeout=1,
            )

            summary = module.run(args)

            self.assertEqual(calls, {"clean": 0, "stage": 0})
            self.assertEqual(summary["decision"], "launch_blocked_by_foreign_claim_or_runtime")
            self.assertEqual(summary["clean_bundles"], [])
            self.assertEqual(summary["aq_staging"], [])
            self.assertFalse(summary["promotion_allowed"])
            self.assertFalse(summary["trade_usable"])

    def test_blocked_relaunch_preserves_prior_aq_readback_compactly(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "root"
            compact = Path(tmpdir) / "compact"
            summaries = root / "summaries"
            checks = root / "checks"
            summaries.mkdir(parents=True)
            checks.mkdir(parents=True)
            (summaries / "autoquant_clean_1h_gate.json").write_text(
                json.dumps(
                    {
                        "timeframe": "1h",
                        "command": {"argv": ["run_tomac.py"], "stdout_path": "/tmp/heavy.out"},
                        "decision": "observation_no_autoquant_survivor_yet",
                        "downstream_allowed": False,
                        "pre_bayes_allowed": False,
                        "bbn_allowed": False,
                        "catboost_allowed": False,
                        "execution_tree_allowed": False,
                        "promotion_allowed": False,
                        "trade_usable": False,
                        "update_goal": False,
                        "survivors_instrument_cost": [],
                        "raw_survivors_before_session_scope": [{"pair": "NQ/USDT"}],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (checks / "run_tomac_1h.exit").write_text("0\n", encoding="utf-8")
            (root / "summary.json").write_text(
                json.dumps(
                    {
                        "decision": "observation_no_autoquant_survivor_yet",
                        "aq_gate_summaries": [{"timeframe": "1h"}],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            module.source_universe = lambda: [module.TomacSource(symbol="ES", source_csv=Path("/tmp/es.csv"))]

            def fake_guard(*args, **kwargs):
                return {
                    "pass": False,
                    "decision": "launch_blocked_by_foreign_claim_or_runtime",
                    "foreign_active_claims": [],
                    "foreign_live_processes": [{"run_root": "/tmp/foreign"}],
                }

            module.run_claim_collision_audit = fake_guard

            args = argparse.Namespace(
                root=str(root),
                compact_root=str(compact),
                symbols="ES",
                start="2021-01-01",
                end="2021-01-02",
                timeframes="1h",
                families=None,
                max_rows=None,
                chunksize=10,
                reuse_clean=True,
                aq_smoke_timeframe="1h",
                aq_symbol_limit=1,
                clean_only=False,
                timeout=1,
            )

            summary = module.run(args)

            self.assertEqual(summary["decision"], "launch_blocked_by_foreign_claim_or_runtime")
            self.assertEqual(summary["aq_commands"], [])
            self.assertEqual(summary["aq_gate_summaries"], [])
            prior = summary["prior_aq_readback"]
            self.assertTrue(prior["present"])
            self.assertEqual(prior["summary_decision"], "observation_no_autoquant_survivor_yet")
            self.assertEqual(prior["summary_aq_gate_count"], 1)
            self.assertEqual(prior["gate_summary_count"], 1)
            self.assertEqual(prior["exit_file_count"], 1)
            self.assertEqual(prior["exit_files"][0]["exit_code"], "0")
            self.assertEqual(prior["gate_summaries"][0]["file"], "summaries/autoquant_clean_1h_gate.json")
            self.assertEqual(prior["gate_summaries"][0]["timeframe"], "1h")
            self.assertEqual(
                prior["gate_summaries"][0]["decision"],
                "observation_no_autoquant_survivor_yet",
            )
            self.assertEqual(prior["gate_summaries"][0]["raw_survivors_before_session_scope_count"], 1)
            self.assertNotIn("command", prior["gate_summaries"][0])
            self.assertFalse(prior["gate_summaries"][0]["promotion_allowed"])
            self.assertFalse(prior["gate_summaries"][0]["trade_usable"])
            self.assertFalse(prior["gate_summaries"][0]["update_goal"])
            self.assertFalse(prior["gate_summaries"][0]["prior_gate_practical_flags_observed"])
            self.assertFalse(prior["gate_summaries"][0]["prior_gate_promotion_allowed"])
            self.assertFalse(prior["gate_summaries"][0]["prior_gate_trade_usable"])
            self.assertFalse(prior["gate_summaries"][0]["prior_gate_update_goal"])
            self.assertFalse(summary["promotion_allowed"])
            self.assertFalse(summary["trade_usable"])

    def test_prior_aq_readback_fails_closed_for_practical_flags(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "root"
            summaries = root / "summaries"
            summaries.mkdir(parents=True)
            (summaries / "autoquant_clean_1h_gate.json").write_text(
                json.dumps(
                    {
                        "timeframe": "1h",
                        "decision": "legacy_claimed_practical",
                        "downstream_allowed": True,
                        "pre_bayes_allowed": True,
                        "bbn_allowed": True,
                        "catboost_allowed": True,
                        "execution_tree_allowed": True,
                        "promotion_allowed": True,
                        "trade_usable": True,
                        "update_goal": True,
                        "survivors_instrument_cost": [{"pair": "NQ/USDT"}],
                        "raw_survivors_before_session_scope": [{"pair": "NQ/USDT"}],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            prior = module.compact_prior_aq_readback(root)

            self.assertEqual(prior["gate_summary_count"], 1)
            gate = prior["gate_summaries"][0]
            self.assertTrue(gate["prior_gate_practical_flags_observed"])
            self.assertFalse(gate["promotion_allowed"])
            self.assertFalse(gate["trade_usable"])
            self.assertFalse(gate["update_goal"])
            self.assertFalse(gate["prior_gate_promotion_allowed"])
            self.assertFalse(gate["prior_gate_trade_usable"])
            self.assertFalse(gate["prior_gate_update_goal"])

    def test_legacy_xau_cost_lookup_normalizes_to_verified_gc_profile(self) -> None:
        module = self.load_module()

        profile = module.futures_cost_profile(module.cost_profile_symbol_for_source("XAU"))

        self.assertIsNotNone(profile)
        self.assertEqual(profile.root_symbol, "GC")
        self.assertEqual(profile.profile_id, "COMEX_GC_IBKR_verified_20260530_v1")
        self.assertEqual(module.product_label_for_symbol("XAU"), "precious_metals_futures")

    def test_generated_strategy_for_vwap_killzone_child_keeps_child_branch_grammar(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "vwap_reclaim_persistence_killzone_filter"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn(
            "branch_path: RangeTransition -> VWAPMeanReclaim -> "
            "VwapReclaimPersistence -> KillzoneFilter -> "
            "tomac_idxfut_clean_vwap_reclaim_persistence_killzone_filter_1m_v1",
            source,
        )
        self.assertIn('elif "vwap_reclaim_persistence_killzone_filter" == "vwap_reclaim_persistence_killzone_filter":', source)
        self.assertIn("killzone_window = (", source)
        self.assertIn("reclaim_long", source)
        self.assertIn("reclaim_short", source)

    def test_generated_strategy_for_vwap_rvol_trend_quality_child_keeps_exact_branch_and_mtf_context(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "vwap_reclaim_rvol_trend_quality_filter"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn("can_short = True", source)
        self.assertIn(
            "branch_path: RangeTransition -> VWAPMeanReclaim -> "
            "VwapReclaimPersistence -> RvolTrendQualityFilter -> "
            "tomac_idxfut_clean_vwap_reclaim_rvol_trend_quality_filter_1m_v1",
            source,
        )
        self.assertIn(
            'elif "vwap_reclaim_rvol_trend_quality_filter" == '
            '"vwap_reclaim_rvol_trend_quality_filter":',
            source,
        )
        self.assertIn("pd.merge_asof", source)
        self.assertIn("trend_aligned_votes", source)
        self.assertIn("trend_counter_votes", source)
        self.assertIn("rolling(5).sum().ge(5)", source)
        self.assertIn('dataframe["trend_counter_votes"].ge(1)', source)
        self.assertIn("distance_quality = vwap_dist_atr.le(0.6)", source)
        self.assertIn("vwap_quality_any", source)
        self.assertIn("vwap_quality_first_daily", source)
        self.assertRegex(
            source,
            r'vwap_quality_any\.groupby\(\s*dataframe\["date"\]\.dt\.strftime\("%Y-%m-%d"\)\s*\)\.cumsum\(\)\.eq\(1\)',
        )
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_generated_strategy_for_impulse_hold_persistence_child_keeps_child_branch_grammar(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "impulse_follow_hold_persistence"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn(
            "branch_path: TrendExpansion -> ImpulseFollowThrough -> HoldPersistence -> "
            "tomac_idxfut_clean_impulse_follow_hold_persistence_1m_v1",
            source,
        )
        self.assertIn('elif "impulse_follow_hold_persistence" == "impulse_follow_hold_persistence":', source)
        self.assertIn("hold_persistence = (", source)
        self.assertIn("trend_root", source)
        self.assertIn("continuation", source)

    def test_candidate_specs_include_impulse_hold_persistence_child(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["impulse_follow_hold_persistence"].branch_path,
            "TrendExpansion -> ImpulseFollowThrough -> HoldPersistence",
        )

    def test_generated_strategy_for_vwap_rvol_trend_quality_child_keeps_child_branch_grammar(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "vwap_reclaim_rvol_trend_quality_filter"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn(
            "branch_path: RangeTransition -> VWAPMeanReclaim -> "
            "VwapReclaimPersistence -> RvolTrendQualityFilter -> "
            "tomac_idxfut_clean_vwap_reclaim_rvol_trend_quality_filter_1m_v1",
            source,
        )
        self.assertIn(
            'elif "vwap_reclaim_rvol_trend_quality_filter" == "vwap_reclaim_rvol_trend_quality_filter":',
            source,
        )
        self.assertIn("vwap_quality_persistence = (", source)
        self.assertIn("trend_quality_ok = (", source)
        self.assertIn("rvol_quality_ok = dataframe[\"rvol96\"].between(0.80, 5.0)", source)

    def test_candidate_specs_include_vwap_rvol_trend_quality_child(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["vwap_reclaim_rvol_trend_quality_filter"].branch_path,
            "RangeTransition -> VWAPMeanReclaim -> VwapReclaimPersistence -> RvolTrendQualityFilter",
        )

    def test_generated_strategy_for_camarilla_r3_s3_reclaim_keeps_exact_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "camarilla_r3_s3_reclaim"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> CamarillaPivotReclaim -> camarilla_r3_s3_reclaim_v1",
        )
        self.assertIn("can_short = True", source)
        self.assertIn(
            "branch_path: RangeReversion -> CamarillaPivotReclaim -> "
            "camarilla_r3_s3_reclaim_v1 -> "
            "tomac_idxfut_clean_camarilla_r3_s3_reclaim_1m_v1",
            source,
        )
        self.assertIn(
            'elif "camarilla_r3_s3_reclaim" == "camarilla_r3_s3_reclaim":',
            source,
        )
        self.assertIn('dataframe["camarilla_r3"]', source)
        self.assertIn('dataframe["camarilla_s3"]', source)
        self.assertIn('dataframe["camarilla_s4"]', source)
        self.assertIn("s3_reclaim", source)
        self.assertIn("r3_reclaim", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)

    def test_candidate_specs_include_camarilla_r3_s3_reclaim(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(by_key["camarilla_r3_s3_reclaim"].direction, "long_short")
        self.assertEqual(
            by_key["camarilla_r3_s3_reclaim"].branch_path,
            "RangeReversion -> CamarillaPivotReclaim -> camarilla_r3_s3_reclaim_v1",
        )

    def test_generated_strategy_for_nr7_excursion_cap_child_keeps_child_branch_grammar(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "nr7_range_expansion_excursion_cap"
        )
        source = module.strategy_source(spec, symbol="6E", timeframe="1m")

        self.assertIn(
            "branch_path: RangeConsolidation -> NarrowRangeCompression -> Nr7RangeExpansion -> ExcursionCap -> "
            "tomac_idxfut_clean_nr7_range_expansion_excursion_cap_1m_v1",
            source,
        )
        self.assertIn('elif "nr7_range_expansion_excursion_cap" == "nr7_range_expansion_excursion_cap":', source)
        self.assertIn("nr7_range = dataframe[\"prior_nr7\"].fillna(False)", source)
        self.assertIn("vwap_excursion_ok", source)
        self.assertIn("reclaim_discount_ok", source)

    def test_candidate_specs_include_nr7_excursion_cap_child(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["nr7_range_expansion_excursion_cap"].branch_path,
            "RangeConsolidation -> NarrowRangeCompression -> Nr7RangeExpansion -> ExcursionCap",
        )

    def test_generated_strategy_for_nr7_vwap_hold_persistence_child_keeps_child_branch_grammar(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "nr7_range_expansion_vwap_hold_persistence"
        )
        source = module.strategy_source(spec, symbol="6E", timeframe="1m")

        self.assertIn(
            "branch_path: RangeConsolidation -> NarrowRangeCompression -> Nr7RangeExpansion -> VwapHoldPersistence -> "
            "tomac_idxfut_clean_nr7_range_expansion_vwap_hold_persistence_1m_v1",
            source,
        )
        self.assertIn(
            'elif "nr7_range_expansion_vwap_hold_persistence" == "nr7_range_expansion_vwap_hold_persistence":',
            source,
        )
        self.assertIn("nr7_range = dataframe[\"prior_nr7\"].fillna(False)", source)
        self.assertIn("vwap_hold_bias", source)
        self.assertIn("session_participation", source)

    def test_candidate_specs_include_nr7_vwap_hold_persistence_child(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["nr7_range_expansion_vwap_hold_persistence"].branch_path,
            "RangeConsolidation -> NarrowRangeCompression -> Nr7RangeExpansion -> VwapHoldPersistence",
        )

    def test_generated_strategy_for_nr7_killzone_filter_child_keeps_child_branch_grammar(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "nr7_range_expansion_killzone_filter"
        )
        source = module.strategy_source(spec, symbol="6E", timeframe="1m")

        self.assertIn(
            "branch_path: RangeConsolidation -> NarrowRangeCompression -> Nr7RangeExpansion -> KillzoneFilter -> "
            "tomac_idxfut_clean_nr7_range_expansion_killzone_filter_1m_v1",
            source,
        )
        self.assertIn(
            'elif "nr7_range_expansion_killzone_filter" == "nr7_range_expansion_killzone_filter":',
            source,
        )
        self.assertIn("nr7_range = dataframe[\"prior_nr7\"].fillna(False)", source)
        self.assertIn("killzone_window", source)
        self.assertIn("session_participation", source)

    def test_candidate_specs_include_nr7_killzone_filter_child(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["nr7_range_expansion_killzone_filter"].branch_path,
            "RangeConsolidation -> NarrowRangeCompression -> Nr7RangeExpansion -> KillzoneFilter",
        )

    def test_generated_strategy_for_prior_day_multifactor_confluence_volume_child_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "prior_day_multifactor_confluence_volume_reclaim"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertIn(
            "branch_path: RangeReversion -> PriorDayLiquiditySweepReversal -> MultiFactorConfluenceReclaim -> VolumeConfirmation -> "
            "tomac_idxfut_clean_prior_day_multifactor_confluence_volume_reclaim_1m_v1",
            source,
        )
        self.assertIn(
            'elif "prior_day_multifactor_confluence_volume_reclaim" == '
            '"prior_day_multifactor_confluence_volume_reclaim":',
            source,
        )
        self.assertIn("can_short = True", source)
        self.assertIn("long_score = (", source)
        self.assertIn("short_score = (", source)
        self.assertIn("raw = trading_window & long_score.ge(4)", source)
        self.assertIn("short_raw = trading_window & short_score.ge(4)", source)
        self.assertIn("extreme_wpr_long = dataframe[\"wpr14\"].lt(-85)", source)
        self.assertIn("extreme_wpr_short = dataframe[\"wpr14\"].gt(-15)", source)
        self.assertIn("volume_confirm = dataframe[\"rvol20\"].gt(1.2)", source)
        self.assertIn("low_vol_env = dataframe[\"atr14\"] < dataframe[\"atr_ma50\"]", source)
        self.assertIn("trend_ok_long = dataframe[\"ema20\"] > dataframe[\"ema50\"]", source)
        self.assertIn("trend_ok_short = dataframe[\"ema20\"] < dataframe[\"ema50\"]", source)

    def test_candidate_specs_include_prior_day_multifactor_confluence_volume_child(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["prior_day_multifactor_confluence_volume_reclaim"].direction,
            "long_short",
        )
        self.assertEqual(
            by_key["prior_day_multifactor_confluence_volume_reclaim"].branch_path,
            "RangeReversion -> PriorDayLiquiditySweepReversal -> MultiFactorConfluenceReclaim -> VolumeConfirmation",
        )

    def test_generated_strategy_for_prior_day_extreme_killzone_child_keeps_same_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "prior_day_extreme_continuation_mtf_resonance_guard_killzone_filter"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn(
            "branch_path: TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> KillzoneFilter -> "
            "tomac_idxfut_clean_prior_day_extreme_continuation_mtf_resonance_guard_killzone_filter_1m_v1",
            source,
        )
        self.assertIn(
            'elif "prior_day_extreme_continuation_mtf_resonance_guard_killzone_filter" == '
            '"prior_day_extreme_continuation_mtf_resonance_guard_killzone_filter":',
            source,
        )
        self.assertIn("killzone_window", source)
        self.assertIn("session_participation", source)
        self.assertIn("prior_day_retest", source)

    def test_candidate_specs_include_prior_day_extreme_killzone_child(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard_killzone_filter"].branch_path,
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> KillzoneFilter",
        )

    def test_generated_strategy_for_prior_day_extreme_participation_quality_guard_child_keeps_same_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn(
            "branch_path: TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> ParticipationQualityGuard -> "
            "tomac_idxfut_clean_prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard_1m_v1",
            source,
        )
        self.assertIn(
            'elif "prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard" == '
            '"prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard":',
            source,
        )
        self.assertIn("participation_impulse", source)
        self.assertIn("volume_acceptance", source)
        self.assertIn("trend_efficiency_guard", source)
        self.assertIn('dataframe["vol96"] = ', source)
        self.assertIn('dataframe["close_location"] = ', source)

    def test_candidate_specs_include_prior_day_extreme_participation_quality_guard_child(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard"].branch_path,
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> ParticipationQualityGuard",
        )

    def test_generated_strategy_for_prior_day_extreme_participation_quality_guard_nq_cadence_lift_keeps_same_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard_nq_cadence_lift"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn(
            "branch_path: TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> "
            "ParticipationQualityGuard -> NQCadenceLift -> "
            "tomac_idxfut_clean_prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard_nq_cadence_lift_1m_v1",
            source,
        )
        self.assertIn(
            'elif "prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard_nq_cadence_lift" == '
            '"prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard_nq_cadence_lift":',
            source,
        )
        self.assertIn("first_chance_window", source)
        self.assertIn("second_chance_reclaim", source)
        self.assertIn("late_morning_window", source)
        self.assertIn("post_lunch_window", source)

    def test_candidate_specs_include_prior_day_extreme_participation_quality_guard_nq_cadence_lift(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard_nq_cadence_lift"].branch_path,
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> ParticipationQualityGuard -> NQCadenceLift",
        )

    def test_generated_strategy_for_state_space_slope_dispersion_trend_hold_keeps_branch_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "state_space_slope_dispersion_trend_hold"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1h")

        self.assertIn(
            "branch_path: TrendExpansion -> StateSpaceTrendSlope -> ResidualDispersionExpansion -> "
            "CrossIndexTrendBreadth -> LowTurnoverAtrHold -> "
            "tomac_idxfut_clean_state_space_slope_dispersion_trend_hold_1h_v1",
            source,
        )
        self.assertIn(
            'elif "state_space_slope_dispersion_trend_hold" == '
            '"state_space_slope_dispersion_trend_hold":',
            source,
        )
        self.assertIn("state_slope_persistence", source)
        self.assertIn("residual_dispersion_expansion", source)
        self.assertIn("mtf_trend_breadth_confirmation", source)

    def test_candidate_specs_include_state_space_slope_dispersion_trend_hold(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["state_space_slope_dispersion_trend_hold"].branch_path,
            "TrendExpansion -> StateSpaceTrendSlope -> ResidualDispersionExpansion -> CrossIndexTrendBreadth -> LowTurnoverAtrHold",
        )

    def test_generated_strategy_for_gsadf_explosive_trend_breakout_keeps_branch_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "gsadf_explosive_trend_breakout"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1h")

        self.assertIn(
            "branch_path: TrendExpansion -> ExplosiveTrendDiagnostics -> GsadfBreakoutPersistence -> "
            "MtfSlopeConfirmation -> FrictionAwareAtrHold -> "
            "tomac_idxfut_clean_gsadf_explosive_trend_breakout_1h_v1",
            source,
        )
        self.assertIn(
            'elif "gsadf_explosive_trend_breakout" == '
            '"gsadf_explosive_trend_breakout":',
            source,
        )
        self.assertIn("explosive_trend_slope_acceleration", source)
        self.assertIn("adf_like_residual_persistence", source)
        self.assertIn("friction_aware_atr_hold", source)

    def test_candidate_specs_include_gsadf_explosive_trend_breakout(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["gsadf_explosive_trend_breakout"].branch_path,
            "TrendExpansion -> ExplosiveTrendDiagnostics -> GsadfBreakoutPersistence -> MtfSlopeConfirmation -> FrictionAwareAtrHold",
        )

    def test_generated_strategy_for_variance_ratio_serial_correlation_trend_hold_keeps_branch_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "variance_ratio_serial_correlation_trend_hold"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1h")

        self.assertIn(
            "branch_path: TrendExpansion -> VarianceRatioPersistence -> PositiveSerialCorrelationTrendHold -> "
            "MtfMomentumConfirmation -> FrictionAwareAtrHold -> "
            "tomac_idxfut_clean_variance_ratio_serial_correlation_trend_hold_1h_v1",
            source,
        )
        self.assertIn(
            'elif "variance_ratio_serial_correlation_trend_hold" == '
            '"variance_ratio_serial_correlation_trend_hold":',
            source,
        )
        self.assertIn("variance_ratio_persistence", source)
        self.assertIn("positive_serial_correlation_trend_hold", source)
        self.assertIn("friction_aware_atr_hold", source)

    def test_candidate_specs_include_variance_ratio_serial_correlation_trend_hold(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["variance_ratio_serial_correlation_trend_hold"].branch_path,
            "TrendExpansion -> VarianceRatioPersistence -> PositiveSerialCorrelationTrendHold -> MtfMomentumConfirmation -> FrictionAwareAtrHold",
        )

    def test_generated_strategy_for_teager_kaiser_energy_impulse_trend_gate_keeps_branch_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "teager_kaiser_energy_impulse_trend_gate"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn(
            "branch_path: TrendExpansion -> NonlinearEnergyImpulse -> TeagerKaiserImpulsePersistence -> "
            "MtfTrendResonance -> FrictionAwareAtrHold -> "
            "tomac_idxfut_clean_teager_kaiser_energy_impulse_trend_gate_30m_v1",
            source,
        )
        self.assertIn(
            'elif "teager_kaiser_energy_impulse_trend_gate" == '
            '"teager_kaiser_energy_impulse_trend_gate":',
            source,
        )
        self.assertIn("teager_kaiser_energy_impulse", source)
        self.assertIn("energy_impulse_persistence", source)
        self.assertIn("mtf_trend_resonance", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)

    def test_candidate_specs_include_teager_kaiser_energy_impulse_trend_gate(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["teager_kaiser_energy_impulse_trend_gate"].branch_path,
            "TrendExpansion -> NonlinearEnergyImpulse -> TeagerKaiserImpulsePersistence -> MtfTrendResonance -> FrictionAwareAtrHold",
        )

    def test_generated_strategy_for_volatility_managed_trend_size_gate_keeps_branch_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "volatility_managed_trend_size_gate"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1h")

        self.assertIn(
            "branch_path: TrendExpansion -> VolatilityManagedExposure -> RealizedVolatilityThrottle -> "
            "ParentSignalRiskThrottle -> tomac_idxfut_clean_volatility_managed_trend_size_gate_1h_v1",
            source,
        )
        self.assertIn(
            'elif "volatility_managed_trend_size_gate" == '
            '"volatility_managed_trend_size_gate":',
            source,
        )
        self.assertIn("realized_volatility_throttle", source)
        self.assertIn("volatility_stress_veto", source)
        self.assertIn("parent_trend_signal_survives", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)

    def test_candidate_specs_include_volatility_managed_trend_size_gate(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["volatility_managed_trend_size_gate"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "VolatilityManagedTrendSizeGate")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> VolatilityManagedExposure -> RealizedVolatilityThrottle -> ParentSignalRiskThrottle",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_volatility_managed_trend_size_gate_5m_v1",
                "tomac_idxfut_clean_volatility_managed_trend_size_gate_15m_v1",
                "tomac_idxfut_clean_volatility_managed_trend_size_gate_30m_v1",
                "tomac_idxfut_clean_volatility_managed_trend_size_gate_1h_v1",
                "tomac_idxfut_clean_volatility_managed_trend_size_gate_4h_v1",
                "tomac_idxfut_clean_volatility_managed_trend_size_gate_1d_v1",
            ],
        )

    def test_generated_strategy_for_mann_kendall_theil_sen_trend_gate_keeps_branch_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "mann_kendall_theil_sen_trend_gate"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1h")

        self.assertIn(
            "branch_path: TrendExpansion -> RankMonotoneTrend -> MannKendallPersistence -> "
            "TheilSenSlopeConfirmation -> FrictionAwareAtrHold -> "
            "tomac_idxfut_clean_mann_kendall_theil_sen_trend_gate_1h_v1",
            source,
        )
        self.assertIn(
            'elif "mann_kendall_theil_sen_trend_gate" == '
            '"mann_kendall_theil_sen_trend_gate":',
            source,
        )
        self.assertIn("mann_kendall_persistence", source)
        self.assertIn("theil_sen_slope_confirmation", source)
        self.assertIn("friction_aware_atr_hold", source)

    def test_candidate_specs_include_mann_kendall_theil_sen_trend_gate(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["mann_kendall_theil_sen_trend_gate"].branch_path,
            "TrendExpansion -> RankMonotoneTrend -> MannKendallPersistence -> TheilSenSlopeConfirmation -> FrictionAwareAtrHold",
        )

    def test_candidate_specs_can_select_rolling_regression_residual_trend_rejoin_gate_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["rolling_regression_residual_trend_rejoin_gate"])

        self.assertEqual([spec.key for spec in specs], ["rolling_regression_residual_trend_rejoin_gate"])
        self.assertEqual(specs[0].class_prefix, "RollingRegressionResidualTrendRejoinGate")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "RollingRegressionTrend")
        self.assertEqual(specs[0].profit_factor, "ResidualPullback")
        self.assertEqual(specs[0].child_profit_factor, "TrendLineRejoin")
        self.assertEqual(specs[0].extra_profit_factors, ("MtfSlopeResonance", "FrictionAwareAtrHold"))
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("30m"),
            "TrendExpansion -> RollingRegressionTrend -> ResidualPullback -> "
            "TrendLineRejoin -> MtfSlopeResonance -> FrictionAwareAtrHold -> "
            "tomac_idxfut_clean_rolling_regression_residual_trend_rejoin_gate_30m_v1",
        )

    def test_rolling_regression_residual_trend_rejoin_strategy_source_uses_shifted_residual_rejoin(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["rolling_regression_residual_trend_rejoin_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("factor_id: tomac_idxfut_clean_rolling_regression_residual_trend_rejoin_gate_30m_v1", source)
        self.assertIn("rolling_regression_residual", source)
        self.assertIn("regression_trendline_rejoin_long", source)
        self.assertIn("regression_trendline_rejoin_short", source)
        self.assertIn("mtf_slope_resonance_long", source)
        self.assertIn("mtf_slope_resonance_short", source)
        self.assertIn("friction_aware_atr_hold", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_elder_force_index_pullback_continuation_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["elder_force_index_pullback_continuation"])

        self.assertEqual([spec.key for spec in specs], ["elder_force_index_pullback_continuation"])
        self.assertEqual(specs[0].class_prefix, "ElderForceIndexPullbackContinuation")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "VolumeImpulseTrend")
        self.assertEqual(specs[0].profit_factor, "ElderForceIndexPullback")
        self.assertEqual(specs[0].child_profit_factor, "MtfTrendResonance")
        self.assertEqual(specs[0].extra_profit_factors, ("FrictionAwareAtrHold",))
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_elder_force_index_pullback_continuation_5m_v1",
                "tomac_idxfut_clean_elder_force_index_pullback_continuation_15m_v1",
                "tomac_idxfut_clean_elder_force_index_pullback_continuation_30m_v1",
                "tomac_idxfut_clean_elder_force_index_pullback_continuation_1h_v1",
                "tomac_idxfut_clean_elder_force_index_pullback_continuation_4h_v1",
                "tomac_idxfut_clean_elder_force_index_pullback_continuation_1d_v1",
            ],
        )

    def test_elder_force_index_pullback_strategy_source_uses_shifted_force_reacceleration(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["elder_force_index_pullback_continuation"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("factor_id: tomac_idxfut_clean_elder_force_index_pullback_continuation_30m_v1", source)
        self.assertIn("elder_force_index", source)
        self.assertIn("elder_force_index_smooth", source)
        self.assertIn("elder_force_index_slope", source)
        self.assertIn("elder_force_pullback_depth_atr", source)
        self.assertIn("elder_force_reacceleration_long", source)
        self.assertIn("elder_force_reacceleration_short", source)
        self.assertIn("mtf_trend_resonance_long", source)
        self.assertIn("mtf_trend_resonance_short", source)
        self.assertIn("friction_aware_atr_hold", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_generated_strategy_for_ultimate_ict_volume_spike_reclaim_keeps_same_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "ultimate_ict_zone_volume_spike_reclaim"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim",
        )
        self.assertIn(
            "branch_path: RangeReversion -> KillzoneLiquiditySweep -> "
            "IctZoneVolumeSpikeReclaim -> "
            "tomac_idxfut_clean_ultimate_ict_zone_volume_spike_reclaim_1m_v1",
            source,
        )
        self.assertIn(
            'elif "ultimate_ict_zone_volume_spike_reclaim" == '
            '"ultimate_ict_zone_volume_spike_reclaim":',
            source,
        )
        self.assertIn("killzone_window", source)
        self.assertIn("liquidity_sweep", source)
        self.assertIn("extreme_wpr", source)
        self.assertIn("ict_zone", source)
        self.assertIn("volume_spike", source)

    def test_generated_strategy_for_ultimate_ict_volume_spike_exit_persistence_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "ultimate_ict_zone_volume_spike_exit_persistence"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim -> ExitPersistence",
        )
        self.assertIn(
            "branch_path: RangeReversion -> KillzoneLiquiditySweep -> "
            "IctZoneVolumeSpikeReclaim -> ExitPersistence -> "
            "tomac_idxfut_clean_ultimate_ict_zone_volume_spike_exit_persistence_1m_v1",
            source,
        )
        self.assertIn(
            'elif "ultimate_ict_zone_volume_spike_exit_persistence" == '
            '"ultimate_ict_zone_volume_spike_exit_persistence":',
            source,
        )
        self.assertIn("score6_urgency", source)
        self.assertIn("persistence_window", source)
        self.assertIn("volume_spike", source)

    def test_generated_strategy_for_ultimate_ict_volume_spike_session_open_bias_cap_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "ultimate_ict_zone_volume_spike_session_open_bias_cap"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim -> SessionOpenBiasCap",
        )
        self.assertIn(
            "branch_path: RangeReversion -> KillzoneLiquiditySweep -> "
            "IctZoneVolumeSpikeReclaim -> SessionOpenBiasCap -> "
            "tomac_idxfut_clean_ultimate_ict_zone_volume_spike_session_open_bias_cap_1m_v1",
            source,
        )
        self.assertIn(
            'elif "ultimate_ict_zone_volume_spike_session_open_bias_cap" == '
            '"ultimate_ict_zone_volume_spike_session_open_bias_cap":',
            source,
        )
        self.assertIn("ny_killzone", source)
        self.assertIn("session_open_bias", source)
        self.assertIn("vwap_reclaim", source)
        self.assertIn("macd_bias", source)

    def test_generated_strategy_for_ultimate_ict_volume_spike_vwap_hold_persistence_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "ultimate_ict_zone_volume_spike_vwap_hold_persistence"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim -> VwapHoldPersistence",
        )
        self.assertIn(
            "branch_path: RangeReversion -> KillzoneLiquiditySweep -> "
            "IctZoneVolumeSpikeReclaim -> VwapHoldPersistence -> "
            "tomac_idxfut_clean_ultimate_ict_zone_volume_spike_vwap_hold_persistence_1m_v1",
            source,
        )
        self.assertIn(
            'elif "ultimate_ict_zone_volume_spike_vwap_hold_persistence" == '
            '"ultimate_ict_zone_volume_spike_vwap_hold_persistence":',
            source,
        )
        self.assertIn("vwap_reclaim", source)
        self.assertIn("vwap_hold", source)
        self.assertIn("persistence_bias", source)

    def test_generated_strategy_for_ultimate_ict_volume_spike_session_open_vwap_hold_compound_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim -> "
            "SessionOpenBiasCap -> VwapHoldPersistence",
        )
        self.assertIn(
            "branch_path: RangeReversion -> KillzoneLiquiditySweep -> "
            "IctZoneVolumeSpikeReclaim -> SessionOpenBiasCap -> VwapHoldPersistence -> "
            "tomac_idxfut_clean_ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence_1m_v1",
            source,
        )
        self.assertIn(
            'elif "ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence" == '
            '"ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence":',
            source,
        )
        self.assertIn("session_open_bias", source)
        self.assertIn("vwap_reclaim", source)
        self.assertIn("vwap_hold", source)
        self.assertIn("persistence_bias", source)

    def test_generated_strategy_for_wpr_fractal_no_be_session_bias_cap_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "wpr_fractal_no_be_session_bias_cap"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprFractalNoBreakEvenFullTarget -> SessionBiasCap",
        )
        self.assertIn(
            "branch_path: RangeReversion -> PdhPdlFractalLiquiditySweep -> "
            "WprFractalNoBreakEvenFullTarget -> SessionBiasCap -> "
            "tomac_idxfut_clean_wpr_fractal_no_be_session_bias_cap_1m_v1",
            source,
        )
        self.assertIn(
            'elif "wpr_fractal_no_be_session_bias_cap" == '
            '"wpr_fractal_no_be_session_bias_cap":',
            source,
        )
        self.assertIn("session_bias_cap_window", source)
        self.assertIn("liquidity_sweep", source)
        self.assertIn("wpr_reclaim", source)
        self.assertIn("session_open_bias", source)
        self.assertIn("vwap_hold", source)

    def test_generated_strategy_for_wpr_fractal_no_be_higher_frame_slope_confirm_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "wpr_fractal_no_be_higher_frame_slope_confirm"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprFractalNoBreakEvenFullTarget -> HigherFrameSlopeConfirm",
        )
        self.assertIn(
            "branch_path: RangeReversion -> PdhPdlFractalLiquiditySweep -> "
            "WprFractalNoBreakEvenFullTarget -> HigherFrameSlopeConfirm -> "
            "tomac_idxfut_clean_wpr_fractal_no_be_higher_frame_slope_confirm_1m_v1",
            source,
        )
        self.assertIn(
            'elif "wpr_fractal_no_be_higher_frame_slope_confirm" == '
            '"wpr_fractal_no_be_higher_frame_slope_confirm":',
            source,
        )
        self.assertIn("higher_frame_slope_confirm", source)
        self.assertIn("ema55_slope_atr", source)
        self.assertIn("ema144_slope_atr", source)
        self.assertIn("liquidity_sweep", source)

    def test_generated_strategy_for_wpr_fractal_ict_zone_reclaim_keeps_exact_source_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "wpr_fractal_ict_zone_reclaim"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprFractalIctZoneReclaim",
        )
        self.assertIn(
            "branch_path: RangeReversion -> PdhPdlFractalLiquiditySweep -> "
            "WprFractalIctZoneReclaim -> "
            "tomac_idxfut_clean_wpr_fractal_ict_zone_reclaim_1m_v1",
            source,
        )
        self.assertIn(
            'elif "wpr_fractal_ict_zone_reclaim" == '
            '"wpr_fractal_ict_zone_reclaim":',
            source,
        )
        self.assertIn("wpr14", source)
        self.assertIn("bull_fvg", source)
        self.assertIn("bear_fvg", source)
        self.assertIn("bull_ob_low", source)
        self.assertIn("bear_ob_high", source)
        self.assertIn("liquidity_sweep", source)
        self.assertIn("short_liquidity_sweep", source)
        self.assertIn("wpr_reclaim", source)
        self.assertIn("short_wpr_reclaim", source)
        self.assertIn("ict_zone", source)
        self.assertIn("short_ict_zone", source)

    def test_generated_strategy_indicators_skip_non_target_pairs_before_heavy_columns(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "wpr_fractal_ict_zone_reclaim"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        indicator_start = source.index("def populate_indicators")
        first_heavy_indicator = source.index('dataframe["ema21"] = ta.EMA', indicator_start)
        pair_guard = source.index('metadata.get("pair") != "ES/USD"', indicator_start)
        early_indicator_body = source[indicator_start:first_heavy_indicator]

        self.assertLess(pair_guard, first_heavy_indicator)
        self.assertIn('if metadata.get("pair") != "ES/USD":', early_indicator_body)
        self.assertIn("return dataframe", early_indicator_body)

    def test_generated_strategy_for_wpr_adx_fractal_sweep_reclaim_keeps_parent_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "wpr_adx_fractal_sweep_reclaim"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprAdxTrendAlignedReclaim",
        )
        self.assertIn(
            "branch_path: RangeReversion -> PdhPdlFractalLiquiditySweep -> "
            "WprAdxTrendAlignedReclaim -> "
            "tomac_idxfut_clean_wpr_adx_fractal_sweep_reclaim_1m_v1",
            source,
        )
        self.assertIn(
            'elif "wpr_adx_fractal_sweep_reclaim" == '
            '"wpr_adx_fractal_sweep_reclaim":',
            source,
        )
        self.assertIn("hour_open_bias", source)
        self.assertIn("volume_ratio", source)
        self.assertIn("adx14", source)
        self.assertIn("confirmed_ssl", source)
        self.assertIn("confirmed_bsl", source)

    def test_generated_strategy_for_wpr_adx_hurst_profile_mss_reclaim_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "wpr_adx_hurst_profile_mss_reclaim"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> "
            "WprAdxTrendAlignedReclaim -> HurstProfileMssReclaim",
        )
        self.assertIn(
            "branch_path: RangeReversion -> PdhPdlFractalLiquiditySweep -> "
            "WprAdxTrendAlignedReclaim -> HurstProfileMssReclaim -> "
            "tomac_idxfut_clean_wpr_adx_hurst_profile_mss_reclaim_1m_v1",
            source,
        )
        self.assertIn(
            'elif "wpr_adx_hurst_profile_mss_reclaim" == '
            '"wpr_adx_hurst_profile_mss_reclaim":',
            source,
        )
        self.assertIn("hurst64", source)
        self.assertIn("profile_poc96", source)
        self.assertIn("bull_mss", source)
        self.assertIn("bear_fvg", source)

    def test_generated_strategy_for_liquidity_sweep_adx_liquidity_pool_context_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "liquidity_sweep_adx_liquidity_pool_context"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> LiquiditySweepDisplacement -> "
            "AdxTrendStrengthReclaim -> LiquidityPoolContextFilter",
        )
        self.assertIn(
            "branch_path: TrendExpansion -> LiquiditySweepDisplacement -> "
            "AdxTrendStrengthReclaim -> LiquidityPoolContextFilter -> "
            "tomac_idxfut_clean_liquidity_sweep_adx_liquidity_pool_context_1m_v1",
            source,
        )
        self.assertIn(
            'elif "liquidity_sweep_adx_liquidity_pool_context" == '
            '"liquidity_sweep_adx_liquidity_pool_context":',
            source,
        )
        self.assertIn("liquidity_pool_band", source)
        self.assertIn("sellside_pool_cluster", source)
        self.assertIn("bull_mss", source)
        common_bear_fvg = 'dataframe["bear_fvg"] = dataframe["high"] < dataframe["prev2_low"]'
        first_family_branch = source.index(
            'if "liquidity_sweep_adx_liquidity_pool_context" == "wpr_adx_hurst_profile_mss_reclaim":'
        )
        self.assertLess(
            source.find(common_bear_fvg),
            first_family_branch,
        )

    def test_generated_strategy_for_value_area_vpoc_htf_trend_mss_filter_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "value_area_vpoc_htf_trend_mss_filter"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeTransition -> MarketProfileValueAreaAcceptance -> "
            "VpocReclaimContinuation -> HtfTrendResonanceMssFilter",
        )
        self.assertIn(
            "branch_path: RangeTransition -> MarketProfileValueAreaAcceptance -> "
            "VpocReclaimContinuation -> HtfTrendResonanceMssFilter -> "
            "tomac_idxfut_clean_value_area_vpoc_htf_trend_mss_filter_1m_v1",
            source,
        )
        self.assertIn(
            'elif "value_area_vpoc_htf_trend_mss_filter" == '
            '"value_area_vpoc_htf_trend_mss_filter":',
            source,
        )
        self.assertIn('for label, rule in {"5m": "5min", "15m": "15min", "30m": "30min", "1h": "1h", "4h": "4h", "1d": "1D"}.items():', source)
        self.assertIn("session_profile_poc_price", source)
        self.assertIn("session_profile_value_area_pos", source)
        self.assertIn("session_or_breakout_atr", source)
        self.assertIn("session_profile_rotation_factor", source)
        self.assertIn("trend_resonance_long", source)
        self.assertIn("bull_mss", source)
        self.assertIn("bear_fvg", source)

    def test_generated_value_area_strategy_uses_incremental_session_profile_updates(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "value_area_vpoc_htf_trend_mss_filter"
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertNotIn("open_range_rows = [row for row in session_rows if row[0] <= open_range_end]", source)
        self.assertNotIn("initial_balance_rows = [row for row in session_rows if row[0] <= initial_balance_end]", source)
        self.assertNotIn("for _, _, _, close_value, volume_value in session_rows:", source)
        self.assertNotIn("ts_local.normalize() + pd.Timedelta(hours=9, minutes=30)", source)
        self.assertNotIn("open_range_end = current_anchor + pd.Timedelta(minutes=10)", source)
        self.assertIn("or_high = max(or_high, highs[idx])", source)
        self.assertIn("ib_high = max(ib_high, highs[idx])", source)
        self.assertIn("profile_map[level] = profile_map.get(level, 0.0) + max(float(volumes[idx]), 0.0)", source)
        self.assertIn("minute_of_day = (ny_dates.dt.hour * 60 + ny_dates.dt.minute).to_numpy(dtype=int)", source)
        self.assertIn("session_minute = minute_of_day[idx]", source)

    def test_generated_strategy_for_wpr_fractal_no_be_fulltarget_keeps_parent_root(self) -> None:
        module = self.load_module()

        spec = module.candidate_specs(families=["wpr_fractal_no_be_fulltarget"])[0]
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprFractalNoBreakEvenFullTarget",
        )
        self.assertIn(
            "branch_path: RangeReversion -> PdhPdlFractalLiquiditySweep -> "
            "WprFractalNoBreakEvenFullTarget -> "
            "tomac_idxfut_clean_wpr_fractal_no_be_fulltarget_1m_v1",
            source,
        )
        self.assertIn(
            'elif "wpr_fractal_no_be_fulltarget" == '
            '"wpr_fractal_no_be_fulltarget":',
            source,
        )
        self.assertIn("liquidity_sweep", source)
        self.assertIn("wpr_reclaim", source)
        self.assertIn("full_target_bias", source)
        self.assertIn("can_short = True", source)
        self.assertIn("short_liquidity_sweep", source)
        self.assertIn("enter_short", source)
        self.assertIn("wpr_reclaim", source)

    def test_generated_strategy_for_crabel_nr7_intraday_expansion_continuation_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "crabel_nr7_intraday_expansion_continuation"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "VolatilityCompressionExpansion -> CrabelNR7 -> Nr7CrabelExpansion -> "
            "IntradayExpansionContinuation",
        )
        self.assertIn(
            "branch_path: VolatilityCompressionExpansion -> CrabelNR7 -> "
            "Nr7CrabelExpansion -> IntradayExpansionContinuation -> "
            "tomac_idxfut_clean_crabel_nr7_intraday_expansion_continuation_1m_v1",
            source,
        )
        self.assertIn(
            'elif "crabel_nr7_intraday_expansion_continuation" == '
            '"crabel_nr7_intraday_expansion_continuation":',
            source,
        )
        self.assertIn("nr7_range", source)
        self.assertIn("nr7_break", source)
        self.assertIn("opening_break", source)
        self.assertIn("continuation_follow_through", source)
        self.assertIn("session_expansion_hold", source)

    def test_generated_strategy_for_crabel_nr7_intraday_expansion_continuation_keeps_child_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "crabel_nr7_intraday_expansion_continuation"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "VolatilityCompressionExpansion -> CrabelNR7 -> Nr7CrabelExpansion -> IntradayExpansionContinuation",
        )
        self.assertIn(
            "branch_path: VolatilityCompressionExpansion -> CrabelNR7 -> "
            "Nr7CrabelExpansion -> IntradayExpansionContinuation -> "
            "tomac_idxfut_clean_crabel_nr7_intraday_expansion_continuation_1m_v1",
            source,
        )
        self.assertIn(
            'elif "crabel_nr7_intraday_expansion_continuation" == '
            '"crabel_nr7_intraday_expansion_continuation":',
            source,
        )
        self.assertIn("nr7_range = dataframe[\"prior_nr7\"].fillna(False)", source)
        self.assertIn("opening_break = dataframe[\"close\"] > dataframe[\"opening_high30\"]", source)
        self.assertIn("continuation_follow_through", source)
        self.assertIn("session_expansion_hold", source)

    def test_generated_strategy_for_fractal_liquidity_macd_rsi_divergence_reclaim_keeps_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "fractal_liquidity_macd_rsi_divergence_reclaim"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> FractalLiquiditySweep -> MacdRsiDivergenceReclaim",
        )
        self.assertIn(
            "branch_path: RangeReversion -> FractalLiquiditySweep -> "
            "MacdRsiDivergenceReclaim -> "
            "tomac_idxfut_clean_fractal_liquidity_macd_rsi_divergence_reclaim_1m_v1",
            source,
        )
        self.assertIn(
            'elif "fractal_liquidity_macd_rsi_divergence_reclaim" == '
            '"fractal_liquidity_macd_rsi_divergence_reclaim":',
            source,
        )
        self.assertIn("macd_bullish_divergence", source)
        self.assertIn("macd_bearish_divergence", source)
        self.assertIn("killzone_window", source)
        self.assertIn("midnight_discount", source)
        self.assertIn("midnight_premium", source)

    def test_generated_strategy_for_fractal_liquidity_macd_divergence_reclaim_keeps_macd_only_root(self) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "fractal_liquidity_macd_divergence_reclaim"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> FractalLiquiditySweep -> MacdDivergenceReclaim",
        )
        self.assertIn(
            "branch_path: RangeReversion -> FractalLiquiditySweep -> "
            "MacdDivergenceReclaim -> "
            "tomac_idxfut_clean_fractal_liquidity_macd_divergence_reclaim_1m_v1",
            source,
        )
        self.assertIn(
            'elif "fractal_liquidity_macd_divergence_reclaim" == '
            '"fractal_liquidity_macd_divergence_reclaim":',
            source,
        )
        self.assertIn("macd_bullish_divergence", source)
        self.assertIn("macd_bearish_divergence", source)
        self.assertIn("fractal_sweep_long", source)
        self.assertIn("fractal_sweep_short", source)
        branch_start = source.index(
            'elif "fractal_liquidity_macd_divergence_reclaim" == '
            '"fractal_liquidity_macd_divergence_reclaim":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        macd_only_block = source[branch_start:next_branch]
        self.assertNotIn('dataframe["rsi14"].gt(30)', macd_only_block)
        self.assertNotIn('dataframe["rsi14"].lt(70)', macd_only_block)

    def test_generated_strategy_for_ote_fvg_order_block_reclaim_session_directional_bias_keeps_exact_child_root(
        self,
    ) -> None:
        module = self.load_module()

        spec = next(
            item for item in module.candidate_specs()
            if item.key == "ote_fvg_order_block_reclaim_session_directional_bias"
        )
        source = module.strategy_source(spec, symbol="ES", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> LiquiditySweepIctRetracement -> OteFvgOrderBlockReclaim -> SessionDirectionalBias",
        )
        self.assertIn(
            "branch_path: RangeReversion -> LiquiditySweepIctRetracement -> "
            "OteFvgOrderBlockReclaim -> SessionDirectionalBias -> "
            "tomac_idxfut_clean_ote_fvg_order_block_reclaim_session_directional_bias_1m_v1",
            source,
        )
        self.assertIn(
            'elif "ote_fvg_order_block_reclaim_session_directional_bias" == '
            '"ote_fvg_order_block_reclaim_session_directional_bias":',
            source,
        )
        self.assertIn("liquidity_sweep_long", source)
        self.assertIn("liquidity_sweep_short", source)
        self.assertIn("ict_zone_long", source)
        self.assertIn("ict_zone_short", source)
        self.assertIn("bull_session_bias", source)
        self.assertIn("bear_session_bias", source)
        self.assertIn("mtf_bias_long", source)
        self.assertIn("mtf_bias_short", source)
        self.assertIn("short_raw", source)

    def test_candidate_specs_include_fractal_liquidity_macd_rsi_divergence_reclaim(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["fractal_liquidity_macd_rsi_divergence_reclaim"].branch_path,
            "RangeReversion -> FractalLiquiditySweep -> MacdRsiDivergenceReclaim",
        )

    def test_candidate_specs_include_fractal_liquidity_macd_divergence_reclaim(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["fractal_liquidity_macd_divergence_reclaim"].branch_path,
            "RangeReversion -> FractalLiquiditySweep -> MacdDivergenceReclaim",
        )

    def test_candidate_specs_include_ote_fvg_order_block_reclaim_session_directional_bias(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["ote_fvg_order_block_reclaim_session_directional_bias"].branch_path,
            "RangeReversion -> LiquiditySweepIctRetracement -> OteFvgOrderBlockReclaim -> SessionDirectionalBias",
        )

    def test_candidate_specs_include_crabel_nr7_intraday_expansion_continuation(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["crabel_nr7_intraday_expansion_continuation"].branch_path,
            "VolatilityCompressionExpansion -> CrabelNR7 -> Nr7CrabelExpansion -> "
            "IntradayExpansionContinuation",
        )

    def test_candidate_specs_include_public_family_rotation_roots(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["opening_drive_breakout"].branch_path,
            "TrendExpansion -> OpeningDriveBreakout -> OpeningDriveBreakout",
        )

    def test_candidate_specs_include_crabel_nr7_intraday_expansion_continuation(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}

        self.assertEqual(
            by_key["crabel_nr7_intraday_expansion_continuation"].branch_path,
            "VolatilityCompressionExpansion -> CrabelNR7 -> Nr7CrabelExpansion -> IntradayExpansionContinuation",
        )
        self.assertEqual(
            by_key["supertrend_adx_displacement"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TrendPullbackOrLiquiditySweepReclaim",
        )
        self.assertEqual(
            by_key["supertrend_adx_pullback_reclaim"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TrendPullbackReclaim",
        )
        self.assertEqual(
            by_key["supertrend_adx_turtle_soup_sweep_reversal"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TurtleSoupSweepReversal",
        )
        self.assertEqual(
            by_key["supertrend_adx_liquidity_sweep_reclaim"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> LiquiditySweepReclaim",
        )
        self.assertEqual(
            by_key["liquidity_sweep_adx_liquidity_pool_context"].branch_path,
            "TrendExpansion -> LiquiditySweepDisplacement -> "
            "AdxTrendStrengthReclaim -> LiquidityPoolContextFilter",
        )
        self.assertEqual(
            by_key["supertrend_adx_pullback_ote_fvg_ob"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TrendPullbackReclaimOteFvgOb",
        )
        self.assertEqual(
            by_key["supertrend_adx_pullback_exit_persistence"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TrendPullbackReclaimExitPersistence",
        )
        self.assertEqual(
            by_key["supertrend_adx_pullback_exit_persistence_high_conviction"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TrendPullbackReclaimExitPersistenceHighConviction",
        )
        self.assertEqual(
            by_key["supertrend_adx_pullback_exit_persistence_opening_drive"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TrendPullbackReclaimExitPersistenceOpeningDrive",
        )
        self.assertEqual(
            by_key["supertrend_adx_pullback_exit_persistence_opening_drive_soft"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TrendPullbackReclaimExitPersistenceOpeningDriveSoft",
        )
        self.assertEqual(
            by_key["supertrend_adx_pullback_exit_persistence_vwap_excursion_cap"].branch_path,
            "TrendExpansion -> SuperTrendAdxDisplacement -> TrendPullbackReclaimExitPersistenceVwapExcursionCap",
        )
        self.assertEqual(
            by_key["mass_index_vortex_trend_continuation"].branch_path,
            "TrendExpansion -> VolatilityExpansionTrend -> MassIndexBulge -> VortexDirectionalContinuation",
        )
        self.assertEqual(
            by_key["aroon_cci_trend_continuation"].branch_path,
            "TrendExpansion -> DirectionalPersistence -> AroonCciTrendContinuation",
        )
        self.assertEqual(
            by_key["aroon_cci_cadence_lift_symbol_guard"].branch_path,
            "TrendExpansion -> DirectionalPersistence -> AroonCciTrendContinuation -> CadenceLiftSymbolGuard",
        )
        self.assertEqual(
            by_key["aroon_cci_cadence_lift_volume_persistence_retest"].branch_path,
            "TrendExpansion -> DirectionalPersistence -> AroonCciTrendContinuation -> "
            "CadenceLiftSymbolGuard -> VolumePersistenceRetest",
        )
        self.assertEqual(
            by_key["vwap_reclaim_persistence"].branch_path,
            "RangeTransition -> VWAPMeanReclaim -> VwapReclaimPersistence",
        )
        self.assertEqual(
            by_key["vwap_reclaim_persistence_killzone_filter"].branch_path,
            "RangeTransition -> VWAPMeanReclaim -> VwapReclaimPersistence -> KillzoneFilter",
        )
        self.assertEqual(
            by_key["donchian_turtle_breakout"].branch_path,
            "TrendExpansion -> BreakoutPersistence -> DonchianTurtleBreakout",
        )
        self.assertEqual(
            by_key["vwap_washout_reclaim"].branch_path,
            "RangeReversion -> VwapStretch -> VwapWashoutReclaim",
        )
        self.assertEqual(
            by_key["dense_trend_pullback_reclaim"].branch_path,
            "TrendExpansion -> PullbackReclaim -> DenseTrendPullbackReclaim",
        )
        self.assertEqual(
            by_key["prior_day_extreme_continuation"].branch_path,
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuation",
        )
        self.assertEqual(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard"].branch_path,
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard",
        )
        self.assertEqual(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard_exit_persistence"].branch_path,
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> ExitPersistence",
        )
        self.assertEqual(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard_cusum_deadzone_gate"].branch_path,
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> CusumDeadzoneGate",
        )
        self.assertEqual(
            by_key["opening_drive_twoleg_continuation_exit_persistence"].branch_path,
            "TrendExpansion -> OpeningDriveExpansion -> OpeningDriveTwoLegContinuation -> ExitPersistence",
        )
        self.assertEqual(
            by_key["impulse_follow"].branch_path,
            "TrendExpansion -> ImpulseFollowThrough -> ImpulseFollowThrough",
        )
        self.assertEqual(
            by_key["wpr_extreme_mean_reclaim"].branch_path,
            "TrendExpansion -> WprExtremePullback -> MeanReclaim",
        )
        self.assertEqual(
            by_key["nr7_range_expansion"].branch_path,
            "RangeConsolidation -> NarrowRangeCompression -> Nr7RangeExpansion",
        )
        self.assertEqual(
            by_key["connors_rsi2_rebound"].branch_path,
            "RangeReversion -> ExhaustionWashout -> ConnorsRsi2Rebound",
        )
        self.assertEqual(
            by_key["ultimate_ict_zone_volume_spike_reclaim"].branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim",
        )
        self.assertEqual(
            by_key["ultimate_ict_zone_volume_spike_session_open_bias_cap"].branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim -> SessionOpenBiasCap",
        )
        self.assertEqual(
            by_key["ultimate_ict_zone_volume_spike_vwap_hold_persistence"].branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim -> VwapHoldPersistence",
        )
        self.assertEqual(
            by_key["ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence"].branch_path,
            "RangeReversion -> KillzoneLiquiditySweep -> IctZoneVolumeSpikeReclaim -> "
            "SessionOpenBiasCap -> VwapHoldPersistence",
        )
        self.assertEqual(
            by_key["wpr_fractal_no_be_session_bias_cap"].branch_path,
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprFractalNoBreakEvenFullTarget -> SessionBiasCap",
        )
        self.assertEqual(
            by_key["wpr_fractal_no_be_higher_frame_slope_confirm"].branch_path,
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprFractalNoBreakEvenFullTarget -> HigherFrameSlopeConfirm",
        )
        self.assertEqual(
            by_key["ote_liquidity_sweep_fvg_ob_reclaim"].branch_path,
            "TrendExpansion -> OteLiquiditySweepReclaim -> FvgObReentry",
        )
        self.assertEqual(
            by_key["ote_fvg_order_block_reclaim_session_directional_bias"].branch_path,
            "RangeReversion -> LiquiditySweepIctRetracement -> OteFvgOrderBlockReclaim -> SessionDirectionalBias",
        )
        self.assertEqual(
            by_key["h4_midnight_macd_rsi_pullback"].branch_path,
            "TrendExpansion -> H4StructureMidnightBias -> MacdRsiPullback",
        )
        self.assertEqual(
            by_key["liquidity_purge_rejection"].branch_path,
            "RangeTransition -> LiquidityPurgeRejection -> KillzoneReversal",
        )
        self.assertEqual(
            by_key["momentum_divergence_reclaim"].branch_path,
            "TrendExpansion -> MomentumDivergence -> DivergenceReclaim",
        )
        self.assertEqual(
            by_key["fractal_liquidity_macd_rsi_divergence_reclaim"].branch_path,
            "RangeReversion -> FractalLiquiditySweep -> MacdRsiDivergenceReclaim",
        )
        self.assertEqual(
            by_key["midnight_open_liquidity_sweep_macd_divergence_reclaim"].branch_path,
            "RangeReversion -> MidnightOpenDiscountPremiumBias -> LiquiditySweepReclaim -> MacdDivergenceReclaim",
        )
        self.assertEqual(
            by_key["silver_bullet_rsi_sniper"].branch_path,
            "SessionRhythm -> SilverBulletSniper -> RsiAtrReversal",
        )
        self.assertEqual(
            by_key["session_window_sweep_reclaim"].branch_path,
            "SessionRhythm -> KillzoneLiquiditySweep -> SessionWindowSweepReclaim",
        )

    def test_candidate_specs_can_select_only_next_family_rotation(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(
            families=[
                "opening_drive_breakout",
                "supertrend_adx_displacement",
                "supertrend_adx_pullback_reclaim",
                "supertrend_adx_turtle_soup_sweep_reversal",
                "supertrend_adx_liquidity_sweep_reclaim",
                "supertrend_adx_pullback_ote_fvg_ob",
                "supertrend_adx_pullback_exit_persistence",
                "supertrend_adx_pullback_exit_persistence_high_conviction",
                "supertrend_adx_pullback_exit_persistence_opening_drive",
                "supertrend_adx_pullback_exit_persistence_opening_drive_soft",
                "supertrend_adx_pullback_exit_persistence_vwap_excursion_cap",
                "vwap_reclaim_persistence",
                "donchian_turtle_breakout",
                "dense_trend_pullback_reclaim",
                "prior_day_extreme_continuation",
                "prior_day_extreme_continuation_mtf_resonance_guard",
                "prior_day_extreme_continuation_mtf_resonance_guard_exit_persistence",
                "prior_day_extreme_continuation_mtf_resonance_guard_cusum_deadzone_gate",
                "prior_day_liquidity_sweep_reversal",
                "impulse_follow",
                "wpr_extreme_mean_reclaim",
                "nr7_range_expansion",
                "connors_rsi2_rebound",
                "ultimate_ict_zone_volume_spike_reclaim",
                "ultimate_ict_zone_volume_spike_session_open_bias_cap",
                "ultimate_ict_zone_volume_spike_vwap_hold_persistence",
                "ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence",
                "ote_liquidity_sweep_fvg_ob_reclaim",
                "ote_fvg_order_block_reclaim_session_directional_bias",
                "h4_midnight_macd_rsi_pullback",
                "liquidity_purge_rejection",
                "momentum_divergence_reclaim",
                "fractal_liquidity_macd_rsi_divergence_reclaim",
                "fractal_liquidity_macd_divergence_reclaim",
                "silver_bullet_rsi_sniper",
                "session_window_sweep_reclaim",
            ]
        )

        self.assertEqual(
            [spec.key for spec in specs],
            [
                "opening_drive_breakout",
                "vwap_reclaim_persistence",
                "donchian_turtle_breakout",
                "dense_trend_pullback_reclaim",
                "prior_day_extreme_continuation",
                "prior_day_extreme_continuation_mtf_resonance_guard",
                "prior_day_extreme_continuation_mtf_resonance_guard_exit_persistence",
                "prior_day_extreme_continuation_mtf_resonance_guard_cusum_deadzone_gate",
                "prior_day_liquidity_sweep_reversal",
                "impulse_follow",
                "wpr_extreme_mean_reclaim",
                "nr7_range_expansion",
                "supertrend_adx_displacement",
                "supertrend_adx_turtle_soup_sweep_reversal",
                "supertrend_adx_pullback_reclaim",
                "supertrend_adx_liquidity_sweep_reclaim",
                "supertrend_adx_pullback_ote_fvg_ob",
                "supertrend_adx_pullback_exit_persistence",
                "supertrend_adx_pullback_exit_persistence_high_conviction",
                "supertrend_adx_pullback_exit_persistence_opening_drive",
                "supertrend_adx_pullback_exit_persistence_opening_drive_soft",
                "supertrend_adx_pullback_exit_persistence_vwap_excursion_cap",
                "connors_rsi2_rebound",
                "ultimate_ict_zone_volume_spike_reclaim",
                "ultimate_ict_zone_volume_spike_session_open_bias_cap",
                "ultimate_ict_zone_volume_spike_vwap_hold_persistence",
                "ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence",
                "ote_liquidity_sweep_fvg_ob_reclaim",
                "ote_fvg_order_block_reclaim_session_directional_bias",
                "h4_midnight_macd_rsi_pullback",
                "liquidity_purge_rejection",
                "momentum_divergence_reclaim",
                "fractal_liquidity_macd_rsi_divergence_reclaim",
                "fractal_liquidity_macd_divergence_reclaim",
                "silver_bullet_rsi_sniper",
                "session_window_sweep_reclaim",
            ],
        )

        with self.assertRaisesRegex(ValueError, "unknown candidate families"):
            module.candidate_specs(families=["does_not_exist"])

    def test_candidate_specs_can_select_liquidity_sweep_adx_liquidity_pool_context_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["liquidity_sweep_adx_liquidity_pool_context"])

        self.assertEqual([spec.key for spec in specs], ["liquidity_sweep_adx_liquidity_pool_context"])

    def test_candidate_specs_can_select_reference_hurst_profile_range_compression_release_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["wpr_adx_reference_hurst_profile_range_compression_release"])

        self.assertEqual(
            [spec.key for spec in specs],
            ["wpr_adx_reference_hurst_profile_range_compression_release"],
        )
        self.assertEqual(specs[0].main_regime, "RangeReversion")
        self.assertEqual(specs[0].sub_regime, "PdhPdlFractalLiquiditySweep")
        self.assertEqual(specs[0].profit_factor, "WprAdxTrendAlignedReclaim")
        self.assertEqual(specs[0].child_profit_factor, "HurstProfileMssReclaim")
        self.assertEqual(
            specs[0].extra_profit_factors,
            ("ReferenceHurstProfileRangeCompressionRelease",),
        )

    def test_candidate_specs_can_select_range_estimator_disagreement_compression_release_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["range_estimator_disagreement_compression_release"])

        self.assertEqual([spec.key for spec in specs], ["range_estimator_disagreement_compression_release"])
        self.assertEqual(specs[0].main_regime, "RangeVolatilityRegime")
        self.assertEqual(specs[0].sub_regime, "EstimatorDisagreementCompression")
        self.assertEqual(specs[0].profit_factor, "CompressionReleaseBreakout")
        self.assertEqual(specs[0].child_profit_factor, "AtrManagedHold")
        self.assertEqual(
            specs[0].factor_id("30m"),
            "tomac_idxfut_clean_range_estimator_disagreement_compression_release_30m_v1",
        )
        self.assertEqual(
            specs[0].branch_path_with_factor("30m"),
            "RangeVolatilityRegime -> EstimatorDisagreementCompression -> "
            "CompressionReleaseBreakout -> AtrManagedHold -> "
            "tomac_idxfut_clean_range_estimator_disagreement_compression_release_30m_v1",
        )

        source = module.strategy_source(specs[0], symbol="NQ", timeframe="30m")
        self.assertIn("range_estimator_disagreement_compression_release", source)
        self.assertIn("parkinson_range_vol", source)
        self.assertIn("garman_klass_range_vol", source)
        self.assertIn("range_estimator_disagreement_z", source)
        self.assertIn("compression_release_breakout", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_yang_zhang_range_vol_split_reacceleration_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["yang_zhang_range_vol_split_reacceleration"])

        self.assertEqual([spec.key for spec in specs], ["yang_zhang_range_vol_split_reacceleration"])
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "RangeBasedVolatility")
        self.assertEqual(specs[0].profit_factor, "YangZhangGapRangeSplit")
        self.assertEqual(specs[0].child_profit_factor, "RogersSatchellReaccelerationAdmission")
        self.assertEqual(
            specs[0].factor_id("30m"),
            "tomac_idxfut_clean_yang_zhang_range_vol_split_reacceleration_30m_v1",
        )
        self.assertEqual(
            specs[0].branch_path_with_factor("30m"),
            "TrendExpansion -> RangeBasedVolatility -> YangZhangGapRangeSplit -> "
            "RogersSatchellReaccelerationAdmission -> "
            "tomac_idxfut_clean_yang_zhang_range_vol_split_reacceleration_30m_v1",
        )

        source = module.strategy_source(specs[0], symbol="NQ", timeframe="30m")
        self.assertIn("yang_zhang_range_vol_split_reacceleration", source)
        self.assertIn("yz_open_jump_vol_share", source)
        self.assertIn("yz_rogers_satchell_range_vol", source)
        self.assertIn("yz_range_vol_reacceleration", source)
        self.assertIn("yz_gap_noise_cap", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_inside_bar_breakout_hold_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["inside_bar_breakout_hold"])

        self.assertEqual([spec.key for spec in specs], ["inside_bar_breakout_hold"])
        self.assertEqual(specs[0].class_prefix, "InsideBarBreakoutHold")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "VolatilityCompression")
        self.assertEqual(specs[0].profit_factor, "InsideRangeBreakoutHold")
        self.assertEqual(specs[0].child_profit_factor, "TrendAcceptance")
        self.assertEqual(specs[0].extra_profit_factors, ("LowTurnoverAtrHold",))
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].factor_id("4h"),
            "tomac_idxfut_clean_inside_bar_breakout_hold_4h_v1",
        )
        self.assertEqual(
            specs[0].branch_path_with_factor("4h"),
            "TrendExpansion -> VolatilityCompression -> InsideRangeBreakoutHold -> "
            "TrendAcceptance -> LowTurnoverAtrHold -> "
            "tomac_idxfut_clean_inside_bar_breakout_hold_4h_v1",
        )

        source = module.strategy_source(specs[0], symbol="NQ", timeframe="4h")
        self.assertIn("inside_bar_breakout_hold", source)
        self.assertIn("inside_range_high", source)
        self.assertIn("inside_range_low", source)
        self.assertIn("inside_breakout_hold_long", source)
        self.assertIn("inside_breakout_hold_short", source)
        self.assertIn('elif "inside_bar_breakout_hold" == "inside_bar_breakout_hold":', source)
        self.assertIn("trend_acceptance_long", source)
        self.assertIn("low_turnover_atr_hold", source)
        self.assertIn('dataframe["inside_breakout_hold_long"].fillna(False)', source)
        self.assertIn('dataframe["inside_breakout_hold_short"].fillna(False)', source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_realized_skew_semivariance_trend_acceptance_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["realized_skew_semivariance_trend_acceptance"])

        self.assertEqual([spec.key for spec in specs], ["realized_skew_semivariance_trend_acceptance"])
        self.assertEqual(specs[0].class_prefix, "RealizedSkewSemivarianceTrendAcceptance")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "RealizedAsymmetryState")
        self.assertEqual(specs[0].profit_factor, "UpsideSemivarianceDominance")
        self.assertEqual(specs[0].child_profit_factor, "TrendAcceptance")
        self.assertEqual(specs[0].extra_profit_factors, ("MtfSlopeResonanceOptional",))
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].factor_id("1h"),
            "tomac_idxfut_clean_realized_skew_semivariance_trend_acceptance_1h_v1",
        )
        self.assertEqual(
            specs[0].branch_path_with_factor("1h"),
            "TrendExpansion -> RealizedAsymmetryState -> UpsideSemivarianceDominance -> "
            "TrendAcceptance -> MtfSlopeResonanceOptional -> "
            "tomac_idxfut_clean_realized_skew_semivariance_trend_acceptance_1h_v1",
        )

        source = module.strategy_source(specs[0], symbol="NQ", timeframe="1h")
        self.assertIn("realized_skew_semivariance_trend_acceptance", source)
        self.assertIn("realized_skew_96_shifted", source)
        self.assertIn("upside_semivariance_96_shifted", source)
        self.assertIn("downside_semivariance_96_shifted", source)
        self.assertIn("semivariance_balance_shifted", source)
        self.assertIn("realized_asymmetry_trend_acceptance_long", source)
        self.assertIn("realized_asymmetry_trend_acceptance_short", source)
        self.assertIn(
            'elif "realized_skew_semivariance_trend_acceptance" == "realized_skew_semivariance_trend_acceptance":',
            source,
        )
        self.assertIn('dataframe["realized_asymmetry_trend_acceptance_long"].fillna(False)', source)
        self.assertIn('dataframe["realized_asymmetry_trend_acceptance_short"].fillna(False)', source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_regression_channel_r2_slope_breadth_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["regression_channel_r2_slope_breadth"])

        self.assertEqual([spec.key for spec in specs], ["regression_channel_r2_slope_breadth"])
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "RegressionChannelTrend")
        self.assertEqual(specs[0].profit_factor, "R2SlopePersistence")
        self.assertEqual(specs[0].child_profit_factor, "CrossIndexBreadthConfirmation")
        self.assertEqual(specs[0].extra_profit_factors, ("AtrStopHoldCompression",))
        self.assertEqual(
            specs[0].branch_path_with_factor("1m"),
            "TrendExpansion -> RegressionChannelTrend -> R2SlopePersistence -> "
            "CrossIndexBreadthConfirmation -> AtrStopHoldCompression -> "
            "tomac_idxfut_clean_regression_channel_r2_slope_breadth_1m_v1",
        )

        source = module.strategy_source(specs[0], symbol="NQ", timeframe="1m")
        self.assertIn("regression_channel_r2_slope_breadth", source)
        self.assertIn("regression_slope_bps_96", source)
        self.assertIn("regression_r2_96", source)
        self.assertIn("cross_index_breadth_proxy", source)
        self.assertIn("atr_stop_hold_compression", source)

    def test_candidate_specs_can_select_linear_regression_r2_slope_trend_rejoin_filter_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["linear_regression_r2_slope_trend_rejoin_filter"])

        self.assertEqual([spec.key for spec in specs], ["linear_regression_r2_slope_trend_rejoin_filter"])
        self.assertEqual(specs[0].class_prefix, "LinearRegressionR2SlopeTrendRejoinFilter")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "LinearRegressionSlopeQuality")
        self.assertEqual(specs[0].profit_factor, "R2TrendFitAdmission")
        self.assertEqual(specs[0].child_profit_factor, "ResidualPullbackRejoin")
        self.assertEqual(specs[0].extra_profit_factors, ("MtfSlopeResonance",))
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(specs[0].allowed_timeframes, ("5m", "15m", "30m", "1h", "4h", "1d"))
        self.assertEqual(
            specs[0].factor_id("15m"),
            "tomac_idxfut_clean_linear_regression_r2_slope_trend_rejoin_15m_v1",
        )
        self.assertEqual(
            specs[0].branch_path_with_factor("15m"),
            "TrendExpansion -> LinearRegressionSlopeQuality -> R2TrendFitAdmission -> "
            "ResidualPullbackRejoin -> MtfSlopeResonance -> "
            "tomac_idxfut_clean_linear_regression_r2_slope_trend_rejoin_15m_v1",
        )

    def test_linear_regression_r2_slope_trend_rejoin_strategy_source_uses_shifted_residual_rejoin(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["linear_regression_r2_slope_trend_rejoin_filter"])[0]

        source = module.strategy_source(spec, symbol="YM", timeframe="15m")

        self.assertIn("factor_id: tomac_idxfut_clean_linear_regression_r2_slope_trend_rejoin_15m_v1", source)
        self.assertIn("can_short = True", source)
        self.assertIn("linear_regression_slope_quality_long", source)
        self.assertIn("linear_regression_slope_quality_short", source)
        self.assertIn("r2_trend_fit_admission_long", source)
        self.assertIn("r2_trend_fit_admission_short", source)
        self.assertIn("residual_pullback_rejoin_long", source)
        self.assertIn("residual_pullback_rejoin_short", source)
        self.assertIn("mtf_slope_resonance_long", source)
        self.assertIn("mtf_slope_resonance_short", source)
        self.assertIn("rolling_regression_residual_shifted", source)
        self.assertIn("rolling_regression_residual_rejoin_delta", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_range_entropy_squeeze_breadth_release_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["range_entropy_squeeze_breadth_release"])

        self.assertEqual([spec.key for spec in specs], ["range_entropy_squeeze_breadth_release"])
        self.assertEqual(specs[0].main_regime, "RangeTransition")
        self.assertEqual(specs[0].sub_regime, "LowEntropySqueeze")
        self.assertEqual(specs[0].profit_factor, "BreadthConfirmedRangeRelease")
        self.assertEqual(specs[0].child_profit_factor, "AtrExpansionHold")
        self.assertEqual(specs[0].extra_profit_factors, ("LowTurnoverExitGuard",))
        self.assertEqual(
            specs[0].branch_path_with_factor("1h"),
            "RangeTransition -> LowEntropySqueeze -> BreadthConfirmedRangeRelease -> "
            "AtrExpansionHold -> LowTurnoverExitGuard -> "
            "tomac_idxfut_clean_range_entropy_squeeze_breadth_release_1h_v1",
        )

        source = module.strategy_source(specs[0], symbol="ES", timeframe="1h")
        self.assertIn("range_entropy_squeeze_breadth_release", source)
        self.assertIn("range_entropy_proxy", source)
        self.assertIn("low_entropy_squeeze", source)
        self.assertIn("breadth_confirmed_range_release", source)
        self.assertIn("atr_expansion_hold", source)
        self.assertIn("low_turnover_exit_guard", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_permutation_entropy_chop_filter_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["permutation_entropy_chop_filter"])

        self.assertEqual([spec.key for spec in specs], ["permutation_entropy_chop_filter"])
        self.assertEqual(specs[0].main_regime, "TransitionRisk")
        self.assertEqual(specs[0].sub_regime, "OrdinalComplexity")
        self.assertEqual(specs[0].profit_factor, "PermutationEntropyChopFilter")
        self.assertEqual(specs[0].child_profit_factor, "ParentTrendExecutionQualityGate")
        self.assertEqual(
            specs[0].branch_path_with_factor("30m"),
            "TransitionRisk -> OrdinalComplexity -> PermutationEntropyChopFilter -> "
            "ParentTrendExecutionQualityGate -> "
            "tomac_idxfut_clean_permutation_entropy_chop_filter_30m_v1",
        )

        source = module.strategy_source(specs[0], symbol="NQ", timeframe="30m")
        self.assertIn("permutation_entropy_chop_filter", source)
        self.assertIn("ordinal_pattern_entropy", source)
        self.assertIn("chop_filter", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_conformal_interval_width_risk_throttle_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["conformal_interval_width_risk_throttle"])

        self.assertEqual([spec.key for spec in specs], ["conformal_interval_width_risk_throttle"])
        self.assertEqual(specs[0].class_prefix, "ConformalIntervalWidthRiskThrottle")
        self.assertEqual(specs[0].main_regime, "TransitionRisk")
        self.assertEqual(specs[0].sub_regime, "DistributionFreeIntervalCalibration")
        self.assertEqual(specs[0].profit_factor, "ConformalWidthMiscoverageState")
        self.assertEqual(specs[0].child_profit_factor, "ParentSignalRiskThrottle")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_conformal_interval_width_risk_throttle_5m_v1",
                "tomac_idxfut_clean_conformal_interval_width_risk_throttle_15m_v1",
                "tomac_idxfut_clean_conformal_interval_width_risk_throttle_30m_v1",
                "tomac_idxfut_clean_conformal_interval_width_risk_throttle_1h_v1",
                "tomac_idxfut_clean_conformal_interval_width_risk_throttle_4h_v1",
                "tomac_idxfut_clean_conformal_interval_width_risk_throttle_1d_v1",
            ],
        )
        self.assertEqual(
            specs[0].branch_path_with_factor("15m"),
            "TransitionRisk -> DistributionFreeIntervalCalibration -> "
            "ConformalWidthMiscoverageState -> ParentSignalRiskThrottle -> "
            "tomac_idxfut_clean_conformal_interval_width_risk_throttle_15m_v1",
        )

    def test_conformal_interval_width_strategy_source_uses_shifted_completed_bar_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["conformal_interval_width_risk_throttle"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("conformal_interval_width_risk_throttle", source)
        self.assertIn("conformal_abs_residual_proxy", source)
        self.assertIn("conformal_residual_quantile", source)
        self.assertIn("conformal_interval_half_width", source)
        self.assertIn("conformal_interval_width_percentile_shifted", source)
        self.assertIn("conformal_miscoverage_rate_shifted", source)
        self.assertIn("conformal_width_risk_throttle_long.fillna(False)", source)
        self.assertIn("conformal_width_risk_throttle_short.fillna(False)", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_mutual_information_regime_channel_admission_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["mutual_information_regime_channel_admission_filter"])

        self.assertEqual([spec.key for spec in specs], ["mutual_information_regime_channel_admission_filter"])
        self.assertEqual(specs[0].class_prefix, "MutualInformationRegimeChannelAdmissionFilter")
        self.assertEqual(specs[0].main_regime, "ValidationMaturity")
        self.assertEqual(specs[0].sub_regime, "InformationRateRegimeChannel")
        self.assertEqual(specs[0].profit_factor, "ConditionalEntropyReduction")
        self.assertEqual(specs[0].child_profit_factor, "ParentSignalAdmissionFilter")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_mutual_information_regime_channel_admission_filter_5m_v1",
                "tomac_idxfut_clean_mutual_information_regime_channel_admission_filter_15m_v1",
                "tomac_idxfut_clean_mutual_information_regime_channel_admission_filter_30m_v1",
                "tomac_idxfut_clean_mutual_information_regime_channel_admission_filter_1h_v1",
                "tomac_idxfut_clean_mutual_information_regime_channel_admission_filter_4h_v1",
                "tomac_idxfut_clean_mutual_information_regime_channel_admission_filter_1d_v1",
            ],
        )

    def test_mutual_information_regime_channel_strategy_source_uses_shifted_entropy_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["mutual_information_regime_channel_admission_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_mutual_information_regime_channel_admission_filter_15m_v1",
            source,
        )
        self.assertIn("InformationRateRegimeChannel", source)
        self.assertIn("regime_channel_outcome_bucket", source)
        self.assertIn("baseline_entropy_proxy", source)
        self.assertIn("conditioned_entropy_proxy", source)
        self.assertIn("mutual_information_regime_channel", source)
        self.assertIn("regime_channel_signal_state_observed = regime_channel_signal_state.shift(6)", source)
        self.assertIn("regime_channel_outcome_bucket.ne(regime_channel_signal_state_observed)", source)
        self.assertIn("observed_signal_sample_count", source)
        self.assertIn("information_rate_sample_floor", source)
        self.assertIn("& information_rate_sample_floor", source)
        self.assertIn("information_rate_admission_long.fillna(False)", source)
        self.assertIn("information_rate_admission_short.fillna(False)", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_jensen_shannon_return_distribution_shift_gate_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["jensen_shannon_return_distribution_shift_gate"])

        self.assertEqual([spec.key for spec in specs], ["jensen_shannon_return_distribution_shift_gate"])
        self.assertEqual(specs[0].class_prefix, "JensenShannonReturnDistributionShiftGate")
        self.assertEqual(specs[0].main_regime, "ValidationMaturity")
        self.assertEqual(specs[0].sub_regime, "DistributionShift")
        self.assertEqual(specs[0].profit_factor, "JensenShannonReturnShapeDrift")
        self.assertEqual(specs[0].child_profit_factor, "ParentSignalAdmissionFilter")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_jensen_shannon_return_distribution_shift_gate_5m_v1",
                "tomac_idxfut_clean_jensen_shannon_return_distribution_shift_gate_15m_v1",
                "tomac_idxfut_clean_jensen_shannon_return_distribution_shift_gate_30m_v1",
                "tomac_idxfut_clean_jensen_shannon_return_distribution_shift_gate_1h_v1",
                "tomac_idxfut_clean_jensen_shannon_return_distribution_shift_gate_4h_v1",
                "tomac_idxfut_clean_jensen_shannon_return_distribution_shift_gate_1d_v1",
            ],
        )

    def test_jensen_shannon_return_distribution_shift_strategy_source_uses_shifted_js_gate(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["jensen_shannon_return_distribution_shift_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_jensen_shannon_return_distribution_shift_gate_15m_v1",
            source,
        )
        self.assertIn("DistributionShift", source)
        self.assertIn("js_return_shifted = log_close.diff().shift(1)", source)
        self.assertIn("def _bernoulli_js_divergence", source)
        self.assertIn("jensen_shannon_return_shape_drift", source)
        self.assertIn("jensen_shannon_range_volume_drift", source)
        self.assertIn("js_distribution_shift_gate", source)
        self.assertIn("jensen_shannon_admission_long.fillna(False)", source)
        self.assertIn("jensen_shannon_admission_short.fillna(False)", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_bartels_rank_serial_randomness_trend_filter_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["bartels_rank_serial_randomness_trend_filter"])

        self.assertEqual([spec.key for spec in specs], ["bartels_rank_serial_randomness_trend_filter"])
        self.assertEqual(specs[0].class_prefix, "BartelsRankSerialRandomnessTrendFilter")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "SerialDependenceQuality")
        self.assertEqual(specs[0].profit_factor, "BartelsRankRandomnessRejection")
        self.assertEqual(specs[0].child_profit_factor, "ParentTrendAdmission")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_bartels_rank_serial_randomness_trend_filter_5m_v1",
                "tomac_idxfut_clean_bartels_rank_serial_randomness_trend_filter_15m_v1",
                "tomac_idxfut_clean_bartels_rank_serial_randomness_trend_filter_30m_v1",
                "tomac_idxfut_clean_bartels_rank_serial_randomness_trend_filter_1h_v1",
                "tomac_idxfut_clean_bartels_rank_serial_randomness_trend_filter_4h_v1",
                "tomac_idxfut_clean_bartels_rank_serial_randomness_trend_filter_1d_v1",
            ],
        )

    def test_bartels_rank_serial_randomness_strategy_source_uses_shifted_rank_serial_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["bartels_rank_serial_randomness_trend_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_bartels_rank_serial_randomness_trend_filter_15m_v1",
            source,
        )
        self.assertIn("SerialDependenceQuality", source)
        self.assertIn("bartels_rank_return_shifted = log_close.diff().shift(1)", source)
        self.assertIn("def _bartels_rank_serial_score", source)
        self.assertIn("bartels_rank_serial_randomness_score", source)
        self.assertIn("bartels_rank_nonrandom_trend_quality", source)
        self.assertIn("bartels_rank_randomness_rejection_long.fillna(False)", source)
        self.assertIn("bartels_rank_randomness_rejection_short.fillna(False)", source)
        self.assertIn("bartels_rank_randomness_failure", source)
        self.assertIn("bartels_rank_trend_failure_long", source)
        self.assertIn("bartels_rank_trend_failure_short", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_realized_vol_term_structure_breakout_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["realized_vol_term_structure_breakout"])

        self.assertEqual([spec.key for spec in specs], ["realized_vol_term_structure_breakout"])
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "RealizedVolTermStructure")
        self.assertEqual(specs[0].profit_factor, "CompressionToExpansionBreakout")
        self.assertEqual(specs[0].child_profit_factor, "AtrManagedHold")
        self.assertEqual(specs[0].extra_profit_factors, ("LowTurnoverExitGuard",))
        self.assertEqual(
            specs[0].branch_path_with_factor("30m"),
            "TrendExpansion -> RealizedVolTermStructure -> CompressionToExpansionBreakout -> "
            "AtrManagedHold -> LowTurnoverExitGuard -> "
            "tomac_idxfut_clean_realized_vol_term_structure_breakout_30m_v1",
        )

        source = module.strategy_source(specs[0], symbol="NQ", timeframe="30m")
        self.assertIn("realized_vol_term_structure_breakout", source)
        self.assertIn("rv_short", source)
        self.assertIn("rv_long", source)
        self.assertIn("rv_ratio", source)
        self.assertIn("compression_to_expansion_breakout", source)
        self.assertIn("atr_managed_hold", source)
        self.assertIn("low_turnover_exit_guard", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_regime_transition_failure_reclaim_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["regime_transition_failure_reclaim"])

        self.assertEqual([spec.key for spec in specs], ["regime_transition_failure_reclaim"])
        self.assertEqual(specs[0].main_regime, "Transition")
        self.assertEqual(specs[0].sub_regime, "RegimeTransitionFailure")
        self.assertEqual(specs[0].profit_factor, "FailedFlipReclaim")
        self.assertEqual(specs[0].child_profit_factor, "MtfConfirmation")
        self.assertEqual(specs[0].extra_profit_factors, ("FixedRrrAtrBracket",))
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("15m"),
            "Transition -> RegimeTransitionFailure -> FailedFlipReclaim -> "
            "MtfConfirmation -> FixedRrrAtrBracket -> "
            "tomac_idxfut_clean_regime_transition_failure_reclaim_15m_v1",
        )

        source = module.strategy_source(specs[0], symbol="NQ", timeframe="15m")
        self.assertIn("regime_transition_failure_reclaim", source)
        self.assertIn("failed_transition_probe_long", source)
        self.assertIn("failed_flip_reclaim_long", source)
        self.assertIn("failed_flip_reclaim_short", source)
        self.assertIn("mtf_confirmation_long", source)
        self.assertIn("mtf_confirmation_short", source)
        self.assertIn("fixed_rrr_atr_bracket", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_evt_tail_index_exceedance_regime_gate_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["evt_tail_index_exceedance_regime_gate"])

        self.assertEqual([spec.key for spec in specs], ["evt_tail_index_exceedance_regime_gate"])
        self.assertEqual(specs[0].main_regime, "ExtremeStress")
        self.assertEqual(specs[0].sub_regime, "TailIndexRegime")
        self.assertEqual(specs[0].profit_factor, "QuantileExceedanceIntensity")
        self.assertEqual(specs[0].child_profit_factor, "TrendReclaimOrRiskOffAdmission")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("4h"),
            "ExtremeStress -> TailIndexRegime -> QuantileExceedanceIntensity -> "
            "TrendReclaimOrRiskOffAdmission -> "
            "tomac_idxfut_clean_evt_tail_index_exceedance_regime_gate_4h_v1",
        )

        source = module.strategy_source(specs[0], symbol="NQ", timeframe="4h")
        self.assertIn("evt_tail_index_exceedance_regime_gate", source)
        self.assertIn("left_tail_exceedance_count", source)
        self.assertIn("right_tail_exceedance_count", source)
        self.assertIn("tail_index_regime_cooldown", source)
        self.assertIn("quantile_exceedance_intensity_long", source)
        self.assertIn("quantile_exceedance_intensity_short", source)
        self.assertIn("trend_reclaim_or_riskoff_admission_long", source)
        self.assertIn("trend_reclaim_or_riskoff_admission_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_intraday_liquidity_seasonality_residual_shock_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["intraday_liquidity_seasonality_residual_shock_filter"])

        self.assertEqual([spec.key for spec in specs], ["intraday_liquidity_seasonality_residual_shock_filter"])
        self.assertEqual(specs[0].main_regime, "SessionLiquidity")
        self.assertEqual(specs[0].sub_regime, "IntradaySeasonality")
        self.assertEqual(specs[0].profit_factor, "LiquidityResidualShockState")
        self.assertEqual(specs[0].child_profit_factor, "TrendReclaimOrBreakoutAdmission")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("1h"),
            "SessionLiquidity -> IntradaySeasonality -> LiquidityResidualShockState -> "
            "TrendReclaimOrBreakoutAdmission -> "
            "tomac_idxfut_clean_intraday_liquidity_seasonality_residual_shock_filter_1h_v1",
        )

        source = module.strategy_source(specs[0], symbol="NQ", timeframe="1h")
        self.assertIn("intraday_liquidity_seasonality_residual_shock_filter", source)
        self.assertIn("liquidity_seasonality_volume_baseline", source)
        self.assertIn("liquidity_seasonality_range_baseline", source)
        self.assertIn("volume_seasonality_residual", source)
        self.assertIn("range_seasonality_residual", source)
        self.assertIn("liquidity_residual_shock_state_long", source)
        self.assertIn("liquidity_residual_shock_state_short", source)
        self.assertIn("trend_reclaim_or_breakout_admission_long", source)
        self.assertIn("trend_reclaim_or_breakout_admission_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_overnight_intraday_disagreement_reclaim_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["overnight_intraday_disagreement_reclaim"])

        self.assertEqual([spec.key for spec in specs], ["overnight_intraday_disagreement_reclaim"])
        self.assertEqual(specs[0].main_regime, "SessionRhythm")
        self.assertEqual(specs[0].sub_regime, "OvernightInventoryDisagreement")
        self.assertEqual(specs[0].profit_factor, "GlobexIntradayContinuationFailure")
        self.assertEqual(specs[0].child_profit_factor, "SessionVwapMidpointReclaim")
        self.assertEqual(specs[0].extra_profit_factors, ("MtfSlopeVeto",))
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("5m"),
            "SessionRhythm -> OvernightInventoryDisagreement -> GlobexIntradayContinuationFailure -> "
            "SessionVwapMidpointReclaim -> MtfSlopeVeto -> "
            "tomac_idxfut_clean_overnight_intraday_disagreement_reclaim_5m_v1",
        )

        source = module.strategy_source(specs[0], symbol="NQ", timeframe="5m")
        self.assertIn("overnight_intraday_disagreement_reclaim", source)
        self.assertIn("overnight_return", source)
        self.assertIn("overnight_midpoint", source)
        self.assertIn("ny_reclaim_window", source)
        self.assertIn("session_vwap_midpoint_reclaim_long", source)
        self.assertIn("session_vwap_midpoint_reclaim_short", source)
        self.assertIn("mtf_slope_veto_long", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_weekly_donchian_adx_breadth_hold_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["weekly_donchian_adx_breadth_hold"])

        self.assertEqual([spec.key for spec in specs], ["weekly_donchian_adx_breadth_hold"])
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "WeeklyBreakoutPersistence")
        self.assertEqual(specs[0].profit_factor, "DonchianAdxTrendHold")
        self.assertEqual(specs[0].child_profit_factor, "CrossIndexBreadthConfirmation")
        self.assertEqual(specs[0].extra_profit_factors, ("LowTurnoverAtrHold",))
        self.assertEqual(
            specs[0].branch_path_with_factor("1h"),
            "TrendExpansion -> WeeklyBreakoutPersistence -> DonchianAdxTrendHold -> "
            "CrossIndexBreadthConfirmation -> LowTurnoverAtrHold -> "
            "tomac_idxfut_clean_weekly_donchian_adx_breadth_hold_1h_v1",
        )

        source = module.strategy_source(specs[0], symbol="NQ", timeframe="1h")
        self.assertIn("weekly_donchian_adx_breadth_hold", source)
        self.assertIn("weekly_donchian_breakout", source)
        self.assertIn("weekly_adx_trend_hold", source)
        self.assertIn("cross_index_breadth_confirmation", source)
        self.assertIn("low_turnover_atr_hold", source)
        self.assertIn('minimal_roi = {"0": 0.0180', source)

    def test_candidate_specs_can_select_heikin_ashi_kama_trend_pullback_rejoin_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["heikin_ashi_kama_trend_pullback_rejoin"])

        self.assertEqual([spec.key for spec in specs], ["heikin_ashi_kama_trend_pullback_rejoin"])
        self.assertEqual(specs[0].main_regime, "RegimeRoot")
        self.assertEqual(specs[0].sub_regime, "TrendExpansion")
        self.assertEqual(specs[0].profit_factor, "HeikinAshiTrendState")
        self.assertEqual(specs[0].child_profit_factor, "KamaEfficiencyPullback")
        self.assertEqual(specs[0].extra_profit_factors, ("RejoinReacceleration", "MtfSlopeResonance"))
        self.assertEqual(
            specs[0].branch_path_with_factor("15m"),
            "RegimeRoot -> TrendExpansion -> HeikinAshiTrendState -> KamaEfficiencyPullback -> "
            "RejoinReacceleration -> MtfSlopeResonance -> "
            "tomac_nq_15m_heikin_ashi_kama_trend_pullback_rejoin_long_deeprejoin_v1",
        )

    def test_heikin_ashi_kama_trend_pullback_rejoin_source_uses_shifted_state(self) -> None:
        module = self.load_module()

        spec = module.candidate_specs(families=["heikin_ashi_kama_trend_pullback_rejoin"])[0]
        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_nq_15m_heikin_ashi_kama_trend_pullback_rejoin_long_deeprejoin_v1", source)
        self.assertIn("can_short = False", source)
        self.assertIn("heikin_ashi_kama_rejoin_long", source)
        self.assertIn("ha_trend_shifted", source)
        self.assertIn("kama_pullback_low_prev", source)
        self.assertIn("kama_efficiency_shifted", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_multires_energy_trend_gate_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["multires_energy_trend_gate"])

        self.assertEqual([spec.key for spec in specs], ["multires_energy_trend_gate"])
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "MultiResolutionEnergyTrend")
        self.assertEqual(specs[0].profit_factor, "DirectionalEnergyRatio")
        self.assertEqual(specs[0].child_profit_factor, "MtfSlopeResonance")
        self.assertEqual(specs[0].extra_profit_factors, ("FrictionAwareRrrBracket",))
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("4h"),
            "TrendExpansion -> MultiResolutionEnergyTrend -> DirectionalEnergyRatio -> "
            "MtfSlopeResonance -> FrictionAwareRrrBracket -> "
            "tomac_idxfut_clean_multires_energy_trend_gate_4h_v1",
        )

        source = module.strategy_source(specs[0], symbol="NQ", timeframe="4h")
        self.assertIn("multires_energy_trend_gate", source)
        self.assertIn("fast_energy", source)
        self.assertIn("slow_energy", source)
        self.assertIn("energy_ratio", source)
        self.assertIn("directional_energy_ratio_long", source)
        self.assertIn("directional_energy_ratio_short", source)
        self.assertIn("mtf_slope_resonance_long", source)
        self.assertIn("mtf_slope_resonance_short", source)
        self.assertIn("friction_aware_rrr_bracket", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_first30_last30_momentum_close_drive_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["first30_last30_momentum_close_drive"])

        self.assertEqual([spec.key for spec in specs], ["first30_last30_momentum_close_drive"])
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "MarketIntradayMomentum")
        self.assertEqual(specs[0].profit_factor, "FirstWindowMomentumContinuation")
        self.assertEqual(specs[0].child_profit_factor, "LastWindowCloseDrive")
        self.assertEqual(specs[0].extra_profit_factors, ("HtfTrendAgreement",))
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("5m"),
            "TrendExpansion -> MarketIntradayMomentum -> FirstWindowMomentumContinuation -> "
            "LastWindowCloseDrive -> HtfTrendAgreement -> "
            "tomac_idxfut_clean_first30_last30_momentum_close_drive_5m_v1",
        )

        source = module.strategy_source(specs[0], symbol="NQ", timeframe="5m")
        self.assertIn("first30_last30_momentum_close_drive", source)
        self.assertIn("first30_return", source)
        self.assertIn("last_window_close_drive", source)
        self.assertIn("htf_trend_agreement_long", source)
        self.assertIn("htf_trend_agreement_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_order_flow_imbalance_proxy_trend_reversal_gate_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["order_flow_imbalance_proxy_trend_reversal_gate"])

        self.assertEqual([spec.key for spec in specs], ["order_flow_imbalance_proxy_trend_reversal_gate"])
        self.assertEqual(specs[0].class_prefix, "OrderFlowImbalanceProxyTrendReversalGate")
        self.assertEqual(specs[0].main_regime, "MicrostructureProxy")
        self.assertEqual(specs[0].sub_regime, "CompletedBarOrderFlowImbalance")
        self.assertEqual(specs[0].profit_factor, "AbsorptionOrContinuationState")
        self.assertEqual(specs[0].child_profit_factor, "MtfTrendReversalAdmission")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("15m"),
            "MicrostructureProxy -> CompletedBarOrderFlowImbalance -> "
            "AbsorptionOrContinuationState -> MtfTrendReversalAdmission -> "
            "tomac_idxfut_clean_order_flow_imbalance_proxy_trend_reversal_gate_15m_v1",
        )

    def test_order_flow_imbalance_proxy_strategy_source_uses_shifted_completed_bar_proxy(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["order_flow_imbalance_proxy_trend_reversal_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("order_flow_imbalance_proxy_trend_reversal_gate", source)
        self.assertIn("clv_order_flow_proxy", source)
        self.assertIn("signed_volume_proxy", source)
        self.assertIn("signed_volume_proxy_shifted", source)
        self.assertIn("ofi_proxy_z", source)
        self.assertIn("absorption_state_long", source)
        self.assertIn("absorption_state_short", source)
        self.assertIn("mtf_trend_reversal_admission_long", source)
        self.assertIn("mtf_trend_reversal_admission_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_rsi_range_shift_regime_trend_filter_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["rsi_range_shift_regime_trend_filter"])

        self.assertEqual([spec.key for spec in specs], ["rsi_range_shift_regime_trend_filter"])
        self.assertEqual(specs[0].class_prefix, "RsiRangeShiftRegimeTrendFilter")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "RsiRangeShiftRegime")
        self.assertEqual(specs[0].profit_factor, "BullBearRangeMigration")
        self.assertEqual(specs[0].child_profit_factor, "ParentTrendAdmissionFilter")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("15m"),
            "TrendExpansion -> RsiRangeShiftRegime -> BullBearRangeMigration -> "
            "ParentTrendAdmissionFilter -> "
            "tomac_idxfut_clean_rsi_range_shift_regime_trend_filter_15m_v1",
        )

    def test_rsi_range_shift_strategy_source_uses_completed_bar_range_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["rsi_range_shift_regime_trend_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("rsi_range_shift_regime_trend_filter", source)
        self.assertIn("rsi_bull_range_support", source)
        self.assertIn("rsi_bear_range_rejection", source)
        self.assertIn("rsi_range_shift_long", source)
        self.assertIn("rsi_range_shift_short", source)
        self.assertIn("parent_trend_admission_long", source)
        self.assertIn("parent_trend_admission_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_adaptive_vwap_deviation_half_life_reversion_gate_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["adaptive_vwap_deviation_half_life_reversion_gate"])

        self.assertEqual([spec.key for spec in specs], ["adaptive_vwap_deviation_half_life_reversion_gate"])
        self.assertEqual(specs[0].class_prefix, "AdaptiveVwapDeviationHalfLifeReversionGate")
        self.assertEqual(specs[0].main_regime, "MeanReversion")
        self.assertEqual(specs[0].sub_regime, "AdaptiveVwapDeviation")
        self.assertEqual(specs[0].profit_factor, "HalfLifeReversionPressure")
        self.assertEqual(specs[0].child_profit_factor, "MtfCompressionRegimeAgreement")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("30m"),
            "MeanReversion -> AdaptiveVwapDeviation -> HalfLifeReversionPressure -> "
            "MtfCompressionRegimeAgreement -> "
            "tomac_idxfut_clean_adaptive_vwap_deviation_half_life_reversion_gate_30m_v1",
        )

    def test_adaptive_vwap_half_life_reversion_strategy_source_uses_completed_bar_decay_proxy(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["adaptive_vwap_deviation_half_life_reversion_gate"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("adaptive_vwap_deviation_half_life_reversion_gate", source)
        self.assertIn("vwap_deviation_atr", source)
        self.assertIn("abs_vwap_deviation_atr_shifted", source)
        self.assertIn("vwap_deviation_decay_ratio", source)
        self.assertIn("half_life_reversion_pressure_long", source)
        self.assertIn("half_life_reversion_pressure_short", source)
        self.assertIn("mtf_compression_regime_agreement_long", source)
        self.assertIn("mtf_compression_regime_agreement_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_mbs_convexity_duration_hedge_risk_transfer_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["mbs_convexity_duration_hedge_risk_transfer_filter"])

        self.assertEqual([spec.key for spec in specs], ["mbs_convexity_duration_hedge_risk_transfer_filter"])
        self.assertEqual(specs[0].class_prefix, "MbsConvexityDurationHedgeRiskTransferFilter")
        self.assertEqual(specs[0].main_regime, "MacroRates")
        self.assertEqual(specs[0].sub_regime, "MortgageConvexityHedging")
        self.assertEqual(specs[0].profit_factor, "DurationExtensionShock")
        self.assertEqual(specs[0].child_profit_factor, "EquityIndexRiskTransferFilter")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("4h"),
            "MacroRates -> MortgageConvexityHedging -> DurationExtensionShock -> "
            "EquityIndexRiskTransferFilter -> "
            "tomac_idxfut_clean_mbs_convexity_duration_hedge_risk_transfer_filter_4h_v1",
        )

    def test_mbs_convexity_strategy_source_uses_shifted_duration_extension_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["mbs_convexity_duration_hedge_risk_transfer_filter"])[0]

        source = module.strategy_source(spec, symbol="ES", timeframe="4h")

        self.assertIn("mbs_convexity_duration_hedge_risk_transfer_filter", source)
        self.assertIn("required_macro_rate_columns", source)
        self.assertIn('"mortgage_30y_rate"', source)
        self.assertIn('"treasury_10y_yield"', source)
        self.assertIn("missing_macro_rate_sidecar", source)
        self.assertIn("mortgage_rate_shock_proxy", source)
        self.assertIn("treasury_rate_shock_proxy", source)
        self.assertIn("mortgage_rate_shock_shifted", source)
        self.assertIn("treasury_rate_shock_shifted", source)
        self.assertIn("duration_extension_shock_state", source)
        self.assertIn("equity_index_risk_transfer_filter_long", source)
        self.assertIn("equity_index_risk_transfer_filter_short", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)
        self.assertNotIn('dataframe["prior_day_close"].pct_change(21)', source)

    def test_candidate_specs_can_select_ultimate_oscillator_mtf_divergence_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["ultimate_oscillator_mtf_divergence_filter"])

        self.assertEqual([spec.key for spec in specs], ["ultimate_oscillator_mtf_divergence_filter"])
        self.assertEqual(specs[0].class_prefix, "UltimateOscillatorMtfDivergenceFilter")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "MultiHorizonMomentum")
        self.assertEqual(specs[0].profit_factor, "UltimateOscillatorDivergence")
        self.assertEqual(specs[0].child_profit_factor, "MtfTrendReclaim")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("30m"),
            "TrendExpansion -> MultiHorizonMomentum -> UltimateOscillatorDivergence -> "
            "MtfTrendReclaim -> "
            "tomac_idxfut_clean_ultimate_oscillator_mtf_divergence_filter_30m_v1",
        )

    def test_ultimate_oscillator_strategy_source_uses_shifted_mtf_divergence(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["ultimate_oscillator_mtf_divergence_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("ultimate_oscillator_mtf_divergence_filter", source)
        self.assertIn("ultimate_oscillator_bp", source)
        self.assertIn("ultimate_oscillator_tr", source)
        self.assertIn("ultimate_oscillator_avg7", source)
        self.assertIn("ultimate_oscillator_avg14", source)
        self.assertIn("ultimate_oscillator_avg28", source)
        self.assertIn("ultimate_oscillator_value", source)
        self.assertIn("ultimate_oscillator_value_shifted", source)
        self.assertIn("ultimate_bullish_divergence", source)
        self.assertIn("ultimate_bearish_divergence", source)
        self.assertIn("mtf_trend_reclaim_long", source)
        self.assertIn("mtf_trend_reclaim_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_true_strength_index_mtf_reacceleration_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["true_strength_index_mtf_reacceleration_filter"])

        self.assertEqual([spec.key for spec in specs], ["true_strength_index_mtf_reacceleration_filter"])
        self.assertEqual(specs[0].class_prefix, "TrueStrengthIndexMtfReaccelerationFilter")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "DoubleSmoothedMomentum")
        self.assertEqual(specs[0].profit_factor, "TrueStrengthIndexReacceleration")
        self.assertEqual(specs[0].child_profit_factor, "MtfTrendReclaim")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("30m"),
            "TrendExpansion -> DoubleSmoothedMomentum -> TrueStrengthIndexReacceleration -> "
            "MtfTrendReclaim -> "
            "tomac_idxfut_clean_true_strength_index_mtf_reacceleration_filter_30m_v1",
        )

    def test_true_strength_index_strategy_source_uses_shifted_mtf_reacceleration(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["true_strength_index_mtf_reacceleration_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("true_strength_index_mtf_reacceleration_filter", source)
        self.assertIn("tsi_price_change", source)
        self.assertIn("tsi_smoothed_pc_25", source)
        self.assertIn("tsi_smoothed_abs_pc_25", source)
        self.assertIn("true_strength_index_value", source)
        self.assertIn("true_strength_index_signal", source)
        self.assertIn("true_strength_index_value_shifted", source)
        self.assertIn("true_strength_index_reacceleration_long", source)
        self.assertIn("true_strength_index_reacceleration_short", source)
        self.assertIn("tsi_mtf_trend_reclaim_long", source)
        self.assertIn("tsi_mtf_trend_reclaim_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_chande_momentum_mtf_reacceleration_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["chande_momentum_mtf_reacceleration_filter"])

        self.assertEqual([spec.key for spec in specs], ["chande_momentum_mtf_reacceleration_filter"])
        self.assertEqual(specs[0].class_prefix, "ChandeMomentumMtfReaccelerationFilter")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "MomentumOscillatorState")
        self.assertEqual(specs[0].profit_factor, "ChandeMomentumReacceleration")
        self.assertEqual(specs[0].child_profit_factor, "MtfTrendReclaim")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("30m"),
            "TrendExpansion -> MomentumOscillatorState -> ChandeMomentumReacceleration -> "
            "MtfTrendReclaim -> "
            "tomac_idxfut_clean_chande_momentum_mtf_reacceleration_filter_30m_v1",
        )

    def test_chande_momentum_strategy_source_uses_shifted_mtf_reacceleration(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["chande_momentum_mtf_reacceleration_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("chande_momentum_mtf_reacceleration_filter", source)
        self.assertIn("chande_momentum_gain_sum", source)
        self.assertIn("chande_momentum_loss_sum", source)
        self.assertIn("chande_momentum_value", source)
        self.assertIn("chande_momentum_signal", source)
        self.assertIn("chande_momentum_value_shifted", source)
        self.assertIn("chande_momentum_reacceleration_long", source)
        self.assertIn("chande_momentum_reacceleration_short", source)
        self.assertIn("cmo_mtf_trend_reclaim_long", source)
        self.assertIn("cmo_mtf_trend_reclaim_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_stochastic_rsi_mtf_reacceleration_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["stochastic_rsi_mtf_reacceleration_filter"])

        self.assertEqual([spec.key for spec in specs], ["stochastic_rsi_mtf_reacceleration_filter"])
        self.assertEqual(specs[0].class_prefix, "StochasticRsiMtfReaccelerationFilter")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "StochasticRsiMomentumState")
        self.assertEqual(specs[0].profit_factor, "StochasticRsiReacceleration")
        self.assertEqual(specs[0].child_profit_factor, "MtfTrendReclaim")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("30m"),
            "TrendExpansion -> StochasticRsiMomentumState -> StochasticRsiReacceleration -> "
            "MtfTrendReclaim -> "
            "tomac_idxfut_clean_stochastic_rsi_mtf_reacceleration_filter_30m_v1",
        )

    def test_stochastic_rsi_strategy_source_uses_shifted_mtf_reacceleration(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["stochastic_rsi_mtf_reacceleration_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("stochastic_rsi_mtf_reacceleration_filter", source)
        self.assertIn("stochastic_rsi_low14", source)
        self.assertIn("stochastic_rsi_high14", source)
        self.assertIn("stochastic_rsi_k", source)
        self.assertIn("stochastic_rsi_d", source)
        self.assertIn("stochastic_rsi_k_shifted", source)
        self.assertIn("stochastic_rsi_reacceleration_long", source)
        self.assertIn("stochastic_rsi_reacceleration_short", source)
        self.assertIn("stoch_rsi_mtf_trend_reclaim_long", source)
        self.assertIn("stoch_rsi_mtf_trend_reclaim_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_kdj_stochastic_jline_reacceleration_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["kdj_stochastic_jline_reacceleration"])

        self.assertEqual([spec.key for spec in specs], ["kdj_stochastic_jline_reacceleration"])
        self.assertEqual(specs[0].class_prefix, "KdjStochasticJlineReacceleration")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "StochasticRangePosition")
        self.assertEqual(specs[0].profit_factor, "KDJJLineReacceleration")
        self.assertEqual(specs[0].child_profit_factor, "MtfSlopeResonance")
        self.assertEqual(specs[0].extra_profit_factors, ("FrictionAwareAtrHold",))
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("1h"),
            "TrendExpansion -> StochasticRangePosition -> KDJJLineReacceleration -> "
            "MtfSlopeResonance -> FrictionAwareAtrHold -> "
            "tomac_idxfut_clean_kdj_stochastic_jline_reacceleration_1h_v1",
        )

    def test_kdj_stochastic_jline_strategy_source_uses_shifted_jline_reacceleration(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["kdj_stochastic_jline_reacceleration"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="1h")

        self.assertIn("kdj_stochastic_jline_reacceleration", source)
        self.assertIn("kdj_low14", source)
        self.assertIn("kdj_high14", source)
        self.assertIn("kdj_rsv", source)
        self.assertIn("kdj_k", source)
        self.assertIn("kdj_d", source)
        self.assertIn("kdj_jline", source)
        self.assertIn("kdj_jline_shifted", source)
        self.assertIn("kdj_jline_reacceleration_long", source)
        self.assertIn("kdj_jline_reacceleration_short", source)
        self.assertIn("kdj_mtf_slope_resonance_long", source)
        self.assertIn("kdj_mtf_slope_resonance_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_anchored_return_memory_decay_reacceleration_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["anchored_return_memory_decay_reacceleration_filter"])

        self.assertEqual([spec.key for spec in specs], ["anchored_return_memory_decay_reacceleration_filter"])
        self.assertEqual(specs[0].class_prefix, "AnchoredReturnMemoryDecayReaccelerationFilter")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "AnchoredSessionReturnMemory")
        self.assertEqual(specs[0].profit_factor, "MemoryDecayPullback")
        self.assertEqual(specs[0].child_profit_factor, "ReaccelerationAfterDecay")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            specs[0].branch_path_with_factor("30m"),
            "TrendExpansion -> AnchoredSessionReturnMemory -> MemoryDecayPullback -> "
            "ReaccelerationAfterDecay -> "
            "tomac_idxfut_clean_anchored_return_memory_decay_reacceleration_filter_30m_v1",
        )

    def test_anchored_return_memory_decay_strategy_source_uses_shifted_completed_bar_memory_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["anchored_return_memory_decay_reacceleration_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("anchored_return_memory_decay_reacceleration_filter", source)
        self.assertIn("anchored_session_return", source)
        self.assertIn("anchored_session_return_shifted", source)
        self.assertIn("anchored_return_memory_mean", source)
        self.assertIn("anchored_return_memory_decay_ratio", source)
        self.assertIn("anchored_return_reacceleration_long", source)
        self.assertIn("anchored_return_reacceleration_short", source)
        self.assertIn("anchored_return_parent_trend_long", source)
        self.assertIn("anchored_return_parent_trend_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_bayesian_surprise_innovation_shock_regime_filter(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["bayesian_surprise_innovation_shock_regime_filter"])

        self.assertEqual([spec.key for spec in specs], ["bayesian_surprise_innovation_shock_regime_filter"])
        self.assertEqual(specs[0].class_prefix, "BayesianSurpriseInnovationShockRegimeFilter")
        self.assertEqual(specs[0].main_regime, "RegimeUncertainty")
        self.assertEqual(specs[0].sub_regime, "PredictiveInnovationShock")
        self.assertEqual(specs[0].profit_factor, "BayesianSurpriseFilter")
        self.assertEqual(specs[0].child_profit_factor, "ParentSignalAdmission")
        self.assertEqual(specs[0].direction, "long")
        timeframes = ("5m", "15m", "30m", "1h", "4h", "1d")
        self.assertTrue(all(specs[0].supports(symbol="NQ", timeframe=timeframe) for timeframe in timeframes))
        self.assertFalse(specs[0].supports(symbol="NQ", timeframe="1m"))
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in timeframes],
            [
                "tomac_idxfut_clean_bayesian_surprise_innovation_shock_regime_filter_5m_v1",
                "tomac_idxfut_clean_bayesian_surprise_innovation_shock_regime_filter_15m_v1",
                "tomac_idxfut_clean_bayesian_surprise_innovation_shock_regime_filter_30m_v1",
                "tomac_idxfut_clean_bayesian_surprise_innovation_shock_regime_filter_1h_v1",
                "tomac_idxfut_clean_bayesian_surprise_innovation_shock_regime_filter_4h_v1",
                "tomac_idxfut_clean_bayesian_surprise_innovation_shock_regime_filter_1d_v1",
            ],
        )
        self.assertEqual(
            specs[0].branch_path_with_factor("15m"),
            "RegimeUncertainty -> PredictiveInnovationShock -> BayesianSurpriseFilter -> "
            "ParentSignalAdmission -> "
            "tomac_idxfut_clean_bayesian_surprise_innovation_shock_regime_filter_15m_v1",
        )

    def test_bayesian_surprise_strategy_source_uses_shifted_surprise_filter(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["bayesian_surprise_innovation_shock_regime_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_idxfut_clean_bayesian_surprise_innovation_shock_regime_filter_15m_v1", source)
        self.assertIn("PredictiveInnovationShock", source)
        self.assertIn("pred_close", source)
        self.assertIn("innovation", source)
        self.assertIn("surprise_z_shifted", source)
        self.assertIn("surprise_decay_shifted", source)
        self.assertIn("informative_not_panic", source)
        self.assertIn("parent_trend_long", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("exit_raw.shift(1)", source)

    def test_bayesian_surprise_gc_strategy_uses_gc_identity_and_pair_names(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["bayesian_surprise_innovation_shock_regime_filter"])[0]

        generated = module.generated_strategy_specs(
            ["GC"],
            "15m",
            families=["bayesian_surprise_innovation_shock_regime_filter"],
        )
        source = module.strategy_source(spec, symbol="GC", timeframe="15m")

        self.assertEqual(len(generated), 1)
        self.assertEqual(generated[0].symbol, "GC")
        self.assertEqual(
            generated[0].class_name,
            "TomacGCBayesianSurpriseInnovationShockRegimeFilterFifteenMinCleanV1",
        )
        self.assertIn('metadata.get("pair") != "GC/USD"', source)
        self.assertIn("symbol: GC", source)
        self.assertNotIn("XAU/USD", source)
        self.assertNotIn("XAU_USD", source)
        self.assertNotIn("TomacXAU", generated[0].class_name)
        self.assertIn("session_scope = \"ETH/full_retained_session\"", source)
        self.assertIn("rth_filter_applied = False", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_asi_trend_breakout_admission_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["asi_trend_breakout_admission_filter"])

        self.assertEqual([spec.key for spec in specs], ["asi_trend_breakout_admission_filter"])
        self.assertEqual(specs[0].class_prefix, "AsiTrendBreakoutAdmissionFilter")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "AccumulativeSwingIndex")
        self.assertEqual(specs[0].profit_factor, "BreakoutLineConfirmation")
        self.assertEqual(specs[0].child_profit_factor, "ParentTrendAdmissionFilter")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_asi_trend_breakout_admission_filter_5m_v1",
                "tomac_idxfut_clean_asi_trend_breakout_admission_filter_15m_v1",
                "tomac_idxfut_clean_asi_trend_breakout_admission_filter_30m_v1",
                "tomac_idxfut_clean_asi_trend_breakout_admission_filter_1h_v1",
                "tomac_idxfut_clean_asi_trend_breakout_admission_filter_4h_v1",
                "tomac_idxfut_clean_asi_trend_breakout_admission_filter_1d_v1",
            ],
        )
        self.assertEqual(
            specs[0].branch_path_with_factor("30m"),
            "TrendExpansion -> AccumulativeSwingIndex -> BreakoutLineConfirmation -> "
            "ParentTrendAdmissionFilter -> "
            "tomac_idxfut_clean_asi_trend_breakout_admission_filter_30m_v1",
        )

    def test_asi_strategy_source_uses_shifted_completed_bar_breakout_admission(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["asi_trend_breakout_admission_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("asi_trend_breakout_admission_filter", source)
        self.assertIn("factor_id: tomac_idxfut_clean_asi_trend_breakout_admission_filter_30m_v1", source)
        self.assertIn("AccumulativeSwingIndex", source)
        self.assertIn("asi_swing_index", source)
        self.assertIn("asi_accumulative_swing_index", source)
        self.assertIn("asi_accumulative_swing_index_shifted", source)
        self.assertIn("asi_breakout_line_shifted", source)
        self.assertIn("asi_breakdown_line_shifted", source)
        self.assertIn("asi_near_zero_veto", source)
        self.assertIn("asi_trend_breakout_admission_long", source)
        self.assertIn("asi_trend_breakout_admission_short", source)
        self.assertIn("asi_parent_trend_admission_long", source)
        self.assertIn("asi_parent_trend_admission_short", source)
        self.assertIn("asi_admission_failure_long", source)
        self.assertIn("asi_admission_failure_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_damiani_volatmeter_trend_admission_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["damiani_volatmeter_trend_admission_filter"])

        self.assertEqual([spec.key for spec in specs], ["damiani_volatmeter_trend_admission_filter"])
        self.assertEqual(specs[0].class_prefix, "DamianiVolatmeterTrendAdmissionFilter")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "DamianiVolatmeter")
        self.assertEqual(specs[0].profit_factor, "NoiseSuppressedTrendExpansion")
        self.assertEqual(specs[0].child_profit_factor, "ParentTrendAdmissionFilter")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_damiani_volatmeter_trend_admission_filter_5m_v1",
                "tomac_idxfut_clean_damiani_volatmeter_trend_admission_filter_15m_v1",
                "tomac_idxfut_clean_damiani_volatmeter_trend_admission_filter_30m_v1",
                "tomac_idxfut_clean_damiani_volatmeter_trend_admission_filter_1h_v1",
                "tomac_idxfut_clean_damiani_volatmeter_trend_admission_filter_4h_v1",
                "tomac_idxfut_clean_damiani_volatmeter_trend_admission_filter_1d_v1",
            ],
        )
        self.assertEqual(
            specs[0].branch_path_with_factor("30m"),
            "TrendExpansion -> DamianiVolatmeter -> NoiseSuppressedTrendExpansion -> "
            "ParentTrendAdmissionFilter -> "
            "tomac_idxfut_clean_damiani_volatmeter_trend_admission_filter_30m_v1",
        )

    def test_damiani_strategy_source_uses_shifted_volatility_noise_admission_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["damiani_volatmeter_trend_admission_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("damiani_volatmeter_trend_admission_filter", source)
        self.assertIn("factor_id: tomac_idxfut_clean_damiani_volatmeter_trend_admission_filter_30m_v1", source)
        self.assertIn("DamianiVolatmeter", source)
        self.assertIn("damiani_volatility_fast", source)
        self.assertIn("damiani_volatility_slow", source)
        self.assertIn("damiani_noise_floor", source)
        self.assertIn("damiani_signal_ratio_shifted", source)
        self.assertIn("damiani_noise_suppressed_state", source)
        self.assertIn("damiani_trend_admission_long", source)
        self.assertIn("damiani_trend_admission_short", source)
        self.assertIn("damiani_parent_trend_admission_long", source)
        self.assertIn("damiani_parent_trend_admission_short", source)
        self.assertIn("damiani_admission_failure_long", source)
        self.assertIn("damiani_admission_failure_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_internal_bar_strength_state_filter_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["internal_bar_strength_state_filter"])

        self.assertEqual([spec.key for spec in specs], ["internal_bar_strength_state_filter"])
        self.assertEqual(specs[0].class_prefix, "InternalBarStrengthStateFilter")
        self.assertEqual(specs[0].main_regime, "MeanReversionPressure")
        self.assertEqual(specs[0].sub_regime, "IntrabarCloseLocation")
        self.assertEqual(specs[0].profit_factor, "InternalBarStrengthState")
        self.assertEqual(specs[0].child_profit_factor, "ParentSignalAdmissionFilter")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_internal_bar_strength_state_filter_5m_v1",
                "tomac_idxfut_clean_internal_bar_strength_state_filter_15m_v1",
                "tomac_idxfut_clean_internal_bar_strength_state_filter_30m_v1",
                "tomac_idxfut_clean_internal_bar_strength_state_filter_1h_v1",
                "tomac_idxfut_clean_internal_bar_strength_state_filter_4h_v1",
                "tomac_idxfut_clean_internal_bar_strength_state_filter_1d_v1",
            ],
        )
        self.assertEqual(
            specs[0].branch_path_with_factor("30m"),
            "MeanReversionPressure -> IntrabarCloseLocation -> InternalBarStrengthState -> "
            "ParentSignalAdmissionFilter -> "
            "tomac_idxfut_clean_internal_bar_strength_state_filter_30m_v1",
        )

    def test_internal_bar_strength_strategy_source_uses_shifted_completed_bar_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["internal_bar_strength_state_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("internal_bar_strength_state_filter", source)
        self.assertIn("factor_id: tomac_idxfut_clean_internal_bar_strength_state_filter_30m_v1", source)
        self.assertIn("IntrabarCloseLocation", source)
        self.assertIn("internal_bar_strength_raw", source)
        self.assertIn("internal_bar_strength_shifted", source)
        self.assertIn("internal_bar_strength_recovery", source)
        self.assertIn("internal_bar_strength_low_reclaim_long", source)
        self.assertIn("internal_bar_strength_high_fade_short", source)
        self.assertIn("internal_bar_strength_parent_admission_long", source)
        self.assertIn("internal_bar_strength_parent_admission_short", source)
        self.assertIn("internal_bar_strength_failure_long", source)
        self.assertIn("internal_bar_strength_failure_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_volume_clock_relative_participation_breakout_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["volume_clock_relative_participation_breakout"])

        self.assertEqual([spec.key for spec in specs], ["volume_clock_relative_participation_breakout"])
        self.assertEqual(specs[0].class_prefix, "VolumeClockRelativeParticipationBreakout")
        self.assertEqual(specs[0].main_regime, "MarketMicrostructure")
        self.assertEqual(specs[0].sub_regime, "VolumeClockState")
        self.assertEqual(specs[0].profit_factor, "RelativeParticipationBreakout")
        self.assertEqual(specs[0].child_profit_factor, "MtfTrendConfirmation")
        self.assertEqual(specs[0].extra_profit_factors, ("FixedRrrAtrBracket",))
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_volume_clock_relative_participation_breakout_5m_v1",
                "tomac_idxfut_clean_volume_clock_relative_participation_breakout_15m_v1",
                "tomac_idxfut_clean_volume_clock_relative_participation_breakout_30m_v1",
                "tomac_idxfut_clean_volume_clock_relative_participation_breakout_1h_v1",
                "tomac_idxfut_clean_volume_clock_relative_participation_breakout_4h_v1",
                "tomac_idxfut_clean_volume_clock_relative_participation_breakout_1d_v1",
            ],
        )
        self.assertEqual(
            specs[0].branch_path_with_factor("30m"),
            "MarketMicrostructure -> VolumeClockState -> RelativeParticipationBreakout -> "
            "MtfTrendConfirmation -> FixedRrrAtrBracket -> "
            "tomac_idxfut_clean_volume_clock_relative_participation_breakout_30m_v1",
        )

    def test_volume_clock_strategy_source_uses_shifted_relative_participation_breakout(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["volume_clock_relative_participation_breakout"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("volume_clock_relative_participation_breakout", source)
        self.assertIn("factor_id: tomac_idxfut_clean_volume_clock_relative_participation_breakout_30m_v1", source)
        self.assertIn("VolumeClockState", source)
        self.assertIn("volume_clock_progress", source)
        self.assertIn("relative_participation", source)
        self.assertIn("volume_clock_accel", source)
        self.assertIn("volume_clock_breakout_long", source)
        self.assertIn("volume_clock_breakout_short", source)
        self.assertIn("volume_clock_mtf_trend_long", source)
        self.assertIn("volume_clock_mtf_trend_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_volume_flow_impulse_trend_rejoin_nq4h_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["volume_flow_impulse_trend_rejoin_filter"])

        self.assertEqual([spec.key for spec in specs], ["volume_flow_impulse_trend_rejoin_filter"])
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "VolumeFlowImpulseTrendRejoinFilter")
        self.assertEqual(spec.direction, "long_short")
        self.assertTrue(spec.supports(symbol="NQ", timeframe="4h"))
        self.assertFalse(spec.supports(symbol="ES", timeframe="4h"))
        self.assertFalse(spec.supports(symbol="NQ", timeframe="1h"))
        self.assertEqual(
            spec.branch_path,
            "RegimeRoot -> TrendExpansion -> VolumeFlowImpulse -> KlingerObvAcceleration -> TrendRejoin",
        )
        self.assertEqual(spec.factor_id("4h"), "tomac_nq_4h_volume_flow_impulse_trend_rejoin_v1")
        self.assertEqual(
            spec.branch_path_with_factor("4h"),
            "RegimeRoot -> TrendExpansion -> VolumeFlowImpulse -> KlingerObvAcceleration -> "
            "TrendRejoin -> tomac_nq_4h_volume_flow_impulse_trend_rejoin_v1",
        )

    def test_volume_flow_impulse_trend_rejoin_source_uses_shifted_klinger_obv_admission(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["volume_flow_impulse_trend_rejoin_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="4h")

        self.assertIn("factor_id: tomac_nq_4h_volume_flow_impulse_trend_rejoin_v1", source)
        self.assertIn("VolumeFlowImpulse", source)
        self.assertIn("volume_flow_klinger_osc", source)
        self.assertIn("volume_flow_klinger_z_shifted", source)
        self.assertIn("volume_flow_obv_accel_shifted", source)
        self.assertIn("volume_flow_impulse_trend_rejoin_long.fillna(False)", source)
        self.assertIn("volume_flow_impulse_trend_rejoin_short.fillna(False)", source)
        self.assertIn("entry = entry_raw.shift(1).fillna(False)", source)
        self.assertIn("short_entry = short_entry_raw.shift(1).fillna(False)", source)
        branch_start = source.index(
            'elif "volume_flow_impulse_trend_rejoin_filter" == "volume_flow_impulse_trend_rejoin_filter":'
        )
        next_branch = source.index('elif "', branch_start + 1)
        volume_flow_block = source[branch_start:next_branch]
        self.assertNotIn("shift(-", volume_flow_block)

    def test_candidate_specs_can_select_decay_weighted_trend_reacceleration_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["decay_weighted_trend_reacceleration_filter"])

        self.assertEqual([spec.key for spec in specs], ["decay_weighted_trend_reacceleration_filter"])
        self.assertEqual(specs[0].class_prefix, "DecayWeightedTrendReaccelerationFilter")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "DecayWeightedTrendState")
        self.assertEqual(specs[0].profit_factor, "PullbackEnergyRelease")
        self.assertEqual(specs[0].child_profit_factor, "ReaccelerationAdmission")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_decay_weighted_trend_reacceleration_filter_5m_v1",
                "tomac_idxfut_clean_decay_weighted_trend_reacceleration_filter_15m_v1",
                "tomac_idxfut_clean_decay_weighted_trend_reacceleration_filter_30m_v1",
                "tomac_idxfut_clean_decay_weighted_trend_reacceleration_filter_1h_v1",
                "tomac_idxfut_clean_decay_weighted_trend_reacceleration_filter_4h_v1",
                "tomac_idxfut_clean_decay_weighted_trend_reacceleration_filter_1d_v1",
            ],
        )

    def test_decay_weighted_trend_reacceleration_strategy_source_uses_shifted_decay_features(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["decay_weighted_trend_reacceleration_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="1h")

        self.assertIn("decay_weighted_trend_reacceleration_filter", source)
        self.assertIn("decay_weighted_trend_fast", source)
        self.assertIn("decay_weighted_trend_slow", source)
        self.assertIn("decay_weighted_trend_spread_shifted", source)
        self.assertIn("decay_weighted_pullback_energy", source)
        self.assertIn("decay_weighted_reacceleration", source)
        self.assertIn("decay_weighted_reacceleration_long", source)
        self.assertIn("decay_weighted_reacceleration_short", source)
        self.assertIn("decay_weighted_parent_trend_long", source)
        self.assertIn("decay_weighted_parent_trend_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_volume_weighted_macd_trend_reacceleration_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["volume_weighted_macd_trend_reacceleration_filter"])

        self.assertEqual([spec.key for spec in specs], ["volume_weighted_macd_trend_reacceleration_filter"])
        self.assertEqual(specs[0].class_prefix, "VolumeWeightedMacdTrendReaccelerationFilter")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "VolumeWeightedMomentum")
        self.assertEqual(specs[0].profit_factor, "VwmacdReacceleration")
        self.assertEqual(specs[0].child_profit_factor, "ParentTrendAdmission")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_volume_weighted_macd_trend_reacceleration_filter_5m_v1",
                "tomac_idxfut_clean_volume_weighted_macd_trend_reacceleration_filter_15m_v1",
                "tomac_idxfut_clean_volume_weighted_macd_trend_reacceleration_filter_30m_v1",
                "tomac_idxfut_clean_volume_weighted_macd_trend_reacceleration_filter_1h_v1",
                "tomac_idxfut_clean_volume_weighted_macd_trend_reacceleration_filter_4h_v1",
                "tomac_idxfut_clean_volume_weighted_macd_trend_reacceleration_filter_1d_v1",
            ],
        )

    def test_volume_weighted_macd_strategy_source_uses_shifted_reacceleration_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["volume_weighted_macd_trend_reacceleration_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="1h")

        self.assertIn("volume_weighted_macd_trend_reacceleration_filter", source)
        self.assertIn("vwmacd_fast_vwma", source)
        self.assertIn("vwmacd_slow_vwma", source)
        self.assertIn("vwmacd_spread", source)
        self.assertIn("vwmacd_spread_shifted", source)
        self.assertIn("vwmacd_reacceleration", source)
        self.assertIn("vwmacd_reacceleration_long", source)
        self.assertIn("vwmacd_reacceleration_short", source)
        self.assertIn("vwmacd_parent_trend_long", source)
        self.assertIn("vwmacd_parent_trend_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_buff_averages_volume_weighted_trend_reacceleration_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(
            families=["buff_averages_volume_weighted_trend_reacceleration_filter"]
        )

        self.assertEqual(
            [spec.key for spec in specs],
            ["buff_averages_volume_weighted_trend_reacceleration_filter"],
        )
        self.assertEqual(specs[0].class_prefix, "BuffAveragesVolumeWeightedTrendReaccelerationFilter")
        self.assertEqual(specs[0].main_regime, "RegimeRoot")
        self.assertEqual(specs[0].sub_regime, "TrendExpansion")
        self.assertEqual(specs[0].profit_factor, "VolumeWeightedAverageSpreadState")
        self.assertEqual(specs[0].child_profit_factor, "BuffAveragesReacceleration")
        self.assertEqual(specs[0].extra_profit_factors, ("MtfTrendResonance",))
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_buff_averages_volume_weighted_trend_reacceleration_filter_5m_v1",
                "tomac_idxfut_clean_buff_averages_volume_weighted_trend_reacceleration_filter_15m_v1",
                "tomac_idxfut_clean_buff_averages_volume_weighted_trend_reacceleration_filter_30m_v1",
                "tomac_idxfut_clean_buff_averages_volume_weighted_trend_reacceleration_filter_1h_v1",
                "tomac_idxfut_clean_buff_averages_volume_weighted_trend_reacceleration_filter_4h_v1",
                "tomac_idxfut_clean_buff_averages_volume_weighted_trend_reacceleration_filter_1d_v1",
            ],
        )
        self.assertEqual(
            specs[0].branch_path_with_factor("30m"),
            "RegimeRoot -> TrendExpansion -> VolumeWeightedAverageSpreadState -> "
            "BuffAveragesReacceleration -> MtfTrendResonance -> "
            "tomac_idxfut_clean_buff_averages_volume_weighted_trend_reacceleration_filter_30m_v1",
        )

    def test_buff_averages_strategy_source_uses_shifted_volume_weighted_spread(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(
            families=["buff_averages_volume_weighted_trend_reacceleration_filter"]
        )[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("buff_averages_volume_weighted_trend_reacceleration_filter", source)
        self.assertIn("buff_averages_price_volume", source)
        self.assertIn("buff_averages_fast", source)
        self.assertIn("buff_averages_slow", source)
        self.assertIn("buff_averages_spread_shifted", source)
        self.assertIn("buff_averages_reacceleration", source)
        self.assertIn("buff_averages_reacceleration_long", source)
        self.assertIn("buff_averages_reacceleration_short", source)
        self.assertIn("buff_averages_mtf_resonance_long", source)
        self.assertIn("buff_averages_mtf_resonance_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_relative_vigor_index_mtf_reacceleration_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["relative_vigor_index_mtf_reacceleration_filter"])

        self.assertEqual([spec.key for spec in specs], ["relative_vigor_index_mtf_reacceleration_filter"])
        self.assertEqual(specs[0].class_prefix, "RelativeVigorIndexMtfReaccelerationFilter")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "RelativeVigorMomentumState")
        self.assertEqual(specs[0].profit_factor, "RelativeVigorReacceleration")
        self.assertEqual(specs[0].child_profit_factor, "MtfTrendReclaim")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_relative_vigor_index_mtf_reacceleration_filter_5m_v1",
                "tomac_idxfut_clean_relative_vigor_index_mtf_reacceleration_filter_15m_v1",
                "tomac_idxfut_clean_relative_vigor_index_mtf_reacceleration_filter_30m_v1",
                "tomac_idxfut_clean_relative_vigor_index_mtf_reacceleration_filter_1h_v1",
                "tomac_idxfut_clean_relative_vigor_index_mtf_reacceleration_filter_4h_v1",
                "tomac_idxfut_clean_relative_vigor_index_mtf_reacceleration_filter_1d_v1",
            ],
        )

    def test_relative_vigor_index_strategy_source_uses_shifted_mtf_reacceleration(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["relative_vigor_index_mtf_reacceleration_filter"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("relative_vigor_index_mtf_reacceleration_filter", source)
        self.assertIn("relative_vigor_index_numerator", source)
        self.assertIn("relative_vigor_index_denominator", source)
        self.assertIn("relative_vigor_index_value", source)
        self.assertIn("relative_vigor_index_signal", source)
        self.assertIn("relative_vigor_index_value_shifted", source)
        self.assertIn("relative_vigor_reacceleration_long", source)
        self.assertIn("relative_vigor_reacceleration_short", source)
        self.assertIn("rvi_mtf_trend_reclaim_long", source)
        self.assertIn("rvi_mtf_trend_reclaim_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_low_volatility_trend_pullback_reacceleration_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["low_volatility_trend_pullback_reacceleration"])

        self.assertEqual([spec.key for spec in specs], ["low_volatility_trend_pullback_reacceleration"])
        self.assertEqual(specs[0].class_prefix, "LowVolatilityTrendPullbackReacceleration")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "LowVolatilityPersistence")
        self.assertEqual(specs[0].profit_factor, "PullbackReacceleration")
        self.assertEqual(specs[0].child_profit_factor, "MtfOptionalResonance")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_low_volatility_trend_pullback_reacceleration_5m_v1",
                "tomac_idxfut_clean_low_volatility_trend_pullback_reacceleration_15m_v1",
                "tomac_idxfut_clean_low_volatility_trend_pullback_reacceleration_30m_v1",
                "tomac_idxfut_clean_low_volatility_trend_pullback_reacceleration_1h_v1",
                "tomac_idxfut_clean_low_volatility_trend_pullback_reacceleration_4h_v1",
                "tomac_idxfut_clean_low_volatility_trend_pullback_reacceleration_1d_v1",
            ],
        )

    def test_low_volatility_trend_pullback_reacceleration_source_uses_shifted_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["low_volatility_trend_pullback_reacceleration"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("factor_id: tomac_idxfut_clean_low_volatility_trend_pullback_reacceleration_30m_v1", source)
        self.assertIn("LowVolatilityPersistence", source)
        self.assertIn("low_volatility_state", source)
        self.assertIn("low_volatility_pullback_depth_atr", source)
        self.assertIn("low_volatility_reacceleration", source)
        self.assertIn("low_volatility_trend_pullback_reacceleration_long", source)
        self.assertIn("low_volatility_trend_pullback_reacceleration_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_session_vwap_absorption_reacceleration_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["session_vwap_absorption_reacceleration"])

        self.assertEqual([spec.key for spec in specs], ["session_vwap_absorption_reacceleration"])
        self.assertEqual(specs[0].class_prefix, "SessionVwapAbsorptionReacceleration")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "LiquidityAbsorption")
        self.assertEqual(specs[0].profit_factor, "SessionVwapReacceleration")
        self.assertEqual(specs[0].child_profit_factor, "MtfOptionalResonance")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_session_vwap_absorption_reacceleration_5m_v1",
                "tomac_idxfut_clean_session_vwap_absorption_reacceleration_15m_v1",
                "tomac_idxfut_clean_session_vwap_absorption_reacceleration_30m_v1",
                "tomac_idxfut_clean_session_vwap_absorption_reacceleration_1h_v1",
                "tomac_idxfut_clean_session_vwap_absorption_reacceleration_4h_v1",
                "tomac_idxfut_clean_session_vwap_absorption_reacceleration_1d_v1",
            ],
        )

    def test_session_vwap_absorption_reacceleration_source_uses_shifted_absorption_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["session_vwap_absorption_reacceleration"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="5m")

        self.assertIn("factor_id: tomac_idxfut_clean_session_vwap_absorption_reacceleration_5m_v1", source)
        self.assertIn("TrendExpansion", source)
        self.assertIn("session_vwap_absorption_distance_atr", source)
        self.assertIn("session_vwap_absorption_compressed", source)
        self.assertIn("session_vwap_reacceleration_long", source)
        self.assertIn("session_vwap_reacceleration_short", source)
        self.assertIn("session_vwap_mtf_optional_resonance_long", source)
        self.assertIn("session_vwap_mtf_optional_resonance_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_bop_volume_pressure_trend_acceptance_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["balance_of_power_volume_pressure_trend_acceptance_filter"])

        self.assertEqual([spec.key for spec in specs], ["balance_of_power_volume_pressure_trend_acceptance_filter"])
        self.assertEqual(specs[0].class_prefix, "BalanceOfPowerVolumePressureTrendAcceptanceFilter")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "CandleBodyPressure")
        self.assertEqual(specs[0].profit_factor, "BalanceOfPowerVolumeConfirmation")
        self.assertEqual(specs[0].child_profit_factor, "MtfTrendAcceptance")
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_balance_of_power_volume_pressure_trend_acceptance_filter_5m_v1",
                "tomac_idxfut_clean_balance_of_power_volume_pressure_trend_acceptance_filter_15m_v1",
                "tomac_idxfut_clean_balance_of_power_volume_pressure_trend_acceptance_filter_30m_v1",
                "tomac_idxfut_clean_balance_of_power_volume_pressure_trend_acceptance_filter_1h_v1",
                "tomac_idxfut_clean_balance_of_power_volume_pressure_trend_acceptance_filter_4h_v1",
                "tomac_idxfut_clean_balance_of_power_volume_pressure_trend_acceptance_filter_1d_v1",
            ],
        )

    def test_bop_volume_pressure_trend_acceptance_source_uses_shifted_pressure(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["balance_of_power_volume_pressure_trend_acceptance_filter"])[0]

        source = module.strategy_source(spec, symbol="YM", timeframe="1h")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_balance_of_power_volume_pressure_trend_acceptance_filter_1h_v1",
            source,
        )
        self.assertIn("CandleBodyPressure", source)
        self.assertIn("bop_pressure_value", source)
        self.assertIn("bop_pressure_shifted", source)
        self.assertIn("bop_volume_participation", source)
        self.assertIn("bop_volume_pressure_trend_acceptance_long", source)
        self.assertIn("bop_volume_pressure_trend_acceptance_short", source)
        self.assertIn("bop_mtf_trend_acceptance_long", source)
        self.assertIn("bop_mtf_trend_acceptance_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_pfe_trend_acceptance_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["polarized_fractal_efficiency_trend_acceptance"])

        self.assertEqual([spec.key for spec in specs], ["polarized_fractal_efficiency_trend_acceptance"])
        self.assertEqual(specs[0].class_prefix, "PolarizedFractalEfficiencyTrendAcceptance")
        self.assertEqual(specs[0].main_regime, "RegimeRoot")
        self.assertEqual(specs[0].sub_regime, "TrendExpansion")
        self.assertEqual(specs[0].profit_factor, "FractalEfficiency")
        self.assertEqual(specs[0].child_profit_factor, "PolarizedFractalEfficiencyTrendAcceptance")
        self.assertEqual(specs[0].extra_profit_factors, ("MtfSlopeResonance",))
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_polarized_fractal_efficiency_trend_acceptance_5m_v1",
                "tomac_idxfut_clean_polarized_fractal_efficiency_trend_acceptance_15m_v1",
                "tomac_idxfut_clean_polarized_fractal_efficiency_trend_acceptance_30m_v1",
                "tomac_idxfut_clean_polarized_fractal_efficiency_trend_acceptance_1h_v1",
                "tomac_idxfut_clean_polarized_fractal_efficiency_trend_acceptance_4h_v1",
                "tomac_idxfut_clean_polarized_fractal_efficiency_trend_acceptance_1d_v1",
            ],
        )

    def test_pfe_trend_acceptance_source_uses_completed_bar_pfe_and_mtf_alignment(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["polarized_fractal_efficiency_trend_acceptance"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="5m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_polarized_fractal_efficiency_trend_acceptance_5m_v1",
            source,
        )
        self.assertIn("PolarizedFractalEfficiencyTrendAcceptance", source)
        self.assertIn("pfe_close_bps", source)
        self.assertIn("pfe_shifted", source)
        self.assertIn("pfe_slope_shifted", source)
        self.assertIn("pfe_lookback_return_bps_shifted", source)
        self.assertIn("pfe_mtf_long_aligned", source)
        self.assertIn("pfe_mtf_short_aligned", source)
        self.assertIn("pfe_trend_acceptance_long", source)
        self.assertIn("pfe_trend_acceptance_short", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_trend_turtle_soup_density_repair_child_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["trend_turtle_soup_density_repair_child"])

        self.assertEqual([spec.key for spec in specs], ["trend_turtle_soup_density_repair_child"])
        self.assertEqual(specs[0].class_prefix, "TrendTurtleSoupDensityRepairChild")
        self.assertEqual(specs[0].main_regime, "RegimeRoot")
        self.assertEqual(specs[0].sub_regime, "TrendPersistence")
        self.assertEqual(specs[0].profit_factor, "DonchianFalseBreak")
        self.assertEqual(specs[0].child_profit_factor, "TurtleSoupContinuationReclaim")
        self.assertEqual(specs[0].extra_profit_factors, ("DensityRepairChild",))
        self.assertEqual(specs[0].direction, "long_short")
        self.assertEqual(
            [specs[0].factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_trend_turtle_soup_density_repair_child_5m_v1",
                "tomac_idxfut_clean_trend_turtle_soup_density_repair_child_15m_v1",
                "tomac_idxfut_clean_trend_turtle_soup_density_repair_child_30m_v1",
                "tomac_idxfut_clean_trend_turtle_soup_density_repair_child_1h_v1",
                "tomac_idxfut_clean_trend_turtle_soup_density_repair_child_4h_v1",
                "tomac_idxfut_clean_trend_turtle_soup_density_repair_child_1d_v1",
            ],
        )

    def test_trend_turtle_soup_density_repair_source_uses_shifted_session_slot_reclaim(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["trend_turtle_soup_density_repair_child"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="5m")

        self.assertIn("factor_id: tomac_idxfut_clean_trend_turtle_soup_density_repair_child_5m_v1", source)
        self.assertIn("TrendTurtleSoupDensityRepairChild", source)
        self.assertIn("turtle_soup_density_repair_session_slot", source)
        self.assertIn("turtle_soup_false_break_low", source)
        self.assertIn("turtle_soup_false_break_high", source)
        self.assertIn("turtle_soup_reclaim_long", source)
        self.assertIn("turtle_soup_reclaim_short", source)
        self.assertIn("turtle_soup_mtf_resonance_long", source)
        self.assertIn("turtle_soup_mtf_resonance_short", source)
        self.assertIn("short_raw", source)

    def test_candidate_specs_can_select_price_stiffness_density_trend_carry_family(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["price_stiffness_density_trend_carry"])

        self.assertEqual([spec.key for spec in specs], ["price_stiffness_density_trend_carry"])
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "PriceStiffnessDensityTrendCarry")
        self.assertEqual(spec.main_regime, "TrendExpansion")
        self.assertEqual(spec.sub_regime, "PriceDistributionStiffness")
        self.assertEqual(spec.profit_factor, "DensityTrendCarry")
        self.assertEqual(spec.child_profit_factor, "MtfResonanceAdmission")
        self.assertEqual(spec.direction, "long_short")
        self.assertTrue(all(spec.supports(symbol="NQ", timeframe=timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")))
        self.assertTrue(all(spec.supports(symbol="YM", timeframe=timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")))
        self.assertTrue(all(spec.supports(symbol="GC", timeframe=timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")))
        self.assertFalse(spec.supports(symbol="XAU", timeframe="5m"))
        self.assertFalse(spec.supports(symbol="ES", timeframe="5m"))
        self.assertFalse(spec.supports(symbol="NQ", timeframe="1m"))
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_price_stiffness_density_trend_carry_5m_v1",
                "tomac_idxfut_clean_price_stiffness_density_trend_carry_15m_v1",
                "tomac_idxfut_clean_price_stiffness_density_trend_carry_30m_v1",
                "tomac_idxfut_clean_price_stiffness_density_trend_carry_1h_v1",
                "tomac_idxfut_clean_price_stiffness_density_trend_carry_4h_v1",
                "tomac_idxfut_clean_price_stiffness_density_trend_carry_1d_v1",
            ],
        )

    def test_price_stiffness_density_trend_carry_source_uses_shifted_completed_bar_features(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["price_stiffness_density_trend_carry"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="5m")

        self.assertIn("factor_id: tomac_idxfut_clean_price_stiffness_density_trend_carry_5m_v1", source)
        self.assertIn("PriceStiffnessDensityTrendCarry", source)
        self.assertIn("price_stiffness_clv", source)
        self.assertIn("price_stiffness_upper", source)
        self.assertIn("price_stiffness_lower", source)
        self.assertIn("price_stiffness_path_efficiency", source)
        self.assertIn("price_stiffness_range_density", source)
        self.assertIn("price_stiffness_mtf_resonance_long", source)
        self.assertIn("price_stiffness_mtf_resonance_short", source)
        self.assertIn("price_stiffness_reclaim_long", source)
        self.assertIn("price_stiffness_reclaim_short", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        branch_start = source.index('elif "price_stiffness_density_trend_carry" == "price_stiffness_density_trend_carry":')
        next_branch = source.index('elif "', branch_start + 1)
        price_stiffness_block = source[branch_start:next_branch]
        self.assertNotIn("shift(-", price_stiffness_block)

    def test_candidate_specs_can_select_hurst_efficiency_density_repair_exact_nq5m_only(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["hurst_efficiency_density_repair"])

        self.assertEqual([spec.key for spec in specs], ["hurst_efficiency_density_repair"])
        self.assertEqual(specs[0].class_prefix, "HurstEfficiencyDensityRepair")
        self.assertEqual(specs[0].main_regime, "TrendExpansion")
        self.assertEqual(specs[0].sub_regime, "HurstEfficiencyPersistence")
        self.assertEqual(specs[0].profit_factor, "CompressionPause")
        self.assertEqual(specs[0].child_profit_factor, "ReaccelerationBreakout")
        self.assertEqual(specs[0].extra_profit_factors, ("DensityRepair",))
        self.assertEqual(specs[0].direction, "long")
        self.assertEqual(specs[0].factor_id("5m"), "tomac_idxfut_clean_hurst_efficiency_density_repair_v1")
        self.assertEqual(
            module.generated_strategy_specs(
                ["NQ", "YM"],
                "5m",
                families=["hurst_efficiency_density_repair"],
            )[0].symbol,
            "NQ",
        )
        self.assertEqual(
            module.generated_strategy_specs(
                ["NQ"],
                "15m",
                families=["hurst_efficiency_density_repair"],
            ),
            [],
        )

    def test_hurst_efficiency_density_repair_source_uses_shifted_state_and_context(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["hurst_efficiency_density_repair"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="5m")

        self.assertIn("factor_id: tomac_idxfut_clean_hurst_efficiency_density_repair_v1", source)
        self.assertIn("HurstEfficiencyPersistence", source)
        self.assertIn("hurst_efficiency_ratio_shifted", source)
        self.assertIn("hurst_proxy_shifted", source)
        self.assertIn("hurst_context_efficiency_ratio_shifted", source)
        self.assertIn("hurst_density_repair_microbreak_long", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("exit_raw.shift(1)", source)
        context_start = source.index("hurst_context_base = dataframe")
        hurst_context_start = source.index('hurst_context_path = dataframe["ema20_15m"]')
        self.assertLess(context_start, hurst_context_start)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_fisher_transform_trend_rejoin_exact_nq5m_only(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["fisher_transform_trend_rejoin"])

        self.assertEqual([spec.key for spec in specs], ["fisher_transform_trend_rejoin"])
        self.assertEqual(specs[0].class_prefix, "FisherTransformTrendRejoin")
        self.assertEqual(specs[0].main_regime, "RegimeRoot")
        self.assertEqual(specs[0].sub_regime, "TrendExpansion")
        self.assertEqual(specs[0].profit_factor, "FisherTransformCycleState")
        self.assertEqual(specs[0].child_profit_factor, "PullbackExhaustion")
        self.assertEqual(specs[0].extra_profit_factors, ("TrendRejoin", "MtfSlopeResonance"))
        self.assertEqual(specs[0].direction, "long")
        self.assertEqual(specs[0].factor_id("5m"), "tomac_idxfut_clean_fisher_transform_trend_rejoin_nq5m_long_v1")
        self.assertEqual(
            module.generated_strategy_specs(
                ["NQ", "YM"],
                "5m",
                families=["fisher_transform_trend_rejoin"],
            )[0].symbol,
            "NQ",
        )
        self.assertEqual(
            module.generated_strategy_specs(
                ["NQ"],
                "15m",
                families=["fisher_transform_trend_rejoin"],
            ),
            [],
        )

    def test_fisher_transform_trend_rejoin_source_uses_shifted_cycle_state(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["fisher_transform_trend_rejoin"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="5m")

        self.assertIn("factor_id: tomac_idxfut_clean_fisher_transform_trend_rejoin_nq5m_long_v1", source)
        self.assertIn("FisherTransformCycleState", source)
        self.assertIn("fisher_transform_value_shifted", source)
        self.assertIn("fisher_transform_signal_shifted", source)
        self.assertIn("fisher_transform_turn", source)
        self.assertIn("fisher_transform_pullback_depth_atr", source)
        self.assertIn("fisher_mtf_slope_resonance_long", source)
        self.assertIn("fisher_transform_rejoin_long.fillna(False)", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("exit_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_kairi_ym5m_year_stability_refinement(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["kairi_ym5m_year_stability_refinement"])

        self.assertEqual([spec.key for spec in specs], ["kairi_ym5m_year_stability_refinement"])
        self.assertEqual(specs[0].class_prefix, "KairiYm5mYearStabilityRefinement")
        self.assertEqual(specs[0].main_regime, "RegimeRoot")
        self.assertEqual(specs[0].sub_regime, "TrendPersistence")
        self.assertEqual(specs[0].profit_factor, "KairiMaDeviationPullback")
        self.assertEqual(specs[0].child_profit_factor, "TrendRejoin")
        self.assertEqual(specs[0].extra_profit_factors, ("Ym5mYearStabilityRefinement",))
        self.assertEqual(specs[0].direction, "long")
        self.assertEqual(
            specs[0].factor_id("5m"),
            "tomac_ym_5m_kairi_ma_deviation_trend_rejoin_year_stability_ystabe18r2s5t140_v1",
        )

    def test_kairi_ym5m_year_stability_exact_candidate_scope_is_ym_5m_only(self) -> None:
        module = self.load_module()

        spec = module.candidate_specs(families=["kairi_ym5m_year_stability_refinement"])[0]
        generated = module.generated_strategy_specs(
            ["NQ", "YM"],
            "5m",
            families=["kairi_ym5m_year_stability_refinement"],
        )

        self.assertEqual(
            spec.factor_id("5m"),
            "tomac_ym_5m_kairi_ma_deviation_trend_rejoin_year_stability_ystabe18r2s5t140_v1",
        )
        self.assertEqual(len(generated), 1)
        self.assertEqual(generated[0].symbol, "YM")
        self.assertEqual(generated[0].timeframe, "5m")
        self.assertEqual(
            generated[0].factor_id,
            "tomac_ym_5m_kairi_ma_deviation_trend_rejoin_year_stability_ystabe18r2s5t140_v1",
        )
        self.assertEqual(
            module.generated_strategy_specs(
                ["YM"],
                "15m",
                families=["kairi_ym5m_year_stability_refinement"],
            ),
            [],
        )

    def test_kairi_ym5m_year_stability_source_uses_shifted_kairi_rejoin(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["kairi_ym5m_year_stability_refinement"])[0]

        source = module.strategy_source(spec, symbol="YM", timeframe="5m")

        self.assertIn(
            "factor_id: tomac_ym_5m_kairi_ma_deviation_trend_rejoin_year_stability_ystabe18r2s5t140_v1",
            source,
        )
        self.assertIn("KairiMaDeviationPullback", source)
        self.assertIn("kairi_ma_deviation_bps", source)
        self.assertIn("kairi_pullback_low_prev", source)
        self.assertIn("kairi_ym5m_year_stability_long", source)
        self.assertIn("kairi_ym5m_mtf_resonance_long", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("exit_raw.shift(1)", source)
        self.assertIn("can_short = False", source)
        self.assertNotIn("shift(-", source)

    def test_source_universe_includes_tomac_6e_long_history(self) -> None:
        module = self.load_module()

        by_symbol = {source.symbol: source for source in module.source_universe()}

        self.assertIn("6E", by_symbol)
        self.assertEqual(
            by_symbol["6E"].source_csv,
            Path("/Users/thrill3r/Downloads/Tomac/eur future 2015-2025/glbx-mdp3-20150101-20251231.ohlcv-1m.csv"),
        )

    def test_source_universe_uses_zip_pristine_es_and_nq_paths(self) -> None:
        module = self.load_module()

        by_symbol = {source.symbol: source for source in module.source_universe()}

        self.assertEqual(
            by_symbol["ES"].source_csv,
            Path("/Users/thrill3r/Downloads/Tomac/es future 2021-2025/glbx-mdp3-20110101-20251231.ohlcv-1m.csv"),
        )
        self.assertEqual(
            by_symbol["ES"].archive_zip,
            Path("/Users/thrill3r/Downloads/Tomac/es future 2021-2025.zip"),
        )
        self.assertEqual(
            by_symbol["NQ"].source_csv,
            Path("/Users/thrill3r/Downloads/Tomac/nq future 2021-2025/glbx-mdp3-20110101-20251231.ohlcv-1m.csv"),
        )
        self.assertEqual(
            by_symbol["NQ"].archive_member,
            "glbx-mdp3-20110101-20251231.ohlcv-1m.csv",
        )

    def test_zip_pristine_validation_rejects_symlink_or_extra_source_files(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "es future 2021-2025.zip"
            source_dir = root / "es future 2021-2025"
            source_dir.mkdir()
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("glbx-mdp3-20110101-20251231.ohlcv-1m.csv", "ts_event,open,high,low,close,volume,symbol\n")
                zf.writestr("manifest.json", "{}\n")
            real_old = source_dir / "glbx-mdp3-20100606-20260403.ohlcv-1m.csv"
            real_old.write_text("polluted\n", encoding="utf-8")
            symlink = source_dir / "glbx-mdp3-20110101-20251231.ohlcv-1m.csv"
            symlink.symlink_to(real_old)
            (source_dir / "manifest.json").write_text("{}\n", encoding="utf-8")

            source = module.TomacSource(
                symbol="ES",
                source_csv=symlink,
                archive_zip=archive,
                archive_member="glbx-mdp3-20110101-20251231.ohlcv-1m.csv",
            )

            with self.assertRaises(ValueError) as context:
                module.validate_zip_pristine_source(source)

        message = str(context.exception)
        self.assertIn("source_csv_is_symlink", message)
        self.assertIn("extracted_source_dir_has_extra_files", message)

    def test_zip_pristine_validation_passes_exact_extracted_zip_payload(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "nq future 2021-2025.zip"
            source_dir = root / "nq future 2021-2025"
            source_dir.mkdir()
            csv_name = "glbx-mdp3-20110101-20251231.ohlcv-1m.csv"
            csv_text = "ts_event,open,high,low,close,volume,symbol\n"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr(csv_name, csv_text)
                zf.writestr("manifest.json", "{}\n")
            (source_dir / csv_name).write_text(csv_text, encoding="utf-8")
            (source_dir / "manifest.json").write_text("{}\n", encoding="utf-8")

            packet = module.validate_zip_pristine_source(
                module.TomacSource(
                    symbol="NQ",
                    source_csv=source_dir / csv_name,
                    archive_zip=archive,
                    archive_member=csv_name,
                )
            )

        self.assertEqual(packet["status"], "pass_zip_pristine_source")
        self.assertEqual(packet["blockers"], [])

    def test_source_universe_canonicalizes_legacy_xau_source_as_gc(self) -> None:
        module = self.load_module()

        by_symbol = {source.symbol: source for source in module.source_universe()}

        self.assertIn("GC", by_symbol)
        self.assertNotIn("XAU", by_symbol)
        self.assertEqual(
            by_symbol["GC"].source_csv,
            Path("/Users/thrill3r/Downloads/Tomac/xau future 2021-2025/glbx-mdp3-20210106-20260105.ohlcv-1m.csv"),
        )

    def test_write_clean_bundle_uses_gc_data_filenames_for_legacy_xau_source(self) -> None:
        module = self.load_module()
        if not module.has_pyarrow():
            self.skipTest("pyarrow unavailable")

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "root"
            source_csv = Path(tmpdir) / "legacy_xau.csv"
            source_csv.write_text(
                "\n".join(
                    [
                        "ts_event,open,high,low,close,volume,symbol",
                        "2025-03-17T13:30:00Z,2300,2301,2299,2300.5,120,GCG5",
                        "2025-03-17T13:30:00Z,1,1.2,0.8,1.1,9999,GCG5-GCJ5",
                        "2025-03-17T13:31:00Z,2301,2302,2300,2301.5,200,GCJ5",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            bundle = module.write_clean_bundle(
                module.TomacSource(symbol="GC", source_csv=source_csv),
                root=root,
                start="2025-03-17",
                end="2025-03-18",
                timeframes=("1m", "5m"),
                max_rows=None,
                chunksize=10,
            )

            self.assertEqual(bundle["symbol"], "GC")
            self.assertTrue((root / "clean" / "GC" / "GC_USD-1m.feather").exists())
            self.assertTrue((root / "clean" / "GC" / "GC_USD-5m.feather").exists())
            self.assertTrue((root / "clean" / "GC" / "clean_quality.json").exists())
            self.assertFalse((root / "clean" / "XAU").exists())
            self.assertFalse((root / "clean" / "GC" / "XAU_USD-1m.feather").exists())

    def test_public_family_strategy_source_is_materially_distinct(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}
        opening_breakout = module.strategy_source(by_key["opening_drive_breakout"], symbol="NQ", timeframe="1m")
        vwap_persist = module.strategy_source(by_key["vwap_reclaim_persistence"], symbol="NQ", timeframe="1m")
        supertrend = module.strategy_source(by_key["supertrend_adx_displacement"], symbol="NQ", timeframe="1m")
        pullback = module.strategy_source(by_key["supertrend_adx_pullback_reclaim"], symbol="NQ", timeframe="1m")
        turtle_soup = module.strategy_source(
            by_key["supertrend_adx_turtle_soup_sweep_reversal"], symbol="NQ", timeframe="1m"
        )
        sweep = module.strategy_source(by_key["supertrend_adx_liquidity_sweep_reclaim"], symbol="NQ", timeframe="1m")
        ote_desc = module.strategy_source(by_key["supertrend_adx_pullback_ote_fvg_ob"], symbol="NQ", timeframe="1m")
        exit_desc = module.strategy_source(by_key["supertrend_adx_pullback_exit_persistence"], symbol="NQ", timeframe="1m")
        high_conv = module.strategy_source(by_key["supertrend_adx_pullback_exit_persistence_high_conviction"], symbol="NQ", timeframe="1m")
        opening_drive = module.strategy_source(by_key["supertrend_adx_pullback_exit_persistence_opening_drive"], symbol="NQ", timeframe="1m")
        opening_drive_soft = module.strategy_source(
            by_key["supertrend_adx_pullback_exit_persistence_opening_drive_soft"],
            symbol="NQ",
            timeframe="1m",
        )
        excursion_cap = module.strategy_source(
            by_key["supertrend_adx_pullback_exit_persistence_vwap_excursion_cap"],
            symbol="NQ",
            timeframe="1m",
        )
        mass_vortex = module.strategy_source(
            by_key["mass_index_vortex_trend_continuation"], symbol="NQ", timeframe="1m"
        )
        aroon_cci = module.strategy_source(
            by_key["aroon_cci_trend_continuation"], symbol="NQ", timeframe="1m"
        )
        aroon_cci_cadence = module.strategy_source(
            by_key["aroon_cci_cadence_lift_symbol_guard"], symbol="NQ", timeframe="1m"
        )
        aroon_cci_cadence_volume_retest = module.strategy_source(
            by_key["aroon_cci_cadence_lift_volume_persistence_retest"], symbol="NQ", timeframe="1m"
        )
        donchian = module.strategy_source(by_key["donchian_turtle_breakout"], symbol="NQ", timeframe="1m")
        dense_pullback = module.strategy_source(by_key["dense_trend_pullback_reclaim"], symbol="NQ", timeframe="1m")
        prior_day = module.strategy_source(by_key["prior_day_extreme_continuation"], symbol="NQ", timeframe="1m")
        prior_day_mtf_guard = module.strategy_source(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard"], symbol="NQ", timeframe="1m"
        )
        prior_day_mtf_guard_exit = module.strategy_source(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard_exit_persistence"],
            symbol="NQ",
            timeframe="1m",
        )
        prior_day_mtf_guard_cusum_deadzone = module.strategy_source(
            by_key["prior_day_extreme_continuation_mtf_resonance_guard_cusum_deadzone_gate"],
            symbol="NQ",
            timeframe="1m",
        )
        opening_drive_twoleg_exit = module.strategy_source(
            by_key["opening_drive_twoleg_continuation_exit_persistence"],
            symbol="NQ",
            timeframe="1m",
        )
        prior_day_sweep = module.strategy_source(by_key["prior_day_liquidity_sweep_reversal"], symbol="NQ", timeframe="1m")
        impulse = module.strategy_source(by_key["impulse_follow"], symbol="NQ", timeframe="1m")
        wpr = module.strategy_source(by_key["wpr_extreme_mean_reclaim"], symbol="NQ", timeframe="1m")
        nr7 = module.strategy_source(by_key["nr7_range_expansion"], symbol="NQ", timeframe="1m")
        connors = module.strategy_source(by_key["connors_rsi2_rebound"], symbol="NQ", timeframe="1m")
        ultimate_ict = module.strategy_source(
            by_key["ultimate_ict_zone_volume_spike_reclaim"], symbol="NQ", timeframe="1m"
        )
        ultimate_ict_session_open = module.strategy_source(
            by_key["ultimate_ict_zone_volume_spike_session_open_bias_cap"], symbol="NQ", timeframe="1m"
        )
        ultimate_ict_vwap_hold = module.strategy_source(
            by_key["ultimate_ict_zone_volume_spike_vwap_hold_persistence"], symbol="NQ", timeframe="1m"
        )
        ultimate_ict_compound = module.strategy_source(
            by_key["ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence"],
            symbol="NQ",
            timeframe="1m",
        )
        wpr_no_be_session_bias = module.strategy_source(
            by_key["wpr_fractal_no_be_session_bias_cap"], symbol="ES", timeframe="1m"
        )
        wpr_no_be_higher_frame_slope = module.strategy_source(
            by_key["wpr_fractal_no_be_higher_frame_slope_confirm"], symbol="ES", timeframe="1m"
        )
        ote_liq = module.strategy_source(by_key["ote_liquidity_sweep_fvg_ob_reclaim"], symbol="NQ", timeframe="1m")
        ote_session_bias = module.strategy_source(
            by_key["ote_fvg_order_block_reclaim_session_directional_bias"], symbol="ES", timeframe="1m"
        )
        h4_midnight = module.strategy_source(by_key["h4_midnight_macd_rsi_pullback"], symbol="NQ", timeframe="1m")
        purge = module.strategy_source(by_key["liquidity_purge_rejection"], symbol="NQ", timeframe="1m")
        divergence = module.strategy_source(by_key["momentum_divergence_reclaim"], symbol="NQ", timeframe="1m")
        fractal_divergence = module.strategy_source(
            by_key["fractal_liquidity_macd_rsi_divergence_reclaim"], symbol="NQ", timeframe="1m"
        )
        midnight_liquidity_macd_divergence = module.strategy_source(
            by_key["midnight_open_liquidity_sweep_macd_divergence_reclaim"], symbol="ES", timeframe="1m"
        )
        silver_bullet = module.strategy_source(by_key["silver_bullet_rsi_sniper"], symbol="NQ", timeframe="1m")

        self.assertIn("opening_drive_breakout", opening_breakout)
        self.assertIn("opening_window", opening_breakout)
        self.assertIn("opening_breakout", opening_breakout)
        self.assertIn("opening_drive_context", opening_breakout)
        self.assertIn('dataframe["close"] > dataframe["prior_high80"]', opening_breakout)
        self.assertIn('dataframe["close"] > dataframe["session_vwap"]', opening_breakout)
        self.assertIn("supertrend_trend", supertrend)
        self.assertIn("vwap_reclaim_persistence", vwap_persist)
        self.assertIn("session_vwap", vwap_persist)
        self.assertIn("vwap_excursion_long", vwap_persist)
        self.assertIn("reclaim_long", vwap_persist)
        self.assertIn("long_transition | short_transition", vwap_persist)
        self.assertIn("adx14", supertrend)
        self.assertIn("sweep_low40", supertrend)
        self.assertIn("supertrend_adx_displacement", supertrend)
        self.assertIn("supertrend_adx_pullback_reclaim", pullback)
        self.assertIn('dataframe["close"] > dataframe["ema21"]', pullback)
        self.assertIn("supertrend_adx_turtle_soup_sweep_reversal", turtle_soup)
        self.assertIn("TurtleSoupSweepReversal", turtle_soup)
        self.assertIn("killzone_window", turtle_soup)
        self.assertIn("liquidity_sweep", turtle_soup)
        self.assertIn("close_reclaim", turtle_soup)
        self.assertIn("momentum_reversal", turtle_soup)
        self.assertIn("supertrend_adx_liquidity_sweep_reclaim", sweep)
        self.assertIn("sweep_close_reclaim", sweep)
        self.assertIn("supertrend_adx_pullback_ote_fvg_ob", ote_desc)
        self.assertIn("ote_long_62", ote_desc)
        self.assertIn("bull_ob_low", ote_desc)
        self.assertIn("ict_zone", ote_desc)
        self.assertIn("supertrend_adx_pullback_exit_persistence", exit_desc)
        self.assertIn("late_failure", exit_desc)
        self.assertIn('dataframe["close"] < dataframe["session_vwap"]', exit_desc)
        self.assertIn("supertrend_adx_pullback_exit_persistence_high_conviction", high_conv)
        self.assertIn("breakout_bias", high_conv)
        self.assertIn('dataframe["ema55"] > dataframe["ema89"]', high_conv)
        self.assertIn("supertrend_adx_pullback_exit_persistence_opening_drive", opening_drive)
        self.assertIn("minute_of_day_ny", opening_drive)
        self.assertIn("opening_window", opening_drive)
        self.assertIn("supertrend_adx_pullback_exit_persistence_opening_drive_soft", opening_drive_soft)
        self.assertIn("opening_drive_context", opening_drive_soft)
        self.assertIn("breakout_bias", opening_drive_soft)
        self.assertIn("(opening_drive_context | breakout_bias)", opening_drive_soft)
        self.assertIn("supertrend_adx_pullback_exit_persistence_vwap_excursion_cap", excursion_cap)
        self.assertIn("vwap_excursion_ok", excursion_cap)
        self.assertIn("reclaim_discount_ok", excursion_cap)
        self.assertIn("exit_persistence_guard = True", excursion_cap)
        self.assertIn("mass_index_vortex_trend_continuation", mass_vortex)
        self.assertIn("mass_index25", mass_vortex)
        self.assertIn("vortex_plus14", mass_vortex)
        self.assertIn("vortex_minus14", mass_vortex)
        self.assertIn("economic_slope", mass_vortex)
        self.assertIn("ema21_slope_bps_12", mass_vortex)
        self.assertIn("ema55_slope_bps_48", mass_vortex)
        self.assertIn("breakout_hold", mass_vortex)
        self.assertIn("aroon_cci_trend_continuation", aroon_cci)
        self.assertIn("aroon_up25", aroon_cci)
        self.assertIn("aroon_down25", aroon_cci)
        self.assertIn("cci20", aroon_cci)
        self.assertIn("directional_persistence", aroon_cci)
        self.assertIn("cci_impulse", aroon_cci)
        self.assertIn("economic_slope", aroon_cci)
        self.assertIn("continuation_hold", aroon_cci)
        self.assertIn("aroon_cci_cadence_lift_symbol_guard", aroon_cci_cadence)
        self.assertIn('metadata.get("pair") in ("NQ/USD", "ES/USD")', aroon_cci_cadence)
        self.assertIn("cci_reacceleration", aroon_cci_cadence)
        self.assertIn("cci_zero_reclaim", aroon_cci_cadence)
        self.assertIn("cadence_lift_hold", aroon_cci_cadence)
        self.assertIn("economic_slope", aroon_cci_cadence)
        self.assertIn("aroon_cci_cadence_lift_volume_persistence_retest", aroon_cci_cadence_volume_retest)
        self.assertIn('metadata.get("pair") in ("NQ/USD", "ES/USD")', aroon_cci_cadence_volume_retest)
        self.assertIn("volume_persistence_retest", aroon_cci_cadence_volume_retest)
        self.assertIn("retest_volume_expansion", aroon_cci_cadence_volume_retest)
        self.assertIn("retest_vwap_acceptance", aroon_cci_cadence_volume_retest)
        self.assertIn('metadata.get("pair") != "NQ/USD"', donchian)
        self.assertIn("prior_high80", donchian)
        self.assertIn("donchian_turtle_breakout", donchian)
        self.assertIn("dense_trend_pullback_reclaim", dense_pullback)
        self.assertIn('dataframe["ema96"] > dataframe["ema390"]', dense_pullback)
        self.assertIn('dataframe["close"].shift(5) < dataframe["ema32"].shift(5)', dense_pullback)
        self.assertIn('dataframe["close"] > dataframe["session_vwap"]', dense_pullback)
        self.assertIn("prior_day_extreme_continuation", prior_day)
        self.assertIn("prior_day_high", prior_day)
        self.assertIn("prior_day_range", prior_day)
        self.assertIn("persist = crossed & crossed.shift(1) & crossed.shift(2)", prior_day)
        self.assertIn('dataframe["close"] > dataframe["session_vwap"]', prior_day)
        self.assertIn(
            "TrendExpansion -> PriorDayExtremeContinuation -> "
            "PriorDayExtremeContinuationMtfResonanceGuard -> "
            "tomac_idxfut_clean_prior_day_extreme_continuation_mtf_resonance_guard_1m_v1",
            prior_day_mtf_guard,
        )
        self.assertIn("prior_day_extreme_continuation_mtf_resonance_guard", prior_day_mtf_guard)
        self.assertIn("mtf_fast_alignment", prior_day_mtf_guard)
        self.assertIn("mtf_slow_alignment", prior_day_mtf_guard)
        self.assertIn("mtf_resonance_guard", prior_day_mtf_guard)
        self.assertIn(
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> "
            "ExitPersistence -> tomac_idxfut_clean_prior_day_extreme_continuation_mtf_resonance_guard_exit_persistence_1m_v1",
            prior_day_mtf_guard_exit,
        )
        self.assertIn(
            "prior_day_extreme_continuation_mtf_resonance_guard_exit_persistence",
            prior_day_mtf_guard_exit,
        )
        self.assertIn("exit_persistence_window", prior_day_mtf_guard_exit)
        self.assertIn("persistence_bias", prior_day_mtf_guard_exit)
        self.assertIn("exit_persistence_guard = True", prior_day_mtf_guard_exit)
        self.assertIn(
            "TrendExpansion -> PriorDayExtremeContinuation -> PriorDayExtremeContinuationMtfResonanceGuard -> "
            "CusumDeadzoneGate -> tomac_idxfut_clean_prior_day_extreme_continuation_mtf_resonance_guard_cusum_deadzone_gate_1m_v1",
            prior_day_mtf_guard_cusum_deadzone,
        )
        self.assertIn(
            "prior_day_extreme_continuation_mtf_resonance_guard_cusum_deadzone_gate",
            prior_day_mtf_guard_cusum_deadzone,
        )
        self.assertIn("cusum_positive_event", prior_day_mtf_guard_cusum_deadzone)
        self.assertIn("deadzone_excursion", prior_day_mtf_guard_cusum_deadzone)
        self.assertIn("rearm_breakout", prior_day_mtf_guard_cusum_deadzone)
        self.assertIn("cooldown_bars_remaining", prior_day_mtf_guard_cusum_deadzone)
        self.assertIn(
            "TrendExpansion -> OpeningDriveExpansion -> OpeningDriveTwoLegContinuation -> ExitPersistence -> tomac_idxfut_clean_opening_drive_twoleg_continuation_exit_persistence_1m_v1",
            opening_drive_twoleg_exit,
        )
        self.assertIn("opening_drive_twoleg_continuation_exit_persistence", opening_drive_twoleg_exit)
        self.assertIn("second_leg_reclaim", opening_drive_twoleg_exit)
        self.assertIn("exit_persistence_guard = True", opening_drive_twoleg_exit)
        self.assertIn('dataframe["close"] > dataframe["session_vwap"]', opening_drive_twoleg_exit)
        self.assertIn("prior_day_liquidity_sweep_reversal", prior_day_sweep)
        self.assertIn("sweep_depth", prior_day_sweep)
        self.assertIn('dataframe["low"] < dataframe["prior_day_low"]', prior_day_sweep)
        self.assertIn('dataframe["close"] > dataframe["prior_day_low"]', prior_day_sweep)
        self.assertIn('dataframe["minute_of_day_ny"].between(9 * 60 + 35, 14 * 60 + 30)', prior_day_sweep)
        self.assertIn("down_extension", prior_day_sweep)
        self.assertIn("impulse_follow", impulse)
        self.assertIn("bar_range_atr", impulse)
        self.assertIn('dataframe["body_atr"].between(0.45, 3.2)', impulse)
        self.assertIn('dataframe["close"] > dataframe["close"].shift(1)', impulse)
        self.assertIn("wpr_extreme_mean_reclaim", wpr)
        self.assertIn("wpr14", wpr)
        self.assertIn('dataframe["wpr14"].lt(-80)', wpr)
        self.assertIn('dataframe["close"] > dataframe["range_low40"]', wpr)
        self.assertIn("nr7_range", nr7)
        self.assertIn("prior_nr7", nr7)
        self.assertIn("connors_rsi", connors)
        self.assertIn("rsi2", connors)
        self.assertIn("ultimate_ict_zone_volume_spike_reclaim", ultimate_ict)
        self.assertIn("KillzoneLiquiditySweep", ultimate_ict)
        self.assertIn("extreme_wpr", ultimate_ict)
        self.assertIn("ict_zone", ultimate_ict)
        self.assertIn("volume_spike", ultimate_ict)
        self.assertIn("ultimate_ict_zone_volume_spike_session_open_bias_cap", ultimate_ict_session_open)
        self.assertIn("SessionOpenBiasCap", ultimate_ict_session_open)
        self.assertIn("session_open_bias", ultimate_ict_session_open)
        self.assertIn("vwap_reclaim", ultimate_ict_session_open)
        self.assertIn("macd_bias", ultimate_ict_session_open)
        self.assertIn("ultimate_ict_zone_volume_spike_vwap_hold_persistence", ultimate_ict_vwap_hold)
        self.assertIn("VwapHoldPersistence", ultimate_ict_vwap_hold)
        self.assertIn("vwap_reclaim", ultimate_ict_vwap_hold)
        self.assertIn("vwap_hold", ultimate_ict_vwap_hold)
        self.assertIn("persistence_bias", ultimate_ict_vwap_hold)
        self.assertIn(
            "ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence",
            ultimate_ict_compound,
        )
        self.assertIn("SessionOpenBiasCap -> VwapHoldPersistence", ultimate_ict_compound)
        self.assertIn("session_open_bias", ultimate_ict_compound)
        self.assertIn("vwap_reclaim", ultimate_ict_compound)
        self.assertIn("vwap_hold", ultimate_ict_compound)
        self.assertIn("persistence_bias", ultimate_ict_compound)
        self.assertIn("wpr_fractal_no_be_session_bias_cap", wpr_no_be_session_bias)
        self.assertIn("PdhPdlFractalLiquiditySweep", wpr_no_be_session_bias)
        self.assertIn("SessionBiasCap", wpr_no_be_session_bias)
        self.assertIn("session_bias_cap_window", wpr_no_be_session_bias)
        self.assertIn("session_open_bias", wpr_no_be_session_bias)
        self.assertIn("vwap_hold", wpr_no_be_session_bias)
        self.assertIn("wpr_fractal_no_be_higher_frame_slope_confirm", wpr_no_be_higher_frame_slope)
        self.assertIn("HigherFrameSlopeConfirm", wpr_no_be_higher_frame_slope)
        self.assertIn("higher_frame_slope_confirm", wpr_no_be_higher_frame_slope)
        self.assertIn("ema55_slope_atr", wpr_no_be_higher_frame_slope)
        self.assertIn("ema144_slope_atr", wpr_no_be_higher_frame_slope)
        self.assertIn("ote_liquidity_sweep_fvg_ob_reclaim", ote_liq)
        self.assertIn("OteLiquiditySweepReclaim", ote_liq)
        self.assertIn("liquidity_sweep", ote_liq)
        self.assertIn("near_fvg", ote_liq)
        self.assertIn("near_ob", ote_liq)
        self.assertIn("ote_fvg_order_block_reclaim_session_directional_bias", ote_session_bias)
        self.assertIn("LiquiditySweepIctRetracement", ote_session_bias)
        self.assertIn("SessionDirectionalBias", ote_session_bias)
        self.assertIn("bull_session_bias", ote_session_bias)
        self.assertIn("bear_session_bias", ote_session_bias)
        self.assertIn("mtf_bias_long", ote_session_bias)
        self.assertIn("mtf_bias_short", ote_session_bias)
        self.assertIn("liquidity_sweep_short", ote_session_bias)
        self.assertIn("h4_midnight_macd_rsi_pullback", h4_midnight)
        self.assertIn("h4_structure_bias", h4_midnight)
        self.assertIn("midnight_open", h4_midnight)
        self.assertIn("macd_reclaim", h4_midnight)
        self.assertIn("liquidity_purge_rejection", purge)
        self.assertIn("killzone_window", purge)
        self.assertIn("purge", purge)
        self.assertIn("macd_hist", purge)
        self.assertIn("momentum_divergence_reclaim", divergence)
        self.assertIn("momentum_divergence", divergence)
        self.assertIn('dataframe["macd_line"] > dataframe["macd_line"].shift(5)', divergence)
        self.assertIn("fractal_liquidity_macd_rsi_divergence_reclaim", fractal_divergence)
        self.assertIn("FractalLiquiditySweep", fractal_divergence)
        self.assertIn("midnight_open", fractal_divergence)
        self.assertIn("macd_divergence", fractal_divergence)
        self.assertIn("structure_bias_long", fractal_divergence)
        self.assertIn('dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)', fractal_divergence)
        self.assertIn('dataframe["minute_of_day_ny"].between(13 * 60 + 30, 15 * 60 + 50)', fractal_divergence)
        self.assertIn('dataframe["rsi14"].gt(30)', fractal_divergence)
        self.assertIn('dataframe["rsi14"].lt(70)', fractal_divergence)
        self.assertIn(
            "midnight_open_liquidity_sweep_macd_divergence_reclaim",
            midnight_liquidity_macd_divergence,
        )
        self.assertIn("MidnightOpenDiscountPremiumBias", midnight_liquidity_macd_divergence)
        self.assertIn("midnight_open", midnight_liquidity_macd_divergence)
        self.assertIn("liq_low20", midnight_liquidity_macd_divergence)
        self.assertIn("liq_high20", midnight_liquidity_macd_divergence)
        self.assertIn("macd_line", midnight_liquidity_macd_divergence)
        self.assertIn('dataframe["minute_of_day_ny"].between(2 * 60, 5 * 60)', midnight_liquidity_macd_divergence)
        self.assertIn('dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)', midnight_liquidity_macd_divergence)
        self.assertIn('dataframe["minute_of_day_ny"].between(13 * 60 + 30, 16 * 60)', midnight_liquidity_macd_divergence)
        self.assertIn("silver_bullet_rsi_sniper", silver_bullet)
        self.assertIn("silver_bullet_window", silver_bullet)
        self.assertIn('dataframe["minute_of_day_ny"].between(10 * 60, 11 * 60)', silver_bullet)
        self.assertIn('dataframe["rsi14"].between(22, 40)', silver_bullet)
        self.assertNotIn(
            "shift(-",
            opening_breakout
            + vwap_persist
            + supertrend
            + pullback
            + turtle_soup
            + sweep
            + ote_desc
            + exit_desc
            + high_conv
            + opening_drive
            + opening_drive_soft
            + excursion_cap
            + donchian
            + dense_pullback
            + prior_day
            + prior_day_mtf_guard
            + prior_day_mtf_guard_exit
            + prior_day_sweep
            + impulse
            + wpr
            + nr7
            + connors
            + ultimate_ict
            + ultimate_ict_session_open
            + ultimate_ict_vwap_hold
            + ultimate_ict_compound
            + wpr_no_be_session_bias
            + ote_liq
            + h4_midnight
            + purge
            + divergence
            + fractal_divergence
            + silver_bullet,
        )

    def test_strategy_source_uses_symbol_specific_product_provenance_label(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}
        fx_source = module.strategy_source(by_key["connors_rsi2_rebound"], symbol="6E", timeframe="1m")
        index_source = module.strategy_source(by_key["nr7_range_expansion"], symbol="NQ", timeframe="1m")
        opening_source = module.strategy_source(by_key["opening_drive_breakout"], symbol="YM", timeframe="1m")

        self.assertIn("product: fx_futures", fx_source)
        self.assertIn("product: equity_index", index_source)
        self.assertIn("product: equity_index", opening_source)

    def test_strategy_source_produces_session_open_when_child_branches_reference_it(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}
        source = module.strategy_source(
            by_key["ultimate_ict_zone_volume_spike_exit_persistence"], symbol="NQ", timeframe="1m"
        )

        self.assertIn('dataframe["close"] > dataframe["session_open"]', source)
        self.assertIn('dataframe["session_open"] =', source)

    def test_timeframe_class_suffix_uses_exact_ladder_mapping(self) -> None:
        module = self.load_module()

        self.assertEqual(module.timeframe_class_suffix("1m"), "OneMin")
        self.assertEqual(module.timeframe_class_suffix("5m"), "FiveMin")
        self.assertEqual(module.timeframe_class_suffix("15m"), "FifteenMin")
        self.assertEqual(module.timeframe_class_suffix("30m"), "ThirtyMin")
        self.assertEqual(module.timeframe_class_suffix("1h"), "OneHour")
        self.assertEqual(module.timeframe_class_suffix("4h"), "FourHour")
        self.assertEqual(module.timeframe_class_suffix("1d"), "OneDay")

    def test_aq_workspace_timerange_matches_clean_window(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            workspace = module.prepare_aq_workspace(
                Path(tmp),
                symbols=["ES"],
                timeframe="5m",
                start="2025-03-01",
                end="2025-03-10",
            )
            config = json.loads((workspace / "config.tomac.json").read_text(encoding="utf-8"))
            copied_runner = (workspace / "run_tomac.py").read_text(encoding="utf-8")

        self.assertEqual(config["timerange"], "20250301-20250310")
        self.assertEqual(config["trading_mode"], "futures")
        self.assertEqual(config["margin_mode"], "isolated")
        self.assertEqual(config["dataformat_ohlcv"], "feather")

        self.assertIn("def _synthetic_leverage_tiers", copied_runner)
        self.assertIn("exchange._leverage_tiers[pair]", copied_runner)

    def test_stage_aq_inputs_uses_futures_datadir(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean_dir = root / "clean/ES"
            clean_dir.mkdir(parents=True)
            pd.DataFrame(
                {
                    "date": pd.date_range("2025-03-17T13:30:00Z", periods=3, freq="5min"),
                    "open": [100.0, 101.0, 102.0],
                    "high": [101.0, 102.0, 103.0],
                    "low": [99.0, 100.0, 101.0],
                    "close": [100.5, 101.5, 102.5],
                    "volume": [10.0, 11.0, 12.0],
                }
            ).to_feather(clean_dir / "ES_USD-5m.feather")

            staged = module.stage_aq_inputs(
                root,
                symbols=["ES"],
                timeframe="5m",
                start="2025-03-17",
                end="2025-03-18",
            )

            staged_path = Path(staged["data"][0])
            self.assertEqual(
                staged_path,
                root / "aq_workspaces/5m/user_data/data/futures/ES_USD-5m-futures.feather",
            )
            self.assertTrue(staged_path.exists())
            self.assertEqual(
                staged["strategy_specs"][0]["branch_path"],
                "TrendExpansion -> SessionLiquidity -> OpeningDriveRvolVwapContinuation -> "
                "tomac_idxfut_clean_opening_drive_rvol_vwap_continuation_5m_v1",
            )

    def test_stage_aq_inputs_uses_gc_data_filename_for_legacy_xau_request(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean_dir = root / "clean/GC"
            clean_dir.mkdir(parents=True)
            pd.DataFrame(
                {
                    "date": pd.date_range("2025-03-17T13:30:00Z", periods=3, freq="15min"),
                    "open": [2300.0, 2301.0, 2302.0],
                    "high": [2301.0, 2302.0, 2303.0],
                    "low": [2299.0, 2300.0, 2301.0],
                    "close": [2300.5, 2301.5, 2302.5],
                    "volume": [10.0, 11.0, 12.0],
                }
            ).to_feather(clean_dir / "GC_USD-15m.feather")

            staged = module.stage_aq_inputs(
                root,
                symbols=["XAU"],
                timeframe="15m",
                start="2025-03-17",
                end="2025-03-18",
            )

            staged_path = Path(staged["data"][0])
            self.assertEqual(
                staged_path,
                root / "aq_workspaces/15m/user_data/data/futures/GC_USD-15m-futures.feather",
            )
            self.assertTrue(staged_path.exists())
            self.assertFalse(
                (root / "aq_workspaces/15m/user_data/data/futures/XAU_USD-15m-futures.feather").exists()
            )
            self.assertEqual(staged["aq_dense_fill"][0]["symbol"], "GC")
            self.assertTrue(staged["aq_dense_fill"][0]["source_clean_feather"].endswith("GC_USD-15m.feather"))
            self.assertTrue(staged["aq_dense_fill"][0]["aq_feather"].endswith("GC_USD-15m-futures.feather"))

    def test_stage_aq_inputs_materializes_mbs_macro_rate_sidecar_for_mbs_family(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean_dir = root / "clean/ES"
            clean_dir.mkdir(parents=True)
            pd.DataFrame(
                {
                    "date": pd.date_range("2025-03-17T13:30:00Z", periods=3, freq="4h"),
                    "open": [100.0, 101.0, 102.0],
                    "high": [101.0, 102.0, 103.0],
                    "low": [99.0, 100.0, 101.0],
                    "close": [100.5, 101.5, 102.5],
                    "volume": [10.0, 11.0, 12.0],
                }
            ).to_feather(clean_dir / "ES_USD-4h.feather")
            source_dir = root / "source_evidence"
            source_dir.mkdir(parents=True)
            (source_dir / "fred_mortgage30us.csv").write_text(
                "DATE,MORTGAGE30US\n2025-03-14,6.65\n2025-03-21,6.71\n",
                encoding="utf-8",
            )
            (source_dir / "fred_dgs10.csv").write_text(
                "DATE,DGS10\n2025-03-14,4.31\n2025-03-17,4.34\n",
                encoding="utf-8",
            )

            staged = module.stage_aq_inputs(
                root,
                symbols=["ES"],
                timeframe="4h",
                start="2025-03-17",
                end="2025-03-18",
                families=["mbs_convexity_duration_hedge_risk_transfer_filter"],
            )

            staged_frame = pd.read_feather(staged["data"][0])
            self.assertIn("mortgage_30y_rate", staged_frame.columns)
            self.assertIn("treasury_10y_yield", staged_frame.columns)
            self.assertEqual(staged_frame["mortgage_30y_rate"].dropna().unique().tolist(), [6.65])
            self.assertEqual(staged_frame["treasury_10y_yield"].dropna().unique().tolist(), [4.34])
            self.assertEqual(staged["macro_sidecar"]["status"], "materialized")
            self.assertFalse(staged["macro_sidecar"]["future_lookahead"])

    def test_mbs_macro_rate_sidecar_accepts_observation_date_header(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "source_evidence"
            source_dir.mkdir(parents=True)
            (source_dir / "fred_mortgage30us.csv").write_text(
                "observation_date,MORTGAGE30US\n2025-03-14,6.65\n2025-03-21,6.71\n",
                encoding="utf-8",
            )
            (source_dir / "fred_dgs10.csv").write_text(
                "observation_date,DGS10\n2025-03-14,4.31\n2025-03-17,4.34\n",
                encoding="utf-8",
            )
            frame = pd.DataFrame(
                {
                    "date": pd.date_range("2025-03-17T13:30:00Z", periods=2, freq="4h"),
                    "open": [100.0, 101.0],
                    "high": [101.0, 102.0],
                    "low": [99.0, 100.0],
                    "close": [100.5, 101.5],
                    "volume": [10.0, 11.0],
                }
            )

            merged, stats = module.merge_mbs_macro_rate_sidecar(frame, root)

            self.assertEqual(stats["status"], "materialized")
            self.assertEqual(merged["mortgage_30y_rate"].dropna().unique().tolist(), [6.65])
            self.assertEqual(merged["treasury_10y_yield"].dropna().unique().tolist(), [4.34])
            self.assertFalse(stats["future_lookahead"])

    def test_jolts_macro_sidecar_materializes_only_after_release_effective_timestamp(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "source_evidence"
            source_dir.mkdir(parents=True)
            (source_dir / "fred_jolts_unemploy.csv").write_text(
                "DATE,JTSJOL,JTSQUR,UNEMPLOY,jolts_release_effective\n"
                "2025-03-01,7192,2.1,7083,2025-04-01T14:00:00Z\n"
                "2025-04-01,7391,2.0,7199,2025-04-29T14:00:00Z\n",
                encoding="utf-8",
            )
            frame = pd.DataFrame(
                {
                    "date": pd.to_datetime(
                        [
                            "2025-04-01T13:59:00Z",
                            "2025-04-01T14:00:00Z",
                            "2025-04-29T13:59:00Z",
                            "2025-04-29T14:00:00Z",
                        ],
                        utc=True,
                    ),
                    "open": [100.0, 101.0, 102.0, 103.0],
                    "high": [101.0, 102.0, 103.0, 104.0],
                    "low": [99.0, 100.0, 101.0, 102.0],
                    "close": [100.5, 101.5, 102.5, 103.5],
                    "volume": [10.0, 11.0, 12.0, 13.0],
                }
            )

            merged, stats = module.merge_jolts_macro_sidecar(frame, root)

            self.assertEqual(stats["status"], "materialized")
            self.assertFalse(stats["future_lookahead"])
            self.assertEqual(stats["merge_method"], "backward_asof_release_effective_timestamp")
            self.assertEqual(
                stats["provenance_columns"],
                ["jolts_source_observation_date", "jolts_release_effective_timestamp"],
            )
            self.assertEqual(
                merged["jolts_release_effective"].tolist(),
                [False, True, True, True],
            )
            self.assertIn("jolts_source_observation_date", merged.columns)
            self.assertIn("jolts_release_effective_timestamp", merged.columns)
            self.assertTrue(pd.isna(merged.loc[0, "jolts_source_observation_date"]))
            self.assertEqual(
                merged.loc[1, "jolts_source_observation_date"].isoformat(),
                "2025-03-01T00:00:00+00:00",
            )
            self.assertEqual(
                merged.loc[3, "jolts_release_effective_timestamp"].isoformat(),
                "2025-04-29T14:00:00+00:00",
            )
            self.assertTrue(pd.isna(merged.loc[0, "job_openings_to_unemployed_proxy"]))
            self.assertAlmostEqual(
                merged.loc[1, "job_openings_to_unemployed_proxy"],
                7192 / 7083,
            )
            self.assertAlmostEqual(
                merged.loc[2, "job_openings_to_unemployed_proxy"],
                7192 / 7083,
            )
            self.assertAlmostEqual(
                merged.loc[3, "job_openings_to_unemployed_proxy"],
                7391 / 7199,
            )
            self.assertTrue(pd.isna(merged.loc[0, "jolts_quits_rate_proxy"]))
            self.assertEqual(merged["jolts_quits_rate_proxy"].iloc[1:].tolist(), [2.1, 2.1, 2.0])

    def test_jolts_macro_sidecar_requires_explicit_release_effective_timestamp(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "source_evidence"
            source_dir.mkdir(parents=True)
            (source_dir / "fred_jolts_unemploy.csv").write_text(
                "observation_date,JTSJOL,JTSQUR,UNEMPLOY\n"
                "2025-03-01,7192,2.1,7083\n",
                encoding="utf-8",
            )
            frame = pd.DataFrame(
                {
                    "date": pd.to_datetime(["2025-04-01T14:00:00Z"], utc=True),
                    "open": [100.0],
                    "high": [101.0],
                    "low": [99.0],
                    "close": [100.5],
                    "volume": [10.0],
                }
            )

            merged, stats = module.merge_jolts_macro_sidecar(frame, root)

            self.assertEqual(stats["status"], "missing_required_columns")
            self.assertEqual(stats["missing_columns"], ["jolts_release_effective"])
            self.assertFalse(stats["future_lookahead"])
            self.assertNotIn("job_openings_to_unemployed_proxy", merged.columns)
            self.assertNotIn("jolts_release_effective", merged.columns)

    def test_stage_aq_inputs_materializes_jolts_macro_sidecar_for_jolts_family(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean_dir = root / "clean/NQ"
            clean_dir.mkdir(parents=True)
            pd.DataFrame(
                {
                    "date": pd.to_datetime(
                        [
                            "2025-04-01T13:59:00Z",
                            "2025-04-01T14:00:00Z",
                            "2025-04-01T14:01:00Z",
                        ],
                        utc=True,
                    ),
                    "open": [100.0, 101.0, 102.0],
                    "high": [101.0, 102.0, 103.0],
                    "low": [99.0, 100.0, 101.0],
                    "close": [100.5, 101.5, 102.5],
                    "volume": [10.0, 11.0, 12.0],
                }
            ).to_feather(clean_dir / "NQ_USD-1m.feather")
            source_dir = root / "source_evidence"
            source_dir.mkdir(parents=True)
            (source_dir / "fred_jolts_unemploy.csv").write_text(
                "DATE,JTSJOL,JTSQUR,UNEMPLOY,jolts_release_effective\n"
                "2025-03-01,7192,2.1,7083,2025-04-01T14:00:00Z\n",
                encoding="utf-8",
            )

            staged = module.stage_aq_inputs(
                root,
                symbols=["NQ"],
                timeframe="1m",
                start="2025-04-01",
                end="2025-04-01",
                families=["jolts_labor_tightness_regime_filter"],
            )

            staged_frame = pd.read_feather(staged["data"][0])
            self.assertIn("job_openings_to_unemployed_proxy", staged_frame.columns)
            self.assertIn("jolts_quits_rate_proxy", staged_frame.columns)
            self.assertIn("jolts_release_effective", staged_frame.columns)
            self.assertIn("jolts_source_observation_date", staged_frame.columns)
            self.assertIn("jolts_release_effective_timestamp", staged_frame.columns)
            self.assertEqual(staged_frame["jolts_release_effective"].tolist(), [False, True, True])
            self.assertTrue(pd.isna(staged_frame.loc[0, "job_openings_to_unemployed_proxy"]))
            self.assertEqual(staged["macro_sidecar"]["status"], "materialized")
            self.assertEqual(
                staged["macro_sidecar"]["materialized_columns"],
                ["job_openings_to_unemployed_proxy", "jolts_quits_rate_proxy", "jolts_release_effective"],
            )
            self.assertEqual(
                staged["macro_sidecar"]["provenance_columns"],
                ["jolts_source_observation_date", "jolts_release_effective_timestamp"],
            )

    def test_score_rows_keeps_symbol_specific_regime_branch_and_cost_gate(self) -> None:
        module = self.load_module()

        specs = module.generated_strategy_specs(["ES"], "5m")
        stdout = "\n".join(
            [
                "---",
                "strategy:         TomacESOpeningDriveRvolVwapContinuationFiveMinCleanV1",
                "pairs:            ES/USD,YM/USD,NQ/USD",
                "sharpe:           1.8000",
                "sortino:          2.1000",
                "calmar:           1.2000",
                "total_profit_pct: 200.0000",
                "trade_count:      1500",
                "win_rate_pct:     55.0000",
                "profit_factor:    1.4500",
                "per_pair:",
                "  ES/USD: sharpe=1.80 trades=1500 profit_pct=200.00 dd_pct=-4.00 wr=55.0 pf=1.45",
                "  YM/USD: sharpe=9.99 trades=999 profit_pct=999.00 dd_pct=-1.00 wr=99.0 pf=9.99",
            ]
        )

        rows = module.score_rows(stdout, specs)
        per_pair = [row for row in rows if row["scope"] == "per_pair"]

        self.assertEqual(len(per_pair), 1)
        self.assertEqual(per_pair[0]["symbol"], "ES")
        self.assertTrue(per_pair[0]["gate1_survivor"])
        self.assertEqual(
            per_pair[0]["branch_path"],
            "TrendExpansion -> SessionLiquidity -> OpeningDriveRvolVwapContinuation -> "
            "tomac_idxfut_clean_opening_drive_rvol_vwap_continuation_5m_v1",
        )
        self.assertTrue(per_pair[0]["survives_instrument_cost"])
        self.assertGreater(per_pair[0]["instrument_cost_total_profit_pct"], 0.0)
        self.assertNotIn("5bps_per_side_total_profit_pct", per_pair[0])

    def test_score_rows_uses_symbol_specific_futures_cost_for_gate1(self) -> None:
        module = self.load_module()

        row = module.classify_screen_row(
            {
                "scope": "per_pair",
                "symbol": "ES",
                "pair": "ES/USD",
                "timeframe": "5m",
                "strategy_name": "SyntheticCostProbe",
                "factor_id": "synthetic_cost_probe",
                "branch_path": "TrendExpansion -> SyntheticCostProbe",
                "family": "synthetic",
                "direction": "long",
                "trade_count": 120,
                "wins": 70,
                "losses": 50,
                "days": 60,
                "total_profit_pct": 20.0,
                "representative_entry_price": 5200.0,
            }
        )

        self.assertEqual(row["cost_profile_id"], "CME_ES_IBKR_verified_20260530_v1")
        self.assertGreater(row["instrument_round_trip_cost_pct"], 0.0)
        self.assertLess(row["instrument_round_trip_cost_pct"], 0.10)
        self.assertGreater(row["instrument_cost_total_profit_pct"], 0.0)
        self.assertNotIn("5bps_per_side_total_profit_pct", row)
        self.assertTrue(row["survives_instrument_cost"])
        self.assertTrue(row["gate1_survivor"])

    def test_verified_es_nq_ym_cost_profiles_use_ibkr_fee_components(self) -> None:
        module = self.load_module()

        expected = {
            "ES": ("CME", 0.25, 12.5),
            "NQ": ("CME", 0.25, 5.0),
            "YM": ("CBOT", 1.0, 5.0),
        }
        for symbol, (exchange, tick_size, tick_value) in expected.items():
            with self.subTest(symbol=symbol):
                profile = module.futures_cost_profile(symbol)

                self.assertIsNotNone(profile)
                self.assertEqual(profile.exchange, exchange)
                self.assertEqual(profile.tick_size, tick_size)
                self.assertEqual(profile.tick_value, tick_value)
                self.assertEqual(profile.commission_per_contract_side, 0.85)
                self.assertEqual(profile.exchange_fees_per_contract_side, 1.38)
                self.assertEqual(profile.regulatory_fees_per_contract_side, 0.02)
                self.assertAlmostEqual(
                    2.0
                    * (
                        profile.commission_per_contract_side
                        + profile.exchange_fees_per_contract_side
                        + profile.regulatory_fees_per_contract_side
                    ),
                    4.50,
                )
                self.assertIn("IBKR", profile.source)

    def test_wrapper_uses_shared_verified_micro_futures_cost_profile(self) -> None:
        module = self.load_module()

        profile = module.futures_cost_profile("MNQ")

        self.assertIsNotNone(profile)
        self.assertEqual(profile.profile_id, "CME_MNQ_IBKR_verified_20260530_v1")
        self.assertEqual(profile.root_symbol, "MNQ")
        self.assertAlmostEqual(profile.all_in_per_contract_per_side, 0.62)
        self.assertTrue(profile.verified_for_promotion)

    def test_nq_realistic_contract_cost_wall_is_sub_bps_not_10bps_stress(self) -> None:
        module = self.load_module()

        profile = module.futures_cost_profile("NQ")

        self.assertIsNotNone(profile)
        self.assertAlmostEqual(profile.round_trip_fee_cash(), 4.50)
        self.assertAlmostEqual(profile.round_trip_cost_cash(), 19.50)
        self.assertLess(profile.round_trip_cost_pct(15000.0) * 100.0, 0.70)

    def test_cost_wall_buckets_distinguish_bps_false_negative_from_no_edge_churn(self) -> None:
        module = self.load_module()

        false_negative = module.classify_screen_row(
            {
                "scope": "per_pair",
                "symbol": "NQ",
                "pair": "NQ/USD",
                "timeframe": "1m",
                "strategy_name": "SyntheticBpsFalseNegative",
                "factor_id": "synthetic_bps_false_negative",
                "branch_path": "TrendExpansion -> SyntheticBpsFalseNegative",
                "family": "synthetic",
                "direction": "long",
                "trade_count": 100,
                "wins": 52,
                "losses": 48,
                "days": 100,
                "total_profit_pct": 1.0,
                "representative_entry_price": 15000.0,
            }
        )
        churn = module.classify_screen_row(
            {
                "scope": "per_pair",
                "symbol": "NQ",
                "pair": "NQ/USD",
                "timeframe": "1m",
                "strategy_name": "SyntheticNoEdgeChurn",
                "factor_id": "synthetic_no_edge_churn",
                "branch_path": "MicroScalp -> SyntheticNoEdgeChurn",
                "family": "synthetic",
                "direction": "long",
                "trade_count": 26304,
                "wins": 13200,
                "losses": 13104,
                "days": 1260,
                "total_profit_pct": 8.41728,
                "representative_entry_price": 15000.0,
            }
        )

        self.assertTrue(false_negative["survives_instrument_cost"])
        self.assertNotIn("survives_5bps_per_side", false_negative)
        self.assertEqual(false_negative["cost_wall_bucket"], "realistic_cost_survivor")
        self.assertGreater(false_negative["gross_edge_bps_per_trade"], false_negative["instrument_cost_bps_per_trade"])

        self.assertFalse(churn["survives_instrument_cost"])
        self.assertEqual(churn["cost_wall_bucket"], "zero_edge_churn_not_rescued_by_realistic_cost")
        self.assertLess(churn["gross_edge_bps_per_trade"], churn["instrument_cost_bps_per_trade"])

    def test_score_rows_uses_actual_backtest_span_for_density(self) -> None:
        module = self.load_module()

        specs = module.generated_strategy_specs(["NQ"], "1m", families=["aroon_cci_trend_continuation"])
        stdout = "\n".join(
            [
                "Backtested 2021-01-04 02:40:00 -> 2021-02-15 23:16:00 | Max open trades : 1",
                "---",
                "strategy:         TomacNQAroonCciTrendContinuationOneMinCleanV1",
                "pairs:            NQ/USD",
                "sharpe:           2.8979",
                "sortino:          9.2213",
                "calmar:           128.0706",
                "total_profit_pct: 4.0000",
                "trade_count:      50",
                "win_rate_pct:     58.8235",
                "profit_factor:    2.3566",
                "per_pair:",
                "  NQ/USD: sharpe=2.8979 trades=50 profit_pct=6.00 dd_pct=-0.71 wr=58.8 pf=2.36",
            ]
        )

        rows = module.score_rows(stdout, specs)
        per_pair = next(row for row in rows if row["scope"] == "per_pair")

        self.assertGreater(per_pair["trades_per_day"], 1.0)
        self.assertNotIn("density_target_1_to_3_per_day", per_pair)

    def test_score_rows_recovers_freqtrade_result_table_when_timeout_precedes_machine_block(self) -> None:
        module = self.load_module()

        specs = module.generated_strategy_specs(["NQ"], "1m", families=["regression_channel_r2_slope_breadth"])
        stdout = "\n".join(
            [
                "Result for strategy TomacNQRegressionChannelR2SlopeBreadthOneMinCleanV1",
                "│ NQ/USD │    304 │         0.02 │       7547.257 │         7.55 │      0:57:00 │  148     0   156  48.7 │",
                "│ ES/USD │      0 │          0.0 │          0.000 │          0.0 │         0:00 │    0     0     0     0 │",
                "│  TOTAL │    304 │         0.02 │       7547.257 │         7.55 │      0:57:00 │  148     0   156  48.7 │",
                "│ Backtesting from              │ 2021-01-04 02:40:00            │",
                "│ Backtesting to                │ 2025-12-31 00:00:00            │",
                "│ Total/Daily Avg Trades        │ 304 / 0.17                     │",
                "│ Total profit %                │ 7.55%                          │",
                "│ Sortino                       │ 0.43                           │",
                "│ Sharpe                        │ 0.24                           │",
                "│ Calmar                        │ 2.34                           │",
                "│ Profit factor                 │ 1.20                           │",
                "│ Max % of account underwater   │ 3.38%                          │",
                "Backtested 2021-01-04 02:40:00 -> 2025-12-31 00:00:00 | Max open trades : 1",
                "│ TomacNQRegressionChannelR2SlopeBreadthOneMinCleanV1 │    304 │         0.02 │       7547.257 │         7.55 │      0:57:00 │  148     0   156  48.7 │ 3543.122 USD  3.38% │",
            ]
        )

        rows = module.score_rows(stdout, specs)
        per_pair = next(row for row in rows if row["scope"] == "per_pair")

        self.assertEqual(per_pair["symbol"], "NQ")
        self.assertEqual(per_pair["trade_count"], 304)
        self.assertAlmostEqual(per_pair["total_profit_pct"], 7.55)
        self.assertAlmostEqual(per_pair["profit_factor"], 1.20)
        self.assertTrue(per_pair["survives_instrument_cost"])
        self.assertNotIn("survives_5bps_per_side", per_pair)
        self.assertLess(per_pair["trades_per_day"], 1.0)
        self.assertNotIn("density_target_1_to_3_per_day", per_pair)
        self.assertTrue(per_pair["gate1_survivor"])

    def test_gate1_survivor_accepts_bidirectional_parent_replay_direction(self) -> None:
        module = self.load_module()

        row = module.classify_screen_row(
            {
                "scope": "per_pair",
                "symbol": "ES",
                "pair": "ES/USD",
                "timeframe": "1m",
                "strategy_name": "TomacESWprFractalNoBeFullTargetOneMinCleanV1",
                "factor_id": "tomac_idxfut_clean_wpr_fractal_no_be_fulltarget_1m_v1",
                "branch_path": (
                    "RangeReversion -> PdhPdlFractalLiquiditySweep -> "
                    "WprFractalNoBreakEvenFullTarget -> "
                    "tomac_idxfut_clean_wpr_fractal_no_be_fulltarget_1m_v1"
                ),
                "family": "wpr_fractal_no_be_fulltarget",
                "direction": "long_short",
                "trade_count": 120,
                "wins": 80,
                "losses": 40,
                "days": 60,
                "total_profit_pct": 20.0,
                "representative_entry_price": 5200.0,
            }
        )

        self.assertTrue(row["direction_consistent_local"])
        self.assertTrue(row["gate1_survivor"])

    def test_gate1_survivor_uses_verified_futures_contract_cost_not_5bps_stress(self) -> None:
        module = self.load_module()

        row = module.classify_screen_row(
            {
                "scope": "per_pair",
                "symbol": "NQ",
                "pair": "NQ/USD",
                "timeframe": "5m",
                "strategy_name": "SyntheticHardCostProbe",
                "factor_id": "synthetic_hard_cost_probe",
                "branch_path": "RangeConsolidation -> SyntheticHardCostProbe",
                "family": "synthetic",
                "direction": "long",
                "trade_count": 1362,
                "wins": 690,
                "losses": 671,
                "days": 1260,
                "total_profit_pct": 18.17,
                "representative_entry_price": 18000.0,
            }
        )

        self.assertTrue(row["survives_instrument_cost"])
        self.assertNotIn("survives_1bps_per_side", row)
        self.assertNotIn("survives_2bps_per_side", row)
        self.assertNotIn("survives_5bps_per_side", row)
        self.assertNotIn("cost_stress_5bps_role", row)
        self.assertTrue(row["gate1_survivor"])

    def test_gate1_survivor_blocks_unverified_default_futures_cost_profile(self) -> None:
        module = self.load_module()

        row = module.classify_screen_row(
            {
                "scope": "per_pair",
                "symbol": "RTY",
                "pair": "RTY/USD",
                "timeframe": "5m",
                "strategy_name": "SyntheticUnverifiedDefaultCostProfile",
                "factor_id": "synthetic_unverified_default_cost_profile",
                "branch_path": "TrendExpansion -> SyntheticUnverifiedDefaultCostProfile",
                "family": "synthetic",
                "direction": "long",
                "trade_count": 120,
                "wins": 70,
                "losses": 50,
                "days": 60,
                "total_profit_pct": 20.0,
                "representative_entry_price": 2100.0,
            }
        )

        self.assertEqual(row["cost_profile_id"], "CME_RTY_default_v1")
        self.assertEqual(row["cost_model_status"], "default_assumption_unverified")
        self.assertFalse(row["cost_model_verified_for_promotion"])
        self.assertTrue(row["survives_instrument_cost"])
        self.assertEqual(row["cost_model_blocker"], "cost_model_unverified")
        self.assertFalse(row["gate1_survivor"])

    def test_legacy_xau_tomac_source_normalizes_to_gc_for_gate1(self) -> None:
        module = self.load_module()

        row = module.classify_screen_row(
            {
                "scope": "per_pair",
                "symbol": "XAU",
                "pair": "XAU/USD",
                "timeframe": "15m",
                "strategy_name": "SyntheticXauGcAliasCostProbe",
                "factor_id": "synthetic_xau_gc_alias_cost_probe",
                "branch_path": "RegimeUncertainty -> SyntheticXauGcAliasCostProbe",
                "family": "synthetic",
                "direction": "long",
                "trade_count": 5236,
                "wins": 2534,
                "losses": 2702,
                "days": 1822,
                "total_profit_pct": 97.58,
                "representative_entry_price": 2300.0,
            }
        )

        self.assertEqual(row["symbol"], "GC")
        self.assertEqual(row["pair"], "GC/USD")
        self.assertEqual(row["legacy_symbol_alias"], "XAU")
        self.assertEqual(row["legacy_pair_alias"], "XAU/USD")
        self.assertEqual(row["cost_profile_id"], "COMEX_GC_IBKR_verified_20260530_v1")
        self.assertEqual(row["cost_model_status"], "verified_ibkr_broker_side")
        self.assertTrue(row["promotion_cost_verified"])
        self.assertEqual(row["cost_model_blocker"], "none")
        self.assertTrue(row["survives_instrument_cost"])
        self.assertGreater(row["instrument_cost_total_profit_pct"], 0.0)
        self.assertTrue(row["gate1_survivor"])

    def test_cost_survival_is_separate_from_trade_sample_floor(self) -> None:
        module = self.load_module()

        row = module.classify_screen_row(
            {
                "scope": "per_pair",
                "symbol": "ES",
                "pair": "ES/USD",
                "timeframe": "5m",
                "strategy_name": "SyntheticSparseProfitableProbe",
                "factor_id": "synthetic_sparse_profitable_probe",
                "branch_path": "TrendExpansion -> SyntheticSparseProfitableProbe",
                "family": "synthetic",
                "direction": "long",
                "trade_count": 20,
                "wins": 12,
                "losses": 8,
                "days": 10,
                "total_profit_pct": 100.0,
                "representative_entry_price": 5200.0,
            }
        )

        self.assertNotIn("survives_5bps_per_side", row)
        self.assertTrue(row["survives_instrument_cost"])
        self.assertFalse(row["minimum_trade_sample_floor_met"])
        self.assertNotIn("density_target_1_to_3_per_day", row)
        self.assertFalse(row["gate1_survivor"])

    def test_gate_summary_does_not_promote_retired_transition_fields_as_hard_gates(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            compact_root = Path(tmp) / "compact"
            stdout_path = root / "command-output/run_tomac_1m.out"
            stdout_path.parent.mkdir(parents=True)
            stdout_path.write_text("", encoding="utf-8")

            gate = module.write_aq_gate_summary(
                root,
                compact_root,
                timeframe="1m",
                command={
                    "name": "run_tomac_1m",
                    "exit": 0,
                    "timed_out": False,
                    "stdout_path": str(stdout_path),
                    "stderr_path": str(root / "command-output/run_tomac_1m.err"),
                    "exit_path": str(root / "checks/run_tomac_1m.exit"),
                },
                specs=[],
            )

        required_next = gate["hard_promotion_gates_required_next"]
        self.assertNotIn("transition_hazard_lt_0_60", required_next)
        self.assertNotIn("pda_hybrid_alignment_true", required_next)
        self.assertIn("duration_readiness_confirmed", required_next)
        self.assertIn("path_ranker_or_catboost_runtime_score_visible", required_next)
        self.assertIn("execution_tree_readiness_gte_0_65", required_next)

    def test_gate_summary_reports_realistic_cost_survivors_without_gate1_promotion(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            compact_root = Path(tmp) / "compact"
            stdout_path = root / "command-output/run_tomac_1m.out"
            stdout_path.parent.mkdir(parents=True)
            stdout_path.write_text(
                "\n".join(
                    [
                        "---",
                        "strategy:         TomacNQRegressionChannelR2SlopeBreadthOneMinCleanV1",
                        "pairs:            NQ/USD",
                        "sharpe:           0.2400",
                        "sortino:          0.4300",
                        "calmar:           2.3400",
                        "total_profit_pct: 7.5500",
                        "trade_count:      304",
                        "win_rate_pct:     48.7000",
                        "profit_factor:    1.2000",
                        "per_pair:",
                        "  NQ/USD: sharpe=0.24 trades=304 profit_pct=7.55 dd_pct=-3.38 wr=48.7 pf=1.20",
                    ]
                ),
                encoding="utf-8",
            )

            gate = module.write_aq_gate_summary(
                root,
                compact_root,
                timeframe="1m",
                command={
                    "name": "run_tomac_1m",
                    "exit": 124,
                    "timed_out": True,
                    "stdout_path": str(stdout_path),
                    "stderr_path": str(root / "command-output/run_tomac_1m.err"),
                    "exit_path": str(root / "checks/run_tomac_1m.exit"),
                },
                specs=module.generated_strategy_specs(["NQ"], "1m", families=["regression_channel_r2_slope_breadth"]),
                clean_bundles=[
                    {
                        "symbol": "NQ",
                        "session_scope": "ETH/full_retained_session",
                        "rth_filter_applied": False,
                        "eth_full_retained_session_evidence": True,
                        "eth_full_retained_coverage_status": "verified_retained_rows_outside_rth",
                        "timeframes": {"1m": {"quality_ok": True}},
                        "source_archive_validation": {
                            "status": "pass_zip_pristine_source",
                            "blockers": [],
                        },
                    }
                ],
            )

        self.assertEqual(gate["decision"], "gate1_autoquant_instrument_cost_survivor_downstream_required")
        self.assertTrue(gate["downstream_allowed"])
        self.assertEqual([row["pair"] for row in gate["survivors_instrument_cost"]], ["NQ/USD"])
        self.assertNotIn("bps_stress_false_negative_rechecks", gate)
        self.assertEqual(gate["survivors_instrument_cost"][0]["cost_wall_bucket"], "realistic_cost_survivor")

    def test_gate_summary_blocks_downstream_without_eth_full_session_evidence(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            compact_root = Path(tmp) / "compact"
            stdout_path = root / "command-output/run_tomac_1m.out"
            stdout_path.parent.mkdir(parents=True)
            stdout_path.write_text(
                "\n".join(
                    [
                        "---",
                        "strategy:         TomacESOpeningDriveRvolVwapContinuationOneMinCleanV1",
                        "pairs:            ES/USD",
                        "sharpe:           2.0000",
                        "sortino:          2.0000",
                        "calmar:           2.0000",
                        "total_profit_pct: 200.0000",
                        "trade_count:      1500",
                        "win_rate_pct:     55.0000",
                        "profit_factor:    1.5000",
                        "per_pair:",
                        "  ES/USD: sharpe=2.00 trades=1500 profit_pct=200.00 dd_pct=-4.00 wr=55.0 pf=1.50",
                    ]
                ),
                encoding="utf-8",
            )

            gate = module.write_aq_gate_summary(
                root,
                compact_root,
                timeframe="1m",
                command={
                    "name": "run_tomac_1m",
                    "exit": 0,
                    "timed_out": False,
                    "stdout_path": str(stdout_path),
                    "stderr_path": str(root / "command-output/run_tomac_1m.err"),
                    "exit_path": str(root / "checks/run_tomac_1m.exit"),
                },
                specs=module.generated_strategy_specs(["ES"], "1m", families=["opening_drive_rvol_vwap_continuation"]),
                clean_bundles=[
                    {
                        "symbol": "ES",
                        "session_scope": "ETH/full_retained_session",
                        "rth_filter_applied": False,
                        "eth_full_retained_session_evidence": False,
                        "eth_full_retained_coverage_status": "session_scope_unverified_no_rows_outside_rth",
                        "timeframes": {"1m": {"quality_ok": True}},
                        "source_archive_validation": {
                            "status": "pass_zip_pristine_source",
                            "blockers": [],
                        },
                    }
                ],
            )

        self.assertEqual(gate["decision"], "blocked_session_scope_unverified_no_downstream")
        self.assertFalse(gate["downstream_allowed"])
        self.assertFalse(gate["pre_bayes_allowed"])
        self.assertFalse(gate["bbn_allowed"])
        self.assertFalse(gate["survivors_instrument_cost"])
        self.assertNotIn("survivors_5bps", gate)
        self.assertEqual(gate["session_scope"], "ETH/full_retained_session")
        self.assertFalse(gate["eth_full_retained_session_evidence"])
        self.assertEqual(gate["source_archive_validation_status"], "pass_zip_pristine_source")

    def test_gate_summary_blocks_downstream_without_zip_pristine_source_validation(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            compact_root = Path(tmp) / "compact"
            stdout_path = root / "command-output/run_tomac_5m.out"
            stdout_path.parent.mkdir(parents=True)
            specs = module.generated_strategy_specs(
                ["NQ"],
                "5m",
                families=["opening_drive_rvol_vwap_continuation"],
            )
            stdout_path.write_text(
                "\n".join(
                    [
                        "---",
                        f"strategy:         {specs[0].class_name}",
                        "pairs:            NQ/USD",
                        "sharpe:           1.2000",
                        "sortino:          1.8000",
                        "calmar:           2.1000",
                        "total_profit_pct: 18.1700",
                        "trade_count:      1362",
                        "win_rate_pct:     50.6610",
                        "profit_factor:    1.1200",
                        "per_pair:",
                        "  NQ/USD: sharpe=1.20 trades=1362 profit_pct=18.17 dd_pct=-4.00 wr=50.7 pf=1.12",
                    ]
                ),
                encoding="utf-8",
            )

            gate = module.write_aq_gate_summary(
                root,
                compact_root,
                timeframe="5m",
                command={
                    "name": "run_tomac_5m",
                    "exit": 0,
                    "timed_out": False,
                    "stdout_path": str(stdout_path),
                    "stderr_path": str(root / "command-output/run_tomac_5m.err"),
                    "exit_path": str(root / "checks/run_tomac_5m.exit"),
                },
                specs=specs,
                clean_bundles=[
                    {
                        "symbol": "NQ",
                        "source_csv": "/tmp/polluted.csv",
                        "session_scope": "ETH/full_retained_session",
                        "rth_filter_applied": False,
                        "eth_full_retained_session_evidence": True,
                        "eth_full_retained_coverage_status": "verified_retained_rows_outside_rth",
                        "timeframes": {"5m": {"quality_ok": True}},
                    }
                ],
            )

        self.assertEqual(gate["decision"], "blocked_source_archive_validation_unverified_no_downstream")
        self.assertFalse(gate["downstream_allowed"])
        self.assertFalse(gate["survivors_instrument_cost"])
        self.assertEqual(gate["source_archive_validation_status"], "fail_closed_polluted_or_unverified_source")
        self.assertEqual(
            gate["data_provenance"]["source_archive_validation"]["status"],
            "fail_closed_polluted_or_unverified_source",
        )
        self.assertEqual(
            gate["data_provenance"]["source_archive_validation"]["symbol_statuses"][0]["status"],
            "missing_source_archive_validation",
        )

    def test_gate_summary_uses_instrument_cost_as_authority_and_5bps_as_stress(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            compact_root = Path(tmp) / "compact"
            stdout_path = root / "command-output/run_tomac_5m.out"
            stdout_path.parent.mkdir(parents=True)
            specs = module.generated_strategy_specs(
                ["NQ"],
                "5m",
                families=["opening_drive_rvol_vwap_continuation"],
            )
            stdout_path.write_text(
                "\n".join(
                    [
                        "---",
                        f"strategy:         {specs[0].class_name}",
                        "pairs:            NQ/USD",
                        "sharpe:           1.2000",
                        "sortino:          1.8000",
                        "calmar:           2.1000",
                        "total_profit_pct: 18.1700",
                        "trade_count:      1362",
                        "win_rate_pct:     50.6610",
                        "profit_factor:    1.1200",
                        "per_pair:",
                        "  NQ/USD: sharpe=1.20 trades=1362 profit_pct=18.17 dd_pct=-4.00 wr=50.7 pf=1.12",
                    ]
                ),
                encoding="utf-8",
            )

            gate = module.write_aq_gate_summary(
                root,
                compact_root,
                timeframe="5m",
                command={
                    "name": "run_tomac_5m",
                    "exit": 0,
                    "timed_out": False,
                    "stdout_path": str(stdout_path),
                    "stderr_path": str(root / "command-output/run_tomac_5m.err"),
                    "exit_path": str(root / "checks/run_tomac_5m.exit"),
                },
                specs=specs,
                clean_bundles=[
                    {
                        "symbol": "NQ",
                        "session_scope": "ETH/full_retained_session",
                        "rth_filter_applied": False,
                        "eth_full_retained_session_evidence": True,
                        "eth_full_retained_coverage_status": "verified_retained_rows_outside_rth",
                        "timeframes": {"5m": {"quality_ok": True}},
                        "source_archive_validation": {
                            "status": "pass_zip_pristine_source",
                            "blockers": [],
                        },
                    }
                ],
            )

        self.assertEqual(gate["decision"], "gate1_autoquant_instrument_cost_survivor_downstream_required")
        self.assertTrue(gate["downstream_allowed"])
        self.assertEqual(gate["cost_gate_authority"], "instrument_cost")
        self.assertEqual(gate["source_archive_validation_status"], "pass_zip_pristine_source")
        self.assertEqual(
            gate["data_provenance"]["source_archive_validation"]["status"],
            "pass_zip_pristine_source",
        )
        self.assertNotIn("cost_stress_5bps_role", gate)
        self.assertEqual(len(gate["survivors_instrument_cost"]), 1)
        self.assertEqual(gate["survivors_declared_cost"], gate["survivors_instrument_cost"])
        self.assertEqual(gate["raw_survivors_before_session_scope"], gate["raw_instrument_cost_survivors_before_session_scope"])
        survivor = gate["survivors_instrument_cost"][0]
        self.assertTrue(survivor["survives_instrument_cost"])
        self.assertNotIn("survives_5bps_per_side", survivor)
        self.assertNotIn("survivors_5bps", gate)
        self.assertNotIn("cost_stress_survivors_5bps", gate)

    def test_terminal_regime_feedback_packets_carry_clean_provenance_and_pending_placement(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            compact_root = Path(tmp) / "compact"
            gate = {
                "timeframe": "15m",
                "command": {"exit": 0, "timed_out": False},
                "decision": "gate1_autoquant_instrument_cost_survivor_downstream_required",
                "rank_rows": 4,
                "session_scope": "ETH/full_retained_session",
                "rth_filter_applied": False,
                "eth_full_retained_session_evidence": True,
                "source_archive_validation_status": "pass_zip_pristine_source",
                "data_provenance": {
                    "cleaning_status": "cleaned_or_verified_retained",
                    "raw_fallback_used": False,
                    "source_archive_validation": {
                        "status": "pass_zip_pristine_source",
                        "symbol_statuses": [{"symbol": "NQ", "status": "pass_zip_pristine_source"}],
                    },
                },
                "survivors_instrument_cost": [
                    {
                        "symbol": "NQ",
                        "timeframe": "15m",
                        "family": "htf_range_breakout_retest_te_selective",
                        "factor_id": "tomac_idxfut_clean_htf_range_breakout_retest_te_selective_15m_v1",
                        "branch_path": (
                            "TrendExpansion -> HtfRangeBreakoutRetestAcceptance -> SelectivePosteriorV1 -> "
                            "tomac_idxfut_clean_htf_range_breakout_retest_te_selective_15m_v1"
                        ),
                        "trade_count": 42,
                        "cost_profile_id": "CME_NQ_IBKR_verified_20260530_v1",
                        "cost_model_status": "verified_ibkr_broker_side",
                        "cost_model_verified_for_promotion": True,
                        "promotion_cost_verified": True,
                        "instrument_cost_total_profit_pct": 1.25,
                        "survives_instrument_cost": True,
                        "gate1_survivor": True,
                    }
                ],
                "realistic_cost_survivors_before_gate1": [],
                "downstream_allowed": True,
                "pre_bayes_allowed": True,
                "bbn_allowed": True,
                "catboost_allowed": False,
                "execution_tree_allowed": False,
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
            }
            summary = {
                "symbols": ["NQ", "YM"],
                "timeframes": ("1m", "3m", "5m", "15m", "30m", "1h", "4h"),
                "families": ["htf_range_breakout_retest_te_selective"],
                "aq_gate_summaries": [gate],
            }

            module.write_terminal_regime_feedback_packets(root, compact_root, summary)

            terminal = json.loads((root / "checks/terminal_metrics.json").read_text(encoding="utf-8"))
            terminal_summary = json.loads(
                (root / "summaries/terminal_summary.json").read_text(encoding="utf-8")
            )
            regime = json.loads(
                (root / "checks/regime_feedback_evidence_packet.json").read_text(encoding="utf-8")
            )
            compact_terminal_summary = json.loads(
                (compact_root / "summaries/terminal_summary.json").read_text(encoding="utf-8")
            )
            compact_regime = json.loads(
                (compact_root / "checks/regime_feedback_evidence_packet.json").read_text(encoding="utf-8")
            )

        self.assertEqual(terminal["source_archive_validation_status"], "pass_zip_pristine_source")
        self.assertEqual(
            terminal["data_provenance"]["source_archive_validation"]["status"],
            "pass_zip_pristine_source",
        )
        self.assertTrue(terminal["downstream_allowed"])
        self.assertFalse(terminal["trade_usable"])
        self.assertTrue(terminal["branch_fields_preserved"])
        self.assertEqual(terminal_summary["factor_id"], terminal["factor_id"])
        self.assertEqual(compact_terminal_summary["factor_id"], terminal["factor_id"])
        self.assertEqual(
            terminal["branch_path"],
            "TrendExpansion -> HtfRangeBreakoutRetestAcceptance -> SelectivePosteriorV1 -> "
            "tomac_idxfut_clean_htf_range_breakout_retest_te_selective_15m_v1",
        )
        self.assertEqual(terminal["cost_row"]["symbol"], "NQ")
        self.assertEqual(terminal["cost_gate_authority"], "instrument_cost")
        checker_script = module.REPO / "support/scripts/research/regime_root_metrics_contract_check.py"
        checker_spec = importlib.util.spec_from_file_location("regime_root_metrics_contract_check", checker_script)
        assert checker_spec is not None and checker_spec.loader is not None
        checker = importlib.util.module_from_spec(checker_spec)
        sys.modules[checker_spec.name] = checker
        checker_spec.loader.exec_module(checker)
        contract_report = checker.check_payload(terminal, path=root / "checks/terminal_metrics.json")
        self.assertEqual(contract_report["decision"], "contract_ok", contract_report)
        self.assertEqual(regime["schema_version"], "autoquant-regime-feedback-evidence-packet/v1")
        self.assertEqual(regime["evidence_type"], "backtest_autoquant_feedback")
        self.assertEqual(regime["feedback_source"], "exact_aq_backtest")
        self.assertEqual(regime["entry_policy"]["entry_allowed_regime"], "TrendExpansion")
        self.assertEqual(regime["entry_policy"]["other_regimes_policy"], "reference_veto_only_no_entry")
        self.assertFalse(regime["practical_flags"]["trade_usable"])
        self.assertEqual(regime["per_timeframe_evidence"][0]["factor_id"], regime["factor_id"])
        self.assertIn("accepted_paper_live_execution_feedback_missing", regime["blockers"])
        self.assertEqual(regime["data_provenance"]["cleaning_status"], "cleaned_or_verified_retained")
        self.assertEqual(
            regime["belief_network_placement"]["status"],
            "pending_belief_network_and_execution_tree_readback",
        )
        self.assertFalse(regime["execution_tree_placement"]["visible_in_execution_tree"])
        self.assertFalse(regime["regime_feedback_admission"]["trade_usable_report_allowed"])
        self.assertEqual(compact_regime["factor_id"], regime["factor_id"])

    def test_successful_aq_run_writes_terminal_metrics_and_regime_packet(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            compact_root = Path(tmp) / "compact"
            source = module.TomacSource(symbol="NQ", source_csv=Path("/tmp/nq.csv"))
            gate = {
                "timeframe": "5m",
                "command": {"exit": 0, "timed_out": False},
                "decision": "gate1_autoquant_instrument_cost_survivor_downstream_required",
                "rank_rows": 2,
                "session_scope": "ETH/full_retained_session",
                "rth_filter_applied": False,
                "eth_full_retained_session_evidence": True,
                "source_archive_validation_status": "pass_zip_pristine_source",
                "data_provenance": {
                    "cleaning_status": "cleaned_or_verified_retained",
                    "raw_fallback_used": False,
                    "source_archive_validation": {"status": "pass_zip_pristine_source"},
                },
                "survivors_instrument_cost": [
                    {
                        "symbol": "NQ",
                        "timeframe": "5m",
                        "family": "trend_expansion_only_regime_transition_strict_state_shift",
                        "factor_id": (
                            "tomac_nq_5m_trend_expansion_only_regime_transition_long_"
                            "strict_state_shift_exact_aq_v1"
                        ),
                        "branch_path": (
                            "RegimeTransition -> TrendExpansionOnly -> "
                            "CompressionBreakoutStateShift -> StrictStateShift -> "
                            "tomac_nq_5m_trend_expansion_only_regime_transition_long_"
                            "strict_state_shift_exact_aq_v1"
                        ),
                        "trade_count": 1028,
                        "instrument_cost_total_profit_pct": 0.961667,
                        "survives_instrument_cost": True,
                        "gate1_survivor": True,
                    }
                ],
                "downstream_allowed": True,
                "pre_bayes_allowed": True,
                "bbn_allowed": True,
                "catboost_allowed": False,
                "execution_tree_allowed": False,
                "promotion_allowed": False,
                "trade_usable": False,
                "update_goal": False,
                "cost_gate_authority": "instrument_cost",
            }

            module.source_universe = lambda: [source]
            module.run_claim_collision_audit = lambda *args, **kwargs: {
                "pass": True,
                "decision": "claim_collision_guard_pass",
                "foreign_active_claims": [],
                "foreign_live_processes": [],
            }
            module.write_clean_bundle = lambda *args, **kwargs: {
                "symbol": "NQ",
                "session_scope": "ETH/full_retained_session",
                "rth_filter_applied": False,
                "eth_full_retained_session_evidence": True,
                "timeframes": {"5m": {"quality_ok": True}},
                "source_archive_validation": {
                    "status": "pass_zip_pristine_source",
                    "blockers": [],
                },
            }
            module.stage_aq_inputs = lambda *args, **kwargs: {
                "workspace": str(root / "aq_workspace"),
                "strategy_specs": [],
            }
            module.run_cmd = lambda *args, **kwargs: {"exit": 0, "timed_out": False}
            module.write_aq_gate_summary = lambda *args, **kwargs: gate

            summary = module.run(
                argparse.Namespace(
                    root=str(root),
                    compact_root=str(compact_root),
                    symbols="NQ",
                    start="2021-01-01",
                    end="2021-01-02",
                    timeframes="5m",
                    families="trend_expansion_only_regime_transition_strict_state_shift",
                    max_rows=None,
                    chunksize=10,
                    reuse_clean=False,
                    aq_smoke_timeframe="5m",
                    aq_symbol_limit=1,
                    clean_only=False,
                    timeout=1,
                )
            )

            terminal = json.loads((root / "checks/terminal_metrics.json").read_text(encoding="utf-8"))
            terminal_summary = json.loads(
                (root / "summaries/terminal_summary.json").read_text(encoding="utf-8")
            )
            regime = json.loads(
                (root / "checks/regime_feedback_evidence_packet.json").read_text(encoding="utf-8")
            )
            compact_terminal = json.loads(
                (compact_root / "checks/terminal_metrics.json").read_text(encoding="utf-8")
            )
            compact_terminal_summary = json.loads(
                (compact_root / "summaries/terminal_summary.json").read_text(encoding="utf-8")
            )
            compact_regime = json.loads(
                (compact_root / "checks/regime_feedback_evidence_packet.json").read_text(encoding="utf-8")
            )

        self.assertEqual(summary["aq_gate_summaries"], [gate])
        self.assertEqual(terminal["terminal_status"], "gate1_clean_survivor_pending_downstream_regime_feedback")
        self.assertEqual(terminal["terminal_decision"], gate["decision"])
        self.assertFalse(terminal["trade_usable"])
        self.assertEqual(regime["schema_version"], "autoquant-regime-feedback-evidence-packet/v1")
        self.assertEqual(regime["evidence_type"], "backtest_autoquant_feedback")
        self.assertEqual(regime["feedback_source"], "exact_aq_backtest")
        self.assertEqual(regime["entry_policy"]["entry_allowed_regime"], "TrendExpansion")
        self.assertFalse(regime["regime_feedback_admission"]["pre_bayes_feedback"])
        self.assertFalse(regime["practical_flags"]["promotion_allowed"])
        self.assertIn("same_tree_practical_closure_missing", regime["blockers"])
        self.assertEqual(
            regime["belief_network_placement"]["status"],
            "pending_belief_network_and_execution_tree_readback",
        )
        self.assertEqual(terminal_summary["terminal_decision"], gate["decision"])
        self.assertEqual(compact_terminal["factor_id"], terminal["factor_id"])
        self.assertEqual(compact_terminal_summary["factor_id"], terminal["factor_id"])
        self.assertEqual(compact_regime["factor_id"], regime["factor_id"])

    def test_run_reuse_clean_loads_existing_bundle_without_raw_source(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean_dir = root / "clean/ES"
            clean_dir.mkdir(parents=True)
            feather = clean_dir / "ES_USD-5m.feather"
            pd.DataFrame(
                {
                    "date": pd.date_range("2025-03-17T13:30:00Z", periods=3, freq="5min"),
                    "open": [100.0, 101.0, 102.0],
                    "high": [101.0, 102.0, 103.0],
                    "low": [99.0, 100.0, 101.0],
                    "close": [100.5, 101.5, 102.5],
                    "volume": [10.0, 11.0, 12.0],
                }
            ).to_feather(feather)
            bundle = {
                "symbol": "ES",
                "source_csv": "/does/not/exist.csv",
                "session_scope": "ETH/full_retained_session",
                "rth_filter_applied": False,
                "eth_full_retained_session_evidence": True,
                "source_archive_validation": {
                    "status": "pass_zip_pristine_source",
                    "blockers": [],
                },
                "timeframes": {
                    "5m": {
                        "symbol": "ES",
                        "timeframe": "5m",
                        "quality_ok": True,
                        "feather": str(feather),
                    }
                },
            }
            (clean_dir / "clean_quality.json").write_text(json.dumps(bundle), encoding="utf-8")
            original_universe = module.source_universe
            module.source_universe = lambda: [
                module.TomacSource(symbol="ES", source_csv=Path("/does/not/exist.csv"))
            ]
            try:
                summary = module.run(
                    module.argparse.Namespace(
                        root=str(root),
                        compact_root=str(root / "compact"),
                        symbols="ES",
                        start="2025-03-17",
                        end="2025-03-18",
                        timeframes="5m",
                        max_rows=None,
                        chunksize=10,
                        clean_only=True,
                        reuse_clean=True,
                        aq_smoke_timeframe=None,
                        aq_symbol_limit=1,
                        timeout=10,
                    )
                )
            finally:
                module.source_universe = original_universe

            self.assertEqual(summary["clean_bundles"][0]["source_csv"], "/does/not/exist.csv")
            self.assertEqual(summary["aq_staging"], [])

    def test_reuse_clean_requires_zip_pristine_source_validation_before_aq(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean_dir = root / "clean/ES"
            clean_dir.mkdir(parents=True)
            feather = clean_dir / "ES_USD-5m.feather"
            pd.DataFrame(
                {
                    "date": pd.date_range("2025-03-17T13:30:00Z", periods=3, freq="5min"),
                    "open": [100.0, 101.0, 102.0],
                    "high": [101.0, 102.0, 103.0],
                    "low": [99.0, 100.0, 101.0],
                    "close": [100.5, 101.5, 102.5],
                    "volume": [10.0, 11.0, 12.0],
                }
            ).to_feather(feather)
            (clean_dir / "clean_quality.json").write_text(
                json.dumps(
                    {
                        "symbol": "ES",
                        "session_scope": "ETH/full_retained_session",
                        "rth_filter_applied": False,
                        "eth_full_retained_session_evidence": True,
                        "timeframes": {
                            "5m": {
                                "symbol": "ES",
                                "timeframe": "5m",
                                "quality_ok": True,
                                "feather": str(feather),
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "pass_zip_pristine_source"):
                module.load_clean_bundle(root, "ES", ("5m",))

    def test_reuse_clean_requires_eth_full_retained_session_evidence_before_aq(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean_dir = root / "clean/ES"
            clean_dir.mkdir(parents=True)
            feather = clean_dir / "ES_USD-5m.feather"
            pd.DataFrame(
                {
                    "date": pd.date_range("2025-03-17T13:30:00Z", periods=3, freq="5min"),
                    "open": [100.0, 101.0, 102.0],
                    "high": [101.0, 102.0, 103.0],
                    "low": [99.0, 100.0, 101.0],
                    "close": [100.5, 101.5, 102.5],
                    "volume": [10.0, 11.0, 12.0],
                }
            ).to_feather(feather)
            (clean_dir / "clean_quality.json").write_text(
                json.dumps(
                    {
                        "symbol": "ES",
                        "session_scope": "RTH_comparison",
                        "rth_filter_applied": True,
                        "eth_full_retained_session_evidence": False,
                        "source_archive_validation": {
                            "status": "pass_zip_pristine_source",
                            "blockers": [],
                        },
                        "timeframes": {
                            "5m": {
                                "symbol": "ES",
                                "timeframe": "5m",
                                "quality_ok": True,
                                "feather": str(feather),
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "ETH/full retained session proof"):
                module.load_clean_bundle(root, "ES", ("5m",))

    def test_generated_strategy_specs_can_select_camarilla_r3_s3_reclaim_branch(self) -> None:
        module = self.load_module()

        by_key = {spec.key: spec for spec in module.candidate_specs()}
        spec = by_key["camarilla_r3_s3_reclaim"]
        generated = module.generated_strategy_specs(
            ["NQ"],
            "1m",
            families=["camarilla_r3_s3_reclaim"],
        )

        self.assertEqual(
            spec.branch_path,
            "RangeReversion -> CamarillaPivotReclaim -> camarilla_r3_s3_reclaim_v1",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(generated[0].class_name, "TomacNQCamarillaR3S3ReclaimOneMinCleanV1")
        self.assertEqual(generated[0].factor_id, "tomac_idxfut_clean_camarilla_r3_s3_reclaim_1m_v1")
        self.assertEqual(
            generated[0].branch_path,
            "RangeReversion -> CamarillaPivotReclaim -> camarilla_r3_s3_reclaim_v1 -> "
            "tomac_idxfut_clean_camarilla_r3_s3_reclaim_1m_v1",
        )

    def test_generated_strategy_for_camarilla_r3_s3_reclaim_uses_prior_session_reclaim(self) -> None:
        module = self.load_module()

        spec = next(item for item in module.candidate_specs() if item.key == "camarilla_r3_s3_reclaim")
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertIn(
            "branch_path: RangeReversion -> CamarillaPivotReclaim -> camarilla_r3_s3_reclaim_v1 -> "
            "tomac_idxfut_clean_camarilla_r3_s3_reclaim_1m_v1",
            source,
        )
        self.assertIn('elif "camarilla_r3_s3_reclaim" == "camarilla_r3_s3_reclaim":', source)
        self.assertIn('dataframe["cam_r3"]', source)
        self.assertIn('dataframe["cam_s3"]', source)
        self.assertIn("s3_reclaim", source)
        self.assertIn("r3_reclaim", source)
        self.assertIn("camarilla_extension", source)
        self.assertIn("short_raw", source)
        self.assertIn("session_vwap", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_generated_strategy_for_lunch_liquidity_vacuum_vwap_magnet_reversal(self) -> None:
        module = self.load_module()

        spec = next(
            item
            for item in module.candidate_specs()
            if item.key == "lunch_liquidity_vacuum_vwap_magnet_reversal"
        )
        generated = module.generated_strategy_specs(
            ["NQ"],
            "1m",
            families=["lunch_liquidity_vacuum_vwap_magnet_reversal"],
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertEqual(
            spec.branch_path,
            "SessionRhythm -> LunchLiquidityVacuum -> VwapMagnetReversal",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            generated[0].class_name,
            "TomacNQLunchLiquidityVacuumVwapMagnetReversalOneMinCleanV1",
        )
        self.assertEqual(
            generated[0].factor_id,
            "tomac_idxfut_clean_lunch_liquidity_vacuum_vwap_magnet_reversal_1m_v1",
        )
        self.assertIn(
            "branch_path: SessionRhythm -> LunchLiquidityVacuum -> VwapMagnetReversal -> "
            "tomac_idxfut_clean_lunch_liquidity_vacuum_vwap_magnet_reversal_1m_v1",
            source,
        )
        self.assertIn(
            'elif "lunch_liquidity_vacuum_vwap_magnet_reversal" == '
            '"lunch_liquidity_vacuum_vwap_magnet_reversal":',
            source,
        )
        self.assertIn('dataframe["minute_of_day_ny"].between(11 * 60 + 20, 13 * 60 + 40)', source)
        self.assertIn("liquidity_vacuum", source)
        self.assertIn("vwap_magnet_distance", source)
        self.assertIn("mtf_range_votes", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_participation_clock_breakout_family_is_registered_with_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["participation_clock_breakout"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "ParticipationClockBreakout")
        self.assertEqual(
            spec.branch_path,
            "SessionLiquidity -> ParticipationClock -> RelativeVolumeAcceleration -> OpeningRangeAcceptance",
        )
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_participation_clock_breakout_5m_v1",
                "tomac_idxfut_clean_participation_clock_breakout_15m_v1",
                "tomac_idxfut_clean_participation_clock_breakout_30m_v1",
                "tomac_idxfut_clean_participation_clock_breakout_1h_v1",
                "tomac_idxfut_clean_participation_clock_breakout_4h_v1",
                "tomac_idxfut_clean_participation_clock_breakout_1d_v1",
            ],
        )

    def test_participation_clock_breakout_strategy_source_uses_shifted_opening_range_acceptance(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["participation_clock_breakout"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_idxfut_clean_participation_clock_breakout_15m_v1", source)
        self.assertIn("ParticipationClock", source)
        self.assertIn("RelativeVolumeAcceleration", source)
        self.assertIn("opening_range_acceptance", source)
        self.assertIn("participation_clock", source)
        self.assertIn("rvol_acceleration", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)


    def test_candidate_specs_can_select_rsrs_high_low_regression_trend_admission(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["rsrs_high_low_regression_trend_admission"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "RsrsHighLowRegressionTrendAdmission")
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> HighLowRegressionTrendQuality -> RsrsZscoreAdmission -> FixedRrrContinuation",
        )
        self.assertEqual(
            spec.factor_id("1m"),
            "tomac_idxfut_clean_rsrs_high_low_regression_trend_admission_1m_v1",
        )

    def test_generated_strategy_for_rsrs_high_low_regression_uses_shifted_admission(self) -> None:
        module = self.load_module()

        spec = module.candidate_specs(families=["rsrs_high_low_regression_trend_admission"])[0]
        generated = module.generated_strategy_specs(
            ["NQ"],
            "1m",
            families=["rsrs_high_low_regression_trend_admission"],
        )
        source = module.strategy_source(spec, symbol="NQ", timeframe="1m")

        self.assertEqual(
            generated[0].class_name,
            "TomacNQRsrsHighLowRegressionTrendAdmissionOneMinCleanV1",
        )
        self.assertIn(
            "branch_path: TrendExpansion -> HighLowRegressionTrendQuality -> RsrsZscoreAdmission -> "
            "FixedRrrContinuation -> tomac_idxfut_clean_rsrs_high_low_regression_trend_admission_1m_v1",
            source,
        )
        self.assertIn(
            'elif "rsrs_high_low_regression_trend_admission" == "rsrs_high_low_regression_trend_admission":',
            source,
        )
        self.assertIn('dataframe["rsrs_beta_24"]', source)
        self.assertIn('dataframe["rsrs_z_144_shifted"]', source)
        self.assertIn('dataframe["rsrs_r2_24_shifted"]', source)
        self.assertIn('dataframe["rsrs_right_skew_score_shifted"]', source)
        self.assertIn(
            'return dataframe.drop(columns=["__row_order"], errors="ignore").copy()',
            source,
        )
        self.assertLess(
            source.index('if "rsrs_high_low_regression_trend_admission" == "rsrs_high_low_regression_trend_admission":'),
            source.index("def _rank_trend_corr"),
        )
        self.assertLess(
            source.index('return dataframe.drop(columns=["__row_order"], errors="ignore").copy()'),
            source.index("def _rank_trend_corr"),
        )
        self.assertIn("rsrs_trend_admission_long", source)
        self.assertIn("rsrs_trend_admission_short", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_candidate_specs_can_select_range_compression_participation_trend_breakout(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["range_compression_participation_trend_breakout"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "RangeCompressionParticipationTrendBreakout")
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.branch_path,
            "RegimeRoot -> LowVolatilityCompression -> ParticipationExpansion -> TrendBreakoutRejoin",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("5m", "15m", "30m", "1h", "4h", "1d")],
            [
                "tomac_idxfut_clean_range_compression_participation_trend_breakout_5m_v1",
                "tomac_idxfut_clean_range_compression_participation_trend_breakout_15m_v1",
                "tomac_idxfut_clean_range_compression_participation_trend_breakout_30m_v1",
                "tomac_idxfut_clean_range_compression_participation_trend_breakout_1h_v1",
                "tomac_idxfut_clean_range_compression_participation_trend_breakout_4h_v1",
                "tomac_idxfut_clean_range_compression_participation_trend_breakout_1d_v1",
            ],
        )

    def test_range_compression_participation_trend_breakout_source_uses_shifted_mtf_participation(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["range_compression_participation_trend_breakout"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_idxfut_clean_range_compression_participation_trend_breakout_15m_v1", source)
        self.assertIn("RangeCompressionParticipationTrendBreakout", source)
        self.assertIn("range_compression_state", source)
        self.assertIn("participation_expansion", source)
        self.assertIn("range_compression_mtf_resonance_long", source)
        self.assertIn("range_compression_mtf_resonance_short", source)
        self.assertIn("trend_breakout_rejoin_long", source)
        self.assertIn("trend_breakout_rejoin_short", source)
        self.assertIn("short_raw", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_trend_magic_cci_atr_candidates_are_registered_with_exact_nq_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(
            families=[
                "trend_magic_cci_atr_slow_long",
                "trend_magic_cci_atr_balanced_long",
            ]
        )

        self.assertEqual([spec.key for spec in specs], [
            "trend_magic_cci_atr_slow_long",
            "trend_magic_cci_atr_balanced_long",
        ])
        slow, balanced = specs
        self.assertEqual(slow.class_prefix, "TrendMagicCciAtrSlowLong")
        self.assertEqual(slow.direction, "long")
        self.assertTrue(slow.supports(symbol="NQ", timeframe="15m"))
        self.assertTrue(slow.supports(symbol="NQ", timeframe="5m"))
        self.assertFalse(slow.supports(symbol="ES", timeframe="15m"))
        self.assertFalse(slow.supports(symbol="NQ", timeframe="30m"))
        self.assertEqual(
            [slow.factor_id(timeframe) for timeframe in ("5m", "15m")],
            [
                "tomac_nq_5m_trend_magic_cci_atr_slow_long_exact_aq_v1",
                "tomac_nq_15m_trend_magic_cci_atr_slow_long_exact_aq_v1",
            ],
        )
        self.assertEqual(
            slow.branch_path_with_factor("15m"),
            "TrendExpansion -> TrendMagicCciAtrTrail -> MtfTrendContinuation -> "
            "SlowLongFrictionAwareAtrBracket -> "
            "tomac_nq_15m_trend_magic_cci_atr_slow_long_exact_aq_v1",
        )
        self.assertEqual(balanced.class_prefix, "TrendMagicCciAtrBalancedLong")
        self.assertEqual(balanced.direction, "long")
        self.assertTrue(balanced.supports(symbol="NQ", timeframe="5m"))
        self.assertFalse(balanced.supports(symbol="NQ", timeframe="15m"))
        self.assertEqual(
            balanced.factor_id("5m"),
            "tomac_nq_5m_trend_magic_cci_atr_balanced_long_exact_aq_v1",
        )

    def test_trend_magic_cci_atr_source_uses_shifted_trail_and_mtf_context(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["trend_magic_cci_atr_slow_long"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn("factor_id: tomac_nq_15m_trend_magic_cci_atr_slow_long_exact_aq_v1", source)
        self.assertIn("can_short = False", source)
        self.assertIn("TrendMagicCciAtrTrail", source)
        self.assertIn("trend_magic_cci_shifted", source)
        self.assertIn("trend_magic_atr_shifted", source)
        self.assertIn("trend_magic_line_shifted", source)
        self.assertIn("trend_magic_context_votes_long", source)
        self.assertIn("trend_magic_cci_atr_long", source)
        self.assertIn("trend_magic_mtf_continuation_long", source)
        self.assertIn("trend_magic_friction_aware_atr_bracket", source)
        self.assertIn("trend_magic_failure_long", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("exit_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_trendexpansion_event_duration_clock_is_registered_as_trend_root(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["trendexpansion_event_duration_liquidity_clock"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "TrendExpansionEventDurationLiquidityClock")
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.branch_path,
            "TrendExpansion -> EventDurationLiquidityClock -> ACDStyleDurationCompression -> ParentTrendAdmission",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("1m", "3m", "5m", "15m", "30m", "1h", "4h")],
            [
                "tomac_idxfut_clean_trendexpansion_event_duration_liquidity_clock_1m_v1",
                "tomac_idxfut_clean_trendexpansion_event_duration_liquidity_clock_3m_v1",
                "tomac_idxfut_clean_trendexpansion_event_duration_liquidity_clock_5m_v1",
                "tomac_idxfut_clean_trendexpansion_event_duration_liquidity_clock_15m_v1",
                "tomac_idxfut_clean_trendexpansion_event_duration_liquidity_clock_30m_v1",
                "tomac_idxfut_clean_trendexpansion_event_duration_liquidity_clock_1h_v1",
                "tomac_idxfut_clean_trendexpansion_event_duration_liquidity_clock_4h_v1",
            ],
        )

    def test_trendexpansion_event_duration_clock_source_reuses_shifted_duration_logic(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["trendexpansion_event_duration_liquidity_clock"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="15m")

        self.assertIn(
            "factor_id: tomac_idxfut_clean_trendexpansion_event_duration_liquidity_clock_15m_v1",
            source,
        )
        self.assertIn(
            "branch_path: TrendExpansion -> EventDurationLiquidityClock -> ACDStyleDurationCompression -> "
            "ParentTrendAdmission -> tomac_idxfut_clean_trendexpansion_event_duration_liquidity_clock_15m_v1",
            source,
        )
        self.assertIn("event_duration_liquidity_clock", source)
        self.assertIn("event_clock_duration_proxy", source)
        self.assertIn("event_clock_trend_participation", source)
        self.assertIn("event_duration_parent_admission_long", source)
        self.assertIn("event_duration_parent_admission_short", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertIn("exit_raw.shift(1)", source)
        self.assertIn("short_exit_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)

    def test_three_minute_timeframe_resamples_for_independent_factor_coverage(self) -> None:
        module = self.load_module()

        self.assertEqual(module.freq_for_timeframe("3m"), "3min")

        frame = pd.DataFrame(
            {
                "date": pd.date_range("2026-01-01T00:00:00Z", periods=6, freq="1min"),
                "open": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                "high": [1.5, 2.5, 3.5, 4.5, 5.5, 6.5],
                "low": [0.5, 1.5, 2.5, 3.5, 4.5, 5.5],
                "close": [1.2, 2.2, 3.2, 4.2, 5.2, 6.2],
                "volume": [10, 20, 30, 40, 50, 60],
            }
        )

        out = module.resample_clean_ohlcv(frame, "3m")

        self.assertEqual(len(out), 2)
        self.assertEqual(out.loc[0, "open"], 1.0)
        self.assertEqual(out.loc[0, "high"], 3.5)
        self.assertEqual(out.loc[0, "low"], 0.5)
        self.assertEqual(out.loc[0, "close"], 3.2)
        self.assertEqual(out.loc[0, "volume"], 60)

    def test_aroon_band_acceptance_trendbirth_registers_independent_timeframes(self) -> None:
        module = self.load_module()

        specs = module.candidate_specs(families=["aroon_band_acceptance_trendbirth"])

        self.assertEqual(len(specs), 1)
        spec = specs[0]
        self.assertEqual(spec.class_prefix, "AroonBandAcceptanceTrendbirth")
        self.assertEqual(spec.direction, "long_short")
        self.assertEqual(
            spec.branch_path,
            "RegimeTransition -> TrendExpansionOnly -> ClosedBarTrendBirth -> AroonBandAcceptance",
        )
        self.assertEqual(
            [spec.factor_id(timeframe) for timeframe in ("1m", "3m", "5m", "15m", "30m", "1h", "4h")],
            [
                "aroon_band_acceptance_trendbirth_1m_v8",
                "aroon_band_acceptance_trendbirth_3m_v8",
                "aroon_band_acceptance_trendbirth_5m_v8",
                "aroon_band_acceptance_trendbirth_15m_v8",
                "aroon_band_acceptance_trendbirth_30m_v8",
                "aroon_band_acceptance_trendbirth_1h_v8",
                "aroon_band_acceptance_trendbirth_4h_v8",
            ],
        )

    def test_aroon_band_acceptance_trendbirth_source_uses_shifted_band_acceptance(self) -> None:
        module = self.load_module()
        spec = module.candidate_specs(families=["aroon_band_acceptance_trendbirth"])[0]

        source = module.strategy_source(spec, symbol="NQ", timeframe="30m")

        self.assertIn("factor_id: aroon_band_acceptance_trendbirth_30m_v8", source)
        self.assertIn("TrendExpansionOnly", source)
        self.assertIn("ClosedBarTrendBirth", source)
        self.assertIn("AroonBandAcceptance", source)
        self.assertIn("aroon_trend_birth_long", source)
        self.assertIn("aroon_band_acceptance_long", source)
        self.assertIn("aroon_band_acceptance_short", source)
        self.assertIn("entry_raw.shift(1)", source)
        self.assertIn("short_entry_raw.shift(1)", source)
        self.assertNotIn("shift(-", source)


if __name__ == "__main__":
    unittest.main()
