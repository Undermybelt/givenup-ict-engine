"""
run_tomac_one.py — additive single-strategy wrapper around run_tomac.py with optional timeframe override.

Lives in the ict-engine repo so it does not modify the user's ~/Auto-Quant
runtime layout. Imports run_tomac from /Users/thrill3r/Auto-Quant; reuses
its _build_exchange_with_synthetic_pairs synthetic-market injection so
NQ/USD-style pseudo-pairs pass freqtrade's exchange validation.

The motivation is the freqtrade quirk surfaced in Slice 82: config.tomac.json
declares timeframe="1h" and freqtrade applies that to the data loader before
the strategy class's `timeframe = "5m"` attribute is read, which trips the
faster->slower @informative merge guard. Passing `--timeframe 5m` through
the args dict overrides the config-level timeframe up front and resolves it.

Usage (run from /Users/thrill3r/Auto-Quant so the synthetic-market path is
relative to the user's runtime data dir):

    cd /Users/thrill3r/Auto-Quant
    uv run python /Users/thrill3r/projects-ict-engine/ict-engine/\\
        scripts/auto_quant_external/run_tomac_one.py STRATEGY [TIMEFRAME]
"""
from __future__ import annotations

import sys
from pathlib import Path

AUTO_QUANT = Path("/Users/thrill3r/Auto-Quant")
if str(AUTO_QUANT) not in sys.path:
    sys.path.insert(0, str(AUTO_QUANT))

import run_tomac as rt  # noqa: E402

from freqtrade.configuration import Configuration  # noqa: E402
from freqtrade.enums import RunMode  # noqa: E402
from freqtrade.optimize.backtesting import Backtesting  # noqa: E402


def run(strategy: str, timeframe: str | None = None) -> int:
    args = {
        "config": [str(rt.CONFIG)],
        "user_data_dir": str(rt.USER_DATA),
        "datadir": str(rt.DATA_DIR),
        "strategy": strategy,
        "strategy_path": str(rt.STRATEGIES_DIR),
        "export": "none",
        "exportfilename": None,
        "cache": "none",
    }
    if timeframe:
        args["timeframe"] = timeframe
    config = Configuration(args, RunMode.BACKTEST).get_config()
    exchange = rt._build_exchange_with_synthetic_pairs(config)
    bt = Backtesting(config, exchange=exchange)
    bt.start()
    metrics = rt.extract_metrics(bt.results, strategy)
    rt.emit_block(
        strategy,
        rt.get_commit(),
        config["exchange"]["pair_whitelist"],
        metrics,
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: run_tomac_one.py STRATEGY [TIMEFRAME]", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
