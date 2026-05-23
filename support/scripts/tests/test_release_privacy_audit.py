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

from release_privacy_audit import build_report, format_report, rust_test_lines, scan_root  # noqa: E402


class ReleasePrivacyAuditTest(unittest.TestCase):
    def test_blocks_root_readme_private_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("run with /Users/alice/private.csv\n", encoding="utf-8")

            report = build_report(root, sample_limit=10)

        self.assertEqual(report["summary"]["status"], "needs_fix")
        self.assertEqual(report["summary"]["release_blocking_hits"], 1)
        self.assertEqual(report["summary"]["release_blocking_paths"], ["README.md"])
        self.assertIn("/Users/<redacted>", report["blocking_samples"][0]["excerpt"])

    def test_classifies_tests_and_policy_references_as_non_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            test_dir = root / "support" / "scripts" / "tests"
            test_dir.mkdir(parents=True)
            (test_dir / "test_example.py").write_text(
                "self.assertNotIn('/Users/example', text)\n", encoding="utf-8"
            )
            (root / "AGENT.md").write_text("Do not expose /Users/...\n", encoding="utf-8")

            report = build_report(root, sample_limit=10)

        self.assertEqual(report["summary"]["status"], "pass")
        self.assertEqual(report["summary"]["release_blocking_hits"], 0)
        self.assertGreaterEqual(report["summary"]["by_classification"]["test_or_policy_reference"], 1)

    def test_classifies_historical_support_docs_separately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "support" / "docs" / "bug" / "0.1.0"
            docs.mkdir(parents=True)
            (docs / "old.md").write_text("old run /Users/alice/Downloads/Tomac/data.csv\n", encoding="utf-8")

            report = build_report(root, sample_limit=10)

        self.assertEqual(report["summary"]["status"], "pass")
        self.assertEqual(report["summary"]["release_blocking_hits"], 0)
        self.assertEqual(report["summary"]["by_classification"]["historical_docs"], 2)

    def test_secret_like_tokens_are_release_blocking_anywhere(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "support").mkdir()
            (root / "support" / "docs.md").write_text(
                "token " + "sk-" + "abcdefghijklmnopqrstuvwxyz123456" + "\n",
                encoding="utf-8",
            )

            report = build_report(root, sample_limit=10)

        self.assertEqual(report["summary"]["status"], "needs_fix")
        self.assertEqual(report["summary"]["release_blocking_hits"], 1)
        self.assertIn("sk-<redacted>", report["blocking_samples"][0]["excerpt"])

    def test_secret_like_tokens_in_historical_docs_still_block_release(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "support" / "docs" / "plans"
            docs.mkdir(parents=True)
            (docs / "old.md").write_text(
                "legacy token " + "sk-" + "abcdefghijklmnopqrstuvwxyz123456" + "\n",
                encoding="utf-8",
            )

            report = build_report(root, sample_limit=10)

        self.assertEqual(report["summary"]["status"], "needs_fix")
        self.assertEqual(report["summary"]["release_blocking_hits"], 1)
        self.assertEqual(
            report["summary"]["release_blocking_paths"],
            ["support/docs/plans/old.md"],
        )

    def test_compact_report_omits_root_and_limits_samples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for index in range(12):
                (root / f"file-{index}.md").write_text("/Users/alice/data\n", encoding="utf-8")
            report = build_report(root, sample_limit=12)

        compact = json.loads(format_report(report, compact=True))

        self.assertNotIn("root", compact)
        self.assertEqual(len(compact["samples"]), 10)
        self.assertEqual(len(compact["blocking_samples"]), 10)

    def test_scan_skips_binary_suffixes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "image.png").write_bytes(b"/Users/alice/secret")

            hits = scan_root(root)

        self.assertEqual(hits, [])

    def test_rust_test_context_is_non_blocking(self) -> None:
        source = """
#[test]
fn covers_private_tmp_fixture() {
    let value = "/private/tmp/a.json";
    assert!(value.contains("tmp"));
}

fn production_example() {
    let value = "/private/tmp/a.json";
}
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "main.rs").write_text(source, encoding="utf-8")

            report = build_report(root, sample_limit=10)

        self.assertEqual(rust_test_lines(source), {3, 4, 5, 6})
        self.assertEqual(report["summary"]["release_blocking_hits"], 1)
        self.assertEqual(report["summary"]["by_classification"]["test_or_policy_reference"], 1)


if __name__ == "__main__":
    unittest.main()
