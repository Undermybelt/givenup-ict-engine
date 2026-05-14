#!/usr/bin/env python3
"""Board B scoped Manipulation stop/take-profit grid v2.

This imports the immutable v1 evaluator, changes only run identity and a
predeclared broader stop/take-profit grid, then writes all artifacts under this
run root.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


RUN_ID = "20260511T205047+0800-codex-board-b-manipulation-stop-tp-grid-v2"
RUN_SLUG = "20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2"
RECIPE_ID = "ManipulationStopTakeProfitGridV2"
SCHEMA_VERSION = "board-b-manipulation-stop-tp-grid/v2"


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "Cargo.toml").exists() and (candidate / "docs").exists():
            return candidate
    raise RuntimeError(f"cannot locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
BASE_SCRIPT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T204718-codex-board-b-manipulation-stop-tp-v1/scripts/"
    "manipulation_stop_tp_v1.py"
)


def load_base_module() -> Any:
    spec = importlib.util.spec_from_file_location("manipulation_stop_tp_v1_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import base evaluator: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def patch_module(module: Any) -> None:
    run_root = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs" / RUN_SLUG
    out_dir = run_root / "manipulation-stop-tp-grid-v2"
    check_dir = run_root / "checks"
    fail_closed_dir = run_root / "ict-engine-fail-closed"
    variants: list[dict[str, Any]] = []
    for horizon in [24, 36, 48, 72]:
        for tp in [0.06, 0.08, 0.10, 0.12]:
            for sl in [0.04, 0.05, 0.06]:
                variants.append(
                    {
                        "variant_id": f"short_tp{int(tp * 1000):03d}_sl{int(sl * 1000):03d}_h{horizon}",
                        "direction": "short",
                        "tp": tp,
                        "sl": sl,
                        "horizon": horizon,
                    }
                )
    for horizon in [12, 24, 48]:
        for tp in [0.03, 0.05, 0.08]:
            variants.append(
                {
                    "variant_id": f"long_tp{int(tp * 1000):03d}_sl030_h{horizon}",
                    "direction": "long",
                    "tp": tp,
                    "sl": 0.03,
                    "horizon": horizon,
                }
            )

    module.RUN_ID = RUN_ID
    module.RUN_SLUG = RUN_SLUG
    module.RECIPE_ID = RECIPE_ID
    module.SCHEMA_VERSION = SCHEMA_VERSION
    module.RUN_ROOT = run_root
    module.OUT_DIR = out_dir
    module.CHECK_DIR = check_dir
    module.FAIL_CLOSED_DIR = fail_closed_dir
    module.SUMMARY_CSV = out_dir / "manipulation_stop_tp_grid_v2_summary.csv"
    module.BRANCH_ROWS_CSV = out_dir / "manipulation_stop_tp_grid_v2_branch_rows.csv"
    module.REPORT_JSON = out_dir / "manipulation_stop_tp_grid_v2.json"
    module.REPORT_MD = out_dir / "manipulation_stop_tp_grid_v2.md"
    module.ASSERTIONS = check_dir / "manipulation_stop_tp_grid_v2_assertions.out"
    module.FAIL_CLOSED_MD = fail_closed_dir / "manipulation_stop_tp_grid_v2_fail_closed_summary.md"
    module.VARIANTS = variants


def main() -> int:
    module = load_base_module()
    patch_module(module)
    return module.main()


if __name__ == "__main__":
    raise SystemExit(main())
