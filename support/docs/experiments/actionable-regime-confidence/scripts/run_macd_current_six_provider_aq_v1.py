#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SCRIPT = Path(__file__).resolve()
BASE = SCRIPT.parents[1]
RUN_STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
ROOT = BASE / "runs" / f"{RUN_STAMP}-codex-macd-current-six-provider-aq-v1"
REPO = BASE.parents[2]
PY = Path("/Users/thrill3r/.venvs/ict-engine-provider-py313/bin/python")
if not PY.exists():
    PY = Path("python3")
FETCH = REPO / "scripts/auto_quant_external/fetch_external.py"
ICT = REPO / "target/debug/ict-engine"


@dataclass(frozen=True)
class ProviderSpec:
    provider: str
    label: str
    symbol: str
    timeframe: str
    out_name: str
    command: list[str] | None
    request_json: dict | None = None


PROVIDERS = [
    ProviderSpec(
        "yfinance/YF",
        "yfinance/YF SPY 1h",
        "SPY",
        "1h",
        "yf_spy_1h.csv",
        [str(PY), str(FETCH), "yahoo", "--symbol", "SPY", "--interval", "1h", "--start", "2025-01-01", "--end", "2026-05-12"],
    ),
    ProviderSpec(
        "IBKR",
        "IBKR SPY 1h",
        "SPY",
        "1h",
        "ibkr_spy_1h.csv",
        [
            str(PY),
            str(FETCH),
            "ibkr-historical",
            "--symbol",
            "SPY",
            "--sec-type",
            "STK",
            "--exchange",
            "SMART",
            "--currency",
            "USD",
            "--primary-exchange",
            "ARCA",
            "--bar-size",
            "1 hour",
            "--duration",
            "6 M",
            "--what-to-show",
            "TRADES",
            "--host",
            "127.0.0.1",
            "--port",
            "4002",
            "--client-id",
            "166",
        ],
    ),
    ProviderSpec(
        "Binance",
        "Binance BTCUSDT 1h",
        "BTC",
        "1h",
        "binance_btcusdt_1h.csv",
        [str(PY), str(FETCH), "binance-kline", "--symbol", "BTCUSDT", "--interval", "1h", "--start", "2025-01-01", "--end", "2026-05-12"],
    ),
    ProviderSpec(
        "Bybit",
        "Bybit BTCUSDT 1h",
        "BTC",
        "1h",
        "bybit_btcusdt_1h.csv",
        [str(PY), str(FETCH), "bybit-kline", "--category", "linear", "--symbol", "BTCUSDT", "--interval", "1h", "--start", "2025-01-01", "--end", "2026-05-12"],
    ),
    ProviderSpec(
        "Kraken",
        "Kraken XBTUSD 1h",
        "BTC",
        "1h",
        "kraken_xbtusd_1h.csv",
        [str(PY), str(FETCH), "kraken-kline", "--market", "spot", "--pair", "XBTUSD", "--interval", "1h", "--start", "2026-03-01", "--end", "2026-05-12"],
    ),
    ProviderSpec(
        "TradingViewRemix/TVR",
        "TradingViewRemix/TVR QQQ 1h",
        "QQQ",
        "1h",
        "tvr_qqq_1h.csv",
        None,
        {
            "market_key": "board-a-macd-current-tvr-QQQ-1h",
            "interval": "1h",
            "count": 1200,
            "related_roles": ["etf_reference"],
            "provider_preferences": {"etf_reference": "tradingview_mcp"},
            "symbol_overrides": {"etf_reference": {"display_symbol": "NASDAQ:QQQ", "tradingview_mcp": "NASDAQ:QQQ"}},
        },
    ),
]


BRANCHES = [
    {
        "id": "macd_zero_line_reclaim_long_v1",
        "class": "MacdZeroLineReclaimLongV1",
        "direction": "long",
        "path": "TrendExpansion -> MomentumPersistence -> macd_zero_line_reclaim -> macd_zero_line_reclaim_long_v1",
        "roi": "100",
        "stoploss": "-0.040",
    },
    {
        "id": "macd_signal_pullback_continuation_v1",
        "class": "MacdSignalPullbackContinuationV1",
        "direction": "long",
        "path": "TrendExpansion -> MomentumPersistence -> macd_signal_pullback -> macd_signal_pullback_continuation_v1",
        "roi": "100",
        "stoploss": "-0.045",
    },
]


def run_cmd(name: str, argv: list[str], timeout: int = 180, extra_env: dict[str, str] | None = None) -> dict:
    command_dir = ROOT / "command-output"
    checks_dir = ROOT / "checks"
    command_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)
    (command_dir / f"{name}.cmd").write_text(" ".join(argv) + "\n", encoding="utf-8")
    try:
        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
        proc = subprocess.run(argv, cwd=REPO, text=True, capture_output=True, timeout=timeout, env=env)
        timed_out = False
        rc = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        rc = 124
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n"
    (command_dir / f"{name}.out").write_text(stdout, encoding="utf-8")
    (command_dir / f"{name}.err").write_text(stderr, encoding="utf-8")
    (checks_dir / f"{name}.exit").write_text(f"{rc}\n", encoding="utf-8")
    return {"name": name, "argv": argv, "exit": rc, "timed_out": timed_out}


def row_count(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def normalize_provider_csv(source: Path, destination: Path) -> int:
    """Write dispatch-compatible OHLCV with a timestamp header."""
    if not source.exists() or source.stat().st_size == 0:
        return 0
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        time_key = next((key for key in ("timestamp", "time", "datetime", "ts_event", "date", "ts") if key in headers), None)
        if not time_key:
            return 0
        required = ["open", "high", "low", "close", "volume"]
        if any(key not in headers for key in required):
            return 0
        rows = []
        for row in reader:
            rows.append(
                {
                    "timestamp": row.get(time_key, ""),
                    "open": row.get("open", ""),
                    "high": row.get("high", ""),
                    "low": row.get("low", ""),
                    "close": row.get("close", ""),
                    "volume": row.get("volume", ""),
                }
            )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def write_tvr_request_and_fetch(spec: ProviderSpec, out_path: Path) -> dict:
    request_path = ROOT / "requests/tvr_qqq_1h.json"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(json.dumps(spec.request_json, indent=2) + "\n", encoding="utf-8")
    env = {
        "HOME": "/tmp/ict-engine-tv-stdio-home",
        "ICT_ENGINE_TRADINGVIEW_MCP_CMD": "uv",
        "ICT_ENGINE_TRADINGVIEW_MCP_ARGS": "--directory /Users/thrill3r/tradingview-mcp/tradingview-mcp run tradingview-mcp",
    }
    result = run_cmd(
        "06_tvr_local_stdio_qqq_1h",
        [str(ICT), "market-data-harness", "--action", "fetch", "--request-json", str(request_path)],
        timeout=180,
        extra_env=env,
    )
    out_json = ROOT / "command-output/06_tvr_local_stdio_qqq_1h.out"
    rows = []
    try:
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        for item in payload.get("results", []):
            if item.get("ok") and item.get("provider") == "tradingview_mcp":
                for candle in item.get("data", []):
                    rows.append(
                        {
                            "timestamp": candle.get("timestamp"),
                            "open": candle.get("open"),
                            "high": candle.get("high"),
                            "low": candle.get("low"),
                            "close": candle.get("close"),
                            "volume": candle.get("volume"),
                        }
                    )
    except Exception as exc:  # noqa: BLE001
        (ROOT / "command-output/06_tvr_parse.err").write_text(repr(exc) + "\n", encoding="utf-8")
    if rows:
        with out_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
            writer.writeheader()
            writer.writerows(rows)
    return result


def strategy_source(branch: dict) -> str:
    if branch["class"] == "MacdZeroLineReclaimLongV1":
        return '''from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class MacdZeroLineReclaimLongV1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 100}
    stoploss = -0.040
    trailing_stop = True
    trailing_stop_positive = 0.010
    trailing_stop_positive_offset = 0.022
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 240

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema34"] = ta.EMA(dataframe, timeperiod=34)
        dataframe["ema89"] = ta.EMA(dataframe, timeperiod=89)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        trend = (dataframe["close"] > dataframe["ema34"]) & (dataframe["ema34"] > dataframe["ema89"])
        zero_reclaim = (dataframe["macd"] > 0) & (dataframe["macd"].shift(1) <= 0)
        momentum_ok = dataframe["rsi"].between(44, 72) & (dataframe["macdhist"] > dataframe["macdhist"].shift(1))
        dataframe.loc[trend & zero_reclaim & momentum_ok, ["enter_long", "enter_tag"]] = (1, "macd_zero_line_reclaim_long_v1")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        exit_signal = (dataframe["macd"] < dataframe["macdsignal"]) | (dataframe["close"] < dataframe["ema34"]) | (dataframe["rsi"] > 78)
        dataframe.loc[exit_signal, "exit_long"] = 1
        return dataframe
'''
    return '''from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class MacdSignalPullbackContinuationV1(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "1h"
    can_short = False
    minimal_roi = {"0": 100}
    stoploss = -0.045
    trailing_stop = True
    trailing_stop_positive = 0.012
    trailing_stop_positive_offset = 0.026
    trailing_only_offset_is_reached = True
    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 240

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema55"] = ta.EMA(dataframe, timeperiod=55)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        trend = (dataframe["close"] > dataframe["ema55"]) & (dataframe["ema21"] > dataframe["ema55"])
        signal_reclaim = (dataframe["macd"] > dataframe["macdsignal"]) & (dataframe["macd"].shift(1) <= dataframe["macdsignal"].shift(1))
        pullback_zone = (dataframe["macd"] > 0) & dataframe["rsi"].between(40, 68)
        dataframe.loc[trend & signal_reclaim & pullback_zone, ["enter_long", "enter_tag"]] = (1, "macd_signal_pullback_continuation_v1")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        exit_signal = (dataframe["macd"] < 0) | (dataframe["close"] < dataframe["ema55"]) | (dataframe["rsi"] > 80)
        dataframe.loc[exit_signal, "exit_long"] = 1
        return dataframe
'''


def provider_slug(provider: str) -> str:
    return provider.lower().replace("/", "-").replace(" ", "-")


def main() -> int:
    for sub in ("data/provider/raw", "data/provider/normalized", "agent-material", "summaries", "checks", "command-output", "requests", "state", "scripts"):
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCRIPT, ROOT / "scripts" / SCRIPT.name)

    provider_rows = []
    command_results = []
    for index, spec in enumerate(PROVIDERS, start=1):
        raw_path = ROOT / "data/provider/raw" / spec.out_name
        normalized_path = ROOT / "data/provider/normalized" / spec.out_name
        if spec.command is None:
            result = write_tvr_request_and_fetch(spec, raw_path)
        else:
            argv = [*spec.command, "--output", str(raw_path)]
            result = run_cmd(f"{index:02d}_{provider_slug(spec.provider)}_fetch", argv, timeout=240)
        command_results.append(result)
        rows = normalize_provider_csv(raw_path, normalized_path)
        provider_rows.append(
            {
                "provider": spec.provider,
                "provider_label": spec.label,
                "symbol": spec.symbol,
                "timeframe": spec.timeframe,
                "path": str(normalized_path) if rows else "",
                "raw_path": str(raw_path) if row_count(raw_path) else "",
                "rows": rows,
                "aq_provider_invoked": "true",
                "provider_requested": "true",
                "provider_unreachable": "false" if result["exit"] == 0 and rows else "true",
                "provider_data_acquired": "true" if result["exit"] == 0 and rows else "false",
                "local_cache_replay": "false",
                "exit": result["exit"],
            }
        )

    with (ROOT / "summaries/provider_provenance_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(provider_rows[0].keys()))
        writer.writeheader()
        writer.writerows(provider_rows)

    acquired = [row for row in provider_rows if row["provider_data_acquired"] == "true"]
    material_rows = []
    material_paths = []
    for branch in BRANCHES:
        strategy_path = ROOT / "agent-material" / f"{branch['class']}.py"
        strategy_path.write_text(strategy_source(branch), encoding="utf-8")
        parts = [part.strip() for part in branch["path"].split(" -> ")]
        for row in acquired:
            package_id = f"hdr-{branch['id']}-{provider_slug(row['provider'])}-1h-v1"
            material_path = ROOT / "agent-material" / f"{package_id}.material.json"
            material = {
                "package_id": package_id,
                "title": f"HDR {branch['id']} - {row['provider_label']}",
                "symbol": row["symbol"],
                "timeframe": row["timeframe"],
                "timerange": "20250101-20260512",
                "direction": branch["direction"],
                "data_path": row["path"],
                "strategy_source_path": str(strategy_path),
                "strategy_class_name": branch["class"],
                    "strategy_brief": "MACD momentum current-provider AQ probe; diagnostic only, not promotion.",
                "evaluation_priority": ["provider_trade_density", "cross_provider_survival", "regime_conditioned_win_rate"],
                "consumer_evidence_profile": {
                    "branch_path": branch["path"],
                    "regime_profit_branch_path": branch["path"],
                    "branch_id": branch["id"],
                    "main_regime": parts[0],
                    "sub_regime": parts[1],
                    "sub_sub_regime_or_profit_factor": parts[2],
                    "profit_factor": parts[3],
                    "provider": row["provider"],
                    "promotion_allowed": False,
                    "trade_usable": False,
                    "update_goal": False,
                },
                "notes": [
                    f"source_provider={row['provider_label']}",
                    f"branch_path={branch['path']}",
                    "aq_provider_invoked=true",
                    "provider_data_acquired_this_step=true",
                    "local_cache_replay=false",
                    "macd_current_provider_probe=true",
                    "promotion_allowed=false until ordered downstream chain passes calibrated >=95 gates",
                ],
            }
            material_path.write_text(json.dumps(material, indent=2) + "\n", encoding="utf-8")
            material_paths.append(str(material_path))
            material_rows.append(
                {
                    "provider": row["provider"],
                    "provider_label": row["provider_label"],
                    "branch_id": branch["id"],
                    "branch_path": branch["path"],
                    "material_path": str(material_path),
                    "strategy_path": str(strategy_path),
                    "rows": row["rows"],
                }
            )

    if material_rows:
        with (ROOT / "summaries/material_paths.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(material_rows[0].keys()))
            writer.writeheader()
            writer.writerows(material_rows)

    py_compile = run_cmd("07_strategy_py_compile", [str(PY), "-m", "py_compile", *[str(ROOT / "agent-material" / f"{b['class']}.py") for b in BRANCHES]], timeout=60)
    batch = dispatch = rank = None
    if material_paths and py_compile["exit"] == 0:
        batch = run_cmd(
            "08_auto_quant_agent_material_batch",
            [str(ICT), "auto-quant-agent-material-batch", "--symbol", "MACD_CURRENT_2155", "--state-dir", str(ROOT / "state"), "--max-parallel", "2", *sum([["--material", p] for p in material_paths], [])],
            timeout=900,
        )
        if batch["exit"] == 0:
            dispatch = run_cmd("09_auto_quant_agent_material_dispatch", [str(ICT), "auto-quant-agent-material-dispatch", "--symbol", "MACD_CURRENT_2155", "--state-dir", str(ROOT / "state")], timeout=900)
        if dispatch and dispatch["exit"] == 0:
            rank = run_cmd("10_auto_quant_agent_material_rank", [str(ICT), "auto-quant-agent-material-rank", "--symbol", "MACD_CURRENT_2155", "--state-dir", str(ROOT / "state")], timeout=240)

    rank_rows = []
    if rank and rank["exit"] == 0:
        rank_files = sorted((ROOT / "state/auto-quant/MACD_CURRENT_2155").glob("auto_quant_agent_material_rank.*.json"))
        if rank_files:
            payload = json.loads(rank_files[-1].read_text(encoding="utf-8"))
            for item in payload.get("ranking", []):
                rank_rows.append(item)
    by_provider = {}
    for item in rank_rows:
        provider = item.get("consumer_evidence_profile", {}).get("provider") or item.get("provider") or "unknown"
        stats = by_provider.setdefault(provider, {"rows": 0, "nonzero_rows": 0, "trade_count_sum": 0, "positive_rows": 0})
        stats["rows"] += 1
        trades = int(item.get("trade_count") or 0)
        stats["trade_count_sum"] += trades
        if trades:
            stats["nonzero_rows"] += 1
        if float(item.get("total_profit_pct") or 0) > 0:
            stats["positive_rows"] += 1

    summary = {
        "run_root": str(ROOT),
        "provider_rows": provider_rows,
        "provider_count": len(PROVIDERS),
        "provider_data_acquired_count": len(acquired),
        "material_count": len(material_rows),
        "rank_rows": len(rank_rows),
        "rank_nonzero_trade_rows": sum(1 for row in rank_rows if int(row.get("trade_count") or 0) > 0),
        "rank_total_trade_count": sum(int(row.get("trade_count") or 0) for row in rank_rows),
        "by_provider": by_provider,
        "command_results": command_results + [py_compile] + [x for x in (batch, dispatch, rank) if x],
        "pre_bayes_filter_allowed": False,
        "bbn_allowed": False,
        "catboost_allowed": False,
        "execution_tree_allowed": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    (ROOT / "summaries/macd_current_six_provider_aq_v1.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (ROOT / "checks/macd_current_six_provider_aq_v1.exit").write_text("0\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
