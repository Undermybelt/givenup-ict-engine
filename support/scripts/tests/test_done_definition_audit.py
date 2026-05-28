#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path
import json
import hashlib

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from done_definition_audit import (  # noqa: E402
    build_smoke_environment,
    evaluate_practical_admission_source_gate,
    evaluate_quickstart_surface,
    evaluate_main_rs_guardrail,
    format_report,
    parse_main_rs_baseline,
    run_command,
    evaluate_help_audit_policy,
    summarize,
    write_practical_admission_debt_manifest,
)


class DoneDefinitionAuditTest(unittest.TestCase):
    def test_evaluate_quickstart_surface_fails_when_command_order_drifts(self) -> None:
        import done_definition_audit

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "AGENT.md"
            readme = root / "README.md"
            consumer = root / "support" / "docs" / "consumer-quickstart.md"
            contributor = root / "support" / "docs" / "contributor-quickstart.md"
            consumer.parent.mkdir(parents=True, exist_ok=True)
            contributor.parent.mkdir(parents=True, exist_ok=True)

            agent.write_text(
                "```bash\n"
                "cargo run --quiet -- provider-status --compact\n"
                "cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-first-run --human\n"
                "cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --agent\n"
                "```\n",
                encoding="utf-8",
            )
            readme.write_text(
                "support/docs/consumer-quickstart.md\n"
                "support/docs/contributor-quickstart.md\n"
                "```bash\n"
                "cargo run -- provider-status --compact\n"
                "cargo run -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-first-run --human\n"
                "cargo run -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --agent\n"
                "```\n",
                encoding="utf-8",
            )
            consumer.write_text(
                "```bash\n"
                "cargo run --quiet -- provider-status --compact\n"
                "cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --human\n"
                "cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-first-run --human\n"
                "cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --agent\n"
                "cargo run --quiet -- pre-bayes-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --output-format json\n"
                "cargo run --quiet -- policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --output-format agent\n"
                "```\n",
                encoding="utf-8",
            )
            contributor.write_text("# ok\n", encoding="utf-8")

            originals = (
                done_definition_audit.ROOT,
                done_definition_audit.AGENT_ENTRY_PATH,
                done_definition_audit.README_PATH,
                done_definition_audit.CONSUMER_QUICKSTART_PATH,
                done_definition_audit.CONTRIBUTOR_QUICKSTART_PATH,
            )
            try:
                done_definition_audit.ROOT = root
                done_definition_audit.AGENT_ENTRY_PATH = agent
                done_definition_audit.README_PATH = readme
                done_definition_audit.CONSUMER_QUICKSTART_PATH = consumer
                done_definition_audit.CONTRIBUTOR_QUICKSTART_PATH = contributor
                gate = evaluate_quickstart_surface()
            finally:
                (
                    done_definition_audit.ROOT,
                    done_definition_audit.AGENT_ENTRY_PATH,
                    done_definition_audit.README_PATH,
                    done_definition_audit.CONSUMER_QUICKSTART_PATH,
                    done_definition_audit.CONTRIBUTOR_QUICKSTART_PATH,
                ) = originals

        self.assertEqual(gate["status"], "fail")
        self.assertIn("support/docs/consumer-quickstart.md", gate["details"]["command_order_drift"])

    def test_evaluate_quickstart_surface_passes_when_canonical_blocks_exist(self) -> None:
        import done_definition_audit

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = root / "AGENT.md"
            readme = root / "README.md"
            consumer = root / "support" / "docs" / "consumer-quickstart.md"
            contributor = root / "support" / "docs" / "contributor-quickstart.md"
            consumer.parent.mkdir(parents=True, exist_ok=True)
            contributor.parent.mkdir(parents=True, exist_ok=True)

            agent.write_text(
                "```bash\n"
                "cargo run --quiet -- provider-status --compact\n"
                "cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-first-run --human\n"
                "cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --agent\n"
                "```\n",
                encoding="utf-8",
            )
            readme.write_text(
                "support/docs/consumer-quickstart.md\n"
                "support/docs/contributor-quickstart.md\n"
                "```bash\n"
                "cargo run -- provider-status --compact\n"
                "cargo run -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-first-run --human\n"
                "cargo run -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --agent\n"
                "```\n",
                encoding="utf-8",
            )
            consumer.write_text(
                "```bash\n"
                "cargo run --quiet -- provider-status --compact\n"
                "cargo run --quiet -- analyze --symbol DEMO --demo --state-dir /tmp/ict-engine-first-run --human\n"
                "cargo run --quiet -- workflow-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --agent\n"
                "cargo run --quiet -- pre-bayes-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --refresh --output-format json\n"
                "cargo run --quiet -- policy-training-status --symbol DEMO --state-dir /tmp/ict-engine-first-run --output-format agent\n"
                "```\n",
                encoding="utf-8",
            )
            contributor.write_text("# ok\n", encoding="utf-8")

            originals = (
                done_definition_audit.ROOT,
                done_definition_audit.AGENT_ENTRY_PATH,
                done_definition_audit.README_PATH,
                done_definition_audit.CONSUMER_QUICKSTART_PATH,
                done_definition_audit.CONTRIBUTOR_QUICKSTART_PATH,
            )
            try:
                done_definition_audit.ROOT = root
                done_definition_audit.AGENT_ENTRY_PATH = agent
                done_definition_audit.README_PATH = readme
                done_definition_audit.CONSUMER_QUICKSTART_PATH = consumer
                done_definition_audit.CONTRIBUTOR_QUICKSTART_PATH = contributor
                gate = evaluate_quickstart_surface()
            finally:
                (
                    done_definition_audit.ROOT,
                    done_definition_audit.AGENT_ENTRY_PATH,
                    done_definition_audit.README_PATH,
                    done_definition_audit.CONSUMER_QUICKSTART_PATH,
                    done_definition_audit.CONTRIBUTOR_QUICKSTART_PATH,
                ) = originals

        self.assertEqual(gate["status"], "pass")
        self.assertEqual(gate["details"]["command_order_drift"], [])

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

    def test_compact_report_keeps_passed_practical_admission_untracked_debt(self) -> None:
        report = {
            "timestamp_utc": "2026-05-28T11:10:00Z",
            "repo_root": str(SCRIPTS_ROOT.parents[1]),
            "summary": {"status": "pass"},
            "gates": [
                {
                    "id": "practical_admission_source_surface",
                    "status": "pass",
                    "heavy": False,
                    "details": {
                        "tracked_violation_count": 0,
                        "tracked_violating_files": 0,
                        "untracked_violation_count": 2,
                        "untracked_violating_files": 1,
                        "violation_count": 2,
                        "violating_files": 1,
                        "debt_manifest_file": "/tmp/practical-admission-source-debt.json",
                        "sample_violations": [
                            {
                                "file": "support/docs/experiments/actionable-regime-confidence/scripts/run_untracked_bad_v1.py",
                                "violation": "practical_flag_without_extension_complete_guard",
                            }
                        ],
                    },
                }
            ],
        }

        compact = json.loads(format_report(report, compact=True))
        gate = compact["gates"][0]

        self.assertEqual(gate["status"], "pass")
        self.assertEqual(gate["details"]["untracked_violation_count"], 2)
        self.assertEqual(gate["details"]["tracked_violation_count"], 0)
        self.assertEqual(gate["details"]["debt_manifest_file"], "/tmp/practical-admission-source-debt.json")

    def test_practical_admission_source_gate_writes_debt_manifest(self) -> None:
        import done_definition_audit

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scanner = root / "support" / "scripts" / "research" / "downstream_practical_admission_source_check.py"
            wrapper_root = root / "support" / "docs" / "experiments" / "actionable-regime-confidence" / "scripts"
            scanner.parent.mkdir(parents=True)
            wrapper_root.mkdir(parents=True)
            scanner.write_text("# scanner placeholder\n", encoding="utf-8")
            tracked = wrapper_root / "run_tracked_good_v1.py"
            untracked = wrapper_root / "run_untracked_bad_v1.py"
            tracked.write_text("# tracked good\n", encoding="utf-8")
            untracked.write_text("# untracked bad\n", encoding="utf-8")

            def fake_run_command(cmd, *, cwd, timeout, env=None):
                del cmd, cwd, timeout, env
                return (
                    "fail",
                    {
                        "returncode": 1,
                        "stdout": json.dumps(
                            [
                                {"file": str(tracked), "ok": True, "violations": []},
                                {
                                    "file": str(untracked),
                                    "ok": False,
                                    "violations": [
                                        {
                                            "line": 9,
                                            "column": 20,
                                            "key": "trade_usable",
                                            "value": "admitted",
                                            "violation": "practical_flag_without_extension_complete_guard",
                                        }
                                    ],
                                },
                            ]
                        ),
                        "stderr": "",
                    },
                )

            originals = (
                done_definition_audit.ROOT,
                done_definition_audit.PRACTICAL_ADMISSION_SOURCE_CHECK_PATH,
                done_definition_audit.PRACTICAL_ADMISSION_WRAPPER_ROOT,
                done_definition_audit.run_command,
                done_definition_audit.tracked_wrapper_file_set,
            )
            try:
                done_definition_audit.ROOT = root
                done_definition_audit.PRACTICAL_ADMISSION_SOURCE_CHECK_PATH = scanner
                done_definition_audit.PRACTICAL_ADMISSION_WRAPPER_ROOT = wrapper_root
                done_definition_audit.run_command = fake_run_command
                done_definition_audit.tracked_wrapper_file_set = lambda wrapper_files, timeout_seconds: {tracked}
                gate = evaluate_practical_admission_source_gate(30)
            finally:
                (
                    done_definition_audit.ROOT,
                    done_definition_audit.PRACTICAL_ADMISSION_SOURCE_CHECK_PATH,
                    done_definition_audit.PRACTICAL_ADMISSION_WRAPPER_ROOT,
                    done_definition_audit.run_command,
                    done_definition_audit.tracked_wrapper_file_set,
                ) = originals

        manifest_path = Path(gate["details"]["debt_manifest_file"])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], "practical-admission-source-debt/v1")
        self.assertEqual(manifest["untracked_violation_count"], 1)
        self.assertEqual(manifest["tracked_violation_count"], 0)
        self.assertEqual(manifest["violation_count"], 1)
        self.assertEqual(manifest["timestamp_utc"], manifest["generated_at"])
        self.assertEqual(manifest["summary"]["untracked_violation_count"], 1)
        self.assertEqual(manifest["untracked_violations"][0]["key"], "trade_usable")

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

    def test_evaluate_help_audit_policy_passes_timeout_to_child_build(self) -> None:
        import done_definition_audit

        captured = {}

        def fake_run_command(cmd, *, cwd, timeout, env=None):
            del cmd, cwd
            captured["timeout"] = timeout
            captured["env_timeout"] = env.get("ICT_ENGINE_HELP_AUDIT_BUILD_TIMEOUT_SECONDS")
            return (
                "pass",
                {
                    "command": ["python", "support/scripts/help_audit.py"],
                    "stdout": json.dumps(
                        {
                            "summary": {
                                "command_count": 1,
                                "commands_with_no_output_modes": 0,
                                "none_output_mode_policy_matches_expected": True,
                                "status": "pass",
                            },
                            "none_output_mode_policy": {
                                "unclassified_none_commands": [],
                                "missing_expected_commands": [],
                            },
                        }
                    ),
                    "stderr": "",
                },
            )

        old_run_command = done_definition_audit.run_command
        try:
            done_definition_audit.run_command = fake_run_command
            gate = evaluate_help_audit_policy(600)
        finally:
            done_definition_audit.run_command = old_run_command

        self.assertEqual(gate["status"], "pass")
        self.assertEqual(captured["timeout"], 600)
        self.assertEqual(captured["env_timeout"], "600")

    def test_practical_admission_source_gate_fails_on_unsafe_wrapper_scan(self) -> None:
        import done_definition_audit

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scanner = root / "support" / "scripts" / "research" / "downstream_practical_admission_source_check.py"
            wrapper_root = root / "support" / "docs" / "experiments" / "actionable-regime-confidence" / "scripts"
            scanner.parent.mkdir(parents=True)
            wrapper_root.mkdir(parents=True)
            scanner.write_text("# scanner placeholder\n", encoding="utf-8")
            (wrapper_root / "run_bad_v1.py").write_text("# bad\n", encoding="utf-8")

            def fake_run_command(cmd, *, cwd, timeout, env=None):
                del cwd, timeout, env
                if cmd[:3] == ["git", "ls-files", "--"]:
                    return (
                        "pass",
                        {
                            "returncode": 0,
                            "stdout": "support/docs/experiments/actionable-regime-confidence/scripts/run_bad_v1.py\n",
                            "stderr": "",
                        },
                    )
                self.assertIn(str(scanner), cmd)
                self.assertIn(str(wrapper_root / "run_bad_v1.py"), cmd)
                return (
                    "fail",
                    {
                        "returncode": 1,
                        "stdout": json.dumps(
                            [
                                {
                                    "file": str(wrapper_root / "run_bad_v1.py"),
                                    "ok": False,
                                    "violations": [
                                        {
                                            "line": 7,
                                            "column": 20,
                                            "key": "promotion_allowed",
                                            "value": "admitted",
                                            "violation": "practical_flag_without_extension_complete_guard",
                                        }
                                    ],
                                }
                            ]
                        ),
                        "stderr": "",
                    },
                )

            originals = (
                done_definition_audit.ROOT,
                done_definition_audit.PRACTICAL_ADMISSION_SOURCE_CHECK_PATH,
                done_definition_audit.PRACTICAL_ADMISSION_WRAPPER_ROOT,
                done_definition_audit.run_command,
            )
            try:
                done_definition_audit.ROOT = root
                done_definition_audit.PRACTICAL_ADMISSION_SOURCE_CHECK_PATH = scanner
                done_definition_audit.PRACTICAL_ADMISSION_WRAPPER_ROOT = wrapper_root
                done_definition_audit.run_command = fake_run_command
                gate = evaluate_practical_admission_source_gate(30)
            finally:
                (
                    done_definition_audit.ROOT,
                    done_definition_audit.PRACTICAL_ADMISSION_SOURCE_CHECK_PATH,
                    done_definition_audit.PRACTICAL_ADMISSION_WRAPPER_ROOT,
                    done_definition_audit.run_command,
                ) = originals

        self.assertEqual(gate["id"], "practical_admission_source_surface")
        self.assertEqual(gate["status"], "fail")
        self.assertEqual(gate["details"]["scanned_files"], 1)
        self.assertEqual(gate["details"]["violating_files"], 1)
        self.assertEqual(gate["details"]["violation_count"], 1)
        self.assertEqual(
            gate["details"]["violations_by_type"],
            {"practical_flag_without_extension_complete_guard": 1},
        )
        self.assertEqual(gate["details"]["sample_violations"][0]["key"], "promotion_allowed")

    def test_practical_admission_source_gate_passes_when_wrapper_scan_is_clean(self) -> None:
        import done_definition_audit

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scanner = root / "support" / "scripts" / "research" / "downstream_practical_admission_source_check.py"
            wrapper_root = root / "support" / "docs" / "experiments" / "actionable-regime-confidence" / "scripts"
            scanner.parent.mkdir(parents=True)
            wrapper_root.mkdir(parents=True)
            scanner.write_text("# scanner placeholder\n", encoding="utf-8")
            (wrapper_root / "run_good_v1.py").write_text("# good\n", encoding="utf-8")

            def fake_run_command(cmd, *, cwd, timeout, env=None):
                del cmd, cwd, timeout, env
                return (
                    "pass",
                    {
                        "returncode": 0,
                        "stdout": json.dumps(
                            [
                                {
                                    "file": str(wrapper_root / "run_good_v1.py"),
                                    "ok": True,
                                    "violations": [],
                                }
                            ]
                        ),
                        "stderr": "",
                    },
                )

            originals = (
                done_definition_audit.ROOT,
                done_definition_audit.PRACTICAL_ADMISSION_SOURCE_CHECK_PATH,
                done_definition_audit.PRACTICAL_ADMISSION_WRAPPER_ROOT,
                done_definition_audit.run_command,
            )
            try:
                done_definition_audit.ROOT = root
                done_definition_audit.PRACTICAL_ADMISSION_SOURCE_CHECK_PATH = scanner
                done_definition_audit.PRACTICAL_ADMISSION_WRAPPER_ROOT = wrapper_root
                done_definition_audit.run_command = fake_run_command
                gate = evaluate_practical_admission_source_gate(30)
            finally:
                (
                    done_definition_audit.ROOT,
                    done_definition_audit.PRACTICAL_ADMISSION_SOURCE_CHECK_PATH,
                    done_definition_audit.PRACTICAL_ADMISSION_WRAPPER_ROOT,
                    done_definition_audit.run_command,
                ) = originals

        self.assertEqual(gate["status"], "pass")
        self.assertEqual(gate["details"]["scanned_files"], 1)
        self.assertEqual(gate["details"]["violating_files"], 0)
        self.assertEqual(gate["details"]["violation_count"], 0)

    def test_practical_admission_source_gate_reports_untracked_violations_without_failing_tracked_source(self) -> None:
        import done_definition_audit

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scanner = root / "support" / "scripts" / "research" / "downstream_practical_admission_source_check.py"
            wrapper_root = root / "support" / "docs" / "experiments" / "actionable-regime-confidence" / "scripts"
            scanner.parent.mkdir(parents=True)
            wrapper_root.mkdir(parents=True)
            scanner.write_text("# scanner placeholder\n", encoding="utf-8")
            tracked = wrapper_root / "run_tracked_good_v1.py"
            untracked = wrapper_root / "run_untracked_bad_v1.py"
            tracked.write_text("# tracked good\n", encoding="utf-8")
            untracked.write_text("# untracked bad\n", encoding="utf-8")

            def fake_run_command(cmd, *, cwd, timeout, env=None):
                del cmd, cwd, timeout, env
                return (
                    "fail",
                    {
                        "returncode": 1,
                        "stdout": json.dumps(
                            [
                                {"file": str(tracked), "ok": True, "violations": []},
                                {
                                    "file": str(untracked),
                                    "ok": False,
                                    "violations": [
                                        {
                                            "line": 9,
                                            "column": 20,
                                            "key": "trade_usable",
                                            "value": "admitted",
                                            "violation": "practical_flag_without_extension_complete_guard",
                                        }
                                    ],
                                },
                            ]
                        ),
                        "stderr": "",
                    },
                )

            originals = (
                done_definition_audit.ROOT,
                done_definition_audit.PRACTICAL_ADMISSION_SOURCE_CHECK_PATH,
                done_definition_audit.PRACTICAL_ADMISSION_WRAPPER_ROOT,
                done_definition_audit.run_command,
                done_definition_audit.tracked_wrapper_file_set,
            )
            try:
                done_definition_audit.ROOT = root
                done_definition_audit.PRACTICAL_ADMISSION_SOURCE_CHECK_PATH = scanner
                done_definition_audit.PRACTICAL_ADMISSION_WRAPPER_ROOT = wrapper_root
                done_definition_audit.run_command = fake_run_command
                done_definition_audit.tracked_wrapper_file_set = lambda wrapper_files, timeout_seconds: {tracked}
                gate = evaluate_practical_admission_source_gate(30)
            finally:
                (
                    done_definition_audit.ROOT,
                    done_definition_audit.PRACTICAL_ADMISSION_SOURCE_CHECK_PATH,
                    done_definition_audit.PRACTICAL_ADMISSION_WRAPPER_ROOT,
                    done_definition_audit.run_command,
                    done_definition_audit.tracked_wrapper_file_set,
                ) = originals

        self.assertEqual(gate["status"], "pass")
        self.assertEqual(gate["details"]["tracked_scanned_files"], 1)
        self.assertEqual(gate["details"]["tracked_violating_files"], 0)
        self.assertEqual(gate["details"]["tracked_violation_count"], 0)
        self.assertEqual(gate["details"]["untracked_scanned_files"], 1)
        self.assertEqual(gate["details"]["untracked_violating_files"], 1)
        self.assertEqual(gate["details"]["untracked_violation_count"], 1)

    def test_practical_admission_debt_manifest_reports_quarantine_match(self) -> None:
        import done_definition_audit

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            quarantine_path = root / "support" / "docs" / "audits" / "practical-admission-source-debt-quarantine.json"
            quarantine_path.parent.mkdir(parents=True)
            untracked_violations = [
                {
                    "file": "support/docs/experiments/actionable-regime-confidence/scripts/run_untracked_bad_v1.py",
                    "line": 9,
                    "key": "trade_usable",
                    "violation": "practical_flag_without_extension_complete_guard",
                }
            ]
            fingerprint = hashlib.sha256(
                json.dumps(untracked_violations, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
            ).hexdigest()
            quarantine_path.write_text(
                json.dumps(
                    {
                        "schema_version": "practical-admission-source-debt-quarantine/v1",
                        "untracked_violation_count": 1,
                        "untracked_violating_files": 1,
                        "untracked_violations_sha256": fingerprint,
                        "decision": "quarantined_untracked_wrapper_debt",
                    }
                ),
                encoding="utf-8",
            )

            original_root = done_definition_audit.ROOT
            try:
                done_definition_audit.ROOT = root
                manifest_path = write_practical_admission_debt_manifest(
                    {
                        "violation_count": 1,
                        "tracked_violation_count": 0,
                        "tracked_violating_files": 0,
                        "untracked_violation_count": 1,
                        "untracked_violating_files": 1,
                        "violations_by_type": {"practical_flag_without_extension_complete_guard": 1},
                        "tracked_violations": [],
                        "untracked_violations": untracked_violations,
                    }
                )
            finally:
                done_definition_audit.ROOT = original_root

        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        self.assertTrue(manifest["quarantine"]["matched"])
        self.assertEqual(manifest["quarantine"]["decision"], "quarantined_untracked_wrapper_debt")
        self.assertEqual(manifest["quarantine"]["manifest_file"], "support/docs/audits/practical-admission-source-debt-quarantine.json")
        self.assertEqual(manifest["quarantine"]["untracked_violations_sha256"], fingerprint)


if __name__ == "__main__":
    unittest.main()
