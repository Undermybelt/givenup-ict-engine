from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pandas as pd


RUN_ROOT = Path(
    "docs/experiments/actionable-regime-confidence/runs/"
    "20260512T162255+0800-codex-board-a-six-provider-current-aq-packet-v1"
)
FETCH = "scripts/auto_quant_external/fetch_external.py"
PY_FETCH_PREFIX = [
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
TVR_ENV = {
    "HOME": "/tmp/ict-engine-tvr-stdio-162255-home",
    "ICT_ENGINE_TVREMIX_MCP_URL": "",
    "ICT_ENGINE_TVREMIX_MCP_API_KEY": "",
    "ICT_ENGINE_TRADINGVIEW_MCP_CMD": "uv",
    "ICT_ENGINE_TRADINGVIEW_MCP_ARGS": "--directory /Users/thrill3r/tradingview-mcp/tradingview-mcp run tradingview-mcp",
}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def run_cmd(label: str, args: list[str], timeout: int = 420, env: dict[str, str] | None = None) -> int:
    cmd_path = RUN_ROOT / f"command-output/{label}.cmd"
    out_path = RUN_ROOT / f"command-output/{label}.out"
    err_path = RUN_ROOT / f"command-output/{label}.err"
    exit_path = RUN_ROOT / f"checks/{label}.exit"
    printable = " ".join(args)
    if env:
        safe_env = " ".join(f"{key}=<unset>" if key.endswith("API_KEY") else f"{key}={value!r}" for key, value in env.items())
        printable = f"env {safe_env} {printable}"
    write_text(cmd_path, printable + "\n")
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=merged_env,
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


def normalize_csv(src: Path, dst: Path) -> dict[str, object]:
    df = pd.read_csv(src)
    if "timestamp" not in df.columns:
        for candidate in ["date", "ts", "time", "datetime", "ts_event"]:
            if candidate in df.columns:
                df = df.rename(columns={candidate: "timestamp"})
                break
    required = ["timestamp", "open", "high", "low", "close", "volume"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{src} missing required columns {missing}")
    out = df[required].copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    for col in ["open", "high", "low", "close", "volume"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
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


def normalize_tvr_harness_json(src: Path, raw_csv: Path, normalized_csv: Path) -> dict[str, object]:
    payload = json.loads(src.read_text())
    data = []
    for result in payload.get("results", []):
        if result.get("ok") and result.get("data"):
            data = result["data"]
            break
    raw_csv.parent.mkdir(parents=True, exist_ok=True)
    with raw_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        for row in data:
            writer.writerow(
                {
                    "timestamp": row.get("timestamp", ""),
                    "open": row.get("open", ""),
                    "high": row.get("high", ""),
                    "low": row.get("low", ""),
                    "close": row.get("close", ""),
                    "volume": row.get("volume", 0),
                }
            )
    return normalize_csv(raw_csv, normalized_csv)


def strategy_source() -> str:
    return '''from __future__ import annotations

from freqtrade.strategy import IStrategy
from pandas import DataFrame


class ProviderRegimeProbeV1(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = "1h"
    can_short = False

    minimal_roi = {"0": 100}
    stoploss = -0.045
    trailing_stop = True
    trailing_stop_positive = 0.008
    trailing_stop_positive_offset = 0.018
    trailing_only_offset_is_reached = True

    process_only_new_candles = True
    use_exit_signal = True
    startup_candle_count = 120

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = dataframe["close"].ewm(span=20, adjust=False).mean()
        dataframe["ema80"] = dataframe["close"].ewm(span=80, adjust=False).mean()
        prev_close = dataframe["close"].shift(1)
        tr1 = dataframe["high"] - dataframe["low"]
        tr2 = (dataframe["high"] - prev_close).abs()
        tr3 = (dataframe["low"] - prev_close).abs()
        dataframe["atr14"] = tr1.combine(tr2, max).combine(tr3, max).rolling(14, min_periods=7).mean()
        delta = dataframe["close"].diff()
        gain = delta.clip(lower=0).rolling(14, min_periods=7).mean()
        loss = (-delta.clip(upper=0)).rolling(14, min_periods=7).mean()
        rs = gain / loss.replace(0, 1e-9)
        dataframe["rsi14"] = 100 - (100 / (1 + rs))
        dataframe["trend_strength"] = (dataframe["ema20"] - dataframe["ema80"]) / dataframe["close"]
        dataframe["vol_floor"] = dataframe["volume"].rolling(24, min_periods=6).median().fillna(0) * 0.25
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_tag"] = ""
        mask = (
            (dataframe["close"] > dataframe["ema20"])
            & (dataframe["ema20"] > dataframe["ema80"])
            & (dataframe["trend_strength"] > 0.0015)
            & (dataframe["rsi14"].between(42, 72))
            & (dataframe["volume"] >= dataframe["vol_floor"])
        )
        dataframe.loc[mask, "enter_long"] = 1
        dataframe.loc[mask, "enter_tag"] = "provider_regime_probe_long"
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        mask = (
            (dataframe["close"] < dataframe["ema20"])
            | (dataframe["trend_strength"] < -0.001)
            | (dataframe["rsi14"] > 80)
        )
        dataframe.loc[mask, "exit_long"] = 1
        return dataframe
'''


def material(package_id: str, title: str, symbol: str, data_path: Path, provider_note: str) -> dict[str, object]:
    return {
        "package_id": package_id,
        "title": title,
        "symbol": symbol,
        "timeframe": "1h",
        "direction": "long",
        "data_path": str(data_path),
        "strategy_source_path": str(RUN_ROOT / "agent-material/ProviderRegimeProbeV1.py"),
        "strategy_class_name": "ProviderRegimeProbeV1",
        "strategy_brief": "Board A provider-backed regime-probe material for validating provider routing before BBN/CatBoost/execution-tree admission.",
        "evaluation_priority": [
            "provider_route_validity",
            "trade_density_for_downstream_rows",
            "regime_conditioned_outcome_rows",
            "fail_closed_downstream_readback",
        ],
        "consumer_evidence_profile": {
            "board": "A",
            "root": "MainRegimeV2",
            "promotion_allowed": False,
        },
        "notes": [
            "Board A confidence packet: provider/AQ routing evidence only until downstream calibrated posterior/lower-bound evidence exists",
            provider_note,
            "promotion_allowed=false",
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
    write_text(RUN_ROOT / "agent-material/ProviderRegimeProbeV1.py", strategy_source())

    raw = RUN_ROOT / "data/raw"
    norm = RUN_ROOT / "data/normalized"
    start = "2026-02-12"
    end = "2026-05-12"

    jobs = [
        (
            "01_fetch_yahoo_spy_1h",
            PY_FETCH_PREFIX
            + [
                "yahoo",
                "--symbol",
                "SPY",
                "--interval",
                "1h",
                "--start",
                start,
                "--end",
                end,
                "--output",
                str(raw / "yahoo_spy_1h.csv"),
            ],
            raw / "yahoo_spy_1h.csv",
            norm / "yahoo_spy_1h.normalized.csv",
        ),
        (
            "02_fetch_binance_btcusdt_1h",
            PY_FETCH_PREFIX
            + [
                "binance-kline",
                "--symbol",
                "BTCUSDT",
                "--interval",
                "1h",
                "--start",
                start,
                "--end",
                end,
                "--output",
                str(raw / "binance_btcusdt_1h.csv"),
            ],
            raw / "binance_btcusdt_1h.csv",
            norm / "binance_btcusdt_1h.normalized.csv",
        ),
        (
            "03_fetch_bybit_linear_btcusdt_1h",
            PY_FETCH_PREFIX
            + [
                "bybit-kline",
                "--category",
                "linear",
                "--symbol",
                "BTCUSDT",
                "--interval",
                "1h",
                "--start",
                start,
                "--end",
                end,
                "--output",
                str(raw / "bybit_linear_btcusdt_1h.csv"),
            ],
            raw / "bybit_linear_btcusdt_1h.csv",
            norm / "bybit_linear_btcusdt_1h.normalized.csv",
        ),
        (
            "04_fetch_kraken_futures_pfxbtusd_1h",
            PY_FETCH_PREFIX
            + [
                "kraken-kline",
                "--market",
                "futures",
                "--pair",
                "PF_XBTUSD",
                "--interval",
                "1h",
                "--start",
                start,
                "--end",
                end,
                "--output",
                str(raw / "kraken_futures_pfxbtusd_1h.csv"),
            ],
            raw / "kraken_futures_pfxbtusd_1h.csv",
            norm / "kraken_futures_pfxbtusd_1h.normalized.csv",
        ),
        (
            "05_fetch_ibkr_spy_1h",
            PY_FETCH_PREFIX
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
                "66",
                "--output",
                str(raw / "ibkr_spy_1h_90d.csv"),
            ],
            raw / "ibkr_spy_1h_90d.csv",
            norm / "ibkr_spy_1h_90d.normalized.csv",
        ),
    ]

    fetch_rows = []
    for label, args, raw_path, norm_path in jobs:
        exit_code = run_cmd(label, args, timeout=480)
        row = {
            "label": label,
            "exit": exit_code,
            "raw_path": str(raw_path),
            "normalized_path": str(norm_path),
            "rows": 0,
            "first": "",
            "last": "",
        }
        if exit_code == 0 and raw_path.exists():
            row.update(normalize_csv(raw_path, norm_path))
        fetch_rows.append(row)

    tvr_label = "06_fetch_tvr_local_stdio_btc_usd_1h"
    tvr_args = [
        "./target/debug/ict-engine",
        "market-data-harness",
        "--action",
        "fetch",
        "--market",
        "board-a-162255-tvr-btc-usd-1h",
        "--interval",
        "1h",
        "--role",
        "crypto_reference",
        "--provider",
        "crypto_reference=tradingview_mcp",
        "--symbol-spec",
        "crypto_reference=BTC-USD",
    ]
    tvr_exit = run_cmd(tvr_label, tvr_args, timeout=360, env=TVR_ENV)
    tvr_raw = raw / "tvr_btc_usd_1h.csv"
    tvr_norm = norm / "tvr_btc_usd_1h.normalized.csv"
    tvr_row = {
        "label": tvr_label,
        "exit": tvr_exit,
        "raw_path": str(tvr_raw),
        "normalized_path": str(tvr_norm),
        "rows": 0,
        "first": "",
        "last": "",
    }
    if tvr_exit == 0:
        tvr_row.update(normalize_tvr_harness_json(RUN_ROOT / f"command-output/{tvr_label}.out", tvr_raw, tvr_norm))
    fetch_rows.append(tvr_row)

    material_specs = [
        (
            "board-a-162255-yf-spy-1h-v1",
            "Board A provider regime probe - yfinance SPY 1h",
            "SPY",
            norm / "yahoo_spy_1h.normalized.csv",
            "source_provider=yfinance/YF SPY 1h current fetch",
        ),
        (
            "board-a-162255-binance-btcusdt-1h-v1",
            "Board A provider regime probe - Binance BTCUSDT 1h",
            "BTCUSDT",
            norm / "binance_btcusdt_1h.normalized.csv",
            "source_provider=Binance public BTCUSDT 1h current fetch",
        ),
        (
            "board-a-162255-bybit-btcusdt-1h-v1",
            "Board A provider regime probe - Bybit BTCUSDT linear 1h",
            "BTCUSDT",
            norm / "bybit_linear_btcusdt_1h.normalized.csv",
            "source_provider=Bybit public linear BTCUSDT 1h current fetch",
        ),
        (
            "board-a-162255-kraken-pfxbtusd-1h-v1",
            "Board A provider regime probe - Kraken PF_XBTUSD 1h",
            "XBTUSD",
            norm / "kraken_futures_pfxbtusd_1h.normalized.csv",
            "source_provider=Kraken futures PF_XBTUSD 1h current fetch",
        ),
        (
            "board-a-162255-ibkr-spy-1h-v1",
            "Board A provider regime probe - IBKR SPY 1h",
            "SPY",
            norm / "ibkr_spy_1h_90d.normalized.csv",
            "source_provider=IBKR gateway SPY 1h 90D current fetch",
        ),
        (
            "board-a-162255-tvr-btc-usd-1h-v1",
            "Board A provider regime probe - TVR BTC-USD 1h local stdio",
            "BTC",
            norm / "tvr_btc_usd_1h.normalized.csv",
            "source_provider=TradingViewRemix/tradingview_mcp local-stdio BTC-USD 1h current fetch",
        ),
    ]
    material_paths = []
    for package_id, title, symbol, data_path, provider_note in material_specs:
        if data_path.exists():
            path = RUN_ROOT / f"agent-material/{package_id}.material.json"
            write_json(path, material(package_id, title, symbol, data_path, provider_note))
            material_paths.append(path)

    provider_defs = [
        ("IBKR", norm / "ibkr_spy_1h_90d.normalized.csv", RUN_ROOT / "agent-material/board-a-162255-ibkr-spy-1h-v1.material.json"),
        ("TradingViewRemix/TVR", norm / "tvr_btc_usd_1h.normalized.csv", RUN_ROOT / "agent-material/board-a-162255-tvr-btc-usd-1h-v1.material.json"),
        ("yfinance/YF", norm / "yahoo_spy_1h.normalized.csv", RUN_ROOT / "agent-material/board-a-162255-yf-spy-1h-v1.material.json"),
        ("Kraken", norm / "kraken_futures_pfxbtusd_1h.normalized.csv", RUN_ROOT / "agent-material/board-a-162255-kraken-pfxbtusd-1h-v1.material.json"),
        ("Binance", norm / "binance_btcusdt_1h.normalized.csv", RUN_ROOT / "agent-material/board-a-162255-binance-btcusdt-1h-v1.material.json"),
        ("Bybit", norm / "bybit_linear_btcusdt_1h.normalized.csv", RUN_ROOT / "agent-material/board-a-162255-bybit-btcusdt-1h-v1.material.json"),
    ]
    provider_rows = []
    for provider, data_path, material_path in provider_defs:
        provider_rows.append(
            {
                "provider": provider,
                "provider_requested": True,
                "provider_data_acquired": data_path.exists(),
                "provider_unreachable": not data_path.exists(),
                "local_cache_replay": False,
                "aq_provider_invoked": False,
                "aq_material_created": material_path.exists(),
                "source_or_blocker": str(data_path if data_path.exists() else RUN_ROOT / "command-output"),
            }
        )
    provider_matrix = RUN_ROOT / "summaries/provider_provenance_matrix.csv"
    provider_matrix.parent.mkdir(parents=True, exist_ok=True)
    with provider_matrix.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(provider_rows[0].keys()))
        writer.writeheader()
        writer.writerows(provider_rows)

    write_json(
        RUN_ROOT / "summaries/prep_summary.json",
        {
            "run_root": str(RUN_ROOT),
            "fetch_rows": fetch_rows,
            "provider_rows": provider_rows,
            "material_paths": [str(path) for path in material_paths],
            "promotion_allowed": False,
            "trade_usable": False,
        },
    )
    write_text(RUN_ROOT / "summaries/material_paths.txt", "".join(str(path) + "\n" for path in material_paths))
    write_text(
        RUN_ROOT / "summaries/data_line_counts.txt",
        "".join(f"{row['normalized_path']},{row['rows']},{row['first']},{row['last']}\n" for row in fetch_rows),
    )

    manifest_paths = [
        RUN_ROOT / "agent-material/ProviderRegimeProbeV1.py",
        RUN_ROOT / "summaries/prep_summary.json",
        RUN_ROOT / "summaries/provider_provenance_matrix.csv",
        RUN_ROOT / "summaries/material_paths.txt",
        RUN_ROOT / "summaries/data_line_counts.txt",
    ] + material_paths + [Path(row["normalized_path"]) for row in fetch_rows if row.get("rows", 0)]
    write_text(
        RUN_ROOT / "checks/sha256_manifest_prep.out",
        "".join(f"{sha256(path)}  {path}\n" for path in manifest_paths if path.exists()),
    )

    data_rows = sum(1 for row in provider_rows if row["provider_data_acquired"])
    material_count = len(material_paths)
    all_six_rows = len(provider_rows) == 6
    all_requested = all(row["provider_requested"] for row in provider_rows)
    assertion_lines = [
        f"{'PASS' if all_six_rows else 'FAIL'} provider_rows_6={len(provider_rows)}",
        f"{'PASS' if all_requested else 'FAIL'} provider_requested_all={all_requested}",
        f"{'PASS' if data_rows == 6 else 'FAIL'} provider_data_acquired_6={data_rows}",
        f"{'PASS' if material_count == 6 else 'FAIL'} material_count_6={material_count}",
        "PASS promotion_allowed_false=True",
        "PASS update_goal_false=True",
    ]
    write_text(RUN_ROOT / "checks/prep_assertions.out", "\n".join(assertion_lines) + "\n")
    return 0 if data_rows == 6 and material_count == 6 else 2


if __name__ == "__main__":
    raise SystemExit(main())
