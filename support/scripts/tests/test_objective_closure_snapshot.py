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
    effective_done_child_timeout_seconds,
    effective_timeout_seconds,
    format_report,
    stage_done_definition_proof,
    stage_release_readiness_proof,
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
        self.assertIn("--practical-admission-source-timeout-seconds", specs["done_definition"]["argv"])
        self.assertIn("--help-audit-timeout-seconds", specs["done_definition"]["argv"])
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

    def test_summarize_snapshot_includes_done_definition_blocker_details(self) -> None:
        summary = summarize_snapshot(
            {
                "head": "abc123",
                "tracked_worktree_fingerprint": {
                    "sha256": "fingerprint",
                    "status": "dirty",
                    "tracked_status_entries": 7,
                },
                "report_timestamp": "2026-05-29T13:50:40Z",
                "status": "pass",
                "completion_ready": False,
                "evidence_level": "partial_skipped_gates",
                "pass_count": 12,
                "fail_count": 0,
                "skip_count": 4,
                "total_gates": 16,
                "quickstart_surface": "pass",
                "unresolved": [],
                "skipped_gates": [
                    "cargo_check_all_targets",
                    "cargo_clippy_all_targets_deny_warnings",
                    "cargo_test",
                    "smoke_acceptance_tmp_state",
                ],
                "next_action": "rerun with --run-all-heavy before treating done-definition as completion proof",
                "proof_applied": False,
                "proof_rejected_reason": "proof_has_skipped_gates",
            },
            {
                "status": "pass",
                "same_tree_practical_closure": {
                    "status": "pass",
                    "promotion_allowed": True,
                    "trade_usable": True,
                    "provider_execution_feedback_chain": "pass",
                    "evidence_packet": "packet.json",
                    "evidence_packet_validated": True,
                },
            },
            {
                "status": "pass",
                "unresolved_next_actions": {},
            },
            snapshot_timestamp="2026-05-29T13:50:52Z",
        )

        self.assertIn("done_definition_not_completion_ready", summary["blockers"])
        self.assertEqual(
            summary["blocker_details"]["done_definition_not_completion_ready"],
            {
                "head": "abc123",
                "tracked_worktree_fingerprint": {
                    "sha256": "fingerprint",
                    "status": "dirty",
                    "tracked_status_entries": 7,
                },
                "report_timestamp": "2026-05-29T13:50:40Z",
                "status": "pass",
                "completion_ready": False,
                "evidence_level": "partial_skipped_gates",
                "pass_count": 12,
                "fail_count": 0,
                "skip_count": 4,
                "total_gates": 16,
                "quickstart_surface": "pass",
                "unresolved": [],
                "skipped_gates": [
                    "cargo_check_all_targets",
                    "cargo_clippy_all_targets_deny_warnings",
                    "cargo_test",
                    "smoke_acceptance_tmp_state",
                ],
                "next_action": "rerun with --run-all-heavy before treating done-definition as completion proof",
                "proof_applied": False,
                "proof_rejected_reason": "proof_has_skipped_gates",
            },
        )

    def test_done_definition_blocker_preserves_failed_source_surface_detail(self) -> None:
        summary = summarize_snapshot(
            {
                "head": "abc123",
                "status": "needs_fix",
                "completion_ready": False,
                "quickstart_surface": "pass",
                "practical_admission_source_surface": {
                    "status": "fail",
                    "tracked_violation_count": 0,
                    "tracked_violating_files": 0,
                    "untracked_violation_count": 0,
                    "untracked_violating_files": 0,
                    "violation_count": 0,
                    "violating_files": 0,
                    "scanner_error": "timeout",
                    "scanner_timeout_seconds": 120,
                    "scanner_command": {
                        "argv_head": ["python3", "downstream_practical_admission_source_check.py"],
                        "target_arg_count": 1064,
                    },
                },
            },
            {
                "status": "pass",
                "same_tree_practical_closure": {
                    "status": "pass",
                    "promotion_allowed": True,
                    "trade_usable": True,
                    "provider_execution_feedback_chain": "pass",
                    "evidence_packet": "packet.json",
                    "evidence_packet_validated": True,
                },
            },
            {
                "status": "pass",
                "unresolved_next_actions": {},
            },
            snapshot_timestamp="2026-05-31T03:24:07Z",
        )

        detail = summary["blocker_details"]["done_definition_not_completion_ready"]
        source_detail = detail["practical_admission_source_surface"]
        self.assertEqual(source_detail["status"], "fail")
        self.assertEqual(source_detail["scanner_error"], "timeout")
        self.assertEqual(source_detail["scanner_timeout_seconds"], 120)
        self.assertEqual(source_detail["scanner_command"]["target_arg_count"], 1064)
        self.assertEqual(source_detail["tracked_violation_count"], 0)

    def test_summarize_snapshot_blocks_without_validated_same_tree_practical_closure_packet(self) -> None:
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

        self.assertEqual(summary["status"], "not_complete")
        self.assertFalse(summary["surface_green"])
        self.assertFalse(summary["completion_proven"])
        self.assertIn("same_tree_practical_closure_unproven", summary["blockers"])
        self.assertEqual(
            summary["blocker_details"]["same_tree_practical_closure_unproven"],
            {
                "reason": "validated_same_tree_practical_closure_packet_missing",
                "promotion_allowed_true": None,
                "trade_usable_true": None,
                "same_tree_practical_closure": None,
                "missing_practical_chain_stages": [
                    "provider_data",
                    "pre_bayes",
                    "bbn_workflow",
                    "path_ranker",
                    "execution_tree",
                    "feedback_update",
                    "policy_training",
                ],
                "blocking_context": {
                    "status": "pass",
                    "blocking_reasons": [],
                    "active_claims": None,
                    "fresh_active_claims_without_live_process": None,
                    "wait_only_active_claims_without_live_process": None,
                    "live_factor_processes": None,
                    "stale_safe_takeover_candidates": None,
                },
            },
        )
        self.assertIn("same_tree_practical_closure_packet", summary["manual_requirements_remaining"])

    def test_summarize_snapshot_does_not_treat_raw_factor_claim_flags_as_practical_closure(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": True,
                "quickstart_surface": "pass",
            },
            {
                "status": "pass",
                "promotion_allowed_true": 1,
                "trade_usable_true": 1,
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
        self.assertEqual(
            summary["blocker_details"]["same_tree_practical_closure_unproven"],
            {
                "reason": "raw_factor_claim_flags_are_not_validated_practical_closure",
                "promotion_allowed_true": 1,
                "trade_usable_true": 1,
                "same_tree_practical_closure": None,
                "missing_practical_chain_stages": [
                    "provider_data",
                    "pre_bayes",
                    "bbn_workflow",
                    "path_ranker",
                    "execution_tree",
                    "feedback_update",
                    "policy_training",
                ],
                "blocking_context": {
                    "status": "pass",
                    "blocking_reasons": [],
                    "active_claims": None,
                    "fresh_active_claims_without_live_process": None,
                    "wait_only_active_claims_without_live_process": None,
                    "live_factor_processes": None,
                    "stale_safe_takeover_candidates": None,
                },
            },
        )
        self.assertIn(
            {
                "surface": "factor_closure",
                "reason": "same_tree_practical_closure_unproven",
                "action": "produce or locate a validated same_tree_practical_closure packet; do not use raw promotion_allowed_true/trade_usable_true claim counters as proof",
            },
            summary["prioritized_next_actions"],
        )

    def test_summarize_snapshot_rejects_unvalidated_practical_closure_packet(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": True,
                "quickstart_surface": "pass",
            },
            {
                "status": "pass",
                "promotion_allowed_true": 0,
                "trade_usable_true": 0,
                "same_tree_practical_closure": {
                    "status": "pass",
                    "promotion_allowed": True,
                    "trade_usable": True,
                    "provider_execution_feedback_chain": "pass",
                    "evidence_packet": "checks/terminal_metrics.json",
                },
            },
            {
                "status": "pass",
            },
            snapshot_timestamp="2026-05-27T11:00:10Z",
        )

        self.assertEqual(summary["status"], "not_complete")
        self.assertFalse(summary["surface_green"])
        self.assertIn("same_tree_practical_closure_unproven", summary["blockers"])
        self.assertEqual(
            summary["blocker_details"]["same_tree_practical_closure_unproven"]["reason"],
            "same_tree_practical_closure_evidence_not_validated",
        )

    def test_summarize_snapshot_reports_partial_same_tree_stage_gap(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": True,
                "quickstart_surface": "pass",
            },
            {
                "status": "needs_attention",
                "promotion_allowed_true": 0,
                "trade_usable_true": 0,
                "same_tree_practical_closure": {
                    "status": "pass",
                    "promotion_allowed": True,
                    "trade_usable": True,
                    "provider_execution_feedback_chain": "pass",
                    "evidence_packet": "checks/terminal_metrics.json",
                    "evidence_packet_validated": False,
                    "validated_stage_coverage": [
                        "provider_data",
                        "pre_bayes",
                        "bbn_workflow",
                    ],
                },
                "active_claims": 2,
                "fresh_active_claims_without_live_process": 1,
                "wait_only_active_claims_without_live_process": 1,
                "live_factor_processes": 0,
                "stale_safe_takeover_candidates": 0,
                "blocking_reasons": ["active_claims"],
                "next_action": "wait for fresh active claims to progress",
            },
            {
                "status": "pass",
            },
            snapshot_timestamp="2026-05-27T11:00:10Z",
        )

        self.assertIn("same_tree_practical_closure_unproven", summary["blockers"])
        detail = summary["blocker_details"]["same_tree_practical_closure_unproven"]
        self.assertEqual(detail["reason"], "same_tree_practical_closure_evidence_not_validated")
        self.assertEqual(
            detail["present_practical_chain_stages"],
            ["provider_data", "pre_bayes", "bbn_workflow"],
        )
        self.assertEqual(
            detail["missing_practical_chain_stages"],
            ["path_ranker", "execution_tree", "feedback_update", "policy_training"],
        )
        self.assertEqual(
            detail["blocking_context"],
            {
                "status": "needs_attention",
                "blocking_reasons": ["active_claims"],
                "active_claims": 2,
                "fresh_active_claims_without_live_process": 1,
                "wait_only_active_claims_without_live_process": 1,
                "live_factor_processes": 0,
                "stale_safe_takeover_candidates": 0,
            },
        )

    def test_summarize_snapshot_counts_same_tree_gap_when_factor_claims_block(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": True,
                "quickstart_surface": "pass",
            },
            {
                "status": "needs_attention",
                "promotion_allowed_true": 0,
                "trade_usable_true": 0,
                "same_tree_practical_closure": None,
                "active_claims": 2,
                "fresh_active_claims_without_live_process": 1,
                "wait_only_active_claims_without_live_process": 1,
                "live_factor_processes": 0,
                "stale_safe_takeover_candidates": 0,
                "blocking_reasons": ["active_claims"],
                "next_action": "wait for fresh active claims to progress",
            },
            {
                "status": "pass",
            },
            snapshot_timestamp="2026-05-27T11:00:10Z",
        )

        self.assertIn("factor_closure_blocked", summary["blockers"])
        self.assertIn("same_tree_practical_closure_unproven", summary["blockers"])
        self.assertEqual(
            summary["blocker_details"]["same_tree_practical_closure_unproven"]["missing_practical_chain_stages"],
            [
                "provider_data",
                "pre_bayes",
                "bbn_workflow",
                "path_ranker",
                "execution_tree",
                "feedback_update",
                "policy_training",
            ],
        )

    def test_summarize_snapshot_allows_surface_green_with_validated_practical_closure_packet(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": True,
                "quickstart_surface": "pass",
            },
            {
                "status": "pass",
                "promotion_allowed_true": 0,
                "trade_usable_true": 0,
                "same_tree_practical_closure": {
                    "status": "pass",
                    "promotion_allowed": True,
                    "trade_usable": True,
                    "provider_execution_feedback_chain": "pass",
                    "evidence_packet": "same_tree_practical_closure.json",
                    "evidence_packet_validated": True,
                },
            },
            {
                "status": "pass",
            },
            snapshot_timestamp="2026-05-27T11:00:10Z",
        )

        self.assertEqual(summary["status"], "surface_green_manual_end_to_end_proof_required")
        self.assertTrue(summary["surface_green"])
        self.assertFalse(summary["completion_proven"])
        self.assertNotIn("same_tree_practical_closure_unproven", summary["blockers"])
        self.assertNotIn("same_tree_practical_closure_packet", summary["manual_requirements_remaining"])
        self.assertIn("truthful_completion_commit", summary["manual_requirements_remaining"])

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
        self.assertNotIn("factor_closure_blocked", summary["blockers"])
        self.assertNotIn(
            {
                "surface": "factor_closure",
                "reason": "practical_closure_blocked",
                "action": "no claim terminalization blockers found",
            },
            summary["prioritized_next_actions"],
        )
        self.assertIn(
            {
                "surface": "factor_closure",
                "reason": "same_tree_practical_closure_unproven",
                "action": "produce or locate a validated same_tree_practical_closure packet; do not use raw promotion_allowed_true/trade_usable_true claim counters as proof",
            },
            summary["prioritized_next_actions"],
        )

    def test_build_snapshot_blocks_on_untracked_practical_admission_source_debt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 0},
                    "report": {
                        "timestamp_utc": "2026-05-28T11:00:00Z",
                        "summary": {
                            "status": "pass",
                            "completion_ready": True,
                            "evidence_level": "full_enabled_gate_coverage",
                            "unresolved": [],
                            "skipped_gates": [],
                            "next_action": "done-definition gates have full enabled coverage",
                        },
                        "gates": [
                            {"id": "quickstart_surface", "status": "pass"},
                            {
                                "id": "practical_admission_source_surface",
                                "status": "pass",
                                "details": {
                                    "tracked_violation_count": 0,
                                    "untracked_violation_count": 3,
                                    "untracked_violating_files": 2,
                                    "debt_manifest_file": str(output_dir / "child-debt.json"),
                                    "sample_violations": [
                                        {
                                            "file": "support/docs/experiments/actionable-regime-confidence/scripts/run_untracked_bad_v1.py",
                                            "violation": "practical_flag_without_extension_complete_guard",
                                        }
                                    ],
                                },
                            },
                        ],
                    },
                    "output_path": output_dir / "done_definition_audit.compact.json",
                },
                "factor_closure": {
                    "command": {"argv": ["factor"], "returncode": 0},
                    "report": {
                        "generated_at": "2026-05-28T11:00:01+00:00",
                        "summary": {
                            "status": "pass",
                            "active_claims": 0,
                            "invalid_active_claims": 0,
                            "live_factor_processes": 0,
                            "blocking_reasons": [],
                            "promotion_allowed_true": 1,
                            "trade_usable_true": 1,
                            "next_action": "no claim terminalization blockers found",
                        },
                        "attention_claim_count": 0,
                        "attention_live_process_count": 0,
                        "attention_groups": {"by_owner": {}},
                    },
                    "output_path": output_dir / "factor_claim_terminalization_audit.compact.json",
                },
                "release_readiness": {
                    "command": {"argv": ["release"], "returncode": 0},
                    "report": {
                        "timestamp_utc": "2026-05-28T11:00:02Z",
                        "summary": {
                            "status": "pass",
                            "unresolved": [],
                            "pass_count": 3,
                            "fail_count": 0,
                            "skip_count": 0,
                        },
                    },
                    "output_path": output_dir / "release_readiness_audit.compact.json",
                },
            }
            (output_dir / "child-debt.json").write_text(
                json.dumps(
                    {
                        "schema_version": "practical-admission-source-debt/v1",
                        "summary": {"untracked_violation_count": 3},
                        "untracked_violations": [{"file": "run_untracked_bad_v1.py"}],
                    }
                ),
                encoding="utf-8",
            )

            snapshot = build_snapshot(
                audit_results,
                run_all_heavy=True,
                check_remotes=True,
                output_dir=output_dir,
            )
            staged_manifest_exists = (output_dir / "practical_admission_source_debt_manifest.json").exists()

        summary = snapshot["summary"]
        self.assertEqual(summary["status"], "not_complete")
        self.assertIn("practical_admission_source_debt", summary["blockers"])
        self.assertEqual(
            summary["blocker_details"]["practical_admission_source_debt"],
            {
                "tracked_violation_count": 0,
                "tracked_violating_files": None,
                "untracked_violation_count": 3,
                "untracked_violating_files": 2,
                "violation_count": None,
                "violating_files": None,
                "debt_manifest_file": "practical_admission_source_debt_manifest.json",
            },
        )
        self.assertIn(
            {
                "surface": "done_definition",
                "reason": "practical_admission_source_debt",
                "action": "retire, quarantine, or track unsafe untracked practical-admission wrappers before objective closure",
            },
            summary["prioritized_next_actions"],
        )
        self.assertEqual(
            snapshot["audits"]["done_definition"]["surface"]["practical_admission_source_surface"]["untracked_violation_count"],
            3,
        )
        self.assertEqual(
            snapshot["evidence_files"]["practical_admission_source_debt_manifest"],
            "practical_admission_source_debt_manifest.json",
        )
        self.assertTrue(staged_manifest_exists)

    def test_build_snapshot_blocks_on_untracked_await_launch_source_debt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 0},
                    "report": {
                        "timestamp_utc": "2026-05-29T00:55:00Z",
                        "summary": {
                            "status": "pass",
                            "completion_ready": True,
                            "evidence_level": "full_enabled_gate_coverage",
                            "unresolved": [],
                            "skipped_gates": [],
                            "next_action": "done-definition gates have full enabled coverage",
                        },
                        "gates": [
                            {"id": "quickstart_surface", "status": "pass"},
                            {
                                "id": "await_launch_source_surface",
                                "status": "pass",
                                "details": {
                                    "tracked_violation_count": 0,
                                    "untracked_violation_count": 2,
                                    "untracked_violating_files": 2,
                                    "sample_violations": [
                                        {
                                            "file": "support/docs/experiments/actionable-regime-confidence/scripts/run_tomac_bad_await_launch_v1.py",
                                            "violation": "await_launch_active_claim_guard_missing",
                                        }
                                    ],
                                },
                            },
                        ],
                    },
                    "output_path": output_dir / "done_definition_audit.compact.json",
                },
                "factor_closure": {
                    "command": {"argv": ["factor"], "returncode": 0},
                    "report": {
                        "generated_at": "2026-05-29T00:55:01+00:00",
                        "summary": {
                            "status": "pass",
                            "active_claims": 0,
                            "invalid_active_claims": 0,
                            "live_factor_processes": 0,
                            "blocking_reasons": [],
                            "promotion_allowed_true": 1,
                            "trade_usable_true": 1,
                            "next_action": "no claim terminalization blockers found",
                        },
                        "attention_claim_count": 0,
                        "attention_live_process_count": 0,
                        "attention_groups": {"by_owner": {}},
                    },
                    "output_path": output_dir / "factor_claim_terminalization_audit.compact.json",
                },
                "release_readiness": {
                    "command": {"argv": ["release"], "returncode": 0},
                    "report": {
                        "timestamp_utc": "2026-05-29T00:55:02Z",
                        "summary": {"status": "pass", "unresolved": [], "pass_count": 3, "fail_count": 0, "skip_count": 0},
                    },
                    "output_path": output_dir / "release_readiness_audit.compact.json",
                },
            }

            snapshot = build_snapshot(
                audit_results,
                run_all_heavy=True,
                check_remotes=True,
                output_dir=output_dir,
            )

        summary = snapshot["summary"]
        self.assertEqual(summary["status"], "not_complete")
        self.assertIn("await_launch_source_debt", summary["blockers"])
        self.assertEqual(
            summary["blocker_details"]["await_launch_source_debt"],
            {
                "tracked_violation_count": 0,
                "tracked_violating_files": None,
                "untracked_violation_count": 2,
                "untracked_violating_files": 2,
                "violation_count": None,
                "violating_files": None,
            },
        )
        self.assertIn(
            {
                "surface": "done_definition",
                "reason": "await_launch_source_debt",
                "action": "retire, quarantine, or track await-launch wrappers that can launch with active/fresh claims present",
            },
            summary["prioritized_next_actions"],
        )
        self.assertEqual(
            snapshot["audits"]["done_definition"]["surface"]["await_launch_source_surface"]["untracked_violation_count"],
            2,
        )

    def test_build_snapshot_stages_await_launch_source_debt_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_manifest = output_dir / "child-await-launch-debt.json"
            source_manifest.write_text(
                json.dumps(
                    {
                        "schema_version": "await-launch-source-debt/v1",
                        "summary": {"untracked_violation_count": 2},
                        "untracked_violations": [{"file": "run_tomac_bad_await_launch_v1.py"}],
                    }
                ),
                encoding="utf-8",
            )
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 0},
                    "report": {
                        "timestamp_utc": "2026-05-29T01:00:00Z",
                        "summary": {
                            "status": "pass",
                            "completion_ready": True,
                            "evidence_level": "full_enabled_gate_coverage",
                            "unresolved": [],
                            "skipped_gates": [],
                            "next_action": "done-definition gates have full enabled coverage",
                        },
                        "gates": [
                            {"id": "quickstart_surface", "status": "pass"},
                            {
                                "id": "await_launch_source_surface",
                                "status": "pass",
                                "details": {
                                    "tracked_violation_count": 0,
                                    "untracked_violation_count": 2,
                                    "untracked_violating_files": 2,
                                    "debt_manifest_file": str(source_manifest),
                                    "quarantine": {
                                        "matched": True,
                                        "decision": "quarantined_untracked_await_launch_debt",
                                        "manifest_file": "support/docs/audits/await-launch-source-debt-quarantine.json",
                                    },
                                },
                            },
                        ],
                    },
                    "output_path": output_dir / "done_definition_audit.compact.json",
                },
                "factor_closure": {
                    "command": {"argv": ["factor"], "returncode": 0},
                    "report": {
                        "generated_at": "2026-05-29T01:00:01+00:00",
                        "summary": {
                            "status": "pass",
                            "active_claims": 0,
                            "invalid_active_claims": 0,
                            "live_factor_processes": 0,
                            "blocking_reasons": [],
                            "promotion_allowed_true": 1,
                            "trade_usable_true": 1,
                            "next_action": "no claim terminalization blockers found",
                        },
                        "attention_claim_count": 0,
                        "attention_live_process_count": 0,
                        "attention_groups": {"by_owner": {}},
                    },
                    "output_path": output_dir / "factor_claim_terminalization_audit.compact.json",
                },
                "release_readiness": {
                    "command": {"argv": ["release"], "returncode": 0},
                    "report": {
                        "timestamp_utc": "2026-05-29T01:00:02Z",
                        "summary": {"status": "pass", "unresolved": [], "pass_count": 3, "fail_count": 0, "skip_count": 0},
                    },
                    "output_path": output_dir / "release_readiness_audit.compact.json",
                },
            }

            snapshot = build_snapshot(
                audit_results,
                run_all_heavy=True,
                check_remotes=True,
                output_dir=output_dir,
            )
            staged_manifest_exists = (output_dir / "await_launch_source_debt_manifest.json").exists()

        self.assertTrue(staged_manifest_exists)
        self.assertEqual(
            snapshot["evidence_files"]["await_launch_source_debt_manifest"],
            "await_launch_source_debt_manifest.json",
        )
        self.assertEqual(
            snapshot["summary"]["blocker_details"]["quarantined_await_launch_source_debt"]["debt_manifest_file"],
            "await_launch_source_debt_manifest.json",
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

    def test_summarize_snapshot_treats_quarantined_untracked_source_debt_as_externalized(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": True,
                "quickstart_surface": "pass",
                "practical_admission_source_surface": {
                    "status": "pass",
                    "tracked_violation_count": 0,
                    "tracked_violating_files": 0,
                    "untracked_violation_count": 3,
                    "untracked_violating_files": 2,
                    "debt_manifest_file": "practical_admission_source_debt_manifest.json",
                    "quarantine": {
                        "matched": True,
                        "decision": "quarantined_untracked_wrapper_debt",
                        "manifest_file": "support/docs/audits/practical-admission-source-debt-quarantine.json",
                    },
                },
            },
            {
                "status": "pass",
                "promotion_allowed_true": 1,
                "trade_usable_true": 1,
            },
            {
                "status": "pass",
                "unresolved_next_actions": {},
            },
            snapshot_timestamp="2026-05-28T12:00:00Z",
        )

        self.assertNotIn("practical_admission_source_debt", summary["blockers"])
        self.assertEqual(
            summary["blocker_details"]["quarantined_practical_admission_source_debt"],
            {
                "tracked_violation_count": 0,
                "tracked_violating_files": 0,
                "untracked_violation_count": 3,
                "untracked_violating_files": 2,
                "violation_count": None,
                "violating_files": None,
                "debt_manifest_file": "practical_admission_source_debt_manifest.json",
                "quarantine_manifest_file": "support/docs/audits/practical-admission-source-debt-quarantine.json",
            },
        )
        self.assertNotIn(
            {
                "surface": "done_definition",
                "reason": "practical_admission_source_debt",
                "action": "retire, quarantine, or track unsafe untracked practical-admission wrappers before objective closure",
            },
            summary["prioritized_next_actions"],
        )

    def test_summarize_snapshot_treats_quarantined_fixed_bps_source_debt_as_externalized(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": True,
                "quickstart_surface": "pass",
                "fixed_bps_cost_model_source_surface": {
                    "status": "pass",
                    "tracked_violation_count": 0,
                    "tracked_violating_files": 0,
                    "untracked_violation_count": 5,
                    "untracked_violating_files": 3,
                    "debt_manifest_file": "fixed_bps_cost_model_source_debt_manifest.json",
                    "quarantine": {
                        "matched": True,
                        "decision": "quarantined_untracked_fixed_bps_cost_model_debt",
                        "manifest_file": "support/docs/audits/fixed-bps-cost-model-source-debt-quarantine.json",
                    },
                },
            },
            {
                "status": "pass",
                "promotion_allowed_true": 1,
                "trade_usable_true": 1,
            },
            {
                "status": "pass",
                "unresolved_next_actions": {},
            },
            snapshot_timestamp="2026-05-31T12:00:00Z",
        )

        self.assertNotIn("fixed_bps_cost_model_source_debt", summary["blockers"])
        self.assertEqual(
            summary["blocker_details"]["quarantined_fixed_bps_cost_model_source_debt"],
            {
                "tracked_violation_count": 0,
                "tracked_violating_files": 0,
                "untracked_violation_count": 5,
                "untracked_violating_files": 3,
                "violation_count": None,
                "violating_files": None,
                "debt_manifest_file": "fixed_bps_cost_model_source_debt_manifest.json",
                "quarantine_manifest_file": "support/docs/audits/fixed-bps-cost-model-source-debt-quarantine.json",
            },
        )
        self.assertNotIn(
            {
                "surface": "done_definition",
                "reason": "fixed_bps_cost_model_source_debt",
                "action": "retire, quarantine, or track fixed-bps cost-model source debt before objective closure",
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

    def test_summarize_snapshot_lists_missing_run_root_factor_actions(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": True,
                "quickstart_surface": "pass",
            },
            {
                "status": "needs_attention",
                "next_action": "restore or terminalize missing run roots",
                "attention_action_queue": {
                    "missing_run_root_claims": [
                        {
                            "claim_file": "missing-root.claim",
                            "age_minutes": 4,
                            "run_root_state": "missing",
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
                "reason": "missing_run_root_claim",
                "action": "restore run root for missing-root.claim or terminalize the claim with explicit evidence",
            },
            summary["prioritized_next_actions"],
        )

    def test_summarize_snapshot_includes_factor_closure_blocker_details(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": True,
                "quickstart_surface": "pass",
            },
            {
                "status": "needs_attention",
                "active_claims": 2,
                "coordination_only_active_claims": 1,
                "invalid_active_claims": 0,
                "live_factor_processes": 1,
                "blocking_reasons": ["active_claims", "live_factor_processes"],
                "promotion_allowed_true": 0,
                "trade_usable_true": 0,
                "attention_claim_count": 2,
                "attention_live_process_count": 1,
                "attention_by_owner": {"codex": 2},
                "attention_by_actionability": {
                    "live_runtime_owner": 1,
                    "wait_only_without_live_process": 1,
                },
                "attention_action_queue": {
                    "live_runtime_run_roots": [
                        {
                            "pid": 9126,
                            "run_root": "ict-engine-tomac-15y",
                            "exit_file_state": "none",
                            "command_excerpt": "python run_tomac.py --root /tmp/ict-engine-tomac-15y",
                        }
                    ],
                    "externalize_wait_only_claims": [
                        {
                            "claim_file": "wait.claim",
                            "stale_safe_takeover_candidate": False,
                        }
                    ],
                },
                "next_action": "wait for live factor processes to exit",
            },
            {
                "status": "pass",
                "unresolved_next_actions": {},
            },
            snapshot_timestamp="2026-05-27T11:00:10Z",
        )

        self.assertIn("factor_closure_blocked", summary["blockers"])
        self.assertEqual(
            summary["blocker_details"]["factor_closure_blocked"],
            {
                "status": "needs_attention",
                "active_claims": 2,
                "coordination_only_active_claims": 1,
                "invalid_active_claims": 0,
                "live_factor_processes": 1,
                "blocking_reasons": ["active_claims", "live_factor_processes"],
                "attention_claim_count": 2,
                "attention_live_process_count": 1,
                "attention_by_owner": {"codex": 2},
                "attention_by_actionability": {
                    "live_runtime_owner": 1,
                    "wait_only_without_live_process": 1,
                },
                "action_queue": {
                    "live_runtime_run_roots": [
                        {
                            "pid": 9126,
                            "run_root": "ict-engine-tomac-15y",
                            "exit_file_state": "none",
                            "command_excerpt": "python run_tomac.py --root /tmp/ict-engine-tomac-15y",
                        }
                    ],
                    "externalize_wait_only_claims": [
                        {
                            "claim_file": "wait.claim",
                            "stale_safe_takeover_candidate": False,
                        }
                    ],
                },
                "next_action": "wait for live factor processes to exit",
            },
        )

    def test_summarize_snapshot_includes_release_readiness_blocker_details(self) -> None:
        summary = summarize_snapshot(
            {
                "completion_ready": True,
                "quickstart_surface": "pass",
            },
            {
                "status": "pass",
                "same_tree_practical_closure": {
                    "status": "pass",
                    "promotion_allowed": True,
                    "trade_usable": True,
                    "provider_execution_feedback_chain": "pass",
                    "evidence_packet": "packet.json",
                    "evidence_packet_validated": True,
                },
            },
            {
                "head": "abc123",
                "report_timestamp": "2026-05-29T13:23:46Z",
                "status": "needs_fix",
                "unresolved": ["worktree_clean_for_release", "remote_readback"],
                "pass_count": 2,
                "fail_count": 2,
                "skip_count": 1,
                "skipped_remote_gates": [],
                "unresolved_next_actions": {
                    "worktree_clean_for_release": "commit or exclude a narrow source slice",
                    "remote_readback": "restore release mirror git/network/auth readback",
                },
                "remote_details": {
                    "enabled": True,
                    "failed_sides": ["release_mirror"],
                    "origin_status": "pass",
                    "release_mirror_status": "fail",
                    "next_action": "restore release mirror git/network/auth readback",
                },
            },
            snapshot_timestamp="2026-05-29T13:23:50Z",
        )

        self.assertIn("release_readiness_blocked", summary["blockers"])
        self.assertEqual(
            summary["blocker_details"]["release_readiness_blocked"],
            {
                "head": "abc123",
                "report_timestamp": "2026-05-29T13:23:46Z",
                "status": "needs_fix",
                "unresolved": ["worktree_clean_for_release", "remote_readback"],
                "pass_count": 2,
                "fail_count": 2,
                "skip_count": 1,
                "skipped_remote_gates": [],
                "unresolved_next_actions": {
                    "worktree_clean_for_release": "commit or exclude a narrow source slice",
                    "remote_readback": "restore release mirror git/network/auth readback",
                },
                "remote_details": {
                    "enabled": True,
                    "failed_sides": ["release_mirror"],
                    "origin_status": "pass",
                    "release_mirror_status": "fail",
                    "next_action": "restore release mirror git/network/auth readback",
                },
            },
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
                        "coordination_only_active_claims": 1,
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
            snapshot["audits"]["factor_closure"]["surface"]["coordination_only_active_claims"],
            1,
        )
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
                    "surface": "factor_closure",
                    "reason": "same_tree_practical_closure_unproven",
                    "action": "produce or locate a validated same_tree_practical_closure packet; do not use raw promotion_allowed_true/trade_usable_true claim counters as proof",
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

    def test_run_command_timeout_kills_child_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "grandchild-survived.txt"
            status = run_command(
                [
                    sys.executable,
                    "-c",
                    (
                        "import subprocess, sys, time; "
                        "subprocess.Popen([sys.executable, '-c', "
                        "'import pathlib, sys, time; time.sleep(1.5); pathlib.Path(sys.argv[1]).write_text(\"alive\")', "
                        "sys.argv[1]]); "
                        "time.sleep(5)"
                    ),
                    str(marker),
                ],
                cwd=SCRIPTS_ROOT,
                timeout=1,
            )

            import time

            time.sleep(2)

            self.assertEqual(status["error"], "timeout")
            self.assertFalse(marker.exists())

    def test_run_command_timeout_kills_descendant_process_groups(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "nested-session-survived.txt"
            status = run_command(
                [
                    sys.executable,
                    "-c",
                    (
                        "import subprocess, sys, time; "
                        "subprocess.Popen([sys.executable, '-c', "
                        "'import pathlib, sys, time; time.sleep(1.5); pathlib.Path(sys.argv[1]).write_text(\"alive\")', "
                        "sys.argv[1]], start_new_session=True); "
                        "time.sleep(5)"
                    ),
                    str(marker),
                ],
                cwd=SCRIPTS_ROOT,
                timeout=1,
            )

            import time

            time.sleep(2)

            self.assertEqual(status["error"], "timeout")
            self.assertFalse(marker.exists())

    def test_effective_timeout_seconds_defaults_higher_for_heavy_mode(self) -> None:
        self.assertEqual(effective_timeout_seconds(None, run_all_heavy=False), 300)
        self.assertEqual(effective_timeout_seconds(None, run_all_heavy=True), 300)
        self.assertEqual(effective_timeout_seconds(17, run_all_heavy=True), 17)

    def test_effective_done_child_timeout_keeps_source_scan_inside_parent_budget(self) -> None:
        self.assertEqual(effective_done_child_timeout_seconds(300), 240)
        self.assertEqual(effective_done_child_timeout_seconds(180), 120)
        self.assertEqual(effective_done_child_timeout_seconds(90), 30)
        self.assertEqual(effective_done_child_timeout_seconds(17), 17)

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

    def test_build_snapshot_preserves_practical_source_scanner_timeout_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 1},
                    "report": {
                        "timestamp_utc": "2026-05-29T03:00:00Z",
                        "summary": {
                            "status": "needs_fix",
                            "completion_ready": False,
                            "evidence_level": "blocked",
                            "unresolved": ["practical_admission_source_surface"],
                            "skipped_gates": [],
                            "next_action": "fix practical admission source scan before completion proof",
                        },
                        "gates": [
                            {"id": "quickstart_surface", "status": "pass"},
                            {
                                "id": "practical_admission_source_surface",
                                "status": "fail",
                                "details": {
                                    "scan_scope": "tracked_run_wrappers_plus_tracked_report_files",
                                    "candidate_wrapper_files": 1063,
                                    "scanned_files": 120,
                                    "tracked_scanned_files": 120,
                                    "untracked_scanned_files": 0,
                                    "violating_files": 0,
                                    "violation_count": 0,
                                    "tracked_violation_count": 0,
                                    "untracked_violation_count": 0,
                                    "violations_by_type": {},
                                    "scanner_error": "timeout",
                                    "scanner_timeout_seconds": 180,
                                    "scanner_returncode": None,
                                    "scanner_command": ["python3", "support/scripts/research/downstream_practical_admission_source_check.py"],
                                    "stderr": "source scan timed out",
                                },
                            },
                        ],
                    },
                    "output_path": output_dir / "done_definition_audit.compact.json",
                },
                "factor_closure": {
                    "command": {"argv": ["factor"], "returncode": 0},
                    "report": {
                        "generated_at": "2026-05-29T03:00:01+00:00",
                        "summary": {
                            "status": "needs_attention",
                            "active_claims": 0,
                            "invalid_active_claims": 0,
                            "live_factor_processes": 1,
                            "blocking_reasons": ["live_factor_processes"],
                            "promotion_allowed_true": 0,
                            "trade_usable_true": 0,
                            "next_action": "wait for live factor processes to exit",
                        },
                        "attention_claim_count": 0,
                        "attention_live_process_count": 1,
                        "attention_groups": {"by_owner": {}},
                    },
                    "output_path": output_dir / "factor_claim_terminalization_audit.compact.json",
                },
                "release_readiness": {
                    "command": {"argv": ["release"], "returncode": 1},
                    "report": {
                        "timestamp_utc": "2026-05-29T03:00:02Z",
                        "summary": {
                            "status": "needs_fix",
                            "unresolved": ["worktree_clean_for_release"],
                            "pass_count": 1,
                            "fail_count": 1,
                            "skip_count": 0,
                        },
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

        source_surface = snapshot["audits"]["done_definition"]["surface"]["practical_admission_source_surface"]
        self.assertEqual(source_surface["scan_scope"], "tracked_run_wrappers_plus_tracked_report_files")
        self.assertEqual(source_surface["candidate_wrapper_files"], 1063)
        self.assertEqual(source_surface["scanned_files"], 120)
        self.assertEqual(source_surface["tracked_scanned_files"], 120)
        self.assertEqual(source_surface["untracked_scanned_files"], 0)
        self.assertEqual(source_surface["scanner_error"], "timeout")
        self.assertEqual(source_surface["scanner_timeout_seconds"], 180)
        self.assertEqual(source_surface["scanner_returncode"], None)
        self.assertEqual(source_surface["scanner_command"][1], "support/scripts/research/downstream_practical_admission_source_check.py")
        self.assertEqual(source_surface["stderr"], "source scan timed out")
        self.assertIn("done_definition_not_completion_ready", snapshot["summary"]["blockers"])

    def test_build_snapshot_applies_valid_done_definition_proof_without_hiding_other_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            proof_path = output_dir / "heavy_done_definition.compact.json"
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 0},
                    "report": {
                        "head": "selected-source-head",
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
                    "head": "selected-source-head",
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
                        "head": "selected-source-head",
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
                        "head": "selected-source-head",
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

    def test_build_snapshot_rejects_done_definition_proof_for_different_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 0},
                    "report": {
                        "head": "current-selected-head",
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
                    "report": {"head": "current-selected-head", "summary": {"status": "pass", "unresolved": []}},
                    "output_path": output_dir / "release_readiness_audit.compact.json",
                },
            }

            snapshot = build_snapshot(
                audit_results,
                run_all_heavy=False,
                check_remotes=False,
                output_dir=output_dir,
                done_definition_proof={
                    "path": output_dir / "stale_done_definition.compact.json",
                    "report": {
                        "head": "older-heavy-proof-head",
                        "timestamp_utc": "2026-05-28T00:59:00Z",
                        "summary": {
                            "status": "pass",
                            "completion_ready": True,
                            "evidence_level": "full_enabled_gate_coverage",
                            "unresolved": [],
                            "skipped_gates": [],
                        },
                        "gates": [{"id": "quickstart_surface", "status": "pass"}],
                    },
                },
            )

        done_surface = snapshot["audits"]["done_definition"]["surface"]
        self.assertFalse(done_surface["proof_applied"])
        self.assertEqual(done_surface["proof_rejected_reason"], "proof_head_mismatch")
        self.assertIn("done_definition_not_completion_ready", snapshot["summary"]["blockers"])

    def test_build_snapshot_rejects_done_definition_proof_for_dirty_fingerprint_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 0},
                    "report": {
                        "head": "selected-source-head",
                        "tracked_worktree_fingerprint": "current-dirty-fingerprint",
                        "timestamp_utc": "2026-05-29T01:20:00Z",
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
                    "report": {"head": "selected-source-head", "summary": {"status": "pass", "unresolved": []}},
                    "output_path": output_dir / "release_readiness_audit.compact.json",
                },
            }

            snapshot = build_snapshot(
                audit_results,
                run_all_heavy=False,
                check_remotes=True,
                output_dir=output_dir,
                done_definition_proof={
                    "path": output_dir / "same_head_stale_tree.compact.json",
                    "report": {
                        "head": "selected-source-head",
                        "tracked_worktree_fingerprint": "old-dirty-fingerprint",
                        "timestamp_utc": "2026-05-29T01:19:00Z",
                        "summary": {
                            "status": "pass",
                            "completion_ready": True,
                            "evidence_level": "full_enabled_gate_coverage",
                            "unresolved": [],
                            "skipped_gates": [],
                        },
                        "gates": [{"id": "quickstart_surface", "status": "pass"}],
                    },
                },
            )

        done_surface = snapshot["audits"]["done_definition"]["surface"]
        self.assertFalse(done_surface["proof_applied"])
        self.assertEqual(done_surface["proof_rejected_reason"], "proof_worktree_fingerprint_mismatch")
        self.assertEqual(done_surface["proof_worktree_fingerprint"], "old-dirty-fingerprint")
        self.assertEqual(done_surface["tracked_worktree_fingerprint"], "current-dirty-fingerprint")
        self.assertIn("done_definition_not_completion_ready", snapshot["summary"]["blockers"])

    def test_build_snapshot_rejects_done_definition_proof_without_fingerprint_when_current_has_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 0},
                    "report": {
                        "head": "selected-source-head",
                        "tracked_worktree_fingerprint": "current-dirty-fingerprint",
                        "timestamp_utc": "2026-05-29T01:30:00Z",
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
                    "report": {"head": "selected-source-head", "summary": {"status": "pass", "unresolved": []}},
                    "output_path": output_dir / "release_readiness_audit.compact.json",
                },
            }

            snapshot = build_snapshot(
                audit_results,
                run_all_heavy=False,
                check_remotes=True,
                output_dir=output_dir,
                done_definition_proof={
                    "path": output_dir / "fingerprintless_heavy.compact.json",
                    "report": {
                        "head": "selected-source-head",
                        "timestamp_utc": "2026-05-29T01:29:00Z",
                        "summary": {
                            "status": "pass",
                            "completion_ready": True,
                            "evidence_level": "full_enabled_gate_coverage",
                            "unresolved": [],
                            "skipped_gates": [],
                        },
                        "gates": [{"id": "quickstart_surface", "status": "pass"}],
                    },
                },
            )

        done_surface = snapshot["audits"]["done_definition"]["surface"]
        self.assertFalse(done_surface["proof_applied"])
        self.assertEqual(done_surface["proof_rejected_reason"], "proof_worktree_fingerprint_missing")
        self.assertEqual(done_surface["tracked_worktree_fingerprint"], "current-dirty-fingerprint")
        self.assertIn("done_definition_not_completion_ready", snapshot["summary"]["blockers"])

    def test_build_snapshot_preserves_current_practical_source_surface_when_applying_done_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 0},
                    "report": {
                        "head": "selected-source-head",
                        "timestamp_utc": "2026-05-28T12:00:00Z",
                        "summary": {
                            "status": "pass",
                            "completion_ready": False,
                            "evidence_level": "partial_skipped_gates",
                            "unresolved": [],
                            "skipped_gates": ["cargo_test"],
                            "next_action": "rerun heavy gates",
                        },
                        "gates": [
                            {"id": "quickstart_surface", "status": "pass"},
                            {
                                "id": "practical_admission_source_surface",
                                "status": "pass",
                                "details": {
                                    "tracked_violation_count": 0,
                                    "tracked_violating_files": 0,
                                    "untracked_violation_count": 3,
                                    "untracked_violating_files": 2,
                                    "debt_manifest_file": str(output_dir / "child-debt.json"),
                                    "quarantine": {
                                        "matched": True,
                                        "decision": "quarantined_untracked_wrapper_debt",
                                        "manifest_file": "support/docs/audits/practical-admission-source-debt-quarantine.json",
                                    },
                                },
                            },
                        ],
                    },
                    "output_path": output_dir / "done_definition_audit.compact.json",
                },
                "factor_closure": {
                    "command": {"argv": ["factor"], "returncode": 0},
                    "report": {
                        "generated_at": "2026-05-28T12:00:01+00:00",
                        "summary": {
                            "status": "pass",
                            "active_claims": 0,
                            "invalid_active_claims": 0,
                            "live_factor_processes": 0,
                            "blocking_reasons": [],
                            "promotion_allowed_true": 1,
                            "trade_usable_true": 1,
                        },
                    },
                    "output_path": output_dir / "factor_claim_terminalization_audit.compact.json",
                },
                "release_readiness": {
                    "command": {"argv": ["release"], "returncode": 0},
                    "report": {
                        "timestamp_utc": "2026-05-28T12:00:02Z",
                        "summary": {"status": "pass", "unresolved": []},
                    },
                    "output_path": output_dir / "release_readiness_audit.compact.json",
                },
            }
            (output_dir / "child-debt.json").write_text(
                json.dumps({"schema_version": "practical-admission-source-debt/v1"}),
                encoding="utf-8",
            )

            snapshot = build_snapshot(
                audit_results,
                run_all_heavy=False,
                check_remotes=False,
                output_dir=output_dir,
                done_definition_proof={
                    "path": output_dir / "heavy_done_definition.compact.json",
                    "report": {
                        "head": "selected-source-head",
                        "timestamp_utc": "2026-05-28T11:59:00Z",
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
                },
            )

        done_surface = snapshot["audits"]["done_definition"]["surface"]
        self.assertTrue(done_surface["completion_ready"])
        self.assertTrue(done_surface["proof_applied"])
        self.assertEqual(
            done_surface["practical_admission_source_surface"]["quarantine"]["matched"],
            True,
        )
        self.assertNotIn("practical_admission_source_debt", snapshot["summary"]["blockers"])
        self.assertIn(
            "quarantined_practical_admission_source_debt",
            snapshot["summary"]["blocker_details"],
        )

    def test_build_snapshot_blocks_when_release_remote_checks_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 0},
                    "report": {
                        "timestamp_utc": "2026-05-28T13:00:00Z",
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
                    "output_path": output_dir / "done_definition_audit.compact.json",
                },
                "factor_closure": {
                    "command": {"argv": ["factor"], "returncode": 0},
                    "report": {
                        "generated_at": "2026-05-28T13:00:01+00:00",
                        "summary": {
                            "status": "pass",
                            "active_claims": 0,
                            "invalid_active_claims": 0,
                            "live_factor_processes": 0,
                            "blocking_reasons": [],
                            "promotion_allowed_true": 1,
                            "trade_usable_true": 1,
                            "next_action": "no claim terminalization blockers found",
                        },
                    },
                    "output_path": output_dir / "factor_claim_terminalization_audit.compact.json",
                },
                "release_readiness": {
                    "command": {"argv": ["release"], "returncode": 0},
                    "report": {
                        "timestamp_utc": "2026-05-28T13:00:02Z",
                        "summary": {
                            "status": "pass",
                            "unresolved": [],
                            "pass_count": 3,
                            "fail_count": 0,
                            "skip_count": 2,
                        },
                        "gates": [
                            {
                                "id": "remote_readback",
                                "status": "skip",
                                "details": {
                                    "enable_with": "--check-remotes",
                                    "reason": "network_check_not_enabled",
                                },
                            },
                            {
                                "id": "release_version_tag_available",
                                "status": "skip",
                                "details": {
                                    "enable_with": "--check-remotes",
                                    "reason": "network_check_not_enabled",
                                    "rule": "release tag availability must be checked against release mirror tags, not local tags",
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
                check_remotes=False,
                output_dir=output_dir,
            )

        self.assertEqual(snapshot["summary"]["status"], "not_complete")
        self.assertIn("release_remote_checks_not_run", snapshot["summary"]["blockers"])
        self.assertEqual(
            snapshot["summary"]["blocker_details"]["release_remote_checks_not_run"],
            {"skipped_gates": ["remote_readback", "release_version_tag_available"]},
        )
        self.assertEqual(
            snapshot["audits"]["release_readiness"]["surface"]["skipped_remote_gates"],
            ["remote_readback", "release_version_tag_available"],
        )
        self.assertIn(
            {
                "surface": "release_readiness",
                "reason": "release_remote_checks_not_run",
                "action": "rerun objective closure with --check-remotes before treating release readiness as closed",
            },
            snapshot["summary"]["prioritized_next_actions"],
        )

    def test_build_snapshot_does_not_call_tag_skip_remote_checks_not_run_when_remote_readback_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 0},
                    "report": {
                        "timestamp_utc": "2026-05-28T13:00:00Z",
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
                    "output_path": output_dir / "done_definition_audit.compact.json",
                },
                "factor_closure": {
                    "command": {"argv": ["factor"], "returncode": 0},
                    "report": {
                        "generated_at": "2026-05-28T13:00:01+00:00",
                        "summary": {
                            "status": "pass",
                            "active_claims": 0,
                            "invalid_active_claims": 0,
                            "live_factor_processes": 0,
                            "blocking_reasons": [],
                            "promotion_allowed_true": 1,
                            "trade_usable_true": 1,
                        },
                    },
                    "output_path": output_dir / "factor_claim_terminalization_audit.compact.json",
                },
                "release_readiness": {
                    "command": {"argv": ["release"], "returncode": 1},
                    "report": {
                        "timestamp_utc": "2026-05-28T13:00:02Z",
                        "summary": {
                            "status": "needs_fix",
                            "unresolved": ["remote_readback"],
                            "pass_count": 3,
                            "fail_count": 1,
                            "skip_count": 1,
                        },
                        "gates": [
                            {
                                "id": "remote_readback",
                                "status": "fail",
                                "details": {
                                    "next_action": "restore release mirror git/network/auth readback, or rerun from a network that can reach the release mirror, then rerun release readiness audit with --check-remotes",
                                },
                            },
                            {
                                "id": "release_version_tag_available",
                                "status": "skip",
                                "details": {
                                    "enable_with": "--check-remotes",
                                    "reason": "release_mirror_tags_unavailable",
                                    "blocked_by_gate": "remote_readback",
                                    "next_action": "resolve remote_readback, then rerun release readiness audit with --check-remotes",
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

        self.assertIn("release_readiness_blocked", snapshot["summary"]["blockers"])
        self.assertNotIn("release_remote_checks_not_run", snapshot["summary"]["blockers"])
        self.assertEqual(
            snapshot["audits"]["release_readiness"]["surface"]["skipped_remote_gates"],
            [],
        )

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

    def test_build_snapshot_applies_clean_release_readiness_proof_without_hiding_origin_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            proof_path = output_dir / "clean_export_release.compact.json"
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 0},
                    "report": {
                        "timestamp_utc": "2026-05-28T14:00:00Z",
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
                    "command": {"argv": ["factor"], "returncode": 0},
                    "report": {
                        "generated_at": "2026-05-28T14:00:01+00:00",
                        "summary": {
                            "status": "pass",
                            "active_claims": 0,
                            "invalid_active_claims": 0,
                            "live_factor_processes": 0,
                            "blocking_reasons": [],
                            "promotion_allowed_true": 1,
                            "trade_usable_true": 1,
                        },
                    },
                    "output_path": output_dir / "factor_claim_terminalization_audit.compact.json",
                },
                "release_readiness": {
                    "command": {"argv": ["release"], "returncode": 1},
                    "report": {
                        "timestamp_utc": "2026-05-28T14:00:02Z",
                        "remote_details": {"enabled": True},
                        "summary": {
                            "status": "needs_fix",
                            "unresolved": ["worktree_clean_for_release", "source_origin_matches_selected_source"],
                            "pass_count": 7,
                            "fail_count": 2,
                            "skip_count": 0,
                        },
                        "gates": [
                            {
                                "id": "worktree_clean_for_release",
                                "status": "fail",
                                "details": {"next_action": "commit or exclude a narrow source slice"},
                            },
                            {
                                "id": "source_origin_matches_selected_source",
                                "status": "fail",
                                "details": {"next_action": "sync local source with origin/main before selecting a release export commit"},
                            },
                        ],
                    },
                    "output_path": output_dir / "release_readiness_audit.compact.json",
                },
            }
            release_readiness_proof = {
                "path": proof_path,
                "report": {
                    "timestamp_utc": "2026-05-28T13:59:00Z",
                    "remote_details": {"enabled": True},
                    "summary": {
                        "status": "needs_fix",
                        "unresolved": ["source_origin_matches_selected_source"],
                        "pass_count": 8,
                        "fail_count": 1,
                        "skip_count": 0,
                    },
                    "gates": [
                        {"id": "worktree_clean_for_release", "status": "pass", "details": {}},
                        {
                            "id": "source_origin_matches_selected_source",
                            "status": "fail",
                            "details": {"next_action": "sync local source with origin/main before selecting a release export commit"},
                        },
                    ],
                },
            }

            snapshot = build_snapshot(
                audit_results,
                run_all_heavy=False,
                check_remotes=True,
                output_dir=output_dir,
                release_readiness_proof=release_readiness_proof,
            )

        release_surface = snapshot["audits"]["release_readiness"]["surface"]
        self.assertTrue(release_surface["proof_applied"])
        self.assertEqual(release_surface["proof_source"], "clean_export_release.compact.json")
        self.assertEqual(release_surface["unresolved"], ["source_origin_matches_selected_source"])
        self.assertIn("release_readiness_blocked", snapshot["summary"]["blockers"])
        self.assertNotIn(
            {
                "surface": "release_readiness",
                "reason": "worktree_clean_for_release",
                "action": "commit or exclude a narrow source slice",
            },
            snapshot["summary"]["prioritized_next_actions"],
        )
        self.assertIn(
            {
                "surface": "release_readiness",
                "reason": "source_origin_matches_selected_source",
                "action": "sync local source with origin/main before selecting a release export commit",
            },
            snapshot["summary"]["prioritized_next_actions"],
        )
        self.assertEqual(snapshot["evidence_files"]["release_readiness_proof"], "clean_export_release.compact.json")

    def test_build_snapshot_rejects_release_readiness_proof_without_remote_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 0},
                    "report": {
                        "summary": {"status": "pass", "completion_ready": True, "skipped_gates": []},
                        "gates": [{"id": "quickstart_surface", "status": "pass"}],
                    },
                    "output_path": output_dir / "done_definition_audit.compact.json",
                },
                "factor_closure": {
                    "command": {"argv": ["factor"], "returncode": 0},
                    "report": {"summary": {"status": "pass", "promotion_allowed_true": 1, "trade_usable_true": 1}},
                    "output_path": output_dir / "factor_claim_terminalization_audit.compact.json",
                },
                "release_readiness": {
                    "command": {"argv": ["release"], "returncode": 1},
                    "report": {
                        "summary": {"status": "needs_fix", "unresolved": ["worktree_clean_for_release"], "skip_count": 0},
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

            snapshot = build_snapshot(
                audit_results,
                run_all_heavy=False,
                check_remotes=True,
                output_dir=output_dir,
                release_readiness_proof={
                    "path": output_dir / "partial_release.compact.json",
                    "report": {
                        "remote_details": {"enabled": False},
                        "summary": {"status": "pass", "unresolved": [], "skip_count": 2},
                        "gates": [{"id": "worktree_clean_for_release", "status": "pass"}],
                    },
                },
            )

        release_surface = snapshot["audits"]["release_readiness"]["surface"]
        self.assertFalse(release_surface["proof_applied"])
        self.assertEqual(release_surface["proof_rejected_reason"], "proof_remote_checks_not_enabled")
        self.assertEqual(release_surface["unresolved"], ["worktree_clean_for_release"])

    def test_build_snapshot_rejects_release_readiness_proof_for_different_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 0},
                    "report": {
                        "summary": {"status": "pass", "completion_ready": True, "skipped_gates": []},
                        "gates": [{"id": "quickstart_surface", "status": "pass"}],
                    },
                    "output_path": output_dir / "done_definition_audit.compact.json",
                },
                "factor_closure": {
                    "command": {"argv": ["factor"], "returncode": 0},
                    "report": {"summary": {"status": "pass", "promotion_allowed_true": 1, "trade_usable_true": 1}},
                    "output_path": output_dir / "factor_claim_terminalization_audit.compact.json",
                },
                "release_readiness": {
                    "command": {"argv": ["release"], "returncode": 1},
                    "report": {
                        "head": "current-selected-head",
                        "remote_details": {"enabled": True},
                        "summary": {
                            "status": "needs_fix",
                            "unresolved": ["worktree_clean_for_release", "source_origin_matches_selected_source"],
                            "skip_count": 0,
                        },
                        "gates": [
                            {
                                "id": "worktree_clean_for_release",
                                "status": "fail",
                                "details": {"next_action": "commit or exclude a narrow source slice"},
                            },
                            {
                                "id": "source_origin_matches_selected_source",
                                "status": "fail",
                                "details": {"next_action": "push selected source commit or publish from a clean export at the selected commit"},
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
                release_readiness_proof={
                    "path": output_dir / "stale_release.compact.json",
                    "report": {
                        "head": "older-clean-export-head",
                        "remote_details": {"enabled": True},
                        "summary": {
                            "status": "needs_fix",
                            "unresolved": ["source_origin_matches_selected_source"],
                            "skip_count": 0,
                        },
                        "gates": [
                            {"id": "worktree_clean_for_release", "status": "pass"},
                            {
                                "id": "source_origin_matches_selected_source",
                                "status": "fail",
                                "details": {"next_action": "push selected source commit or publish from a clean export at the selected commit"},
                            },
                        ],
                    },
                },
            )

        release_surface = snapshot["audits"]["release_readiness"]["surface"]
        self.assertFalse(release_surface["proof_applied"])
        self.assertEqual(release_surface["proof_rejected_reason"], "proof_head_mismatch")
        self.assertEqual(
            release_surface["unresolved"],
            ["worktree_clean_for_release", "source_origin_matches_selected_source"],
        )

    def test_build_snapshot_rejects_release_readiness_proof_when_snapshot_remote_checks_are_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            audit_results = {
                "done_definition": {
                    "command": {"argv": ["done"], "returncode": 0},
                    "report": {
                        "summary": {"status": "pass", "completion_ready": True, "skipped_gates": []},
                        "gates": [{"id": "quickstart_surface", "status": "pass"}],
                    },
                    "output_path": output_dir / "done_definition_audit.compact.json",
                },
                "factor_closure": {
                    "command": {"argv": ["factor"], "returncode": 0},
                    "report": {"summary": {"status": "pass", "promotion_allowed_true": 1, "trade_usable_true": 1}},
                    "output_path": output_dir / "factor_claim_terminalization_audit.compact.json",
                },
                "release_readiness": {
                    "command": {"argv": ["release"], "returncode": 0},
                    "report": {
                        "remote_details": {"enabled": False},
                        "summary": {"status": "pass", "unresolved": [], "skip_count": 2},
                        "gates": [
                            {
                                "id": "remote_readback",
                                "status": "skip",
                                "details": {"enable_with": "--check-remotes", "reason": "network_check_not_enabled"},
                            }
                        ],
                    },
                    "output_path": output_dir / "release_readiness_audit.compact.json",
                },
            }

            snapshot = build_snapshot(
                audit_results,
                run_all_heavy=False,
                check_remotes=False,
                output_dir=output_dir,
                release_readiness_proof={
                    "path": output_dir / "clean_release.compact.json",
                    "report": {
                        "remote_details": {"enabled": True},
                        "summary": {"status": "pass", "unresolved": [], "skip_count": 0},
                        "gates": [{"id": "worktree_clean_for_release", "status": "pass"}],
                    },
                },
            )

        release_surface = snapshot["audits"]["release_readiness"]["surface"]
        self.assertFalse(release_surface["proof_applied"])
        self.assertEqual(release_surface["proof_rejected_reason"], "snapshot_remote_checks_not_enabled")
        self.assertIn("release_remote_checks_not_run", snapshot["summary"]["blockers"])

    def test_stage_release_readiness_proof_copies_external_proof_into_packet(self) -> None:
        with tempfile.TemporaryDirectory() as src_tmp, tempfile.TemporaryDirectory() as packet_tmp:
            source_path = Path(src_tmp) / "release.json"
            output_dir = Path(packet_tmp)
            source_report = {"remote_details": {"enabled": True}, "summary": {"status": "pass", "skip_count": 0}}
            source_path.write_text(json.dumps(source_report), encoding="utf-8")

            staged = stage_release_readiness_proof(
                {"path": source_path, "report": source_report},
                output_dir=output_dir,
            )

            self.assertEqual(staged["path"], output_dir / "release_readiness_proof.compact.json")
            self.assertEqual(staged["report"], source_report)
            self.assertEqual(
                json.loads((output_dir / "release_readiness_proof.compact.json").read_text(encoding="utf-8")),
                source_report,
            )
