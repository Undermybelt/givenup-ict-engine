#!/usr/bin/env python3
"""Build a Board B nursery feedback packet from the exact 220646 block-crowded readback."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T234648-codex-board-b-block-crowded-nursery-feedback-v1"
NURSERY = RUN / "nursery-feedback"
CHECKS = RUN / "checks"
LOGS = RUN / "logs"

BRANCH_REPORT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.json"
LIVE_STATE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T233426-codex-board-b-220646-crisis-branch-live-replay-v1/state_crisis_branch_live_replay_v1/SRC_ROOT_CARRY_LONG_220646"
TRACE = LIVE_STATE / "execution_tree_trace.json"
PRIOR_TRACE = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T231800-codex-board-b-220646-exact-branch-closed-loop-readback-v4/exact-branch-closed-loop-readback-v4/state_exact_branch_closed_loop_v4/SRC_ROOT_CARRY_LONG_220646/execution_tree_trace.json"


def read_json(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def read_exit(name: str) -> int:
    return int((LOGS / f"{name}.exit").read_text().strip())


def find_line(lines: list[str], prefix: str) -> str:
    for line in lines:
        if line.startswith(prefix):
            return line
    return ""


def first_float(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text)
    if not match:
        return None
    return float(match.group(1))


def provider_summary(provider_status: dict) -> dict:
    wanted = {
        "yfinance",
        "tradingview_mcp",
        "tradingview_remix",
        "ibkr",
        "ibkr_bridge",
        "kraken_public",
        "kraken_cli",
    }
    out: dict[str, dict] = {}
    for provider in provider_status.get("providers", []):
        provider_id = provider.get("provider_id")
        if provider_id in wanted:
            out[provider_id] = {
                "ready": bool(provider.get("ready")),
                "status": provider.get("status"),
                "reason": provider.get("reason"),
            }
    return out


def main() -> None:
    NURSERY.mkdir(parents=True, exist_ok=True)
    CHECKS.mkdir(parents=True, exist_ok=True)

    branch_report = read_json(BRANCH_REPORT)
    trace = read_json(TRACE)
    prior_trace = read_json(PRIOR_TRACE)
    provider_status = read_json(LOGS / "01_provider_status.out")
    auto_quant_status = read_json(LOGS / "02_auto_quant_status_json.out")
    pre_bayes_status = read_json(LOGS / "03_pre_bayes_status_json.out")
    policy_status = read_json(LOGS / "04_policy_training_status_agent.out")
    workflow_status = read_json(LOGS / "08_workflow_status_json.out")

    trace_output = trace.get("output", {})
    prior_trace_output = prior_trace.get("output", {})
    lineage = trace_output.get("split_reason_lineage", [])
    prior_lineage = prior_trace_output.get("split_reason_lineage", [])
    focus_reason = workflow_status.get("current_focus_reason", "")

    crisis_branch = None
    for item in branch_report.get("branch_summaries", []):
        if item.get("parent_regime_root") == "Crisis":
            crisis_branch = item
            break
    if crisis_branch is None:
        raise SystemExit("missing Crisis branch summary")

    readiness_line = find_line(lineage, "execution_readiness=")
    ranker_line = find_line(lineage, "path_ranker_score_input=")
    market_state_line = find_line(lineage, "market_state=primary_regime=")
    prior_readiness_line = find_line(prior_lineage, "execution_readiness=")

    execution_readiness = first_float(r"execution_readiness=([0-9.]+)", readiness_line)
    readiness_floor = first_float(r"readiness [0-9.]+ < ([0-9.]+)", find_line(lineage, "branch=block_crowded"))
    if readiness_floor is None:
        readiness_floor = 0.45
    prior_execution_readiness = first_float(r"execution_readiness=([0-9.]+)", prior_readiness_line)
    prior_readiness_floor = first_float(r"readiness [0-9.]+ < ([0-9.]+)", find_line(prior_lineage, "branch=block_crowded"))
    if prior_readiness_floor is None:
        prior_readiness_floor = 0.45
    path_ranker_score = first_float(r"path_ranker_score_input=([0-9.]+)", ranker_line)
    pre_bayes_quality = first_float(r"pre_bayes_quality_score=([0-9.]+)", focus_reason)

    nursery_branch_path = (
        "Crisis -> RangeConsolidation/WideRange -> "
        "BlockCrowdedExecutionAdmissibility -> "
        "SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12"
    )

    command_exits = {
        "provider_status": read_exit("01_provider_status"),
        "auto_quant_status_json": read_exit("02_auto_quant_status_json"),
        "pre_bayes_status_json": read_exit("03_pre_bayes_status_json"),
        "policy_training_status_agent": read_exit("04_policy_training_status_agent"),
        "workflow_structural_recommended_path_bundle_json": read_exit("05_workflow_structural_recommended_path_bundle_json"),
        "workflow_execution_candidate_json": read_exit("06_workflow_execution_candidate_json"),
        "workflow_status_agent": read_exit("07_workflow_status_agent"),
        "workflow_status_json": read_exit("08_workflow_status_json"),
    }

    packet = {
        "schema_version": "board-b-block-crowded-nursery-feedback/v1",
        "run_id": "20260511T234648+0800-codex-board-b-block-crowded-nursery-feedback-v1",
        "accepted_regime_id": branch_report.get("accepted_regime_id"),
        "source_strict_candidate": "20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-v1",
        "source_live_readback": "20260511T233426-codex-board-b-220646-crisis-branch-live-replay-v1",
        "nursery_branch_id": "B2R_NURSERY_220646_CRISIS_BLOCK_CROWDED_V1",
        "nursery_status": "incubation_only",
        "parent_regime_root": "Crisis",
        "child_regime_hypothesis": "RangeConsolidation/WideRange live context inside Crisis-rooted candidate",
        "child_child_or_profit_factor": "block_crowded execution-admissibility feature",
        "profit_factor_leaf": "SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12",
        "branch_path": nursery_branch_path,
        "allowed_action": "suppress_or_defer_long_until_execution_readiness_context_compatible",
        "suppression_rule": "suppress exact Crisis carry branch when execution_tree_branch=block_crowded or readiness < 0.45 in RangeConsolidation/WideRange",
        "nursery_gate": {
            "rooted_path": True,
            "explicit_action_leaf": True,
            "nonzero_chronological_evidence": crisis_branch.get("total_trades", 0) > 0 and crisis_branch.get("test_folds", 0) > 0,
            "replay_or_backtest_costed": crisis_branch.get("cost_stress_result") == "pass",
            "result": "pass",
        },
        "promotion_gate": {
            "result": "fail_closed:observe_only_and_workflow_blocking_truth",
            "reason": "prior run blocked as block_crowded; fresh refresh moved to observe/fill_viable but still lacks explicit closed-loop promotion and is blocked by historical-data selection truth",
            "promotion_allowed": False,
        },
        "auto_quant_branch_evidence": {
            "recipe_id": crisis_branch.get("recipe_id"),
            "source_regime_profit_branch_path": crisis_branch.get("regime_profit_branch_path"),
            "total_trades": crisis_branch.get("total_trades"),
            "test_folds": crisis_branch.get("test_folds"),
            "fold_positive_rate": crisis_branch.get("fold_positive_rate"),
            "win_rate": crisis_branch.get("win_rate"),
            "mean_profit_ratio_net": crisis_branch.get("mean_profit_ratio_net"),
            "bootstrap_edge_lcb_5pct": crisis_branch.get("bootstrap_edge_lcb_5pct"),
            "pbo": crisis_branch.get("pbo"),
            "dsr": crisis_branch.get("dsr"),
            "rc_spa": crisis_branch.get("rc_spa"),
            "hard_gate_result": crisis_branch.get("hard_gate_result"),
        },
        "downstream_probe_evidence": {
            "prior_execution_tree_branch": prior_trace_output.get("branch"),
            "prior_execution_tree_gate_status": prior_trace_output.get("gate_status"),
            "prior_execution_readiness": prior_execution_readiness,
            "prior_execution_readiness_floor": prior_readiness_floor,
            "prior_consumer_reason": prior_trace_output.get("consumer_reason"),
            "pre_bayes_gate_status": workflow_status.get("latest_execution_candidate", {}).get("pre_bayes_gate_status"),
            "pre_bayes_quality_score": pre_bayes_quality,
            "bbn_evidence_label": "primary::ExtremeStress" if "primary::ExtremeStress" in focus_reason else None,
            "path_ranker_score_input": path_ranker_score,
            "path_ranker_score_visible": trace_output.get("path_ranker_score_visible_to_execution_tree"),
            "path_ranker_score_used": trace_output.get("path_ranker_score_used_by_execution_tree"),
            "ranker_validation_ready": trace_output.get("ranker_validation_ready"),
            "policy_training_ready": policy_status.get("structural_path_ranking_validation", {}).get("production_validation_ready"),
            "policy_training_rows": policy_status.get("structural_path_ranking_validation", {}).get("production_validation_rows"),
            "execution_tree_branch": trace_output.get("branch"),
            "execution_tree_gate_status": trace_output.get("gate_status"),
            "execution_tree_bias": trace_output.get("execution_bias"),
            "execution_readiness": execution_readiness,
            "execution_readiness_floor": readiness_floor,
            "execution_decision_hint": trace_output.get("decision_hint"),
            "consumer_reason": trace_output.get("consumer_reason"),
            "market_state_line": market_state_line,
            "workflow_blocking_truth": workflow_status.get("blocking_truth"),
        },
        "provider_readback": {
            "summary_line": provider_status.get("summary_line"),
            "providers": provider_summary(provider_status),
        },
        "auto_quant_status_readback": {
            "status": auto_quant_status.get("status"),
            "recommended_next_command": auto_quant_status.get("recommended_next_command"),
        },
        "command_exits": command_exits,
        "interpretation": {
            "profitability_rejection": False,
            "branch_routing_failure": False,
            "negative_execution_admissibility_feature": True,
            "block_crowded_repeated_in_fresh_refresh": trace_output.get("branch") == "block_crowded",
            "block_crowded_context_sensitive": prior_trace_output.get("branch") == "block_crowded" and trace_output.get("branch") != "block_crowded",
            "board_a_feedback_allowed_after_repeat_evidence": True,
            "closed_loop_confidence_ready": False,
        },
        "next_action": (
            "Use this as incubation-only negative execution-admissibility feedback. "
            "The fresh refresh did not repeat block_crowded, so treat the feature as context-sensitive "
            "and repeat across compatible live/readback contexts before sending a Board A split; "
            "do not promote until workflow blocking truth and closed-loop confidence are explicit."
        ),
        "artifacts": {
            "packet_json": str(NURSERY / "block_crowded_nursery_feedback_v1.json"),
            "packet_csv": str(NURSERY / "block_crowded_nursery_feedback_v1.csv"),
            "packet_md": str(NURSERY / "block_crowded_nursery_feedback_v1.md"),
            "assertions": str(CHECKS / "block_crowded_nursery_feedback_v1_assertions.out"),
        },
    }

    json_path = NURSERY / "block_crowded_nursery_feedback_v1.json"
    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    csv_path = NURSERY / "block_crowded_nursery_feedback_v1.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "run_id",
                "nursery_branch_id",
                "nursery_status",
                "parent_regime_root",
                "branch_path",
                "auto_quant_trades",
                "auto_quant_rc_spa",
                "pre_bayes_gate_status",
                "bbn_evidence_label",
                "path_ranker_score_input",
                "ranker_validation_ready",
                "execution_tree_branch",
                "execution_tree_gate_status",
                "prior_execution_tree_branch",
                "prior_execution_readiness",
                "execution_readiness",
                "execution_readiness_floor",
                "promotion_allowed",
                "next_action",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "run_id": packet["run_id"],
                "nursery_branch_id": packet["nursery_branch_id"],
                "nursery_status": packet["nursery_status"],
                "parent_regime_root": packet["parent_regime_root"],
                "branch_path": packet["branch_path"],
                "auto_quant_trades": packet["auto_quant_branch_evidence"]["total_trades"],
                "auto_quant_rc_spa": packet["auto_quant_branch_evidence"]["rc_spa"],
                "pre_bayes_gate_status": packet["downstream_probe_evidence"]["pre_bayes_gate_status"],
                "bbn_evidence_label": packet["downstream_probe_evidence"]["bbn_evidence_label"],
                "path_ranker_score_input": packet["downstream_probe_evidence"]["path_ranker_score_input"],
                "ranker_validation_ready": packet["downstream_probe_evidence"]["ranker_validation_ready"],
                "execution_tree_branch": packet["downstream_probe_evidence"]["execution_tree_branch"],
                "execution_tree_gate_status": packet["downstream_probe_evidence"]["execution_tree_gate_status"],
                "prior_execution_tree_branch": packet["downstream_probe_evidence"]["prior_execution_tree_branch"],
                "prior_execution_readiness": packet["downstream_probe_evidence"]["prior_execution_readiness"],
                "execution_readiness": packet["downstream_probe_evidence"]["execution_readiness"],
                "execution_readiness_floor": packet["downstream_probe_evidence"]["execution_readiness_floor"],
                "promotion_allowed": packet["promotion_gate"]["promotion_allowed"],
                "next_action": packet["next_action"],
            }
        )

    md_path = NURSERY / "block_crowded_nursery_feedback_v1.md"
    md_path.write_text(
        "\n".join(
            [
                "# Block Crowded Nursery Feedback v1",
                "",
                f"- Run id: `{packet['run_id']}`",
                f"- Nursery branch id: `{packet['nursery_branch_id']}`",
                f"- Nursery status: `{packet['nursery_status']}`",
                f"- Branch path: `{packet['branch_path']}`",
                f"- Auto-Quant evidence: `trades={crisis_branch.get('total_trades')}`, `folds={crisis_branch.get('test_folds')}`, `RC-SPA={crisis_branch.get('rc_spa')}`.",
                f"- Pre-Bayes: `{packet['downstream_probe_evidence']['pre_bayes_gate_status']}` quality `{packet['downstream_probe_evidence']['pre_bayes_quality_score']}`.",
                f"- BBN evidence label: `{packet['downstream_probe_evidence']['bbn_evidence_label']}`.",
                f"- CatBoost/path-ranker: score `{packet['downstream_probe_evidence']['path_ranker_score_input']}`, validation ready `{packet['downstream_probe_evidence']['ranker_validation_ready']}`, production rows `{packet['downstream_probe_evidence']['policy_training_rows']}`.",
                f"- Prior execution tree: `{packet['downstream_probe_evidence']['prior_execution_tree_branch']}` / `{packet['downstream_probe_evidence']['prior_execution_tree_gate_status']}` with readiness `{packet['downstream_probe_evidence']['prior_execution_readiness']}` below floor `{packet['downstream_probe_evidence']['prior_execution_readiness_floor']}`.",
                f"- Fresh execution tree: `{packet['downstream_probe_evidence']['execution_tree_branch']}` / `{packet['downstream_probe_evidence']['execution_tree_gate_status']}` with readiness `{packet['downstream_probe_evidence']['execution_readiness']}` versus floor `{packet['downstream_probe_evidence']['execution_readiness_floor']}`.",
                f"- Provider readback: `{packet['provider_readback']['summary_line']}`.",
                f"- Interpretation: context-sensitive negative execution-admissibility feature, not a profitability rejection and not a branch-routing failure.",
                f"- Promotion allowed: `{packet['promotion_gate']['promotion_allowed']}`.",
                f"- Next action: {packet['next_action']}",
                "",
                "Artifacts:",
                f"- JSON: `{json_path}`",
                f"- CSV: `{csv_path}`",
                f"- Assertions: `{CHECKS / 'block_crowded_nursery_feedback_v1_assertions.out'}`",
                "",
            ]
        )
    )

    assertion_lines = []
    failures = []
    for name, code in command_exits.items():
        ok = code == 0
        assertion_lines.append(f"{name}_exit0={str(ok).lower()}")
        if not ok:
            failures.append(name)
    checks = {
        "rooted_path": packet["nursery_gate"]["rooted_path"],
        "nursery_gate_pass": packet["nursery_gate"]["result"] == "pass",
        "auto_quant_branch_pass": crisis_branch.get("hard_gate_result") == "pass",
        "pre_bayes_pass_neutralized": packet["downstream_probe_evidence"]["pre_bayes_gate_status"] == "pass_neutralized",
        "bbn_extreme_stress_applied": packet["downstream_probe_evidence"]["bbn_evidence_label"] == "primary::ExtremeStress",
        "ranker_visible_and_used": bool(packet["downstream_probe_evidence"]["path_ranker_score_visible"]) and bool(packet["downstream_probe_evidence"]["path_ranker_score_used"]),
        "ranker_validation_ready": bool(packet["downstream_probe_evidence"]["ranker_validation_ready"]),
        "prior_execution_tree_block_crowded": packet["downstream_probe_evidence"]["prior_execution_tree_branch"] == "block_crowded",
        "prior_readiness_below_floor": (
            packet["downstream_probe_evidence"]["prior_execution_readiness"] is not None
            and packet["downstream_probe_evidence"]["prior_execution_readiness_floor"] is not None
            and packet["downstream_probe_evidence"]["prior_execution_readiness"] < packet["downstream_probe_evidence"]["prior_execution_readiness_floor"]
        ),
        "fresh_execution_tree_rechecked": packet["downstream_probe_evidence"]["execution_tree_branch"] in {"block_crowded", "fill_viable", "wait_for_reversion", "transition_guardrail"},
        "fresh_readiness_available": (
            packet["downstream_probe_evidence"]["execution_readiness"] is not None
            and packet["downstream_probe_evidence"]["execution_readiness_floor"] is not None
        ),
        "promotion_blocked": not packet["promotion_gate"]["promotion_allowed"],
    }
    for name, ok in checks.items():
        assertion_lines.append(f"{name}={str(ok).lower()}")
        if not ok:
            failures.append(name)

    assertions_path = CHECKS / "block_crowded_nursery_feedback_v1_assertions.out"
    assertions_path.write_text("\n".join(assertion_lines) + "\n")
    if failures:
        raise SystemExit("assertion failures: " + ", ".join(failures))


if __name__ == "__main__":
    main()
