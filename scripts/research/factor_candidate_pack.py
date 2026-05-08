from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any


def _trade_density_label(trade_count: int) -> str:
    if trade_count <= 0:
        return "invalid"
    if trade_count < 10:
        return "anecdotal"
    if trade_count < 30:
        return "probe_only"
    if trade_count < 80:
        return "thin"
    return "preferred_density"


def _market_status(metrics: dict[str, Any]) -> str:
    trade_count = int(metrics.get("trade_count", 0) or 0)
    return "covered" if trade_count > 0 else "flat"


def _select_strategy(
    manifest: dict[str, Any],
    strategy_name: str | None,
) -> dict[str, Any]:
    strategies = manifest.get("strategies", [])
    if not strategies:
        raise ValueError("manifest contains no strategies")
    if strategy_name:
        for strategy in strategies:
            if strategy.get("name") == strategy_name:
                return strategy
        raise ValueError(f"strategy '{strategy_name}' not found in manifest")
    return strategies[0]


def _candidate_expression(
    strategy: dict[str, Any],
    manifest: dict[str, Any],
    candidate_spec: dict[str, Any],
) -> dict[str, Any]:
    metadata = strategy.get("metadata", {})
    operator_set = candidate_spec.get("operator_set") or metadata.get("factors_used", [])
    return {
        "schema_version": "factor-expression/v1",
        "strategy_name": strategy.get("name"),
        "mutation_id": metadata.get("mutation_id"),
        "base_factor": metadata.get("base_factor"),
        "expression_text": candidate_spec.get("expression_text")
        or metadata.get("hypothesis", ""),
        "operator_set": operator_set,
        "complexity": candidate_spec.get("complexity", len(operator_set)),
        "paradigm": metadata.get("paradigm"),
        "expected_regime": metadata.get("expected_regime"),
        "target_market_hypothesis": candidate_spec.get(
            "target_market_hypothesis",
            list(strategy.get("per_pair_metrics", {}).keys()),
        ),
        "base_timeframe": candidate_spec.get("base_timeframe", manifest.get("timeframe")),
        "context_timeframes": candidate_spec.get("context_timeframes", []),
        "regime_role": candidate_spec.get("regime_role", "mixed"),
    }


def _eval_grid_summary(
    strategy: dict[str, Any],
    manifest: dict[str, Any],
    candidate_spec: dict[str, Any],
    autoresearch_status: dict[str, Any],
) -> dict[str, Any]:
    aggregate = strategy.get("validation_metrics") or {}
    per_pair = strategy.get("per_pair_metrics") or {}
    breadth_matrix: dict[str, Any] = {}
    for market, metrics in per_pair.items():
        trade_count = int(metrics.get("trade_count", 0) or 0)
        breadth_matrix[market] = {
            "status": _market_status(metrics),
            "trade_count": trade_count,
            "trade_density_label": _trade_density_label(trade_count),
            "sharpe": metrics.get("sharpe"),
            "win_rate_pct": metrics.get("win_rate_pct"),
        }
    aggregate_trade_count = int(aggregate.get("trade_count", 0) or 0)
    return {
        "schema_version": "factor-eval-grid-summary/v1",
        "selected_strategy": strategy.get("name"),
        "timeframe": manifest.get("timeframe"),
        "breadth_matrix": breadth_matrix,
        "trade_density_summary": {
            "aggregate_trade_count": aggregate_trade_count,
            "aggregate_label": _trade_density_label(aggregate_trade_count),
            "covered_market_count": sum(
                1 for item in breadth_matrix.values() if item["status"] == "covered"
            ),
        },
        "aggregate_metrics": {
            "sharpe": aggregate.get("sharpe"),
            "win_rate_pct": aggregate.get("win_rate_pct"),
            "profit_factor": aggregate.get("profit_factor"),
            "total_profit_pct": aggregate.get("total_profit_pct"),
            "max_drawdown_pct": aggregate.get("max_drawdown_pct"),
            "trade_count": aggregate_trade_count,
        },
        "resonance_summary": candidate_spec.get(
            "resonance_summary",
            {
                "base_timeframe": candidate_spec.get(
                    "base_timeframe", manifest.get("timeframe")
                ),
                "context_stack": candidate_spec.get("context_timeframes", []),
                "resonance_by_timeframe": {},
            },
        ),
        "autoresearch": {
            "effective_status": autoresearch_status.get("effective_status"),
            "decision_counts": autoresearch_status.get("decision_counts", {}),
            "failure_tag_counts": autoresearch_status.get("failure_tag_counts", {}),
            "best_attempt_score_delta": (
                (autoresearch_status.get("best_attempt") or {})
                .get("decision", {})
                .get("score_delta")
            ),
        },
    }


def _transfer_score(strategy: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    per_pair = strategy.get("per_pair_metrics") or {}
    covered = []
    sharpe_values = []
    trade_counts = []
    for market, metrics in per_pair.items():
        trade_count = int(metrics.get("trade_count", 0) or 0)
        if trade_count > 0:
            covered.append(market)
            sharpe_values.append(float(metrics.get("sharpe", 0.0) or 0.0))
            trade_counts.append(trade_count)
    covered_count = len(covered)
    if covered_count <= 1:
        status = "single_market_only"
        overall_transfer_score = 0.0
    else:
        avg_sharpe = mean(sharpe_values) if sharpe_values else 0.0
        avg_trade_count = mean(trade_counts) if trade_counts else 0.0
        density_score = min(avg_trade_count / 80.0, 1.0)
        sharpe_score = max(min(avg_sharpe / 2.0, 1.0), 0.0)
        breadth_score = min(covered_count / 3.0, 1.0)
        overall_transfer_score = round(
            density_score * 0.35 + sharpe_score * 0.35 + breadth_score * 0.30,
            6,
        )
        status = "cross_market_candidate"
    return {
        "schema_version": "transfer-score/v1",
        "strategy_name": strategy.get("name"),
        "covered_market_count": covered_count,
        "covered_markets": covered,
        "status": status,
        "overall_transfer_score": overall_transfer_score,
        "average_sharpe": round(mean(sharpe_values), 6) if sharpe_values else 0.0,
        "average_trade_count": round(mean(trade_counts), 6) if trade_counts else 0.0,
        "timeframe": manifest.get("timeframe"),
    }


def build_factor_candidate_pack(
    *,
    manifest: dict[str, Any],
    strategy_name: str | None = None,
    candidate_spec: dict[str, Any] | None = None,
    autoresearch_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate_spec = candidate_spec or {}
    autoresearch_status = autoresearch_status or {}
    strategy = _select_strategy(manifest, strategy_name)
    return {
        "factor_expression": _candidate_expression(strategy, manifest, candidate_spec),
        "factor_eval_grid_summary": _eval_grid_summary(
            strategy, manifest, candidate_spec, autoresearch_status
        ),
        "transfer_score": _transfer_score(strategy, manifest),
    }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a white-box factor candidate pack from Auto-Quant manifest evidence."
    )
    parser.add_argument("--manifest-json", required=True)
    parser.add_argument("--strategy-name")
    parser.add_argument("--candidate-spec-json")
    parser.add_argument("--autoresearch-status-json")
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = _load_json(Path(args.manifest_json))
    candidate_spec = (
        _load_json(Path(args.candidate_spec_json)) if args.candidate_spec_json else {}
    )
    autoresearch_status = (
        _load_json(Path(args.autoresearch_status_json))
        if args.autoresearch_status_json
        else {}
    )
    bundle = build_factor_candidate_pack(
        manifest=manifest,
        strategy_name=args.strategy_name,
        candidate_spec=candidate_spec,
        autoresearch_status=autoresearch_status,
    )
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in bundle.items():
        _write_json(output_dir / f"{name}.json", payload)
    print(
        json.dumps(
            {
                "ok": True,
                "output_dir": str(output_dir),
                "strategy_name": bundle["factor_expression"]["strategy_name"],
                "artifacts": [f"{name}.json" for name in bundle],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
