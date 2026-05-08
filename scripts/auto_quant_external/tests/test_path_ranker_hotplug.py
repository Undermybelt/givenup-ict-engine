from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
