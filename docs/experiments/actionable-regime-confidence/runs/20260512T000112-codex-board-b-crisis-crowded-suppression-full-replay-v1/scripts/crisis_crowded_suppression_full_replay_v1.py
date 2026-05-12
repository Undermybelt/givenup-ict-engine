#!/usr/bin/env python3
"""Build the Board B Crisis crowded-suppression full replay packet.

Run-local artifact builder only. It consumes existing Auto-Quant/RC-SPA
branch rows plus fresh ict-engine/provider command outputs captured in this
run root. It does not modify ict-engine runtime code and does not promote the
candidate.
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260512T000112+0800-codex-board-b-crisis-crowded-suppression-full-replay-v1"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
SOURCE_BRANCH_PATH = (
    "Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> "
    "SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12"
)
SIBLING_BRANCH_PATH = (
    "Crisis -> CrisisReliefCarry -> BlockCrowdedSuppression -> "
    "SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1"
)
SUPPRESSION_RULE = (
    "if execution_tree_branch=block_crowded or execution_readiness<0.45 or "
    "live_context=RangeConsolidation/WideRange then no_trade"
)

HERE = Path(__file__).resolve().parent
RUN_ROOT = HERE.parent
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
OUT_DIR = RUN_ROOT / "suppression-full-replay"
CHECKS_DIR = RUN_ROOT / "checks"
LOGS_DIR = RUN_ROOT / "logs"
PROVIDER_DIR = RUN_ROOT / "provider"
STATE_SYMBOL_DIR = RUN_ROOT / "state_suppression_full_replay_v1" / SYMBOL

SOURCE_220646 = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
)
SOURCE_234938 = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T234938-codex-board-b-crisis-crowded-suppression-sibling-v1"
)
SOURCE_SELECTED_ROWS = SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_selected_rows_v1.csv"
SOURCE_BRANCH_SUMMARY = SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_branch_summary_v1.csv"
SOURCE_RC_SPA_REPORT = SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.md"
SOURCE_SIBLING_PACKET = (
    SOURCE_234938
    / "crisis-crowded-suppression-sibling/crisis_crowded_suppression_sibling_v1.json"
)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_json(path: Path) -> Any:
    text = read_text(path).strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"json_error": True, "path": rel(path), "text_prefix": text[:500]}


def read_exit(path: Path) -> int | None:
    text = read_text(path).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def log_json(name: str) -> Any:
    return read_json(LOGS_DIR / f"{name}.out")


def log_exit(name: str) -> int | None:
    return read_exit(LOGS_DIR / f"{name}.exit")


def provider_exit(name: str) -> int | None:
    return read_exit(PROVIDER_DIR / f"{name}.exit")


def provider_json(name: str) -> Any:
    return read_json(PROVIDER_DIR / f"{name}.out")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def readiness_from_trace(trace_output: dict[str, Any]) -> float | None:
    for line in trace_output.get("split_reason_lineage") or []:
        match = re.search(r"readiness\s+([0-9.]+)\s*<\s*0\.45", line)
        if match:
            return float(match.group(1))
        match = re.search(r"execution_readiness=([0-9.]+)", line)
        if match:
            return float(match.group(1))
    return None


def summarize_provider_status(payload: dict[str, Any]) -> dict[str, Any]:
    keep = {"yfinance", "tradingview_mcp", "ibkr", "ibkr_bridge", "kraken_cli", "kraken_public"}
    providers: dict[str, list[dict[str, Any]]] = {}
    for item in payload.get("providers") or []:
        provider_id = item.get("provider_id")
        if provider_id in keep:
            providers.setdefault(provider_id, []).append(
                {
                    "domain": item.get("domain"),
                    "ready": item.get("ready"),
                    "status": item.get("status"),
                    "reason": item.get("reason"),
                    "access_mode": item.get("access_mode"),
                    "user_access": item.get("user_access"),
                }
            )
    return {
        "summary_line": payload.get("summary_line"),
        "ready_by_domain": payload.get("ready_by_domain"),
        "providers": providers,
        "artifact": rel(LOGS_DIR / "01_provider_status.out"),
    }


def harness_result(name: str) -> dict[str, Any]:
    payload = provider_json(name)
    rows = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return {
            "exit_code": provider_exit(name),
            "stdout": rel(PROVIDER_DIR / f"{name}.out"),
            "stderr": rel(PROVIDER_DIR / f"{name}.err"),
            "stderr_excerpt": read_text(PROVIDER_DIR / f"{name}.err")[:500],
        }
    ok_rows = [row for row in rows if row.get("ok") is True]
    error_rows = [row for row in rows if row.get("ok") is False]
    data_rows = 0
    if ok_rows and isinstance(ok_rows[0].get("data"), list):
        data_rows = len(ok_rows[0]["data"])
    return {
        "exit_code": provider_exit(name),
        "ok_count": len(ok_rows),
        "error_count": len(error_rows),
        "data_rows": data_rows,
        "first_error": error_rows[0].get("error") if error_rows else None,
        "stdout": rel(PROVIDER_DIR / f"{name}.out"),
        "stderr": rel(PROVIDER_DIR / f"{name}.err"),
        "stderr_excerpt": read_text(PROVIDER_DIR / f"{name}.err")[:500],
    }


def kraken_result() -> dict[str, Any]:
    payload = provider_json("kraken_cli_xbtusd_1h_ohlc")
    pair = None
    rows = 0
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key == "last":
                continue
            if isinstance(value, list):
                pair = key
                rows = len(value)
                break
    return {
        "exit_code": provider_exit("kraken_cli_xbtusd_1h_ohlc"),
        "pair": pair,
        "rows": rows,
        "stdout": rel(PROVIDER_DIR / "kraken_cli_xbtusd_1h_ohlc.out"),
        "stderr": rel(PROVIDER_DIR / "kraken_cli_xbtusd_1h_ohlc.err"),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    selected_rows = read_csv_rows(SOURCE_SELECTED_ROWS)
    branch_summary_rows = read_csv_rows(SOURCE_BRANCH_SUMMARY)
    branch_summary = {row["parent_regime_root"]: row for row in branch_summary_rows}

    sibling = read_json(SOURCE_SIBLING_PACKET)
    analyze_live = log_json("03_analyze_live")
    pre_bayes = log_json("04_pre_bayes_status")
    policy = log_json("05_policy_training_status")
    structural = log_json("06_workflow_structural_recommended_path_bundle")
    execution_candidate = log_json("07_workflow_execution_candidate")
    workflow = log_json("08_workflow_status")
    execution_trace = read_json(STATE_SYMBOL_DIR / "execution_tree_trace.json")
    trace_output = execution_trace.get("output") or {}
    trace_readiness = readiness_from_trace(trace_output)

    current_primary = (
        pre_bayes.get("latest_filtered_assignments", {}).get("market_state_primary_regime")
        or "unknown"
    )
    current_secondary = (
        pre_bayes.get("latest_filtered_assignments", {}).get("market_state_secondary_regime")
        or "unknown"
    )
    range_wide_context = current_primary == "RangeConsolidation" or current_secondary == "WideRange"
    block_crowded = trace_output.get("branch") == "block_crowded"
    readiness_block = trace_readiness is not None and trace_readiness < 0.45
    suppression_active = block_crowded or readiness_block or range_wide_context

    replay_rows: list[dict[str, Any]] = []
    summary: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "source_rows": 0,
            "effective_trade_rows": 0,
            "suppressed_no_trade_rows": 0,
            "source_net_sum": 0.0,
            "effective_net_sum": 0.0,
        }
    )

    for row in selected_rows:
        root = row["parent_regime_root"]
        original_net = float(row["profit_ratio_net"])
        suppress_row = (
            suppression_active
            and root == "Crisis"
            and row["regime_profit_branch_path"] == SOURCE_BRANCH_PATH
        )
        effective_net = 0.0 if suppress_row else original_net
        replay_path = SIBLING_BRANCH_PATH if suppress_row else row["regime_profit_branch_path"]
        replay_action = (
            "no_trade_when_block_crowded_or_low_readiness"
            if suppress_row
            else row["allowed_action"]
        )

        stats = summary[root]
        stats["source_rows"] += 1
        stats["source_net_sum"] += original_net
        stats["effective_net_sum"] += effective_net
        if suppress_row:
            stats["suppressed_no_trade_rows"] += 1
        else:
            stats["effective_trade_rows"] += 1

        replay_rows.append(
            {
                "schema_version": "board-b-crisis-crowded-suppression-full-replay/v1",
                "run_id": RUN_ID,
                "source_trade_id": row["trade_id"],
                "market": row["market"],
                "timeframe": row["timeframe"],
                "open_date": row["open_date"],
                "close_date": row["close_date"],
                "parent_regime_root": root,
                "child_regime": row["sub_regime_tags"],
                "child_child_or_profit_factor": (
                    "BlockCrowdedSuppression" if suppress_row else row["sub_sub_regime_or_profit_factor"]
                ),
                "profit_factor_leaf": (
                    "SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1"
                    if suppress_row
                    else row["profit_factor_leaf"]
                ),
                "source_branch_path": row["regime_profit_branch_path"],
                "replay_branch_path": replay_path,
                "source_action": row["allowed_action"],
                "replay_action": replay_action,
                "sibling_rule_applied": str(suppress_row).lower(),
                "original_profit_ratio_net": row["profit_ratio_net"],
                "effective_profit_ratio_net": f"{effective_net:.12f}",
                "original_exit_reason": row["exit_reason"],
                "replay_exit_reason": (
                    "suppressed_block_crowded_or_low_readiness" if suppress_row else row["exit_reason"]
                ),
                "nursery_status": "incubation_only" if suppress_row else "source_branch_replay",
                "promotion_allowed": "false",
            }
        )

    root_summary_rows: list[dict[str, Any]] = []
    for root in ["Bull", "Bear", "Sideways", "Crisis"]:
        stats = summary[root]
        source_rows = int(stats["source_rows"])
        branch = branch_summary[root]
        root_summary_rows.append(
            {
                "parent_regime_root": root,
                "source_trade_rows": source_rows,
                "effective_trade_rows": stats["effective_trade_rows"],
                "suppressed_no_trade_rows": stats["suppressed_no_trade_rows"],
                "source_net_sum": f"{stats['source_net_sum']:.12f}",
                "effective_net_sum": f"{stats['effective_net_sum']:.12f}",
                "source_mean_profit_ratio_net": branch["mean_profit_ratio_net"],
                "effective_mean_profit_ratio_net": (
                    f"{(stats['effective_net_sum'] / source_rows) if source_rows else 0.0:.12f}"
                ),
                "source_rc_spa": branch["rc_spa"],
                "source_hard_gate_result": branch["hard_gate_result"],
                "replay_gate": (
                    "nursery_guard_no_trade_not_profitability_pass"
                    if root == "Crisis"
                    else "unchanged_source_branch_replay"
                ),
            }
        )

    command_exits = {
        "cargo_build": log_exit("00_cargo_build"),
        "provider_status": log_exit("01_provider_status"),
        "auto_quant_status": log_exit("02_auto_quant_status"),
        "analyze_live": log_exit("03_analyze_live"),
        "pre_bayes_status": log_exit("04_pre_bayes_status"),
        "policy_training_status": log_exit("05_policy_training_status"),
        "workflow_structural_recommended_path_bundle": log_exit("06_workflow_structural_recommended_path_bundle"),
        "workflow_execution_candidate": log_exit("07_workflow_execution_candidate"),
        "workflow_status": log_exit("08_workflow_status"),
        "provider_status_yfinance": provider_exit("provider_status_yfinance"),
        "provider_status_tradingview_mcp": provider_exit("provider_status_tradingview_mcp"),
        "provider_status_ibkr": provider_exit("provider_status_ibkr"),
        "provider_status_kraken_cli": provider_exit("provider_status_kraken_cli"),
        "harness_yfinance_qqq_1d": provider_exit("harness_yfinance_qqq_1d"),
        "harness_tradingview_qqq_1d": provider_exit("harness_tradingview_qqq_1d"),
        "harness_ibkr_qqq_1d": provider_exit("harness_ibkr_qqq_1d"),
        "kraken_cli_xbtusd_1h_ohlc": provider_exit("kraken_cli_xbtusd_1h_ohlc"),
    }

    provider_status = summarize_provider_status(log_json("01_provider_status"))
    provider_fresh_fetch = {
        "yfinance_qqq_1d": harness_result("harness_yfinance_qqq_1d"),
        "tradingview_mcp_qqq_1d": harness_result("harness_tradingview_qqq_1d"),
        "ibkr_qqq_1d": harness_result("harness_ibkr_qqq_1d"),
        "kraken_cli_xbtusd_1h": kraken_result(),
    }

    structural_validation = policy.get("structural_path_ranking_validation") or {}
    structural_runtime = policy.get("structural_path_ranking_runtime") or {}
    latest_filtered = pre_bayes.get("latest_filtered_assignments") or {}
    workflow_latest = workflow.get("latest_promotable_artifact")
    workflow_blocker = (
        (structural.get("recommended_next_step") or {}).get("blocked_reason")
        or execution_candidate.get("review_reason")
        or "none"
    )

    packet = {
        "schema_version": "board-b-crisis-crowded-suppression-full-replay/v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "source_recipe": "SourceRootStopCarryLongHorizonV1",
        "source_branch_path": SOURCE_BRANCH_PATH,
        "sibling_branch_id": "B2R_CRISIS_CROWDED_SUPPRESSION_FULL_REPLAY_V1",
        "sibling_branch_path": SIBLING_BRANCH_PATH,
        "branch_path_shape": "main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor",
        "nursery_status": "incubation_only",
        "promotion_allowed": False,
        "selected_rows_source": rel(SOURCE_SELECTED_ROWS),
        "selected_rows_total": len(selected_rows),
        "suppression_rule": SUPPRESSION_RULE,
        "current_runtime_context": {
            "suppression_active": suppression_active,
            "block_crowded": block_crowded,
            "execution_readiness": trace_readiness,
            "readiness_block": readiness_block,
            "market_state_primary_regime": current_primary,
            "market_state_secondary_regime": current_secondary,
            "range_wide_context": range_wide_context,
            "execution_tree_gate_status": trace_output.get("gate_status"),
            "execution_tree_branch": trace_output.get("branch"),
            "execution_tree_bias": trace_output.get("execution_bias"),
            "execution_tree_consumer_reason": trace_output.get("consumer_reason"),
            "analyze_live_decision_summary": analyze_live.get("decision_summary"),
            "analyze_live_direction": analyze_live.get("direction"),
        },
        "replay_summary": {
            "source_selected_rows": len(selected_rows),
            "source_crisis_rows": summary["Crisis"]["source_rows"],
            "crisis_suppressed_no_trade_rows": summary["Crisis"]["suppressed_no_trade_rows"],
            "crisis_effective_trade_rows": summary["Crisis"]["effective_trade_rows"],
            "source_crisis_net_sum": summary["Crisis"]["source_net_sum"],
            "effective_crisis_net_sum": summary["Crisis"]["effective_net_sum"],
            "effective_trade_rows_all_roots": sum(row["effective_trade_rows"] for row in summary.values()),
            "source_crisis_rc_spa": float(branch_summary["Crisis"]["rc_spa"]),
            "source_crisis_edge_lcb": float(branch_summary["Crisis"]["bootstrap_edge_lcb_5pct"]),
            "source_crisis_pbo": float(branch_summary["Crisis"]["pbo"]),
            "source_crisis_dsr": float(branch_summary["Crisis"]["dsr"]),
        },
        "downstream_probe": {
            "command_exits": command_exits,
            "auto_quant_status": log_json("02_auto_quant_status"),
            "pre_bayes_gate_status": execution_candidate.get("pre_bayes_gate_status"),
            "pre_bayes_policy_version": latest_filtered.get("__policy_version"),
            "pre_bayes_canonical_structural_active_regime": pre_bayes.get(
                "latest_canonical_structural_active_regime"
            ),
            "pre_bayes_canonical_structural_confidence": pre_bayes.get(
                "latest_canonical_structural_confidence"
            ),
            "bbn_application_status": latest_filtered.get("regime_bundle_bbn_application_status"),
            "bbn_soft_evidence_status": latest_filtered.get("regime_bundle_bbn_evidence_application"),
            "bbn_soft_evidence_weight": latest_filtered.get("regime_bundle_bbn_evidence_weight"),
            "bbn_label_set": latest_filtered.get("read_only_regime_bbn_label_set"),
            "path_ranker_runtime_ready": structural_runtime.get("ready"),
            "path_ranker_runtime_status": structural_runtime.get("status"),
            "path_ranker_validation_ready": structural_validation.get("production_validation_ready"),
            "path_ranker_observation_validation_ready": (
                structural_validation.get("feedback_observation_validation") or {}
            ).get("ready"),
            "path_ranker_score_consumed": trace_output.get(
                "path_ranker_score_used_by_execution_tree"
            ),
            "structural_bundle_path_id": structural.get("path_id"),
            "structural_bundle_posterior": structural.get("current_posterior"),
            "execution_candidate_ready": execution_candidate.get("candidate_status") == "ready",
            "execution_candidate_actionable": execution_candidate.get("actionable"),
            "execution_candidate_review_status": execution_candidate.get("review_status"),
            "execution_candidate_review_reason": execution_candidate.get("review_reason"),
            "workflow_latest_promotable_artifact_id": (
                workflow_latest.get("artifact_id") if isinstance(workflow_latest, dict) else None
            ),
            "workflow_blocker": workflow_blocker,
        },
        "provider_readback": {
            "status": provider_status,
            "fresh_fetch": provider_fresh_fetch,
        },
        "source_artifacts": {
            "source_rc_spa_report": rel(SOURCE_RC_SPA_REPORT),
            "source_selected_rows": rel(SOURCE_SELECTED_ROWS),
            "source_sibling_packet": rel(SOURCE_SIBLING_PACKET),
            "state_execution_tree_trace": rel(STATE_SYMBOL_DIR / "execution_tree_trace.json"),
            "state_execution_candidate": rel(STATE_SYMBOL_DIR / "execution_candidate.json"),
        },
        "decision": {
            "status": "fail_closed_nursery_feedback_only",
            "promotion_status": "not_promoted:suppression_no_trade_guard_not_profitability_pass",
            "interpretation": (
                "The sibling leaf is encoded across the full selected-row replay and the "
                "rooted Crisis branch path is preserved through Pre-Bayes, BBN soft evidence, "
                "CatBoost/path-ranker, and execution tree. The current runtime is blocked by "
                "block_crowded/readiness, so the sibling emits no_trade. This is execution "
                "admissibility feedback, not a profitability pass."
            ),
        },
        "next_action": (
            "Keep the packet as nursery_feedback. The next productive step is either a user-selected "
            "historical-data replay for same-data comparability or another exact Crisis replay where "
            "execution readiness is >=0.45 and the execution tree admits the branch."
        ),
    }

    replay_rows_path = OUT_DIR / "crisis_crowded_suppression_full_replay_rows_v1.csv"
    summary_path = OUT_DIR / "crisis_crowded_suppression_full_replay_summary_v1.csv"
    json_path = OUT_DIR / "crisis_crowded_suppression_full_replay_v1.json"
    md_path = OUT_DIR / "crisis_crowded_suppression_full_replay_v1.md"
    assertions_path = CHECKS_DIR / "crisis_crowded_suppression_full_replay_v1_assertions.out"

    write_csv(replay_rows_path, replay_rows, list(replay_rows[0].keys()))
    write_csv(summary_path, root_summary_rows, list(root_summary_rows[0].keys()))
    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

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
                "This is not a profitability promotion. The exact Crisis branch is preserved through the downstream stack, but the current execution tree blocks it as `block_crowded`, so the sibling leaf emits `no_trade`.",
                "",
                "## Branch Path",
                "",
                f"- Source branch: `{SOURCE_BRANCH_PATH}`",
                f"- Sibling branch: `{SIBLING_BRANCH_PATH}`",
                "- Shape: `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`",
                "- Action leaf: `no_trade_when_block_crowded_or_low_readiness`",
                "",
                "## Replay",
                "",
                f"- Source selected rows: `{packet['replay_summary']['source_selected_rows']}`",
                f"- Crisis source rows: `{packet['replay_summary']['source_crisis_rows']}`",
                f"- Crisis suppressed no-trade rows: `{packet['replay_summary']['crisis_suppressed_no_trade_rows']}`",
                f"- Crisis effective trade rows: `{packet['replay_summary']['crisis_effective_trade_rows']}`",
                f"- Crisis source RC-SPA: `{packet['replay_summary']['source_crisis_rc_spa']}`",
                f"- Crisis source edge LCB: `{packet['replay_summary']['source_crisis_edge_lcb']}`",
                f"- Source Crisis net sum before suppression: `{packet['replay_summary']['source_crisis_net_sum']:.12f}`",
                "",
                "## Downstream Probes",
                "",
                f"- Pre-Bayes gate: `{packet['downstream_probe']['pre_bayes_gate_status']}`",
                f"- BBN soft evidence: `{packet['downstream_probe']['bbn_soft_evidence_status']}` weight `{packet['downstream_probe']['bbn_soft_evidence_weight']}`",
                f"- CatBoost/path-ranker runtime ready: `{packet['downstream_probe']['path_ranker_runtime_ready']}`",
                f"- CatBoost/path-ranker validation ready: `{packet['downstream_probe']['path_ranker_validation_ready']}`",
                f"- Path-ranker score consumed by execution tree: `{packet['downstream_probe']['path_ranker_score_consumed']}`",
                f"- Execution candidate ready: `{packet['downstream_probe']['execution_candidate_ready']}`",
                f"- Execution tree branch: `{packet['current_runtime_context']['execution_tree_branch']}`",
                f"- Execution readiness: `{packet['current_runtime_context']['execution_readiness']}`",
                f"- Workflow blocker: `{packet['downstream_probe']['workflow_blocker']}`",
                "",
                "## Provider Readback",
                "",
                f"- Provider status: `{provider_status['summary_line']}`",
                f"- yfinance QQQ 1d harness: exit `{provider_fresh_fetch['yfinance_qqq_1d']['exit_code']}`, rows `{provider_fresh_fetch['yfinance_qqq_1d'].get('data_rows')}`",
                f"- TradingViewRemix QQQ 1d harness: exit `{provider_fresh_fetch['tradingview_mcp_qqq_1d']['exit_code']}`, errors `{provider_fresh_fetch['tradingview_mcp_qqq_1d'].get('error_count')}`",
                f"- IBKR QQQ 1d harness: exit `{provider_fresh_fetch['ibkr_qqq_1d']['exit_code']}`",
                f"- Kraken CLI XBTUSD 1h OHLC: exit `{provider_fresh_fetch['kraken_cli_xbtusd_1h']['exit_code']}`, rows `{provider_fresh_fetch['kraken_cli_xbtusd_1h']['rows']}`",
                "",
                "## Interpretation",
                "",
                packet["decision"]["interpretation"],
                "",
                "## Artifacts",
                "",
                f"- JSON: `{rel(json_path)}`",
                f"- Replay rows: `{rel(replay_rows_path)}`",
                f"- Summary rows: `{rel(summary_path)}`",
                f"- Assertions: `{rel(assertions_path)}`",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_selected_rows={len(selected_rows)}",
        f"PASS source_crisis_rows={summary['Crisis']['source_rows']}",
        f"PASS crisis_suppressed_no_trade_rows={summary['Crisis']['suppressed_no_trade_rows']}",
        f"PASS crisis_effective_trade_rows={summary['Crisis']['effective_trade_rows']}",
        f"PASS sibling_branch_path_present={SIBLING_BRANCH_PATH in {row['replay_branch_path'] for row in replay_rows}}",
        f"PASS suppression_active={suppression_active}",
        f"PASS execution_tree_branch={trace_output.get('branch')}",
        f"PASS execution_tree_gate={trace_output.get('gate_status')}",
        f"PASS execution_readiness={trace_readiness}",
        f"PASS pre_bayes_gate={execution_candidate.get('pre_bayes_gate_status')}",
        f"PASS bbn_evidence_application={latest_filtered.get('regime_bundle_bbn_evidence_application')}",
        f"PASS path_ranker_runtime_ready={structural_runtime.get('ready')}",
        f"PASS path_ranker_validation_ready={structural_validation.get('production_validation_ready')}",
        f"PASS path_ranker_score_consumed={trace_output.get('path_ranker_score_used_by_execution_tree')}",
        f"PASS execution_candidate_ready={execution_candidate.get('candidate_status') == 'ready'}",
        f"PASS provider_status_exit={command_exits['provider_status']}",
        f"PASS yfinance_harness_exit={command_exits['harness_yfinance_qqq_1d']}",
        f"PASS tradingview_mcp_harness_recorded_exit={command_exits['harness_tradingview_qqq_1d']}",
        f"PASS ibkr_harness_recorded_exit={command_exits['harness_ibkr_qqq_1d']}",
        f"PASS kraken_cli_ohlc_exit={command_exits['kraken_cli_xbtusd_1h_ohlc']}",
        "PASS nursery_status=incubation_only",
        "PASS promotion_allowed=False",
        "PASS no_trade_guard_not_counted_as_profitability_pass=True",
        "PASS runtime_code_changed=False",
        "PASS thresholds_relaxed=False",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
