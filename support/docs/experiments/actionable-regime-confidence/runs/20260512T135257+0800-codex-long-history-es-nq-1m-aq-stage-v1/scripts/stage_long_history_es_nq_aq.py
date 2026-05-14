#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd


RUN_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = RUN_ROOT / "workspace" / "auto-quant"
DATA_DIR = WORKSPACE / "user_data" / "data"
STRATEGY_DIR = WORKSPACE / "user_data" / "strategies_external"
SOURCE_AQ = Path("/Users/thrill3r/Auto-Quant")
SOURCE_DATA = Path("/Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf/cleaned-1m")
TIMEFRAMES = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "1h": "1h",
    "4h": "4h",
    "1d": "1D",
}
MARKETS = {
    "NQ": {
        "pair": "NQ/USD",
        "source": SOURCE_DATA / "nq.continuous-1m.json",
    },
    "ES": {
        "pair": "ES/USD",
        "source": SOURCE_DATA / "es.continuous-1m.json",
    },
}


def load_candles(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text())
    df = pd.DataFrame(payload["candles"])
    df["date"] = pd.to_datetime(df["timestamp"], utc=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["date", "open", "high", "low", "close"])
    df["volume"] = df["volume"].fillna(0.0)
    df = df.sort_values("date").drop_duplicates(subset=["date"], keep="first")
    return df[["date", "open", "high", "low", "close", "volume"]].reset_index(drop=True)


def resample(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    if timeframe == "1m":
        return df.copy()
    rule = TIMEFRAMES[timeframe]
    out = (
        df.set_index("date")
        .resample(rule, label="left", closed="left")
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        .dropna(subset=["open", "high", "low", "close"])
        .reset_index()
    )
    return out[["date", "open", "high", "low", "close", "volume"]]


def write_feather(df: pd.DataFrame, pair: str, timeframe: str) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    out["date"] = (out["date"].astype("int64") // 1_000_000).astype("int64")
    filename = f"{pair.replace('/', '_')}-{timeframe}.feather"
    path = DATA_DIR / filename
    out.to_feather(path)
    return path


def copy_runtime_files() -> None:
    shutil.copy2(SOURCE_AQ / "run_tomac.py", WORKSPACE / "run_tomac.py")
    shutil.copy2(
        SOURCE_AQ / "user_data" / "strategies_external" / "TomacNQ_KillzoneBreakout.py",
        STRATEGY_DIR / "TomacNQ_KillzoneBreakout.py",
    )
    config = json.loads((SOURCE_AQ / "config.tomac.json").read_text())
    config["exchange"]["pair_whitelist"] = [spec["pair"] for spec in MARKETS.values()]
    config["timeframe"] = "1h"
    config["timerange"] = "20120701-20251231"
    config["max_open_trades"] = 2
    (WORKSPACE / "config.tomac.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")


def main() -> int:
    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    copy_runtime_files()

    rows = []
    for market, spec in MARKETS.items():
        base = load_candles(spec["source"])
        for timeframe in TIMEFRAMES:
            frame = resample(base, timeframe)
            out_path = write_feather(frame, spec["pair"], timeframe)
            rows.append(
                {
                    "market": market,
                    "pair": spec["pair"],
                    "timeframe": timeframe,
                    "rows": int(len(frame)),
                    "start": frame["date"].min().isoformat() if not frame.empty else None,
                    "end": frame["date"].max().isoformat() if not frame.empty else None,
                    "source": str(spec["source"]),
                    "output": str(out_path),
                }
            )

    manifest = {
        "run_root": str(RUN_ROOT),
        "workspace": str(WORKSPACE),
        "source_auto_quant": str(SOURCE_AQ),
        "source_data_root": str(SOURCE_DATA),
        "config": str(WORKSPACE / "config.tomac.json"),
        "strategy": str(STRATEGY_DIR / "TomacNQ_KillzoneBreakout.py"),
        "timerange": "20120701-20251231",
        "timeframes": list(TIMEFRAMES),
        "rows": rows,
    }
    (RUN_ROOT / "long_history_es_nq_aq_stage_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    pd.DataFrame(rows).to_csv(RUN_ROOT / "long_history_es_nq_aq_stage_rows.csv", index=False)
    print(json.dumps({"status": "staged", "rows": rows}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
