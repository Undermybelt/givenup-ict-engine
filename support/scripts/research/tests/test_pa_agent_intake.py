from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import pa_agent_intake as intake  # noqa: E402


class PaAgentIntakeTests(unittest.TestCase):
    def test_zero_config_writes_consumer_artifacts(self) -> None:
        with TemporaryDirectory() as tmpdir:
            config = intake.IntakeConfig(
                output_dir=Path(tmpdir),
                pa_agent_root=None,
                profile=dict(intake.DEFAULT_PERSONAL_PROFILE),
                source_mode="embedded_defaults",
                include_prompt_inventory=False,
            )

            paths = intake.write_artifacts(config)
            bundle = json.loads(paths["bundle"].read_text(encoding="utf-8"))
            index = json.loads(paths["artifact_index"].read_text(encoding="utf-8"))

        self.assertTrue(bundle["consumer_contract"]["zero_config"])
        self.assertTrue(bundle["consumer_contract"]["hotplug_config_supported"])
        self.assertFalse(bundle["consumer_contract"]["trade_usable"])
        self.assertFalse(index["trade_usable"])
        self.assertEqual(index["taxonomy_count"], 9)
        self.assertEqual(index["artifacts"]["bundle"], "pa_agent_intake_bundle.json")
        self.assertNotIn("/", index["artifacts"]["bundle"])
        self.assertEqual(bundle["personal_profile"]["base_timeframe"], "1m")
        self.assertIn("4h", bundle["personal_profile"]["context_timeframes"])
        self.assertEqual(len(bundle["regime_taxonomy"]), 9)
        self.assertEqual(
            bundle["candidate_pack_template"]["promotion_state"],
            "candidate_observation",
        )
        self.assertEqual(
            bundle["personal_profile"]["strict_gate_policy"]["execution_readiness_min"],
            0.45,
        )

    def test_opt_in_pa_agent_root_extracts_cycle_enum_and_prompt_inventory(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "PA_Agent"
            schema_dir = root / "pa_agent" / "ai" / "prompts"
            schema_dir.mkdir(parents=True)
            (root / "prompt_engineering").mkdir()
            (root / "prompt_engineering" / "二元决策.txt").write_text("x", encoding="utf-8")
            (root / "pa_agent" / "ai" / "router.py").parent.mkdir(parents=True, exist_ok=True)
            (root / "pa_agent" / "ai" / "router.py").write_text("# router", encoding="utf-8")
            (schema_dir / "schemas.py").write_text(
                'STAGE1_SCHEMA={"properties":{"cycle_position":{"enum":["spike","unknown"]}}}',
                encoding="utf-8",
            )
            out = Path(tmpdir) / "out"
            config = intake.IntakeConfig(
                output_dir=out,
                pa_agent_root=root,
                profile=dict(intake.DEFAULT_PERSONAL_PROFILE),
                source_mode="opt_in",
                include_prompt_inventory=True,
            )

            paths = intake.write_artifacts(config)
            bundle = json.loads(paths["bundle"].read_text(encoding="utf-8"))

        self.assertTrue(bundle["source"]["pa_agent_detected"])
        self.assertEqual(bundle["source"]["cycle_position_enum"], ["spike", "unknown"])
        self.assertEqual(bundle["prompt_inventory"], ["二元决策.txt"])
        by_key = {item["pa_agent_key"]: item for item in bundle["regime_taxonomy"]}
        self.assertTrue(by_key["spike"]["source_present"])
        self.assertFalse(by_key["trading_range"]["source_present"])

    def test_profile_override_is_hotplugged_without_code_change(self) -> None:
        with TemporaryDirectory() as tmpdir:
            profile = Path(tmpdir) / "profile.json"
            profile.write_text(
                json.dumps({"base_timeframe": "5m", "context_timeframes": ["15m", "1h"]}),
                encoding="utf-8",
            )
            args = intake.parse_args(
                ["--profile", str(profile), "--output-dir", str(Path(tmpdir) / "artifacts")]
            )
            config = intake._build_config(args)

        self.assertEqual(config.profile["base_timeframe"], "5m")
        self.assertEqual(config.profile["context_timeframes"], ["15m", "1h"])


if __name__ == "__main__":
    unittest.main()