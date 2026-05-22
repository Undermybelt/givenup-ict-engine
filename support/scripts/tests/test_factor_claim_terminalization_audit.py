#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from factor_claim_terminalization_audit import build_report, parse_claim_text, summarize  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
