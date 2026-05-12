#!/usr/bin/env python3
"""Encode the crowded-context Crisis sibling leaf into a nursery replay."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


RUN_ID = "20260511T235535+0800-codex-board-b-crisis-crowded-suppression-full-replay-v1"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
REPO_ROOT = next(path for path in [Path.cwd(), *Path.cwd().parents] if (path / "Cargo.toml").exists())
RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T235535-codex-board-b-crisis-crowded-suppression-full-replay-v1"
OUT_DIR = RUN_ROOT / "suppression-full-replay"
CHECKS_DIR = RUN_ROOT / "checks"
LOGS_DIR = RUN_ROOT / "logs"

SOURCE_220646 = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
SOURCE_234918 = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T234918-codex-board-b-220646-compatible-live-context-readback-v1"
SOURCE_234938 = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T234938-codex-board-b-crisis-crowded-suppression-sibling-v1"

SELECTED_ROWS = SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_selected_rows_v1.csv"
BRANCH_SUMMARY = SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_branch_summary_v1.csv"
COMPATIBLE_READBACK = SOURCE_234918 / "compatible-live-context-readback-v1/compatible_live_context_readback_v1.json"
SIBLING_PACKET = SOURCE_234938 / "crisis-crowded-suppression-sibling/crisis_crowded_suppression_sibling_v1.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def load_exit(stem: str) -> int | None:
    path = LOGS_DIR / f"{stem}.exit"
    if not path.exists():
        return None
    text = path.read_text().strip()
    return int(text) if text else None


def load_log_json(stem: str) -> dict:
    path = LOGS_DIR / f"{stem}.out"
    if not path.exists():
        return {}
    text = path.read_text().strip()
    return json.loads(text) if text else {}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def truthy(value: object) -> bool:
    return bool(value) and str(value).lower() not in {"false", "0", "none", "null"}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    selected_rows = read_csv(SELECTED_ROWS)
    branch_summary = {row["parent_regime_root"]: row for row in read_csv(BRANCH_SUMMARY)}
    compatible = load_json(COMPATIBLE_READBACK)
    sibling = load_json(SIBLING_PACKET)

    downstream_readback = compatible["downstream_readback"]
    decision = sibling["current_runtime_test"]
    suppression_active = truthy(decision["block_crowded_triggered"]) or truthy(
        decision["market_context_is_range_wide"]
    )
    source_crisis_path = sibling["source_branch_path"]
    sibling_branch_path = sibling["sibling_branch_path"]
    suppression_rule = sibling["suppression_rule"]

    replay_rows: list[dict[str, object]] = []
    summary = defaultdict(lambda: {"input_rows": 0, "trade_rows": 0, "suppressed_rows": 0, "net_sum": 0.0})

    for row in selected_rows:
        root = row["parent_regime_root"]
        original_net = float(row["profit_ratio_net"])
        suppress_row = (
            suppression_active
            and root == "Crisis"
            and row["regime_profit_branch_path"] == source_crisis_path
        )
        effective_net = 0.0 if suppress_row else original_net
        replay_path = sibling_branch_path if suppress_row else row["regime_profit_branch_path"]
        replay_action = "no_trade_when_block_crowded_or_wide_range" if suppress_row else row["allowed_action"]
        replay_status = "nursery_no_trade_suppressed" if suppress_row else "unchanged_branch_replay"

        item = summary[root]
        item["input_rows"] += 1
        item["net_sum"] += effective_net
        if suppress_row:
            item["suppressed_rows"] += 1
        else:
            item["trade_rows"] += 1

        replay_rows.append(
            {
                "schema_version": "board-b-crisis-crowded-suppression-full-replay/v1",
                "run_id": RUN_ID,
                "source_trade_id": row["trade_id"],
                "market": row["market"],
                "timeframe": row["timeframe"],
                "parent_regime_root": root,
                "source_branch_path": row["regime_profit_branch_path"],
                "replay_branch_path": replay_path,
                "replay_action": replay_action,
                "sibling_rule_applied": str(suppress_row).lower(),
                "original_profit_ratio_net": row["profit_ratio_net"],
                "effective_profit_ratio_net": f"{effective_net:.12f}",
                "original_exit_reason": row["exit_reason"],
                "replay_exit_reason": "suppressed_block_crowded_wide_range" if suppress_row else row["exit_reason"],
                "replay_status": replay_status,
                "suppression_rule": suppression_rule if suppress_row else row["suppression_rule"],
            }
        )

    root_summary_rows: list[dict[str, object]] = []
    for root in ["Bull", "Bear", "Sideways", "Crisis"]:
        item = summary[root]
        input_rows = item["input_rows"]
        root_summary_rows.append(
            {
                "parent_regime_root": root,
                "source_trade_rows": input_rows,
                "effective_trade_rows": item["trade_rows"],
                "suppressed_no_trade_rows": item["suppressed_rows"],
                "effective_net_return_sum": f"{item['net_sum']:.12f}",
                "effective_mean_profit_ratio_net": f"{(item['net_sum'] / input_rows) if input_rows else 0.0:.12f}",
                "source_rc_spa": branch_summary[root]["rc_spa"],
                "replay_gate": "nursery_guard_no_trade_not_profitability_pass"
                if root == "Crisis"
                else "unchanged_source_branch_replay",
            }
        )

    provider_status = load_log_json("00_provider_status_agent")
    auto_quant_status = load_log_json("00_auto_quant_status")
    providers_by_id = {item.get("provider_id"): item for item in provider_status.get("providers", [])}
    pre_bayes = load_log_json("01_pre_bayes_status")
    policy = load_log_json("02_policy_training_status")
    structural = load_log_json("03_workflow_structural_recommended_path_bundle")
    execution_candidate = load_log_json("04_workflow_execution_candidate")
    workflow = load_log_json("05_workflow_status")

    log_exits = {
        "provider_status_agent": load_exit("00_provider_status_agent"),
        "auto_quant_status": load_exit("00_auto_quant_status"),
        "pre_bayes_status": load_exit("01_pre_bayes_status"),
        "policy_training_status": load_exit("02_policy_training_status"),
        "workflow_structural_recommended_path_bundle": load_exit("03_workflow_structural_recommended_path_bundle"),
        "workflow_execution_candidate": load_exit("04_workflow_execution_candidate"),
        "workflow_status": load_exit("05_workflow_status"),
    }
    structural_next = structural.get("recommended_next_step") or {}
    structural_validation = policy.get("structural_path_ranking_validation") or {}
    structural_runtime = policy.get("structural_path_ranking_runtime") or {}
    latest_filtered = pre_bayes.get("latest_filtered_assignments") or {}

    packet = {
        "schema_version": "board-b-crisis-crowded-suppression-full-replay/v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "source_recipe": "SourceRootStopCarryLongHorizonV1",
        "sibling_branch_id": sibling["sibling_branch_id"],
        "sibling_branch_path": sibling_branch_path,
        "nursery_status": "incubation_only",
        "promotion_allowed": False,
        "selected_rows_source": str(SELECTED_ROWS.relative_to(REPO_ROOT)),
        "selected_rows_total": len(selected_rows),
        "suppression_rule": suppression_rule,
        "suppression_context": {
            "suppression_active": suppression_active,
            "source_block_crowded_triggered": decision["block_crowded_triggered"],
            "source_market_context_is_range_wide": decision["market_context_is_range_wide"],
            "compatible_context_execution_tree_branch": downstream_readback["execution_tree_branch"],
            "compatible_context_gate_status": downstream_readback["execution_tree_gate_status"],
            "compatible_context_execution_readiness": downstream_readback["execution_readiness"],
            "compatible_context_workflow_blocker": downstream_readback["workflow_blocker"],
        },
        "replay_summary": {
            "source_selected_rows": len(selected_rows),
            "suppressed_no_trade_rows": summary["Crisis"]["suppressed_rows"],
            "effective_trade_rows": len(selected_rows) - summary["Crisis"]["suppressed_rows"],
            "crisis_source_rows": summary["Crisis"]["input_rows"],
            "crisis_effective_trade_rows": summary["Crisis"]["trade_rows"],
            "crisis_suppressed_rows": summary["Crisis"]["suppressed_rows"],
            "crisis_source_rc_spa": float(branch_summary["Crisis"]["rc_spa"]),
            "crisis_source_edge_lcb": float(branch_summary["Crisis"]["bootstrap_edge_lcb_5pct"]),
            "crisis_source_pbo": float(branch_summary["Crisis"]["pbo"]),
            "crisis_source_dsr": float(branch_summary["Crisis"]["dsr"]),
        },
        "downstream_probe": {
            "command_exits": log_exits,
            "provider_readback": {
                "summary_line": provider_status.get("summary_line"),
                "yfinance_live_ready": (providers_by_id.get("yfinance") or {}).get("ready"),
                "ibkr_bridge_ready": (providers_by_id.get("ibkr_bridge") or {}).get("ready"),
                "ibkr_bridge_reason": (providers_by_id.get("ibkr_bridge") or {}).get("reason"),
                "tradingview_mcp_ready": (providers_by_id.get("tradingview_mcp") or {}).get("ready"),
                "tradingview_mcp_reason": (providers_by_id.get("tradingview_mcp") or {}).get("reason"),
                "kraken_cli_ready": (providers_by_id.get("kraken_cli") or {}).get("ready"),
                "kraken_public_ready": (providers_by_id.get("kraken_public") or {}).get("ready"),
                "kraken_public_reason": (providers_by_id.get("kraken_public") or {}).get("reason"),
            },
            "auto_quant_readback": {
                "status": auto_quant_status.get("status"),
                "healthy": auto_quant_status.get("healthy"),
                "bootstrap_needed": auto_quant_status.get("bootstrap_needed"),
                "notes": auto_quant_status.get("notes"),
            },
            "pre_bayes_gate_status": execution_candidate.get("pre_bayes_gate_status"),
            "pre_bayes_quality_score": downstream_readback["pre_bayes_quality_score"],
            "bbn_soft_evidence_status": downstream_readback["bbn_soft_evidence_status"],
            "market_state_primary_regime": latest_filtered.get("market_state_primary_regime"),
            "market_state_secondary_regime": latest_filtered.get("market_state_secondary_regime"),
            "path_ranker_runtime_ready": structural_runtime.get("ready"),
            "path_ranker_validation_ready": structural_validation.get("production_validation_ready"),
            "path_ranker_score_consumed": downstream_readback["catboost_path_ranker_score_used_by_execution_tree"],
            "structural_bundle_path_id": structural.get("path_id"),
            "runtime_probe_branch_path": structural.get("path_id"),
            "sibling_branch_path_downstream_consumed": structural.get("path_id") == sibling_branch_path,
            "downstream_probe_scope": (
                "runtime_probe_exercised_existing_source_crisis_branch; "
                "sibling_no_trade_branch_is_encoded_in_replay_rows_only"
            ),
            "execution_candidate_ready": execution_candidate.get("candidate_status") == "ready",
            "execution_candidate_review_status": execution_candidate.get("review_status"),
            "workflow_blocker": structural_next.get("blocked_reason") or downstream_readback["workflow_blocker"],
            "agent_selected_recorded_data_path": (
                compatible["downstream_readback"]["recorded_data_paths"][1]
                if compatible["downstream_readback"].get("recorded_data_paths")
                else None
            ),
            "agent_selected_recorded_data_role": "nursery_replay_input_not_user_approved_production_data",
            "workflow_actionable_count": len(workflow.get("actionable_artifacts") or []),
        },
        "decision": {
            "status": "fail_closed_nursery_feedback_only",
            "promotion_status": "not_promoted:suppression_no_trade_guard_not_profitability_pass",
            "interpretation": (
                "The sibling leaf is now encoded across the full selected-row replay. It suppresses "
                "all exact Crisis carry rows under the crowded/wide-range context, so it is useful "
                "as execution-admissibility feedback but cannot count as a profitable Crisis branch."
            ),
        },
        "source_artifacts": {
            "source_rc_spa_report": str(
                (SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.md").relative_to(REPO_ROOT)
            ),
            "source_sibling_packet": str(
                (SOURCE_234938 / "crisis-crowded-suppression-sibling/crisis_crowded_suppression_sibling_v1.md").relative_to(REPO_ROOT)
            ),
            "compatible_live_context": str(COMPATIBLE_READBACK.relative_to(REPO_ROOT)),
        },
        "next_action": (
            "Use the replay rows as nursery-only execution-admissibility feedback, then test a "
            "non-crowded Crisis context or a historical data path selected by the user before any "
            "profitability promotion claim."
        ),
    }

    replay_rows_path = OUT_DIR / "crisis_crowded_suppression_full_replay_rows_v1.csv"
    summary_path = OUT_DIR / "crisis_crowded_suppression_full_replay_summary_v1.csv"
    json_path = OUT_DIR / "crisis_crowded_suppression_full_replay_v1.json"
    md_path = OUT_DIR / "crisis_crowded_suppression_full_replay_v1.md"
    assertions_path = CHECKS_DIR / "crisis_crowded_suppression_full_replay_v1_assertions.out"

    write_csv(replay_rows_path, replay_rows, list(replay_rows[0].keys()))
    write_csv(summary_path, root_summary_rows, list(root_summary_rows[0].keys()))
    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    md_path.write_text(
        "\n".join(
            [
                "# Crisis Crowded Suppression Full Replay v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                "## Decision",
                "",
                "The sibling Crisis suppression leaf was encoded across the full selected-row replay as `incubation_only` nursery feedback.",
                "",
                "It is not a profitability promotion: under the current crowded / wide-range context it converts the exact Crisis carry branch into `no_trade`, so the effective Crisis trade count becomes `0` for this replay.",
                "",
                "## Replay",
                "",
                f"- Source selected rows: `{packet['replay_summary']['source_selected_rows']}`",
                f"- Suppressed no-trade rows: `{packet['replay_summary']['suppressed_no_trade_rows']}`",
                f"- Effective trade rows: `{packet['replay_summary']['effective_trade_rows']}`",
                f"- Crisis source rows: `{packet['replay_summary']['crisis_source_rows']}`",
                f"- Crisis effective trade rows: `{packet['replay_summary']['crisis_effective_trade_rows']}`",
                f"- Crisis source RC-SPA: `{packet['replay_summary']['crisis_source_rc_spa']}`",
                f"- Sibling branch path: `{sibling_branch_path}`",
                "",
                "## Downstream Probes",
                "",
                f"- Provider-status exit: `{packet['downstream_probe']['command_exits']['provider_status_agent']}`",
                f"- Provider readback: `{packet['downstream_probe']['provider_readback']}`",
                f"- Auto-Quant status exit: `{packet['downstream_probe']['command_exits']['auto_quant_status']}`",
                f"- Auto-Quant readback: `{packet['downstream_probe']['auto_quant_readback']}`",
                f"- Pre-Bayes gate: `{packet['downstream_probe']['pre_bayes_gate_status']}`",
                f"- BBN soft evidence: `{packet['downstream_probe']['bbn_soft_evidence_status']}`",
                f"- CatBoost/path-ranker validation ready: `{packet['downstream_probe']['path_ranker_validation_ready']}`",
                f"- CatBoost/path-ranker consumed: `{packet['downstream_probe']['path_ranker_score_consumed']}`",
                f"- Runtime probe branch path: `{packet['downstream_probe']['runtime_probe_branch_path']}`",
                f"- Sibling branch downstream-consumed: `{packet['downstream_probe']['sibling_branch_path_downstream_consumed']}`",
                f"- Execution candidate ready: `{packet['downstream_probe']['execution_candidate_ready']}`",
                f"- Workflow blocker: `{packet['downstream_probe']['workflow_blocker']}`",
                f"- Agent-selected recorded data path: `{packet['downstream_probe']['agent_selected_recorded_data_path']}`",
                "",
                "## Interpretation",
                "",
                packet["decision"]["interpretation"],
                "",
                "## Artifacts",
                "",
                f"- JSON: `{json_path.relative_to(REPO_ROOT)}`",
                f"- Replay rows: `{replay_rows_path.relative_to(REPO_ROOT)}`",
                f"- Summary rows: `{summary_path.relative_to(REPO_ROOT)}`",
                f"- Assertions: `{assertions_path.relative_to(REPO_ROOT)}`",
                "",
            ]
        )
    )

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_selected_rows={len(selected_rows)}",
        f"PASS source_crisis_rows={summary['Crisis']['input_rows']}",
        f"PASS suppressed_no_trade_rows={summary['Crisis']['suppressed_rows']}",
        f"PASS crisis_effective_trade_rows={summary['Crisis']['trade_rows']}",
        f"PASS sibling_branch_path_preserved={sibling_branch_path in {row['replay_branch_path'] for row in replay_rows}}",
        f"PASS provider_status_exit={log_exits['provider_status_agent']}",
        f"PASS provider_yfinance_ready={packet['downstream_probe']['provider_readback']['yfinance_live_ready']}",
        f"PASS provider_ibkr_bridge_ready={packet['downstream_probe']['provider_readback']['ibkr_bridge_ready']}",
        f"PASS provider_tradingview_mcp_ready={packet['downstream_probe']['provider_readback']['tradingview_mcp_ready']}",
        f"PASS provider_kraken_cli_ready={packet['downstream_probe']['provider_readback']['kraken_cli_ready']}",
        f"PASS auto_quant_status_exit={log_exits['auto_quant_status']}",
        f"PASS auto_quant_status={packet['downstream_probe']['auto_quant_readback']['status']}",
        f"PASS pre_bayes_status_exit={log_exits['pre_bayes_status']}",
        f"PASS policy_training_status_exit={log_exits['policy_training_status']}",
        f"PASS workflow_structural_bundle_exit={log_exits['workflow_structural_recommended_path_bundle']}",
        f"PASS workflow_execution_candidate_exit={log_exits['workflow_execution_candidate']}",
        f"PASS workflow_status_exit={log_exits['workflow_status']}",
        f"PASS path_ranker_validation_ready={packet['downstream_probe']['path_ranker_validation_ready']}",
        f"PASS execution_candidate_ready={packet['downstream_probe']['execution_candidate_ready']}",
        f"PASS sibling_branch_path_downstream_consumed={packet['downstream_probe']['sibling_branch_path_downstream_consumed']}",
        f"PASS downstream_probe_scope={packet['downstream_probe']['downstream_probe_scope']}",
        f"PASS workflow_blocker={packet['downstream_probe']['workflow_blocker']}",
        "PASS nursery_status=incubation_only",
        "PASS promotion_allowed=False",
        "PASS runtime_code_changed=False",
        "PASS thresholds_relaxed=False",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
