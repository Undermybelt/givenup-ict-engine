from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import transition_evidence_aggregator as agg  # noqa: E402


class TransitionEvidenceAggregatorTests(unittest.TestCase):
    def test_transition_alert_remains_telemetry_when_confidence_fails_and_drift_fires(self) -> None:
        regime = {
            "candidate_id": "regime-a",
            "confidence_95": False,
            "transition_prob": 0.72,
            "flip_rate": 0.5,
            "regime_confidence_gate": "reject",
        }
        drift_rows = [
            {"source": "bocd", "transition_prob": 0.96, "drift_flag": True, "severity": 0.9},
            {"source": "adwin", "transition_prob": 0.30, "drift_flag": True, "severity": 0.6},
        ]

        result = agg.build_transition_evidence(regime_report=regime, drift_rows=drift_rows)

        self.assertEqual(result["schema_version"], "transition-evidence-aggregator/v1")
        self.assertTrue(result["transition_alert_95"])
        self.assertGreaterEqual(result["transition_hazard"], 0.95)
        self.assertIn("bocd", result["drift_flags"])
        self.assertEqual(result["execution_tree_block_hint"], "none")
        self.assertEqual(result["transition_hazard_role"], "telemetry_only")

    def test_transition_evidence_allows_execution_when_regime_is_stable(self) -> None:
        regime = {
            "candidate_id": "regime-b",
            "confidence_95": True,
            "transition_prob": 0.05,
            "flip_rate": 0.0,
            "regime_confidence_gate": "pass",
        }

        result = agg.build_transition_evidence(regime_report=regime, drift_rows=[])

        self.assertFalse(result["transition_alert_95"])
        self.assertLess(result["transition_hazard"], 0.2)
        self.assertEqual(result["execution_tree_block_hint"], "none")

    def test_markov_sequence_adds_matrix_multistep_stationary_and_exit_hazard(self) -> None:
        regime = {
            "candidate_id": "regime-markov",
            "confidence_95": True,
            "active_regime": "trend",
            "transition_prob": 0.05,
            "flip_rate": 0.0,
            "regime_confidence_gate": "pass",
        }
        sequence_rows = [
            {"regime": "trend"},
            {"regime": "trend"},
            {"regime": "range"},
            {"regime": "range"},
            {"regime": "trend"},
            {"regime": "transition"},
            {"regime": "trend"},
        ]

        result = agg.build_transition_evidence(
            regime_report=regime,
            drift_rows=[],
            regime_sequence_rows=sequence_rows,
        )

        self.assertEqual(result["markov_state_sequence_length"], 7)
        self.assertEqual(result["markov_transition_count"], 6)
        self.assertAlmostEqual(result["markov_transition_matrix"]["trend"]["trend"], 1 / 3)
        self.assertAlmostEqual(result["markov_transition_matrix"]["trend"]["range"], 1 / 3)
        self.assertAlmostEqual(result["markov_transition_matrix"]["trend"]["transition"], 1 / 3)
        self.assertAlmostEqual(result["markov_two_step_probabilities"]["trend"], 11 / 18)
        self.assertAlmostEqual(result["markov_current_regime_exit_probability"], 2 / 3)
        self.assertAlmostEqual(result["transition_hazard"], 2 / 3)
        self.assertAlmostEqual(sum(result["markov_stationary_distribution"].values()), 1.0)
        self.assertEqual(result["transition_hazard_role"], "telemetry_only")
        self.assertEqual(result["execution_tree_block_hint"], "none")

    def test_cli_writes_transition_evidence_json(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            regime_json = tmp / "regime.json"
            drift_jsonl = tmp / "drift.jsonl"
            sequence_jsonl = tmp / "sequence.jsonl"
            output_json = tmp / "transition_evidence.json"
            regime_json.write_text(
                json.dumps(
                    {
                        "candidate_id": "cli",
                        "confidence_95": False,
                        "active_regime": "trend",
                        "transition_prob": 0.8,
                        "flip_rate": 0.3,
                    }
                ),
                encoding="utf-8",
            )
            drift_jsonl.write_text(
                json.dumps({"source": "kswin", "transition_prob": 0.97, "drift_flag": True, "severity": 0.8}) + "\n",
                encoding="utf-8",
            )
            sequence_jsonl.write_text(
                "\n".join(
                    [
                        json.dumps({"regime": "trend"}),
                        json.dumps({"regime": "range"}),
                        json.dumps({"regime": "trend"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            exit_code = agg.main(
                [
                    "--regime-report-json",
                    str(regime_json),
                    "--drift-jsonl",
                    str(drift_jsonl),
                    "--regime-sequence-jsonl",
                    str(sequence_jsonl),
                    "--output-json",
                    str(output_json),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertIn('"transition_alert_95": true', output_json.read_text())
            self.assertIn('"markov_transition_matrix"', output_json.read_text())


if __name__ == "__main__":
    unittest.main()
