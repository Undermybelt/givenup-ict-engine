#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path
import json

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from done_definition_audit import (  # noqa: E402
    evaluate_main_rs_guardrail,
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


if __name__ == "__main__":
    unittest.main()
