from __future__ import annotations

import json
import importlib
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import mim_cost_window_material_builder as builder  # noqa: E402


class MimCostWindowMaterialBuilderTests(unittest.TestCase):
    def test_package_import_works_without_script_path_hack(self) -> None:
        module = importlib.import_module("support.scripts.research.mim_cost_window_material_builder")

        self.assertTrue(hasattr(module, "build_material_bundle"))

    def _write_csv(self, path: Path) -> None:
        start = datetime(2026, 5, 21, 13, 30, tzinfo=timezone.utc)
        rows = ["ts,open,high,low,close,volume"]
        price = 100.0
        for day in range(2):
            for idx in range(90):
                drift = 0.035 if day == 0 and idx < 30 else 0.010 if day == 0 else 0.0
                open_ = price
                close = price + drift
                high = max(open_, close) + 0.025
                low = min(open_, close) - 0.020
                ts = (start + timedelta(days=day, minutes=idx)).isoformat().replace("+00:00", "Z")
                rows.append(f"{ts},{open_:.6f},{high:.6f},{low:.6f},{close:.6f},{1200 + idx:.2f}")
                price = close
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    def test_build_material_bundle_preserves_branch_identity_without_promotion(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            csv_path = tmp / "retained.csv"
            out_dir = tmp / "bundle"
            self._write_csv(csv_path)

            result = builder.build_material_bundle(
                csv_path,
                out_dir,
                symbol="TEST",
                provider="retained-real",
                market="US_EQ",
                product="single_stock",
                branch_path=(
                    "TrendExpansion -> IntradayMomentumCostWindow -> "
                    "mim_cost_window_regime_filter -> test_mim_cost_window_v1"
                ),
                factor_id="test_mim_cost_window_v1",
            )

            self.assertEqual(result["event_count"], 2)
            material = json.loads(Path(result["material_path"]).read_text(encoding="utf-8"))
            profile = material["consumer_evidence_profile"]
            self.assertEqual(profile["branch_path"], "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_mim_cost_window_v1")
            self.assertEqual(profile["main_regime"], "TrendExpansion")
            self.assertEqual(profile["base_timeframe"], "1m")
            self.assertEqual(profile["context_timeframes"], ["5m", "15m", "30m", "1h", "4h", "1d"])
            self.assertEqual(profile["provider"], "retained-real")
            self.assertFalse(profile["promotion_allowed"])
            self.assertFalse(profile["trade_usable"])
            self.assertFalse(profile["downstream_allowed"])
            self.assertTrue(Path(result["strategy_source_path"]).exists())
            self.assertTrue(Path(result["events_jsonl"]).exists())

    def test_cli_writes_bundle_summary(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            csv_path = tmp / "retained.csv"
            out_dir = tmp / "bundle"
            self._write_csv(csv_path)

            exit_code = builder.main(
                [
                    "--input-csv",
                    str(csv_path),
                    "--output-dir",
                    str(out_dir),
                    "--symbol",
                    "TEST",
                    "--provider",
                    "retained-real",
                    "--market",
                    "US_EQ",
                    "--product",
                    "single_stock",
                    "--branch-path",
                    "TrendExpansion -> IntradayMomentumCostWindow -> mim_cost_window_regime_filter -> test_mim_cost_window_v1",
                    "--factor-id",
                    "test_mim_cost_window_v1",
                ]
            )

            self.assertEqual(exit_code, 0)
            summary = json.loads((out_dir / "mim_cost_window_material_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["symbol"], "TEST")
            self.assertEqual(summary["event_count"], 2)
            self.assertFalse(summary["promotion_allowed"])


if __name__ == "__main__":
    unittest.main()
