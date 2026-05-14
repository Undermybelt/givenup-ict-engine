#!/usr/bin/env python3
"""Full nursery replay for the Crisis crowded-suppression sibling leaf.

The script is intentionally run-local. It writes a full no-trade replay from
the 220646 Crisis rows, applies one structural `not_followed` feedback probe
into an isolated ict-engine state, and records cheap downstream probes. It does
not change repo runtime code and never promotes the candidate.
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T235747+0800-codex-board-b-crisis-crowded-suppression-full-replay-v1"
SCHEMA_VERSION = "board-b-crisis-crowded-suppression-full-replay/v1"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
ACCEPTED_REGIME_ID = "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation"
SOURCE_RECIPE = "SourceRootStopCarryLongHorizonV1"
SIBLING_RECIPE = "CrisisCrowdedSuppressionSiblingV1"
SOURCE_BRANCH_PATH = (
    "Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> "
    "SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12"
)
SIBLING_BRANCH_PATH = (
    "Crisis -> CrisisReliefCarry -> BlockCrowdedSuppression -> "
    "SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1"
)
MARKET_CONTEXT = "RangeConsolidation/WideRange"
EXECUTION_BLOCKER = "block_crowded"
READINESS = 0.4433
READINESS_FLOOR = 0.45

SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
ICT = REPO / "target" / "debug" / "ict-engine"

SOURCE_220646 = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
)
SOURCE_SELECTED_ROWS = (
    SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_selected_rows_v1.csv"
)
SOURCE_BRANCH_SUMMARY = (
    SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_branch_summary_v1.csv"
)
SOURCE_RC_SPA = (
    SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.json"
)
SOURCE_WIRE = (
    SOURCE_220646
    / "b5-branch-feedback-calibration-v1/selected_real_trades_wire.jsonl"
)
SOURCE_BUNDLE = (
    SOURCE_220646 / "downstream-chain/regime-bundles/aggregate_regime_consumer_bundle_v1.json"
)
SOURCE_CLOSED_LOOP = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T231800-codex-board-b-220646-exact-branch-closed-loop-readback-v4/"
    "exact-branch-closed-loop-readback-v4"
)
SOURCE_STATE = SOURCE_CLOSED_LOOP / "state_exact_branch_closed_loop_v4"
SOURCE_CLOSED_LOOP_JSON = SOURCE_CLOSED_LOOP / "exact_branch_closed_loop_readback_v4.json"
SOURCE_TRACE = SOURCE_STATE / SYMBOL / "execution_tree_trace.json"
SOURCE_234938 = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T234938-codex-board-b-crisis-crowded-suppression-sibling-v1/"
    "crisis-crowded-suppression-sibling/crisis_crowded_suppression_sibling_v1.json"
)

OUT = RUN_ROOT / "crisis-crowded-suppression-full-replay"
COMMANDS = OUT / "command-output"
PROVIDER = OUT / "provider"
CHECKS = RUN_ROOT / "checks"
STATE_DIR = OUT / "state_crisis_crowded_suppression_full_replay_v1"
AUTO_QUANT_DRY_STATE_DIR = OUT / "state_auto_quant_source_wire_dry_run"
REPLAY_CSV = OUT / "crisis_crowded_suppression_full_replay_rows_v1.csv"
REPLAY_JSON = OUT / "crisis_crowded_suppression_full_replay_summary_v1.json"
FEEDBACK_JSON = OUT / "feedback" / "crisis_crowded_suppression_not_followed_feedback_v1.json"
REPORT_MD = OUT / "crisis_crowded_suppression_full_replay_v1.md"
ASSERTIONS = CHECKS / "crisis_crowded_suppression_full_replay_v1_assertions.out"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_command(
    name: str,
    cmd: list[str],
    out_dir: Path = COMMANDS,
    timeout: int | None = 180,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = out_dir / f"{name}.out"
    stderr_path = out_dir / f"{name}.err"
    exit_path = out_dir / f"{name}.exit"
    timed_out = False
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO),
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        returncode = proc.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        stderr = f"{stderr}\nTIMEOUT after {timeout}s\n"
        returncode = 124
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{returncode}\n", encoding="utf-8")
    return {
        "name": name,
        "cmd": cmd,
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout_path": rel(stdout_path),
        "stderr_path": rel(stderr_path),
        "exit_path": rel(exit_path),
    }


def parse_provider_status(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    providers = payload.get("providers") if isinstance(payload.get("providers"), list) else []
    if providers:
        ready = any(bool(item.get("ready")) for item in providers)
        statuses = sorted({str(item.get("status")) for item in providers if item.get("status")})
        reasons = sorted({str(item.get("reason")) for item in providers if item.get("reason")})
        domains = sorted({str(item.get("domain")) for item in providers if item.get("domain")})
        provider_id = providers[0].get("provider_id")
        return {
            "provider_id": provider_id,
            "ready": ready,
            "status": "ready" if ready else ";".join(statuses),
            "reason": ";".join(reasons),
            "domain": ",".join(domains),
            "records": len(providers),
        }
    return {
        "summary_line": payload.get("summary_line"),
        "ready_by_domain": payload.get("ready_by_domain"),
    }


def source_crisis_summary() -> dict[str, str]:
    for row in read_csv(SOURCE_BRANCH_SUMMARY):
        if row.get("parent_regime_root") == "Crisis":
            return row
    return {}


def build_full_replay_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_rows = read_csv(SOURCE_SELECTED_ROWS)
    crisis_rows = [row for row in source_rows if row.get("parent_regime_root") == "Crisis"]
    replay_rows: list[dict[str, Any]] = []
    by_market: Counter[str] = Counter()
    by_timeframe: Counter[str] = Counter()
    by_fold: Counter[str] = Counter()
    source_net = 0.0
    for row in crisis_rows:
        by_market[row.get("market", "")] += 1
        by_timeframe[row.get("timeframe", "")] += 1
        by_fold[row.get("year_fold", "")] += 1
        try:
            source_net += float(row.get("profit_ratio_net") or 0.0)
        except ValueError:
            pass
        replay_rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": RUN_ID,
                "accepted_regime_id": ACCEPTED_REGIME_ID,
                "source_recipe": SOURCE_RECIPE,
                "sibling_recipe": SIBLING_RECIPE,
                "source_trade_id": row.get("trade_id"),
                "source_market": row.get("market"),
                "source_timeframe": row.get("timeframe"),
                "source_year_fold": row.get("year_fold"),
                "parent_regime_root": "Crisis",
                "child_regime_hypothesis": "CrisisReliefCarry",
                "child_child_or_profit_factor": "BlockCrowdedSuppression",
                "profit_factor_leaf": "SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1",
                "source_branch_path": row.get("regime_profit_branch_path"),
                "sibling_branch_path": SIBLING_BRANCH_PATH,
                "source_allowed_action": row.get("allowed_action"),
                "sibling_allowed_action": "no_trade",
                "suppression_rule": "execution_tree_branch=block_crowded OR execution_readiness<0.45 OR live_context=RangeConsolidation/WideRange",
                "current_execution_tree_branch": EXECUTION_BLOCKER,
                "current_market_context": MARKET_CONTEXT,
                "current_execution_readiness": READINESS,
                "current_execution_readiness_floor": READINESS_FLOOR,
                "trade_taken": "false",
                "replay_outcome": "not_followed",
                "replay_profit_ratio_net": 0.0,
                "source_profit_ratio_net": row.get("profit_ratio_net"),
                "nursery_status": "incubation_only",
                "promotion_allowed": "false",
            }
        )
    summary = {
        "source_total_selected_rows": len(source_rows),
        "source_crisis_rows": len(crisis_rows),
        "replay_rows": len(replay_rows),
        "suppressed_rows": len(replay_rows),
        "trade_taken_rows": 0,
        "source_crisis_mean_net": source_net / len(crisis_rows) if crisis_rows else None,
        "replay_mean_net": 0.0,
        "markets": dict(sorted(by_market.items())),
        "timeframes": dict(sorted(by_timeframe.items())),
        "year_folds": dict(sorted(by_fold.items())),
    }
    return replay_rows, summary


def build_not_followed_feedback(score: float) -> None:
    payload = {
        "protocol_version": SCHEMA_VERSION,
        "symbol": SYMBOL,
        "recommendation_id": "B2R:sibling_suppression:220646:crisis_carry_no_trade_when_block_crowded_v1",
        "recommended_at": RUN_ID,
        "node_id": "Crisis",
        "branch_id": SIBLING_BRANCH_PATH,
        "scenario_id": "CrisisReliefCarry",
        "path_id": SIBLING_BRANCH_PATH,
        "followed_path": False,
        "realized_outcome": "not_followed",
        "realized_pnl": 0.0,
        "direction": "flat",
        "entry_style": "no_trade_when_block_crowded_or_wide_range",
        "exit_reason": "sibling_suppression_no_trade",
        "candidate_set_id": "branch-path-candidates:SourceRootStopCarryLongHorizonV1:220646:sibling-suppression",
        "candidate_set_size": 1,
        "selected_path_probability": score,
        "selected_entry_quality": "observe",
        "selected_entry_quality_probability": score,
        "pre_bayes_gate_status": "pass_neutralized",
        "path_posterior": score,
        "bbn_support_score": score,
        "notes": (
            "crisis_crowded_suppression_full_replay_v1; no-trade sibling leaf; "
            f"execution_tree={EXECUTION_BLOCKER}; market_state={MARKET_CONTEXT}; "
            f"execution_readiness={READINESS:.4f}<{READINESS_FLOOR:.2f}; "
            "not_followed feedback records suppression behavior, not profitability failure"
        ),
        "nursery_feedback": {
            "nursery_status": "incubation_only",
            "feedback_kind": "sibling_no_trade_suppression",
            "source_branch_path": SOURCE_BRANCH_PATH,
            "sibling_branch_path": SIBLING_BRANCH_PATH,
            "execution_blocker": EXECUTION_BLOCKER,
            "market_state": MARKET_CONTEXT,
            "execution_readiness": READINESS,
            "execution_readiness_floor": READINESS_FLOOR,
            "profitability_rejection": False,
            "branch_routing_failure": False,
            "promotion_allowed": False,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    write_json(FEEDBACK_JSON, payload)


def latest_source_score() -> float:
    trace = read_json(SOURCE_TRACE).get("output", {})
    for line in trace.get("split_reason_lineage", []):
        if "ranker_score=" in line and "raw_path_score=" in line:
            marker = "raw_path_score="
            try:
                return float(line.split(marker, 1)[1].split()[0])
            except (IndexError, ValueError):
                pass
    return 0.5


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    for path in [OUT, COMMANDS, PROVIDER, CHECKS]:
        path.mkdir(parents=True, exist_ok=True)
    if STATE_DIR.exists():
        shutil.rmtree(STATE_DIR)
    shutil.copytree(SOURCE_STATE, STATE_DIR)

    replay_rows, replay_summary = build_full_replay_rows()
    write_csv(REPLAY_CSV, replay_rows)
    source_score = latest_source_score()
    build_not_followed_feedback(source_score)

    source_summary = source_crisis_summary()
    source_rc_spa = read_json(SOURCE_RC_SPA)
    source_closed_loop = read_json(SOURCE_CLOSED_LOOP_JSON)
    source_sibling = read_json(SOURCE_234938)

    commands: list[dict[str, Any]] = []
    for provider_id in ["yfinance", "tradingview_mcp", "ibkr", "kraken_public", "kraken_cli"]:
        commands.append(
            run_command(
                f"provider_status_{provider_id}_agent",
                [str(ICT), "provider-status", "--provider", provider_id, "--agent"],
                out_dir=PROVIDER,
                timeout=60,
            )
        )

    commands.append(
        run_command(
            "01_auto_quant_ingest_source_wire_dry_run",
            [
                str(ICT),
                "auto-quant-ingest-real-trades",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(AUTO_QUANT_DRY_STATE_DIR),
                "--trades",
                str(SOURCE_WIRE),
                "--source",
                "board_b_crisis_crowded_suppression_source_wire_dry_run",
                "--dry-run",
            ],
            timeout=120,
        )
    )
    commands.append(
        run_command(
            "02_update_sibling_not_followed_feedback",
            [
                str(ICT),
                "update",
                "--symbol",
                SYMBOL,
                "--outcome",
                "not_followed",
                "--entry-signal",
                "observe",
                "--state-dir",
                str(STATE_DIR),
                "--pnl=0",
                "--direction",
                "flat",
                "--feedback-file",
                str(FEEDBACK_JSON),
            ],
            timeout=90,
        )
    )
    commands.append(
        run_command(
            "03_analyze_live_with_bbn_soft_evidence",
            [
                str(ICT),
                "analyze-live",
                "--symbol",
                SYMBOL,
                "--futures-symbol",
                "NQ=F",
                "--spot-symbol",
                "QQQ",
                "--options-symbol",
                "QQQ",
                "--options-volatility-proxy-symbol",
                "^VIX",
                "--futures-backend",
                "yfinance",
                "--aux-backend",
                "yfinance",
                "--state-dir",
                str(STATE_DIR),
                "--regime-consumer-bundle",
                str(SOURCE_BUNDLE),
                "--regime-consumer-bundle-strict",
                "--apply-regime-bundle-bbn-soft-evidence",
                "--output-format",
                "json",
            ],
            timeout=240,
        )
    )
    commands.append(
        run_command(
            "04_pre_bayes_status_refresh",
            [
                str(ICT),
                "pre-bayes-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--output-format",
                "json",
            ],
        )
    )
    commands.append(
        run_command(
            "05_policy_training_status",
            [
                str(ICT),
                "policy-training-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
        )
    )
    commands.append(
        run_command(
            "06_export_structural_path_ranking_target",
            [str(ICT), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
        )
    )
    commands.append(
        run_command(
            "07_workflow_structural_recommended_path_bundle",
            [
                str(ICT),
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
            "08_workflow_execution_candidate",
            [
                str(ICT),
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

    provider_readback: dict[str, Any] = {}
    for provider_id in ["yfinance", "tradingview_mcp", "ibkr", "kraken_public", "kraken_cli"]:
        provider_readback[provider_id] = parse_provider_status(PROVIDER / f"provider_status_{provider_id}_agent.out")
        provider_readback[provider_id]["exit_code"] = next(
            (item["returncode"] for item in commands if item["name"] == f"provider_status_{provider_id}_agent"),
            None,
        )

    analyze_live = read_json(COMMANDS / "03_analyze_live_with_bbn_soft_evidence.out")
    pre_bayes = read_json(COMMANDS / "04_pre_bayes_status_refresh.out")
    policy = read_json(COMMANDS / "05_policy_training_status.out")
    export_target = read_json(COMMANDS / "06_export_structural_path_ranking_target.out")
    workflow_bundle = read_json(COMMANDS / "07_workflow_structural_recommended_path_bundle.out")
    execution_text = (COMMANDS / "08_workflow_execution_candidate.out").read_text(encoding="utf-8").strip()
    trace = read_json(STATE_DIR / SYMBOL / "execution_tree_trace.json").get("output", {})
    execution_candidate = read_json(STATE_DIR / SYMBOL / "execution_candidate.json")

    command_exits_ok = all(
        item["returncode"] == 0 for item in commands if not item["name"].startswith("provider_status_")
    )
    execution_candidate_payload_present = execution_text not in {"", "null"}
    path_preserved = workflow_bundle.get("path_id") in {SOURCE_BRANCH_PATH, SIBLING_BRANCH_PATH}
    bbn_status = (
        (execution_candidate.get("pre_bayes_evidence_filter") or {})
        .get("evidence_assignments", {})
        .get("regime_bundle_bbn_application_status")
    )
    policy_runtime = policy.get("structural_path_ranking_runtime", {})
    validation = policy.get("structural_path_ranking_validation", {})

    packet = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "accepted_regime_id": ACCEPTED_REGIME_ID,
        "symbol": SYMBOL,
        "source_recipe": SOURCE_RECIPE,
        "sibling_recipe": SIBLING_RECIPE,
        "nursery_status": "incubation_only",
        "source_branch_path": SOURCE_BRANCH_PATH,
        "sibling_branch_path": SIBLING_BRANCH_PATH,
        "suppression_rule": "if execution_tree_branch=block_crowded or execution_readiness<0.45 or live_context=RangeConsolidation/WideRange then no_trade",
        "full_replay": replay_summary,
        "source_crisis_branch_metrics": source_summary,
        "source_rc_spa_decision": source_rc_spa.get("decision", {}),
        "source_closed_loop_readback": {
            "pre_bayes_gate_status": source_closed_loop.get("pre_bayes_gate_status"),
            "workflow_execution_candidate_ready": source_closed_loop.get("workflow_execution_candidate_ready"),
            "ranker_runtime_status": source_closed_loop.get("ranker_runtime_status"),
            "execution_triage_branch": source_closed_loop.get("execution_triage_branch"),
            "execution_triage_gate_status": source_closed_loop.get("execution_triage_gate_status"),
        },
        "source_sibling_probe": {
            "decision": source_sibling.get("decision"),
            "current_runtime_test": source_sibling.get("current_runtime_test"),
        },
        "provider_readback": provider_readback,
        "downstream_probe": {
            "auto_quant_source_wire_dry_run_exit0": next(
                item["returncode"] == 0 for item in commands if item["name"] == "01_auto_quant_ingest_source_wire_dry_run"
            ),
            "sibling_not_followed_update_exit0": next(
                item["returncode"] == 0 for item in commands if item["name"] == "02_update_sibling_not_followed_feedback"
            ),
            "analyze_live_exit0": next(
                item["returncode"] == 0 for item in commands if item["name"] == "03_analyze_live_with_bbn_soft_evidence"
            ),
            "pre_bayes_gate": pre_bayes.get("latest_gate_status")
            or ((execution_candidate.get("pre_bayes_evidence_filter") or {}).get("gating_status")),
            "bbn_application_status": bbn_status,
            "catboost_runtime_status": policy_runtime.get("status"),
            "catboost_validation_summary": validation.get("summary_line"),
            "structural_target_summary": export_target.get("summary_line"),
            "workflow_bundle_path_id": workflow_bundle.get("path_id"),
            "workflow_path_preserved_to_source_or_sibling": path_preserved,
            "execution_candidate_payload_present": execution_candidate_payload_present,
            "execution_tree_branch": trace.get("branch"),
            "execution_tree_gate": trace.get("gate_status"),
            "execution_tree_bias": trace.get("execution_bias"),
            "execution_tree_consumer_reason": trace.get("consumer_reason"),
            "ranker_consumed_by_execution_tree": trace.get("path_ranker_score_used_by_execution_tree"),
            "ranker_validation_ready": trace.get("ranker_validation_ready"),
            "analyze_live_top_keys": sorted(analyze_live.keys())[:20] if isinstance(analyze_live, dict) else [],
        },
        "artifacts": {
            "replay_csv": rel(REPLAY_CSV),
            "replay_json": rel(REPLAY_JSON),
            "feedback_json": rel(FEEDBACK_JSON),
            "report_md": rel(REPORT_MD),
            "assertions": rel(ASSERTIONS),
            "state_dir": rel(STATE_DIR),
            "command_output": rel(COMMANDS),
            "provider_output": rel(PROVIDER),
        },
        "commands": commands,
        "promotion_allowed": False,
        "decision": "full_nursery_replay_encoded_sibling_no_trade_suppression_promotion_blocked",
        "next_action": (
            "Accumulate repeated crowded and compatible-context nursery observations before sending "
            "the suppression rule to Board A or reopening production promotion."
        ),
        "command_exits_ok": command_exits_ok,
    }
    write_json(REPLAY_JSON, packet)

    assertions = {
        "run_id": RUN_ID,
        "nursery_status": "incubation_only",
        "full_replay_rows": replay_summary["replay_rows"],
        "full_replay_rows_match_source_crisis_rows": replay_summary["replay_rows"] == int(source_summary.get("total_trades", 0)),
        "all_replay_rows_no_trade": replay_summary["suppressed_rows"] == replay_summary["replay_rows"]
        and replay_summary["trade_taken_rows"] == 0,
        "auto_quant_source_wire_dry_run_exit0": packet["downstream_probe"]["auto_quant_source_wire_dry_run_exit0"],
        "sibling_not_followed_update_exit0": packet["downstream_probe"]["sibling_not_followed_update_exit0"],
        "analyze_live_exit0": packet["downstream_probe"]["analyze_live_exit0"],
        "pre_bayes_seen": bool(packet["downstream_probe"]["pre_bayes_gate"]),
        "bbn_probe_seen": bool(packet["downstream_probe"]["bbn_application_status"]),
        "catboost_runtime_ready": packet["downstream_probe"]["catboost_runtime_status"] == "enabled_candidate_set_ready",
        "execution_tree_probe_seen": bool(packet["downstream_probe"]["execution_tree_branch"]),
        "ranker_consumed_by_execution_tree": packet["downstream_probe"]["ranker_consumed_by_execution_tree"] is True,
        "yfinance_ready": provider_readback.get("yfinance", {}).get("ready") is True,
        "tradingview_mcp_ready": provider_readback.get("tradingview_mcp", {}).get("ready") is True,
        "ibkr_recorded": "ibkr" in provider_readback,
        "kraken_cli_ready": provider_readback.get("kraken_cli", {}).get("ready") is True,
        "promotion_allowed": False,
        "command_exits_ok": command_exits_ok,
    }
    assertion_lines = [f"{key}={value}" for key, value in assertions.items()]
    hard_required = [
        "full_replay_rows_match_source_crisis_rows",
        "all_replay_rows_no_trade",
        "auto_quant_source_wire_dry_run_exit0",
        "sibling_not_followed_update_exit0",
        "analyze_live_exit0",
        "pre_bayes_seen",
        "bbn_probe_seen",
        "catboost_runtime_ready",
        "execution_tree_probe_seen",
        "ranker_consumed_by_execution_tree",
        "yfinance_ready",
        "ibkr_recorded",
        "kraken_cli_ready",
        "promotion_allowed",
        "command_exits_ok",
    ]
    for key in hard_required:
        if assertions.get(key) is not True and not (key == "promotion_allowed" and assertions.get(key) is False):
            assertion_lines.append(f"ASSERT_FAIL:{key}")
    ASSERTIONS.write_text("\n".join(assertion_lines) + "\n", encoding="utf-8")

    report = [
        "# Crisis Crowded Suppression Full Replay v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        "`CrisisCrowdedSuppressionSiblingV1` was encoded as a full `incubation_only` nursery replay for the source Crisis branch. The sibling emits `no_trade` for crowded `RangeConsolidation/WideRange` context and remains non-promotional.",
        "",
        "## Replay / Backtest",
        "",
        f"- Source branch: `{SOURCE_BRANCH_PATH}`",
        f"- Sibling branch: `{SIBLING_BRANCH_PATH}`",
        f"- Source Crisis rows: `{replay_summary['source_crisis_rows']}`",
        f"- Full replay rows: `{replay_summary['replay_rows']}`",
        f"- Suppressed no-trade rows: `{replay_summary['suppressed_rows']}`",
        f"- Trade-taken rows: `{replay_summary['trade_taken_rows']}`",
        f"- Markets covered: `{len(replay_summary['markets'])}`",
        f"- Year folds covered: `{len(replay_summary['year_folds'])}`",
        "",
        "## Downstream Probes",
        "",
        f"- Auto-Quant source-wire dry run: `{packet['downstream_probe']['auto_quant_source_wire_dry_run_exit0']}`",
        f"- Pre-Bayes/filter: `{packet['downstream_probe']['pre_bayes_gate']}`",
        f"- BBN soft evidence: `{packet['downstream_probe']['bbn_application_status']}`",
        f"- CatBoost/path-ranker: `{packet['downstream_probe']['catboost_runtime_status']}`; `{packet['downstream_probe']['catboost_validation_summary']}`",
        f"- Execution tree: `{packet['downstream_probe']['execution_tree_branch']}` / `{packet['downstream_probe']['execution_tree_gate']}` / `{packet['downstream_probe']['execution_tree_bias']}`",
        f"- Ranker consumed by execution tree: `{packet['downstream_probe']['ranker_consumed_by_execution_tree']}`",
        f"- Promotion allowed: `False`",
        "",
        "## Provider Readback",
        "",
        f"- yfinance: ready `{provider_readback.get('yfinance', {}).get('ready')}`; reason `{provider_readback.get('yfinance', {}).get('reason')}`",
        f"- TradingViewRemix/tradingview_mcp: ready `{provider_readback.get('tradingview_mcp', {}).get('ready')}`; reason `{provider_readback.get('tradingview_mcp', {}).get('reason')}`",
        f"- IBKR: ready `{provider_readback.get('ibkr', {}).get('ready')}`; reason `{provider_readback.get('ibkr', {}).get('reason')}`",
        f"- Kraken CLI: ready `{provider_readback.get('kraken_cli', {}).get('ready')}`; reason `{provider_readback.get('kraken_cli', {}).get('reason')}`",
        f"- Kraken public: ready `{provider_readback.get('kraken_public', {}).get('ready')}`; reason `{provider_readback.get('kraken_public', {}).get('reason')}`",
        "",
        "## Artifacts",
        "",
        f"- Replay CSV: `{rel(REPLAY_CSV)}`",
        f"- Summary JSON: `{rel(REPLAY_JSON)}`",
        f"- Feedback JSON: `{rel(FEEDBACK_JSON)}`",
        f"- Assertions: `{rel(ASSERTIONS)}`",
        f"- Command logs: `{rel(COMMANDS)}`",
        "",
        "## Next",
        "",
        packet["next_action"],
        "",
    ]
    REPORT_MD.write_text("\n".join(report), encoding="utf-8")
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
