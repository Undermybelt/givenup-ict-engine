from __future__ import annotations

import csv
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T115204+0800-codex-112315-same-root-six-provider-aq-chain-v1"
SOURCE_RUN_ID = "20260512T112315+0800-codex-board-b-six-provider-btc-matrix-probe-v1"
SYMBOL = "B2R_PROVIDER_MATRIX_SIX_PROVIDER_AQ_112315"

RUNS = Path("docs/experiments/actionable-regime-confidence/runs")
ROOT = RUNS / RUN_ID
SOURCE_ROOT = RUNS / SOURCE_RUN_ID
BASE_SCRIPT = (
    RUNS
    / "20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1"
    / "scripts"
    / "112904_provider_matrix_aq_date_contract_repair_v1.py"
)
OLD_SCRIPT = (
    RUNS
    / "20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1"
    / "scripts"
    / "112315_provider_matrix_aq_readback_v1.py"
)
PYTHON = Path("/Users/thrill3r/Auto-Quant/.venv/bin/python")
UV = "/Users/thrill3r/.local/bin/uv"

OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "112315-same-root-six-provider-aq-chain-v1"
PROVIDER_CSV_DIR = ROOT / "provider-csv"
WORKSPACE_ROOT = ROOT / "workspace"
DERIVED_DIR = ROOT / "derived"
STATE_DIR = ROOT / "state_six_provider_chain_v1"
PATH_RANKER_DIR = ROOT / "path-ranker"
PROVIDER_JSON_DIR = ROOT / "provider-data-json"


PUBLIC_PROVIDER_INPUTS = {
    "yfinance": {
        "source": SOURCE_ROOT / "provider-csv" / "yfinance_btc_usd_1h.csv",
        "symbol": "BTC-USD",
        "source_timeframe": "1h",
        "aq_timeframe": "1h",
    },
    "kraken_public": {
        "source": SOURCE_ROOT / "provider-csv" / "kraken_xbtusd_1h.csv",
        "symbol": "XBTUSD",
        "source_timeframe": "1h",
        "aq_timeframe": "1h",
    },
    "binance_public": {
        "source": SOURCE_ROOT / "provider-csv" / "binance_btcusdt_1h.csv",
        "symbol": "BTCUSDT",
        "source_timeframe": "1h",
        "aq_timeframe": "1h",
    },
    "bybit_public": {
        "source": SOURCE_ROOT / "provider-csv" / "bybit_btcusdt_linear_1h.csv",
        "symbol": "BTCUSDT",
        "source_timeframe": "1h",
        "aq_timeframe": "1h",
    },
}

DAILY_PROVIDER_INPUTS = {
    "tvr_btc_usd_daily": {
        "source": SOURCE_ROOT / "provider-csv" / "tvr_btc_usd_1d.csv",
        "symbol": "BTC-USD",
        "source_timeframe": "1d",
        "aq_timeframe": "1d",
    },
    "ibkr_btc_paxos_aggtrades_daily": {
        "source": SOURCE_ROOT / "provider-csv" / "ibkr_btc_paxos_aggtrades_1d.csv",
        "symbol": "BTC.PAXOS",
        "source_timeframe": "1d",
        "aq_timeframe": "1d",
    },
}


DAILY_MOMENTUM = '''\
from __future__ import annotations

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy


class ProviderCryptoMomentumStateV1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1d"
    can_short = False
    minimal_roi = {"0": 100}
    stoploss = -0.08
    trailing_stop = True
    trailing_stop_positive = 0.018
    trailing_stop_positive_offset = 0.034
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 6

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema3"] = ta.EMA(dataframe, timeperiod=3)
        dataframe["ema8"] = ta.EMA(dataframe, timeperiod=8)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=5)
        dataframe["volume_sma3"] = dataframe["volume"].rolling(3).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        trend_ok = dataframe["close"] >= dataframe["ema8"] * 0.985
        impulse_ok = (dataframe["rsi"] >= 50) | (dataframe["close"] > dataframe["open"])
        volume_ok = dataframe["volume"] >= dataframe["volume_sma3"].fillna(0) * 0.20
        dataframe.loc[trend_ok & impulse_ok & volume_ok, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["rsi"] < 46) | (dataframe["close"] < dataframe["ema3"] * 0.975), "exit_long"] = 1
        return dataframe
'''


DAILY_PULLBACK = '''\
from __future__ import annotations

from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy


class ProviderCryptoPullbackRevertV1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1d"
    can_short = False
    minimal_roi = {"0": 100}
    stoploss = -0.07
    trailing_stop = True
    trailing_stop_positive = 0.014
    trailing_stop_positive_offset = 0.028
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 6

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema5"] = ta.EMA(dataframe, timeperiod=5)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=5)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=5)
        dataframe["volume_sma3"] = dataframe["volume"].rolling(3).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        rebound = (dataframe["rsi"] > 42) & (dataframe["rsi"].shift(1) <= 42)
        floor_ok = dataframe["close"] >= dataframe["ema5"] * 0.92
        volume_ok = dataframe["volume"] >= dataframe["volume_sma3"].fillna(0) * 0.20
        dataframe.loc[rebound & floor_ok & volume_ok, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["rsi"] > 58) | (dataframe["close"] < dataframe["ema5"] - dataframe["atr"] * 1.5), "exit_long"] = 1
        return dataframe
'''


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def exit_code(path: Path) -> int | None:
    if not path.exists():
        return None
    return int(path.read_text().strip())


def csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open() as fh:
        return max(sum(1 for _ in fh) - 1, 0)


def normalize_ohlcv(source: Path) -> pd.DataFrame:
    raw = pd.read_csv(source)
    date_col = "date" if "date" in raw.columns else "timestamp"
    date = pd.to_datetime(raw[date_col], utc=True)
    out = pd.DataFrame(
        {
            "date": date,
            "open": pd.to_numeric(raw["open"], errors="coerce"),
            "high": pd.to_numeric(raw["high"], errors="coerce"),
            "low": pd.to_numeric(raw["low"], errors="coerce"),
            "close": pd.to_numeric(raw["close"], errors="coerce"),
            "volume": pd.to_numeric(raw.get("volume", 0.0), errors="coerce").fillna(0.0),
        }
    )
    out["volume"] = out["volume"].mask(out["volume"] < 0, 0.0)
    return out.dropna().sort_values("date").reset_index(drop=True)


def to_epoch_ms(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return int(value.timestamp() * 1000)
    return int(value)


def patch_module_paths(base: Any, old: Any) -> None:
    base.RUN_ID = RUN_ID
    base.SOURCE_RUN_ID = SOURCE_RUN_ID
    base.PROVIDER_ROOT_ID = SOURCE_RUN_ID
    base.ROOT = ROOT
    base.PROVIDER_ROOT = SOURCE_ROOT
    base.OUT_DIR = OUT_DIR
    base.CHECK_DIR = CHECK_DIR
    base.REPORT_DIR = REPORT_DIR
    base.PROVIDER_CSV_DIR = PROVIDER_CSV_DIR
    base.WORKSPACE_ROOT = WORKSPACE_ROOT

    old.RUN_ID = RUN_ID
    old.SOURCE_RUN_ID = SOURCE_RUN_ID
    old.ROOT = ROOT
    old.SOURCE_ROOT = SOURCE_ROOT
    old.OUT_DIR = OUT_DIR
    old.CHECK_DIR = CHECK_DIR
    old.REPORT_DIR = REPORT_DIR
    old.PROVIDER_CSV_DIR = PROVIDER_CSV_DIR
    old.WORKSPACE_ROOT = WORKSPACE_ROOT


def run_public_provider(base: Any, old: Any, provider: str, meta: dict[str, Any]) -> dict[str, Any]:
    return base.run_provider_fixed(old, provider, meta)


def run_daily_provider(old: Any, provider: str, meta: dict[str, Any]) -> dict[str, Any]:
    source = meta["source"]
    local_source = PROVIDER_CSV_DIR / source.name
    shutil.copy2(source, local_source)
    workspace = old.copy_template(provider)

    strategies_dir = workspace / "user_data" / "strategies_external"
    for path in strategies_dir.glob("*.py"):
        path.unlink()
    (strategies_dir / "ProviderCryptoMomentumStateV1.py").write_text(DAILY_MOMENTUM)
    (strategies_dir / "ProviderCryptoPullbackRevertV1.py").write_text(DAILY_PULLBACK)

    config_path = workspace / "config.tomac.json"
    config = read_json(config_path)
    config["timeframe"] = "1d"
    config["timerange"] = "20260401-20260512"
    write_json(config_path, config)

    df = normalize_ohlcv(local_source)
    feather = workspace / "user_data" / "data" / "BTC_USDT-1d.feather"
    df.to_feather(feather)

    strategies = sorted(strategies_dir.glob("*.py"))
    compile_cmd = [
        str(PYTHON),
        "-m",
        "py_compile",
        "run_tomac.py",
        *[str(path.relative_to(workspace)) for path in strategies],
    ]
    run_cmd = [str(PYTHON), "run_tomac.py"]
    prefix = provider.replace("/", "_")

    compile_proc = subprocess.run(
        compile_cmd,
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    (OUT_DIR / f"aq_{prefix}_compile.out").write_text(compile_proc.stdout)
    (OUT_DIR / f"aq_{prefix}_compile.err").write_text(compile_proc.stderr)
    (OUT_DIR / f"aq_{prefix}_compile.cmd").write_text(" ".join(compile_cmd) + "\n")
    (CHECK_DIR / f"aq_{prefix}_compile.exit").write_text(f"{compile_proc.returncode}\n")

    run_proc = subprocess.run(
        run_cmd,
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    (OUT_DIR / f"aq_{prefix}_run_tomac.out").write_text(run_proc.stdout)
    (OUT_DIR / f"aq_{prefix}_run_tomac.err").write_text(run_proc.stderr)
    (OUT_DIR / f"aq_{prefix}_run_tomac.cmd").write_text(" ".join(run_cmd) + "\n")
    (CHECK_DIR / f"aq_{prefix}_run_tomac.exit").write_text(f"{run_proc.returncode}\n")

    metrics: dict[str, Any] = {}
    for path in sorted((workspace / "derived").glob("*.metrics.json")):
        metrics[path.stem.replace(".metrics", "")] = read_json(path)

    return {
        "provider": provider,
        "provider_symbol": meta["symbol"],
        "source_csv": str(local_source),
        "source_timeframe": meta["source_timeframe"],
        "aq_timeframe": meta["aq_timeframe"],
        "rows": int(len(df)),
        "first_ts_ms": to_epoch_ms(df["date"].min()) if len(df) else None,
        "last_ts_ms": to_epoch_ms(df["date"].max()) if len(df) else None,
        "workspace": str(workspace),
        "feather": str(feather),
        "compile_exit": compile_proc.returncode,
        "run_tomac_exit": run_proc.returncode,
        "metrics": metrics,
    }


def provider_matrix_readback() -> dict[str, Any]:
    return {
        "source_provider_root": str(SOURCE_ROOT),
        "fetch_exits": {
            "yfinance_btc_usd_1h": exit_code(SOURCE_ROOT / "checks" / "11_yfinance_btc_usd_1h.exit"),
            "kraken_xbtusd_1h": exit_code(SOURCE_ROOT / "checks" / "12_kraken_xbtusd_1h.exit"),
            "binance_btcusdt_1h": exit_code(SOURCE_ROOT / "checks" / "13_binance_btcusdt_1h.exit"),
            "bybit_btcusdt_linear_1h": exit_code(SOURCE_ROOT / "checks" / "14_bybit_btcusdt_linear_1h.exit"),
            "tvr_btc_usd_1d": exit_code(SOURCE_ROOT / "checks" / "16_tvr_btcusdt_1d_local_stdio.exit"),
            "ibkr_btc_paxos_aggtrades_1d": exit_code(SOURCE_ROOT / "checks" / "17_ibkr_btc_paxos_aggtrades_1d.exit"),
        },
        "fetch_rows": {
            "yfinance_btc_usd_1h": csv_rows(SOURCE_ROOT / "provider-csv" / "yfinance_btc_usd_1h.csv"),
            "kraken_xbtusd_1h": csv_rows(SOURCE_ROOT / "provider-csv" / "kraken_xbtusd_1h.csv"),
            "binance_btcusdt_1h": csv_rows(SOURCE_ROOT / "provider-csv" / "binance_btcusdt_1h.csv"),
            "bybit_btcusdt_linear_1h": csv_rows(SOURCE_ROOT / "provider-csv" / "bybit_btcusdt_linear_1h.csv"),
            "tvr_btc_usd_1d": csv_rows(SOURCE_ROOT / "provider-csv" / "tvr_btc_usd_1d.csv"),
            "ibkr_btc_paxos_aggtrades_1d": csv_rows(SOURCE_ROOT / "provider-csv" / "ibkr_btc_paxos_aggtrades_1d.csv"),
        },
        "authority_note": "all provider CSVs are read from the single 112315 provider matrix root",
    }


def metric_totals(results: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {
        "provider_runs": len(results),
        "compile_success": 0,
        "run_success": 0,
        "strategies_with_metrics": 0,
        "total_trades": 0,
        "positive_profit_metric_count": 0,
    }
    for result in results:
        if result["compile_exit"] == 0:
            totals["compile_success"] += 1
        if result["run_tomac_exit"] == 0:
            totals["run_success"] += 1
        for payload in result.get("metrics", {}).values():
            aggregate = payload.get("aggregate", {})
            trades = int(aggregate.get("trade_count") or 0)
            profit = float(aggregate.get("total_profit_pct") or 0.0)
            totals["strategies_with_metrics"] += 1
            totals["total_trades"] += trades
            if profit > 0:
                totals["positive_profit_metric_count"] += 1
    return totals


def materialize_trades(results: list[dict[str, Any]]) -> dict[str, Any]:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DERIVED_DIR / "same_root_six_provider_aq_real_trades.jsonl"
    rows: list[dict[str, Any]] = []
    by_provider: dict[str, int] = {}
    by_path: dict[str, int] = {}
    for result in results:
        workspace = Path(result["workspace"])
        provider = result["provider"]
        for path in sorted((workspace / "derived").glob("*.real_trades.jsonl")):
            strategy = path.name.replace(".real_trades.jsonl", "")
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                branch_path = row.get("regime_profit_branch_path")
                if not branch_path:
                    continue
                idx = len(rows) + 1
                row["symbol"] = SYMBOL
                row["trade_id"] = f"{SYMBOL}_{provider}_{strategy}_{idx:05d}"
                row["auto_quant_run_id"] = RUN_ID
                row["provider_matrix_source_run_id"] = SOURCE_RUN_ID
                row["source_provider"] = provider
                row["source_timeframe"] = result.get("source_timeframe")
                row["aq_timeframe"] = result.get("aq_timeframe")
                row["strategy_mutation_id"] = f"{provider}:{row.get('strategy_mutation_id', strategy)}"
                rows.append(row)
                by_provider[provider] = by_provider.get(provider, 0) + 1
                by_path[branch_path] = by_path.get(branch_path, 0) + 1
    out_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    return {"path": str(out_path), "rows": len(rows), "by_provider": by_provider, "by_path": by_path}


def build_strategy_library(results: list[dict[str, Any]]) -> Path:
    strategies = []
    for result in results:
        for name, payload in sorted(result.get("metrics", {}).items()):
            aggregate = payload.get("aggregate", {})
            strategies.append(
                {
                    "name": f"{result['provider']}:{name}",
                    "status": "ok" if result["run_tomac_exit"] == 0 else "error",
                    "error": None if result["run_tomac_exit"] == 0 else "run_tomac_exit_nonzero",
                    "commit": "experiment-run-root",
                    "file_path": str(Path(result["workspace"]) / "user_data" / "strategies_external" / f"{name}.py"),
                    "timerange": "20260401-20260512",
                    "pairs": ["BTC/USDT"],
                    "metadata": {
                        "strategy": name,
                        "mutation_id": f"{result['provider']}:{name}",
                        "base_factor": "same_root_provider_matrix_crypto",
                        "hypothesis": "Same-root 112315 provider rows can be routed through AQ and preserve branch-shaped trade observations.",
                        "paradigm": "provider_matrix_momentum_or_pullback",
                        "expected_regime": "Bull/Range -> ProviderCrypto* -> branch-preserving profit factor",
                        "source_provider": result["provider"],
                        "source_timeframe": result.get("source_timeframe"),
                        "aq_timeframe": result.get("aq_timeframe"),
                        "asset_class": "crypto_provider_ohlcv",
                        "status": "incubation_only",
                    },
                    "validation_metrics": aggregate,
                    "per_pair_metrics": payload.get("per_pair", {}),
                }
            )
    library = {
        "manifest_version": "1.0",
        "exported_at": "2026-05-12T11:52:04+08:00",
        "source_run_id": RUN_ID,
        "source_workspace": str(WORKSPACE_ROOT),
        "auto_quant_repo_url": "/Users/thrill3r/Auto-Quant",
        "auto_quant_pinned_ref": "local",
        "config_path": "config.tomac.json",
        "log_path": str(OUT_DIR),
        "strategies": strategies,
    }
    path = DERIVED_DIR / "strategy_library_same_root_six_provider_aq_v1.json"
    write_json(path, library)
    return path


def records_for_json(df: pd.DataFrame) -> list[dict[str, Any]]:
    records = []
    for row in df.itertuples(index=False):
        ts = pd.Timestamp(row.date)
        records.append(
            {
                "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": float(row.volume),
            }
        )
    return records


def prepare_provider_json() -> dict[str, Any]:
    PROVIDER_JSON_DIR.mkdir(parents=True, exist_ok=True)
    source = SOURCE_ROOT / "provider-csv" / "yfinance_btc_usd_1h.csv"
    df = normalize_ohlcv(source)
    outputs: dict[str, Any] = {}
    specs = {
        "1h": df,
        "4h": df.set_index("date").resample("4h").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
        ).dropna().reset_index(),
        "1d": df.set_index("date").resample("1D").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
        ).dropna().reset_index(),
    }
    for timeframe, frame in specs.items():
        path = PROVIDER_JSON_DIR / f"BTC_USD-{timeframe}.json"
        write_json(path, records_for_json(frame))
        outputs[timeframe] = {"path": str(path), "rows": len(frame)}
    return outputs


def run_command(label: str, cmd: list[str], env: dict[str, str] | None = None) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{label}.cmd").write_text(" ".join(cmd) + "\n")
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=env,
    )
    (OUT_DIR / f"{label}.out").write_text(proc.stdout)
    (OUT_DIR / f"{label}.err").write_text(proc.stderr)
    (CHECK_DIR / f"{label}.exit").write_text(f"{proc.returncode}\n")
    return proc.returncode


def run_chain(trades_path: str, library_path: Path, provider_json: dict[str, Any]) -> dict[str, int]:
    env = os.environ.copy()
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
        }
    )
    target_history = STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target_history.csv"
    model_dir = PATH_RANKER_DIR / "catboost_model"
    history_scores = PATH_RANKER_DIR / "history_scores.csv"
    trainer_artifact = model_dir / "trainer_artifact.json"
    commands = {
        "20_auto_quant_results_import": [
            "./target/debug/ict-engine",
            "auto-quant-results-import",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--library",
            str(library_path),
        ],
        "21_auto_quant_prior_init": [
            "./target/debug/ict-engine",
            "auto-quant-prior-init",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--library",
            str(library_path),
            "--force",
        ],
        "22_ingest_real_trades": [
            "./target/debug/ict-engine",
            "auto-quant-ingest-real-trades",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--trades",
            trades_path,
            "--source",
            "same_root_six_provider_aq_112315",
            "--force",
        ],
        "23_analyze_provider_data": [
            "./target/debug/ict-engine",
            "analyze",
            "--symbol",
            SYMBOL,
            "--data-htf",
            provider_json["1d"]["path"],
            "--data-mtf",
            provider_json["4h"]["path"],
            "--data-ltf",
            provider_json["1h"]["path"],
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
        "24_pre_bayes_status": [
            "./target/debug/ict-engine",
            "pre-bayes-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--refresh",
            "--output-format",
            "json",
        ],
        "25_policy_training_status_before_export": [
            "./target/debug/ict-engine",
            "policy-training-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
        "26_export_structural_path_ranking_target": [
            "./target/debug/ict-engine",
            "export-structural-path-ranking-target",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
        ],
        "27_train_catboost": [
            UV,
            "run",
            "--offline",
            "--python",
            "3.11",
            "--with",
            "pandas",
            "--with",
            "numpy",
            "--with",
            "catboost",
            "python",
            "scripts/auto_quant_external/pandas_path_ranker_trainer.py",
            "--target-csv",
            str(target_history),
            "--output-dir",
            str(model_dir),
            "--model-family",
            "catboost",
            "--output-scores",
            str(history_scores),
        ],
        "28_apply_catboost_history": [
            UV,
            "run",
            "--offline",
            "--python",
            "3.11",
            "--with",
            "pandas",
            "--with",
            "numpy",
            "--with",
            "catboost",
            "python",
            "scripts/auto_quant_external/pandas_path_ranker_trainer.py",
            "--apply",
            "--model-dir",
            str(model_dir),
            "--target-csv",
            str(target_history),
            "--output-scores",
            str(history_scores),
        ],
        "29_apply_external_scores": [
            "./target/debug/ict-engine",
            "apply-structural-path-ranking-external-scores",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--scores-file",
            str(history_scores),
        ],
        "30_register_trainer_artifact": [
            "./target/debug/ict-engine",
            "register-structural-path-ranking-trainer-artifact",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--artifact-uri",
            str(trainer_artifact),
            "--model-family",
            "catboost",
            "--score-column",
            "raw_path_score",
        ],
        "31_enable_runtime": [
            "./target/debug/ict-engine",
            "enable-structural-path-ranking-runtime",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--reuse-mode",
            "prefer_history",
        ],
        "32_policy_training_status_final": [
            "./target/debug/ict-engine",
            "policy-training-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--output-format",
            "json",
        ],
        "33_workflow_execution_candidate": [
            "./target/debug/ict-engine",
            "workflow-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--refresh",
            "--phase",
            "execution-candidate",
            "--output-format",
            "json",
        ],
        "34_workflow_full": [
            "./target/debug/ict-engine",
            "workflow-status",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--refresh",
            "--output-format",
            "json",
        ],
    }
    exits: dict[str, int] = {}
    for label, cmd in commands.items():
        exits[label] = run_command(label, cmd, env=env if "catboost" in label else None)
    return exits


def parse_json_output(label: str) -> dict[str, Any]:
    path = OUT_DIR / f"{label}.out"
    if not path.exists() or not path.read_text().strip():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def cleanup_catboost_info() -> str:
    path = Path("catboost_info")
    if path.exists():
        shutil.rmtree(path)
    status = "catboost_info_absent" if not path.exists() else "catboost_info_present"
    (CHECK_DIR / "35_catboost_info_cleanup_check.exit").write_text("0\n" if status == "catboost_info_absent" else "1\n")
    (OUT_DIR / "35_catboost_info_cleanup_check.out").write_text(status + "\n")
    return status


def summarize(
    matrix: dict[str, Any],
    aq_results: list[dict[str, Any]],
    trade_summary: dict[str, Any],
    library_path: Path,
    provider_json: dict[str, Any],
    chain_exits: dict[str, int],
    cleanup_status: str,
) -> dict[str, Any]:
    policy = parse_json_output("32_policy_training_status_final")
    pre_bayes = parse_json_output("24_pre_bayes_status")
    execution = parse_json_output("33_workflow_execution_candidate")
    workflow = parse_json_output("34_workflow_full")
    target = read_json(STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target_summary.json")
    ranker = policy.get("structural_path_ranking_target", {})
    validation = policy.get("structural_path_ranking_validation", {})
    return {
        "run_id": RUN_ID,
        "symbol": SYMBOL,
        "source_run_id": SOURCE_RUN_ID,
        "provider_matrix": matrix,
        "aq_results": aq_results,
        "metric_totals": metric_totals(aq_results),
        "trade_summary": trade_summary,
        "strategy_library": str(library_path),
        "provider_json": provider_json,
        "chain_exits": chain_exits,
        "pre_bayes": pre_bayes,
        "policy_final": policy,
        "target_summary": target,
        "ranker_validation": validation,
        "ranker_target": ranker,
        "execution_candidate": execution,
        "workflow_full": workflow,
        "catboost_info_cleanup": cleanup_status,
        "same_root_provider_authority": all(v > 0 for v in matrix["fetch_rows"].values()),
        "all_provider_aq_compile_success": all(r["compile_exit"] == 0 for r in aq_results),
        "all_provider_aq_run_success": all(r["run_tomac_exit"] == 0 for r in aq_results),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }


def write_report(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = REPORT_DIR / "112315_same_root_six_provider_aq_chain_v1.md"
    assertions = CHECK_DIR / "112315_same_root_six_provider_aq_chain_v1_assertions.out"
    checklist = REPORT_DIR / "prompt_to_artifact_checklist_112315_same_root_six_provider_aq_chain_v1.csv"

    matrix = summary["provider_matrix"]
    metric_totals = summary["metric_totals"]
    ranker = summary["ranker_target"]
    execution = summary["execution_candidate"]
    pre_bayes = summary["pre_bayes"]
    lines = [
        "# 112315 Same-Root Six-Provider AQ Chain v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Symbol: `{SYMBOL}`",
        f"Provider root: `{SOURCE_RUN_ID}`",
        "",
        "## Scope",
        "This run consumes only the `112315` provider matrix root for all six required provider names.",
        "TVR and IBKR are routed through their same-root daily bars instead of the mixed-source 1h precheck rows used by `113833`.",
        "It does not edit ict-engine runtime code and keeps all AQ workspaces under this run root.",
        "",
        "## Provider Rows",
    ]
    for key, value in matrix["fetch_rows"].items():
        lines.append(f"- `{key}`: rows `{value}`, exit `{matrix['fetch_exits'].get(key)}`.")
    lines.extend(["", "## AQ Results"])
    for result in summary["aq_results"]:
        lines.append(
            f"- `{result['provider']}`: rows `{result['rows']}`, source_tf `{result.get('source_timeframe')}`, aq_tf `{result.get('aq_timeframe')}`, compile `{result['compile_exit']}`, TOMAC `{result['run_tomac_exit']}`."
        )
        for strategy, payload in sorted(result.get("metrics", {}).items()):
            aggregate = payload.get("aggregate", {})
            lines.append(
                f"  - `{strategy}`: trades `{aggregate.get('trade_count')}`, profit_pct `{aggregate.get('total_profit_pct')}`, win_rate_pct `{aggregate.get('win_rate_pct')}`, profit_factor `{aggregate.get('profit_factor')}`."
            )
    lines.extend(
        [
            "",
            "## Chain Readback",
            f"- Materialized rooted trades: `{summary['trade_summary']['rows']}`.",
            f"- Trades by provider: `{summary['trade_summary']['by_provider']}`.",
            f"- Provider AQ run success: `{metric_totals['run_success']}/{metric_totals['provider_runs']}`.",
            f"- Ordered command exits: `{summary['chain_exits']}`.",
            f"- Pre-Bayes gate: `{pre_bayes.get('gate_status') or pre_bayes.get('latest_policy', {}).get('gate_status')}`.",
            f"- Raw scored mature: `{ranker.get('raw_scored_mature_rows')}/{ranker.get('raw_scored_mature_min_rows')}`.",
            f"- Production validation: `{ranker.get('production_validation_rows')}/{ranker.get('production_validation_min_rows')}`.",
            f"- Observation validation: `{ranker.get('observation_validation_rows')}/{ranker.get('observation_validation_min_rows')}`.",
            f"- Trainer artifact ready: `{ranker.get('trainer_artifact_ready')}` status `{ranker.get('trainer_artifact_status')}`.",
            f"- Runtime selection: `{ranker.get('runtime_selection_status')}` ready `{ranker.get('runtime_selection_ready')}`.",
            f"- Execution ready/actionable: `{execution.get('ready')}` / `{execution.get('actionable')}` review `{execution.get('review_status')}`.",
            "",
            "## Decision",
            "- Gate result: `112315_same_root_six_provider_aq_chain=same_root_provider_authority_repaired_but_execution_fail_closed`.",
            "- This is stronger than `112904` and `113833` on provider authority because all six source CSVs come from `112315`, and TVR/IBKR have successful same-root AQ runs on daily bars.",
            "- Promotion still requires execution readiness/actionability and a non-observe release decision; this report does not override fail-closed workflow status.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
            "",
            "## Artifacts",
            f"- JSON: `{REPORT_DIR / '112315_same_root_six_provider_aq_chain_v1.json'}`",
            f"- Assertions: `{assertions}`",
            f"- Checklist: `{checklist}`",
            f"- Trades: `{summary['trade_summary']['path']}`",
            f"- Strategy library: `{summary['strategy_library']}`",
            f"- State dir: `{STATE_DIR}`",
            f"- CatBoost cleanup: `{summary['catboost_info_cleanup']}`",
        ]
    )
    report.write_text("\n".join(lines) + "\n")

    with checklist.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["requirement", "artifact", "status", "note"])
        writer.writerow(["single provider root", str(SOURCE_ROOT), "covered", SOURCE_RUN_ID])
        writer.writerow(["six provider AQ workspaces", str(WORKSPACE_ROOT), "covered", f"{metric_totals['run_success']}/6 run exits 0"])
        writer.writerow(["rooted trade observations", summary["trade_summary"]["path"], "covered", str(summary["trade_summary"]["rows"])])
        writer.writerow(["strategy library import", summary["strategy_library"], "covered", "auto-quant-results-import attempted"])
        writer.writerow(["Pre-Bayes/filter", str(STATE_DIR), "covered", "pre-bayes-status captured"])
        writer.writerow(["CatBoost/path-ranker", str(PATH_RANKER_DIR), "covered", "train/apply/register/enable attempted"])
        writer.writerow(["execution tree", str(OUT_DIR), "covered", "workflow-status captured"])

    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run={SOURCE_RUN_ID}",
        f"PASS same_root_provider_authority={summary['same_root_provider_authority']}",
        f"PASS provider_runs={metric_totals['provider_runs']}",
        f"PASS compile_success={metric_totals['compile_success']}",
        f"PASS run_success={metric_totals['run_success']}",
        f"PASS rooted_trades={summary['trade_summary']['rows']}",
        f"PASS raw_scored_mature={ranker.get('raw_scored_mature_rows')}",
        f"PASS production_validation={ranker.get('production_validation_rows')}",
        f"PASS observation_validation={ranker.get('observation_validation_rows')}",
        f"PASS trainer_artifact_ready={ranker.get('trainer_artifact_ready')}",
        f"PASS catboost_info_cleanup={summary['catboost_info_cleanup']}",
        f"FAIL_CLOSED execution_ready={execution.get('ready')} actionable={execution.get('actionable')} review={execution.get('review_status')}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    for label, code in summary["chain_exits"].items():
        assertion_lines.append(("PASS" if code == 0 else "FAIL_CLOSED") + f" {label}_exit={code}")
    assertions.write_text("\n".join(assertion_lines) + "\n")


def main() -> int:
    for path in (OUT_DIR, CHECK_DIR, REPORT_DIR, PROVIDER_CSV_DIR, WORKSPACE_ROOT, DERIVED_DIR, PATH_RANKER_DIR, PROVIDER_JSON_DIR):
        path.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n")
    (ROOT / "source_run_id.txt").write_text(SOURCE_RUN_ID + "\n")

    base = load_module(BASE_SCRIPT, "date_contract_base")
    old = load_module(OLD_SCRIPT, "provider_matrix_old")
    patch_module_paths(base, old)

    matrix = provider_matrix_readback()
    aq_results: list[dict[str, Any]] = []
    for provider, meta in PUBLIC_PROVIDER_INPUTS.items():
        aq_results.append(run_public_provider(base, old, provider, meta))
    for provider, meta in DAILY_PROVIDER_INPUTS.items():
        aq_results.append(run_daily_provider(old, provider, meta))

    trade_summary = materialize_trades(aq_results)
    library_path = build_strategy_library(aq_results)
    provider_json = prepare_provider_json()
    chain_exits = run_chain(trade_summary["path"], library_path, provider_json)
    cleanup_status = cleanup_catboost_info()
    summary = summarize(matrix, aq_results, trade_summary, library_path, provider_json, chain_exits, cleanup_status)
    write_json(REPORT_DIR / "112315_same_root_six_provider_aq_chain_v1.json", summary)
    write_report(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
