from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SCRIPT_ROOT.parents[2]
sys.path.insert(0, str(SCRIPT_ROOT))

import external_history_adoption as adoption  # noqa: E402


class ExternalHistoryAdoptionTests(unittest.TestCase):
    def test_build_adoption_bundle_prefers_1h_primary_and_emits_commands(self) -> None:
        bundle = adoption.build_adoption_bundle(
            repo_root=REPO_ROOT,
            market_selector="NQ",
            profile_selector="thrill3r_nq_external_history_v1",
            workflow_symbol="BTCUSDT_EXT_1H",
            objective="regime_conditioned_profitability",
            state_dir="/tmp/ext-history-state",
            timeframe_inputs={
                "1d": "/tmp/nq-1d.json",
                "4h": "/tmp/nq-4h.json",
                "1h": "/tmp/nq-1h.json",
            },
        )

        self.assertEqual(bundle["selected_profile"]["profile_id"], "thrill3r_nq_external_history_v1")
        self.assertEqual(bundle["primary_input"]["timeframe"], "1h")
        self.assertIn("--profile thrill3r_nq_external_history_v1", bundle["suggested_commands"]["workflow_status"])
        self.assertIn("--data-1d '/tmp/nq-1d.json'", bundle["suggested_commands"]["factor_research"])
        self.assertIn("--data-ltf '/tmp/nq-1h.json'", bundle["suggested_commands"]["analyze"])

    def test_main_writes_bundle_and_command_file(self) -> None:
        with TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            input_path = out / "btc-1h.json"
            input_path.write_text(
                json.dumps(
                    {
                        "symbol": "BTCUSDT",
                        "candles": [
                            {
                                "timestamp": "2026-05-02T23:00:00Z",
                                "open": 1,
                                "high": 2,
                                "low": 0.5,
                                "close": 1.5,
                                "volume": 10,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            exit_code = adoption.main(
                [
                    "--repo-root",
                    str(REPO_ROOT),
                    "--market",
                    "NQ",
                    "--symbol",
                    "BTCUSDT_EXT_1H",
                    "--input",
                    f"1h={input_path}",
                    "--output-dir",
                    str(out),
                ]
            )

            self.assertEqual(exit_code, 0)
            bundle = json.loads(
                (out / "external_history_adoption_bundle.json").read_text(encoding="utf-8")
            )
            shell = (out / "suggested_commands.sh").read_text(encoding="utf-8")
            self.assertEqual(bundle["primary_input"]["timeframe"], "1h")
            self.assertIn("factor-research", shell)
            self.assertIn("auto-quant-prepare", shell)


if __name__ == "__main__":
    unittest.main()
