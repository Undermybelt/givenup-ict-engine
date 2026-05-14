#!/usr/bin/env python3
"""Materialize Board B B2R nursery feedback for the exact 220646 branch.

This is a run-local artifact builder. It consumes already captured command
outputs plus the source RC-SPA and execution-tree artifacts, then writes a
single incubation-only nursery packet. It does not modify ict-engine runtime
code and does not promote the candidate.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T234513+0800-codex-board-b-b2r-block-crowded-nursery-v1"
SOURCE_RC_SPA_RUN_ID = "20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-v1"
SOURCE_CLOSED_LOOP_RUN_ID = "20260511T231800+0800-codex-board-b-220646-exact-branch-closed-loop-readback-v4"
SOURCE_FEEDBACK_PACKET_ID = "20260511T233358+0800-codex-board-b-220646-block-crowded-feedback-packet-v1"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
RECIPE_ID = "SourceRootStopCarryLongHorizonV1"
BRANCH_PATH = (
    "Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> "
    "SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12"
)

HERE = Path(__file__).resolve().parent
RUN_ROOT = HERE.parent
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())

SOURCE_RC_SPA = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/"
    "branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.json"
)
SOURCE_BRANCH_SUMMARY = SOURCE_RC_SPA.with_name("source_root_stop_carry_longhorizon_branch_summary_v1.csv")
SOURCE_CLOSED_LOOP_DIR = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T231800-codex-board-b-220646-exact-branch-closed-loop-readback-v4/"
    "exact-branch-closed-loop-readback-v4"
)
SOURCE_CLOSED_LOOP_JSON = SOURCE_CLOSED_LOOP_DIR / "exact_branch_closed_loop_readback_v4.json"
SOURCE_BLOCK_DIAGNOSIS = SOURCE_CLOSED_LOOP_DIR / "execution_tree_block_crowded_diagnosis_v1.md"
SOURCE_BLOCK_FEEDBACK = SOURCE_CLOSED_LOOP_DIR / "execution_tree_block_crowded_feedback_packet_v1.md"
SOURCE_STATE_DIR = SOURCE_CLOSED_LOOP_DIR / "state_exact_branch_closed_loop_v4" / SYMBOL
SOURCE_EXECUTION_TRACE = SOURCE_STATE_DIR / "execution_tree_trace.json"
SOURCE_EXECUTION_CANDIDATE = SOURCE_STATE_DIR / "execution_candidate.json"

OUT_DIR = RUN_ROOT / "b2r-nursery"
CHECK_DIR = RUN_ROOT / "checks"
CSV_PATH = OUT_DIR / "b2r_block_crowded_nursery_feedback_v1.csv"
JSON_PATH = OUT_DIR / "b2r_block_crowded_nursery_feedback_v1.json"
MD_PATH = OUT_DIR / "b2r_block_crowded_nursery_feedback_v1.md"
ASSERTIONS = CHECK_DIR / "b2r_block_crowded_nursery_v1_assertions.out"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"missing": True, "path": rel(path)}
    text = read_text(path).strip()
    if not text:
        return {"empty": True, "path": rel(path)}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"json_error": f"{type(exc).__name__}:{exc}", "path": rel(path)}
    return data if isinstance(data, dict) else {"value": data}


def exit_code(path: Path) -> int | None:
    try:
        return int(read_text(path).strip())
    except Exception:
        return None


def command_record(group: str, name: str) -> dict[str, Any]:
    base = RUN_ROOT / group / name
    return {
        "name": f"{group}/{name}",
        "stdout": rel(base.with_suffix(".out")),
        "stderr": rel(base.with_suffix(".err")),
        "exit": rel(base.with_suffix(".exit")),
        "exit_code": exit_code(base.with_suffix(".exit")),
    }


def parse_provider_status() -> dict[str, Any]:
    path = RUN_ROOT / "provider/provider_status_agent.out"
    payload = read_json(path)
    providers: dict[str, dict[str, Any]] = {}
    for item in payload.get("providers", []):
        provider_id = item.get("provider_id")
        if provider_id in {
            "yfinance",
            "tradingview_mcp",
            "ibkr",
            "ibkr_bridge",
            "kraken_cli",
            "kraken_public",
        }:
            providers[provider_id] = {
                "domain": item.get("domain"),
                "ready": bool(item.get("ready")),
                "status": item.get("status"),
                "reason": item.get("reason"),
            }
    return {
        "summary_line": payload.get("summary_line"),
        "ready_by_domain": payload.get("ready_by_domain"),
        "providers": providers,
        "artifact": rel(path),
    }


def parse_harness(name: str) -> dict[str, Any]:
    out = RUN_ROOT / f"provider/{name}.out"
    err = RUN_ROOT / f"provider/{name}.err"
    payload = read_json(out)
    results = payload.get("results") if isinstance(payload.get("results"), list) else []
    ok = sum(1 for row in results if row.get("ok") is True)
    failed = sum(1 for row in results if row.get("ok") is False)
    return {
        "exit_code": exit_code(RUN_ROOT / f"provider/{name}.exit"),
        "ok_count": ok,
        "error_count": failed,
        "stdout": rel(out),
        "stderr": rel(err),
        "stderr_excerpt": read_text(err)[:500],
    }


def parse_kraken() -> dict[str, Any]:
    out = RUN_ROOT / "provider/kraken_cli_xbtusd_1h_ohlc.out"
    payload = read_json(out)
    rows = 0
    pair = None
    for key, value in payload.items():
        if key == "last":
            continue
        if isinstance(value, list):
            pair = key
            rows = len(value)
            break
    return {
        "exit_code": exit_code(RUN_ROOT / "provider/kraken_cli_xbtusd_1h_ohlc.exit"),
        "pair": pair,
        "rows": rows,
        "stdout": rel(out),
        "stderr": rel(RUN_ROOT / "provider/kraken_cli_xbtusd_1h_ohlc.err"),
    }


def parse_auto_quant() -> dict[str, Any]:
    help_exit = exit_code(RUN_ROOT / "auto-quant/auto_quant_runpy_help.exit")
    visibility = read_json(RUN_ROOT / "auto-quant/local_auto_quant_visibility.out")
    return {
        "runpy_help_exit": help_exit,
        "runpy_help_stderr": rel(RUN_ROOT / "auto-quant/auto_quant_runpy_help.err"),
        "visibility_exit": exit_code(RUN_ROOT / "auto-quant/local_auto_quant_visibility.exit"),
        "visibility": visibility,
        "source_rc_spa_artifact": rel(SOURCE_RC_SPA),
    }


def find_branch_summary_row() -> dict[str, str]:
    if not SOURCE_BRANCH_SUMMARY.exists():
        return {}
    with SOURCE_BRANCH_SUMMARY.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("regime_profit_branch_path") == BRANCH_PATH or row.get("branch_path") == BRANCH_PATH:
                return row
    return {}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)

    rc_spa = read_json(SOURCE_RC_SPA)
    rc_decision = rc_spa.get("decision", {})
    closed_loop = read_json(SOURCE_CLOSED_LOOP_JSON)
    execution_trace = read_json(SOURCE_EXECUTION_TRACE)
    execution_candidate = read_json(SOURCE_EXECUTION_CANDIDATE)
    pre_bayes = read_json(RUN_ROOT / "ict-engine/pre_bayes_status_refresh_json.out")
    policy = read_json(RUN_ROOT / "ict-engine/policy_training_status_json.out")
    structural_bundle = read_json(RUN_ROOT / "ict-engine/workflow_structural_recommended_path_bundle.out")
    workflow_candidate = read_json(RUN_ROOT / "ict-engine/workflow_execution_candidate.out")
    export_target = read_json(RUN_ROOT / "ict-engine/export_structural_path_ranking_target.out")
    branch_row = find_branch_summary_row()

    execution_output = execution_trace.get("output", {})
    provider = parse_provider_status()
    yfinance = parse_harness("harness_yfinance_qqq_1d")
    tradingview = parse_harness("harness_tradingview_qqq_1d")
    ibkr = parse_harness("harness_ibkr_qqq_1d")
    kraken = parse_kraken()
    auto_quant = parse_auto_quant()

    nursery_row = {
        "nursery_branch_id": "B2R-220646-crisis-block-crowded-v1",
        "nursery_status": "incubation_only",
        "parent_regime_root": "Crisis",
        "root_confidence_source": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "child_regime_hypothesis": "CrisisReliefCarry",
        "child_child_or_profit_factor": "StopManagedPanicRecovery",
        "profit_factor_leaf": "SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12",
        "action_leaf": "long_relief_research_only_when_execution_context_not_crowded",
        "branch_path": BRANCH_PATH,
        "why_keep_exploring": (
            "Strict RC-SPA passed and downstream branch identity reached Pre-Bayes, CatBoost/path-ranker, "
            "and execution tree; only execution-tree admissibility blocked on block_crowded under "
            "RangeConsolidation/WideRange."
        ),
        "backtest_artifact": rel(SOURCE_RC_SPA),
        "provider_panel": "yfinance fresh fetch ok; Kraken CLI OHLC ok; TradingViewRemix MCP and IBKR fresh probes fail/degraded",
        "trade_count": str(branch_row.get("total_trades") or branch_row.get("trade_count") or ""),
        "win_rate_net": str(branch_row.get("win_rate_net") or branch_row.get("fold_positive_rate") or ""),
        "edge_lcb": str(branch_row.get("bootstrap_edge_lcb_5pct") or ""),
        "max_drawdown_or_tail_loss": str(branch_row.get("tail_loss_p95") or ""),
        "rc_spa_score_if_available": str(rc_decision.get("stable_profit_score")),
        "filter_probe_result": str(pre_bayes.get("latest_gate_status") or workflow_candidate.get("pre_bayes_gate_status")),
        "bbn_probe_result": str((execution_candidate.get("pre_bayes_evidence_filter") or {}).get("evidence_assignments", {}).get("regime_bundle_bbn_application_status")),
        "catboost_probe_result": str((policy.get("structural_path_ranking_runtime") or {}).get("status")),
        "execution_tree_probe_result": str(execution_output.get("branch")),
        "feedback_to_board_a": "nursery_feedback:block_crowded_negative_execution_admissibility_for_exact_crisis_branch",
        "promotion_blocker": str(execution_output.get("consumer_reason")),
    }

    packet = {
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source_rc_spa_run_id": SOURCE_RC_SPA_RUN_ID,
        "source_closed_loop_run_id": SOURCE_CLOSED_LOOP_RUN_ID,
        "source_feedback_packet_id": SOURCE_FEEDBACK_PACKET_ID,
        "symbol": SYMBOL,
        "recipe_id": RECIPE_ID,
        "nursery_row": nursery_row,
        "provider_readback": {
            "status": provider,
            "harness_yfinance_qqq_1d": yfinance,
            "harness_tradingview_qqq_1d": tradingview,
            "harness_ibkr_qqq_1d": ibkr,
            "kraken_cli_xbtusd_1h_ohlc": kraken,
        },
        "auto_quant_readback": auto_quant,
        "downstream_readback": {
            "rc_spa_gate": rc_decision.get("gate_result"),
            "stable_profit_score": rc_decision.get("stable_profit_score"),
            "price_root_paths_passed": rc_decision.get("price_root_paths_passed"),
            "manipulation_component_pass": rc_decision.get("manipulation_component_pass"),
            "closed_loop_summary": closed_loop,
            "structural_bundle_path_id": structural_bundle.get("path_id"),
            "workflow_candidate_status": workflow_candidate.get("candidate_status"),
            "pre_bayes_gate": pre_bayes.get("latest_gate_status") or workflow_candidate.get("pre_bayes_gate_status"),
            "pre_bayes_quality": (execution_candidate.get("pre_bayes_evidence_filter") or {}).get("evidence_quality_score"),
            "bbn_application_status": (execution_candidate.get("pre_bayes_evidence_filter") or {}).get("evidence_assignments", {}).get("regime_bundle_bbn_application_status"),
            "catboost_runtime_status": (policy.get("structural_path_ranking_runtime") or {}).get("status"),
            "catboost_validation_summary": (policy.get("structural_path_ranking_validation") or {}).get("summary_line"),
            "export_target_summary": export_target.get("summary_line"),
            "execution_tree_branch": execution_output.get("branch"),
            "execution_tree_gate": execution_output.get("gate_status"),
            "execution_tree_reason": execution_output.get("consumer_reason"),
            "execution_tree_ranker_score_used": execution_output.get("path_ranker_score_used_by_execution_tree"),
            "execution_tree_ranker_validation_ready": execution_output.get("ranker_validation_ready"),
        },
        "commands": [
            command_record("provider", "provider_status_agent"),
            command_record("provider", "harness_yfinance_qqq_1d"),
            command_record("provider", "harness_tradingview_qqq_1d"),
            command_record("provider", "harness_ibkr_qqq_1d"),
            command_record("provider", "kraken_cli_xbtusd_1h_ohlc"),
            command_record("auto-quant", "auto_quant_runpy_help"),
            command_record("auto-quant", "local_auto_quant_visibility"),
            command_record("ict-engine", "pre_bayes_status_refresh_json"),
            command_record("ict-engine", "policy_training_status_json"),
            command_record("ict-engine", "export_structural_path_ranking_target"),
            command_record("ict-engine", "workflow_structural_recommended_path_bundle"),
            command_record("ict-engine", "workflow_execution_candidate"),
        ],
        "promotion_allowed": False,
        "decision": "nursery_feedback_materialized_promotion_blocked_by_execution_admissibility",
        "next_action": "Accumulate more non-crowded compatible execution-context observations before rerunning 220646 promotion readback.",
    }

    JSON_PATH.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(nursery_row.keys()))
        writer.writeheader()
        writer.writerow(nursery_row)

    lines = [
        "# B2R Block-Crowded Nursery Feedback v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        "- Nursery status: `incubation_only`",
        "- Promotion allowed: `false`",
        f"- Exact branch path: `{BRANCH_PATH}`",
        f"- RC-SPA score: `{rc_decision.get('stable_profit_score')}`; gate `{rc_decision.get('gate_result')}`; price roots `{rc_decision.get('price_root_paths_passed')}/4`",
        f"- Pre-Bayes/filter: `{packet['downstream_readback']['pre_bayes_gate']}`",
        f"- BBN probe: `{packet['downstream_readback']['bbn_application_status']}`",
        f"- CatBoost/path-ranker: `{packet['downstream_readback']['catboost_runtime_status']}`; validation `{packet['downstream_readback']['catboost_validation_summary']}`",
        f"- Execution tree: `{packet['downstream_readback']['execution_tree_branch']}` / `{packet['downstream_readback']['execution_tree_gate']}`",
        f"- Blocker: `{packet['downstream_readback']['execution_tree_reason']}`",
        "",
        "## Provider Readback",
        "",
        "| Provider | Fresh result | Artifact |",
        "|---|---|---|",
        f"| `yfinance` | harness ok `{yfinance['ok_count']}` exit `{yfinance['exit_code']}` | `{yfinance['stdout']}` |",
        f"| `TradingViewRemix/tradingview_mcp` | harness ok `{tradingview['ok_count']}` errors `{tradingview['error_count']}` exit `{tradingview['exit_code']}` | `{tradingview['stdout']}` |",
        f"| `IBKR` | harness ok `{ibkr['ok_count']}` errors `{ibkr['error_count']}` exit `{ibkr['exit_code']}` | `{ibkr['stdout']}` |",
        f"| `Kraken CLI` | OHLC rows `{kraken['rows']}` exit `{kraken['exit_code']}` | `{kraken['stdout']}` |",
        "",
        "## Auto-Quant Readback",
        "",
        f"- Local visibility: `{auto_quant['visibility']}`",
        f"- Source Auto-Quant/RC-SPA artifact: `{auto_quant['source_rc_spa_artifact']}`",
        f"- `run.py --help` exit `{auto_quant['runpy_help_exit']}`; this is a default-strategy discovery issue, not a blocker for the existing `220646` sourced artifact.",
        "",
        "## Nursery Row",
        "",
        f"- CSV: `{rel(CSV_PATH)}`",
        f"- JSON: `{rel(JSON_PATH)}`",
        "",
        "## Next",
        "",
        packet["next_action"],
        "",
    ]
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")

    assertions = {
        "run_id": RUN_ID,
        "rc_spa_gate_pass": rc_decision.get("gate_result") == "pass",
        "branch_path_preserved": structural_bundle.get("path_id") == BRANCH_PATH,
        "pre_bayes_seen": packet["downstream_readback"]["pre_bayes_gate"] == "pass_neutralized",
        "catboost_runtime_ready": packet["downstream_readback"]["catboost_runtime_status"] == "enabled_candidate_set_ready",
        "execution_tree_block_crowded": packet["downstream_readback"]["execution_tree_branch"] == "block_crowded",
        "ranker_used_by_execution_tree": packet["downstream_readback"]["execution_tree_ranker_score_used"] is True,
        "yfinance_fresh_ok": yfinance["ok_count"] > 0 and yfinance["exit_code"] == 0,
        "kraken_cli_fresh_ok": kraken["rows"] > 0 and kraken["exit_code"] == 0,
        "nursery_status": nursery_row["nursery_status"],
        "promotion_allowed": False,
        "report_md": rel(MD_PATH),
        "report_json": rel(JSON_PATH),
        "report_csv": rel(CSV_PATH),
    }
    required_true = [
        "rc_spa_gate_pass",
        "branch_path_preserved",
        "pre_bayes_seen",
        "catboost_runtime_ready",
        "execution_tree_block_crowded",
        "ranker_used_by_execution_tree",
        "yfinance_fresh_ok",
        "kraken_cli_fresh_ok",
    ]
    failures = [key for key in required_true if assertions.get(key) is not True]
    if assertions["nursery_status"] != "incubation_only":
        failures.append("nursery_status")
    if assertions["promotion_allowed"] is not False:
        failures.append("promotion_allowed")
    with ASSERTIONS.open("w", encoding="utf-8") as handle:
        for key, value in assertions.items():
            handle.write(f"{key}={value}\n")
        for key in failures:
            handle.write(f"ASSERT_FAIL:{key}\n")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
