from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import tomac_strategy_inventory as inventory  # noqa: E402


class TomacStrategyInventoryTests(unittest.TestCase):
    def test_scan_tree_extracts_family_indicators_and_metadata(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            scan_file = root / "futures_factor_research_20260521" / "tomac_pair_relative_value_scan.py"
            scan_file.parent.mkdir(parents=True, exist_ok=True)
            scan_file.write_text(
                "\n".join(
                    [
                        "PAIR = ('NQ', 'YM')",
                        "BRANCH = 'RangeReversion -> CrossIndexRelativeValue -> ZScoreMeanReversion'",
                        "def build_zscore_signal():",
                        "    return '15m zscore pair relative value'",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            strategy_file = root / "90wr1.5rrr_strategy.py"
            strategy_file.write_text(
                "\n".join(
                    [
                        "class TomacNQSuperTrendAdxDisplacement:",
                        "    pass",
                        "",
                        "NOTES = 'NQ 1m 15m supertrend adx breakout with liquidity sweep reclaim'",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            rows = inventory.scan_tomac_tree(root)
            by_path = {row.relative_path: row for row in rows}

            pair_row = by_path["futures_factor_research_20260521/tomac_pair_relative_value_scan.py"]
            self.assertEqual(pair_row.file_kind, "scan")
            self.assertEqual(pair_row.family, "pair_relative_value")
            self.assertIn("zscore", pair_row.indicators)
            self.assertIn("relative_value", pair_row.indicators)
            self.assertEqual(pair_row.symbols, ["NQ", "YM"])
            self.assertIn("15m", pair_row.timeframes)

            strategy_row = by_path["90wr1.5rrr_strategy.py"]
            self.assertEqual(strategy_row.file_kind, "strategy")
            self.assertEqual(strategy_row.family, "trend_continuation")
            self.assertEqual(strategy_row.strategy_classes, ["TomacNQSuperTrendAdxDisplacement"])
            self.assertIn("supertrend", strategy_row.indicators)
            self.assertIn("adx", strategy_row.indicators)
            self.assertIn("breakout", strategy_row.indicators)
            self.assertEqual(strategy_row.symbols, ["NQ"])
            self.assertEqual(strategy_row.timeframes, ["1m", "15m"])

    def test_build_summary_counts_families_indicators_and_symbols(self) -> None:
        rows = [
            inventory.TomacStrategyRow(
                relative_path="a.py",
                file_kind="scan",
                family="pair_relative_value",
                symbols=["NQ", "YM"],
                timeframes=["15m"],
                indicators=["relative_value", "zscore"],
                strategy_classes=[],
                branch_hints=["RangeReversion -> CrossIndexRelativeValue -> ZScoreMeanReversion"],
            ),
            inventory.TomacStrategyRow(
                relative_path="b.py",
                file_kind="strategy",
                family="trend_continuation",
                symbols=["NQ"],
                timeframes=["1m", "15m"],
                indicators=["adx", "supertrend", "breakout"],
                strategy_classes=["TomacNQSuperTrendAdxDisplacement"],
                branch_hints=[],
            ),
            inventory.TomacStrategyRow(
                relative_path="c.py",
                file_kind="scan",
                family="trend_continuation",
                symbols=["YM"],
                timeframes=["1m"],
                indicators=["opening_drive", "rvol", "breakout"],
                strategy_classes=[],
                branch_hints=[],
            ),
        ]

        summary = inventory.build_summary(rows)

        self.assertEqual(summary["total_files"], 3)
        self.assertEqual(summary["family_counts"]["trend_continuation"], 2)
        self.assertEqual(summary["family_counts"]["pair_relative_value"], 1)
        self.assertEqual(summary["symbol_counts"]["NQ"], 2)
        self.assertEqual(summary["symbol_counts"]["YM"], 2)
        self.assertEqual(summary["indicator_counts"]["breakout"], 2)
        self.assertEqual(summary["file_kind_counts"]["scan"], 2)
        self.assertEqual(summary["timeframe_counts"]["15m"], 2)

    def test_cli_writes_inventory_json(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "Tomac"
            root.mkdir(parents=True, exist_ok=True)
            (root / "tomac_session_seasonality_scan.py").write_text(
                "BRANCH = 'SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotMomentum'\n",
                encoding="utf-8",
            )
            output = Path(tmpdir) / "inventory.json"

            exit_code = inventory.main(["--tomac-root", str(root), "--output-json", str(output)])

            self.assertEqual(exit_code, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["total_files"], 1)
            self.assertEqual(payload["summary"]["branch_count"], 1)
            self.assertEqual(payload["rows"][0]["family"], "session_seasonality")
            self.assertEqual(
                payload["branch_rows"][0]["branch_path"],
                "SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotMomentum",
            )

    def test_scan_tree_extracts_branch_hints_from_branch_function_calls(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            scan_file = root / "futures_factor_research_20260521" / "tomac_dense_family_scan.py"
            scan_file.parent.mkdir(parents=True, exist_ok=True)
            scan_file.write_text(
                "\n".join(
                    [
                        "def branch(main, sub, factor):",
                        "    return f\"{main} -> {sub} -> {factor}\"",
                        "",
                        "def score_summary(fid):",
                        "    if fid.startswith('vwap'):",
                        "        path = branch('RangeTransition', 'VWAPMeanReclaim', fid)",
                        "    elif fid.startswith('nr7'):",
                        "        path = branch('VolatilityCompressionExpansion', 'CrabelNR7', fid)",
                        "    elif fid.startswith('trend_pullback'):",
                        "        path = branch('TrendExpansion', 'PullbackReclaim', fid)",
                        "    else:",
                        "        path = branch('TrendExpansion', 'DonchianChannel', fid)",
                        "    return path",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            rows = inventory.scan_tomac_tree(root)

            self.assertEqual(len(rows), 1)
            self.assertEqual(
                rows[0].branch_hints,
                [
                    "RangeTransition -> VWAPMeanReclaim",
                    "VolatilityCompressionExpansion -> CrabelNR7",
                    "TrendExpansion -> PullbackReclaim",
                    "TrendExpansion -> DonchianChannel",
                ],
            )

    def test_scan_tree_extracts_fast_daily_regime_hints_from_add_trade_calls(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            scan_file = root / "futures_factor_research_20260521" / "tomac_fast_daily_scan.py"
            scan_file.parent.mkdir(parents=True, exist_ok=True)
            scan_file.write_text(
                "\n".join(
                    [
                        "def simulate_symbol(trades, symbol, day, regular, j, hold):",
                        '    add_trade(trades, symbol, "OR30_breakout_h60", "OpeningDrive", 1, regular, j, hold)',
                        '    add_trade(trades, symbol, "OR30_failed_breakout_fade_h60", "FailedBreakoutFade", -1, regular, j, hold)',
                        '    add_trade(trades, symbol, "PDH_sweep_reversal_h60", "LiquiditySweepReversal", -1, day, j, hold)',
                        '    add_trade(trades, symbol, "NR7_crabel_expansion_h60", "CompressionExpansion", 1, day, j, hold)',
                        '    add_trade(trades, symbol, "VWAP_reclaim_persist_h60", "VwapReclaimPersistence", 1, day, j, hold)',
                        '    add_trade(trades, symbol, "OR30_twoleg_continuation_h60", "OpeningDriveTwoLegContinuation", 1, regular, j, hold)',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            rows = inventory.scan_tomac_tree(root)

            self.assertEqual(len(rows), 1)
            self.assertIn(rows[0].family, {"opening_drive", "range_transition", "volatility_expansion"})
            self.assertEqual(
                rows[0].branch_hints,
                [
                    "TrendExpansion -> OpeningDriveBreakout",
                    "RangeReversion -> OpeningDriveFailedBreakoutFade",
                    "RangeReversion -> PriorDayLiquiditySweepReversal",
                    "VolatilityCompressionExpansion -> CrabelNR7",
                    "RangeTransition -> VWAPMeanReclaim -> VwapReclaimPersistence",
                    "TrendExpansion -> OpeningDriveExpansion -> OpeningDriveTwoLegContinuation",
                ],
            )

    def test_scan_tree_extracts_fast_daily_regime_hints_when_factor_id_is_variable(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            scan_file = root / "futures_factor_research_20260521" / "tomac_fast_daily_scan.py"
            scan_file.parent.mkdir(parents=True, exist_ok=True)
            scan_file.write_text(
                "\n".join(
                    [
                        "def simulate_symbol(trades, symbol, g, j, hold):",
                        '    fid = f"OR30_breakout_h{hold}"',
                        '    add_trade(trades, symbol, fid, "OpeningDrive", 1, g, j, hold)',
                        '    add_trade(trades, symbol, fid, "FailedBreakoutFade", -1, g, j, hold)',
                        '    add_trade(trades, symbol, fid, "LiquiditySweepReversal", -1, g, j, hold)',
                        '    add_trade(trades, symbol, fid, "VwapReclaimPersistence", 1, g, j, hold)',
                        '    add_trade(trades, symbol, fid, "OpeningDriveTwoLegContinuation", 1, g, j, hold)',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            rows = inventory.scan_tomac_tree(root)

            self.assertEqual(len(rows), 1)
            self.assertEqual(
                rows[0].branch_hints,
                [
                    "TrendExpansion -> OpeningDriveBreakout",
                    "RangeReversion -> OpeningDriveFailedBreakoutFade",
                    "RangeReversion -> PriorDayLiquiditySweepReversal",
                    "RangeTransition -> VWAPMeanReclaim -> VwapReclaimPersistence",
                    "TrendExpansion -> OpeningDriveExpansion -> OpeningDriveTwoLegContinuation",
                ],
            )

    def test_scan_tree_prefers_local_branch_identity_over_import_noise(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            scan_file = root / "futures_factor_research_20260521" / "tomac_mtf_trend_continuation_scan.py"
            scan_file.parent.mkdir(parents=True, exist_ok=True)
            scan_file.write_text(
                "\n".join(
                    [
                        "from tomac_high_excursion_scan import clean_window",
                        "BRANCH = 'TrendExpansion -> InitialBalanceExtension -> MtfTrendContinuation'",
                        "ALT = 'TrendExpansion -> MtfTrendAlignment -> DonchianContinuation'",
                        "def build_signal():",
                        "    return 'NQ YM XAU 1m 5m 15m 30m 1h 4h 1d trend continuation'",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            rows = inventory.scan_tomac_tree(root)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].family, "trend_continuation")
            self.assertEqual(
                rows[0].branch_hints,
                [
                    "TrendExpansion -> InitialBalanceExtension -> MtfTrendContinuation",
                    "TrendExpansion -> MtfTrendAlignment -> DonchianContinuation",
                ],
            )

    def test_scan_tree_strips_trailing_quote_and_comma_from_branch_hints(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            scan_file = root / "futures_factor_research_20260521" / "tomac_session_seasonality_scan.py"
            scan_file.parent.mkdir(parents=True, exist_ok=True)
            scan_file.write_text(
                "\n".join(
                    [
                        "BRANCH_BY_MODE = {",
                        '    "momentum": "SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotMomentum",',
                        '    "contrarian": "SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotContrarian",',
                        "}",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            rows = inventory.scan_tomac_tree(root)

            self.assertEqual(len(rows), 1)
            self.assertEqual(
                rows[0].branch_hints,
                [
                    "SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotMomentum",
                    "SessionRhythm -> TimeOfDaySeasonality -> AdaptiveSlotContrarian",
                ],
            )

    def test_scan_tree_classifies_root_ict_scripts_as_trend_continuation(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            strategy_file = root / "ultimate_ict_strategy.py"
            strategy_file.write_text(
                "\n".join(
                    [
                        "AM_KILLZONE = ('09:30', '11:30')",
                        "PM_KILLZONE = ('13:30', '15:30')",
                        "def check_ultimate_long(row, prev_row):",
                        "    liquidity_sweep = prev_row['low'] <= prev_row['pdl']",
                        "    reclaim = row['close'] > prev_row['pdl']",
                        "    bull_fvg = row['close'] < row['bull_fvg']",
                        "    near_ob = abs(row['close'] - row['bull_ob']) < row['atr'] * 2",
                        "    in_ote_zone = row['close'] >= row['ote_long_79']",
                        "    return liquidity_sweep and reclaim and bull_fvg and near_ob and in_ote_zone",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            rows = inventory.scan_tomac_tree(root)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].file_kind, "strategy")
            self.assertEqual(rows[0].family, "trend_continuation")
            self.assertIn("liquidity_sweep", rows[0].indicators)
            self.assertIn("session", rows[0].indicators)

    def test_extract_inline_branch_hints_ignores_long_non_branch_noise(self) -> None:
        noisy_text = "\n".join(
            [
                "HELP = 'A' * 400",
                "DOC = 'factor metrics " + ("x -> y " * 80) + "'",
                "BRANCH = 'TrendExpansion -> PullbackReclaim -> DenseContinuation'",
            ]
        )

        hints = inventory._extract_branch_hints(noisy_text)

        self.assertEqual(hints, ["TrendExpansion -> PullbackReclaim -> DenseContinuation"])

    def test_build_branch_rows_flattens_multi_branch_sources(self) -> None:
        rows = [
            inventory.TomacStrategyRow(
                relative_path="futures_factor_research_20260521/tomac_high_excursion_scan.py",
                file_kind="scan",
                family="high_excursion",
                symbols=["NQ", "YM", "XAU"],
                timeframes=["1m", "5m", "15m"],
                indicators=["high_excursion", "rvol", "vwap"],
                strategy_classes=[],
                branch_hints=[
                    "TrendExpansion -> InitialBalanceExtension",
                    "TrendExpansion -> PriorDayExtremeContinuation",
                    "RangeTransition -> OvernightInventoryFade",
                    "TrendExpansion -> ImpulseFollowThrough",
                ],
            )
        ]

        branch_rows = inventory.build_branch_rows(rows)
        branch_paths = [row.branch_path for row in branch_rows]
        families = {row.branch_path: row.family for row in branch_rows}

        self.assertEqual(len(branch_rows), 4)
        self.assertIn("TrendExpansion -> PriorDayExtremeContinuation", branch_paths)
        self.assertEqual(families["RangeTransition -> OvernightInventoryFade"], "range_transition")
        self.assertEqual(families["TrendExpansion -> ImpulseFollowThrough"], "high_excursion")


if __name__ == "__main__":
    unittest.main()
