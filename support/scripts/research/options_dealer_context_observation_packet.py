from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


CONTRACT_MULTIPLIER = 100.0


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


def _load_option_rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    rows = payload.get("rows") or payload.get("option_rows")
    if isinstance(rows, list):
        return rows
    raise ValueError(f"option rows missing in {path}")


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _normal_pdf(value: float) -> float:
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


def _bs_gamma(spot_price: float, strike: float, implied_vol: float, days_to_expiry: float) -> float:
    if spot_price <= 0.0 or strike <= 0.0 or implied_vol <= 0.0:
        return 0.0
    time_to_expiry = max(days_to_expiry / 365.0, 1.0 / 365.0)
    vol_sqrt_t = implied_vol * math.sqrt(time_to_expiry)
    if vol_sqrt_t <= 0.0:
        return 0.0
    d1 = (math.log(spot_price / strike) + 0.5 * implied_vol * implied_vol * time_to_expiry) / vol_sqrt_t
    return _normal_pdf(d1) / (spot_price * vol_sqrt_t)


def _row_float(row: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            try:
                value = float(row[key])
                return value if math.isfinite(value) else default
            except (TypeError, ValueError):
                return default
    return default


def _row_type(row: dict[str, Any]) -> str:
    raw = str(row.get("option_type") or row.get("type") or row.get("contract_type") or "").strip().lower()
    if raw.startswith("c"):
        return "call"
    if raw.startswith("p"):
        return "put"
    symbol = str(row.get("contractSymbol") or row.get("symbol") or "").upper()
    if symbol:
        if "C" in symbol[-10:]:
            return "call"
        if "P" in symbol[-10:]:
            return "put"
    return "unknown"


def _weighted_mean(items: list[tuple[float, float]]) -> float | None:
    total_weight = sum(weight for _, weight in items)
    if total_weight <= 0.0:
        return None
    return sum(value * weight for value, weight in items) / total_weight


def classify_options_dealer_context(option_rows: list[dict[str, Any]], *, spot_price: float) -> dict[str, Any]:
    normalized: list[dict[str, Any]] = []
    for row in option_rows:
        option_type = _row_type(row)
        strike = _row_float(row, "strike")
        oi = _row_float(row, "openInterest", "open_interest", "oi")
        volume = _row_float(row, "volume")
        iv = _row_float(row, "impliedVolatility", "implied_volatility", "iv")
        days_to_expiry = _row_float(row, "days_to_expiry", "dte", default=1.0)
        if option_type not in {"call", "put"} or strike <= 0.0 or oi <= 0.0 or iv <= 0.0:
            continue
        gamma = _bs_gamma(spot_price, strike, iv, days_to_expiry)
        exposure = gamma * oi * CONTRACT_MULTIPLIER * spot_price * spot_price
        normalized.append(
            {
                "option_type": option_type,
                "strike": strike,
                "open_interest": oi,
                "volume": volume,
                "implied_volatility": iv,
                "days_to_expiry": days_to_expiry,
                "gamma": gamma,
                "gamma_exposure": exposure,
            }
        )

    if not normalized:
        return {
            "gamma_wall": None,
            "put_wall": None,
            "call_wall": None,
            "dealer_gamma_regime": "unknown",
            "expected_pin_or_acceleration": "unknown",
            "zero_dte_pressure": "unknown",
            "skew_stress": None,
            "confidence": 0.0,
            "fail_closed_reason": "missing_option_chain_oi_iv_rows",
            "normalized_rows": [],
        }

    calls = [row for row in normalized if row["option_type"] == "call"]
    puts = [row for row in normalized if row["option_type"] == "put"]
    call_wall_row = max(calls, key=lambda row: row["open_interest"], default=None)
    put_wall_row = max(puts, key=lambda row: row["open_interest"], default=None)
    gamma_wall_row = max(normalized, key=lambda row: row["open_interest"])

    call_gamma = sum(row["gamma_exposure"] for row in calls)
    put_gamma = sum(row["gamma_exposure"] for row in puts)
    total_gamma = max(call_gamma + put_gamma, 1e-9)
    net_gamma_ratio = (call_gamma - put_gamma) / total_gamma
    dealer_gamma_regime = (
        "positive_gamma_pin_risk"
        if abs(net_gamma_ratio) <= 0.55
        else "call_dominant_acceleration_risk"
        if net_gamma_ratio > 0.55
        else "put_dominant_acceleration_risk"
    )

    call_wall = call_wall_row["strike"] if call_wall_row else None
    put_wall = put_wall_row["strike"] if put_wall_row else None
    if call_wall is not None and put_wall is not None and put_wall <= spot_price <= call_wall and dealer_gamma_regime == "positive_gamma_pin_risk":
        expected = "pin_between_put_call_walls"
    elif put_wall is not None and spot_price < put_wall:
        expected = "downside_acceleration_below_put_wall"
    elif call_wall is not None and spot_price > call_wall:
        expected = "upside_acceleration_above_call_wall"
    else:
        expected = "wall_retest_observation_only"

    put_iv = _weighted_mean([(row["implied_volatility"], row["open_interest"]) for row in puts])
    call_iv = _weighted_mean([(row["implied_volatility"], row["open_interest"]) for row in calls])
    skew_stress = None if put_iv is None or call_iv is None else round(put_iv - call_iv, 6)
    zero_dte_rows = [row for row in normalized if row["days_to_expiry"] <= 1.0]
    zero_dte_ratio = sum(row["gamma_exposure"] for row in zero_dte_rows) / total_gamma
    zero_dte_pressure = "elevated" if zero_dte_ratio >= 0.5 else "present" if zero_dte_ratio > 0.0 else "none"
    confidence = min(0.85, 0.35 + min(len(normalized), 20) * 0.015 + min(total_gamma / 1_000_000_000.0, 0.2))

    return {
        "gamma_wall": gamma_wall_row["strike"],
        "put_wall": put_wall,
        "call_wall": call_wall,
        "dealer_gamma_regime": dealer_gamma_regime,
        "expected_pin_or_acceleration": expected,
        "zero_dte_pressure": zero_dte_pressure,
        "skew_stress": skew_stress,
        "net_gamma_ratio": round(net_gamma_ratio, 6),
        "call_gamma_exposure": round(call_gamma, 6),
        "put_gamma_exposure": round(put_gamma, 6),
        "total_gamma_exposure": round(total_gamma, 6),
        "confidence": round(confidence, 6),
        "fail_closed_reason": "single_snapshot_observation_only_not_promotable",
        "normalized_rows": normalized,
    }


def build_observation_packet(
    *,
    symbol: str,
    provider: str,
    spot_price: float,
    option_rows: list[dict[str, Any]],
    snapshot_time: str,
    packet_version: str = "2026-05-16.observation-v1",
) -> dict[str, Any]:
    context = classify_options_dealer_context(option_rows, spot_price=spot_price)
    branch_path = (
        "RangeConsolidation -> OptionsDealerContext -> yfinance_option_chain_gamma_wall -> "
        "options_dealer_context_yf_chain_observation_v1"
    )
    per_regime_template = {
        "win_rate": None,
        "trade_count": 0,
        "expectancy": None,
        "sample_window": None,
        "instrument_coverage": [],
        "confidence": 0.0,
        "fail_closed_reason": "no_realized_trades_observation_only",
    }
    per_regime_statistics = {
        "trend": dict(per_regime_template),
        "range": dict(per_regime_template),
        "transition": dict(per_regime_template),
        "stress": dict(per_regime_template),
        "other": dict(per_regime_template),
    }
    per_regime_statistics["range"] = {
        "win_rate": None,
        "trade_count": 0,
        "expectancy": None,
        "sample_window": snapshot_time,
        "instrument_coverage": [f"{provider}:{symbol}:options_chain"],
        "confidence": context["confidence"],
        "fail_closed_reason": "single_snapshot_observation_only_not_promotable",
    }
    row = {
        "symbol": symbol,
        "provider": provider,
        "snapshot_time": snapshot_time,
        "spot_price": spot_price,
        "gamma_wall": context["gamma_wall"],
        "put_wall": context["put_wall"],
        "call_wall": context["call_wall"],
        "dealer_gamma_regime": context["dealer_gamma_regime"],
        "zero_dte_pressure": context["zero_dte_pressure"],
        "skew_stress": context["skew_stress"],
        "expected_pin_or_acceleration": context["expected_pin_or_acceleration"],
        "net_gamma_ratio": context.get("net_gamma_ratio"),
        "call_gamma_exposure": context.get("call_gamma_exposure"),
        "put_gamma_exposure": context.get("put_gamma_exposure"),
        "total_gamma_exposure": context.get("total_gamma_exposure"),
        "evidence_source": f"{provider}:option_chain",
        "confidence": context["confidence"],
        "fail_closed_reason": context["fail_closed_reason"],
        "actionable": False,
        "main_regime": "RangeConsolidation",
        "sub_regime": "OptionsDealerContext",
        "sub_sub_regime_or_profit_factor": "yfinance_option_chain_gamma_wall",
        "profit_factor": "options_dealer_context_yf_chain_observation_v1",
        "regime_profit_branch_path": branch_path,
    }
    return {
        "factor_name": "options_dealer_context",
        "factor_version": packet_version,
        "promotion_allowed": False,
        "trade_usable": False,
        "actionable": False,
        "definition": "Observation-only options dealer context packet derived from option-chain IV/OI/volume and approximate Black-Scholes gamma exposure. It supplies gamma, put, call wall, skew, and 0DTE pressure fields; it cannot become actionable without realized outcomes and broader provider coverage.",
        "branch_path_contract": {
            "main_regime": "RangeConsolidation",
            "sub_regime": "OptionsDealerContext",
            "sub_sub_regime_or_profit_factor": "yfinance_option_chain_gamma_wall",
            "profit_factor": "options_dealer_context_yf_chain_observation_v1",
            "regime_profit_branch_path": branch_path,
        },
        "coverage_target": [f"{provider}:{symbol}:options_chain"],
        "source_row_count": len(option_rows),
        "normalized_row_count": len(context["normalized_rows"]),
        "rows": [row],
        "per_regime_statistics": per_regime_statistics,
        "quality_gate": {
            "downstream_allowed": False,
            "promotion_allowed": False,
            "trade_usable": False,
            "required_levels_present": all(row.get(key) is not None for key in ("gamma_wall", "put_wall", "call_wall")),
            "single_market_only": True,
            "single_snapshot_only": True,
            "fail_closed_reason": context["fail_closed_reason"],
        },
        "field_mapping": {
            "structure": ["gamma_wall", "put_wall", "call_wall"],
            "technicals": ["dealer_gamma_regime", "zero_dte_pressure", "skew_stress", "expected_pin_or_acceleration"],
            "smt": [],
            "regime_posterior_evidence": ["dealer_gamma_regime", "zero_dte_pressure", "skew_stress", "confidence"],
            "execution_tree_features": [
                "gamma_wall",
                "put_wall",
                "call_wall",
                "dealer_gamma_regime",
                "expected_pin_or_acceleration",
                "skew_stress",
            ],
            "feedback_update_learning_fields": [
                "provider",
                "snapshot_time",
                "spot_price",
                "regime_profit_branch_path",
                "realized_outcome_required_before_learning",
            ],
        },
    }


def fetch_yfinance_option_rows(symbol: str, *, expirations_limit: int = 2) -> tuple[float, list[dict[str, Any]]]:
    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("yfinance is required for --fetch-yfinance") from exc
    ticker = yf.Ticker(symbol)
    history = ticker.history(period="5d", interval="1d", auto_adjust=False)
    if history.empty:
        raise RuntimeError(f"no yfinance history for {symbol}")
    spot_price = float(history["Close"].dropna().iloc[-1])
    today = datetime.now(UTC).date()
    rows: list[dict[str, Any]] = []
    for expiry in list(ticker.options)[:expirations_limit]:
        chain = ticker.option_chain(expiry)
        expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
        days_to_expiry = max((expiry_date - today).days, 0)
        for option_type, frame in (("call", chain.calls), ("put", chain.puts)):
            for record in frame.to_dict(orient="records"):
                record["option_type"] = option_type
                record["expiry"] = expiry
                record["days_to_expiry"] = days_to_expiry
                rows.append(record)
    return spot_price, rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a fail-closed options dealer context observation packet.")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--provider", default="yfinance")
    parser.add_argument("--spot-price", type=float)
    parser.add_argument("--snapshot-time", default=datetime.now(UTC).isoformat())
    parser.add_argument("--option-rows-json")
    parser.add_argument("--fetch-yfinance", action="store_true")
    parser.add_argument("--expirations-limit", type=int, default=2)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-csv")
    parser.add_argument("--normalized-rows-json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.fetch_yfinance:
        spot_price, option_rows = fetch_yfinance_option_rows(args.symbol, expirations_limit=args.expirations_limit)
    else:
        if args.spot_price is None or not args.option_rows_json:
            raise SystemExit("--spot-price and --option-rows-json are required unless --fetch-yfinance is set")
        spot_price = args.spot_price
        option_rows = _load_option_rows(Path(args.option_rows_json))
    packet = build_observation_packet(
        symbol=args.symbol,
        provider=args.provider,
        spot_price=spot_price,
        option_rows=option_rows,
        snapshot_time=args.snapshot_time,
    )
    _write_json(Path(args.output_json), packet)
    if args.output_csv:
        _write_csv(Path(args.output_csv), packet["rows"])
    if args.normalized_rows_json:
        context = classify_options_dealer_context(option_rows, spot_price=spot_price)
        _write_json(Path(args.normalized_rows_json), {"rows": context["normalized_rows"]})
    print(
        json.dumps(
            {
                "ok": True,
                "factor_name": packet["factor_name"],
                "symbol": args.symbol,
                "normalized_row_count": packet["normalized_row_count"],
                "downstream_allowed": packet["quality_gate"]["downstream_allowed"],
                "output_json": args.output_json,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
