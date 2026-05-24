from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import regime_branch_grammar_check as checker  # noqa: E402


class RegimeBranchGrammarCheckTests(unittest.TestCase):
    def test_accepts_recursive_regime_then_profit_factor_suffix(self) -> None:
        result = checker.check_branch_path(
            "TrendExpansion -> BullTrendAcceleration -> RootEvidencePullbackMssCisd -> "
            "strict_trend_root_pullback_mss_cisd -> pda_transition_guard_v1"
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["decision"], "branch_grammar_ok")
        self.assertEqual(result["violations"], [])
        self.assertEqual(
            result["segment_roles"],
            [
                "main_regime",
                "sub_regime",
                "sub_regime",
                "profit_factor",
                "profit_factor",
            ],
        )

    def test_rejects_regime_after_profit_factor(self) -> None:
        result = checker.check_branch_path(
            "TrendExpansion -> RootEvidencePullbackMssCisd -> pullback_reclaim_factor -> "
            "RangeReversion -> vwap_fade_overlay"
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["decision"], "branch_grammar_violation")
        self.assertIn(
            "regime_segment_after_profit_factor:index=3:value=RangeReversion",
            result["violations"],
        )

    def test_rejects_market_product_timeframe_prefix(self) -> None:
        result = checker.check_branch_path(
            "IBKR -> FUTURES -> MNQ -> 1m -> TrendExpansion -> PullbackContinuation -> factor_v1"
        )

        self.assertFalse(result["ok"])
        self.assertIn("branch_path_not_canonical_regime_root", result["violations"])

    def test_cli_checks_metrics_json_branch_path(self) -> None:
        metrics = {
            "branch_path": (
                "TrendExpansion -> BullTrendAcceleration -> pullback_reclaim_factor -> "
                "RangeReversion -> vwap_fade_overlay"
            )
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(report["file"], str(path))

    def test_rejects_mismatched_regime_profit_branch_path_field(self) -> None:
        metrics = {
            "branch_path": (
                "TrendExpansion -> PullbackContinuation -> trend_pullback_reclaim_v1"
            ),
            "regime_profit_branch_path": (
                "FUTURES -> equity_index -> MNQ -> 1m -> TrendExpansion -> "
                "PullbackContinuation -> trend_pullback_reclaim_v1"
            ),
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "terminal_metrics.json"
            path.write_text(json.dumps(metrics), encoding="utf-8")

            report = checker.check_metrics_file(path)

        self.assertFalse(report["ok"])
        self.assertIn(
            "branch_path_field_not_canonical:regime_profit_branch_path",
            report["violations"],
        )


if __name__ == "__main__":
    unittest.main()
