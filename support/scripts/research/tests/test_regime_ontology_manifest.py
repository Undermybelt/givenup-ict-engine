from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import regime_ontology_manifest as manifest  # noqa: E402


class RegimeOntologyManifestTests(unittest.TestCase):
    def test_manifest_emits_expected_expert_counts(self) -> None:
        result = manifest.build_manifest()

        self.assertEqual(result["schema_version"], "regime-ontology-manifest/v1")
        self.assertEqual(result["counts"]["primary"], 5)
        self.assertEqual(result["counts"]["secondary"], 16)
        self.assertEqual(result["counts"]["dimension"], 24)
        self.assertGreaterEqual(result["counts"]["transition"], 8)
        self.assertEqual(result["expert_count"], 53)
        self.assertEqual(result["source_concept_guidance"]["concept_count"], 25)

    def test_manifest_covers_rust_regime_labels_and_unknown_abstain(self) -> None:
        result = manifest.build_manifest()
        labels = {expert["label_id"]: expert for expert in result["experts"]}

        for label in ["TrendExpansion", "RangeConsolidation", "ExtremeStress", "ReversalBrewing", "Unknown"]:
            self.assertIn(f"primary::{label}", labels)
        for label in ["BullTrendAcceleration", "LiquidityCrunch", "StructureBreakdown", "Unknown"]:
            self.assertIn(f"secondary::{label}", labels)
        for label in ["volatility::CrisisVol", "liquidity::ThinLiquidity", "structure::Breakout", "behavior::Capitulation"]:
            self.assertIn(label, labels)
        self.assertEqual(labels["primary::Unknown"]["abstain_policy"], "always_abstain")
        self.assertEqual(labels["secondary::Unknown"]["abstain_policy"], "always_abstain")

    def test_each_active_expert_has_confidence_contract(self) -> None:
        result = manifest.build_manifest()

        for expert in result["experts"]:
            self.assertIn(expert["target_coverage"], {0.95, 0.99})
            self.assertIn("abstain_policy", expert)
            self.assertIn("positive_definition", expert)
            self.assertIn("negative_definition", expert)
            self.assertIn("required_features", expert)
            self.assertGreaterEqual(expert["min_support"], 0)

    def test_manifest_embeds_sanitized_ict_concept_guidance(self) -> None:
        result = manifest.build_manifest()
        guidance = result["source_concept_guidance"]
        concepts = {concept["concept"]: concept for concept in guidance["concepts"]}

        for concept in [
            "liquidity_sweep",
            "liquidity_pool",
            "fair_value_gap",
            "inversion_fair_value_gap",
            "market_structure_shift",
            "smt_divergence",
        ]:
            self.assertIn(concept, concepts)
            self.assertIn("factor_candidates", concepts[concept])
            self.assertIn("bbn_node_candidates", concepts[concept])
            self.assertIn("agent_output_fields", concepts[concept])

        serialized = json.dumps(guidance, sort_keys=True)
        self.assertNotIn("/Users/", serialized)
        self.assertNotIn("Downloads", serialized)
        self.assertNotIn("source_root", serialized)
        self.assertEqual(guidance["usage"]["path_dependency"], "none")

    def test_cli_writes_manifest_json_and_expert_bank_jsonl(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            output_json = tmp / "regime_ontology_manifest.json"
            output_jsonl = tmp / "regime_expert_bank_manifest.jsonl"

            exit_code = manifest.main([
                "--output-json",
                str(output_json),
                "--output-jsonl",
                str(output_jsonl),
            ])

            self.assertEqual(exit_code, 0)
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["expert_count"], 53)
            self.assertEqual(payload["source_concept_guidance"]["concept_count"], 25)
            self.assertEqual(len(output_jsonl.read_text(encoding="utf-8").splitlines()), 53)


if __name__ == "__main__":
    unittest.main()
