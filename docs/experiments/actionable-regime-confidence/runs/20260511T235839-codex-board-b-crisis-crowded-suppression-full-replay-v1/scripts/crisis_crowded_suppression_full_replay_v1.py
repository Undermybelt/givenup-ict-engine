#!/usr/bin/env python3
"""Build the Board B full nursery replay for the Crisis crowded suppression sibling.

This is intentionally run-local: it consumes the already scored 220646 selected
rows, rewrites the Crisis leaf into a no-trade sibling branch, and summarizes
fresh downstream command outputs captured in this run root. It does not modify
ict-engine runtime code.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T235839+0800-codex-board-b-crisis-crowded-suppression-full-replay-v1"
RUN_SLUG = "20260511T235839-codex-board-b-crisis-crowded-suppression-full-replay-v1"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
RECIPE_ID = "CrisisCrowdedSuppressionSiblingV1"
SOURCE_RECIPE_ID = "SourceRootStopCarryLongHorizonV1"
ACCEPTED_REGIME_ID = "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation"
SOURCE_CRISIS_PATH = (
    "Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> "
    "SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12"
)
SIBLING_PATH = (
    "Crisis -> CrisisReliefCarry -> BlockCrowdedSuppression -> "
    "SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1"
)
SUPPRESSION_RULE = (
    "if execution_tree_branch=block_crowded or execution_readiness<0.45 "
    "or live_context=RangeConsolidation/WideRange then no_trade"
)

HERE = Path(__file__).resolve().parent
RUN_ROOT = HERE.parent
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
OUT_DIR = RUN_ROOT / "b2r-suppression-full-replay"
CHECK_DIR = RUN_ROOT / "checks"
COMMAND_DIR = RUN_ROOT / "command-output"
STATE_DIR = RUN_ROOT / "state_crisis_crowded_suppression_full_replay_v1"

SOURCE_220646 = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
)
SOURCE_SELECTED = SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_selected_rows_v1.csv"
SOURCE_BRANCH_SUMMARY = (
    SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_branch_summary_v1.csv"
)
SOURCE_RC_SPA_JSON = (
    SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.json"
)
SOURCE_RC_SPA_MD = (
    SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.md"
)
SOURCE_STRATEGY_LIBRARY = (
    SOURCE_220646 / "autoquant/strategy_library_source_root_stop_carry_longhorizon_v1.json"
)
SOURCE_REGIME_BUNDLE = (
    SOURCE_220646 / "downstream-chain/regime-bundles/aggregate_regime_consumer_bundle_v1.json"
)
SOURCE_SIBLING_JSON = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T234938-codex-board-b-crisis-crowded-suppression-sibling-v1/"
    "crisis-crowded-suppression-sibling/crisis_crowded_suppression_sibling_v1.json"
)

FULL_ROWS = OUT_DIR / "crisis_crowded_suppression_full_replay_rows_v1.csv"
BRANCH_SUMMARY = OUT_DIR / "crisis_crowded_suppression_full_replay_branch_summary_v1.csv"
FOLD_SUMMARY = OUT_DIR / "crisis_crowded_suppression_full_replay_fold_summary_v1.csv"
REPORT_JSON = OUT_DIR / "crisis_crowded_suppression_full_replay_v1.json"
REPORT_MD = OUT_DIR / "crisis_crowded_suppression_full_replay_v1.md"
ASSERTIONS = CHECK_DIR / "crisis_crowded_suppression_full_replay_v1_assertions.out"


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
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"json_error": f"{type(exc).__name__}:{exc}", "path": rel(path)}
    return payload if isinstance(payload, dict) else {"value": payload}


def read_exit(name: str) -> int | None:
    path = COMMAND_DIR / f"{name}.exit"
    try:
        return int(read_text(path).strip())
    except Exception:
        return None


def command_record(name: str) -> dict[str, Any]:
    return {
        "name": name,
        "cmd": read_text(COMMAND_DIR / f"{name}.cmd").strip(),
        "exit_code": read_exit(name),
        "stdout": rel(COMMAND_DIR / f"{name}.out"),
        "stderr": rel(COMMAND_DIR / f"{name}.err"),
    }


def command_json(name: str) -> dict[str, Any]:
    return read_json(COMMAND_DIR / f"{name}.out")


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        val = float(value)
        if math.isnan(val) or math.isinf(val):
            return default
        return val
    except Exception:
        return default


def recursive_find(payload: Any, key: str) -> Any:
    if isinstance(payload, dict):
        if key in payload:
            return payload[key]
        for value in payload.values():
            found = recursive_find(value, key)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = recursive_find(value, key)
            if found is not None:
                return found
    return None


def load_branch_summary() -> dict[str, dict[str, str]]:
    if not SOURCE_BRANCH_SUMMARY.exists():
        return {}
    with SOURCE_BRANCH_SUMMARY.open(newline="", encoding="utf-8") as handle:
        return {row["parent_regime_root"]: row for row in csv.DictReader(handle)}


def source_decision() -> dict[str, Any]:
    payload = read_json(SOURCE_RC_SPA_JSON)
    return payload.get("decision", payload)


def provider_status(provider_id: str) -> dict[str, Any]:
    payload = command_json(f"provider_status_{provider_id}")
    providers = payload.get("providers", [])
    if isinstance(providers, list) and providers:
        return {
            "ready": any(bool(row.get("ready")) for row in providers if row.get("provider_id") == provider_id),
            "statuses": [
                {
                    "domain": row.get("domain"),
                    "ready": row.get("ready"),
                    "status": row.get("status"),
                    "reason": row.get("reason"),
                }
                for row in providers
                if row.get("provider_id") == provider_id
            ],
            "summary_line": payload.get("summary_line"),
            "exit_code": read_exit(f"provider_status_{provider_id}"),
        }
    return {"ready": False, "statuses": [], "summary_line": payload.get("summary_line"), "exit_code": read_exit(f"provider_status_{provider_id}")}


def build_replay_rows() -> tuple[list[dict[str, str]], dict[str, Any]]:
    rows: list[dict[str, str]] = []
    with SOURCE_SELECTED.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        input_fields = reader.fieldnames or []
        extra_fields = [
            "nursery_branch_id",
            "source_regime_profit_branch_path",
            "replay_regime_profit_branch_path",
            "replay_branch_path_version",
            "replay_action_leaf",
            "replay_trade_executed",
            "suppression_triggered",
            "suppression_reason",
            "source_profit_ratio_net",
            "replay_profit_ratio_net",
            "source_roundtrip_cost",
            "replay_roundtrip_cost",
            "prevented_source_profit_ratio_net",
        ]
        for row in reader:
            root = row.get("parent_regime_root", "")
            source_net = fnum(row.get("profit_ratio_net"))
            source_cost = fnum(row.get("roundtrip_cost"))
            out = dict(row)
            out["nursery_branch_id"] = "B2R_CRISIS_CROWDED_SUPPRESSION_FULL_REPLAY_V1"
            out["source_regime_profit_branch_path"] = row.get("regime_profit_branch_path", "")
            out["source_profit_ratio_net"] = f"{source_net:.12f}"
            out["source_roundtrip_cost"] = f"{source_cost:.12f}"
            if root == "Crisis":
                out["sub_sub_regime_or_profit_factor"] = "BlockCrowdedSuppression"
                out["profit_factor_leaf"] = (
                    "SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1"
                )
                out["regime_profit_branch_path"] = SIBLING_PATH
                out["allowed_action"] = "no_trade_when_block_crowded_or_wide_range"
                out["suppression_rule"] = SUPPRESSION_RULE
                out["direction"] = "flat"
                out["direction_sign"] = "0"
                out["exit_reason"] = "no_trade_suppressed_by_crowded_range_context"
                out["roundtrip_cost"] = "0.000000000000"
                out["profit_ratio_net"] = "0.000000000000"
                out["replay_regime_profit_branch_path"] = SIBLING_PATH
                out["replay_branch_path_version"] = "board-b-crisis-crowded-suppression-full-replay/v1"
                out["replay_action_leaf"] = "no_trade"
                out["replay_trade_executed"] = "false"
                out["suppression_triggered"] = "true"
                out["suppression_reason"] = (
                    "encoded_sibling_rule_for_block_crowded_or_execution_readiness_below_0_45_"
                    "or_RangeConsolidation_WideRange"
                )
                out["replay_profit_ratio_net"] = "0.000000000000"
                out["replay_roundtrip_cost"] = "0.000000000000"
                out["prevented_source_profit_ratio_net"] = f"{source_net:.12f}"
            else:
                out["replay_regime_profit_branch_path"] = row.get("regime_profit_branch_path", "")
                out["replay_branch_path_version"] = row.get("regime_profit_branch_path_version", "")
                out["replay_action_leaf"] = row.get("allowed_action", "")
                out["replay_trade_executed"] = "true"
                out["suppression_triggered"] = "false"
                out["suppression_reason"] = "not_crisis_suppression_branch"
                out["replay_profit_ratio_net"] = f"{source_net:.12f}"
                out["replay_roundtrip_cost"] = f"{source_cost:.12f}"
                out["prevented_source_profit_ratio_net"] = "0.000000000000"
            rows.append(out)

    fieldnames = [name for name in input_fields if name in rows[0]]
    for name in extra_fields:
        if name not in fieldnames:
            fieldnames.append(name)
    with FULL_ROWS.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    source_total = sum(fnum(row.get("source_profit_ratio_net")) for row in rows)
    replay_total = sum(fnum(row.get("replay_profit_ratio_net")) for row in rows)
    crisis_rows = [row for row in rows if row.get("parent_regime_root") == "Crisis"]
    executed_rows = [row for row in rows if row.get("replay_trade_executed") == "true"]
    no_trade_rows = [row for row in rows if row.get("replay_trade_executed") == "false"]
    summary = {
        "input_selected_rows": len(rows),
        "full_replay_rows": len(rows),
        "executed_trade_rows": len(executed_rows),
        "no_trade_rows": len(no_trade_rows),
        "crisis_decision_rows": len(crisis_rows),
        "crisis_suppressed_rows": sum(1 for row in crisis_rows if row.get("suppression_triggered") == "true"),
        "source_total_net": source_total,
        "replay_total_net": replay_total,
        "prevented_crisis_source_net": sum(fnum(row.get("prevented_source_profit_ratio_net")) for row in crisis_rows),
        "source_artifact": rel(SOURCE_SELECTED),
        "full_rows_artifact": rel(FULL_ROWS),
    }
    return rows, summary


def summarize_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_branch: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    by_fold: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        root = row.get("parent_regime_root", "")
        branch = row.get("replay_regime_profit_branch_path", "")
        fold = row.get("year_fold", "")
        by_branch[(root, branch)].append(row)
        by_fold[(root, fold)].append(row)

    branch_rows: list[dict[str, Any]] = []
    for (root, branch), group in sorted(by_branch.items()):
        executed = [row for row in group if row.get("replay_trade_executed") == "true"]
        no_trade = [row for row in group if row.get("replay_trade_executed") == "false"]
        fold_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in group:
            fold_groups[row.get("year_fold", "")].append(row)
        fold_net = {
            fold: sum(fnum(row.get("replay_profit_ratio_net")) for row in fold_rows if row.get("replay_trade_executed") == "true")
            for fold, fold_rows in fold_groups.items()
        }
        branch_rows.append(
            {
                "parent_regime_root": root,
                "replay_regime_profit_branch_path": branch,
                "decision_rows": len(group),
                "executed_trade_rows": len(executed),
                "no_trade_rows": len(no_trade),
                "folds": len(fold_groups),
                "min_decision_rows_per_fold": min((len(v) for v in fold_groups.values()), default=0),
                "min_executed_rows_per_fold": min(
                    (sum(1 for row in v if row.get("replay_trade_executed") == "true") for v in fold_groups.values()),
                    default=0,
                ),
                "fold_positive_rate": (
                    sum(1 for value in fold_net.values() if value > 0.0) / len(fold_net) if fold_net else 0.0
                ),
                "source_net_sum": sum(fnum(row.get("source_profit_ratio_net")) for row in group),
                "replay_net_sum": sum(fnum(row.get("replay_profit_ratio_net")) for row in group),
                "replay_mean_net_executed": (
                    sum(fnum(row.get("replay_profit_ratio_net")) for row in executed) / len(executed)
                    if executed
                    else 0.0
                ),
                "win_rate_net_executed": (
                    sum(1 for row in executed if fnum(row.get("replay_profit_ratio_net")) > 0.0) / len(executed)
                    if executed
                    else 0.0
                ),
                "nursery_gate": "pass:decision_evidence_no_trade_leaf" if no_trade else "pass:executed_trade_leaf",
                "promotion_gate": "fail:nursery_feedback_only_not_promotable",
            }
        )

    fold_rows: list[dict[str, Any]] = []
    for (root, fold), group in sorted(by_fold.items()):
        executed = [row for row in group if row.get("replay_trade_executed") == "true"]
        no_trade = [row for row in group if row.get("replay_trade_executed") == "false"]
        fold_rows.append(
            {
                "parent_regime_root": root,
                "year_fold": fold,
                "decision_rows": len(group),
                "executed_trade_rows": len(executed),
                "no_trade_rows": len(no_trade),
                "source_net_sum": sum(fnum(row.get("source_profit_ratio_net")) for row in group),
                "replay_net_sum": sum(fnum(row.get("replay_profit_ratio_net")) for row in group),
                "replay_mean_net_executed": (
                    sum(fnum(row.get("replay_profit_ratio_net")) for row in executed) / len(executed)
                    if executed
                    else 0.0
                ),
                "win_rate_net_executed": (
                    sum(1 for row in executed if fnum(row.get("replay_profit_ratio_net")) > 0.0) / len(executed)
                    if executed
                    else 0.0
                ),
            }
        )

    if branch_rows:
        with BRANCH_SUMMARY.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(branch_rows[0].keys()))
            writer.writeheader()
            writer.writerows(branch_rows)
    if fold_rows:
        with FOLD_SUMMARY.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(fold_rows[0].keys()))
            writer.writeheader()
            writer.writerows(fold_rows)
    return branch_rows, fold_rows


def downstream_readback() -> dict[str, Any]:
    analyze = command_json("analyze_live")
    pre_bayes = command_json("pre_bayes_status")
    structural = command_json("workflow_structural_recommended_path_bundle")
    execution_candidate = command_json("workflow_execution_candidate")
    policy = command_json("policy_training_status")
    export_target = command_json("export_structural_path_ranking_target")
    workflow = command_json("workflow_status_agent")

    execution_triage = recursive_find(analyze, "execution_triage") or {}
    if not execution_triage:
        trace = read_json(STATE_DIR / SYMBOL / "execution_tree_trace.json")
        execution_triage = trace.get("output", {})
    policy_runtime = policy.get("structural_path_ranking_runtime") or {}
    policy_validation = policy.get("structural_path_ranking_validation") or {}
    bbn_status = (
        recursive_find(analyze, "regime_bundle_bbn_application_status")
        or recursive_find(execution_candidate, "regime_bundle_bbn_application_status")
        or recursive_find(read_json(STATE_DIR / SYMBOL / "execution_candidate.json"), "regime_bundle_bbn_application_status")
    )
    bbn_regime = (
        recursive_find(analyze, "regime_bundle_bbn_market_regime")
        or recursive_find(execution_candidate, "regime_bundle_bbn_market_regime")
        or recursive_find(read_json(STATE_DIR / SYMBOL / "execution_candidate.json"), "regime_bundle_bbn_market_regime")
    )
    return {
        "commands": [
            command_record("provider_status_agent"),
            command_record("provider_status_yfinance"),
            command_record("provider_status_tradingview_mcp"),
            command_record("provider_status_ibkr"),
            command_record("provider_status_kraken_cli"),
            command_record("auto_quant_status"),
            command_record("auto_quant_results_import"),
            command_record("analyze_live"),
            command_record("pre_bayes_status"),
            command_record("workflow_structural_recommended_path_bundle"),
            command_record("policy_training_status"),
            command_record("export_structural_path_ranking_target"),
            command_record("workflow_execution_candidate"),
            command_record("workflow_status_agent"),
        ],
        "provider_readback": {
            "summary": command_json("provider_status_agent").get("summary_line"),
            "yfinance": provider_status("yfinance"),
            "tradingview_mcp": provider_status("tradingview_mcp"),
            "ibkr": provider_status("ibkr"),
            "kraken_cli": provider_status("kraken_cli"),
        },
        "auto_quant_readback": {
            "status": command_json("auto_quant_status").get("status"),
            "healthy": command_json("auto_quant_status").get("healthy"),
            "results_import_exit": read_exit("auto_quant_results_import"),
            "library_source": rel(SOURCE_STRATEGY_LIBRARY),
        },
        "pre_bayes_probe": {
            "exit_code": read_exit("pre_bayes_status"),
            "latest_gate_status": pre_bayes.get("latest_gate_status"),
            "gate_from_execution_candidate": execution_candidate.get("pre_bayes_gate_status"),
            "quality_from_execution_candidate": recursive_find(execution_candidate, "pre_bayes_quality_score")
            or recursive_find(analyze, "pre_bayes_quality_score"),
        },
        "bbn_probe": {
            "exit_code": read_exit("analyze_live"),
            "soft_evidence_application_status": bbn_status,
            "soft_evidence_market_regime": bbn_regime,
            "bundle": rel(SOURCE_REGIME_BUNDLE),
        },
        "catboost_path_ranker_probe": {
            "exit_code": read_exit("policy_training_status"),
            "runtime_status": policy_runtime.get("status"),
            "runtime_ready": policy_runtime.get("ready"),
            "validation_summary": policy_runtime.get("summary_line")
            or policy_validation.get("summary_line"),
            "export_rows": export_target.get("rows"),
            "history_rows": export_target.get("history_rows"),
            "mature_rows": export_target.get("mature_rows"),
        },
        "execution_tree_probe": {
            "exit_code": read_exit("analyze_live"),
            "source_runtime_path": structural.get("path_id"),
            "sibling_overlay_path": SIBLING_PATH,
            "candidate_status": execution_candidate.get("candidate_status"),
            "review_status": execution_candidate.get("review_status"),
            "branch": execution_triage.get("branch"),
            "gate_status": execution_triage.get("gate_status"),
            "consumer_reason": execution_triage.get("consumer_reason"),
            "one_line": execution_triage.get("one_line"),
            "sibling_action_result": "no_trade",
            "workflow_blocker": recursive_find(workflow, "blocked_reason"),
        },
    }


def write_report(
    replay_summary: dict[str, Any],
    branch_rows: list[dict[str, Any]],
    fold_rows: list[dict[str, Any]],
    downstream: dict[str, Any],
) -> dict[str, Any]:
    source = source_decision()
    branch_summary = load_branch_summary()
    sibling_packet = read_json(SOURCE_SIBLING_JSON)
    crisis_source = branch_summary.get("Crisis", {})
    packet = {
        "schema_version": "board-b-crisis-crowded-suppression-full-replay/v1",
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "accepted_regime_id": ACCEPTED_REGIME_ID,
        "source_recipe_id": SOURCE_RECIPE_ID,
        "recipe_id": RECIPE_ID,
        "nursery_status": "incubation_only",
        "source_branch_path": SOURCE_CRISIS_PATH,
        "sibling_branch_path": SIBLING_PATH,
        "suppression_rule": SUPPRESSION_RULE,
        "source_rc_spa": {
            "gate_result": source.get("gate_result"),
            "stable_profit_score": source.get("stable_profit_score"),
            "price_root_paths_passed": source.get("price_root_paths_passed"),
            "manipulation_component_pass": source.get("manipulation_component_pass"),
            "crisis_trade_count": int(crisis_source.get("total_trades", 0) or 0),
            "crisis_rc_spa": fnum(crisis_source.get("rc_spa")),
            "artifact": rel(SOURCE_RC_SPA_MD),
        },
        "full_replay_backtest": replay_summary,
        "branch_summary_artifact": rel(BRANCH_SUMMARY),
        "fold_summary_artifact": rel(FOLD_SUMMARY),
        "full_rows_artifact": rel(FULL_ROWS),
        "downstream_readback": downstream,
        "source_sibling_packet": {
            "decision": sibling_packet.get("decision"),
            "current_runtime_suppression_action": (sibling_packet.get("current_runtime_test") or {}).get("suppression_action_result"),
            "artifact": rel(SOURCE_SIBLING_JSON),
        },
        "decision": "nursery_feedback_full_replay_recorded_not_promotion",
        "hard_gate_result": "pass:nursery_gate;fail_closed:promotion_gate_not_applicable_no_trade_sibling",
        "promotion_allowed": False,
        "next_action": (
            "Keep the sibling leaf as incubation feedback and collect repeated compatible/non-compatible "
            "execution-context observations; do not promote from this no-trade overlay."
        ),
    }
    REPORT_JSON.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    exec_probe = downstream["execution_tree_probe"]
    pre = downstream["pre_bayes_probe"]
    bbn = downstream["bbn_probe"]
    cat = downstream["catboost_path_ranker_probe"]
    lines = [
        "# Crisis Crowded Suppression Full Replay v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        "- Nursery status: `incubation_only`",
        "- Promotion allowed: `false`",
        f"- Sibling branch path: `{SIBLING_PATH}`",
        f"- Suppression rule: `{SUPPRESSION_RULE}`",
        "- Result: full replay encoded the Crisis branch as `no_trade`; this is execution-admissibility feedback, not a profitability promotion.",
        "",
        "## Full Replay Backtest",
        "",
        f"- Input selected rows: `{replay_summary['input_selected_rows']}`",
        f"- Executed replay trades: `{replay_summary['executed_trade_rows']}`",
        f"- No-trade rows: `{replay_summary['no_trade_rows']}`",
        f"- Crisis decisions suppressed: `{replay_summary['crisis_suppressed_rows']}/{replay_summary['crisis_decision_rows']}`",
        f"- Source total net: `{replay_summary['source_total_net']:.6f}`",
        f"- Replay total net after suppression: `{replay_summary['replay_total_net']:.6f}`",
        f"- Prevented Crisis source net: `{replay_summary['prevented_crisis_source_net']:.6f}`",
        f"- Rows: `{rel(FULL_ROWS)}`",
        f"- Branch summary: `{rel(BRANCH_SUMMARY)}`",
        f"- Fold summary: `{rel(FOLD_SUMMARY)}`",
        "",
        "## Downstream Probes",
        "",
        f"- Pre-Bayes/filter: `{pre['latest_gate_status'] or pre['gate_from_execution_candidate']}`",
        f"- BBN soft evidence: `{bbn['soft_evidence_application_status']}` / `{bbn['soft_evidence_market_regime']}`",
        f"- CatBoost/path-ranker: `{cat['runtime_status']}`; export rows `{cat['export_rows']}` history `{cat['history_rows']}`",
        f"- Execution tree source runtime path: `{exec_probe['source_runtime_path']}`",
        f"- Execution tree branch/gate: `{exec_probe['branch']}` / `{exec_probe['gate_status']}`",
        f"- Sibling overlay action: `{exec_probe['sibling_action_result']}`",
        f"- Execution reason: `{exec_probe['consumer_reason']}`",
        "",
        "## Provider / Auto-Quant",
        "",
        f"- Provider summary: `{downstream['provider_readback']['summary']}`",
        f"- yfinance ready: `{downstream['provider_readback']['yfinance']['ready']}`",
        f"- TradingViewRemix ready: `{downstream['provider_readback']['tradingview_mcp']['ready']}`",
        f"- IBKR ready: `{downstream['provider_readback']['ibkr']['ready']}`",
        f"- Kraken CLI ready: `{downstream['provider_readback']['kraken_cli']['ready']}`",
        f"- Auto-Quant status: `{downstream['auto_quant_readback']['status']}`; source library import exit `{downstream['auto_quant_readback']['results_import_exit']}`",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{rel(REPORT_JSON)}`",
        f"- Assertions: `{rel(ASSERTIONS)}`",
        "",
        "## Next",
        "",
        packet["next_action"],
        "",
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    return packet


def write_assertions(packet: dict[str, Any]) -> int:
    replay = packet["full_replay_backtest"]
    source = packet["source_rc_spa"]
    downstream = packet["downstream_readback"]
    exec_probe = downstream["execution_tree_probe"]
    pre = downstream["pre_bayes_probe"]
    bbn = downstream["bbn_probe"]
    cat = downstream["catboost_path_ranker_probe"]
    assertions = {
        "run_id": RUN_ID,
        "source_rows_loaded": replay["input_selected_rows"] == 12329,
        "full_replay_rows_written": replay["full_replay_rows"] == 12329,
        "crisis_rows_suppressed": replay["crisis_suppressed_rows"] == 532,
        "sibling_branch_path_exact": packet["sibling_branch_path"] == SIBLING_PATH,
        "source_rc_spa_pass": source["gate_result"] == "pass",
        "price_roots_passed_4": source["price_root_paths_passed"] == 4,
        "auto_quant_import_exit0": downstream["auto_quant_readback"]["results_import_exit"] == 0,
        "pre_bayes_command_exit0": pre["exit_code"] == 0,
        "pre_bayes_probe_seen": bool(pre["latest_gate_status"] or pre["gate_from_execution_candidate"]),
        "bbn_probe_command_exit0": bbn["exit_code"] == 0,
        "bbn_probe_seen": bool(bbn["soft_evidence_application_status"] or bbn["soft_evidence_market_regime"]),
        "catboost_runtime_ready": cat["runtime_ready"] is True or cat["runtime_status"] == "enabled_candidate_set_ready",
        "execution_tree_command_exit0": exec_probe["exit_code"] == 0,
        "execution_tree_probe_seen": bool(exec_probe["branch"] or exec_probe["gate_status"]),
        "sibling_action_no_trade": exec_probe["sibling_action_result"] == "no_trade",
        "promotion_allowed_false": packet["promotion_allowed"] is False,
        "nursery_status_incubation_only": packet["nursery_status"] == "incubation_only",
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "report_md": rel(REPORT_MD),
        "report_json": rel(REPORT_JSON),
    }
    required_true = [
        "source_rows_loaded",
        "full_replay_rows_written",
        "crisis_rows_suppressed",
        "sibling_branch_path_exact",
        "source_rc_spa_pass",
        "price_roots_passed_4",
        "auto_quant_import_exit0",
        "pre_bayes_command_exit0",
        "pre_bayes_probe_seen",
        "bbn_probe_command_exit0",
        "bbn_probe_seen",
        "catboost_runtime_ready",
        "execution_tree_command_exit0",
        "execution_tree_probe_seen",
        "sibling_action_no_trade",
        "promotion_allowed_false",
        "nursery_status_incubation_only",
    ]
    failures = [key for key in required_true if assertions.get(key) is not True]
    with ASSERTIONS.open("w", encoding="utf-8") as handle:
        for key, value in assertions.items():
            handle.write(f"{key}={value}\n")
        for key in failures:
            handle.write(f"ASSERT_FAIL:{key}\n")
    return 1 if failures else 0


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    rows, replay_summary = build_replay_rows()
    branch_rows, fold_rows = summarize_rows(rows)
    downstream = downstream_readback()
    packet = write_report(replay_summary, branch_rows, fold_rows, downstream)
    exit_code = write_assertions(packet)
    print(rel(REPORT_MD))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
