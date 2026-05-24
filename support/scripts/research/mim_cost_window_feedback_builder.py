from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable


def build_feedback_rows(
    events: Iterable[dict[str, object]],
    *,
    factor_id: str,
    close_after_minutes: int = 30,
    cost_bps_per_side: float = 5.0,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, event in enumerate(events, start=1):
        side = int(event.get("side") or 0)
        if side == 0:
            continue
        branch_path = str(event.get("branch_path") or "")
        if not branch_path:
            raise ValueError("event row missing branch_path")
        parts = _branch_parts(branch_path)
        event_ts = _parse_ts(str(event.get("event_ts") or ""))
        label = int(event.get("triple_barrier_label") or 0)
        outcome, exit_reason, pnl = _outcome_from_label(label, cost_bps_per_side=cost_bps_per_side)
        symbol = str(event.get("symbol") or "")
        resonance = event.get("mtf_trend_resonance")
        if not isinstance(resonance, dict):
            resonance = {"enabled": False, "aligned_timeframes": [], "resonance_score": 0.0}
        row = {
            "schema_version": "1.0",
            "symbol": symbol,
            "trade_id": f"sim-mim-{factor_id}-{event_ts:%Y%m%d}-{index:03d}",
            "strategy_name": factor_id,
            "strategy_mutation_id": factor_id,
            "auto_quant_run_id": f"retained_real_mim_cost_window_feedback:{factor_id}",
            "open_ts_ms": int(event_ts.timestamp() * 1000),
            "close_ts_ms": int((event_ts + timedelta(minutes=close_after_minutes)).timestamp() * 1000),
            "direction": "long" if side > 0 else "short",
            "pnl": pnl,
            "realized_outcome": outcome,
            "regime_at_entry": _regime_alias(parts[0] if parts else ""),
            "entry_signal": "high" if resonance.get("enabled") else "medium",
            "factors_used": [
                {
                    "factor_name": branch_path,
                    "category": "regime_profit_branch_path",
                    "direction": "long" if side > 0 else "short",
                    "value": 1.0,
                    "confidence": float(resonance.get("resonance_score") or 0.0),
                    "weighted_score": float(resonance.get("resonance_score") or 0.0),
                    "uncertainty_contribution": 1.0 - float(resonance.get("resonance_score") or 0.0),
                }
            ],
            "model_probabilities_before_trade": {
                "selected_direction": "long" if side > 0 else "short",
                "selected_probability": float(resonance.get("resonance_score") or 0.0),
                "uncertainty": 1.0 - float(resonance.get("resonance_score") or 0.0),
            },
            "structural_feedback": {
                "protocol_version": "structural-feedback-v1",
                "recommendation_id": f"sim-mim-{factor_id}-{event_ts:%Y%m%d}-{index:03d}",
                "recommended_at": event_ts.isoformat(),
                "node_id": f"{symbol}_mim_cost_window_feedback",
                "branch_id": " -> ".join(parts[:2]) if len(parts) >= 2 else branch_path,
                "scenario_id": " -> ".join(parts[:3]) if len(parts) >= 3 else branch_path,
                "path_id": branch_path,
                "followed_path": True,
                "exit_reason": exit_reason,
                "notes": "retained-real MIM event feedback; simulated from event labels, not broker fills",
            },
            "regime_profit_branch_path": branch_path,
            "branch_path": branch_path,
            "main_regime": parts[0] if parts else str(event.get("main_regime") or ""),
            "sub_regime": parts[1] if len(parts) > 1 else str(event.get("sub_regime") or ""),
            "sub_sub_regime_or_profit_factor": parts[2] if len(parts) > 2 else "",
            "profit_factor": " -> ".join(parts[3:]) if len(parts) > 3 else str(event.get("profit_factor") or factor_id),
            "mtf_trend_resonance": resonance,
            "feedback_source": "retained_real_event_label_simulation",
            "broker_fill_evidence": False,
            "provider": event.get("provider") or "",
            "cost_bps_per_side": cost_bps_per_side,
            "promotion_allowed": False,
            "trade_usable": False,
            "downstream_allowed": False,
        }
        rows.append(row)
    return rows


def build_summary(rows: list[dict[str, object]], *, factor_id: str) -> dict[str, object]:
    return {
        "schema_version": "mim-cost-window-feedback-summary/v1",
        "factor_id": factor_id,
        "feedback_rows": len(rows),
        "wins": sum(1 for row in rows if row.get("realized_outcome") == "win"),
        "losses": sum(1 for row in rows if row.get("realized_outcome") == "loss"),
        "source": "retained_real_event_label_simulation",
        "broker_fill_evidence": False,
        "provider_fetch_started": False,
        "auto_quant_started": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "downstream_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build simulated feedback rows from MIM retained-real events.")
    parser.add_argument("--events-jsonl", required=True, type=Path)
    parser.add_argument("--output-jsonl", required=True, type=Path)
    parser.add_argument("--summary-json", required=True, type=Path)
    parser.add_argument("--factor-id", required=True)
    parser.add_argument("--close-after-minutes", type=int, default=30)
    parser.add_argument("--cost-bps-per-side", type=float, default=5.0)
    args = parser.parse_args(argv)
    events = _read_jsonl(args.events_jsonl)
    rows = build_feedback_rows(
        events,
        factor_id=args.factor_id,
        close_after_minutes=args.close_after_minutes,
        cost_bps_per_side=args.cost_bps_per_side,
    )
    _write_jsonl(args.output_jsonl, rows)
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(build_summary(rows, factor_id=args.factor_id), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(build_summary(rows, factor_id=args.factor_id), indent=2, sort_keys=True))
    return 0


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _outcome_from_label(label: int, *, cost_bps_per_side: float) -> tuple[str, str, float]:
    cost = cost_bps_per_side / 10_000.0
    if label > 0:
        return "win", "triple_barrier_profit_take", max(0.0001, 0.006 - cost)
    if label < 0:
        return "loss", "triple_barrier_stop_loss", -0.004 - cost
    return "breakeven", "triple_barrier_vertical_timeout", -cost


def _parse_ts(value: str) -> datetime:
    if not value:
        raise ValueError("event row missing event_ts")
    clean = value.strip()
    if clean.endswith("Z"):
        clean = clean[:-1] + "+00:00"
    parsed = datetime.fromisoformat(clean)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _branch_parts(branch_path: str) -> list[str]:
    return [part.strip() for part in branch_path.split("->") if part.strip()]


def _regime_alias(regime: str) -> str:
    return "trend" if regime == "TrendExpansion" else regime


if __name__ == "__main__":
    raise SystemExit(main())
