#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_time(value: str) -> str:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "").strip()
    if value == "":
        raise ValueError(f"missing {key}")
    return float(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--timeframe", required=True)
    parser.add_argument("--source-command", required=True)
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    rows = []
    with in_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamp = parse_time(row.get("date") or row.get("timestamp") or row.get("time") or "")
            rows.append(
                {
                    "timestamp": timestamp,
                    "open": parse_float(row, "open"),
                    "high": parse_float(row, "high"),
                    "low": parse_float(row, "low"),
                    "close": parse_float(row, "close"),
                    "volume": parse_float(row, "volume") if row.get("volume", "").strip() else 0.0,
                }
            )

    rows.sort(key=lambda item: item["timestamp"])
    deduped = []
    seen = set()
    for row in rows:
        if row["timestamp"] in seen:
            continue
        seen.add(row["timestamp"])
        deduped.append(row)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(deduped, indent=2) + "\n")
    provenance = {
        "provider": args.provider,
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "source_csv": str(in_path),
        "output_json": str(out_path),
        "source_command": args.source_command,
        "row_count": len(deduped),
        "first_timestamp": deduped[0]["timestamp"] if deduped else None,
        "last_timestamp": deduped[-1]["timestamp"] if deduped else None,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    out_path.with_suffix(out_path.suffix + ".provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n"
    )
    print(json.dumps(provenance, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
