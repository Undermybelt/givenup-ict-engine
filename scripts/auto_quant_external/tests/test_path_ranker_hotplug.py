from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import pandas_path_ranker_trainer as trainer  # noqa: E402
import path_ranker_integration as integration  # noqa: E402


class UserWeightsFallbackTests(unittest.TestCase):
    def test_weighted_sum_fallback_uses_user_weights_file(self) -> None:
        features = pd.DataFrame(
            {
                "evidence_quality_score": [1.0, 0.2],
                "risk_reward": [0.2, 1.0],
            }
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            weights_path = Path(tmpdir) / "user_weights.json"
            weights_path.write_text(
                '{\n'
                '  "evidence_quality_score": 0.9,\n'
                '  "risk_reward": -0.4\n'
                '}\n',
                encoding="utf-8",
            )

            scores = trainer.weighted_sum_fallback(features, weights_path=weights_path)

        self.assertGreater(scores[0], scores[1])


class ReuseModelFlowTests(unittest.TestCase):
    def test_reuse_model_dir_skips_training_and_applies_existing_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            policy_dir = state_dir / "NQ" / "policy_training"
            policy_dir.mkdir(parents=True)
            target_csv = policy_dir / "structural_path_ranking_target.csv"
            target_csv.write_text("candidate_set_id,path_id\nset1,path1\n", encoding="utf-8")

            existing_model_dir = Path(tmpdir) / "existing_model"
            existing_model_dir.mkdir()

            with mock.patch.object(integration, "run_trainer") as run_trainer, mock.patch.object(
                integration, "run_apply"
            ) as run_apply:
                argv = [
                    "path_ranker_integration.py",
                    "--state-dir",
                    str(state_dir),
                    "--symbol",
                    "NQ",
                    "--reuse-model-dir",
                    str(existing_model_dir),
                ]
                with mock.patch.object(sys, "argv", argv):
                    integration.main()

            run_trainer.assert_not_called()
            run_apply.assert_called_once_with(
                str(existing_model_dir),
                str(target_csv),
                str(policy_dir / "scores.csv"),
                None,
            )

    def test_register_runtime_artifact_triggers_repo_cli_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            policy_dir = state_dir / "NQ" / "policy_training"
            policy_dir.mkdir(parents=True)
            target_csv = policy_dir / "structural_path_ranking_target.csv"
            target_csv.write_text("candidate_set_id,path_id\nset1,path1\n", encoding="utf-8")
            output_dir = policy_dir / "path_ranker_model"
            output_dir.mkdir()
            (output_dir / "path_ranker_direct_model.json").write_text("{}", encoding="utf-8")

            with mock.patch.object(integration, "run_trainer") as run_trainer, mock.patch.object(
                integration, "run_apply"
            ) as run_apply, mock.patch.object(
                integration, "register_runtime_artifact"
            ) as register_runtime_artifact:
                argv = [
                    "path_ranker_integration.py",
                    "--state-dir",
                    str(state_dir),
                    "--symbol",
                    "NQ",
                    "--register-runtime-artifact",
                ]
                with mock.patch.object(sys, "argv", argv):
                    integration.main()

            run_trainer.assert_called_once()
            run_apply.assert_called_once()
            register_runtime_artifact.assert_called_once_with(
                state_dir=str(state_dir),
                symbol="NQ",
                model_dir=str(output_dir),
                score_column="raw_path_score",
                reuse_mode="candidate_set_only",
            )


class DirectModelArtifactTests(unittest.TestCase):
    def test_create_direct_model_artifact_emits_repo_runtime_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            trainer.create_direct_model_artifact(
                output_dir=output_dir,
                features=["rank", "current_posterior"],
                trained_rows=12,
                output_transform="sigmoid",
            )

            artifact = json.loads((output_dir / "path_ranker_direct_model.json").read_text(encoding="utf-8"))

        self.assertEqual(artifact["protocol_version"], "structural-path-ranking-direct-model-v1")
        self.assertEqual(artifact["model_family"], "weighted_feature_sum_v1")
        self.assertEqual(
            artifact["feature_schema_version"],
            "structural-path-ranking-trainer-manifest-v1",
        )
        self.assertEqual(artifact["output_transform"], "sigmoid")
        self.assertIn("current_posterior", artifact["numerical_feature_weights"])
        self.assertIn("rank", artifact["numerical_feature_weights"])

    def test_build_registered_artifact_prefers_direct_model_family_when_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            trainer.create_direct_model_artifact(
                output_dir=output_dir,
                features=["rank"],
                trained_rows=7,
            )

            metadata = trainer.build_registered_artifact_metadata(
                output_dir=output_dir,
                trained_rows=7,
                history_rows=9,
                calibration_rows=3,
                selected_features=["rank"],
            )

        self.assertEqual(metadata["protocol_version"], "structural-path-ranking-trainer-artifact-v1")
        self.assertEqual(metadata["model_family"], "weighted_feature_sum_v1")
        self.assertEqual(metadata["score_column"], "raw_path_score")
        self.assertEqual(metadata["trained_rows"], 7)
        self.assertEqual(metadata["history_rows"], 9)
        self.assertEqual(metadata["calibration_rows"], 3)
        self.assertTrue(str(metadata["artifact_uri"]).endswith("path_ranker_direct_model.json"))


if __name__ == "__main__":
    unittest.main()
