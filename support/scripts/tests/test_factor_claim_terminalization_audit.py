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

from factor_claim_terminalization_audit import (  # noqa: E402
    _is_live_factor_command,
    build_report,
    format_report,
    parse_claim_text,
    summarize,
)


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

    def test_build_report_treats_terminal_status_and_markdown_bullets_as_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            project_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            run_root = project_root / "support" / "docs" / "experiments" / "run-a"
            (run_root / "checks").mkdir(parents=True)
            (run_root / "summaries").mkdir(parents=True)
            (run_root / "checks" / "terminal_metrics.json").write_text(
                '{"promotion_allowed": false, "trade_usable": false}',
                encoding="utf-8",
            )

            (claims_dir / "bullet-terminal.claim").write_text(
                f"""
# Claim

- owner: codex
- status: terminal_observation_only
- run_root: {run_root.relative_to(project_root)}
- terminal_decision: fail_closed_observation_only
- promotion_allowed: false
- trade_usable: false
""",
                encoding="utf-8",
            )
            (claims_dir / "plain-terminal.claim").write_text(
                f"""
owner=codex
status=terminal
run_root={run_root.relative_to(project_root)}
terminal_decision=drop_gate1
promotion_allowed=false
trade_usable=false
""",
                encoding="utf-8",
            )

            report = build_report(claims_dir, project_root)

            self.assertEqual(report["summary"]["total_claims"], 2)
            self.assertEqual(report["summary"]["terminalized_claims"], 2)
            self.assertEqual(report["summary"]["active_claims"], 0)
            self.assertEqual(report["summary"]["status"], "pass")
            self.assertEqual(report["claims"][0]["status"], "terminalized")
            self.assertEqual(report["claims"][0]["decision"], "fail_closed_observation_only")

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
        self.assertEqual(
            summary["blocking_reasons"],
            [
                "active_claims",
                "missing_run_roots",
                "trade_usable_true",
                "promotion_allowed_true",
            ],
        )
        self.assertIn("terminalize or externalize active claims", summary["next_action"])
        self.assertIn("restore or terminalize missing run roots", summary["next_action"])
        self.assertIn("review positive trade/promotion flags", summary["next_action"])

    def test_build_report_marks_unclaimed_live_factor_processes_attention(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            live_run_root = Path("/tmp/ict-engine-tomac-psar-arooncci-gate1-repair-test")
            (claims_dir / "terminal.claim").write_text(
                """
owner=codex
status=terminalized
decision=fail_closed
promotion_allowed=false
trade_usable=false
""",
                encoding="utf-8",
            )

            report = build_report(
                claims_dir=claims_dir,
                repo_root=repo_root,
                live_processes=[
                    {
                        "pid": 12345,
                        "ppid": 123,
                        "elapsed": "00:12",
                        "command_excerpt": "python3 /tmp/run_tomac_psar_arooncci_gate1.py --out "
                        f"{live_run_root}/full",
                        "run_root": str(live_run_root),
                        "exit_file": str(live_run_root / "checks" / "01_full_repair.exit"),
                        "exit_file_exists": False,
                    }
                ],
            )
            compact = format_report(report, compact=True)

            self.assertEqual(report["summary"]["status"], "needs_attention")
            self.assertEqual(report["summary"]["active_claims"], 0)
            self.assertEqual(report["summary"]["live_factor_processes"], 1)
            self.assertIn("live_factor_processes", report["summary"]["blocking_reasons"])
            self.assertEqual(compact["attention_live_process_count"], 1)
            self.assertEqual(compact["attention_live_processes"][0]["pid"], 12345)

    def test_live_process_classifier_ignores_ps_rg_readback_commands(self) -> None:
        command = (
            "/bin/zsh -lc sleep 75; ps -axo pid,ppid,etime,%cpu,%mem,command | "
            "rg -i 'run_tomac_psar_arooncci|tomac-psar|run_ibkr_axon|"
            "auto-quant-agent-material|fetch_external\\.py|factor-research|cargo run' | "
            "rg -v 'rg -i'"
        )

        self.assertFalse(_is_live_factor_command(command))

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
        self.assertEqual(
            compact["attention_groups"],
            {
                "by_owner": {"codex": 2},
                "by_run_root_state": {"missing": 1, "present": 1},
                "by_status": {"active": 1, "terminalized": 1},
            },
        )
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
