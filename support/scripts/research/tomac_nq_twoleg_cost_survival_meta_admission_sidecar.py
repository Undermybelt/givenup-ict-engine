from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import factor_payoff_shape_report as payoff
import payoff_to_path_ranker_target as path_target
import purged_cv_backtest_guard as purged_cv
import real_trade_feedback_labels as trade_labels
import instrument_cost_model as cost_model


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
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def summarize_labels(labels: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for label in labels:
        grouped[str(label.get("pair", ""))].append(label)
    pair_breakdown: dict[str, dict[str, Any]] = {}
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
        "trade_count": len(labels),
        "pair_breakdown": pair_breakdown,
        "total_net_return": round(sum(float(label.get("net_return", 0.0)) for label in labels), 6),
    }


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


def build_pair_labels(
    *,
    pair: str,
    trades: list[dict[str, Any]],
    candles: list[dict[str, Any]],
    output_dir: Path,
    fallback_symbol: str,
    sl_mult: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
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
    _write_jsonl(output_dir / "labels" / f"{pair.replace('/', '_')}.jsonl", labels)
    return labels, cost_summary


def run_sidecar(
    *,
    output_dir: Path,
    factor_id: str,
    branch_path: str,
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

    portfolio_labels: list[dict[str, Any]] = []
    cost_summaries: dict[str, dict[str, Any]] = {}
    for pair, pair_trades in sorted(trades_by_pair.items()):
        candles = candles_by_pair.get(pair)
        if candles is None:
            raise KeyError(f"missing 1m candles for pair {pair}")
        pair_labels, cost_summary = build_pair_labels(
            pair=pair,
            trades=pair_trades,
            candles=candles,
            output_dir=output_dir,
            fallback_symbol=symbol,
            sl_mult=sl_mult,
        )
        portfolio_labels.extend(pair_labels)
        cost_summaries[pair] = cost_summary

    labels_path = output_dir / "labels" / "portfolio_labels.jsonl"
    _write_jsonl(labels_path, portfolio_labels)
    portfolio_summary = summarize_labels(portfolio_labels)

    payoff_report = payoff.build_payoff_shape_report(
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
    effective_gate = str(payoff_report.get("promotion_gate", "reject"))
    purged_gate = str(purged_report.get("purged_cv_gate", "reject"))
    if purged_gate in {"reject", "insufficient_data"}:
        effective_gate = "reject"
    elif purged_gate == "probe" and effective_gate == "promote":
        effective_gate = "probe"
    payoff_report["promotion_gate"] = effective_gate
    payoff_report["purged_cv_gate"] = purged_gate
    if effective_gate == "reject" and "purged_cv_reject" not in payoff_report["failure_tags"]:
        payoff_report["failure_tags"].append("purged_cv_reject")

    payoff_path = output_dir / "payoff" / "portfolio_payoff_report.json"
    purged_path = output_dir / "payoff" / "portfolio_purged_cv_guard.json"
    _write_json(payoff_path, payoff_report)
    _write_json(purged_path, purged_report)

    path_ranker = path_target.export_targets(
        labels_jsonl=labels_path,
        payoff_report_json=payoff_path,
        output_dir=output_dir / "path_ranker",
        symbol=symbol,
        auxiliary_fields=["pair", "regime_profit_branch_path", "profit_factor"],
    )

    summary = {
        "ok": True,
        "factor_id": factor_id,
        "branch_path": branch_path,
        "symbol": symbol,
        "trade_count": portfolio_summary["trade_count"],
        "portfolio_summary": portfolio_summary,
        "instrument_cost_models": cost_summaries,
        "payoff_gate": payoff_report["promotion_gate"],
        "purged_cv_gate": purged_gate,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "artifact_paths": {
            "trades_jsonl": str(output_dir / "trades.jsonl"),
            "labels_jsonl": str(labels_path),
            "payoff_report_json": str(payoff_path),
            "purged_cv_guard_json": str(purged_path),
            "path_ranker_handoff_summary_json": str(output_dir / "path_ranker" / "path_ranker_handoff_summary.json"),
        },
        "path_ranker_summary": path_ranker,
        "failure_tags": payoff_report.get("failure_tags", []),
        "next_recommended_layer": "same_root_autoquant_or_downstream_readback_required",
    }
    _write_json(output_dir / "summary.json", summary)
    return summary


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build fail-closed real-trade label/payoff artifacts for the TOMAC OpeningDriveTwoLeg CostSurvivalMetaAdmission child."
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--trade-wire-jsonl", required=True)
    parser.add_argument("--candles-json", action="append", default=[])
    parser.add_argument("--factor-id", required=True)
    parser.add_argument("--branch-path", required=True)
    parser.add_argument("--symbol", default="NQ")
    parser.add_argument("--sl-mult", type=float, default=0.01)
    args = parser.parse_args(argv)

    candles_by_pair: dict[str, list[dict[str, Any]]] = {}
    for item in args.candles_json:
        pair, path = item.split("=", 1)
        candles_by_pair[pair] = trade_labels._load_candles(Path(path))
    summary = run_sidecar(
        output_dir=Path(args.output_dir).resolve(),
        factor_id=args.factor_id,
        branch_path=args.branch_path,
        symbol=args.symbol,
        sl_mult=args.sl_mult,
        candles_by_pair=candles_by_pair,
        trades=_read_jsonl(Path(args.trade_wire_jsonl).resolve()),
    )
    print(json.dumps(summary, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
