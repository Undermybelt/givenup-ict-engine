from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_candles(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    results = payload.get("results", [])
    if not results:
        raise ValueError(f"candles json missing results for {path}")
    return results[0]["data"]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _canonical_main_regime(raw: str) -> str:
    normalized = raw.strip().lower()
    if normalized.startswith("range"):
        return "Range"
    if normalized.startswith("trend"):
        return "Trend"
    if normalized.startswith("transition") or normalized.startswith("reversal"):
        return "Transition"
    if normalized.startswith("stress"):
        return "Stress"
    return "Other"


def _direction_for_trade_plan(raw: str) -> str:
    value = raw.strip().lower()
    if value == "bull":
        return "bull"
    if value == "bear":
        return "bear"
    return "none"


def _detect_fvgs(candles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if len(candles) < 3:
        return out
    for index in range(1, len(candles) - 1):
        prev = candles[index - 1]
        nxt = candles[index + 1]
        prev_high = float(prev["high"])
        prev_low = float(prev["low"])
        next_high = float(nxt["high"])
        next_low = float(nxt["low"])
        if next_low > prev_high:
            out.append(
                {
                    "origin_bar": index,
                    "created_timestamp": str(candles[index]["timestamp"]),
                    "original_direction": "bull",
                    "top": next_low,
                    "bottom": prev_high,
                }
            )
        if next_high < prev_low:
            out.append(
                {
                    "origin_bar": index,
                    "created_timestamp": str(candles[index]["timestamp"]),
                    "original_direction": "bear",
                    "top": prev_low,
                    "bottom": next_high,
                }
            )
    return out


def _fill_ratio_for_fvg(fvg: dict[str, Any], candle: dict[str, Any]) -> float:
    top = float(fvg["top"])
    bottom = float(fvg["bottom"])
    width = max(top - bottom, 1e-9)
    if fvg["original_direction"] == "bull":
        deepest = max(min(float(candle["low"]), top), bottom)
        return (top - deepest) / width
    highest = min(max(float(candle["high"]), bottom), top)
    return (highest - bottom) / width


def classify_latest_fvg_lifecycle(
    candles: list[dict[str, Any]],
    *,
    confirm_window: int = 8,
) -> dict[str, Any]:
    fvgs = _detect_fvgs(candles)
    if not fvgs:
        return {
            "fvg_type": "none",
            "direction": "none",
            "original_direction": "none",
            "top": None,
            "bottom": None,
            "midpoint": None,
            "fill_ratio": 0.0,
            "inverted": False,
            "respected": False,
            "failed": False,
            "validation_state": "fail_closed",
            "origin_bar": None,
            "fill_bar": None,
            "confirm_bar": None,
            "created_timestamp": None,
            "fill_timestamp": None,
            "confirm_timestamp": None,
            "confidence": 0.0,
            "fail_closed_reason": "no_fvg_detected",
        }

    classified = [_classify_one_fvg(candles, fvg, confirm_window=confirm_window) for fvg in fvgs]
    return max(
        classified,
        key=lambda item: (
            3 if item["inverted"] else 2 if item["fill_ratio"] >= 1.0 else 1 if item["fill_ratio"] > 0.0 else 0,
            item["origin_bar"] or -1,
        ),
    )


def _classify_one_fvg(
    candles: list[dict[str, Any]],
    latest: dict[str, Any],
    *,
    confirm_window: int,
) -> dict[str, Any]:
    top = float(latest["top"])
    bottom = float(latest["bottom"])
    fill_ratio = 0.0
    fill_bar: int | None = None
    fill_timestamp: str | None = None
    respected = False
    confirm_bar: int | None = None
    confirm_timestamp: str | None = None
    original_direction = str(latest["original_direction"])

    scan_start = int(latest["origin_bar"]) + 2
    for bar in range(scan_start, len(candles)):
        candle = candles[bar]
        ratio = _fill_ratio_for_fvg(latest, candle)
        fill_ratio = max(fill_ratio, ratio)
        if ratio > 0.0 and fill_bar is None:
            fill_bar = bar
            fill_timestamp = str(candle["timestamp"])
        if fill_bar is not None and ratio < 1.0:
            respected = True
        if ratio >= 1.0:
            fill_bar = bar
            fill_timestamp = str(candle["timestamp"])
            break

    if fill_bar is not None and fill_ratio >= 1.0:
        end_bar = min(fill_bar + confirm_window, len(candles) - 1)
        for bar in range(fill_bar + 1, end_bar + 1):
            candle = candles[bar]
            close = float(candle["close"])
            if original_direction == "bull" and close < bottom:
                confirm_bar = bar
                confirm_timestamp = str(candle["timestamp"])
                break
            if original_direction == "bear" and close > top:
                confirm_bar = bar
                confirm_timestamp = str(candle["timestamp"])
                break

    inverted = confirm_bar is not None
    direction = {"bull": "bear", "bear": "bull"}.get(original_direction, "none") if inverted else original_direction
    validation_state = "inverted" if inverted else "filled" if fill_ratio >= 1.0 else "open"
    fvg_type = "IFVG" if inverted else "FVG"
    confidence = 0.78 if inverted else 0.62 if fill_ratio >= 1.0 else 0.48 if fill_ratio > 0 else 0.35
    return {
        "fvg_type": fvg_type,
        "direction": direction,
        "original_direction": original_direction,
        "top": top,
        "bottom": bottom,
        "midpoint": round((top + bottom) / 2.0, 10),
        "fill_ratio": round(min(fill_ratio, 1.0), 6),
        "inverted": inverted,
        "respected": respected and not inverted,
        "failed": inverted,
        "validation_state": validation_state,
        "origin_bar": latest["origin_bar"],
        "fill_bar": fill_bar,
        "confirm_bar": confirm_bar,
        "created_timestamp": latest["created_timestamp"],
        "fill_timestamp": fill_timestamp,
        "confirm_timestamp": confirm_timestamp,
        "confidence": confidence,
        "fail_closed_reason": "single_observation_only_not_promotable",
    }


def build_observation_packet(
    *,
    analyze_payload: dict[str, Any],
    execution_candidate_payload: dict[str, Any],
    candles: list[dict[str, Any]],
    provider: str,
    timeframe: str,
    packet_version: str = "2026-05-16.observation-v1",
) -> dict[str, Any]:
    report = analyze_payload["report"]
    trade_plan = report["trade_plan"]
    regime_filter = execution_candidate_payload["pre_bayes_evidence_filter"]
    assignments = regime_filter.get("evidence_assignments", {})
    market_primary = assignments.get(
        "market_state_primary_regime",
        regime_filter.get("raw_market_regime_label", "other"),
    )
    main_regime = _canonical_main_regime(str(market_primary))
    normalized_regime_key = main_regime.lower() if main_regime != "Other" else "other"
    entry_packets = report.get("multi_timeframe", {}).get("entry_model_packets", {})
    session = "unknown"
    if entry_packets:
        session = next(iter(entry_packets.values())).get("session_label", "unknown")

    lifecycle = classify_latest_fvg_lifecycle(candles)
    symbol = str(report["symbol"])
    instrument_ref = f"{provider}:{symbol}:{timeframe}"
    trade_direction = _direction_for_trade_plan(str(trade_plan.get("direction", "")))
    counted_trade = trade_direction in {"bull", "bear"} and lifecycle["fvg_type"] != "none"
    realized_r = 0.0
    if counted_trade:
        if lifecycle["direction"] == trade_direction:
            realized_r = min(float(lifecycle["confidence"]), 1.0)
        elif lifecycle["direction"] in {"bull", "bear"}:
            realized_r = -min(float(lifecycle["confidence"]), 1.0)

    per_regime_template = {
        "win_rate": None,
        "trade_count": 0,
        "expectancy": None,
        "sample_window": None,
        "instrument_coverage": [],
        "confidence": 0.0,
        "fail_closed_reason": "no_provider_backed_labeled_outcomes",
    }
    per_regime_statistics = {
        "trend": dict(per_regime_template),
        "range": dict(per_regime_template),
        "transition": dict(per_regime_template),
        "stress": dict(per_regime_template),
        "other": dict(per_regime_template),
    }
    per_regime_statistics[normalized_regime_key] = {
        "win_rate": (1.0 if realized_r > 0 else 0.0) if counted_trade else None,
        "trade_count": 1 if counted_trade else 0,
        "expectancy": round(realized_r, 6) if counted_trade else None,
        "sample_window": f"{candles[0]['timestamp']} -> {candles[-1]['timestamp']}" if candles else None,
        "instrument_coverage": [instrument_ref],
        "confidence": round(float(lifecycle["confidence"]), 6),
        "fail_closed_reason": "single_observation_only_not_promotable",
    }
    fail_closed_reason = lifecycle.get("fail_closed_reason") or "single_observation_only_not_promotable"
    if lifecycle["top"] is None or lifecycle["bottom"] is None:
        fail_closed_reason = f"{fail_closed_reason}|missing_required_gap_levels"

    branch_path = f"{main_regime} -> FvgIfvgLifecycle -> gap_lifecycle_state -> fvg_ifvg_lifecycle_observation_v1"
    return {
        "factor_name": "fvg_ifvg_lifecycle",
        "factor_version": packet_version,
        "promotion_allowed": False,
        "trade_usable": False,
        "actionable": False,
        "definition": "Provider-backed FVG/IFVG lifecycle observation packet. Tracks open, filled, inverted, respected, and failed gap states with exact top/bottom levels. Gate 1 observation only.",
        "branch_path_contract": {
            "main_regime": main_regime,
            "sub_regime": "FvgIfvgLifecycle",
            "sub_sub_regime_or_profit_factor": "gap_lifecycle_state",
            "profit_factor": "fvg_ifvg_lifecycle_observation_v1",
            "regime_profit_branch_path": branch_path,
        },
        "coverage_target": [instrument_ref],
        "rows": [
            {
                "symbol": symbol,
                "provider": provider,
                "timeframe": timeframe,
                "session": session,
                "fvg_type": lifecycle["fvg_type"],
                "direction": lifecycle["direction"],
                "original_direction": lifecycle["original_direction"],
                "top": lifecycle["top"],
                "bottom": lifecycle["bottom"],
                "midpoint": lifecycle["midpoint"],
                "fill_ratio": lifecycle["fill_ratio"],
                "inverted": lifecycle["inverted"],
                "respected": lifecycle["respected"],
                "failed": lifecycle["failed"],
                "validation_state": lifecycle["validation_state"],
                "origin_bar": lifecycle["origin_bar"],
                "fill_bar": lifecycle["fill_bar"],
                "confirm_bar": lifecycle["confirm_bar"],
                "created_timestamp": lifecycle["created_timestamp"],
                "fill_timestamp": lifecycle["fill_timestamp"],
                "confirm_timestamp": lifecycle["confirm_timestamp"],
                "provider_provenance": "retained_split_observation",
                "confidence": lifecycle["confidence"],
                "fail_closed_reason": fail_closed_reason,
                "actionable": False,
                "selected_direction": trade_plan.get("direction"),
                "entry": trade_plan.get("entry"),
                "stop_loss": trade_plan.get("stop_loss"),
                "take_profit_1": (trade_plan.get("take_profits") or [None])[0],
                "realized_r": round(realized_r, 6) if counted_trade else None,
                "main_regime": main_regime,
                "sub_regime": "FvgIfvgLifecycle",
                "sub_sub_regime_or_profit_factor": "gap_lifecycle_state",
                "profit_factor": "fvg_ifvg_lifecycle_observation_v1",
                "regime_profit_branch_path": branch_path,
            }
        ],
        "per_regime_statistics": per_regime_statistics,
        "quality_gate": {
            "downstream_allowed": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "required_levels_present": lifecycle["top"] is not None and lifecycle["bottom"] is not None,
            "single_market_only": True,
            "fail_closed_reason": fail_closed_reason,
        },
        "field_mapping": {
            "structure": ["fvg_type", "direction", "top", "bottom", "validation_state"],
            "technicals": ["fvg_type", "direction", "top", "bottom", "midpoint", "fill_ratio", "inverted", "respected"],
            "smt": [],
            "regime_posterior_evidence": ["main_regime", "session", "validation_state", "confidence"],
            "execution_tree_features": ["top", "bottom", "midpoint", "fill_ratio", "inverted", "failed", "validation_state"],
            "feedback_update_learning_fields": ["realized_r", "provider", "timeframe", "regime_profit_branch_path"],
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a fail-closed FVG/IFVG lifecycle observation packet from provider-backed candles.")
    parser.add_argument("--analyze-json", required=True)
    parser.add_argument("--execution-candidate-json", required=True)
    parser.add_argument("--candles-json", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--timeframe", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    packet = build_observation_packet(
        analyze_payload=_load_json(Path(args.analyze_json)),
        execution_candidate_payload=_load_json(Path(args.execution_candidate_json)),
        candles=_load_candles(Path(args.candles_json)),
        provider=args.provider,
        timeframe=args.timeframe,
    )
    _write_json(Path(args.output_json), packet)
    if args.output_csv:
        _write_csv(Path(args.output_csv), packet["rows"])
    print(
        json.dumps(
            {
                "ok": True,
                "factor_name": packet["factor_name"],
                "main_regime": packet["branch_path_contract"]["main_regime"],
                "output_json": args.output_json,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
