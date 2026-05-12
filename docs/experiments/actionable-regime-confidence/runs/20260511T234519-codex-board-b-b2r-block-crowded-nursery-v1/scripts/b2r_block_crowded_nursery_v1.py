#!/usr/bin/env python3
"""Build the Board B B2R nursery packet for the 220646 execution blocker."""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[6]
RUN_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = RUN_ROOT / "b2r-nursery"

PREV_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T231800-codex-board-b-220646-exact-branch-closed-loop-readback-v4/"
    "exact-branch-closed-loop-readback-v4"
)
LIVE_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T233426-codex-board-b-220646-crisis-branch-live-replay-v1"
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def read_exit(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except FileNotFoundError:
        return None


def nested(data: dict, *keys, default=None):
    cur = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    previous = read_json(PREV_ROOT / "exact_branch_closed_loop_readback_v4.json")
    previous_trace = read_json(
        PREV_ROOT
        / "state_exact_branch_closed_loop_v4/SRC_ROOT_CARRY_LONG_220646/"
        "execution_tree_trace.json"
    )
    provider_status = read_json(RUN_ROOT / "logs/01_provider_status_agent.out")
    auto_quant_status = read_json(RUN_ROOT / "logs/02_auto_quant_status_local.out")
    readonly_execution = read_json(
        RUN_ROOT / "logs/03_workflow_execution_candidate_231800_readonly.out"
    )
    readonly_structural = read_json(
        RUN_ROOT / "logs/04_workflow_structural_bundle_231800_readonly.out"
    )
    readonly_pre_bayes = read_json(RUN_ROOT / "logs/05_pre_bayes_status_231800_readonly.out")
    live_analyze = read_json(LIVE_ROOT / "logs/03_analyze_live_crisis_bundle.out")
    live_execution = read_json(LIVE_ROOT / "logs/05_workflow_execution_candidate.out")
    live_structural = read_json(
        LIVE_ROOT / "logs/04b_workflow_structural_recommended_path_bundle.out"
    )

    branch_path = previous["workflow_bundle_path_id"]
    live_triage = live_analyze["execution_triage"]
    previous_trace_out = previous_trace["output"]

    ready_providers = [
        item["provider_id"]
        for item in provider_status.get("providers", [])
        if item.get("ready")
    ]
    provider_reasons = {
        item["provider_id"]: item.get("reason")
        for item in provider_status.get("providers", [])
        if item.get("provider_id")
        in {"yfinance", "tradingview_mcp", "kraken_cli", "ibkr", "kraken_public"}
    }

    gates = [
        {
            "gate": "nursery_status",
            "value": "incubation_only",
            "pass": True,
            "source": "Board B nursery contract",
        },
        {
            "gate": "exact_branch_path_preserved_previous",
            "value": str(previous["workflow_bundle_path_is_required_branch_path"]).lower(),
            "pass": bool(previous["workflow_bundle_path_is_required_branch_path"]),
            "source": "231800 exact-branch readback",
        },
        {
            "gate": "exact_branch_path_preserved_live_replay",
            "value": str(live_structural.get("path_id") == branch_path).lower(),
            "pass": live_structural.get("path_id") == branch_path,
            "source": "233426 workflow structural bundle",
        },
        {
            "gate": "previous_block_crowded_observed",
            "value": previous["execution_triage_branch"],
            "pass": previous["execution_triage_branch"] == "block_crowded",
            "source": "231800 execution tree",
        },
        {
            "gate": "fresh_execution_not_block_crowded",
            "value": live_triage["branch"],
            "pass": live_triage["branch"] != "block_crowded",
            "source": "233426 analyze-live execution triage",
        },
        {
            "gate": "fresh_execution_gate_observe_only",
            "value": live_triage["gate_status"],
            "pass": live_triage["gate_status"] == "observe",
            "source": "233426 analyze-live execution triage",
        },
        {
            "gate": "pre_bayes_live_gate",
            "value": live_analyze["pre_bayes_gate"],
            "pass": live_analyze["pre_bayes_gate"] == "pass_neutralized",
            "source": "233426 analyze-live",
        },
        {
            "gate": "catboost_ranker_history_ready",
            "value": previous["ranker_runtime_status"],
            "pass": bool(previous["ranker_runtime_ready"]),
            "source": "231800 closed-loop readback",
        },
        {
            "gate": "provider_status_exit0",
            "value": str(read_exit(RUN_ROOT / "logs/01_provider_status_agent.exit")),
            "pass": read_exit(RUN_ROOT / "logs/01_provider_status_agent.exit") == 0,
            "source": "fresh provider-status",
        },
        {
            "gate": "local_auto_quant_healthy",
            "value": str(auto_quant_status.get("healthy")).lower(),
            "pass": bool(auto_quant_status.get("healthy")),
            "source": "fresh local Auto-Quant status",
        },
        {
            "gate": "promotion_allowed",
            "value": "false",
            "pass": True,
            "source": "nursery feedback only; live replay is observe, not execute",
        },
    ]

    packet = {
        "schema_version": "board-b-b2r-block-crowded-nursery/v1",
        "run_id": "20260511T234519+0800-codex-board-b-b2r-block-crowded-nursery-v1",
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "recipe_id": "SourceRootStopCarryLongHorizonV1",
        "nursery_branch_id": "B2R-220646-crisis-block-crowded-execution-admissibility-v1",
        "nursery_status": "incubation_only",
        "parent_regime_root": "Crisis",
        "branch_path": branch_path,
        "action_leaf": "observe_or_skip_until_execution_context_compatible",
        "regime_prior_confidence": 85.7407,
        "previous_execution_feedback": {
            "source": str(PREV_ROOT / "exact_branch_closed_loop_readback_v4.json"),
            "execution_branch": previous["execution_triage_branch"],
            "execution_gate_status": previous["execution_triage_gate_status"],
            "execution_reason": previous["execution_triage_consumer_reason"],
            "execution_readiness": 0.4433,
            "decision_hint": previous_trace_out.get("decision_hint"),
            "path_ranker_visible": previous_trace_out.get(
                "path_ranker_score_visible_to_execution_tree"
            ),
            "path_ranker_used": previous_trace_out.get(
                "path_ranker_score_used_by_execution_tree"
            ),
        },
        "fresh_live_replay_feedback": {
            "source": str(LIVE_ROOT / "logs/03_analyze_live_crisis_bundle.out"),
            "execution_branch": live_triage["branch"],
            "execution_gate_status": live_triage["gate_status"],
            "execution_bias": live_triage["execution_bias"],
            "execution_score": live_triage["execution_score"],
            "execution_reason": live_triage["consumer_reason"],
            "decision_hint": live_triage["decision_hint"],
            "pre_bayes_gate": live_analyze["pre_bayes_gate"],
            "workflow_candidate_status": live_execution.get("candidate_status"),
            "workflow_review_status": live_execution.get("review_status"),
            "structural_path_preserved": live_structural.get("path_id") == branch_path,
            "factor_research_next_step_blocker": nested(
                live_analyze, "next_step", "blocked_reason"
            ),
        },
        "block_crowded_feature_packet": {
            "feature_name": "execution_admissibility_block_crowded_context_v1",
            "feature_role": "negative execution-admissibility / market-state feature",
            "previous_value": True,
            "fresh_value": False,
            "interpretation": (
                "The exact Crisis branch can move from block_crowded to fill_viable/observe "
                "as live market-state readiness changes. Keep this as nursery feedback and "
                "do not turn it into a promotion signal without execution-tree admit plus "
                "closed-loop confidence."
            ),
        },
        "provider_status": {
            "summary_line": provider_status.get("summary_line"),
            "ready_providers": ready_providers,
            "selected_provider_reasons": provider_reasons,
        },
        "auto_quant_status": {
            "status": auto_quant_status.get("status"),
            "healthy": auto_quant_status.get("healthy"),
            "data_ready": auto_quant_status.get("data_ready"),
            "managed_dir": auto_quant_status.get("managed_dir"),
            "notes": auto_quant_status.get("notes"),
        },
        "downstream_stage_readback": {
            "pre_bayes_gate_status": readonly_pre_bayes.get("latest_gate_status"),
            "bbn_soft_evidence_label_set": nested(
                readonly_pre_bayes, "latest_filtered_assignments", "read_only_regime_bbn_label_set"
            ),
            "catboost_ranker_runtime_status": nested(
                readonly_structural, "path_ranker_runtime", "status"
            ),
            "catboost_ranker_runtime_source": readonly_structural.get(
                "path_ranker_runtime_source"
            ),
            "execution_candidate_status": readonly_execution.get("candidate_status"),
            "execution_candidate_review_status": readonly_execution.get("review_status"),
        },
        "promotion_allowed": False,
        "promotion_blocker": (
            "incubation_only: fresh exact-branch replay is fill_viable/observe, not admitted "
            "execution; factor-research continuation also requires explicit historical data "
            "selection."
        ),
        "next_action": (
            "Record block_crowded/fill_viable as nursery execution-admissibility feedback; "
            "only rerun promotion when the exact branch reaches execution_tree_admitted or "
            "after a predeclared historical-data continuation is selected."
        ),
        "gates": gates,
    }

    json_path = OUT_DIR / "b2r_block_crowded_nursery_v1.json"
    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    gates_path = OUT_DIR / "b2r_block_crowded_nursery_v1_gates.csv"
    with gates_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["gate", "value", "pass", "source"])
        writer.writeheader()
        for row in gates:
            writer.writerow(row)

    assertions = [
        f"nursery_status={packet['nursery_status']}",
        f"branch_path_preserved_previous={previous['workflow_bundle_path_is_required_branch_path']}",
        f"branch_path_preserved_live_replay={live_structural.get('path_id') == branch_path}",
        f"previous_execution_branch={previous['execution_triage_branch']}",
        f"fresh_execution_branch={live_triage['branch']}",
        f"fresh_execution_gate={live_triage['gate_status']}",
        f"pre_bayes_live_gate={live_analyze['pre_bayes_gate']}",
        f"catboost_ranker_runtime_status={previous['ranker_runtime_status']}",
        f"provider_summary={provider_status.get('summary_line')}",
        f"auto_quant_local_status={auto_quant_status.get('status')}",
        f"promotion_allowed={packet['promotion_allowed']}",
        "update_goal=false",
    ]
    assertions_path = OUT_DIR / "b2r_block_crowded_nursery_v1_assertions.out"
    assertions_path.write_text("\n".join(assertions) + "\n")

    md_path = OUT_DIR / "b2r_block_crowded_nursery_v1.md"
    md_path.write_text(
        "\n".join(
            [
                "# B2R Block-Crowded Nursery v1",
                "",
                "## Decision",
                "",
                "`block_crowded` is retained as a negative execution-admissibility feature for the exact Crisis branch, but this packet is `incubation_only` and does not promote `220646`.",
                "",
                "## Branch",
                "",
                f"- Branch path: `{branch_path}`",
                "- Parent root: `Crisis`",
                "- Recipe: `SourceRootStopCarryLongHorizonV1`",
                "- Prior score: `85.7407` from strict RC-SPA; price roots stayed `4/4` passed in the source packet.",
                "",
                "## Evidence",
                "",
                f"- Previous exact-branch readback: `{previous['execution_triage_branch']}` / `{previous['execution_triage_gate_status']}` with readiness `0.4433 < 0.45`.",
                f"- Fresh live replay: `{live_triage['branch']}` / `{live_triage['gate_status']}` with execution score `{live_triage['execution_score']:.4f}`.",
                f"- Fresh Pre-Bayes gate: `{live_analyze['pre_bayes_gate']}`.",
                f"- Fresh structural bundle path preserved: `{live_structural.get('path_id') == branch_path}`.",
                f"- CatBoost/path-ranker runtime source remains `{readonly_structural.get('path_ranker_runtime_source')}` with status `{nested(readonly_structural, 'path_ranker_runtime', 'status')}`.",
                f"- Provider readback: `{provider_status.get('summary_line')}`.",
                f"- Local Auto-Quant readback: `{auto_quant_status.get('status')}`, healthy `{auto_quant_status.get('healthy')}`, data_ready `{auto_quant_status.get('data_ready')}`.",
                "",
                "## Interpretation",
                "",
                "The exact branch path reaches Pre-Bayes, BBN soft-evidence readback, CatBoost/path-ranker history, and execution-candidate surfaces. The prior blocked state and fresh observe state should be treated as branch-local execution-context feedback, not as a profitability rejection and not as a promotion signal.",
                "",
                "The live replay changed `block_crowded` to `fill_viable`, but the execution tree still returned `observe` and the workflow asks for explicit historical-data selection before factor-research continuation. Therefore the correct state is nursery feedback only.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path}`",
                f"- Gates: `{gates_path}`",
                f"- Assertions: `{assertions_path}`",
                "- Logs: `docs/experiments/actionable-regime-confidence/runs/20260511T234519-codex-board-b-b2r-block-crowded-nursery-v1/logs/`",
                "- Concurrent fresh replay consumed read-only: `docs/experiments/actionable-regime-confidence/runs/20260511T233426-codex-board-b-220646-crisis-branch-live-replay-v1/`",
                "",
                "## Next",
                "",
                "Keep `220646` blocked for promotion. Continue only after the exact branch reaches execution-tree admit, or after a predeclared historical-data continuation is selected and replayed through the same rooted branch path.",
                "",
            ]
        )
    )

    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
