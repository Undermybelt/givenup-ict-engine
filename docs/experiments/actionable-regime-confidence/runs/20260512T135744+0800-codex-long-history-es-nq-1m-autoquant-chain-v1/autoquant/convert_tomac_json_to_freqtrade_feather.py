from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "user_data" / "data"
SOURCE_ROOT = Path("/Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf")
MARKETS = ("ES", "NQ")
TIMEFRAMES = ("1m", "5m", "15m", "1h", "4h", "1d")


def load_candles(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    candles = payload["candles"]
    df = pd.DataFrame(candles)
    df["date"] = pd.to_datetime(df["timestamp"], utc=True).astype("int64") // 1_000_000
    return df[["date", "open", "high", "low", "close", "volume"]].astype(
        {
            "date": "int64",
            "open": "float64",
            "high": "float64",
            "low": "float64",
            "close": "float64",
            "volume": "float64",
        }
    )


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for market in MARKETS:
        for timeframe in TIMEFRAMES:
            source = SOURCE_ROOT / f"cleaned-{timeframe}" / f"{market.lower()}.continuous-{timeframe}.json"
            output = DATA_DIR / f"{market}_USD-{timeframe}.feather"
            df = load_candles(source)
            df.to_feather(output)
            dates = pd.to_datetime(df["date"], unit="ms", utc=True)
            rows.append(
                {
                    "market": market,
                    "pair": f"{market}/USD",
                    "timeframe": timeframe,
                    "source_path": str(source),
                    "output_path": str(output),
                    "rows": len(df),
                    "first_timestamp": dates.iloc[0].isoformat(),
                    "last_timestamp": dates.iloc[-1].isoformat(),
                    "output_bytes": output.stat().st_size,
                }
            )
    manifest_csv = PROJECT_DIR.parent / "data" / "freqtrade_feather_manifest.csv"
    manifest_json = PROJECT_DIR.parent / "data" / "freqtrade_feather_manifest.json"
    manifest_csv.parent.mkdir(parents=True, exist_ok=True)
    with manifest_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    manifest_json.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"converted": len(rows), "manifest_csv": str(manifest_csv)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
