#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from objective_closure_snapshot import (  # noqa: E402
    QUICKSTART_CHAIN,
    build_audit_specs,
    build_failure_report,
    build_snapshot,
    effective_timeout_seconds,
    format_report,
    run_command,
    summarize_snapshot,
    write_report_file,
)


class ObjectiveClosureSnapshotTest(unittest.TestCase):
    def test_build_audit_specs_includes_output_paths_and_passthrough_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            specs = build_audit_specs(
                output_dir=Path(tmp),
                run_all_heavy=True,
                check_remotes=True,
            )

        self.assertIn("--run-all-heavy", specs["done_definition"]["argv"])
        self.assertIn("--check-remotes", specs["release_readiness"]["argv"])
        self.assertIn("--output", specs["done_definition"]["argv"])
        self.assertTrue(str(specs["factor_closure"]["output_path"]).endswith("factor_claim_terminalization_audit.compact.json"))

    def test_summarize_snapshot_marks_blocked_surface_when_child_audits_are_red(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": False,
                "quickstart_surface": "pass",
            },
            {
                "status": "needs_attention",
            },
            {
                "status": "needs_fix",
            },
        )

        self.assertEqual(summary["status"], "not_complete")
        self.assertFalse(summary["surface_green"])
        self.assertFalse(summary["completion_proven"])
        self.assertIn("done_definition_not_completion_ready", summary["blockers"])
        self.assertIn("factor_closure_blocked", summary["blockers"])
        self.assertIn("release_readiness_blocked", summary["blockers"])

    def test_summarize_snapshot_keeps_manual_requirement_even_when_child_surfaces_are_green(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": True,
                "quickstart_surface": "pass",
            },
            {
                "status": "pass",
            },
            {
                "status": "pass",
            },
        )

        self.assertEqual(summary["status"], "surface_green_manual_end_to_end_proof_required")
        self.assertTrue(summary["surface_green"])
        self.assertFalse(summary["completion_proven"])
        self.assertIn("same_tree_practical_closure_packet", summary["manual_requirements_remaining"])

    def test_build_snapshot_emits_quickstart_chain_and_evidence_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            audit_results = {
                "done_definition": {
                "command": {"argv": ["done"], "returncode": 0},
                "report": {
                    "timestamp_utc": "2026-05-27T11:00:00Z",
                    "summary": {
                        "status": "pass",
                        "completion_ready": False,
                        "evidence_level": "partial_skipped_gates",
                            "unresolved": [],
                            "skipped_gates": ["cargo_test"],
                        },
                        "gates": [{"id": "quickstart_surface", "status": "pass"}],
                    },
                    "output_path": output_dir / "done_definition_audit.compact.json",
                },
                "factor_closure": {
                "command": {"argv": ["factor"], "returncode": 1},
                "report": {
                    "generated_at": "2026-05-27T11:00:01+00:00",
                    "summary": {
                        "status": "needs_attention",
                        "active_claims": 10,
                        "invalid_active_claims": 0,
                        "live_factor_processes": 2,
                        "blocking_reasons": ["active_claims", "live_factor_processes"],
                        "promotion_allowed_true": 0,
                        "trade_usable_true": 0,
                        "next_action": "wait",
                    },
                    "attention_claim_count": 10,
                    "attention_live_process_count": 2,
                    "attention_groups": {"by_owner": {"codex": 10}},
                },
                "output_path": output_dir / "factor_claim_terminalization_audit.compact.json",
            },
                "release_readiness": {
                    "command": {"argv": ["release"], "returncode": 1},
                    "report": {
                        "timestamp_utc": "2026-05-27T11:00:02Z",
                        "summary": {
                            "status": "needs_fix",
                            "unresolved": ["worktree_clean_for_release", "remote_readback"],
                            "pass_count": 2,
                            "fail_count": 2,
                            "skip_count": 1,
                        }
                    },
                    "output_path": output_dir / "release_readiness_audit.compact.json",
                },
            }

            snapshot = build_snapshot(
                audit_results,
                run_all_heavy=False,
                check_remotes=True,
                output_dir=output_dir,
            )

        self.assertEqual(snapshot["schema_version"], "objective-closure-snapshot/v1")
        self.assertEqual(snapshot["quickstart_chain"], QUICKSTART_CHAIN)
        self.assertEqual(
            snapshot["evidence_files"]["done_definition"],
            str(output_dir / "done_definition_audit.compact.json"),
        )
        self.assertEqual(
            snapshot["audits"]["done_definition"]["surface"]["report_timestamp"],
            "2026-05-27T11:00:00Z",
        )
        self.assertEqual(snapshot["audits"]["factor_closure"]["surface"]["live_factor_processes"], 2)
        self.assertEqual(
            snapshot["audits"]["factor_closure"]["surface"]["blocking_reasons"],
            ["active_claims", "live_factor_processes"],
        )
        self.assertEqual(
            snapshot["audits"]["factor_closure"]["surface"]["attention_by_owner"],
            {"codex": 10},
        )
        self.assertEqual(
            snapshot["audits"]["release_readiness"]["surface"]["report_timestamp"],
            "2026-05-27T11:00:02Z",
        )
        self.assertEqual(snapshot["summary"]["status"], "not_complete")

    def test_format_report_compact_emits_single_line_json(self) -> None:
        text = format_report({"summary": {"status": "not_complete"}}, compact=True)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\n  ", text)
        self.assertIn('"status":"not_complete"', text)
        json.loads(text)

    def test_run_command_returns_structured_timeout_details(self) -> None:
        status = run_command(
            [
                sys.executable,
                "-c",
                "import sys, time; sys.stdout.write('out'); sys.stdout.flush(); time.sleep(2)",
            ],
            cwd=SCRIPTS_ROOT,
            timeout=1,
        )

        self.assertEqual(status["error"], "timeout")
        self.assertEqual(status["timeout_seconds"], 1)
        self.assertEqual(status["returncode"], None)
        self.assertIn("out", status["stdout"])

    def test_effective_timeout_seconds_defaults_higher_for_heavy_mode(self) -> None:
        self.assertEqual(effective_timeout_seconds(None, run_all_heavy=False), 90)
        self.assertEqual(effective_timeout_seconds(None, run_all_heavy=True), 300)
        self.assertEqual(effective_timeout_seconds(17, run_all_heavy=True), 17)

    def test_write_report_file_persists_failure_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            report = build_failure_report(
                failed_audit="done_definition",
                error="missing_json_output",
                command_result={"argv": ["done"], "error": "timeout"},
                run_all_heavy=True,
                check_remotes=True,
                output_dir=output_dir,
            )
            write_report_file(report, output_dir)
            saved = json.loads((output_dir / "objective_closure_snapshot.json").read_text(encoding="utf-8"))

        self.assertEqual(saved["summary"]["status"], "snapshot_failed")
        self.assertEqual(saved["summary"]["failed_audit"], "done_definition")
        self.assertEqual(saved["options"]["run_all_heavy"], True)
