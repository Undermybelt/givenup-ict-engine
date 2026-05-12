#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


SCRIPT = Path(__file__).resolve()
BASE = SCRIPT.parents[1]
RUN_STAMP = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%dT%H%M%S+0800")
ROOT = BASE / "runs" / f"{RUN_STAMP}-codex-high-density-six-provider-aq-runtime-evidence-v1"
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
        "TradingViewRemix/TVR BTC-USD 1h",
        "BTC",
        "1h",
        "tvr_btc_usd_1h.csv",
        None,
        {
            "market_key": "board-a-204858-tvr-BTC-USD-1h",
            "interval": "1h",
            "count": 1200,
            "related_roles": ["crypto_reference"],
            "provider_preferences": {"crypto_reference": "tradingview_mcp"},
            "symbol_overrides": {"crypto_reference": {"display_symbol": "BTC-USD", "tradingview_mcp": "BTC-USD"}},
        },
    ),
]


BRANCHES = [
    {
        "id": "runtime_density_upbar_reclaim_long_v1",
        "class": "RuntimeDensityUpbarReclaimLongV1",
        "direction": "long",
        "path": "Transition -> RuntimeEvidenceDensity -> upbar_reclaim -> runtime_density_upbar_reclaim_long_v1",
        "entry": '(dataframe["close"] > dataframe["open"]) & (dataframe["volume"] > 0)',
        "exit": '(dataframe["close"] < dataframe["open"]) | (dataframe["rsi14"] > 74)',
        "roi": "0.004",
        "stoploss": "-0.014",
    },
    {
        "id": "runtime_density_downbar_failure_short_v1",
        "class": "RuntimeDensityDownbarFailureShortV1",
        "direction": "short",
        "path": "Transition -> RuntimeEvidenceDensity -> downbar_failure -> runtime_density_downbar_failure_short_v1",
        "entry": '(dataframe["close"] < dataframe["open"]) & (dataframe["volume"] > 0)',
        "exit": '(dataframe["close"] > dataframe["open"]) | (dataframe["rsi14"] < 26)',
        "roi": "0.004",
        "stoploss": "-0.014",
    },
]


def run_cmd(name: str, argv: list[str], timeout: int = 180) -> dict:
    command_dir = ROOT / "command-output"
    checks_dir = ROOT / "checks"
    command_dir.mkdir(parents=True, exist_ok=True)
    checks_dir.mkdir(parents=True, exist_ok=True)
    (command_dir / f"{name}.cmd").write_text(" ".join(argv) + "\n", encoding="utf-8")
    try:
        proc = subprocess.run(argv, cwd=REPO, text=True, capture_output=True, timeout=timeout)
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
    request_path = ROOT / "requests/tvr_btc_usd_1h.json"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(json.dumps(spec.request_json, indent=2) + "\n", encoding="utf-8")
    result = run_cmd("06_tvr_local_stdio_btc_usd_1h", [str(ICT), "market-data-harness", "--action", "fetch", "--request-json", str(request_path)], timeout=180)
    out_json = ROOT / "command-output/06_tvr_local_stdio_btc_usd_1h.out"
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
    enter_col = "enter_short" if branch["direction"] == "short" else "enter_long"
    exit_col = "exit_short" if branch["direction"] == "short" else "exit_long"
    can_short = "True" if branch["direction"] == "short" else "False"
    return f'''from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class {branch["class"]}(IStrategy):
    timeframe = "1h"
    can_short = {can_short}
    minimal_roi = {{"0": {branch["roi"]}, "12": 0}}
    stoploss = {branch["stoploss"]}
    startup_candle_count = 30

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["rsi14"] = ta.RSI(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        condition = {branch["entry"]}
        dataframe.loc[condition, ["{enter_col}", "enter_tag"]] = (1, "{branch["id"]}")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[{branch["exit"]}, ["{exit_col}", "exit_tag"]] = (1, "{branch["id"]}_exit")
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
                "strategy_brief": "High-density runtime evidence probe; density diagnostic only, not promotion.",
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
                    "aq_provider_invoked=true",
                    "provider_data_acquired_this_step=true",
                    "local_cache_replay=false",
                    "high_density_probe=true",
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
            [str(ICT), "auto-quant-agent-material-batch", "--symbol", "HDR_204858", "--state-dir", str(ROOT / "state"), "--max-parallel", "3", *sum([["--material", p] for p in material_paths], [])],
            timeout=900,
        )
        if batch["exit"] == 0:
            dispatch = run_cmd("09_auto_quant_agent_material_dispatch", [str(ICT), "auto-quant-agent-material-dispatch", "--symbol", "HDR_204858", "--state-dir", str(ROOT / "state")], timeout=900)
        if dispatch and dispatch["exit"] == 0:
            rank = run_cmd("10_auto_quant_agent_material_rank", [str(ICT), "auto-quant-agent-material-rank", "--symbol", "HDR_204858", "--state-dir", str(ROOT / "state")], timeout=240)

    rank_rows = []
    if rank and rank["exit"] == 0:
        rank_files = sorted((ROOT / "state/auto-quant/HDR_204858").glob("auto_quant_agent_material_rank.*.json"))
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
    (ROOT / "summaries/high_density_six_provider_aq_runtime_evidence_v1.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (ROOT / "checks/high_density_six_provider_aq_runtime_evidence_v1.exit").write_text("0\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
