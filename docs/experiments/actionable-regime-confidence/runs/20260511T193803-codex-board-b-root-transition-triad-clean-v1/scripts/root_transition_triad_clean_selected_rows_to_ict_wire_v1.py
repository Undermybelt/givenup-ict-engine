#!/usr/bin/env python3
"""Convert clean RootTransitionTriad selected rows to ict-engine wire JSONL.

This is a run-local diagnostic artifact for dry-run fail-closed readback after
Board B RC-SPA rejection. It does not mutate ict-engine state by itself.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T193803+0800-codex-board-b-root-transition-triad-clean-v1"
RECIPE_ID = "RootTransitionTriadV1"
SYMBOL = "ROOT_TRIAD_CLEAN_193803_SELECTED"
SCHEMA_VERSION = "1.0"

HERE = Path(__file__).resolve().parent
RUN_ROOT = HERE.parent
INPUT_CSV = RUN_ROOT / "branch-rc-spa" / "root_transition_triad_selected_rows_v1.csv"
OUTPUT_JSONL = RUN_ROOT / "ict-engine-fail-closed" / "root_transition_triad_clean_real_trades_wire_v1.jsonl"
COUNT_FILE = RUN_ROOT / "ict-engine-fail-closed" / "root_transition_triad_clean_real_trades_wire_v1.count"
SAMPLE_JSON = RUN_ROOT / "ict-engine-fail-closed" / "root_transition_triad_clean_real_trades_wire_v1.sample.json"


def parse_ts_ms(value: str) -> int:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def factor_direction_for_root(root: str) -> str:
    if root == "Bull":
        return "Bull"
    if root in {"Bear", "Crisis"}:
        return "Bear"
    return "Neutral"


def factor_direction_for_pnl(pnl: float) -> str:
    if pnl > 0.0:
        return "Bull"
    if pnl < 0.0:
        return "Bear"
    return "Neutral"


def confidence(row: dict[str, str]) -> float:
    for key in ("source_ticker_confidence", "parent_regime_confidence_floor"):
        try:
            value = float(row.get(key) or 0.0)
        except ValueError:
            value = 0.0
        if value > 0.0:
            return value
    return 0.5


def record_from_row(row: dict[str, str], idx: int, total: int) -> dict[str, Any]:
    pnl = float(row["profit_ratio_net"])
    root = row["parent_regime_root"]
    conf = confidence(row)
    uncertainty = max(0.0, 1.0 - conf)
    variant_id = row["variant_id"]
    branch_path = row["regime_profit_branch_path"]
    direction = row.get("direction") or "long"
    trade_id = row.get("trade_id") or (
        f"{RECIPE_ID}|{variant_id}|{row['market']}|{row['timeframe']}|{row['open_date']}|{idx}"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "symbol": SYMBOL,
        "trade_id": trade_id,
        "strategy_name": RECIPE_ID,
        "strategy_mutation_id": f"board-b-root-transition-triad-clean-{variant_id}",
        "auto_quant_run_id": RUN_ID,
        "open_ts_ms": parse_ts_ms(row["open_date"]),
        "close_ts_ms": parse_ts_ms(row.get("close_date") or row["open_date"]),
        "direction": direction,
        "pnl": pnl,
        "realized_outcome": "win" if pnl > 0.0 else "loss",
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
            {
                "factor_name": row.get("profit_factor_leaf") or variant_id,
                "category": row.get("profit_factor_family") or "root_transition_price_action",
                "direction": factor_direction_for_pnl(pnl),
                "value": pnl,
                "confidence": 0.60,
                "weighted_score": pnl,
                "uncertainty_contribution": 0.40,
            },
        ],
        "structural_feedback": {
            "protocol_version": row.get("regime_profit_branch_path_version") or "board-b-root-transition-triad/v1",
            "recommendation_id": trade_id,
            "recommended_at": row["open_date"],
            "symbol": SYMBOL,
            "node_id": root,
            "branch_id": branch_path,
            "scenario_id": row.get("sub_regime_tags") or root,
            "path_id": branch_path,
            "direction": direction,
            "entry_style": variant_id,
            "candidate_set_id": RUN_ID,
            "candidate_set_size": total,
            "followed_path": True,
            "realized_outcome": "win" if pnl > 0.0 else "loss",
            "realized_pnl": pnl,
            "exit_reason": row.get("exit_reason") or None,
            "notes": "diagnostic_dry_run_only_root_transition_triad_clean_rc_spa_rejected",
        },
    }


def main() -> int:
    with INPUT_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    records = [record_from_row(row, idx, len(rows)) for idx, row in enumerate(rows, start=1)]
    with OUTPUT_JSONL.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
    COUNT_FILE.write_text(f"{len(records)}\n", encoding="utf-8")
    if records:
        SAMPLE_JSON.write_text(json.dumps(records[0], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "records": len(records), "output": str(OUTPUT_JSONL)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
