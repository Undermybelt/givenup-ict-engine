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


def _from_analyze_price_action(price_action: dict[str, Any]) -> dict[str, Any] | None:
    evidence = price_action.get("order_block_variant")
    if not isinstance(evidence, dict):
        return None
    high = evidence.get("high")
    low = evidence.get("low")
    midpoint = evidence.get("midpoint")
    if midpoint is None and high is not None and low is not None:
        midpoint = round((float(high) + float(low)) / 2.0, 10)
    return {
        "variant": evidence.get("variant") or "none",
        "direction": str(evidence.get("direction") or "Neutral").lower(),
        "high": high,
        "low": low,
        "midpoint": midpoint,
        "validation_state": evidence.get("validation_state") or "fail_closed",
        "mitigation_count": int(evidence.get("mitigation_count") or 0),
        "breaker_confirmed": bool(evidence.get("breaker_confirmed")),
        "rejection_confirmed": bool(evidence.get("rejection_confirmed")),
        "origin_bar": evidence.get("origin_bar"),
        "first_mitigation_bar": evidence.get("first_mitigation_bar"),
        "confirmation_bar": evidence.get("confirmation_bar"),
        "confidence": float(evidence.get("confidence") or 0.0),
        "fail_closed_reason": evidence.get("fail_closed_reason"),
    }


def _detect_order_blocks(candles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for index in range(2, len(candles)):
        prev2 = candles[index - 2]
        prev1 = candles[index - 1]
        curr = candles[index]
        prev1_bear = float(prev1["close"]) < float(prev1["open"])
        prev1_bull = float(prev1["close"]) > float(prev1["open"])
        curr_bull = float(curr["close"]) > float(curr["open"])
        curr_bear = float(curr["close"]) < float(curr["open"])
        if prev1_bear and curr_bull and float(curr["close"]) > float(prev2["high"]):
            blocks.append(
                {
                    "direction": "bull",
                    "high": float(prev1["high"]),
                    "low": float(prev1["low"]),
                    "origin_bar": index - 1,
                }
            )
        if prev1_bull and curr_bear and float(curr["close"]) < float(prev2["low"]):
            blocks.append(
                {
                    "direction": "bear",
                    "high": float(prev1["high"]),
                    "low": float(prev1["low"]),
                    "origin_bar": index - 1,
                }
            )
    return blocks


def classify_latest_order_block_variant(
    candles: list[dict[str, Any]],
    price_action: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if price_action:
        from_analyze = _from_analyze_price_action(price_action)
        if from_analyze and from_analyze["variant"] != "none":
            return from_analyze

    blocks = _detect_order_blocks(candles)
    if not blocks:
        return {
            "variant": "none",
            "direction": "neutral",
            "high": None,
            "low": None,
            "midpoint": None,
            "validation_state": "fail_closed",
            "mitigation_count": 0,
            "breaker_confirmed": False,
            "rejection_confirmed": False,
            "origin_bar": None,
            "first_mitigation_bar": None,
            "confirmation_bar": None,
            "confidence": 0.0,
            "fail_closed_reason": "no_order_block_detected",
        }

    classified = [_classify_one_order_block(candles, block) for block in blocks]
    return max(
        classified,
        key=lambda item: (
            3
            if item["breaker_confirmed"]
            else 2
            if item["rejection_confirmed"]
            else 1
            if item["mitigation_count"] > 0
            else 0,
            item["origin_bar"] or -1,
        ),
    )


def _classify_one_order_block(
    candles: list[dict[str, Any]],
    latest: dict[str, Any],
) -> dict[str, Any]:
    high = float(latest["high"])
    low = float(latest["low"])
    direction = latest["direction"]
    origin_bar = int(latest["origin_bar"])
    mitigation_count = 0
    first_mitigation_bar: int | None = None
    breaker_confirmed = False
    rejection_confirmed = False
    confirmation_bar: int | None = None

    for bar in range(origin_bar + 1, len(candles)):
        candle = candles[bar]
        overlaps = float(candle["low"]) <= high and float(candle["high"]) >= low
        if not overlaps:
            continue
        mitigation_count += 1
        if first_mitigation_bar is None:
            first_mitigation_bar = bar
        close = float(candle["close"])
        if direction == "bull" and close < low:
            breaker_confirmed = True
            confirmation_bar = bar
            break
        if direction == "bear" and close > high:
            breaker_confirmed = True
            confirmation_bar = bar
            break
        rejection_confirmed = True

    variant = "order_block"
    validation_state = "unmitigated"
    if breaker_confirmed:
        variant = "breaker_block"
        validation_state = "breaker_confirmed"
    elif rejection_confirmed:
        variant = "rejection_block"
        validation_state = "rejection_confirmed"
    elif mitigation_count > 0:
        variant = "mitigation_block"
        validation_state = "mitigated"

    confidence = 0.78 if breaker_confirmed else 0.70 if rejection_confirmed else 0.62
    return {
        "variant": variant,
        "direction": direction,
        "high": high,
        "low": low,
        "midpoint": round((high + low) / 2.0, 10),
        "validation_state": validation_state,
        "mitigation_count": mitigation_count,
        "breaker_confirmed": breaker_confirmed,
        "rejection_confirmed": rejection_confirmed,
        "origin_bar": origin_bar,
        "first_mitigation_bar": first_mitigation_bar,
        "confirmation_bar": confirmation_bar,
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
    price_action = report.get("price_action", {})
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

    variant = classify_latest_order_block_variant(candles, price_action)
    symbol = str(report["symbol"])
    instrument_ref = f"{provider}:{symbol}:{timeframe}"
    trade_direction = _direction_for_trade_plan(str(trade_plan.get("direction", "")))
    counted_trade = trade_direction in {"bull", "bear"} and variant["variant"] != "none"
    realized_r = 0.0
    if counted_trade:
        if variant["direction"] == trade_direction:
            realized_r = min(float(variant["confidence"]), 1.0)
        elif variant["direction"] in {"bull", "bear"}:
            realized_r = -min(float(variant["confidence"]), 1.0)

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
        "confidence": round(float(variant["confidence"]), 6),
        "fail_closed_reason": "single_observation_only_not_promotable",
    }
    fail_closed_reason = variant.get("fail_closed_reason") or "single_observation_only_not_promotable"
    if variant["high"] is None or variant["low"] is None:
        fail_closed_reason = f"{fail_closed_reason}|missing_required_order_block_levels"

    branch_path = (
        f"{main_regime} -> OrderBlockVariant -> block_validation_state "
        "-> order_block_variant_observation_v1"
    )
    return {
        "factor_name": "order_block_variant_classifier",
        "factor_version": packet_version,
        "promotion_allowed": False,
        "trade_usable": False,
        "actionable": False,
        "definition": "Provider-backed order-block variant observation packet. Classifies order block, mitigation block, breaker block, rejection block, and fail-closed missing evidence with exact high/low/midpoint levels.",
        "branch_path_contract": {
            "main_regime": main_regime,
            "sub_regime": "OrderBlockVariant",
            "sub_sub_regime_or_profit_factor": "block_validation_state",
            "profit_factor": "order_block_variant_observation_v1",
            "regime_profit_branch_path": branch_path,
        },
        "coverage_target": [instrument_ref],
        "rows": [
            {
                "symbol": symbol,
                "provider": provider,
                "timeframe": timeframe,
                "session": session,
                "variant": variant["variant"],
                "direction": variant["direction"],
                "high": variant["high"],
                "low": variant["low"],
                "midpoint": variant["midpoint"],
                "validation_state": variant["validation_state"],
                "mitigation_count": variant["mitigation_count"],
                "breaker_confirmed": variant["breaker_confirmed"],
                "rejection_confirmed": variant["rejection_confirmed"],
                "origin_bar": variant["origin_bar"],
                "first_mitigation_bar": variant["first_mitigation_bar"],
                "confirmation_bar": variant["confirmation_bar"],
                "provider_provenance": "retained_split_observation",
                "confidence": variant["confidence"],
                "fail_closed_reason": fail_closed_reason,
                "actionable": False,
                "selected_direction": trade_plan.get("direction"),
                "entry": trade_plan.get("entry"),
                "stop_loss": trade_plan.get("stop_loss"),
                "take_profit_1": (trade_plan.get("take_profits") or [None])[0],
                "realized_r": round(realized_r, 6) if counted_trade else None,
                "main_regime": main_regime,
                "sub_regime": "OrderBlockVariant",
                "sub_sub_regime_or_profit_factor": "block_validation_state",
                "profit_factor": "order_block_variant_observation_v1",
                "regime_profit_branch_path": branch_path,
            }
        ],
        "per_regime_statistics": per_regime_statistics,
        "quality_gate": {
            "downstream_allowed": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "required_levels_present": variant["high"] is not None and variant["low"] is not None,
            "single_market_only": True,
            "fail_closed_reason": fail_closed_reason,
        },
        "field_mapping": {
            "structure": ["variant", "direction", "high", "low", "validation_state"],
            "technicals": [
                "variant",
                "direction",
                "high",
                "low",
                "midpoint",
                "mitigation_count",
                "breaker_confirmed",
                "rejection_confirmed",
            ],
            "smt": [],
            "regime_posterior_evidence": ["main_regime", "session", "validation_state", "confidence"],
            "execution_tree_features": [
                "high",
                "low",
                "midpoint",
                "validation_state",
                "mitigation_count",
                "breaker_confirmed",
                "rejection_confirmed",
            ],
            "feedback_update_learning_fields": [
                "realized_r",
                "provider",
                "timeframe",
                "regime_profit_branch_path",
            ],
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a fail-closed order-block variant observation packet from provider-backed candles."
    )
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
