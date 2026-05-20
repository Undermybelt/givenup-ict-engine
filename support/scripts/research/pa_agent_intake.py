from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "pa-agent-intake/v1"
DEFAULT_STAGE = "observation_only"
DEFAULT_OUTPUT_DIR = Path("/tmp/ict-engine-pa-agent-intake")


DEFAULT_PERSONAL_PROFILE: dict[str, Any] = {
    "profile_id": "thrill3r-price-action-intake-v1",
    "base_timeframe": "1m",
    "context_timeframes": ["5m", "15m", "30m", "1h", "4h", "1d"],
    "daily_trade_target": "1-3",
    "strict_gate_policy": {
        "after_realistic_costs": True,
        "min_trade_density": "sufficient_for_daily_1_to_3",
        "aq_to_downstream_direction_consistent": True,
        "transition_hazard_lt": 0.60,
        "pda_hybrid_alignment": True,
        "execution_readiness_min": 0.65,
    },
    "promotion_policy": "never_promote_pa_agent_alone",
}


DEFAULT_TAXONOMY: list[dict[str, Any]] = [
    {
        "pa_agent_key": "spike",
        "main_regime": "TrendExpansion",
        "sub_regime": "price_action_spike",
        "candidate_use": "impulse or exhaustion observation",
    },
    {
        "pa_agent_key": "micro_channel",
        "main_regime": "TrendExpansion",
        "sub_regime": "micro_channel_continuation",
        "candidate_use": "small-cycle continuation filter",
    },
    {
        "pa_agent_key": "tight_channel",
        "main_regime": "TrendExpansion",
        "sub_regime": "tight_channel_continuation",
        "candidate_use": "pullback depth and continuation quality prior",
    },
    {
        "pa_agent_key": "normal_channel",
        "main_regime": "TrendExpansion",
        "sub_regime": "normal_channel_pullback",
        "candidate_use": "trend pullback/reclaim candidate filter",
    },
    {
        "pa_agent_key": "broad_channel",
        "main_regime": "TransitionOrWideTrend",
        "sub_regime": "broad_channel_two_sided_risk",
        "candidate_use": "hazard guard and lower sizing prior",
    },
    {
        "pa_agent_key": "trending_tr",
        "main_regime": "RangeCompression",
        "sub_regime": "trend_biased_trading_range",
        "candidate_use": "range breakout/reclaim observation",
    },
    {
        "pa_agent_key": "trading_range",
        "main_regime": "RangeCompression",
        "sub_regime": "balanced_trading_range",
        "candidate_use": "mean reversion and boundary reclaim observation",
    },
    {
        "pa_agent_key": "extreme_tr",
        "main_regime": "ExtremeChop",
        "sub_regime": "no_trade_disorder",
        "candidate_use": "execution block / observation only",
    },
    {
        "pa_agent_key": "unknown",
        "main_regime": "Unknown",
        "sub_regime": "insufficient_structure",
        "candidate_use": "block promotion and collect more evidence",
    },
]


DEFAULT_ROUTER_RULES: list[dict[str, Any]] = [
    {
        "when": {"cycle_position": ["micro_channel", "tight_channel", "normal_channel", "broad_channel"], "direction": "bullish"},
        "suggested_candidate_family": "price_action_bull_channel_context",
        "observation_tags": ["channel", "bullish", "pullback_or_continuation"],
    },
    {
        "when": {"cycle_position": ["micro_channel", "tight_channel", "normal_channel", "broad_channel"], "direction": "bearish"},
        "suggested_candidate_family": "price_action_bear_channel_context",
        "observation_tags": ["channel", "bearish", "pullback_or_continuation"],
    },
    {
        "when": {"cycle_position": "spike", "direction": "bullish"},
        "suggested_candidate_family": "bullish_spike_continuation_or_exhaustion",
        "observation_tags": ["spike", "bullish", "exhaustion_guard_required"],
    },
    {
        "when": {"cycle_position": "spike", "direction": "bearish"},
        "suggested_candidate_family": "bearish_spike_continuation_or_exhaustion",
        "observation_tags": ["spike", "bearish", "exhaustion_guard_required"],
    },
    {
        "when": {"cycle_position": ["trading_range", "trending_tr"]},
        "suggested_candidate_family": "range_boundary_reclaim_or_breakout",
        "observation_tags": ["range", "boundary", "false_breakout"],
    },
    {
        "when": {"detected_patterns_contains": "wedge"},
        "suggested_candidate_family": "wedge_compression_breakout_or_failure",
        "observation_tags": ["wedge", "compression", "transition_hazard"],
    },
    {
        "when": {"detected_patterns_contains": "reversal_attempt"},
        "suggested_candidate_family": "second_entry_reversal_attempt",
        "observation_tags": ["second_entry", "failed_breakout", "confirmation_required"],
    },
]


TRACE_SCHEMA: dict[str, Any] = {
    "required_fields": ["node_id", "question", "answer", "reason", "bar_range"],
    "answer_enum": ["是", "否", "中性", "等待", "不适用"],
    "terminal_outcomes": ["wait", "reject", "trade", "proceed"],
    "ict_engine_mapping": {
        "node_id": "evidence_step_id",
        "answer": "binary_or_neutral_observation",
        "reason": "human_rationale_untrusted_text",
        "bar_range": "source_window_hint",
        "branch": "normalized_direction_or_subtype",
    },
    "trust_boundary": "untrusted_observation_not_trade_proof",
}


@dataclass(frozen=True)
class IntakeConfig:
    output_dir: Path
    pa_agent_root: Path | None
    profile: dict[str, Any]
    source_mode: str
    include_prompt_inventory: bool


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _extract_cycle_enum(schema_text: str | None) -> list[str]:
    if not schema_text:
        return [item["pa_agent_key"] for item in DEFAULT_TAXONOMY]
    match = re.search(r'"cycle_position".*?"enum"\s*:\s*\[(.*?)\]', schema_text, re.S)
    if not match:
        return [item["pa_agent_key"] for item in DEFAULT_TAXONOMY]
    return re.findall(r'"([a-z_]+)"', match.group(1)) or [item["pa_agent_key"] for item in DEFAULT_TAXONOMY]


def _prompt_inventory(root: Path | None) -> list[str]:
    if root is None:
        return []
    prompt_dir = root / "prompt_engineering"
    if not prompt_dir.exists():
        return []
    return sorted(path.name for path in prompt_dir.glob("*.txt"))


def _source_summary(root: Path | None) -> dict[str, Any]:
    if root is None:
        return {"mode": "embedded_defaults", "pa_agent_detected": False}
    schema_path = root / "pa_agent" / "ai" / "prompts" / "schemas.py"
    router_path = root / "pa_agent" / "ai" / "router.py"
    schema_text = _safe_read(schema_path)
    router_text = _safe_read(router_path)
    warnings = []
    if schema_path.exists() and schema_text is None:
        warnings.append("schemas.py_unreadable")
    if router_path.exists() and router_text is None:
        warnings.append("router.py_unreadable")
    return {
        "mode": "opt_in_pa_agent_root",
        "pa_agent_detected": bool(schema_text or router_text),
        "cycle_position_enum": _extract_cycle_enum(schema_text),
        "router_rule_source_present": bool(router_text),
        "source_access_warnings": warnings,
    }


def _taxonomy_from_source(root: Path | None) -> list[dict[str, Any]]:
    source = _source_summary(root)
    observed_keys = set(source.get("cycle_position_enum") or [])
    taxonomy = []
    for item in DEFAULT_TAXONOMY:
        cloned = dict(item)
        cloned["source_present"] = (not observed_keys) or item["pa_agent_key"] in observed_keys
        taxonomy.append(cloned)
    return taxonomy


def _artifact_bundle(config: IntakeConfig) -> dict[str, Any]:
    taxonomy = _taxonomy_from_source(config.pa_agent_root)
    bundle = {
        "schema_version": SCHEMA_VERSION,
        "source": _source_summary(config.pa_agent_root),
        "consumer_contract": {
            "zero_config": True,
            "hotplug_config_supported": True,
            "token_friendly": True,
            "no_runtime_pollution": True,
            "trade_usable": False,
            "promotion_state": DEFAULT_STAGE,
            "consumer_choice": "Users may keep PA Agent intake disabled, use embedded defaults, or opt in with --pa-agent-root/--profile.",
        },
        "personal_profile": config.profile,
        "regime_taxonomy": taxonomy,
        "decision_trace_schema": TRACE_SCHEMA,
        "router_rules": DEFAULT_ROUTER_RULES,
        "candidate_pack_template": _candidate_pack_template(config.profile),
    }
    if config.include_prompt_inventory:
        bundle["prompt_inventory"] = _prompt_inventory(config.pa_agent_root)
    return bundle


def _candidate_pack_template(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "factor-expression/v1",
        "candidate_id": "pa_agent_price_action_observation_pack_v1",
        "display_name": "PA Agent Price Action Observation Pack",
        "family": "Board B",
        "status": "inactive_by_default",
        "promotion_state": "candidate_observation",
        "base_factor": "price_action_llm_trace_context",
        "expression_text": "PA Agent cycle_position + direction + gate_trace/decision_trace converted to untrusted observation evidence; never trade proof by itself.",
        "operator_set": [
            "cycle_position",
            "direction",
            "detected_patterns",
            "gate_trace",
            "decision_trace",
            "bar_range",
        ],
        "complexity": 3,
        "expected_regime": "TrendExpansion -> PriceActionContext -> pa_agent_trace_observation -> pa_agent_price_action_observation_pack_v1",
        "target_market_hypothesis": [
            "market/product/symbol/timeframe labels supplied by caller",
            "default ladder: " + ",".join(profile.get("context_timeframes", [])),
        ],
        "base_timeframe": profile.get("base_timeframe", "1m"),
        "context_timeframes": profile.get("context_timeframes", []),
        "regime_role": "weak prior and trace audit only",
        "filter_belief_execution_mapping": {
            "pre_bayes_targets": ["filtered_regime_label", "factor_uncertainty", "trace_consistency"],
            "belief_targets": ["regime_posterior_prior", "transition_hazard", "pa_trace_conflict"],
            "path_ranking_targets": ["regime_profit_branch_path", "trace_density", "historical_outcome_alignment"],
            "execution_tree_targets": ["execution_readiness", "no_trade_guard", "invalidation_level"],
            "feedback_update_learning_fields": ["realized_outcome", "regime_profit_branch_path", "trace_node_id", "bar_range"],
            "structural_feedback_required": True,
        },
        "admission_gate": profile.get("strict_gate_policy", {}),
        "trade_usable": False,
        "trade_usable_reason": "PA Agent is subjective LLM/price-action evidence; ict-engine downstream gates must promote separately.",
    }


def write_artifacts(config: IntakeConfig) -> dict[str, Path]:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    bundle = _artifact_bundle(config)
    paths = {
        "bundle": config.output_dir / "pa_agent_intake_bundle.json",
        "regime_taxonomy": config.output_dir / "regime_taxonomy.json",
        "decision_trace_schema": config.output_dir / "decision_trace_schema.json",
        "router_rules": config.output_dir / "router_rules.json",
        "candidate_pack_template": config.output_dir / "candidate_pack_template.json",
    }
    paths["bundle"].write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    paths["regime_taxonomy"].write_text(json.dumps(bundle["regime_taxonomy"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    paths["decision_trace_schema"].write_text(json.dumps(bundle["decision_trace_schema"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    paths["router_rules"].write_text(json.dumps(bundle["router_rules"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    paths["candidate_pack_template"].write_text(json.dumps(bundle["candidate_pack_template"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return paths


def _build_config(args: argparse.Namespace) -> IntakeConfig:
    profile = dict(DEFAULT_PERSONAL_PROFILE)
    if args.profile:
        override = _read_json(Path(args.profile))
        profile.update(override)
    pa_agent_root = Path(args.pa_agent_root).expanduser().resolve() if args.pa_agent_root else None
    return IntakeConfig(
        output_dir=Path(args.output_dir).expanduser().resolve(),
        pa_agent_root=pa_agent_root,
        profile=profile,
        source_mode="opt_in" if pa_agent_root else "embedded_defaults",
        include_prompt_inventory=bool(args.include_prompt_inventory),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build PA Agent intake artifacts for ict-engine.")
    parser.add_argument("--pa-agent-root", default="", help="Optional PA_Agent repo root. If omitted, embedded defaults are used.")
    parser.add_argument("--profile", default="", help="Optional JSON profile overriding the built-in personal defaults.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Artifact directory. Defaults to /tmp.")
    parser.add_argument("--include-prompt-inventory", action="store_true", help="Include prompt_engineering/*.txt filenames when --pa-agent-root is provided.")
    parser.add_argument("--compact", action="store_true", help="Print one token-friendly status line.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = _build_config(args)
    paths = write_artifacts(config)
    if args.compact:
        print(
            "pa_agent_intake status=ok trade_usable=false mode={} artifacts={} taxonomy={} rules={}".format(
                config.source_mode,
                paths["bundle"],
                len(_taxonomy_from_source(config.pa_agent_root)),
                len(DEFAULT_ROUTER_RULES),
            )
        )
    else:
        print(json.dumps({key: str(value) for key, value in paths.items()}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())