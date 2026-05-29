#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import io
import tracemalloc
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPT = Path(__file__).with_name("run_tomac_nq_bidir_opening_drive_exact_downstream_v1.py")
EXPECTED_BRANCH = (
    "TrendExpansion -> OpeningDrive -> BidirectionalIntradayTrendContinuation -> "
    "tomac_nq_bidir_opening_drive_t10_w0_e900_x1245_exact_v1"
)
EXPECTED_FACTOR_ID = "tomac_nq_bidir_opening_drive_t10_w0_e900_x1245_exact_v1"
EXPECTED_ROW_CAPS = {
    "1m": 2000,
    "5m": 1000,
    "15m": 500,
    "30m": 300,
    "1h": 200,
    "4h": 120,
    "1d": 90,
}


def load_module():
    spec = importlib.util.spec_from_file_location("tomac_bidir_exact_downstream", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load wrapper: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TomacBidirExactDownstreamTests(unittest.TestCase):
    def test_run_cli_help_exits_without_creating_run_root(self) -> None:
        module = load_module()

        original_root = module.ROOT
        with tempfile.TemporaryDirectory() as tmp:
            module.ROOT = Path(tmp) / "help-root"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                rc = module.run_cli(["--help"])

            self.assertEqual(rc, 0)
            self.assertIn("TOMAC NQ bidirectional opening-drive exact downstream", buffer.getvalue())
            self.assertFalse(module.ROOT.exists())

        module.ROOT = original_root

    def test_strategy_library_preserves_exact_branch_and_source_root(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            module.MATERIALS = tmp_path / "materials"
            module.SOURCE = tmp_path / "source-root"
            module.SOURCE_LIBRARY = tmp_path / "source-root/materials/library.json"
            module.SOURCE_LIBRARY.parent.mkdir(parents=True, exist_ok=True)
            module.SOURCE_LIBRARY.write_text(
                json.dumps(
                    {
                        "manifest_version": "1.0",
                        "timeframe": "1m",
                        "strategies": [
                            {
                                "name": EXPECTED_FACTOR_ID,
                                "status": "ok",
                                "metadata": {"branch_path": EXPECTED_BRANCH},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            library = module.write_strategy_library()
            payload = json.loads(library.read_text(encoding="utf-8"))
            strategy = payload["strategies"][0]
            metadata = strategy["metadata"]

        self.assertEqual(strategy["name"], EXPECTED_FACTOR_ID)
        self.assertEqual(metadata["branch_path"], EXPECTED_BRANCH)
        self.assertEqual(metadata["regime_profit_branch_path"], EXPECTED_BRANCH)
        self.assertEqual(metadata["bounded_rows"], EXPECTED_ROW_CAPS)
        self.assertEqual(metadata["source_packet"], str(module.SOURCE))
        self.assertFalse(metadata["promotion_allowed"])
        self.assertFalse(metadata["trade_usable"])

    def test_prepare_local_data_uses_exact_owner_workspace_ladder(self) -> None:
        module = load_module()

        original_root = module.ROOT
        original_checks = module.CHECKS
        original_data_dir = module.DATA_DIR
        original_source = module.SOURCE
        original_row_caps = dict(module.ROW_CAPS)
        original_feather_to_csv = module.feather_to_csv
        original_trim_csv_rows = module.trim_csv_rows

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            module.ROOT = tmp_path / "root"
            module.CHECKS = module.ROOT / "checks"
            module.DATA_DIR = module.ROOT / "data/provider/normalized"
            module.SOURCE = tmp_path / "source"
            module.ROW_CAPS = dict(EXPECTED_ROW_CAPS)

            data_root = module.SOURCE / "aq_workspace/user_data/data/futures"
            data_root.mkdir(parents=True, exist_ok=True)
            for timeframe in EXPECTED_ROW_CAPS:
                (data_root / f"NQ_USD-{timeframe}-futures.feather").write_text("placeholder", encoding="utf-8")

            seen = []

            def fake_feather_to_csv(source_feather: Path, target_csv: Path, py_runner: Path) -> int:
                seen.append(source_feather.name)
                target_csv.parent.mkdir(parents=True, exist_ok=True)
                target_csv.write_text("timestamp,open,high,low,close,volume\n", encoding="utf-8")
                return 123

            def fake_trim_csv_rows(source: Path, target: Path, keep_rows: int) -> int:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(
                        handle,
                        fieldnames=["timestamp", "open", "high", "low", "close", "volume"],
                    )
                    writer.writeheader()
                    writer.writerow(
                        {
                            "timestamp": "2026-01-01T00:00:00+00:00",
                            "open": 1.0,
                            "high": 2.0,
                            "low": 0.5,
                            "close": 1.5,
                            "volume": 10,
                        }
                    )
                return keep_rows

            module.feather_to_csv = fake_feather_to_csv
            module.trim_csv_rows = fake_trim_csv_rows

            summary = module.prepare_local_data()
            source_summary = json.loads((module.CHECKS / "source_data_summary.json").read_text(encoding="utf-8"))
            cleaned_15m = module.DATA_DIR / "cleaned-15m" / "tomac_nq_bidir_opening_drive_exact_downstream_v1.continuous-15m.json"
            cleaned_1d = module.DATA_DIR / "cleaned-1d" / "tomac_nq_bidir_opening_drive_exact_downstream_v1.continuous-1d.json"
            self.assertTrue(cleaned_15m.exists())
            self.assertTrue(cleaned_1d.exists())
            cleaned_payload = json.loads(cleaned_15m.read_text(encoding="utf-8"))
            self.assertEqual(cleaned_payload["symbol"], module.SYMBOL)
            self.assertEqual(len(cleaned_payload["candles"]), 1)

        self.assertEqual(set(summary), set(EXPECTED_ROW_CAPS))
        self.assertEqual(set(source_summary["timeframes"]), set(EXPECTED_ROW_CAPS))
        self.assertEqual(sorted(seen), sorted(f"NQ_USD-{tf}-futures.feather" for tf in EXPECTED_ROW_CAPS))
        self.assertEqual(source_summary["timeframes"]["15m"]["kept_rows"], EXPECTED_ROW_CAPS["15m"])
        self.assertEqual(source_summary["timeframes"]["1d"]["kept_rows"], EXPECTED_ROW_CAPS["1d"])

        module.ROOT = original_root
        module.CHECKS = original_checks
        module.DATA_DIR = original_data_dir
        module.SOURCE = original_source
        module.ROW_CAPS = original_row_caps
        module.feather_to_csv = original_feather_to_csv
        module.trim_csv_rows = original_trim_csv_rows

    def test_prepare_local_data_reuses_existing_full_csv_without_feather_read(self) -> None:
        module = load_module()

        original_root = module.ROOT
        original_checks = module.CHECKS
        original_data_dir = module.DATA_DIR
        original_source = module.SOURCE
        original_row_caps = dict(module.ROW_CAPS)
        original_source_full_csv_root = module.SOURCE_FULL_CSV_ROOT
        original_feather_to_csv = module.feather_to_csv

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            module.ROOT = tmp_path / "root"
            module.CHECKS = module.ROOT / "checks"
            module.DATA_DIR = module.ROOT / "data/provider/normalized"
            module.SOURCE = tmp_path / "source"
            module.ROW_CAPS = {"1m": 2, "5m": 1}
            module.SOURCE_FULL_CSV_ROOT = tmp_path / "source-full-csv"
            module.SOURCE_FULL_CSV_ROOT.mkdir(parents=True)

            for timeframe in module.ROW_CAPS:
                csv_path = module.SOURCE_FULL_CSV_ROOT / f"nq_usd_{timeframe}_full.csv"
                with csv_path.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(
                        handle,
                        fieldnames=["timestamp", "open", "high", "low", "close", "volume"],
                    )
                    writer.writeheader()
                    for idx in range(3):
                        writer.writerow(
                            {
                                "timestamp": f"2026-01-01T00:0{idx}:00+00:00",
                                "open": idx,
                                "high": idx + 1,
                                "low": idx - 1,
                                "close": idx + 0.5,
                                "volume": 10,
                            }
                        )

            def fail_feather_to_csv(*_args: object, **_kwargs: object) -> int:
                raise AssertionError("feather_to_csv should not run when reusable full CSVs exist")

            module.feather_to_csv = fail_feather_to_csv

            summary = module.prepare_local_data()

        self.assertEqual(summary["1m"]["full_rows"], "reused_existing_csv")
        self.assertEqual(summary["1m"]["kept_rows"], 2)
        self.assertEqual(summary["5m"]["kept_rows"], 1)
        self.assertEqual(summary["1m"]["full_csv"], str(module.SOURCE_FULL_CSV_ROOT / "nq_usd_1m_full.csv"))

        module.ROOT = original_root
        module.CHECKS = original_checks
        module.DATA_DIR = original_data_dir
        module.SOURCE = original_source
        module.ROW_CAPS = original_row_caps
        module.SOURCE_FULL_CSV_ROOT = original_source_full_csv_root
        module.feather_to_csv = original_feather_to_csv

    def test_lineage_counters_parse_validation_tuple_strings(self) -> None:
        module = load_module()

        counters = module.validation_counters(
            {
                "split_reason_lineage": [
                    "path_ranker=Ranker runtime raw_scored_mature=604/30 production_validation=604/30 observation_validation=23/30"
                ]
            }
        )

        self.assertEqual(
            counters,
            {
                "raw_scored_mature": "604/30",
                "production_validation": "604/30",
                "observation_validation": "23/30",
            },
        )

    def test_practical_admission_uses_current_readiness_floor_and_transition_hazard_is_telemetry(self) -> None:
        module = load_module()

        flags = module.practical_admission_flags(
            actionable=True,
            branch_survived=True,
            candidate_status="trade_candidate",
            counters={
                "raw_scored_mature": "1155/30",
                "production_validation": "1155/30",
                "observation_validation": "32/30",
            },
            readiness=0.4571420722343286,
            hazard=0.91,
            path_ranker_used=True,
            all_ok=True,
        )

        self.assertTrue(flags["validation_ready"])
        self.assertTrue(flags["branch_local_admitted"])
        self.assertTrue(flags["path_ranker_used"])
        self.assertFalse(flags["promotion_allowed"])
        self.assertFalse(flags["trade_usable"])
        self.assertFalse(flags["update_goal"])

    def test_practical_admission_keeps_trade_flags_false_until_path_ranker_is_used(self) -> None:
        module = load_module()

        flags = module.practical_admission_flags(
            actionable=True,
            branch_survived=True,
            candidate_status="trade_candidate",
            counters={
                "raw_scored_mature": "1155/30",
                "production_validation": "1155/30",
                "observation_validation": "32/30",
            },
            readiness=0.4571420722343286,
            hazard=0.43,
            path_ranker_used=False,
            all_ok=True,
        )

        self.assertTrue(flags["branch_local_admitted"])
        self.assertFalse(flags["promotion_allowed"])
        self.assertFalse(flags["trade_usable"])
        self.assertFalse(flags["update_goal"])

    def test_trim_csv_rows_keeps_tail_with_bounded_memory(self) -> None:
        module = load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source.csv"
            target = tmp_path / "target.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["timestamp", "open", "high", "low", "close", "volume"],
                )
                writer.writeheader()
                for idx in range(50000):
                    writer.writerow(
                        {
                            "timestamp": f"2026-01-01T00:{idx % 60:02d}:00+00:00",
                            "open": idx,
                            "high": idx + 1,
                            "low": idx - 1,
                            "close": idx + 0.5,
                            "volume": idx * 10,
                        }
                    )

            tracemalloc.start()
            try:
                kept = module.trim_csv_rows(source, target, 25)
                _current, peak = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()

            with target.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(kept, 25)
        self.assertEqual(len(rows), 25)
        self.assertEqual(rows[0]["open"], "49975")
        self.assertEqual(rows[-1]["open"], "49999")
        self.assertLess(peak, 2_000_000)

    def test_main_uses_data_root_for_full_ladder_analyze(self) -> None:
        module = load_module()

        original_root = module.ROOT
        original_state = module.STATE
        original_cmd = module.CMD
        original_checks = module.CHECKS
        original_summaries = module.SUMMARIES
        original_materials = module.MATERIALS
        original_model_dir = module.MODEL_DIR
        original_data_dir = module.DATA_DIR
        original_scores = module.SCORES
        original_script = module.SCRIPT
        original_ict = module.ICT
        original_write_strategy_library = module.write_strategy_library
        original_prepare_local_data = module.prepare_local_data
        original_run_cmd = module.run_cmd
        original_write_summary = module.write_summary

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            module.ROOT = tmp_path / "root"
            module.STATE = module.ROOT / "state"
            module.CMD = module.ROOT / "command-output"
            module.CHECKS = module.ROOT / "checks"
            module.SUMMARIES = module.ROOT / "summaries"
            module.MATERIALS = module.ROOT / "materials"
            module.MODEL_DIR = module.ROOT / "path_ranker_model"
            module.DATA_DIR = module.ROOT / "data/provider/normalized"
            module.SCORES = module.ROOT / "path_ranker_scores.csv"
            module.SCRIPT = tmp_path / "script.py"
            module.SCRIPT.write_text("# test script\n", encoding="utf-8")
            module.ICT = Path("/tmp/fake-ict-engine")

            captured: list[tuple[str, list[object], int]] = []

            def fake_write_strategy_library() -> Path:
                path = module.MATERIALS / "library.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}", encoding="utf-8")
                return path

            def fake_prepare_local_data() -> dict:
                module.DATA_DIR.mkdir(parents=True, exist_ok=True)
                for timeframe in EXPECTED_ROW_CAPS:
                    (module.DATA_DIR / f"nq_usd_{timeframe}_ultra.csv").write_text(
                        "timestamp,open,high,low,close,volume\n",
                        encoding="utf-8",
                    )
                return {"prepared": True}

            def fake_run_cmd(name: str, argv: list[object], timeout: int = 300) -> dict:
                captured.append((name, list(argv), timeout))
                return {"name": name, "exit": 0, "timed_out": False}

            def fake_write_summary(command_results: list[dict], data_summary: dict) -> None:
                return None

            module.write_strategy_library = fake_write_strategy_library
            module.prepare_local_data = fake_prepare_local_data
            module.run_cmd = fake_run_cmd
            module.write_summary = fake_write_summary

            rc = module.main()

        analyze_cmds = [argv for name, argv, _timeout in captured if name in {"03_analyze_seed", "12_analyze_after_ranker"}]
        self.assertEqual(rc, 0)
        self.assertEqual(len(analyze_cmds), 2)
        for argv in analyze_cmds:
            self.assertIn("--data-root", argv)
            self.assertIn(module.DATA_DIR, argv)
            self.assertNotIn("--data-ltf", argv)
            self.assertNotIn("--data-mtf", argv)
            self.assertNotIn("--data-htf", argv)

        module.ROOT = original_root
        module.STATE = original_state
        module.CMD = original_cmd
        module.CHECKS = original_checks
        module.SUMMARIES = original_summaries
        module.MATERIALS = original_materials
        module.MODEL_DIR = original_model_dir
        module.DATA_DIR = original_data_dir
        module.SCORES = original_scores
        module.SCRIPT = original_script
        module.ICT = original_ict
        module.write_strategy_library = original_write_strategy_library
        module.prepare_local_data = original_prepare_local_data
        module.run_cmd = original_run_cmd
        module.write_summary = original_write_summary

    def test_write_summary_does_not_emit_closure_without_full_practical_lifecycle(self) -> None:
        module = load_module()

        original_root = module.ROOT
        original_state = module.STATE
        original_checks = module.CHECKS
        original_summaries = module.SUMMARIES

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            module.ROOT = tmp_path / "root"
            module.STATE = module.ROOT / "state"
            module.CHECKS = module.ROOT / "checks"
            module.SUMMARIES = module.ROOT / "summaries"
            state_symbol = module.STATE / module.SYMBOL
            state_symbol.mkdir(parents=True, exist_ok=True)
            (state_symbol / "policy_training").mkdir(parents=True, exist_ok=True)
            (state_symbol / "workflow_snapshot.json").write_text(
                json.dumps(
                    {
                        "closed_loop_branch_admission": {
                            "path_id": EXPECTED_BRANCH,
                            "actionable": True,
                            "candidate_status": "trade_candidate",
                        }
                    }
                ),
                encoding="utf-8",
            )
            (state_symbol / "execution_candidate.json").write_text(
                json.dumps(
                    {
                        "path_id": EXPECTED_BRANCH,
                        "actionable": True,
                        "candidate_status": "trade_candidate",
                    }
                ),
                encoding="utf-8",
            )
            (state_symbol / "execution_tree_trace.json").write_text(
                json.dumps(
                    {
                        "output": {
                            "path_id": EXPECTED_BRANCH,
                            "actionable": True,
                            "candidate_status": "trade_candidate",
                            "execution_readiness": 0.4571420722343286,
                            "hybrid_transition_hazard": 0.91,
                            "path_ranker_score_visible_to_execution_tree": True,
                            "path_ranker_score_used_by_execution_tree": True,
                            "split_reason_lineage": [
                                "path_ranker=Ranker runtime raw_scored_mature=1155/30 production_validation=1155/30 observation_validation=32/30"
                            ],
                        }
                    }
                ),
                encoding="utf-8",
            )
            (state_symbol / "policy_training/structural_path_ranking_target_summary.json").write_text(
                json.dumps({"rows": 1}),
                encoding="utf-8",
            )

            module.write_summary(
                [{"name": "all", "exit": 0, "timed_out": False}],
                {"prepared": True},
            )
            packet_path = module.SUMMARIES / "same_tree_practical_closure.json"
            metrics_path = module.CHECKS / "terminal_metrics.json"
            metrics_exists = metrics_path.exists()
            packet_exists = packet_path.exists()

        self.assertTrue(metrics_exists)
        self.assertFalse(packet_exists)

        module.ROOT = original_root
        module.STATE = original_state
        module.CHECKS = original_checks
        module.SUMMARIES = original_summaries

    def test_write_summary_removes_stale_same_tree_practical_closure_when_gate_fails(self) -> None:
        module = load_module()

        original_root = module.ROOT
        original_state = module.STATE
        original_checks = module.CHECKS
        original_summaries = module.SUMMARIES

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            module.ROOT = tmp_path / "root"
            module.STATE = module.ROOT / "state"
            module.CHECKS = module.ROOT / "checks"
            module.SUMMARIES = module.ROOT / "summaries"
            state_symbol = module.STATE / module.SYMBOL
            state_symbol.mkdir(parents=True, exist_ok=True)
            (state_symbol / "policy_training").mkdir(parents=True, exist_ok=True)
            (state_symbol / "workflow_snapshot.json").write_text("{}", encoding="utf-8")
            (state_symbol / "execution_candidate.json").write_text(
                json.dumps(
                    {
                        "path_id": EXPECTED_BRANCH,
                        "actionable": True,
                        "candidate_status": "trade_candidate",
                    }
                ),
                encoding="utf-8",
            )
            (state_symbol / "execution_tree_trace.json").write_text(
                json.dumps(
                    {
                        "output": {
                            "path_id": EXPECTED_BRANCH,
                            "actionable": True,
                            "candidate_status": "trade_candidate",
                            "execution_readiness": 0.4571420722343286,
                            "path_ranker_score_visible_to_execution_tree": True,
                            "path_ranker_score_used_by_execution_tree": False,
                            "split_reason_lineage": [
                                "path_ranker=Ranker runtime raw_scored_mature=1155/30 production_validation=1155/30 observation_validation=32/30"
                            ],
                        }
                    }
                ),
                encoding="utf-8",
            )
            (state_symbol / "policy_training/structural_path_ranking_target_summary.json").write_text(
                json.dumps({"rows": 1}),
                encoding="utf-8",
            )
            module.SUMMARIES.mkdir(parents=True)
            stale_packet = module.SUMMARIES / "same_tree_practical_closure.json"
            stale_packet.write_text(
                json.dumps(
                    {
                        "status": "pass",
                        "promotion_allowed": True,
                        "trade_usable": True,
                        "provider_execution_feedback_chain": "pass",
                        "evidence_packet": "checks/terminal_metrics.json",
                    }
                ),
                encoding="utf-8",
            )

            module.write_summary(
                [{"name": "all", "exit": 0, "timed_out": False}],
                {"prepared": True},
            )
            stale_exists = stale_packet.exists()

        self.assertFalse(stale_exists)

        module.ROOT = original_root
        module.STATE = original_state
        module.CHECKS = original_checks
        module.SUMMARIES = original_summaries


if __name__ == "__main__":
    unittest.main()
