from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import factor_payoff_shape_report as payoff
import payoff_to_path_ranker_target as path_target
import purged_cv_backtest_guard as purged_cv
import real_trade_feedback_labels as trade_labels
import instrument_cost_model as cost_model


DEFAULT_STRATEGY = "TomacTodBalancedPortfolioExactV1"
DEFAULT_FACTOR_ID = "tomac_tod_balanced_adaptive_slot_portfolio_exact_v1"
DEFAULT_SYMBOL = "NQ_XAU_YM"


@dataclass(frozen=True)
class PairArtifacts:
    pair: str
    labels_jsonl: Path
    payoff_report_json: Path
    label_count: int
    meta_label_wins: int
    total_net_return: float


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=False) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize_timestamp(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def normalize_backtest_trade(trade: dict[str, Any], trade_id: str, factor_id: str) -> dict[str, Any]:
    pair = str(trade["pair"])
    is_short = bool(trade.get("is_short", False))
    direction = "short" if is_short else "long"
    profit_ratio = float(trade.get("profit_ratio", 0.0))
    pnl = float(trade.get("profit_abs", trade.get("close_profit_abs", 0.0)) or 0.0)
    normalized = {
        "trade_id": trade_id,
        "pair": pair,
        "direction": direction,
        "open_ts_ms": trade_labels._timestamp_ms(_normalize_timestamp(trade["open_date"])),
        "close_ts_ms": trade_labels._timestamp_ms(_normalize_timestamp(trade["close_date"])),
        "open_rate": float(trade["open_rate"]),
        "close_rate": float(trade["close_rate"]),
        "profit_ratio": profit_ratio,
        "profit_ratio_is_net": True,
        "pnl": pnl,
        "min_rate": float(trade["min_rate"]) if trade.get("min_rate") is not None else None,
        "max_rate": float(trade["max_rate"]) if trade.get("max_rate") is not None else None,
        "realized_outcome": "win" if profit_ratio > 0 else "loss" if profit_ratio < 0 else "flat",
        "regime_profit_branch_path": trade.get("enter_tag", factor_id),
        "main_regime": "SessionRhythm",
        "sub_regime": "TimeOfDaySeasonality",
        "sub_sub_regime_or_profit_factor": factor_id,
        "profit_factor": factor_id,
        "structural_feedback": {
            "exit_reason": trade.get("exit_reason", "exit_signal"),
        },
        "factors_used": [
            {
                "category": "regime_profit_branch_path",
                "confidence": 1.0,
            }
        ],
    }
    return normalized


def export_trades_from_run_tomac(
    *,
    run_tomac_path: Path,
    strategy_name: str,
    factor_id: str,
) -> list[dict[str, Any]]:
    module = _load_module(run_tomac_path, "tomac_run_tomac_sidecar")
    result = module.run_backtest(strategy_name)
    strategy = result.get("strategy", {}).get(strategy_name)
    if not strategy:
        raise ValueError(f"strategy {strategy_name} not found in backtest result")
    trades = strategy.get("trades") or []
    exported: list[dict[str, Any]] = []
    for index, trade in enumerate(trades):
        exported.append(normalize_backtest_trade(trade, f"{factor_id}-{index:05d}", factor_id))
    return exported


def _load_csv_candles(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    normalized: list[dict[str, Any]] = []
    for row in rows:
        timestamp = row.get("timestamp") or row.get("date")
        normalized.append(
            {
                "timestamp": str(timestamp),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row.get("volume", 0.0)),
            }
        )
    return normalized


def _load_json_candles(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "results" in payload:
        return trade_labels._load_candles(path)
    if not isinstance(payload, list):
        raise ValueError(f"unsupported candle payload in {path}")
    return payload


def _load_feather_candles(path: Path) -> list[dict[str, Any]]:
    import pandas as pd

    frame = pd.read_feather(path)
    timestamp_column = "date" if "date" in frame.columns else "timestamp"
    required = {"open", "high", "low", "close"}
    if not required.issubset(frame.columns):
        missing = sorted(required - set(frame.columns))
        raise ValueError(f"missing candle columns {missing} in {path}")
    rows: list[dict[str, Any]] = []
    for row in frame.itertuples(index=False):
        data = row._asdict()
        rows.append(
            {
                "timestamp": _normalize_timestamp(data[timestamp_column]),
                "open": float(data["open"]),
                "high": float(data["high"]),
                "low": float(data["low"]),
                "close": float(data["close"]),
                "volume": float(data.get("volume", 0.0) or 0.0),
            }
        )
    return rows


def load_candles(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".csv":
        return _load_csv_candles(path)
    if path.suffix == ".json":
        return _load_json_candles(path)
    if path.suffix == ".feather":
        return _load_feather_candles(path)
    raise ValueError(f"unsupported candle file format: {path}")


def load_candles_by_pair(candles_dir: Path) -> dict[str, list[dict[str, Any]]]:
    pair_map: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(candles_dir.glob("*_USD-1m-futures.feather")):
        base = path.name.split("_USD-", 1)[0]
        pair_map[f"{base}/USD"] = load_candles(path)
    if not pair_map:
        raise FileNotFoundError(f"no *_USD-1m-futures.feather files found under {candles_dir}")
    return pair_map


def summarize_labels(labels: list[dict[str, Any]]) -> dict[str, Any]:
    total_net_return = round(sum(float(label.get("net_return", 0.0)) for label in labels), 6)
    pair_breakdown: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for label in labels:
        grouped[str(label.get("pair", ""))].append(label)
    for pair, pair_labels in grouped.items():
        pair_breakdown[pair] = {
            "label_count": len(pair_labels),
            "meta_label_wins": sum(int(label.get("meta_label", 0)) for label in pair_labels),
            "total_net_return": round(sum(float(label.get("net_return", 0.0)) for label in pair_labels), 6),
            "avg_realized_R": round(
                sum(float(label.get("realized_R", 0.0)) for label in pair_labels) / max(1, len(pair_labels)),
                6,
            ),
        }
    return {
        "label_count": len(labels),
        "meta_label_wins": sum(int(label.get("meta_label", 0)) for label in labels),
        "total_net_return": total_net_return,
        "pair_breakdown": pair_breakdown,
    }


def pair_trades_are_net_costed(trades: list[dict[str, Any]]) -> bool:
    return bool(trades) and all(bool(trade.get("profit_ratio_is_net")) for trade in trades)


def _pair_root(pair: str, fallback_symbol: str) -> str:
    text = str(pair or fallback_symbol).strip()
    if "/" in text:
        text = text.split("/", 1)[0]
    return cost_model.normalize_futures_root(text or fallback_symbol)


def _apply_verified_instrument_fee(
    labels: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    *,
    pair: str,
    fallback_symbol: str,
    sl_mult: float,
) -> dict[str, Any]:
    root = _pair_root(pair, fallback_symbol)
    profile = cost_model.assert_verified_for_promotion(root)
    adjusted = 0
    for label, trade in zip(labels, trades):
        if bool(trade.get("profit_ratio_is_net")):
            fee_fraction = 0.0
        else:
            entry_price = float(label["entry_price"])
            fee_fraction = profile.round_trip_fee_fraction(entry_price)
            adjusted += 1
        label["instrument_cost_round_turn_fraction"] = fee_fraction
        label["instrument_cost_model_status"] = profile.status
        label["instrument_cost_profile_id"] = profile.profile_id
        label["net_return"] = float(label["gross_return"]) - fee_fraction
        label["realized_R"] = label["net_return"] / sl_mult
        label["meta_label"] = 1 if label["net_return"] > 0.0 else 0
    return {
        "symbol_root": root,
        "cost_model_status": profile.status,
        "cost_profile_id": profile.profile_id,
        "adjusted_label_count": adjusted,
    }


def build_pair_artifacts(
    *,
    pair: str,
    trades: list[dict[str, Any]],
    candles: list[dict[str, Any]],
    factor_id: str,
    output_dir: Path,
    fallback_symbol: str,
    sl_mult: float,
) -> tuple[PairArtifacts, dict[str, Any]]:
    labels = trade_labels.build_labels(
        candles=candles,
        trade_wire=trades,
        sl_mult=sl_mult,
    )
    cost_summary = _apply_verified_instrument_fee(
        labels,
        trades,
        pair=pair,
        fallback_symbol=fallback_symbol,
        sl_mult=sl_mult,
    )
    for label in labels:
        label["pair"] = pair
    labels_path = output_dir / "labels" / f"{pair.replace('/', '_')}.jsonl"
    _write_jsonl(labels_path, labels)
    report = payoff.build_payoff_shape_report(
        candidate_id=f"{factor_id}:{pair.replace('/', '_')}",
        trades=labels,
        nb_trials=1,
        periods_per_year=252,
    )
    report_path = output_dir / "payoff" / f"{pair.replace('/', '_')}_payoff_report.json"
    _write_json(report_path, report)
    summary = summarize_labels(labels)
    return PairArtifacts(
        pair=pair,
        labels_jsonl=labels_path,
        payoff_report_json=report_path,
        label_count=summary["label_count"],
        meta_label_wins=summary["meta_label_wins"],
        total_net_return=summary["total_net_return"],
    ), cost_summary


def run_sidecar(
    *,
    output_dir: Path,
    factor_id: str,
    symbol: str,
    sl_mult: float,
    candles_by_pair: dict[str, list[dict[str, Any]]],
    trades: list[dict[str, Any]],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(output_dir / "trades.jsonl", trades)
    trades_by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        trades_by_pair[str(trade["pair"])].append(trade)

    pair_artifacts: list[PairArtifacts] = []
    cost_summaries: dict[str, dict[str, Any]] = {}
    portfolio_labels: list[dict[str, Any]] = []
    for pair, pair_trades in sorted(trades_by_pair.items()):
        candles = candles_by_pair.get(pair)
        if candles is None:
            raise KeyError(f"missing 1m candles for pair {pair}")
        pair_info, cost_summary = build_pair_artifacts(
            pair=pair,
            trades=pair_trades,
            candles=candles,
            factor_id=factor_id,
            output_dir=output_dir,
            fallback_symbol=symbol,
            sl_mult=sl_mult,
        )
        pair_artifacts.append(pair_info)
        cost_summaries[pair] = cost_summary
        portfolio_labels.extend(_read_jsonl(pair_info.labels_jsonl))

    portfolio_labels_path = output_dir / "labels" / "portfolio_labels.jsonl"
    _write_jsonl(portfolio_labels_path, portfolio_labels)
    portfolio_report = payoff.build_payoff_shape_report(
        candidate_id=factor_id,
        trades=portfolio_labels,
        nb_trials=1,
        periods_per_year=252,
    )
    purged_report = purged_cv.build_guard_report(
        labels=portfolio_labels,
        nb_trials=1,
        embargo_bars=1,
        fold_count=4,
    )
    portfolio_report.update(
        {
            "pbo": purged_report.get("pbo"),
            "oos_sharpe_lcb": purged_report.get("oos_sharpe_lcb"),
            "embargo_bars": purged_report.get("embargo_bars"),
            "leakage_flags": purged_report.get("leakage_flags", []),
            "purged_cv_gate": purged_report.get("purged_cv_gate"),
        }
    )
    effective_gate = str(portfolio_report.get("promotion_gate", "reject"))
    purged_gate = str(purged_report.get("purged_cv_gate", "reject"))
    if purged_gate in {"reject", "insufficient_data"}:
        effective_gate = "reject"
    elif purged_gate == "probe" and effective_gate == "promote":
        effective_gate = "probe"
    portfolio_report["promotion_gate"] = effective_gate
    if effective_gate == "reject" and "purged_cv_reject" not in portfolio_report["failure_tags"]:
        portfolio_report["failure_tags"].append("purged_cv_reject")

    payoff_report_path = output_dir / "payoff" / "portfolio_payoff_report.json"
    purged_path = output_dir / "payoff" / "portfolio_purged_cv_guard.json"
    _write_json(payoff_report_path, portfolio_report)
    _write_json(purged_path, purged_report)
    handoff = path_target.export_targets(
        labels_jsonl=portfolio_labels_path,
        payoff_report_json=payoff_report_path,
        output_dir=output_dir / "path_ranker",
        symbol=symbol,
        auxiliary_fields=["pair"],
    )
    label_summary = summarize_labels(portfolio_labels)
    result = {
        "ok": True,
        "factor_id": factor_id,
        "symbol": symbol,
        "trade_count": len(trades),
        "portfolio_summary": label_summary,
        "instrument_cost_models": cost_summaries,
        "payoff_gate": portfolio_report["promotion_gate"],
        "failure_tags": portfolio_report["failure_tags"],
        "purged_cv_gate": purged_report.get("purged_cv_gate"),
        "pair_artifacts": [
            {
                "pair": artifact.pair,
                "labels_jsonl": str(artifact.labels_jsonl),
                "payoff_report_json": str(artifact.payoff_report_json),
                "label_count": artifact.label_count,
                "meta_label_wins": artifact.meta_label_wins,
                "total_net_return": artifact.total_net_return,
            }
            for artifact in pair_artifacts
        ],
        "artifact_paths": {
            "trades_jsonl": str(output_dir / "trades.jsonl"),
            "portfolio_labels_jsonl": str(portfolio_labels_path),
            "portfolio_payoff_report_json": str(payoff_report_path),
            "portfolio_purged_cv_guard_json": str(purged_path),
            "path_ranker_summary_json": str(output_dir / "path_ranker" / "path_ranker_handoff_summary.json"),
        },
        "path_ranker_handoff": handoff,
    }
    _write_json(output_dir / "summary.json", result)
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the balanced TOMAC practical sidecar from an exact AQ root.")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--candles-dir", required=True)
    parser.add_argument("--trades-jsonl")
    parser.add_argument("--run-tomac")
    parser.add_argument("--strategy-name", default=DEFAULT_STRATEGY)
    parser.add_argument("--factor-id", default=DEFAULT_FACTOR_ID)
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--sl-mult", type=float, default=0.01)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = Path(args.output_dir).resolve()
    candles_by_pair = load_candles_by_pair(Path(args.candles_dir).resolve())
    if args.trades_jsonl:
        trades = _read_jsonl(Path(args.trades_jsonl).resolve())
    elif args.run_tomac:
        trades = export_trades_from_run_tomac(
            run_tomac_path=Path(args.run_tomac).resolve(),
            strategy_name=args.strategy_name,
            factor_id=args.factor_id,
        )
    else:
        raise SystemExit("either --trades-jsonl or --run-tomac is required")
    result = run_sidecar(
        output_dir=output_dir,
        factor_id=args.factor_id,
        symbol=args.symbol,
        sl_mult=args.sl_mult,
        candles_by_pair=candles_by_pair,
        trades=trades,
    )
    print(json.dumps(result, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
