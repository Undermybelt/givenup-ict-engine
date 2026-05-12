from __future__ import annotations

import importlib.util
import json
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
RUN_TOMAC = RUN_ROOT / "workspace" / "auto-quant" / "run_tomac.py"
STRATEGY = "TomacNQ_KillzoneBreakout"


def load_run_tomac():
    spec = importlib.util.spec_from_file_location("isolated_run_tomac", RUN_TOMAC)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {RUN_TOMAC}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def describe(value):
    out = {"type": type(value).__name__}
    if hasattr(value, "shape"):
        out["shape"] = list(value.shape)
        out["columns"] = [str(c) for c in getattr(value, "columns", [])]
    elif isinstance(value, dict):
        out["len"] = len(value)
        out["keys"] = [str(k) for k in list(value.keys())[:40]]
    elif isinstance(value, (list, tuple)):
        out["len"] = len(value)
        out["sample_types"] = [type(v).__name__ for v in list(value)[:5]]
    else:
        out["repr"] = repr(value)[:300]
    return out


def main() -> int:
    run_tomac = load_run_tomac()
    results = run_tomac.run_backtest(STRATEGY)
    strategy = results.get("strategy", {}).get(STRATEGY, {}) or {}
    shape = {
        "top_level": describe(results),
        "strategy": describe(strategy),
        "strategy_children": {str(k): describe(v) for k, v in strategy.items()},
    }
    print(json.dumps(shape, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
