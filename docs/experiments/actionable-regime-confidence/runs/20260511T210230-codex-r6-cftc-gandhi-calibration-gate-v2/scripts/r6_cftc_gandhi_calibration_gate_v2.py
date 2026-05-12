#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
SOURCE = REPO / (
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T210030-codex-r6-cftc-schema-ready-calibration-gate-v1/"
    "scripts/r6_cftc_schema_ready_calibration_gate_v1.py"
)


def main() -> int:
    spec = importlib.util.spec_from_file_location("r6_cftc_schema_ready_calibration_gate_v1", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.RUN_ID = "20260511T210230-codex-r6-cftc-gandhi-calibration-gate-v2"
    module.RUN_ROOT = Path(__file__).resolve().parents[1]
    module.OUT = module.RUN_ROOT / "r6-cftc-gandhi-calibration-gate"
    module.CHECKS = module.RUN_ROOT / "checks"
    return module.main()


if __name__ == "__main__":
    raise SystemExit(main())
