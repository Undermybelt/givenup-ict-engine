from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


TIMEFRAMES = ("1m", "5m", "15m", "1h", "4h", "1d")


def pair_filename(pair: str) -> str:
    return pair.replace("/", "_").replace(":", "_")


def load_candles(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text())
    candles = payload.get("candles", [])
    if not candles:
        raise ValueError(f"no candles in {path}")
    df = pd.DataFrame(candles)
    rename = {"timestamp": "date"}
    df = df.rename(columns=rename)
    required = ["date", "open", "high", "low", "close", "volume"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{path} missing columns {missing}")
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="raise")
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="raise")
    df = df.sort_values("date").drop_duplicates(subset=["date"], keep="first")
    return df[required].reset_index(drop=True)


def write_feather(df: pd.DataFrame, output_dir: Path, pair: str, timeframe: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    out["date"] = (out["date"].astype("int64") // 1_000_000).astype("int64")
    path = output_dir / f"{pair_filename(pair)}-{timeframe}.feather"
    out.to_feather(path)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleaned-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--summary-json", required=True)
    parser.add_argument("--summary-csv", required=True)
    parser.add_argument("--markets", default="NQ,ES")
    args = parser.parse_args()

    cleaned_root = Path(args.cleaned_root).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    market_pairs = {
        market.strip().upper(): f"{market.strip().upper()}/USD"
        for market in args.markets.split(",")
        if market.strip()
    }

    rows: list[dict[str, object]] = []
    for market, pair in market_pairs.items():
        stem = market.lower()
        for timeframe in TIMEFRAMES:
            source = cleaned_root / f"cleaned-{timeframe}" / f"{stem}.continuous-{timeframe}.json"
            df = load_candles(source)
            out = write_feather(df, output_dir, pair, timeframe)
            rows.append(
                {
                    "market": market,
                    "pair": pair,
                    "timeframe": timeframe,
                    "source": str(source),
                    "output": str(out),
                    "rows": int(len(df)),
                    "first": df["date"].min().isoformat(),
                    "last": df["date"].max().isoformat(),
                }
            )

    summary = {
        "protocol": "long-history-cleaned-json-to-auto-quant-feather-v1",
        "cleaned_root": str(cleaned_root),
        "output_dir": str(output_dir),
        "markets": list(market_pairs),
        "timeframes": list(TIMEFRAMES),
        "rows": rows,
    }
    summary_json = Path(args.summary_json)
    summary_csv = Path(args.summary_csv)
    summary_json.write_text(json.dumps(summary, indent=2) + "\n")
    pd.DataFrame(rows).to_csv(summary_csv, index=False)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
