#!/usr/bin/env python3
"""Convert the 184218 Board B NQ/Tomac branch rows to ict-engine wire JSONL.

This is a run-local diagnostic artifact. It does not mutate ict-engine state;
the generated JSONL is intended for dry-run `auto-quant-ingest-real-trades`
readback after RC-SPA rejection.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T184218+0800-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1"
RECIPE_ID = "TomacNQRootAwareBranchMatrixV1"
SYMBOL = "TOMAC_NQ_BRANCH_MATRIX_184218"
SCHEMA_VERSION = "1.0"

HERE = Path(__file__).resolve().parent
RUN_ROOT = HERE.parent
INPUT_CSV = RUN_ROOT / "branch-rc-spa" / "nq_rootaware_tomac_branch_path_trades_v1.csv"
OUTPUT_JSONL = HERE / "nq_rootaware_tomac_real_trades_wire_v1.jsonl"
SAMPLE_JSON = HERE / "nq_rootaware_tomac_real_trades_wire_v1.sample.json"
COUNT_FILE = HERE / "nq_rootaware_tomac_real_trades_wire_v1.count"


def parse_ts_ms(value: str) -> int:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def factor_direction_for_root(root: str) -> str:
    if root == "Bull":
        return "Bull"
    if root == "Bear":
        return "Bear"
    return "Neutral"


def factor_direction_for_pnl(pnl: float) -> str:
    if pnl > 0:
        return "Bull"
    if pnl < 0:
        return "Bear"
    return "Neutral"


def confidence(row: dict[str, str]) -> float:
    for key in ("parent_regime_confidence_floor", "source_anchor_confidence"):
        try:
            value = float(row.get(key) or 0.0)
        except ValueError:
            value = 0.0
        if value > 0.0:
            return value
    return 0.5


def record_from_row(row: dict[str, str]) -> dict[str, Any]:
    pnl = float(row["profit_ratio_net"])
    root = row["parent_regime_root"]
    conf = confidence(row)
    side = row.get("side") or "long"
    branch_path = row["regime_profit_branch_path"]
    recommended_at = row["open_date"]
    row_id = row["row_id"]
    variant_id = row["variant_id"]
    trade_id = f"{RECIPE_ID}|{variant_id}|{row['pair']}|{recommended_at}|{row_id}"
    uncertainty = max(0.0, 1.0 - conf)
    return {
        "schema_version": SCHEMA_VERSION,
        "symbol": SYMBOL,
        "trade_id": trade_id,
        "strategy_name": row.get("strategy_class") or RECIPE_ID,
        "strategy_mutation_id": "board-b-nq-rootaware-tomac-branch-rc-spa-v1",
        "auto_quant_run_id": RUN_ID,
        "open_ts_ms": parse_ts_ms(row["open_date"]),
        "close_ts_ms": parse_ts_ms(row["close_date"] or row["open_date"]),
        "direction": side,
        "pnl": pnl,
        "regime_at_entry": root,
        "entry_signal": row.get("enter_tag") or variant_id,
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
            "recommended_at": recommended_at,
            "node_id": root,
            "branch_id": branch_path,
            "scenario_id": row.get("sub_regime_tags") or root,
            "path_id": branch_path,
            "followed_path": True,
            "exit_reason": row.get("exit_reason") or None,
            "notes": (
                "diagnostic_dry_run_only_nq_rootaware_tomac_rc_spa_rejected;"
                f"variant={variant_id};side={side}"
            ),
        },
    }


def main() -> int:
    HERE.mkdir(parents=True, exist_ok=True)
    with INPUT_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    records = [record_from_row(row) for row in rows]
    with OUTPUT_JSONL.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
    if records:
        SAMPLE_JSON.write_text(json.dumps(records[0], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    COUNT_FILE.write_text(f"{len(records)}\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "input_csv": str(INPUT_CSV),
                "output_jsonl": str(OUTPUT_JSONL),
                "records": len(records),
                "sample_json": str(SAMPLE_JSON),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
