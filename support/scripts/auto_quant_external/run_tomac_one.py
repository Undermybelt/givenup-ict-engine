"""
run_tomac_one.py — additive single-strategy wrapper around run_tomac.py with optional timeframe override.

Lives in the ict-engine repo so it does not modify the user's Auto-Quant
runtime layout. Imports run_tomac from the current Auto-Quant checkout; reuses
its _build_exchange_with_synthetic_pairs synthetic-market injection so
NQ/USD-style pseudo-pairs pass freqtrade's exchange validation.

The motivation is the freqtrade quirk surfaced in Slice 82: config.tomac.json
declares timeframe="1h" and freqtrade applies that to the data loader before
the strategy class's `timeframe = "5m"` attribute is read, which trips the
faster->slower @informative merge guard. Passing `--timeframe 5m` through
the args dict overrides the config-level timeframe up front and resolves it.

Usage (run from the Auto-Quant checkout so the synthetic-market path is
relative to the user's runtime data dir):

    cd <auto-quant-root>
    uv run python <ict-engine-repo>/\\
        support/scripts/auto_quant_external/run_tomac_one.py STRATEGY [TIMEFRAME] [EXPORT_PATH] [PAIRS] [TIMERANGE]

When EXPORT_PATH is provided the run enables `--export trades` and writes the
per-trade backtest result there for downstream portfolio-diversity scoring.

When PAIRS (comma-separated, e.g. "SPY/USD,IWM/USD") is provided it overrides
the config's pair_whitelist for cross-market validation. The synthetic-market
injection is rebuilt against the new pair list.

When TIMERANGE (freqtrade format "YYYYMMDD-YYYYMMDD") is provided it limits
the backtest window — used for train/test split validation.
"""
from __future__ import annotations

from contextlib import contextmanager
import importlib
import sys
import json
from pathlib import Path

AUTO_QUANT = Path.cwd()
if str(AUTO_QUANT) not in sys.path:
    sys.path.insert(0, str(AUTO_QUANT))

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import run_tomac as rt  # noqa: E402
from support.scripts.research import instrument_cost_model  # noqa: E402

from freqtrade.configuration import Configuration  # noqa: E402
from freqtrade.enums import RunMode  # noqa: E402
from freqtrade.optimize.backtesting import Backtesting  # noqa: E402


def _pair_tokens(pair: str) -> tuple[str, str]:
    base, _, quote = pair.partition("/")
    return base.upper(), quote.upper() or "USD"


def _futures_feather_exists(pair: str, timeframe: str | None, data_dir: Path) -> bool:
    base, quote = _pair_tokens(pair)
    timeframes = [timeframe] if timeframe else ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    stems = [f"{base}_{quote}-{tf}-futures.feather" for tf in timeframes if tf]
    search_roots = [data_dir / "futures", data_dir / "binance" / "futures"]
    return any((root / stem).exists() for root in search_roots for stem in stems)


def _futures_datadir(pair: str, timeframe: str | None, data_dir: Path) -> Path:
    base, quote = _pair_tokens(pair)
    timeframes = [timeframe] if timeframe else ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    stems = [f"{base}_{quote}-{tf}-futures.feather" for tf in timeframes if tf]
    for root in (data_dir, data_dir / "binance"):
        if any((root / "futures" / stem).exists() for stem in stems):
            return root
    return data_dir


def select_datadir_for_pairs(pairs: list[str] | None, timeframe: str | None, data_dir: Path) -> Path:
    if not pairs:
        return data_dir
    for pair in pairs:
        selected = _futures_datadir(pair, timeframe, data_dir)
        if selected != data_dir:
            return selected
    return data_dir


def should_use_futures_mode(
    pairs: list[str] | None,
    *,
    timeframe: str | None = None,
    data_dir: Path | None = None,
) -> bool:
    """Return true when the requested pseudo-pairs are futures-like.

    Short TOMAC index-futures strategies must run with Freqtrade futures mode;
    otherwise Freqtrade rejects `can_short=True` strategies as spot-market shorts.
    Non-futures pseudo-pairs such as QQQ/USD stay on the default spot path.
    """

    if not pairs:
        return False
    root = data_dir or Path(rt.DATA_DIR)
    for pair in pairs:
        base, _quote = _pair_tokens(pair)
        if instrument_cost_model.futures_cost_profile(base) is not None:
            return True
        if _futures_feather_exists(pair, timeframe, root):
            return True
    return False


def _synthetic_leverage_tiers(_pair: str) -> list[dict[str, float | None]]:
    return [
        {
            "minNotional": 0.0,
            "maxNotional": 1_000_000_000.0,
            "maintenanceMarginRate": 0.005,
            "maxLeverage": 20.0,
            "maintAmt": 0.0,
        }
    ]


def _attach_synthetic_leverage_tiers(exchange: object, pairs: list[str] | None) -> None:
    if not pairs:
        return
    try:
        tiers = getattr(exchange, "_leverage_tiers", None)
        if tiers is None:
            tiers = {}
            setattr(exchange, "_leverage_tiers", tiers)
        for pair in pairs:
            tiers[pair] = _synthetic_leverage_tiers(pair)
    except Exception:
        return


def write_backtest_export(results: dict[str, object], export_path: str | None) -> None:
    if not export_path:
        return
    path = Path(export_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, default=str), encoding="utf-8")


def build_backtest_args(
    *,
    strategy: str,
    timeframe: str | None = None,
    export_path: str | None = None,
    pairs: list[str] | None = None,
    timerange: str | None = None,
) -> dict[str, object]:
    datadir = Path(rt.DATA_DIR)
    if should_use_futures_mode(pairs, timeframe=timeframe, data_dir=datadir):
        datadir = select_datadir_for_pairs(pairs, timeframe, datadir)
    args: dict[str, object] = {
        "config": [str(rt.CONFIG)],
        "user_data_dir": str(rt.USER_DATA),
        "datadir": str(datadir),
        "strategy": strategy,
        "strategy_path": str(rt.STRATEGIES_DIR),
        "export": "trades" if export_path else "none",
        "exportfilename": Path(export_path) if export_path else None,
        "cache": "none",
    }
    if timeframe:
        args["timeframe"] = timeframe
    if pairs:
        args["pairs"] = pairs
    if timerange:
        args["timerange"] = timerange
    if should_use_futures_mode(pairs, timeframe=timeframe, data_dir=Path(rt.DATA_DIR)):
        args["trading_mode"] = "futures"
        args["margin_mode"] = "isolated"
        args["dataformat_ohlcv"] = "feather"
    return args


@contextmanager
def ohlcv_fill_missing_mode(*, fill_missing: bool):
    """Optionally force Freqtrade historical OHLCV loaders to keep source gaps."""

    if fill_missing:
        yield
        return
    from freqtrade.data import history  # noqa: WPS433

    patched: list[tuple[object, str, object]] = []

    def force_no_fill(func):
        def wrapper(*args, **kwargs):
            kwargs["fill_up_missing"] = False
            return func(*args, **kwargs)

        return wrapper

    def patch_attr(module: object | None, name: str) -> None:
        if module is None or not hasattr(module, name):
            return
        original = getattr(module, name)
        patched.append((module, name, original))
        setattr(module, name, force_no_fill(original))

    def optional_module(name: str) -> object | None:
        try:
            return importlib.import_module(name)
        except ImportError:
            return None

    patch_attr(history, "load_data")
    patch_attr(history, "load_pair_history")
    patch_attr(optional_module("freqtrade.data.history.history_utils"), "load_data")
    patch_attr(optional_module("freqtrade.data.history.history_utils"), "load_pair_history")
    patch_attr(optional_module("freqtrade.data.dataprovider"), "load_pair_history")

    try:
        yield
    finally:
        for module, name, original in reversed(patched):
            setattr(module, name, original)


def run(
    strategy: str,
    timeframe: str | None = None,
    export_path: str | None = None,
    pairs: list[str] | None = None,
    timerange: str | None = None,
    *,
    fill_missing: bool = True,
) -> int:
    args = build_backtest_args(
        strategy=strategy,
        timeframe=timeframe,
        export_path=export_path,
        pairs=pairs,
        timerange=timerange,
    )
    config = Configuration(args, RunMode.BACKTEST).get_config()
    if pairs:
        config["exchange"]["pair_whitelist"] = pairs
    if should_use_futures_mode(pairs or config["exchange"].get("pair_whitelist"), timeframe=timeframe):
        config["trading_mode"] = "futures"
        config["margin_mode"] = "isolated"
        config["dataformat_ohlcv"] = "feather"
    exchange = rt._build_exchange_with_synthetic_pairs(config)
    if config.get("trading_mode") == "futures":
        _attach_synthetic_leverage_tiers(exchange, config["exchange"].get("pair_whitelist"))
    with ohlcv_fill_missing_mode(fill_missing=fill_missing):
        bt = Backtesting(config, exchange=exchange)
        bt.start()
    write_backtest_export(bt.results, export_path)
    metrics = rt.extract_metrics(bt.results, strategy)
    rt.emit_block(
        strategy,
        rt.get_commit(),
        config["exchange"]["pair_whitelist"],
        metrics,
    )
    return 0


if __name__ == "__main__":
    argv = sys.argv[1:]
    fill_missing = True
    if "--no-fill-missing" in argv:
        fill_missing = False
        argv = [arg for arg in argv if arg != "--no-fill-missing"]
    if len(argv) < 1:
        print(
            "Usage: run_tomac_one.py STRATEGY [TIMEFRAME] [EXPORT_PATH] [PAIRS] [TIMERANGE]",
            file=sys.stderr,
        )
        raise SystemExit(2)
    strategy = argv[0]
    timeframe = argv[1] if len(argv) > 1 else None
    export_path = argv[2] if len(argv) > 2 else None
    pairs_arg = argv[3] if len(argv) > 3 else None
    pairs = [p.strip() for p in pairs_arg.split(",") if p.strip()] if pairs_arg else None
    timerange = argv[4] if len(argv) > 4 else None
    raise SystemExit(run(strategy, timeframe, export_path, pairs, timerange, fill_missing=fill_missing))
