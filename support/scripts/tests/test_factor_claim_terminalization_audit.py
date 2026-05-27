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
    _drop_stale_failed_tomac_prep_wrappers,
    _attribute_parent_run_roots,
    _extract_run_root,
    _infer_exit_file,
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
Owner: codex
run-root: /tmp/example-run
terminalized_at: 2026-05-22T21:52:00+08:00
Decision: fail_closed
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

    def test_parse_claim_text_unwraps_markdown_scalar_values(self) -> None:
        parsed = parse_claim_text(
            """
- owner: `codex`
- status: `active`
- run_root: `/tmp/example-run`
- decision: `drop_gate1`
"""
        )

        self.assertEqual(parsed["owner"], "codex")
        self.assertEqual(parsed["status"], "active")
        self.assertEqual(parsed["run_root"], "/tmp/example-run")
        self.assertEqual(parsed["decision"], "drop_gate1")

    def test_parse_claim_text_keeps_absolute_run_root_over_later_relative_duplicate(self) -> None:
        parsed = parse_claim_text(
            """
run_root: /tmp/real-run-root
decision: drop_gate1
run_root=support/docs/experiments/run-a
"""
        )

        self.assertEqual(parsed["run_root"], "/tmp/real-run-root")

    def test_parse_claim_text_prefers_explicit_bool_fields_over_negated_non_goals(self) -> None:
        parsed = parse_claim_text(
            """
agent_name=codex-etn-readback
owner=Codex CLI
scope=read existing ETN branch evidence
active_task=verify current ETN terminal artifacts
non_goals=no provider fetch; no promotion_allowed=true; no trade_usable=true
write_surface=/tmp/ict-engine-etn-readback
tmp_root=/tmp/ict-engine-etn-readback
status=active
promotion_allowed=false
trade_usable=false
"""
        )

        self.assertEqual(parsed["promotion_allowed"], False)
        self.assertEqual(parsed["trade_usable"], False)

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
            self.assertEqual(report["summary"]["valid_active_claims"], 0)
            self.assertEqual(report["summary"]["invalid_active_claims"], 1)
            self.assertEqual(report["summary"]["missing_run_roots"], 1)
            self.assertEqual(report["summary"]["trade_usable_true"], 0)
            self.assertEqual(report["summary"]["promotion_allowed_true"], 0)
            active = [claim for claim in report["claims"] if claim["status"] == "active"][0]
            self.assertEqual(active["claim_file"], "active.claim")

    def test_build_report_resolves_relative_run_root_against_claim_repo_field(self) -> None:
        with tempfile.TemporaryDirectory() as claim_repo_tmp, tempfile.TemporaryDirectory() as audit_repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            claim_repo = Path(claim_repo_tmp)
            audit_repo = Path(audit_repo_tmp)
            claims_dir = Path(claims_tmp)
            run_root = claim_repo / "support" / "docs" / "experiments" / "run-a"
            run_root.mkdir(parents=True)

            (claims_dir / "repo-relative.claim").write_text(
                f"""
owner=codex
repo={claim_repo}
status=terminalized
run_root={run_root.relative_to(claim_repo)}
decision=drop_gate1
promotion_allowed=false
trade_usable=false
""",
                encoding="utf-8",
            )

            report = build_report(claims_dir=claims_dir, repo_root=audit_repo)

            self.assertEqual(report["summary"]["status"], "pass")
            self.assertEqual(report["summary"]["missing_run_roots"], 0)
            self.assertTrue(report["claims"][0]["run_root_exists"])

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

    def test_build_report_treats_run_root_terminal_artifacts_as_terminalized_even_if_claim_status_is_active(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)

            decision_run_root = repo_root / "support" / "docs" / "experiments" / "run-decision"
            decision_run_root.mkdir(parents=True)
            (decision_run_root / "summaries").mkdir(parents=True, exist_ok=True)
            (decision_run_root / "checks").mkdir(parents=True, exist_ok=True)
            (decision_run_root / "summaries" / "terminal_decision_summary.md").write_text(
                """
# Exact lane

Decision: observation_no_survivor
promotion_allowed=false
trade_usable=false
""",
                encoding="utf-8",
            )
            (decision_run_root / "checks" / "terminal_metrics.json").write_text(
                json.dumps(
                    {
                        "decision": "observation_no_survivor",
                        "promotion_allowed": False,
                        "trade_usable": False,
                    }
                ),
                encoding="utf-8",
            )

            json_run_root = repo_root / "support" / "docs" / "experiments" / "run-json"
            json_run_root.mkdir(parents=True)
            (json_run_root / "summaries").mkdir(parents=True, exist_ok=True)
            (json_run_root / "summaries" / "terminal_summary.json").write_text(
                json.dumps(
                    {
                        "status": "launch_finished",
                        "scan_exit": 0,
                        "target_row_count": 0,
                        "promotion_allowed": False,
                        "trade_usable": False,
                    }
                ),
                encoding="utf-8",
            )

            (claims_dir / "decision-active.claim").write_text(
                f"""
agent_name=codex-derived-terminal-decision
owner=codex
claimed_at=2026-05-27T13:39:48+0800
last_progress_at=2026-05-27T13:45:00+0800
scope=Board B same-root decision packet
active_task=read same-root terminal packet
non_goals=no relaunch
write_surface=/tmp/example-workdoc.md
run_root={decision_run_root.relative_to(repo_root)}
status=active
progress_report=/tmp/example-progress.md
promotion_allowed=false
trade_usable=false
""",
                encoding="utf-8",
            )
            (claims_dir / "json-active.claim").write_text(
                f"""
agent_name=codex-derived-terminal-json
owner=codex
claimed_at=2026-05-27T13:50:04+0800
last_progress_at=2026-05-27T13:55:00+0800
scope=Board B same-root launch packet
active_task=read launch-finished packet
non_goals=no relaunch
write_surface=/tmp/example-json-workdoc.md
run_root={json_run_root.relative_to(repo_root)}
status=active
progress_report=/tmp/example-json-progress.md
promotion_allowed=false
trade_usable=false
""",
                encoding="utf-8",
            )

            report = build_report(claims_dir=claims_dir, repo_root=repo_root)

            self.assertEqual(report["summary"]["terminalized_claims"], 2)
            self.assertEqual(report["summary"]["active_claims"], 0)
            self.assertEqual(
                [claim["status"] for claim in report["claims"]],
                ["terminalized", "terminalized"],
            )

    def test_build_report_reads_json_payload_in_claim_suffix_as_json(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            (claims_dir / "readonly-terminal.claim").write_text(
                json.dumps(
                    {
                        "active_task": "classify non-duplicate Board B progress",
                        "agent_name": "codex-readonly-auditor",
                        "non_goals": ["no provider", "no promotion"],
                        "owner": "Codex CLI",
                        "scope": "read-only extension breadth audit",
                        "status": "terminal_readonly_audit_written",
                        "tmp_root": "/tmp/ict-engine-agent-claims/board-b-factor-refinement",
                        "write_surface": "/tmp/terminalization_audit.json",
                        "promotion_allowed": False,
                        "trade_usable": False,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            report = build_report(claims_dir=claims_dir, repo_root=repo_root)

            self.assertEqual(report["summary"]["total_claims"], 1)
            self.assertEqual(report["summary"]["terminalized_claims"], 1)
            self.assertEqual(report["summary"]["active_claims"], 0)
            self.assertEqual(report["summary"]["invalid_active_claims"], 0)
            self.assertEqual(report["summary"]["status"], "pass")
            self.assertEqual(report["claims"][0]["agent_name"], "codex-readonly-auditor")

    def test_build_report_ignores_generated_audit_json_reports(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            (claims_dir / "terminalization_audit_20260524T_current_codex_resume.json").write_text(
                '{"summary": {"status": "needs_attention", "active_claims": 10}}',
                encoding="utf-8",
            )
            (claims_dir / "20260524T_after_payx_matrix_audit.json").write_text(
                '{"summary": {"status": "needs_attention", "active_claims": 10}}',
                encoding="utf-8",
            )
            (claims_dir / "readback.json").write_text(
                '{"owner": "codex", "decision": "readback_complete", "promotion_allowed": false, "trade_usable": false}',
                encoding="utf-8",
            )

            report = build_report(claims_dir=claims_dir, repo_root=repo_root)

            self.assertEqual(report["summary"]["total_claims"], 1)
            self.assertEqual(report["summary"]["terminalized_claims"], 1)
            self.assertEqual(report["summary"]["active_claims"], 0)
            self.assertEqual(report["claims"][0]["claim_file"], "readback.json")

    def test_build_report_ignores_generated_claim_sidecars(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            (claims_dir / "20260524T220713+0800-codex-avgo-terminal-provider-blocked-readback.summary.json").write_text(
                '{"agent_name": "codex-avgo-readback", "status": "provider_blocked"}',
                encoding="utf-8",
            )
            (claims_dir / "20260524T220713+0800-codex-avgo-terminal-provider-blocked-readback.summary.json.check").write_text(
                "checked\n",
                encoding="utf-8",
            )
            (claims_dir / "20260524T2220+0800-codex-ote-provider-guard-readonly.exit").write_text(
                "2\n",
                encoding="utf-8",
            )
            (claims_dir / "20260524T213435+0800-codex-mgc-microtrend-readonly-extension-auditor.claim.pretty").write_text(
                '{"claim_file": "source.pretty", "status": "active"}',
                encoding="utf-8",
            )
            (claims_dir / "terminalization_audit_20260524T213435+0800_codex-mgc.json.pretty").write_text(
                '{"summary": {"active_claims": 99}}',
                encoding="utf-8",
            )
            (claims_dir / "real.claim").write_text(
                """
agent_name=codex-test
owner=codex
scope=real claim
active_task=unit test
non_goals=none
write_surface=tmp
tmp_root=/tmp/ict-engine-claim-audit-test
status=active
promotion_allowed=false
trade_usable=false
""",
                encoding="utf-8",
            )

            report = build_report(claims_dir=claims_dir, repo_root=repo_root)

            self.assertEqual(report["summary"]["total_claims"], 1)
            self.assertEqual(report["claims"][0]["claim_file"], "real.claim")

    def test_build_report_ignores_none_and_pending_run_root_sentinels(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            for index, sentinel in enumerate(
                [
                    "none",
                    "pending",
                    "pending_runner_timestamp",
                    "pending_runner_launch_after_ibkr_fetch_clear",
                    "n/a",
                    "na",
                    "null",
                    "-",
                ]
            ):
                (claims_dir / f"sentinel-{index}.claim").write_text(
                    f"""
owner=codex
status=externalized_not_launched
decision=externalized_pending_backend_clear_no_factor_verdict
run_root={sentinel}
promotion_allowed=false
trade_usable=false
""",
                    encoding="utf-8",
                )

            report = build_report(claims_dir=claims_dir, repo_root=repo_root)

            self.assertEqual(report["summary"]["total_claims"], 8)
            self.assertEqual(report["summary"]["terminalized_claims"], 8)
            self.assertEqual(report["summary"]["active_claims"], 0)
            self.assertEqual(report["summary"]["missing_run_roots"], 0)
            self.assertTrue(all(claim["run_root"] is None for claim in report["claims"]))

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

    def test_build_report_treats_terminal_readback_heading_case_as_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            run_root = repo_root / "support" / "docs" / "experiments" / "run-a"
            run_root.mkdir(parents=True)

            (claims_dir / "terminal-readback.md").write_text(
                f"""
# Terminal Readback

Decision: drop_gate1_no_hard_5bps_density_survivor

Run root:
{run_root.relative_to(repo_root)}

promotion_allowed=false
trade_usable=false
""",
                encoding="utf-8",
            )
            (claims_dir / "terminal-status.claim").write_text(
                f"""
owner=codex
terminal_status=drop_gate1
terminal_at=2026-05-23T08:41:35+0800
run_root={run_root.relative_to(repo_root)}
promotion_allowed=false
trade_usable=false
""",
                encoding="utf-8",
            )

            report = build_report(claims_dir=claims_dir, repo_root=repo_root)

            self.assertEqual(report["summary"]["terminalized_claims"], 2)
            self.assertEqual(report["summary"]["active_claims"], 0)
            self.assertEqual(report["summary"]["status"], "pass")
            self.assertEqual(report["claims"][0]["decision"], "drop_gate1_no_hard_5bps_density_survivor")
            self.assertEqual(report["claims"][1]["decision"], "drop_gate1")

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

    def test_build_report_flags_active_claims_missing_board_local_identity_fields(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            (claims_dir / "unnamed-active.claim").write_text(
                """
owner=codex
claimed_at=2026-05-25T10:00:00+0800
last_progress_at=2026-05-25T10:05:00+0800
scope=still active but vague
run_root=/tmp/example-active-run
progress_report=/tmp/example-active-run/progress.md
""",
                encoding="utf-8",
            )
            (claims_dir / "named-active.claim").write_text(
                """
agent_name=codex-named-guard
owner=codex
claimed_at=2026-05-25T10:00:00+0800
last_progress_at=2026-05-25T10:05:00+0800
scope=Board B named active lane
active_task=verify a specific gate
non_goals=no provider launch
write_surface=/tmp only
tmp_root=/tmp/named-active
status=active
progress_report=/tmp/named-active/progress.md
""",
                encoding="utf-8",
            )

            report = build_report(claims_dir=claims_dir, repo_root=repo_root)
            compact = format_report(report, compact=True)

            self.assertEqual(report["summary"]["invalid_active_claims"], 1)
            self.assertEqual(report["summary"]["valid_active_claims"], 1)
            self.assertIn("invalid_active_claims", report["summary"]["blocking_reasons"])
            invalid_claim = next(
                claim for claim in compact["attention_claims"] if claim["claim_file"] == "unnamed-active.claim"
            )
            self.assertEqual(
                invalid_claim["missing_identity_fields"],
                ["agent_name", "active_task", "non_goals", "write_surface", "status"],
            )

    def test_build_report_flags_active_claims_missing_timestamp_and_report_fields(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            (claims_dir / "missing-timestamps.claim").write_text(
                """
agent_name=codex-stale-claim
owner=Codex CLI
scope=Board B exact lane
active_task=run exact gate
non_goals=no promotion
write_surface=/tmp/ict-engine-stale
tmp_root=/tmp/ict-engine-stale
status=active
promotion_allowed=false
trade_usable=false
""",
                encoding="utf-8",
            )

            report = build_report(claims_dir=claims_dir, repo_root=repo_root)
            compact = format_report(report, compact=True)

            self.assertEqual(report["summary"]["invalid_active_claims"], 1)
            invalid_claim = compact["attention_claims"][0]
            self.assertEqual(
                invalid_claim["missing_identity_fields"],
                ["claimed_at", "last_progress_at", "progress_report_or_latest_report"],
            )

    def test_live_process_classifier_ignores_ps_rg_readback_commands(self) -> None:
        command = (
            "/bin/zsh -lc sleep 75; ps -axo pid,ppid,etime,%cpu,%mem,command | "
            "rg -i 'run_tomac_psar_arooncci|tomac-psar|run_ibkr_axon|"
            "auto-quant-agent-material|fetch_external\\.py|factor-research|cargo run' | "
            "rg -v 'rg -i'"
        )

        self.assertFalse(_is_live_factor_command(command))

    def test_live_process_classifier_ignores_ps_auxww_rg_readback_commands(self) -> None:
        command = (
            "/bin/zsh -lc ps auxww | rg -i "
            '"run_ibkr|fetch_external\\.py.*ibkr|auto-quant-agent-material-|'
            'run_tomac|run_bybit"'
        )

        self.assertFalse(_is_live_factor_command(command))

    def test_live_process_classifier_ignores_sed_readback_of_factor_wrappers(self) -> None:
        command = (
            "/bin/zsh -lc sed -n '1,260p' "
            "support/docs/experiments/actionable-regime-confidence/runs/example/"
            "scripts/run_ibkr_ntnx_bayesian_markov_trend_detector_1m_mtf_gate1.py"
        )

        self.assertFalse(_is_live_factor_command(command))

    def test_live_process_classifier_ignores_bare_search_readback_commands(self) -> None:
        command = (
            "rg -i run_tomac_psar_arooncci|tomac-psar|run_ibkr_|"
            "auto-quant-agent-material|fetch_external\\.py|prepare_external\\.py|"
            "factor-research|01_full_repair"
        )

        self.assertFalse(_is_live_factor_command(command))

    def test_live_process_classifier_detects_bybit_factor_wrappers(self) -> None:
        command = (
            "/opt/homebrew/bin/python3 "
            "/tmp/run_bybit_hype_pengu_stoprun_reclaim_1m_full_ladder_20260523.py"
        )

        self.assertTrue(_is_live_factor_command(command))

    def test_live_process_classifier_detects_yfinance_factor_wrappers(self) -> None:
        command = (
            "/opt/homebrew/bin/python3 "
            "/tmp/run_yf_crwd5m_late_session_hazard_trim_fresh_gate1_20260523.py"
        )

        self.assertTrue(_is_live_factor_command(command))

    def test_live_process_classifier_detects_public_provider_wrapper_families(self) -> None:
        commands = [
            "/opt/homebrew/bin/python3 /tmp/run_binance_altcoin_rsi_reclaim_1m_mtf_v1.py",
            "/opt/homebrew/bin/python3 /tmp/run_kraken_btc_tsmom_rsi2_aq_v1.py",
            "/opt/homebrew/bin/python3 /tmp/run_external_seed_intraday_momentum_qqq_yf_1m_origin_aq_v1.py",
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(_is_live_factor_command(command))

    def test_live_process_classifier_detects_ibkr_provider_status_probe(self) -> None:
        command = (
            "cargo run --quiet -- provider-status --provider ibkr --agent"
        )

        self.assertTrue(_is_live_factor_command(command))

    def test_live_process_classifier_detects_direct_ict_engine_board_b_cli_child(self) -> None:
        command = (
            ".local-artifacts/cargo-target/debug/ict-engine analyze "
            "--symbol TOMAC_NQ_BIDIR_OPENING_DRIVE_TWOLEG_PROFILE "
            "--data-root /tmp/ict-engine-nq-twoleg-openingdrive-obs30-mtf-readback-followup/data-mtf "
            "--state-dir /tmp/ict-engine-nq-twoleg-openingdrive-obs30-mtf-readback-followup/state "
            "--agent"
        )

        self.assertTrue(_is_live_factor_command(command))
        self.assertEqual(
            _extract_run_root(command),
            Path("/tmp/ict-engine-nq-twoleg-openingdrive-obs30-mtf-readback-followup"),
        )

    def test_live_process_classifier_detects_tomac_helper_scans(self) -> None:
        command = (
            "/opt/homebrew/bin/python3 "
            "/Users/example/Downloads/Tomac/futures_factor_research_20260521/"
            "tomac_tod_portfolio_density_repair_scan.py --leaderboard "
            "/tmp/ict-engine-tomac-session-seasonality-rebuild/leaderboard.csv "
            "--out /tmp/ict-engine-tomac-tod-balanced-portfolio-rebuild-wide"
        )

        self.assertTrue(_is_live_factor_command(command))

    def test_live_process_classifier_ignores_tomac_await_launch_watchers(self) -> None:
        command = (
            "/opt/homebrew/bin/python3 "
            "/Users/example/ict-engine/support/docs/experiments/actionable-regime-confidence/scripts/"
            "run_tomac_prior_day_extreme_continuation_await_launch_v1.py "
            "--root /tmp/ict-engine-tomac-prior-day-extreme-continuation-prep-20260526T092700+0800 "
            "--status-out /tmp/ict-engine-tomac-prior-day-extreme-continuation-prep-20260526T092700+0800/summaries/await_launch_status.json"
        )

        self.assertFalse(_is_live_factor_command(command))

    def test_drop_stale_failed_tomac_prep_wrapper_without_live_child(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "ict-engine-tomac-liquidity-sweep-adx-trend-strength-reclaim-prep-20260526T135002+0800"
            checks = run_root / "checks"
            checks.mkdir(parents=True)
            (checks / "source_launch.exit").write_text("1\n", encoding="utf-8")

            wrapper = {
                "pid": 67655,
                "ppid": 8761,
                "elapsed": "14:03",
                "run_root": str(run_root),
                "exit_file": None,
                "exit_file_exists": False,
                "command_excerpt": (
                    "python support/docs/experiments/actionable-regime-confidence/scripts/"
                    "run_tomac_liquidity_sweep_adx_trend_strength_reclaim_prep_v1.py "
                    f"--root {run_root} --launch"
                ),
            }

            self.assertEqual(_drop_stale_failed_tomac_prep_wrappers([wrapper]), [])

    def test_drop_stale_failed_tomac_prep_wrapper_keeps_parent_with_live_child(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "ict-engine-tomac-liquidity-sweep-adx-trend-strength-reclaim-prep-20260526T135002+0800"
            checks = run_root / "checks"
            checks.mkdir(parents=True)
            (checks / "source_launch.exit").write_text("1\n", encoding="utf-8")

            wrapper = {
                "pid": 67655,
                "ppid": 8761,
                "elapsed": "14:03",
                "run_root": str(run_root),
                "exit_file": None,
                "exit_file_exists": False,
                "command_excerpt": (
                    "python support/docs/experiments/actionable-regime-confidence/scripts/"
                    "run_tomac_liquidity_sweep_adx_trend_strength_reclaim_prep_v1.py "
                    f"--root {run_root} --launch"
                ),
            }
            child = {
                "pid": 67679,
                "ppid": 67655,
                "elapsed": "14:02",
                "run_root": None,
                "exit_file": None,
                "exit_file_exists": False,
                "command_excerpt": "uv run --with pandas --with numpy --with tqdm python /Users/example/Downloads/Tomac/90wr1.5rrr_strategy.py",
            }

            self.assertEqual(_drop_stale_failed_tomac_prep_wrappers([wrapper, child]), [wrapper, child])

    def test_live_process_classifier_detects_custom_tomac_scanner_and_lane_root(self) -> None:
        command = (
            "/opt/homebrew/bin/python3 /tmp/tomac_strict_trend_ote_reaction_scan.py "
            "--start 2021-01-01 --end 2025-12-31T23:59:59 "
            "--out /tmp/ict-engine-tomac-nq-strict-trend-root-ote-reaction-gate1-"
            "20260525T005122+0800/full-2021-2025"
        )

        self.assertTrue(_is_live_factor_command(command))
        self.assertEqual(
            _extract_run_root(command),
            Path("/tmp/ict-engine-tomac-nq-strict-trend-root-ote-reaction-gate1-20260525T005122+0800"),
        )

    def test_live_process_classifier_detects_custom_tomac_postscan_and_lane_root(self) -> None:
        command = (
            "/opt/homebrew/bin/python3 /tmp/tomac_nq_body_momentum_cost_aware_overlay_postscan.py "
            "--trades-dir /tmp/source/trades "
            "--summary /tmp/source/summary.json "
            "--out /tmp/ict-engine-tomac-nq-body-momentum-cost-aware-overlay-postscan-"
            "20260525T0230+0800/full-2021-2025 --max-rows 120"
        )

        self.assertTrue(_is_live_factor_command(command))
        self.assertEqual(
            _extract_run_root(command),
            Path("/tmp/ict-engine-tomac-nq-body-momentum-cost-aware-overlay-postscan-20260525T0230+0800"),
        )

    def test_live_process_classifier_detects_custom_tomac_smoke_with_root_arg(self) -> None:
        command = (
            "/opt/homebrew/Cellar/python@3.13/3.13.12_1/Frameworks/Python.framework/Versions/3.13/"
            "Resources/Python.app/Contents/MacOS/Python /tmp/tomac_nq_strict_ote_density_repair_smoke.py "
            "--root /tmp/ict-engine-tomac-nq-strict-ote-density-repair-fullwindow-20260525T130328+0800 "
            "--start 2021-01-01 --end 2025-12-31 23:59:59 --max-rows 2000000"
        )

        self.assertTrue(_is_live_factor_command(command))
        self.assertEqual(
            _extract_run_root(command),
            Path("/tmp/ict-engine-tomac-nq-strict-ote-density-repair-fullwindow-20260525T130328+0800"),
        )

    def test_extract_run_root_from_provider_output_inside_run_root(self) -> None:
        command = (
            "/opt/homebrew/bin/python3 support/scripts/auto_quant_external/fetch_external.py "
            "ibkr-historical --symbol AVGO --bar-size 15 mins --duration 1 M "
            "--output /Users/example/ict-engine/support/docs/experiments/"
            "actionable-regime-confidence/runs/20260524T213610+0800-codex-ibkr-avgo/"
            "data/provider/raw/ibkr_avgo_15m_1m.csv"
        )

        self.assertEqual(
            _extract_run_root(command),
            Path(
                "/Users/example/ict-engine/support/docs/experiments/"
                "actionable-regime-confidence/runs/20260524T213610+0800-codex-ibkr-avgo"
            ),
        )

    def test_extract_run_root_from_tmp_provider_output_csv_parent(self) -> None:
        command = (
            "/opt/homebrew/bin/python3 support/scripts/auto_quant_external/fetch_external.py "
            "yahoo --symbol TEM --interval 15m --start 2026-03-26 --end 2026-05-24 "
            "--output /tmp/ict-engine-yf-tem-trend-mtf-20260524T2213+0800/tem_15m.csv"
        )

        self.assertEqual(
            _extract_run_root(command),
            Path("/tmp/ict-engine-yf-tem-trend-mtf-20260524T2213+0800"),
        )

    def test_extract_run_root_normalizes_tmp_lane_subdirs(self) -> None:
        lane_root = Path("/tmp/ict-engine-kraken-ltcusd-supertrend-adx-1m-mtf-gate1")
        commands = [
            f"/opt/homebrew/bin/python3 {lane_root}/scripts/run_kraken_ltcusd_supertrend_adx_1m_mtf_gate1_v1.py",
            f"ict-engine auto-quant-agent-material-dispatch --symbol KRAKEN_LTCUSD --state-dir {lane_root}/state",
            f"/bin/zsh -lc RUN_ROOT={lane_root}/checks python3 helper.py",
            f"fetch_external.py kraken-kline --output {lane_root}/data/provider/raw/kraken_linkusd_4h.csv",
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(_extract_run_root(command), lane_root)

    def test_infer_exit_file_from_provider_output_timeframe_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "runs" / "20260524T213610+0800-codex-ibkr-avgo"
            checks_dir = run_root / "checks"
            checks_dir.mkdir(parents=True)
            (checks_dir / "00_provider_status_ibkr.exit").write_text("0\n", encoding="utf-8")
            command = (
                "/opt/homebrew/bin/python3 support/scripts/auto_quant_external/fetch_external.py "
                "ibkr-historical --symbol AVGO --bar-size 30 mins --duration 1 M "
                f"--output {run_root}/data/provider/raw/ibkr_avgo_30m_1m.csv"
            )

            self.assertEqual(
                _infer_exit_file(run_root, command),
                checks_dir / "fetch_30m_1m.exit",
            )

    def test_attribute_parent_run_roots_from_child_provider_process(self) -> None:
        run_root = (
            "/Users/example/ict-engine/support/docs/experiments/"
            "actionable-regime-confidence/runs/20260524T221141+0800-codex-ibkr-mes"
        )
        processes = [
            {
                "pid": 52673,
                "ppid": 61304,
                "elapsed": "08:47",
                "run_root": None,
                "exit_file": None,
                "exit_file_exists": False,
                "command_excerpt": "python support/docs/experiments/scripts/run_ibkr_futures_strict_trend_root_ote_overlay_1m_mtf_gate1_v1.py",
            },
            {
                "pid": 59345,
                "ppid": 52673,
                "elapsed": "02:43",
                "run_root": run_root,
                "exit_file": f"{run_root}/checks/fetch_15m_1m.exit",
                "exit_file_exists": False,
                "command_excerpt": "python support/scripts/auto_quant_external/fetch_external.py ibkr-historical --symbol MES",
            },
        ]

        attributed = _attribute_parent_run_roots(processes)

        self.assertEqual(attributed[0]["run_root"], run_root)
        self.assertEqual(attributed[0]["run_root_attribution"], "child_process")
        self.assertEqual(attributed[0]["run_root_attribution_pid"], 59345)
        self.assertEqual(attributed[1]["run_root"], run_root)

    def test_attribute_child_run_root_from_parent_autoquant_process(self) -> None:
        run_root = "/tmp/ict-engine-kraken-ltcusd-supertrend-adx-1m-mtf-gate1"
        processes = [
            {
                "pid": 78480,
                "ppid": 78045,
                "elapsed": "00:27",
                "run_root": run_root,
                "exit_file": None,
                "exit_file_exists": False,
                "command_excerpt": "ict-engine auto-quant-agent-material-dispatch --state-dir /tmp/ict-engine-kraken/state",
            },
            {
                "pid": 79145,
                "ppid": 78480,
                "elapsed": "00:01",
                "run_root": None,
                "exit_file": None,
                "exit_file_exists": False,
                "command_excerpt": "/Users/example/Auto-Quant/.venv/bin/python run_tomac.py",
            },
        ]

        attributed = _attribute_parent_run_roots(processes)

        self.assertEqual(attributed[1]["run_root"], run_root)
        self.assertEqual(attributed[1]["run_root_attribution"], "parent_process")
        self.assertEqual(attributed[1]["run_root_attribution_pid"], 78480)

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
                    "agent_name": "codex-active-lane",
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
                    "agent_name": "codex-positive-review",
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
        self.assertEqual([claim["agent_name"] for claim in compact["attention_claims"]], ["codex-active-lane", "codex-positive-review"])
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
