#!/usr/bin/env python3
"""Convert Board B 220646 selected branch rows to ict-engine real-trade JSONL."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-v1"
RECIPE_ID = "SourceRootStopCarryLongHorizonV1"
SYMBOL = "SRCROOT_STOP_CARRY_LONG_220646"
WIRE_SCHEMA_VERSION = "board-b-real-trades-wire/v1"

HERE = Path(__file__).resolve().parent
RUN_ROOT = HERE.parent
INPUT_CSV = RUN_ROOT / "branch-rc-spa" / "source_root_stop_carry_longhorizon_selected_rows_v1.csv"
OUTPUT_JSONL = HERE / "source_root_stop_carry_longhorizon_real_trades_wire_v1.jsonl"
SAMPLE_JSON = HERE / "source_root_stop_carry_longhorizon_real_trades_wire_v1.sample.json"
COUNT_FILE = HERE / "source_root_stop_carry_longhorizon_real_trades_wire_v1.count"


def parse_ts_ms(value: str) -> int:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def to_float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key) or default)
    except ValueError:
        return default


def confidence(row: dict[str, str]) -> float:
    values = [
        to_float(row, "parent_regime_confidence_floor", 0.0),
        to_float(row, "source_ticker_confidence", 0.0),
    ]
    return max([value for value in values if value > 0.0], default=0.5)


def factor_direction_for_root(root: str) -> str:
    if root == "Bull":
        return "Bull"
    if root in {"Bear", "Crisis"}:
        return "Bear"
    return "Neutral"


def factor_direction_for_pnl(pnl: float) -> str:
    if pnl > 0:
        return "Bull"
    if pnl < 0:
        return "Bear"
    return "Neutral"


def record_from_row(row: dict[str, str]) -> dict[str, Any]:
    pnl = to_float(row, "profit_ratio_net")
    root = row["parent_regime_root"]
    conf = confidence(row)
    branch_path = row["regime_profit_branch_path"]
    trade_id = row["trade_id"]
    variant_id = row["variant_id"]
    open_date = row["open_date"]
    close_date = row.get("close_date") or open_date
    uncertainty = max(0.0, 1.0 - conf)
    direction = row.get("direction") or ("long" if to_float(row, "direction_sign") >= 0 else "short")
    return {
        "schema_version": WIRE_SCHEMA_VERSION,
        "symbol": SYMBOL,
        "trade_id": trade_id,
        "strategy_name": RECIPE_ID,
        "strategy_mutation_id": variant_id,
        "auto_quant_run_id": RUN_ID,
        "open_ts_ms": parse_ts_ms(open_date),
        "close_ts_ms": parse_ts_ms(close_date),
        "direction": direction,
        "pnl": pnl,
        "regime_at_entry": root,
        "entry_signal": variant_id,
        "factors_used": [
            {
                "factor_name": "market_regime_context.root",
                "category": "regime_context",
                "direction": factor_direction_for_root(root),
                "value": conf,
                "confidence": conf,
                "weighted_score": conf,
                "uncertainty_contribution": uncertainty,
            },
            {
                "factor_name": "regime_profit_branch_path",
                "category": "branch_path",
                "direction": factor_direction_for_pnl(pnl),
                "value": pnl,
                "confidence": conf,
                "weighted_score": pnl,
                "uncertainty_contribution": uncertainty,
            },
        ],
        "structural_feedback": {
            "protocol_version": row["regime_profit_branch_path_version"],
            "recommendation_id": trade_id,
            "recommended_at": open_date,
            "node_id": root,
            "branch_id": branch_path,
            "scenario_id": row.get("sub_regime_tags") or root,
            "path_id": branch_path,
            "followed_path": True,
            "exit_reason": row.get("exit_reason") or None,
            "notes": (
                "board_b_220646_branch_rc_spa_passed;"
                f"variant={variant_id};horizon={row.get('trade_or_bar_horizon', '')};"
                f"action={row.get('allowed_action', '')}"
            ),
        },
    }


def main() -> int:
    HERE.mkdir(parents=True, exist_ok=True)
    with INPUT_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    records = [record_from_row(row) for row in rows if row.get("parent_regime_root") in {"Bull", "Bear", "Sideways", "Crisis"}]
    with OUTPUT_JSONL.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
    if records:
        SAMPLE_JSON.write_text(json.dumps(records[0], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    COUNT_FILE.write_text(f"{len(records)}\n", encoding="utf-8")
    print(json.dumps({"input_rows": len(rows), "wire_records": len(records), "output": str(OUTPUT_JSONL)}, indent=2, sort_keys=True))
    return 0 if records else 1


if __name__ == "__main__":
    raise SystemExit(main())
