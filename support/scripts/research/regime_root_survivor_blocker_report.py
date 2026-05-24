#!/usr/bin/env python3
"""Build a compact blocker report for a regime-rooted Gate 1 survivor."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import regime_factor_tree_normalizer as tree_normalizer


PRE_BAYES_ACCEPTED_GATE_STATUSES = {"pass", "pass_hard", "pass_neutralized"}
VALIDATION_MIN_ROWS = 30


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def get_path(payload: dict[str, Any], dotted: str, default: Any = None) -> Any:
    current: Any = payload
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def listify(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def boolish(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return None


def first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def intish(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if "/" in stripped:
            stripped = stripped.split("/", 1)[0].strip()
        try:
            return int(float(stripped))
        except ValueError:
            return None
    return None


def gate1_branch_path(gate1: dict[str, Any], filter_payload: dict[str, Any]) -> Any:
    evidence_assignments = filter_payload.get("evidence_assignments")
    if not isinstance(evidence_assignments, dict):
        evidence_assignments = {}
    branch_paths = gate1.get("branch_paths")
    first_branch_path = None
    if isinstance(branch_paths, list):
        first_branch_path = next((path for path in branch_paths if isinstance(path, str) and path), None)
    return first_present(
        evidence_assignments.get("regime_profit_branch_path"),
        gate1.get("branch_path"),
        gate1.get("regime_profit_branch_path"),
        gate1.get("rooted_branch_path"),
        gate1.get("branch_path_template"),
        first_branch_path,
    )


def survivor_hint_tokens(survivor_hints: list[Any] | None) -> set[str]:
    tokens: set[str] = set()
    for hint in survivor_hints or []:
        if not isinstance(hint, str):
            continue
        compact = hint.strip().lower()
        if not compact:
            continue
        tokens.add(compact)
        for separator in ("/", ":", "|", ",", " "):
            compact = compact.replace(separator, " ")
        tokens.update(part for part in compact.split() if part)
    return tokens


def row_matches_survivor_hints(row: dict[str, Any], survivor_tokens: set[str]) -> bool:
    if not survivor_tokens:
        return False
    for key in ("package_id", "strategy_id", "symbol", "contract"):
        value = row.get(key)
        if isinstance(value, str) and value.strip().lower() in survivor_tokens:
            return True
    return False


def extract_branch_labels(metrics: dict[str, Any], survivor_hints: list[Any] | None = None) -> dict[str, str]:
    labels: dict[str, str] = {}
    sources: list[dict[str, Any]] = [metrics]
    survivor_tokens = survivor_hint_tokens(survivor_hints)
    for key in ("provider_row", "cost_row"):
        value = metrics.get(key)
        if isinstance(value, dict):
            sources.append(value)
    nested_labels = metrics.get("labels")
    if isinstance(nested_labels, dict):
        sources.append(nested_labels)
    provider_rows = metrics.get("provider_rows")
    if isinstance(provider_rows, list):
        rows = [row for row in provider_rows if isinstance(row, dict)]
        matched_rows = [row for row in rows if row_matches_survivor_hints(row, survivor_tokens)]
        unmatched_rows = [row for row in rows if row not in matched_rows]
        sources.extend(matched_rows)
        sources.extend(unmatched_rows)

    label_keys = (
        "market",
        "product",
        "provider",
        "symbol",
        "symbols",
        "contract",
        "timeframe",
        "timeframes",
        "base_timeframe",
        "ladder_timeframes",
        "window",
        "duration",
        "category",
    )
    for source in sources:
        for key in label_keys:
            value = source.get(key)
            if isinstance(value, str) and value and key not in labels:
                labels[key] = value
    return labels


def cost_survivors_5bps(metrics: dict[str, Any]) -> list[Any]:
    survivors: list[Any] = []
    for key, value in metrics.items():
        if key == "exact_survivors_5bps" or (
            key.startswith("exact_") and key.endswith("_survivors_5bps")
        ):
            survivors.extend(listify(value))
    cost_rows: list[dict[str, Any]] = []
    for key in ("cost_row", "cost_rows", "cost_stress", "cost_stress_rows", "selected_gate1_row"):
        value = metrics.get(key)
        if isinstance(value, dict):
            cost_rows.append(value)
        elif isinstance(value, list):
            cost_rows.extend(row for row in value if isinstance(row, dict))

    for cost_row in cost_rows:
        try:
            trade_count = cost_row.get("trade_count") or 0
            net_5bps = first_present(
                cost_row.get("net_after_5bps_side_pct"),
                cost_row.get("net_after_5bps_per_side_pct"),
                cost_row.get("5bps_per_side_total_profit_pct"),
                cost_row.get("five_bps_per_side_pct"),
            )
            has_density = int(trade_count) > 0
            survives_5bps = cost_row.get("survives_5bps_per_side") is True or float(net_5bps) > 0.0
        except (TypeError, ValueError):
            has_density = False
            survives_5bps = False
        if has_density and survives_5bps:
            survivors.append(cost_row.get("label") or cost_row.get("package_id") or cost_row.get("strategy_id") or cost_row.get("symbol") or "cost_row")
    return sorted(set(survivors))


def validation_report(*sources: dict[str, Any]) -> dict[str, Any]:
    nested_sources: list[dict[str, Any]] = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        nested_sources.append(source)
        for key in ("validation", "structural_path_ranking_validation", "policy_training"):
            value = source.get(key)
            if isinstance(value, dict):
                nested_sources.append(value)
        lineage = source.get("split_reason_lineage")
        if isinstance(lineage, list):
            parsed = validation_from_lineage(lineage)
            if parsed:
                nested_sources.append(parsed)

    def first_int(*keys: str) -> int:
        for source in nested_sources:
            for key in keys:
                parsed = intish(source.get(key))
                if parsed is not None:
                    return parsed
        return 0

    raw_rows = first_int("raw_scored_mature_rows", "raw_scored_mature", "mature_rows")
    production_rows = first_int("production_validation_rows", "production_validation")
    observation_rows = first_int("observation_validation_rows", "observation_validation")
    raw_min = first_int("raw_scored_mature_min_rows") or VALIDATION_MIN_ROWS
    production_min = first_int("production_validation_min_rows") or VALIDATION_MIN_ROWS
    observation_min = first_int("observation_validation_min_rows") or VALIDATION_MIN_ROWS
    return {
        "raw_scored_mature_rows": raw_rows,
        "raw_scored_mature_min_rows": raw_min,
        "raw_scored_mature_shortfall_rows": max(0, raw_min - raw_rows),
        "production_validation_rows": production_rows,
        "production_validation_min_rows": production_min,
        "production_validation_shortfall_rows": max(0, production_min - production_rows),
        "observation_validation_rows": observation_rows,
        "observation_validation_min_rows": observation_min,
        "observation_validation_shortfall_rows": max(0, observation_min - observation_rows),
    }


def validation_from_lineage(lineage: list[Any]) -> dict[str, int]:
    parsed: dict[str, int] = {}
    pairs = {
        "raw_scored_mature": "raw_scored_mature",
        "production_validation": "production_validation",
        "observation_validation": "observation_validation",
    }
    for item in lineage:
        if not isinstance(item, str):
            continue
        for key, prefix in pairs.items():
            match = re.search(rf"\b{re.escape(key)}=(\d+)/(\d+)", item)
            if not match:
                continue
            parsed[f"{prefix}_rows"] = int(match.group(1))
            parsed[f"{prefix}_min_rows"] = int(match.group(2))
    return parsed


def classify(report: dict[str, Any]) -> tuple[str, list[str], str]:
    blockers: list[str] = []
    gate1 = report["gate1"]
    downstream = report["downstream"]
    pre_bayes = report["pre_bayes"]
    execution = report["execution_tree"]
    validation = report.get("validation", {})
    branch_path_violations = listify(report.get("branch_path_violations"))

    if not gate1["branch_fields_preserved"]:
        blockers.append("rooted_branch_metadata_not_preserved")
    for violation in branch_path_violations:
        blockers.append(f"branch_path_violation:{violation}")
    if not gate1["has_5bps_survivor"]:
        blockers.append("no_real_cost_5bps_survivor")
    if pre_bayes["gating_status"] not in PRE_BAYES_ACCEPTED_GATE_STATUSES:
        blockers.append(f"pre_bayes_{pre_bayes['gating_status'] or 'missing'}")
    for flag in pre_bayes["conflict_flags"]:
        if flag.startswith("pda_sequence"):
            continue
        blockers.append(f"pre_bayes_conflict:{flag}")
    if downstream["execution_candidate_status"] != "trade_candidate":
        blockers.append(f"execution_candidate_{downstream['execution_candidate_status'] or 'missing'}")
    if downstream["execution_readiness"] is None or downstream["execution_readiness"] < 0.65:
        blockers.append("execution_readiness_below_0_65")
    if downstream["transition_hazard"] is None or downstream["transition_hazard"] >= 0.60:
        blockers.append("transition_hazard_ge_0_60")
    if downstream["ranker_validation_ready"] is not True:
        blockers.append("ranker_validation_not_ready")
    if execution["path_ranker_score_visible_to_execution_tree"] and not execution["path_ranker_score_used_by_execution_tree"]:
        blockers.append("path_ranker_visible_but_not_used")
    if validation.get("raw_scored_mature_shortfall_rows", 0) > 0:
        blockers.append("raw_scored_mature_below_30")
    if validation.get("production_validation_shortfall_rows", 0) > 0:
        blockers.append("production_validation_below_30")
    if validation.get("observation_validation_shortfall_rows", 0) > 0:
        blockers.append("observation_validation_below_30")

    if not gate1["has_5bps_survivor"]:
        decision = "drop_gate1_economics"
        next_action = "rotate to a different public family or market cell before downstream."
    elif branch_path_violations:
        decision = "repair_branch_path_to_canonical_regime_root"
        next_action = "rewrite the branch path so it starts at the canonical main regime and move market/provider/symbol/timeframe into portability labels before rerunning downstream."
    elif any(item.startswith("pre_bayes_conflict:multi_timeframe_direction_conflict") for item in blockers):
        decision = "repair_same_root_mtf_and_regime_alignment"
        next_action = "rebuild exact-root inputs with complete real/derived MTF ladder and verify factor direction agrees with current regime before rerunning Pre-Bayes/BBN/CatBoost/execution tree."
    elif any(item.endswith("_below_30") for item in blockers):
        decision = "repair_same_root_validation_rows"
        next_action = "add same-root feedback rows with root evidence fields until raw-scored mature, production validation, and observation validation all reach 30/30 before promotion."
    elif "path_ranker_visible_but_not_used" in blockers:
        decision = "repair_execution_gate_status_before_ranker_consumption"
        next_action = "keep CatBoost score visible-only until execution_gate_status is pass; fix exact execution candidate materialization and validation rows first."
    elif not blockers:
        decision = "candidate_meets_current_gate_shape"
        next_action = "run full promotion verification, including fresh provider parity and repeated readiness stability."
    else:
        decision = "observe_only_execution_blocked"
        next_action = "preserve as observation and work the listed blockers without lowering gates."
    return decision, sorted(set(blockers)), next_action


def build_report(gate1_path: Path, execution_candidate_path: Path, execution_tree_path: Path) -> dict[str, Any]:
    gate1 = load_json(gate1_path)
    candidate = load_json(execution_candidate_path)
    tree = load_json(execution_tree_path)

    filter_payload = candidate.get("pre_bayes_evidence_filter")
    if not isinstance(filter_payload, dict):
        filter_payload = {}
    tree_output = tree.get("output") if isinstance(tree.get("output"), dict) else {}

    exact_5bps = cost_survivors_5bps(gate1)
    branch_path = gate1_branch_path(gate1, filter_payload)
    normalized_branch = tree_normalizer.normalize_branch_path(
        str(branch_path or ""),
        extract_branch_labels(gate1, exact_5bps),
    )
    report = {
        "schema_version": "regime-root-survivor-blocker-report/v1",
        "inputs": {
            "gate1_metrics": str(gate1_path),
            "execution_candidate": str(execution_candidate_path),
            "execution_tree": str(execution_tree_path),
        },
        "branch_path": branch_path,
        "canonical_branch_path": normalized_branch["canonical_branch_path"],
        "canonical_root_ok": normalized_branch["canonical_root_ok"],
        "branch_path_violations": normalized_branch["violations"],
        "branch_labels": normalized_branch["labels"],
        "branch_normalization_warnings": normalized_branch["warnings"],
        "gate1": {
            "branch_fields_preserved": bool(gate1.get("branch_fields_preserved") or branch_path),
            "has_5bps_survivor": bool(exact_5bps),
            "exact_5bps_survivors": exact_5bps,
            "rank_total_trade_count": gate1.get("rank_total_trade_count"),
            "decision": gate1.get("decision"),
        },
        "pre_bayes": {
            "gating_status": filter_payload.get("gating_status"),
            "evidence_quality_score": filter_payload.get("evidence_quality_score"),
            "conflict_flags": listify(filter_payload.get("conflict_flags")),
            "raw_market_regime_label": filter_payload.get("raw_market_regime_label"),
            "raw_factor_alignment": filter_payload.get("raw_factor_alignment"),
            "raw_multi_timeframe_direction_bias": filter_payload.get("raw_multi_timeframe_direction_bias"),
            "filtered_factor_alignment": filter_payload.get("filtered_factor_alignment"),
            "filtered_multi_timeframe_direction_bias": filter_payload.get("filtered_multi_timeframe_direction_bias"),
        },
        "downstream": {
            "execution_candidate_status": candidate.get("candidate_status"),
            "execution_candidate_actionable": boolish(candidate.get("actionable")),
            "execution_readiness": first_present(tree_output.get("execution_readiness"), get_path(candidate, "execution_triage.execution_readiness")),
            "transition_hazard": tree_output.get("hybrid_transition_hazard"),
            "pda_hybrid_alignment": boolish(tree_output.get("pda_hybrid_alignment")),
            "ranker_validation_ready": boolish(tree_output.get("ranker_validation_ready")),
        },
        "validation": validation_report(gate1, candidate, tree_output),
        "execution_tree": {
            "decision_hint": tree_output.get("decision_hint"),
            "gate_status": tree_output.get("gate_status"),
            "branch": tree_output.get("branch"),
            "branch_probability": tree_output.get("branch_probability"),
            "posterior_uncertainty": tree_output.get("posterior_uncertainty"),
            "path_ranker_score_visible_to_execution_tree": boolish(tree_output.get("path_ranker_score_visible_to_execution_tree")),
            "path_ranker_score_used_by_execution_tree": boolish(tree_output.get("path_ranker_score_used_by_execution_tree")),
        },
    }
    decision, blockers, next_action = classify(report)
    report["decision"] = decision
    report["blockers"] = blockers
    report["next_action"] = next_action
    report["promotion_allowed"] = decision == "candidate_meets_current_gate_shape"
    report["trade_usable"] = False
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Regime-Root Survivor Blocker Report",
        "",
        f"Decision: `{report['decision']}`",
        "",
        f"Branch: `{report.get('branch_path') or 'unknown'}`",
        f"Canonical branch: `{report.get('canonical_branch_path') or 'unknown'}`",
        f"Labels: `{json.dumps(report.get('branch_labels') or {}, sort_keys=True)}`",
        "",
        "## Gate 1",
        "",
        f"- branch_fields_preserved: `{report['gate1']['branch_fields_preserved']}`",
        f"- exact_5bps_survivors: `{','.join(report['gate1']['exact_5bps_survivors']) or 'none'}`",
        f"- rank_total_trade_count: `{report['gate1']['rank_total_trade_count']}`",
        "",
        "## Pre-Bayes / Execution",
        "",
        f"- pre_bayes_gating_status: `{report['pre_bayes']['gating_status']}`",
        f"- evidence_quality_score: `{report['pre_bayes']['evidence_quality_score']}`",
        f"- conflict_flags: `{','.join(report['pre_bayes']['conflict_flags']) or 'none'}`",
        f"- execution_candidate_status: `{report['downstream']['execution_candidate_status']}`",
        f"- execution_readiness: `{report['downstream']['execution_readiness']}`",
        f"- transition_hazard: `{report['downstream']['transition_hazard']}`",
        f"- pda_hybrid_alignment: `{report['downstream']['pda_hybrid_alignment']}`",
        f"- ranker_validation_ready: `{report['downstream']['ranker_validation_ready']}`",
        f"- raw_scored_mature: `{report['validation']['raw_scored_mature_rows']}/{report['validation']['raw_scored_mature_min_rows']}`",
        f"- production_validation: `{report['validation']['production_validation_rows']}/{report['validation']['production_validation_min_rows']}`",
        f"- observation_validation: `{report['validation']['observation_validation_rows']}/{report['validation']['observation_validation_min_rows']}`",
        f"- path_ranker_visible: `{report['execution_tree']['path_ranker_score_visible_to_execution_tree']}`",
        f"- path_ranker_used: `{report['execution_tree']['path_ranker_score_used_by_execution_tree']}`",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- `{blocker}`" for blocker in report["blockers"])
    lines.extend(["", "## Next Action", "", report["next_action"], ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate1-metrics", required=True, type=Path)
    parser.add_argument("--execution-candidate", required=True, type=Path)
    parser.add_argument("--execution-tree", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    args = parser.parse_args()

    report = build_report(args.gate1_metrics, args.execution_candidate, args.execution_tree)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"decision": report["decision"], "blockers": report["blockers"], "output_json": str(args.output_json)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
