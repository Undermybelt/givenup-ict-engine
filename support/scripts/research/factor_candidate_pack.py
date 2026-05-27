from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from statistics import mean
from typing import Any
import zipfile


def _trade_density_label(trade_count: int | None) -> str:
    if trade_count is None:
        return "external_evidence"
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
    if metrics.get("trade_count") is None:
        return "external_evidence" if metrics.get("sharpe") is not None else "flat"
    trade_count = int(metrics.get("trade_count", 0) or 0)
    return "covered" if trade_count > 0 else "flat"


def _branch_path_parts(branch_path: str) -> list[str]:
    return [part.strip() for part in branch_path.split("->") if part.strip()]


def _training_timeframe(base_timeframe: str | None, context_timeframes: list[Any]) -> str | None:
    if not base_timeframe:
        return None
    if context_timeframes and str(context_timeframes[0]) != str(base_timeframe):
        return f"{base_timeframe}_and_{context_timeframes[0]}"
    return str(base_timeframe)


def _timeframe_roles(candidate_spec: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    base_timeframe = candidate_spec.get("base_timeframe") or manifest.get("timeframe")
    context_timeframes = candidate_spec.get("context_timeframes") or []
    return {
        "training_timeframe": _training_timeframe(base_timeframe, context_timeframes),
        "neutralization_timeframe": (
            str(context_timeframes[1])
            if len(context_timeframes) >= 3
            else (str(context_timeframes[0]) if context_timeframes else None)
        ),
        "confirmation_timeframe": (
            str(context_timeframes[-1]) if context_timeframes else None
        ),
    }


def _branch_path_contract(
    candidate_spec: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any] | None:
    explicit = candidate_spec.get("branch_path_contract")
    if isinstance(explicit, dict):
        return explicit
    branch_path = candidate_spec.get("expected_regime")
    if not isinstance(branch_path, str) or "->" not in branch_path:
        return None
    parts = _branch_path_parts(branch_path)
    if len(parts) < 4:
        return None
    roles = _timeframe_roles(candidate_spec, manifest)
    contract = {
        "main_regime": parts[0],
        "sub_regime": parts[1],
        "sub_sub_regime_or_profit_factor": parts[2],
        "profit_factor": " -> ".join(parts[3:]),
        "regime_profit_branch_path": " -> ".join(parts),
        "branch_path_segments": parts,
        "branch_path_depth": len(parts),
        "branch_path_leaf": parts[-1],
    }
    for key, value in roles.items():
        if value:
            contract[key] = value
    return contract


def _timeframe_ladder_evidence(
    candidate_spec: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any] | None:
    explicit = candidate_spec.get("timeframe_ladder_evidence")
    if isinstance(explicit, dict):
        return explicit
    resonance = candidate_spec.get("resonance_summary")
    branch_path = candidate_spec.get("expected_regime")
    if not isinstance(resonance, dict) or not isinstance(branch_path, str):
        return None
    roles = _timeframe_roles(candidate_spec, manifest)
    return {
        "schema_version": "board-b-factor-refinement-timeframe-ladder/v1",
        "branch_path": branch_path,
        **{key: value for key, value in roles.items() if value},
        "resonance_summary": resonance,
        "promotion_state": candidate_spec.get("promotion_state"),
        "promotion_blocker": candidate_spec.get("promotion_blocker"),
    }


def _timeframe_ladder_transfer(
    candidate_spec: dict[str, Any],
) -> dict[str, Any] | None:
    explicit = candidate_spec.get("timeframe_ladder_transfer")
    if isinstance(explicit, dict):
        return explicit
    resonance = candidate_spec.get("resonance_summary")
    if not isinstance(resonance, dict):
        return None
    by_timeframe = resonance.get("resonance_by_timeframe") or {}
    confirmation = by_timeframe.get("4h") or by_timeframe.get("confirmation") or {}
    confirmation_decision = (
        confirmation.get("decision") if isinstance(confirmation, dict) else None
    )
    high_tf_result = (
        f"{confirmation_decision}_not_promotion"
        if confirmation_decision
        else "not_promoted"
    )
    return {
        "small_cycle_decision": (
            by_timeframe.get("5m", {}).get("decision")
            if isinstance(by_timeframe.get("5m"), dict)
            else None
        ),
        "medium_neutralization_result": (
            by_timeframe.get("1h", {}).get("decision")
            if isinstance(by_timeframe.get("1h"), dict)
            else None
        ),
        "high_timeframe_confirmation_result": high_tf_result,
        "promotion_allowed": False,
        "trade_usable": False,
        "promotion_blocker": candidate_spec.get("promotion_blocker"),
    }


def _signal_diagnostics_evidence(candidate_spec: dict[str, Any]) -> dict[str, Any] | None:
    explicit = candidate_spec.get("signal_diagnostics_evidence")
    if isinstance(explicit, dict):
        return explicit
    return None


def _signal_diagnostics_metadata(candidate_spec: dict[str, Any]) -> dict[str, Any] | None:
    evidence = _signal_diagnostics_evidence(candidate_spec)
    if not evidence:
        return None
    best_bucket = evidence.get("best_bucket") or {}
    ladder = evidence.get("timeframe_ladder_summary") or {}
    return {
        "schema_version": "candidate-pack-signal-diagnostics-evidence/v1",
        "source_schema_version": evidence.get("schema_version"),
        "diagnostic_only": True,
        "diagnostic_candidate_passed_gate": bool(
            evidence.get(
                "diagnostic_candidate_passed_gate",
                evidence.get("promotion_allowed"),
            )
        ),
        "requires_downstream_live_gates": True,
        "diagnostic_reason": (
            evidence.get("diagnostic_reason") or evidence.get("trade_usable_reason")
        ),
        "best_bucket": {
            "horizon": best_bucket.get("horizon"),
            "regime": best_bucket.get("regime"),
            "n": best_bucket.get("n"),
            "t_stat": best_bucket.get("t_stat"),
            "ic_spearman": best_bucket.get("ic_spearman"),
            "mean_signed_return_bps_after_cost": best_bucket.get(
                "mean_signed_return_bps_after_cost"
            ),
            "candidate_passed_gate": bool(best_bucket.get("candidate_passed_gate")),
        },
        "timeframe_ladder_summary": ladder if ladder else None,
    }


def _declared_friction_expectancy(metrics: dict[str, Any]) -> tuple[float | None, list[str]]:
    blockers: list[str] = []
    for key in (
        "net_after_declared_friction_pct",
        "instrument_cost_total_profit_pct",
        "net_after_5bps_side_pct",
        "net_after_5bps_per_side_pct",
        "5bps_per_side_total_profit_pct",
    ):
        value = metrics.get(key)
        if value is not None:
            return float(value), blockers
    raw_profit = metrics.get("total_profit_pct")
    if raw_profit is not None:
        blockers.append("declared_friction_missing_raw_profit_only")
        return float(raw_profit), blockers
    blockers.append("declared_friction_expectancy_missing")
    return None, blockers


def _factor_profitability_lifecycle(
    candidate_spec: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    regime_confidence = candidate_spec.get("regime_confidence")
    expectancy, expectancy_blockers = _declared_friction_expectancy(metrics)
    leakage_passed = candidate_spec.get("leakage_check", "pass") == "pass"
    provider_state = candidate_spec.get("provider_state", "ready")

    if regime_confidence is None:
        blockers.append("regime_confidence_missing")
    elif float(regime_confidence) < float(candidate_spec.get("regime_confidence_floor", 0.95)):
        blockers.append("regime_confidence_below_floor")
    if not leakage_passed:
        blockers.append("leakage_check_failed")
    if provider_state == "blocked":
        blockers.append("provider_state_blocked")
    blockers.extend(expectancy_blockers)
    if expectancy is not None and float(expectancy) <= 0.0:
        blockers.append("declared_friction_expectancy_non_positive")

    learning_ok = not blockers
    evidence_count = int(metrics.get("trade_count") or 0)
    return {
        "schema_version": "factor-profitability-lifecycle/v1",
        "learning_admission": {
            "status": "admitted" if learning_ok else "blocked",
            "long_run_expectancy_after_declared_friction": expectancy,
            "evidence_count": evidence_count,
            "leakage_check": "pass" if leakage_passed else "fail",
            "provider_state": provider_state,
            "blockers": [] if learning_ok else blockers,
        },
        "paper_admission": {
            "status": "observe",
            "blockers": ["forward_validation_required", *expectancy_blockers],
        },
        "live_trade": {
            "status": "blocked",
            "promotion_allowed": False,
            "trade_usable": False,
            "update_goal": False,
            "blockers": ["live_execution_gate_not_evaluated"],
        },
    }


def _win_rate_pct(value: Any) -> float | None:
    if value is None:
        return None
    win_rate = float(value)
    if win_rate <= 1.0:
        win_rate *= 100.0
    return round(win_rate, 6)


def _max_drawdown_pct(value: Any) -> float | None:
    if value is None:
        return None
    drawdown = abs(float(value))
    if drawdown <= 1.0:
        drawdown *= 100.0
    return round(drawdown, 6)


def _docstring_metadata(source_text: str) -> dict[str, Any]:
    try:
        module = ast.parse(source_text)
    except SyntaxError:
        return {}
    doc = ast.get_docstring(module) or ""
    metadata: dict[str, Any] = {}
    for raw_line in doc.splitlines():
        line = raw_line.strip()
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        normalized_key = key.strip().lower().replace(" ", "_")
        value = value.strip()
        if not value:
            continue
        if normalized_key == "paradigm":
            metadata["paradigm"] = value
        elif normalized_key == "hypothesis":
            metadata["hypothesis"] = value
        elif normalized_key == "strategy":
            metadata["strategy"] = value
        elif normalized_key == "mutation_id":
            metadata["mutation_id"] = value
        elif normalized_key == "base_factor":
            metadata["base_factor"] = value
        elif normalized_key == "expected_regime":
            metadata["expected_regime"] = value
        elif normalized_key == "factors_used":
            metadata["factors_used"] = [
                item.strip() for item in value.split(",") if item.strip()
            ] or [value]
        elif normalized_key == "parent":
            metadata["parent_strategy"] = value
        elif normalized_key == "asset_class":
            metadata["asset_class"] = value
        elif normalized_key == "status":
            metadata["status_hint"] = value
        elif normalized_key == "created":
            metadata["created"] = value
        elif normalized_key == "external_data":
            metadata["external_data"] = value
        elif normalized_key == "uses_mtf":
            metadata["uses_mtf"] = value.lower() == "yes"
    return metadata


def _branch_path_fields(expected_regime: Any) -> dict[str, str]:
    branch_path = str(expected_regime or "").strip()
    if not branch_path:
        return {
            "main_regime": "",
            "sub_regime": "",
            "sub_sub_regime_or_profit_factor": "",
            "profit_factor": "",
            "regime_profit_branch_path": "",
            "branch_path_segments": [],
            "branch_path_depth": 0,
            "branch_path_leaf": "",
        }
    parts = [part.strip() for part in branch_path.split("->") if part.strip()]
    return {
        "main_regime": parts[0] if len(parts) > 0 else "",
        "sub_regime": parts[1] if len(parts) > 1 else "",
        "sub_sub_regime_or_profit_factor": parts[2] if len(parts) > 2 else "",
        "profit_factor": " -> ".join(parts[3:]) if len(parts) > 3 else "",
        "regime_profit_branch_path": " -> ".join(parts),
        "branch_path_segments": parts,
        "branch_path_depth": len(parts),
        "branch_path_leaf": parts[-1] if parts else "",
    }


def build_manifest_from_freqtrade_backtest_zip(zip_path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(zip_path) as archive:
        result_name = next(
            (
                name
                for name in archive.namelist()
                if name.endswith(".json") and not name.endswith("_config.json")
            ),
            None,
        )
        if not result_name:
            raise ValueError(f"{zip_path} does not contain a backtest result JSON")

        config_name = next(
            (name for name in archive.namelist() if name.endswith("_config.json")),
            None,
        )
        result_payload = json.loads(archive.read(result_name))
        config_payload = (
            json.loads(archive.read(config_name)) if config_name else {}
        )

        strategies: list[dict[str, Any]] = []
        for strategy_name, payload in (result_payload.get("strategy") or {}).items():
            strategy_source_name = next(
                (
                    name
                    for name in archive.namelist()
                    if name.endswith(f"{strategy_name}.py")
                ),
                None,
            )
            strategy_metadata = {}
            if strategy_source_name:
                strategy_metadata = _docstring_metadata(
                    archive.read(strategy_source_name).decode("utf-8")
                )

            pair_metrics: dict[str, Any] = {}
            total_pair_metrics: dict[str, Any] | None = None
            for item in payload.get("results_per_pair", []):
                key = item.get("key")
                if not key:
                    continue
                metrics = {
                    "sharpe": item.get("sharpe"),
                    "trade_count": int(item.get("trades", 0) or 0),
                    "win_rate_pct": _win_rate_pct(item.get("winrate")),
                    "profit_factor": item.get("profit_factor"),
                    "total_profit_pct": item.get("profit_total_pct"),
                    "max_drawdown_pct": _max_drawdown_pct(
                        item.get("max_drawdown_account")
                    ),
                }
                if key == "TOTAL":
                    total_pair_metrics = metrics
                else:
                    pair_metrics[key] = metrics

            aggregate_trade_count = int(
                payload.get("total_trades")
                or (total_pair_metrics or {}).get("trade_count")
                or 0
            )
            total_profit_pct = None
            if payload.get("profit_total") is not None:
                total_profit_pct = round(float(payload["profit_total"]) * 100.0, 6)
            elif total_pair_metrics:
                total_profit_pct = total_pair_metrics.get("total_profit_pct")

            strategies.append(
                {
                    "name": payload.get("strategy_name") or strategy_name,
                    "status": "ok",
                    "metadata": {
                        "strategy": strategy_name,
                        "mutation_id": strategy_metadata.get("mutation_id"),
                        "base_factor": strategy_metadata.get("base_factor"),
                        "hypothesis": strategy_metadata.get("hypothesis", ""),
                        "paradigm": strategy_metadata.get("paradigm"),
                        "expected_regime": strategy_metadata.get("expected_regime"),
                        "factors_used": strategy_metadata.get("factors_used", []),
                        "source_artifact": str(zip_path),
                        "strategy_source_name": strategy_source_name,
                        "parent_strategy": strategy_metadata.get("parent_strategy"),
                        "asset_class": strategy_metadata.get("asset_class"),
                        "status_hint": strategy_metadata.get("status_hint"),
                        "created": strategy_metadata.get("created"),
                        "uses_mtf": strategy_metadata.get("uses_mtf"),
                        "external_data": strategy_metadata.get("external_data"),
                    },
                    "validation_metrics": {
                        "sharpe": payload.get("sharpe"),
                        "trade_count": aggregate_trade_count,
                        "win_rate_pct": _win_rate_pct(
                            (
                                float(payload.get("wins")) / aggregate_trade_count
                                if payload.get("wins") is not None and aggregate_trade_count
                                else None
                            )
                        ),
                        "profit_factor": payload.get("profit_factor"),
                        "total_profit_pct": total_profit_pct,
                        "max_drawdown_pct": _max_drawdown_pct(
                            payload.get("max_drawdown_account")
                        ),
                    },
                    "per_pair_metrics": pair_metrics,
                }
            )

    if not strategies:
        raise ValueError(f"{zip_path} does not contain strategy results")

    timeframe = strategies[0]["validation_metrics"].get("timeframe") or config_payload.get(
        "timeframe"
    )
    if not timeframe:
        timeframe = next(
            (
                payload.get("timeframe")
                for payload in (result_payload.get("strategy") or {}).values()
                if payload.get("timeframe")
            ),
            None,
        )

    return {
        "manifest_version": "freqtrade-backtest-manifest/v1",
        "timeframe": timeframe,
        "strategies": strategies,
    }


def build_strategy_library_manifest_from_freqtrade_backtest_zip(
    zip_path: Path,
    *,
    repo_url: str = "",
    pinned_ref: str = "",
    config_path: str = "",
    log_path: str = "",
    exported_at: str | None = None,
) -> dict[str, Any]:
    manifest = build_manifest_from_freqtrade_backtest_zip(zip_path)
    strategies: list[dict[str, Any]] = []
    for strategy in manifest.get("strategies", []):
        metadata = strategy.get("metadata", {})
        strategy_name = strategy.get("name", "")
        per_pair_metrics = strategy.get("per_pair_metrics") or {}
        branch_fields = _branch_path_fields(metadata.get("expected_regime"))
        strategies.append(
            {
                "name": strategy_name,
                "file_path": metadata.get("strategy_source_name", ""),
                "metadata": {
                    "strategy": metadata.get("strategy", strategy_name),
                    "mutation_id": metadata.get("mutation_id", ""),
                    "base_factor": metadata.get("base_factor", ""),
                    "hypothesis": metadata.get("hypothesis", ""),
                    "paradigm": metadata.get("paradigm", ""),
                    "expected_regime": metadata.get("expected_regime", ""),
                    "main_regime": branch_fields["main_regime"],
                    "sub_regime": branch_fields["sub_regime"],
                    "sub_sub_regime_or_profit_factor": branch_fields[
                        "sub_sub_regime_or_profit_factor"
                    ],
                    "profit_factor": branch_fields["profit_factor"],
                    "regime_profit_branch_path": branch_fields[
                        "regime_profit_branch_path"
                    ],
                    "branch_path_segments": branch_fields["branch_path_segments"],
                    "branch_path_depth": branch_fields["branch_path_depth"],
                    "branch_path_leaf": branch_fields["branch_path_leaf"],
                    "factors_used": metadata.get("factors_used", []),
                    "parent": metadata.get("parent_strategy", ""),
                    "asset_class": metadata.get("asset_class", ""),
                    "status": metadata.get("status_hint", "active"),
                    "created": metadata.get("created", ""),
                },
                "status": strategy.get("status", "ok"),
                "validation_metrics": strategy.get("validation_metrics"),
                "per_pair_metrics": per_pair_metrics,
                "pairs": list(per_pair_metrics.keys()),
                "timerange": (
                    f"{strategy.get('validation_metrics', {}).get('backtest_start', '')}"
                ),
                "commit": pinned_ref,
                "error": None,
            }
        )
    return {
        "manifest_version": "1.0",
        "exported_at": exported_at or "",
        "auto_quant_repo_url": repo_url,
        "auto_quant_pinned_ref": pinned_ref,
        "config_path": config_path,
        "timeframe": manifest.get("timeframe", ""),
        "log_path": log_path,
        "strategies": strategies,
        "validation_errors": [],
    }


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
    branch_path_contract = _branch_path_contract(candidate_spec, manifest)
    return {
        "schema_version": "factor-expression/v1",
        "candidate_id": candidate_spec.get("candidate_id"),
        "display_name": candidate_spec.get("display_name"),
        "family": candidate_spec.get("family"),
        "status": candidate_spec.get("status"),
        "promotion_state": candidate_spec.get("promotion_state"),
        "strategy_name": strategy.get("name"),
        "mutation_id": candidate_spec.get("mutation_id") or metadata.get("mutation_id"),
        "base_factor": candidate_spec.get("base_factor") or metadata.get("base_factor"),
        "expression_text": candidate_spec.get("expression_text")
        or metadata.get("hypothesis", ""),
        "operator_set": operator_set,
        "complexity": candidate_spec.get("complexity", len(operator_set)),
        "paradigm": candidate_spec.get("paradigm") or metadata.get("paradigm"),
        "expected_regime": candidate_spec.get("expected_regime")
        or metadata.get("expected_regime"),
        "target_market_hypothesis": candidate_spec.get(
            "target_market_hypothesis",
            list(strategy.get("per_pair_metrics", {}).keys()),
        ),
        "base_timeframe": candidate_spec.get("base_timeframe", manifest.get("timeframe")),
        "context_timeframes": candidate_spec.get("context_timeframes", []),
        "branch_path_contract": branch_path_contract,
        "regime_role": candidate_spec.get("regime_role", "mixed"),
        "evidence_window": candidate_spec.get("evidence_window"),
        "strategy_source": candidate_spec.get("strategy_source"),
        "filter_belief_execution_mapping": {
            "pre_bayes_targets": candidate_spec.get("pre_bayes_targets", []),
            "belief_targets": candidate_spec.get("belief_targets", []),
            "path_ranking_targets": candidate_spec.get("path_ranking_targets", []),
            "execution_tree_targets": candidate_spec.get("execution_tree_targets", []),
            "execution_tree_blockers_intended": candidate_spec.get(
                "execution_tree_blockers_intended", []
            ),
            "structural_feedback_required": candidate_spec.get(
                "structural_feedback_required", False
            ),
        },
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
            "profit_factor": metrics.get("profit_factor"),
            "total_profit_pct": metrics.get("total_profit_pct"),
            "max_drawdown_pct": metrics.get("max_drawdown_pct"),
        }
    for market, metrics in (candidate_spec.get("cross_market_metrics") or {}).items():
        if market in breadth_matrix:
            continue
        trade_count = metrics.get("trade_count")
        breadth_matrix[market] = {
            "status": _market_status(metrics),
            "trade_count": trade_count,
            "trade_density_label": _trade_density_label(
                int(trade_count) if trade_count is not None else None
            ),
            "sharpe": metrics.get("sharpe"),
            "win_rate_pct": metrics.get("win_rate_pct"),
            "profit_factor": metrics.get("profit_factor"),
            "total_profit_pct": metrics.get("total_profit_pct"),
            "max_drawdown_pct": metrics.get("max_drawdown_pct"),
            "source_window": metrics.get("window"),
            "evidence_source": metrics.get("evidence_source", "candidate_spec"),
            "notes": metrics.get("notes", []),
        }
    aggregate_trade_count = int(aggregate.get("trade_count", 0) or 0)
    timeframe_ladder_evidence = _timeframe_ladder_evidence(candidate_spec, manifest)
    signal_diagnostics = _signal_diagnostics_metadata(candidate_spec)
    lifecycle = _factor_profitability_lifecycle(candidate_spec, aggregate)
    return {
        "schema_version": "factor-eval-grid-summary/v1",
        "selected_strategy": strategy.get("name"),
        "timeframe": manifest.get("timeframe"),
        "candidate_status": candidate_spec.get("status"),
        "promotion_state": candidate_spec.get("promotion_state"),
        "factor_profitability_lifecycle": lifecycle,
        "timeframe_ladder_evidence": timeframe_ladder_evidence,
        "signal_diagnostics_evidence": signal_diagnostics,
        "breadth_matrix": breadth_matrix,
        "trade_density_summary": {
            "aggregate_trade_count": aggregate_trade_count,
            "aggregate_label": _trade_density_label(aggregate_trade_count),
            "covered_market_count": sum(
                1
                for item in breadth_matrix.values()
                if item["status"] in {"covered", "external_evidence"}
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
        "cross_market_evidence": candidate_spec.get("cross_market_metrics", {}),
    }


def _transfer_score(
    strategy: dict[str, Any],
    manifest: dict[str, Any],
    candidate_spec: dict[str, Any],
) -> dict[str, Any]:
    per_pair = strategy.get("per_pair_metrics") or {}
    aggregate = strategy.get("validation_metrics") or {}
    market_evidence: dict[str, Any] = {
        market: {**metrics, "evidence_source": "manifest"}
        for market, metrics in per_pair.items()
    }
    for market, metrics in (candidate_spec.get("cross_market_metrics") or {}).items():
        market_evidence.setdefault(
            market,
            {**metrics, "evidence_source": metrics.get("evidence_source", "candidate_spec")},
        )

    covered = []
    sharpe_values = []
    trade_counts = []
    markets_without_trade_counts = []
    for market, metrics in market_evidence.items():
        trade_count = metrics.get("trade_count")
        has_trade_count = trade_count is not None and int(trade_count or 0) > 0
        has_quality_signal = metrics.get("sharpe") is not None
        if has_trade_count or has_quality_signal:
            covered.append(market)
            if metrics.get("sharpe") is not None:
                sharpe_values.append(float(metrics.get("sharpe", 0.0) or 0.0))
            if has_trade_count:
                trade_counts.append(int(trade_count or 0))
            else:
                markets_without_trade_counts.append(market)
    covered_count = len(covered)
    profitability_expectancy, profitability_blockers = _declared_friction_expectancy(aggregate)
    profitability_positive = (
        profitability_expectancy is not None
        and profitability_expectancy > 0.0
        and not profitability_blockers
    )
    if profitability_positive:
        profitability_status = "declared_friction_positive"
        profitability_score = min(float(profitability_expectancy) / 5.0, 1.0)
    elif profitability_expectancy is not None and profitability_expectancy <= 0.0:
        profitability_status = "declared_friction_non_positive"
        profitability_score = 0.0
    else:
        profitability_status = "declared_friction_missing"
        profitability_score = 0.0
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
            density_score * 0.25
            + sharpe_score * 0.20
            + breadth_score * 0.20
            + profitability_score * 0.35,
            6,
        )
        status = "cross_market_candidate"
    return {
        "schema_version": "transfer-score/v1",
        "strategy_name": strategy.get("name"),
        "covered_market_count": covered_count,
        "covered_markets": covered,
        "markets_without_trade_counts": markets_without_trade_counts,
        "status": status,
        "overall_transfer_score": overall_transfer_score,
        "profitability_status": profitability_status,
        "profitability_blockers": profitability_blockers,
        "long_run_expectancy_after_declared_friction": profitability_expectancy,
        "average_sharpe": round(mean(sharpe_values), 6) if sharpe_values else 0.0,
        "average_trade_count": round(mean(trade_counts), 6) if trade_counts else 0.0,
        "timeframe": manifest.get("timeframe"),
        "market_evidence": market_evidence,
        "branch_path_contract": _branch_path_contract(candidate_spec, manifest),
        "timeframe_ladder_transfer": _timeframe_ladder_transfer(candidate_spec),
        "evidence_source": (
            "manifest+candidate_spec"
            if candidate_spec.get("cross_market_metrics")
            else "manifest_only"
        ),
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
        "transfer_score": _transfer_score(strategy, manifest, candidate_spec),
    }


def _demo_manifest() -> dict[str, Any]:
    return {
        "manifest_version": "1.0",
        "timeframe": "1m",
        "strategies": [
            {
                "name": "DemoSignalDiagnosticsCandidate",
                "status": "ok",
                "metadata": {
                    "strategy": "DemoSignalDiagnosticsCandidate",
                    "mutation_id": "demo-signal-diagnostics-v1",
                    "base_factor": "demo_signal",
                    "hypothesis": "zero-config candidate-pack smoke path",
                    "paradigm": "diagnostic_demo",
                    "expected_regime": "Transition -> Demo -> demo_signal -> demo_signal_v1",
                    "factors_used": ["demo_signal"],
                    "asset_class": "demo",
                },
                "validation_metrics": {
                    "sharpe": 1.0,
                    "trade_count": 40,
                    "win_rate_pct": 55.0,
                    "profit_factor": 1.2,
                    "total_profit_pct": 1.0,
                    "max_drawdown_pct": 1.0,
                },
                "per_pair_metrics": {
                    "DEMO/USD": {
                        "sharpe": 1.0,
                        "trade_count": 40,
                        "win_rate_pct": 55.0,
                        "profit_factor": 1.2,
                    }
                },
            }
        ],
    }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _compact_line(summary: dict[str, Any]) -> str:
    return (
        "factor_candidate_pack "
        f"ok={str(summary['ok']).lower()} "
        f"strategy={summary['strategy_name']} "
        f"artifacts={len(summary['artifacts'])} "
        f"output_dir={summary['output_dir']}"
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a white-box factor candidate pack from Auto-Quant manifest evidence."
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--manifest-json")
    source_group.add_argument("--freqtrade-backtest-zip")
    source_group.add_argument("--demo", action="store_true", help="Use bundled zero-config demo manifest")
    parser.add_argument("--strategy-name")
    parser.add_argument("--candidate-spec-json")
    parser.add_argument("--signal-diagnostics-json")
    parser.add_argument("--autoresearch-status-json")
    parser.add_argument("--emit-strategy-library-json")
    parser.add_argument("--repo-url", default="")
    parser.add_argument("--pinned-ref", default="")
    parser.add_argument("--config-path", default="")
    parser.add_argument("--log-path", default="")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--compact", action="store_true", help="Print one token-friendly summary line")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.manifest_json:
        manifest = _load_json(Path(args.manifest_json))
    elif args.freqtrade_backtest_zip:
        manifest = build_manifest_from_freqtrade_backtest_zip(
            Path(args.freqtrade_backtest_zip)
        )
    else:
        manifest = _demo_manifest()
    candidate_spec = (
        _load_json(Path(args.candidate_spec_json)) if args.candidate_spec_json else {}
    )
    if args.signal_diagnostics_json:
        candidate_spec = {
            **candidate_spec,
            "signal_diagnostics_evidence": _load_json(Path(args.signal_diagnostics_json)),
        }
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
    if args.emit_strategy_library_json:
        if not args.freqtrade_backtest_zip:
            raise ValueError("--emit-strategy-library-json requires --freqtrade-backtest-zip")
        strategy_manifest = build_strategy_library_manifest_from_freqtrade_backtest_zip(
            Path(args.freqtrade_backtest_zip),
            repo_url=args.repo_url,
            pinned_ref=args.pinned_ref,
            config_path=args.config_path,
            log_path=args.log_path,
        )
        _write_json(Path(args.emit_strategy_library_json).resolve(), strategy_manifest)
    summary = {
        "ok": True,
        "output_dir": str(output_dir),
        "strategy_name": bundle["factor_expression"]["strategy_name"],
        "artifacts": [f"{name}.json" for name in bundle],
    }
    if args.compact:
        print(_compact_line(summary))
    else:
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
