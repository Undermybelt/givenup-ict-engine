#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from factor_claim_terminalization_audit import (  # noqa: E402
    _drop_stale_failed_tomac_prep_wrappers,
    _attribute_parent_run_roots,
    _attribute_run_roots_from_cwd,
    _compact_text,
    _extract_run_root,
    _infer_exit_file,
    _is_live_factor_command,
    build_report,
    format_report,
    parse_claim_text,
    summarize,
)


class FactorClaimTerminalizationAuditTest(unittest.TestCase):
    def test_compact_live_process_marks_exit_file_stale_for_current_process(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "ict-engine-live-root"
            checks = run_root / "checks"
            checks.mkdir(parents=True)
            exit_file = checks / "tomac_aq.exit"
            exit_file.write_text("1\n", encoding="utf-8")

            # The exit file predates a currently running process and must not be
            # presented as a current terminal result for the live process.
            stale_mtime = datetime.now(timezone.utc).timestamp() - 600
            exit_file.touch()
            os.utime(exit_file, (stale_mtime, stale_mtime))

            report = {
                "schema_version": "factor-claim-terminalization-audit/v1",
                "generated_at": "2026-05-28T01:10:00+00:00",
                "claims_dir": str(Path(tmp) / "claims"),
                "repo_root": "/Users/example/ict-engine",
                "summary": {"status": "needs_attention"},
                "claims": [],
                "live_factor_processes": [
                    {
                        "pid": 123,
                        "ppid": 1,
                        "elapsed": "00:30",
                        "run_root": str(run_root),
                        "exit_file": str(exit_file),
                        "exit_file_exists": True,
                        "command_excerpt": "python run_tomac_index_futures_clean_aq_v1.py",
                    }
                ],
            }

            compact = format_report(report, compact=True)

        self.assertEqual(compact["attention_live_processes"][0]["exit_file_state"], "stale_for_process")

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

    def test_parse_claim_text_does_not_infer_true_from_negated_non_goals_without_explicit_fields(self) -> None:
        parsed = parse_claim_text(
            """
agent_name=codex-xlc-child
owner=codex
scope=child takeover
active_task=materialize exact child helper
non_goals=no same-turn fetch; no promotion_allowed=true; no trade_usable=true
write_surface=/tmp/example-workdoc.md
run_root=/tmp/example-run
status=active
"""
        )

        self.assertIsNone(parsed["promotion_allowed"])
        self.assertIsNone(parsed["trade_usable"])

    def test_summarize_treats_nested_live_run_root_under_tmp_root_as_live_runtime_owner(self) -> None:
        claims = [
            {
                "claim_file": "nested-live.claim",
                "status": "active",
                "owner": "codex",
                "agent_name": "codex-nested-live",
                "scope": "same-root child loop",
                "active_task": "wait for current aq child",
                "run_root": "/tmp/ict-engine-parent",
                "tmp_root": "/tmp/ict-engine-parent",
                "run_root_exists": True,
                "missing_identity_fields": [],
                "promotion_allowed": False,
                "trade_usable": False,
                "last_progress_at": "2026-05-27T20:53:20+0800",
            }
        ]
        live_processes = [
            {
                "pid": 1,
                "ppid": 2,
                "elapsed": "00:10",
                "run_root": "/tmp/ict-engine-parent/aq",
                "exit_file": None,
                "exit_file_exists": False,
                "command_excerpt": "python run_tomac.py",
            }
        ]

        summary = summarize(
            claims,
            live_processes=live_processes,
            now=datetime(2026, 5, 27, 14, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(summary["active_claims_without_live_process"], 0)
        self.assertEqual(summary["wait_only_active_claims_without_live_process"], 0)
        self.assertFalse(claims[0]["wait_only_without_live_process"])
        self.assertTrue(claims[0]["live_runtime_owner"])

    def test_summarize_treats_matching_factor_id_without_run_root_as_live_runtime_owner(self) -> None:
        claims = [
            {
                "claim_file": "wpr-live.claim",
                "status": "active",
                "owner": "codex",
                "agent_name": "codex-wpr-live",
                "scope": "reference hurst launch",
                "active_task": "wait for generic aq workspace runner",
                "run_root": "/tmp/ict-engine-wpr-launch",
                "tmp_root": "/tmp/ict-engine-wpr-launch",
                "run_root_exists": True,
                "missing_identity_fields": [],
                "promotion_allowed": False,
                "trade_usable": False,
                "last_progress_at": "2026-05-27T23:38:46+0800",
                "factor_id": "tomac_idxfut_clean_wpr_adx_reference_hurst_profile_range_compression_release_1m_v1",
                "branch_path": "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprAdxTrendAlignedReclaim -> HurstProfileMssReclaim -> ReferenceHurstProfileRangeCompressionRelease -> tomac_idxfut_clean_wpr_adx_reference_hurst_profile_range_compression_release_1m_v1",
            }
        ]
        live_processes = [
            {
                "pid": 1374,
                "ppid": 94167,
                "elapsed": "01:42",
                "run_root": None,
                "exit_file": None,
                "exit_file_exists": False,
                "command_excerpt": "/Users/example/Auto-Quant/.venv/bin/python run_tomac.py",
                "factor_id": "tomac_idxfut_clean_wpr_adx_reference_hurst_profile_range_compression_release_1m_v1",
                "branch_path": "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprAdxTrendAlignedReclaim -> HurstProfileMssReclaim -> ReferenceHurstProfileRangeCompressionRelease -> tomac_idxfut_clean_wpr_adx_reference_hurst_profile_range_compression_release_1m_v1",
            }
        ]

        summary = summarize(
            claims,
            live_processes=live_processes,
            now=datetime(2026, 5, 27, 15, 45, tzinfo=timezone.utc),
        )

        self.assertEqual(summary["active_claims_without_live_process"], 0)
        self.assertTrue(claims[0]["live_runtime_owner"])

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

    def test_build_report_excludes_terminalized_status_variants_from_active_claims(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            run_root = repo_root / "support" / "docs" / "experiments" / "run-a"
            run_root.mkdir(parents=True)

            (claims_dir / "terminal-variant.claim").write_text(
                f"""
owner=codex
run_root={run_root}
status=terminalized_superseded_by_runtime_repair_takeover
terminalized_at=2026-05-27T22:27:40+0800
decision=terminalized_superseded_by_runtime_repair_takeover
promotion_allowed=false
trade_usable=false
""",
                encoding="utf-8",
            )

            report = build_report(claims_dir=claims_dir, repo_root=repo_root)

            self.assertEqual(report["summary"]["total_claims"], 1)
            self.assertEqual(report["summary"]["terminalized_claims"], 1)
            self.assertEqual(report["summary"]["active_claims"], 0)
            self.assertEqual(report["summary"]["valid_active_claims"], 0)
            self.assertEqual(report["summary"]["invalid_active_claims"], 0)

    def test_build_report_keeps_explicit_active_status_even_when_decision_field_exists(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            run_root = repo_root / "support" / "docs" / "experiments" / "run-active"
            run_root.mkdir(parents=True)

            (claims_dir / "active-with-decision.claim").write_text(
                f"""
agent_name=codex-runtime-replay
owner=codex
claimed_at=2026-05-27T13:50:04+0800
last_progress_at=2026-05-27T15:52:23+0800
scope=Board B same-root runtime replay
active_task=continue direct replay after runtime fix
non_goals=no promotion
write_surface=/tmp/example-workdoc.md
run_root={run_root.relative_to(repo_root)}
status=active_debug_replay_after_runtime_fix
progress_report=/tmp/example-progress.md
decision=active_replay_after_runtime_fix
promotion_allowed=false
trade_usable=false
""",
                encoding="utf-8",
            )

            report = build_report(claims_dir=claims_dir, repo_root=repo_root)

            self.assertEqual(report["summary"]["terminalized_claims"], 0)
            self.assertEqual(report["summary"]["active_claims"], 1)
            self.assertEqual(report["claims"][0]["status"], "active")

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
            (claims_dir / "stale-active-decision.claim").write_text(
                f"""
agent_name=codex-derived-terminal-stale-active
owner=codex
claimed_at=2026-05-27T13:50:04+0800
last_progress_at=2026-05-27T13:55:00+0800
scope=Board B same-root terminal packet with stale active decision
active_task=read stale active decision after terminal metrics landed
non_goals=no relaunch
write_surface=/tmp/example-stale-active-workdoc.md
run_root={decision_run_root.relative_to(repo_root)}
status=active
decision=active_loop_still_running
progress_report=/tmp/example-stale-active-progress.md
promotion_allowed=false
trade_usable=false
""",
                encoding="utf-8",
            )

            report = build_report(claims_dir=claims_dir, repo_root=repo_root)

            self.assertEqual(report["summary"]["terminalized_claims"], 3)
            self.assertEqual(report["summary"]["active_claims"], 0)
            self.assertEqual(
                [claim["status"] for claim in report["claims"]],
                ["terminalized", "terminalized", "terminalized"],
            )

    def test_compact_portable_paths_collapses_tmp_runtime_paths(self) -> None:
        report = {
            "schema_version": "factor-claim-terminalization-audit/v1",
            "generated_at": "2026-05-27T12:00:00+00:00",
            "claims_dir": "/tmp/ict-engine-agent-claims/board-b-factor-refinement",
            "repo_root": "/Users/example/projects/ict-engine",
            "summary": {"status": "needs_attention"},
            "claims": [
                {
                    "claim_file": "demo.claim",
                    "status": "active",
                    "agent_name": "codex",
                    "owner": "codex",
                    "scope": "demo",
                    "decision": None,
                    "run_root": "/private/tmp/ict-engine-demo-run",
                    "run_root_exists": True,
                    "missing_identity_fields": [],
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "age_minutes": 1,
                    "live_runtime_owner": False,
                    "wait_only_without_live_process": False,
                    "stale_safe_takeover_candidate": False,
                    "summary_files": [],
                }
            ],
            "live_factor_processes": [
                {
                    "pid": 1,
                    "ppid": 2,
                    "elapsed": "00:01",
                    "run_root": "/private/tmp/ict-engine-demo-run",
                    "exit_file": "/private/tmp/ict-engine-demo-run/checks/round_00.exit",
                    "exit_file_exists": True,
                    "command_excerpt": "python /private/tmp/ict-engine-demo-run/run_tomac.py",
                }
            ],
        }

        compact = format_report(report, compact=True, portable_paths=True)

        self.assertEqual(compact["claims_dir"], "ict-engine-agent-claims/board-b-factor-refinement")
        self.assertEqual(compact["attention_live_processes"][0]["run_root"], "ict-engine-demo-run")
        self.assertEqual(
            compact["attention_live_processes"][0]["exit_file"],
            "ict-engine-demo-run/checks/round_00.exit",
        )
        self.assertEqual(
            compact["attention_live_processes"][0]["command_excerpt"],
            "python ict-engine-demo-run/run_tomac.py",
        )

    def test_compact_text_portable_paths_preserves_non_tmp_strings(self) -> None:
        value = _compact_text("factor_closure_blocked", root="/Users/example/projects/ict-engine", portable_paths=True)
        self.assertEqual(value, "factor_closure_blocked")

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
        self.assertIn("wait for fresh active claims to progress", summary["next_action"])
        self.assertIn("restore or terminalize missing run roots", summary["next_action"])
        self.assertIn("review positive trade/promotion flags", summary["next_action"])

    def test_terminalized_no_launch_missing_root_does_not_block_closure(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            missing_root = Path(repo_tmp) / "never-created-aq-root"
            (claims_dir / "duplicate-no-launch.claim").write_text(
                f"""
agent_name=codex-duplicate-no-launch
owner=codex
status=terminalized_duplicate_collision_deferred
decision=terminalized_duplicate_collision_deferred_no_launch
scope=duplicate launch packet that intentionally never created AQ output
run_root={missing_root}
promotion_allowed=false
trade_usable=false
""",
                encoding="utf-8",
            )

            report = build_report(claims_dir=claims_dir, repo_root=repo_root)

        self.assertEqual(report["summary"]["status"], "pass")
        self.assertEqual(report["summary"]["terminalized_claims"], 1)
        self.assertEqual(report["summary"]["missing_run_roots"], 0)
        self.assertEqual(report["summary"]["blocking_reasons"], [])
        self.assertFalse(report["claims"][0]["missing_run_root_attention"])

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

    def test_build_report_marks_stale_safe_takeover_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            stale_run_root = repo_root / "support" / "docs" / "experiments" / "stale-run"
            stale_run_root.mkdir(parents=True)
            fresh_run_root = repo_root / "support" / "docs" / "experiments" / "fresh-run"
            fresh_run_root.mkdir(parents=True)

            (claims_dir / "stale-active.claim").write_text(
                f"""
agent_name=codex-stale-lane
owner=codex
claimed_at=2026-05-27T13:00:00+0800
last_progress_at=2026-05-27T13:05:00+0800
scope=Board B stale active lane
active_task=wait for next action
non_goals=no duplicate launch
write_surface=/tmp/stale-workdoc.md
run_root={stale_run_root.relative_to(repo_root)}
status=active_prep_only_contract_ready
progress_report=/tmp/stale-progress.md
promotion_allowed=false
trade_usable=false
""",
                encoding="utf-8",
            )
            (claims_dir / "fresh-active.claim").write_text(
                f"""
agent_name=codex-fresh-lane
owner=codex
claimed_at=2026-05-27T15:50:00+0800
last_progress_at=2026-05-27T15:55:00+0800
scope=Board B fresh active lane
active_task=still running
non_goals=no duplicate launch
write_surface=/tmp/fresh-workdoc.md
run_root={fresh_run_root.relative_to(repo_root)}
status=active_launch_ready
progress_report=/tmp/fresh-progress.md
promotion_allowed=false
trade_usable=false
""",
                encoding="utf-8",
            )

            report = build_report(
                claims_dir=claims_dir,
                repo_root=repo_root,
                live_processes=[],
                now=datetime(2026, 5, 27, 8, 10, 0, tzinfo=timezone.utc),
            )
            compact = format_report(report, compact=True)

            self.assertEqual(report["summary"]["stale_active_claims"], 1)
            self.assertEqual(report["summary"]["stale_safe_takeover_candidates"], 1)
            stale_claim = next(claim for claim in compact["attention_claims"] if claim["claim_file"] == "stale-active.claim")
            fresh_claim = next(claim for claim in compact["attention_claims"] if claim["claim_file"] == "fresh-active.claim")
            self.assertTrue(stale_claim["stale_safe_takeover_candidate"])
            self.assertGreaterEqual(stale_claim["age_minutes"], 60)
            self.assertFalse(fresh_claim["stale_safe_takeover_candidate"])

    def test_summarize_surfaces_non_live_wait_only_active_claim_debt(self) -> None:
        summary = summarize(
            [
                {
                    "status": "active_prep_surface_ready_wait_board_clear",
                    "run_root": "/tmp/ict-engine-wait-only",
                    "tmp_root": "/tmp/ict-engine-wait-only",
                    "run_root_exists": True,
                    "decision": "launch_ready_prep_only_wait_live_factor_processes_to_clear",
                    "active_task": "wait for shared writers to clear before launch",
                    "scope": "Board B exact child prep",
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "missing_identity_fields": [],
                },
                {
                    "status": "active_exact_gate1_launch_in_flight",
                    "run_root": "/Users/example/repo/support/docs/experiments/run-live-owner",
                    "tmp_root": "/tmp/ict-engine-live-owner",
                    "run_root_exists": True,
                    "decision": "exact_iwm_rerelaunch_with_repaired_timeout_handler_and_longer_1m_budget_in_flight",
                    "active_task": "wait for terminal metrics after exact rerelaunch",
                    "scope": "Board B exact live runner",
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "missing_identity_fields": [],
                },
            ],
            live_processes=[
                {
                    "pid": 12345,
                    "ppid": 123,
                    "elapsed": "00:12",
                    "command_excerpt": "python /tmp/run_ibkr_iwm_exact.py --root /tmp/ict-engine-live-owner",
                    "run_root": "/tmp/ict-engine-live-owner",
                    "exit_file": None,
                    "exit_file_exists": False,
                }
            ],
        )

        self.assertEqual(summary["active_claims"], 2)
        self.assertEqual(summary["active_claims_without_live_process"], 1)
        self.assertEqual(summary["wait_only_active_claims_without_live_process"], 1)
        self.assertEqual(summary["fresh_wait_only_active_claims_without_live_process"], 1)
        self.assertEqual(summary["stale_wait_only_active_claims_without_live_process"], 0)
        self.assertIn(
            "wait for fresh wait-only claims to progress or stale-safe timeout",
            summary["next_action"],
        )
        self.assertNotIn("terminalize or externalize active claims", summary["next_action"])

    def test_summarize_surfaces_stale_wait_only_claims_as_cleanup(self) -> None:
        summary = summarize(
            [
                {
                    "status": "active_prep_surface_ready_wait_board_clear",
                    "run_root": "/tmp/ict-engine-stale-wait",
                    "tmp_root": "/tmp/ict-engine-stale-wait",
                    "run_root_exists": True,
                    "decision": "launch_ready_prep_only_wait_live_factor_processes_to_clear",
                    "active_task": "wait for shared writers to clear before launch",
                    "scope": "Board B stale wait-only claim",
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "missing_identity_fields": [],
                    "last_progress_at": "2026-05-27T14:00:00+00:00",
                }
            ],
            live_processes=[],
            now=datetime(2026, 5, 27, 16, 0, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(summary["wait_only_active_claims_without_live_process"], 1)
        self.assertEqual(summary["fresh_wait_only_active_claims_without_live_process"], 0)
        self.assertEqual(summary["stale_wait_only_active_claims_without_live_process"], 1)
        self.assertIn(
            "terminalize or externalize active claims",
            summary["next_action"],
        )
        self.assertIn(
            "externalize or terminalize stale-safe wait-only active claims that do not own a live runtime",
            summary["next_action"],
        )

    def test_summarize_surfaces_fresh_active_claims_without_live_process_as_wait_not_cleanup(self) -> None:
        summary = summarize(
            [
                {
                    "status": "active_setup",
                    "run_root": "/tmp/ict-engine-fresh-active",
                    "tmp_root": "/tmp/ict-engine-fresh-active",
                    "run_root_exists": True,
                    "decision": None,
                    "active_task": "create packet then inspect live claims",
                    "scope": "Board B fresh continuation setup",
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "missing_identity_fields": [],
                    "last_progress_at": "2026-05-27T15:59:00+00:00",
                }
            ],
            live_processes=[],
            now=datetime(2026, 5, 27, 16, 0, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(summary["active_claims"], 1)
        self.assertEqual(summary["active_claims_without_live_process"], 1)
        self.assertEqual(summary["wait_only_active_claims_without_live_process"], 0)
        self.assertEqual(summary["stale_safe_takeover_candidates"], 0)
        self.assertEqual(summary["fresh_active_claims_without_live_process"], 1)
        self.assertIn(
            "wait for fresh active claims to progress, then rerun before terminalizing",
            summary["next_action"],
        )
        self.assertNotIn("terminalize or externalize active claims", summary["next_action"])

    def test_summarize_matches_tmp_and_private_tmp_live_runtime_roots(self) -> None:
        summary = summarize(
            [
                {
                    "status": "active",
                    "run_root": "/tmp/ict-engine-tomac-example-20260528T211900+0800/run",
                    "tmp_root": "/tmp/ict-engine-tomac-example-20260528T211900+0800",
                    "run_root_exists": True,
                    "decision": "exact_aq_launch_in_progress",
                    "active_task": "wait for terminal exact-AQ evidence",
                    "scope": "Board B exact AQ launch",
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "missing_identity_fields": [],
                    "last_progress_at": "2026-05-28T13:19:00+00:00",
                }
            ],
            live_processes=[
                {
                    "pid": 15179,
                    "ppid": 10858,
                    "elapsed": "02:07",
                    "command_excerpt": "python run_tomac.py",
                    "run_root": "/private/tmp/ict-engine-tomac-example-20260528T211900+0800",
                    "exit_file": None,
                    "exit_file_exists": False,
                }
            ],
            now=datetime(2026, 5, 28, 13, 36, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(summary["active_claims"], 1)
        self.assertEqual(summary["live_factor_processes"], 1)
        self.assertEqual(summary["active_claims_without_live_process"], 0)
        self.assertEqual(summary["fresh_active_claims_without_live_process"], 0)
        self.assertNotIn(
            "wait for fresh active claims to progress, then rerun before terminalizing",
            summary["next_action"],
        )
        self.assertIn(
            "wait for live factor processes to exit or claim them before closure",
            summary["next_action"],
        )

    def test_format_report_compact_surfaces_fresh_active_claim_queue(self) -> None:
        full_report = {
            "schema_version": "factor-claim-terminalization-audit/v1",
            "generated_at": "2026-05-28T01:14:00+00:00",
            "claims_dir": "/tmp/claims",
            "repo_root": "/repo",
            "summary": {
                "status": "needs_attention",
                "active_claims": 1,
                "fresh_active_claims_without_live_process": 1,
            },
            "claims": [
                {
                    "claim_file": "fresh.claim",
                    "claim_path": "/tmp/claims/fresh.claim",
                    "status": "active",
                    "agent_name": "codex-fresh",
                    "owner": "codex",
                    "scope": "fresh setup",
                    "run_root": "/tmp/fresh",
                    "run_root_exists": True,
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "age_minutes": 2,
                    "live_runtime_owner": False,
                    "wait_only_without_live_process": False,
                    "stale_safe_takeover_candidate": False,
                    "fresh_without_live_process": True,
                    "missing_identity_fields": [],
                    "summary_files": [],
                }
            ],
            "live_factor_processes": [],
        }

        compact = format_report(full_report, compact=True)

        self.assertEqual(
            compact["attention_groups"]["by_actionability"],
            {"fresh_active_without_live_process": 1},
        )
        self.assertEqual(
            compact["attention_action_queue"]["fresh_active_claims_without_live_process"],
            [
                {
                    "claim_file": "fresh.claim",
                    "age_minutes": 2,
                    "status": "active",
                }
            ],
        )

    def test_valid_audit_only_coordination_claim_does_not_block_factor_closure(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            run_root = Path(repo_tmp) / "ict-engine-closed-loop-loophole-audit"
            run_root.mkdir()
            (run_root / "workdoc.md").write_text("# audit\n", encoding="utf-8")

            (claims_dir / "audit-only.claim").write_text(
                json.dumps(
                    {
                        "schema_version": "board-b-factor-claim/v1",
                        "agent_name": "codex-closed-loop-loophole-audit",
                        "owner": "codex",
                        "claimed_at": "2026-05-29T00:36:43+0800",
                        "last_progress_at": "2026-05-29T00:36:43+0800",
                        "scope": "Closed-loop factor-training loophole audit and current objective evidence review; no provider, IBKR, Auto-Quant, freqtrade, or run_tomac launch.",
                        "active_task": "Audit current evidence, objective snapshot coverage, active claims, and code-level done-definition gaps; patch only concrete verified defects.",
                        "non_goals": [
                            "Do not launch provider, IBKR, Auto-Quant, freqtrade, or run_tomac.py during this audit claim.",
                            "Do not touch active TOMAC factor lanes except read-only claim/workdoc/artifact inspection.",
                            "Do not mark promotion_allowed, trade_usable, or update_goal true unless the full current closed-loop evidence proves it.",
                        ],
                        "write_surface": str(run_root / "workdoc.md"),
                        "run_root": str(run_root),
                        "tmp_root": str(run_root),
                        "branch_path": "objective-closure-audit -> factor-training closed-loop loophole ledger",
                        "factor_id": "closed_loop_factor_training_loophole_audit_20260529T003643",
                        "status": "active_audit_only",
                        "decision": "objective_not_proven_audit_in_progress",
                        "progress_report": "promotion_allowed=false trade_usable=false update_goal=false",
                        "promotion_allowed": False,
                        "trade_usable": False,
                        "update_goal": False,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            report = build_report(claims_dir=claims_dir, repo_root=repo_root)
            compact = format_report(report, compact=True)

        self.assertEqual(report["summary"]["status"], "pass")
        self.assertEqual(report["summary"]["active_claims"], 0)
        self.assertEqual(report["summary"]["coordination_only_active_claims"], 1)
        self.assertEqual(report["summary"]["blocking_reasons"], [])
        self.assertEqual(compact["attention_claim_count"], 0)
        self.assertEqual(compact["attention_action_queue"]["fresh_active_claims_without_live_process"], [])

    def test_valid_inventory_claim_does_not_block_factor_closure(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp, tempfile.TemporaryDirectory() as claims_tmp:
            repo_root = Path(repo_tmp)
            claims_dir = Path(claims_tmp)
            run_root = Path(repo_tmp) / "ict-engine-false-negative-amnesty"
            run_root.mkdir()
            (run_root / "workdoc.md").write_text("# inventory\n", encoding="utf-8")

            (claims_dir / "inventory.claim.json").write_text(
                json.dumps(
                    {
                        "agent_name": "hermes-gpt55-false-negative-amnesty",
                        "owner": "Hermes GPT-5.5",
                        "claimed_at": "20260529T013008",
                        "last_progress_at": "20260529T013008",
                        "scope": "False-negative amnesty inventory for old readiness/transition/PDA blockers",
                        "active_task": "Scan artifacts for candidates wrongly blocked by old gates; no provider/AQ launch yet",
                        "non_goals": "No Board docs as active source; no trade usability promotion without current artifacts",
                        "write_surface": str(run_root / "workdoc.md"),
                        "run_root": str(run_root),
                        "tmp_root": str(run_root),
                        "status": "active_inventory",
                        "progress_report": "created claim/workdoc/repo packet; next run compact audit and artifact scans",
                        "promotion_allowed": False,
                        "trade_usable": False,
                        "update_goal": False,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            report = build_report(claims_dir=claims_dir, repo_root=repo_root)
            compact = format_report(report, compact=True)

        self.assertEqual(report["summary"]["status"], "pass")
        self.assertEqual(report["summary"]["active_claims"], 0)
        self.assertEqual(report["summary"]["coordination_only_active_claims"], 1)
        self.assertEqual(report["summary"]["blocking_reasons"], [])
        self.assertEqual(compact["attention_claim_count"], 0)
        self.assertEqual(compact["attention_action_queue"]["fresh_active_claims_without_live_process"], [])

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

    def test_live_process_classifier_ignores_tomac_provider_parity_probe_diagnostics(self) -> None:
        command = (
            "/opt/homebrew/Cellar/python@3.13/3.13.12_1/Frameworks/Python.framework/Versions/3.13/"
            "Resources/Python.app/Contents/MacOS/Python "
            "support/scripts/research/tomac_tod_balanced_provider_parity_probe.py "
            "--root /tmp/ict-engine-tomac-tod-balanced-practical-repair-20260526T214903+0800"
        )

        self.assertFalse(_is_live_factor_command(command))

    def test_live_process_classifier_ignores_tomac_matrix_diagnostics(self) -> None:
        command = (
            "/opt/homebrew/Cellar/python@3.13/3.13.12_1/Frameworks/Python.framework/Versions/3.13/"
            "Resources/Python.app/Contents/MacOS/Python "
            "support/scripts/research/tomac_factor_coverage_matrix.py "
            "--tomac-root support/docs/experiments/actionable-regime-confidence/runs"
        )

        self.assertFalse(_is_live_factor_command(command))

    def test_live_process_classifier_ignores_run_tomac_help_probe(self) -> None:
        command = (
            "/opt/homebrew/Cellar/python@3.13/3.13.12_1/Frameworks/Python.framework/Versions/3.13/"
            "Resources/Python.app/Contents/MacOS/Python "
            "/private/tmp/ict-engine-tomac-opening-drive-twoleg-participation-quality-persistence-lift-autoquant-loop-20260528T011500/"
            "aq_workspace/run_tomac.py --help"
        )

        self.assertFalse(_is_live_factor_command(command))

    def test_live_process_classifier_ignores_unittest_names_with_factor_markers(self) -> None:
        command = (
            "/opt/homebrew/Cellar/python@3.13/3.13.12_1/Frameworks/Python.framework/Versions/3.13/"
            "Resources/Python.app/Contents/MacOS/Python -m unittest "
            "support.scripts.tests.test_factor_claim_terminalization_audit."
            "FactorClaimTerminalizationAuditTest."
            "test_live_process_classifier_ignores_run_tomac_help_probe -v"
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

    def test_drop_stale_failed_tomac_prep_wrappers_drops_terminalized_parent_without_child(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "ict-engine-tomac-balanced-structure-ict-transition-hazard-trim-prep"
            checks = run_root / "checks"
            summaries = run_root / "summaries"
            checks.mkdir(parents=True)
            summaries.mkdir(parents=True)
            (checks / "terminal_metrics.json").write_text('{"decision":"observation"}\n', encoding="utf-8")
            (checks / "round_03_run_tomac.exit").write_text("0\n", encoding="utf-8")
            (summaries / "terminal_decision_summary.md").write_text("Decision: observation\n", encoding="utf-8")

            wrapper = {
                "pid": 50109,
                "ppid": 46666,
                "elapsed": "43:02",
                "run_root": str(run_root),
                "exit_file": str(checks / "round_03_run_tomac.exit"),
                "exit_file_exists": True,
                "command_excerpt": (
                    "python support/docs/experiments/actionable-regime-confidence/scripts/"
                    f"run_tomac_tod_balanced_structure_ict_transition_hazard_trim_prep_v1.py --root {run_root} --launch"
                ),
            }

            self.assertEqual(_drop_stale_failed_tomac_prep_wrappers([wrapper]), [])

    def test_drop_stale_failed_tomac_prep_wrappers_drops_terminalized_run_tomac_child_without_descendants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "ict-engine-opening-drive-structure-ict-transition-hazard-trim-prep" / "aq"
            checks = run_root / "checks"
            summaries = run_root / "summaries"
            checks.mkdir(parents=True)
            summaries.mkdir(parents=True)
            (checks / "terminal_metrics.json").write_text('{"decision":"observation"}\n', encoding="utf-8")
            (checks / "round_03_run_tomac.exit").write_text("0\n", encoding="utf-8")
            (summaries / "terminal_decision_summary.md").write_text("Decision: observation\n", encoding="utf-8")

            child = {
                "pid": 68979,
                "ppid": 49561,
                "elapsed": "07:52",
                "run_root": str(run_root),
                "exit_file": str(checks / "round_03_run_tomac.exit"),
                "exit_file_exists": True,
                "command_excerpt": "[local-path] run_tomac.py",
            }

            self.assertEqual(_drop_stale_failed_tomac_prep_wrappers([child]), [])

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

    def test_attribute_run_root_from_cwd_for_local_run_tomac_child_without_parent_context(self) -> None:
        run_root = "/private/tmp/ict-engine-tomac-prior-day-extreme-mtf-resonance-guard-participation-quality-guard-prep-20260527T135004+0800"
        processes = [
            {
                "pid": 34279,
                "ppid": 19372,
                "elapsed": "03:38",
                "run_root": None,
                "exit_file": None,
                "exit_file_exists": False,
                "command_excerpt": "/Users/example/Auto-Quant/.venv/bin/python run_tomac.py",
            },
        ]

        attributed = _attribute_run_roots_from_cwd(
            processes,
            {
                34279: f"{run_root}/aq/aq_workspaces/1m",
            },
        )

        self.assertEqual(attributed[0]["run_root"], run_root)
        self.assertEqual(attributed[0]["run_root_attribution"], "cwd")
        self.assertEqual(attributed[0]["run_root_attribution_pid"], 34279)

    def test_attribute_workspace_identity_from_generic_aq_workspace_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "aq-debug" / "aq_workspaces" / "1m"
            strategies = workspace / "user_data" / "strategies_external"
            strategies.mkdir(parents=True)
            (strategies / "TomacNQWpr.py").write_text(
                """
class Dummy:
    \"""
    factor_id: tomac_idxfut_clean_wpr_adx_reference_hurst_profile_range_compression_release_1m_v1
    branch_path: RangeReversion -> PdhPdlFractalLiquiditySweep -> WprAdxTrendAlignedReclaim -> HurstProfileMssReclaim -> ReferenceHurstProfileRangeCompressionRelease -> tomac_idxfut_clean_wpr_adx_reference_hurst_profile_range_compression_release_1m_v1
    \"""
""",
                encoding="utf-8",
            )
            processes = [
                {
                    "pid": 1374,
                    "ppid": 94167,
                    "elapsed": "01:42",
                    "run_root": None,
                    "exit_file": None,
                    "exit_file_exists": False,
                    "command_excerpt": "/Users/example/Auto-Quant/.venv/bin/python run_tomac.py",
                }
            ]

            attributed = _attribute_run_roots_from_cwd(
                processes,
                {1374: str(workspace)},
            )

        self.assertIsNone(attributed[0]["run_root"])
        self.assertEqual(
            attributed[0]["factor_id"],
            "tomac_idxfut_clean_wpr_adx_reference_hurst_profile_range_compression_release_1m_v1",
        )
        self.assertEqual(
            attributed[0]["branch_path"],
            "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprAdxTrendAlignedReclaim -> HurstProfileMssReclaim -> ReferenceHurstProfileRangeCompressionRelease -> tomac_idxfut_clean_wpr_adx_reference_hurst_profile_range_compression_release_1m_v1",
        )
        self.assertEqual(attributed[0]["run_root_attribution"], "cwd_workspace_identity")

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
                    "age_minutes": 91,
                    "live_runtime_owner": False,
                    "wait_only_without_live_process": True,
                    "stale_safe_takeover_candidate": True,
                    "summary_files": [],
                },
                {
                    "claim_file": "fresh-missing.claim",
                    "claim_path": "/tmp/claims/fresh-missing.claim",
                    "status": "active",
                    "agent_name": "codex-fresh-missing",
                    "owner": "codex",
                    "scope": "fresh missing root",
                    "decision": None,
                    "run_root": "/tmp/fresh-missing-run",
                    "run_root_exists": False,
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "age_minutes": 4,
                    "live_runtime_owner": False,
                    "wait_only_without_live_process": False,
                    "fresh_without_live_process": True,
                    "stale_safe_takeover_candidate": False,
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
            "live_factor_processes": [
                {
                    "pid": 4321,
                    "run_root": "/tmp/live-run-a",
                    "exit_file_state": "present",
                    "command_excerpt": "python run_tomac.py",
                }
            ],
        }

        compact = format_report(full_report, compact=True)

        self.assertNotIn("claims", compact)
        self.assertNotIn("repo_root", compact)
        self.assertEqual(compact["summary"], full_report["summary"])
        self.assertEqual(compact["attention_claim_count"], 3)
        self.assertEqual(
            compact["attention_groups"],
            {
                "by_actionability": {
                    "active_claim_debt": 1,
                    "fresh_active_without_live_process": 1,
                    "stale_safe_takeover_candidate": 1,
                },
                "by_owner": {"codex": 3},
                "by_run_root_state": {"missing": 2, "present": 1},
                "by_status": {"active": 2, "terminalized": 1},
            },
        )
        self.assertEqual(
            compact["attention_clusters"],
            [
                {
                    "owner": "codex",
                    "scope_family": "fresh missing root",
                    "claim_count": 1,
                    "status_counts": {"active": 1},
                    "claim_files": ["fresh-missing.claim"],
                },
                {
                    "owner": "codex",
                    "scope_family": "positive flag",
                    "claim_count": 1,
                    "status_counts": {"terminalized": 1},
                    "claim_files": ["positive.claim"],
                },
                {
                    "owner": "codex",
                    "scope_family": "still running",
                    "claim_count": 1,
                    "status_counts": {"active": 1},
                    "claim_files": ["active.claim"],
                },
            ],
        )
        self.assertEqual(
            [claim["claim_file"] for claim in compact["attention_claims"]],
            ["active.claim", "fresh-missing.claim", "positive.claim"],
        )
        self.assertEqual(
            [claim["agent_name"] for claim in compact["attention_claims"]],
            ["codex-active-lane", "codex-fresh-missing", "codex-positive-review"],
        )
        self.assertEqual(compact["attention_claims"][0]["run_root_state"], "missing")
        self.assertEqual(
            compact["attention_action_queue"],
            {
                "fresh_active_claims_without_live_process": [
                    {
                        "claim_file": "fresh-missing.claim",
                        "age_minutes": 4,
                        "status": "active",
                    }
                ],
                "missing_run_root_claims": [
                    {
                        "claim_file": "active.claim",
                        "age_minutes": 91,
                        "run_root_state": "missing",
                    },
                    {
                        "claim_file": "fresh-missing.claim",
                        "age_minutes": 4,
                        "run_root_state": "missing",
                    },
                ],
                "externalize_wait_only_claims": [
                    {
                        "claim_file": "active.claim",
                        "age_minutes": 91,
                        "stale_safe_takeover_candidate": True,
                    }
                ],
                "stale_safe_takeover_claims": [
                    {
                        "claim_file": "active.claim",
                        "age_minutes": 91,
                        "wait_only_without_live_process": True,
                    }
                ],
                "live_runtime_run_roots": [
                    {
                        "pid": 4321,
                        "run_root": "/tmp/live-run-a",
                        "exit_file_state": "none",
                    }
                ],
            },
        )
        self.assertNotIn("claim_path", compact["attention_claims"][0])
        self.assertNotIn("run_root", compact["attention_claims"][0])

    def test_format_report_compact_clusters_similar_board_b_claim_families(self) -> None:
        full_report = {
            "schema_version": "factor-claim-terminalization-audit/v1",
            "generated_at": "2026-05-27T10:00:00+00:00",
            "claims_dir": "/tmp/claims",
            "repo_root": "/Users/example/ict-engine",
            "summary": {"status": "needs_attention", "active_claims": 3},
            "claims": [
                {
                    "claim_file": "cluster-a.claim",
                    "claim_path": "/tmp/claims/cluster-a.claim",
                    "status": "active",
                    "agent_name": "codex-a",
                    "owner": "codex",
                    "scope": "Board B TOMAC same-root continuation on TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation using repaired replay evidence.",
                    "decision": None,
                    "run_root": "/tmp/ict-engine-cluster-a",
                    "run_root_exists": True,
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "summary_files": [],
                },
                {
                    "claim_file": "cluster-b.claim",
                    "claim_path": "/tmp/claims/cluster-b.claim",
                    "status": "active",
                    "agent_name": "codex-b",
                    "owner": "codex",
                    "scope": "Board B fresh reopen of the stale XME IBKR exact 1m trend-continuation lane under TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation using IBKR historical truth first.",
                    "decision": None,
                    "run_root": "/tmp/ict-engine-cluster-b",
                    "run_root_exists": True,
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "summary_files": [],
                },
                {
                    "claim_file": "cluster-c.claim",
                    "claim_path": "/tmp/claims/cluster-c.claim",
                    "status": "active",
                    "agent_name": "codex-c",
                    "owner": "codex",
                    "scope": "Board B TOMAC stale takeover on RangeReversion -> PdhPdlFractalLiquiditySweep -> WprAdxTrendAlignedReclaim using existing prep evidence.",
                    "decision": None,
                    "run_root": "/tmp/ict-engine-cluster-c",
                    "run_root_exists": True,
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "summary_files": [],
                },
            ],
        }

        compact = format_report(full_report, compact=True)

        self.assertEqual(
            compact["attention_clusters"],
            [
                {
                    "owner": "codex",
                    "scope_family": "TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation",
                    "claim_count": 2,
                    "status_counts": {"active": 2},
                    "claim_files": ["cluster-a.claim", "cluster-b.claim"],
                },
                {
                    "owner": "codex",
                    "scope_family": "RangeReversion -> PdhPdlFractalLiquiditySweep -> WprAdxTrendAlignedReclaim",
                    "claim_count": 1,
                    "status_counts": {"active": 1},
                    "claim_files": ["cluster-c.claim"],
                },
            ],
        )

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
