#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("run_tomac_compression_breakout_continuation_prep_v1.py")
SPEC = importlib.util.spec_from_file_location("tomac_compression_breakout_continuation_prep", SCRIPT)


class TomacCompressionBreakoutContinuationPrepTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        assert SPEC is not None and SPEC.loader is not None
        sys.modules[SPEC.name] = module
        SPEC.loader.exec_module(module)
        return module

    def test_plan_preserves_regime_rooted_branch_and_commands(self) -> None:
        module = self.load_module()

        plan = module.build_plan(Path("/tmp/out"), Path("/tmp/compact"), launch=False)

        self.assertEqual(
            plan.branch_path,
            "RangeConsolidation -> VolatilityCompression -> CompressionBreakoutContinuation -> tomac_idxfut_clean_compression_breakout_continuation_1m_v1",
        )
        self.assertEqual(plan.factor_id, "tomac_idxfut_clean_compression_breakout_continuation_1m_v1")
        self.assertEqual(plan.run_mode, "source_prep_no_launch")
        self.assertIn("run_tomac_index_futures_clean_aq_v1.py", " ".join(plan.command))
        self.assertIn("--families compression_breakout_continuation", " ".join(plan.command))
        self.assertIn("--clean-only", plan.command)
        self.assertIn("tomac_factor_coverage_matrix.py", " ".join(plan.coverage_command))

    def test_plan_uses_current_python_for_child_commands(self) -> None:
        module = self.load_module()

        plan = module.build_plan(Path("/tmp/out"), Path("/tmp/compact"), launch=True)

        self.assertEqual(plan.command[0], sys.executable)
        self.assertEqual(plan.coverage_command[0], sys.executable)

    def test_main_prep_only_writes_plan_and_summary_without_scan(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "run"
            compact = Path(tmpdir) / "compact"

            def fake_run_cmd(name: str, argv: list[str], cwd: Path, output_root: Path) -> dict[str, object]:
                (output_root / "checks").mkdir(parents=True, exist_ok=True)
                (output_root / "checks" / f"{name}.exit").write_text("0\n", encoding="utf-8")
                return {"name": name, "exit": 0, "stdout": "", "stderr": ""}

            module.run_cmd = fake_run_cmd
            exit_code = module.main(["--root", str(root), "--compact-root", str(compact)])

            self.assertEqual(exit_code, 0)
            summary = json.loads((root / "summaries" / "terminal_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["run_mode"], "source_prep_no_launch")
            self.assertEqual(summary["status"], "source_prep_complete")
            self.assertFalse(summary["scan_executed"])
            self.assertIsNone(summary["scan_exit"])
            compact_summary = json.loads((compact / "summaries" / "terminal_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(compact_summary["status"], "source_prep_complete")

    def test_main_launch_updates_summary_to_finished_after_scan(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "run"
            compact = Path(tmpdir) / "compact"

            def fake_run_cmd(name: str, argv: list[str], cwd: Path, output_root: Path) -> dict[str, object]:
                (output_root / "checks").mkdir(parents=True, exist_ok=True)
                (output_root / "checks" / f"{name}.exit").write_text("0\n", encoding="utf-8")
                return {"name": name, "exit": 0, "stdout": "", "stderr": ""}

            module.run_cmd = fake_run_cmd
            module.load_claim_audit = lambda: {"claims": [], "live_factor_processes": []}
            exit_code = module.main(["--root", str(root), "--compact-root", str(compact), "--launch"])

            self.assertEqual(exit_code, 0)
            summary = json.loads((root / "summaries" / "terminal_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["run_mode"], "launch")
            self.assertEqual(summary["status"], "launch_finished")
            self.assertTrue(summary["scan_executed"])
            self.assertEqual(summary["scan_exit"], 0)

    def test_main_launch_blocks_foreign_active_claim_before_scan(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "run"
            compact = Path(tmpdir) / "compact"

            def fake_run_cmd(name: str, argv: list[str], cwd: Path, output_root: Path) -> dict[str, object]:
                if name == "tomac_clean_aq":
                    self.fail("launch guard must block before starting AQ")
                (output_root / "checks").mkdir(parents=True, exist_ok=True)
                (output_root / "checks" / f"{name}.exit").write_text("0\n", encoding="utf-8")
                return {"name": name, "exit": 0, "stdout": "", "stderr": ""}

            module.run_cmd = fake_run_cmd
            module.load_claim_audit = lambda: {
                "claims": [
                    {
                        "claim_file": "foreign.claim",
                        "status": "active",
                        "run_root": str(Path(tmpdir) / "foreign-root"),
                        "coordination_only": False,
                    }
                ],
                "live_factor_processes": [],
            }

            exit_code = module.main(["--root", str(root), "--compact-root", str(compact), "--launch"])

            self.assertEqual(exit_code, 1)
            summary = json.loads((root / "summaries" / "terminal_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "launch_blocked_by_collision_guard")
            self.assertFalse(summary["scan_executed"])
            self.assertIsNone(summary["scan_exit"])
            self.assertEqual(summary["collision_guard"]["foreign_active_claims"], ["foreign.claim"])

    def test_collision_guard_allows_current_root_claim_and_blocks_foreign_live_root(self) -> None:
        module = self.load_module()

        with tempfile.TemporaryDirectory() as tmpdir:
            current_root = Path(tmpdir) / "current" / "run"
            audit = {
                "claims": [
                    {
                        "claim_file": "current.claim",
                        "status": "active",
                        "run_root": str(current_root.parent),
                        "coordination_only": False,
                    }
                ],
                "live_factor_processes": [
                    {"pid": 42, "run_root": str(Path(tmpdir) / "foreign" / "run")},
                ],
            }

            guard = module.collision_guard(audit, current_root)

            self.assertFalse(guard["ready"])
            self.assertEqual(guard["foreign_active_claims"], [])
            self.assertEqual(guard["foreign_live_roots"], [str(Path(tmpdir) / "foreign" / "run")])


if __name__ == "__main__":
    unittest.main()
