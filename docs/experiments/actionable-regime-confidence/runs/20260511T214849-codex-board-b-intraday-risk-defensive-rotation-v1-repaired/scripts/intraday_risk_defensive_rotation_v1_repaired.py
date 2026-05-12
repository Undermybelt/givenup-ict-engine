#!/usr/bin/env python3
"""Failed fresh-root wrapper for IntradayRiskDefensiveRotationV1.

Retained only because the Board B ledger records this operational failure.
The wrapper is not self-contained: it imports the run-local source script from
the `214454` root, which was not present at the later readback.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


RUN_ID = "20260511T214849+0800-codex-board-b-intraday-risk-defensive-rotation-v1-repaired"
RUN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
SOURCE_SCRIPT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T214454-codex-board-b-intraday-risk-defensive-rotation-v1/scripts/"
    "intraday_risk_defensive_rotation_v1.py"
)


def load_source() -> Any:
    spec = importlib.util.spec_from_file_location("intraday_rotation_source_214454", SOURCE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import source script: {SOURCE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_source()
    module.RUN_ID = RUN_ID
    module.RUN_ROOT = RUN_ROOT
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
