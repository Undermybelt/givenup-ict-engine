from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TIMESTAMP_KEYS = ("timestamp", "time", "datetime", "ts_event", "date", "ts")
OPEN_KEYS = ("open", "o")
HIGH_KEYS = ("high", "h")
LOW_KEYS = ("low", "l")
CLOSE_KEYS = ("close", "c")
VOLUME_KEYS = ("volume", "v")


def _normalized_key(value: str) -> str:
    return value.strip().lower()


def _first_present(mapping: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    raise ValueError(f"missing required field from {keys}")


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, (int, float)):
        raw = float(value)
        return _datetime_from_numeric(raw)

    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("timestamp must not be empty")
        try:
            return _datetime_from_numeric(float(trimmed))
        except ValueError:
            pass
        normalized = trimmed.replace("Z", "+00:00") if trimmed.endswith("Z") else trimmed
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    raise ValueError(f"unsupported timestamp value: {value!r}")


def _datetime_from_numeric(value: float) -> datetime:
    seconds = value / 1000.0 if abs(value) >= 1_000_000_000_000 else value
    return datetime.fromtimestamp(seconds, tz=timezone.utc)


def _parse_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return float(value)


def _normalize_row(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        normalized = {_normalized_key(key): value for key, value in row.items()}
        return {
            "timestamp": _parse_timestamp(_first_present(normalized, TIMESTAMP_KEYS)),
            "open": _parse_optional_float(_first_present(normalized, OPEN_KEYS)),
            "high": _parse_optional_float(_first_present(normalized, HIGH_KEYS)),
            "low": _parse_optional_float(_first_present(normalized, LOW_KEYS)),
            "close": _parse_optional_float(_first_present(normalized, CLOSE_KEYS)),
            "volume": _parse_optional_float(normalized.get("volume", normalized.get("v"))),
        }

    if isinstance(row, list):
        if len(row) < 5:
            raise ValueError("row list must contain at least timestamp/open/high/low/close")
        volume = row[5] if len(row) > 5 else None
        return {
            "timestamp": _parse_timestamp(row[0]),
            "open": _parse_optional_float(row[1]),
            "high": _parse_optional_float(row[2]),
            "low": _parse_optional_float(row[3]),
            "close": _parse_optional_float(row[4]),
            "volume": _parse_optional_float(volume),
        }

    raise ValueError(f"unsupported row shape: {type(row)!r}")


def _unwrap_json_rows(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if isinstance(payload.get("candles"), list):
            return payload["candles"]
        if isinstance(payload.get("data"), list):
            return payload["data"]
        if isinstance(payload.get("rows"), list):
            return payload["rows"]
        result = payload.get("result")
        if isinstance(result, dict) and isinstance(result.get("list"), list):
            return result["list"]
    raise ValueError("JSON input must be a list or an object with candles/data/rows/result.list")


def _load_rows(path: Path, input_format: str) -> list[Any]:
    format_name = input_format if input_format != "auto" else _infer_input_format(path)
    if format_name == "csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    if format_name == "json":
        return _unwrap_json_rows(json.loads(path.read_text(encoding="utf-8")))
    if format_name == "parquet":
        try:
            import polars as pl
        except ModuleNotFoundError as exc:
            raise ValueError(
                "parquet input requires polars to be installed in this opt-in lane"
            ) from exc
        return pl.read_parquet(path).to_dicts()
    raise ValueError(f"unsupported input format '{format_name}'")


def _infer_input_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".parquet":
        return "parquet"
    return "json"


def normalize_rows(rows: list[Any]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        normalized = _normalize_row(row)
        key = normalized["timestamp"].isoformat()
        deduped[key] = normalized
    return [deduped[key] for key in sorted(deduped)]


def render_candle_payload(symbol: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "candles": [
            {
                "timestamp": row["timestamp"].isoformat().replace("+00:00", "Z"),
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"],
            }
            for row in rows
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize external OHLCV into ict-engine candle JSON."
    )
    parser.add_argument("--input", required=True, help="Input CSV, JSON, or parquet file.")
    parser.add_argument("--output", required=True, help="Output candle JSON path.")
    parser.add_argument("--symbol", required=True, help="Symbol to stamp into the output payload.")
    parser.add_argument(
        "--input-format",
        default="auto",
        choices=["auto", "csv", "json", "parquet"],
        help="Explicit input format override.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    rows = normalize_rows(_load_rows(input_path, args.input_format))
    payload = render_candle_payload(args.symbol, rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "symbol": args.symbol,
                "rows": len(rows),
                "input": str(input_path),
                "output": str(output_path),
                "input_format": args.input_format,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
