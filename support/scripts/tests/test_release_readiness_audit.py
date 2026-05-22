#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from release_readiness_audit import (  # noqa: E402
    evaluate_docs_freshness,
    evaluate_source_origin_alignment,
    evaluate_version_tag,
    evaluate_version_tag_unknown,
    format_report,
    parse_cargo_metadata,
    parse_ls_remote,
    summarize,
)


class ReleaseReadinessAuditTest(unittest.TestCase):
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

    def test_version_tag_fails_when_release_mirror_already_has_version(self) -> None:
        gate = evaluate_version_tag("0.1.4", {"v0.1.3", "v0.1.4"})
        self.assertEqual(gate["status"], "fail")
        self.assertIn("v0.1.4", gate["details"]["blocking_tags"])

    def test_version_tag_is_skipped_without_release_mirror_tags(self) -> None:
        gate = evaluate_version_tag_unknown("network_check_not_enabled")
        self.assertEqual(gate["id"], "release_version_tag_available")
        self.assertEqual(gate["status"], "skip")
        self.assertEqual(gate["details"]["reason"], "network_check_not_enabled")
        self.assertEqual(gate["details"]["enable_with"], "--check-remotes")

    def test_source_origin_alignment_does_not_compare_mirror_commit_to_source_head(self) -> None:
        gate = evaluate_source_origin_alignment(
            head="source-head",
            origin_main="other-source-head",
            mirror_main="mirror-export-commit",
        )
        self.assertEqual(gate["status"], "fail")
        self.assertEqual(gate["details"]["release_mirror_main"], "mirror-export-commit")
        self.assertEqual(gate["details"]["rule"], "source origin/main must match the selected source commit before a clean export is published")

    def test_docs_freshness_fails_on_historical_release_notes(self) -> None:
        gate = evaluate_docs_freshness(
            "This signoff is historical v0.1.3 evidence, not current release permission.",
            "These notes are historical v0.1.3 draft notes. They are not valid release notes.",
        )
        self.assertEqual(gate["status"], "fail")
        self.assertIn("release_signoff_historical", gate["details"]["markers"])
        self.assertIn("release_notes_historical", gate["details"]["markers"])

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


if __name__ == "__main__":
    unittest.main()
