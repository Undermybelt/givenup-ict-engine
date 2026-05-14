#!/usr/bin/env python3
"""Convert the rejected Sapienza/Binance PnL bridge rows to ict-engine wire JSONL.

The output is used only for dry-run fail-closed parsing. It deliberately picks
the best-scored horizon from the bridge report, so each source event/control is
represented once instead of duplicating all tested horizons.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T200931+0800-codex-board-b-sapienza-binance-pnl-bridge-v1"
RECIPE_ID = "SapienzaBinancePnlBridgeV1"
SYMBOL = "SAPIENZA_BINANCE_PNL_200931"
SCHEMA_VERSION = "1.0"

HERE = Path(__file__).resolve().parent
RUN_ROOT = HERE.parent
INPUT_CSV = RUN_ROOT / "sapienza-binance-pnl-bridge" / "sapienza_binance_pnl_rows_v1.csv"
REPORT_JSON = RUN_ROOT / "sapienza-binance-pnl-bridge" / "sapienza_binance_pnl_bridge_v1.json"
OUT_DIR = RUN_ROOT / "ict-engine-fail-closed"
OUTPUT_JSONL = OUT_DIR / "sapienza_binance_real_trades_wire_v1.jsonl"
COUNT_FILE = OUT_DIR / "sapienza_binance_real_trades_wire_v1.count"
SAMPLE_JSON = OUT_DIR / "sapienza_binance_real_trades_wire_v1.sample.json"


def parse_ts_ms(value: str) -> int:
    text = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def factor_direction(value: float) -> str:
    if value > 0.0:
        return "Bull"
    if value < 0.0:
        return "Bear"
    return "Neutral"


def record_from_row(row: dict[str, str], index: int, total: int) -> dict[str, Any]:
    pnl = float(row["provider_return"])
    target = int(row["target"])
    branch_path = row["regime_profit_branch_path"]
    is_positive = target == 1
    trade_id = (
        f"{RECIPE_ID}|{row['provider_symbol']}|{row['pump_index']}|"
        f"{row['event_dt']}|{row['horizon_hours']}h|{row['row_type']}|{index}"
    )
    confidence = 0.970640354706 if is_positive else 0.50
    return {
        "schema_version": SCHEMA_VERSION,
        "symbol": SYMBOL,
        "trade_id": trade_id,
        "strategy_name": RECIPE_ID,
        "strategy_mutation_id": f"board-b-sapienza-binance-{row['horizon_hours']}h",
        "auto_quant_run_id": RUN_ID,
        "open_ts_ms": parse_ts_ms(row["entry_dt"]),
        "close_ts_ms": parse_ts_ms(row["exit_dt"]),
        "direction": "long",
        "pnl": pnl,
        "realized_outcome": "win" if pnl > 0.0 else "loss",
        "regime_at_entry": "Manipulation(scoped)" if is_positive else "Control(non_event)",
        "entry_signal": row["row_type"],
        "factors_used": [
            {
                "factor_name": "market_regime_context.root",
                "category": "regime_context",
                "direction": "Neutral",
                "value": confidence,
                "confidence": confidence,
                "weighted_score": confidence,
                "uncertainty_contribution": max(0.0, 1.0 - confidence),
            },
            {
                "factor_name": "regime_profit_branch_path",
                "category": "branch_path",
                "direction": factor_direction(pnl),
                "value": pnl,
                "confidence": confidence,
                "weighted_score": pnl,
                "uncertainty_contribution": max(0.0, 1.0 - confidence),
            },
            {
                "factor_name": "SapienzaTelegramPumpDumpPositiveControl",
                "category": "direct_manipulation_provider_reconstructed_pnl",
                "direction": factor_direction(pnl),
                "value": pnl,
                "confidence": 0.60,
                "weighted_score": pnl,
                "uncertainty_contribution": 0.40,
            },
        ],
        "structural_feedback": {
            "protocol_version": "board-b-sapienza-binance-pnl-bridge/v1",
            "recommendation_id": trade_id,
            "recommended_at": row["event_dt"],
            "symbol": SYMBOL,
            "node_id": "Manipulation(scoped)" if is_positive else "Control(non_event)",
            "branch_id": branch_path,
            "scenario_id": row["row_type"],
            "path_id": branch_path,
            "direction": "long",
            "entry_style": row["bridge_precision"],
            "candidate_set_id": RUN_ID,
            "candidate_set_size": total,
            "followed_path": True,
            "realized_outcome": "win" if pnl > 0.0 else "loss",
            "realized_pnl": pnl,
            "exit_reason": None,
            "notes": "diagnostic_dry_run_only_sapienza_binance_bridge_rc_spa_rejected",
        },
    }


def main() -> int:
    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    best_horizon = str(report["best_horizon"]["horizon_hours"])
    with INPUT_CSV.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row["horizon_hours"] == best_horizon]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = [record_from_row(row, index, len(rows)) for index, row in enumerate(rows, start=1)]
    with OUTPUT_JSONL.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    COUNT_FILE.write_text(f"{len(records)}\n", encoding="utf-8")
    if records:
        SAMPLE_JSON.write_text(json.dumps(records[0], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "records": len(records), "best_horizon": best_horizon, "output": str(OUTPUT_JSONL)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
