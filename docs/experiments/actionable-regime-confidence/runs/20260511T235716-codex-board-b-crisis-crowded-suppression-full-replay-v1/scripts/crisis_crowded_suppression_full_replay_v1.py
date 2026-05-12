#!/usr/bin/env python3
"""Encode the Crisis crowded-suppression sibling leaf into a full nursery replay."""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T235716+0800-codex-board-b-crisis-crowded-suppression-full-replay-v1"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
RECIPE_ID = "SourceRootStopCarryLongHorizonV1"
ACCEPTED_REGIME_ID = "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation"
SOURCE_BRANCH_PATH = (
    "Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> "
    "SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12"
)
SIBLING_BRANCH_PATH = (
    "Crisis -> CrisisReliefCarry -> BlockCrowdedSuppression -> "
    "SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1"
)
SIBLING_BRANCH_ID = "B2R_CRISIS_CROWDED_SUPPRESSION_FULL_REPLAY_V1"
SUPPRESSION_RULE = (
    "if execution_tree_branch=block_crowded or execution_readiness<0.45 "
    "or live_context=RangeConsolidation/WideRange then no_trade"
)

HERE = Path(__file__).resolve().parent
RUN_ROOT = HERE.parent
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
ICT = REPO_ROOT / "target/debug/ict-engine"
TRAINER = REPO_ROOT / "scripts/auto_quant_external/pandas_path_ranker_trainer.py"

SOURCE_220646 = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
)
SOURCE_SELECTED_ROWS = (
    SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_selected_rows_v1.csv"
)
SOURCE_SUMMARY_ROWS = (
    SOURCE_220646 / "branch-rc-spa/source_root_stop_carry_longhorizon_branch_summary_v1.csv"
)
SOURCE_STATE = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T234658-codex-board-b-b2r-block-crowded-nursery-feedback-v1/"
    "state_b2r_block_crowded_nursery_v1"
)
SIBLING_PACKET = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T234938-codex-board-b-crisis-crowded-suppression-sibling-v1/"
    "crisis-crowded-suppression-sibling/crisis_crowded_suppression_sibling_v1.json"
)
COMPATIBLE_CONTEXT = (
    REPO_ROOT
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T234918-codex-board-b-220646-compatible-live-context-readback-v1/"
    "compatible-live-context-readback-v1/compatible_live_context_readback_v1.json"
)

OUT_DIR = RUN_ROOT / "crisis-crowded-suppression-full-replay"
LOG_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"
STATE_DIR = RUN_ROOT / "state_crisis_crowded_suppression_full_replay_v1"
CATBOOST_DIR = OUT_DIR / "catboost/path_ranker_model_py313"
SCORES_DIR = OUT_DIR / "catboost/scores_py313"
REPLAY_ROWS = OUT_DIR / "crisis_crowded_suppression_full_replay_rows_v1.csv"
REPLAY_SUMMARY_CSV = OUT_DIR / "crisis_crowded_suppression_full_replay_summary_v1.csv"
FEEDBACK_FILE = OUT_DIR / "crisis_crowded_suppression_no_trade_feedback_v1.json"
SUMMARY_JSON = OUT_DIR / "crisis_crowded_suppression_full_replay_v1.json"
SUMMARY_MD = OUT_DIR / "crisis_crowded_suppression_full_replay_v1.md"
ASSERTIONS = CHECK_DIR / "crisis_crowded_suppression_full_replay_v1_assertions.out"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(name: str, args: list[str], timeout_seconds: int = 360) -> dict[str, Any]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            args,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        returncode = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout_seconds}s\n"
        returncode = 124
        timed_out = True
    out_path = LOG_DIR / f"{name}.out"
    err_path = LOG_DIR / f"{name}.err"
    exit_path = LOG_DIR / f"{name}.exit"
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{returncode}\n", encoding="utf-8")
    parsed = None
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout_path": rel(out_path),
        "stderr_path": rel(err_path),
        "exit_path": rel(exit_path),
        "parsed": parsed,
    }


def parse_float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, "") or default)
    except ValueError:
        return default


def crisis_source_rows() -> list[dict[str, str]]:
    rows = read_csv(SOURCE_SELECTED_ROWS)
    return [
        row
        for row in rows
        if row.get("parent_regime_root") == "Crisis"
        and row.get("regime_profit_branch_path") == SOURCE_BRANCH_PATH
    ]


def crisis_summary_row() -> dict[str, str]:
    for row in read_csv(SOURCE_SUMMARY_ROWS):
        if row.get("parent_regime_root") == "Crisis" and row.get("regime_profit_branch_path") == SOURCE_BRANCH_PATH:
            return row
    raise RuntimeError("missing Crisis source branch summary row")


def build_full_replay_rows(
    source_rows: list[dict[str, str]],
    sibling_packet: dict[str, Any],
    compatible_context: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in source_rows:
        replay = dict(row)
        replay["source_regime_profit_branch_path"] = row["regime_profit_branch_path"]
        replay["regime_profit_branch_path"] = SIBLING_BRANCH_PATH
        replay["variant_id"] = "crisis_carry_no_trade_when_block_crowded_v1"
        replay["sub_regime_tags"] = "CrisisReliefCarry"
        replay["sub_sub_regime_or_profit_factor"] = "BlockCrowdedSuppression"
        replay["profit_factor_family"] = "crisis_crowded_suppression"
        replay["profit_factor_leaf"] = (
            "SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1"
        )
        replay["allowed_action"] = "carry_replay_when_not_block_crowded_nursery_only"
        replay["suppression_rule"] = SUPPRESSION_RULE
        replay["sibling_branch_id"] = SIBLING_BRANCH_ID
        replay["nursery_status"] = "incubation_only"
        replay["sibling_replay_action"] = "carry_replay_if_not_block_crowded"
        replay["sibling_context_bucket"] = "historical_source_row_without_live_crowding_label"
        replay["sibling_counted_trade"] = "true"
        replay["sibling_guard_reason"] = ""
        replay["sibling_profit_ratio_net"] = row.get("profit_ratio_net", "")
        rows.append(replay)

    if source_rows:
        guard = dict(source_rows[0])
    else:
        guard = {key: "" for key in read_csv(SOURCE_SELECTED_ROWS)[0].keys()}
    downstream = compatible_context.get("downstream_readback", {})
    guard["source_regime_profit_branch_path"] = SOURCE_BRANCH_PATH
    guard["regime_profit_branch_path"] = SIBLING_BRANCH_PATH
    guard["variant_id"] = "crisis_carry_no_trade_when_block_crowded_v1"
    guard["market"] = "LIVE_CONTEXT"
    guard["timeframe"] = "runtime_probe"
    guard["trade_id"] = f"{SIBLING_BRANCH_ID}:live_guard:{sibling_packet['run_id']}"
    guard["sub_regime_tags"] = "CrisisReliefCarry"
    guard["sub_sub_regime_or_profit_factor"] = "BlockCrowdedSuppression"
    guard["profit_factor_family"] = "crisis_crowded_suppression"
    guard["profit_factor_leaf"] = (
        "SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1"
    )
    guard["allowed_action"] = "no_trade_when_block_crowded_or_wide_range"
    guard["suppression_rule"] = SUPPRESSION_RULE
    guard["direction"] = "flat"
    guard["direction_sign"] = "0"
    guard["entry_close"] = ""
    guard["exit_close"] = ""
    guard["exit_reason"] = "suppression_no_trade_block_crowded_range_wide"
    guard["gross_return"] = "0.0"
    guard["profit_ratio_net"] = "0.0"
    guard["year_fold"] = "live_context"
    guard["source_panel"] = "ict_engine_live_runtime_probe"
    guard["sibling_branch_id"] = SIBLING_BRANCH_ID
    guard["nursery_status"] = "incubation_only"
    guard["sibling_replay_action"] = "no_trade"
    guard["sibling_context_bucket"] = downstream.get("market_state") or "RangeConsolidation/WideRange"
    guard["sibling_counted_trade"] = "false"
    guard["sibling_guard_reason"] = downstream.get("workflow_blocker") or "block_crowded_or_wide_range"
    guard["sibling_profit_ratio_net"] = "0.0"
    rows.append(guard)
    return rows


def write_replay_artifacts(
    replay_rows: list[dict[str, Any]],
    source_rows: list[dict[str, str]],
    summary_row: dict[str, str],
    sibling_packet: dict[str, Any],
    compatible_context: dict[str, Any],
) -> dict[str, Any]:
    base_fields = list(read_csv(SOURCE_SELECTED_ROWS)[0].keys())
    extra_fields = [
        "source_regime_profit_branch_path",
        "sibling_branch_id",
        "nursery_status",
        "sibling_replay_action",
        "sibling_context_bucket",
        "sibling_counted_trade",
        "sibling_guard_reason",
        "sibling_profit_ratio_net",
    ]
    write_csv(REPLAY_ROWS, replay_rows, base_fields + extra_fields)

    trade_rows = [row for row in replay_rows if row["sibling_counted_trade"] == "true"]
    no_trade_rows = [row for row in replay_rows if row["sibling_counted_trade"] == "false"]
    fold_counts = Counter(row.get("year_fold") for row in trade_rows)
    fold_returns = Counter()
    for row in trade_rows:
        fold_returns[row.get("year_fold")] += parse_float(row, "profit_ratio_net")
    positive_folds = sum(1 for value in fold_returns.values() if value > 0.0)
    min_fold_trades = min(fold_counts.values()) if fold_counts else 0
    wins = sum(1 for row in trade_rows if parse_float(row, "profit_ratio_net") > 0.0)
    mean_net = sum(parse_float(row, "profit_ratio_net") for row in trade_rows) / max(len(trade_rows), 1)
    win_rate = wins / max(len(trade_rows), 1)
    fold_positive_rate = positive_folds / max(len(fold_counts), 1)
    downstream = compatible_context.get("downstream_readback", {})
    sibling_runtime = sibling_packet.get("current_runtime_test", {})
    replay_summary = {
        "schema_version": "board-b-crisis-crowded-suppression-full-replay/v1",
        "run_id": RUN_ID,
        "accepted_regime_id": ACCEPTED_REGIME_ID,
        "source_recipe": RECIPE_ID,
        "source_branch_path": SOURCE_BRANCH_PATH,
        "sibling_branch_id": SIBLING_BRANCH_ID,
        "sibling_branch_path": SIBLING_BRANCH_PATH,
        "suppression_rule": SUPPRESSION_RULE,
        "nursery_status": "incubation_only",
        "source_trade_rows": len(source_rows),
        "replay_rows_total": len(replay_rows),
        "replay_counted_trade_rows": len(trade_rows),
        "no_trade_guard_rows": len(no_trade_rows),
        "folds": sorted(k for k in fold_counts.keys() if k),
        "test_folds": len(fold_counts),
        "min_trades_per_test_fold": min_fold_trades,
        "fold_positive_rate": fold_positive_rate,
        "win_rate": win_rate,
        "mean_profit_ratio_net": mean_net,
        "source_crisis_rc_spa": parse_float(summary_row, "rc_spa"),
        "source_crisis_lcb": parse_float(summary_row, "bootstrap_edge_lcb_5pct"),
        "source_crisis_pbo": parse_float(summary_row, "pbo"),
        "source_crisis_dsr": parse_float(summary_row, "dsr"),
        "source_crisis_hard_gate_result": summary_row.get("hard_gate_result"),
        "sibling_runtime_test": {
            "execution_tree_branch": sibling_runtime.get("execution_tree_branch"),
            "execution_tree_gate_status": sibling_runtime.get("execution_tree_gate_status"),
            "consumer_reason": sibling_runtime.get("execution_tree_consumer_reason"),
            "suppression_action_result": sibling_runtime.get("suppression_action_result"),
        },
        "compatible_live_context": {
            "execution_tree_branch": downstream.get("execution_tree_branch"),
            "execution_tree_gate_status": downstream.get("execution_tree_gate_status"),
            "execution_readiness": downstream.get("execution_readiness"),
            "market_state": downstream.get("market_state"),
            "workflow_blocker": downstream.get("workflow_blocker"),
            "compatible_context_observed": compatible_context.get("decision", {}).get("compatible_context_observed"),
        },
        "decision": "full_nursery_replay_rows_encoded_and_guarded_no_trade_context_added",
        "promotion_allowed": False,
    }
    write_csv(
        REPLAY_SUMMARY_CSV,
        [replay_summary],
        [
            "run_id",
            "sibling_branch_id",
            "nursery_status",
            "source_trade_rows",
            "replay_rows_total",
            "replay_counted_trade_rows",
            "no_trade_guard_rows",
            "test_folds",
            "min_trades_per_test_fold",
            "fold_positive_rate",
            "win_rate",
            "mean_profit_ratio_net",
            "source_crisis_rc_spa",
            "source_crisis_lcb",
            "source_crisis_pbo",
            "source_crisis_dsr",
            "source_crisis_hard_gate_result",
            "promotion_allowed",
        ],
    )
    return replay_summary


def write_sibling_feedback(compatible_context: dict[str, Any]) -> dict[str, Any]:
    downstream = compatible_context.get("downstream_readback", {})
    selected_probability = float(
        downstream.get("execution_score")
        or downstream.get("pre_bayes_quality_score")
        or 0.56
    )
    feedback = {
        "protocol_version": "structural-feedback-v1",
        "recommendation_id": (
            f"structural-feedback:{SYMBOL}:crisis-crowded-suppression-full-replay-v1:"
            f"path:{SIBLING_BRANCH_PATH}"
        ),
        "recommended_at": now_utc(),
        "symbol": SYMBOL,
        "node_id": f"{SYMBOL}:Crisis",
        "branch_id": f"{SYMBOL}:CrisisReliefCarry:BlockCrowdedSuppression",
        "scenario_id": "CrisisReliefCarry",
        "path_id": SIBLING_BRANCH_PATH,
        "candidate_set_id": f"structural-feedback:{SYMBOL}:crisis-crowded-suppression-full-replay-v1",
        "candidate_set_size": 1,
        "selected_path_probability": selected_probability,
        "direction": "Observe",
        "entry_style": "no_trade_guard",
        "selected_entry_quality": "medium",
        "selected_entry_quality_probability": selected_probability,
        "pre_bayes_gate_status": downstream.get("pre_bayes_gate") or "pass_neutralized",
        "path_posterior": selected_probability,
        "bbn_support_score": selected_probability,
        "followed_path": True,
        "realized_outcome": "abandoned",
        "realized_pnl": 0.0,
        "exit_reason": "suppression_no_trade_block_crowded_range_wide",
        "notes": (
            "B2R nursery no-trade guard: sibling Crisis leaf suppresses crowded "
            "RangeConsolidation/WideRange contexts; record as neutral abandoned guard, "
            "not as promotion-grade profitability."
        ),
    }
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    FEEDBACK_FILE.write_text(json.dumps(feedback, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return feedback


def export_target_paths(export: dict[str, Any], history: bool = False) -> list[dict[str, Any]]:
    key = "history_jsonl_path" if history else "jsonl_path"
    raw_path = export.get(key) or export.get("jsonl_path")
    if not raw_path:
        return []
    path = Path(str(raw_path))
    if not path.exists():
        path = REPO_ROOT / str(raw_path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def combine_score_files(paths: list[Path], output: Path) -> int:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for path in paths:
        if not path.exists():
            continue
        for row in read_csv(path):
            key = (row.get("candidate_set_id", ""), row.get("path_id", ""))
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    if not rows:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "candidate_set_id,path_id,raw_path_score,score_model_family,score_source_kind,score_model_artifact_uri,score_generator\n",
            encoding="utf-8",
        )
        return 0
    write_csv(output, rows, list(rows[0].keys()))
    return len(rows)


def parsed(commands: list[dict[str, Any]], name: str) -> Any:
    for command in commands:
        if command["name"] == name:
            return command.get("parsed")
    return None


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    if STATE_DIR.exists():
        shutil.rmtree(STATE_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    SCORES_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE_STATE, STATE_DIR)

    sibling_packet = load_json(SIBLING_PACKET)
    compatible_context = load_json(COMPATIBLE_CONTEXT)
    source_rows = crisis_source_rows()
    summary_row = crisis_summary_row()
    replay_rows = build_full_replay_rows(source_rows, sibling_packet, compatible_context)
    replay_summary = write_replay_artifacts(replay_rows, source_rows, summary_row, sibling_packet, compatible_context)
    feedback = write_sibling_feedback(compatible_context)

    commands: list[dict[str, Any]] = []
    commands.append(run_command("00_provider_status_agent", [str(ICT), "provider-status", "--agent"]))
    commands.append(
        run_command(
            "00b_auto_quant_status_json",
            [str(ICT), "auto-quant-status", "--state-dir", str(STATE_DIR / "auto-quant"), "--output-format", "json"],
        )
    )
    commands.append(
        run_command(
            "01_update_sibling_no_trade_guard",
            [
                str(ICT),
                "update",
                "--symbol",
                SYMBOL,
                "--outcome",
                "abandoned",
                "--entry-signal",
                "medium",
                "--state-dir",
                str(STATE_DIR),
                "--pnl=0.0",
                "--feedback-file",
                str(FEEDBACK_FILE),
            ],
        )
    )
    commands.append(
        run_command(
            "02_export_structural_target_before_catboost",
            [str(ICT), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
        )
    )
    target_csv = STATE_DIR / SYMBOL / "policy_training/structural_path_ranking_target.csv"
    history_csv = STATE_DIR / SYMBOL / "policy_training/structural_path_ranking_target_history.csv"
    commands.append(
        run_command(
            "03_train_catboost_path_ranker_on_history",
            [
                "python3.13",
                str(TRAINER),
                "--target-csv",
                str(history_csv),
                "--output-dir",
                str(CATBOOST_DIR),
                "--model-family",
                "catboost",
            ],
        )
    )
    current_scores = SCORES_DIR / "current_scores_py313.csv"
    history_scores = SCORES_DIR / "history_scores_py313.csv"
    combined_scores = SCORES_DIR / "combined_scores_py313.csv"
    commands.append(
        run_command(
            "04_apply_catboost_to_current_target",
            [
                "python3.13",
                str(TRAINER),
                "--apply",
                "--model-dir",
                str(CATBOOST_DIR),
                "--target-csv",
                str(target_csv),
                "--output-scores",
                str(current_scores),
            ],
        )
    )
    commands.append(
        run_command(
            "05_apply_catboost_to_history_target",
            [
                "python3.13",
                str(TRAINER),
                "--apply",
                "--model-dir",
                str(CATBOOST_DIR),
                "--target-csv",
                str(history_csv),
                "--output-scores",
                str(history_scores),
            ],
        )
    )
    combined_score_rows = combine_score_files([current_scores, history_scores], combined_scores)
    commands.append(
        run_command(
            "06_apply_catboost_external_scores",
            [
                str(ICT),
                "apply-structural-path-ranking-external-scores",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--scores-file",
                str(combined_scores),
            ],
        )
    )
    trainer_artifact = CATBOOST_DIR / "trainer_artifact.json"
    trainer_payload = load_json(trainer_artifact) if trainer_artifact.exists() else {}
    trained_rows = str(int(trainer_payload.get("trained_rows") or len(read_csv(history_csv))))
    calibration_rows = str(int(trainer_payload.get("calibration_rows") or len(read_csv(history_csv))))
    commands.append(
        run_command(
            "07_register_catboost_path_ranker_artifact",
            [
                str(ICT),
                "register-structural-path-ranking-trainer-artifact",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--artifact-uri",
                str(trainer_artifact),
                "--model-family",
                "catboost",
                "--score-column",
                "raw_path_score",
                "--trained-rows",
                trained_rows,
                "--calibration-rows",
                calibration_rows,
            ],
        )
    )
    commands.append(
        run_command(
            "08_enable_structural_path_ranking_runtime",
            [
                str(ICT),
                "enable-structural-path-ranking-runtime",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--reuse-mode",
                "prefer_history",
            ],
        )
    )
    commands.append(
        run_command(
            "09_export_structural_target_after_catboost",
            [str(ICT), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
        )
    )
    commands.append(
        run_command(
            "10_workflow_structural_bundle_agent",
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
            "11_workflow_execution_candidate_agent",
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
    commands.append(
        run_command(
            "12_workflow_status_json",
            [str(ICT), "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
        )
    )
    commands.append(
        run_command(
            "13_policy_training_status_json",
            [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
        )
    )
    commands.append(
        run_command(
            "14_pre_bayes_status_json",
            [str(ICT), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"],
        )
    )

    export_after = parsed(commands, "09_export_structural_target_after_catboost") or {}
    current_rows = export_target_paths(export_after, history=False)
    history_rows = export_target_paths(export_after, history=True)
    current_path_ids = {str(row.get("path_id")) for row in current_rows}
    history_path_ids = {str(row.get("path_id")) for row in history_rows}
    policy = parsed(commands, "13_policy_training_status_json") or {}
    workflow_bundle = parsed(commands, "10_workflow_structural_bundle_agent") or {}
    workflow_candidate = parsed(commands, "11_workflow_execution_candidate_agent") or {}
    workflow_status = parsed(commands, "12_workflow_status_json") or {}
    pre_bayes = parsed(commands, "14_pre_bayes_status_json") or {}
    provider = parsed(commands, "00_provider_status_agent") or {}
    auto_quant = parsed(commands, "00b_auto_quant_status_json") or {}

    target = policy.get("structural_path_ranking_target", {})
    validation = policy.get("structural_path_ranking_validation", {})
    observation_validation = validation.get("feedback_observation_validation", {})
    runtime = policy.get("structural_path_ranking_runtime", {})
    provider_text = (REPO_ROOT / commands[0]["stdout_path"]).read_text(encoding="utf-8")
    command_failures = [cmd for cmd in commands if cmd["returncode"] != 0]
    sibling_in_current = SIBLING_BRANCH_PATH in current_path_ids
    sibling_in_history = SIBLING_BRANCH_PATH in history_path_ids
    workflow_path_id = workflow_bundle.get("path_id") if isinstance(workflow_bundle, dict) else None
    sibling_selected = workflow_path_id == SIBLING_BRANCH_PATH
    execution_candidate_ready = (
        isinstance(workflow_candidate, dict)
        and (
            workflow_candidate.get("candidate_status") == "ready"
            or workflow_candidate.get("actionable") is True
            or workflow_candidate.get("ready") is True
        )
    )
    pre_bayes_gate = (
        pre_bayes.get("latest_gate_status")
        or pre_bayes.get("gating_status")
        or pre_bayes.get("pre_bayes_gate_status")
        or pre_bayes.get("status")
    )
    bbn_network = STATE_DIR / SYMBOL / "bbn_network.json"
    bbn_applied = bbn_network.exists() and commands[2]["returncode"] == 0
    promotion_allowed = False

    summary = {
        "schema_version": "board-b-crisis-crowded-suppression-full-replay/v1",
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "accepted_regime_id": ACCEPTED_REGIME_ID,
        "recipe_id": RECIPE_ID,
        "sibling_branch_id": SIBLING_BRANCH_ID,
        "sibling_branch_path": SIBLING_BRANCH_PATH,
        "source_branch_path": SOURCE_BRANCH_PATH,
        "state_dir": rel(STATE_DIR),
        "replay_summary": replay_summary,
        "feedback_file": rel(FEEDBACK_FILE),
        "catboost": {
            "trainer_model_dir": rel(CATBOOST_DIR),
            "trainer_artifact": rel(trainer_artifact) if trainer_artifact.exists() else None,
            "combined_scores": rel(combined_scores),
            "combined_score_rows": combined_score_rows,
            "sibling_in_current_target": sibling_in_current,
            "sibling_in_history_target": sibling_in_history,
            "trainer_artifact_ready": bool(target.get("trainer_artifact_ready")),
            "runtime_ready": bool(target.get("runtime_selection_ready") or runtime.get("ready")),
            "production_validation_ready": validation.get("production_validation_ready"),
            "production_validation_rows": validation.get("production_validation_rows"),
            "observation_validation_ready": observation_validation.get("ready"),
            "observation_validation_rows": observation_validation.get("mature_observations")
            or observation_validation.get("total_observations"),
        },
        "downstream": {
            "pre_bayes_gate": pre_bayes_gate,
            "bbn_network_present": bbn_network.exists(),
            "bbn_update_applied": bbn_applied,
            "workflow_bundle_path_id": workflow_path_id,
            "workflow_bundle_selected_sibling": sibling_selected,
            "workflow_execution_candidate_ready": execution_candidate_ready,
            "workflow_blocker": workflow_status.get("recommended_next_step", {}).get("blocked_reason")
            if isinstance(workflow_status.get("recommended_next_step"), dict)
            else None,
        },
        "provider_readback": {
            "summary_line": provider.get("summary_line") if isinstance(provider, dict) else None,
            "yfinance_ready_seen": "yfinance" in provider_text and '"ready": true' in provider_text,
            "tradingview_mcp_unhealthy_seen": "tradingview_mcp" in provider_text
            and "configured_runtime_unhealthy" in provider_text,
            "ibkr_recorded_seen": "ibkr" in provider_text,
            "kraken_cli_ready_seen": "kraken_cli" in provider_text and '"ready": true' in provider_text,
        },
        "auto_quant_readback": {
            "status": auto_quant.get("status") if isinstance(auto_quant, dict) else None,
            "summary_line": auto_quant.get("summary_line") if isinstance(auto_quant, dict) else None,
        },
        "commands": [{key: value for key, value in cmd.items() if key != "parsed"} for cmd in commands],
        "command_failures": len(command_failures),
        "promotion_allowed": promotion_allowed,
        "decision": (
            "nursery_feedback: full replay rows and downstream probes completed; "
            "sibling no-trade guard reached structural target/history but remains non-promotional"
        ),
        "next_action": (
            "Keep this as B2R nursery feedback. Require repeated compatible-context and crowded-context "
            "observations before changing production Board B promotion logic."
        ),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_MD.write_text(
        "\n".join(
            [
                "# Crisis Crowded Suppression Full Replay v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                "## Scope",
                "",
                "This run encodes `CrisisCrowdedSuppressionSiblingV1` into full B2R nursery replay rows and reruns the cheap downstream chain on isolated state. It is not promotion evidence.",
                "",
                "## Replay",
                "",
                f"- Source branch: `{SOURCE_BRANCH_PATH}`",
                f"- Sibling branch: `{SIBLING_BRANCH_PATH}`",
                f"- Replay counted trade rows: `{replay_summary['replay_counted_trade_rows']}`",
                f"- No-trade guard rows: `{replay_summary['no_trade_guard_rows']}`",
                f"- Test folds: `{replay_summary['test_folds']}`; min fold trades `{replay_summary['min_trades_per_test_fold']}`",
                f"- Source Crisis RC-SPA: `{replay_summary['source_crisis_rc_spa']}`",
                f"- Suppression rule: `{SUPPRESSION_RULE}`",
                "",
                "## Downstream",
                "",
                f"- BBN update applied: `{bbn_applied}`",
                f"- Pre-Bayes gate: `{pre_bayes_gate}`",
                f"- CatBoost score rows: `{combined_score_rows}`",
                f"- Sibling path in current target: `{sibling_in_current}`",
                f"- Sibling path in history target: `{sibling_in_history}`",
                f"- CatBoost trainer artifact ready: `{summary['catboost']['trainer_artifact_ready']}`",
                f"- Runtime ready: `{summary['catboost']['runtime_ready']}`",
                f"- Production validation rows: `{summary['catboost']['production_validation_rows']}`",
                f"- Observation validation rows: `{summary['catboost']['observation_validation_rows']}`",
                f"- Workflow bundle path: `{workflow_path_id}`",
                f"- Workflow selected sibling: `{sibling_selected}`",
                f"- Execution candidate ready: `{execution_candidate_ready}`",
                "",
                "## Decision",
                "",
                "The sibling no-trade guard is encoded and visible to the downstream path-ranker target/history, but it remains `incubation_only`. Promotion stays blocked because a no-trade guard is not a profitability pass and the workflow still needs repeated context evidence before production logic changes.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{rel(SUMMARY_JSON)}`",
                f"- Replay rows: `{rel(REPLAY_ROWS)}`",
                f"- Replay summary: `{rel(REPLAY_SUMMARY_CSV)}`",
                f"- Feedback file: `{rel(FEEDBACK_FILE)}`",
                f"- Assertions: `{rel(ASSERTIONS)}`",
                f"- Command output: `{rel(LOG_DIR)}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ASSERTIONS.write_text(
        "\n".join(
            [
                f"run_id={RUN_ID}",
                f"command_failures={len(command_failures)}",
                f"source_trade_rows={len(source_rows)}",
                f"replay_counted_trade_rows={replay_summary['replay_counted_trade_rows']}",
                f"no_trade_guard_rows={replay_summary['no_trade_guard_rows']}",
                f"sibling_branch_path_preserved={all(row['regime_profit_branch_path'] == SIBLING_BRANCH_PATH for row in replay_rows)}",
                f"feedback_realized_outcome={feedback['realized_outcome']}",
                f"bbn_update_applied={bbn_applied}",
                f"pre_bayes_gate={pre_bayes_gate}",
                f"catboost_combined_score_rows={combined_score_rows}",
                f"sibling_in_current_target={sibling_in_current}",
                f"sibling_in_history_target={sibling_in_history}",
                f"trainer_artifact_ready={summary['catboost']['trainer_artifact_ready']}",
                f"runtime_ready={summary['catboost']['runtime_ready']}",
                f"production_validation_ready={summary['catboost']['production_validation_ready']}",
                f"observation_validation_ready={summary['catboost']['observation_validation_ready']}",
                f"workflow_bundle_selected_sibling={sibling_selected}",
                f"workflow_execution_candidate_ready={execution_candidate_ready}",
                f"promotion_allowed={promotion_allowed}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"summary": rel(SUMMARY_JSON), "command_failures": len(command_failures)}, sort_keys=True))
    return 0 if len(command_failures) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
