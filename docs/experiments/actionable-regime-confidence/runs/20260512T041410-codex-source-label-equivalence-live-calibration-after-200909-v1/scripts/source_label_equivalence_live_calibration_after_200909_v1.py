#!/usr/bin/env python3
"""Rerun the existing source-label confidence calibration against the live intake root."""

from __future__ import annotations

import importlib.util
from pathlib import Path


RUN_ID = "20260512T041410-codex-source-label-equivalence-live-calibration-after-200909-v1"
SLUG = "source-label-equivalence-live-calibration-after-200909-v1"
OLD_SCRIPT = (
    Path(__file__).resolve().parents[6]
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260512T011056-codex-source-label-equivalence-calibration-after-root-poll-v1/"
    / "scripts/source_label_equivalence_confidence_calibration_after_root_poll_v1.py"
)


def main() -> int:
    spec = importlib.util.spec_from_file_location("source_label_calibration_base", OLD_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load calibration script: {OLD_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    run_root = Path(__file__).resolve().parents[1]
    module.RUN_ROOT = run_root
    module.RUN_ID = RUN_ID
    module.OUT = run_root / SLUG
    module.CHECKS = run_root / "checks"
    module.COMMAND_OUT = run_root / "command-output"
    return module.main()


if __name__ == "__main__":
    raise SystemExit(main())
