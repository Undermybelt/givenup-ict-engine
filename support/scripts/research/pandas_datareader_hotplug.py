#!/usr/bin/env python3
"""Optional pandas-datareader bridge for consumer-safe ict-engine data intake.

The script is zero-config: capability and demo modes need only the Python stdlib.
Live external fetches require an explicit --source and an installed pandas-datareader.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Any, Iterable

VERSION = 1
SUPPORTED_SOURCES = {
    "fred": {
        "asset_class": "macro",
        "requires_api_key": False,
        "interval_support": ["daily", "weekly", "monthly"],
        "freshness": "historical",
        "runtime_input_mode": "observation_context",
    },
    "famafrench": {
        "asset_class": "style_factor",
        "requires_api_key": False,
        "interval_support": ["daily", "weekly", "monthly"],
        "freshness": "historical",
        "runtime_input_mode": "diagnostic_context",
    },
    "stooq": {
        "asset_class": "reference_ohlcv",
        "requires_api_key": False,
        "interval_support": ["daily"],
        "freshness": "delayed_or_historical",
        "runtime_input_mode": "optional_backfill",
    },
    "yahoo-actions": {
        "asset_class": "corporate_action",
        "requires_api_key": False,
        "interval_support": ["event_series"],
        "freshness": "historical",
        "runtime_input_mode": "adjustment_check",
    },
}
PERSONAL_DEFAULTS = {
    "macro_regime_rates": {"source": "fred", "symbols": ["DGS10", "DGS2", "FEDFUNDS"]},
    "macro_vol_credit": {"source": "fred", "symbols": ["VIXCLS", "BAMLH0A0HYM2"]},
    "equity_style_factors": {"source": "famafrench", "symbols": ["F-F_Research_Data_Factors"]},
    "reference_ohlcv": {"source": "stooq", "symbols": ["SPY", "QQQ", "TLT", "GLD", "USO"]},
    "corporate_actions": {"source": "yahoo-actions", "symbols": ["SPY", "QQQ"]},
}
DEMO_ROWS = [
    {"date": "2026-01-02", "symbol": "DEMO", "open": 100.0, "high": 101.2, "low": 99.7, "close": 100.8, "volume": 1200000},
    {"date": "2026-01-05", "symbol": "DEMO", "open": 100.9, "high": 102.0, "low": 100.1, "close": 101.7, "volume": 1350000},
    {"date": "2026-01-06", "symbol": "DEMO", "open": 101.5, "high": 103.1, "low": 101.0, "close": 102.6, "volume": 1420000},
]


def compact_error(category: str, message: str, retryable: bool = False) -> dict[str, Any]:
    return {"category": category, "message": message, "retryable": retryable}


def capability_bundle() -> dict[str, Any]:
    return {
        "ok": True,
        "bridge": "pandas_datareader_hotplug",
        "version": VERSION,
        "zero_config": True,
        "trade_usable": False,
        "default_runtime": "disabled_until_user_opt_in",
        "sources": SUPPORTED_SOURCES,
        "personal_default_sets": PERSONAL_DEFAULTS,
        "pollution_policy": "stdout_or_explicit_output_path_only",
        "install_hint": "python -m pip install pandas-datareader",
    }


def dataframe_to_records(frame: Any, limit: int) -> list[dict[str, Any]]:
    reset = frame.reset_index()
    records: list[dict[str, Any]] = []
    for raw in reset.tail(limit).to_dict(orient="records"):
        row: dict[str, Any] = {}
        for key, value in raw.items():
            label = str(key)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            elif hasattr(value, "item"):
                value = value.item()
            row[label] = value
        records.append(row)
    return records


def normalize_csv_records(rows: Iterable[dict[str, Any]], limit: int) -> str:
    rows = list(rows)[-limit:]
    if not rows:
        return ""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def demo_bundle(limit: int) -> dict[str, Any]:
    rows = DEMO_ROWS[-limit:]
    return {
        "ok": True,
        "bridge": "pandas_datareader_hotplug",
        "source": "demo",
        "symbol": "DEMO",
        "trade_usable": False,
        "data_grade": "fixture_only",
        "provenance": {
            "provider": "embedded_demo_fixture",
            "network": False,
            "dependency_required": False,
        },
        "capability": capability_bundle(),
        "row_count": len(rows),
        "records": rows,
    }


def load_datareader() -> Any:
    try:
        from pandas_datareader import data as web  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "pandas-datareader is not installed; use --capabilities/--demo for zero-config, "
            "or install with: python -m pip install pandas-datareader"
        ) from exc
    return web


def fetch_source(args: argparse.Namespace) -> dict[str, Any]:
    if args.source not in SUPPORTED_SOURCES:
        return {
            "ok": False,
            "bridge": "pandas_datareader_hotplug",
            "error": compact_error("validation", f"unsupported source: {args.source}"),
            "capability": capability_bundle(),
        }
    if not args.symbol:
        return {
            "ok": False,
            "bridge": "pandas_datareader_hotplug",
            "error": compact_error("validation", "--symbol is required for fetch mode"),
            "capability": capability_bundle(),
        }
    try:
        web = load_datareader()
        start = args.start or (date.today() - timedelta(days=args.days)).isoformat()
        end = args.end or date.today().isoformat()
        frame = web.DataReader(
            args.symbol,
            args.source,
            start=start,
            end=end,
            retry_count=args.retry_count,
            pause=args.pause,
        )
        if isinstance(frame, dict):
            records = {
                str(key): dataframe_to_records(value, args.limit)
                for key, value in frame.items()
                if hasattr(value, "reset_index")
            }
            row_count = sum(len(value) for value in records.values())
        else:
            records = dataframe_to_records(frame, args.limit)
            row_count = len(records)
        return {
            "ok": True,
            "bridge": "pandas_datareader_hotplug",
            "source": args.source,
            "symbol": args.symbol,
            "start": start,
            "end": end,
            "trade_usable": False,
            "data_grade": "observation_or_backtest_reference",
            "capability": SUPPORTED_SOURCES[args.source],
            "provenance": {
                "provider": "pandas-datareader",
                "network": True,
                "dependency_required": True,
                "fetched_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            },
            "row_count": row_count,
            "records": records,
        }
    except RuntimeError as exc:
        return {
            "ok": False,
            "bridge": "pandas_datareader_hotplug",
            "source": args.source,
            "symbol": args.symbol,
            "trade_usable": False,
            "error": compact_error("config", str(exc), retryable=False),
            "capability": capability_bundle(),
        }
    except Exception as exc:  # pragma: no cover - depends on external provider behavior
        message = str(exc)
        category = "rate_limit" if "429" in message or "rate" in message.lower() else "api"
        return {
            "ok": False,
            "bridge": "pandas_datareader_hotplug",
            "source": args.source,
            "symbol": args.symbol,
            "trade_usable": False,
            "error": compact_error(category, message, retryable=True),
            "capability": SUPPORTED_SOURCES[args.source],
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capabilities", action="store_true", help="print supported optional sources")
    parser.add_argument("--demo", action="store_true", help="print embedded zero-config fixture")
    parser.add_argument("--source", choices=sorted(SUPPORTED_SOURCES), help="explicit pandas-datareader source")
    parser.add_argument("--symbol", help="provider symbol or dataset id")
    parser.add_argument("--start", help="inclusive start date YYYY-MM-DD")
    parser.add_argument("--end", help="inclusive end date YYYY-MM-DD")
    parser.add_argument("--days", type=int, default=365, help="lookback if --start omitted")
    parser.add_argument("--limit", type=int, default=20, help="max trailing rows to emit")
    parser.add_argument("--retry-count", type=int, default=2)
    parser.add_argument("--pause", type=float, default=0.25)
    parser.add_argument("--output", help="optional JSON output path; stdout is always compact JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.capabilities:
        payload = capability_bundle()
    elif args.demo:
        payload = demo_bundle(args.limit)
    else:
        payload = fetch_source(args)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(text)
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
