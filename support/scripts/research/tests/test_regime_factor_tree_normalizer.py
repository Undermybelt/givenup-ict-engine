from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import regime_factor_tree_normalizer as normalizer  # noqa: E402


class RegimeFactorTreeNormalizerTests(unittest.TestCase):
    def test_moves_futures_symbol_timeframe_prefix_into_labels(self) -> None:
        result = normalizer.normalize_branch_path(
            "FUTURES -> precious_metals -> SI -> 5m -> RangeConsolidation -> TightRangeBandExpansionFade -> factor_v1"
        )

        self.assertEqual(
            result["canonical_branch_path"],
            "RangeConsolidation -> TightRangeBandExpansionFade -> factor_v1",
        )
        self.assertEqual(
            result["labels"],
            {
                "market": "FUTURES",
                "product": "precious_metals",
                "symbol": "SI",
                "timeframe": "5m",
            },
        )
        self.assertTrue(result["was_normalized"])
        self.assertEqual(result["main_regime"], "RangeConsolidation")
        self.assertEqual(
            result["full_rooted_identity_path"],
            "FUTURES -> precious_metals -> SI -> 5m -> RangeConsolidation -> TightRangeBandExpansionFade -> factor_v1",
        )

    def test_moves_crypto_market_prefix_into_labels(self) -> None:
        result = normalizer.normalize_branch_path(
            "CryptoLinearPerp -> RangeReversion -> ConnorsRsi2Rebound -> bybit_sandusdt_connors_rsi2_rebound_30m_exact_v1",
            labels={"symbol": "SANDUSDT", "timeframe": "30m"},
        )

        self.assertEqual(
            result["canonical_branch_path"],
            "RangeReversion -> ConnorsRsi2Rebound -> bybit_sandusdt_connors_rsi2_rebound_30m_exact_v1",
        )
        self.assertEqual(result["labels"]["market"], "CryptoLinearPerp")
        self.assertEqual(result["labels"]["symbol"], "SANDUSDT")
        self.assertEqual(result["labels"]["timeframe"], "30m")
        self.assertEqual(result["main_regime"], "RangeReversion")
        self.assertTrue(result["canonical_root_ok"])
        self.assertEqual(result["violations"], [])

    def test_reports_non_main_regime_root_without_guessing_remap(self) -> None:
        result = normalizer.normalize_branch_path(
            "FalseBreakoutReversal -> TurtleSoupReversal -> factor_v1",
            labels={"market": "FUTURES", "symbol": "SI", "timeframe": "15m"},
        )

        self.assertEqual(
            result["canonical_branch_path"],
            "FalseBreakoutReversal -> TurtleSoupReversal -> factor_v1",
        )
        self.assertFalse(result["canonical_root_ok"])
        self.assertEqual(result["violations"], ["non_main_regime_root:FalseBreakoutReversal"])
        self.assertEqual(result["labels"]["symbol"], "SI")

    def test_provider_and_symbol_prefixes_are_labels_not_tree_nodes(self) -> None:
        result = normalizer.normalize_branch_path(
            "IBKR -> FUTURES -> M2K -> 1m -> RangeReversion -> LiquiditySweepRejectShort -> factor_v1",
            labels={"window": "7 D"},
        )

        self.assertEqual(
            result["canonical_branch_path"],
            "RangeReversion -> LiquiditySweepRejectShort -> factor_v1",
        )
        self.assertEqual(
            result["labels"],
            {
                "provider": "IBKR",
                "market": "FUTURES",
                "symbol": "M2K",
                "timeframe": "1m",
                "window": "7 D",
            },
        )
        self.assertEqual(result["main_regime"], "RangeReversion")

    def test_preserves_already_regime_rooted_path(self) -> None:
        result = normalizer.normalize_branch_path(
            "TrendExpansion -> TrendReclaim -> tvr_crwd5m_trend_reclaim_full_ladder_v1",
            labels={"market": "US_EQ", "symbol": "CRWD", "timeframe": "5m"},
        )

        self.assertEqual(
            result["canonical_branch_path"],
            "TrendExpansion -> TrendReclaim -> tvr_crwd5m_trend_reclaim_full_ladder_v1",
        )
        self.assertFalse(result["was_normalized"])
        self.assertEqual(result["labels"]["market"], "US_EQ")

    def test_legacy_prefix_labels_override_stale_payload_symbol(self) -> None:
        result = normalizer.normalize_branch_path(
            "US_EQ -> single_stock -> CRWD -> 5m -> RangeReversion -> AiSecuritySoftwareOversoldReclaim -> factor_v1",
            labels={
                "market": "US_EQ",
                "product": "single_stock",
                "symbol": "YF_AI_SECURITY_CRWD5M_PDA_SEQUENCE_CONSISTENCY_LIGHT_DOWNSTREAM",
                "timeframe": "5m",
            },
        )

        self.assertEqual(result["labels"]["symbol"], "CRWD")
        self.assertEqual(result["labels"]["product"], "single_stock")
        self.assertEqual(result["labels"]["timeframe"], "5m")
        self.assertEqual(result["main_regime"], "RangeReversion")

    def test_requires_known_regime_root(self) -> None:
        result = normalizer.normalize_branch_path("US_EQ -> single_stock -> CRWD -> 5m")

        self.assertEqual(result["canonical_branch_path"], "")
        self.assertIn("missing_known_main_regime", result["warnings"])

    def test_metrics_file_preserves_portability_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / "terminal_metrics.json"
            metrics_path.write_text(
                """
{
  "branch_path": "IBKR -> FUTURES -> M2K -> 1m -> RangeReversion -> LiquiditySweepRejectShort -> factor_v1",
  "market": "FUTURES",
  "product": "equity_index",
  "provider": "IBKR",
  "symbol": "M2K",
  "contract": "202606",
  "timeframe": "1m",
  "base_timeframe": "1m",
  "ladder_timeframes": "1m/5m/15m/30m/1h/4h/1d",
  "window": "7 D",
  "duration": "7 D",
  "category": "futures"
}
""",
                encoding="utf-8",
            )

            result = normalizer.normalize_metrics_file(metrics_path)

        self.assertEqual(
            result["canonical_branch_path"],
            "RangeReversion -> LiquiditySweepRejectShort -> factor_v1",
        )
        self.assertEqual(result["labels"]["contract"], "202606")
        self.assertEqual(result["labels"]["base_timeframe"], "1m")
        self.assertEqual(result["labels"]["ladder_timeframes"], "1m/5m/15m/30m/1h/4h/1d")
        self.assertEqual(result["labels"]["window"], "7 D")
        self.assertEqual(result["labels"]["duration"], "7 D")

    def test_metrics_file_extracts_nested_labels_for_new_packets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / "terminal_metrics.json"
            metrics_path.write_text(
                """
{
  "branch_path": "TrendExpansion -> CryptoKstCoppockMomentum -> factor_v1",
  "labels": {
    "market": "CryptoLinearPerp",
    "provider": "Bybit public linear",
    "symbols": "FILUSDT/INJUSDT",
    "timeframes": "1m/5m/15m/30m/1h/4h/1d",
    "category": "linear",
    "window": "2026-02-17..2026-05-17"
  }
}
""",
                encoding="utf-8",
            )

            result = normalizer.normalize_metrics_file(metrics_path)

        self.assertEqual(result["canonical_branch_path"], "TrendExpansion -> CryptoKstCoppockMomentum -> factor_v1")
        self.assertTrue(result["canonical_root_ok"])
        self.assertEqual(result["labels"]["symbols"], "FILUSDT/INJUSDT")
        self.assertEqual(result["labels"]["timeframes"], "1m/5m/15m/30m/1h/4h/1d")

    def test_metrics_file_uses_branch_path_template_for_current_gate1_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / "terminal_metrics.json"
            metrics_path.write_text(
                """
{
  "branch_fields_preserved": true,
  "branch_path_template": "TrendExpansion -> MicroTrendPullbackReclaim -> factor_v1",
  "branch_paths": [
    "TrendExpansion -> MicroTrendPullbackReclaim -> factor_v1"
  ],
  "provider_rows": [
    {
      "market": "FUTURES",
      "product": "precious_metals",
      "provider": "IBKR",
      "symbol": "MGC",
      "timeframe": "1m",
      "duration": "2 D"
    }
  ]
}
""",
                encoding="utf-8",
            )

            result = normalizer.normalize_metrics_file(metrics_path)

        self.assertEqual(
            result["canonical_branch_path"],
            "TrendExpansion -> MicroTrendPullbackReclaim -> factor_v1",
        )
        self.assertTrue(result["canonical_root_ok"])
        self.assertEqual(result["violations"], [])
        self.assertEqual(result["labels"]["market"], "FUTURES")
        self.assertEqual(result["labels"]["product"], "precious_metals")
        self.assertEqual(result["labels"]["provider"], "IBKR")
        self.assertEqual(result["labels"]["symbol"], "MGC")
        self.assertEqual(result["labels"]["timeframe"], "1m")
        self.assertEqual(result["labels"]["duration"], "2 D")

    def test_metrics_file_extracts_cost_stress_row_label_and_ladder_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / "terminal_metrics.json"
            metrics_path.write_text(
                """
{
  "branch_path": "TrendExpansion -> BuyNowPayLaterOpeningDriveVwapReclaim -> opening_drive_vwap_reclaim -> factor_v1",
  "row_counts": {
    "1m": 11700,
    "5m": 4992,
    "15m": 1664,
    "30m": 832,
    "1h": 448,
    "4h": 316,
    "1d": 251
  },
  "selected_windows": {
    "1m": "30 D",
    "5m": "3 M",
    "15m": "3 M",
    "30m": "3 M",
    "1h": "3 M",
    "4h": "6 M",
    "1d": "1 Y"
  },
  "cost_stress_rows": [
    {
      "label": "SEZL/30m/quality",
      "branch_path": "TrendExpansion -> BuyNowPayLaterOpeningDriveVwapReclaim -> opening_drive_vwap_reclaim -> factor_v1"
    },
    {
      "label": "SEZL/15m/quality",
      "branch_path": "TrendExpansion -> BuyNowPayLaterOpeningDriveVwapReclaim -> opening_drive_vwap_reclaim -> factor_v1"
    }
  ]
}
""",
                encoding="utf-8",
            )

            result = normalizer.normalize_metrics_file(metrics_path)

        self.assertEqual(
            result["canonical_branch_path"],
            "TrendExpansion -> BuyNowPayLaterOpeningDriveVwapReclaim -> opening_drive_vwap_reclaim -> factor_v1",
        )
        self.assertEqual(result["labels"]["symbol"], "SEZL")
        self.assertEqual(result["labels"]["timeframes"], "1m/5m/15m/30m/1h/4h/1d")
        self.assertEqual(
            result["labels"]["window"],
            "1m=30 D;5m=3 M;15m=3 M;30m=3 M;1h=3 M;4h=6 M;1d=1 Y",
        )
        self.assertNotIn("provider", result["labels"])

    def test_full_identity_path_includes_portability_labels_without_polluting_canonical_branch(self) -> None:
        result = normalizer.normalize_branch_path(
            "TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> factor_v1",
            labels={
                "market": "FUTURES",
                "product": "equity_index_future",
                "symbol": "NQ",
                "timeframe": "1m",
                "provider": "TOMAC_LOCAL",
            },
        )

        self.assertEqual(
            result["canonical_branch_path"],
            "TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> factor_v1",
        )
        self.assertEqual(
            result["full_rooted_identity_path"],
            "FUTURES -> equity_index_future -> NQ -> 1m -> TOMAC_LOCAL -> TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> factor_v1",
        )


if __name__ == "__main__":
    unittest.main()
