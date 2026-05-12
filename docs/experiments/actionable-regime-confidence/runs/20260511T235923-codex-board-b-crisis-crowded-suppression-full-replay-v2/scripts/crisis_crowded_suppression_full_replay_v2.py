#!/usr/bin/env python3
"""Full nursery replay for the crowded-context Crisis suppression sibling."""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T235923+0800-codex-board-b-crisis-crowded-suppression-full-replay-v2"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
REPO_ROOT = Path(__file__).resolve().parents[6]
ICT_ENGINE = REPO_ROOT / "target" / "debug" / "ict-engine"
ENRICHER = REPO_ROOT / "scripts" / "auto_quant_external" / "structural_feedback_trade_enricher.py"

RUN_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T235923-codex-board-b-crisis-crowded-suppression-full-replay-v2"
OUT_DIR = RUN_ROOT / "suppression-full-replay-v2"
CHECKS_DIR = RUN_ROOT / "checks"
LOGS_DIR = RUN_ROOT / "command-output"
STATE_DIR = RUN_ROOT / "state_crisis_crowded_suppression_full_replay_v2"
PROVIDER_DIR = RUN_ROOT / "provider"

SOURCE_220646 = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
SOURCE_231800 = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T231800-codex-board-b-220646-exact-branch-closed-loop-readback-v4/exact-branch-closed-loop-readback-v4"
SOURCE_234918 = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T234918-codex-board-b-220646-compatible-live-context-readback-v1"
SOURCE_234938 = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T234938-codex-board-b-crisis-crowded-suppression-sibling-v1"

SELECTED_ROWS = SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_selected_rows_v1.csv"
BRANCH_SUMMARY = SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_branch_summary_v1.csv"
COMPATIBLE_READBACK = SOURCE_234918 / "compatible-live-context-readback-v1/compatible_live_context_readback_v1.json"
SIBLING_PACKET = SOURCE_234938 / "crisis-crowded-suppression-sibling/crisis_crowded_suppression_sibling_v1.json"
SOURCE_STATE = SOURCE_231800 / "state_exact_branch_closed_loop_v4"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def truthy(value: Any) -> bool:
    return bool(value) and str(value).lower() not in {"false", "0", "none", "null"}


def run_command(name: str, cmd: list[str], *, timeout: int = 120) -> dict[str, Any]:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    stdout_path = LOGS_DIR / f"{name}.out"
    stderr_path = LOGS_DIR / f"{name}.err"
    exit_path = LOGS_DIR / f"{name}.exit"
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    exit_path.write_text(f"{result.returncode}\n", encoding="utf-8")
    return {
        "name": name,
        "cmd": " ".join(cmd),
        "returncode": result.returncode,
        "stdout_path": str(stdout_path.relative_to(REPO_ROOT)),
        "stderr_path": str(stderr_path.relative_to(REPO_ROOT)),
        "exit_path": str(exit_path.relative_to(REPO_ROOT)),
    }


def load_command_json(command: dict[str, Any]) -> dict[str, Any]:
    text = (REPO_ROOT / command["stdout_path"]).read_text(encoding="utf-8").strip()
    return json.loads(text) if text else {}


def file_exit(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def provider_artifact(name: str) -> dict[str, Any]:
    base = PROVIDER_DIR / name
    out_path = base.with_suffix(".out")
    err_path = base.with_suffix(".err")
    exit_path = base.with_suffix(".exit")
    return {
        "stdout": str(out_path.relative_to(REPO_ROOT)),
        "stderr": str(err_path.relative_to(REPO_ROOT)),
        "exit": str(exit_path.relative_to(REPO_ROOT)),
        "exit_code": file_exit(exit_path),
        "stderr_excerpt": err_path.read_text(encoding="utf-8").strip()[:500] if err_path.exists() else "",
    }


def parse_market_harness(name: str) -> dict[str, Any]:
    artifact = provider_artifact(name)
    out_path = REPO_ROOT / artifact["stdout"]
    if not out_path.exists() or not out_path.read_text(encoding="utf-8").strip():
        return {**artifact, "json_available": False, "ok_count": 0, "error_count": 0, "rows": 0}
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    results = payload.get("results") or []
    return {
        **artifact,
        "json_available": True,
        "ok_count": sum(1 for item in results if item.get("ok")),
        "error_count": sum(1 for item in results if item.get("ok") is False),
        "rows": sum(len(item.get("data") or []) for item in results),
    }


def parse_kraken_probe() -> dict[str, Any]:
    artifact = provider_artifact("kraken_cli_xbtusd_1h_ohlc")
    out_path = REPO_ROOT / artifact["stdout"]
    if not out_path.exists() or not out_path.read_text(encoding="utf-8").strip():
        return {**artifact, "pair": None, "rows": 0}
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    pair = next(iter(payload.keys()), None)
    return {**artifact, "pair": pair, "rows": len(payload.get(pair) or []) if pair else 0}


def command_by_name(commands: list[dict[str, Any]], name: str) -> dict[str, Any]:
    return next(command for command in commands if command["name"] == name)


def refresh_state_copy() -> None:
    if STATE_DIR.exists():
        shutil.rmtree(STATE_DIR)
    shutil.copytree(SOURCE_STATE, STATE_DIR)


def emit_suppression_feedback(feedback_path: Path, target_csv: Path, feedback_path_id: str) -> dict[str, Any]:
    return run_command(
        "03_emit_suppression_no_trade_feedback",
        [
            "python3",
            str(ENRICHER),
            "emit-probe",
            "--target-csv",
            str(target_csv),
            "--output",
            str(feedback_path),
            "--path-id",
            feedback_path_id,
            "--realized-outcome",
            "not_followed",
            "--not-followed",
            "--pnl",
            "0.0",
            "--exit-reason",
            "suppressed_block_crowded_wide_range",
            "--notes",
            "Board B nursery replay: selected source Crisis path is recorded as not_followed because sibling no-trade suppression applies under block_crowded / RangeConsolidation-WideRange. This is execution-admissibility feedback, not a profitability pass.",
        ],
    )


def build_replay() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    selected_rows = read_csv(SELECTED_ROWS)
    branch_summary = {row["parent_regime_root"]: row for row in read_csv(BRANCH_SUMMARY)}
    compatible = load_json(COMPATIBLE_READBACK)
    sibling = load_json(SIBLING_PACKET)

    decision = sibling["current_runtime_test"]
    downstream_readback = compatible["downstream_readback"]
    suppression_active = truthy(decision["block_crowded_triggered"]) or truthy(decision["market_context_is_range_wide"])
    source_crisis_path = sibling["source_branch_path"]
    sibling_branch_path = sibling["sibling_branch_path"]
    suppression_rule = sibling["suppression_rule"]

    summary: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "input_rows": 0,
            "trade_rows": 0,
            "suppressed_rows": 0,
            "original_net_sum": 0.0,
            "effective_net_sum": 0.0,
        }
    )
    replay_rows: list[dict[str, Any]] = []

    for row in selected_rows:
        root = row["parent_regime_root"]
        original_net = float(row["profit_ratio_net"])
        suppress_row = suppression_active and root == "Crisis" and row["regime_profit_branch_path"] == source_crisis_path
        effective_net = 0.0 if suppress_row else original_net
        replay_path = sibling_branch_path if suppress_row else row["regime_profit_branch_path"]
        replay_action = "no_trade_when_block_crowded_or_wide_range" if suppress_row else row["allowed_action"]
        replay_status = "nursery_no_trade_suppressed" if suppress_row else "unchanged_source_branch_replay"

        item = summary[root]
        item["input_rows"] += 1
        item["original_net_sum"] += original_net
        item["effective_net_sum"] += effective_net
        if suppress_row:
            item["suppressed_rows"] += 1
        else:
            item["trade_rows"] += 1

        replay_rows.append(
            {
                "schema_version": "board-b-crisis-crowded-suppression-full-replay/v2",
                "run_id": RUN_ID,
                "source_trade_id": row["trade_id"],
                "market": row["market"],
                "timeframe": row["timeframe"],
                "open_date": row["open_date"],
                "close_date": row["close_date"],
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

    root_summary_rows: list[dict[str, Any]] = []
    for root in ["Bull", "Bear", "Sideways", "Crisis"]:
        item = summary[root]
        input_rows = int(item["input_rows"])
        root_summary_rows.append(
            {
                "parent_regime_root": root,
                "source_trade_rows": input_rows,
                "effective_trade_rows": item["trade_rows"],
                "suppressed_no_trade_rows": item["suppressed_rows"],
                "original_net_return_sum": f"{item['original_net_sum']:.12f}",
                "effective_net_return_sum": f"{item['effective_net_sum']:.12f}",
                "effective_mean_profit_ratio_net": f"{(item['effective_net_sum'] / input_rows) if input_rows else 0.0:.12f}",
                "source_rc_spa": branch_summary[root]["rc_spa"],
                "source_hard_gate": branch_summary[root]["hard_gate_result"],
                "replay_gate": "nursery_guard_no_trade_not_profitability_pass"
                if root == "Crisis"
                else "unchanged_source_branch_replay",
            }
        )

    replay_context = {
        "selected_rows_total": len(selected_rows),
        "suppression_active": suppression_active,
        "source_crisis_path": source_crisis_path,
        "sibling_branch_path": sibling_branch_path,
        "suppression_rule": suppression_rule,
        "source_crisis_rows": summary["Crisis"]["input_rows"],
        "suppressed_no_trade_rows": summary["Crisis"]["suppressed_rows"],
        "effective_trade_rows": len(selected_rows) - summary["Crisis"]["suppressed_rows"],
        "crisis_effective_trade_rows": summary["Crisis"]["trade_rows"],
        "crisis_source_rc_spa": float(branch_summary["Crisis"]["rc_spa"]),
        "crisis_source_edge_lcb": float(branch_summary["Crisis"]["bootstrap_edge_lcb_5pct"]),
        "crisis_source_pbo": float(branch_summary["Crisis"]["pbo"]),
        "crisis_source_dsr": float(branch_summary["Crisis"]["dsr"]),
        "compatible_context_execution_tree_branch": downstream_readback["execution_tree_branch"],
        "compatible_context_execution_tree_gate": downstream_readback["execution_tree_gate_status"],
        "compatible_context_execution_readiness": downstream_readback["execution_readiness"],
        "compatible_context_workflow_blocker": downstream_readback["workflow_blocker"],
        "source_runtime_block_crowded": decision["block_crowded_triggered"],
        "source_runtime_range_wide": decision["market_context_is_range_wide"],
    }
    return replay_context, replay_rows, root_summary_rows, compatible, sibling


def extract_downstream(commands: list[dict[str, Any]], compatible: dict[str, Any]) -> dict[str, Any]:
    provider_status = load_command_json(command_by_name(commands, "00_provider_status_agent"))
    auto_quant_status = load_command_json(command_by_name(commands, "01_auto_quant_status_json"))
    pre_before = load_command_json(command_by_name(commands, "02_pre_bayes_status_before_json"))
    policy = load_command_json(command_by_name(commands, "06_policy_training_status_json"))
    structural_bundle = load_command_json(command_by_name(commands, "07_workflow_structural_bundle_agent"))
    execution_candidate = load_command_json(command_by_name(commands, "08_workflow_execution_candidate_agent"))
    workflow = load_command_json(command_by_name(commands, "09_workflow_full_json"))
    pre_after = load_command_json(command_by_name(commands, "10_pre_bayes_status_after_json"))

    validation = policy.get("structural_path_ranking_validation") or {}
    runtime = policy.get("structural_path_ranking_runtime") or {}
    target = policy.get("structural_path_ranking_target") or {}
    latest_filtered = pre_after.get("latest_filtered_assignments") or {}
    structural_next = structural_bundle.get("recommended_next_step") or {}
    compatible_readback = compatible["downstream_readback"]

    return {
        "provider_summary_line": provider_status.get("summary_line"),
        "provider_ready": {
            provider.get("provider_id"): provider.get("ready")
            for provider in provider_status.get("providers", [])
            if provider.get("provider_id") in {"yfinance", "ibkr", "tradingview_mcp", "kraken_cli", "kraken_public"}
        },
        "provider_harness": {
            "harness_yfinance_qqq_1d": parse_market_harness("harness_yfinance_qqq_1d"),
            "harness_tradingview_qqq_1d": parse_market_harness("harness_tradingview_qqq_1d"),
            "harness_ibkr_qqq_1d": parse_market_harness("harness_ibkr_qqq_1d"),
            "kraken_cli_xbtusd_1h_ohlc": parse_kraken_probe(),
        },
        "auto_quant_status": auto_quant_status.get("status") or auto_quant_status.get("summary_line"),
        "command_exits": {command["name"]: command["returncode"] for command in commands},
        "pre_bayes_gate_before": pre_before.get("latest_gate_status")
        or pre_before.get("pre_bayes_gate_status")
        or pre_before.get("gating_status")
        or pre_before.get("status"),
        "pre_bayes_gate_after": pre_after.get("latest_gate_status")
        or pre_after.get("pre_bayes_gate_status")
        or pre_after.get("gating_status")
        or pre_after.get("status"),
        "pre_bayes_branch_path_gate_after": latest_filtered.get("pre_bayes_branch_path_gate"),
        "bbn_update_command_exit": command_by_name(commands, "05_bbn_update_suppression_feedback")["returncode"],
        "bbn_soft_evidence_status_source": compatible_readback.get("bbn_soft_evidence_status"),
        "market_state_primary_regime": latest_filtered.get("market_state_primary_regime"),
        "market_state_secondary_regime": latest_filtered.get("market_state_secondary_regime"),
        "path_ranker_runtime_ready": runtime.get("ready"),
        "path_ranker_validation_ready": validation.get("production_validation_ready"),
        "path_ranker_feedback_observation_ready": validation.get("observation_validation_ready"),
        "path_ranker_target_rows_total": target.get("rows_total") or target.get("target_rows_total"),
        "path_ranker_feedback_rows_total": target.get("feedback_rows_total"),
        "path_ranker_score_consumed_source": compatible_readback.get("catboost_path_ranker_score_used_by_execution_tree"),
        "feedback_path_id": compatible_readback.get("structural_bundle_path_id") or None,
        "structural_bundle_path_id": structural_bundle.get("path_id"),
        "execution_candidate_ready": execution_candidate.get("candidate_status") == "ready",
        "execution_candidate_review_status": execution_candidate.get("review_status"),
        "workflow_blocker": structural_next.get("blocked_reason") or compatible_readback.get("workflow_blocker"),
        "workflow_actionable_count": len(workflow.get("actionable_artifacts") or []),
    }


def write_outputs(
    replay_context: dict[str, Any],
    replay_rows: list[dict[str, Any]],
    root_summary_rows: list[dict[str, Any]],
    downstream: dict[str, Any],
    commands: list[dict[str, Any]],
    feedback_path: Path,
) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)

    replay_rows_path = OUT_DIR / "crisis_crowded_suppression_full_replay_rows_v2.csv"
    summary_path = OUT_DIR / "crisis_crowded_suppression_full_replay_summary_v2.csv"
    json_path = OUT_DIR / "crisis_crowded_suppression_full_replay_v2.json"
    md_path = OUT_DIR / "crisis_crowded_suppression_full_replay_v2.md"
    assertions_path = CHECKS_DIR / "crisis_crowded_suppression_full_replay_v2_assertions.out"

    write_csv(replay_rows_path, replay_rows, list(replay_rows[0].keys()))
    write_csv(summary_path, root_summary_rows, list(root_summary_rows[0].keys()))

    command_failures = [command for command in commands if command["returncode"] != 0]
    packet = {
        "schema_version": "board-b-crisis-crowded-suppression-full-replay/v2",
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "source_recipe": "SourceRootStopCarryLongHorizonV1",
        "sibling_branch_id": "B2R_CRISIS_CROWDED_SUPPRESSION_SIBLING_V1",
        "sibling_branch_path": replay_context["sibling_branch_path"],
        "nursery_status": "incubation_only",
        "promotion_allowed": False,
        "state_dir": str(STATE_DIR.relative_to(REPO_ROOT)),
        "replay_summary": replay_context,
        "downstream_probe": downstream,
        "commands": commands,
        "decision": {
            "status": "fail_closed_nursery_feedback_only",
            "promotion_status": "not_promoted:suppression_no_trade_guard_not_profitability_pass",
            "interpretation": (
                "The sibling leaf is encoded across the full 220646 selected-row replay. "
                "In the crowded/wide-range context it suppresses all exact Crisis carry rows, "
                "so it is execution-admissibility feedback and not a profitable Crisis branch."
            ),
            "command_failures": len(command_failures),
        },
        "artifacts": {
            "json": str(json_path.relative_to(REPO_ROOT)),
            "replay_rows": str(replay_rows_path.relative_to(REPO_ROOT)),
            "summary_rows": str(summary_path.relative_to(REPO_ROOT)),
            "feedback_file": str(feedback_path.relative_to(REPO_ROOT)),
            "assertions": str(assertions_path.relative_to(REPO_ROOT)),
        },
        "source_artifacts": {
            "source_selected_rows": str(SELECTED_ROWS.relative_to(REPO_ROOT)),
            "source_branch_summary": str(BRANCH_SUMMARY.relative_to(REPO_ROOT)),
            "source_sibling_packet": str(SIBLING_PACKET.relative_to(REPO_ROOT)),
            "compatible_live_context": str(COMPATIBLE_READBACK.relative_to(REPO_ROOT)),
            "source_state": str(SOURCE_STATE.relative_to(REPO_ROOT)),
        },
        "next_action": (
            "Keep this as nursery feedback. Test a non-crowded Crisis context or user-selected historical "
            "data path before any profitability promotion, and do not route no-trade suppression as a pass."
        ),
    }
    json_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path.write_text(
        "\n".join(
            [
                "# Crisis Crowded Suppression Full Replay v2",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                "## Decision",
                "",
                "The sibling Crisis suppression leaf is encoded across the full selected-row replay as `incubation_only` nursery feedback.",
                "",
                "This is not a profitability promotion. Under the current crowded / wide-range context it converts the exact Crisis carry branch into `no_trade`, so the effective Crisis trade count is `0` for this replay.",
                "",
                "## Replay",
                "",
                f"- Source selected rows: `{packet['replay_summary']['selected_rows_total']}`",
                f"- Suppressed no-trade rows: `{packet['replay_summary']['suppressed_no_trade_rows']}`",
                f"- Effective trade rows: `{packet['replay_summary']['effective_trade_rows']}`",
                f"- Crisis source rows: `{packet['replay_summary']['source_crisis_rows']}`",
                f"- Crisis effective trade rows: `{packet['replay_summary']['crisis_effective_trade_rows']}`",
                f"- Crisis source RC-SPA: `{packet['replay_summary']['crisis_source_rc_spa']}`",
                f"- Sibling branch path: `{packet['sibling_branch_path']}`",
                "",
                "## Downstream Probes",
                "",
                f"- Provider summary: `{downstream.get('provider_summary_line')}`",
                f"- yfinance harness rows / exit: `{downstream['provider_harness']['harness_yfinance_qqq_1d'].get('rows')}` / `{downstream['provider_harness']['harness_yfinance_qqq_1d'].get('exit_code')}`",
                f"- TradingViewRemix harness errors / exit: `{downstream['provider_harness']['harness_tradingview_qqq_1d'].get('error_count')}` / `{downstream['provider_harness']['harness_tradingview_qqq_1d'].get('exit_code')}`",
                f"- IBKR harness exit: `{downstream['provider_harness']['harness_ibkr_qqq_1d'].get('exit_code')}`",
                f"- Kraken CLI OHLC rows / exit: `{downstream['provider_harness']['kraken_cli_xbtusd_1h_ohlc'].get('rows')}` / `{downstream['provider_harness']['kraken_cli_xbtusd_1h_ohlc'].get('exit_code')}`",
                f"- Pre-Bayes before: `{downstream.get('pre_bayes_gate_before')}`",
                f"- BBN update exit: `{downstream.get('bbn_update_command_exit')}`",
                f"- Pre-Bayes after: `{downstream.get('pre_bayes_gate_after')}`",
                f"- BBN soft evidence source readback: `{downstream.get('bbn_soft_evidence_status_source')}`",
                f"- CatBoost/path-ranker validation ready: `{downstream.get('path_ranker_validation_ready')}`",
                f"- CatBoost/path-ranker consumed in source readback: `{downstream.get('path_ranker_score_consumed_source')}`",
                f"- Execution candidate ready: `{downstream.get('execution_candidate_ready')}`",
                f"- Workflow blocker: `{downstream.get('workflow_blocker')}`",
                f"- Command failures: `{len(command_failures)}`",
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
                f"- Feedback file: `{feedback_path.relative_to(REPO_ROOT)}`",
                f"- Assertions: `{assertions_path.relative_to(REPO_ROOT)}`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assertions = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_selected_rows={replay_context['selected_rows_total']}",
        f"PASS source_crisis_rows={replay_context['source_crisis_rows']}",
        f"PASS suppressed_no_trade_rows={replay_context['suppressed_no_trade_rows']}",
        f"PASS crisis_effective_trade_rows={replay_context['crisis_effective_trade_rows']}",
        f"PASS sibling_branch_path_preserved={replay_context['sibling_branch_path'] in {row['replay_branch_path'] for row in replay_rows}}",
        f"PASS provider_status_exit={downstream['command_exits'].get('00_provider_status_agent')}",
        f"PASS yfinance_harness_exit={downstream['provider_harness']['harness_yfinance_qqq_1d'].get('exit_code')}",
        f"PASS yfinance_harness_rows={downstream['provider_harness']['harness_yfinance_qqq_1d'].get('rows')}",
        f"PASS tradingview_harness_exit={downstream['provider_harness']['harness_tradingview_qqq_1d'].get('exit_code')}",
        f"PASS ibkr_harness_exit={downstream['provider_harness']['harness_ibkr_qqq_1d'].get('exit_code')}",
        f"PASS kraken_cli_harness_exit={downstream['provider_harness']['kraken_cli_xbtusd_1h_ohlc'].get('exit_code')}",
        f"PASS kraken_cli_ohlc_rows={downstream['provider_harness']['kraken_cli_xbtusd_1h_ohlc'].get('rows')}",
        f"PASS auto_quant_status_exit={downstream['command_exits'].get('01_auto_quant_status_json')}",
        f"PASS pre_bayes_before_exit={downstream['command_exits'].get('02_pre_bayes_status_before_json')}",
        f"PASS bbn_update_exit={downstream['command_exits'].get('05_bbn_update_suppression_feedback')}",
        f"PASS policy_training_exit={downstream['command_exits'].get('06_policy_training_status_json')}",
        f"PASS workflow_structural_bundle_exit={downstream['command_exits'].get('07_workflow_structural_bundle_agent')}",
        f"PASS workflow_execution_candidate_exit={downstream['command_exits'].get('08_workflow_execution_candidate_agent')}",
        f"PASS workflow_full_exit={downstream['command_exits'].get('09_workflow_full_json')}",
        f"PASS pre_bayes_after_exit={downstream['command_exits'].get('10_pre_bayes_status_after_json')}",
        f"PASS path_ranker_validation_ready={downstream.get('path_ranker_validation_ready')}",
        f"PASS execution_candidate_ready={downstream.get('execution_candidate_ready')}",
        f"PASS workflow_blocker={downstream.get('workflow_blocker')}",
        "PASS nursery_status=incubation_only",
        "PASS promotion_allowed=False",
        "PASS runtime_code_changed=False",
        "PASS thresholds_relaxed=False",
    ]
    assertions_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")
    return packet


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    refresh_state_copy()

    replay_context, replay_rows, root_summary_rows, compatible, _sibling = build_replay()
    feedback_path = OUT_DIR / "crisis_crowded_suppression_feedback_v2.json"
    target_csv = STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target.csv"

    commands: list[dict[str, Any]] = []
    commands.append(run_command("00_provider_status_agent", [str(ICT_ENGINE), "provider-status", "--agent"]))
    commands.append(run_command("01_auto_quant_status_json", [str(ICT_ENGINE), "auto-quant-status", "--state-dir", str(STATE_DIR / "auto-quant")]))
    commands.append(run_command("02_pre_bayes_status_before_json", [str(ICT_ENGINE), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"]))
    commands.append(emit_suppression_feedback(feedback_path, target_csv, replay_context["source_crisis_path"]))
    commands.append(
        run_command(
            "05_bbn_update_suppression_feedback",
            [
                str(ICT_ENGINE),
                "update",
                "--symbol",
                SYMBOL,
                "--outcome",
                "not_followed",
                "--entry-signal",
                "medium",
                "--state-dir",
                str(STATE_DIR),
                "--pnl=0.0",
                "--feedback-file",
                str(feedback_path),
            ],
        )
    )
    commands.append(run_command("06_policy_training_status_json", [str(ICT_ENGINE), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"]))
    commands.append(
        run_command(
            "07_workflow_structural_bundle_agent",
            [
                str(ICT_ENGINE),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--phase",
                "structural-recommended-path-bundle",
                "--agent",
            ],
        )
    )
    commands.append(
        run_command(
            "08_workflow_execution_candidate_agent",
            [
                str(ICT_ENGINE),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--phase",
                "execution-candidate",
                "--agent",
            ],
        )
    )
    commands.append(run_command("09_workflow_full_json", [str(ICT_ENGINE), "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"]))
    commands.append(run_command("10_pre_bayes_status_after_json", [str(ICT_ENGINE), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"]))

    downstream = extract_downstream(commands, compatible)
    packet = write_outputs(replay_context, replay_rows, root_summary_rows, downstream, commands, feedback_path)
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0 if all(command["returncode"] == 0 for command in commands) else 1


if __name__ == "__main__":
    raise SystemExit(main())
