from __future__ import annotations

import argparse
import json
import math
import re
from bisect import bisect_right
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any


ACCEPTED_EXECUTION_FEEDBACK_MARKERS = (
    "paper_execution_feedback",
    "live_execution_feedback",
    "paper_trade_feedback",
    "live_trade_feedback",
    "broker_execution_feedback",
)
SIMULATED_FEEDBACK_MARKERS = (
    "simulated_backtest",
    "retained_real_event_label_simulation",
    "ibkr_paper_trade_simulation",
    "paper_trade_simulation",
    "simulation_child_gate",
    "child_gate_filtered",
    "simulated_feedback",
)
NEGATED_EXECUTION_FEEDBACK_MARKER_PREFIXES = {
    "not",
    "no",
    "non",
    "without",
    "missing",
    "absent",
    "fake",
    "spoofed",
}
NEGATED_EXECUTION_FEEDBACK_MARKER_LOOKBACK = 3


def _timestamp_ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)


def _load_candles(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    results = payload.get("results", [])
    if not results:
        raise ValueError("candles json missing results[0].data")
    candles = results[0].get("data", [])
    if not candles:
        raise ValueError("candles json missing results[0].data")
    return candles


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=False) + "\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("json payload must be an object")
    return payload


def _required_text(row: dict[str, Any], key: str) -> str:
    value = str(row.get(key) or "").strip()
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _required_float(row: dict[str, Any], key: str) -> float:
    try:
        value = float(row[key])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"{key} is required and must be numeric") from None
    if not math.isfinite(value):
        raise ValueError(f"{key} must be finite")
    return value


def _required_int(row: dict[str, Any], key: str) -> int:
    try:
        value = int(row[key])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"{key} is required and must be integer-like") from None
    return value


def _accepted_feedback_source(value: str) -> str:
    source = value.strip()
    normalized = source.lower()
    if not source:
        raise ValueError("feedback_source is required")
    if any(marker in normalized for marker in SIMULATED_FEEDBACK_MARKERS):
        raise ValueError("simulated feedback sources cannot be accepted paper/broker feedback")
    if not _source_has_accepted_feedback_marker(normalized):
        raise ValueError("feedback_source must include an accepted paper/live/broker execution marker")
    return source


def _is_accepted_feedback_source(value: str | None) -> bool:
    normalized = str(value or "").strip().lower()
    if not normalized:
        return False
    if any(marker in normalized for marker in SIMULATED_FEEDBACK_MARKERS):
        return False
    return _source_has_accepted_feedback_marker(normalized)


def _source_has_accepted_feedback_marker(value: str) -> bool:
    tokens = _source_marker_tokens(value)
    for index, token in enumerate(tokens):
        if token not in ACCEPTED_EXECUTION_FEEDBACK_MARKERS:
            continue
        lookback_tokens = tokens[
            max(0, index - NEGATED_EXECUTION_FEEDBACK_MARKER_LOOKBACK) : index
        ]
        if any(token in NEGATED_EXECUTION_FEEDBACK_MARKER_PREFIXES for token in lookback_tokens):
            continue
        return True
    return False


def _source_marker_tokens(value: str) -> list[str]:
    return [
        token
        for token in re.split(r"[^a-z0-9_]+", value)
        if token
    ]


def _side_to_direction(side: object) -> str:
    normalized = str(side or "").strip().lower()
    if normalized in {"buy", "bot", "long", "bull"}:
        return "Bull"
    if normalized in {"sell", "sld", "short", "bear"}:
        return "Bear"
    raise ValueError(f"unsupported IBKR side/action: {side!r}")


def _side_is_buy(side: object) -> bool:
    normalized = str(side or "").strip().lower()
    if normalized in {"buy", "bot", "long", "bull"}:
        return True
    if normalized in {"sell", "sld", "short", "bear"}:
        return False
    raise ValueError(f"unsupported IBKR side/action: {side!r}")


def _outcome_from_pnl(pnl: float) -> str:
    if pnl > 0:
        return "win"
    if pnl < 0:
        return "loss"
    return "breakeven"


def build_accepted_paper_execution_feedback_rows(
    captures: list[dict[str, Any]],
    *,
    symbol: str,
    strategy_name: str,
    factor_id: str,
    branch_path: str,
    auto_quant_run_id: str,
    feedback_source: str,
    session_scope: str = "ETH/full_retained_session",
    rth_filter_applied: bool = False,
) -> list[dict[str, Any]]:
    """Convert paired IBKR paper/broker fills into accepted real-trade wire rows.

    This consumes already captured execution and commission evidence. It does
    not submit orders, infer fills, or turn simulated/backtest rows into broker
    feedback.
    """

    source = _accepted_feedback_source(feedback_source)
    rows: list[dict[str, Any]] = []
    for index, capture in enumerate(captures):
        prefix = f"capture[{index}]"
        entry_exec_id = _required_text(capture, "entry_exec_id")
        exit_exec_id = _required_text(capture, "exit_exec_id")
        commission = _required_float(capture, "commission")
        commission_currency = _required_text(capture, "commission_currency")
        realized_pnl = _required_float(capture, "realized_pnl")
        open_ts_ms = _required_int(capture, "open_ts_ms")
        close_ts_ms = _required_int(capture, "close_ts_ms")
        if close_ts_ms < open_ts_ms:
            raise ValueError(f"{prefix} closes before it opens")
        open_rate = _required_float(capture, "open_rate")
        close_rate = _required_float(capture, "close_rate")
        quantity = _required_float(capture, "quantity")
        if quantity <= 0:
            raise ValueError(f"{prefix} quantity must be positive")

        direction = _side_to_direction(capture.get("side") or capture.get("action"))
        trade_id = str(capture.get("trade_id") or f"ibkr-paper-{entry_exec_id}-{exit_exec_id}")
        broker_execution = {
            "source": str(capture.get("source") or "ibkr_execDetails_commissionReport"),
            "entry_exec_id": entry_exec_id,
            "exit_exec_id": exit_exec_id,
            "order_id": _required_int(capture, "order_id"),
            "client_id": _required_int(capture, "client_id"),
            "perm_id": _required_int(capture, "perm_id"),
            "conid": _required_int(capture, "conid"),
            "local_symbol": _required_text(capture, "local_symbol"),
            "sec_type": _required_text(capture, "sec_type"),
            "exchange": _required_text(capture, "exchange"),
            "currency": _required_text(capture, "currency"),
            "quantity": quantity,
            "commission": commission,
            "commission_currency": commission_currency,
            "realized_pnl": realized_pnl,
        }
        row = {
            "schema_version": "1.0",
            "symbol": symbol,
            "trade_id": trade_id,
            "strategy_name": strategy_name,
            "strategy_mutation_id": factor_id,
            "auto_quant_run_id": auto_quant_run_id,
            "open_ts_ms": open_ts_ms,
            "close_ts_ms": close_ts_ms,
            "direction": direction,
            "pnl": realized_pnl,
            "realized_outcome": _outcome_from_pnl(realized_pnl),
            "open_rate": open_rate,
            "close_rate": close_rate,
            "profit_ratio": capture.get("profit_ratio"),
            "regime_profit_branch_path": branch_path,
            "structural_feedback": {
                "protocol_version": "structural-feedback-v1",
                "path_id": branch_path,
                "followed_path": True,
                "exit_reason": str(capture.get("exit_reason") or "ibkr_paper_fill"),
                "notes": "Accepted IBKR paper/broker execution capture with execDetails and commissionReport evidence.",
            },
            "source": source,
            "feedback_source": source,
            "broker_realized": True,
            "broker_fill_evidence": True,
            "broker_execution": broker_execution,
            "session_scope": session_scope,
            "rth_filter_applied": bool(rth_filter_applied),
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
        }
        if row["profit_ratio"] in (None, ""):
            row.pop("profit_ratio")
        rows.append(row)
    return rows


def _readback_row_contract(row: dict[str, Any]) -> dict[str, Any]:
    contract = row.get("contract")
    if not isinstance(contract, dict):
        raise ValueError("IBKR execution readback row missing contract object")
    return contract


def _readback_row_symbol(row: dict[str, Any]) -> str:
    contract = _readback_row_contract(row)
    return str(contract.get("symbol") or "").strip()


def _readback_row_key(row: dict[str, Any]) -> tuple[str, str, str, float]:
    contract = _readback_row_contract(row)
    conid = str(contract.get("conId") or "").strip()
    local_symbol = str(contract.get("localSymbol") or "").strip()
    symbol = str(contract.get("symbol") or "").strip()
    quantity = _required_float(row, "shares")
    if quantity <= 0:
        raise ValueError("IBKR execution readback row shares must be positive")
    return conid, local_symbol, symbol, quantity


def _readback_row_timestamp_ms(row: dict[str, Any]) -> int:
    value = str(row.get("time") or "").strip()
    if not value:
        raise ValueError("IBKR execution readback row time is required")
    return _timestamp_ms(value)


def _readback_row_to_capture(entry: dict[str, Any], exit_row: dict[str, Any]) -> dict[str, Any]:
    if entry.get("broker_fill_evidence") is not True or exit_row.get("broker_fill_evidence") is not True:
        raise ValueError("IBKR readback rows require broker fill evidence")
    if entry.get("commission_report_present") is not True or exit_row.get("commission_report_present") is not True:
        raise ValueError("IBKR readback rows require commissionReport evidence")
    entry_contract = _readback_row_contract(entry)
    exit_contract = _readback_row_contract(exit_row)
    entry_ts_ms = _readback_row_timestamp_ms(entry)
    exit_ts_ms = _readback_row_timestamp_ms(exit_row)
    commission = abs(_required_float(entry, "commission")) + abs(_required_float(exit_row, "commission"))
    realized_pnl = _required_float(exit_row, "realized_pnl")
    return {
        "entry_exec_id": _required_text(entry, "exec_id"),
        "exit_exec_id": _required_text(exit_row, "exec_id"),
        "order_id": _required_int(entry, "order_id"),
        "client_id": _required_int(entry, "client_id"),
        "perm_id": _required_int(entry, "perm_id"),
        "conid": _required_int(entry_contract, "conId"),
        "local_symbol": _required_text(entry_contract, "localSymbol"),
        "sec_type": _required_text(entry_contract, "secType"),
        "exchange": str(entry.get("exchange") or entry_contract.get("exchange") or exit_contract.get("exchange") or "").strip(),
        "currency": str(entry.get("currency") or entry_contract.get("currency") or exit_contract.get("currency") or "").strip(),
        "side": entry.get("side"),
        "quantity": _required_float(entry, "shares"),
        "open_ts_ms": entry_ts_ms,
        "close_ts_ms": exit_ts_ms,
        "open_rate": _required_float(entry, "price"),
        "close_rate": _required_float(exit_row, "price"),
        "commission": commission,
        "commission_currency": _required_text(exit_row, "currency"),
        "realized_pnl": realized_pnl,
        "source": "ibkr_reqExecutions_readback_execDetails_commissionReport",
    }


def build_ibkr_readback_captures(readback: dict[str, Any], *, symbol: str | None = None) -> list[dict[str, Any]]:
    """Pair local IBKR execution readback rows into accepted-feedback captures.

    This is an offline converter for rows already captured by a read-only IBKR
    execution audit. It deliberately ignores unpaired executions instead of
    inventing fills or PnL.
    """

    rows = readback.get("rows")
    if not isinstance(rows, list):
        return []

    requested_symbol = (symbol or str(readback.get("symbol") or "")).strip()
    pending_buy: dict[tuple[str, str, str, float], list[dict[str, Any]]] = {}
    pending_sell: dict[tuple[str, str, str, float], list[dict[str, Any]]] = {}
    captures: list[dict[str, Any]] = []
    eligible_rows = [
        row
        for row in rows
        if isinstance(row, dict)
        and row.get("broker_fill_evidence") is True
        and row.get("commission_report_present") is True
    ]
    ordered_rows = sorted(
        eligible_rows,
        key=lambda row: str(row.get("time") or ""),
    )
    for row in ordered_rows:
        if requested_symbol and _readback_row_symbol(row) != requested_symbol:
            continue
        key = _readback_row_key(row)
        is_buy = _side_is_buy(row.get("side"))
        if is_buy:
            open_rows = pending_sell.setdefault(key, [])
            if open_rows:
                entry = open_rows.pop(0)
                captures.append(_readback_row_to_capture(entry, row))
            else:
                pending_buy.setdefault(key, []).append(row)
            continue
        open_rows = pending_buy.setdefault(key, [])
        if open_rows:
            entry = open_rows.pop(0)
            captures.append(_readback_row_to_capture(entry, row))
        else:
            pending_sell.setdefault(key, []).append(row)
    return captures


def build_accepted_feedback_conversion_summary(
    *,
    rows: list[dict[str, Any]],
    input_mode: str,
    input_path: str,
    output_jsonl: str,
    input_rows_seen: int,
    paired_captures: int,
    symbol: str,
    strategy_name: str,
    factor_id: str,
    branch_path: str,
    auto_quant_run_id: str,
    feedback_source: str,
) -> dict[str, Any]:
    accepted_source: str | None = None
    mixed_sources = False
    broker_fill_evidence_rows = 0
    broker_realized_rows = 0
    for row in rows:
        source = str(row.get("source") or row.get("feedback_source") or "").strip()
        if source:
            if accepted_source is None:
                accepted_source = source
            elif source != accepted_source:
                mixed_sources = True
        if row.get("broker_fill_evidence") is True:
            broker_fill_evidence_rows += 1
        if row.get("broker_realized") is True:
            broker_realized_rows += 1

    accepted_feedback_rows = len(rows)
    accepted_source_valid = _is_accepted_feedback_source(accepted_source)
    ready = (
        accepted_feedback_rows > 0
        and not mixed_sources
        and accepted_source is not None
        and accepted_source_valid
        and broker_fill_evidence_rows >= accepted_feedback_rows
        and broker_realized_rows >= accepted_feedback_rows
    )
    status = "ready" if ready else "no_accepted_execution_feedback_rows"
    summary = {
        "schema_version": "accepted-execution-feedback-conversion/v1",
        "status": status,
        "accepted_execution_feedback_ready": ready,
        "accepted_feedback_rows": accepted_feedback_rows,
        "accepted_source": accepted_source if ready else None,
        "broker_fill_evidence_rows": broker_fill_evidence_rows,
        "broker_realized_rows": broker_realized_rows,
        "input_mode": input_mode,
        "input_path": input_path,
        "input_rows_seen": input_rows_seen,
        "paired_captures": paired_captures,
        "output_jsonl": output_jsonl,
        "symbol": symbol,
        "strategy_name": strategy_name,
        "factor_id": factor_id,
        "branch_path": branch_path,
        "auto_quant_run_id": auto_quant_run_id,
        "feedback_source": feedback_source,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    if not ready:
        summary["terminal_status"] = "terminalized_accepted_execution_feedback_missing"
        summary["terminal_decision"] = "accepted_execution_feedback_missing"
    return summary


def _direction_to_side(direction: str) -> int:
    normalized = direction.strip().lower()
    if normalized in {"bull", "long", "buy"}:
        return 1
    if normalized in {"bear", "short", "sell"}:
        return -1
    raise ValueError(f"unsupported trade direction: {direction}")


def _directional_return(side: int, entry: float, price: float) -> float:
    return side * ((price - entry) / entry)


def _timeframe_ms(candles: list[dict[str, Any]]) -> int:
    timestamps = [_timestamp_ms(str(candle["timestamp"])) for candle in candles]
    deltas = [right - left for left, right in zip(timestamps, timestamps[1:]) if right > left]
    if not deltas:
        raise ValueError("at least two ordered candles are required")
    return int(median(deltas))


def _floor_index(
    *,
    target_ts_ms: int,
    candle_ts_ms: list[int],
    max_gap_ms: int,
) -> int:
    index = bisect_right(candle_ts_ms, target_ts_ms) - 1
    if index < 0:
        raise ValueError(f"no candle at or before timestamp {target_ts_ms}")
    gap_ms = target_ts_ms - candle_ts_ms[index]
    if gap_ms > max_gap_ms:
        raise ValueError(
            f"timestamp {target_ts_ms} exceeded alignment gap {max_gap_ms}ms with nearest candle {candle_ts_ms[index]}"
        )
    return index


def _path_mfe_mae(
    *,
    candles: list[dict[str, Any]],
    entry_index: int,
    exit_index: int,
    entry_price: float,
    side: int,
) -> tuple[float, float]:
    mfe = 0.0
    mae = 0.0
    for candle in candles[entry_index + 1 : exit_index + 1]:
        high = float(candle["high"])
        low = float(candle["low"])
        returns = [
            _directional_return(side, entry_price, high),
            _directional_return(side, entry_price, low),
        ]
        mfe = max(mfe, max(returns))
        mae = min(mae, min(returns))
    return mfe, mae


def _regime_confidence(trade: dict[str, Any]) -> float | None:
    factors = trade.get("factors_used")
    if not isinstance(factors, list):
        return None
    for factor in factors:
        if not isinstance(factor, dict):
            continue
        if factor.get("category") == "regime_profit_branch_path":
            try:
                return float(factor["confidence"])
            except (KeyError, TypeError, ValueError):
                return None
    return None


def _actual_trade_sign(trade: dict[str, Any]) -> int:
    outcome = str(trade.get("realized_outcome", "")).strip().lower()
    if outcome == "win":
        return 1
    if outcome == "loss":
        return -1
    try:
        pnl = float(trade.get("pnl", 0.0))
    except (TypeError, ValueError):
        pnl = 0.0
    if pnl > 0.0:
        return 1
    if pnl < 0.0:
        return -1
    return 0


def _trade_float(trade: dict[str, Any], key: str) -> float | None:
    value = trade.get(key)
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_labels_from_trade_wire(
    *,
    trade_wire: list[dict[str, Any]],
    sl_mult: float,
    timeframe_ms: int,
    round_trip_cost_fraction: float = 0.0,
) -> list[dict[str, Any]]:
    if sl_mult <= 0:
        raise ValueError("sl_mult must be positive")
    if timeframe_ms <= 0:
        raise ValueError("timeframe_ms must be positive")
    if round_trip_cost_fraction < 0:
        raise ValueError("round_trip_cost_fraction must be >= 0")

    ordered = sorted(trade_wire, key=lambda row: int(row["open_ts_ms"]))
    if not ordered:
        return []

    base_ts_ms = min(int(row["open_ts_ms"]) for row in ordered)
    labels: list[dict[str, Any]] = []

    for trade in ordered:
        open_ts_ms = int(trade["open_ts_ms"])
        close_ts_ms = int(trade["close_ts_ms"])
        if close_ts_ms < open_ts_ms:
            raise ValueError(f"trade {trade.get('trade_id', '<unknown>')} closes before it opens")

        side = _direction_to_side(str(trade["direction"]))
        entry_price = _trade_float(trade, "open_rate")
        exit_price = _trade_float(trade, "close_rate")
        if entry_price is None or exit_price is None:
            raise ValueError("trade wire labels require open_rate and close_rate")

        min_rate = _trade_float(trade, "min_rate")
        max_rate = _trade_float(trade, "max_rate")
        if min_rate is not None and max_rate is not None:
            returns = [
                _directional_return(side, entry_price, max_rate),
                _directional_return(side, entry_price, min_rate),
            ]
            mfe = max(returns)
            mae = min(returns)
        else:
            proxy_return = _directional_return(side, entry_price, exit_price)
            mfe = max(0.0, proxy_return)
            mae = min(0.0, proxy_return)

        gross_return = _trade_float(trade, "profit_ratio")
        if gross_return is None:
            gross_return = _directional_return(side, entry_price, exit_price)
        net_return = gross_return - round_trip_cost_fraction
        entry_index = int((open_ts_ms - base_ts_ms) // timeframe_ms)
        exit_index = int((close_ts_ms - base_ts_ms) // timeframe_ms)
        label = {
            "trade_id": trade.get("trade_id", ""),
            "entry_index": entry_index,
            "exit_index": exit_index,
            "entry_timestamp": trade.get("open_date", open_ts_ms),
            "exit_timestamp": trade.get("close_date", close_ts_ms),
            "side": side,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "barrier_hit": trade.get("exit_reason", "real_trade"),
            "proxy_gross_return": _directional_return(side, entry_price, exit_price),
            "gross_return": gross_return,
            "net_return": net_return,
            "realized_R": net_return / sl_mult,
            "mfe": mfe,
            "mae": mae,
            "time_to_hit": max(0, exit_index - entry_index),
            "meta_label": 1 if net_return > 0.0 else 0,
            "realized_outcome": trade.get("realized_outcome", ""),
            "wire_pnl": trade.get("pnl", 0.0),
            "regime_profit_branch_path": trade.get("regime_profit_branch_path", ""),
            "main_regime": trade.get("main_regime", ""),
            "sub_regime": trade.get("sub_regime", ""),
            "sub_sub_regime_or_profit_factor": trade.get("sub_sub_regime_or_profit_factor", ""),
            "profit_factor": trade.get("profit_factor", ""),
        }
        regime_confidence = _regime_confidence(trade)
        if regime_confidence is not None:
            label["regime_confidence"] = regime_confidence
        labels.append(label)
    return labels


def build_labels(
    *,
    candles: list[dict[str, Any]],
    trade_wire: list[dict[str, Any]],
    sl_mult: float,
    round_trip_cost_fraction: float = 0.0,
    max_alignment_gap_bars: int = 3,
) -> list[dict[str, Any]]:
    if sl_mult <= 0:
        raise ValueError("sl_mult must be positive")
    if max_alignment_gap_bars < 0:
        raise ValueError("max_alignment_gap_bars must be >= 0")
    if round_trip_cost_fraction < 0:
        raise ValueError("round_trip_cost_fraction must be >= 0")

    candle_ts_ms = [_timestamp_ms(str(candle["timestamp"])) for candle in candles]
    max_gap_ms = _timeframe_ms(candles) * max_alignment_gap_bars
    labels: list[dict[str, Any]] = []

    for trade in trade_wire:
        entry_index = _floor_index(
            target_ts_ms=int(trade["open_ts_ms"]),
            candle_ts_ms=candle_ts_ms,
            max_gap_ms=max_gap_ms,
        )
        exit_index = _floor_index(
            target_ts_ms=int(trade["close_ts_ms"]),
            candle_ts_ms=candle_ts_ms,
            max_gap_ms=max_gap_ms,
        )
        if exit_index < entry_index:
            raise ValueError(f"trade {trade.get('trade_id', '<unknown>')} closes before it opens")

        side = _direction_to_side(str(trade["direction"]))
        entry_candle = candles[entry_index]
        exit_candle = candles[exit_index]
        entry_price = _trade_float(trade, "open_rate")
        if entry_price is None:
            entry_price = float(entry_candle["close"])
        exit_price = _trade_float(trade, "close_rate")
        if exit_price is None:
            exit_price = float(exit_candle["close"])

        min_rate = _trade_float(trade, "min_rate")
        max_rate = _trade_float(trade, "max_rate")
        if min_rate is not None and max_rate is not None:
            returns = [
                _directional_return(side, entry_price, max_rate),
                _directional_return(side, entry_price, min_rate),
            ]
            mfe = max(returns)
            mae = min(returns)
        else:
            mfe, mae = _path_mfe_mae(
                candles=candles,
                entry_index=entry_index,
                exit_index=exit_index,
                entry_price=entry_price,
                side=side,
            )

        proxy_gross_return = _directional_return(side, entry_price, exit_price)
        profit_ratio = _trade_float(trade, "profit_ratio")
        if profit_ratio is not None:
            gross_return = profit_ratio
        else:
            actual_sign = _actual_trade_sign(trade)
            proxy_magnitude = abs(proxy_gross_return)
            if actual_sign != 0 and proxy_magnitude <= 0.0:
                proxy_magnitude = max(abs(mfe), abs(mae), 1e-9)
            gross_return = proxy_magnitude * actual_sign if actual_sign != 0 else proxy_gross_return
        net_return = gross_return - round_trip_cost_fraction

        label = {
            "trade_id": trade.get("trade_id", ""),
            "entry_index": entry_index,
            "exit_index": exit_index,
            "entry_timestamp": entry_candle.get("timestamp"),
            "exit_timestamp": exit_candle.get("timestamp"),
            "side": side,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "barrier_hit": trade.get("structural_feedback", {}).get("exit_reason", "real_trade"),
            "proxy_gross_return": proxy_gross_return,
            "gross_return": gross_return,
            "net_return": net_return,
            "realized_R": net_return / sl_mult,
            "mfe": mfe,
            "mae": mae,
            "time_to_hit": exit_index - entry_index,
            "meta_label": 1 if net_return > 0.0 else 0,
            "realized_outcome": trade.get("realized_outcome", ""),
            "wire_pnl": trade.get("pnl", 0.0),
            "regime_profit_branch_path": trade.get("regime_profit_branch_path", ""),
            "main_regime": trade.get("main_regime", ""),
            "sub_regime": trade.get("sub_regime", ""),
            "sub_sub_regime_or_profit_factor": trade.get("sub_sub_regime_or_profit_factor", ""),
            "profit_factor": trade.get("profit_factor", ""),
        }
        regime_confidence = _regime_confidence(trade)
        if regime_confidence is not None:
            label["regime_confidence"] = regime_confidence
        labels.append(label)
    return labels


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build label rows from retained candles plus real-trade feedback wire.")
    parser.add_argument("--candles-json")
    parser.add_argument("--trade-wire-jsonl")
    parser.add_argument("--ibkr-paper-captures-jsonl")
    parser.add_argument("--ibkr-execution-readback-json")
    parser.add_argument("--ibkr-contract-symbol")
    parser.add_argument("--output-jsonl", required=True)
    parser.add_argument("--summary-json")
    parser.add_argument("--metrics-json")
    parser.add_argument("--sl-mult", type=float, default=0.01)
    parser.add_argument("--round-trip-cost-fraction", type=float, default=0.0)
    parser.add_argument("--max-alignment-gap-bars", type=int, default=3)
    parser.add_argument("--symbol")
    parser.add_argument("--strategy-name")
    parser.add_argument("--factor-id")
    parser.add_argument("--branch-path")
    parser.add_argument("--auto-quant-run-id")
    parser.add_argument("--feedback-source")
    parser.add_argument("--session-scope", default="ETH/full_retained_session")
    parser.add_argument("--rth-filter-applied", action="store_true")
    args = parser.parse_args(argv)

    feedback_modes = [bool(args.ibkr_paper_captures_jsonl), bool(args.ibkr_execution_readback_json)]
    if args.ibkr_paper_captures_jsonl or args.ibkr_execution_readback_json:
        missing = [
            name
            for name in ("symbol", "strategy_name", "factor_id", "branch_path", "auto_quant_run_id", "feedback_source")
            if not getattr(args, name)
        ]
        if missing:
            mode = "--ibkr-paper-captures-jsonl" if args.ibkr_paper_captures_jsonl else "--ibkr-execution-readback-json"
            parser.error(mode + " requires " + ", ".join(f"--{name.replace('_', '-')}" for name in missing))
        if args.candles_json or args.trade_wire_jsonl:
            parser.error("IBKR feedback conversion cannot be combined with --candles-json or --trade-wire-jsonl")
        if all(feedback_modes):
            parser.error("choose only one IBKR feedback conversion input")
    elif not (args.candles_json and args.trade_wire_jsonl):
        parser.error("label mode requires --candles-json and --trade-wire-jsonl")

    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.ibkr_paper_captures_jsonl or args.ibkr_execution_readback_json:
        input_path = args.ibkr_execution_readback_json or args.ibkr_paper_captures_jsonl
        input_mode = "ibkr_execution_readback" if args.ibkr_execution_readback_json else "ibkr_paper_captures"
        if args.ibkr_execution_readback_json:
            readback = _load_json(Path(args.ibkr_execution_readback_json))
            raw_rows = readback.get("rows")
            input_rows_seen = len(raw_rows) if isinstance(raw_rows, list) else 0
            captures = build_ibkr_readback_captures(
                readback,
                symbol=args.ibkr_contract_symbol,
            )
        else:
            captures = _load_jsonl(Path(args.ibkr_paper_captures_jsonl))
            input_rows_seen = len(captures)
        rows = build_accepted_paper_execution_feedback_rows(
            captures,
            symbol=args.symbol,
            strategy_name=args.strategy_name,
            factor_id=args.factor_id,
            branch_path=args.branch_path,
            auto_quant_run_id=args.auto_quant_run_id,
            feedback_source=args.feedback_source,
            session_scope=args.session_scope,
            rth_filter_applied=args.rth_filter_applied,
        )
        _write_jsonl(Path(args.output_jsonl), rows)
        summary = build_accepted_feedback_conversion_summary(
            rows=rows,
            input_mode=input_mode,
            input_path=input_path,
            output_jsonl=args.output_jsonl,
            input_rows_seen=input_rows_seen,
            paired_captures=len(captures),
            symbol=args.symbol,
            strategy_name=args.strategy_name,
            factor_id=args.factor_id,
            branch_path=args.branch_path,
            auto_quant_run_id=args.auto_quant_run_id,
            feedback_source=args.feedback_source,
        )
        if args.summary_json:
            _write_json(Path(args.summary_json), summary)
        if args.metrics_json:
            _write_json(Path(args.metrics_json), summary)
        print(json.dumps({"ok": True, **summary}, indent=2))
        return 0

    labels = build_labels(
        candles=_load_candles(Path(args.candles_json)),
        trade_wire=_load_jsonl(Path(args.trade_wire_jsonl)),
        sl_mult=args.sl_mult,
        round_trip_cost_fraction=args.round_trip_cost_fraction,
        max_alignment_gap_bars=args.max_alignment_gap_bars,
    )
    _write_jsonl(Path(args.output_jsonl), labels)
    print(json.dumps({"ok": True, "labels": len(labels), "output": args.output_jsonl}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
