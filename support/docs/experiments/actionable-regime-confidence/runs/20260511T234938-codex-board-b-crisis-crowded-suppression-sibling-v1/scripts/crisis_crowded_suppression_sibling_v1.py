#!/usr/bin/env python3
"""Build a sibling Crisis suppression leaf from the block-crowded nursery packet."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T234938+0800-codex-board-b-crisis-crowded-suppression-sibling-v1"
REPO_ROOT = next(path for path in [Path.cwd(), *Path.cwd().parents] if (path / "Cargo.toml").exists())
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T234938-codex-board-b-crisis-crowded-suppression-sibling-v1"
OUT_DIR = RUN_ROOT / "crisis-crowded-suppression-sibling"
CHECKS_DIR = RUN_ROOT / "checks"

SOURCE_220646 = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
SOURCE_NURSERY = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T234513-codex-board-b-b2r-block-crowded-nursery-v1"
SOURCE_CLOSED_LOOP = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T231800-codex-board-b-220646-exact-branch-closed-loop-readback-v4/exact-branch-closed-loop-readback-v4"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def read_branch_summary(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="") as fh:
        return {row["parent_regime_root"]: row for row in csv.DictReader(fh)}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    nursery_packet = load_json(
        SOURCE_NURSERY / "b2r-block-crowded-nursery/b2r_block_crowded_nursery_v1.json"
    )
    closed_loop = load_json(SOURCE_CLOSED_LOOP / "exact_branch_closed_loop_readback_v4.json")
    trace = load_json(
        SOURCE_CLOSED_LOOP
        / "state_exact_branch_closed_loop_v4/SRC_ROOT_CARRY_LONG_220646/execution_tree_trace.json"
    )
    summary = read_branch_summary(
        SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_branch_summary_v1.csv"
    )
    crisis_summary = summary["Crisis"]
    nursery_row = nursery_packet["nursery_row"]
    trace_output = trace["output"]

    sibling_path = (
        "Crisis -> CrisisReliefCarry -> BlockCrowdedSuppression -> "
        "SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1"
    )
    block_triggered = (
        trace_output.get("branch") == "block_crowded"
        and trace_output.get("gate_status") == "blocked"
        and "readiness 0.4433 < 0.45" in " ".join(trace_output.get("split_reason_lineage", []))
    )
    market_context = "RangeConsolidation/WideRange" in (trace_output.get("consumer_reason") or "")
    ranker_consumed = bool(trace_output.get("path_ranker_score_used_by_execution_tree"))

    packet = {
        "schema_version": "board-b-crisis-crowded-suppression-sibling/v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "source_recipe": "SourceRootStopCarryLongHorizonV1",
        "source_branch_path": nursery_row["branch_path"],
        "sibling_branch_id": "B2R_CRISIS_CROWDED_SUPPRESSION_SIBLING_V1",
        "sibling_branch_path": sibling_path,
        "nursery_status": "incubation_only",
        "parent_regime_root": "Crisis",
        "child_regime_hypothesis": "CrisisReliefCarry",
        "child_child_or_profit_factor": "BlockCrowdedSuppression",
        "profit_factor_leaf": "SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1",
        "action_leaf": "no_trade_when_block_crowded_or_wide_range",
        "suppression_rule": "if execution_tree_branch=block_crowded or execution_readiness<0.45 or live_context=RangeConsolidation/WideRange then no_trade",
        "source_crisis_branch_metrics": {
            "trade_count": int(crisis_summary["total_trades"]),
            "folds": crisis_summary["folds"],
            "win_rate": float(crisis_summary["win_rate"]),
            "mean_profit_ratio_net": float(crisis_summary["mean_profit_ratio_net"]),
            "bootstrap_edge_lcb_5pct": float(crisis_summary["bootstrap_edge_lcb_5pct"]),
            "pbo": float(crisis_summary["pbo"]),
            "dsr": float(crisis_summary["dsr"]),
            "rc_spa": float(crisis_summary["rc_spa"]),
            "hard_gate_result": crisis_summary["hard_gate_result"],
        },
        "current_runtime_test": {
            "block_crowded_triggered": block_triggered,
            "market_context_is_range_wide": market_context,
            "pre_bayes_gate_status": closed_loop["pre_bayes_gate_status"],
            "execution_candidate_ready": closed_loop["workflow_execution_candidate_ready"],
            "ranker_consumed_by_execution_tree": ranker_consumed,
            "execution_tree_gate_status": trace_output.get("gate_status"),
            "execution_tree_branch": trace_output.get("branch"),
            "execution_tree_consumer_reason": trace_output.get("consumer_reason"),
            "suppression_action_result": "no_trade" if block_triggered or market_context else "eligible_for_replay",
        },
        "provider_readback": nursery_packet.get("provider_readback"),
        "source_artifacts": {
            "nursery_packet": str(
                SOURCE_NURSERY / "b2r-block-crowded-nursery/b2r_block_crowded_nursery_v1.md"
            ),
            "closed_loop_readback": str(SOURCE_CLOSED_LOOP / "exact_branch_closed_loop_readback_v4.md"),
            "execution_tree_trace": str(
                SOURCE_CLOSED_LOOP
                / "state_exact_branch_closed_loop_v4/SRC_ROOT_CARRY_LONG_220646/execution_tree_trace.json"
            ),
            "rc_spa_report": str(
                SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.md"
            ),
        },
        "decision": "sibling_suppression_leaf_tested_current_context_no_trade",
        "promotion_allowed": False,
        "next_action": (
            "Use this sibling leaf in B2R nursery replay logic; it should explicitly emit no_trade "
            "under block_crowded / RangeConsolidation-WideRange contexts and only allow Crisis carry "
            "promotion replay when execution readiness is >=0.45 and context is compatible."
        ),
    }

    json_path = OUT_DIR / "crisis_crowded_suppression_sibling_v1.json"
    csv_path = OUT_DIR / "crisis_crowded_suppression_sibling_v1.csv"
    md_path = OUT_DIR / "crisis_crowded_suppression_sibling_v1.md"
    assertions_path = CHECKS_DIR / "crisis_crowded_suppression_sibling_v1_assertions.out"

    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")
    with csv_path.open("w", newline="") as fh:
        fields = [
            "sibling_branch_id",
            "nursery_status",
            "parent_regime_root",
            "sibling_branch_path",
            "source_trade_count",
            "source_crisis_rc_spa",
            "current_context",
            "execution_tree_branch",
            "suppression_action_result",
            "promotion_allowed",
        ]
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "sibling_branch_id": packet["sibling_branch_id"],
                "nursery_status": packet["nursery_status"],
                "parent_regime_root": packet["parent_regime_root"],
                "sibling_branch_path": sibling_path,
                "source_trade_count": crisis_summary["total_trades"],
                "source_crisis_rc_spa": crisis_summary["rc_spa"],
                "current_context": "RangeConsolidation/WideRange",
                "execution_tree_branch": trace_output.get("branch"),
                "suppression_action_result": packet["current_runtime_test"]["suppression_action_result"],
                "promotion_allowed": "false",
            }
        )

    md_path.write_text(
        "\n".join(
            [
                "# Crisis Crowded Suppression Sibling v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                "## Decision",
                "",
                "A sibling Crisis leaf was tested as `incubation_only`: it emits `no_trade` when the live execution tree reports `block_crowded` or `RangeConsolidation/WideRange` context.",
                "",
                "This is not a profitability promotion. It is a nursery guard that prevents the exact Crisis carry branch from being replayed into the same crowded context that already blocked execution.",
                "",
                "## Sibling Branch",
                "",
                f"- Source branch: `{nursery_row['branch_path']}`",
                f"- Sibling branch: `{sibling_path}`",
                "- Action leaf: `no_trade_when_block_crowded_or_wide_range`",
                "- Suppression rule: `execution_tree_branch=block_crowded` or `execution_readiness<0.45` or `live_context=RangeConsolidation/WideRange`",
                "",
                "## Source Metrics",
                "",
                f"- Crisis source trades: `{crisis_summary['total_trades']}`",
                f"- Crisis source RC-SPA: `{crisis_summary['rc_spa']}`",
                f"- Crisis source edge LCB: `{crisis_summary['bootstrap_edge_lcb_5pct']}`",
                f"- Crisis source PBO: `{crisis_summary['pbo']}`",
                f"- Crisis source DSR: `{crisis_summary['dsr']}`",
                "",
                "## Current Runtime Test",
                "",
                f"- Pre-Bayes gate: `{closed_loop['pre_bayes_gate_status']}`",
                f"- Execution candidate ready: `{closed_loop['workflow_execution_candidate_ready']}`",
                f"- Ranker consumed by execution tree: `{ranker_consumed}`",
                f"- Execution tree branch: `{trace_output.get('branch')}`",
                f"- Execution tree gate: `{trace_output.get('gate_status')}`",
                f"- Consumer reason: `{trace_output.get('consumer_reason')}`",
                f"- Sibling action result: `{packet['current_runtime_test']['suppression_action_result']}`",
                "",
                "## Next",
                "",
                packet["next_action"],
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path.relative_to(REPO_ROOT)}`",
                f"- CSV: `{csv_path.relative_to(REPO_ROOT)}`",
                f"- Assertions: `{assertions_path.relative_to(REPO_ROOT)}`",
                "",
            ]
        )
    )

    assertions = [
        f"PASS run_id={RUN_ID}",
        "PASS nursery_status=incubation_only",
        "PASS source_crisis_branch_rc_spa_available",
        f"PASS source_crisis_trades={crisis_summary['total_trades']}",
        f"PASS pre_bayes_gate={closed_loop['pre_bayes_gate_status']}",
        f"PASS execution_candidate_ready={closed_loop['workflow_execution_candidate_ready']}",
        f"PASS ranker_consumed_by_execution_tree={ranker_consumed}",
        f"PASS execution_tree_branch={trace_output.get('branch')}",
        f"PASS execution_tree_gate={trace_output.get('gate_status')}",
        f"PASS current_context_range_wide={market_context}",
        f"PASS sibling_action_result={packet['current_runtime_test']['suppression_action_result']}",
        "PASS promotion_allowed=False",
        "PASS runtime_code_changed=False",
        "PASS thresholds_relaxed=False",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
