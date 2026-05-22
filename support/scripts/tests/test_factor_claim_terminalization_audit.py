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

from factor_claim_terminalization_audit import build_report, format_report, parse_claim_text, summarize  # noqa: E402


class FactorClaimTerminalizationAuditTest(unittest.TestCase):
    def test_parse_claim_text_accepts_colon_and_equals_claims(self) -> None:
        parsed = parse_claim_text(
            """
owner: codex
run_root: /tmp/example-run
terminalized_at: 2026-05-22T21:52:00+08:00
decision: fail_closed
summary: promotion_allowed=false; trade_usable=false
"""
        )
        self.assertEqual(parsed["owner"], "codex")
        self.assertEqual(parsed["run_root"], "/tmp/example-run")
        self.assertEqual(parsed["decision"], "fail_closed")
        self.assertEqual(parsed["promotion_allowed"], False)
        self.assertEqual(parsed["trade_usable"], False)

        parsed_equals = parse_claim_text(
            """
owner=codex-current-turn
run_root=support/docs/experiments/example
status=terminalized_readonly
decision=readback_complete
summary=promotion_allowed=true; trade_usable=true
"""
        )
        self.assertEqual(parsed_equals["status"], "terminalized_readonly")
        self.assertEqual(parsed_equals["promotion_allowed"], True)
        self.assertEqual(parsed_equals["trade_usable"], True)

    def test_build_report_classifies_active_and_terminal_claims(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            run_root = repo_root / "support" / "docs" / "experiments" / "run-a"
            run_root.mkdir(parents=True)

            (claims_dir / "terminal.claim").write_text(
                f"""
owner=codex
run_root={run_root.relative_to(repo_root)}
terminalized_at=2026-05-22T21:00:00+0800
decision=negative
summary=promotion_allowed=false; trade_usable=false
""",
                encoding="utf-8",
            )
            (claims_dir / "active.claim").write_text(
                """
owner=codex
scope=still active
run_root=/tmp/missing-run-root-for-test
""",
                encoding="utf-8",
            )

            report = build_report(claims_dir=claims_dir, repo_root=repo_root)
            self.assertEqual(report["summary"]["total_claims"], 2)
            self.assertEqual(report["summary"]["terminalized_claims"], 1)
            self.assertEqual(report["summary"]["active_claims"], 1)
            self.assertEqual(report["summary"]["missing_run_roots"], 1)
            self.assertEqual(report["summary"]["trade_usable_true"], 0)
            self.assertEqual(report["summary"]["promotion_allowed_true"], 0)
            active = [claim for claim in report["claims"] if claim["status"] == "active"][0]
            self.assertEqual(active["claim_file"], "active.claim")

    def test_build_report_reads_json_claim_with_decision_as_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            (claims_dir / "readback.json").write_text(
                """
{
  "owner": "codex",
  "scope": "read-only ranking",
  "decision": "continue_goal_active; no promotion_allowed/trade_usable evidence found"
}
""",
                encoding="utf-8",
            )

            report = build_report(claims_dir=claims_dir, repo_root=repo_root)
            self.assertEqual(report["summary"]["total_claims"], 1)
            self.assertEqual(report["summary"]["terminalized_claims"], 1)
            self.assertEqual(report["summary"]["active_claims"], 0)
            self.assertEqual(report["claims"][0]["decision"], "continue_goal_active; no promotion_allowed/trade_usable evidence found")

    def test_summarize_marks_needs_attention_for_active_or_positive_claims(self) -> None:
        summary = summarize(
            [
                {"status": "terminalized", "run_root_exists": True, "promotion_allowed": False, "trade_usable": False},
                {"status": "active", "run_root": "/tmp/missing", "run_root_exists": False, "promotion_allowed": None, "trade_usable": None},
                {"status": "terminalized", "run_root_exists": True, "promotion_allowed": True, "trade_usable": True},
            ]
        )
        self.assertEqual(summary["status"], "needs_attention")
        self.assertEqual(summary["active_claims"], 1)
        self.assertEqual(summary["missing_run_roots"], 1)
        self.assertEqual(summary["trade_usable_true"], 1)
        self.assertEqual(summary["promotion_allowed_true"], 1)

    def test_format_report_compact_keeps_only_attention_claim_summaries(self) -> None:
        full_report = {
            "schema_version": "factor-claim-terminalization-audit/v1",
            "generated_at": "2026-05-22T00:00:00+00:00",
            "claims_dir": "/tmp/claims",
            "repo_root": "/Users/example/ict-engine",
            "summary": {
                "status": "needs_attention",
                "total_claims": 3,
                "terminalized_claims": 1,
                "active_claims": 1,
                "missing_run_roots": 1,
                "trade_usable_true": 1,
                "promotion_allowed_true": 1,
            },
            "claims": [
                {
                    "claim_file": "terminal.claim",
                    "claim_path": "/tmp/claims/terminal.claim",
                    "status": "terminalized",
                    "owner": "codex",
                    "scope": "done",
                    "decision": "drop",
                    "run_root": "/Users/example/ict-engine/support/docs/experiments/run-a",
                    "run_root_exists": True,
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "summary_files": ["summaries/terminal_decision_summary.md"],
                },
                {
                    "claim_file": "active.claim",
                    "claim_path": "/tmp/claims/active.claim",
                    "status": "active",
                    "owner": "codex",
                    "scope": "still running",
                    "decision": None,
                    "run_root": "/tmp/missing-run-root",
                    "run_root_exists": False,
                    "promotion_allowed": None,
                    "trade_usable": None,
                    "summary_files": [],
                },
                {
                    "claim_file": "positive.claim",
                    "claim_path": "/tmp/claims/positive.claim",
                    "status": "terminalized",
                    "owner": "codex",
                    "scope": "positive flag",
                    "decision": "review",
                    "run_root": "/tmp/run",
                    "run_root_exists": True,
                    "promotion_allowed": True,
                    "trade_usable": True,
                    "summary_files": ["checks/terminal_metrics.json"],
                },
            ],
        }

        compact = format_report(full_report, compact=True)

        self.assertNotIn("claims", compact)
        self.assertNotIn("repo_root", compact)
        self.assertEqual(compact["summary"], full_report["summary"])
        self.assertEqual(compact["attention_claim_count"], 2)
        self.assertEqual([claim["claim_file"] for claim in compact["attention_claims"]], ["active.claim", "positive.claim"])
        self.assertEqual(compact["attention_claims"][0]["run_root_state"], "missing")
        self.assertNotIn("claim_path", compact["attention_claims"][0])
        self.assertNotIn("run_root", compact["attention_claims"][0])

    def test_format_report_compact_sanitizes_free_text_paths(self) -> None:
        full_report = {
            "schema_version": "factor-claim-terminalization-audit/v1",
            "generated_at": "2026-05-22T00:00:00+00:00",
            "claims_dir": "/tmp/claims",
            "repo_root": "/Users/example/ict-engine",
            "summary": {"status": "needs_attention"},
            "claims": [
                {
                    "claim_file": "active.claim",
                    "claim_path": "/tmp/claims/active.claim",
                    "status": "active",
                    "owner": "codex",
                    "scope": "inspect /Users/example/ict-engine/support/docs/private.md and /Users/example/Downloads/private.csv",
                    "decision": "blocked by /Users/example/ict-engine/state/local",
                    "run_root": "/Users/example/ict-engine/support/docs/experiments/run-a",
                    "run_root_exists": True,
                    "promotion_allowed": None,
                    "trade_usable": None,
                    "summary_files": [],
                },
            ],
        }

        compact = format_report(full_report, compact=True)
        serialized = json.dumps(compact, sort_keys=True)

        self.assertIn("support/docs/private.md", compact["attention_claims"][0]["scope"])
        self.assertIn("[local-path]", compact["attention_claims"][0]["scope"])
        self.assertEqual(compact["attention_claims"][0]["decision"], "blocked by state/local")
        self.assertNotIn("/Users/example", serialized)

    def test_format_report_full_keeps_original_report(self) -> None:
        full_report = {"summary": {"status": "pass"}, "claims": []}
        self.assertIs(format_report(full_report, compact=False), full_report)


if __name__ == "__main__":
    unittest.main()
