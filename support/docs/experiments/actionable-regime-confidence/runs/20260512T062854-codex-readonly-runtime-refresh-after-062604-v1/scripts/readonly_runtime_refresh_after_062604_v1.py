#!/usr/bin/env python3
"""Summarize read-only provider/runtime refresh evidence after the 062604 audit."""

from __future__ import annotations

import json
from pathlib import Path


RUN_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = RUN_ROOT / "readonly-runtime-refresh-after-062604-v1"
CHECK_DIR = RUN_ROOT / "checks"

TARGET_ROOTS = [
    Path("/tmp/ict-engine-board-a-r6-owner-export-v1"),
    Path("/tmp/ict-engine-native-subhour-source-label-intake"),
    Path("/tmp/ict-engine-source-panel-recency-extension"),
]


def read_json(name: str) -> dict:
    with (ARTIFACT_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text(name: str) -> str:
    return (ARTIFACT_DIR / name).read_text(encoding="utf-8")


def provider_status(provider_report: dict, provider_id: str) -> dict:
    for row in provider_report.get("providers", []):
        if row.get("provider_id") == provider_id:
            return {
                "ready": bool(row.get("ready")),
                "status": row.get("status"),
                "reason": row.get("reason"),
                "domain": row.get("domain"),
            }
    return {"ready": False, "status": "missing", "reason": "not_reported", "domain": None}


def main() -> int:
    provider = read_json("provider_status_agent.out")
    auto_quant_v71 = read_json("auto_quant_status_v71_state.json")
    auto_quant_fresh = read_json("auto_quant_status_fresh_state.json")
    analyze = read_json("analyze_live_nq_yfinance_agent.out")
    pre_bayes = read_json("pre_bayes_status_nq_post_analyze.json")
    workflow = read_json("workflow_status_nq_post_analyze_agent.out")
    policy = read_json("policy_training_status_nq_post_analyze.json")
    path_export = read_json("export_structural_path_ranking_target_nq_post_analyze.out")

    target_roots = {str(path): path.exists() for path in TARGET_ROOTS}
    provider_readiness = {
        key: provider_status(provider, key)
        for key in [
            "yfinance",
            "kraken_cli",
            "kraken_public",
            "ibkr",
            "ibkr_bridge",
            "tradingview_remix",
        ]
    }

    policy_entry_models = {
        row.get("entry_model_id"): {
            "ready": bool(row.get("ready")),
            "matched_rows": row.get("matched_rows"),
            "summary_line": row.get("summary_line"),
        }
        for row in policy.get("entry_models", [])
    }

    assertions = {
        "provider_status_called": True,
        "analyze_live_ran": bool(analyze.get("decision_summary")),
        "pre_bayes_pass_neutralized": pre_bayes.get("latest_gate_status") == "pass_neutralized",
        "workflow_blocked": workflow.get("blocking_status") in {"blocked", "fail_closed"},
        "policy_training_ready": any(row["ready"] for row in policy_entry_models.values()),
        "catboost_matched_rows_positive": any((row.get("matched_rows") or 0) > 0 for row in policy_entry_models.values()),
        "path_ranking_export_ready": bool(policy.get("structural_path_ranking_target", {}).get("export_ready")),
        "path_ranking_mature_rows_positive": (path_export.get("mature_rows") or 0) > 0,
        "required_roots_present": any(target_roots.values()),
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
    }

    report = {
        "run_id": "20260512T062854+0800-codex-readonly-runtime-refresh-after-062604-v1",
        "decision": "readonly_runtime_refresh_after_062604_v1=runtime_surfaces_called_no_required_root_no_promotion",
        "state_dir": "/private/tmp/ict-engine-board-a-readonly-runtime-after-062604-v1",
        "provider_summary": provider.get("summary_line"),
        "provider_readiness": provider_readiness,
        "auto_quant": {
            "v71_state_status": auto_quant_v71.get("status"),
            "v71_healthy": auto_quant_v71.get("healthy"),
            "v71_bootstrap_needed": auto_quant_v71.get("bootstrap_needed"),
            "fresh_state_status": auto_quant_fresh.get("status"),
            "fresh_healthy": auto_quant_fresh.get("healthy"),
            "fresh_bootstrap_needed": auto_quant_fresh.get("bootstrap_needed"),
        },
        "analyze_live": {
            "decision_summary": analyze.get("decision_summary"),
            "direction": analyze.get("direction"),
            "pre_bayes_gate": analyze.get("pre_bayes_gate"),
            "execution_gate": analyze.get("execution_triage", {}).get("gate_status"),
            "execution_branch": analyze.get("execution_triage", {}).get("branch"),
            "execution_score": analyze.get("execution_triage", {}).get("execution_score"),
            "next_step": analyze.get("next_step"),
            "evidence": analyze.get("evidence", []),
        },
        "pre_bayes": {
            "latest_gate_status": pre_bayes.get("latest_gate_status"),
            "latest_canonical_structural_active_regime": pre_bayes.get("latest_canonical_structural_active_regime"),
            "latest_canonical_structural_confidence": pre_bayes.get("latest_canonical_structural_confidence"),
            "latest_filtered_assignments": pre_bayes.get("latest_filtered_assignments"),
            "latest_uses_soft_evidence": pre_bayes.get("latest_uses_soft_evidence"),
        },
        "workflow": {
            "blocking_status": workflow.get("blocking_status"),
            "blocking_reason": workflow.get("blocking_reason"),
            "focus_phase": workflow.get("focus_phase"),
            "closed_loop_ready": workflow.get("closed_loop_branch_admission", {}).get("ready"),
            "closed_loop_status": workflow.get("closed_loop_branch_admission", {}).get("status"),
            "closed_loop_review_status": workflow.get("closed_loop_branch_admission", {}).get("review_status"),
            "next_step": workflow.get("next_step"),
        },
        "policy_training": {
            "analyze_runs": policy.get("analyze_runs"),
            "entry_models": policy_entry_models,
            "structural_path_ranking_validation": policy.get("structural_path_ranking_validation"),
            "structural_path_ranking_target": {
                "export_ready": policy.get("structural_path_ranking_target", {}).get("export_ready"),
                "rows": policy.get("structural_path_ranking_target", {}).get("rows"),
                "mature_rows": policy.get("structural_path_ranking_target", {}).get("mature_rows"),
                "raw_scored_mature_rows": policy.get("structural_path_ranking_target", {}).get("raw_scored_mature_rows"),
                "production_validation_rows": policy.get("structural_path_ranking_target", {}).get("production_validation_rows"),
                "trainer_artifact_ready": policy.get("structural_path_ranking_target", {}).get("trainer_artifact_ready"),
                "runtime_selection_enabled": policy.get("structural_path_ranking_target", {}).get("runtime_selection_enabled"),
            },
            "summary_line": policy.get("summary_line"),
        },
        "path_ranking_export": {
            "rows": path_export.get("rows"),
            "candidate_set_size": path_export.get("candidate_set_size"),
            "mature_rows": path_export.get("mature_rows"),
            "rows_with_propensity_estimate": path_export.get("rows_with_propensity_estimate"),
            "rows_with_calibrated_path_prob": path_export.get("rows_with_calibrated_path_prob"),
            "rows_with_training_weight": path_export.get("rows_with_training_weight"),
            "summary_line": path_export.get("summary_line"),
        },
        "required_target_roots": target_roots,
        "canonical_merge": False,
        "downstream_promotion_rerun": False,
        "strict_full_objective": False,
        "trade_usable": False,
        "update_goal": False,
        "assertions": assertions,
        "next_action": (
            "Keep this as read-only runtime evidence. Do not promote until one required "
            "source/control root unlocks; then rerun direct verifier, split calibration, "
            "canonical merge, providers, AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, "
            "and execution-tree readback in order."
        ),
    }

    summary_json = ARTIFACT_DIR / "readonly_runtime_refresh_after_062604_v1.json"
    summary_md = ARTIFACT_DIR / "readonly_runtime_refresh_after_062604_v1.md"
    assertions_out = CHECK_DIR / "readonly_runtime_refresh_after_062604_v1_assertions.out"

    summary_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Readonly Runtime Refresh After 062604 v1",
        "",
        f"Run id: `{report['run_id']}`",
        "",
        "## Decision",
        "",
        f"`{report['decision']}`",
        "",
        "Runtime surfaces were called, but this is non-promoting because the required source/control roots remain absent.",
        "",
        "## Surface Readback",
        "",
        f"- Provider status: `{report['provider_summary']}`.",
        f"- yfinance ready: `{str(provider_readiness['yfinance']['ready']).lower()}`; Kraken CLI ready: `{str(provider_readiness['kraken_cli']['ready']).lower()}`; IBKR market-data ready: `{str(provider_readiness['ibkr']['ready']).lower()}`.",
        f"- Auto-Quant checked state: `{report['auto_quant']['v71_state_status']}`; fresh state: `{report['auto_quant']['fresh_state_status']}`.",
        f"- analyze-live: `{report['analyze_live']['decision_summary']}`, direction `{report['analyze_live']['direction']}`, pre-Bayes `{report['analyze_live']['pre_bayes_gate']}`, execution gate `{report['analyze_live']['execution_gate']}`.",
        f"- Pre-Bayes post-analyze: `{report['pre_bayes']['latest_gate_status']}`, structural regime `{report['pre_bayes']['latest_canonical_structural_active_regime']}`, confidence `{report['pre_bayes']['latest_canonical_structural_confidence']}`.",
        f"- Workflow post-analyze: `{report['workflow']['blocking_status']}` / `{report['workflow']['blocking_reason']}`.",
        f"- Policy/CatBoost rows: `cisd={policy_entry_models.get('cisd_rb_long_v1', {}).get('matched_rows')}`, `breaker={policy_entry_models.get('breaker_rb_long_v1', {}).get('matched_rows')}`.",
        f"- Path-ranking export: rows `{report['path_ranking_export']['rows']}`, mature rows `{report['path_ranking_export']['mature_rows']}`, calibrated rows `{report['path_ranking_export']['rows_with_calibrated_path_prob']}`.",
        "",
        "## Required Roots",
        "",
    ]
    for path, exists in target_roots.items():
        lines.append(f"- `{path}`: `{str(exists).lower()}`")
    lines.extend(
        [
            "",
            "## Accounting",
            "",
            "- Canonical merge: `false`.",
            "- Downstream promotion rerun: `false`.",
            "- Strict full objective: `false`.",
            "- Trade usable: `false`.",
            "- `update_goal=false`.",
            "",
            "## Next",
            "",
            report["next_action"],
            "",
        ]
    )
    summary_md.write_text("\n".join(lines), encoding="utf-8")

    assertion_lines = [f"{key}={str(value).lower()}" for key, value in sorted(assertions.items())]
    assertions_out.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")

    if not assertions["provider_status_called"] or not assertions["analyze_live_ran"]:
        return 1
    if assertions["required_roots_present"] or assertions["update_goal"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
