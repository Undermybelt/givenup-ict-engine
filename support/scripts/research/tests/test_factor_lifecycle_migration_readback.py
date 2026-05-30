from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import factor_lifecycle_migration_readback as readback  # noqa: E402


class FactorLifecycleMigrationReadbackTests(unittest.TestCase):
    def _write_csv(
        self, path: Path, fieldnames: list[str], rows: list[dict[str, str]]
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_old_drop_reclassified_as_learning_admitted_paper_observe(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = Path(tmpdir)
            summaries = run_root / "summaries"
            checks = run_root / "checks"
            summaries.mkdir()
            checks.mkdir()
            (run_root / "materials").mkdir()
            (summaries / "terminal_decision_summary.md").write_text(
                "\n".join(
                    [
                        "decision=drop_gate1_no_exact_1m_5bps_density_survivor",
                        "regime_confidence=0.96",
                        "leakage_check=pass",
                    ]
                ),
                encoding="utf-8",
            )
            with (summaries / "gate1_cost_stress.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "package_id",
                        "trade_count",
                        "net_after_declared_friction_pct",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "package_id": "old_sparse_positive_v1",
                        "trade_count": "4",
                        "net_after_declared_friction_pct": "0.42",
                    }
                )
            (checks / "terminal_metrics.json").write_text(
                json.dumps(
                    {
                        "validation": {
                            "raw_scored_mature": 4,
                            "production": 4,
                            "observation": 4,
                        },
                        "execution_readiness": 0.41,
                        "transition_hazard": 0.72,
                    }
                ),
                encoding="utf-8",
            )

            result = readback.build_migration_readback(run_root)

        self.assertEqual(
            result["migration_decision"],
            "old_drop_reclassified_learning_admitted_paper_observe",
        )
        self.assertEqual(result["learning_admission_status"], "admitted")
        self.assertEqual(result["paper_admission_status"], "observe")
        self.assertEqual(result["live_trade_status"], "blocked")
        self.assertFalse(result["writes_old_artifacts"])
        self.assertFalse(result["promotion_allowed"])
        self.assertFalse(result["trade_usable"])
        self.assertIn("summaries/terminal_decision_summary.md", result["evidence_paths"])
        self.assertIn("summaries/gate1_cost_stress.csv", result["evidence_paths"])

    def test_reads_bounded_summary_and_check_files_with_declared_friction_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = Path(tmpdir)
            summaries = run_root / "summaries"
            checks = run_root / "checks"
            materials = run_root / "materials"
            summaries.mkdir()
            checks.mkdir()
            materials.mkdir()
            (summaries / "terminal_decision_summary.md").write_text(
                "\n".join(
                    [
                        "decision=drop_gate1_no_exact_1m_5bps_density_survivor",
                        "regime_confidence=0.96",
                        "leakage_check=pass",
                    ]
                ),
                encoding="utf-8",
            )
            self._write_csv(
                summaries / "custom_terminal_cost_summary.csv",
                [
                    "package_id",
                    "trade_count",
                    "instrument_cost_total_profit_pct",
                ],
                [
                    {
                        "package_id": "old_declared_alias_v1",
                        "trade_count": "7",
                        "instrument_cost_total_profit_pct": "0.31",
                    }
                ],
            )
            (checks / "execution_readback.json").write_text(
                json.dumps(
                    {
                        "validation": {
                            "raw_scored_mature": 7,
                            "production_validation": 7,
                            "observation_validation": 7,
                        },
                        "execution_candidate_readiness": 0.52,
                        "hybrid_transition_hazard": 0.81,
                    }
                ),
                encoding="utf-8",
            )

            result = readback.build_migration_readback(run_root)

        self.assertEqual(result["learning_admission_status"], "admitted")
        self.assertEqual(
            result["migration_decision"],
            "old_drop_reclassified_learning_admitted_paper_observe",
        )
        self.assertEqual(result["long_run_expectancy_after_declared_friction"], 0.31)
        self.assertEqual(result["validation_rows"]["raw_scored_mature"], 7)
        self.assertIn("summaries/custom_terminal_cost_summary.csv", result["evidence_paths"])
        self.assertIn("checks/execution_readback.json", result["evidence_paths"])
        self.assertEqual(result["blockers"], [])

    def test_ignores_retired_transition_telemetry_when_reading_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = Path(tmpdir)
            summaries = run_root / "summaries"
            checks = run_root / "checks"
            summaries.mkdir()
            checks.mkdir()
            (summaries / "terminal_decision_summary.md").write_text(
                "\n".join(
                    [
                        "decision=old_candidate",
                        "regime_confidence=0.96",
                        "leakage_check=pass",
                    ]
                ),
                encoding="utf-8",
            )
            self._write_csv(
                summaries / "rank_rows_cost_stress.csv",
                ["package_id", "trade_count", "net_after_5bps_per_side_pct"],
                [
                    {
                        "package_id": "old_candidate_v1",
                        "trade_count": "40",
                        "net_after_5bps_per_side_pct": "0.72",
                    }
                ],
            )
            (checks / "terminal_metrics.json").write_text(
                json.dumps(
                    {
                        "validation": {
                            "raw_scored_mature": 40,
                            "production": 40,
                            "observation": 40,
                        },
                        "execution_readiness": 0.72,
                        "transition_hazard": 0.99,
                        "hybrid_transition_hazard": 0.99,
                    }
                ),
                encoding="utf-8",
            )

            result = readback.build_migration_readback(run_root)

        self.assertEqual(result["learning_admission_status"], "blocked")
        self.assertEqual(result["paper_admission_status"], "blocked")
        self.assertEqual(result["live_trade_status"], "blocked")
        self.assertIn("legacy_fixed_cost_readback_not_cost_authority", result["blockers"])
        self.assertNotIn("transition_hazard", result)

    def test_raw_profit_fallback_blocks_learning_without_practical_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = Path(tmpdir)
            summaries = run_root / "summaries"
            checks = run_root / "checks"
            summaries.mkdir()
            checks.mkdir()
            (summaries / "terminal_decision_summary.md").write_text(
                "\n".join(
                    [
                        "decision=drop_gate1_no_exact_1m_5bps_density_survivor",
                        "regime_confidence=0.97",
                        "leakage_check=pass",
                    ]
                ),
                encoding="utf-8",
            )
            self._write_csv(
                summaries / "terminal_summary.csv",
                ["package_id", "trade_count", "total_profit_pct"],
                [
                    {
                        "package_id": "old_raw_only_v1",
                        "trade_count": "40",
                        "total_profit_pct": "4.20",
                    }
                ],
            )
            (checks / "terminal_metrics.json").write_text(
                json.dumps(
                    {
                        "validation": {
                            "raw_scored_mature": 40,
                            "production": 40,
                            "observation": 40,
                        },
                        "execution_readiness": 0.92,
                        "transition_hazard": 0.10,
                    }
                ),
                encoding="utf-8",
            )

            result = readback.build_migration_readback(run_root)

        self.assertEqual(result["learning_admission_status"], "blocked")
        self.assertEqual(result["paper_admission_status"], "blocked")
        self.assertEqual(result["live_trade_status"], "blocked")
        self.assertIn("declared_friction_missing_raw_profit_only", result["blockers"])
        self.assertEqual(result["long_run_expectancy_after_declared_friction"], 4.20)
        self.assertFalse(result["promotion_allowed"])
        self.assertFalse(result["trade_usable"])
        self.assertFalse(result["update_goal"])

    def test_readback_never_sets_practical_flags_from_migration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = Path(tmpdir)
            summaries = run_root / "summaries"
            checks = run_root / "checks"
            summaries.mkdir()
            checks.mkdir()
            (summaries / "terminal_decision_summary.md").write_text(
                "\n".join(
                    [
                        "decision=keep_old_lifecycle_candidate",
                        "regime_confidence=0.99",
                        "leakage_check=pass",
                    ]
                ),
                encoding="utf-8",
            )
            self._write_csv(
                summaries / "rank_rows_cost_stress.csv",
                ["package_id", "net_after_5bps_per_side_pct"],
                [
                    {
                        "package_id": "old_live_ready_shape_v1",
                        "net_after_5bps_per_side_pct": "1.50",
                    }
                ],
            )
            (checks / "terminal_metrics.json").write_text(
                json.dumps(
                    {
                        "validation": {
                            "raw_scored_mature": 50,
                            "production": 50,
                            "observation": 50,
                        },
                        "execution_readiness": 0.91,
                        "transition_hazard": 0.12,
                    }
                ),
                encoding="utf-8",
            )

            result = readback.build_migration_readback(run_root)

        self.assertEqual(result["learning_admission_status"], "blocked")
        self.assertEqual(result["paper_admission_status"], "blocked")
        self.assertEqual(result["live_trade_status"], "blocked")
        self.assertIn("legacy_fixed_cost_readback_not_cost_authority", result["blockers"])
        self.assertFalse(result["promotion_allowed"])
        self.assertFalse(result["trade_usable"])
        self.assertFalse(result["update_goal"])

    def test_reads_tomac_legacy_root_summary_and_leaderboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_root = Path(tmpdir)
            (run_root / "terminal_decision_summary.md").write_text(
                "\n".join(
                    [
                        "decision: `reject_less_than_one_trade_per_3_sessions`",
                        "regime_confidence: `0.96`",
                        "leakage_check: `pass`",
                    ]
                ),
                encoding="utf-8",
            )
            (run_root / "summary.json").write_text(
                json.dumps(
                    {
                        "best": {
                            "decision": "reject_less_than_one_trade_per_3_sessions",
                            "trade_count": 38,
                            "cost_stress": {
                                "5bps": {
                                    "net_ret": 0.019535640591735546,
                                    "trades": 38,
                                }
                            },
                        },
                        "downstream_allowed": False,
                        "promotion_allowed": False,
                        "trade_usable": False,
                    }
                ),
                encoding="utf-8",
            )
            self._write_csv(
                run_root / "leaderboard.csv",
                [
                    "factor_id",
                    "trade_count",
                    "net_5bps",
                    "downstream_allowed",
                    "promotion_allowed",
                    "trade_usable",
                ],
                [
                    {
                        "factor_id": "tomac_sparse_positive_v1",
                        "trade_count": "38",
                        "net_5bps": "0.019535640591735546",
                        "downstream_allowed": "False",
                        "promotion_allowed": "False",
                        "trade_usable": "False",
                    }
                ],
            )

            result = readback.build_migration_readback(run_root)

        self.assertEqual(
            result["old_decision"], "reject_less_than_one_trade_per_3_sessions"
        )
        self.assertEqual(result["learning_admission_status"], "blocked")
        self.assertEqual(result["paper_admission_status"], "blocked")
        self.assertEqual(result["live_trade_status"], "blocked")
        self.assertIsNone(result["long_run_expectancy_after_declared_friction"])
        self.assertIn("legacy_fixed_cost_readback_not_cost_authority", result["blockers"])
        self.assertIn("terminal_decision_summary.md", result["evidence_paths"])
        self.assertIn("summary.json", result["evidence_paths"])
        self.assertIn("leaderboard.csv", result["evidence_paths"])
        self.assertFalse(result["promotion_allowed"])
        self.assertFalse(result["trade_usable"])


if __name__ == "__main__":
    unittest.main()
