from __future__ import annotations

import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "run_tomac_one.py"


class RunTomacOneConfigTests(unittest.TestCase):
    def load_module(self, tmp: Path, captured: dict[str, object]):
        user_data = tmp / "user_data"
        data_dir = user_data / "data"
        strategies = user_data / "strategies_external"
        strategies.mkdir(parents=True)

        run_tomac = types.ModuleType("run_tomac")
        run_tomac.CONFIG = tmp / "config.tomac.json"
        run_tomac.USER_DATA = user_data
        run_tomac.DATA_DIR = data_dir
        run_tomac.STRATEGIES_DIR = strategies
        run_tomac.get_commit = lambda: "testcommit"
        run_tomac._build_exchange_with_synthetic_pairs = lambda config: object()
        run_tomac.extract_metrics = lambda results, strategy: {"aggregate": {}, "per_pair": {}}
        run_tomac.emit_block = lambda strategy, commit, pairs, metrics: None

        configuration = types.ModuleType("freqtrade.configuration")

        class FakeConfiguration:
            def __init__(self, args, mode):
                self.args = dict(args)
                captured["args"] = dict(args)

            def get_config(self):
                return {
                    "exchange": {"name": "binance", "pair_whitelist": ["ES/USD"]},
                    "trading_mode": self.args.get("trading_mode", "spot"),
                    "margin_mode": self.args.get("margin_mode", ""),
                }

        configuration.Configuration = FakeConfiguration

        enums = types.ModuleType("freqtrade.enums")
        enums.RunMode = types.SimpleNamespace(BACKTEST="backtest")

        backtesting_module = types.ModuleType("freqtrade.optimize.backtesting")

        class FakeBacktesting:
            def __init__(self, config, exchange=None):
                captured["config"] = dict(config)
                self.results = captured.get("backtesting_results", {"strategy": {}})
                history = sys.modules.get("freqtrade.data.history")
                if history is not None and hasattr(history, "load_data"):
                    history.load_data(datadir="fixture", pairs=["NQ/USD"], timeframe="15m")

            def start(self):
                captured["started"] = True

        backtesting_module.Backtesting = FakeBacktesting
        data_module = types.ModuleType("freqtrade.data")
        history_module = types.ModuleType("freqtrade.data.history")
        history_module.load_data = lambda **kwargs: captured.setdefault(
            "history_load_calls", []
        ).append(dict(kwargs))
        data_module.history = history_module

        old_modules = {
            name: sys.modules.get(name)
            for name in (
                "run_tomac",
                "freqtrade",
                "freqtrade.configuration",
                "freqtrade.enums",
                "freqtrade.optimize",
                "freqtrade.optimize.backtesting",
                "freqtrade.data",
                "freqtrade.data.history",
            )
        }
        sys.modules["run_tomac"] = run_tomac
        sys.modules["freqtrade"] = types.ModuleType("freqtrade")
        sys.modules["freqtrade.configuration"] = configuration
        sys.modules["freqtrade.enums"] = enums
        sys.modules["freqtrade.optimize"] = types.ModuleType("freqtrade.optimize")
        sys.modules["freqtrade.optimize.backtesting"] = backtesting_module
        sys.modules["freqtrade.data"] = data_module
        sys.modules["freqtrade.data.history"] = history_module

        spec = importlib.util.spec_from_file_location("run_tomac_one_under_test", SCRIPT)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load {SCRIPT}")
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        finally:
            for name, value in old_modules.items():
                if value is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = value
        return module, strategies, data_dir

    def test_short_strategy_forces_futures_mode_before_strategy_resolution(self) -> None:
        with TemporaryDirectory() as tmpdir:
            captured: dict[str, object] = {}
            module, strategies, _data_dir = self.load_module(Path(tmpdir), captured)
            (strategies / "ShortNqCandidate.py").write_text(
                "class ShortNqCandidate:\n    can_short = True\n",
                encoding="utf-8",
            )

            module.run("ShortNqCandidate", "30m", None, ["NQ/USD"], "20210103-20251231")

        args = captured["args"]
        self.assertEqual(args["trading_mode"], "futures")
        self.assertEqual(args["margin_mode"], "isolated")

    def test_existing_futures_feather_forces_futures_mode_for_long_strategy(self) -> None:
        with TemporaryDirectory() as tmpdir:
            captured: dict[str, object] = {}
            module, strategies, data_dir = self.load_module(Path(tmpdir), captured)
            (strategies / "LongNqCandidate.py").write_text(
                "class LongNqCandidate:\n    can_short = False\n",
                encoding="utf-8",
            )
            futures_file = data_dir / "binance" / "futures" / "NQ_USD-15m-futures.feather"
            futures_file.parent.mkdir(parents=True)
            futures_file.write_text("placeholder", encoding="utf-8")

            module.run("LongNqCandidate", "15m", None, ["NQ/USD"], "20210103-20251231")

        args = captured["args"]
        self.assertEqual(args["trading_mode"], "futures")
        self.assertEqual(args["margin_mode"], "isolated")
        self.assertEqual(Path(args["datadir"]), data_dir / "binance")

    def test_root_futures_feather_keeps_root_data_dir(self) -> None:
        with TemporaryDirectory() as tmpdir:
            captured: dict[str, object] = {}
            module, strategies, data_dir = self.load_module(Path(tmpdir), captured)
            (strategies / "LongNqCandidate.py").write_text(
                "class LongNqCandidate:\n    can_short = False\n",
                encoding="utf-8",
            )
            futures_file = data_dir / "futures" / "NQ_USD-15m-futures.feather"
            futures_file.parent.mkdir(parents=True)
            futures_file.write_text("placeholder", encoding="utf-8")

            module.run("LongNqCandidate", "15m", None, ["NQ/USD"], "20210103-20251231")

        args = captured["args"]
        self.assertEqual(args["trading_mode"], "futures")
        self.assertEqual(args["margin_mode"], "isolated")
        self.assertEqual(Path(args["datadir"]), data_dir)

    def test_plain_spot_long_strategy_keeps_default_mode(self) -> None:
        with TemporaryDirectory() as tmpdir:
            captured: dict[str, object] = {}
            module, strategies, _data_dir = self.load_module(Path(tmpdir), captured)
            (strategies / "LongSpyCandidate.py").write_text(
                "class LongSpyCandidate:\n    can_short = False\n",
                encoding="utf-8",
            )

            module.run("LongSpyCandidate", "15m", None, ["SPY/USD"], "20210103-20251231")

        args = captured["args"]
        self.assertNotIn("trading_mode", args)
        self.assertNotIn("margin_mode", args)

    def test_run_writes_backtesting_results_to_requested_export_path(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            export_path = tmp / "exports" / "trades.json"
            strategy = "LongNqCandidate"
            captured: dict[str, object] = {
                "backtesting_results": {
                    "strategy": {
                        strategy: {
                            "trades": [
                                {
                                    "pair": "NQ/USD",
                                    "open_timestamp": 1700000000000,
                                    "close_timestamp": 1700000300000,
                                    "profit_abs": 12.5,
                                }
                            ],
                            "results_per_pair": [],
                        }
                    },
                    "strategy_comparison": [],
                }
            }
            module, strategies, _data_dir = self.load_module(tmp, captured)
            (strategies / f"{strategy}.py").write_text(
                f"class {strategy}:\n    can_short = False\n",
                encoding="utf-8",
            )

            module.run(strategy, "5m", str(export_path), ["NQ/USD"], "20210103-20251231")
            self.assertTrue(export_path.exists())
            payload = json.loads(export_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["strategy"][strategy]["trades"][0]["pair"], "NQ/USD")
            self.assertEqual(payload["strategy"][strategy]["trades"][0]["profit_abs"], 12.5)

    def test_no_fill_missing_mode_patches_freqtrade_history_loader(self) -> None:
        with TemporaryDirectory() as tmpdir:
            captured: dict[str, object] = {}
            module, strategies, _data_dir = self.load_module(Path(tmpdir), captured)
            (strategies / "LongNqCandidate.py").write_text(
                "class LongNqCandidate:\n    can_short = False\n",
                encoding="utf-8",
            )

            data_module = types.ModuleType("freqtrade.data")
            history_module = types.ModuleType("freqtrade.data.history")
            history_module.load_data = lambda **kwargs: captured.setdefault(
                "history_load_calls", []
            ).append(dict(kwargs))
            data_module.history = history_module
            with mock.patch.dict(
                sys.modules,
                {
                    "freqtrade": types.ModuleType("freqtrade"),
                    "freqtrade.data": data_module,
                    "freqtrade.data.history": history_module,
                },
            ):
                module.run(
                    "LongNqCandidate",
                    "15m",
                    None,
                    ["NQ/USD"],
                    "20210103-20251231",
                    fill_missing=False,
                )

        calls = captured["history_load_calls"]
        self.assertTrue(calls)
        self.assertTrue(all(call["fill_up_missing"] is False for call in calls))


if __name__ == "__main__":
    unittest.main()
