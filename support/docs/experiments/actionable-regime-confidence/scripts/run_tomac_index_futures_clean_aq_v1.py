#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
BASE = REPO / "support/docs/experiments/actionable-regime-confidence"
TOMAC = Path("/Users/thrill3r/Downloads/Tomac")
AQ_REPO = Path("/Users/thrill3r/Auto-Quant")
AQ_PY = AQ_REPO / ".venv/bin/python"
if not AQ_PY.exists():
    AQ_PY = Path("python3")
RESEARCH_SCRIPT_DIR = REPO / "support/scripts/research"
if str(RESEARCH_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(RESEARCH_SCRIPT_DIR))
from instrument_cost_model import (  # noqa: E402
    futures_cost_profile,
    normalize_futures_root,
    product_label_for_symbol,
)

STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
DEFAULT_ROOT = Path("/tmp") / f"ict-engine-tomac-index-futures-clean-aq-{STAMP}"
DEFAULT_COMPACT_ROOT = BASE / "runs" / f"{STAMP}-codex-tomac-index-futures-clean-aq-v1"
DEFAULT_START = "2021-01-01"
DEFAULT_END = "2025-12-31"
DEFAULT_TIMEFRAMES = ("1m", "5m", "15m", "30m", "1h", "4h", "1d")
MONTH_CODES = "FGHJKMNQUVXZ"
CONTRACT_ROOT_ALIASES = {
    "XAU": "GC",
}
SESSIONS_2021_2025 = 1260
SESSION_SCOPE = "ETH/full_retained_session"
RTH_FILTER_APPLIED = False
RTH_START_UTC_MINUTE = 13 * 60 + 30
RTH_END_UTC_MINUTE = 21 * 60


def has_pyarrow() -> bool:
    try:
        import pyarrow  # noqa: F401
    except Exception:
        return False
    return True


def pyarrow_runtime_reexec_argv(
    *,
    current_executable: Path,
    preferred_python: Path,
    argv: list[str],
    pyarrow_available: bool,
    script_path: Path,
) -> list[str] | None:
    if pyarrow_available or not preferred_python.exists():
        return None
    if current_executable.resolve() == preferred_python.resolve():
        return None
    return [str(preferred_python), str(script_path), *argv[1:]]


def ensure_pyarrow_runtime() -> None:
    reexec_argv = pyarrow_runtime_reexec_argv(
        current_executable=Path(sys.executable),
        preferred_python=AQ_PY,
        argv=sys.argv,
        pyarrow_available=has_pyarrow(),
        script_path=Path(__file__).resolve(),
    )
    if reexec_argv is not None:
        os.execv(reexec_argv[0], reexec_argv)


@dataclass(frozen=True)
class TomacSource:
    symbol: str
    source_csv: Path
    schema: str = "databento_parent_ohlcv_1m"


@dataclass(frozen=True)
class CandidateSpec:
    key: str
    class_prefix: str
    main_regime: str
    sub_regime: str
    profit_factor: str
    direction: str
    roi: float
    stoploss: float
    trailing_positive: float
    trailing_offset: float
    child_profit_factor: str | None = None
    extra_profit_factors: tuple[str, ...] = ()

    @property
    def branch_path(self) -> str:
        segments = [self.main_regime, self.sub_regime, self.profit_factor]
        if self.child_profit_factor:
            segments.append(self.child_profit_factor)
        segments.extend(self.extra_profit_factors)
        return " -> ".join(segments)

    def factor_id(self, timeframe: str) -> str:
        return f"tomac_idxfut_clean_{self.key}_{timeframe}_v1"

    def branch_path_with_factor(self, timeframe: str) -> str:
        return f"{self.branch_path} -> {self.factor_id(timeframe)}"


@dataclass(frozen=True)
class GeneratedStrategySpec:
    class_name: str
    symbol: str
    timeframe: str
    factor_id: str
    branch_path: str
    family: str
    direction: str


def source_universe() -> list[TomacSource]:
    return [
        TomacSource(
            symbol="ES",
            source_csv=TOMAC / "es future 2021-2025/glbx-mdp3-20100606-20260403.ohlcv-1m.csv",
        ),
        TomacSource(
            symbol="YM",
            source_csv=TOMAC / "ym future 2021-2025/glbx-mdp3-20110101-20251231.ohlcv-1m.csv",
        ),
        TomacSource(
            symbol="NQ",
            source_csv=TOMAC / "nq future 2021-2025/glbx-mdp3-20100606-20260403.ohlcv-1m.csv",
        ),
        TomacSource(
            symbol="6E",
            source_csv=TOMAC / "eur future 2015-2025/glbx-mdp3-20150101-20251231.ohlcv-1m.csv",
        ),
        TomacSource(
            symbol="XAU",
            source_csv=TOMAC / "xau future 2021-2025/glbx-mdp3-20210106-20260105.ohlcv-1m.csv",
        ),
    ]


def candidate_specs(families: list[str] | None = None) -> list[CandidateSpec]:
    specs = [
        CandidateSpec(
            key="opening_drive_rvol_vwap_continuation",
            class_prefix="OpeningDriveRvolVwapContinuation",
            main_regime="TrendExpansion",
            sub_regime="SessionLiquidity",
            profit_factor="OpeningDriveRvolVwapContinuation",
            direction="long",
            roi=0.0060,
            stoploss=-0.0065,
            trailing_positive=0.0015,
            trailing_offset=0.0045,
        ),
        CandidateSpec(
            key="opening_drive_breakout",
            class_prefix="OpeningDriveBreakout",
            main_regime="TrendExpansion",
            sub_regime="OpeningDriveBreakout",
            profit_factor="OpeningDriveBreakout",
            direction="long",
            roi=0.0070,
            stoploss=-0.0062,
            trailing_positive=0.0018,
            trailing_offset=0.0052,
        ),
        CandidateSpec(
            key="opening_drive_twoleg_continuation_exit_persistence",
            class_prefix="OpeningDriveTwoLegContinuationExitPersistence",
            main_regime="TrendExpansion",
            sub_regime="OpeningDriveExpansion",
            profit_factor="OpeningDriveTwoLegContinuation",
            child_profit_factor="ExitPersistence",
            direction="long",
            roi=0.0084,
            stoploss=-0.0058,
            trailing_positive=0.0020,
            trailing_offset=0.0058,
        ),
        CandidateSpec(
            key="vwap_washout_reclaim",
            class_prefix="VwapWashoutReclaim",
            main_regime="RangeReversion",
            sub_regime="VwapStretch",
            profit_factor="VwapWashoutReclaim",
            direction="long",
            roi=0.0045,
            stoploss=-0.0055,
            trailing_positive=0.0012,
            trailing_offset=0.0038,
        ),
        CandidateSpec(
            key="camarilla_r3_s3_reclaim",
            class_prefix="CamarillaR3S3Reclaim",
            main_regime="RangeReversion",
            sub_regime="CamarillaPivotReclaim",
            profit_factor="camarilla_r3_s3_reclaim_v1",
            direction="long_short",
            roi=0.0058,
            stoploss=-0.0058,
            trailing_positive=0.0014,
            trailing_offset=0.0044,
        ),
        CandidateSpec(
            key="vwap_reclaim_persistence",
            class_prefix="VwapReclaimPersistence",
            main_regime="RangeTransition",
            sub_regime="VWAPMeanReclaim",
            profit_factor="VwapReclaimPersistence",
            direction="long",
            roi=0.0052,
            stoploss=-0.0058,
            trailing_positive=0.0014,
            trailing_offset=0.0042,
        ),
        CandidateSpec(
            key="vwap_reclaim_persistence_killzone_filter",
            class_prefix="VwapReclaimPersistenceKillzoneFilter",
            main_regime="RangeTransition",
            sub_regime="VWAPMeanReclaim",
            profit_factor="VwapReclaimPersistence",
            child_profit_factor="KillzoneFilter",
            direction="long",
            roi=0.0054,
            stoploss=-0.0057,
            trailing_positive=0.0014,
            trailing_offset=0.0042,
        ),
        CandidateSpec(
            key="vwap_reclaim_rvol_trend_quality_filter",
            class_prefix="VwapReclaimRvolTrendQualityFilter",
            main_regime="RangeTransition",
            sub_regime="VWAPMeanReclaim",
            profit_factor="VwapReclaimPersistence",
            child_profit_factor="RvolTrendQualityFilter",
            direction="long_short",
            roi=0.0048,
            stoploss=-0.0058,
            trailing_positive=0.0012,
            trailing_offset=0.0038,
        ),
        CandidateSpec(
            key="midday_compression_failed_break_vwap_fade",
            class_prefix="MiddayCompressionFailedBreakVwapFade",
            main_regime="IndexFutures",
            sub_regime="IntradayRangeCompression",
            profit_factor="MiddayCompression",
            child_profit_factor="FailedBreakAuctionFade",
            extra_profit_factors=("VwapReversionPersistence",),
            direction="long_short",
            roi=0.0046,
            stoploss=-0.0048,
            trailing_positive=0.0011,
            trailing_offset=0.0034,
        ),
        CandidateSpec(
            key="lunch_liquidity_vacuum_vwap_magnet_reversal",
            class_prefix="LunchLiquidityVacuumVwapMagnetReversal",
            main_regime="SessionRhythm",
            sub_regime="LunchLiquidityVacuum",
            profit_factor="VwapMagnetReversal",
            direction="long_short",
            roi=0.0048,
            stoploss=-0.0048,
            trailing_positive=0.0011,
            trailing_offset=0.0036,
        ),
        CandidateSpec(
            key="compression_breakout_continuation",
            class_prefix="CompressionBreakoutContinuation",
            main_regime="RangeConsolidation",
            sub_regime="VolatilityCompression",
            profit_factor="CompressionBreakoutContinuation",
            direction="long",
            roi=0.0055,
            stoploss=-0.0060,
            trailing_positive=0.0013,
            trailing_offset=0.0040,
        ),
        CandidateSpec(
            key="donchian_turtle_breakout",
            class_prefix="DonchianTurtleBreakout",
            main_regime="TrendExpansion",
            sub_regime="BreakoutPersistence",
            profit_factor="DonchianTurtleBreakout",
            direction="long",
            roi=0.0080,
            stoploss=-0.0085,
            trailing_positive=0.0020,
            trailing_offset=0.0060,
        ),
        CandidateSpec(
            key="dense_trend_pullback_reclaim",
            class_prefix="DenseTrendPullbackReclaim",
            main_regime="TrendExpansion",
            sub_regime="PullbackReclaim",
            profit_factor="DenseTrendPullbackReclaim",
            direction="long",
            roi=0.0072,
            stoploss=-0.0072,
            trailing_positive=0.0018,
            trailing_offset=0.0054,
        ),
        CandidateSpec(
            key="prior_day_extreme_continuation",
            class_prefix="PriorDayExtremeContinuation",
            main_regime="TrendExpansion",
            sub_regime="PriorDayExtremeContinuation",
            profit_factor="PriorDayExtremeContinuation",
            direction="long",
            roi=0.0080,
            stoploss=-0.0072,
            trailing_positive=0.0019,
            trailing_offset=0.0058,
        ),
        CandidateSpec(
            key="prior_day_extreme_continuation_mtf_resonance_guard",
            class_prefix="PriorDayExtremeContinuationMtfResonanceGuard",
            main_regime="TrendExpansion",
            sub_regime="PriorDayExtremeContinuation",
            profit_factor="PriorDayExtremeContinuationMtfResonanceGuard",
            direction="long",
            roi=0.0084,
            stoploss=-0.0070,
            trailing_positive=0.0020,
            trailing_offset=0.0060,
        ),
        CandidateSpec(
            key="prior_day_extreme_continuation_mtf_resonance_guard_exit_persistence",
            class_prefix="PriorDayExtremeContinuationMtfResonanceGuardExitPersistence",
            main_regime="TrendExpansion",
            sub_regime="PriorDayExtremeContinuation",
            profit_factor="PriorDayExtremeContinuationMtfResonanceGuard",
            child_profit_factor="ExitPersistence",
            direction="long",
            roi=0.0102,
            stoploss=-0.0066,
            trailing_positive=0.0022,
            trailing_offset=0.0066,
        ),
        CandidateSpec(
            key="prior_day_extreme_continuation_mtf_resonance_guard_cusum_deadzone_gate",
            class_prefix="PriorDayExtremeContinuationMtfResonanceGuardCusumDeadzoneGate",
            main_regime="TrendExpansion",
            sub_regime="PriorDayExtremeContinuation",
            profit_factor="PriorDayExtremeContinuationMtfResonanceGuard",
            child_profit_factor="CusumDeadzoneGate",
            direction="long",
            roi=0.0094,
            stoploss=-0.0068,
            trailing_positive=0.0021,
            trailing_offset=0.0062,
        ),
        CandidateSpec(
            key="prior_day_extreme_continuation_mtf_resonance_guard_killzone_filter",
            class_prefix="PriorDayExtremeContinuationMtfResonanceGuardKillzoneFilter",
            main_regime="TrendExpansion",
            sub_regime="PriorDayExtremeContinuation",
            profit_factor="PriorDayExtremeContinuationMtfResonanceGuard",
            child_profit_factor="KillzoneFilter",
            direction="long",
            roi=0.0098,
            stoploss=-0.0068,
            trailing_positive=0.0021,
            trailing_offset=0.0064,
        ),
        CandidateSpec(
            key="prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard",
            class_prefix="PriorDayExtremeContinuationMtfResonanceGuardParticipationQualityGuard",
            main_regime="TrendExpansion",
            sub_regime="PriorDayExtremeContinuation",
            profit_factor="PriorDayExtremeContinuationMtfResonanceGuard",
            child_profit_factor="ParticipationQualityGuard",
            direction="long",
            roi=0.0092,
            stoploss=-0.0064,
            trailing_positive=0.0020,
            trailing_offset=0.0060,
        ),
        CandidateSpec(
            key="prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard_nq_cadence_lift",
            class_prefix="PriorDayExtremeContinuationMtfResonanceGuardParticipationQualityGuardNqCadenceLift",
            main_regime="TrendExpansion",
            sub_regime="PriorDayExtremeContinuation",
            profit_factor="PriorDayExtremeContinuationMtfResonanceGuard",
            child_profit_factor="ParticipationQualityGuard",
            extra_profit_factors=("NQCadenceLift",),
            direction="long",
            roi=0.0088,
            stoploss=-0.0062,
            trailing_positive=0.0019,
            trailing_offset=0.0058,
        ),
        CandidateSpec(
            key="prior_day_liquidity_sweep_reversal",
            class_prefix="PriorDayLiquiditySweepReversal",
            main_regime="RangeReversion",
            sub_regime="PriorDayLiquiditySweepReversal",
            profit_factor="PdlSweepReclaim",
            direction="long",
            roi=0.0068,
            stoploss=-0.0060,
            trailing_positive=0.0016,
            trailing_offset=0.0048,
        ),
        CandidateSpec(
            key="prior_day_multifactor_confluence_volume_reclaim",
            class_prefix="PriorDayMultiFactorConfluenceVolumeReclaim",
            main_regime="RangeReversion",
            sub_regime="PriorDayLiquiditySweepReversal",
            profit_factor="MultiFactorConfluenceReclaim",
            child_profit_factor="VolumeConfirmation",
            direction="long_short",
            roi=0.0072,
            stoploss=-0.0058,
            trailing_positive=0.0018,
            trailing_offset=0.0050,
        ),
        CandidateSpec(
            key="impulse_follow",
            class_prefix="ImpulseFollowThrough",
            main_regime="TrendExpansion",
            sub_regime="ImpulseFollowThrough",
            profit_factor="ImpulseFollowThrough",
            direction="long",
            roi=0.0088,
            stoploss=-0.0070,
            trailing_positive=0.0021,
            trailing_offset=0.0060,
        ),
        CandidateSpec(
            key="impulse_follow_hold_persistence",
            class_prefix="ImpulseFollowHoldPersistence",
            main_regime="TrendExpansion",
            sub_regime="ImpulseFollowThrough",
            profit_factor="HoldPersistence",
            direction="long",
            roi=0.0084,
            stoploss=-0.0068,
            trailing_positive=0.0020,
            trailing_offset=0.0058,
        ),
        CandidateSpec(
            key="wpr_extreme_mean_reclaim",
            class_prefix="WprExtremeMeanReclaim",
            main_regime="TrendExpansion",
            sub_regime="WprExtremePullback",
            profit_factor="MeanReclaim",
            direction="long",
            roi=0.0074,
            stoploss=-0.0066,
            trailing_positive=0.0018,
            trailing_offset=0.0052,
        ),
        CandidateSpec(
            key="wpr_fractal_no_be_fulltarget",
            class_prefix="WprFractalNoBeFullTarget",
            main_regime="RangeReversion",
            sub_regime="PdhPdlFractalLiquiditySweep",
            profit_factor="WprFractalNoBreakEvenFullTarget",
            direction="long_short",
            roi=0.0072,
            stoploss=-0.0064,
            trailing_positive=0.0018,
            trailing_offset=0.0052,
        ),
        CandidateSpec(
            key="wpr_fractal_no_be_session_bias_cap",
            class_prefix="WprFractalNoBeSessionBiasCap",
            main_regime="RangeReversion",
            sub_regime="PdhPdlFractalLiquiditySweep",
            profit_factor="WprFractalNoBreakEvenFullTarget",
            child_profit_factor="SessionBiasCap",
            direction="long",
            roi=0.0074,
            stoploss=-0.0064,
            trailing_positive=0.0018,
            trailing_offset=0.0052,
        ),
        CandidateSpec(
            key="wpr_fractal_no_be_higher_frame_slope_confirm",
            class_prefix="WprFractalNoBeHigherFrameSlopeConfirm",
            main_regime="RangeReversion",
            sub_regime="PdhPdlFractalLiquiditySweep",
            profit_factor="WprFractalNoBreakEvenFullTarget",
            child_profit_factor="HigherFrameSlopeConfirm",
            direction="long",
            roi=0.0075,
            stoploss=-0.0062,
            trailing_positive=0.0019,
            trailing_offset=0.0053,
        ),
        CandidateSpec(
            key="wpr_fractal_ict_zone_reclaim",
            class_prefix="WprFractalIctZoneReclaim",
            main_regime="RangeReversion",
            sub_regime="PdhPdlFractalLiquiditySweep",
            profit_factor="WprFractalIctZoneReclaim",
            direction="long_short",
            roi=0.0076,
            stoploss=-0.0064,
            trailing_positive=0.0018,
            trailing_offset=0.0052,
        ),
        CandidateSpec(
            key="wpr_adx_fractal_sweep_reclaim",
            class_prefix="WprAdxFractalSweepReclaim",
            main_regime="RangeReversion",
            sub_regime="PdhPdlFractalLiquiditySweep",
            profit_factor="WprAdxTrendAlignedReclaim",
            direction="long_short",
            roi=0.0072,
            stoploss=-0.0064,
            trailing_positive=0.0018,
            trailing_offset=0.0052,
        ),
        CandidateSpec(
            key="wpr_adx_hurst_profile_mss_reclaim",
            class_prefix="WprAdxHurstProfileMssReclaim",
            main_regime="RangeReversion",
            sub_regime="PdhPdlFractalLiquiditySweep",
            profit_factor="WprAdxTrendAlignedReclaim",
            child_profit_factor="HurstProfileMssReclaim",
            direction="long_short",
            roi=0.0068,
            stoploss=-0.0058,
            trailing_positive=0.0016,
            trailing_offset=0.0048,
        ),
        CandidateSpec(
            key="value_area_vpoc_htf_trend_mss_filter",
            class_prefix="ValueAreaVpocHtfTrendMssFilter",
            main_regime="RangeTransition",
            sub_regime="MarketProfileValueAreaAcceptance",
            profit_factor="VpocReclaimContinuation",
            child_profit_factor="HtfTrendResonanceMssFilter",
            direction="long_short",
            roi=0.0074,
            stoploss=-0.0060,
            trailing_positive=0.0018,
            trailing_offset=0.0052,
        ),
        CandidateSpec(
            key="nr7_range_expansion",
            class_prefix="Nr7RangeExpansion",
            main_regime="RangeConsolidation",
            sub_regime="NarrowRangeCompression",
            profit_factor="Nr7RangeExpansion",
            direction="long",
            roi=0.0070,
            stoploss=-0.0075,
            trailing_positive=0.0018,
            trailing_offset=0.0055,
        ),
        CandidateSpec(
            key="nr7_range_expansion_excursion_cap",
            class_prefix="Nr7RangeExpansionExcursionCap",
            main_regime="RangeConsolidation",
            sub_regime="NarrowRangeCompression",
            profit_factor="Nr7RangeExpansion",
            child_profit_factor="ExcursionCap",
            direction="long",
            roi=0.0074,
            stoploss=-0.0060,
            trailing_positive=0.0018,
            trailing_offset=0.0052,
        ),
        CandidateSpec(
            key="nr7_range_expansion_vwap_hold_persistence",
            class_prefix="Nr7RangeExpansionVwapHoldPersistence",
            main_regime="RangeConsolidation",
            sub_regime="NarrowRangeCompression",
            profit_factor="Nr7RangeExpansion",
            child_profit_factor="VwapHoldPersistence",
            direction="long",
            roi=0.0072,
            stoploss=-0.0062,
            trailing_positive=0.0018,
            trailing_offset=0.0051,
        ),
        CandidateSpec(
            key="nr7_range_expansion_killzone_filter",
            class_prefix="Nr7RangeExpansionKillzoneFilter",
            main_regime="RangeConsolidation",
            sub_regime="NarrowRangeCompression",
            profit_factor="Nr7RangeExpansion",
            child_profit_factor="KillzoneFilter",
            direction="long",
            roi=0.0071,
            stoploss=-0.0063,
            trailing_positive=0.0018,
            trailing_offset=0.0051,
        ),
        CandidateSpec(
            key="crabel_nr7_intraday_expansion_continuation",
            class_prefix="CrabelNr7IntradayExpansionContinuation",
            main_regime="VolatilityCompressionExpansion",
            sub_regime="CrabelNR7",
            profit_factor="Nr7CrabelExpansion",
            child_profit_factor="IntradayExpansionContinuation",
            direction="long",
            roi=0.0076,
            stoploss=-0.0062,
            trailing_positive=0.0019,
            trailing_offset=0.0054,
        ),
        CandidateSpec(
            key="supertrend_adx_displacement",
            class_prefix="SupertrendAdxDisplacement",
            main_regime="TrendExpansion",
            sub_regime="SuperTrendAdxDisplacement",
            profit_factor="TrendPullbackOrLiquiditySweepReclaim",
            direction="long",
            roi=0.0075,
            stoploss=-0.0075,
            trailing_positive=0.0018,
            trailing_offset=0.0055,
        ),
        CandidateSpec(
            key="supertrend_adx_turtle_soup_sweep_reversal",
            class_prefix="SupertrendAdxTurtleSoupSweepReversal",
            main_regime="TrendExpansion",
            sub_regime="SuperTrendAdxDisplacement",
            profit_factor="TurtleSoupSweepReversal",
            direction="long",
            roi=0.0082,
            stoploss=-0.0072,
            trailing_positive=0.0019,
            trailing_offset=0.0058,
        ),
        CandidateSpec(
            key="supertrend_adx_pullback_reclaim",
            class_prefix="SupertrendAdxPullbackReclaim",
            main_regime="TrendExpansion",
            sub_regime="SuperTrendAdxDisplacement",
            profit_factor="TrendPullbackReclaim",
            direction="long",
            roi=0.0070,
            stoploss=-0.0070,
            trailing_positive=0.0017,
            trailing_offset=0.0050,
        ),
        CandidateSpec(
            key="supertrend_adx_liquidity_sweep_reclaim",
            class_prefix="SupertrendAdxLiquiditySweepReclaim",
            main_regime="TrendExpansion",
            sub_regime="SuperTrendAdxDisplacement",
            profit_factor="LiquiditySweepReclaim",
            direction="long",
            roi=0.0080,
            stoploss=-0.0078,
            trailing_positive=0.0019,
            trailing_offset=0.0058,
        ),
        CandidateSpec(
            key="supertrend_adx_pullback_ote_fvg_ob",
            class_prefix="SupertrendAdxPullbackOteFvgOb",
            main_regime="TrendExpansion",
            sub_regime="SuperTrendAdxDisplacement",
            profit_factor="TrendPullbackReclaimOteFvgOb",
            direction="long",
            roi=0.0078,
            stoploss=-0.0068,
            trailing_positive=0.0019,
            trailing_offset=0.0056,
        ),
        CandidateSpec(
            key="supertrend_adx_pullback_exit_persistence",
            class_prefix="SupertrendAdxPullbackExitPersistence",
            main_regime="TrendExpansion",
            sub_regime="SuperTrendAdxDisplacement",
            profit_factor="TrendPullbackReclaimExitPersistence",
            direction="long",
            roi=0.0074,
            stoploss=-0.0070,
            trailing_positive=0.0018,
            trailing_offset=0.0054,
        ),
        CandidateSpec(
            key="supertrend_adx_pullback_exit_persistence_high_conviction",
            class_prefix="SupertrendAdxPullbackExitPersistenceHighConviction",
            main_regime="TrendExpansion",
            sub_regime="SuperTrendAdxDisplacement",
            profit_factor="TrendPullbackReclaimExitPersistenceHighConviction",
            direction="long",
            roi=0.0090,
            stoploss=-0.0064,
            trailing_positive=0.0022,
            trailing_offset=0.0064,
        ),
        CandidateSpec(
            key="supertrend_adx_pullback_exit_persistence_opening_drive",
            class_prefix="SupertrendAdxPullbackExitPersistenceOpeningDrive",
            main_regime="TrendExpansion",
            sub_regime="SuperTrendAdxDisplacement",
            profit_factor="TrendPullbackReclaimExitPersistenceOpeningDrive",
            direction="long",
            roi=0.0095,
            stoploss=-0.0066,
            trailing_positive=0.0024,
            trailing_offset=0.0068,
        ),
        CandidateSpec(
            key="supertrend_adx_pullback_exit_persistence_opening_drive_soft",
            class_prefix="SupertrendAdxPullbackExitPersistenceOpeningDriveSoft",
            main_regime="TrendExpansion",
            sub_regime="SuperTrendAdxDisplacement",
            profit_factor="TrendPullbackReclaimExitPersistenceOpeningDriveSoft",
            direction="long",
            roi=0.0084,
            stoploss=-0.0068,
            trailing_positive=0.0020,
            trailing_offset=0.0060,
        ),
        CandidateSpec(
            key="supertrend_adx_pullback_exit_persistence_vwap_excursion_cap",
            class_prefix="SupertrendAdxPullbackExitPersistenceVwapExcursionCap",
            main_regime="TrendExpansion",
            sub_regime="SuperTrendAdxDisplacement",
            profit_factor="TrendPullbackReclaimExitPersistenceVwapExcursionCap",
            direction="long",
            roi=0.0080,
            stoploss=-0.0069,
            trailing_positive=0.0019,
            trailing_offset=0.0058,
        ),
        CandidateSpec(
            key="mass_index_vortex_trend_continuation",
            class_prefix="MassIndexVortexTrendContinuation",
            main_regime="TrendExpansion",
            sub_regime="VolatilityExpansionTrend",
            profit_factor="MassIndexBulge",
            child_profit_factor="VortexDirectionalContinuation",
            direction="long",
            roi=0.0082,
            stoploss=-0.0068,
            trailing_positive=0.0020,
            trailing_offset=0.0058,
        ),
        CandidateSpec(
            key="aroon_cci_trend_continuation",
            class_prefix="AroonCciTrendContinuation",
            main_regime="TrendExpansion",
            sub_regime="DirectionalPersistence",
            profit_factor="AroonCciTrendContinuation",
            direction="long",
            roi=0.0078,
            stoploss=-0.0066,
            trailing_positive=0.0019,
            trailing_offset=0.0056,
        ),
        CandidateSpec(
            key="aroon_cci_cadence_lift_symbol_guard",
            class_prefix="AroonCciCadenceLiftSymbolGuard",
            main_regime="TrendExpansion",
            sub_regime="DirectionalPersistence",
            profit_factor="AroonCciTrendContinuation",
            child_profit_factor="CadenceLiftSymbolGuard",
            direction="long",
            roi=0.0072,
            stoploss=-0.0064,
            trailing_positive=0.0017,
            trailing_offset=0.0052,
        ),
        CandidateSpec(
            key="connors_rsi2_rebound",
            class_prefix="ConnorsRsi2Rebound",
            main_regime="RangeReversion",
            sub_regime="ExhaustionWashout",
            profit_factor="ConnorsRsi2Rebound",
            direction="long",
            roi=0.0055,
            stoploss=-0.0065,
            trailing_positive=0.0015,
            trailing_offset=0.0045,
        ),
        CandidateSpec(
            key="ultimate_ict_zone_volume_spike_reclaim",
            class_prefix="UltimateIctZoneVolumeSpikeReclaim",
            main_regime="RangeReversion",
            sub_regime="KillzoneLiquiditySweep",
            profit_factor="IctZoneVolumeSpikeReclaim",
            direction="long",
            roi=0.0068,
            stoploss=-0.0060,
            trailing_positive=0.0016,
            trailing_offset=0.0048,
        ),
        CandidateSpec(
            key="ultimate_ict_zone_volume_spike_exit_persistence",
            class_prefix="UltimateIctZoneVolumeSpikeExitPersistence",
            main_regime="RangeReversion",
            sub_regime="KillzoneLiquiditySweep",
            profit_factor="IctZoneVolumeSpikeReclaim",
            child_profit_factor="ExitPersistence",
            direction="long",
            roi=0.0082,
            stoploss=-0.0064,
            trailing_positive=0.0019,
            trailing_offset=0.0056,
        ),
        CandidateSpec(
            key="ultimate_ict_zone_volume_spike_session_open_bias_cap",
            class_prefix="UltimateIctZoneVolumeSpikeSessionOpenBiasCap",
            main_regime="RangeReversion",
            sub_regime="KillzoneLiquiditySweep",
            profit_factor="IctZoneVolumeSpikeReclaim",
            child_profit_factor="SessionOpenBiasCap",
            direction="long",
            roi=0.0076,
            stoploss=-0.0062,
            trailing_positive=0.0018,
            trailing_offset=0.0052,
        ),
        CandidateSpec(
            key="ultimate_ict_zone_volume_spike_vwap_hold_persistence",
            class_prefix="UltimateIctZoneVolumeSpikeVwapHoldPersistence",
            main_regime="RangeReversion",
            sub_regime="KillzoneLiquiditySweep",
            profit_factor="IctZoneVolumeSpikeReclaim",
            child_profit_factor="VwapHoldPersistence",
            direction="long",
            roi=0.0079,
            stoploss=-0.0063,
            trailing_positive=0.0018,
            trailing_offset=0.0054,
        ),
        CandidateSpec(
            key="ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence",
            class_prefix="UltimateIctZoneVolumeSpikeSessionOpenBiasCapVwapHoldPersistence",
            main_regime="RangeReversion",
            sub_regime="KillzoneLiquiditySweep",
            profit_factor="IctZoneVolumeSpikeReclaim",
            child_profit_factor="SessionOpenBiasCap",
            extra_profit_factors=("VwapHoldPersistence",),
            direction="long",
            roi=0.0081,
            stoploss=-0.0061,
            trailing_positive=0.0019,
            trailing_offset=0.0055,
        ),
        CandidateSpec(
            key="ote_liquidity_sweep_fvg_ob_reclaim",
            class_prefix="OteLiquiditySweepFvgObReclaim",
            main_regime="TrendExpansion",
            sub_regime="OteLiquiditySweepReclaim",
            profit_factor="FvgObReentry",
            direction="long",
            roi=0.0078,
            stoploss=-0.0068,
            trailing_positive=0.0019,
            trailing_offset=0.0056,
        ),
        CandidateSpec(
            key="ote_fvg_order_block_reclaim_session_directional_bias",
            class_prefix="OteFvgOrderBlockReclaimSessionDirectionalBias",
            main_regime="RangeReversion",
            sub_regime="LiquiditySweepIctRetracement",
            profit_factor="OteFvgOrderBlockReclaim",
            child_profit_factor="SessionDirectionalBias",
            direction="long_short",
            roi=0.0074,
            stoploss=-0.0062,
            trailing_positive=0.0018,
            trailing_offset=0.0052,
        ),
        CandidateSpec(
            key="h4_midnight_macd_rsi_pullback",
            class_prefix="H4MidnightMacdRsiPullback",
            main_regime="TrendExpansion",
            sub_regime="H4StructureMidnightBias",
            profit_factor="MacdRsiPullback",
            direction="long",
            roi=0.0072,
            stoploss=-0.0068,
            trailing_positive=0.0018,
            trailing_offset=0.0052,
        ),
        CandidateSpec(
            key="h4_midnight_macd_rsi_pullback_session_cadence_guard",
            class_prefix="H4MidnightMacdRsiPullbackSessionCadenceGuard",
            main_regime="TrendExpansion",
            sub_regime="H4StructureMidnightBias",
            profit_factor="MacdRsiPullback",
            child_profit_factor="SessionCadenceGuard",
            direction="long",
            roi=0.0070,
            stoploss=-0.0066,
            trailing_positive=0.0018,
            trailing_offset=0.0051,
        ),
        CandidateSpec(
            key="liquidity_purge_rejection",
            class_prefix="LiquidityPurgeRejection",
            main_regime="RangeTransition",
            sub_regime="LiquidityPurgeRejection",
            profit_factor="KillzoneReversal",
            direction="long",
            roi=0.0066,
            stoploss=-0.0062,
            trailing_positive=0.0017,
            trailing_offset=0.0050,
        ),
        CandidateSpec(
            key="momentum_divergence_reclaim",
            class_prefix="MomentumDivergenceReclaim",
            main_regime="TrendExpansion",
            sub_regime="MomentumDivergence",
            profit_factor="DivergenceReclaim",
            direction="long",
            roi=0.0070,
            stoploss=-0.0066,
            trailing_positive=0.0017,
            trailing_offset=0.0052,
        ),
        CandidateSpec(
            key="fractal_liquidity_macd_rsi_divergence_reclaim",
            class_prefix="FractalLiquidityMacdRsiDivergenceReclaim",
            main_regime="RangeReversion",
            sub_regime="FractalLiquiditySweep",
            profit_factor="MacdRsiDivergenceReclaim",
            direction="long",
            roi=0.0072,
            stoploss=-0.0068,
            trailing_positive=0.0018,
            trailing_offset=0.0054,
        ),
        CandidateSpec(
            key="fractal_liquidity_macd_divergence_reclaim",
            class_prefix="FractalLiquidityMacdDivergenceReclaim",
            main_regime="RangeReversion",
            sub_regime="FractalLiquiditySweep",
            profit_factor="MacdDivergenceReclaim",
            direction="long",
            roi=0.0072,
            stoploss=-0.0068,
            trailing_positive=0.0018,
            trailing_offset=0.0054,
        ),
        CandidateSpec(
            key="midnight_open_liquidity_sweep_macd_divergence_reclaim",
            class_prefix="MidnightOpenLiquiditySweepMacdDivergenceReclaim",
            main_regime="RangeReversion",
            sub_regime="MidnightOpenDiscountPremiumBias",
            profit_factor="LiquiditySweepReclaim",
            child_profit_factor="MacdDivergenceReclaim",
            direction="long",
            roi=0.0073,
            stoploss=-0.0068,
            trailing_positive=0.0018,
            trailing_offset=0.0053,
        ),
        CandidateSpec(
            key="liquidity_sweep_adx_liquidity_pool_context",
            class_prefix="LiquiditySweepAdxLiquidityPoolContext",
            main_regime="TrendExpansion",
            sub_regime="LiquiditySweepDisplacement",
            profit_factor="AdxTrendStrengthReclaim",
            child_profit_factor="LiquidityPoolContextFilter",
            direction="long_short",
            roi=0.0073,
            stoploss=-0.0061,
            trailing_positive=0.0018,
            trailing_offset=0.0052,
        ),
        CandidateSpec(
            key="wpr_adx_reference_hurst_profile_range_compression_release",
            class_prefix="WprAdxReferenceHurstProfileRangeCompressionRelease",
            main_regime="RangeReversion",
            sub_regime="PdhPdlFractalLiquiditySweep",
            profit_factor="WprAdxTrendAlignedReclaim",
            child_profit_factor="HurstProfileMssReclaim",
            extra_profit_factors=("ReferenceHurstProfileRangeCompressionRelease",),
            direction="long",
            roi=0.0066,
            stoploss=-0.0059,
            trailing_positive=0.0015,
            trailing_offset=0.0047,
        ),
        CandidateSpec(
            key="silver_bullet_rsi_sniper",
            class_prefix="SilverBulletRsiSniper",
            main_regime="SessionRhythm",
            sub_regime="SilverBulletSniper",
            profit_factor="RsiAtrReversal",
            direction="long",
            roi=0.0068,
            stoploss=-0.0064,
            trailing_positive=0.0017,
            trailing_offset=0.0050,
        ),
        CandidateSpec(
            key="regression_channel_r2_slope_breadth",
            class_prefix="RegressionChannelR2SlopeBreadth",
            main_regime="TrendExpansion",
            sub_regime="RegressionChannelTrend",
            profit_factor="R2SlopePersistence",
            child_profit_factor="CrossIndexBreadthConfirmation",
            extra_profit_factors=("AtrStopHoldCompression",),
            direction="long",
            roi=0.0072,
            stoploss=-0.0061,
            trailing_positive=0.0018,
            trailing_offset=0.0054,
        ),
        CandidateSpec(
            key="session_window_sweep_reclaim",
            class_prefix="SessionWindowSweepReclaim",
            main_regime="SessionRhythm",
            sub_regime="KillzoneLiquiditySweep",
            profit_factor="SessionWindowSweepReclaim",
            direction="long",
            roi=0.0067,
            stoploss=-0.0063,
            trailing_positive=0.0017,
            trailing_offset=0.0051,
        ),
        CandidateSpec(
            key="tod_balanced_ym_late_session_cadence_addon",
            class_prefix="TodBalancedYMLateSessionCadenceAddon",
            main_regime="SessionRhythm",
            sub_regime="TimeOfDaySeasonality",
            profit_factor="BalancedAdaptiveSlotPortfolio",
            child_profit_factor="SparseMonthSlotCoverageExpansion",
            extra_profit_factors=("YMLateSessionCadenceAddOn",),
            direction="long",
            roi=0.0058,
            stoploss=-0.0060,
            trailing_positive=0.0015,
            trailing_offset=0.0046,
        ),
    ]
    if not families:
        return specs
    requested = set(families)
    selected = [spec for spec in specs if spec.key in requested]
    missing = sorted(requested.difference({spec.key for spec in specs}))
    if missing:
        raise ValueError(f"unknown candidate families: {','.join(missing)}")
    return selected


def is_outright_contract(contract: str, symbol: str) -> bool:
    text = str(contract or "").upper().strip()
    root_symbol = CONTRACT_ROOT_ALIASES.get(symbol.upper(), symbol.upper())
    root = re.escape(root_symbol)
    return re.fullmatch(rf"{root}[{MONTH_CODES}][0-9]{{1,2}}", text) is not None


def select_front_outright_rows(frame: pd.DataFrame, symbol: str) -> tuple[pd.DataFrame, dict[str, int]]:
    if frame.empty:
        return frame.copy(), {
            "input_rows": 0,
            "outright_rows": 0,
            "spread_rows_dropped": 0,
            "duplicate_timestamp_rows_dropped": 0,
        }

    work = frame.copy()
    if "date" not in work.columns:
        work["date"] = pd.to_datetime(work["ts_event"], utc=True)
    else:
        work["date"] = pd.to_datetime(work["date"], utc=True)
    work["contract"] = work["symbol"].astype(str).str.upper().str.strip()
    outright = work["contract"].map(lambda value: is_outright_contract(value, symbol))
    before = len(work)
    work = work.loc[outright].copy()
    spread_rows_dropped = before - len(work)
    if work.empty:
        return work, {
            "input_rows": int(before),
            "outright_rows": 0,
            "spread_rows_dropped": int(spread_rows_dropped),
            "duplicate_timestamp_rows_dropped": 0,
        }

    work["volume"] = pd.to_numeric(work["volume"], errors="coerce").fillna(0)
    for column in ("open", "high", "low", "close"):
        work[column] = pd.to_numeric(work[column], errors="coerce")
    work = work.dropna(subset=["date", "open", "high", "low", "close"])
    before_dedup = len(work)
    work = (
        work.sort_values(["date", "volume", "contract"], ascending=[True, False, True])
        .drop_duplicates(subset=["date"], keep="first")
        .sort_values("date")
        .reset_index(drop=True)
    )
    return work[["date", "contract", "open", "high", "low", "close", "volume"]].copy(), {
        "input_rows": int(before),
        "outright_rows": int(before_dedup),
        "spread_rows_dropped": int(spread_rows_dropped),
        "duplicate_timestamp_rows_dropped": int(before_dedup - len(work)),
    }


def back_adjust_rolls(frame: pd.DataFrame, *, symbol: str) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    if frame.empty:
        return frame.copy(), []

    work = frame.copy()
    work["date"] = pd.to_datetime(work["date"], utc=True)
    work = work.sort_values("date").reset_index(drop=True)
    for column in ("open", "high", "low", "close", "volume"):
        work[column] = pd.to_numeric(work[column], errors="coerce")
    work = work.dropna(subset=["date", "open", "high", "low", "close"]).reset_index(drop=True)

    cumulative_delta = 0.0
    ledger: list[dict[str, Any]] = []
    adjusted_rows: list[dict[str, Any]] = []
    previous_raw: pd.Series | None = None
    previous_contract: str | None = None

    for index, row in work.iterrows():
        contract = str(row["contract"])
        if previous_raw is not None and previous_contract != contract:
            boundary_delta = float(previous_raw["close"]) - float(row["open"])
            cumulative_delta += boundary_delta
            ledger.append(
                {
                    "symbol": symbol,
                    "roll_index": len(ledger) + 1,
                    "roll_time": row["date"].isoformat(),
                    "old_contract": previous_contract,
                    "new_contract": contract,
                    "prev_raw_close": float(previous_raw["close"]),
                    "new_raw_open": float(row["open"]),
                    "adjustment_delta": float(boundary_delta),
                    "cumulative_delta_after_roll": float(cumulative_delta),
                    "method": "boundary_prev_close_minus_new_open",
                    "future_lookahead": False,
                }
            )
        adjusted = row.to_dict()
        for column in ("open", "high", "low", "close"):
            adjusted[column] = float(row[column]) + cumulative_delta
        adjusted["raw_open"] = float(row["open"])
        adjusted["raw_high"] = float(row["high"])
        adjusted["raw_low"] = float(row["low"])
        adjusted["raw_close"] = float(row["close"])
        adjusted["roll_adjustment"] = float(cumulative_delta)
        adjusted_rows.append(adjusted)
        previous_raw = row
        previous_contract = contract

    adjusted_frame = pd.DataFrame(adjusted_rows)
    adjusted_frame = adjusted_frame[
        [
            "date",
            "contract",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "raw_open",
            "raw_high",
            "raw_low",
            "raw_close",
            "roll_adjustment",
        ]
    ]
    return adjusted_frame, ledger


def freq_for_timeframe(timeframe: str) -> str:
    mapping = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1h",
        "4h": "4h",
        "1d": "1D",
    }
    if timeframe not in mapping:
        raise ValueError(f"unsupported timeframe: {timeframe}")
    return mapping[timeframe]


def resample_clean_ohlcv(frame: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    work = frame.copy()
    work["date"] = pd.to_datetime(work["date"], utc=True)
    work = work.sort_values("date").set_index("date")
    freq = freq_for_timeframe(timeframe)
    out = work.resample(freq, label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    )
    out = out.dropna(subset=["open", "high", "low", "close"]).reset_index()
    return out[["date", "open", "high", "low", "close", "volume"]].copy()


def dense_calendar_for_aq(frame: pd.DataFrame, timeframe: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    if frame.empty:
        empty = frame[["date", "open", "high", "low", "close", "volume"]].copy()
        return empty, {
            "timeframe": timeframe,
            "input_rows": 0,
            "output_rows": 0,
            "filled_rows": 0,
            "method": "past_close_forward_fill_ohlc_volume_zero",
            "future_lookahead": False,
        }

    work = frame[["date", "open", "high", "low", "close", "volume"]].copy()
    work["date"] = pd.to_datetime(work["date"], utc=True)
    work = work.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    freq = freq_for_timeframe(timeframe)
    calendar = pd.date_range(work["date"].min(), work["date"].max(), freq=freq, tz="UTC")
    dense = work.set_index("date").reindex(calendar)
    missing = dense["close"].isna()
    past_close = dense["close"].ffill()
    for column in ("open", "high", "low", "close"):
        dense.loc[missing, column] = past_close.loc[missing]
    dense.loc[missing, "volume"] = 0.0
    dense = dense.dropna(subset=["open", "high", "low", "close"]).reset_index(names="date")
    dense = dense[["date", "open", "high", "low", "close", "volume"]].copy()
    dense["volume"] = pd.to_numeric(dense["volume"], errors="coerce").fillna(0)
    stats = {
        "timeframe": timeframe,
        "input_rows": int(len(work)),
        "output_rows": int(len(dense)),
        "filled_rows": int(missing.sum()),
        "method": "past_close_forward_fill_ohlc_volume_zero",
        "future_lookahead": False,
    }
    return dense, stats


def session_coverage_stats(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        outside_rth_rows = 0
        rth_rows = 0
        first_outside = None
        last_outside = None
    else:
        work = frame.copy()
        work["date"] = pd.to_datetime(work["date"], utc=True)
        minute_of_day = work["date"].dt.hour * 60 + work["date"].dt.minute
        rth_mask = minute_of_day.between(RTH_START_UTC_MINUTE, RTH_END_UTC_MINUTE - 1)
        outside = work.loc[~rth_mask]
        outside_rth_rows = int((~rth_mask).sum())
        rth_rows = int(rth_mask.sum())
        first_outside = outside["date"].min().isoformat() if len(outside) else None
        last_outside = outside["date"].max().isoformat() if len(outside) else None
    evidence = outside_rth_rows > 0
    return {
        "session_scope": SESSION_SCOPE,
        "rth_filter_applied": RTH_FILTER_APPLIED,
        "eth_full_retained_session_evidence": evidence,
        "eth_full_retained_coverage_status": "verified_retained_rows_outside_rth"
        if evidence
        else "session_scope_unverified_no_rows_outside_rth",
        "rth_1m_rows": rth_rows,
        "outside_rth_1m_rows": outside_rth_rows,
        "first_outside_rth_timestamp": first_outside,
        "last_outside_rth_timestamp": last_outside,
        "session_coverage_evidence": (
            f"{outside_rth_rows} selected 1m rows outside CME/CBOT equity-index RTH "
            f"window 13:30-21:00 UTC; no RTH filter applied."
        ),
    }


def clean_quality(frame: pd.DataFrame, *, symbol: str, timeframe: str) -> dict[str, Any]:
    if frame.empty:
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "rows": 0,
            "first": None,
            "last": None,
            "max_abs_return_pct": None,
            "gap_ratio": None,
            "large_return_gt_20pct_count": 0,
            "quality_ok": False,
        }
    work = frame.copy()
    work["date"] = pd.to_datetime(work["date"], utc=True)
    returns = work["close"].pct_change().abs().replace([float("inf")], pd.NA).dropna()
    deltas = work["date"].sort_values().diff().dropna()
    expected = pd.Timedelta(freq_for_timeframe(timeframe))
    if timeframe == "1d":
        gap_ratio = 0.0
    else:
        gap_ratio = float((deltas > expected * 3).mean()) if len(deltas) else 0.0
    max_abs = float(returns.max() * 100.0) if len(returns) else 0.0
    large_count = int((returns > 0.20).sum()) if len(returns) else 0
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "rows": int(len(work)),
        "first": work["date"].min().isoformat(),
        "last": work["date"].max().isoformat(),
        "max_abs_return_pct": round(max_abs, 6),
        "gap_ratio": round(gap_ratio, 6),
        "large_return_gt_20pct_count": large_count,
        "quality_ok": bool(large_count == 0 and max_abs < 20.0),
    }


def clean_source_to_1m(
    source: TomacSource,
    *,
    start: str,
    end: str,
    max_rows: int | None = None,
    chunksize: int = 500_000,
) -> tuple[pd.DataFrame, list[dict[str, Any]], dict[str, Any]]:
    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
    selected_chunks: list[pd.DataFrame] = []
    stats = {
        "symbol": source.symbol,
        "source_csv": str(source.source_csv),
        "schema": source.schema,
        "raw_rows_seen": 0,
        "date_filtered_rows": 0,
        "spread_rows_dropped": 0,
        "duplicate_timestamp_rows_dropped": 0,
        "selection_method": "highest_current_volume_outright_per_timestamp",
        "roll_adjustment_method": "boundary_prev_close_minus_new_open",
        "future_lookahead": False,
    }
    usecols = ["ts_event", "open", "high", "low", "close", "volume", "symbol"]
    remaining = max_rows

    for chunk in pd.read_csv(source.source_csv, usecols=usecols, chunksize=chunksize):
        if remaining is not None and remaining <= 0:
            break
        stats["raw_rows_seen"] += int(len(chunk))
        chunk["date"] = pd.to_datetime(chunk["ts_event"], utc=True)
        chunk = chunk.loc[(chunk["date"] >= start_ts) & (chunk["date"] < end_ts)].copy()
        if remaining is not None and len(chunk) > remaining:
            chunk = chunk.head(remaining)
        remaining = None if remaining is None else remaining - len(chunk)
        if chunk.empty:
            continue
        stats["date_filtered_rows"] += int(len(chunk))
        selected, selection_stats = select_front_outright_rows(chunk, source.symbol)
        stats["spread_rows_dropped"] += selection_stats["spread_rows_dropped"]
        stats["duplicate_timestamp_rows_dropped"] += selection_stats["duplicate_timestamp_rows_dropped"]
        if not selected.empty:
            selected_chunks.append(selected)

    if selected_chunks:
        selected_all = pd.concat(selected_chunks, ignore_index=True)
        selected_all = (
            selected_all.sort_values(["date", "volume"], ascending=[True, False])
            .drop_duplicates(subset=["date"], keep="first")
            .sort_values("date")
            .reset_index(drop=True)
        )
    else:
        selected_all = pd.DataFrame(columns=["date", "contract", "open", "high", "low", "close", "volume"])

    adjusted, ledger = back_adjust_rolls(selected_all, symbol=source.symbol)
    stats["selected_1m_rows"] = int(len(selected_all))
    stats["clean_1m_rows"] = int(len(adjusted))
    stats["roll_count"] = int(len(ledger))
    stats["first"] = adjusted["date"].min().isoformat() if len(adjusted) else None
    stats["last"] = adjusted["date"].max().isoformat() if len(adjusted) else None
    stats.update(session_coverage_stats(adjusted))
    stats["contracts"] = (
        selected_all["contract"].value_counts().sort_index().astype(int).to_dict()
        if len(selected_all)
        else {}
    )
    return adjusted, ledger, stats


def write_clean_bundle(
    source: TomacSource,
    *,
    root: Path,
    start: str,
    end: str,
    timeframes: tuple[str, ...],
    max_rows: int | None,
    chunksize: int,
) -> dict[str, Any]:
    clean_dir = root / "clean" / source.symbol
    clean_dir.mkdir(parents=True, exist_ok=True)
    clean_1m, ledger, stats = clean_source_to_1m(
        source,
        start=start,
        end=end,
        max_rows=max_rows,
        chunksize=chunksize,
    )
    ledger_path = clean_dir / "roll_ledger.csv"
    with ledger_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "symbol",
            "roll_index",
            "roll_time",
            "old_contract",
            "new_contract",
            "prev_raw_close",
            "new_raw_open",
            "adjustment_delta",
            "cumulative_delta_after_roll",
            "method",
            "future_lookahead",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ledger)

    timeframe_stats: dict[str, Any] = {}
    for timeframe in timeframes:
        out = resample_clean_ohlcv(clean_1m, timeframe) if timeframe != "1m" else clean_1m[
            ["date", "open", "high", "low", "close", "volume"]
        ].copy()
        out_path = clean_dir / f"{source.symbol}_USD-{timeframe}.feather"
        out["date"] = pd.to_datetime(out["date"], utc=True)
        out.to_feather(out_path)
        quality = clean_quality(out, symbol=source.symbol, timeframe=timeframe)
        quality["feather"] = str(out_path)
        timeframe_stats[timeframe] = quality

    bundle = {
        **stats,
        "clean_dir": str(clean_dir),
        "roll_ledger": str(ledger_path),
        "timeframes": timeframe_stats,
    }
    (clean_dir / "clean_quality.json").write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    return bundle


def load_clean_bundle(root: Path, symbol: str, timeframes: tuple[str, ...]) -> dict[str, Any]:
    quality_path = root / "clean" / symbol / "clean_quality.json"
    if not quality_path.exists():
        raise FileNotFoundError(f"missing clean bundle for {symbol}: {quality_path}")
    bundle = json.loads(quality_path.read_text(encoding="utf-8"))
    missing: list[str] = []
    for timeframe in timeframes:
        info = (bundle.get("timeframes") or {}).get(timeframe)
        if not info or not info.get("quality_ok") or not Path(str(info.get("feather", ""))).exists():
            missing.append(timeframe)
    if missing:
        raise FileNotFoundError(f"clean bundle for {symbol} missing quality-ok timeframes: {','.join(missing)}")
    return bundle


def timeframe_class_suffix(timeframe: str) -> str:
    exact = {
        "1m": "OneMin",
        "5m": "FiveMin",
        "15m": "FifteenMin",
        "30m": "ThirtyMin",
        "1h": "OneHour",
        "4h": "FourHour",
        "1d": "OneDay",
    }
    if timeframe in exact:
        return exact[timeframe]

    match = re.fullmatch(r"([0-9]+)([mhd])", timeframe)
    if not match:
        raise ValueError(f"unsupported timeframe for strategy class suffix: {timeframe}")
    unit = {"m": "Min", "h": "Hour", "d": "Day"}[match.group(2)]
    return f"{match.group(1)}{unit}"


def strategy_class_name(spec: CandidateSpec, *, symbol: str, timeframe: str) -> str:
    return f"Tomac{symbol}{spec.class_prefix}{timeframe_class_suffix(timeframe)}CleanV1"


def generated_strategy_specs(
    symbols: list[str],
    timeframe: str,
    *,
    families: list[str] | None = None,
) -> list[GeneratedStrategySpec]:
    generated: list[GeneratedStrategySpec] = []
    for symbol in symbols:
        for spec in candidate_specs(families=families):
            generated.append(
                GeneratedStrategySpec(
                    class_name=strategy_class_name(spec, symbol=symbol, timeframe=timeframe),
                    symbol=symbol,
                    timeframe=timeframe,
                    factor_id=spec.factor_id(timeframe),
                    branch_path=spec.branch_path_with_factor(timeframe),
                    family=spec.key,
                    direction=spec.direction,
                )
            )
    return generated


def futures_feather_path(workspace: Path, symbol: str, timeframe: str) -> Path:
    return workspace / "user_data/data/futures" / f"{symbol}_USD-{timeframe}-futures.feather"


def patch_copied_tomac_runner(runner_path: Path) -> None:
    text = runner_path.read_text(encoding="utf-8")
    if "def _synthetic_leverage_tiers" in text:
        return
    leverage_func = '''

def _synthetic_leverage_tiers(pair: str) -> list[dict[str, float | None]]:
    return [
        {
            "minNotional": 0.0,
            "maxNotional": 1_000_000_000.0,
            "maintenanceMarginRate": 0.005,
            "maxLeverage": 20.0,
            "maintAmt": 0.0,
        }
    ]
'''
    text = text.replace(
        "\n\ndef _build_exchange_with_synthetic_pairs(config: dict[str, Any]):",
        leverage_func + "\n\ndef _build_exchange_with_synthetic_pairs(config: dict[str, Any]):",
    )
    text = text.replace(
        "        exchange._api_async.markets[pair] = market\n",
        "        exchange._api_async.markets[pair] = market\n"
        "        if trading_mode == \"futures\":\n"
        "            exchange._leverage_tiers[pair] = _synthetic_leverage_tiers(pair)\n",
    )
    runner_path.write_text(text, encoding="utf-8")


def strategy_source(spec: CandidateSpec, *, symbol: str, timeframe: str) -> str:
    class_name = strategy_class_name(spec, symbol=symbol, timeframe=timeframe)
    factor_id = spec.factor_id(timeframe)
    branch_path = spec.branch_path_with_factor(timeframe)
    product_label = product_label_for_symbol(symbol)
    can_short = spec.direction == "long_short"
    trailing_stop = spec.key not in {
        "wpr_fractal_no_be_fulltarget",
        "wpr_adx_fractal_sweep_reclaim",
        "wpr_adx_hurst_profile_mss_reclaim",
        "value_area_vpoc_htf_trend_mss_filter",
    }
    startup_candle_count = 420 if spec.key == "value_area_vpoc_htf_trend_mss_filter" else (
        320 if spec.key == "wpr_adx_hurst_profile_mss_reclaim" else 220
    )
    return textwrap.dedent(
        f"""
        from freqtrade.strategy import IStrategy
        from pandas import DataFrame
        import bisect
        import pandas as pd
        import numpy as np
        import talib.abstract as ta


        class {class_name}(IStrategy):
            \"\"\"
            data_cleaner: tomac_index_futures_clean_aq_v1
            no_future_rule: entries and exits use raw conditions shifted by one closed bar
            factor_id: {factor_id}
            branch_path: {branch_path}
            market: futures
            product: {product_label}
            symbol: {symbol}
            timeframe_label: {timeframe}
            \"\"\"
            INTERFACE_VERSION = 3
            timeframe = "{timeframe}"
            can_short = {can_short}
            minimal_roi = {{"0": {spec.roi:.4f}, "60": {spec.roi * 0.45:.4f}, "180": {spec.roi * 0.18:.4f}}}
            stoploss = {spec.stoploss}
            trailing_stop = {trailing_stop}
            trailing_stop_positive = {spec.trailing_positive}
            trailing_stop_positive_offset = {spec.trailing_offset}
            trailing_only_offset_is_reached = True
            process_only_new_candles = True
            use_exit_signal = True
            startup_candle_count = {startup_candle_count}

            def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
                if metadata.get("pair") != "{symbol}/USD":
                    return dataframe
                dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
                dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
                dataframe["ema32"] = ta.EMA(dataframe, timeperiod=32)
                dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
                dataframe["ema55"] = ta.EMA(dataframe, timeperiod=55)
                dataframe["ema89"] = ta.EMA(dataframe, timeperiod=89)
                dataframe["ema96"] = ta.EMA(dataframe, timeperiod=96)
                dataframe["ema144"] = ta.EMA(dataframe, timeperiod=144)
                dataframe["ema390"] = ta.EMA(dataframe, timeperiod=390)
                dataframe["adx14"] = ta.ADX(dataframe, timeperiod=14)
                dataframe["atr14"] = ta.ATR(dataframe, timeperiod=14)
                dataframe["atr96"] = ta.ATR(dataframe, timeperiod=96)
                dataframe["rsi2"] = ta.RSI(dataframe, timeperiod=2)
                dataframe["rsi3"] = ta.RSI(dataframe, timeperiod=3)
                dataframe["rsi14"] = ta.RSI(dataframe, timeperiod=14)
                dataframe["vol_ma20"] = dataframe["volume"].rolling(20).mean()
                dataframe["vol_ma30"] = dataframe["volume"].rolling(30).mean()
                dataframe["vol_ma96"] = dataframe["volume"].rolling(96).mean()
                dataframe["vol96"] = dataframe["vol_ma96"]
                typical = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
                day = dataframe["date"].dt.strftime("%Y-%m-%d")
                ny = dataframe["date"].dt.tz_convert("America/New_York")
                dataframe["minute_of_day_ny"] = ny.dt.hour * 60 + ny.dt.minute
                dataframe["session_open"] = dataframe.groupby(day)["open"].transform("first")
                dataframe["hour_open"] = dataframe.groupby([day, ny.dt.hour])["open"].transform("first")
                pv = typical * dataframe["volume"]
                dataframe["session_vwap"] = pv.groupby(day).cumsum() / dataframe["volume"].groupby(day).cumsum().replace(0, 1)
                prior_day_high = dataframe.groupby(day)["high"].max().shift(1)
                prior_day_low = dataframe.groupby(day)["low"].min().shift(1)
                prior_day_close = dataframe.groupby(day)["close"].last().shift(1)
                dataframe["prior_day_high"] = day.map(prior_day_high)
                dataframe["prior_day_low"] = day.map(prior_day_low)
                dataframe["prior_day_close"] = day.map(prior_day_close)
                dataframe["prior_day_range"] = dataframe["prior_day_high"] - dataframe["prior_day_low"]
                dataframe["camarilla_pp"] = (
                    dataframe["prior_day_high"] + dataframe["prior_day_low"] + dataframe["prior_day_close"]
                ) / 3.0
                dataframe["camarilla_r3"] = dataframe["prior_day_close"] + dataframe["prior_day_range"] * 1.1 / 4.0
                dataframe["camarilla_s3"] = dataframe["prior_day_close"] - dataframe["prior_day_range"] * 1.1 / 4.0
                dataframe["camarilla_r4"] = dataframe["prior_day_close"] + dataframe["prior_day_range"] * 1.1 / 2.0
                dataframe["camarilla_s4"] = dataframe["prior_day_close"] - dataframe["prior_day_range"] * 1.1 / 2.0
                dataframe["cam_pp"] = dataframe["camarilla_pp"]
                dataframe["cam_r3"] = dataframe["camarilla_r3"]
                dataframe["cam_s3"] = dataframe["camarilla_s3"]
                dataframe["cam_r4"] = dataframe["camarilla_r4"]
                dataframe["cam_s4"] = dataframe["camarilla_s4"]
                dataframe["range_high40"] = dataframe["high"].rolling(40).max().shift(1)
                dataframe["range_low40"] = dataframe["low"].rolling(40).min().shift(1)
                dataframe["prior_high80"] = dataframe["high"].rolling(80).max().shift(1)
                dataframe["prior_low80"] = dataframe["low"].rolling(80).min().shift(1)
                dataframe["rvol30"] = dataframe["volume"] / dataframe["vol_ma30"].replace(0, 1)
                dataframe["rvol96"] = dataframe["volume"] / dataframe["vol96"].replace(0, 1)
                dataframe["rvol20"] = dataframe["volume"] / dataframe["vol_ma20"].replace(0, 1)
                dataframe["volume_ratio"] = dataframe["volume"] / dataframe["vol_ma20"].replace(0, 1)
                dataframe["atr_ma50"] = dataframe["atr14"].rolling(50).mean()
                dataframe["body_atr"] = (dataframe["close"] - dataframe["open"]).abs() / dataframe["atr14"]
                dataframe["bar_range"] = dataframe["high"] - dataframe["low"]
                bar_range_safe = dataframe["bar_range"].replace(0, np.nan)
                dataframe["close_location"] = (
                    (dataframe["close"] - dataframe["low"]) / bar_range_safe
                ).clip(0.0, 1.0)
                dataframe["bar_range_atr"] = dataframe["bar_range"] / dataframe["atr14"]
                macd_line, macd_signal, macd_hist = ta.MACD(dataframe["close"], fastperiod=12, slowperiod=26, signalperiod=9)
                dataframe["macd_line"] = macd_line
                dataframe["macd_signal"] = macd_signal
                dataframe["macd_hist"] = macd_hist
                dataframe["prior_nr7"] = dataframe["bar_range"].shift(1) <= dataframe["bar_range"].rolling(7).min().shift(2)
                dataframe["nr7_high"] = dataframe["high"].rolling(7).max().shift(1)
                dataframe["lower_band40"] = dataframe["close"].rolling(40).mean() - dataframe["close"].rolling(40).std() * 2.0
                wpr_high14 = dataframe["high"].rolling(14).max()
                wpr_low14 = dataframe["low"].rolling(14).min()
                dataframe["wpr14"] = ((wpr_high14 - dataframe["close"]) / (wpr_high14 - wpr_low14).replace(0, 1)) * -100.0
                dataframe["connors_rsi"] = (dataframe["rsi3"] + dataframe["rsi2"] + dataframe["close"].pct_change().rolling(100).rank(pct=True) * 100.0) / 3.0
                hl2 = (dataframe["high"] + dataframe["low"]) / 2.0
                dataframe["supertrend_upper"] = hl2 + 3.0 * dataframe["atr14"]
                dataframe["supertrend_lower"] = hl2 - 3.0 * dataframe["atr14"]
                dataframe["supertrend_trend_raw"] = 0
                dataframe.loc[
                    dataframe["close"] > dataframe["supertrend_upper"].shift(1),
                    "supertrend_trend_raw",
                ] = 1
                dataframe.loc[
                    dataframe["close"] < dataframe["supertrend_lower"].shift(1),
                    "supertrend_trend_raw",
                ] = -1
                dataframe["supertrend_trend"] = (
                    dataframe["supertrend_trend_raw"].replace(0, float("nan")).ffill().fillna(0)
                )
                hl_range = dataframe["high"] - dataframe["low"]
                mass_ema9 = hl_range.ewm(span=9, adjust=False).mean()
                mass_ema9_ema9 = mass_ema9.ewm(span=9, adjust=False).mean()
                dataframe["mass_index25"] = (mass_ema9 / mass_ema9_ema9.replace(0, np.nan)).rolling(25).sum()
                plus_vm = (dataframe["high"] - dataframe["low"].shift(1)).abs()
                minus_vm = (dataframe["low"] - dataframe["high"].shift(1)).abs()
                true_range = pd.concat([
                    dataframe["high"] - dataframe["low"],
                    (dataframe["high"] - dataframe["close"].shift(1)).abs(),
                    (dataframe["low"] - dataframe["close"].shift(1)).abs(),
                ], axis=1).max(axis=1)
                tr14 = true_range.rolling(14).sum().replace(0, np.nan)
                dataframe["vortex_plus14"] = plus_vm.rolling(14).sum() / tr14
                dataframe["vortex_minus14"] = minus_vm.rolling(14).sum() / tr14
                dataframe["ema21_slope_bps_12"] = (dataframe["ema21"] - dataframe["ema21"].shift(12)) / dataframe["close"].replace(0, np.nan) * 10000.0
                dataframe["ema55_slope_bps_48"] = (dataframe["ema55"] - dataframe["ema55"].shift(48)) / dataframe["close"].replace(0, np.nan) * 10000.0
                regression_window = 96
                regression_x = pd.Series(np.arange(regression_window, dtype=float))

                def _regression_slope_bps(values: np.ndarray) -> float:
                    if len(values) != regression_window or np.isnan(values).any():
                        return np.nan
                    slope = np.polyfit(regression_x, values.astype(float), 1)[0]
                    base = values[-1]
                    if abs(base) <= 1e-12:
                        return np.nan
                    return float(slope / base * 10000.0)

                def _regression_r2(values: np.ndarray) -> float:
                    if len(values) != regression_window or np.isnan(values).any():
                        return np.nan
                    slope, intercept = np.polyfit(regression_x, values.astype(float), 1)
                    fitted = slope * regression_x + intercept
                    total = float(np.sum((values - values.mean()) ** 2))
                    if total <= 1e-12:
                        return np.nan
                    residual = float(np.sum((values - fitted) ** 2))
                    return float(1.0 - residual / total)

                dataframe["regression_slope_bps_96"] = dataframe["close"].rolling(regression_window).apply(
                    _regression_slope_bps,
                    raw=True,
                )
                dataframe["regression_r2_96"] = dataframe["close"].rolling(regression_window).apply(
                    _regression_r2,
                    raw=True,
                )
                aroon_window = 25
                dataframe["aroon_up25"] = dataframe["high"].rolling(aroon_window + 1).apply(
                    lambda values: 100.0 * (aroon_window - (len(values) - 1 - int(np.argmax(values)))) / aroon_window,
                    raw=True,
                )
                dataframe["aroon_down25"] = dataframe["low"].rolling(aroon_window + 1).apply(
                    lambda values: 100.0 * (aroon_window - (len(values) - 1 - int(np.argmin(values)))) / aroon_window,
                    raw=True,
                )
                cci_tp = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
                cci_ma = cci_tp.rolling(20).mean()
                cci_mad = (cci_tp - cci_ma).abs().rolling(20).mean().replace(0, np.nan)
                dataframe["cci20"] = (cci_tp - cci_ma) / (0.015 * cci_mad)
                dataframe["sweep_low40"] = dataframe["low"] <= dataframe["range_low40"]
                dataframe["sweep_close_reclaim"] = dataframe["close"] > dataframe["range_low40"]
                dataframe["swing_high34"] = dataframe["high"].rolling(34).max().shift(1)
                dataframe["swing_low34"] = dataframe["low"].rolling(34).min().shift(1)
                dataframe["swing_range34"] = dataframe["swing_high34"] - dataframe["swing_low34"]
                dataframe["ote_long_62"] = dataframe["swing_high34"] - dataframe["swing_range34"] * 0.62
                dataframe["ote_long_79"] = dataframe["swing_high34"] - dataframe["swing_range34"] * 0.79
                dataframe["prev2_high"] = dataframe["high"].shift(2)
                dataframe["prev2_low"] = dataframe["low"].shift(2)
                dataframe["bull_fvg"] = dataframe["low"] > dataframe["prev2_high"]
                dataframe["bear_fvg"] = dataframe["high"] < dataframe["prev2_low"]
                dataframe["bear_candle_prev"] = dataframe["close"].shift(1) < dataframe["open"].shift(1)
                dataframe["bull_candle_prev"] = dataframe["close"].shift(1) > dataframe["open"].shift(1)
                dataframe["bull_momentum2"] = (dataframe["close"] > dataframe["open"]) & (dataframe["close"].shift(1) > dataframe["open"].shift(1))
                dataframe["bear_momentum2"] = (dataframe["close"] < dataframe["open"]) & (dataframe["close"].shift(1) < dataframe["open"].shift(1))
                dataframe["bull_ob_low"] = dataframe["low"].shift(1).where(dataframe["bear_candle_prev"] & dataframe["bull_momentum2"]).ffill()
                dataframe["bull_ob_high"] = dataframe["high"].shift(1).where(dataframe["bear_candle_prev"] & dataframe["bull_momentum2"]).ffill()
                dataframe["bear_ob_low"] = dataframe["low"].shift(1).where(dataframe["bull_candle_prev"] & dataframe["bear_momentum2"]).ffill()
                dataframe["bear_ob_high"] = dataframe["high"].shift(1).where(dataframe["bull_candle_prev"] & dataframe["bear_momentum2"]).ffill()
                dataframe["liq_high20"] = dataframe["high"].rolling(20).max().shift(1)
                dataframe["liq_low20"] = dataframe["low"].rolling(20).min().shift(1)
                dataframe["liq_high60"] = dataframe["high"].rolling(60).max().shift(1)
                dataframe["liq_low60"] = dataframe["low"].rolling(60).min().shift(1)
                fractal_window = 7
                fractal_dist = 3
                fractal_high_raw = dataframe["high"].shift(fractal_dist).where(
                    dataframe["high"].shift(fractal_dist) == dataframe["high"].rolling(fractal_window).max()
                )
                fractal_low_raw = dataframe["low"].shift(fractal_dist).where(
                    dataframe["low"].shift(fractal_dist) == dataframe["low"].rolling(fractal_window).min()
                )
                dataframe["bsl_fractal"] = fractal_high_raw.ffill()
                dataframe["ssl_fractal"] = fractal_low_raw.ffill()
                dataframe["confirmed_bsl"] = dataframe["bsl_fractal"]
                dataframe["confirmed_ssl"] = dataframe["ssl_fractal"]
                dataframe["swing_high8"] = dataframe["high"].rolling(8).max().shift(1)
                dataframe["swing_low8"] = dataframe["low"].rolling(8).min().shift(1)
                dataframe["bull_mss"] = (
                    (dataframe["close"] > dataframe["swing_high8"])
                    & (dataframe["close"].shift(1) <= dataframe["swing_high8"].shift(1))
                )
                dataframe["bear_mss"] = (
                    (dataframe["close"] < dataframe["swing_low8"])
                    & (dataframe["close"].shift(1) >= dataframe["swing_low8"].shift(1))
                )
                dataframe["sellside_pool_cluster"] = dataframe[
                    ["liq_low20", "liq_low60", "confirmed_ssl"]
                ].min(axis=1)
                dataframe["buyside_pool_cluster"] = dataframe[
                    ["liq_high20", "liq_high60", "confirmed_bsl"]
                ].max(axis=1)
                pool_width = (
                    dataframe["buyside_pool_cluster"] - dataframe["sellside_pool_cluster"]
                )
                atr_safe = dataframe["atr14"].replace(0, np.nan)
                dataframe["liquidity_pool_band"] = pool_width / atr_safe
                dataframe["pool_distance_atr"] = np.minimum(
                    (dataframe["close"] - dataframe["sellside_pool_cluster"]).abs(),
                    (dataframe["close"] - dataframe["buyside_pool_cluster"]).abs(),
                ) / atr_safe
                dataframe["sweep_strength"] = np.maximum(
                    (dataframe["sellside_pool_cluster"] - dataframe["low"]).clip(lower=0),
                    (dataframe["high"] - dataframe["buyside_pool_cluster"]).clip(lower=0),
                ) / atr_safe
                dataframe["fvg_mitigation_score"] = np.where(
                    dataframe["bull_fvg"].fillna(False),
                    ((dataframe["close"] - dataframe["prev2_high"]).clip(lower=0) / atr_safe),
                    np.where(
                        dataframe["bear_fvg"].fillna(False),
                        ((dataframe["prev2_low"] - dataframe["close"]).clip(lower=0) / atr_safe),
                        0.0,
                    ),
                )
                if "{spec.key}" == "wpr_adx_hurst_profile_mss_reclaim":
                    def _hurst_rs(series: pd.Series) -> float:
                        values = series.to_numpy(dtype=float)
                        if len(values) < 32 or np.isnan(values).any():
                            return np.nan
                        demeaned = values - values.mean()
                        sigma = demeaned.std()
                        if sigma <= 1e-12:
                            return np.nan
                        cumulative = np.cumsum(demeaned)
                        spread = cumulative.max() - cumulative.min()
                        if spread <= 1e-12:
                            return np.nan
                        return float(np.log(spread / sigma) / np.log(len(values)))

                    def _rolling_profile_levels(price_series: pd.Series, volume_series: pd.Series, window: int = 96, bins: int = 24):
                        prices = price_series.to_numpy(dtype=float)
                        volumes = volume_series.to_numpy(dtype=float)
                        poc = np.full(len(prices), np.nan)
                        val = np.full(len(prices), np.nan)
                        vah = np.full(len(prices), np.nan)
                        for idx in range(window - 1, len(prices)):
                            window_prices = prices[idx - window + 1: idx + 1]
                            window_volumes = volumes[idx - window + 1: idx + 1]
                            if np.isnan(window_prices).any() or np.isnan(window_volumes).any():
                                continue
                            lo = float(np.min(window_prices))
                            hi = float(np.max(window_prices))
                            if hi - lo <= 1e-9:
                                poc[idx] = hi
                                val[idx] = lo
                                vah[idx] = hi
                                continue
                            hist, edges = np.histogram(window_prices, bins=bins, range=(lo, hi), weights=window_volumes)
                            if hist.sum() <= 0:
                                continue
                            centers = (edges[:-1] + edges[1:]) / 2.0
                            poc_idx = int(np.argmax(hist))
                            left = poc_idx
                            right = poc_idx
                            covered = float(hist[poc_idx])
                            target = float(hist.sum()) * 0.70
                            while covered < target and (left > 0 or right < len(hist) - 1):
                                left_vol = hist[left - 1] if left > 0 else -1.0
                                right_vol = hist[right + 1] if right < len(hist) - 1 else -1.0
                                if right_vol >= left_vol and right < len(hist) - 1:
                                    right += 1
                                    covered += float(hist[right])
                                elif left > 0:
                                    left -= 1
                                    covered += float(hist[left])
                                else:
                                    break
                            poc[idx] = float(centers[poc_idx])
                            val[idx] = float(centers[left])
                            vah[idx] = float(centers[right])
                        return poc, val, vah

                    dataframe["prev2_low"] = dataframe["low"].shift(2)
                    dataframe["bear_fvg"] = dataframe["high"] < dataframe["prev2_low"]
                    dataframe["hurst64"] = dataframe["close"].rolling(64).apply(_hurst_rs, raw=False)
                    dataframe["hurst128"] = dataframe["close"].rolling(128).apply(_hurst_rs, raw=False)
                    profile_poc96, profile_val96, profile_vah96 = _rolling_profile_levels(
                        typical,
                        dataframe["volume"],
                        window=96,
                        bins=24,
                    )
                    dataframe["profile_poc96"] = profile_poc96
                    dataframe["profile_val96"] = profile_val96
                    dataframe["profile_vah96"] = profile_vah96
                    profile_atr = dataframe["atr14"].replace(0, np.nan)
                    dataframe["profile_poc_dist_atr"] = (
                        (dataframe["close"] - dataframe["profile_poc96"]).abs() / profile_atr
                    )
                if "{spec.key}" == "value_area_vpoc_htf_trend_mss_filter":
                    def _round_to_row(value: float, row_size: float) -> float:
                        if not np.isfinite(value):
                            return value
                        roundoff = 1.0 / max(row_size, 1e-12)
                        return np.ceil(float(value) * roundoff) / roundoff

                    def _signed_breakout(close: float, low: float | None, high: float | None) -> float:
                        if low is None or high is None:
                            return np.nan
                        if close > high:
                            return close - high
                        if close < low:
                            return close - low
                        return 0.0

                    def _value_area_position(close: float, val: float | None, vah: float | None) -> float:
                        if val is None or vah is None:
                            return np.nan
                        width = vah - val
                        if width <= 1e-12:
                            return 0.5
                        return (close - val) / width

                    def _session_profile_arrays(frame: DataFrame, row_size: float):
                        count = len(frame)
                        session_or_breakout_atr = np.full(count, np.nan)
                        session_ib_breakout_atr = np.full(count, np.nan)
                        session_profile_poc_dist_atr = np.full(count, np.nan)
                        session_profile_value_area_pos = np.full(count, np.nan)
                        session_profile_rotation_factor = np.full(count, np.nan)
                        session_profile_poc_price = np.full(count, np.nan)
                        session_profile_val = np.full(count, np.nan)
                        session_profile_vah = np.full(count, np.nan)
                        dates = pd.to_datetime(frame["date"], utc=True)
                        closes = frame["close"].to_numpy(dtype=float)
                        highs = frame["high"].to_numpy(dtype=float)
                        lows = frame["low"].to_numpy(dtype=float)
                        volumes = frame["volume"].to_numpy(dtype=float)
                        atrs = frame["atr14"].replace(0, np.nan).to_numpy(dtype=float)
                        ny_dates = dates.dt.tz_convert("America/New_York")
                        minute_of_day = (ny_dates.dt.hour * 60 + ny_dates.dt.minute).to_numpy(dtype=int)
                        session_keys = (
                            ny_dates.dt.tz_localize(None).dt.normalize()
                            - pd.to_timedelta((minute_of_day < 570).astype(int), unit="D")
                        ).to_numpy()
                        current_session_key = None
                        profile_map = {{}}
                        profile_levels = []
                        total_profile_volume = 0.0
                        or_low = None
                        or_high = None
                        ib_low = None
                        ib_high = None
                        for idx in range(count):
                            session_key = session_keys[idx]
                            session_minute = minute_of_day[idx]
                            if session_minute < 570:
                                session_minute += 1440
                            if current_session_key is None or session_key != current_session_key:
                                current_session_key = session_key
                                profile_map = {{}}
                                profile_levels = []
                                total_profile_volume = 0.0
                                or_low = None
                                or_high = None
                                ib_low = None
                                ib_high = None
                            if session_minute <= 580:
                                if or_low is None:
                                    or_low = lows[idx]
                                    or_high = highs[idx]
                                else:
                                    or_low = min(or_low, lows[idx])
                                    or_high = max(or_high, highs[idx])
                            if session_minute <= 630:
                                if ib_low is None:
                                    ib_low = lows[idx]
                                    ib_high = highs[idx]
                                else:
                                    ib_low = min(ib_low, lows[idx])
                                    ib_high = max(ib_high, highs[idx])
                            level = _round_to_row(closes[idx], row_size)
                            if np.isfinite(level):
                                if level not in profile_map:
                                    bisect.insort(profile_levels, level)
                                    profile_map[level] = 0.0
                                profile_map[level] = profile_map.get(level, 0.0) + max(float(volumes[idx]), 0.0)
                                total_profile_volume += max(float(volumes[idx]), 0.0)
                            atr = atrs[idx]
                            if not np.isfinite(atr) or atr <= 1e-12:
                                continue
                            if not profile_levels or total_profile_volume <= 0:
                                continue
                            levels = profile_levels
                            level_volumes = [profile_map[level] for level in levels]
                            max_volume = max(level_volumes)
                            poc_indices = [pos for pos, volume_value in enumerate(level_volumes) if volume_value == max_volume]
                            poc_idx = poc_indices[len(poc_indices) // 2]
                            poc_price = float(levels[poc_idx])
                            covered_volume = float(level_volumes[poc_idx])
                            target_volume = total_profile_volume * 0.70
                            min_idx = poc_idx
                            max_idx = poc_idx
                            while covered_volume <= target_volume and (min_idx > 0 or max_idx < len(levels) - 1):
                                last_min = min_idx
                                last_max = max_idx
                                next_min_idx = max(min_idx - 1, 0)
                                next_max_idx = min(max_idx + 1, len(levels) - 1)
                                low_volume = level_volumes[next_min_idx] if next_min_idx != last_min else None
                                high_volume = level_volumes[next_max_idx] if next_max_idx != last_max else None
                                if high_volume is None or (low_volume is not None and low_volume > high_volume):
                                    covered_volume += float(low_volume or 0.0)
                                    min_idx = next_min_idx
                                elif low_volume is None or (high_volume is not None and low_volume <= high_volume):
                                    covered_volume += float(high_volume or 0.0)
                                    max_idx = next_max_idx
                                else:
                                    break
                            val = float(levels[min_idx])
                            vah = float(levels[max_idx])
                            profile_width = float(levels[-1] - levels[0]) if len(levels) > 1 else 0.0
                            ib_width = ib_high - ib_low if ib_low is not None and ib_high is not None else np.nan
                            session_or_breakout_atr[idx] = _signed_breakout(closes[idx], or_low, or_high) / atr
                            session_ib_breakout_atr[idx] = _signed_breakout(closes[idx], ib_low, ib_high) / atr
                            session_profile_poc_dist_atr[idx] = (closes[idx] - poc_price) / atr
                            session_profile_value_area_pos[idx] = _value_area_position(closes[idx], val, vah)
                            session_profile_rotation_factor[idx] = (
                                profile_width / max(float(ib_width), row_size)
                                if np.isfinite(ib_width)
                                else np.nan
                            )
                            session_profile_poc_price[idx] = poc_price
                            session_profile_val[idx] = val
                            session_profile_vah[idx] = vah
                        return (
                            session_or_breakout_atr,
                            session_ib_breakout_atr,
                            session_profile_poc_dist_atr,
                            session_profile_value_area_pos,
                            session_profile_rotation_factor,
                            session_profile_poc_price,
                            session_profile_val,
                            session_profile_vah,
                        )

                    dataframe["prev2_low"] = dataframe["low"].shift(2)
                    dataframe["bear_fvg"] = dataframe["high"] < dataframe["prev2_low"]
                    dataframe["swing_high8"] = dataframe["high"].rolling(8).max().shift(1)
                    dataframe["swing_low8"] = dataframe["low"].rolling(8).min().shift(1)
                    dataframe["bull_mss"] = (
                        (dataframe["close"] > dataframe["swing_high8"])
                        & (dataframe["close"].shift(1) <= dataframe["swing_high8"].shift(1))
                    )
                    dataframe["bear_mss"] = (
                        (dataframe["close"] < dataframe["swing_low8"])
                        & (dataframe["close"].shift(1) >= dataframe["swing_low8"].shift(1))
                    )
                    profile_row_size = {{"NQ": 0.25, "ES": 0.25, "YM": 1.0, "6E": 0.00005, "XAU": 0.1}}.get("{symbol}", 0.25)
                    (
                        dataframe["session_or_breakout_atr"],
                        dataframe["session_ib_breakout_atr"],
                        dataframe["session_profile_poc_dist_atr"],
                        dataframe["session_profile_value_area_pos"],
                        dataframe["session_profile_rotation_factor"],
                        dataframe["session_profile_poc_price"],
                        dataframe["session_profile_val"],
                        dataframe["session_profile_vah"],
                    ) = _session_profile_arrays(dataframe, row_size=profile_row_size)
                dataframe["midnight_open"] = dataframe.groupby(day)["open"].transform("first")
                dataframe["__row_order"] = range(len(dataframe))
                context_base = dataframe[["__row_order", "date", "open", "high", "low", "close", "volume"]].copy()
                context_base["__date_utc"] = pd.to_datetime(context_base["date"], utc=True)
                context_base = context_base.sort_values("__date_utc")
                for label, rule in {{"5m": "5min", "15m": "15min", "30m": "30min", "1h": "1h", "4h": "4h", "1d": "1D"}}.items():
                    tf = (
                        context_base.set_index("__date_utc")[["open", "high", "low", "close", "volume"]]
                        .resample(rule, label="right", closed="right")
                        .agg({{"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}})
                        .dropna()
                    )
                    tf[f"ema20_{{label}}"] = tf["close"].ewm(span=20, adjust=False, min_periods=20).mean()
                    tf[f"ema50_{{label}}"] = tf["close"].ewm(span=50, adjust=False, min_periods=50).mean()
                    tf[f"slope_{{label}}"] = tf[f"ema20_{{label}}"] - tf[f"ema20_{{label}}"].shift(6)
                    tf.index.name = "__date_utc"
                    keep = [f"ema20_{{label}}", f"ema50_{{label}}", f"slope_{{label}}"]
                    merged = pd.merge_asof(
                        context_base[["__row_order", "__date_utc"]],
                        tf[keep].reset_index(),
                        on="__date_utc",
                        direction="backward",
                    ).sort_values("__row_order")
                    for column in keep:
                        dataframe[column] = merged[column].to_numpy()
                dataframe = dataframe.drop(columns=["__row_order"], errors="ignore")
                return dataframe

            def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
                dataframe["enter_long"] = 0
                dataframe["enter_short"] = 0
                dataframe["enter_tag"] = ""
                if metadata.get("pair") != "{symbol}/USD":
                    return dataframe
                trend = (dataframe["ema21"] > dataframe["ema55"]) & (dataframe["close"] > dataframe["ema21"])
                vwap_reclaim = (dataframe["close"] > dataframe["session_vwap"]) & (dataframe["close"].shift(1) <= dataframe["session_vwap"].shift(1))
                breakout = dataframe["close"] > dataframe["range_high40"]
                rvol_ok = dataframe["rvol30"].between(0.85, 4.0)
                rsi_ok = dataframe["rsi14"].between(42, 76)
                body_ok = dataframe["body_atr"].between(0.05, 2.2)
                exit_persistence_guard = False
                short_raw = None
                if "{spec.key}" == "opening_drive_breakout":
                    opening_window = dataframe["minute_of_day_ny"].between(9 * 60 + 35, 11 * 60 + 30)
                    opening_breakout = dataframe["close"] > dataframe["prior_high80"]
                    opening_drive_context = dataframe["close"] > dataframe["range_high40"] * 0.998
                    raw = (
                        trend
                        & opening_window
                        & opening_breakout
                        & opening_drive_context
                        & (dataframe["close"] > dataframe["session_vwap"])
                        & dataframe["rvol96"].between(1.00, 5.0)
                        & dataframe["rsi14"].between(50, 78)
                        & dataframe["body_atr"].between(0.15, 2.4)
                    )
                elif "{spec.key}" == "opening_drive_twoleg_continuation_exit_persistence":
                    opening_window = dataframe["minute_of_day_ny"].between(9 * 60 + 40, 13 * 60)
                    opening_drive_context = dataframe["close"] > dataframe["range_high40"] * 0.998
                    initial_breakout = dataframe["high"].shift(3).rolling(6).max() > dataframe["range_high40"].shift(3)
                    vwap_retest = dataframe["low"].between(
                        dataframe["session_vwap"] - dataframe["atr14"] * 0.22,
                        dataframe["session_vwap"] + dataframe["atr14"] * 0.30,
                    )
                    or_edge_retest = dataframe["low"].between(
                        dataframe["range_high40"] - dataframe["atr14"] * 0.26,
                        dataframe["range_high40"] + dataframe["atr14"] * 0.18,
                    )
                    second_leg_reclaim = (
                        initial_breakout
                        & (vwap_retest | or_edge_retest)
                        & (dataframe["close"] > dataframe["range_high40"])
                        & (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["close"].shift(1) > dataframe["session_vwap"].shift(1))
                    )
                    persistence_bias = (
                        (dataframe["macd_line"] > dataframe["macd_signal"])
                        & (dataframe["close"] > dataframe["ema21"])
                        & (dataframe["close"] > dataframe["close"].shift(2))
                    )
                    raw = (
                        trend
                        & opening_window
                        & opening_drive_context
                        & second_leg_reclaim
                        & persistence_bias.fillna(False)
                        & dataframe["rvol96"].between(0.95, 4.8)
                        & dataframe["rsi14"].between(50, 76)
                        & dataframe["body_atr"].between(0.10, 2.1)
                    )
                    exit_persistence_guard = True
                elif "{spec.key}" == "vwap_washout_reclaim":
                    raw = vwap_reclaim & rvol_ok & rsi_ok & (dataframe["low"] <= dataframe["range_low40"])
                elif "{spec.key}" == "camarilla_r3_s3_reclaim":
                    trading_window = dataframe["minute_of_day_ny"].between(9 * 60 + 35, 15 * 60 + 35)
                    atr = dataframe["atr14"].clip(lower=0.01)
                    s3_reclaim = (
                        (dataframe["low"].rolling(4).min() <= dataframe["cam_s3"] - atr * 0.03)
                        & (dataframe["close"] > dataframe["cam_s3"])
                        & (dataframe["close"].shift(1) <= dataframe["cam_s3"].shift(1) + atr.shift(1) * 0.08)
                    )
                    r3_reclaim = (
                        (dataframe["high"].rolling(4).max() >= dataframe["cam_r3"] + atr * 0.03)
                        & (dataframe["close"] < dataframe["cam_r3"])
                        & (dataframe["close"].shift(1) >= dataframe["cam_r3"].shift(1) - atr.shift(1) * 0.08)
                    )
                    long_extension = (
                        ((dataframe["cam_s3"] - dataframe["low"].rolling(4).min()) / atr).between(0.05, 1.80)
                        | (dataframe["low"] <= dataframe["cam_s4"])
                    )
                    short_extension = (
                        ((dataframe["high"].rolling(4).max() - dataframe["cam_r3"]) / atr).between(0.05, 1.80)
                        | (dataframe["high"] >= dataframe["cam_r4"])
                    )
                    camarilla_extension = long_extension | short_extension
                    long_confirm = (
                        (dataframe["close"] > dataframe["ema21"])
                        & (dataframe["close"] > dataframe["session_vwap"] - atr * 0.18)
                    )
                    short_confirm = (
                        (dataframe["close"] < dataframe["ema21"])
                        & (dataframe["close"] < dataframe["session_vwap"] + atr * 0.18)
                    )
                    range_reversion_context = (
                        dataframe["adx14"].between(8, 36)
                        & dataframe["prior_day_range"].gt(atr * 1.2)
                    )
                    raw = (
                        trading_window
                        & s3_reclaim.fillna(False)
                        & long_extension.fillna(False)
                        & long_confirm.fillna(False)
                        & range_reversion_context.fillna(False)
                        & (dataframe["close"] < dataframe["cam_r3"])
                        & dataframe["rvol96"].between(0.65, 5.5)
                        & dataframe["rsi14"].between(28, 64)
                        & dataframe["body_atr"].between(0.06, 2.30)
                    )
                    short_raw = (
                        trading_window
                        & r3_reclaim.fillna(False)
                        & short_extension.fillna(False)
                        & short_confirm.fillna(False)
                        & range_reversion_context.fillna(False)
                        & (dataframe["close"] > dataframe["cam_s3"])
                        & dataframe["rvol96"].between(0.65, 5.5)
                        & dataframe["rsi14"].between(36, 72)
                        & dataframe["body_atr"].between(0.06, 2.30)
                    )
                elif "{spec.key}" == "vwap_reclaim_persistence":
                    vwap_excursion_long = ((dataframe["session_vwap"] - dataframe["low"]) / dataframe["atr14"].clip(lower=0.01)).between(0.35, 1.8)
                    vwap_excursion_short = ((dataframe["high"] - dataframe["session_vwap"]) / dataframe["atr14"].clip(lower=0.01)).between(0.35, 1.8)
                    reclaim_long = (
                        (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["close"].shift(1) > dataframe["session_vwap"].shift(1))
                        & (dataframe["close"].shift(2) > dataframe["session_vwap"].shift(2))
                    )
                    reclaim_short = (
                        (dataframe["close"] < dataframe["session_vwap"])
                        & (dataframe["close"].shift(1) < dataframe["session_vwap"].shift(1))
                        & (dataframe["close"].shift(2) < dataframe["session_vwap"].shift(2))
                    )
                    long_transition = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & dataframe["rvol30"].between(1.2, 4.0)
                        & dataframe["rsi14"].between(46, 72)
                        & dataframe["body_atr"].between(0.04, 1.8)
                        & vwap_excursion_long
                        & reclaim_long
                    )
                    short_transition = (
                        (dataframe["ema21"] < dataframe["ema55"])
                        & dataframe["rvol30"].between(1.2, 4.0)
                        & dataframe["rsi14"].between(28, 54)
                        & dataframe["body_atr"].between(0.04, 1.8)
                        & vwap_excursion_short
                        & reclaim_short
                    )
                    raw = long_transition | short_transition
                elif "{spec.key}" == "vwap_reclaim_persistence_killzone_filter":
                    vwap_excursion_long = ((dataframe["session_vwap"] - dataframe["low"]) / dataframe["atr14"].clip(lower=0.01)).between(0.35, 1.8)
                    vwap_excursion_short = ((dataframe["high"] - dataframe["session_vwap"]) / dataframe["atr14"].clip(lower=0.01)).between(0.35, 1.8)
                    reclaim_long = (
                        (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["close"].shift(1) > dataframe["session_vwap"].shift(1))
                        & (dataframe["close"].shift(2) > dataframe["session_vwap"].shift(2))
                    )
                    reclaim_short = (
                        (dataframe["close"] < dataframe["session_vwap"])
                        & (dataframe["close"].shift(1) < dataframe["session_vwap"].shift(1))
                        & (dataframe["close"].shift(2) < dataframe["session_vwap"].shift(2))
                    )
                    long_transition = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & dataframe["rvol30"].between(1.2, 4.0)
                        & dataframe["rsi14"].between(46, 72)
                        & dataframe["body_atr"].between(0.04, 1.8)
                        & vwap_excursion_long
                        & reclaim_long
                    )
                    short_transition = (
                        (dataframe["ema21"] < dataframe["ema55"])
                        & dataframe["rvol30"].between(1.2, 4.0)
                        & dataframe["rsi14"].between(28, 54)
                        & dataframe["body_atr"].between(0.04, 1.8)
                        & vwap_excursion_short
                        & reclaim_short
                    )
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(2 * 60, 5 * 60)
                        | dataframe["minute_of_day_ny"].between(9 * 60 + 30, 16 * 60)
                    )
                    raw = killzone_window & (long_transition | short_transition)
                elif "{spec.key}" == "vwap_reclaim_rvol_trend_quality_filter":
                    atr = dataframe["atr96"].clip(lower=0.01)
                    below_excursion = ((dataframe["session_vwap"] - dataframe["low"]) / atr).where(
                        dataframe["session_vwap"].notna()
                    )
                    above_excursion = ((dataframe["high"] - dataframe["session_vwap"]) / atr).where(
                        dataframe["session_vwap"].notna()
                    )
                    max_below_excursion = below_excursion.groupby(dataframe["date"].dt.strftime("%Y-%m-%d")).cummax()
                    max_above_excursion = above_excursion.groupby(dataframe["date"].dt.strftime("%Y-%m-%d")).cummax()
                    long_above_vwap = dataframe["close"] > dataframe["session_vwap"]
                    short_below_vwap = dataframe["close"] < dataframe["session_vwap"]
                    long_persist = long_above_vwap.rolling(5).sum().ge(5)
                    short_persist = short_below_vwap.rolling(5).sum().ge(5)
                    long_reclaim_confirmed = long_persist & (
                        dataframe["close"].shift(5) <= dataframe["session_vwap"].shift(5)
                    )
                    short_reclaim_confirmed = short_persist & (
                        dataframe["close"].shift(5) >= dataframe["session_vwap"].shift(5)
                    )
                    long_aligned_votes = 0
                    long_counter_votes = 0
                    short_aligned_votes = 0
                    short_counter_votes = 0
                    for label in ("5m", "15m", "30m", "1h"):
                        trend_side = pd.Series(0, index=dataframe.index)
                        trend_side = trend_side.mask(
                            (dataframe[f"ema20_{{label}}"] > dataframe[f"ema50_{{label}}"])
                            & (dataframe[f"slope_{{label}}"] > 0),
                            1,
                        )
                        trend_side = trend_side.mask(
                            (dataframe[f"ema20_{{label}}"] < dataframe[f"ema50_{{label}}"])
                            & (dataframe[f"slope_{{label}}"] < 0),
                            -1,
                        )
                        long_aligned_votes = long_aligned_votes + trend_side.eq(1).astype(int)
                        long_counter_votes = long_counter_votes + trend_side.eq(-1).astype(int)
                        short_aligned_votes = short_aligned_votes + trend_side.eq(-1).astype(int)
                        short_counter_votes = short_counter_votes + trend_side.eq(1).astype(int)
                    dataframe["trend_aligned_votes"] = long_aligned_votes.where(
                        long_above_vwap, short_aligned_votes
                    )
                    dataframe["trend_counter_votes"] = long_counter_votes.where(
                        long_above_vwap, short_counter_votes
                    )
                    vwap_dist_atr = (dataframe["close"] - dataframe["session_vwap"]).abs() / atr
                    vwap_quality_persistence = (
                        long_persist
                        | short_persist
                    )
                    trend_quality_ok = (
                        dataframe["trend_counter_votes"].ge(1)
                    )
                    rvol_quality_ok = dataframe["rvol96"].between(0.80, 5.0)
                    distance_quality = vwap_dist_atr.le(0.6)
                    long_quality = (
                        long_reclaim_confirmed
                        & vwap_quality_persistence
                        & trend_quality_ok
                        & dataframe["close"].gt(dataframe["ema32"])
                        & max_below_excursion.ge(0.55)
                        & rvol_quality_ok
                        & distance_quality
                    )
                    short_quality = (
                        short_reclaim_confirmed
                        & vwap_quality_persistence
                        & trend_quality_ok
                        & dataframe["close"].lt(dataframe["ema32"])
                        & max_above_excursion.ge(0.55)
                        & rvol_quality_ok
                        & distance_quality
                    )
                    vwap_quality_any = (long_quality | short_quality).fillna(False)
                    vwap_quality_first_daily = vwap_quality_any & vwap_quality_any.groupby(
                        dataframe["date"].dt.strftime("%Y-%m-%d")
                    ).cumsum().eq(1)
                    long_quality = long_quality & vwap_quality_first_daily
                    short_quality = short_quality & vwap_quality_first_daily
                    raw = long_quality
                    short_raw = short_quality
                elif "{spec.key}" == "midday_compression_failed_break_vwap_fade":
                    atr = dataframe["atr14"].clip(lower=0.01)
                    midday_window = dataframe["minute_of_day_ny"].between(11 * 60, 13 * 60 + 45)
                    compression_high = dataframe["high"].rolling(48).max().shift(1)
                    compression_low = dataframe["low"].rolling(48).min().shift(1)
                    compression_range_atr = (compression_high - compression_low) / atr
                    compression_ok = compression_range_atr.between(0.55, 1.35)
                    failed_break_long = (
                        (dataframe["low"].rolling(4).min() < compression_low - atr * 0.08)
                        & (dataframe["close"] > compression_low)
                        & (dataframe["close"] > dataframe["session_vwap"] - atr * 0.20)
                    )
                    failed_break_short = (
                        (dataframe["high"].rolling(4).max() > compression_high + atr * 0.08)
                        & (dataframe["close"] < compression_high)
                        & (dataframe["close"] < dataframe["session_vwap"] + atr * 0.20)
                    )
                    participation_failure = dataframe["rvol96"].between(0.45, 1.45)
                    local_range_root = dataframe["adx14"].between(8, 26) & dataframe["bar_range_atr"].between(0.04, 1.45)
                    mtf_range_or_transition_votes = 0
                    for label in ("5m", "15m", "30m", "1h"):
                        slope_abs = dataframe[f"slope_{{label}}"].abs()
                        ema_gap = (dataframe[f"ema20_{{label}}"] - dataframe[f"ema50_{{label}}"]).abs()
                        mtf_range_or_transition_votes = mtf_range_or_transition_votes + (
                            slope_abs.le(0.0018) | ema_gap.le(atr * 0.55)
                        ).astype(int)
                    mtf_range_filter = mtf_range_or_transition_votes.ge(2)
                    vwap_distance_ok = ((dataframe["close"] - dataframe["session_vwap"]).abs() / atr).le(0.85)
                    long_fade = (
                        midday_window
                        & compression_ok
                        & failed_break_long.fillna(False)
                        & participation_failure
                        & local_range_root
                        & mtf_range_filter
                        & vwap_distance_ok
                        & dataframe["rsi14"].between(32, 58)
                    )
                    short_fade = (
                        midday_window
                        & compression_ok
                        & failed_break_short.fillna(False)
                        & participation_failure
                        & local_range_root
                        & mtf_range_filter
                        & vwap_distance_ok
                        & dataframe["rsi14"].between(42, 68)
                    )
                    raw = long_fade
                    short_raw = short_fade
                elif "{spec.key}" == "lunch_liquidity_vacuum_vwap_magnet_reversal":
                    atr = dataframe["atr14"].clip(lower=0.01)
                    lunch_window = dataframe["minute_of_day_ny"].between(11 * 60 + 20, 13 * 60 + 40)
                    prior_range = (dataframe["prior_day_high"] - dataframe["prior_day_low"]).abs()
                    local_high = dataframe["high"].rolling(36).max().shift(1)
                    local_low = dataframe["low"].rolling(36).min().shift(1)
                    local_range_atr = (local_high - local_low) / atr
                    liquidity_vacuum = (
                        dataframe["rvol96"].between(0.35, 1.20)
                        & dataframe["bar_range_atr"].between(0.03, 1.25)
                        & local_range_atr.between(0.60, 2.20)
                    )
                    vwap_magnet_distance = (dataframe["close"] - dataframe["session_vwap"]).abs() / atr
                    long_inventory_stretch = (
                        (dataframe["low"].rolling(5).min() < local_low - atr * 0.10)
                        & (dataframe["close"] > local_low)
                        & (dataframe["close"] < dataframe["session_vwap"])
                    )
                    short_inventory_stretch = (
                        (dataframe["high"].rolling(5).max() > local_high + atr * 0.10)
                        & (dataframe["close"] < local_high)
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                    mtf_range_votes = 0
                    for label in ("5m", "15m", "30m", "1h"):
                        slope_abs = dataframe[f"slope_{{label}}"].abs()
                        ema_gap = (dataframe[f"ema20_{{label}}"] - dataframe[f"ema50_{{label}}"]).abs()
                        mtf_range_votes = mtf_range_votes + (
                            slope_abs.le(0.0016) | ema_gap.le(atr * 0.50)
                        ).astype(int)
                    range_context = (
                        mtf_range_votes.ge(2)
                        & dataframe["adx14"].between(7, 28)
                        & prior_range.gt(atr * 1.0)
                    )
                    long_reclaim = (
                        long_inventory_stretch.fillna(False)
                        & (dataframe["close"] > dataframe["low"].rolling(3).max().shift(1))
                        & dataframe["rsi14"].between(30, 58)
                    )
                    short_reclaim = (
                        short_inventory_stretch.fillna(False)
                        & (dataframe["close"] < dataframe["high"].rolling(3).min().shift(1))
                        & dataframe["rsi14"].between(42, 70)
                    )
                    raw = (
                        lunch_window
                        & liquidity_vacuum
                        & range_context.fillna(False)
                        & long_reclaim
                        & vwap_magnet_distance.between(0.18, 1.35)
                    )
                    short_raw = (
                        lunch_window
                        & liquidity_vacuum
                        & range_context.fillna(False)
                        & short_reclaim
                        & vwap_magnet_distance.between(0.18, 1.35)
                    )
                elif "{spec.key}" == "compression_breakout_continuation":
                    compression = ((dataframe["range_high40"] - dataframe["range_low40"]) / dataframe["atr14"]).between(1.0, 8.0)
                    raw = breakout & compression & rvol_ok & rsi_ok & body_ok
                elif "{spec.key}" == "donchian_turtle_breakout":
                    donchian_break = (dataframe["close"] > dataframe["prior_high80"]) & (dataframe["close"].shift(1) <= dataframe["prior_high80"].shift(1))
                    turtle_trend = (dataframe["ema21"] > dataframe["ema55"]) & (dataframe["ema55"] > dataframe["ema144"])
                    raw = donchian_break & turtle_trend & dataframe["rvol96"].between(0.75, 5.5) & dataframe["rsi14"].between(50, 78)
                elif "{spec.key}" == "dense_trend_pullback_reclaim":
                    trend_root = (
                        (dataframe["ema96"] > dataframe["ema390"])
                        & (dataframe["ema32"] > dataframe["ema55"])
                    )
                    pullback_reclaim = (
                        (dataframe["close"].shift(5) < dataframe["ema32"].shift(5))
                        & (dataframe["close"] > dataframe["ema32"])
                        & (dataframe["low"] <= dataframe["ema32"] + dataframe["atr14"] * 0.18)
                    )
                    raw = (
                        trend_root
                        & dataframe["rvol96"].between(0.80, 5.0)
                        & dataframe["rsi14"].between(46, 78)
                        & dataframe["body_atr"].between(0.06, 2.2)
                        & pullback_reclaim
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                elif "{spec.key}" == "prior_day_extreme_continuation":
                    trend_root = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    crossed = dataframe["close"] > dataframe["prior_day_high"]
                    persist = crossed & crossed.shift(1) & crossed.shift(2)
                    impulse = ((dataframe["close"] - dataframe["open"]) / dataframe["atr14"]).between(0.12, 2.8)
                    raw = (
                        trend_root
                        & persist
                        & dataframe["prior_day_range"].gt(dataframe["atr14"] * 1.2)
                        & dataframe["rvol96"].between(0.80, 5.5)
                        & dataframe["rsi14"].between(50, 80)
                        & impulse
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                elif "{spec.key}" == "prior_day_extreme_continuation_mtf_resonance_guard":
                    trend_root = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    crossed = dataframe["close"] > dataframe["prior_day_high"]
                    persist = crossed & crossed.shift(1) & crossed.shift(2)
                    impulse = ((dataframe["close"] - dataframe["open"]) / dataframe["atr14"]).between(0.14, 2.8)
                    mtf_fast_alignment = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema21"] > dataframe["ema21"].shift(5))
                        & (dataframe["close"] > dataframe["ema21"])
                    )
                    mtf_slow_alignment = (
                        (dataframe["ema55"] > dataframe["ema144"])
                        & (dataframe["ema144"] > dataframe["ema390"])
                        & (dataframe["ema144"] > dataframe["ema144"].shift(21))
                    )
                    mtf_resonance_guard = (
                        mtf_fast_alignment
                        & mtf_slow_alignment
                        & dataframe["rvol96"].between(0.90, 5.5)
                        & dataframe["rsi14"].between(52, 78)
                        & dataframe["body_atr"].between(0.10, 2.4)
                    )
                    raw = (
                        trend_root
                        & persist
                        & dataframe["prior_day_range"].gt(dataframe["atr14"] * 1.25)
                        & impulse
                        & mtf_resonance_guard
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                elif "{spec.key}" == "prior_day_extreme_continuation_mtf_resonance_guard_exit_persistence":
                    trend_root = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    crossed = dataframe["close"] > dataframe["prior_day_high"]
                    persist = crossed & crossed.shift(1) & crossed.shift(2)
                    impulse = ((dataframe["close"] - dataframe["open"]) / dataframe["atr14"]).between(0.16, 2.6)
                    mtf_fast_alignment = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema21"] > dataframe["ema21"].shift(5))
                        & (dataframe["close"] > dataframe["ema21"])
                    )
                    mtf_slow_alignment = (
                        (dataframe["ema55"] > dataframe["ema144"])
                        & (dataframe["ema144"] > dataframe["ema390"])
                        & (dataframe["ema144"] > dataframe["ema144"].shift(21))
                    )
                    mtf_resonance_guard = (
                        mtf_fast_alignment
                        & mtf_slow_alignment
                        & dataframe["rvol96"].between(0.95, 5.2)
                        & dataframe["rsi14"].between(54, 76)
                        & dataframe["body_atr"].between(0.12, 2.2)
                    )
                    exit_persistence_window = (
                        dataframe["minute_of_day_ny"].between(9 * 60 + 35, 12 * 60)
                        | dataframe["minute_of_day_ny"].between(13 * 60, 15 * 60 + 30)
                    )
                    persistence_bias = (
                        (dataframe["close"] > dataframe["range_high40"] * 0.996)
                        | ((dataframe["macd_line"] > dataframe["macd_signal"]) & (dataframe["close"] > dataframe["session_vwap"]))
                    )
                    raw = (
                        trend_root
                        & persist
                        & dataframe["prior_day_range"].gt(dataframe["atr14"] * 1.25)
                        & impulse
                        & mtf_resonance_guard
                        & exit_persistence_window
                        & persistence_bias.fillna(False)
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                    exit_persistence_guard = True
                elif "{spec.key}" == "prior_day_extreme_continuation_mtf_resonance_guard_cusum_deadzone_gate":
                    trend_root = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    crossed = dataframe["close"] > dataframe["prior_day_high"]
                    persist = crossed & crossed.shift(1) & crossed.shift(2)
                    impulse = ((dataframe["close"] - dataframe["open"]) / dataframe["atr14"]).between(0.15, 2.7)
                    mtf_fast_alignment = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema21"] > dataframe["ema21"].shift(5))
                        & (dataframe["close"] > dataframe["ema21"])
                    )
                    mtf_slow_alignment = (
                        (dataframe["ema55"] > dataframe["ema144"])
                        & (dataframe["ema144"] > dataframe["ema390"])
                        & (dataframe["ema144"] > dataframe["ema144"].shift(21))
                    )
                    mtf_resonance_guard = (
                        mtf_fast_alignment
                        & mtf_slow_alignment
                        & dataframe["rvol96"].between(0.95, 5.0)
                        & dataframe["rsi14"].between(54, 76)
                        & dataframe["body_atr"].between(0.10, 2.1)
                    )
                    atr_guard = dataframe["atr14"].clip(lower=0.01)
                    displacement = dataframe["close"].diff().fillna(0.0)
                    cusum_step = displacement.where(displacement > 0.0, 0.0) - atr_guard * 0.06
                    cusum_positive_event = cusum_step.rolling(8, min_periods=1).sum() > atr_guard * 0.35
                    deadzone_excursion = ((dataframe["close"] - dataframe["session_vwap"]).abs() / atr_guard).between(0.18, 1.6)
                    rearm_breakout = (
                        (dataframe["close"] > dataframe["range_high40"])
                        & (dataframe["close"].shift(1) <= dataframe["range_high40"].shift(1))
                    )
                    cooldown_trigger = (
                        (dataframe["close"] < dataframe["ema21"])
                        | (dataframe["rsi14"] < 50)
                        | (dataframe["rvol96"] < 0.85)
                    ).fillna(False)
                    cooldown_seed = cooldown_trigger.astype(int) * 10
                    cooldown_bars_remaining = (
                        cooldown_seed.rolling(10, min_periods=1).max().shift(1).fillna(0)
                    )
                    raw = (
                        trend_root
                        & persist
                        & dataframe["prior_day_range"].gt(atr_guard * 1.25)
                        & impulse
                        & mtf_resonance_guard
                        & cusum_positive_event.fillna(False)
                        & deadzone_excursion.fillna(False)
                        & rearm_breakout.fillna(False)
                        & cooldown_bars_remaining.le(0)
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                elif "{spec.key}" == "prior_day_extreme_continuation_mtf_resonance_guard_killzone_filter":
                    trend_root = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    crossed = dataframe["close"] > dataframe["prior_day_high"]
                    persist = crossed & crossed.shift(1) & crossed.shift(2)
                    impulse = ((dataframe["close"] - dataframe["open"]) / dataframe["atr14"]).between(0.14, 2.7)
                    mtf_fast_alignment = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema21"] > dataframe["ema21"].shift(5))
                        & (dataframe["close"] > dataframe["ema21"])
                    )
                    mtf_slow_alignment = (
                        (dataframe["ema55"] > dataframe["ema144"])
                        & (dataframe["ema144"] > dataframe["ema390"])
                        & (dataframe["ema144"] > dataframe["ema144"].shift(21))
                    )
                    mtf_resonance_guard = (
                        mtf_fast_alignment
                        & mtf_slow_alignment
                        & dataframe["rvol96"].between(0.95, 5.0)
                        & dataframe["rsi14"].between(54, 76)
                        & dataframe["body_atr"].between(0.10, 2.1)
                    )
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(9 * 60 + 35, 12 * 60)
                        | dataframe["minute_of_day_ny"].between(13 * 60, 15 * 60 + 30)
                    )
                    session_participation = (
                        dataframe["rvol96"].between(1.00, 4.8)
                        & dataframe["body_atr"].between(0.14, 2.2)
                    )
                    prior_day_retest = (
                        ((dataframe["close"] - dataframe["prior_day_high"]) / dataframe["atr14"].clip(lower=0.01))
                        .between(0.00, 0.85)
                    )
                    raw = (
                        trend_root
                        & persist
                        & dataframe["prior_day_range"].gt(dataframe["atr14"] * 1.25)
                        & impulse
                        & mtf_resonance_guard
                        & killzone_window
                        & session_participation
                        & prior_day_retest.fillna(False)
                        & (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["close"] > dataframe["ema21"])
                    )
                elif "{spec.key}" == "prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard":
                    trend_root = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    crossed = dataframe["close"] > dataframe["prior_day_high"]
                    persist = crossed & crossed.shift(1) & crossed.shift(2)
                    impulse = ((dataframe["close"] - dataframe["open"]) / dataframe["atr14"]).between(0.16, 2.4)
                    mtf_fast_alignment = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema21"] > dataframe["ema21"].shift(5))
                        & (dataframe["close"] > dataframe["ema21"])
                    )
                    mtf_slow_alignment = (
                        (dataframe["ema55"] > dataframe["ema144"])
                        & (dataframe["ema144"] > dataframe["ema390"])
                        & (dataframe["ema144"] > dataframe["ema144"].shift(21))
                    )
                    mtf_resonance_guard = (
                        mtf_fast_alignment
                        & mtf_slow_alignment
                        & dataframe["rsi14"].between(55, 74)
                        & dataframe["body_atr"].between(0.12, 1.8)
                    )
                    participation_impulse = (
                        dataframe["rvol96"].between(1.10, 3.8)
                        & dataframe["body_atr"].between(0.18, 1.9)
                    )
                    volume_acceptance = (
                        dataframe["close_location"].between(0.58, 0.98)
                        & dataframe["volume"].gt(dataframe["vol96"].fillna(0) * 1.10)
                    )
                    trend_efficiency_guard = (
                        ((dataframe["close"] - dataframe["ema21"]) / dataframe["atr14"].clip(lower=0.01)).between(0.10, 1.10)
                        & ((dataframe["ema21"] - dataframe["ema55"]) / dataframe["atr14"].clip(lower=0.01)).between(0.08, 1.60)
                    )
                    retest_efficiency = (
                        ((dataframe["close"] - dataframe["prior_day_high"]) / dataframe["atr14"].clip(lower=0.01))
                        .between(0.06, 0.72)
                    )
                    raw = (
                        trend_root
                        & persist
                        & dataframe["prior_day_range"].gt(dataframe["atr14"] * 1.20)
                        & impulse
                        & mtf_resonance_guard
                        & participation_impulse
                        & volume_acceptance.fillna(False)
                        & trend_efficiency_guard.fillna(False)
                        & retest_efficiency.fillna(False)
                        & (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["close"] > dataframe["ema21"])
                    )
                elif "{spec.key}" == "prior_day_extreme_continuation_mtf_resonance_guard_participation_quality_guard_nq_cadence_lift":
                    trend_root = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    crossed = dataframe["close"] > dataframe["prior_day_high"]
                    persist = crossed & crossed.shift(1) & crossed.shift(2)
                    impulse = ((dataframe["close"] - dataframe["open"]) / dataframe["atr14"]).between(0.12, 2.6)
                    mtf_fast_alignment = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema21"] > dataframe["ema21"].shift(5))
                        & (dataframe["close"] > dataframe["ema21"])
                    )
                    mtf_slow_alignment = (
                        (dataframe["ema55"] > dataframe["ema144"])
                        & (dataframe["ema144"] > dataframe["ema390"])
                        & (dataframe["ema144"] > dataframe["ema144"].shift(21))
                    )
                    mtf_resonance_guard = (
                        mtf_fast_alignment
                        & mtf_slow_alignment
                        & dataframe["rsi14"].between(52, 76)
                        & dataframe["body_atr"].between(0.10, 2.0)
                    )
                    participation_impulse = (
                        dataframe["rvol96"].between(0.92, 4.2)
                        & dataframe["body_atr"].between(0.12, 2.0)
                    )
                    volume_acceptance = (
                        dataframe["close_location"].between(0.52, 0.99)
                        & dataframe["volume"].gt(dataframe["vol96"].fillna(0) * 0.92)
                    )
                    trend_efficiency_guard = (
                        ((dataframe["close"] - dataframe["ema21"]) / dataframe["atr14"].clip(lower=0.01)).between(0.04, 1.35)
                        & ((dataframe["ema21"] - dataframe["ema55"]) / dataframe["atr14"].clip(lower=0.01)).between(0.04, 1.80)
                    )
                    retest_efficiency = (
                        ((dataframe["close"] - dataframe["prior_day_high"]) / dataframe["atr14"].clip(lower=0.01))
                        .between(0.02, 0.88)
                    )
                    first_chance_window = dataframe["minute_of_day_ny"].between(9 * 60 + 35, 10 * 60 + 20)
                    late_morning_window = dataframe["minute_of_day_ny"].between(10 * 60 + 20, 11 * 60 + 55)
                    post_lunch_window = dataframe["minute_of_day_ny"].between(13 * 60, 15 * 60 + 30)
                    second_chance_reclaim = (
                        (dataframe["low"] <= dataframe["prior_day_high"] + dataframe["atr14"] * 0.24)
                        & (dataframe["close"] > dataframe["prior_day_high"])
                        & (dataframe["close"] > dataframe["open"])
                    )
                    raw = (
                        trend_root
                        & dataframe["prior_day_range"].gt(dataframe["atr14"] * 1.10)
                        & mtf_resonance_guard
                        & participation_impulse
                        & volume_acceptance.fillna(False)
                        & trend_efficiency_guard.fillna(False)
                        & (
                            (
                                first_chance_window
                                & persist
                                & impulse
                                & retest_efficiency.fillna(False)
                            )
                            | (
                                (late_morning_window | post_lunch_window)
                                & crossed
                                & second_chance_reclaim.fillna(False)
                                & dataframe["rsi14"].between(50, 78)
                                & dataframe["body_atr"].between(0.08, 1.7)
                            )
                        )
                        & (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["close"] > dataframe["ema21"])
                    )
                elif "{spec.key}" == "prior_day_liquidity_sweep_reversal":
                    reversal_window = dataframe["minute_of_day_ny"].between(9 * 60 + 35, 14 * 60 + 30)
                    sweep_depth = (dataframe["prior_day_low"] - dataframe["low"]) / dataframe["atr14"].clip(lower=0.01)
                    sweep_reclaim = (
                        (dataframe["low"] < dataframe["prior_day_low"])
                        & (dataframe["close"] > dataframe["prior_day_low"])
                    )
                    reclaim_impulse = ((dataframe["close"] - dataframe["open"]) / dataframe["atr14"].clip(lower=0.01)).between(0.08, 2.4)
                    down_extension = dataframe["close"].shift(1) < dataframe["ema21"].shift(1)
                    raw = (
                        reversal_window
                        & dataframe["prior_day_range"].gt(dataframe["atr14"] * 1.0)
                        & dataframe["rvol96"].between(0.75, 5.0)
                        & dataframe["rsi14"].between(32, 60)
                        & dataframe["body_atr"].between(0.08, 2.4)
                        & sweep_depth.between(0.05, 1.4)
                        & sweep_reclaim
                        & reclaim_impulse
                        & down_extension
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                elif "{spec.key}" == "prior_day_multifactor_confluence_volume_reclaim":
                    trading_window = (
                        dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)
                        | dataframe["minute_of_day_ny"].between(13 * 60 + 30, 15 * 60 + 30)
                    )
                    extreme_wpr_long = dataframe["wpr14"].lt(-85)
                    extreme_wpr_short = dataframe["wpr14"].gt(-15)
                    extreme_rsi_long = dataframe["rsi14"].lt(25)
                    extreme_rsi_short = dataframe["rsi14"].gt(75)
                    price_sweep_long = (
                        (dataframe["low"] < dataframe["prior_day_low"])
                        & (dataframe["close"] > dataframe["prior_day_low"])
                    )
                    price_sweep_short = (
                        (dataframe["high"] > dataframe["prior_day_high"])
                        & (dataframe["close"] < dataframe["prior_day_high"])
                    )
                    volume_confirm = dataframe["rvol20"].gt(1.2)
                    low_vol_env = dataframe["atr14"] < dataframe["atr_ma50"]
                    trend_ok_long = dataframe["ema20"] > dataframe["ema50"]
                    trend_ok_short = dataframe["ema20"] < dataframe["ema50"]
                    long_score = (
                        extreme_wpr_long.astype(int)
                        + extreme_rsi_long.astype(int)
                        + price_sweep_long.astype(int)
                        + volume_confirm.astype(int)
                        + low_vol_env.astype(int)
                        + trend_ok_long.astype(int)
                    )
                    short_score = (
                        extreme_wpr_short.astype(int)
                        + extreme_rsi_short.astype(int)
                        + price_sweep_short.astype(int)
                        + volume_confirm.astype(int)
                        + low_vol_env.astype(int)
                        + trend_ok_short.astype(int)
                    )
                    raw = trading_window & long_score.ge(4)
                    short_raw = trading_window & short_score.ge(4)
                elif "{spec.key}" == "fractal_liquidity_macd_rsi_divergence_reclaim":
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)
                        | dataframe["minute_of_day_ny"].between(13 * 60 + 30, 15 * 60 + 50)
                    )
                    midnight_discount = (
                        (dataframe["close"] < dataframe["midnight_open"])
                        & (dataframe["close"] > dataframe["midnight_open"] - dataframe["atr14"] * 1.2)
                    )
                    midnight_premium = (
                        (dataframe["close"] > dataframe["midnight_open"])
                        & (dataframe["close"] < dataframe["midnight_open"] + dataframe["atr14"] * 1.2)
                    )
                    higher_frame_bias_long = (
                        (dataframe["ema144"] > dataframe["ema390"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    higher_frame_bias_short = (
                        (dataframe["ema144"] < dataframe["ema390"])
                        & (dataframe["ema55"] < dataframe["ema144"])
                    )
                    structure_bias_long = higher_frame_bias_long & midnight_discount
                    structure_bias_short = higher_frame_bias_short & midnight_premium
                    fractal_sweep_long = (
                        ((dataframe["low"] < dataframe["liq_low20"]) & (dataframe["close"] > dataframe["liq_low20"]))
                        | ((dataframe["low"] < dataframe["liq_low60"]) & (dataframe["close"] > dataframe["liq_low60"]))
                        | ((dataframe["low"] < dataframe["prior_day_low"]) & (dataframe["close"] > dataframe["prior_day_low"]))
                    )
                    fractal_sweep_short = (
                        ((dataframe["high"] > dataframe["liq_high20"]) & (dataframe["close"] < dataframe["liq_high20"]))
                        | ((dataframe["high"] > dataframe["liq_high60"]) & (dataframe["close"] < dataframe["liq_high60"]))
                        | ((dataframe["high"] > dataframe["prior_day_high"]) & (dataframe["close"] < dataframe["prior_day_high"]))
                    )
                    macd_bullish_divergence = (
                        (dataframe["macd_line"] > dataframe["macd_line"].shift(5))
                        & (dataframe["close"] <= dataframe["close"].shift(5))
                    )
                    macd_bearish_divergence = (
                        (dataframe["macd_line"] < dataframe["macd_line"].shift(5))
                        & (dataframe["close"] >= dataframe["close"].shift(5))
                    )
                    raw = (
                        killzone_window
                        & (
                            (
                                structure_bias_long.fillna(False)
                                & fractal_sweep_long.fillna(False)
                                & macd_bullish_divergence.fillna(False)
                                & dataframe["rsi14"].gt(30)
                            )
                            | (
                                structure_bias_short.fillna(False)
                                & fractal_sweep_short.fillna(False)
                                & macd_bearish_divergence.fillna(False)
                                & dataframe["rsi14"].lt(70)
                            )
                        )
                        & dataframe["rvol96"].between(0.70, 5.2)
                        & dataframe["body_atr"].between(0.08, 2.2)
                    )
                elif "{spec.key}" == "fractal_liquidity_macd_divergence_reclaim":
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)
                        | dataframe["minute_of_day_ny"].between(13 * 60 + 30, 15 * 60 + 50)
                    )
                    midnight_discount = (
                        (dataframe["close"] < dataframe["midnight_open"])
                        & (dataframe["close"] > dataframe["midnight_open"] - dataframe["atr14"] * 1.2)
                    )
                    midnight_premium = (
                        (dataframe["close"] > dataframe["midnight_open"])
                        & (dataframe["close"] < dataframe["midnight_open"] + dataframe["atr14"] * 1.2)
                    )
                    higher_frame_bias_long = (
                        (dataframe["ema144"] > dataframe["ema390"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    higher_frame_bias_short = (
                        (dataframe["ema144"] < dataframe["ema390"])
                        & (dataframe["ema55"] < dataframe["ema144"])
                    )
                    structure_bias_long = higher_frame_bias_long & midnight_discount
                    structure_bias_short = higher_frame_bias_short & midnight_premium
                    fractal_sweep_long = (
                        ((dataframe["low"] < dataframe["liq_low20"]) & (dataframe["close"] > dataframe["liq_low20"]))
                        | ((dataframe["low"] < dataframe["liq_low60"]) & (dataframe["close"] > dataframe["liq_low60"]))
                        | ((dataframe["low"] < dataframe["prior_day_low"]) & (dataframe["close"] > dataframe["prior_day_low"]))
                    )
                    fractal_sweep_short = (
                        ((dataframe["high"] > dataframe["liq_high20"]) & (dataframe["close"] < dataframe["liq_high20"]))
                        | ((dataframe["high"] > dataframe["liq_high60"]) & (dataframe["close"] < dataframe["liq_high60"]))
                        | ((dataframe["high"] > dataframe["prior_day_high"]) & (dataframe["close"] < dataframe["prior_day_high"]))
                    )
                    macd_bullish_divergence = (
                        (dataframe["macd_line"] > dataframe["macd_line"].shift(5))
                        & (dataframe["close"] <= dataframe["close"].shift(5))
                    )
                    macd_bearish_divergence = (
                        (dataframe["macd_line"] < dataframe["macd_line"].shift(5))
                        & (dataframe["close"] >= dataframe["close"].shift(5))
                    )
                    raw = (
                        killzone_window
                        & (
                            (
                                structure_bias_long.fillna(False)
                                & fractal_sweep_long.fillna(False)
                                & macd_bullish_divergence.fillna(False)
                            )
                            | (
                                structure_bias_short.fillna(False)
                                & fractal_sweep_short.fillna(False)
                                & macd_bearish_divergence.fillna(False)
                            )
                        )
                        & dataframe["rvol96"].between(0.70, 5.2)
                        & dataframe["body_atr"].between(0.08, 2.2)
                    )
                elif "{spec.key}" == "impulse_follow":
                    trend_root = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    continuation = (
                        (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["close"] > dataframe["ema21"])
                        & (dataframe["close"] > dataframe["close"].shift(1))
                    )
                    raw = (
                        trend_root
                        & continuation
                        & dataframe["rvol96"].between(0.85, 6.0)
                        & dataframe["rsi14"].between(52, 82)
                        & dataframe["body_atr"].between(0.45, 3.2)
                        & dataframe["bar_range_atr"].between(0.80, 4.0)
                    )
                elif "{spec.key}" == "impulse_follow_hold_persistence":
                    trend_root = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    continuation = (
                        (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["close"] > dataframe["ema21"])
                        & (dataframe["close"] > dataframe["close"].shift(1))
                    )
                    hold_persistence = (
                        (dataframe["close"].shift(1) > dataframe["session_vwap"].shift(1))
                        & (dataframe["close"].shift(1) > dataframe["ema21"].shift(1))
                        & (dataframe["close"].shift(2) > dataframe["session_vwap"].shift(2))
                        & (dataframe["close"].shift(2) > dataframe["ema21"].shift(2))
                    )
                    raw = (
                        trend_root
                        & continuation
                        & hold_persistence.fillna(False)
                        & dataframe["rvol96"].between(1.10, 6.0)
                        & dataframe["rsi14"].between(54, 80)
                        & dataframe["body_atr"].between(0.38, 2.8)
                        & dataframe["bar_range_atr"].between(0.75, 3.6)
                    )
                elif "{spec.key}" == "wpr_extreme_mean_reclaim":
                    trend_root = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                        & (dataframe["close"] > dataframe["ema21"])
                    )
                    liquidity_reclaim = (
                        (dataframe["low"] <= dataframe["range_low40"])
                        & (dataframe["close"] > dataframe["range_low40"])
                    )
                    raw = (
                        trend_root
                        & liquidity_reclaim
                        & dataframe["wpr14"].lt(-80)
                        & dataframe["rvol96"].between(0.70, 4.8)
                        & dataframe["rsi14"].between(38, 68)
                        & dataframe["body_atr"].between(0.06, 1.8)
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                elif "{spec.key}" == "wpr_fractal_no_be_fulltarget":
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)
                        | dataframe["minute_of_day_ny"].between(13 * 60 + 30, 16 * 60)
                    )
                    short_liquidity_sweep = (
                        (dataframe["high"] > dataframe["prior_day_high"])
                        | (dataframe["high"] > dataframe["bsl_fractal"])
                        | (dataframe["high"] > dataframe["liq_high20"])
                    )
                    liquidity_sweep = (
                        (dataframe["low"] < dataframe["prior_day_low"])
                        | (dataframe["low"] < dataframe["ssl_fractal"])
                        | (dataframe["low"] < dataframe["liq_low20"])
                    )
                    short_wpr_reclaim = (
                        (
                            ((dataframe["high"] > dataframe["prior_day_high"]) & (dataframe["close"] < dataframe["prior_day_high"]))
                            | ((dataframe["high"] > dataframe["bsl_fractal"]) & (dataframe["close"] < dataframe["bsl_fractal"]))
                            | ((dataframe["high"] > dataframe["liq_high20"]) & (dataframe["close"] < dataframe["liq_high20"]))
                        )
                        & (dataframe["close"] < dataframe["open"])
                        & dataframe["wpr14"].gt(-20)
                    )
                    wpr_reclaim = (
                        (
                            ((dataframe["low"] < dataframe["prior_day_low"]) & (dataframe["close"] > dataframe["prior_day_low"]))
                            | ((dataframe["low"] < dataframe["ssl_fractal"]) & (dataframe["close"] > dataframe["ssl_fractal"]))
                            | ((dataframe["low"] < dataframe["liq_low20"]) & (dataframe["close"] > dataframe["liq_low20"]))
                        )
                        & (dataframe["close"] > dataframe["open"])
                        & dataframe["wpr14"].lt(-80)
                    )
                    long_risk_points = dataframe["close"] - dataframe["low"] + dataframe["atr14"]
                    short_risk_points = dataframe["high"] - dataframe["close"] + dataframe["atr14"]
                    full_target_bias = dataframe["atr14"].ge(0.75) & long_risk_points.between(1.5, 15.0)
                    short_full_target_bias = dataframe["atr14"].ge(0.75) & short_risk_points.between(1.5, 15.0)
                    raw = (
                        killzone_window
                        & liquidity_sweep.fillna(False)
                        & wpr_reclaim.fillna(False)
                        & full_target_bias.fillna(False)
                    )
                    short_raw = (
                        killzone_window
                        & short_liquidity_sweep.fillna(False)
                        & short_wpr_reclaim.fillna(False)
                        & short_full_target_bias.fillna(False)
                    )
                elif "{spec.key}" == "wpr_fractal_no_be_session_bias_cap":
                    session_bias_cap_window = dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)
                    liquidity_sweep = (
                        (dataframe["low"] < dataframe["prior_day_low"])
                        | (dataframe["low"] < dataframe["liq_low20"])
                    )
                    wpr_reclaim = (
                        (dataframe["close"] > dataframe["prior_day_low"].fillna(dataframe["liq_low20"]))
                        & (dataframe["close"] > dataframe["open"])
                        & dataframe["wpr14"].lt(-82)
                    )
                    session_open_bias = (
                        (dataframe["close"] > dataframe["session_open"])
                        & (dataframe["session_vwap"] > dataframe["session_open"] * 0.9985)
                    )
                    vwap_hold = (
                        (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["close"].shift(1) > dataframe["session_vwap"].shift(1))
                    )
                    raw = (
                        session_bias_cap_window
                        & liquidity_sweep.fillna(False)
                        & wpr_reclaim.fillna(False)
                        & session_open_bias.fillna(False)
                        & vwap_hold.fillna(False)
                        & dataframe["rvol96"].between(0.95, 5.5)
                        & dataframe["rsi14"].between(26, 58)
                        & dataframe["body_atr"].between(0.08, 2.4)
                    )
                elif "{spec.key}" == "wpr_fractal_no_be_higher_frame_slope_confirm":
                    liquidity_sweep = (
                        (dataframe["low"] < dataframe["prior_day_low"])
                        | (dataframe["low"] < dataframe["liq_low20"])
                    )
                    wpr_reclaim = (
                        (dataframe["close"] > dataframe["prior_day_low"].fillna(dataframe["liq_low20"]))
                        & (dataframe["close"] > dataframe["open"])
                        & dataframe["wpr14"].lt(-82)
                    )
                    ema55_slope_atr = (
                        (dataframe["ema55"] - dataframe["ema55"].shift(30))
                        / dataframe["atr14"].clip(lower=0.01)
                    )
                    ema144_slope_atr = (
                        (dataframe["ema144"] - dataframe["ema144"].shift(90))
                        / dataframe["atr14"].clip(lower=0.01)
                    )
                    higher_frame_slope_confirm = (
                        (dataframe["ema55"] > dataframe["ema144"])
                        & (dataframe["ema144"] > dataframe["ema390"])
                        & ema55_slope_atr.between(0.04, 3.5)
                        & ema144_slope_atr.between(0.06, 5.5)
                    )
                    vwap_hold = (
                        (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["close"].shift(1) > dataframe["session_vwap"].shift(1))
                    )
                    raw = (
                        liquidity_sweep.fillna(False)
                        & wpr_reclaim.fillna(False)
                        & higher_frame_slope_confirm.fillna(False)
                        & vwap_hold.fillna(False)
                        & (dataframe["close"] > dataframe["ema21"])
                        & dataframe["rvol96"].between(0.85, 4.5)
                        & dataframe["rsi14"].between(30, 62)
                        & dataframe["body_atr"].between(0.06, 2.0)
                    )
                elif "{spec.key}" == "wpr_fractal_ict_zone_reclaim":
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(2 * 60, 5 * 60)
                        | dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)
                        | dataframe["minute_of_day_ny"].between(13 * 60 + 30, 15 * 60 + 30)
                    )
                    liquidity_sweep = (
                        ((dataframe["low"].shift(1) <= dataframe["prior_day_low"].shift(1)) & (dataframe["close"] > dataframe["prior_day_low"]))
                        | ((dataframe["low"].shift(1) <= dataframe["confirmed_ssl"].shift(1)) & (dataframe["close"] > dataframe["confirmed_ssl"]))
                    )
                    short_liquidity_sweep = (
                        ((dataframe["high"].shift(1) >= dataframe["prior_day_high"].shift(1)) & (dataframe["close"] < dataframe["prior_day_high"]))
                        | ((dataframe["high"].shift(1) >= dataframe["confirmed_bsl"].shift(1)) & (dataframe["close"] < dataframe["confirmed_bsl"]))
                    )
                    wpr_reclaim = (
                        dataframe["wpr14"].lt(-82)
                        & (dataframe["wpr14"] > dataframe["wpr14"].shift(1))
                        & (dataframe["close"] > dataframe["open"])
                    )
                    short_wpr_reclaim = (
                        dataframe["wpr14"].gt(-18)
                        & (dataframe["wpr14"] < dataframe["wpr14"].shift(1))
                        & (dataframe["close"] < dataframe["open"])
                    )
                    ict_zone = (
                        dataframe["close"].between(dataframe["bull_ob_low"], dataframe["bull_ob_high"])
                        | dataframe["bull_fvg"].fillna(False)
                        | (dataframe["low"] <= dataframe["prev2_high"] * 1.002)
                    )
                    short_ict_zone = (
                        dataframe["close"].between(dataframe["bear_ob_low"], dataframe["bear_ob_high"])
                        | dataframe["bear_fvg"].fillna(False)
                        | (dataframe["high"] >= dataframe["prev2_low"] * 0.998)
                    )
                    volume_confirmation = dataframe["rvol96"].between(0.85, 5.5)
                    raw = (
                        killzone_window
                        & liquidity_sweep.fillna(False)
                        & wpr_reclaim.fillna(False)
                        & ict_zone.fillna(False)
                        & volume_confirmation
                        & dataframe["rsi14"].between(24, 60)
                        & dataframe["body_atr"].between(0.06, 2.4)
                    )
                    short_raw = (
                        killzone_window
                        & short_liquidity_sweep.fillna(False)
                        & short_wpr_reclaim.fillna(False)
                        & short_ict_zone.fillna(False)
                        & volume_confirmation
                        & dataframe["rsi14"].between(40, 76)
                        & dataframe["body_atr"].between(0.06, 2.4)
                    )
                elif "{spec.key}" == "wpr_adx_fractal_sweep_reclaim":
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)
                        | dataframe["minute_of_day_ny"].between(13 * 60 + 30, 15 * 60 + 30)
                    )
                    liquidity_sweep = (
                        ((dataframe["low"] < dataframe["prior_day_low"]) & (dataframe["close"] > dataframe["prior_day_low"]))
                        | ((dataframe["low"] < dataframe["confirmed_ssl"]) & (dataframe["close"] > dataframe["confirmed_ssl"]))
                    )
                    short_liquidity_sweep = (
                        ((dataframe["high"] > dataframe["prior_day_high"]) & (dataframe["close"] < dataframe["prior_day_high"]))
                        | ((dataframe["high"] > dataframe["confirmed_bsl"]) & (dataframe["close"] < dataframe["confirmed_bsl"]))
                    )
                    hour_open_bias = dataframe["close"] > dataframe["hour_open"]
                    short_hour_open_bias = dataframe["close"] < dataframe["hour_open"]
                    volume_ratio_ok = dataframe["volume_ratio"] > 0.8
                    adx_ok = dataframe["adx14"] > 25
                    raw = (
                        killzone_window
                        & liquidity_sweep.fillna(False)
                        & dataframe["wpr14"].lt(-75)
                        & hour_open_bias.fillna(False)
                        & volume_ratio_ok.fillna(False)
                        & adx_ok.fillna(False)
                    )
                    short_raw = (
                        killzone_window
                        & short_liquidity_sweep.fillna(False)
                        & dataframe["wpr14"].gt(-25)
                        & short_hour_open_bias.fillna(False)
                        & volume_ratio_ok.fillna(False)
                        & adx_ok.fillna(False)
                    )
                elif "{spec.key}" == "wpr_adx_hurst_profile_mss_reclaim":
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)
                        | dataframe["minute_of_day_ny"].between(13 * 60 + 30, 15 * 60 + 30)
                    )
                    liquidity_sweep = (
                        ((dataframe["low"] < dataframe["prior_day_low"]) & (dataframe["close"] > dataframe["prior_day_low"]))
                        | ((dataframe["low"] < dataframe["confirmed_ssl"]) & (dataframe["close"] > dataframe["confirmed_ssl"]))
                    )
                    short_liquidity_sweep = (
                        ((dataframe["high"] > dataframe["prior_day_high"]) & (dataframe["close"] < dataframe["prior_day_high"]))
                        | ((dataframe["high"] > dataframe["confirmed_bsl"]) & (dataframe["close"] < dataframe["confirmed_bsl"]))
                    )
                    wpr_rehook_long = dataframe["wpr14"].lt(-75) & dataframe["wpr14"].gt(dataframe["wpr14"].shift(1))
                    wpr_rehook_short = dataframe["wpr14"].gt(-25) & dataframe["wpr14"].lt(dataframe["wpr14"].shift(1))
                    hour_open_bias = dataframe["close"] > dataframe["hour_open"]
                    short_hour_open_bias = dataframe["close"] < dataframe["hour_open"]
                    volume_ratio_ok = dataframe["volume_ratio"] > 0.8
                    adx_ok = dataframe["adx14"].between(22, 48)
                    hurst_ok = dataframe["hurst64"].lt(0.46) & dataframe["hurst128"].lt(0.49)
                    higher_frame_range_ok = (
                        (dataframe["slope_15m"].abs() / dataframe["atr14"].clip(lower=0.01)).le(1.8)
                        & (dataframe["slope_30m"].abs() / dataframe["atr14"].clip(lower=0.01)).le(2.6)
                    )
                    profile_long = (
                        (
                            ((dataframe["low"] < dataframe["profile_val96"]) & (dataframe["close"] > dataframe["profile_val96"]))
                            | ((dataframe["low"] < dataframe["profile_poc96"]) & (dataframe["close"] > dataframe["profile_poc96"]))
                        )
                        & dataframe["profile_poc96"].notna()
                        & dataframe["profile_poc_dist_atr"].le(0.55)
                    )
                    profile_short = (
                        (
                            ((dataframe["high"] > dataframe["profile_vah96"]) & (dataframe["close"] < dataframe["profile_vah96"]))
                            | ((dataframe["high"] > dataframe["profile_poc96"]) & (dataframe["close"] < dataframe["profile_poc96"]))
                        )
                        & dataframe["profile_poc96"].notna()
                        & dataframe["profile_poc_dist_atr"].le(0.55)
                    )
                    structure_long = (
                        dataframe["bull_mss"].fillna(False)
                        | (dataframe["bull_fvg"].fillna(False) & (dataframe["close"] > dataframe["ema21"]))
                    )
                    structure_short = (
                        dataframe["bear_mss"].fillna(False)
                        | (dataframe["bear_fvg"].fillna(False) & (dataframe["close"] < dataframe["ema21"]))
                    )
                    raw = (
                        killzone_window
                        & liquidity_sweep.fillna(False)
                        & wpr_rehook_long.fillna(False)
                        & hour_open_bias.fillna(False)
                        & volume_ratio_ok.fillna(False)
                        & adx_ok.fillna(False)
                        & hurst_ok.fillna(False)
                        & higher_frame_range_ok.fillna(False)
                        & profile_long.fillna(False)
                        & structure_long.fillna(False)
                    )
                    short_raw = (
                        killzone_window
                        & short_liquidity_sweep.fillna(False)
                        & wpr_rehook_short.fillna(False)
                        & short_hour_open_bias.fillna(False)
                        & volume_ratio_ok.fillna(False)
                        & adx_ok.fillna(False)
                        & hurst_ok.fillna(False)
                        & higher_frame_range_ok.fillna(False)
                        & profile_short.fillna(False)
                        & structure_short.fillna(False)
                    )
                elif "{spec.key}" == "value_area_vpoc_htf_trend_mss_filter":
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(9 * 60 + 35, 11 * 60 + 30)
                        | dataframe["minute_of_day_ny"].between(13 * 60, 15 * 60 + 30)
                    )
                    fast_long_votes = pd.Series(0, index=dataframe.index, dtype=int)
                    fast_short_votes = pd.Series(0, index=dataframe.index, dtype=int)
                    slow_long_votes = pd.Series(0, index=dataframe.index, dtype=int)
                    slow_short_votes = pd.Series(0, index=dataframe.index, dtype=int)
                    counter_long_votes = pd.Series(0, index=dataframe.index, dtype=int)
                    counter_short_votes = pd.Series(0, index=dataframe.index, dtype=int)
                    for label in ("5m", "15m", "30m", "1h", "4h", "1d"):
                        aligned_long = (
                            (dataframe[f"ema20_{{label}}"] > dataframe[f"ema50_{{label}}"])
                            & (dataframe[f"slope_{{label}}"] > 0)
                        )
                        aligned_short = (
                            (dataframe[f"ema20_{{label}}"] < dataframe[f"ema50_{{label}}"])
                            & (dataframe[f"slope_{{label}}"] < 0)
                        )
                        if label in ("5m", "15m", "30m"):
                            fast_long_votes = fast_long_votes + aligned_long.fillna(False).astype(int)
                            fast_short_votes = fast_short_votes + aligned_short.fillna(False).astype(int)
                        else:
                            slow_long_votes = slow_long_votes + aligned_long.fillna(False).astype(int)
                            slow_short_votes = slow_short_votes + aligned_short.fillna(False).astype(int)
                        counter_long_votes = counter_long_votes + aligned_short.fillna(False).astype(int)
                        counter_short_votes = counter_short_votes + aligned_long.fillna(False).astype(int)
                    trend_resonance_long = (
                        fast_long_votes.ge(2)
                        & slow_long_votes.ge(1)
                        & counter_long_votes.le(1)
                    )
                    trend_resonance_short = (
                        fast_short_votes.ge(2)
                        & slow_short_votes.ge(1)
                        & counter_short_votes.le(1)
                    )
                    vpoc_reclaim_long = (
                        dataframe["session_profile_poc_price"].notna()
                        & (dataframe["low"] <= dataframe["session_profile_poc_price"] + dataframe["atr14"] * 0.10)
                        & (dataframe["close"] > dataframe["session_profile_poc_price"])
                    )
                    vpoc_reclaim_short = (
                        dataframe["session_profile_poc_price"].notna()
                        & (dataframe["high"] >= dataframe["session_profile_poc_price"] - dataframe["atr14"] * 0.10)
                        & (dataframe["close"] < dataframe["session_profile_poc_price"])
                    )
                    value_area_reaccept_long = (
                        dataframe["session_profile_val"].notna()
                        & (dataframe["low"] < dataframe["session_profile_val"])
                        & (dataframe["close"] > dataframe["session_profile_val"])
                    )
                    value_area_reaccept_short = (
                        dataframe["session_profile_vah"].notna()
                        & (dataframe["high"] > dataframe["session_profile_vah"])
                        & (dataframe["close"] < dataframe["session_profile_vah"])
                    )
                    value_area_acceptance_long = (
                        dataframe["session_profile_value_area_pos"].between(0.55, 1.45)
                        & dataframe["session_profile_poc_dist_atr"].between(0.0, 1.25)
                        & dataframe["session_or_breakout_atr"].gt(-0.10)
                        & dataframe["session_ib_breakout_atr"].gt(-0.10)
                        & dataframe["session_profile_rotation_factor"].between(0.90, 5.50)
                    )
                    value_area_acceptance_short = (
                        dataframe["session_profile_value_area_pos"].between(-0.45, 0.45)
                        & dataframe["session_profile_poc_dist_atr"].between(-1.25, 0.0)
                        & dataframe["session_or_breakout_atr"].lt(0.10)
                        & dataframe["session_ib_breakout_atr"].lt(0.10)
                        & dataframe["session_profile_rotation_factor"].between(0.90, 5.50)
                    )
                    structure_confirm_long = (
                        dataframe["bull_mss"].fillna(False)
                        | (dataframe["bull_fvg"].fillna(False) & (dataframe["close"] > dataframe["ema21"]))
                    )
                    structure_confirm_short = (
                        dataframe["bear_mss"].fillna(False)
                        | (dataframe["bear_fvg"].fillna(False) & (dataframe["close"] < dataframe["ema21"]))
                    )
                    long_quality = (
                        trend_resonance_long
                        & (vpoc_reclaim_long | value_area_reaccept_long)
                        & value_area_acceptance_long
                        & structure_confirm_long
                        & (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["close"] > dataframe["session_vwap"])
                        & dataframe["rvol96"].between(0.85, 5.0)
                        & dataframe["rsi14"].between(48, 74)
                        & dataframe["body_atr"].between(0.08, 2.40)
                    )
                    short_quality = (
                        trend_resonance_short
                        & (vpoc_reclaim_short | value_area_reaccept_short)
                        & value_area_acceptance_short
                        & structure_confirm_short
                        & (dataframe["ema21"] < dataframe["ema55"])
                        & (dataframe["close"] < dataframe["session_vwap"])
                        & dataframe["rvol96"].between(0.85, 5.0)
                        & dataframe["rsi14"].between(26, 52)
                        & dataframe["body_atr"].between(0.08, 2.40)
                    )
                    raw = killzone_window & long_quality
                    short_raw = killzone_window & short_quality
                elif "{spec.key}" == "liquidity_sweep_adx_liquidity_pool_context":
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(9 * 60 + 35, 11 * 60 + 30)
                        | dataframe["minute_of_day_ny"].between(13 * 60, 15 * 60 + 30)
                    )
                    trend_root_long = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                        & dataframe["adx14"].between(20, 55)
                    )
                    trend_root_short = (
                        (dataframe["ema21"] < dataframe["ema55"])
                        & (dataframe["ema55"] < dataframe["ema144"])
                        & dataframe["adx14"].between(20, 55)
                    )
                    sellside_sweep_reclaim = (
                        dataframe["sellside_pool_cluster"].notna()
                        & (dataframe["low"] < dataframe["sellside_pool_cluster"] - dataframe["atr14"] * 0.03)
                        & (dataframe["close"] > dataframe["sellside_pool_cluster"])
                    )
                    buyside_sweep_reclaim = (
                        dataframe["buyside_pool_cluster"].notna()
                        & (dataframe["high"] > dataframe["buyside_pool_cluster"] + dataframe["atr14"] * 0.03)
                        & (dataframe["close"] < dataframe["buyside_pool_cluster"])
                    )
                    structure_confirm_long = (
                        dataframe["bull_mss"].fillna(False)
                        | dataframe["bull_fvg"].fillna(False)
                    )
                    structure_confirm_short = (
                        dataframe["bear_mss"].fillna(False)
                        | dataframe["bear_fvg"].fillna(False)
                    )
                    long_quality = (
                        trend_root_long
                        & sellside_sweep_reclaim
                        & structure_confirm_long
                        & dataframe["liquidity_pool_band"].between(0.10, 3.50)
                        & dataframe["pool_distance_atr"].between(0.0, 0.65)
                        & dataframe["sweep_strength"].between(0.02, 1.50)
                        & dataframe["fvg_mitigation_score"].between(0.0, 1.50)
                        & dataframe["rvol96"].between(0.85, 5.5)
                        & dataframe["rsi14"].between(46, 76)
                        & dataframe["body_atr"].between(0.08, 2.40)
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                    short_quality = (
                        trend_root_short
                        & buyside_sweep_reclaim
                        & structure_confirm_short
                        & dataframe["liquidity_pool_band"].between(0.10, 3.50)
                        & dataframe["pool_distance_atr"].between(0.0, 0.65)
                        & dataframe["sweep_strength"].between(0.02, 1.50)
                        & dataframe["fvg_mitigation_score"].between(0.0, 1.50)
                        & dataframe["rvol96"].between(0.85, 5.5)
                        & dataframe["rsi14"].between(24, 54)
                        & dataframe["body_atr"].between(0.08, 2.40)
                        & (dataframe["close"] < dataframe["session_vwap"])
                    )
                    raw = killzone_window & long_quality
                    short_raw = killzone_window & short_quality
                elif "{spec.key}" == "nr7_range_expansion":
                    nr7_range = dataframe["prior_nr7"].fillna(False)
                    nr7_break = (dataframe["close"] > dataframe["nr7_high"]) & (dataframe["close"].shift(1) <= dataframe["nr7_high"].shift(1))
                    raw = nr7_range & nr7_break & dataframe["rvol96"].between(0.80, 6.0) & dataframe["rsi14"].between(48, 76) & body_ok
                elif "{spec.key}" == "nr7_range_expansion_excursion_cap":
                    nr7_range = dataframe["prior_nr7"].fillna(False)
                    nr7_break = (
                        (dataframe["close"] > dataframe["nr7_high"])
                        & (dataframe["close"].shift(1) <= dataframe["nr7_high"].shift(1))
                    )
                    vwap_excursion_ok = (
                        ((dataframe["close"] - dataframe["session_vwap"]).abs() / dataframe["atr14"].clip(lower=0.01))
                        .between(0.03, 1.00)
                    )
                    reclaim_discount_ok = (
                        ((dataframe["close"] - dataframe["nr7_high"]) / dataframe["atr14"].clip(lower=0.01))
                        .between(0.00, 0.65)
                    )
                    raw = (
                        nr7_range
                        & nr7_break
                        & dataframe["rvol96"].between(0.85, 6.0)
                        & dataframe["rsi14"].between(50, 74)
                        & body_ok
                        & (dataframe["close"] > dataframe["session_vwap"])
                        & vwap_excursion_ok
                        & reclaim_discount_ok
                    )
                elif "{spec.key}" == "nr7_range_expansion_vwap_hold_persistence":
                    nr7_range = dataframe["prior_nr7"].fillna(False)
                    nr7_break = (
                        (dataframe["close"] > dataframe["nr7_high"])
                        & (dataframe["close"].shift(1) <= dataframe["nr7_high"].shift(1))
                    )
                    vwap_hold_bias = (
                        (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["close"].shift(1) > dataframe["session_vwap"].shift(1))
                        & (dataframe["close"].shift(2) > dataframe["session_vwap"].shift(2))
                    )
                    session_participation = (
                        dataframe["rvol96"].between(0.90, 5.5)
                        & dataframe["body_atr"].between(0.14, 2.8)
                    )
                    raw = (
                        nr7_range
                        & nr7_break
                        & dataframe["rsi14"].between(50, 76)
                        & body_ok
                        & session_participation
                        & vwap_hold_bias.fillna(False)
                    )
                elif "{spec.key}" == "nr7_range_expansion_killzone_filter":
                    nr7_range = dataframe["prior_nr7"].fillna(False)
                    nr7_break = (
                        (dataframe["close"] > dataframe["nr7_high"])
                        & (dataframe["close"].shift(1) <= dataframe["nr7_high"].shift(1))
                    )
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(2 * 60, 5 * 60)
                        | dataframe["minute_of_day_ny"].between(9 * 60 + 30, 12 * 60)
                    )
                    session_participation = (
                        dataframe["rvol96"].between(0.95, 5.0)
                        & dataframe["body_atr"].between(0.14, 2.4)
                    )
                    raw = (
                        nr7_range
                        & nr7_break
                        & killzone_window
                        & dataframe["rsi14"].between(50, 76)
                        & body_ok
                        & session_participation
                        & (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["close"] > dataframe["ema21"])
                    )
                elif "{spec.key}" == "crabel_nr7_intraday_expansion_continuation":
                    nr7_range = dataframe["prior_nr7"].fillna(False)
                    nr7_break = (
                        (dataframe["close"] > dataframe["nr7_high"])
                        & (dataframe["close"].shift(1) <= dataframe["nr7_high"].shift(1))
                    )
                    opening_break = dataframe["close"] > dataframe["opening_high30"].fillna(dataframe["nr7_high"])
                    continuation_follow_through = (
                        (dataframe["close"] > dataframe["high"].shift(1).fillna(dataframe["close"]))
                        & (dataframe["close"].shift(1) > dataframe["open"].shift(1))
                    )
                    session_expansion_hold = (
                        (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["close"].shift(1) > dataframe["session_vwap"].shift(1))
                        & (dataframe["close"] > dataframe["ema21"])
                    )
                    raw = (
                        nr7_range
                        & nr7_break
                        & opening_break.fillna(False)
                        & continuation_follow_through.fillna(False)
                        & session_expansion_hold.fillna(False)
                        & dataframe["minute_of_day_ny"].between(9 * 60 + 35, 14 * 60 + 30)
                        & dataframe["rvol96"].between(0.85, 4.2)
                        & dataframe["rsi14"].between(52, 78)
                        & dataframe["body_atr"].between(0.12, 2.2)
                    )
                elif "{spec.key}" == "connors_rsi2_rebound":
                    down2 = (dataframe["close"].shift(1) < dataframe["close"].shift(2)) & (dataframe["close"].shift(2) < dataframe["close"].shift(3))
                    washout = (dataframe["rsi2"].shift(1) < 10) | (dataframe["connors_rsi"].shift(1) < 25)
                    lower_reclaim = (dataframe["low"] <= dataframe["lower_band40"] * 1.004) & (dataframe["close"] > dataframe["lower_band40"])
                    raw = down2 & washout & lower_reclaim & dataframe["rvol96"].between(0.55, 6.5) & dataframe["rsi14"].between(24, 64)
                elif "{spec.key}" == "ultimate_ict_zone_volume_spike_reclaim":
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(2 * 60, 5 * 60)
                        | dataframe["minute_of_day_ny"].between(9 * 60 + 30, 12 * 60)
                    )
                    liquidity_sweep = (
                        (dataframe["low"] < dataframe["prior_day_low"])
                        | (dataframe["low"] < dataframe["liq_low20"])
                    )
                    reclaim = (
                        (dataframe["close"] > dataframe["prior_day_low"].fillna(dataframe["liq_low20"]))
                        & (dataframe["close"] > dataframe["open"])
                    )
                    extreme_wpr = dataframe["wpr14"].lt(-82)
                    ict_zone = (
                        dataframe["close"].between(dataframe["bull_ob_low"], dataframe["bull_ob_high"])
                        | dataframe["bull_fvg"]
                        | dataframe["close"].between(dataframe["ote_long_79"], dataframe["ote_long_62"])
                    )
                    volume_spike = dataframe["rvol96"].between(1.15, 6.0)
                    raw = (
                        killzone_window
                        & liquidity_sweep.fillna(False)
                        & reclaim.fillna(False)
                        & extreme_wpr.fillna(False)
                        & ict_zone.fillna(False)
                        & volume_spike
                        & dataframe["rsi14"].between(24, 58)
                        & dataframe["body_atr"].between(0.08, 2.6)
                    )
                elif "{spec.key}" == "ultimate_ict_zone_volume_spike_exit_persistence":
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(2 * 60, 5 * 60)
                        | dataframe["minute_of_day_ny"].between(9 * 60 + 30, 12 * 60)
                    )
                    liquidity_sweep = (
                        (dataframe["low"] < dataframe["prior_day_low"])
                        | (dataframe["low"] < dataframe["liq_low20"])
                    )
                    reclaim = (
                        (dataframe["close"] > dataframe["prior_day_low"].fillna(dataframe["liq_low20"]))
                        & (dataframe["close"] > dataframe["open"])
                    )
                    extreme_wpr = dataframe["wpr14"].lt(-84)
                    ict_zone = (
                        dataframe["close"].between(dataframe["bull_ob_low"], dataframe["bull_ob_high"])
                        | dataframe["bull_fvg"]
                        | dataframe["close"].between(dataframe["ote_long_79"], dataframe["ote_long_62"])
                    )
                    volume_spike = dataframe["rvol96"].between(1.25, 6.0)
                    score6_urgency = (
                        (dataframe["close"] > dataframe["session_open"])
                        & (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["macd_line"] > dataframe["macd_signal"])
                    )
                    persistence_window = (
                        dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)
                        | dataframe["minute_of_day_ny"].between(14 * 60, 16 * 60)
                    )
                    raw = (
                        killzone_window
                        & liquidity_sweep.fillna(False)
                        & reclaim.fillna(False)
                        & extreme_wpr.fillna(False)
                        & ict_zone.fillna(False)
                        & volume_spike
                        & score6_urgency.fillna(False)
                        & persistence_window
                        & dataframe["rsi14"].between(28, 60)
                        & dataframe["body_atr"].between(0.10, 2.2)
                    )
                elif "{spec.key}" == "ultimate_ict_zone_volume_spike_session_open_bias_cap":
                    ny_killzone = dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)
                    liquidity_sweep = (
                        (dataframe["low"] < dataframe["prior_day_low"])
                        | (dataframe["low"] < dataframe["liq_low20"])
                    )
                    reclaim = (
                        (dataframe["close"] > dataframe["prior_day_low"].fillna(dataframe["liq_low20"]))
                        & (dataframe["close"] > dataframe["open"])
                    )
                    extreme_wpr = dataframe["wpr14"].lt(-84)
                    ict_zone = (
                        dataframe["close"].between(dataframe["bull_ob_low"], dataframe["bull_ob_high"])
                        | dataframe["bull_fvg"]
                        | dataframe["close"].between(dataframe["ote_long_79"], dataframe["ote_long_62"])
                    )
                    volume_spike = dataframe["rvol96"].between(1.25, 5.5)
                    session_open_bias = (
                        (dataframe["close"] > dataframe["session_open"])
                        & (dataframe["session_vwap"] > dataframe["session_open"] * 0.9985)
                    )
                    vwap_reclaim = (
                        (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["low"] <= dataframe["session_vwap"] * 1.0015)
                    )
                    macd_bias = (
                        (dataframe["macd_line"] > dataframe["macd_signal"])
                        & (dataframe["macd_hist"] > dataframe["macd_hist"].shift(1))
                    )
                    body_cap = dataframe["body_atr"].between(0.09, 1.85)
                    raw = (
                        ny_killzone
                        & liquidity_sweep.fillna(False)
                        & reclaim.fillna(False)
                        & extreme_wpr.fillna(False)
                        & ict_zone.fillna(False)
                        & volume_spike
                        & session_open_bias.fillna(False)
                        & vwap_reclaim.fillna(False)
                        & macd_bias.fillna(False)
                        & dataframe["rsi14"].between(30, 58)
                        & body_cap
                    )
                elif "{spec.key}" == "ultimate_ict_zone_volume_spike_vwap_hold_persistence":
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(9 * 60 + 35, 11 * 60 + 45)
                        | dataframe["minute_of_day_ny"].between(14 * 60, 15 * 60 + 30)
                    )
                    liquidity_sweep = (
                        (dataframe["low"] < dataframe["prior_day_low"])
                        | (dataframe["low"] < dataframe["liq_low20"])
                    )
                    reclaim = (
                        (dataframe["close"] > dataframe["prior_day_low"].fillna(dataframe["liq_low20"]))
                        & (dataframe["close"] > dataframe["open"])
                    )
                    extreme_wpr = dataframe["wpr14"].lt(-84)
                    ict_zone = (
                        dataframe["close"].between(dataframe["bull_ob_low"], dataframe["bull_ob_high"])
                        | dataframe["bull_fvg"]
                        | dataframe["close"].between(dataframe["ote_long_79"], dataframe["ote_long_62"])
                    )
                    volume_spike = dataframe["rvol96"].between(1.20, 5.8)
                    vwap_reclaim = (
                        (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["low"] <= dataframe["session_vwap"] * 1.0018)
                    )
                    vwap_hold = (
                        (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["close"].shift(1) > dataframe["session_vwap"].shift(1))
                    )
                    persistence_bias = (
                        (dataframe["macd_line"] > dataframe["macd_signal"])
                        & (dataframe["close"] > dataframe["ema21"])
                    )
                    raw = (
                        killzone_window
                        & liquidity_sweep.fillna(False)
                        & reclaim.fillna(False)
                        & extreme_wpr.fillna(False)
                        & ict_zone.fillna(False)
                        & volume_spike
                        & vwap_reclaim.fillna(False)
                        & vwap_hold.fillna(False)
                        & persistence_bias.fillna(False)
                        & dataframe["rsi14"].between(31, 60)
                        & dataframe["body_atr"].between(0.10, 2.0)
                    )
                elif "{spec.key}" == "ultimate_ict_zone_volume_spike_session_open_bias_cap_vwap_hold_persistence":
                    ny_killzone = dataframe["minute_of_day_ny"].between(9 * 60 + 35, 11 * 60 + 30)
                    liquidity_sweep = (
                        (dataframe["low"] < dataframe["prior_day_low"])
                        | (dataframe["low"] < dataframe["liq_low20"])
                    )
                    reclaim = (
                        (dataframe["close"] > dataframe["prior_day_low"].fillna(dataframe["liq_low20"]))
                        & (dataframe["close"] > dataframe["open"])
                    )
                    extreme_wpr = dataframe["wpr14"].lt(-84)
                    ict_zone = (
                        dataframe["close"].between(dataframe["bull_ob_low"], dataframe["bull_ob_high"])
                        | dataframe["bull_fvg"]
                        | dataframe["close"].between(dataframe["ote_long_79"], dataframe["ote_long_62"])
                    )
                    volume_spike = dataframe["rvol96"].between(1.25, 5.5)
                    session_open_bias = (
                        (dataframe["close"] > dataframe["session_open"])
                        & (dataframe["session_vwap"] > dataframe["session_open"] * 0.9985)
                    )
                    vwap_reclaim = (
                        (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["low"] <= dataframe["session_vwap"] * 1.0015)
                    )
                    vwap_hold = (
                        (dataframe["close"] > dataframe["session_vwap"])
                        & (dataframe["close"].shift(1) > dataframe["session_vwap"].shift(1))
                    )
                    macd_bias = (
                        (dataframe["macd_line"] > dataframe["macd_signal"])
                        & (dataframe["macd_hist"] > dataframe["macd_hist"].shift(1))
                    )
                    persistence_bias = (
                        (dataframe["close"] > dataframe["ema21"])
                        & (dataframe["ema21"] > dataframe["ema55"])
                    )
                    raw = (
                        ny_killzone
                        & liquidity_sweep.fillna(False)
                        & reclaim.fillna(False)
                        & extreme_wpr.fillna(False)
                        & ict_zone.fillna(False)
                        & volume_spike
                        & session_open_bias.fillna(False)
                        & vwap_reclaim.fillna(False)
                        & vwap_hold.fillna(False)
                        & macd_bias.fillna(False)
                        & persistence_bias.fillna(False)
                        & dataframe["rsi14"].between(32, 58)
                        & dataframe["body_atr"].between(0.10, 1.8)
                    )
                elif "{spec.key}" == "ote_liquidity_sweep_fvg_ob_reclaim":
                    trend_root = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                    liquidity_sweep = (
                        (dataframe["low"] < dataframe["prior_day_low"])
                        | (dataframe["low"] < dataframe["liq_low20"])
                    )
                    reclaimed = (
                        (dataframe["close"] > dataframe["prior_day_low"].fillna(dataframe["liq_low20"]))
                        & dataframe["sweep_close_reclaim"]
                    )
                    in_ote = dataframe["close"].between(dataframe["ote_long_79"], dataframe["ote_long_62"])
                    near_fvg = dataframe["bull_fvg"] | (dataframe["low"] <= dataframe["prev2_high"] * 1.002)
                    near_ob = dataframe["close"].between(dataframe["bull_ob_low"], dataframe["bull_ob_high"])
                    raw = (
                        trend_root
                        & liquidity_sweep.fillna(False)
                        & reclaimed.fillna(False)
                        & in_ote.fillna(False)
                        & (near_fvg.fillna(False) | near_ob.fillna(False))
                        & dataframe["rvol96"].between(0.75, 5.0)
                        & dataframe["rsi14"].between(42, 72)
                        & dataframe["body_atr"].between(0.08, 2.2)
                    )
                elif "{spec.key}" == "ote_fvg_order_block_reclaim_session_directional_bias":
                    am_window = dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)
                    pm_window = dataframe["minute_of_day_ny"].between(13 * 60 + 30, 16 * 60)
                    session_window = am_window | pm_window
                    prior_day_reclaim_long = (
                        (dataframe["low"] < dataframe["prior_day_low"])
                        & (dataframe["close"] > dataframe["prior_day_low"])
                    )
                    prior_day_reclaim_short = (
                        (dataframe["high"] > dataframe["prior_day_high"])
                        & (dataframe["close"] < dataframe["prior_day_high"])
                    )
                    local_reclaim_long = (
                        (dataframe["low"] < dataframe["liq_low20"])
                        & (dataframe["close"] > dataframe["liq_low20"])
                    )
                    local_reclaim_short = (
                        (dataframe["high"] > dataframe["liq_high20"])
                        & (dataframe["close"] < dataframe["liq_high20"])
                    )
                    liquidity_sweep_long = prior_day_reclaim_long | local_reclaim_long
                    liquidity_sweep_short = prior_day_reclaim_short | local_reclaim_short
                    ote_long = dataframe["close"].between(dataframe["ote_long_79"], dataframe["ote_long_62"])
                    ote_short = dataframe["close"].between(dataframe["ote_short_62"], dataframe["ote_short_79"])
                    near_bull_fvg = dataframe["bull_fvg"] | (dataframe["low"] <= dataframe["prev2_high"] * 1.002)
                    near_bear_fvg = dataframe["bear_fvg"] | (dataframe["high"] >= dataframe["prev2_low"] * 0.998)
                    near_bull_ob = dataframe["close"].between(dataframe["bull_ob_low"], dataframe["bull_ob_high"])
                    near_bear_ob = dataframe["close"].between(dataframe["bear_ob_low"], dataframe["bear_ob_high"])
                    ict_zone_long = ote_long & (near_bull_fvg.fillna(False) | near_bull_ob.fillna(False))
                    ict_zone_short = ote_short & (near_bear_fvg.fillna(False) | near_bear_ob.fillna(False))
                    bull_session_bias = (
                        (dataframe["close"] > dataframe["session_open"])
                        & (dataframe["session_vwap"] > dataframe["session_open"] * 0.998)
                        & (dataframe["ema21"] > dataframe["ema55"])
                    )
                    bear_session_bias = (
                        (dataframe["close"] < dataframe["session_open"])
                        & (dataframe["session_vwap"] < dataframe["session_open"] * 1.002)
                        & (dataframe["ema21"] < dataframe["ema55"])
                    )
                    mtf_bias_long = (
                        (dataframe["ema20_15m"] > dataframe["ema50_15m"])
                        & (dataframe["ema20_1h"] > dataframe["ema50_1h"])
                        & (dataframe["slope_4h"] > 0)
                    )
                    mtf_bias_short = (
                        (dataframe["ema20_15m"] < dataframe["ema50_15m"])
                        & (dataframe["ema20_1h"] < dataframe["ema50_1h"])
                        & (dataframe["slope_4h"] < 0)
                    )
                    long_score = (
                        liquidity_sweep_long.astype(int)
                        + ict_zone_long.fillna(False).astype(int)
                        + bull_session_bias.fillna(False).astype(int)
                        + mtf_bias_long.fillna(False).astype(int)
                        + dataframe["rvol96"].between(0.85, 4.8).astype(int)
                        + dataframe["body_atr"].between(0.08, 2.0).astype(int)
                    )
                    short_score = (
                        liquidity_sweep_short.astype(int)
                        + ict_zone_short.fillna(False).astype(int)
                        + bear_session_bias.fillna(False).astype(int)
                        + mtf_bias_short.fillna(False).astype(int)
                        + dataframe["rvol96"].between(0.85, 4.8).astype(int)
                        + dataframe["body_atr"].between(0.08, 2.0).astype(int)
                    )
                    raw = (
                        session_window
                        & long_score.ge(4)
                        & dataframe["rsi14"].between(36, 68)
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                    short_raw = (
                        session_window
                        & short_score.ge(4)
                        & dataframe["rsi14"].between(32, 64)
                        & (dataframe["close"] < dataframe["session_vwap"])
                    )
                elif "{spec.key}" == "h4_midnight_macd_rsi_pullback":
                    h4_structure_bias = (
                        (dataframe["ema144"] > dataframe["ema390"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    midnight_discount = (
                        dataframe["close"] < dataframe["midnight_open"]
                    ) & (
                        dataframe["close"] > dataframe["midnight_open"] - dataframe["atr14"] * 1.2
                    )
                    macd_reclaim = (
                        (dataframe["macd_line"] > dataframe["macd_signal"])
                        & (dataframe["macd_line"].shift(1) <= dataframe["macd_signal"].shift(1))
                    )
                    raw = (
                        h4_structure_bias
                        & midnight_discount.fillna(False)
                        & macd_reclaim.fillna(False)
                        & dataframe["rsi14"].between(44, 66)
                        & dataframe["rvol96"].between(0.70, 4.5)
                        & dataframe["body_atr"].between(0.06, 1.8)
                        & (dataframe["close"] > dataframe["ema21"])
                    )
                elif "{spec.key}" == "h4_midnight_macd_rsi_pullback_session_cadence_guard":
                    h4_structure_bias = (
                        (dataframe["ema144"] > dataframe["ema390"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    midnight_discount = (
                        dataframe["close"] < dataframe["midnight_open"]
                    ) & (
                        dataframe["close"] > dataframe["midnight_open"] - dataframe["atr14"] * 1.05
                    )
                    macd_reclaim = (
                        (dataframe["macd_line"] > dataframe["macd_signal"])
                        & (dataframe["macd_line"].shift(1) <= dataframe["macd_signal"].shift(1))
                    )
                    session_cadence = (
                        dataframe["minute_of_day_ny"].between(3 * 60, 5 * 60 + 30)
                        | dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)
                        | dataframe["minute_of_day_ny"].between(13 * 60 + 30, 15 * 60)
                    )
                    mtf_trend_reclaim = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["close"] > dataframe["ema21"])
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                    raw = (
                        h4_structure_bias
                        & midnight_discount.fillna(False)
                        & macd_reclaim.fillna(False)
                        & session_cadence.fillna(False)
                        & mtf_trend_reclaim.fillna(False)
                        & dataframe["rsi14"].between(46, 64)
                        & dataframe["rvol96"].between(0.85, 4.0)
                        & dataframe["body_atr"].between(0.08, 1.5)
                    )
                elif "{spec.key}" == "liquidity_purge_rejection":
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(2 * 60, 5 * 60)
                        | dataframe["minute_of_day_ny"].between(9 * 60 + 30, 16 * 60)
                    )
                    purge = (
                        (dataframe["low"] < dataframe["liq_low20"])
                        & (dataframe["close"] > dataframe["liq_low20"])
                    ) | (
                        (dataframe["low"] < dataframe["prior_day_low"])
                        & (dataframe["close"] > dataframe["prior_day_low"])
                    )
                    momentum_turn = dataframe["macd_hist"] > dataframe["macd_hist"].shift(1)
                    raw = (
                        killzone_window
                        & purge.fillna(False)
                        & momentum_turn.fillna(False)
                        & dataframe["rsi14"].between(28, 58)
                        & dataframe["rvol96"].between(0.70, 5.0)
                        & dataframe["body_atr"].between(0.10, 2.6)
                    )
                elif "{spec.key}" == "momentum_divergence_reclaim":
                    trend_root = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    liquidity_reclaim = (
                        (dataframe["low"] < dataframe["liq_low20"])
                        & (dataframe["close"] > dataframe["liq_low20"])
                    )
                    momentum_divergence = (
                        (dataframe["macd_line"] > dataframe["macd_line"].shift(5))
                        & (dataframe["close"] <= dataframe["close"].shift(5))
                    )
                    raw = (
                        trend_root
                        & liquidity_reclaim.fillna(False)
                        & momentum_divergence.fillna(False)
                        & dataframe["rsi14"].between(38, 68)
                        & dataframe["rvol96"].between(0.70, 5.0)
                        & dataframe["body_atr"].between(0.08, 2.0)
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                elif "{spec.key}" == "fractal_liquidity_macd_rsi_divergence_reclaim":
                    structure_bias_long = (
                        (dataframe["ema144"] > dataframe["ema390"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                        & (dataframe["close"] < dataframe["midnight_open"])
                    )
                    structure_bias_short = (
                        (dataframe["ema144"] < dataframe["ema390"])
                        & (dataframe["ema55"] < dataframe["ema144"])
                        & (dataframe["close"] > dataframe["midnight_open"])
                    )
                    session_window = (
                        dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)
                        | dataframe["minute_of_day_ny"].between(13 * 60 + 30, 15 * 60 + 50)
                    )
                    fractal_sweep_long = (
                        (dataframe["low"] < dataframe["liq_low20"])
                        & (dataframe["close"] > dataframe["liq_low20"])
                    ) | (
                        (dataframe["low"] < dataframe["liq_low60"])
                        & (dataframe["close"] > dataframe["liq_low60"])
                    )
                    fractal_sweep_short = (
                        (dataframe["high"] > dataframe["liq_high20"])
                        & (dataframe["close"] < dataframe["liq_high20"])
                    ) | (
                        (dataframe["high"] > dataframe["liq_high60"])
                        & (dataframe["close"] < dataframe["liq_high60"])
                    )
                    macd_divergence_long = (
                        (dataframe["macd_line"] > dataframe["macd_line"].shift(5))
                        & (dataframe["close"] <= dataframe["close"].shift(5))
                    )
                    macd_divergence_short = (
                        (dataframe["macd_line"] < dataframe["macd_line"].shift(5))
                        & (dataframe["close"] >= dataframe["close"].shift(5))
                    )
                    raw = (
                        session_window
                        & (
                            (
                                structure_bias_long.fillna(False)
                                & fractal_sweep_long.fillna(False)
                                & macd_divergence_long.fillna(False)
                                & dataframe["rsi14"].gt(30)
                            )
                            | (
                                structure_bias_short.fillna(False)
                                & fractal_sweep_short.fillna(False)
                                & macd_divergence_short.fillna(False)
                                & dataframe["rsi14"].lt(70)
                            )
                        )
                        & dataframe["rvol96"].between(0.70, 5.2)
                        & dataframe["body_atr"].between(0.08, 2.2)
                    )
                elif "{spec.key}" == "fractal_liquidity_macd_divergence_reclaim":
                    structure_bias_long = (
                        (dataframe["ema144"] > dataframe["ema390"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                        & (dataframe["close"] < dataframe["midnight_open"])
                    )
                    structure_bias_short = (
                        (dataframe["ema144"] < dataframe["ema390"])
                        & (dataframe["ema55"] < dataframe["ema144"])
                        & (dataframe["close"] > dataframe["midnight_open"])
                    )
                    session_window = (
                        dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)
                        | dataframe["minute_of_day_ny"].between(13 * 60 + 30, 15 * 60 + 50)
                    )
                    fractal_sweep_long = (
                        (dataframe["low"] < dataframe["liq_low20"])
                        & (dataframe["close"] > dataframe["liq_low20"])
                    ) | (
                        (dataframe["low"] < dataframe["liq_low60"])
                        & (dataframe["close"] > dataframe["liq_low60"])
                    )
                    fractal_sweep_short = (
                        (dataframe["high"] > dataframe["liq_high20"])
                        & (dataframe["close"] < dataframe["liq_high20"])
                    ) | (
                        (dataframe["high"] > dataframe["liq_high60"])
                        & (dataframe["close"] < dataframe["liq_high60"])
                    )
                    macd_bullish_divergence = (
                        (dataframe["macd_line"] > dataframe["macd_line"].shift(5))
                        & (dataframe["close"] <= dataframe["close"].shift(5))
                    )
                    macd_bearish_divergence = (
                        (dataframe["macd_line"] < dataframe["macd_line"].shift(5))
                        & (dataframe["close"] >= dataframe["close"].shift(5))
                    )
                    raw = (
                        session_window
                        & (
                            (
                                structure_bias_long.fillna(False)
                                & fractal_sweep_long.fillna(False)
                                & macd_bullish_divergence.fillna(False)
                            )
                            | (
                                structure_bias_short.fillna(False)
                                & fractal_sweep_short.fillna(False)
                                & macd_bearish_divergence.fillna(False)
                            )
                        )
                        & dataframe["rvol96"].between(0.70, 5.2)
                        & dataframe["body_atr"].between(0.08, 2.2)
                    )
                elif "{spec.key}" == "midnight_open_liquidity_sweep_macd_divergence_reclaim":
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(2 * 60, 5 * 60)
                        | dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)
                        | dataframe["minute_of_day_ny"].between(13 * 60 + 30, 16 * 60)
                    )
                    midnight_discount_bias = dataframe["close"] < dataframe["midnight_open"]
                    midnight_premium_bias = dataframe["close"] > dataframe["midnight_open"]
                    liquidity_sweep_reclaim_long = (
                        (dataframe["low"] < dataframe["liq_low20"])
                        & (dataframe["close"] > dataframe["liq_low20"])
                    ) | (
                        (dataframe["low"] < dataframe["liq_low60"])
                        & (dataframe["close"] > dataframe["liq_low60"])
                    )
                    liquidity_sweep_reclaim_short = (
                        (dataframe["high"] > dataframe["liq_high20"])
                        & (dataframe["close"] < dataframe["liq_high20"])
                    ) | (
                        (dataframe["high"] > dataframe["liq_high60"])
                        & (dataframe["close"] < dataframe["liq_high60"])
                    )
                    macd_divergence_long = (
                        (dataframe["macd_line"] > dataframe["macd_line"].shift(5))
                        & (dataframe["close"] <= dataframe["close"].shift(5))
                    )
                    macd_divergence_short = (
                        (dataframe["macd_line"] < dataframe["macd_line"].shift(5))
                        & (dataframe["close"] >= dataframe["close"].shift(5))
                    )
                    raw = (
                        killzone_window
                        & (
                            (
                                midnight_discount_bias.fillna(False)
                                & liquidity_sweep_reclaim_long.fillna(False)
                                & macd_divergence_long.fillna(False)
                                & dataframe["rsi14"].between(30, 62)
                            )
                            | (
                                midnight_premium_bias.fillna(False)
                                & liquidity_sweep_reclaim_short.fillna(False)
                                & macd_divergence_short.fillna(False)
                                & dataframe["rsi14"].between(38, 70)
                            )
                        )
                        & dataframe["rvol96"].between(0.70, 5.2)
                        & dataframe["body_atr"].between(0.08, 2.3)
                    )
                elif "{spec.key}" == "silver_bullet_rsi_sniper":
                    silver_bullet_window = (
                        dataframe["minute_of_day_ny"].between(10 * 60, 11 * 60)
                        | dataframe["minute_of_day_ny"].between(14 * 60, 15 * 60)
                    )
                    liquidity_reclaim = (
                        (dataframe["low"] < dataframe["prior_day_low"])
                        & (dataframe["close"] > dataframe["prior_day_low"])
                    ) | (
                        (dataframe["low"] < dataframe["liq_low20"])
                        & (dataframe["close"] > dataframe["liq_low20"])
                    )
                    raw = (
                        silver_bullet_window
                        & liquidity_reclaim.fillna(False)
                        & dataframe["rsi14"].between(22, 40)
                        & dataframe["atr14"].gt(dataframe["bar_range"].rolling(30).mean() * 0.2)
                        & dataframe["rvol96"].between(0.65, 5.5)
                        & dataframe["body_atr"].between(0.08, 2.4)
                    )
                elif "{spec.key}" == "regression_channel_r2_slope_breadth":
                    regression_channel_r2_slope_breadth = True
                    r2_slope_persistence = (
                        dataframe["regression_slope_bps_96"].between(0.45, 8.0)
                        & dataframe["regression_r2_96"].between(0.18, 0.88)
                        & dataframe["regression_slope_bps_96"].gt(
                            dataframe["regression_slope_bps_96"].shift(24) * 0.35
                        )
                    )
                    mtf_slope_confirmation = (
                        (dataframe["slope_5m"] > 0)
                        & (dataframe["slope_15m"] > 0)
                        & (dataframe["slope_30m"] > 0)
                        & (dataframe["slope_1h"] > -dataframe["atr14"] * 0.12)
                    )
                    cross_index_breadth_proxy = (
                        (dataframe["close"] > dataframe["ema55"])
                        & (dataframe["ema21_slope_bps_12"] > 0.20)
                        & (dataframe["ema55_slope_bps_48"] > -0.12)
                    )
                    exhaustion_veto = (
                        (dataframe["close"] > dataframe["ema21"] + dataframe["atr14"] * 3.4)
                        | (dataframe["rsi14"] > 82)
                        | (dataframe["slope_4h"] < -dataframe["atr14"] * 0.18)
                        | (dataframe["slope_1d"] < -dataframe["atr14"] * 0.10)
                    )
                    atr_stop_hold_compression = (
                        dataframe["body_atr"].between(0.10, 1.95)
                        & dataframe["bar_range_atr"].between(0.18, 3.0)
                    )
                    raw = (
                        regression_channel_r2_slope_breadth
                        & r2_slope_persistence.fillna(False)
                        & mtf_slope_confirmation.fillna(False)
                        & cross_index_breadth_proxy.fillna(False)
                        & atr_stop_hold_compression.fillna(False)
                        & ~exhaustion_veto.fillna(False)
                        & dataframe["minute_of_day_ny"].between(9 * 60 + 35, 15 * 60 + 30)
                        & dataframe["rvol96"].between(0.75, 4.8)
                        & dataframe["rsi14"].between(48, 76)
                    )
                elif "{spec.key}" == "tod_balanced_ym_late_session_cadence_addon":
                    sparse_month_window = dataframe["date"].dt.strftime("%Y-%m").isin(
                        ["2024-11", "2024-12", "2025-01"]
                    )
                    late_session_window = dataframe["minute_of_day_ny"].between(10 * 60, 10 * 60 + 59)
                    trend_resonance = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"] - dataframe["atr14"] * 0.18)
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                    cadence_addon_reclaim = (
                        (
                            (dataframe["low"] <= dataframe["ema21"] + dataframe["atr14"] * 0.10)
                            & (dataframe["close"] > dataframe["ema21"])
                        )
                        | (
                            (dataframe["low"] <= dataframe["session_vwap"] + dataframe["atr14"] * 0.06)
                            & (dataframe["close"] > dataframe["session_vwap"])
                        )
                    )
                    raw = (
                        sparse_month_window
                        & late_session_window
                        & trend_resonance
                        & cadence_addon_reclaim.fillna(False)
                        & dataframe["rvol96"].between(0.65, 4.8)
                        & dataframe["rsi14"].between(46, 72)
                        & dataframe["adx14"].between(14, 42)
                        & dataframe["body_atr"].between(0.05, 1.6)
                    )
                elif "{spec.key}" == "supertrend_adx_displacement":
                    trend_root = (
                        (dataframe["supertrend_trend"] > 0)
                        & (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    adx_ok = dataframe["adx14"].between(18, 55)
                    displacement = dataframe["body_atr"].between(0.12, 2.8)
                    pullback_reclaim = (
                        (dataframe["low"] <= dataframe["ema21"] + dataframe["atr14"] * 0.15)
                        & (dataframe["close"] > dataframe["ema21"])
                    )
                    liquidity_sweep_reclaim = dataframe["sweep_low40"] & dataframe["sweep_close_reclaim"]
                    raw = (
                        trend_root
                        & adx_ok
                        & dataframe["rvol96"].between(0.70, 5.5)
                        & dataframe["rsi14"].between(45, 78)
                        & displacement
                        & (pullback_reclaim | liquidity_sweep_reclaim)
                    )
                elif "{spec.key}" == "supertrend_adx_pullback_reclaim":
                    trend_root = (
                        (dataframe["supertrend_trend"] > 0)
                        & (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    raw = (
                        trend_root
                        & dataframe["adx14"].between(20, 55)
                        & dataframe["rvol96"].between(0.75, 5.0)
                        & dataframe["rsi14"].between(48, 76)
                        & dataframe["body_atr"].between(0.10, 2.4)
                        & (dataframe["low"] <= dataframe["ema21"] + dataframe["atr14"] * 0.12)
                        & (dataframe["close"] > dataframe["ema21"])
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                elif "{spec.key}" == "supertrend_adx_turtle_soup_sweep_reversal":
                    killzone_window = (
                        dataframe["minute_of_day_ny"].between(9 * 60 + 30, 11 * 60 + 30)
                        | dataframe["minute_of_day_ny"].between(13 * 60 + 30, 16 * 60)
                    )
                    supertrend_bias = (
                        (dataframe["supertrend_trend"] > 0)
                        & (dataframe["ema21"] > dataframe["ema55"])
                    )
                    liquidity_sweep = (
                        (dataframe["low"] < dataframe["liq_low20"])
                        | (dataframe["low"] < dataframe["liq_low60"])
                        | (dataframe["low"] < dataframe["prior_day_low"])
                    )
                    close_reclaim = (
                        (dataframe["close"] > dataframe["liq_low20"].fillna(dataframe["liq_low60"]))
                        & (dataframe["close"] > dataframe["open"])
                    )
                    momentum_reversal = dataframe["macd_hist"] > dataframe["macd_hist"].shift(1)
                    displacement_intent = dataframe["adx14"] > 20
                    raw = (
                        killzone_window
                        & supertrend_bias.fillna(False)
                        & liquidity_sweep.fillna(False)
                        & close_reclaim.fillna(False)
                        & (momentum_reversal.fillna(False) | displacement_intent.fillna(False))
                        & dataframe["rvol96"].between(0.85, 5.8)
                        & dataframe["rsi14"].between(32, 62)
                        & dataframe["body_atr"].between(0.10, 2.4)
                        & (dataframe["close"] > dataframe["session_vwap"] * 0.998)
                    )
                elif "{spec.key}" == "supertrend_adx_pullback_exit_persistence":
                    trend_root = (
                        (dataframe["supertrend_trend"] > 0)
                        & (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    raw = (
                        trend_root
                        & dataframe["adx14"].between(20, 55)
                        & dataframe["rvol96"] .between(0.75, 5.0)
                        & dataframe["rsi14"].between(48, 76)
                        & dataframe["body_atr"].between(0.10, 2.4)
                        & (dataframe["low"] <= dataframe["ema21"] + dataframe["atr14"] * 0.12)
                        & (dataframe["close"] > dataframe["ema21"])
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                    exit_persistence_guard = True
                elif "{spec.key}" == "supertrend_adx_pullback_exit_persistence_high_conviction":
                    trend_root = (
                        (dataframe["supertrend_trend"] > 0)
                        & (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema89"])
                        & (dataframe["ema89"] > dataframe["ema144"])
                    )
                    breakout_bias = dataframe["close"] > dataframe["range_high40"] * 0.995
                    raw = (
                        trend_root
                        & dataframe["adx14"].between(24, 55)
                        & dataframe["rvol96"].between(1.10, 4.5)
                        & dataframe["rsi14"].between(52, 74)
                        & dataframe["body_atr"].between(0.16, 2.0)
                        & (dataframe["low"] <= dataframe["ema21"] + dataframe["atr14"] * 0.10)
                        & (dataframe["close"] > dataframe["ema21"])
                        & (dataframe["close"] > dataframe["session_vwap"])
                        & breakout_bias
                    )
                    exit_persistence_guard = True
                elif "{spec.key}" == "supertrend_adx_pullback_exit_persistence_opening_drive":
                    trend_root = (
                        (dataframe["supertrend_trend"] > 0)
                        & (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema89"])
                        & (dataframe["ema89"] > dataframe["ema144"])
                    )
                    opening_window = dataframe["minute_of_day_ny"].between(9 * 60 + 35, 11 * 60 + 30)
                    breakout_bias = dataframe["close"] > dataframe["range_high40"] * 0.998
                    raw = (
                        trend_root
                        & opening_window
                        & dataframe["adx14"].between(24, 55)
                        & dataframe["rvol96"].between(1.20, 5.0)
                        & dataframe["rsi14"].between(54, 76)
                        & dataframe["body_atr"].between(0.18, 2.0)
                        & (dataframe["low"] <= dataframe["ema21"] + dataframe["atr14"] * 0.10)
                        & (dataframe["close"] > dataframe["ema21"])
                        & (dataframe["close"] > dataframe["session_vwap"])
                        & breakout_bias
                    )
                    exit_persistence_guard = True
                elif "{spec.key}" == "supertrend_adx_pullback_exit_persistence_opening_drive_soft":
                    trend_root = (
                        (dataframe["supertrend_trend"] > 0)
                        & (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    opening_drive_context = dataframe["minute_of_day_ny"].between(9 * 60 + 35, 13 * 60)
                    breakout_bias = (
                        (dataframe["close"] > dataframe["range_high40"] * 0.997)
                        | (dataframe["body_atr"] > 0.20)
                    )
                    raw = (
                        trend_root
                        & dataframe["adx14"].between(21, 55)
                        & dataframe["rvol96"].between(0.95, 5.0)
                        & dataframe["rsi14"].between(50, 76)
                        & dataframe["body_atr"].between(0.12, 2.3)
                        & (dataframe["low"] <= dataframe["ema21"] + dataframe["atr14"] * 0.11)
                        & (dataframe["close"] > dataframe["ema21"])
                        & (dataframe["close"] > dataframe["session_vwap"])
                        & (opening_drive_context | breakout_bias)
                    )
                    exit_persistence_guard = True
                elif "{spec.key}" == "supertrend_adx_pullback_exit_persistence_vwap_excursion_cap":
                    trend_root = (
                        (dataframe["supertrend_trend"] > 0)
                        & (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    vwap_excursion_ok = (
                        ((dataframe["close"] - dataframe["session_vwap"]).abs() / dataframe["atr14"].clip(lower=0.01))
                        .between(0.02, 1.10)
                    )
                    reclaim_discount_ok = (
                        ((dataframe["close"] - dataframe["ema21"]) / dataframe["atr14"].clip(lower=0.01))
                        .between(0.01, 0.55)
                    )
                    raw = (
                        trend_root
                        & dataframe["adx14"].between(21, 55)
                        & dataframe["rvol96"].between(0.85, 5.0)
                        & dataframe["rsi14"].between(49, 76)
                        & dataframe["body_atr"].between(0.11, 2.2)
                        & (dataframe["low"] <= dataframe["ema21"] + dataframe["atr14"] * 0.11)
                        & (dataframe["close"] > dataframe["ema21"])
                        & (dataframe["close"] > dataframe["session_vwap"])
                        & vwap_excursion_ok
                        & reclaim_discount_ok
                    )
                    exit_persistence_guard = True
                elif "{spec.key}" == "mass_index_vortex_trend_continuation":
                    trend_root = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    mass_bulge = (
                        dataframe["mass_index25"].between(24.5, 28.5)
                        & (dataframe["mass_index25"] > dataframe["mass_index25"].shift(3))
                    )
                    vortex_direction = (
                        (dataframe["vortex_plus14"] > dataframe["vortex_minus14"] * 1.06)
                        & (dataframe["vortex_plus14"] > dataframe["vortex_plus14"].shift(3))
                    )
                    economic_slope = (
                        (dataframe["ema21_slope_bps_12"] > 10.0)
                        & (dataframe["ema55_slope_bps_48"] > 10.0)
                    )
                    breakout_hold = (
                        (dataframe["close"] > dataframe["range_high40"])
                        | (
                            (dataframe["low"] <= dataframe["ema21"] + dataframe["atr14"] * 0.10)
                            & (dataframe["close"] > dataframe["ema21"])
                            & (dataframe["close"] > dataframe["session_vwap"])
                        )
                    )
                    raw = (
                        trend_root
                        & mass_bulge.fillna(False)
                        & vortex_direction.fillna(False)
                        & economic_slope.fillna(False)
                        & breakout_hold.fillna(False)
                        & dataframe["adx14"].between(18, 52)
                        & dataframe["rvol96"].between(0.70, 5.2)
                        & dataframe["rsi14"].between(48, 78)
                        & dataframe["body_atr"].between(0.08, 2.3)
                    )
                elif "{spec.key}" == "aroon_cci_trend_continuation":
                    trend_root = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    directional_persistence = (
                        (dataframe["aroon_up25"] > 70.0)
                        & (dataframe["aroon_down25"] < 35.0)
                        & (dataframe["aroon_up25"] > dataframe["aroon_down25"] + 35.0)
                    )
                    cci_impulse = dataframe["cci20"].between(80.0, 220.0)
                    economic_slope = (
                        (dataframe["ema21_slope_bps_12"] > 10.0)
                        & (dataframe["ema55_slope_bps_48"] > 10.0)
                    )
                    continuation_hold = (
                        (dataframe["close"] > dataframe["range_high40"])
                        | (
                            (dataframe["low"] <= dataframe["ema21"] + dataframe["atr14"] * 0.12)
                            & (dataframe["close"] > dataframe["ema21"])
                            & (dataframe["close"] > dataframe["session_vwap"])
                        )
                    )
                    raw = (
                        trend_root
                        & directional_persistence.fillna(False)
                        & cci_impulse.fillna(False)
                        & economic_slope.fillna(False)
                        & continuation_hold.fillna(False)
                        & dataframe["adx14"].between(16, 50)
                        & dataframe["rvol96"].between(0.65, 5.0)
                        & dataframe["rsi14"].between(48, 78)
                        & dataframe["body_atr"].between(0.08, 2.2)
                    )
                elif "{spec.key}" == "aroon_cci_cadence_lift_symbol_guard":
                    symbol_ok = metadata.get("pair") in ("NQ/USD", "ES/USD")
                    trend_root = (
                        (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    directional_persistence = (
                        (dataframe["aroon_up25"] > 62.0)
                        & (dataframe["aroon_down25"] < 45.0)
                        & (dataframe["aroon_up25"] > dataframe["aroon_down25"] + 22.0)
                    )
                    cci_reacceleration = (
                        dataframe["cci20"].between(45.0, 210.0)
                        & (dataframe["cci20"] > dataframe["cci20"].shift(2) + 12.0)
                    )
                    cci_zero_reclaim = (
                        (dataframe["cci20"] > 10.0)
                        & (dataframe["cci20"].shift(3) < 0.0)
                    )
                    economic_slope = (
                        (dataframe["ema21_slope_bps_12"] > 10.0)
                        & (dataframe["ema55_slope_bps_48"] > 10.0)
                    )
                    cadence_lift_hold = (
                        (dataframe["close"] > dataframe["range_high40"] * 0.998)
                        | (
                            (dataframe["low"] <= dataframe["ema21"] + dataframe["atr14"] * 0.16)
                            & (dataframe["close"] > dataframe["ema21"])
                            & (dataframe["close"] > dataframe["session_vwap"])
                        )
                    )
                    raw = (
                        symbol_ok
                        & trend_root
                        & directional_persistence.fillna(False)
                        & (cci_reacceleration.fillna(False) | cci_zero_reclaim.fillna(False))
                        & economic_slope.fillna(False)
                        & cadence_lift_hold.fillna(False)
                        & dataframe["adx14"].between(15, 52)
                        & dataframe["rvol96"].between(0.55, 5.2)
                        & dataframe["rsi14"].between(47, 79)
                        & dataframe["body_atr"].between(0.06, 2.3)
                    )
                elif "{spec.key}" == "supertrend_adx_liquidity_sweep_reclaim":
                    trend_root = (
                        (dataframe["supertrend_trend"] > 0)
                        & (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    raw = (
                        trend_root
                        & dataframe["adx14"].between(18, 55)
                        & dataframe["rvol96"].between(0.80, 6.0)
                        & dataframe["rsi14"].between(44, 80)
                        & dataframe["body_atr"].between(0.12, 2.8)
                        & dataframe["sweep_low40"]
                        & dataframe["sweep_close_reclaim"]
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                elif "{spec.key}" == "supertrend_adx_pullback_ote_fvg_ob":
                    trend_root = (
                        (dataframe["supertrend_trend"] > 0)
                        & (dataframe["ema21"] > dataframe["ema55"])
                        & (dataframe["ema55"] > dataframe["ema144"])
                    )
                    pullback_reclaim = (
                        (dataframe["low"] <= dataframe["ema21"] + dataframe["atr14"] * 0.12)
                        & (dataframe["close"] > dataframe["ema21"])
                        & (dataframe["close"] > dataframe["session_vwap"])
                    )
                    in_ote = dataframe["close"].between(dataframe["ote_long_79"], dataframe["ote_long_62"])
                    near_fvg = dataframe["bull_fvg"] | (dataframe["low"] <= dataframe["prev2_high"] * 1.002)
                    near_ob = dataframe["close"].between(dataframe["bull_ob_low"], dataframe["bull_ob_high"])
                    ict_zone = in_ote & (near_fvg | near_ob)
                    raw = (
                        trend_root
                        & dataframe["adx14"].between(20, 55)
                        & dataframe["rvol96"].between(0.75, 5.0)
                        & dataframe["rsi14"].between(48, 74)
                        & dataframe["body_atr"].between(0.10, 2.2)
                        & pullback_reclaim
                        & ict_zone.fillna(False)
                    )
                elif "{spec.key}" == "midday_compression_failed_break_vwap_fade":
                    end_of_day = dataframe["minute_of_day_ny"].ge(15 * 60 + 45)
                    mean_target_long = (
                        dataframe["close"].ge(dataframe["session_vwap"])
                        | dataframe["rsi14"].gt(64)
                    )
                    mean_target_short = (
                        dataframe["close"].le(dataframe["session_vwap"])
                        | dataframe["rsi14"].lt(36)
                    )
                    raw = end_of_day | mean_target_long.fillna(False)
                    short_raw = end_of_day | mean_target_short.fillna(False)
                elif "{spec.key}" == "lunch_liquidity_vacuum_vwap_magnet_reversal":
                    end_of_day = dataframe["minute_of_day_ny"].ge(15 * 60 + 30)
                    mean_target_long = (
                        dataframe["close"].ge(dataframe["session_vwap"])
                        | dataframe["rsi14"].gt(62)
                    )
                    mean_target_short = (
                        dataframe["close"].le(dataframe["session_vwap"])
                        | dataframe["rsi14"].lt(38)
                    )
                    raw = end_of_day | mean_target_long.fillna(False)
                    short_raw = end_of_day | mean_target_short.fillna(False)
                else:
                    raw = trend & vwap_reclaim & breakout & rvol_ok & rsi_ok & body_ok
                entry_raw = raw.fillna(False)
                entry = entry_raw.shift(1).fillna(False)
                dataframe.loc[entry, ["enter_long", "enter_tag"]] = (1, "{factor_id}")
                if short_raw is not None:
                    short_entry_raw = short_raw.fillna(False)
                    short_entry = short_entry_raw.shift(1).fillna(False)
                    dataframe.loc[short_entry, ["enter_short", "enter_tag"]] = (1, "{factor_id}")
                return dataframe

            def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
                dataframe["exit_long"] = 0
                dataframe["exit_short"] = 0
                if metadata.get("pair") != "{symbol}/USD":
                    return dataframe
                short_raw = None
                if "{spec.key}" in ("supertrend_adx_pullback_exit_persistence", "supertrend_adx_pullback_exit_persistence_high_conviction", "supertrend_adx_pullback_exit_persistence_opening_drive", "supertrend_adx_pullback_exit_persistence_opening_drive_soft"):
                    exit_stack = (
                        (dataframe["close"] < dataframe["session_vwap"])
                        & (dataframe["close"] < dataframe["ema21"])
                        & (
                            (dataframe["ema21"] < dataframe["ema55"])
                            | (dataframe["close"] < dataframe["ema55"])
                        )
                    )
                    late_failure = (
                        (dataframe["rsi14"] > 84)
                        | ((dataframe["supertrend_trend"] < 0) & (dataframe["adx14"] < 18))
                    )
                    raw = exit_stack | late_failure
                elif "{spec.key}" == "prior_day_extreme_continuation_mtf_resonance_guard_exit_persistence":
                    exit_stack = (
                        (dataframe["close"] < dataframe["session_vwap"])
                        & (dataframe["close"] < dataframe["ema21"])
                        & (
                            (dataframe["ema21"] < dataframe["ema55"])
                            | (dataframe["close"] < dataframe["prior_day_high"].fillna(dataframe["ema55"]))
                        )
                    )
                    late_failure = (
                        (dataframe["rsi14"] > 86)
                        | ((dataframe["macd_line"] < dataframe["macd_signal"]) & (dataframe["close"] < dataframe["ema21"]))
                    )
                    raw = exit_stack | late_failure
                elif "{spec.key}" == "wpr_fractal_no_be_fulltarget":
                    end_of_day = dataframe["minute_of_day_ny"].ge(16 * 60 + 10)
                    raw = end_of_day
                    short_raw = end_of_day
                elif "{spec.key}" == "wpr_adx_fractal_sweep_reclaim":
                    end_of_day = dataframe["minute_of_day_ny"].ge(15 * 60 + 30)
                    raw = end_of_day
                    short_raw = end_of_day
                elif "{spec.key}" == "wpr_fractal_ict_zone_reclaim":
                    end_of_day = dataframe["minute_of_day_ny"].ge(15 * 60 + 45)
                    mean_target_long = (
                        (dataframe["close"] >= dataframe["session_vwap"])
                        | dataframe["rsi14"].gt(68)
                    )
                    mean_target_short = (
                        (dataframe["close"] <= dataframe["session_vwap"])
                        | dataframe["rsi14"].lt(32)
                    )
                    raw = end_of_day | mean_target_long.fillna(False)
                    short_raw = end_of_day | mean_target_short.fillna(False)
                elif "{spec.key}" == "wpr_adx_hurst_profile_mss_reclaim":
                    end_of_day = dataframe["minute_of_day_ny"].ge(15 * 60 + 30)
                    mean_target_long = (
                        (
                            (dataframe["close"] >= dataframe["profile_poc96"])
                            & (dataframe["close"] >= dataframe["session_vwap"])
                        )
                        | dataframe["rsi14"].gt(68)
                    )
                    mean_target_short = (
                        (
                            (dataframe["close"] <= dataframe["profile_poc96"])
                            & (dataframe["close"] <= dataframe["session_vwap"])
                        )
                        | dataframe["rsi14"].lt(32)
                    )
                    raw = end_of_day | mean_target_long.fillna(False)
                    short_raw = end_of_day | mean_target_short.fillna(False)
                elif "{spec.key}" == "value_area_vpoc_htf_trend_mss_filter":
                    end_of_day = dataframe["minute_of_day_ny"].ge(15 * 60 + 45)
                    vpoc_loss_long = (
                        dataframe["session_profile_poc_price"].notna()
                        & (dataframe["close"] < dataframe["session_profile_poc_price"])
                    )
                    vpoc_loss_short = (
                        dataframe["session_profile_poc_price"].notna()
                        & (dataframe["close"] > dataframe["session_profile_poc_price"])
                    )
                    raw = (
                        end_of_day
                        | vpoc_loss_long.fillna(False)
                        | (dataframe["close"] < dataframe["session_vwap"])
                        | (dataframe["close"] < dataframe["ema21"])
                        | dataframe["rsi14"].gt(80)
                    )
                    short_raw = (
                        end_of_day
                        | vpoc_loss_short.fillna(False)
                        | (dataframe["close"] > dataframe["session_vwap"])
                        | (dataframe["close"] > dataframe["ema21"])
                        | dataframe["rsi14"].lt(20)
                    )
                elif "{spec.key}" == "vwap_reclaim_rvol_trend_quality_filter":
                    raw = (
                        dataframe["close"].lt(dataframe["session_vwap"])
                        | dataframe["close"].lt(dataframe["ema32"])
                        | dataframe["rsi14"].gt(82)
                    )
                    short_raw = (
                        dataframe["close"].gt(dataframe["session_vwap"])
                        | dataframe["close"].gt(dataframe["ema32"])
                        | dataframe["rsi14"].lt(18)
                    )
                elif "{spec.key}" == "camarilla_r3_s3_reclaim":
                    end_of_day = dataframe["minute_of_day_ny"].ge(15 * 60 + 45)
                    mean_target_long = (
                        dataframe["close"].ge(dataframe["cam_pp"])
                        | dataframe["close"].ge(dataframe["session_vwap"])
                        | dataframe["rsi14"].gt(72)
                    )
                    mean_target_short = (
                        dataframe["close"].le(dataframe["cam_pp"])
                        | dataframe["close"].le(dataframe["session_vwap"])
                        | dataframe["rsi14"].lt(28)
                    )
                    raw = end_of_day | mean_target_long.fillna(False)
                    short_raw = end_of_day | mean_target_short.fillna(False)
                else:
                    raw = (
                        (dataframe["close"] < dataframe["session_vwap"])
                        | (dataframe["ema21"] < dataframe["ema55"])
                        | (dataframe["rsi14"] > 82)
                    )
                exit_raw = raw.fillna(False)
                exit_signal = exit_raw.shift(1).fillna(False)
                dataframe.loc[exit_signal, "exit_long"] = 1
                if short_raw is not None:
                    short_exit_raw = short_raw.fillna(False)
                    short_exit_signal = short_exit_raw.shift(1).fillna(False)
                    dataframe.loc[short_exit_signal, "exit_short"] = 1
                return dataframe
        """
    ).lstrip()


def prepare_aq_workspace(
    root: Path,
    *,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
) -> Path:
    workspace = root / "aq_workspaces" / timeframe
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "user_data/strategies_external").mkdir(parents=True, exist_ok=True)
    (workspace / "user_data/data/futures").mkdir(parents=True, exist_ok=True)
    shutil.copy2(AQ_REPO / "run_tomac.py", workspace / "run_tomac.py")
    patch_copied_tomac_runner(workspace / "run_tomac.py")
    shutil.copy2(AQ_REPO / "config.tomac.json", workspace / "config.tomac.json")
    config = json.loads((workspace / "config.tomac.json").read_text(encoding="utf-8"))
    config.setdefault("exchange", {})
    config["exchange"]["pair_whitelist"] = [f"{symbol}/USD" for symbol in symbols]
    config["timeframe"] = timeframe
    config["timerange"] = f"{start.replace('-', '')}-{end.replace('-', '')}"
    config["trading_mode"] = "futures"
    config["margin_mode"] = "isolated"
    config["dataformat_ohlcv"] = "feather"
    config["max_open_trades"] = 1
    config["fee"] = 0.0
    (workspace / "config.tomac.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return workspace


def stage_aq_inputs(
    root: Path,
    *,
    symbols: list[str],
    timeframe: str,
    start: str,
    end: str,
    families: list[str] | None = None,
) -> dict[str, Any]:
    workspace = prepare_aq_workspace(root, symbols=symbols, timeframe=timeframe, start=start, end=end)
    staged: list[str] = []
    dense_fill_stats: list[dict[str, Any]] = []
    for symbol in symbols:
        clean_feather = root / "clean" / symbol / f"{symbol}_USD-{timeframe}.feather"
        target = futures_feather_path(workspace, symbol, timeframe)
        clean_frame = pd.read_feather(clean_feather)
        dense_frame, fill_stats = dense_calendar_for_aq(clean_frame, timeframe)
        target.parent.mkdir(parents=True, exist_ok=True)
        dense_frame.to_feather(target)
        fill_stats["symbol"] = symbol
        fill_stats["source_clean_feather"] = str(clean_feather)
        fill_stats["aq_feather"] = str(target)
        dense_fill_stats.append(fill_stats)
        staged.append(str(target))
    strategy_paths: list[str] = []
    for symbol in symbols:
        for spec in candidate_specs(families=families):
            strategy_path = (
                workspace
                / "user_data/strategies_external"
                / f"{strategy_class_name(spec, symbol=symbol, timeframe=timeframe)}.py"
            )
            strategy_path.write_text(strategy_source(spec, symbol=symbol, timeframe=timeframe), encoding="utf-8")
            strategy_paths.append(str(strategy_path))
    return {
        "workspace": str(workspace),
        "data": staged,
        "strategies": strategy_paths,
        "strategy_specs": [spec.__dict__ for spec in generated_strategy_specs(symbols, timeframe, families=families)],
        "aq_dense_fill": dense_fill_stats,
    }


def safe_float(value: object) -> float:
    try:
        return float(str(value).strip())
    except Exception:
        return 0.0


def safe_table_float(value: object) -> float:
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group(0)) if match else 0.0


def table_cells(line: str) -> list[str]:
    if "│" not in line:
        return []
    return [cell.strip() for cell in line.split("│")[1:-1]]


def backtest_days_between(start: object, end: object) -> int | None:
    start_ts = pd.to_datetime(start, utc=True, errors="coerce")
    end_ts = pd.to_datetime(end, utc=True, errors="coerce")
    if pd.isna(start_ts) or pd.isna(end_ts) or end_ts < start_ts:
        return None
    return max(1, int(math.ceil((end_ts - start_ts).total_seconds() / 86400.0)))


def parse_blocks(stdout: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    per_pair: dict[str, dict[str, float]] = {}
    in_per_pair = False
    backtest_days: int | None = None
    for line in stdout.splitlines():
        stripped = line.strip()
        span_match = re.search(r"Backtested\s+(.+?)\s+->\s+(.+?)\s+\|", stripped)
        if span_match:
            start = pd.to_datetime(span_match.group(1), utc=True, errors="coerce")
            end = pd.to_datetime(span_match.group(2), utc=True, errors="coerce")
            if not pd.isna(start) and not pd.isna(end) and end >= start:
                backtest_days = max(1, int(math.ceil((end - start).total_seconds() / 86400.0)))
            continue
        if stripped == "---":
            if current:
                if backtest_days is not None:
                    current["days"] = backtest_days
                current["per_pair"] = per_pair
                blocks.append(current)
                current = {}
                per_pair = {}
            in_per_pair = False
            continue
        if stripped == "per_pair:":
            in_per_pair = True
            continue
        if in_per_pair and stripped and ":" in stripped:
            pair, metrics_text = stripped.split(":", 1)
            pair = pair.strip()
            if "/" not in pair or not pair.endswith("/USD"):
                continue
            metrics: dict[str, float] = {}
            for token in metrics_text.strip().split():
                if "=" not in token:
                    continue
                key, value = token.split("=", 1)
                metrics[key] = safe_float(value)
            if "trades" not in metrics or "profit_pct" not in metrics:
                continue
            per_pair[pair] = metrics
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current[key.strip()] = value.strip()
        in_per_pair = False
    if current:
        if backtest_days is not None:
            current["days"] = backtest_days
        current["per_pair"] = per_pair
        blocks.append(current)
    return blocks


def parse_freqtrade_result_table_blocks(stdout: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    per_pair: dict[str, dict[str, float]] = {}
    in_primary_report = False
    summary_start: str | None = None
    summary_end: str | None = None

    def flush() -> None:
        nonlocal current, per_pair, in_primary_report, summary_start, summary_end
        if current is not None and (per_pair or current.get("trade_count")):
            if per_pair and not current.get("pairs"):
                current["pairs"] = ",".join(per_pair)
            if current.get("days") is None:
                days = backtest_days_between(summary_start, summary_end)
                if days is not None:
                    current["days"] = days
            current["per_pair"] = per_pair
            blocks.append({key: value for key, value in current.items() if not key.startswith("_")})
        current = None
        per_pair = {}
        in_primary_report = False
        summary_start = None
        summary_end = None

    for line in stdout.splitlines():
        stripped = line.strip()
        result_match = re.match(r"Result for strategy\s+(\S+)", stripped)
        if result_match:
            flush()
            current = {"strategy": result_match.group(1)}
            continue
        if current is None:
            continue

        span_match = re.search(r"Backtested\s+(.+?)\s+->\s+(.+?)\s+\|", stripped)
        if span_match:
            days = backtest_days_between(span_match.group(1), span_match.group(2))
            if days is not None:
                current["days"] = days

        if "BACKTESTING REPORT" in stripped:
            in_primary_report = True
            continue
        if any(
            marker in stripped
            for marker in (
                "LEFT OPEN TRADES REPORT",
                "ENTER TAG STATS",
                "EXIT REASON STATS",
                "MIXED TAG STATS",
                "SUMMARY METRICS",
                "STRATEGY SUMMARY",
            )
        ):
            in_primary_report = False

        cells = table_cells(line)
        if len(cells) >= 2:
            metric, value = cells[0], cells[1]
            if metric == "Backtesting from":
                summary_start = value
            elif metric == "Backtesting to":
                summary_end = value
            elif metric == "Total/Daily Avg Trades":
                current["trade_count"] = int(safe_table_float(value))
            elif metric == "Total profit %":
                current["total_profit_pct"] = safe_table_float(value)
            elif metric == "Sharpe":
                current["sharpe"] = safe_table_float(value)
            elif metric == "Sortino":
                current["sortino"] = safe_table_float(value)
            elif metric == "Calmar":
                current["calmar"] = safe_table_float(value)
            elif metric == "Profit factor":
                current["profit_factor"] = safe_table_float(value)
                for pair_metrics in per_pair.values():
                    if not pair_metrics.get("pf"):
                        pair_metrics["pf"] = current["profit_factor"]
            elif metric == "Max % of account underwater":
                current["max_drawdown_pct"] = -abs(safe_table_float(value))

        if len(cells) < 7:
            continue

        pair = cells[0]
        if not (pair.endswith("/USD") or pair == "TOTAL"):
            continue
        win_loss = [safe_table_float(token) for token in re.findall(r"-?\d+(?:\.\d+)?", cells[6])]
        wins = int(win_loss[0]) if len(win_loss) >= 1 else 0
        losses = int(win_loss[2]) if len(win_loss) >= 3 else 0
        win_rate = win_loss[3] if len(win_loss) >= 4 else 0.0
        metrics = {
            "trades": int(safe_table_float(cells[1])),
            "profit_pct": safe_table_float(cells[4]),
            "wr": win_rate,
            "pf": safe_float(current.get("profit_factor")),
            "wins": wins,
            "losses": losses,
        }
        if pair == "TOTAL":
            current["trade_count"] = metrics["trades"]
            current["total_profit_pct"] = metrics["profit_pct"]
            current["win_rate_pct"] = metrics["wr"]
        else:
            per_pair[pair] = metrics

    flush()
    return blocks


def classify_screen_row(row: dict[str, Any]) -> dict[str, Any]:
    scored = dict(row)
    trades = int(safe_float(scored.get("trade_count")))
    gross = safe_float(scored.get("total_profit_pct") or scored.get("raw_total_profit_pct"))
    days = max(1, int(scored.get("days") or SESSIONS_2021_2025))
    wins = int(scored.get("wins") or 1)
    losses = int(scored.get("losses") or 1)
    scored["trade_count"] = trades
    scored["raw_total_profit_pct"] = round(gross, 6)
    scored["trades_per_day"] = round(trades / days, 6)
    for bps in (0, 1, 2, 5):
        scored[f"{bps}bps_per_side_total_profit_pct"] = round(gross - trades * bps * 0.02, 6)
    profile = futures_cost_profile(str(scored.get("symbol") or scored.get("pair") or ""))
    representative_price = safe_float(scored.get("representative_entry_price") or scored.get("last_close"))
    if representative_price <= 0:
        defaults = {"ES": 5200.0, "NQ": 18000.0, "YM": 39000.0, "XAU": 2300.0}
        representative_price = defaults.get(profile.root_symbol if profile else "", 1.0)
    if profile is not None:
        cost_pct = profile.round_trip_cost_pct(representative_price)
        fee_pct = profile.round_trip_fee_pct(representative_price)
        scored["cost_profile_id"] = profile.profile_id
        scored["cost_profile_source"] = profile.source
        scored["cost_model_status"] = profile.status
        scored["cost_model_verified_for_promotion"] = profile.verified_for_promotion
        scored["promotion_cost_verified"] = profile.verified_for_promotion
        scored["cost_model_blocker"] = "none" if profile.verified_for_promotion else "cost_model_unverified"
        scored["instrument_fee_only_round_trip_cash"] = round(profile.round_trip_fee_cash(), 6)
        scored["instrument_all_in_round_trip_cash"] = round(profile.round_trip_cost_cash(), 6)
        scored["instrument_fee_only_round_trip_pct"] = round(fee_pct, 6)
        scored["instrument_fee_only_bps_per_trade"] = round(fee_pct * 100.0, 6)
        scored["instrument_round_trip_cost_pct"] = round(cost_pct, 6)
        scored["instrument_cost_bps_per_trade"] = round(cost_pct * 100.0, 6)
        scored["gross_edge_bps_per_trade"] = round(gross / trades * 100.0, 6) if trades > 0 else 0.0
        scored["instrument_fee_only_total_profit_pct"] = round(gross - trades * fee_pct, 6)
        scored["instrument_cost_total_profit_pct"] = round(gross - trades * cost_pct, 6)
        scored["survives_instrument_fee_only"] = scored["instrument_fee_only_total_profit_pct"] > 0
        scored["survives_instrument_cost"] = scored["instrument_cost_total_profit_pct"] > 0
    else:
        scored["cost_profile_id"] = "unknown"
        scored["cost_profile_source"] = "missing_futures_cost_profile"
        scored["cost_model_status"] = "cost_model_unverified"
        scored["cost_model_verified_for_promotion"] = False
        scored["promotion_cost_verified"] = False
        scored["cost_model_blocker"] = "cost_model_unverified"
        scored["instrument_fee_only_round_trip_cash"] = None
        scored["instrument_all_in_round_trip_cash"] = None
        scored["instrument_fee_only_round_trip_pct"] = None
        scored["instrument_fee_only_bps_per_trade"] = None
        scored["instrument_round_trip_cost_pct"] = None
        scored["instrument_cost_bps_per_trade"] = None
        scored["gross_edge_bps_per_trade"] = round(gross / trades * 100.0, 6) if trades > 0 else 0.0
        scored["instrument_fee_only_total_profit_pct"] = None
        scored["instrument_cost_total_profit_pct"] = None
        scored["survives_instrument_fee_only"] = False
        scored["survives_instrument_cost"] = False
    scored["density_target_1_to_3_per_day"] = 1.0 <= scored["trades_per_day"] <= 3.0
    scored["minimum_trade_sample_floor_met"] = trades >= 30
    scored["survives_1bps_per_side"] = scored["1bps_per_side_total_profit_pct"] > 0
    scored["survives_2bps_per_side"] = scored["2bps_per_side_total_profit_pct"] > 0
    scored["survives_5bps_per_side"] = scored["5bps_per_side_total_profit_pct"] > 0
    scored["cost_stress_5bps_role"] = "telemetry_not_futures_hard_gate"
    if gross <= 0:
        scored["cost_wall_bucket"] = "gross_negative_not_cost_rescuable"
    elif not scored["survives_instrument_cost"]:
        scored["cost_wall_bucket"] = "zero_edge_churn_not_rescued_by_realistic_cost"
    elif not scored["survives_5bps_per_side"]:
        scored["cost_wall_bucket"] = "bps_stress_false_negative_recheck"
    elif scored["gross_edge_bps_per_trade"] >= 10.0 and scored["trades_per_day"] <= 3.0:
        scored["cost_wall_bucket"] = "large_move_low_turnover_cost_negligible"
    else:
        scored["cost_wall_bucket"] = "realistic_cost_survivor"
    scored["has_win_loss_diversity"] = wins > 0 and losses > 0
    scored["direction_consistent_local"] = scored.get("direction") in {"long", "short", "long_short"}
    scored["gate1_survivor"] = bool(
        scored["density_target_1_to_3_per_day"]
        and scored["minimum_trade_sample_floor_met"]
        and scored["cost_model_verified_for_promotion"]
        and scored["survives_instrument_cost"]
        and scored["has_win_loss_diversity"]
        and scored["direction_consistent_local"]
    )
    return scored


def score_rows(stdout: str, specs: list[GeneratedStrategySpec]) -> list[dict[str, Any]]:
    by_class = {spec.class_name: spec for spec in specs}
    rows: list[dict[str, Any]] = []
    blocks = parse_blocks(stdout)
    seen_machine_blocks = {str(block.get("strategy") or "") for block in blocks}
    blocks.extend(
        block
        for block in parse_freqtrade_result_table_blocks(stdout)
        if str(block.get("strategy") or "") not in seen_machine_blocks
    )
    for block in blocks:
        strategy_name = str(block.get("strategy") or "")
        spec = by_class.get(strategy_name)
        if spec is None:
            continue
        aggregate = classify_screen_row(
            {
                "scope": "aggregate",
                "symbol": spec.symbol,
                "pair": ",".join(block.get("pairs", "").split(",")),
                "timeframe": spec.timeframe,
                "strategy_name": strategy_name,
                "factor_id": spec.factor_id,
                "branch_path": spec.branch_path,
                "family": spec.family,
                "direction": spec.direction,
                "trade_count": int(safe_float(block.get("trade_count"))),
                "win_rate_pct": safe_float(block.get("win_rate_pct")),
                "sharpe": safe_float(block.get("sharpe")),
                "sortino": safe_float(block.get("sortino")),
                "calmar": safe_float(block.get("calmar")),
                "profit_factor": safe_float(block.get("profit_factor")),
                "total_profit_pct": safe_float(block.get("total_profit_pct")),
                "days": int(safe_float(block.get("days"))) if block.get("days") is not None else None,
            }
        )
        rows.append(aggregate)
        expected_pair = f"{spec.symbol}/USD"
        metrics = (block.get("per_pair") or {}).get(expected_pair)
        if metrics is None:
            continue
        rows.append(
            classify_screen_row(
                {
                    "scope": "per_pair",
                    "symbol": spec.symbol,
                    "pair": expected_pair,
                    "timeframe": spec.timeframe,
                    "strategy_name": strategy_name,
                    "factor_id": spec.factor_id,
                    "branch_path": spec.branch_path,
                    "family": spec.family,
                    "direction": spec.direction,
                    "trade_count": int(safe_float(metrics.get("trades"))),
                    "wins": int(safe_float(metrics.get("wins"))),
                    "losses": int(safe_float(metrics.get("losses"))),
                    "win_rate_pct": safe_float(metrics.get("wr")),
                    "sharpe": safe_float(metrics.get("sharpe")),
                    "profit_factor": safe_float(metrics.get("pf")),
                    "total_profit_pct": safe_float(metrics.get("profit_pct")),
                    "days": int(safe_float(block.get("days"))) if block.get("days") is not None else None,
                }
            )
        )
    return rows


def session_scope_summary(clean_bundles: list[dict[str, Any]] | None) -> dict[str, Any]:
    bundles = clean_bundles or []
    statuses = [str(bundle.get("eth_full_retained_coverage_status") or "missing_session_scope_evidence") for bundle in bundles]
    evidence = bool(bundles) and all(bool(bundle.get("eth_full_retained_session_evidence")) for bundle in bundles)
    return {
        "session_scope": SESSION_SCOPE,
        "rth_filter_applied": RTH_FILTER_APPLIED,
        "eth_full_retained_session_evidence": evidence,
        "eth_full_retained_coverage_status": "verified_retained_rows_outside_rth_all_symbols"
        if evidence
        else "session_scope_unverified_missing_or_partial_outside_rth_evidence",
        "symbol_session_coverage_status": statuses,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sanitize_aq_subprocess_env(env: dict[str, str] | None = None) -> dict[str, str]:
    sanitized = dict(os.environ if env is None else env)
    sanitized.pop("PYTHONPATH", None)
    sanitized.pop("PYTHONHOME", None)
    sanitized.pop("PYTHONUSERBASE", None)
    sanitized["PYTHONNOUSERSITE"] = "1"
    return sanitized


def run_cmd(
    root: Path,
    name: str,
    argv: list[object],
    cwd: Path,
    timeout: int,
    *,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    out_dir = root / "command-output"
    checks = root / "checks"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks.mkdir(parents=True, exist_ok=True)
    argv_s = [str(item) for item in argv]
    (out_dir / f"{name}.cmd").write_text(" ".join(argv_s) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(argv_s, cwd=cwd, text=True, capture_output=True, timeout=timeout, env=env)
        stdout, stderr, rc, timed_out = proc.stdout, proc.stderr, proc.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        stderr = stderr + f"\nTIMEOUT after {timeout}s\n"
        rc, timed_out = 124, True
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    out_path = out_dir / f"{name}.out"
    err_path = out_dir / f"{name}.err"
    exit_path = checks / f"{name}.exit"
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{rc}\n", encoding="utf-8")
    return {
        "name": name,
        "exit": rc,
        "timed_out": timed_out,
        "stdout_path": str(out_path),
        "stderr_path": str(err_path),
        "exit_path": str(exit_path),
    }


def normalize_root_path(value: object) -> str | None:
    if value in (None, ""):
        return None
    return str(Path(str(value)).expanduser().resolve())


def allowed_collision_roots(root: Path, compact_root: Path) -> set[Path]:
    roots = {root, compact_root}
    if root.name == "aq":
        roots.add(root.parent)
    return roots


def claim_collision_blockers(audit: dict[str, Any], *, allowed_roots: set[Path]) -> dict[str, Any]:
    allowed = {normalize_root_path(root) for root in allowed_roots}
    foreign_active_claims: list[dict[str, Any]] = []
    for claim in audit.get("claims") or []:
        if str(claim.get("status") or "").lower() != "active":
            continue
        if bool(claim.get("coordination_only")):
            continue
        claim_roots = {
            normalize_root_path(claim.get("run_root")),
            normalize_root_path(claim.get("tmp_root")),
        }
        claim_roots.discard(None)
        if claim_roots and claim_roots.issubset(allowed):
            continue
        foreign_active_claims.append(
            {
                "claim_file": claim.get("claim_file"),
                "run_root": claim.get("run_root"),
                "tmp_root": claim.get("tmp_root"),
                "scope": claim.get("scope"),
            }
        )

    foreign_live_processes: list[dict[str, Any]] = []
    for process in audit.get("live_factor_processes") or []:
        process_root = normalize_root_path(process.get("run_root"))
        if process_root in allowed:
            continue
        foreign_live_processes.append(
            {
                "pid": process.get("pid"),
                "run_root": process.get("run_root"),
                "command_excerpt": process.get("command_excerpt") or process.get("command"),
            }
        )

    return {
        "pass": not foreign_active_claims and not foreign_live_processes,
        "foreign_active_claims": foreign_active_claims,
        "foreign_live_processes": foreign_live_processes,
    }


def run_claim_collision_audit(root: Path, compact_root: Path, *, allowed_roots: set[Path]) -> dict[str, Any]:
    command = run_cmd(
        root,
        "pre_aq_claim_collision_audit",
        ["python3", "support/scripts/factor_claim_terminalization_audit.py"],
        cwd=REPO,
        timeout=180,
    )
    audit_path = Path(command["stdout_path"])
    try:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        guard = {
            "pass": False,
            "decision": "launch_blocked_claim_audit_json_parse_failure",
            "error": str(exc),
            "command": command,
        }
    else:
        guard = claim_collision_blockers(audit, allowed_roots=allowed_roots)
        guard.update(
            {
                "decision": "claim_collision_guard_pass" if guard["pass"] else "launch_blocked_by_foreign_claim_or_runtime",
                "command": command,
                "audit_summary": audit.get("summary"),
            }
        )
    for base in (root, compact_root):
        checks = base / "checks"
        summaries = base / "summaries"
        checks.mkdir(parents=True, exist_ok=True)
        summaries.mkdir(parents=True, exist_ok=True)
        (checks / "pre_aq_claim_collision_guard.json").write_text(json.dumps(guard, indent=2) + "\n", encoding="utf-8")
        if not guard["pass"]:
            (summaries / "terminal_no_launch_summary.json").write_text(json.dumps(guard, indent=2) + "\n", encoding="utf-8")
    return guard


def write_aq_gate_summary(
    root: Path,
    compact_root: Path,
    *,
    timeframe: str,
    command: dict[str, Any],
    specs: list[GeneratedStrategySpec],
    clean_bundles: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    stdout_path = Path(command["stdout_path"])
    rows = score_rows(stdout_path.read_text(encoding="utf-8"), specs)
    session_scope = session_scope_summary(clean_bundles)
    for row in rows:
        row.update(session_scope)
    raw_survivors = [row for row in rows if row.get("scope") == "per_pair" and row.get("gate1_survivor")]
    survivors = raw_survivors if session_scope["eth_full_retained_session_evidence"] else []
    raw_realistic_cost_survivors = [
        row
        for row in rows
        if row.get("scope") == "per_pair" and row.get("survives_instrument_cost")
    ]
    realistic_cost_survivors = (
        raw_realistic_cost_survivors if session_scope["eth_full_retained_session_evidence"] else []
    )
    bps_false_negative_rechecks = [
        row
        for row in realistic_cost_survivors
        if row.get("cost_wall_bucket") == "bps_stress_false_negative_recheck"
    ]
    stress_survivors = [
        row
        for row in rows
        if row.get("scope") == "per_pair" and row.get("survives_5bps_per_side")
    ]
    decision = (
        "gate1_autoquant_instrument_cost_density_survivor_downstream_required"
        if survivors
        else "blocked_session_scope_unverified_no_downstream"
        if raw_survivors and not session_scope["eth_full_retained_session_evidence"]
        else "observation_realistic_cost_survivor_needs_non_cost_gate_repair"
        if realistic_cost_survivors
        else "observation_no_autoquant_survivor_yet"
    )
    gate = {
        "timeframe": timeframe,
        "command": command,
        "rank_rows": len(rows),
        "decision": decision,
        "downstream_allowed": bool(survivors),
        "pre_bayes_allowed": bool(survivors),
        "bbn_allowed": bool(survivors),
        "catboost_allowed": False,
        "execution_tree_allowed": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        **session_scope,
        "survivors_instrument_cost": survivors,
        "raw_instrument_cost_survivors_before_session_scope": raw_survivors,
        "survivors_declared_cost": survivors,
        "realistic_cost_survivors_before_gate1": realistic_cost_survivors,
        "raw_realistic_cost_survivors_before_session_scope": raw_realistic_cost_survivors,
        "bps_stress_false_negative_rechecks": bps_false_negative_rechecks,
        "survivors_5bps": stress_survivors if session_scope["eth_full_retained_session_evidence"] else [],
        "cost_stress_survivors_5bps": stress_survivors if session_scope["eth_full_retained_session_evidence"] else [],
        "raw_cost_stress_survivors_5bps_before_session_scope": stress_survivors,
        "raw_survivors_before_session_scope": raw_survivors,
        "cost_gate_authority": "instrument_cost",
        "cost_stress_5bps_role": "telemetry_not_futures_hard_gate",
        "hard_promotion_gates_required_next": {
            "direction_consistent_aq_to_execution_tree": "not_run_yet",
            "duration_readiness_confirmed": "not_run_yet",
            "path_ranker_or_catboost_runtime_score_visible": "not_run_yet",
            "execution_tree_readiness_gte_0_65": "not_run_yet",
            "lifecycle_or_paper_sim_observation_complete": "not_run_yet",
            "cost_model_bound_to_selected_contract": "not_run_yet",
        },
        "retired_telemetry_not_hard_gates": [
            "transition_hazard",
            "hybrid_transition_hazard",
            "pda_hybrid_alignment",
        ],
    }
    summaries = root / "summaries"
    summaries.mkdir(parents=True, exist_ok=True)
    write_csv(summaries / f"autoquant_clean_{timeframe}_rows.csv", rows)
    (summaries / f"autoquant_clean_{timeframe}_gate.json").write_text(
        json.dumps(gate, indent=2) + "\n", encoding="utf-8"
    )
    compact_summaries = compact_root / "summaries"
    compact_summaries.mkdir(parents=True, exist_ok=True)
    if rows:
        write_csv(compact_summaries / f"autoquant_clean_{timeframe}_rows.csv", rows)
    (compact_summaries / f"autoquant_clean_{timeframe}_gate.json").write_text(
        json.dumps(gate, indent=2) + "\n", encoding="utf-8"
    )
    return gate


def write_claim_collision_no_launch_summary(
    root: Path,
    compact_root: Path,
    *,
    args: argparse.Namespace,
    requested_symbols: list[str],
    matched_symbols: list[str],
    skipped_symbols: list[str],
    timeframes: tuple[str, ...],
    families: list[str] | None,
    clean_bundles: list[dict[str, Any]],
    aq_staging: list[dict[str, Any]],
    guard: dict[str, Any],
) -> dict[str, Any]:
    summary = {
        "run_root": str(root),
        "compact_root": str(compact_root),
        "start": args.start,
        "end": args.end,
        "requested_symbols": requested_symbols,
        "symbols": matched_symbols,
        "skipped_symbols": skipped_symbols,
        "timeframes": timeframes,
        "families": families or [spec.key for spec in candidate_specs()],
        "clean_bundles": clean_bundles,
        "aq_staging": aq_staging,
        "aq_commands": [],
        "aq_gate_summaries": [],
        "decision": guard["decision"],
        "downstream_allowed": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "claim_collision_guard": guard,
    }
    (root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (compact_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root)
    compact_root = Path(args.compact_root)
    root.mkdir(parents=True, exist_ok=True)
    compact_root.mkdir(parents=True, exist_ok=True)
    requested_symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]
    timeframes = tuple(item.strip() for item in args.timeframes.split(",") if item.strip())
    raw_families = getattr(args, "families", None)
    families = [item.strip() for item in raw_families.split(",") if item.strip()] if raw_families else None
    if families is not None:
        candidate_specs(families=families)
    source_by_symbol = {source.symbol: source for source in source_universe()}
    sources = [source_by_symbol[symbol] for symbol in requested_symbols if symbol in source_by_symbol]
    if not sources:
        raise SystemExit(f"no sources matched symbols={requested_symbols}")
    matched_symbols = [source.symbol for source in sources]
    skipped_symbols = [symbol for symbol in requested_symbols if symbol not in source_by_symbol]

    if args.aq_smoke_timeframe and not args.clean_only:
        guard = run_claim_collision_audit(
            root,
            compact_root,
            allowed_roots=allowed_collision_roots(root, compact_root),
        )
        if not guard["pass"]:
            return write_claim_collision_no_launch_summary(
                root,
                compact_root,
                args=args,
                requested_symbols=requested_symbols,
                matched_symbols=matched_symbols,
                skipped_symbols=skipped_symbols,
                timeframes=timeframes,
                families=families,
                clean_bundles=[],
                aq_staging=[],
                guard=guard,
            )

    clean_bundles = []
    for source in sources:
        if args.reuse_clean:
            clean_bundles.append(load_clean_bundle(root, source.symbol, timeframes))
        else:
            clean_bundles.append(
                write_clean_bundle(
                    source,
                    root=root,
                    start=args.start,
                    end=args.end,
                    timeframes=timeframes,
                    max_rows=args.max_rows,
                    chunksize=args.chunksize,
                )
            )

    aq_staging: list[dict[str, Any]] = []
    aq_commands: list[dict[str, Any]] = []
    aq_gate_summaries: list[dict[str, Any]] = []
    if args.aq_smoke_timeframe:
        aq_symbols = matched_symbols[: args.aq_symbol_limit]
        aq_staging.append(
            stage_aq_inputs(
                root,
                symbols=aq_symbols,
                timeframe=args.aq_smoke_timeframe,
                start=args.start,
                end=args.end,
                families=families,
            )
        )
        if not args.clean_only:
            guard = run_claim_collision_audit(
                root,
                compact_root,
                allowed_roots=allowed_collision_roots(root, compact_root),
            )
            if not guard["pass"]:
                return write_claim_collision_no_launch_summary(
                    root,
                    compact_root,
                    args=args,
                    requested_symbols=requested_symbols,
                    matched_symbols=matched_symbols,
                    skipped_symbols=skipped_symbols,
                    timeframes=timeframes,
                    families=families,
                    clean_bundles=clean_bundles,
                    aq_staging=aq_staging,
                    guard=guard,
                )
            workspace = Path(aq_staging[-1]["workspace"])
            aq_env = sanitize_aq_subprocess_env()
            command = run_cmd(
                root,
                f"run_tomac_{args.aq_smoke_timeframe}",
                [AQ_PY, "run_tomac.py"],
                cwd=workspace,
                timeout=args.timeout,
                env=aq_env,
            )
            aq_commands.append(command)
            aq_gate_summaries.append(
                write_aq_gate_summary(
                    root,
                    compact_root,
                    timeframe=args.aq_smoke_timeframe,
                    command=command,
                    specs=generated_strategy_specs(aq_symbols, args.aq_smoke_timeframe, families=families),
                    clean_bundles=clean_bundles,
                )
            )

    summary = {
        "run_root": str(root),
        "compact_root": str(compact_root),
        "start": args.start,
        "end": args.end,
        "requested_symbols": requested_symbols,
        "symbols": matched_symbols,
        "skipped_symbols": skipped_symbols,
        "timeframes": timeframes,
        "families": families or [spec.key for spec in candidate_specs()],
        "clean_bundles": clean_bundles,
        "aq_staging": aq_staging,
        "aq_commands": aq_commands,
        "aq_gate_summaries": aq_gate_summaries,
        "future_leakage_policy": {
            "front_selection": "current timestamp volume only",
            "roll_adjustment": "previous selected close minus new selected open at roll boundary",
            "strategy_signals": "entry and exit raw conditions shifted one closed bar",
            "uses_shift_negative": False,
        },
    }
    (root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (compact_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    parser.add_argument("--compact-root", default=str(DEFAULT_COMPACT_ROOT))
    parser.add_argument("--symbols", default="ES,YM,NQ")
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--timeframes", default=",".join(DEFAULT_TIMEFRAMES))
    parser.add_argument("--families", default=None)
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--chunksize", type=int, default=500_000)
    parser.add_argument("--clean-only", action="store_true")
    parser.add_argument("--reuse-clean", action="store_true")
    parser.add_argument("--aq-smoke-timeframe", default=None)
    parser.add_argument("--aq-symbol-limit", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=1800)
    return parser.parse_args()


if __name__ == "__main__":
    ensure_pyarrow_runtime()
    print(json.dumps(run(parse_args()), indent=2))
