from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


FORBIDDEN_TRUE_KEYS = (
    "broker_fill_evidence",
    "provider_fetch_started",
    "auto_quant_started",
    "promotion_allowed",
    "trade_usable",
    "downstream_allowed",
)

SIMULATED_SOURCES = {
    "retained_real_event_label_simulation",
    "ibkr_paper_trade_simulation",
    "paper_trade_simulation",
}


def validate_bundle(
    rows: Iterable[dict[str, object]],
    *,
    summary: dict[str, object] | None = None,
    require_trend_root: bool = True,
    require_mtf_resonance: bool = True,
    max_trade_gap_days: float = 3.0,
    max_trades_per_day: float = 3.0,
) -> dict[str, object]:
    row_list = list(rows)
    violations: list[str] = []
    sources: set[str] = set()

    for index, row in enumerate(row_list):
        source = str(row.get("feedback_source") or row.get("source") or "")
        if source:
            sources.add(source)
            if source not in SIMULATED_SOURCES:
                violations.append(f"row[{index}].unknown_feedback_source:{source}")
        for key in FORBIDDEN_TRUE_KEYS:
            if _truthy(row.get(key)):
                violations.append(f"row[{index}].{key}_true")
        if require_trend_root:
            _validate_trend_branch(row, index=index, violations=violations)
        if require_mtf_resonance:
            _validate_mtf_resonance(row, index=index, violations=violations)

    _validate_trade_frequency(
        row_list,
        max_trade_gap_days=max_trade_gap_days,
        max_trades_per_day=max_trades_per_day,
        violations=violations,
    )

    if summary is not None:
        summary_source = str(summary.get("source") or summary.get("feedback_source") or "")
        if summary_source:
            sources.add(summary_source)
            if summary_source not in SIMULATED_SOURCES:
                violations.append(f"summary.unknown_feedback_source:{summary_source}")
        for key in FORBIDDEN_TRUE_KEYS:
            if _truthy(summary.get(key)):
                violations.append(f"summary.{key}_true")

    blocker_categories = classify_blockers(row_list, summary=summary, violations=violations)
    ok = not violations
    return {
        "schema_version": "simulated-feedback-admission-guard/v1",
        "ok": ok,
        "row_count": len(row_list),
        "sources": sorted(sources),
        "violations": violations,
        "blocker_categories": blocker_categories,
        "next_action_keywords": _next_action_keywords(blocker_categories),
        "broker_fill_evidence": False,
        "provider_fetch_started": False,
        "auto_quant_started": False,
        "promotion_allowed": False,
        "trade_usable": False,
        "downstream_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail closed if simulated feedback is marked as provider/AQ/downstream/trade evidence."
    )
    parser.add_argument("--feedback-jsonl", required=True, type=Path)
    parser.add_argument("--summary-json", type=Path)
    parser.add_argument("--report-json", required=True, type=Path)
    parser.add_argument("--allow-non-trend-root", action="store_true")
    parser.add_argument("--allow-missing-mtf-resonance", action="store_true")
    parser.add_argument("--max-trade-gap-days", type=float, default=3.0)
    parser.add_argument("--max-trades-per-day", type=float, default=3.0)
    args = parser.parse_args(argv)

    rows = _read_jsonl(args.feedback_jsonl)
    summary = _read_json(args.summary_json) if args.summary_json else None
    report = validate_bundle(
        rows,
        summary=summary,
        require_trend_root=not args.allow_non_trend_root,
        require_mtf_resonance=not args.allow_missing_mtf_resonance,
        max_trade_gap_days=args.max_trade_gap_days,
        max_trades_per_day=args.max_trades_per_day,
    )
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 2


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    if isinstance(value, (int, float)):
        return value != 0
    return bool(value)


def classify_blockers(
    rows: list[dict[str, object]],
    *,
    summary: dict[str, object] | None,
    violations: list[str],
) -> dict[str, dict[str, object]]:
    payload = summary or {}
    categories: dict[str, dict[str, object]] = {
        "root": _category(
            [
                violation
                for violation in violations
                if any(
                    marker in violation
                    for marker in (
                        "branch_path",
                        "non_trend_root",
                        "main_regime_mismatch",
                        "branch_depth",
                    )
                )
            ]
        ),
        "mtf": _category([violation for violation in violations if ".mtf_" in violation or "missing_mtf" in violation]),
        "frequency": _category([violation for violation in violations if violation.startswith("frequency.")]),
        "cost_5bps": _category(_cost_5bps_reasons(payload)),
        "trade_count": _category(_trade_count_reasons(rows, payload)),
        "provider_parity": _category(_provider_parity_reasons(payload)),
        "validation": _category(_validation_reasons(payload)),
        "execution_readiness": _category(_execution_reasons(payload)),
    }
    return categories


def _category(reasons: list[str]) -> dict[str, object]:
    return {
        "ok": not reasons,
        "reasons": reasons,
    }


def _next_action_keywords(categories: dict[str, dict[str, object]]) -> list[str]:
    keywords: list[str] = []
    for name, detail in categories.items():
        if detail["ok"]:
            continue
        keywords.append(
            {
                "root": "fix_regime_root_branch_path",
                "mtf": "require_real_mtf_trend_resonance",
                "frequency": "repair_trade_frequency_or_window",
                "cost_5bps": "rerun_exact_5bps_cost_stress",
                "trade_count": "increase_positive_trade_count",
                "provider_parity": "prove_provider_parity",
                "validation": "repair_validation_rows",
                "execution_readiness": "repair_execution_readiness",
            }[name]
        )
    return keywords


def _cost_5bps_reasons(payload: dict[str, object]) -> list[str]:
    if not payload:
        return ["missing_cost_5bps_summary"]
    if _has_list_value(
        payload,
        (
            "exact_5bps_survivors",
            "origin_survivors_5bps",
            "origin_survivors_5bps_density",
            "exact_1m_survivors_5bps",
            "origin_1m_survivors_5bps",
            "origin_1m_survivors_5bps_density",
        ),
    ):
        return []
    if any(_cost_row_survives_5bps(row) for row in _iter_cost_rows(payload)):
        return []
    return ["no_positive_exact_5bps_survivor"]


def _trade_count_reasons(rows: list[dict[str, object]], payload: dict[str, object]) -> list[str]:
    counts: list[float] = []
    for source in [payload, *rows]:
        for key in ("trade_count", "rank_total_trade_count", "total_trade_count"):
            value = source.get(key)
            if isinstance(value, (int, float)):
                counts.append(float(value))
    if counts and max(counts) > 0:
        return []
    if rows:
        return []
    return ["no_positive_trade_count_evidence"]


def _provider_parity_reasons(payload: dict[str, object]) -> list[str]:
    if not payload:
        return ["missing_provider_parity"]
    for key in ("provider_parity", "provider_parity_pass", "provider_parity_ok"):
        if key in payload:
            return [] if _truthy(payload.get(key)) else [f"{key}_false"]
    return ["missing_provider_parity"]


def _validation_reasons(payload: dict[str, object]) -> list[str]:
    if not payload:
        return ["missing_validation_rows"]
    reasons: list[str] = []
    for key in ("raw_scored_mature_rows", "production_validation_rows", "observation_validation_rows"):
        value = payload.get(key)
        if isinstance(value, (int, float)) and value >= 30:
            continue
        reasons.append(f"{key}_lt_30")
    return reasons


def _execution_reasons(payload: dict[str, object]) -> list[str]:
    if not payload:
        return ["missing_execution_readiness"]
    reasons: list[str] = []
    readiness = payload.get("execution_readiness")
    if not isinstance(readiness, (int, float)) or readiness < 0.45:
        reasons.append("execution_readiness_lt_0.45")
    hazard = payload.get("transition_hazard")
    if isinstance(hazard, (int, float)) and hazard >= 0.60:
        reasons.append("transition_hazard_gte_0.60")
    actionable = payload.get("actionable")
    if actionable is not None and not _truthy(actionable):
        reasons.append("actionable_false")
    return reasons


def _has_list_value(payload: dict[str, object], keys: tuple[str, ...]) -> bool:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list) and value:
            return True
    return False


def _iter_cost_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for key in ("cost_row", "cost_stress"):
        value = payload.get(key)
        if isinstance(value, dict):
            rows.append(value)
        elif isinstance(value, list):
            rows.extend(row for row in value if isinstance(row, dict))
    value = payload.get("cost_stress_rows")
    if isinstance(value, list):
        rows.extend(row for row in value if isinstance(row, dict))
    return rows


def _cost_row_survives_5bps(row: dict[str, object]) -> bool:
    if _truthy(row.get("survives_5bps_per_side")):
        return _trade_count_from_row(row) > 0
    for key in ("net_after_5bps_side_pct", "net_after_5bps_per_side_pct", "5bps_per_side_total_profit_pct"):
        value = row.get(key)
        if isinstance(value, (int, float)) and value > 0 and _trade_count_from_row(row) > 0:
            return True
    return False


def _trade_count_from_row(row: dict[str, object]) -> float:
    for key in ("trade_count", "trades", "total_trades"):
        value = row.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return 0.0


def _validate_trend_branch(row: dict[str, object], *, index: int, violations: list[str]) -> None:
    branch_path = str(row.get("branch_path") or "").strip()
    regime_path = str(row.get("regime_profit_branch_path") or "").strip()
    if not branch_path:
        violations.append(f"row[{index}].missing_branch_path")
        return
    if regime_path and regime_path != branch_path:
        violations.append(f"row[{index}].branch_path_mismatch")
    parts = _branch_parts(branch_path)
    if not parts:
        violations.append(f"row[{index}].empty_branch_path")
        return
    main_regime = str(row.get("main_regime") or parts[0]).strip()
    if parts[0] != "TrendExpansion":
        violations.append(f"row[{index}].non_trend_root:{parts[0]}")
    if main_regime and main_regime != parts[0]:
        violations.append(f"row[{index}].main_regime_mismatch:{main_regime}!={parts[0]}")
    if len(parts) < 3:
        violations.append(f"row[{index}].branch_depth_lt_3:{len(parts)}")


def _validate_mtf_resonance(row: dict[str, object], *, index: int, violations: list[str]) -> None:
    resonance = row.get("mtf_trend_resonance")
    if not isinstance(resonance, dict):
        violations.append(f"row[{index}].missing_mtf_trend_resonance")
        return
    if not _truthy(resonance.get("enabled")):
        violations.append(f"row[{index}].mtf_enabled_false")
    if not _truthy(resonance.get("aligned")):
        violations.append(f"row[{index}].mtf_aligned_false")
    aligned_timeframes = resonance.get("aligned_timeframes")
    if not isinstance(aligned_timeframes, list):
        violations.append(f"row[{index}].mtf_aligned_timeframes_not_list")
        return
    min_aligned = int(resonance.get("min_aligned") or 3)
    if len(aligned_timeframes) < min_aligned:
        violations.append(f"row[{index}].mtf_aligned_timeframes_lt_min:{len(aligned_timeframes)}<{min_aligned}")
    for key in ("promotion_allowed", "trade_usable", "downstream_allowed"):
        if _truthy(resonance.get(key)):
            violations.append(f"row[{index}].mtf_{key}_true")


def _branch_parts(branch_path: str) -> list[str]:
    return [part.strip() for part in branch_path.split("->") if part.strip()]


def _validate_trade_frequency(
    rows: list[dict[str, object]],
    *,
    max_trade_gap_days: float,
    max_trades_per_day: float,
    violations: list[str],
) -> None:
    timestamps: list[datetime] = []
    timestamps_by_pair: dict[str, list[datetime]] = {}
    for index, row in enumerate(rows):
        timestamp = _row_timestamp(row)
        if timestamp is None:
            violations.append(f"row[{index}].missing_open_timestamp")
            continue
        timestamps.append(timestamp)
        pair = str(row.get("pair") or "").strip()
        if pair:
            timestamps_by_pair.setdefault(pair, []).append(timestamp)
    if not timestamps:
        return
    if timestamps_by_pair:
        max_daily = max(
            _max_daily_count(pair_timestamps) for pair_timestamps in timestamps_by_pair.values()
        )
    else:
        max_daily = _max_daily_count(timestamps)
    if max_daily > max_trades_per_day:
        violations.append(f"frequency.trades_per_day_gt_max:{max_daily:.2f}>{max_trades_per_day:.2f}")
    if timestamps_by_pair:
        pair_gaps = [
            gap
            for pair_timestamps in timestamps_by_pair.values()
            for gap in [_max_gap_days(pair_timestamps)]
            if gap is not None
        ]
        max_gap = max(pair_gaps) if pair_gaps else None
    else:
        max_gap = _max_gap_days(timestamps)
    if max_gap is None:
        return
    if max_gap > max_trade_gap_days:
        violations.append(f"frequency.max_gap_days_gt_allowed:{max_gap:.2f}>{max_trade_gap_days:.2f}")


def _max_daily_count(timestamps: list[datetime]) -> int:
    by_day: dict[str, int] = {}
    for timestamp in timestamps:
        day = timestamp.date().isoformat()
        by_day[day] = by_day.get(day, 0) + 1
    return max(by_day.values(), default=0)


def _max_gap_days(timestamps: list[datetime]) -> float | None:
    if len(timestamps) < 2:
        return None
    sorted_ts = sorted(timestamps)
    gaps = [
        (later - earlier).total_seconds() / 86_400.0
        for earlier, later in zip(sorted_ts, sorted_ts[1:])
    ]
    return max(gaps)


def _row_timestamp(row: dict[str, object]) -> datetime | None:
    raw_ms = row.get("open_ts_ms")
    if isinstance(raw_ms, (int, float)):
        return datetime.fromtimestamp(float(raw_ms) / 1000.0, tz=timezone.utc)
    for key in ("open_ts", "event_ts", "recommended_at"):
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
