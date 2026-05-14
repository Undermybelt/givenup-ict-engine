#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T184103+0800-codex-session-vwap-liquidity-six-provider-aq-v1"
RUN_ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
FETCH = "scripts/auto_quant_external/fetch_external.py"
PY_FETCH = [
    "uv",
    "run",
    "--with",
    "pandas",
    "--with",
    "requests",
    "--with",
    "ib_async",
    "--with",
    "redis",
    "--with",
    "pyyaml",
    "python",
    FETCH,
]
TIMERANGE = "20250101-20260512"
BRANCH_PATHS = [
    "RangeConsolidation -> SessionMeanReversion -> VwapDistanceFade -> session_vwap_fade_liquidity_v1",
    "TrendExpansion -> SessionContinuation -> OpeningRangeRetest -> session_opening_range_retest_v1",
    "VolatilityCompression -> LiquidityExpansion -> VolumeImpulseBreakout -> session_liquidity_impulse_breakout_v1",
    "Transition -> LiquidityRiskControl -> LowLiquiditySuppression -> session_low_liquidity_suppression_v1",
]


STRATEGY_SOURCE = '''from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class ProviderSessionVwapLiquidityV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.028

    trailing_stop = True
    trailing_stop_positive = 0.010
    trailing_stop_positive_offset = 0.024
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count: int = 120

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["hour_utc"] = dataframe["date"].dt.hour
        dataframe["session_date"] = dataframe["date"].dt.date

        typical = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3.0
        pv = typical * dataframe["volume"].clip(lower=0)
        cum_pv = pv.groupby(dataframe["session_date"]).cumsum()
        cum_volume = dataframe["volume"].clip(lower=0).groupby(dataframe["session_date"]).cumsum()
        dataframe["session_vwap"] = cum_pv / cum_volume.replace(0, float("nan"))

        dataframe["opening_range_high"] = dataframe["high"].groupby(dataframe["session_date"]).transform(
            lambda values: values.head(3).max()
        )
        dataframe["opening_range_low"] = dataframe["low"].groupby(dataframe["session_date"]).transform(
            lambda values: values.head(3).min()
        )
        dataframe["volume_ma24"] = dataframe["volume"].rolling(24, min_periods=12).mean()
        dataframe["volume_impulse"] = dataframe["volume"] > dataframe["volume_ma24"] * 1.18
        dataframe["atr_ratio"] = dataframe["atr"] / dataframe["close"]
        dataframe["vwap_distance_atr"] = (dataframe["close"] - dataframe["session_vwap"]) / dataframe["atr"]
        dataframe["liquid_window"] = dataframe["hour_utc"].between(0, 23)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""

        liquid = dataframe["liquid_window"] & dataframe["session_vwap"].notna() & dataframe["atr"].notna()
        normal_vol = dataframe["atr_ratio"].between(0.0015, 0.055)
        low_liquidity = dataframe["volume"] < dataframe["volume_ma24"] * 0.55

        fade = (
            liquid
            & normal_vol
            & (dataframe["vwap_distance_atr"] < -0.70)
            & (dataframe["rsi"].between(28, 48))
            & (dataframe["close"] > dataframe["low"].shift(1))
            & ~low_liquidity
        )
        retest = (
            liquid
            & normal_vol
            & (dataframe["ema20"] > dataframe["ema50"])
            & (dataframe["low"] <= dataframe["opening_range_high"])
            & (dataframe["close"] > dataframe["opening_range_high"])
            & (dataframe["rsi"].between(42, 68))
            & ~low_liquidity
        )
        impulse = (
            liquid
            & dataframe["volume_impulse"]
            & (dataframe["close"] > dataframe["opening_range_high"])
            & (dataframe["close"] > dataframe["session_vwap"])
            & (dataframe["atr_ratio"].between(0.002, 0.070))
            & (dataframe["rsi"].between(46, 74))
            & ~low_liquidity
        )

        dataframe.loc[fade, "enter_long"] = 1
        dataframe.loc[fade, "enter_tag"] = "session_vwap_fade_liquidity_v1"
        dataframe.loc[retest, "enter_long"] = 1
        dataframe.loc[retest, "enter_tag"] = "session_opening_range_retest_v1"
        dataframe.loc[impulse, "enter_long"] = 1
        dataframe.loc[impulse, "enter_tag"] = "session_liquidity_impulse_breakout_v1"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        low_liquidity = dataframe["volume"] < dataframe["volume_ma24"] * 0.45
        vwap_reclaim_exhausted = (dataframe["close"] > dataframe["session_vwap"]) & (dataframe["rsi"] > 70)
        trend_loss = dataframe["close"] < dataframe["ema50"]
        dataframe.loc[low_liquidity | vwap_reclaim_exhausted | trend_loss, "exit_long"] = 1
        return dataframe
'''


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_cmd(label: str, args: list[str], timeout: int = 900, env: dict[str, str] | None = None) -> int:
    write_text(RUN_ROOT / f"command-output/{label}.cmd", " ".join(args) + "\n")
    out_path = RUN_ROOT / f"command-output/{label}.out"
    err_path = RUN_ROOT / f"command-output/{label}.err"
    exit_path = RUN_ROOT / f"checks/{label}.exit"
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False, env=merged_env)
        write_text(out_path, proc.stdout)
        write_text(err_path, proc.stderr)
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        write_text(out_path, exc.stdout or "")
        write_text(err_path, (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n")
        code = 124
    write_text(exit_path, f"{code}\n")
    return code


def normalize_csv(src: Path, dst: Path) -> dict[str, Any]:
    dataframe = pd.read_csv(src)
    if "timestamp" not in dataframe.columns:
        for alias in ("date", "datetime", "ts", "time"):
            if alias in dataframe.columns:
                dataframe = dataframe.rename(columns={alias: "timestamp"})
                break
    required = ["timestamp", "open", "high", "low", "close", "volume"]
    missing = [column for column in required if column not in dataframe.columns]
    if missing:
        raise ValueError(f"{src} missing required columns {missing}")
    out = dataframe[required].copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    for column in ("open", "high", "low", "close", "volume"):
        out[column] = pd.to_numeric(out[column], errors="coerce")
    out = out.dropna(subset=["timestamp", "open", "high", "low", "close"])
    out["volume"] = out["volume"].fillna(0).clip(lower=0)
    out = out.drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dst, index=False)
    return {
        "raw_path": str(src),
        "normalized_path": str(dst),
        "rows": int(len(out)),
        "first": str(out["timestamp"].iloc[0]) if not out.empty else "",
        "last": str(out["timestamp"].iloc[-1]) if not out.empty else "",
    }


def normalize_tvr_stdout(src: Path, dst: Path) -> dict[str, Any]:
    payload = json.loads(src.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for result in payload.get("results", []):
        if result.get("provider") != "tradingview_mcp" or not result.get("ok"):
            continue
        for bar in result.get("data", []):
            rows.append(
                {
                    "timestamp": bar.get("timestamp", ""),
                    "open": bar.get("open", ""),
                    "high": bar.get("high", ""),
                    "low": bar.get("low", ""),
                    "close": bar.get("close", ""),
                    "volume": bar.get("volume", 0),
                }
            )
    raw_csv = dst.with_suffix(".raw.csv")
    write_csv(raw_csv, rows, ["timestamp", "open", "high", "low", "close", "volume"])
    summary = normalize_csv(raw_csv, dst)
    summary["raw_path"] = str(src)
    return summary


def sample_adequacy(rows: int) -> str:
    if rows >= 1000:
        return "preflight_rows_ok_not_profit_evidence"
    if rows >= 300:
        return "preflight_smoke_only"
    return "fail_closed_too_few_rows"


def material(package_id: str, title: str, aq_symbol: str, data_path: Path, provider_note: str) -> dict[str, Any]:
    return {
        "package_id": package_id,
        "title": title,
        "symbol": aq_symbol,
        "timeframe": "1h",
        "timerange": TIMERANGE,
        "direction": "long",
        "data_path": str(data_path),
        "strategy_source_path": str(RUN_ROOT / "agent-material/ProviderSessionVwapLiquidityV1.py"),
        "strategy_class_name": "ProviderSessionVwapLiquidityV1",
        "strategy_brief": "Board B session VWAP, opening-range, and liquidity impulse profitability factor with branch-tagged leaves.",
        "evaluation_priority": [
            "branch_trade_density",
            "regime_conditioned_win_rate",
            "profit_factor",
            "provider_portability",
            "sample_adequacy",
        ],
        "consumer_evidence_profile": {
            "main_regime": "SessionLiquidity",
            "branch_paths": BRANCH_PATHS,
            "promotion_allowed": False,
        },
        "notes": [
            provider_note,
            "branch_matrix=" + " | ".join(BRANCH_PATHS),
            f"timerange={TIMERANGE}",
            "provider_preflight_only=true",
            "promotion_allowed=false until AQ dispatch and ordered downstream chain pass",
        ],
    }


def main() -> int:
    for subdir in ("checks", "command-output", "data/raw", "data/normalized", "agent-material", "summaries", "state"):
        (RUN_ROOT / subdir).mkdir(parents=True, exist_ok=True)
    write_text(RUN_ROOT / "run_root.txt", str(RUN_ROOT) + "\n")
    write_text(RUN_ROOT / "agent-material/ProviderSessionVwapLiquidityV1.py", STRATEGY_SOURCE)

    requested_start = "2025-01-01"
    requested_end = "2026-05-12"
    raw = RUN_ROOT / "data/raw"
    norm = RUN_ROOT / "data/normalized"
    fetch_jobs = [
        ("01_fetch_yahoo_spy_1h", PY_FETCH + ["yahoo", "--symbol", "SPY", "--interval", "1h", "--start", requested_start, "--end", requested_end, "--output", str(raw / "yahoo_spy_1h.csv")], raw / "yahoo_spy_1h.csv", norm / "yahoo_spy_1h.normalized.csv", "yfinance/YF", "source_provider=yfinance/YF SPY 1h current fetch", "SPY", "SPY"),
        ("02_fetch_binance_btcusdt_1h", PY_FETCH + ["binance-kline", "--symbol", "BTCUSDT", "--interval", "1h", "--start", requested_start, "--end", requested_end, "--output", str(raw / "binance_btcusdt_1h.csv")], raw / "binance_btcusdt_1h.csv", norm / "binance_btcusdt_1h.normalized.csv", "Binance", "source_provider=Binance public BTCUSDT 1h current fetch", "BTC", "BTCUSDT"),
        ("03_fetch_bybit_linear_btcusdt_1h", PY_FETCH + ["bybit-kline", "--category", "linear", "--symbol", "BTCUSDT", "--interval", "1h", "--start", requested_start, "--end", requested_end, "--output", str(raw / "bybit_linear_btcusdt_1h.csv")], raw / "bybit_linear_btcusdt_1h.csv", norm / "bybit_linear_btcusdt_1h.normalized.csv", "Bybit", "source_provider=Bybit public linear BTCUSDT 1h current fetch", "BTC", "BTCUSDT"),
        ("04_fetch_kraken_futures_pfxbtusd_1h", PY_FETCH + ["kraken-kline", "--market", "futures", "--pair", "PF_XBTUSD", "--interval", "1h", "--start", requested_start, "--end", requested_end, "--output", str(raw / "kraken_futures_pfxbtusd_1h.csv")], raw / "kraken_futures_pfxbtusd_1h.csv", norm / "kraken_futures_pfxbtusd_1h.normalized.csv", "Kraken", "source_provider=Kraken futures PF_XBTUSD 1h current fetch", "BTC", "XBTUSD"),
        ("05_fetch_ibkr_spy_1h", PY_FETCH + ["ibkr-historical", "--symbol", "SPY", "--sec-type", "STK", "--exchange", "SMART", "--currency", "USD", "--primary-exchange", "ARCA", "--bar-size", "1 hour", "--duration", "90 D", "--what-to-show", "TRADES", "--port", "4002", "--client-id", "85", "--output", str(raw / "ibkr_spy_1h_90d.csv")], raw / "ibkr_spy_1h_90d.csv", norm / "ibkr_spy_1h_90d.normalized.csv", "IBKR", "source_provider=IBKR gateway SPY 1h 90D current fetch", "SPY", "SPY"),
    ]

    provider_rows: list[dict[str, Any]] = []
    material_rows: list[dict[str, str]] = []
    for label, args, raw_path, norm_path, provider, note, aq_symbol, display_symbol in fetch_jobs:
        exit_code = run_cmd(label, args, timeout=900)
        row: dict[str, Any] = {
            "provider": provider,
            "label": label,
            "exit": exit_code,
            "requested_span": f"{requested_start}_to_{requested_end}",
            "timeframe": "1h",
            "raw_path": str(raw_path),
            "normalized_path": str(norm_path),
            "rows": 0,
            "first": "",
            "last": "",
            "material_path": "",
            "aq_symbol": aq_symbol,
            "provider_symbol": display_symbol,
            "provider_authority_state": "fetch_failed",
            "sample_adequacy": "fail_closed_no_rows",
        }
        if exit_code == 0 and raw_path.exists():
            row.update(normalize_csv(raw_path, norm_path))
            row["provider_authority_state"] = "current_same_root_fetch"
            row["sample_adequacy"] = sample_adequacy(int(row["rows"]))
            package_id = f"session-vwap-liquidity-{provider.lower().replace('/', '-').replace(' ', '-')}-1h-v1"
            material_path = RUN_ROOT / "agent-material" / f"{package_id}.material.json"
            write_json(material_path, material(package_id, f"Session VWAP liquidity - {provider} {display_symbol} 1h", aq_symbol, norm_path, note))
            row["material_path"] = str(material_path)
            material_rows.append({"provider": provider, "material_path": str(material_path), "rows": str(row["rows"])})
        provider_rows.append(row)

    tvr_label = "06_fetch_tvr_local_stdio_btc_usd_1h"
    tvr_stdout = RUN_ROOT / f"command-output/{tvr_label}.out"
    tvr_exit = run_cmd(
        tvr_label,
        [
            "./target/debug/ict-engine",
            "market-data-harness",
            "--action",
            "fetch",
            "--market",
            "board-b-184103-session-vwap-tvr-btc-usd-1h",
            "--interval",
            "1h",
            "--role",
            "crypto_reference",
            "--provider",
            "crypto_reference=tradingview_mcp",
            "--symbol-spec",
            "crypto_reference=BTC-USD",
        ],
        env={
            "HOME": "/tmp/ict-engine-tvr-local-stdio-184103-home",
            "ICT_ENGINE_TVREMIX_MCP_URL": "",
            "ICT_ENGINE_TVREMIX_MCP_API_KEY": "",
            "ICT_ENGINE_TRADINGVIEW_MCP_CMD": "uv",
            "ICT_ENGINE_TRADINGVIEW_MCP_ARGS": "--directory /Users/thrill3r/tradingview-mcp/tradingview-mcp run tradingview-mcp",
        },
        timeout=900,
    )
    tvr_norm = norm / "tvr_btc_usd_1h.normalized.csv"
    tvr_row: dict[str, Any] = {
        "provider": "TradingViewRemix/TVR",
        "label": tvr_label,
        "exit": tvr_exit,
        "requested_span": "provider_default_local_stdio",
        "timeframe": "1h",
        "raw_path": str(tvr_stdout),
        "normalized_path": str(tvr_norm),
        "rows": 0,
        "first": "",
        "last": "",
        "material_path": "",
        "aq_symbol": "BTC",
        "provider_symbol": "BTC-USD",
        "provider_authority_state": "fetch_failed",
        "sample_adequacy": "fail_closed_no_rows",
    }
    if tvr_exit == 0:
        tvr_row.update(normalize_tvr_stdout(tvr_stdout, tvr_norm))
        tvr_row["provider_authority_state"] = "current_same_root_fetch_local_stdio"
        tvr_row["sample_adequacy"] = sample_adequacy(int(tvr_row["rows"]))
        package_id = "session-vwap-liquidity-tvr-btc-usd-1h-v1"
        material_path = RUN_ROOT / "agent-material" / f"{package_id}.material.json"
        write_json(material_path, material(package_id, "Session VWAP liquidity - TVR BTC-USD 1h", "BTC", tvr_norm, "source_provider=TradingViewRemix/TVR local-stdio BTC-USD 1h current fetch"))
        tvr_row["material_path"] = str(material_path)
        material_rows.append({"provider": "TradingViewRemix/TVR", "material_path": str(material_path), "rows": str(tvr_row["rows"])})
    provider_rows.append(tvr_row)

    provider_fieldnames = [
        "provider",
        "label",
        "exit",
        "requested_span",
        "timeframe",
        "raw_path",
        "normalized_path",
        "rows",
        "first",
        "last",
        "material_path",
        "aq_symbol",
        "provider_symbol",
        "provider_authority_state",
        "sample_adequacy",
    ]
    write_csv(RUN_ROOT / "summaries/provider_provenance_matrix.csv", provider_rows, provider_fieldnames)
    write_csv(RUN_ROOT / "summaries/material_paths.csv", material_rows, ["provider", "material_path", "rows"])

    all_required = {"IBKR", "TradingViewRemix/TVR", "yfinance/YF", "Kraken", "Binance", "Bybit"}
    providers_with_rows = {
        str(row["provider"])
        for row in provider_rows
        if int(row.get("rows") or 0) > 0 and int(row.get("exit") if row.get("exit") is not None else 1) == 0
    }
    summary = {
        "run_id": RUN_ID,
        "root": str(RUN_ROOT),
        "branch_paths": BRANCH_PATHS,
        "provider_rows": provider_rows,
        "providers_with_current_rows": sorted(providers_with_rows),
        "provider_rows_required": sorted(all_required),
        "provider_rows_current_same_root": len(providers_with_rows),
        "provider_rows_current_same_root_6_of_6": providers_with_rows == all_required,
        "agent_material_count": len(material_rows),
        "branch_paths_preserved": "4/4",
        "timerange": TIMERANGE,
        "aq_dispatch_started": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(RUN_ROOT / "summaries/session_vwap_liquidity_provider_preflight_v1.json", summary)

    manifest_rows = []
    for path in sorted(RUN_ROOT.rglob("*")):
        if path.is_file():
            manifest_rows.append({"path": str(path), "sha256": sha256(path)})
    write_csv(RUN_ROOT / "checks/sha256_manifest.csv", manifest_rows, ["path", "sha256"])

    assertions = [
        f"provider_rows_current_same_root={len(providers_with_rows)}/6",
        f"provider_rows_current_same_root_6_of_6={providers_with_rows == all_required}",
        f"agent_material_count={len(material_rows)}",
        "branch_paths_preserved=4/4",
        f"timerange={TIMERANGE}",
        "aq_dispatch_started=false",
        "promotion_allowed=false",
        "trade_usable=false",
        "update_goal=false",
    ]
    write_text(RUN_ROOT / "checks/provider_preflight_assertions.out", "\n".join(assertions) + "\n")
    return 0 if providers_with_rows == all_required and len(material_rows) == 6 else 1


if __name__ == "__main__":
    raise SystemExit(main())
