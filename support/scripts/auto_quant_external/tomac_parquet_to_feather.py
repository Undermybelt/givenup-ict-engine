#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "volume"]
TIME_COLUMN_CANDIDATES = ("date", "datetime", "timestamp", "time", "ts_event", "ts")
SESSION_SCOPE = "ETH/full_retained_session"
RTH_FILTER_APPLIED = False
SYMBOL_ALIASES = {"XAU": "GC"}


def parse_csv_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def canonical_symbol(symbol: str) -> str:
    requested = str(symbol).upper().strip()
    return SYMBOL_ALIASES.get(requested, requested)


def canonical_symbol_sequence(symbols: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    canonical_symbols: list[str] = []
    aliases: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw_symbol in symbols:
        requested = str(raw_symbol).upper().strip()
        if not requested:
            continue
        canonical = canonical_symbol(requested)
        if requested != canonical:
            aliases.append({"requested": requested, "canonical": canonical})
        if canonical not in seen:
            canonical_symbols.append(canonical)
            seen.add(canonical)
    return canonical_symbols, aliases


def source_path_candidates(cache_root: Path, symbol: str, timeframe: str) -> list[Path]:
    requested = str(symbol).upper().strip()
    canonical = canonical_symbol(requested)
    candidates = [cache_root / f"{canonical}_{timeframe}.parquet"]
    if requested and requested != canonical:
        candidates.append(cache_root / f"{requested}_{timeframe}.parquet")
    return candidates


def source_path(cache_root: Path, symbol: str, timeframe: str) -> Path:
    return source_path_candidates(cache_root, symbol, timeframe)[0]


def output_path(output_dir: Path, symbol: str, timeframe: str, quote: str, futures: bool) -> Path:
    pair_stem = f"{canonical_symbol(symbol)}_{quote.upper()}"
    if futures:
        return output_dir / "futures" / f"{pair_stem}-{timeframe}-futures.feather"
    return output_dir / f"{pair_stem}-{timeframe}.feather"


def normalize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    rename: dict[str, str] = {}
    lower_to_original = {column.lower(): column for column in frame.columns}
    for candidate in TIME_COLUMN_CANDIDATES:
        if candidate in lower_to_original:
            rename[lower_to_original[candidate]] = "date"
            break
    for column in ("open", "high", "low", "close", "volume"):
        if column in lower_to_original:
            rename[lower_to_original[column]] = column
    normalized = frame.rename(columns=rename)
    missing = [column for column in REQUIRED_COLUMNS if column not in normalized.columns]
    if missing:
        raise ValueError(f"parquet input missing required columns after normalization: {missing}")
    normalized = normalized[REQUIRED_COLUMNS].copy()
    normalized["date"] = pd.to_datetime(normalized["date"], utc=True, errors="coerce")
    before = len(normalized)
    normalized = normalized.dropna(subset=["date", "open", "high", "low", "close"])
    if normalized.empty:
        raise ValueError(f"no valid OHLC rows after dropping invalid values from {before} rows")
    normalized["volume"] = pd.to_numeric(normalized["volume"], errors="coerce").fillna(0.0)
    for column in ("open", "high", "low", "close"):
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    normalized = normalized.dropna(subset=["open", "high", "low", "close"])
    normalized = normalized.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    return normalized.reset_index(drop=True)


def convert_one(
    *,
    cache_root: Path,
    output_dir: Path,
    symbol: str,
    timeframe: str,
    quote: str = "USD",
    futures: bool = True,
) -> dict[str, Any]:
    requested_symbol = str(symbol).upper().strip()
    canonical = canonical_symbol(requested_symbol)
    source_candidates = source_path_candidates(cache_root, requested_symbol, timeframe)
    src = next((candidate for candidate in source_candidates if candidate.exists()), source_candidates[0])
    if not src.exists():
        tried = ", ".join(str(candidate) for candidate in source_candidates)
        raise FileNotFoundError(f"missing TOMAC parquet cache for {canonical} {timeframe}; tried: {tried}")
    frame = normalize_frame(pd.read_parquet(src))
    target = output_path(output_dir, canonical, timeframe, quote, futures)
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.to_feather(target)
    result = {
        "symbol": canonical,
        "timeframe": timeframe,
        "source": str(src),
        "output": str(target),
        "rows": int(len(frame)),
        "start": frame["date"].min().isoformat(),
        "end": frame["date"].max().isoformat(),
        "columns": REQUIRED_COLUMNS,
        "format": "freqtrade_feather",
        "trading_mode": "futures" if futures else "spot",
        "session_scope": SESSION_SCOPE,
        "rth_filter_applied": RTH_FILTER_APPLIED,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    if requested_symbol != canonical:
        result["raw_requested_symbol"] = requested_symbol
        result["legacy_symbol_alias"] = requested_symbol
    return result


def convert_cache(
    *,
    cache_root: Path,
    output_dir: Path,
    symbols: list[str],
    timeframes: list[str],
    quote: str = "USD",
    futures: bool = True,
) -> dict[str, Any]:
    canonical_symbols, symbol_aliases = canonical_symbol_sequence(symbols)
    outputs = []
    seen: set[str] = set()
    for symbol in symbols:
        canonical = canonical_symbol(symbol)
        if canonical in seen:
            continue
        seen.add(canonical)
        for timeframe in timeframes:
            outputs.append(
                convert_one(
                    cache_root=cache_root,
                    output_dir=output_dir,
                    symbol=symbol,
                    timeframe=timeframe,
                    quote=quote,
                    futures=futures,
                )
            )
    return {
        "ok": True,
        "cache_root": str(cache_root),
        "output_dir": str(output_dir),
        "raw_requested_symbols": [symbol.upper() for symbol in symbols],
        "symbols": canonical_symbols,
        "symbol_aliases": symbol_aliases,
        "timeframes": timeframes,
        "quote": quote.upper(),
        "futures": futures,
        "converted_count": len(outputs),
        "outputs": outputs,
        "session_scope": SESSION_SCOPE,
        "rth_filter_applied": RTH_FILTER_APPLIED,
        "decision": "aq_feather_staged_from_tomac_parquet_cache_no_backtest_launched",
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert local TOMAC parquet cache files into Auto-Quant/FreqTrade feather files."
    )
    parser.add_argument("--cache-root", required=True, help="Directory containing <SYMBOL>_<TIMEFRAME>.parquet files.")
    parser.add_argument("--output-dir", required=True, help="Auto-Quant user_data/data destination directory.")
    parser.add_argument("--symbols", required=True, help="Comma-separated symbols, e.g. NQ,YM,GC. Legacy XAU aliases to GC.")
    parser.add_argument("--timeframes", required=True, help="Comma-separated timeframes, e.g. 5m,15m,30m,1h,4h,1d.")
    parser.add_argument("--quote", default="USD", help="Synthetic quote currency for pair filenames; default USD.")
    parser.add_argument("--spot", action="store_true", help="Write spot-style feathers instead of futures-style feathers.")
    parser.add_argument("--summary-json", default="", help="Optional path to write the conversion summary JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = convert_cache(
        cache_root=Path(args.cache_root).expanduser().resolve(),
        output_dir=Path(args.output_dir).expanduser().resolve(),
        symbols=parse_csv_list(args.symbols),
        timeframes=parse_csv_list(args.timeframes),
        quote=args.quote,
        futures=not args.spot,
    )
    if args.summary_json:
        summary_path = Path(args.summary_json).expanduser().resolve()
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
