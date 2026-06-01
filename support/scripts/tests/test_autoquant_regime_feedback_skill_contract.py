from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
SKILL = REPO / "skills/auto-quant-handoff-harness/SKILL.md"
REFERENCE = (
    REPO
    / "skills/auto-quant-handoff-harness/references/autoquant-regime-feedback-evidence-contract-20260601.md"
)
MANIFEST = REPO / "skills/manifest.json"


class AutoQuantRegimeFeedbackSkillContractTests(unittest.TestCase):
    def test_skill_requires_regime_feedback_packet_and_closed_loop_readbacks(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        reference = REFERENCE.read_text(encoding="utf-8")

        for needle in (
            "${run_root}/checks/regime_feedback_evidence_packet.json",
            "cleaned data provenance",
            "terminal metrics",
            "data_scope_blocked_for_cleaned_target",
            "data_provenance.source_archive_validation.status=pass_zip_pristine_source",
            "source_archive_validation.status=pass_zip_pristine_source",
            "delete/re-extract it from ZIP",
            "pending belief-network and execution-tree placement",
            "accepted paper/live execution feedback packet",
            "belief network / BBN readback",
            "execution_tree_trace or workflow-status",
            "terminal metrics with promotion_allowed=true and trade_usable=true",
            "Life-Harness Runtime Adaptation Contract",
            "https://github.com/undermybelt/Auto-Quant",
            "auto-quant-bootstrap --state-dir <state-dir> --repo-url https://github.com/undermybelt/Auto-Quant",
            "Environment contract",
            "Procedural skill",
            "Action realization",
            "Trajectory regulation",
            "failure_patterns.md",
            "harness_layer_updates.md",
            "regression_review.md",
            "frozen returned artifacts",
            "life_harness_review",
            "life_harness_review.status=pending_return_artifacts",
            "life_harness_review.adoption_evaluation_allowed=true",
            "life_harness_review.artifact_checks",
            "life_harness_review.invalid_artifacts",
            "life_harness_review.status=return_artifact_validation_failed",
            "life_harness_review.status=legacy_handoff_without_life_harness_contract",
            "life_harness_review.status=legacy_handoff_without_lifecycle_layers",
            "life_harness_review.adoption_evaluation_allowed=false",
            "weak run.log",
            "market-data-harness",
            "structural_feedback_replay_harness.py",
            "factor_candidate_harness_presets.json",
            "non-LLM-agent harnesses",
        ):
            self.assertIn(needle, skill)

        for needle in (
            "schema_version: autoquant-regime-feedback-evidence-packet/v1",
            "closed_loop_contract.stage_order",
            "data_provenance",
            "raw_fallback_used: false",
            "cleaned_or_verified_retained",
            "source_archive_validation.status: pass_zip_pristine_source",
            "non-ZIP-pristine",
            "belief_network_placement.target_regime_node",
            "execution_tree_placement.target_branch_path",
            "backtest_autoquant_feedback",
            "visible_in_bbn_feedback",
            "visible_in_execution_tree",
            'Agents should not report "能实战"',
        ):
            self.assertIn(needle, reference)

    def test_manifest_exposes_reference_and_bbn_execution_tree_mapping(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        skill_entry = next(
            item for item in manifest["skills"] if item["id"] == "auto-quant-handoff-harness"
        )

        self.assertIn(
            "skills/auto-quant-handoff-harness/references/autoquant-regime-feedback-evidence-contract-20260601.md",
            skill_entry["references"],
        )
        self.assertIn(
            "Belief network and execution tree placement readbacks",
            skill_entry["runtime_mapping"],
        )
        self.assertIn(
            "Life-Harness lifecycle layer payload",
            skill_entry["runtime_mapping"],
        )
        self.assertIn(
            "Auto-Quant adoption-review life_harness_review surface",
            skill_entry["runtime_mapping"],
        )
        self.assertIn(
            "Tianshi-Xu/Life-Harness arXiv 2605.22166 and source review",
            skill_entry["source_review"],
        )
        self.assertIn(
            "Undermybelt/Auto-Quant release-clone default bootstrap source",
            skill_entry["source_review"],
        )


if __name__ == "__main__":
    unittest.main()
