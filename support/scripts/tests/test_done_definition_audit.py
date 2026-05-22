#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path
import json

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from done_definition_audit import (  # noqa: E402
    build_smoke_environment,
    evaluate_main_rs_guardrail,
    format_report,
    parse_main_rs_baseline,
    run_command,
    summarize,
)


class DoneDefinitionAuditTest(unittest.TestCase):
    def test_parse_main_rs_baseline_extracts_numeric_value(self) -> None:
        text = """
Measured on 2026-05-22:
- `src/main.rs`: 19,202 lines
"""
        self.assertEqual(parse_main_rs_baseline(text), 19202)

    def test_parse_main_rs_baseline_raises_when_missing(self) -> None:
        with self.assertRaises(ValueError):
            parse_main_rs_baseline("no baseline here")

    def test_evaluate_main_rs_guardrail_passes_when_not_growing(self) -> None:
        gate = evaluate_main_rs_guardrail(
            "Current debt: `src/main.rs`: 19,202 lines",
            19202,
        )
        self.assertEqual(gate["status"], "pass")
        self.assertEqual(gate["details"]["delta_lines"], 0)

    def test_evaluate_main_rs_guardrail_fails_when_growing(self) -> None:
        gate = evaluate_main_rs_guardrail(
            "Current debt: `src/main.rs`: 19,202 lines",
            19310,
        )
        self.assertEqual(gate["status"], "fail")
        self.assertEqual(gate["details"]["delta_lines"], 108)

    def test_summarize_marks_fail_when_any_gate_fails(self) -> None:
        gates = [
            {"id": "a", "status": "pass"},
            {"id": "b", "status": "skip"},
            {"id": "c", "status": "fail"},
        ]
        summary = summarize(gates)
        self.assertEqual(summary["status"], "needs_fix")
        self.assertEqual(summary["unresolved"], ["c"])
        self.assertEqual(summary["pass_count"], 1)
        self.assertEqual(summary["skip_count"], 1)
        self.assertEqual(summary["fail_count"], 1)

    def test_summarize_marks_pass_without_failures(self) -> None:
        gates = [
            {"id": "a", "status": "pass"},
            {"id": "b", "status": "skip"},
        ]
        summary = summarize(gates)
        self.assertEqual(summary["status"], "pass")
        self.assertEqual(summary["unresolved"], [])
        self.assertFalse(summary["completion_ready"])
        self.assertEqual(summary["evidence_level"], "partial_skipped_gates")
        self.assertEqual(summary["skipped_gates"], ["b"])
        self.assertIn("--run-all-heavy", summary["next_action"])

    def test_summarize_marks_completion_ready_when_no_failures_or_skips(self) -> None:
        summary = summarize([{"id": "a", "status": "pass"}])
        self.assertEqual(summary["status"], "pass")
        self.assertTrue(summary["completion_ready"])
        self.assertEqual(summary["evidence_level"], "full_enabled_gate_coverage")
        self.assertEqual(summary["skipped_gates"], [])

    def test_run_command_timeout_details_are_json_serializable(self) -> None:
        status, details = run_command(
            [
                sys.executable,
                "-c",
                "import sys, time; sys.stdout.buffer.write(b'out'); sys.stdout.flush(); "
                "sys.stderr.buffer.write(b'err'); sys.stderr.flush(); time.sleep(2)",
            ],
            cwd=SCRIPTS_ROOT,
            timeout=1,
        )
        self.assertEqual(status, "fail")
        self.assertEqual(details["error"], "timeout")
        self.assertIsInstance(details["stdout"], str)
        self.assertIsInstance(details["stderr"], str)
        json.dumps(details)

    def test_run_command_timeout_kills_child_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "child-survived.txt"
            child = (
                "import pathlib, time; "
                "time.sleep(2); "
                f"pathlib.Path({str(marker)!r}).write_text('survived')"
            )
            parent = (
                "import subprocess, sys, time; "
                f"subprocess.Popen([sys.executable, '-c', {child!r}]); "
                "time.sleep(5)"
            )
            status, details = run_command(
                [sys.executable, "-c", parent],
                cwd=SCRIPTS_ROOT,
                timeout=1,
            )
            time.sleep(2.5)
            child_survived = marker.exists()

        self.assertEqual(status, "fail")
        self.assertEqual(details["error"], "timeout")
        self.assertFalse(child_survived)

    def test_build_smoke_environment_uses_fresh_default_state(self) -> None:
        class Args:
            smoke_state_dir = ""

        base_env = {"OUT_DIR": "/tmp/operator-smoke-out"}
        first = build_smoke_environment(Args(), base_env=base_env)
        second = build_smoke_environment(Args(), base_env=base_env)

        self.assertRegex(
            first["STATE_DIR"],
            r"^/tmp/ict-engine-done-definition-audit-smoke-[0-9]{8}T[0-9]{6}[0-9]{6}Z-[0-9]+$",
        )
        self.assertRegex(
            second["STATE_DIR"],
            r"^/tmp/ict-engine-done-definition-audit-smoke-[0-9]{8}T[0-9]{6}[0-9]{6}Z-[0-9]+$",
        )
        self.assertNotEqual(first["STATE_DIR"], second["STATE_DIR"])
        self.assertEqual(first["OUT_DIR"], "/tmp/operator-smoke-out")

    def test_build_smoke_environment_preserves_explicit_state_and_default_out_dir(self) -> None:
        class Args:
            smoke_state_dir = "/tmp/explicit-smoke-state"

        env = build_smoke_environment(Args(), base_env={})

        self.assertEqual(env["STATE_DIR"], "/tmp/explicit-smoke-state")
        self.assertEqual(env["OUT_DIR"], "/tmp/explicit-smoke-state-out")

    def test_format_report_compact_omits_repo_root_and_pass_details(self) -> None:
        report = {
            "timestamp_utc": "2026-05-22T00:00:00Z",
            "repo_root": "/Users/example/ict-engine",
            "summary": {"status": "pass", "pass_count": 1, "fail_count": 0, "skip_count": 1},
            "gates": [
                {
                    "id": "main_rs_line_guardrail",
                    "status": "pass",
                    "heavy": False,
                    "details": {"current_lines": 100},
                },
                {
                    "id": "cargo_test",
                    "status": "skip",
                    "heavy": True,
                    "details": {"reason": "heavy_check_not_enabled", "enable_with": "--run-cargo-test"},
                },
            ],
        }

        text = format_report(report, compact=True)
        parsed = json.loads(text)

        self.assertNotIn("repo_root", parsed)
        self.assertEqual(parsed["summary"], report["summary"])
        self.assertEqual(parsed["gate_count"], 2)
        self.assertEqual(parsed["gates"][0], {"id": "main_rs_line_guardrail", "status": "pass", "heavy": False})
        self.assertEqual(parsed["gates"][1]["details"]["enable_with"], "--run-cargo-test")
        self.assertNotIn("/Users/example", text)
        self.assertNotIn("\n  ", text)

    def test_format_report_compact_relativizes_repo_paths_in_details(self) -> None:
        report = {
            "timestamp_utc": "2026-05-22T00:00:00Z",
            "repo_root": "/Users/example/ict-engine",
            "summary": {"status": "needs_fix"},
            "gates": [
                {
                    "id": "smoke_acceptance_tmp_state",
                    "status": "fail",
                    "heavy": True,
                    "details": {
                        "command": ["bash", "/Users/example/ict-engine/support/scripts/smoke_acceptance.sh"],
                        "stderr": "failed at /Users/example/ict-engine/state",
                    },
                }
            ],
        }

        text = format_report(report, compact=True)
        parsed = json.loads(text)

        self.assertEqual(parsed["gates"][0]["details"]["command"][1], "support/scripts/smoke_acceptance.sh")
        self.assertEqual(parsed["gates"][0]["details"]["stderr"], "failed at state")
        self.assertNotIn("/Users/example", text)


if __name__ == "__main__":
    unittest.main()
