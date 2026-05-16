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


def _normalize_direction(direction: str) -> str:
    value = direction.strip().lower()
    if value == "bull":
        return "bull"
    if value == "bear":
        return "bear"
    raise ValueError(f"unsupported direction {direction}")


def resolve_observation_outcome(
    *,
    direction: str,
    entry: float,
    stop_loss: float,
    take_profit: float,
    future_candles: list[dict[str, Any]],
) -> dict[str, Any]:
    side = _normalize_direction(direction)
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
    }


def _relationship_stable(relationship_type: str, relationship_confidence: float) -> bool:
    return relationship_type in {"positive", "negative"} and relationship_confidence >= 0.3


def _as_string_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [str(value)]


def _required_symbol_coverage(symbol: str) -> list[str]:
    upper = symbol.upper()
    if upper in {"NQ", "MNQ"}:
        return ["NQ", "ES", "YM", "RTY", "QQQ", "SPY", "DIA", "IWM", "NAS100", "US500", "US30", "DXY", "VIX"]
    if upper in {"ES", "MES"}:
        return ["ES", "NQ", "YM", "RTY", "SPY", "QQQ", "DIA", "IWM", "US500", "NAS100", "US30", "VIX", "DXY"]
    if upper == "EURUSD":
        return ["EURUSD", "GBPUSD", "DXY"]
    if upper in {"XAUUSD", "GC", "MGC"}:
        return ["XAUUSD", "XAGUSD", "DXY", "US10Y", "REAL_YIELD", "GDX"]
    if upper in {"BTC", "BTCUSD", "BTCUSDT"}:
        return ["BTC", "ETH", "SOL", "TOTAL", "QQQ", "DXY"]
    return [upper]


def build_observation_packet(
    *,
    analyze_payload: dict[str, Any],
    execution_candidate_payload: dict[str, Any],
    future_candles: list[dict[str, Any]],
    provider: str,
    timeframe: str,
    comparison_symbol: str | None = None,
    comparison_session: str | None = None,
    packet_version: str = "2026-05-16.observation-v1",
) -> dict[str, Any]:
    report = analyze_payload["report"]
    smt = report["smt_correlation"]
    trade_plan = report["trade_plan"]
    regime_filter = execution_candidate_payload["pre_bayes_evidence_filter"]
    assignments = regime_filter.get("evidence_assignments", {})
    market_primary = assignments.get(
        "market_state_primary_regime",
        regime_filter.get("raw_market_regime_label", "other"),
    )
    main_regime = _canonical_main_regime(str(market_primary))
    normalized_regime_key = main_regime.lower() if main_regime != "Other" else "other"
    entry_packets = report["multi_timeframe"].get("entry_model_packets", {})
    base_session = str(smt.get("session") or "unknown")
    if base_session == "unknown" and entry_packets:
        base_session = next(iter(entry_packets.values())).get("session_label", "unknown")
    comparison_session_value = comparison_session or base_session
    session_overlap = base_session == comparison_session_value
    base_timeframe = str(smt.get("timeframe") or timeframe)
    comparison_timeframe = str(smt.get("comparison_timeframe") or timeframe)
    timeframe_aligned = base_timeframe == comparison_timeframe == timeframe
    same_liquidity_event_confirmed = bool(smt.get("same_liquidity_event_confirmed"))
    resolver_primary_related_symbols = _as_string_list(smt.get("primary_related_symbols"))
    resolver_futures_peers = _as_string_list(smt.get("futures_peers"))
    resolver_cfd_proxies = _as_string_list(smt.get("cfd_proxies"))
    resolver_etf_proxies = _as_string_list(smt.get("etf_proxies"))
    resolver_sector_or_industry_peers = _as_string_list(smt.get("sector_or_industry_peers"))
    resolver_currency_macro_drivers = _as_string_list(smt.get("currency_macro_drivers"))
    resolver_session_leaders = _as_string_list(smt.get("session_leaders"))
    resolver_relationship_type = smt.get("resolver_relationship_type")
    resolver_confidence = smt.get("resolver_confidence")
    resolver_evidence_source = smt.get("resolver_evidence_source")

    observation = resolve_observation_outcome(
        direction=trade_plan["direction"],
        entry=float(trade_plan["entry"]),
        stop_loss=float(trade_plan["stop_loss"]),
        take_profit=float(trade_plan["take_profits"][0]),
        future_candles=future_candles,
    )
    symbol = str(report["symbol"])
    comparison_symbol_value = comparison_symbol or smt.get("spot_symbol") or smt.get("futures_symbol") or "unknown"
    relationship_type = str(smt.get("relationship_type") or "uncertain")
    relationship_confidence = float(smt.get("relationship_confidence") or 0.0)
    confidence = min(
        float(smt.get("relationship_confidence") or 0.0),
        0.95 if smt.get("smt_signal") else 0.65,
    )

    fail_closed_reasons: list[str] = []
    if smt.get("trade_use") != "confirmation_only":
        fail_closed_reasons.append("smt_must_remain_confirmation_only")
    if smt.get("fail_closed_reason"):
        fail_closed_reasons.append(str(smt["fail_closed_reason"]))
    if not _relationship_stable(relationship_type, relationship_confidence):
        fail_closed_reasons.append("recent_correlation_unstable")
    if not session_overlap:
        fail_closed_reasons.append("session_not_overlapping")
    if not timeframe_aligned:
        fail_closed_reasons.append("timeframe_not_aligned")
    if not smt.get("paired_market_available"):
        fail_closed_reasons.append("paired_market_not_available")
    if smt.get("base_level") is None or smt.get("comparison_level") is None:
        fail_closed_reasons.append("missing_required_structure_levels")
    if smt.get("smt_signal") and not same_liquidity_event_confirmed:
        fail_closed_reasons.append("same_liquidity_event_not_confirmed")
    if smt.get("smt_signal") and not smt.get("mss_or_cisd_confirmed"):
        fail_closed_reasons.append("missing_mss_or_cisd_confirmation")
    if smt.get("smt_signal") and not smt.get("displacement_confirmed"):
        fail_closed_reasons.append("missing_displacement_confirmation")
    if smt.get("smt_signal") and not smt.get("near_pd_array"):
        fail_closed_reasons.append("missing_pd_array_entry_context")

    instrument_ref = f"{provider}:{symbol}:{timeframe}"
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
        "win_rate": 1.0 if observation["win"] else 0.0,
        "trade_count": 1,
        "expectancy": round(float(observation["realized_r"]), 6),
        "sample_window": f"{future_candles[0]['timestamp']} -> {future_candles[-1]['timestamp']}",
        "instrument_coverage": [instrument_ref],
        "confidence": round(min(confidence, 0.82), 6),
        "fail_closed_reason": "single_observation_only_not_promotable",
    }

    fail_closed_reason = "|".join(dict.fromkeys(fail_closed_reasons)) if fail_closed_reasons else "single_observation_only_not_promotable"
    packet = {
        "factor_name": "smt_relationship_resolver",
        "factor_version": packet_version,
        "promotion_allowed": False,
        "trade_usable": False,
        "actionable": False,
        "definition": "Provider-backed SMT same-event confirmation packet. SMT remains confirmation-only and fails closed when relationship stability, session overlap, or structure levels are missing.",
        "branch_path_contract": {
            "main_regime": main_regime,
            "sub_regime": "CrossMarketSmt",
            "sub_sub_regime_or_profit_factor": "same_event_confirmation_failure",
            "profit_factor": "smt_relationship_resolver_same_event_confirmation_failure_v1",
            "regime_profit_branch_path": f"{main_regime} -> CrossMarketSmt -> same_event_confirmation_failure -> smt_relationship_resolver_same_event_confirmation_failure_v1",
        },
        "coverage_target": _required_symbol_coverage(symbol),
        "rows": [
            {
                "symbol": symbol,
                "provider": provider,
                "timeframe": smt.get("timeframe") or timeframe,
                "comparison_timeframe": comparison_timeframe,
                "timeframe_aligned": timeframe_aligned,
                "base_symbol": symbol,
                "comparison_symbol": comparison_symbol_value,
                "relationship_type": relationship_type,
                "relationship_confidence": relationship_confidence,
                "resolver_relationship_type": resolver_relationship_type,
                "resolver_confidence": resolver_confidence,
                "resolver_evidence_source": resolver_evidence_source,
                "session": base_session,
                "comparison_session": comparison_session_value,
                "session_overlap": session_overlap,
                "smt_signal": smt.get("smt_signal"),
                "base_swing_type": smt.get("base_swing_type"),
                "base_level": smt.get("base_level"),
                "comparison_swing_type": smt.get("comparison_swing_type"),
                "comparison_level": smt.get("comparison_level"),
                "raw_comparison_swing_type": smt.get("raw_comparison_swing_type"),
                "raw_comparison_level": smt.get("raw_comparison_level"),
                "swept_side": smt.get("swept_side"),
                "same_liquidity_event_confirmed": same_liquidity_event_confirmed,
                "normalized_for_inverse_correlation": smt.get("normalized_for_inverse_correlation"),
                "near_pd_array": smt.get("near_pd_array"),
                "pd_array_type": smt.get("pd_array_type"),
                "mss_or_cisd_confirmed": smt.get("mss_or_cisd_confirmed"),
                "displacement_confirmed": smt.get("displacement_confirmed"),
                "provider_provenance": "retained_split_observation",
                "confidence": confidence,
                "fail_closed_reason": fail_closed_reason,
                "actionable": False,
                "selected_direction": trade_plan["direction"],
                "entry": trade_plan["entry"],
                "stop_loss": trade_plan["stop_loss"],
                "take_profit_1": trade_plan["take_profits"][0],
                "observation_outcome": observation["outcome"],
                "observation_exit_reason": observation["exit_reason"],
                "realized_r": round(float(observation["realized_r"]), 6),
                "trade_use": "confirmation_only",
                "main_regime": main_regime,
                "sub_regime": "CrossMarketSmt",
                "sub_sub_regime_or_profit_factor": "same_event_confirmation_failure",
                "profit_factor": "smt_relationship_resolver_same_event_confirmation_failure_v1",
                "regime_profit_branch_path": f"{main_regime} -> CrossMarketSmt -> same_event_confirmation_failure -> smt_relationship_resolver_same_event_confirmation_failure_v1",
                "related_futures_symbols": ",".join(smt.get("related_futures_symbols", [])),
                "related_etf_symbols": ",".join(smt.get("related_etf_symbols", [])),
                "related_options_symbols": ",".join(smt.get("related_options_symbols", [])),
                "related_cfd_symbols": ",".join(smt.get("related_cfd_symbols", [])),
                "related_crypto_symbols": ",".join(smt.get("related_crypto_symbols", [])),
                "primary_related_symbols": ",".join(resolver_primary_related_symbols),
                "futures_peers": ",".join(resolver_futures_peers),
                "cfd_proxies": ",".join(resolver_cfd_proxies),
                "etf_proxies": ",".join(resolver_etf_proxies),
                "sector_or_industry_peers": ",".join(resolver_sector_or_industry_peers),
                "currency_macro_drivers": ",".join(resolver_currency_macro_drivers),
                "session_leaders": ",".join(resolver_session_leaders),
            }
        ],
        "relationship_resolver": {
            "symbol": symbol,
            "primary_related_symbols": resolver_primary_related_symbols,
            "futures_peers": resolver_futures_peers,
            "cfd_proxies": resolver_cfd_proxies,
            "etf_proxies": resolver_etf_proxies,
            "sector_or_industry_peers": resolver_sector_or_industry_peers,
            "currency_macro_drivers": resolver_currency_macro_drivers,
            "session_leaders": resolver_session_leaders,
            "relationship_type": resolver_relationship_type,
            "confidence": resolver_confidence,
            "evidence_source": resolver_evidence_source,
        },
        "per_regime_statistics": per_regime_statistics,
        "quality_gate": {
            "downstream_allowed": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "trade_use": "confirmation_only",
            "same_event_required": True,
            "same_liquidity_event_required": True,
            "session_overlap_required": True,
            "timeframe_alignment_required": True,
            "stable_relationship_required": True,
            "required_levels_present": smt.get("base_level") is not None and smt.get("comparison_level") is not None,
            "same_liquidity_event_confirmed": same_liquidity_event_confirmed,
            "timeframe_aligned": timeframe_aligned,
            "mss_or_cisd_required_for_entry_model": bool(smt.get("mss_or_cisd_confirmed")),
            "displacement_required_for_entry_model": bool(smt.get("displacement_confirmed")),
            "pd_array_required_for_entry_model": bool(smt.get("near_pd_array")),
            "required_coverage_pairs": _required_symbol_coverage(symbol),
            "fail_closed_reason": fail_closed_reason,
        },
        "field_mapping": {
            "structure": ["base_swing_type", "base_level", "comparison_swing_type", "comparison_level", "swept_side", "same_liquidity_event_confirmed"],
            "technicals": [
                "relationship_type",
                "relationship_confidence",
                "resolver_relationship_type",
                "resolver_confidence",
                "normalized_for_inverse_correlation",
            ],
            "smt": [
                "smt_signal",
                "trade_use",
                "near_pd_array",
                "pd_array_type",
                "mss_or_cisd_confirmed",
                "displacement_confirmed",
                "fail_closed_reason",
            ],
            "regime_posterior_evidence": ["main_regime", "session", "session_overlap", "timeframe_aligned"],
            "execution_tree_features": [
                "base_level",
                "comparison_level",
                "swept_side",
                "same_liquidity_event_confirmed",
                "mss_or_cisd_confirmed",
                "displacement_confirmed",
                "near_pd_array",
                "pd_array_type",
            ],
            "feedback_update_learning_fields": ["observation_outcome", "realized_r", "provider", "timeframe", "regime_profit_branch_path"],
        },
    }
    return packet


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an SMT observation packet from provider-backed analyze output.")
    parser.add_argument("--analyze-json", required=True)
    parser.add_argument("--execution-candidate-json", required=True)
    parser.add_argument("--future-ltf-json", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--timeframe", required=True)
    parser.add_argument("--comparison-symbol")
    parser.add_argument("--comparison-session")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    packet = build_observation_packet(
        analyze_payload=_load_json(Path(args.analyze_json)),
        execution_candidate_payload=_load_json(Path(args.execution_candidate_json)),
        future_candles=_load_candles(Path(args.future_ltf_json)),
        provider=args.provider,
        timeframe=args.timeframe,
        comparison_symbol=args.comparison_symbol,
        comparison_session=args.comparison_session,
    )
    _write_json(Path(args.output_json), packet)
    _write_csv(Path(args.output_csv), packet["rows"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
