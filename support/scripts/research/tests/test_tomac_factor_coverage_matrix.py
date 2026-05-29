from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import tomac_factor_coverage_matrix as coverage  # noqa: E402
import tomac_strategy_inventory as inventory  # noqa: E402


class TomacFactorCoverageMatrixTests(unittest.TestCase):
    def test_build_coverage_rows_marks_claimed_and_available_families(self) -> None:
        tomac_rows = [
            inventory.TomacStrategyRow(
                relative_path="tomac_mtf_trend_continuation_scan.py",
                file_kind="scan",
                family="trend_continuation",
                symbols=["NQ"],
                timeframes=["1m", "5m"],
                indicators=["trend"],
                strategy_classes=[],
                branch_hints=["TrendExpansion -> InitialBalanceExtension -> MtfTrendContinuation"],
            ),
            inventory.TomacStrategyRow(
                relative_path="tomac_pair_relative_value_scan.py",
                file_kind="scan",
                family="pair_relative_value",
                symbols=["NQ", "YM"],
                timeframes=["15m"],
                indicators=["pair", "relative_value", "zscore"],
                strategy_classes=[],
                branch_hints=["TrendExpansion -> CrossIndexRelativeMomentum -> ZScoreTrendContinuation"],
            ),
        ]
        active_claims = [
            (
                Path("a.claim"),
                {"agent_name": "codex-ib", "status": "active"},
                "trendexpansion initialbalanceextension mtftrendcontinuation tomacinitialbalanceextension",
            )
        ]

        rows = coverage.build_coverage_rows(tomac_rows, active_claims)
        by_subfamily = {row.subfamily: row for row in rows}

        self.assertEqual(by_subfamily["initial_balance_mtf_continuation"].status, "active_claimed")
        self.assertEqual(by_subfamily["initial_balance_mtf_continuation"].active_claim_count, 1)
        self.assertEqual(by_subfamily["cross_index_relative_value"].status, "available_for_rotation")
        self.assertEqual(by_subfamily["cross_index_relative_value"].active_claim_count, 0)
        self.assertIn("mtftrendcontinuation", by_subfamily["initial_balance_mtf_continuation"].match_tokens)

    def test_main_writes_json_and_csv(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tomac_root = root / "Tomac"
            claims_dir = root / "claims"
            tomac_root.mkdir(parents=True, exist_ok=True)
            claims_dir.mkdir(parents=True, exist_ok=True)
            (tomac_root / "tomac_session_seasonality_scan.py").write_text(
                "BRANCH = 'SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotMomentum'\n",
                encoding="utf-8",
            )
            (claims_dir / "a.claim").write_text(
                json.dumps(
                    {
                        "agent_name": "codex-session",
                        "status": "active",
                        "scope": "SessionRhythm -> TimeOfDaySeasonality -> BalancedAdaptiveSlotPortfolio",
                    }
                ),
                encoding="utf-8",
            )
            output_json = root / "coverage.json"
            output_csv = root / "coverage.csv"

            exit_code = coverage.main(
                [
                    "--tomac-root",
                    str(tomac_root),
                    "--claims-dir",
                    str(claims_dir),
                    "--output-json",
                    str(output_json),
                    "--output-csv",
                    str(output_csv),
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["family_count"], 1)
            self.assertTrue(output_csv.exists())

    def test_initial_balance_claim_does_not_match_pair_relative_value_subfamily(self) -> None:
        row = inventory.TomacStrategyRow(
            relative_path="tomac_pair_relative_value_scan.py",
            file_kind="scan",
            family="pair_relative_value",
            symbols=["NQ", "YM"],
            timeframes=["15m"],
            indicators=["pair", "relative_value", "zscore"],
            strategy_classes=[],
            branch_hints=["TrendExpansion -> CrossIndexRelativeMomentum -> ZScoreTrendContinuation"],
        )
        active_claims = [
            (
                Path("a.claim"),
                {"agent_name": "codex-ib", "status": "active"},
                "trendexpansion initialbalanceextension mtftrendcontinuation tomacinitialbalanceextension",
            )
        ]

        rows = coverage.build_coverage_rows([row], active_claims)

        self.assertEqual(rows[0].subfamily, "cross_index_relative_value")
        self.assertEqual(rows[0].active_claim_count, 0)

    def test_multi_branch_row_expands_into_multiple_subfamilies(self) -> None:
        row = inventory.TomacStrategyRow(
            relative_path="tomac_dense_family_scan.py",
            file_kind="scan",
            family="trend_continuation",
            symbols=["NQ", "YM", "XAU"],
            timeframes=["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
            indicators=["donchian", "trend", "volatility", "vwap"],
            strategy_classes=[],
            branch_hints=[
                "RangeTransition -> VWAPMeanReclaim",
                "VolatilityCompressionExpansion -> CrabelNR7",
                "TrendExpansion -> PullbackReclaim",
                "TrendExpansion -> DonchianChannel",
            ],
        )

        rows = coverage.build_coverage_rows([row], [])
        by_subfamily = {item.subfamily: item for item in rows}

        self.assertIn("vwap_mean_reclaim", by_subfamily)
        self.assertIn("nr7_crabel_range_expansion", by_subfamily)
        self.assertIn("trend_pullback_reclaim", by_subfamily)
        self.assertIn("donchian_trend_breakout", by_subfamily)
        self.assertEqual(by_subfamily["nr7_crabel_range_expansion"].source_files, 1)
        self.assertEqual(by_subfamily["vwap_mean_reclaim"].family, "range_transition")
        self.assertEqual(by_subfamily["nr7_crabel_range_expansion"].family, "volatility_expansion")

    def test_load_active_claims_treats_launch_in_progress_as_active(self) -> None:
        with TemporaryDirectory() as tmpdir:
            claims_dir = Path(tmpdir)
            claim_path = claims_dir / "a.claim"
            claim_path.write_text(
                json.dumps(
                    {
                        "agent_name": "codex-ib",
                        "status": "launch_in_progress_same_root",
                        "scope": "TrendExpansion -> InitialBalanceExtension -> MtfTrendContinuation",
                    }
                ),
                encoding="utf-8",
            )

            rows = coverage._load_active_claims(claims_dir)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][0].name, "a.claim")

    def test_load_active_claims_treats_incubate_status_as_still_covered(self) -> None:
        with TemporaryDirectory() as tmpdir:
            claims_dir = Path(tmpdir)
            claim_path = claims_dir / "a.claim"
            claim_path.write_text(
                json.dumps(
                    {
                        "agent_name": "codex-donchian",
                        "status": "incubate_same_root_positive_but_density_repair_failed",
                        "scope": "TrendExpansion -> DailyDonchianTrendContinuation -> SwingBreakoutContinuation",
                    }
                ),
                encoding="utf-8",
            )

            rows = coverage._load_active_claims(claims_dir)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][0].name, "a.claim")

    def test_load_active_claims_treats_staged_wait_status_as_active(self) -> None:
        with TemporaryDirectory() as tmpdir:
            claims_dir = Path(tmpdir)
            claim_path = claims_dir / "a.claim"
            claim_path.write_text(
                json.dumps(
                    {
                        "agent_name": "codex-ib-stage",
                        "status": "staged_wait_live_backend_clear",
                        "scope": "TrendExpansion -> InitialBalanceExtension -> MtfTrendContinuation",
                    }
                ),
                encoding="utf-8",
            )

            rows = coverage._load_active_claims(claims_dir)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][0].name, "a.claim")

    def test_load_active_claims_ignores_decided_claim_even_if_status_looks_active(self) -> None:
        with TemporaryDirectory() as tmpdir:
            claims_dir = Path(tmpdir)
            claim_path = claims_dir / "a.claim"
            claim_path.write_text(
                json.dumps(
                    {
                        "agent_name": "codex-decided",
                        "status": "active_prep_only_await_launch_verified_blocked",
                        "decision": "takeover_refresh_blocked_live_factor_processes_2",
                        "scope": "TrendExpansion -> DonchianChannel -> TrendBreakoutContinuation",
                    }
                ),
                encoding="utf-8",
            )

            rows = coverage._load_active_claims(claims_dir)

            self.assertEqual(rows, [])

    def test_load_active_claims_ignores_terminalized_timestamp_even_if_status_looks_active(self) -> None:
        with TemporaryDirectory() as tmpdir:
            claims_dir = Path(tmpdir)
            claim_path = claims_dir / "a.claim"
            claim_path.write_text(
                json.dumps(
                    {
                        "agent_name": "codex-terminalized",
                        "status": "staged_wait_live_runtime_clear_same_root",
                        "terminalized_at": "2026-05-26T14:47:53+0800",
                        "scope": "TrendExpansion -> PriorDayExtremeContinuation -> ExitPersistence",
                    }
                ),
                encoding="utf-8",
            )

            rows = coverage._load_active_claims(claims_dir)

            self.assertEqual(rows, [])

    def test_balanced_tod_scope_matches_even_with_structured_fields_present(self) -> None:
        row = inventory.TomacStrategyRow(
            relative_path="tomac_tod_portfolio_aq.py",
            file_kind="utility",
            family="session_seasonality",
            symbols=["NQ"],
            timeframes=["1m"],
            indicators=["seasonality", "tod"],
            strategy_classes=[],
            branch_hints=["SessionRhythm -> TimeOfDaySeasonality -> BalancedAdaptiveSlotPortfolio"],
        )
        active_claims = [
            (
                Path("balanced.claim"),
                {
                    "agent_name": "codex-balanced",
                    "status": "active",
                    "scope": "Board B TOMAC same-root profitability-factor continuation for SessionRhythm -> TimeOfDaySeasonality -> BalancedAdaptiveSlotPortfolio",
                    "write_surface": "/tmp/ict-engine-tomac-tod-balanced-portfolio-training/workdoc.md",
                    "run_root": "/tmp/ict-engine-tomac-tod-balanced-portfolio-training",
                },
                coverage._normalize_claim_text(
                    {
                        "agent_name": "codex-balanced",
                        "status": "active",
                        "scope": "Board B TOMAC same-root profitability-factor continuation for SessionRhythm -> TimeOfDaySeasonality -> BalancedAdaptiveSlotPortfolio",
                        "write_surface": "/tmp/ict-engine-tomac-tod-balanced-portfolio-training/workdoc.md",
                        "run_root": "/tmp/ict-engine-tomac-tod-balanced-portfolio-training",
                    },
                    Path("balanced.claim"),
                ),
            )
        ]

        rows = coverage.build_coverage_rows([row], active_claims)

        self.assertEqual(rows[0].active_claim_count, 1)
        self.assertEqual(rows[0].status, "active_claimed")

    def test_representative_branch_prefers_exact_daily_donchian_hint(self) -> None:
        row = inventory.TomacStrategyRow(
            relative_path="tomac_swing_volatility_scan.py",
            file_kind="scan",
            family="swing_volatility",
            symbols=["NQ"],
            timeframes=["1m"],
            indicators=["donchian", "volatility"],
            strategy_classes=[],
            branch_hints=[
                "VolatilityCompressionExpansion -> DailyAtrSqueezeBreakout -> SwingBreakoutContinuation",
                "TrendExpansion -> DailyDonchianTrendContinuation -> SwingBreakoutContinuation",
            ],
        )

        rows = coverage.build_coverage_rows([row], [])
        by_subfamily = {item.subfamily: item for item in rows}

        self.assertEqual(
            by_subfamily["daily_donchian_trend_continuation"].representative_branch,
            "TrendExpansion -> DailyDonchianTrendContinuation -> SwingBreakoutContinuation",
        )

    def test_build_coverage_rows_ignores_test_files(self) -> None:
        rows = coverage.build_coverage_rows(
            [
                inventory.TomacStrategyRow(
                    relative_path="test_tomac_tod_portfolio_aq.py",
                    file_kind="test",
                    family="session_seasonality",
                    symbols=["NQ"],
                    timeframes=[],
                    indicators=["seasonality", "tod"],
                    strategy_classes=[],
                    branch_hints=["SessionRhythm -> TimeOfDaySeasonality -> BalancedAdaptiveSlotPortfolio"],
                ),
                inventory.TomacStrategyRow(
                    relative_path="tomac_tod_portfolio_aq.py",
                    file_kind="utility",
                    family="session_seasonality",
                    symbols=["NQ"],
                    timeframes=["1m"],
                    indicators=["seasonality", "tod"],
                    strategy_classes=[],
                    branch_hints=["SessionRhythm -> TimeOfDaySeasonality -> BalancedAdaptiveSlotPortfolio"],
                ),
            ],
            [],
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].subfamily, "balanced_tod_portfolio")
        self.assertEqual(rows[0].source_paths, ["tomac_tod_portfolio_aq.py"])

    def test_fast_daily_multi_branch_row_maps_into_distinct_subfamilies(self) -> None:
        row = inventory.TomacStrategyRow(
            relative_path="tomac_fast_daily_scan.py",
            file_kind="scan",
            family="opening_drive",
            symbols=["NQ", "YM", "XAU"],
            timeframes=["1m"],
            indicators=["opening_drive", "liquidity_sweep", "volatility", "vwap"],
            strategy_classes=[],
            branch_hints=[
                "TrendExpansion -> OpeningDriveBreakout",
                "RangeReversion -> OpeningDriveFailedBreakoutFade",
                "RangeReversion -> PriorDayLiquiditySweepReversal",
                "VolatilityCompressionExpansion -> CrabelNR7",
                "RangeTransition -> VWAPMeanReclaim -> VwapReclaimPersistence",
                "TrendExpansion -> OpeningDriveExpansion -> OpeningDriveTwoLegContinuation",
            ],
        )

        rows = coverage.build_coverage_rows([row], [])
        by_subfamily = {item.subfamily: item for item in rows}

        self.assertEqual(by_subfamily["opening_drive_breakout"].family, "opening_drive")
        self.assertEqual(by_subfamily["opening_drive_failed_breakout_fade"].family, "opening_drive")
        self.assertEqual(by_subfamily["opening_drive_two_leg_continuation"].family, "opening_drive")
        self.assertEqual(by_subfamily["prior_day_liquidity_sweep_reversal"].family, "liquidity_sweep_reversal")
        self.assertEqual(by_subfamily["nr7_crabel_range_expansion"].family, "volatility_expansion")
        self.assertEqual(by_subfamily["vwap_reclaim_persistence"].family, "range_transition")

    def test_broad_prior_day_scope_does_not_false_match_high_excursion_claim(self) -> None:
        row = inventory.TomacStrategyRow(
            relative_path="tomac_high_excursion_scan.py",
            file_kind="scan",
            family="high_excursion",
            symbols=["NQ"],
            timeframes=["1m"],
            indicators=["high_excursion", "trend"],
            strategy_classes=[],
            branch_hints=["TrendExpansion -> PriorDayExtremeContinuation"],
        )
        active_claims = [
            (
                Path("crabel.claim"),
                {
                    "agent_name": "codex-crabel",
                    "status": "active",
                    "scope": "Board B TOMAC Crabel NR7 rooted profitability-factor training on local retained futures data with a 1m execution origin and prior-day NR7 context.",
                    "active_task": "Read back whether any NR7_crabel_expansion branch has a real 5bps-per-side Gate 1 survivor before any Auto-Quant handoff.",
                    "write_surface": "/tmp/ict-engine-tomac-crabel-nr7-training/workdoc.md",
                    "branch_path": "VolatilityCompressionExpansion -> CrabelNR7",
                },
                coverage._normalize_claim_text(
                    {
                        "agent_name": "codex-crabel",
                        "status": "active",
                        "scope": "Board B TOMAC Crabel NR7 rooted profitability-factor training on local retained futures data with a 1m execution origin and prior-day NR7 context.",
                        "active_task": "Read back whether any NR7_crabel_expansion branch has a real 5bps-per-side Gate 1 survivor before any Auto-Quant handoff.",
                        "write_surface": "/tmp/ict-engine-tomac-crabel-nr7-training/workdoc.md",
                        "branch_path": "VolatilityCompressionExpansion -> CrabelNR7",
                    },
                    Path("crabel.claim"),
                ),
            )
        ]

        rows = coverage.build_coverage_rows([row], active_claims)

        self.assertEqual(rows[0].subfamily, "high_excursion_priorday_overnight")
        self.assertEqual(rows[0].active_claim_count, 0)
        self.assertEqual(rows[0].status, "available_for_rotation")

    def test_prior_day_extreme_branch_specific_claim_matches_high_excursion(self) -> None:
        row = inventory.TomacStrategyRow(
            relative_path="tomac_high_excursion_scan.py",
            file_kind="scan",
            family="high_excursion",
            symbols=["NQ"],
            timeframes=["1m"],
            indicators=["high_excursion", "trend"],
            strategy_classes=[],
            branch_hints=["TrendExpansion -> PriorDayExtremeContinuation"],
        )
        active_claims = [
            (
                Path("pde.claim"),
                {
                    "agent_name": "codex-pde",
                    "status": "active",
                    "write_surface": "/tmp/ict-engine-factor-docs/board-b/20260526T105509+0800-codex-tomac-prior-day-extreme-continuation-training.md",
                    "run_root": "/tmp/ict-engine-tomac-prior-day-extreme-continuation-20260526T105509+0800",
                },
                coverage._normalize_claim_text(
                    {
                        "agent_name": "codex-pde",
                        "status": "active",
                        "write_surface": "/tmp/ict-engine-factor-docs/board-b/20260526T105509+0800-codex-tomac-prior-day-extreme-continuation-training.md",
                        "run_root": "/tmp/ict-engine-tomac-prior-day-extreme-continuation-20260526T105509+0800",
                    },
                    Path("pde.claim"),
                ),
            )
        ]

        rows = coverage.build_coverage_rows([row], active_claims)

        self.assertEqual(rows[0].active_claim_count, 1)
        self.assertEqual(rows[0].status, "active_claimed")

    def test_prior_day_liquidity_sweep_claim_does_not_false_match_high_excursion(self) -> None:
        row = inventory.TomacStrategyRow(
            relative_path="tomac_high_excursion_scan.py",
            file_kind="scan",
            family="high_excursion",
            symbols=["NQ"],
            timeframes=["1m"],
            indicators=["high_excursion", "trend"],
            strategy_classes=[],
            branch_hints=["TrendExpansion -> PriorDayExtremeContinuation"],
        )
        active_claims = [
            (
                Path("pdl.claim"),
                {
                    "agent_name": "codex-pdl",
                    "status": "active",
                    "scope": "Board B stale-doc takeover for the exact PriorDayLiquiditySweepReversal rooted profitability branch using local retained TOMAC data and a 1m origin.",
                    "write_surface": "/tmp/ict-engine-tomac-prior-day-liquidity-sweep-reversal-takeover-20260526T110807+0800/workdoc.md",
                    "run_root": "/tmp/ict-engine-tomac-prior-day-liquidity-sweep-reversal-takeover-20260526T110807+0800",
                },
                coverage._normalize_claim_text(
                    {
                        "agent_name": "codex-pdl",
                        "status": "active",
                        "scope": "Board B stale-doc takeover for the exact PriorDayLiquiditySweepReversal rooted profitability branch using local retained TOMAC data and a 1m origin.",
                        "write_surface": "/tmp/ict-engine-tomac-prior-day-liquidity-sweep-reversal-takeover-20260526T110807+0800/workdoc.md",
                        "run_root": "/tmp/ict-engine-tomac-prior-day-liquidity-sweep-reversal-takeover-20260526T110807+0800",
                    },
                    Path("pdl.claim"),
                ),
            )
        ]

        rows = coverage.build_coverage_rows([row], active_claims)

        self.assertEqual(rows[0].active_claim_count, 0)
        self.assertEqual(rows[0].status, "available_for_rotation")

    def test_nr7_killzone_child_claim_matches_nr7_family(self) -> None:
        row = inventory.TomacStrategyRow(
            relative_path="tomac_fast_daily_scan.py",
            file_kind="scan",
            family="opening_drive",
            symbols=["NQ", "YM", "XAU"],
            timeframes=["1m"],
            indicators=["opening_drive", "liquidity_sweep", "volatility", "vwap"],
            strategy_classes=[],
            branch_hints=["VolatilityCompressionExpansion -> CrabelNR7"],
        )
        payload = {
            "agent_name": "codex-6e-nr7-range-expansion-killzone-filter-prep-20260526T210420+0800",
            "status": "active",
            "scope": "Board B TOMAC prep-only profitability-factor lane for the exact RangeConsolidation -> NarrowRangeCompression -> Nr7RangeExpansion -> KillzoneFilter child branch using local retained futures history and a 1m origin.",
            "active_task": "Stage the exact sibling child branch packet, workdoc, claim, and prep-only AQ surface for Nr7RangeExpansion -> KillzoneFilter without colliding with the shared TOMAC runtime.",
            "write_surface": "/tmp/ict-engine-tomac-nr7-range-expansion-killzone-filter-prep-20260526T210420+0800/workdoc.md",
            "run_root": "/tmp/ict-engine-tomac-nr7-range-expansion-killzone-filter-prep-20260526T210420+0800",
        }
        active_claims = [
            (
                Path("nr7.claim"),
                payload,
                coverage._normalize_claim_text(payload, Path("nr7.claim")),
            )
        ]

        rows = coverage.build_coverage_rows([row], active_claims)

        self.assertEqual(rows[0].subfamily, "nr7_crabel_range_expansion")
        self.assertEqual(rows[0].active_claim_count, 1)
        self.assertEqual(rows[0].status, "active_claimed")

    def test_opening_drive_twoleg_repair_claim_matches_only_twoleg_subfamily(self) -> None:
        rows = coverage.build_coverage_rows(
            [
                inventory.TomacStrategyRow(
                    relative_path="tomac_fast_daily_scan.py",
                    file_kind="scan",
                    family="opening_drive",
                    symbols=["NQ"],
                    timeframes=["1m"],
                    indicators=["opening_drive"],
                    strategy_classes=[],
                    branch_hints=["TrendExpansion -> OpeningDriveBreakout"],
                ),
                inventory.TomacStrategyRow(
                    relative_path="tomac_fast_daily_scan.py",
                    file_kind="scan",
                    family="opening_drive",
                    symbols=["NQ"],
                    timeframes=["1m"],
                    indicators=["opening_drive"],
                    strategy_classes=[],
                    branch_hints=["TrendExpansion -> OpeningDriveExpansion -> OpeningDriveTwoLegContinuation"],
                ),
            ],
            [
                (
                    Path("twoleg.claim"),
                    {
                        "agent_name": "codex-tomac-opening-drive-twoleg-execution-repair-live-20260526T212648+0800",
                        "status": "active",
                        "scope": "Board B TOMAC same-root execution-repair continuation for TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> tomac_nq_bidir_opening_drive_twoleg_t15_x1080_exact_v1 using retained local NQ 1m history and full MTF context.",
                        "active_task": "Launch the exact local Auto-Quant loop from a fresh run root now that the latest compact audit shows live_factor_processes=0, then classify same-root execution materialization truth without relaxing gates.",
                        "write_surface": "/tmp/ict-engine-tomac-opening-drive-twoleg-execution-repair-live-20260526T212648+0800/workdoc.md",
                        "run_root": "/tmp/ict-engine-tomac-opening-drive-twoleg-execution-repair-live-20260526T212648+0800",
                        "factor_id": "tomac_nq_bidir_opening_drive_twoleg_t15_x1080_exact_v1",
                        "branch_path": "TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> tomac_nq_bidir_opening_drive_twoleg_t15_x1080_exact_v1",
                    },
                    coverage._normalize_claim_text(
                        {
                            "agent_name": "codex-tomac-opening-drive-twoleg-execution-repair-live-20260526T212648+0800",
                            "status": "active",
                            "scope": "Board B TOMAC same-root execution-repair continuation for TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> tomac_nq_bidir_opening_drive_twoleg_t15_x1080_exact_v1 using retained local NQ 1m history and full MTF context.",
                            "active_task": "Launch the exact local Auto-Quant loop from a fresh run root now that the latest compact audit shows live_factor_processes=0, then classify same-root execution materialization truth without relaxing gates.",
                            "write_surface": "/tmp/ict-engine-tomac-opening-drive-twoleg-execution-repair-live-20260526T212648+0800/workdoc.md",
                            "run_root": "/tmp/ict-engine-tomac-opening-drive-twoleg-execution-repair-live-20260526T212648+0800",
                            "factor_id": "tomac_nq_bidir_opening_drive_twoleg_t15_x1080_exact_v1",
                            "branch_path": "TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> tomac_nq_bidir_opening_drive_twoleg_t15_x1080_exact_v1",
                        },
                        Path("twoleg.claim"),
                    ),
                )
            ],
        )
        by_subfamily = {row.subfamily: row for row in rows}

        self.assertEqual(by_subfamily["opening_drive_breakout"].active_claim_count, 0)
        self.assertEqual(by_subfamily["opening_drive_breakout"].status, "available_for_rotation")
        self.assertEqual(by_subfamily["opening_drive_two_leg_continuation"].active_claim_count, 1)
        self.assertEqual(by_subfamily["opening_drive_two_leg_continuation"].status, "active_claimed")

    def test_prior_day_multifactor_reclaim_claim_matches_liquidity_sweep_family(self) -> None:
        row = inventory.TomacStrategyRow(
            relative_path="tomac_fast_daily_scan.py",
            file_kind="scan",
            family="opening_drive",
            symbols=["ES"],
            timeframes=["1m"],
            indicators=["liquidity_sweep", "reversion"],
            strategy_classes=[],
            branch_hints=["RangeReversion -> PriorDayLiquiditySweepReversal"],
        )
        payload = {
            "agent_name": "codex-tomac-prior-day-multifactor-confluence-reclaim-aq-contract-repair-20260526T213617+0800",
            "status": "active_contract_diagnostic_no_launch_foreign_runtime_live",
            "scope": "Board B TOMAC contract-diagnostic continuation for the exact RangeReversion -> PriorDayLiquiditySweepReversal -> MultiFactorConfluenceReclaim branch using existing same-root source-positive evidence and current repo runner ownership.",
            "active_task": "Diagnose the canonical clean-AQ owner for MultiFactorConfluenceReclaim, prove the family-key and AQ-staging contract gap from current source, and prepare the smallest same-root correction path without launching while a foreign TOMAC run_tomac.py is live.",
            "write_surface": "/tmp/ict-engine-tomac-prior-day-multifactor-confluence-reclaim-aq-contract-repair-20260526T213617+0800/workdoc.md",
            "run_root": "/tmp/ict-engine-tomac-prior-day-multifactor-confluence-reclaim-aq-contract-repair-20260526T213617+0800",
            "branch_path": "RangeReversion -> PriorDayLiquiditySweepReversal -> MultiFactorConfluenceReclaim -> tomac_es_prior_day_multifactor_confluence_reclaim_1m_v1",
            "factor_id": "tomac_es_prior_day_multifactor_confluence_reclaim_1m_v1",
        }
        active_claims = [
            (
                Path("prior-day.claim"),
                payload,
                coverage._normalize_claim_text(payload, Path("prior-day.claim")),
            )
        ]

        rows = coverage.build_coverage_rows([row], active_claims)

        self.assertEqual(rows[0].subfamily, "prior_day_liquidity_sweep_reversal")
        self.assertEqual(rows[0].active_claim_count, 1)
        self.assertEqual(rows[0].status, "active_claimed")


if __name__ == "__main__":
    unittest.main()
