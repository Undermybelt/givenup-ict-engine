from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import factor_signal_diagnostics as diag  # noqa: E402


class FactorSignalDiagnosticsTests(unittest.TestCase):
    def test_demo_report_is_zero_config_and_not_trade_usable(self) -> None:
        rows = diag._read_rows(None, demo=True)

        report = diag.build_diagnostics(rows, cost_bps_side=1.0)

        self.assertEqual(report["schema_version"], "ict-engine-factor-signal-diagnostics/v1")
        self.assertEqual(report["rows"], 40)
        self.assertTrue(report["promotion_allowed"])
        self.assertFalse(report["trade_usable"])
        self.assertIn("downstream", report["trade_usable_reason"])

    def test_hotplug_profile_requires_root_delta(self) -> None:
        rows = []
        for idx in range(40):
            rows.append(
                diag.DiagnosticRow(
                    timestamp=str(idx),
                    asset="NQ",
                    horizon="1",
                    regime="Transition",
                    signal=1.0 if idx % 2 == 0 else -1.0,
                    forward_return=0.001 if idx % 2 == 0 else -0.001,
                )
            )
            rows.append(
                diag.DiagnosticRow(
                    timestamp=str(idx),
                    asset="NQ",
                    horizon="1",
                    regime="Range",
                    signal=1.0 if idx % 2 == 0 else -1.0,
                    forward_return=0.0002 if idx % 2 == 0 else -0.0002,
                )
            )
        profile = {
            "root_regime": "Transition",
            "regime_profit_branch_path": "FUTURES -> index -> NQ -> 1m -> Transition -> demo_factor",
            "thresholds": {"min_n": 30, "min_root_delta_bps": 3.0},
        }

        report = diag.build_diagnostics(rows, cost_bps_side=1.0, profile=profile)

        best = report["best_bucket"]
        self.assertEqual(best["regime"], "Transition")
        self.assertGreater(best["root_delta_bps"], 3.0)
        self.assertTrue(report["hotplug_profile_used"])
        self.assertTrue(report["promotion_allowed"])

    def test_cli_writes_optional_json_without_state_pollution(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "report.json"
            rc = diag.main(["--demo", "--output", str(output), "--compact"])

            self.assertEqual(rc, 0)
            payload = json.loads(output.read_text())
            self.assertEqual(payload["rows"], 40)
            self.assertFalse((Path(tmpdir) / "state").exists())


if __name__ == "__main__":
    unittest.main()