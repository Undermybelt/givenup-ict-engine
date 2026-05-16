from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import heuristic_payoff_pipeline as pipeline  # noqa: E402


class HeuristicPayoffPipelineTests(unittest.TestCase):
    def test_zero_config_pipeline_writes_isolated_artifacts(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_csv = tmp / "events.csv"
            output_dir = tmp / "out"
            input_csv.write_text(
                "timestamp,open,high,low,close,side\n"
                "t0,100,101,99,100,1\n"
                "t1,100,103,99.5,102,0\n"
                "t2,102,104,98,99,0\n",
                encoding="utf-8",
            )

            result = pipeline.run_pipeline(
                input_csv=input_csv,
                output_dir=output_dir,
                symbol="NQ",
                candidate_id="zero-config-demo",
            )

            self.assertEqual(result["symbol"], "NQ")
            self.assertEqual(result["candidate_id"], "zero-config-demo")
            self.assertTrue((output_dir / "labels.jsonl").is_file())
            self.assertTrue((output_dir / "payoff_report.json").is_file())
            self.assertTrue((output_dir / "purged_cv_guard.json").is_file())
            self.assertTrue((output_dir / "handoff_summary.json").is_file())
            self.assertTrue((output_dir / "bbn_gate.json").is_file())
            self.assertTrue((output_dir / "factor_formula_library.json").is_file())
            self.assertTrue((output_dir / "paper2code_adapter_report.json").is_file())
            self.assertEqual(result["profile"]["profile_id"], "ict-default-v1")
            self.assertIn("qqq_hv_level", result["profile"]["auxiliary_fields"])
            if result["path_ranker_handoff"]["bbn_gate"]["consume_by_regime_bbn"]:
                self.assertTrue((output_dir / "path_ranker_target.csv").is_file())
            else:
                self.assertTrue((output_dir / "failure_memory.jsonl").is_file())
            self.assertIn("sidecar_closure", result)
            self.assertEqual(result["sidecar_closure"]["formula_library"]["seed_count"], 7)
            self.assertEqual(result["sidecar_closure"]["paper2code_adapter_report"]["adapter_count"], 4)
            self.assertIn("purged_cv_guard", result)

    def test_profile_json_overrides_barriers_and_user_fields(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_csv = tmp / "events.csv"
            profile_json = tmp / "profile.json"
            output_dir = tmp / "out"
            input_csv.write_text(
                "timestamp,open,high,low,close,side\n"
                "t0,100,101,99,100,1\n"
                "t1,100,101.5,99.2,99,0\n",
                encoding="utf-8",
            )
            profile_json.write_text(
                json.dumps(
                    {
                        "profile_id": "tomac-nq-vrp",
                        "pt_mult": 0.015,
                        "sl_mult": 0.01,
                        "max_holding_bars": 1,
                        "cost_bps": 5,
                        "auxiliary_fields": ["vvix_over_vix", "vix3m_level"],
                        "enabled": True,
                    }
                ),
                encoding="utf-8",
            )

            result = pipeline.run_pipeline(
                input_csv=input_csv,
                output_dir=output_dir,
                symbol="NQ",
                candidate_id="profile-demo",
                profile_json=profile_json,
            )

            label_line = (output_dir / "labels.jsonl").read_text(encoding="utf-8").splitlines()[0]
            label = json.loads(label_line)
            self.assertEqual(result["profile"]["profile_id"], "tomac-nq-vrp")
            self.assertEqual(result["profile"]["auxiliary_fields"], ["vvix_over_vix", "vix3m_level"])
            self.assertEqual(label["barrier_hit"], "take_profit")
            self.assertAlmostEqual(label["realized_R"], 1.45, places=6)

    def test_pipeline_runs_bbn_evidence_value_when_profile_provides_rows(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_csv = tmp / "events.csv"
            bbn_rows = tmp / "bbn_rows.jsonl"
            profile_json = tmp / "profile.json"
            output_dir = tmp / "out"
            input_csv.write_text(
                "timestamp,open,high,low,close,side\n"
                "t0,100,101,99,100,1\n"
                "t1,100,103,99,102,0\n",
                encoding="utf-8",
            )
            bbn_rows.write_text(
                json.dumps({"edge_id": "edge-a", "prior_prob": 0.6, "posterior_prob": 0.9, "outcome": 1}) + "\n"
                + json.dumps({"edge_id": "edge-a", "prior_prob": 0.4, "posterior_prob": 0.1, "outcome": 0}) + "\n",
                encoding="utf-8",
            )
            profile_json.write_text(json.dumps({"bbn_evidence_rows_jsonl": str(bbn_rows)}), encoding="utf-8")

            result = pipeline.run_pipeline(
                input_csv=input_csv,
                output_dir=output_dir,
                symbol="NQ",
                candidate_id="bbn-closure-demo",
                profile_json=profile_json,
            )

            self.assertTrue((output_dir / "bbn_evidence_value_report.json").is_file())
            self.assertEqual(result["sidecar_closure"]["bbn_evidence_value_report"]["accepted_edges"], ["edge-a"])

    def test_pipeline_uses_precomputed_labels_when_provided(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_csv = tmp / "events.csv"
            labels_jsonl = tmp / "labels.jsonl"
            output_dir = tmp / "out"
            input_csv.write_text(
                "timestamp,open,high,low,close,side\n"
                "t0,100,101,99,100,0\n"
                "t1,100,102,99,101,0\n",
                encoding="utf-8",
            )
            labels_jsonl.write_text(
                json.dumps(
                    {
                        "trade_id": "wire-1",
                        "entry_index": 0,
                        "exit_index": 1,
                        "entry_timestamp": "t0",
                        "exit_timestamp": "t1",
                        "side": 1,
                        "entry_price": 100.0,
                        "exit_price": 101.0,
                        "barrier_hit": "roi",
                        "gross_return": 0.01,
                        "net_return": 0.01,
                        "realized_R": 1.0,
                        "mfe": 0.02,
                        "mae": -0.01,
                        "time_to_hit": 1,
                        "meta_label": 1,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = pipeline.run_pipeline(
                input_csv=input_csv,
                output_dir=output_dir,
                symbol="NQ",
                candidate_id="precomputed-label-demo",
                labels_jsonl=labels_jsonl,
            )

            label_line = (output_dir / "labels.jsonl").read_text(encoding="utf-8").splitlines()[0]
            label = json.loads(label_line)
            self.assertEqual(result["label_count"], 1)
            self.assertEqual(label["trade_id"], "wire-1")
            self.assertEqual(label["barrier_hit"], "roi")
            self.assertAlmostEqual(label["realized_R"], 1.0)

    def test_pipeline_downgrades_payoff_gate_when_purged_cv_rejects(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_csv = tmp / "events.csv"
            labels_jsonl = tmp / "labels.jsonl"
            output_dir = tmp / "out"
            input_csv.write_text(
                "timestamp,open,high,low,close,side\n"
                "t0,100,101,99,100,0\n"
                "t1,100,102,99,101,0\n"
                "t2,101,103,100,102,0\n",
                encoding="utf-8",
            )
            labels_jsonl.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "trade_id": "overlap-1",
                                "entry_index": 0,
                                "exit_index": 2,
                                "entry_timestamp": "t0",
                                "exit_timestamp": "t2",
                                "side": 1,
                                "entry_price": 100.0,
                                "exit_price": 102.0,
                                "barrier_hit": "roi",
                                "gross_return": 0.02,
                                "net_return": 0.02,
                                "realized_R": 2.0,
                                "mfe": 0.03,
                                "mae": -0.01,
                                "time_to_hit": 2,
                                "meta_label": 1,
                            }
                        ),
                        json.dumps(
                            {
                                "trade_id": "overlap-2",
                                "entry_index": 1,
                                "exit_index": 2,
                                "entry_timestamp": "t1",
                                "exit_timestamp": "t2",
                                "side": 1,
                                "entry_price": 101.0,
                                "exit_price": 102.0,
                                "barrier_hit": "roi",
                                "gross_return": 0.00990099,
                                "net_return": 0.00990099,
                                "realized_R": 0.990099,
                                "mfe": 0.01,
                                "mae": -0.005,
                                "time_to_hit": 1,
                                "meta_label": 1,
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = pipeline.run_pipeline(
                input_csv=input_csv,
                output_dir=output_dir,
                symbol="NQ",
                candidate_id="purged-cv-reject-demo",
                labels_jsonl=labels_jsonl,
            )

            self.assertEqual(result["purged_cv_guard"]["purged_cv_gate"], "insufficient_data")
            self.assertEqual(result["payoff_gate"], "reject")
            self.assertEqual(result["path_ranker_handoff"]["bbn_gate"]["consume_by_regime_bbn"], False)


if __name__ == "__main__":
    unittest.main()
