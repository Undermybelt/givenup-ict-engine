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
    stage_done_definition_proof,
    run_command,
    snapshot_exit_code,
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
        self.assertIn("--portable-paths", specs["factor_closure"]["argv"])
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
            snapshot_timestamp="2026-05-27T11:00:10Z",
        )

        self.assertEqual(summary["status"], "not_complete")
        self.assertFalse(summary["surface_green"])
        self.assertFalse(summary["completion_proven"])
        self.assertIn("done_definition_not_completion_ready", summary["blockers"])
        self.assertIn("factor_closure_blocked", summary["blockers"])
        self.assertIn("release_readiness_blocked", summary["blockers"])
        self.assertEqual(
            summary["child_report_timestamps"],
            {
                "done_definition": None,
                "factor_closure": None,
                "release_readiness": None,
            },
        )
        self.assertEqual(summary["child_report_age_seconds"], {})
        self.assertEqual(summary["prioritized_next_actions"], [])

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
            snapshot_timestamp="2026-05-27T11:00:10Z",
        )

        self.assertEqual(summary["status"], "surface_green_manual_end_to_end_proof_required")
        self.assertTrue(summary["surface_green"])
        self.assertFalse(summary["completion_proven"])
        self.assertIn("same_tree_practical_closure_packet", summary["manual_requirements_remaining"])

    def test_summarize_snapshot_blocks_when_no_practical_factor_is_trade_usable(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": True,
                "quickstart_surface": "pass",
            },
            {
                "status": "pass",
                "promotion_allowed_true": 0,
                "trade_usable_true": 0,
                "next_action": "no claim terminalization blockers found",
            },
            {
                "status": "pass",
            },
            snapshot_timestamp="2026-05-27T11:00:10Z",
        )

        self.assertEqual(summary["status"], "not_complete")
        self.assertFalse(summary["surface_green"])
        self.assertIn("same_tree_practical_closure_unproven", summary["blockers"])
        self.assertIn(
            {
                "surface": "factor_closure",
                "reason": "same_tree_practical_closure_unproven",
                "action": "produce or locate a same-tree practical closure packet with promotion_allowed_true>0 and trade_usable_true>0",
            },
            summary["prioritized_next_actions"],
        )

    def test_summarize_snapshot_does_not_prioritize_done_definition_when_full_coverage_passes(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": True,
                "quickstart_surface": "pass",
                "next_action": "done-definition gates have full enabled coverage",
            },
            {
                "status": "needs_attention",
                "next_action": "wait for fresh active claims to progress",
            },
            {
                "status": "pass",
                "unresolved_next_actions": {},
            },
            snapshot_timestamp="2026-05-27T11:00:10Z",
        )

        self.assertNotIn("done_definition_not_completion_ready", summary["blockers"])
        self.assertNotIn(
            {
                "surface": "done_definition",
                "reason": "completion_proof_gap",
                "action": "done-definition gates have full enabled coverage",
            },
            summary["prioritized_next_actions"],
        )

    def test_summarize_snapshot_lists_every_live_factor_runtime_action(self) -> None:
        live_roots = [
            {"pid": 1001, "run_root": "root-a"},
            {"pid": 1002, "run_root": "root-b"},
            {"pid": 1003, "run_root": "root-c"},
            {"pid": 1004, "run_root": "root-d"},
        ]

        summary = summarize_snapshot(
            {
                "completion_ready": False,
                "quickstart_surface": "pass",
                "next_action": "rerun heavy gates",
            },
            {
                "status": "needs_attention",
                "next_action": "wait for live roots",
                "attention_action_queue": {
                    "live_runtime_run_roots": live_roots,
                },
            },
            {
                "status": "pass",
                "unresolved_next_actions": {},
            },
            snapshot_timestamp="2026-05-27T11:00:10Z",
        )

        live_actions = [
            action
            for action in summary["prioritized_next_actions"]
            if action["surface"] == "factor_closure"
            and action["reason"] == "live_runtime_queue_head"
        ]

        self.assertEqual(len(live_actions), 4)
        self.assertEqual(
            [action["action"] for action in live_actions],
            [
                "wait for pid 1001 run_root root-a to exit or claim it explicitly",
                "wait for pid 1002 run_root root-b to exit or claim it explicitly",
                "wait for pid 1003 run_root root-c to exit or claim it explicitly",
                "wait for pid 1004 run_root root-d to exit or claim it explicitly",
            ],
        )

    def test_summarize_snapshot_lists_every_wait_only_and_stale_factor_action(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": False,
                "quickstart_surface": "pass",
                "next_action": "rerun heavy gates",
            },
            {
                "status": "needs_attention",
                "next_action": "clear factor claims",
                "attention_action_queue": {
                    "externalize_wait_only_claims": [
                        {
                            "claim_file": "wait-a.claim",
                            "stale_safe_takeover_candidate": False,
                        },
                        {
                            "claim_file": "wait-b.claim",
                            "stale_safe_takeover_candidate": True,
                        },
                    ],
                    "stale_safe_takeover_claims": [
                        {"claim_file": "stale-a.claim"},
                        {"claim_file": "stale-b.claim"},
                    ],
                },
            },
            {
                "status": "pass",
                "unresolved_next_actions": {},
            },
            snapshot_timestamp="2026-05-27T11:00:10Z",
        )

        factor_actions = [
            action
            for action in summary["prioritized_next_actions"]
            if action["surface"] == "factor_closure"
        ]

        self.assertIn(
            {
                "surface": "factor_closure",
                "reason": "wait_only_fresh_claim_without_live_runtime",
                "action": "wait for owner progress or stale-safe timeout on wait-a.claim",
            },
            factor_actions,
        )
        self.assertIn(
            {
                "surface": "factor_closure",
                "reason": "wait_only_stale_safe_takeover_candidate",
                "action": "externalize or terminalize stale-safe wait-b.claim",
            },
            factor_actions,
        )
        self.assertIn(
            {
                "surface": "factor_closure",
                "reason": "stale_safe_takeover_queue_head",
                "action": "review takeover ownership of stale-a.claim",
            },
            factor_actions,
        )
        self.assertIn(
            {
                "surface": "factor_closure",
                "reason": "stale_safe_takeover_queue_head",
                "action": "review takeover ownership of stale-b.claim",
            },
            factor_actions,
        )

    def test_summarize_snapshot_lists_fresh_active_claims_as_wait_before_terminalize(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": False,
                "quickstart_surface": "pass",
            },
            {
                "status": "needs_attention",
                "next_action": "wait for fresh active claims to progress, then rerun before terminalizing",
                "attention_action_queue": {
                    "fresh_active_claims_without_live_process": [
                        {
                            "claim_file": "fresh.claim",
                            "age_minutes": 2,
                            "status": "active_setup",
                        }
                    ]
                },
            },
            {
                "status": "pass",
                "unresolved_next_actions": {},
            },
            snapshot_timestamp="2026-05-27T11:00:10Z",
        )

        self.assertIn(
            {
                "surface": "factor_closure",
                "reason": "fresh_active_claim_without_live_runtime",
                "action": "wait for owner progress or inspect fresh active claim fresh.claim before terminalizing",
            },
            summary["prioritized_next_actions"],
        )

    def test_summarize_snapshot_deduplicates_wait_only_stale_factor_claim_actions(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": False,
                "quickstart_surface": "pass",
            },
            {
                "status": "needs_attention",
                "next_action": "clear factor claims",
                "attention_action_queue": {
                    "externalize_wait_only_claims": [
                        {
                            "claim_file": "same.claim",
                            "stale_safe_takeover_candidate": True,
                        }
                    ],
                    "stale_safe_takeover_claims": [
                        {
                            "claim_file": "same.claim",
                            "wait_only_without_live_process": True,
                        }
                    ],
                },
            },
            {
                "status": "pass",
                "unresolved_next_actions": {},
            },
            snapshot_timestamp="2026-05-27T11:00:10Z",
        )

        claim_actions = [
            action
            for action in summary["prioritized_next_actions"]
            if "same.claim" in action["action"]
        ]

        self.assertEqual(
            claim_actions,
            [
                {
                    "surface": "factor_closure",
                    "reason": "wait_only_stale_safe_takeover_candidate",
                    "action": "externalize or terminalize stale-safe same.claim",
                }
            ],
        )

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
                            "next_action": "rerun with --run-all-heavy before treating done-definition as completion proof",
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
                        "active_claims_without_live_process": 8,
                        "wait_only_active_claims_without_live_process": 3,
                        "stale_safe_takeover_candidates": 7,
                        "blocking_reasons": ["active_claims", "live_factor_processes"],
                        "promotion_allowed_true": 0,
                        "trade_usable_true": 0,
                        "next_action": "wait",
                    },
                    "attention_claim_count": 10,
                    "attention_live_process_count": 2,
                    "attention_groups": {
                        "by_owner": {"codex": 10},
                        "by_actionability": {
                            "active_claim_debt": 1,
                            "live_runtime_owner": 2,
                            "stale_safe_takeover_candidate": 7,
                        },
                    },
                    "attention_action_queue": {
                        "externalize_wait_only_claims": [
                            {
                                "claim_file": "wait-only.claim",
                                "age_minutes": 88,
                                "stale_safe_takeover_candidate": True,
                            },
                            {
                                "claim_file": "second-wait-only.claim",
                                "age_minutes": 34,
                                "stale_safe_takeover_candidate": False,
                            }
                        ],
                        "stale_safe_takeover_claims": [
                            {
                                "claim_file": "stale.claim",
                                "age_minutes": 120,
                                "wait_only_without_live_process": False,
                            },
                            {
                                "claim_file": "second-stale.claim",
                                "age_minutes": 95,
                                "wait_only_without_live_process": False,
                            }
                        ],
                        "live_runtime_run_roots": [
                            {
                                "pid": 4321,
                                "run_root": "ict-engine-live-root",
                                "exit_file_state": "none",
                            },
                            {
                                "pid": 9876,
                                "run_root": "ict-engine-second-live-root",
                                "exit_file_state": "present",
                            },
                            {
                                "pid": 2468,
                                "run_root": "ict-engine-third-live-root",
                                "exit_file_state": "stale_for_process",
                            },
                            {
                                "pid": 1357,
                                "run_root": "ict-engine-fourth-live-root",
                                "exit_file_state": "present",
                            }
                        ],
                    },
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
                        },
                        "gates": [
                            {
                                "id": "worktree_clean_for_release",
                                "status": "fail",
                                "details": {
                                    "next_action": "commit or exclude a narrow source slice, then build release evidence from a clean sanitized export",
                                },
                            },
                            {
                                "id": "remote_readback",
                                "status": "fail",
                                "details": {
                                    "next_action": "restore release mirror git/network/auth readback, or rerun from a network that can reach the release mirror, then rerun release readiness audit with --check-remotes",
                                },
                            },
                        ],
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
        self.assertEqual(snapshot["repo_root"], "ict-engine")
        self.assertEqual(snapshot["options"]["output_dir"], ".")
        self.assertEqual(
            snapshot["evidence_files"]["done_definition"],
            "done_definition_audit.compact.json",
        )
        self.assertEqual(
            snapshot["audits"]["done_definition"]["surface"]["report_timestamp"],
            "2026-05-27T11:00:00Z",
        )
        self.assertEqual(
            snapshot["audits"]["done_definition"]["surface"]["next_action"],
            "rerun with --run-all-heavy before treating done-definition as completion proof",
        )
        self.assertEqual(snapshot["audits"]["factor_closure"]["surface"]["live_factor_processes"], 2)
        self.assertEqual(
            snapshot["audits"]["factor_closure"]["surface"]["active_claims_without_live_process"],
            8,
        )
        self.assertEqual(
            snapshot["audits"]["factor_closure"]["surface"]["wait_only_active_claims_without_live_process"],
            3,
        )
        self.assertEqual(
            snapshot["audits"]["factor_closure"]["surface"]["stale_safe_takeover_candidates"],
            7,
        )
        self.assertEqual(
            snapshot["audits"]["factor_closure"]["surface"]["blocking_reasons"],
            ["active_claims", "live_factor_processes"],
        )
        self.assertEqual(
            snapshot["audits"]["factor_closure"]["surface"]["attention_by_owner"],
            {"codex": 10},
        )
        self.assertEqual(
            snapshot["audits"]["factor_closure"]["surface"]["attention_by_actionability"],
            {
                "active_claim_debt": 1,
                "live_runtime_owner": 2,
                "stale_safe_takeover_candidate": 7,
            },
        )
        self.assertEqual(
            snapshot["audits"]["factor_closure"]["surface"]["attention_action_queue"],
            {
                "externalize_wait_only_claims": [
                    {
                        "claim_file": "wait-only.claim",
                        "age_minutes": 88,
                        "stale_safe_takeover_candidate": True,
                    },
                    {
                        "claim_file": "second-wait-only.claim",
                        "age_minutes": 34,
                        "stale_safe_takeover_candidate": False,
                    }
                ],
                "stale_safe_takeover_claims": [
                    {
                        "claim_file": "stale.claim",
                        "age_minutes": 120,
                        "wait_only_without_live_process": False,
                    },
                    {
                        "claim_file": "second-stale.claim",
                        "age_minutes": 95,
                        "wait_only_without_live_process": False,
                    }
                ],
                "live_runtime_run_roots": [
                    {
                        "pid": 4321,
                        "run_root": "ict-engine-live-root",
                        "exit_file_state": "none",
                    },
                    {
                        "pid": 9876,
                        "run_root": "ict-engine-second-live-root",
                        "exit_file_state": "present",
                    },
                    {
                        "pid": 2468,
                        "run_root": "ict-engine-third-live-root",
                        "exit_file_state": "stale_for_process",
                    },
                    {
                        "pid": 1357,
                        "run_root": "ict-engine-fourth-live-root",
                        "exit_file_state": "present",
                    }
                ],
            },
        )
        self.assertEqual(
            snapshot["audits"]["release_readiness"]["surface"]["report_timestamp"],
            "2026-05-27T11:00:02Z",
        )
        self.assertEqual(
            snapshot["audits"]["release_readiness"]["surface"]["unresolved_next_actions"],
            {
                "worktree_clean_for_release": "commit or exclude a narrow source slice, then build release evidence from a clean sanitized export",
                "remote_readback": "restore release mirror git/network/auth readback, or rerun from a network that can reach the release mirror, then rerun release readiness audit with --check-remotes",
            },
        )
        self.assertEqual(snapshot["summary"]["status"], "not_complete")
        self.assertEqual(
            snapshot["summary"]["child_next_actions"],
            {
                "done_definition": "rerun with --run-all-heavy before treating done-definition as completion proof",
                "factor_closure": "wait",
                "release_readiness": {
                    "worktree_clean_for_release": "commit or exclude a narrow source slice, then build release evidence from a clean sanitized export",
                    "remote_readback": "restore release mirror git/network/auth readback, or rerun from a network that can reach the release mirror, then rerun release readiness audit with --check-remotes",
                },
            },
        )
        self.assertEqual(
            snapshot["summary"]["child_report_timestamps"],
            {
                "done_definition": "2026-05-27T11:00:00Z",
                "factor_closure": "2026-05-27T11:00:01+00:00",
                "release_readiness": "2026-05-27T11:00:02Z",
            },
        )
        self.assertEqual(
            sorted(snapshot["summary"]["child_report_age_seconds"].keys()),
            ["done_definition", "factor_closure", "release_readiness"],
        )
        self.assertTrue(
            all(
                isinstance(value, int) and value >= 0
                for value in snapshot["summary"]["child_report_age_seconds"].values()
            )
        )
        self.assertEqual(
            snapshot["summary"]["prioritized_next_actions"],
            [
                {
                    "surface": "done_definition",
                    "reason": "completion_proof_gap",
                    "action": "rerun with --run-all-heavy before treating done-definition as completion proof",
                },
                {
                    "surface": "factor_closure",
                    "reason": "wait_only_stale_safe_takeover_candidate",
                    "action": "externalize or terminalize stale-safe wait-only.claim",
                },
                {
                    "surface": "factor_closure",
                    "reason": "wait_only_fresh_claim_without_live_runtime",
                    "action": "wait for owner progress or stale-safe timeout on second-wait-only.claim",
                },
                {
                    "surface": "factor_closure",
                    "reason": "stale_safe_takeover_queue_head",
                    "action": "review takeover ownership of stale.claim",
                },
                {
                    "surface": "factor_closure",
                    "reason": "stale_safe_takeover_queue_head",
                    "action": "review takeover ownership of second-stale.claim",
                },
                {
                    "surface": "factor_closure",
                    "reason": "live_runtime_queue_head",
                    "action": "wait for pid 4321 run_root ict-engine-live-root to exit or claim it explicitly",
                },
                {
                    "surface": "factor_closure",
                    "reason": "live_runtime_queue_head",
                    "action": "wait for pid 9876 run_root ict-engine-second-live-root to exit or claim it explicitly",
                },
                {
                    "surface": "factor_closure",
                    "reason": "live_runtime_queue_head",
                    "action": "wait for pid 2468 run_root ict-engine-third-live-root to exit or claim it explicitly",
                },
                {
                    "surface": "factor_closure",
                    "reason": "live_runtime_queue_head",
                    "action": "wait for pid 1357 run_root ict-engine-fourth-live-root to exit or claim it explicitly",
                },
                {
                    "surface": "factor_closure",
                    "reason": "practical_closure_blocked",
                    "action": "wait",
                },
                {
                    "surface": "release_readiness",
                    "reason": "worktree_clean_for_release",
                    "action": "commit or exclude a narrow source slice, then build release evidence from a clean sanitized export",
                },
                {
                    "surface": "release_readiness",
                    "reason": "remote_readback",
                    "action": "restore release mirror git/network/auth readback, or rerun from a network that can reach the release mirror, then rerun release readiness audit with --check-remotes",
                },
            ],
        )

    def test_format_report_compact_emits_single_line_json(self) -> None:
        text = format_report({"summary": {"status": "not_complete"}}, compact=True)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\n  ", text)
        self.assertIn('"status":"not_complete"', text)
        json.loads(text)

    def test_snapshot_exit_code_fails_closed_when_completion_is_unproven(self) -> None:
        self.assertEqual(
            snapshot_exit_code({"summary": {"status": "not_complete", "completion_proven": False}}),
            1,
        )
        self.assertEqual(
            snapshot_exit_code({"summary": {"status": "snapshot_failed"}}),
            2,
        )
        self.assertEqual(
            snapshot_exit_code({"summary": {"status": "complete", "completion_proven": True}}),
            0,
        )

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
                command_result={"argv": [str(output_dir / "done.py")], "error": "timeout"},
                run_all_heavy=True,
                check_remotes=True,
                output_dir=output_dir,
            )
            write_report_file(report, output_dir)
            saved = json.loads((output_dir / "objective_closure_snapshot.json").read_text(encoding="utf-8"))

        self.assertEqual(saved["summary"]["status"], "snapshot_failed")
        self.assertEqual(saved["summary"]["failed_audit"], "done_definition")
        self.assertEqual(saved["options"]["run_all_heavy"], True)
        self.assertEqual(saved["repo_root"], "ict-engine")
        self.assertEqual(saved["options"]["output_dir"], ".")
        self.assertEqual(saved["command"]["argv"], ["done.py"])

    def test_build_snapshot_rewrites_absolute_script_and_child_paths_for_packet_portability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            audit_results = {
                "done_definition": {
                    "command": {
                        "argv": [sys.executable, str(SCRIPTS_ROOT / "done_definition_audit.py"), "--compact"],
                        "returncode": 0,
                    },
                    "report": {
                        "timestamp_utc": "2026-05-27T11:00:00Z",
                        "summary": {
                            "status": "pass",
                            "completion_ready": True,
                            "evidence_level": "full_enabled_gate_coverage",
                            "unresolved": [],
                            "skipped_gates": [],
                        },
                        "gates": [{"id": "quickstart_surface", "status": "pass"}],
                    },
                    "output_path": output_dir / "done_definition_audit.compact.json",
                },
                "factor_closure": {
                    "command": {
                        "argv": [sys.executable, str(SCRIPTS_ROOT / "factor_claim_terminalization_audit.py"), "--compact"],
                        "returncode": 0,
                    },
                    "report": {
                        "generated_at": "2026-05-27T11:00:01+00:00",
                        "summary": {
                            "status": "pass",
                            "active_claims": 0,
                            "invalid_active_claims": 0,
                            "live_factor_processes": 0,
                            "blocking_reasons": [],
                            "promotion_allowed_true": 0,
                            "trade_usable_true": 0,
                            "next_action": "none",
                        },
                        "attention_claim_count": 0,
                        "attention_live_process_count": 0,
                        "attention_groups": {"by_owner": {}},
                    },
                    "output_path": output_dir / "factor_claim_terminalization_audit.compact.json",
                },
                "release_readiness": {
                    "command": {
                        "argv": [sys.executable, str(SCRIPTS_ROOT / "release_readiness_audit.py"), "--compact"],
                        "returncode": 0,
                    },
                    "report": {
                        "timestamp_utc": "2026-05-27T11:00:02Z",
                        "summary": {
                            "status": "pass",
                            "unresolved": [],
                            "pass_count": 3,
                            "fail_count": 0,
                            "skip_count": 0,
                        }
                    },
                    "output_path": output_dir / "release_readiness_audit.compact.json",
                },
            }

            snapshot = build_snapshot(
                audit_results,
                run_all_heavy=False,
                check_remotes=False,
                output_dir=output_dir,
            )

        self.assertEqual(snapshot["audit_commands"]["done_definition"][1], "support/scripts/done_definition_audit.py")
        self.assertEqual(snapshot["audit_commands"]["factor_closure"][1], "support/scripts/factor_claim_terminalization_audit.py")
        self.assertEqual(snapshot["audit_commands"]["release_readiness"][1], "support/scripts/release_readiness_audit.py")
        self.assertEqual(snapshot["audit_commands"]["done_definition"][0], "python3")
        self.assertEqual(snapshot["evidence_files"]["release_readiness"], "release_readiness_audit.compact.json")

    def test_build_snapshot_applies_valid_done_definition_proof_without_hiding_other_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            proof_path = output_dir / "heavy_done_definition.compact.json"
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 0},
                    "report": {
                        "timestamp_utc": "2026-05-28T01:00:00Z",
                        "summary": {
                            "status": "pass",
                            "completion_ready": False,
                            "evidence_level": "partial_skipped_gates",
                            "unresolved": [],
                            "skipped_gates": ["cargo_test"],
                            "next_action": "rerun with --run-all-heavy before treating done-definition as completion proof",
                        },
                        "gates": [{"id": "quickstart_surface", "status": "pass"}],
                    },
                    "output_path": output_dir / "done_definition_audit.compact.json",
                },
                "factor_closure": {
                    "command": {"argv": ["factor"], "returncode": 1},
                    "report": {
                        "generated_at": "2026-05-28T01:00:01+00:00",
                        "summary": {
                            "status": "needs_attention",
                            "active_claims": 1,
                            "invalid_active_claims": 0,
                            "live_factor_processes": 1,
                            "blocking_reasons": ["active_claims", "live_factor_processes"],
                            "promotion_allowed_true": 0,
                            "trade_usable_true": 0,
                            "next_action": "wait for live factor process",
                        },
                    },
                    "output_path": output_dir / "factor_claim_terminalization_audit.compact.json",
                },
                "release_readiness": {
                    "command": {"argv": ["release"], "returncode": 1},
                    "report": {
                        "timestamp_utc": "2026-05-28T01:00:02Z",
                        "summary": {
                            "status": "needs_fix",
                            "unresolved": ["worktree_clean_for_release"],
                            "pass_count": 2,
                            "fail_count": 1,
                            "skip_count": 0,
                        },
                        "gates": [
                            {
                                "id": "worktree_clean_for_release",
                                "status": "fail",
                                "details": {"next_action": "commit or exclude a narrow source slice"},
                            }
                        ],
                    },
                    "output_path": output_dir / "release_readiness_audit.compact.json",
                },
            }
            done_definition_proof = {
                "path": proof_path,
                "report": {
                    "timestamp_utc": "2026-05-28T00:59:00Z",
                    "summary": {
                        "status": "pass",
                        "completion_ready": True,
                        "evidence_level": "full_enabled_gate_coverage",
                        "unresolved": [],
                        "skipped_gates": [],
                        "next_action": "done-definition gates have full enabled coverage",
                    },
                    "gates": [{"id": "quickstart_surface", "status": "pass"}],
                },
            }

            snapshot = build_snapshot(
                audit_results,
                run_all_heavy=False,
                check_remotes=True,
                output_dir=output_dir,
                done_definition_proof=done_definition_proof,
            )

        done_surface = snapshot["audits"]["done_definition"]["surface"]
        self.assertTrue(done_surface["completion_ready"])
        self.assertEqual(done_surface["proof_source"], "heavy_done_definition.compact.json")
        self.assertTrue(done_surface["proof_applied"])
        self.assertNotIn("done_definition_not_completion_ready", snapshot["summary"]["blockers"])
        self.assertIn("factor_closure_blocked", snapshot["summary"]["blockers"])
        self.assertIn("release_readiness_blocked", snapshot["summary"]["blockers"])
        self.assertFalse(
            any(
                action["surface"] == "done_definition"
                and action["reason"] == "completion_proof_gap"
                for action in snapshot["summary"]["prioritized_next_actions"]
            )
        )

    def test_build_snapshot_rejects_partial_done_definition_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 0},
                    "report": {
                        "timestamp_utc": "2026-05-28T01:00:00Z",
                        "summary": {
                            "status": "pass",
                            "completion_ready": False,
                            "evidence_level": "partial_skipped_gates",
                            "unresolved": [],
                            "skipped_gates": ["cargo_test"],
                            "next_action": "rerun heavy gates",
                        },
                        "gates": [{"id": "quickstart_surface", "status": "pass"}],
                    },
                    "output_path": output_dir / "done_definition_audit.compact.json",
                },
                "factor_closure": {
                    "command": {"argv": ["factor"], "returncode": 0},
                    "report": {"summary": {"status": "pass"}},
                    "output_path": output_dir / "factor_claim_terminalization_audit.compact.json",
                },
                "release_readiness": {
                    "command": {"argv": ["release"], "returncode": 0},
                    "report": {"summary": {"status": "pass", "unresolved": []}},
                    "output_path": output_dir / "release_readiness_audit.compact.json",
                },
            }

            snapshot = build_snapshot(
                audit_results,
                run_all_heavy=False,
                check_remotes=False,
                output_dir=output_dir,
                done_definition_proof={
                    "path": output_dir / "partial_done_definition.compact.json",
                    "report": {
                        "timestamp_utc": "2026-05-28T00:59:00Z",
                        "summary": {
                            "status": "pass",
                            "completion_ready": False,
                            "evidence_level": "partial_skipped_gates",
                            "unresolved": [],
                            "skipped_gates": ["cargo_test"],
                        },
                    },
                },
            )

        done_surface = snapshot["audits"]["done_definition"]["surface"]
        self.assertFalse(done_surface["proof_applied"])
        self.assertEqual(done_surface["proof_rejected_reason"], "proof_not_completion_ready")
        self.assertIn("done_definition_not_completion_ready", snapshot["summary"]["blockers"])

    def test_stage_done_definition_proof_copies_external_proof_into_packet(self) -> None:
        with tempfile.TemporaryDirectory() as src_tmp, tempfile.TemporaryDirectory() as packet_tmp:
            source_path = Path(src_tmp) / "heavy.json"
            output_dir = Path(packet_tmp)
            source_report = {"summary": {"completion_ready": True, "skipped_gates": []}}
            source_path.write_text(json.dumps(source_report), encoding="utf-8")

            staged = stage_done_definition_proof(
                {"path": source_path, "report": source_report},
                output_dir=output_dir,
            )

            self.assertEqual(staged["path"], output_dir / "done_definition_proof.compact.json")
            self.assertEqual(staged["report"], source_report)
            self.assertEqual(
                json.loads((output_dir / "done_definition_proof.compact.json").read_text(encoding="utf-8")),
                source_report,
            )
