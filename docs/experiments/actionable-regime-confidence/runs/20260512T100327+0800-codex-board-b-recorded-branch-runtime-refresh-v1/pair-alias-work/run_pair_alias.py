from __future__ import annotations

import importlib.util
from pathlib import Path


SOURCE = Path(
    "/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/"
    "20260512T092832+0800-codex-board-b-aq-first-nursery-ltf-v1/"
    "state_b2r_nq_ltf_nursery_v1/.deps/auto-quant/run_tomac.py"
).resolve()
WORK = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("run_tomac_source", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"could not load {SOURCE}")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.USER_DATA = WORK / "user_data"
module.STRATEGIES_DIR = module.USER_DATA / "strategies_external"
module.DATA_DIR = module.USER_DATA / "data"
module.CONFIG = WORK / "config.tomac.nq_alias.json"

raise SystemExit(module.main())
