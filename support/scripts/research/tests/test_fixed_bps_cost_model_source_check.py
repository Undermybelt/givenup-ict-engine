from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import fixed_bps_cost_model_source_check as checker  # noqa: E402


class FixedBpsCostModelSourceCheckTests(unittest.TestCase):
    def write_source(self, source: str, name: str = "run_gate1.py") -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        path = Path(tmpdir.name) / name
        path.write_text(source, encoding="utf-8")
        return path

    def test_flags_cost_bps_argument_default(self) -> None:
        path = self.write_source(
            """
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--cost-bps", type=float, default=5.0)
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertEqual(report["decision"], "fixed_bps_cost_model_source_violation")
        self.assertEqual(report["violations"][0]["violation"], "fixed_bps_cost_argument")

    def test_flags_fixed_bps_ladder_formula(self) -> None:
        path = self.write_source(
            """
def summarize(gross, trades):
    rows = []
    for bps in (0, 1, 2, 5):
        rows.append(gross - trades * bps * 0.02)
    return {
        "net5bps_total_ret_pct": rows[-1],
        "survives_2bps_per_side": rows[2] > 0,
        "5bps_per_side_total_profit_pct": rows[-1],
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        kinds = {hit["violation"] for hit in report["violations"]}
        self.assertIn("fixed_bps_cost_ladder", kinds)
        self.assertIn("fixed_bps_cost_formula", kinds)

    def test_flags_explicit_stress_telemetry_fields(self) -> None:
        path = self.write_source(
            """
def build(summary):
    for bps in (0, 1, 2, 5):
        summary[f"{bps}bps_per_side_total_profit_pct"] = "telemetry_only"
    summary["cost_stress_5bps_role"] = "telemetry_not_futures_hard_gate"
    summary["top_by_5bps"] = []
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        kinds = {hit["violation"] for hit in report["violations"]}
        self.assertIn("fixed_bps_cost_ladder", kinds)
        self.assertIn("fixed_bps_cost_field", kinds)

    def test_allows_readback_only_legacy_cost_fields(self) -> None:
        path = self.write_source(
            """
LEGACY_COST_KEYS = (
    "net_after_5bps_side_pct",
    "5bps_per_side_total_profit_pct",
    "survives_5bps_per_side",
)

def read(row):
    return {key: row.get(key) for key in LEGACY_COST_KEYS}
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"], report["violations"])

    def test_flags_stress_bps_cli_argument(self) -> None:
        path = self.write_source(
            """
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--stress-bps-per-side", type=float, default=5.0)
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        kinds = {hit["violation"] for hit in report["violations"]}
        self.assertIn("fixed_bps_cost_argument", kinds)
        self.assertIn("fixed_bps_cost_argument_default", kinds)

    def test_flags_disguised_diagnostic_stress_bps_names(self) -> None:
        path = self.write_source(
            """
def build(gross, diagnostic_stress_bps=5.0):
    stress_return = diagnostic_stress_bps / 10_000.0
    return gross - stress_return
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        kinds = {hit["violation"] for hit in report["violations"]}
        self.assertIn("fixed_bps_cost_argument", kinds)
        self.assertIn("fixed_bps_cost_formula", kinds)

    def test_flags_string_literal_cost_fields(self) -> None:
        path = self.write_source(
            """
def build(row):
    return {
        "net5bps_return": row.get("net5bps_return"),
        "survives_5bps_per_side": True,
    }
"""
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertIn("fixed_bps_cost_field", {hit["violation"] for hit in report["violations"]})

    def test_checker_does_not_flag_itself(self) -> None:
        report = checker.check_source_file(SCRIPT_ROOT / "fixed_bps_cost_model_source_check.py")

        self.assertTrue(report["ok"], report["violations"])

    def test_allows_signal_threshold_bps_names(self) -> None:
        path = self.write_source(
            """
def signal(row, min_abs_1h_slope_bps=3.0, reclaim_bps_min=8.0):
    slope_bps = row["close_slope_bps"]
    return abs(slope_bps) >= min_abs_1h_slope_bps and row["reclaim_bps"] >= reclaim_bps_min
"""
        )

        report = checker.check_source_file(path)

        self.assertTrue(report["ok"], report["violations"])

    def test_cli_reports_tracked_scope_without_runs_or_paper2code(self) -> None:
        good = self.write_source("slope_bps = 2.0\n", name="signal.py")
        bad = self.write_source("cost_bps = 5\n", name="run_bad.py")

        report = checker.check_paths([good, bad])

        self.assertFalse(report["ok"])
        self.assertEqual(report["checked_files"], 2)
        self.assertEqual(report["violating_files"], 1)

    def test_checker_source_is_skipped_so_it_can_list_forbidden_tokens(self) -> None:
        path = self.write_source("cost_bps = 5\n", name="fixed_bps_cost_model_source_check.py")

        report = checker.check_paths(checker.discover_paths([path]))

        self.assertTrue(report["ok"])
        self.assertEqual(report["checked_files"], 0)

    def test_legacy_revival_tool_is_not_whitelisted(self) -> None:
        path = self.write_source("stress_bps_per_side = 5\n", name="futures_bps_false_negative_revival.py")

        report = checker.check_paths(checker.discover_paths([path]))

        self.assertFalse(report["ok"])
        self.assertEqual(report["checked_files"], 1)
        self.assertEqual(report["violating_files"], 1)

    def test_read_only_legacy_stress_docstring_does_not_bypass_source_check(self) -> None:
        path = self.write_source(
            '''
"""Read-only legacy 5bps/side stress rehearing.

This helper does not promote anything; it rechecks legacy rows against the
verified per-contract instrument-cost model.
"""

def classify(row, stress_bps_per_side=5.0):
    stress_5bps_total_pct = row.get("5bps_per_side_total_profit_pct")
    return stress_5bps_total_pct, stress_bps_per_side
''',
            name="legacy_rehear.py",
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        kinds = {hit["violation"] for hit in report["violations"]}
        self.assertIn("fixed_bps_cost_argument", kinds)
        self.assertIn("fixed_bps_cost_argument_default", kinds)

    def test_role_marker_does_not_bypass_fixed_bps_source_check(self) -> None:
        path = self.write_source(
            '''
def build(row, stress_bps_per_side=5.0):
    return {
        "stress_5bps_total_profit_pct": row.get("5bps_per_side_total_profit_pct"),
        "cost_stress_role": "telemetry_not_futures_hard_gate",
        "stress_bps_per_side": stress_bps_per_side,
    }
''',
            name="stress_telemetry.py",
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        kinds = {hit["violation"] for hit in report["violations"]}
        self.assertIn("fixed_bps_cost_argument", kinds)
        self.assertIn("fixed_bps_cost_argument_default", kinds)

    def test_flags_values_assignment_of_legacy_fixed_bps_cost_fields(self) -> None:
        path = self.write_source(
            '''
def parse(row):
    values = {}
    values["5bps_per_side_total_profit_pct"] = row.get("5bps_per_side_total_profit_pct")
    values["configured_fee_5bps_total_profit_pct"] = row.get("configured_fee_5bps_total_profit_pct")
    return values
''',
            name="legacy_values_emit.py",
        )

        report = checker.check_source_file(path)

        self.assertFalse(report["ok"])
        self.assertIn("fixed_bps_cost_field", {hit["violation"] for hit in report["violations"]})


if __name__ == "__main__":
    unittest.main()
