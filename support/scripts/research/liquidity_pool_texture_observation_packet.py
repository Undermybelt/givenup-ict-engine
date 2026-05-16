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


def resolve_observation_outcome(
    *,
    direction: str,
    entry: float,
    stop_loss: float,
    take_profit: float,
    future_candles: list[dict[str, Any]],
) -> dict[str, Any]:
    side = direction.strip().lower()
    if side not in {"bull", "bear"}:
        return {
            "outcome": "no_trade",
            "exit_reason": f"unsupported_direction:{direction}",
            "exit_timestamp": str(future_candles[0]["timestamp"]) if future_candles else None,
            "exit_index": None,
            "exit_price": entry,
            "realized_r": 0.0,
            "win": False,
            "counted_trade": False,
        }

    for index, candle in enumerate(future_candles):
        high = float(candle["high"])
        low = float(candle["low"])
        timestamp = str(candle["timestamp"])
        if side == "bull":
            stop_hit = low <= stop_loss
            tp_hit = high >= take_profit
            if stop_hit and tp_hit:
                return {
                    "outcome": "ambiguous",
                    "exit_reason": "same_candle_tp_and_stop",
                    "exit_timestamp": timestamp,
                    "exit_index": index,
                    "exit_price": entry,
                    "realized_r": 0.0,
                    "win": False,
                    "counted_trade": True,
                }
            if stop_hit:
                return {
                    "outcome": "loss",
                    "exit_reason": "stop_loss",
                    "exit_timestamp": timestamp,
                    "exit_index": index,
                    "exit_price": stop_loss,
                    "realized_r": -1.0,
                    "win": False,
                    "counted_trade": True,
                }
            if tp_hit:
                risk = max(entry - stop_loss, 1e-9)
                return {
                    "outcome": "win",
                    "exit_reason": "take_profit_1",
                    "exit_timestamp": timestamp,
                    "exit_index": index,
                    "exit_price": take_profit,
                    "realized_r": (take_profit - entry) / risk,
                    "win": True,
                    "counted_trade": True,
                }
        else:
            stop_hit = high >= stop_loss
            tp_hit = low <= take_profit
            if stop_hit and tp_hit:
                return {
                    "outcome": "ambiguous",
                    "exit_reason": "same_candle_tp_and_stop",
                    "exit_timestamp": timestamp,
                    "exit_index": index,
                    "exit_price": entry,
                    "realized_r": 0.0,
                    "win": False,
                    "counted_trade": True,
                }
            if stop_hit:
                return {
                    "outcome": "loss",
                    "exit_reason": "stop_loss",
                    "exit_timestamp": timestamp,
                    "exit_index": index,
                    "exit_price": stop_loss,
                    "realized_r": -1.0,
                    "win": False,
                    "counted_trade": True,
                }
            if tp_hit:
                risk = max(stop_loss - entry, 1e-9)
                return {
                    "outcome": "win",
                    "exit_reason": "take_profit_1",
                    "exit_timestamp": timestamp,
                    "exit_index": index,
                    "exit_price": take_profit,
                    "realized_r": (entry - take_profit) / risk,
                    "win": True,
                    "counted_trade": True,
                }

    last = future_candles[-1]
    close = float(last["close"])
    if side == "bull":
        risk = max(entry - stop_loss, 1e-9)
        realized_r = (close - entry) / risk
    else:
        risk = max(stop_loss - entry, 1e-9)
        realized_r = (entry - close) / risk
    return {
        "outcome": "open",
        "exit_reason": "late_window_exhausted",
        "exit_timestamp": str(last["timestamp"]),
        "exit_index": len(future_candles) - 1,
        "exit_price": close,
        "realized_r": realized_r,
        "win": realized_r > 0.0,
        "counted_trade": True,
    }


def build_observation_packet(
    *,
    analyze_payload: dict[str, Any],
    execution_candidate_payload: dict[str, Any],
    future_candles: list[dict[str, Any]],
    provider: str,
    timeframe: str,
    packet_version: str = "2026-05-15.observation-v1",
) -> dict[str, Any]:
    price_action = analyze_payload["report"]["price_action"]
    trade_plan = analyze_payload["report"]["trade_plan"]
    regime_filter = execution_candidate_payload["pre_bayes_evidence_filter"]
    assignments = regime_filter.get("evidence_assignments", {})
    market_primary = assignments.get(
        "market_state_primary_regime",
        regime_filter.get("raw_market_regime_label", "other"),
    )
    main_regime = _canonical_main_regime(str(market_primary))
    normalized_regime_key = main_regime.lower() if main_regime != "Other" else "other"
    texture = price_action["liquidity_pool_texture"]
    entry_packets = analyze_payload["report"]["multi_timeframe"].get("entry_model_packets", {})
    session = "unknown"
    if entry_packets:
        session = next(iter(entry_packets.values())).get("session_label", "unknown")

    observation = resolve_observation_outcome(
        direction=trade_plan["direction"],
        entry=float(trade_plan["entry"]),
        stop_loss=float(trade_plan["stop_loss"]),
        take_profit=float(trade_plan["take_profits"][0]),
        future_candles=future_candles,
    )
    confidence = float(texture.get("confidence") or 0.0)
    clean_sweep_likelihood = float(texture.get("clean_sweep_likelihood") or 0.0)
    quality_weight = round(min(confidence * max(clean_sweep_likelihood, 0.25), 0.45), 6)
    instrument_ref = f"{provider}:{analyze_payload['report']['symbol']}:{timeframe}"

    stats_template = {
        "win_rate": None,
        "trade_count": 0,
        "expectancy": None,
        "sample_window": None,
        "instrument_coverage": [],
        "confidence": 0.0,
        "fail_closed_reason": "no_provider_backed_labeled_outcomes",
    }
    per_regime_statistics = {
        "trend": dict(stats_template),
        "range": dict(stats_template),
        "transition": dict(stats_template),
        "stress": dict(stats_template),
        "other": dict(stats_template),
    }
    counted_trade = bool(observation.get("counted_trade", True))
    per_regime_statistics[normalized_regime_key] = {
        "win_rate": (1.0 if observation["win"] else 0.0) if counted_trade else None,
        "trade_count": 1 if counted_trade else 0,
        "expectancy": round(float(observation["realized_r"]), 6) if counted_trade else None,
        "sample_window": f"{future_candles[0]['timestamp']} -> {future_candles[-1]['timestamp']}",
        "instrument_coverage": [instrument_ref],
        "confidence": round(min(confidence, 0.82), 6),
        "fail_closed_reason": (
            "single_observation_only_not_promotable"
            if counted_trade
            else "non_directional_trade_plan_not_eligible_for_realized_outcome"
        ),
    }

    packet = {
        "factor_name": "liquidity_pool_texture",
        "factor_version": packet_version,
        "promotion_allowed": False,
        "trade_usable": False,
        "actionable": False,
        "definition": "Provider-backed observational packet for liquidity pool texture using one real analyze snapshot plus held-out future candles. This is Gate 1 observation only, not promotion.",
        "branch_path_contract": {
            "main_regime": main_regime,
            "sub_regime": "LiquidityMap",
            "sub_sub_regime_or_profit_factor": "liquidity_pool_texture",
            "profit_factor": "liquidity_pool_texture:observation_v1",
            "regime_profit_branch_path": f"{main_regime} -> LiquidityMap -> liquidity_pool_texture -> liquidity_pool_texture:observation_v1",
        },
        "coverage_target": [instrument_ref],
        "rows": [
            {
                "symbol": analyze_payload["report"]["symbol"],
                "provider": provider,
                "timeframe": timeframe,
                "session": session,
                "pool_side": "buy_side" if trade_plan["direction"] == "Bull" else "sell_side",
                "pool_type": "nearest_liquidity_pool",
                "texture": texture["texture"],
                "level": texture["level"],
                "high": texture["high"],
                "low": texture["low"],
                "touch_count": texture["touch_count"],
                "spacing_consistency": texture["spacing_consistency"],
                "sweep_detected": observation["outcome"] in {"win", "loss", "ambiguous"},
                "sweep_level": price_action.get("latest_liquidity_sweep_level"),
                "clean_sweep_likelihood": texture["clean_sweep_likelihood"],
                "provider_provenance": "retained_split_observation",
                "confidence": confidence,
                "fail_closed_reason": "single_observation_only_not_promotable",
                "actionable": False,
                "selected_direction": trade_plan["direction"],
                "entry": trade_plan["entry"],
                "stop_loss": trade_plan["stop_loss"],
                "take_profit_1": trade_plan["take_profits"][0],
                "observation_outcome": observation["outcome"],
                "exit_reason": observation["exit_reason"],
                "exit_timestamp": observation["exit_timestamp"],
                "realized_r": observation["realized_r"],
                "market_regime_label": regime_filter.get("raw_market_regime_label"),
                "market_state_primary_regime": assignments.get("market_state_primary_regime"),
                "market_state_secondary_regime": assignments.get("market_state_secondary_regime"),
            }
        ],
        "per_regime_statistics": per_regime_statistics,
        "quality_gate": {
            "quality_weight": quality_weight,
            "downstream_allowed": False,
            "allowed_feedback_targets": [
                "observation_packet_only",
                "provider_split_followup",
                "liquidity_pool_texture_requirements",
            ],
            "fail_closed_reason": "single_provider_single_observation_not_ready_for_candidate_pack_or_downstream_admission",
        },
    }
    return packet


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a fail-closed liquidity-pool-texture observation packet from one analyze snapshot plus held-out future candles.")
    parser.add_argument("--analyze-json", required=True)
    parser.add_argument("--execution-candidate-json", required=True)
    parser.add_argument("--future-ltf-json", required=True)
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
        future_candles=_load_candles(Path(args.future_ltf_json)),
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
                "trade_count": packet["per_regime_statistics"][packet["branch_path_contract"]["main_regime"].lower() if packet["branch_path_contract"]["main_regime"] != "Other" else "other"]["trade_count"],
                "output_json": args.output_json,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
