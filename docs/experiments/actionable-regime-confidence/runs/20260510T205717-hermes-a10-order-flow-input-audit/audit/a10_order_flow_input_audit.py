from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOTS = [
    Path("docs/experiments/actionable-regime-confidence/runs/20260510T202359-hermes-cross-market-regime-validation"),
    Path("docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search"),
    Path("docs/experiments/actionable-regime-confidence/runs/20260510T204325-hermes-a8-transition-sidecar"),
    Path("docs/experiments/actionable-regime-confidence/runs/20260510T205000-hermes-a9-tv-formula-recipes"),
    Path("docs/experiments/actionable-regime-confidence/runs/20260510T185358-codex-accepted95-full-chain/state/NQ"),
]

EXCLUDED_PARTS = {
    ".deps",
    ".venv",
    "__pycache__",
    "node_modules",
    "site-packages",
}

ACCEPTED_SUFFIXES = {".csv", ".json"}
MAX_JSON_BYTES = 50 * 1024 * 1024

OHLCV_FIELDS = {
    "open",
    "high",
    "low",
    "close",
    "volume",
    "count",
    "timestamp",
    "ts",
    "date",
    "datetime",
}

TICK_TRADE_FIELDS = {
    "tick",
    "tick_id",
    "trade_id",
    "trade_price",
    "trade_size",
    "trade_qty",
    "trade_quantity",
    "last_price",
    "last_size",
    "aggressor_side",
    "trade_side",
    "side",
    "buyer_maker",
    "is_buyer_maker",
}

SIGNED_FLOW_FIELDS = {
    "signed_trade_volume",
    "signed_volume",
    "order_flow",
    "order_flow_imbalance",
    "ofi",
    "buy_volume",
    "sell_volume",
    "taker_buy_volume",
    "taker_sell_volume",
    "taker_buy_base_volume",
    "taker_sell_base_volume",
    "buy_qty",
    "sell_qty",
}

QUOTE_FIELDS = {
    "bid",
    "ask",
    "bid_price",
    "ask_price",
    "best_bid",
    "best_ask",
    "bid_size",
    "ask_size",
    "bid_qty",
    "ask_qty",
    "spread",
}

L2_FIELDS = {
    "bid_depth",
    "ask_depth",
    "bid_size_1",
    "ask_size_1",
    "bid_size_2",
    "ask_size_2",
    "bids",
    "asks",
    "order_book",
    "orderbook",
    "book",
    "depth",
    "l2",
    "level2",
}

REQUIRED_FIELD_GROUPS = {
    "tick_or_trade": TICK_TRADE_FIELDS,
    "signed_flow": SIGNED_FLOW_FIELDS,
    "bid_ask_quote": QUOTE_FIELDS,
    "l2_depth": L2_FIELDS,
}


def norm_field(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts)


def iter_candidate_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            if root.suffix.lower() in ACCEPTED_SUFFIXES and not should_skip(root):
                files.append(root)
            continue
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or should_skip(path):
                continue
            if path.suffix.lower() in ACCEPTED_SUFFIXES:
                files.append(path)
    return sorted(set(files))


def csv_fields(path: Path) -> tuple[set[str], int, int]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return set(), 0, 0
        row_count = sum(1 for _ in reader)
    fields = {norm_field(column) for column in header if column}
    return fields, row_count, len(header)


def collect_json_keys(value: Any, keys: set[str], *, limit: int = 20000) -> None:
    if len(keys) >= limit:
        return
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(norm_field(str(key)))
            collect_json_keys(child, keys, limit=limit)
            if len(keys) >= limit:
                return
    elif isinstance(value, list):
        for child in value[:500]:
            collect_json_keys(child, keys, limit=limit)
            if len(keys) >= limit:
                return


def json_fields(path: Path) -> tuple[set[str], int | None, int | None, str | None]:
    size = path.stat().st_size
    if size > MAX_JSON_BYTES:
        return set(), None, None, f"skipped_json_over_{MAX_JSON_BYTES}_bytes"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - audit should record malformed artifacts.
        return set(), None, None, f"json_parse_error:{type(exc).__name__}"
    keys: set[str] = set()
    collect_json_keys(payload, keys)
    top_rows = len(payload) if isinstance(payload, list) else None
    return keys, top_rows, None, None


def classify(fields: set[str]) -> dict[str, list[str]]:
    return {
        group: sorted(fields & accepted)
        for group, accepted in REQUIRED_FIELD_GROUPS.items()
        if fields & accepted
    }


def verdict(fields: set[str], matches: dict[str, list[str]]) -> str:
    if fields & OHLCV_FIELDS and not matches:
        return "ohlcv_or_derived_only"
    if matches:
        if ("tick_or_trade" in matches or "signed_flow" in matches) and (
            "bid_ask_quote" in matches or "l2_depth" in matches
        ):
            return "candidate_real_order_flow_inputs"
        return "partial_microstructure_like_fields_not_sufficient"
    return "no_relevant_fields"


def audit(roots: list[Path]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    group_counts: Counter[str] = Counter()
    verdict_counts: Counter[str] = Counter()
    for path in iter_candidate_files(roots):
        if path.suffix.lower() == ".csv":
            fields, rows, cols = csv_fields(path)
            note = None
        else:
            fields, rows, cols, note = json_fields(path)
        matches = classify(fields)
        file_verdict = verdict(fields, matches)
        verdict_counts[file_verdict] += 1
        for group in matches:
            group_counts[group] += 1
        records.append(
            {
                "path": str(path),
                "suffix": path.suffix.lower(),
                "rows": rows,
                "columns": cols,
                "field_count": len(fields),
                "ohlcv_fields_present": sorted(fields & OHLCV_FIELDS),
                "required_group_matches": matches,
                "verdict": file_verdict,
                "note": note,
            }
        )

    real_candidates = [
        row for row in records if row["verdict"] == "candidate_real_order_flow_inputs"
    ]
    partial_candidates = [
        row
        for row in records
        if row["verdict"] == "partial_microstructure_like_fields_not_sufficient"
    ]
    return {
        "schema_version": "board-a-a10-order-flow-input-audit/v1",
        "objective": "Audit whether durable tick/order-flow/order-book/L2 inputs exist before A10 order-flow entropy.",
        "roots": [str(root) for root in roots],
        "excluded_parts": sorted(EXCLUDED_PARTS),
        "required_field_groups": {
            name: sorted(values) for name, values in REQUIRED_FIELD_GROUPS.items()
        },
        "file_count_scanned": len(records),
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "required_group_file_counts": dict(sorted(group_counts.items())),
        "real_order_flow_candidate_count": len(real_candidates),
        "partial_microstructure_like_file_count": len(partial_candidates),
        "decision": "missing_required_inputs" if not real_candidates else "real_inputs_available",
        "missing_required_inputs": []
        if real_candidates
        else [
            "historical bid/ask quote price and size",
            "historical L2 bid/ask depth or order-book snapshots",
            "signed trade volume or aggressor-side trade labels",
            "buy/sell volume split aligned to Board A windows",
            "durable tick/trade tape aligned to QQQ/NQ/PF_XBTUSD calibration/test windows",
        ],
        "proxy_policy": "OHLCV/count-derived pressure or scripts/research/ofi_session_sidecar.py fallback_mode=ohlcv_proxy_low_confidence is insufficient for A10 acceptance.",
        "records": records,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = audit(ROOTS)
    output_json = Path(args.output_json)
    output_csv = Path(args.output_csv)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "path",
                "suffix",
                "rows",
                "columns",
                "field_count",
                "verdict",
                "ohlcv_fields_present",
                "required_group_matches",
                "note",
            ],
        )
        writer.writeheader()
        for row in report["records"]:
            writer.writerow(
                {
                    **row,
                    "ohlcv_fields_present": ";".join(row["ohlcv_fields_present"]),
                    "required_group_matches": json.dumps(row["required_group_matches"], sort_keys=True),
                }
            )
    print(
        json.dumps(
            {
                "decision": report["decision"],
                "file_count_scanned": report["file_count_scanned"],
                "verdict_counts": report["verdict_counts"],
                "real_order_flow_candidate_count": report["real_order_flow_candidate_count"],
                "partial_microstructure_like_file_count": report["partial_microstructure_like_file_count"],
                "output_json": str(output_json),
                "output_csv": str(output_csv),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
