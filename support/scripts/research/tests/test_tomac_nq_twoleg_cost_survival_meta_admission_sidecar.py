from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import tomac_nq_twoleg_cost_survival_meta_admission_sidecar as sidecar  # noqa: E402


class TomacNqTwolegCostSurvivalMetaAdmissionSidecarTests(unittest.TestCase):
    def test_run_sidecar_writes_fail_closed_artifacts(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            output_dir = tmp / "out"
            candles = [
                {"timestamp": "2024-01-01T00:00:00+00:00", "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0},
                {"timestamp": "2024-01-01T00:01:00+00:00", "open": 100.0, "high": 102.0, "low": 99.5, "close": 101.5, "volume": 1.0},
                {"timestamp": "2024-01-01T00:02:00+00:00", "open": 101.5, "high": 103.0, "low": 101.0, "close": 102.5, "volume": 1.0},
            ]
            trades = [
                {
                    "trade_id": "od-twoleg-00001",
                    "pair": "NQ/USD",
                    "direction": "Bull",
                    "open_ts_ms": 1704067200000,
                    "close_ts_ms": 1704067320000,
                    "open_rate": 100.0,
                    "close_rate": 102.5,
                    "profit_ratio": 0.025,
                    "pnl": 2.5,
                    "min_rate": 99.5,
                    "max_rate": 103.0,
                    "realized_outcome": "win",
                    "regime_profit_branch_path": (
                        "TrendExpansion -> OpeningDrive -> "
                        "BidirectionalIntradayTrendContinuation -> CostSurvivalMetaAdmission"
                    ),
                    "main_regime": "TrendExpansion",
                    "sub_regime": "OpeningDrive",
                    "sub_sub_regime_or_profit_factor": "BidirectionalIntradayTrendContinuation",
                    "profit_factor": "tomac_nq_bidir_opening_drive_twoleg_cost_survival_meta_admission_t15_x1080_v1",
                    "structural_feedback": {"exit_reason": "exit_signal"},
                    "factors_used": [{"category": "regime_profit_branch_path", "confidence": 1.0}],
                }
            ]

            result = sidecar.run_sidecar(
                output_dir=output_dir,
                factor_id="tomac_nq_bidir_opening_drive_twoleg_cost_survival_meta_admission_t15_x1080_v1",
                branch_path=(
                    "TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> "
                    "CostSurvivalMetaAdmission -> "
                    "tomac_nq_bidir_opening_drive_twoleg_cost_survival_meta_admission_t15_x1080_v1"
                ),
                symbol="NQ",
                sl_mult=0.01,
                candles_by_pair={"NQ/USD": candles},
                trades=trades,
            )

            self.assertTrue((output_dir / "summary.json").is_file())
            self.assertTrue((output_dir / "trades.jsonl").is_file())
            self.assertTrue((output_dir / "labels" / "portfolio_labels.jsonl").is_file())
            self.assertTrue((output_dir / "payoff" / "portfolio_payoff_report.json").is_file())
            self.assertTrue((output_dir / "path_ranker" / "path_ranker_handoff_summary.json").is_file())
            self.assertEqual(result["trade_count"], 1)
            self.assertFalse(result["trade_usable"])
            self.assertFalse(result["promotion_allowed"])
            self.assertEqual(result["instrument_cost_models"]["NQ/USD"]["cost_model_status"], "verified_ibkr_broker_side")
            summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["factor_id"], "tomac_nq_bidir_opening_drive_twoleg_cost_survival_meta_admission_t15_x1080_v1")
            self.assertEqual(summary["branch_path"].split(" -> ")[0], "TrendExpansion")


if __name__ == "__main__":
    unittest.main()
