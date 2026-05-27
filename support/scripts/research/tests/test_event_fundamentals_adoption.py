from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SCRIPT_ROOT.parents[2]
sys.path.insert(0, str(SCRIPT_ROOT))

import event_fundamentals_adoption as adoption  # noqa: E402


class EventFundamentalsAdoptionTests(unittest.TestCase):
    def test_build_adoption_bundle_emits_dual_command_lanes_and_sidecar_summary(self) -> None:
        bundle = adoption.build_adoption_bundle(
            repo_root=REPO_ROOT,
            market_selector="NQ",
            profile_selector="thrill3r_nq_event_fundamentals_v1",
            workflow_symbol="NQ_EVENT_CONTEXT",
            objective="regime_conditioned_profitability",
            state_dir="/tmp/event-fund-state",
            artifact_inputs={
                "earnings": "/tmp/earnings.json",
                "fundamentals": "/tmp/fundamentals.json",
            },
        )

        self.assertEqual(
            bundle["selected_profile"]["profile_id"],
            "thrill3r_nq_event_fundamentals_v1",
        )
        self.assertEqual(bundle["default_choice_id"], "keep_zero_config")
        self.assertEqual(bundle["command_choices"][0]["choice_id"], "keep_zero_config")
        self.assertEqual(bundle["command_choices"][1]["choice_id"], "reuse_saved_profile")
        self.assertEqual(
            bundle["artifact_summary"]["provided_artifact_kinds"],
            ["earnings", "fundamentals"],
        )
        self.assertEqual(bundle["artifact_summary"]["provided_artifact_count"], 2)
        self.assertEqual(bundle["artifact_readiness"]["covered_contract_count"], 2)
        self.assertEqual(
            bundle["artifact_readiness"]["covered_contract_ids"],
            ["earnings_event_series", "lagged_fundamentals_sidecar"],
        )
        self.assertEqual(
            bundle["artifact_readiness"]["missing_contract_ids"],
            ["dividend_event_series", "macro_event_series"],
        )
        self.assertIn(
            "Lag fundamentals by effective date before backtest or live reuse.",
            bundle["usage_warnings"],
        )
        self.assertEqual(
            bundle["downstream_handoff"]["readiness"],
            "partial_sidecar_pack",
        )
        self.assertEqual(
            bundle["downstream_handoff"]["missing_artifact_kinds"],
            ["dividends", "macro"],
        )
        self.assertNotIn("--profile", bundle["suggested_commands"]["workflow_status"])
        self.assertIn(
            "--profile thrill3r-nq-event-fundamentals-v1",
            bundle["opt_in_suggested_commands"]["workflow_status"],
        )
        self.assertIn("review_sidecars", bundle["suggested_commands"])
        self.assertIn(
            "event_fundamentals_adoption_bundle.json",
            bundle["suggested_commands"]["review_sidecars"],
        )
        self.assertIn(
            "--sidecar-handoff 'event_fundamentals_adoption_bundle.json'",
            bundle["suggested_commands"]["auto_quant_adoption_review"],
        )

    def test_main_writes_bundle_and_dual_lane_command_file(self) -> None:
        with TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            earnings = out / "earnings.json"
            earnings.write_text(
                json.dumps([{"symbol": "AAPL", "timestamp": "2026-05-01T20:00:00Z"}]),
                encoding="utf-8",
            )
            fundamentals = out / "fundamentals.json"
            fundamentals.write_text(
                json.dumps([{"symbol": "AAPL", "effective_date": "2026-04-30", "pe": 22.1}]),
                encoding="utf-8",
            )

            exit_code = adoption.main(
                [
                    "--repo-root",
                    str(REPO_ROOT),
                    "--market",
                    "NQ",
                    "--symbol",
                    "NQ_EVENT_CONTEXT",
                    "--artifact",
                    f"earnings={earnings}",
                    "--artifact",
                    f"fundamentals={fundamentals}",
                    "--output-dir",
                    str(out),
                ]
            )

            self.assertEqual(exit_code, 0)
            bundle = json.loads(
                (out / "event_fundamentals_adoption_bundle.json").read_text(encoding="utf-8")
            )
            shell = (out / "suggested_commands.sh").read_text(encoding="utf-8")
            self.assertEqual(bundle["default_choice_id"], "keep_zero_config")
            self.assertIn("# keep_zero_config (recommended)", shell)
            self.assertIn("# reuse_saved_profile", shell)
            self.assertIn("workflow-status", shell)
            self.assertIn("review_sidecars", shell)
            self.assertIn("--profile thrill3r-nq-event-fundamentals-v1", shell)
            self.assertIn(
                "--sidecar-handoff 'event_fundamentals_adoption_bundle.json'",
                shell,
            )

    def test_full_artifact_pack_marks_profile_contract_ready(self) -> None:
        bundle = adoption.build_adoption_bundle(
            repo_root=REPO_ROOT,
            market_selector="NQ",
            profile_selector="thrill3r_nq_event_fundamentals_v1",
            workflow_symbol="NQ_EVENT_CONTEXT",
            objective="regime_conditioned_profitability",
            state_dir="/tmp/event-fund-state",
            artifact_inputs={
                "earnings": "/tmp/earnings.json",
                "dividends": "/tmp/dividends.json",
                "macro": "/tmp/macro.json",
                "fundamentals": "/tmp/fundamentals.json",
            },
        )

        self.assertEqual(bundle["artifact_summary"]["provided_artifact_count"], 4)
        self.assertEqual(
            bundle["artifact_summary"]["provided_artifact_kinds"],
            ["dividends", "earnings", "fundamentals", "macro"],
        )
        self.assertTrue(bundle["artifact_readiness"]["profile_contract_ready"])
        self.assertEqual(bundle["artifact_readiness"]["missing_contract_ids"], [])
        self.assertEqual(
            bundle["downstream_handoff"]["readiness"],
            "profile_contract_ready",
        )
        self.assertEqual(bundle["downstream_handoff"]["missing_artifact_kinds"], [])
        self.assertIn(
            "auto_quant_handoff_context",
            bundle["downstream_handoff"]["allowed_use_modes"],
        )
