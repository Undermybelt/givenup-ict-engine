from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import recovered_regime_asset_bundle as builder  # noqa: E402


class RecoveredRegimeAssetBundleTests(unittest.TestCase):
    def _write_ledger(self, path: Path) -> None:
        fieldnames = [
            "asset_id",
            "label",
            "asset_class",
            "status",
            "usable_as",
            "rule_or_condition",
            "calibration_wilson95_lcb",
            "test_wilson95_lcb",
            "min_split_wilson95_lcb",
            "calibration_support",
            "test_support",
            "min_split_support",
            "validation_scope",
            "source_run_root",
            "primary_artifact",
            "ingestion_state",
            "next_action",
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(
                {
                    "asset_id": "bull_sourcebacked_drawdown_volatility_v1",
                    "label": "Bull",
                    "asset_class": "source_backed_parent_root",
                    "status": "V2_accepted_95_scope_limited",
                    "usable_as": "board_a_regime_gate",
                    "rule_or_condition": "volatility <= 0.15",
                    "calibration_wilson95_lcb": "0.952516",
                    "test_wilson95_lcb": "0.961931",
                    "min_split_wilson95_lcb": "",
                    "calibration_support": "2202",
                    "test_support": "3125",
                    "min_split_support": "",
                    "validation_scope": "index+single_stock;1d+1w",
                    "source_run_root": "runs/source",
                    "primary_artifact": "runs/source/report.json",
                    "ingestion_state": "recovered_not_candidate_pack",
                    "next_action": "wire into Board A regime-gate artifact surface",
                }
            )
            writer.writerow(
                {
                    "asset_id": "bull_promoted_runtime_regime_asset_v1",
                    "label": "Bull",
                    "asset_class": "source_backed_parent_root",
                    "status": "V2_accepted_95_runtime_promoted",
                    "usable_as": "board_a_regime_gate",
                    "rule_or_condition": "volatility <= 0.12",
                    "calibration_wilson95_lcb": "0.972",
                    "test_wilson95_lcb": "0.968",
                    "min_split_wilson95_lcb": "0.961",
                    "calibration_support": "2500",
                    "test_support": "3300",
                    "min_split_support": "700",
                    "validation_scope": "index+single_stock;1d+1w",
                    "source_run_root": "runs/promoted",
                    "primary_artifact": "runs/promoted/report.json",
                    "ingestion_state": "promoted_runtime",
                    "next_action": "still requires downstream live admission before practical fields can turn true",
                }
            )

    def test_scope_limited_asset_builds_non_trade_usable_bundle(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            ledger = tmp / "assets.csv"
            self._write_ledger(ledger)
            asset = builder.select_asset(
                builder.load_recovered_assets(ledger),
                "bull_sourcebacked_drawdown_volatility_v1",
            )

            decision = builder.build_decision_from_asset(asset, timestamp="2026-05-16T20:12:00+0800")
            bundle = builder.build_bundle(decision, tmp / "regime_high_confidence_decision.json")

            self.assertEqual(decision["decision_state"], "single_label_95_scope_limited")
            self.assertFalse(decision["trade_usable"])
            self.assertEqual(decision["final_label"], "primary::Bull")
            self.assertEqual(decision["path_ranker_context"]["stable_profit_score"], 0.952516)
            self.assertFalse(bundle["latest_decision"]["trade_usable"])
            self.assertFalse(bundle["consumer_contract"]["promotion_allowed"])
            self.assertIn("scope_limited_no_runtime_promotion", bundle["latest_decision"]["abstain_reasons"])

    def test_cli_writes_decision_and_bundle(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            ledger = tmp / "assets.csv"
            output_dir = tmp / "out"
            self._write_ledger(ledger)

            exit_code = builder.main(
                [
                    "--asset-ledger",
                    str(ledger),
                    "--asset-id",
                    "bull_sourcebacked_drawdown_volatility_v1",
                    "--output-dir",
                    str(output_dir),
                ]
            )

            self.assertEqual(exit_code, 0)
            bundle = json.loads((output_dir / "regime_consumer_bundle.json").read_text(encoding="utf-8"))
            self.assertEqual(bundle["schema_version"], "regime-consumer-bundle/v1")
            self.assertEqual(bundle["latest_decision"]["decision_state"], "single_label_95_scope_limited")
            self.assertFalse(bundle["latest_decision"]["trade_usable"])

    def test_allow_trade_usable_flag_does_not_bypass_downstream_live_admission_requirement(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            ledger = tmp / "assets.csv"
            self._write_ledger(ledger)
            asset = builder.select_asset(
                builder.load_recovered_assets(ledger),
                "bull_promoted_runtime_regime_asset_v1",
            )

            decision = builder.build_decision_from_asset(
                asset,
                timestamp="2026-05-27T14:10:00+0800",
                allow_trade_usable=True,
            )
            bundle = builder.build_bundle(decision, tmp / "regime_high_confidence_decision.json")

            self.assertEqual(decision["decision_state"], "single_label_95_scope_limited")
            self.assertFalse(decision["trade_usable"])
            self.assertFalse(bundle["latest_decision"]["trade_usable"])
            self.assertFalse(bundle["consumer_contract"]["promotion_allowed"])
            self.assertIn(
                "recovered_regime_asset_requires_downstream_live_admission",
                bundle["latest_decision"]["abstain_reasons"],
            )


if __name__ == "__main__":
    unittest.main()
