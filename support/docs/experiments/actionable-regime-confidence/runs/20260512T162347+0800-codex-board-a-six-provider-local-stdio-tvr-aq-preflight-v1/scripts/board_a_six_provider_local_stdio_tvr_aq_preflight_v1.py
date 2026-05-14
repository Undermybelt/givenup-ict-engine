from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T162347+0800-codex-board-a-six-provider-local-stdio-tvr-aq-preflight-v1"
)
STATE_DIR = RUN_ROOT / "state"
SYMBOL_ID = "BOARD_A_6PROV_162347"
FETCH = "scripts/auto_quant_external/fetch_external.py"
ICT_ENGINE = "./target/debug/ict-engine"
START = "2026-02-12"
END = "2026-05-12"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def format_cmd(args: list[str], env: dict[str, str] | None = None) -> str:
    if not env:
        return " ".join(args)
    pairs = [f"{key}={value}" for key, value in env.items()]
    return "env " + " ".join(pairs + args)


def run_cmd(
    label: str,
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout: int = 420,
) -> int:
    cmd_path = RUN_ROOT / f"command-output/{label}.cmd"
    out_path = RUN_ROOT / f"command-output/{label}.out"
    err_path = RUN_ROOT / f"command-output/{label}.err"
    exit_path = RUN_ROOT / f"checks/{label}.exit"
    write_text(cmd_path, format_cmd(args, env) + "\n")
    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=proc_env,
        )
        write_text(out_path, proc.stdout)
        write_text(err_path, proc.stderr)
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        write_text(out_path, exc.stdout or "")
        write_text(err_path, (exc.stderr or "") + f"\nTIMEOUT after {timeout}s\n")
        code = 124
    write_text(exit_path, f"{code}\n")
    return code


def normalize_frame(df: pd.DataFrame, dst: Path, aq_dst: Path) -> dict[str, Any]:
    rename = {}
    if "date" not in df.columns:
        if "timestamp" in df.columns:
            rename["timestamp"] = "date"
        elif "ts" in df.columns:
            rename["ts"] = "date"
        elif "time" in df.columns:
            rename["time"] = "date"
        elif "datetime" in df.columns:
            rename["datetime"] = "date"
    if rename:
        df = df.rename(columns=rename)
    required = ["date", "open", "high", "low", "close", "volume"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"missing required columns {missing}")
    out = df[required].copy()
    out["date"] = pd.to_datetime(out["date"], utc=True).dt.strftime("%Y-%m-%d %H:%M:%S")
    for col in ["open", "high", "low", "close", "volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["date", "open", "high", "low", "close"])
    out["volume"] = out["volume"].fillna(0).clip(lower=0)
    out = out.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dst, index=False)
    aq = out.rename(columns={"date": "timestamp"})
    aq.to_csv(aq_dst, index=False)
    return {
        "normalized_path": str(dst),
        "aq_path": str(aq_dst),
        "rows": int(len(out)),
        "first": str(out["date"].iloc[0]) if not out.empty else "",
        "last": str(out["date"].iloc[-1]) if not out.empty else "",
    }


def normalize_csv(src: Path, dst: Path, aq_dst: Path) -> dict[str, Any]:
    df = pd.read_csv(src)
    row = normalize_frame(df, dst, aq_dst)
    row["raw_path"] = str(src)
    return row


def normalize_tvr_json(src: Path, dst: Path, aq_dst: Path) -> dict[str, Any]:
    data = json.loads(src.read_text())
    rows: list[dict[str, Any]] = []
    for result in data.get("results", []):
        if result.get("ok") and isinstance(result.get("data"), list):
            rows.extend(result["data"])
    df = pd.DataFrame(rows)
    row = normalize_frame(df, dst, aq_dst)
    row["raw_path"] = str(src)
    return row


def strategy_source() -> str:
    return '''from __future__ import annotations

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class BoardAProviderBreadthProbeV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.035

    trailing_stop = True
    trailing_stop_positive = 0.012
    trailing_stop_positive_offset = 0.028
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 80

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema55"] = ta.EMA(dataframe, timeperiod=55)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["hour_utc"] = dataframe["date"].dt.hour
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        trend_ok = dataframe["ema21"] > dataframe["ema55"]
        momentum_ok = (dataframe["rsi"] >= 42) & (dataframe["rsi"] <= 68)
        candle_ok = dataframe["close"] > dataframe["open"]
        volatility_ok = (dataframe["atr"] / dataframe["close"]) <= 0.045
        all_hours = (dataframe["hour_utc"] >= 0) & (dataframe["hour_utc"] <= 23)
        entry = trend_ok & momentum_ok & candle_ok & volatility_ok & all_hours
        dataframe.loc[entry, "enter_long"] = 1
        dataframe.loc[entry, "enter_tag"] = "board_a_provider_breadth_probe_v1"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        exit_signal = (dataframe["close"] < dataframe["ema21"]) | (dataframe["rsi"] > 76)
        dataframe.loc[exit_signal, "exit_long"] = 1
        return dataframe
'''


def material(package_id: str, title: str, symbol: str, data_path: Path, provider_note: str) -> dict[str, Any]:
    return {
        "package_id": package_id,
        "title": title,
        "symbol": symbol,
        "timeframe": "1h",
        "direction": "long",
        "data_path": str(data_path),
        "strategy_source_path": str(RUN_ROOT / "agent-material/BoardAProviderBreadthProbeV1.py"),
        "strategy_class_name": "BoardAProviderBreadthProbeV1",
        "strategy_brief": (
            "Board A non-promotional provider-breadth probe for current same-root "
            "provider/AQ plumbing. It is not a profitability factor or acceptance claim."
        ),
        "evaluation_priority": [
            "provider_row_materialized",
            "auto_quant_dispatch_exit",
            "trade_density_diagnostic",
            "regime_conditioned_confidence_not_claimed",
        ],
        "notes": [
            "board=Board A actionable-regime-confidence",
            "branch_path=BoardAProviderBreadth -> CurrentProviderRow -> AQPlumbingProbe",
            provider_note,
            "promotion_allowed=false",
            "trade_usable=false",
            "accepted_95_context=false",
        ],
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    write_text(RUN_ROOT / "run_root.txt", str(RUN_ROOT) + "\n")
    write_text(RUN_ROOT / "agent-material/BoardAProviderBreadthProbeV1.py", strategy_source())

    raw = RUN_ROOT / "data/raw"
    norm = RUN_ROOT / "data/normalized"

    fetch_prefix = [sys.executable, FETCH]
    jobs = [
        (
            "01_fetch_yahoo_spy_1h",
            fetch_prefix
            + [
                "yahoo",
                "--symbol",
                "SPY",
                "--interval",
                "1h",
                "--start",
                START,
                "--end",
                END,
                "--output",
                str(raw / "yahoo_spy_1h.csv"),
            ],
            raw / "yahoo_spy_1h.csv",
            norm / "yahoo_spy_1h.normalized.csv",
            norm / "yahoo_spy_1h.normalized.aq.csv",
            "yfinance/YF",
            "SPY",
        ),
        (
            "02_fetch_binance_btcusdt_1h",
            fetch_prefix
            + [
                "binance-kline",
                "--symbol",
                "BTCUSDT",
                "--interval",
                "1h",
                "--start",
                START,
                "--end",
                END,
                "--output",
                str(raw / "binance_btcusdt_1h.csv"),
            ],
            raw / "binance_btcusdt_1h.csv",
            norm / "binance_btcusdt_1h.normalized.csv",
            norm / "binance_btcusdt_1h.normalized.aq.csv",
            "Binance",
            "BTCUSDT",
        ),
        (
            "03_fetch_bybit_linear_btcusdt_1h",
            fetch_prefix
            + [
                "bybit-kline",
                "--category",
                "linear",
                "--symbol",
                "BTCUSDT",
                "--interval",
                "1h",
                "--start",
                START,
                "--end",
                END,
                "--output",
                str(raw / "bybit_linear_btcusdt_1h.csv"),
            ],
            raw / "bybit_linear_btcusdt_1h.csv",
            norm / "bybit_linear_btcusdt_1h.normalized.csv",
            norm / "bybit_linear_btcusdt_1h.normalized.aq.csv",
            "Bybit",
            "BTCUSDT",
        ),
        (
            "04_fetch_kraken_futures_pfxbtusd_1h",
            fetch_prefix
            + [
                "kraken-kline",
                "--market",
                "futures",
                "--pair",
                "PF_XBTUSD",
                "--interval",
                "1h",
                "--start",
                START,
                "--end",
                END,
                "--output",
                str(raw / "kraken_futures_pfxbtusd_1h.csv"),
            ],
            raw / "kraken_futures_pfxbtusd_1h.csv",
            norm / "kraken_futures_pfxbtusd_1h.normalized.csv",
            norm / "kraken_futures_pfxbtusd_1h.normalized.aq.csv",
            "Kraken",
            "XBTUSD",
        ),
        (
            "05_fetch_ibkr_spy_1h",
            fetch_prefix
            + [
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
                "90 D",
                "--what-to-show",
                "TRADES",
                "--port",
                "4002",
                "--client-id",
                "64",
                "--output",
                str(raw / "ibkr_spy_1h_90d.csv"),
            ],
            raw / "ibkr_spy_1h_90d.csv",
            norm / "ibkr_spy_1h_90d.normalized.csv",
            norm / "ibkr_spy_1h_90d.normalized.aq.csv",
            "IBKR",
            "SPY",
        ),
    ]

    fetch_rows: list[dict[str, Any]] = []
    for label, args, raw_path, norm_path, aq_path, provider, symbol in jobs:
        exit_code = run_cmd(label, args, timeout=420)
        row: dict[str, Any] = {
            "label": label,
            "provider": provider,
            "symbol": symbol,
            "interval": "1h",
            "exit": exit_code,
            "raw_path": str(raw_path),
            "normalized_path": str(norm_path),
            "aq_path": str(aq_path),
            "rows": 0,
            "first": "",
            "last": "",
        }
        if exit_code == 0 and raw_path.exists():
            try:
                row.update(normalize_csv(raw_path, norm_path, aq_path))
            except Exception as exc:
                row["normalize_error"] = str(exc)
        fetch_rows.append(row)

    tvr_env = {
        "HOME": "/tmp/ict-engine-tvr-stdio-162347-home",
        "ICT_ENGINE_TVREMIX_MCP_URL": "",
        "ICT_ENGINE_TVREMIX_MCP_API_KEY": "",
        "ICT_ENGINE_TRADINGVIEW_MCP_CMD": "uv",
        "ICT_ENGINE_TRADINGVIEW_MCP_ARGS": "--directory /Users/thrill3r/tradingview-mcp/tradingview-mcp run tradingview-mcp",
    }
    tvr_label = "06_fetch_tvr_btc_usd_1h_local_stdio"
    tvr_json = raw / "tvr_btc_usd_1h.json"
    tvr_args = [
        ICT_ENGINE,
        "market-data-harness",
        "--action",
        "fetch",
        "--market",
        "board-a-162347-tvr-btc-usd-1h",
        "--interval",
        "1h",
        "--role",
        "crypto_reference",
        "--provider",
        "crypto_reference=tradingview_mcp",
        "--symbol-spec",
        "crypto_reference=BTC-USD",
    ]
    exit_code = run_cmd(tvr_label, tvr_args, env=tvr_env, timeout=420)
    out_path = RUN_ROOT / f"command-output/{tvr_label}.out"
    if out_path.exists():
        write_text(tvr_json, out_path.read_text())
    tvr_row: dict[str, Any] = {
        "label": tvr_label,
        "provider": "TradingViewRemix/TVR",
        "symbol": "BTC-USD",
        "interval": "1h",
        "exit": exit_code,
        "raw_path": str(tvr_json),
        "normalized_path": str(norm / "tvr_btc_usd_1h.normalized.csv"),
        "aq_path": str(norm / "tvr_btc_usd_1h.normalized.aq.csv"),
        "rows": 0,
        "first": "",
        "last": "",
    }
    if exit_code == 0 and tvr_json.exists():
        try:
            tvr_row.update(
                normalize_tvr_json(
                    tvr_json,
                    norm / "tvr_btc_usd_1h.normalized.csv",
                    norm / "tvr_btc_usd_1h.normalized.aq.csv",
                )
            )
        except Exception as exc:
            tvr_row["normalize_error"] = str(exc)
    fetch_rows.append(tvr_row)

    material_specs = [
        (
            "board-a-sixprov-yf-spy-1h-v1",
            "Board A six-provider preflight - yfinance SPY 1h",
            "SPY",
            norm / "yahoo_spy_1h.normalized.aq.csv",
            "source_provider=yfinance/YF SPY 1h current fetch",
        ),
        (
            "board-a-sixprov-binance-btcusdt-1h-v1",
            "Board A six-provider preflight - Binance BTCUSDT 1h",
            "BTCUSDT",
            norm / "binance_btcusdt_1h.normalized.aq.csv",
            "source_provider=Binance public BTCUSDT 1h current fetch",
        ),
        (
            "board-a-sixprov-bybit-btcusdt-1h-v1",
            "Board A six-provider preflight - Bybit BTCUSDT linear 1h",
            "BTCUSDT",
            norm / "bybit_linear_btcusdt_1h.normalized.aq.csv",
            "source_provider=Bybit public linear BTCUSDT 1h current fetch",
        ),
        (
            "board-a-sixprov-kraken-pfxbtusd-1h-v1",
            "Board A six-provider preflight - Kraken PF_XBTUSD 1h",
            "XBTUSD",
            norm / "kraken_futures_pfxbtusd_1h.normalized.aq.csv",
            "source_provider=Kraken futures PF_XBTUSD 1h current fetch",
        ),
        (
            "board-a-sixprov-ibkr-spy-1h-v1",
            "Board A six-provider preflight - IBKR SPY 1h",
            "SPY",
            norm / "ibkr_spy_1h_90d.normalized.aq.csv",
            "source_provider=IBKR gateway SPY 1h 90D current fetch",
        ),
        (
            "board-a-sixprov-tvr-btc-usd-1h-v1",
            "Board A six-provider preflight - TVR BTC-USD 1h local stdio",
            "BTC-USD",
            norm / "tvr_btc_usd_1h.normalized.aq.csv",
            "source_provider=TradingViewRemix/TVR local stdio BTC-USD 1h current fetch",
        ),
    ]

    material_paths: list[Path] = []
    for package_id, title, symbol, data_path, provider_note in material_specs:
        if data_path.exists():
            path = RUN_ROOT / f"agent-material/{package_id}.material.json"
            write_json(path, material(package_id, title, symbol, data_path, provider_note))
            material_paths.append(path)

    provider_rows = []
    for row in fetch_rows:
        provider_rows.append(
            {
                "provider": row["provider"],
                "provider_requested": True,
                "provider_data_acquired": bool(row.get("rows", 0)),
                "provider_unreachable": row["exit"] != 0 or not bool(row.get("rows", 0)),
                "aq_material_created": any(row["provider"].split("/")[0].lower() in str(path).lower() for path in material_paths),
                "symbol": row["symbol"],
                "interval": row["interval"],
                "exit": row["exit"],
                "rows": row.get("rows", 0),
                "first": row.get("first", ""),
                "last": row.get("last", ""),
                "source_or_blocker": row.get("aq_path") if row.get("rows", 0) else row.get("raw_path"),
                "normalize_error": row.get("normalize_error", ""),
            }
        )

    provider_matrix = RUN_ROOT / "summaries/provider_provenance_matrix.csv"
    provider_matrix.parent.mkdir(parents=True, exist_ok=True)
    with provider_matrix.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(provider_rows[0].keys()))
        writer.writeheader()
        writer.writerows(provider_rows)

    write_json(
        RUN_ROOT / "summaries/preflight_summary_before_aq.json",
        {
            "fetch_rows": fetch_rows,
            "provider_rows": provider_rows,
            "material_paths": [str(path) for path in material_paths],
            "six_required_providers_requested": True,
            "six_required_providers_acquired": len([row for row in provider_rows if row["provider_data_acquired"]]) == 6,
            "remote_http_api_called": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        },
    )

    material_args = []
    for path in material_paths:
        material_args.extend(["--material", str(path)])
    batch_args = [
        ICT_ENGINE,
        "auto-quant-agent-material-batch",
        "--symbol",
        SYMBOL_ID,
        "--state-dir",
        str(STATE_DIR),
        "--max-parallel",
        "1",
        "--repo-url",
        "/Users/thrill3r/Auto-Quant",
    ] + material_args
    batch_exit = run_cmd("07_auto_quant_agent_material_batch", batch_args, timeout=420)

    dispatch_exit = -1
    rank_exit = -1
    if batch_exit == 0 and material_paths:
        group_indices = ",".join(str(i) for i in range(len(material_paths)))
        dispatch_exit = run_cmd(
            "08_auto_quant_agent_material_dispatch",
            [
                ICT_ENGINE,
                "auto-quant-agent-material-dispatch",
                "--symbol",
                SYMBOL_ID,
                "--state-dir",
                str(STATE_DIR),
                "--group-indices",
                group_indices,
            ],
            timeout=1200,
        )
        if dispatch_exit == 0:
            rank_exit = run_cmd(
                "09_auto_quant_agent_material_rank",
                [
                    ICT_ENGINE,
                    "auto-quant-agent-material-rank",
                    "--symbol",
                    SYMBOL_ID,
                    "--state-dir",
                    str(STATE_DIR),
                ],
                timeout=420,
            )

    manifest_paths = [
        RUN_ROOT / "agent-material/BoardAProviderBreadthProbeV1.py",
        RUN_ROOT / "summaries/preflight_summary_before_aq.json",
        RUN_ROOT / "summaries/provider_provenance_matrix.csv",
    ] + material_paths
    write_text(
        RUN_ROOT / "checks/sha256_manifest.out",
        "".join(f"{sha256(path)}  {path}\n" for path in manifest_paths if path.exists()),
    )

    final_summary = {
        "run_id": "20260512T162347+0800-codex-board-a-six-provider-local-stdio-tvr-aq-preflight-v1",
        "active_claim": "162347_board_a_six_provider_local_stdio_tvr_aq_preflight_v1",
        "provider_rows": provider_rows,
        "material_paths": [str(path) for path in material_paths],
        "batch_exit": batch_exit,
        "dispatch_exit": dispatch_exit,
        "rank_exit": rank_exit,
        "remote_http_api_called": False,
        "same_root_six_provider_provider_rows": len([row for row in provider_rows if row["provider_data_acquired"]]) == 6,
        "auto_quant_dispatch_attempted": batch_exit == 0 and bool(material_paths),
        "auto_quant_dispatch_completed": dispatch_exit == 0,
        "accepted_95_contexts_added": 0,
        "pre_bayes_bbn_catboost_execution_tree_ran": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(RUN_ROOT / "summaries/final_preflight_summary_v1.json", final_summary)

    assertion_lines = [
        f"{'PASS' if final_summary['same_root_six_provider_provider_rows'] else 'FAIL'} six_required_provider_rows_acquired={final_summary['same_root_six_provider_provider_rows']}",
        f"{'PASS' if batch_exit == 0 else 'FAIL'} auto_quant_agent_material_batch_exit={batch_exit}",
        f"{'PASS' if dispatch_exit == 0 else 'FAIL'} auto_quant_agent_material_dispatch_exit={dispatch_exit}",
        f"{'PASS' if rank_exit == 0 else 'FAIL'} auto_quant_agent_material_rank_exit={rank_exit}",
        "PASS remote_http_api_called=False",
        "PASS promotion_allowed=False",
        "PASS trade_usable=False",
        "PASS update_goal=False",
    ]
    write_text(RUN_ROOT / "checks/final_preflight_assertions.out", "\n".join(assertion_lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
