#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from release_readiness_audit import (  # noqa: E402
    build_public_remote_probe_plan,
    evaluate_docs_freshness,
    evaluate_remote_readback,
    evaluate_source_origin_alignment,
    evaluate_worktree_clean,
    evaluate_version_tag,
    evaluate_version_tag_unknown,
    format_report,
    parse_cargo_metadata,
    parse_ls_remote,
    parse_origin_divergence,
    summarize,
)


class ReleaseReadinessAuditTest(unittest.TestCase):
    def test_build_public_remote_probe_plan_converts_github_ssh_origin_to_https_fallback(self) -> None:
        plan = build_public_remote_probe_plan(
            "origin",
            "git@github.com:Undermybelt/givenup-ict-engine.git",
        )

        self.assertEqual(plan["remote_name"], "origin")
        self.assertEqual(plan["declared_url"], "git@github.com:Undermybelt/givenup-ict-engine.git")
        self.assertEqual(plan["default_target"], "origin")
        self.assertEqual(
            plan["fallback_public_url"],
            "https://github.com/Undermybelt/givenup-ict-engine.git",
        )
        self.assertEqual(plan["fallback_transport"], "https_public_no_rewrite")

    def test_build_public_remote_probe_plan_marks_https_github_url_for_no_rewrite_probe(self) -> None:
        plan = build_public_remote_probe_plan(
            "release_mirror",
            "https://github.com/Undermybelt/ict-engine-release.git",
        )

        self.assertEqual(
            plan["fallback_public_url"],
            "https://github.com/Undermybelt/ict-engine-release.git",
        )
        self.assertEqual(plan["fallback_transport"], "https_public_no_rewrite")
        self.assertEqual(
            plan["fallback_env_overrides"],
            {
                "GIT_CONFIG_GLOBAL": "/dev/null",
                "GIT_CONFIG_NOSYSTEM": "1",
            },
        )

    def test_parse_cargo_metadata_reads_release_fields(self) -> None:
        metadata = parse_cargo_metadata(
            """
[package]
name = "ict-engine"
version = "0.1.3"
license = "PolyForm-Noncommercial-1.0.0"
repository = "https://github.com/Undermybelt/ict-engine-release"
publish = false
"""
        )
        self.assertEqual(metadata["version"], "0.1.3")
        self.assertEqual(metadata["license"], "PolyForm-Noncommercial-1.0.0")
        self.assertEqual(metadata["repository"], "https://github.com/Undermybelt/ict-engine-release")
        self.assertIs(metadata["publish"], False)

    def test_parse_ls_remote_classifies_heads_and_tags(self) -> None:
        parsed = parse_ls_remote(
            """
abc123\trefs/heads/main
def456\trefs/tags/v0.1.4
ghi789\trefs/tags/v0.1.4^{}
"""
        )
        self.assertEqual(parsed["heads"]["main"], "abc123")
        self.assertEqual(parsed["tags"]["v0.1.4"], "def456")
        self.assertNotIn("v0.1.4^{}", parsed["tags"])

    def test_parse_origin_divergence_maps_left_right_counts(self) -> None:
        parsed = parse_origin_divergence("1\t2\n", ref="origin/main")
        self.assertEqual(parsed, {"ahead": 2, "behind": 1, "ref": "origin/main"})

    def test_worktree_clean_gate_summarizes_dirty_status_classes(self) -> None:
        gate = evaluate_worktree_clean(
            """
 M src/main.rs
M  Cargo.toml
MM src/lib.rs
 D old.txt
R  old.rs -> new.rs
?? scratch.py
"""
        )

        details = gate["details"]
        self.assertEqual(gate["status"], "fail")
        self.assertEqual(details["status_entries"], 6)
        self.assertEqual(details["tracked_entries"], 5)
        self.assertEqual(details["untracked_entries"], 1)
        self.assertEqual(details["staged_entries"], 3)
        self.assertEqual(details["unstaged_entries"], 3)
        self.assertEqual(details["modified_entries"], 3)
        self.assertEqual(details["deleted_entries"], 1)
        self.assertEqual(details["renamed_entries"], 1)
        self.assertEqual(details["status_counts"]["??"], 1)
        self.assertIn("clean sanitized export", details["next_action"])

    def test_version_tag_fails_when_release_mirror_already_has_version(self) -> None:
        gate = evaluate_version_tag("0.1.4", {"v0.1.3", "v0.1.4"}, version_source_path="Cargo.toml")
        self.assertEqual(gate["status"], "fail")
        self.assertIn("v0.1.4", gate["details"]["blocking_tags"])
        self.assertEqual(gate["details"]["version_source_path"], "Cargo.toml")
        self.assertEqual(gate["details"]["suggested_next_patch_version"], "0.1.5")
        self.assertEqual(gate["details"]["suggested_next_patch_tag"], "v0.1.5")
        self.assertIn("Cargo.toml", gate["details"]["next_action"])
        self.assertIn("0.1.5", gate["details"]["next_action"])

    def test_version_tag_suggestion_skips_multiple_existing_patch_tags(self) -> None:
        gate = evaluate_version_tag("0.1.3", {"v0.1.3", "v0.1.4", "v0.1.5"})
        self.assertEqual(gate["status"], "fail")
        self.assertEqual(gate["details"]["suggested_next_patch_version"], "0.1.6")
        self.assertEqual(gate["details"]["suggested_next_patch_tag"], "v0.1.6")

    def test_version_tag_is_skipped_without_release_mirror_tags(self) -> None:
        gate = evaluate_version_tag_unknown("network_check_not_enabled")
        self.assertEqual(gate["id"], "release_version_tag_available")
        self.assertEqual(gate["status"], "skip")
        self.assertEqual(gate["details"]["reason"], "network_check_not_enabled")
        self.assertEqual(gate["details"]["enable_with"], "--check-remotes")

    def test_version_tag_skip_points_to_remote_readback_when_mirror_tags_unavailable(self) -> None:
        gate = evaluate_version_tag_unknown("release_mirror_tags_unavailable")

        self.assertEqual(gate["id"], "release_version_tag_available")
        self.assertEqual(gate["status"], "skip")
        self.assertEqual(gate["details"]["blocked_by_gate"], "remote_readback")
        self.assertIn("remote_readback", gate["details"]["next_action"])

    def test_remote_readback_failure_names_blocked_tag_gate(self) -> None:
        gate = evaluate_remote_readback(
            origin_state="pass",
            origin_details={"returncode": 0, "stdout": "abc\trefs/heads/main\n", "stderr": ""},
            mirror_state="fail",
            mirror_details={
                "returncode": 128,
                "stdout": "",
                "stderr": "Connection closed by 198.18.1.114 port 22\nfatal: Could not read from remote repository.\n",
            },
        )

        self.assertEqual(gate["id"], "remote_readback")
        self.assertEqual(gate["status"], "fail")
        self.assertEqual(gate["details"]["blocked_gate"], "release_version_tag_available")
        self.assertIn("release mirror", gate["details"]["next_action"])
        self.assertIn("--check-remotes", gate["details"]["next_action"])
        self.assertEqual(gate["details"]["origin_status"], "pass")
        self.assertEqual(gate["details"]["release_mirror_status"], "fail")

    def test_remote_readback_failure_points_to_origin_when_only_origin_fails(self) -> None:
        gate = evaluate_remote_readback(
            origin_state="fail",
            origin_details={
                "returncode": 128,
                "stdout": "",
                "stderr": "fatal: unable to access origin\n",
                "remote_name": "origin",
            },
            mirror_state="pass",
            mirror_details={
                "returncode": 0,
                "stdout": "mirror-head\trefs/heads/main\n",
                "stderr": "",
                "remote_name": "release_mirror",
            },
        )

        self.assertEqual(gate["status"], "fail")
        self.assertEqual(gate["details"]["origin_status"], "fail")
        self.assertEqual(gate["details"]["release_mirror_status"], "pass")
        self.assertIn("source origin", gate["details"]["next_action"])
        self.assertNotIn("restore release mirror git/network/auth readback", gate["details"]["next_action"])
        self.assertIn("--check-remotes", gate["details"]["next_action"])

    def test_remote_readback_failure_keeps_public_fallback_diagnostics(self) -> None:
        gate = evaluate_remote_readback(
            origin_state="fail",
            origin_details={
                "argv": ["git", "ls-remote", "--heads", "--tags", "origin"],
                "returncode": 128,
                "stdout": "",
                "stderr": "Connection closed by 198.18.0.190 port 22\nfatal: Could not read from remote repository.\n",
                "remote_name": "origin",
                "declared_url": "git@github.com:Undermybelt/givenup-ict-engine.git",
                "fallback_public_probe": {
                    "target": "https://github.com/Undermybelt/givenup-ict-engine.git",
                    "transport": "https_public_no_rewrite",
                    "result": {
                        "argv": [
                            "git",
                            "ls-remote",
                            "--heads",
                            "--tags",
                            "https://github.com/Undermybelt/givenup-ict-engine.git",
                        ],
                        "returncode": 128,
                        "stdout": "",
                        "stderr": "fatal: unable to access 'https://github.com/Undermybelt/givenup-ict-engine.git/': LibreSSL SSL_connect: SSL_ERROR_SYSCALL in connection to github.com:443 ",
                    },
                },
            },
            mirror_state="fail",
            mirror_details={
                "returncode": 128,
                "stdout": "",
                "stderr": "fatal: unable to access 'https://github.com/Undermybelt/ict-engine-release.git/': LibreSSL SSL_connect: SSL_ERROR_SYSCALL in connection to github.com:443 ",
            },
        )

        self.assertEqual(gate["status"], "fail")
        self.assertEqual(
            gate["details"]["origin"]["fallback_public_probe"]["target"],
            "https://github.com/Undermybelt/givenup-ict-engine.git",
        )
        self.assertEqual(
            gate["details"]["origin"]["fallback_public_probe"]["transport"],
            "https_public_no_rewrite",
        )
        self.assertIn("restore release mirror git/network/auth readback", gate["details"]["next_action"])

    def test_remote_readback_failure_surfaces_release_mirror_fallback_diagnostics(self) -> None:
        gate = evaluate_remote_readback(
            origin_state="pass",
            origin_details={"returncode": 0, "stdout": "abc\trefs/heads/main\n", "stderr": ""},
            mirror_state="fail",
            mirror_details={
                "argv": ["git", "ls-remote", "--heads", "--tags", "https://github.com/Undermybelt/ict-engine-release.git"],
                "returncode": 128,
                "stdout": "",
                "stderr": "Connection closed by 198.18.0.190 port 22\n",
                "fallback_public_probe": {
                    "target": "https://github.com/Undermybelt/ict-engine-release.git",
                    "transport": "https_public_no_rewrite",
                    "result": {"returncode": 128, "stderr": "Connection closed by 198.18.0.190 port 22\n"},
                },
            },
        )

        mirror = gate["details"]["release_mirror"]
        self.assertEqual(
            mirror["fallback_public_probe"]["target"],
            "https://github.com/Undermybelt/ict-engine-release.git",
        )
        self.assertEqual(mirror["fallback_public_probe"]["transport"], "https_public_no_rewrite")

    def test_remote_readback_uses_successful_public_fallback_as_effective_readback(self) -> None:
        gate = evaluate_remote_readback(
            origin_state="fail",
            origin_details={
                "argv": ["git", "ls-remote", "--heads", "--tags", "origin"],
                "returncode": 128,
                "stdout": "",
                "stderr": "Connection closed by 198.18.0.26 port 22\n",
                "remote_name": "origin",
                "declared_url": "git@github.com:Undermybelt/givenup-ict-engine.git",
                "fallback_public_probe": {
                    "target": "https://github.com/Undermybelt/givenup-ict-engine.git",
                    "transport": "https_public_no_rewrite",
                    "result": {
                        "argv": [
                            "git",
                            "ls-remote",
                            "--heads",
                            "--tags",
                            "https://github.com/Undermybelt/givenup-ict-engine.git",
                        ],
                        "returncode": 0,
                        "stdout": "source-head\trefs/heads/main\n",
                        "stderr": "",
                    },
                },
            },
            mirror_state="pass",
            mirror_details={
                "argv": ["git", "ls-remote", "--heads", "--tags", "https://github.com/Undermybelt/ict-engine-release.git"],
                "returncode": 0,
                "stdout": "mirror-head\trefs/heads/main\nv0\trefs/tags/v0.1.7\n",
                "stderr": "",
                "remote_name": "release_mirror",
                "declared_url": "https://github.com/Undermybelt/ict-engine-release.git",
            },
        )

        self.assertEqual(gate["status"], "pass")
        self.assertEqual(gate["details"]["origin_status"], "pass_via_fallback")
        self.assertEqual(gate["details"]["origin_raw_status"], "fail")
        self.assertNotIn("blocked_gate", gate["details"])

    def test_remote_readback_failure_classifies_https_probe_ssh_transport_drift(self) -> None:
        gate = evaluate_remote_readback(
            origin_state="fail",
            origin_details={
                "argv": ["git", "ls-remote", "--heads", "--tags", "origin"],
                "returncode": 128,
                "stdout": "",
                "stderr": "Connection closed by 198.18.0.190 port 22\nfatal: Could not read from remote repository.\n",
                "remote_name": "origin",
                "declared_url": "git@github.com:Undermybelt/givenup-ict-engine.git",
                "fallback_public_probe": {
                    "target": "https://github.com/Undermybelt/givenup-ict-engine.git",
                    "transport": "https_public_no_rewrite",
                    "result": {
                        "argv": [
                            "git",
                            "ls-remote",
                            "--heads",
                            "--tags",
                            "https://github.com/Undermybelt/givenup-ict-engine.git",
                        ],
                        "returncode": 128,
                        "stdout": "",
                        "stderr": "Connection closed by 198.18.0.190 port 22\n",
                    },
                },
            },
            mirror_state="fail",
            mirror_details={
                "argv": ["git", "ls-remote", "--heads", "--tags", "https://github.com/Undermybelt/ict-engine-release.git"],
                "returncode": 128,
                "stdout": "",
                "stderr": "Connection closed by 198.18.0.190 port 22\n",
                "remote_name": "release_mirror",
                "declared_url": "https://github.com/Undermybelt/ict-engine-release.git",
                "fallback_public_probe": {
                    "target": "https://github.com/Undermybelt/ict-engine-release.git",
                    "transport": "https_public_no_rewrite",
                    "result": {
                        "argv": [
                            "git",
                            "ls-remote",
                            "--heads",
                            "--tags",
                            "https://github.com/Undermybelt/ict-engine-release.git",
                        ],
                        "returncode": 128,
                        "stdout": "",
                        "stderr": "Connection closed by 198.18.0.190 port 22\n",
                    },
                },
            },
        )

        self.assertEqual(gate["details"]["diagnostic_class"], "https_probe_ssh_transport_drift")
        self.assertIn("insteadof", gate["details"]["next_action"])
        self.assertIn("core.sshCommand", gate["details"]["next_action"])

    def test_source_origin_alignment_does_not_compare_mirror_commit_to_source_head(self) -> None:
        gate = evaluate_source_origin_alignment(
            head="source-head",
            origin_main="other-source-head",
            mirror_main="mirror-export-commit",
            origin_divergence={"ahead": 2, "behind": 0, "ref": "origin/main"},
        )
        self.assertEqual(gate["status"], "fail")
        self.assertEqual(gate["details"]["release_mirror_main"], "mirror-export-commit")
        self.assertEqual(gate["details"]["source_ahead_of_origin"], 2)
        self.assertEqual(gate["details"]["source_behind_origin"], 0)
        self.assertEqual(gate["details"]["origin_ref"], "origin/main")
        self.assertEqual(gate["details"]["next_action"], "push selected source commit or publish from a clean export at the selected commit")
        self.assertEqual(gate["details"]["rule"], "source origin/main must match the selected source commit before a clean export is published")

    def test_docs_freshness_fails_on_historical_release_notes(self) -> None:
        gate = evaluate_docs_freshness(
            "This signoff is historical v0.1.3 evidence, not current release permission.",
            "These notes are historical v0.1.3 draft notes. They are not valid release notes.",
            signoff_path="support/docs/audits/release-signoff.md",
            notes_path="support/docs/release-notes-draft.md",
        )
        self.assertEqual(gate["status"], "fail")
        self.assertIn("release_signoff_historical", gate["details"]["markers"])
        self.assertIn("release_notes_historical", gate["details"]["markers"])
        self.assertEqual(
            gate["details"]["doc_paths"],
            [
                "support/docs/audits/release-signoff.md",
                "support/docs/release-notes-draft.md",
            ],
        )
        self.assertIn("selected tag/export", gate["details"]["next_action"])

    def test_docs_freshness_fails_when_signoff_and_notes_select_different_tags(self) -> None:
        gate = evaluate_docs_freshness(
            "\n".join(
                [
                    "Selected candidate: `v0.1.8`",
                    "Selected source commit: 547133b8e17f9c92c9e9cc9c4d901c5c0b3918df",
                ]
            ),
            "Version: `v0.1.7`",
        )

        self.assertEqual(gate["status"], "fail")
        self.assertIn("release_docs_tag_mismatch", gate["details"]["markers"])
        self.assertEqual(gate["details"]["signoff_tag"], "v0.1.8")
        self.assertEqual(gate["details"]["notes_tag"], "v0.1.7")

    def test_docs_freshness_fails_when_selected_cargo_version_drifts(self) -> None:
        gate = evaluate_docs_freshness(
            "\n".join(
                [
                    "Selected candidate: `v0.1.7`",
                    "Selected source commit: 518b05579cb3d851accae1da43f8a9cf6d637389",
                ]
            ),
            "Version: `v0.1.7`",
            selected_version="0.1.8",
        )

        self.assertEqual(gate["status"], "fail")
        self.assertIn("release_signoff_tag_mismatch", gate["details"]["markers"])
        self.assertIn("release_notes_tag_mismatch", gate["details"]["markers"])
        self.assertEqual(gate["details"]["expected_tag"], "v0.1.8")
        self.assertEqual(gate["details"]["signoff_tag"], "v0.1.7")
        self.assertEqual(gate["details"]["notes_tag"], "v0.1.7")
        self.assertEqual(
            gate["details"]["signoff_source_commit"],
            "518b05579cb3d851accae1da43f8a9cf6d637389",
        )

    def test_summarize_needs_fix_when_any_required_gate_fails(self) -> None:
        summary = summarize(
            [
                {"id": "a", "status": "pass"},
                {"id": "b", "status": "skip"},
                {"id": "c", "status": "fail"},
            ]
        )
        self.assertEqual(summary["status"], "needs_fix")
        self.assertEqual(summary["unresolved"], ["c"])

    def test_format_report_compact_emits_single_line_json(self) -> None:
        report = {"summary": {"status": "pass"}, "gates": [{"id": "a", "status": "pass"}]}
        text = format_report(report, compact=True)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\n  ", text)
        self.assertIn('"summary":{"status":"pass"}', text)

    def test_format_report_compact_omits_repo_root_and_relativizes_details(self) -> None:
        report = {
            "timestamp_utc": "2026-05-22T00:00:00Z",
            "repo_root": "/Users/example/ict-engine",
            "head": "abc123",
            "cargo": {"version": "0.1.3"},
            "remote_details": {"enabled": False},
            "summary": {"status": "needs_fix"},
            "gates": [
                {
                    "id": "worktree_clean_for_release",
                    "status": "fail",
                    "details": {
                        "sample": [" M /Users/example/ict-engine/src/main.rs"],
                        "stderr": "failed at /Users/example/ict-engine/support/docs/release-notes-draft.md",
                    },
                }
            ],
        }

        text = format_report(report, compact=True)
        parsed = json.loads(text)

        self.assertNotIn("repo_root", parsed)
        self.assertEqual(parsed["head"], "abc123")
        self.assertEqual(parsed["gates"][0]["details"]["sample"], [" M src/main.rs"])
        self.assertEqual(parsed["gates"][0]["details"]["stderr"], "failed at support/docs/release-notes-draft.md")
        self.assertNotIn("/Users/example", text)

    def test_format_report_compact_summarizes_command_outputs(self) -> None:
        report = {
            "timestamp_utc": "2026-05-22T00:00:00Z",
            "head": "abc123",
            "cargo": {"version": "0.1.3"},
            "remote_details": {
                "enabled": True,
                "origin": {
                    "argv": ["git", "ls-remote", "--heads", "--tags", "origin"],
                    "returncode": 0,
                    "stdout": (
                        "abc\trefs/heads/main\n"
                        "def\trefs/heads/green-baseline\n"
                        "123\trefs/tags/v0.0.1\n"
                    ),
                    "stderr": "",
                },
                "release_mirror": {
                    "argv": ["git", "ls-remote", "--heads", "--tags", "release"],
                    "returncode": 128,
                    "stdout": "",
                    "stderr": "Connection closed by 198.18.1.114 port 22\nfatal: Could not read from remote repository.\n",
                },
            },
            "summary": {"status": "needs_fix"},
            "gates": [],
        }

        text = format_report(report, compact=True)
        parsed = json.loads(text)
        origin = parsed["remote_details"]["origin"]
        mirror = parsed["remote_details"]["release_mirror"]

        self.assertNotIn("green-baseline", text)
        self.assertNotIn("refs/tags", text)
        self.assertNotIn("stdout", origin)
        self.assertNotIn("stderr", mirror)
        self.assertEqual(origin["stdout_line_count"], 3)
        self.assertEqual(origin["stderr_line_count"], 0)
        self.assertEqual(mirror["stderr_line_count"], 2)
        self.assertIn("Connection closed", mirror["stderr_excerpt"])


if __name__ == "__main__":
    unittest.main()
