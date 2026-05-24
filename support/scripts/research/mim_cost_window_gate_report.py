from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_gate_report(
    events_jsonl: Path,
    *,
    branch_path: str,
    factor_id: str,
    max_trade_gap_days: float = 3.0,
    max_trades_per_day: float = 3.0,
) -> dict[str, Any]:
    events = _read_jsonl(events_jsonl)
    blockers: list[str] = []
    event_count = len(events)
    eligible_count = sum(1 for row in events if _is_true(row.get("eligible_long")) or int(row.get("side") or 0) != 0)
    positive_count = sum(1 for row in events if int(row.get("triple_barrier_label") or 0) > 0)
    negative_count = sum(1 for row in events if int(row.get("triple_barrier_label") or 0) < 0)
    branch_mismatches = _branch_mismatches(events, branch_path)

    if event_count == 0:
        blockers.append("no_events")
    if eligible_count == 0:
        blockers.append("no_eligible_long_events")
    if positive_count == 0:
        blockers.append("no_positive_triple_barrier_labels")
    if branch_mismatches:
        blockers.append("branch_path_mismatch")
    frequency = _frequency_summary(
        events,
        max_trade_gap_days=max_trade_gap_days,
        max_trades_per_day=max_trades_per_day,
    )
    blockers.extend(frequency["blockers"])

    if branch_mismatches:
        classification = "reject_branch_path_mismatch"
    elif blockers:
        classification = "retain_observation_only"
    else:
        classification = "retained_real_gate1_candidate"

    auto_quant_gate1_ready = classification == "retained_real_gate1_candidate"
    return {
        "schema_version": "mim-cost-window-gate-report/v1",
        "factor_id": factor_id,
        "branch_path": branch_path,
        "event_count": event_count,
        "eligible_long_count": eligible_count,
        "positive_triple_barrier_count": positive_count,
        "negative_triple_barrier_count": negative_count,
        "branch_path_mismatches": branch_mismatches,
        "mtf_trend_resonance": _summarize_mtf(events),
        "frequency": frequency,
        "classification": classification,
        "blockers": blockers,
        "auto_quant_gate1_ready": auto_quant_gate1_ready,
        "provider_fetch_started": False,
        "auto_quant_started": False,
        "downstream_allowed": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "next_action": (
            "run_auto_quant_gate1_when_backend_clear"
            if auto_quant_gate1_ready
            else "retain_as_observation_or_repair_source_events"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify retained-real MIM cost-window event readiness.")
    parser.add_argument("--events-jsonl", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--branch-path", required=True)
    parser.add_argument("--factor-id", required=True)
    parser.add_argument("--max-trade-gap-days", type=float, default=3.0)
    parser.add_argument("--max-trades-per-day", type=float, default=3.0)
    args = parser.parse_args(argv)

    report = build_gate_report(
        args.events_jsonl,
        branch_path=args.branch_path,
        factor_id=args.factor_id,
        max_trade_gap_days=args.max_trade_gap_days,
        max_trades_per_day=args.max_trades_per_day,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            clean = line.strip()
            if not clean:
                continue
            row = json.loads(clean)
            if not isinstance(row, dict):
                raise ValueError(f"event row {line_number} is not an object")
            rows.append(row)
    return rows


def _branch_mismatches(events: list[dict[str, Any]], branch_path: str) -> list[str]:
    mismatches: set[str] = set()
    for row in events:
        for key in ("branch_path", "regime_profit_branch_path"):
            value = row.get(key)
            if value is None:
                continue
            current = str(value or "")
            if current != branch_path:
                mismatches.add(f"{key}:{current}")
    return sorted(mismatches)


def _summarize_mtf(events: list[dict[str, Any]]) -> dict[str, Any]:
    mtf_rows = [row.get("mtf_trend_resonance") for row in events if isinstance(row.get("mtf_trend_resonance"), dict)]
    if not mtf_rows:
        return {
            "enabled": False,
            "aligned_timeframes": [],
            "avg_resonance_score": 0.0,
        }
    aligned = sorted({tf for row in mtf_rows for tf in row.get("aligned_timeframes", [])})
    return {
        "enabled": any(bool(row.get("enabled")) for row in mtf_rows),
        "aligned_timeframes": aligned,
        "avg_resonance_score": sum(float(row.get("resonance_score") or 0.0) for row in mtf_rows) / len(mtf_rows),
    }


def _is_true(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def _frequency_summary(
    events: list[dict[str, Any]],
    *,
    max_trade_gap_days: float,
    max_trades_per_day: float,
) -> dict[str, Any]:
    timestamps: list[datetime] = []
    missing = 0
    for row in events:
        timestamp = _event_timestamp(row)
        if timestamp is None:
            missing += 1
        else:
            timestamps.append(timestamp)

    blockers: list[str] = []
    if missing:
        blockers.append("missing_event_timestamp")

    by_day: dict[str, int] = {}
    for timestamp in timestamps:
        day = timestamp.date().isoformat()
        by_day[day] = by_day.get(day, 0) + 1
    max_daily = max(by_day.values()) if by_day else 0
    if max_daily > max_trades_per_day:
        blockers.append("trades_per_day_gt_max")

    max_gap_days = 0.0
    if len(timestamps) >= 2:
        ordered = sorted(timestamps)
        max_gap_days = max(
            (later - earlier).total_seconds() / 86_400.0
            for earlier, later in zip(ordered, ordered[1:])
        )
        if max_gap_days > max_trade_gap_days:
            blockers.append("max_gap_days_gt_allowed")

    return {
        "timestamp_count": len(timestamps),
        "missing_timestamp_count": missing,
        "max_trade_gap_days": max_gap_days,
        "max_trade_gap_days_allowed": max_trade_gap_days,
        "max_trades_per_day": max_daily,
        "max_trades_per_day_allowed": max_trades_per_day,
        "blockers": blockers,
        "ok": not blockers,
    }


def _event_timestamp(row: dict[str, Any]) -> datetime | None:
    raw_ms = row.get("open_ts_ms")
    if isinstance(raw_ms, (int, float)):
        return datetime.fromtimestamp(float(raw_ms) / 1000.0, tz=timezone.utc)
    for key in ("event_ts", "open_ts", "recommended_at"):
        raw = row.get(key)
        if isinstance(raw, str) and raw.strip():
            clean = raw.strip()
            if clean.endswith("Z"):
                clean = clean[:-1] + "+00:00"
            parsed = datetime.fromisoformat(clean)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
    structural = row.get("structural_feedback")
    if isinstance(structural, dict):
        raw = structural.get("recommended_at")
        if isinstance(raw, str) and raw.strip():
            clean = raw.strip()
            if clean.endswith("Z"):
                clean = clean[:-1] + "+00:00"
            parsed = datetime.fromisoformat(clean)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
    return None


if __name__ == "__main__":
    raise SystemExit(main())
