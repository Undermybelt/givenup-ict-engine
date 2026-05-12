#!/usr/bin/env python3
"""Board B B2R nursery seed for the 220646 block_crowded observation.

This is an additive run-local script. It does not mutate the source 220646
run. It converts the execution-tree block into explicit nursery feedback, then
replays the same rooted branch path through ict-engine status surfaces.
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T234604+0800-codex-board-b-b2r-block-crowded-nursery-v1"
SCHEMA_VERSION = "board-b-b2r-block-crowded-nursery/v1"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
RECIPE_ID = "SourceRootStopCarryLongHorizonV1"
ACCEPTED_REGIME_ID = "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation"
EXACT_BRANCH_PATH = (
    "Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> "
    "SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12"
)
EXECUTION_BLOCKER = "block_crowded"
MARKET_STATE = "RangeConsolidation/WideRange"
READINESS = 0.4433
READINESS_FLOOR = 0.45

SCRIPT = Path(__file__).resolve()
RUN_ROOT = SCRIPT.parents[1]
REPO = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
ICT = REPO / "target" / "debug" / "ict-engine"
TRAINER = REPO / "scripts" / "auto_quant_external" / "pandas_path_ranker_trainer.py"

SOURCE_RUN = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T231800-codex-board-b-220646-exact-branch-closed-loop-readback-v4/"
    "exact-branch-closed-loop-readback-v4"
)
SOURCE_220646 = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    "20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
)
SOURCE_READBACK_JSON = SOURCE_RUN / "exact_branch_closed_loop_readback_v4.json"
SOURCE_FEEDBACK_PACKET = SOURCE_RUN / "execution_tree_block_crowded_feedback_packet_v1.md"
SOURCE_SELECTED_WIRE = (
    SOURCE_220646
    / "b5-branch-feedback-calibration-v1/selected_real_trades_wire.jsonl"
)
SOURCE_B5_FEEDBACK_DIR = SOURCE_220646 / "b5-branch-feedback-calibration-v1/feedback"
SOURCE_HISTORY_SCORES = (
    SOURCE_220646
    / "b5-branch-feedback-calibration-v1/catboost/scores_py313/history_scores_py313.csv"
)

OUT = RUN_ROOT / "b2r-block-crowded-nursery-v1"
COMMANDS = OUT / "command-output"
PROVIDER = OUT / "provider"
FEEDBACK = OUT / "feedback"
CATBOOST = OUT / "catboost"
CHECKS = RUN_ROOT / "checks"
STATE_DIR = OUT / "state_b2r_block_crowded_nursery_v1"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def run_command(
    name: str,
    cmd: list[str],
    out_dir: Path = COMMANDS,
    timeout: int | None = 120,
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


def latest_path_score() -> float:
    score = 0.5
    for row in read_csv_rows(SOURCE_HISTORY_SCORES):
        if row.get("path_id") == EXACT_BRANCH_PATH:
            try:
                score = float(row.get("raw_path_score", score))
            except ValueError:
                pass
    return score


def copy_selected_wire() -> Path:
    target = OUT / "selected_real_trades_wire_seed_220646.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE_SELECTED_WIRE, target)
    return target


def source_feedback_paths() -> list[Path]:
    return sorted(SOURCE_B5_FEEDBACK_DIR.glob("feedback_*.json"))


def build_feedback(score: float, source_readback: dict[str, Any]) -> Path:
    generated = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    feedback = {
        "protocol_version": SCHEMA_VERSION,
        "symbol": SYMBOL,
        "recommendation_id": "B2R:block_crowded:220646:crisis_carry_h8_sl048_tp12",
        "recommended_at": source_readback.get("run_id", RUN_ID),
        "node_id": "Crisis",
        "branch_id": EXACT_BRANCH_PATH,
        "scenario_id": "CrisisReliefCarry",
        "path_id": EXACT_BRANCH_PATH,
        "followed_path": True,
        "realized_outcome": "invalidated",
        "realized_pnl": 0.0,
        "direction": "long",
        "entry_style": "crisis_carry_h8_sl048_tp12",
        "exit_reason": "execution_tree_block_crowded",
        "candidate_set_id": "branch-path-candidates:SourceRootStopCarryLongHorizonV1:220646",
        "candidate_set_size": 4,
        "selected_path_probability": score,
        "selected_entry_quality": "medium",
        "selected_entry_quality_probability": score,
        "pre_bayes_gate_status": source_readback.get("pre_bayes_gate_status", "pass_neutralized"),
        "path_posterior": score,
        "bbn_support_score": score,
        "notes": (
            "b2r_block_crowded_nursery_v1; exact Board B regime_profit_branch_path; "
            f"execution_tree={EXECUTION_BLOCKER}; market_state={MARKET_STATE}; "
            f"execution_readiness={READINESS:.4f}<{READINESS_FLOOR:.2f}; "
            "negative execution-admissibility feedback only, not profitability rejection"
        ),
        "nursery_feedback": {
            "nursery_status": "incubation_only",
            "feedback_kind": "negative_execution_admissibility",
            "execution_blocker": EXECUTION_BLOCKER,
            "market_state": MARKET_STATE,
            "execution_readiness": READINESS,
            "execution_readiness_floor": READINESS_FLOOR,
            "profitability_rejection": False,
            "branch_routing_failure": False,
            "source_feedback_packet": rel(SOURCE_FEEDBACK_PACKET),
            "generated_at": generated,
        },
    }
    path = FEEDBACK / "block_crowded_negative_execution_admissibility_feedback_v1.json"
    write_json(path, feedback)
    return path


def train_and_apply_catboost(commands: list[dict[str, Any]]) -> dict[str, Any]:
    target_dir = STATE_DIR / SYMBOL / "policy_training"
    current_csv = target_dir / "structural_path_ranking_target.csv"
    history_csv = target_dir / "structural_path_ranking_target_history.csv"
    model_dir = CATBOOST / "path_ranker_model_py313"
    scores_dir = CATBOOST / "scores_py313"
    current_scores = scores_dir / "current_scores_py313.csv"
    history_scores = scores_dir / "history_scores_py313.csv"
    combined_scores = scores_dir / "combined_scores_py313.csv"
    result = {
        "target_current_exists": current_csv.exists(),
        "target_history_exists": history_csv.exists(),
        "catboost_train_attempted": False,
        "catboost_trained": False,
        "score_rows": 0,
        "apply_scores_exit_zero": False,
        "trainer_registered": False,
        "runtime_enabled": False,
    }
    if not (current_csv.exists() and history_csv.exists()):
        return result
    if not shutil.which("python3.13"):
        return result
    result["catboost_train_attempted"] = True
    commands.append(
        run_command(
            "09_train_catboost_path_ranker_on_nursery_history",
            [
                "python3.13",
                str(TRAINER),
                "--target-csv",
                str(history_csv),
                "--output-dir",
                str(model_dir),
                "--model-family",
                "catboost",
            ],
            timeout=300,
        )
    )
    result["catboost_trained"] = commands[-1]["returncode"] == 0
    if not result["catboost_trained"]:
        return result
    scores_dir.mkdir(parents=True, exist_ok=True)
    commands.append(
        run_command(
            "10_apply_catboost_to_current_target",
            [
                "python3.13",
                str(TRAINER),
                "--apply",
                "--model-dir",
                str(model_dir),
                "--target-csv",
                str(current_csv),
                "--output-scores",
                str(current_scores),
            ],
            timeout=180,
        )
    )
    commands.append(
        run_command(
            "11_apply_catboost_to_history_target",
            [
                "python3.13",
                str(TRAINER),
                "--apply",
                "--model-dir",
                str(model_dir),
                "--target-csv",
                str(history_csv),
                "--output-scores",
                str(history_scores),
            ],
            timeout=180,
        )
    )
    if not (current_scores.exists() and history_scores.exists()):
        return result
    combined = read_csv_rows(current_scores) + read_csv_rows(history_scores)
    write_csv_rows(combined_scores, combined)
    result["score_rows"] = len(combined)
    commands.append(
        run_command(
            "12_apply_catboost_external_scores",
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
    result["apply_scores_exit_zero"] = commands[-1]["returncode"] == 0
    trainer_artifact = model_dir / "trainer_artifact.json"
    if trainer_artifact.exists():
        commands.append(
            run_command(
                "13_register_catboost_path_ranker_artifact",
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
                    str(max(0, len(read_csv_rows(history_scores)))),
                    "--calibration-rows",
                    str(max(0, len(read_csv_rows(history_scores)))),
                ],
            )
        )
        result["trainer_registered"] = commands[-1]["returncode"] == 0
        commands.append(
            run_command(
                "14_enable_structural_path_ranking_runtime",
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
        result["runtime_enabled"] = commands[-1]["returncode"] == 0
    return result


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    for path in [COMMANDS, PROVIDER, FEEDBACK, CATBOOST, CHECKS]:
        path.mkdir(parents=True, exist_ok=True)

    source_readback = read_json(SOURCE_READBACK_JSON)
    score = latest_path_score()
    selected_wire = copy_selected_wire()
    feedback_path = build_feedback(score, source_readback)

    commands: list[dict[str, Any]] = []
    for provider_name in ["yfinance", "tradingview_mcp", "ibkr", "kraken_public", "kraken_cli"]:
        commands.append(
            run_command(
                f"provider_status_{provider_name}_agent",
                [str(ICT), "provider-status", "--provider", provider_name, "--agent"],
                out_dir=PROVIDER,
                timeout=60,
            )
        )

    commands.append(
        run_command(
            "01_auto_quant_ingest_selected_real_trades",
            [
                str(ICT),
                "auto-quant-ingest-real-trades",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--trades",
                str(selected_wire),
                "--source",
                "board_b_b2r_block_crowded_nursery_seed_220646",
            ],
            timeout=120,
        )
    )
    seeded_baseline_feedback_rows = 0
    for index, path in enumerate(source_feedback_paths(), start=1):
        item = read_json(path)
        outcome = str(item.get("realized_outcome", "breakeven"))
        pnl = str(item.get("realized_pnl", 0.0))
        direction = str(item.get("direction", "long"))
        entry_quality = str(item.get("selected_entry_quality", "medium"))
        commands.append(
            run_command(
                f"02_seed_b5_feedback_{index:03d}",
                [
                    str(ICT),
                    "update",
                    "--symbol",
                    SYMBOL,
                    "--outcome",
                    outcome,
                    "--entry-signal",
                    entry_quality,
                    "--state-dir",
                    str(STATE_DIR),
                    f"--pnl={pnl}",
                    "--direction",
                    direction,
                    "--feedback-file",
                    str(path),
                ],
                timeout=60,
            )
        )
        if commands[-1]["returncode"] == 0:
            seeded_baseline_feedback_rows += 1
    commands.append(
        run_command(
            "03_update_block_crowded_negative_feedback",
            [
                str(ICT),
                "update",
                "--symbol",
                SYMBOL,
                "--outcome",
                "invalidated",
                "--entry-signal",
                "medium",
                "--state-dir",
                str(STATE_DIR),
                "--pnl=0",
                "--direction",
                "long",
                "--feedback-file",
                str(feedback_path),
            ],
        )
    )
    commands.append(
        run_command(
            "04_pre_bayes_status_after_negative_feedback",
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
            "05_workflow_structural_path_outcome_summary",
            [
                str(ICT),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--phase",
                "structural-path-outcome-summary",
                "--agent",
            ],
        )
    )
    commands.append(
        run_command(
            "06_workflow_structural_recommended_path_bundle",
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
            "07_workflow_execution_candidate",
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
            "08_export_structural_path_ranking_target",
            [str(ICT), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
        )
    )
    commands.append(
        run_command(
            "09_policy_training_status_before_catboost",
            [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
        )
    )

    catboost_result = train_and_apply_catboost(commands)

    commands.append(
        run_command(
            "15_policy_training_status_final",
            [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
        )
    )
    commands.append(
        run_command(
            "16_workflow_structural_recommended_path_bundle_final",
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
            "17_workflow_execution_candidate_final",
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

    final_policy = read_json(COMMANDS / "15_policy_training_status_final.out")
    final_structural = read_json(COMMANDS / "16_workflow_structural_recommended_path_bundle_final.out")
    final_execution_text = (COMMANDS / "17_workflow_execution_candidate_final.out").read_text(encoding="utf-8").strip()
    path_summary = read_json(COMMANDS / "05_workflow_structural_path_outcome_summary.out")
    provider_exits = {
        item["name"].removeprefix("provider_status_").removesuffix("_agent"): item["returncode"]
        for item in commands
        if item["name"].startswith("provider_status_")
    }
    command_exits_ok = all(item["returncode"] == 0 for item in commands if not item["name"].startswith("provider_status_"))
    policy_validation = final_policy.get("structural_path_ranking_validation", {}) if isinstance(final_policy, dict) else {}
    final_path = final_structural.get("path_id") if isinstance(final_structural, dict) else None
    final_execution_ready = final_execution_text not in {"", "null"}

    summary = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "accepted_regime_id": ACCEPTED_REGIME_ID,
        "symbol": SYMBOL,
        "recipe_id": RECIPE_ID,
        "nursery_branch_id": "B2R-block-crowded-crisis-carry-220646",
        "nursery_status": "incubation_only",
        "branch_path": EXACT_BRANCH_PATH,
        "parent_regime_root": "Crisis",
        "child_regime_hypothesis": "CrisisReliefCarry",
        "child_child_or_profit_factor": "StopManagedPanicRecovery",
        "profit_factor_leaf": "SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12",
        "action_leaf": "long_relief_research_only_until_closed_loop_passes",
        "feedback_kind": "negative_execution_admissibility",
        "execution_blocker": EXECUTION_BLOCKER,
        "market_state": MARKET_STATE,
        "execution_readiness": READINESS,
        "execution_readiness_floor": READINESS_FLOOR,
        "source_readback": rel(SOURCE_READBACK_JSON),
        "source_feedback_packet": rel(SOURCE_FEEDBACK_PACKET),
        "selected_wire": rel(selected_wire),
        "feedback_artifact": rel(feedback_path),
        "provider_status_exit_codes": provider_exits,
        "seeded_baseline_feedback_rows": seeded_baseline_feedback_rows,
        "seeded_baseline_feedback_expected": len(source_feedback_paths()),
        "auto_quant_seed_ingested": next((item["returncode"] == 0 for item in commands if item["name"] == "01_auto_quant_ingest_selected_real_trades"), False),
        "filter_probe_result": "pre_bayes_status_exit0" if next((item["returncode"] == 0 for item in commands if item["name"] == "04_pre_bayes_status_after_negative_feedback"), False) else "pre_bayes_status_failed",
        "bbn_probe_result": "update_consumed_feedback_exit0" if next((item["returncode"] == 0 for item in commands if item["name"] == "03_update_block_crowded_negative_feedback"), False) else "update_failed",
        "catboost_probe_result": catboost_result,
        "execution_tree_probe_result": {
            "structural_path": final_path,
            "execution_candidate_payload_present": final_execution_ready,
            "policy_validation": policy_validation,
        },
        "path_outcome_summary": path_summary,
        "promotion_blocker": "incubation_only_negative_execution_feedback_not_a_promotion_gate",
        "feedback_to_board_a": (
            "Candidate only: repeated block_crowded observations under "
            "RangeConsolidation/WideRange should become a negative execution-admissibility "
            "feature for this Crisis carry branch."
        ),
        "promotion_allowed": False,
        "command_exits_ok": command_exits_ok,
        "commands": commands,
    }
    write_json(OUT / "b2r_block_crowded_nursery_v1.json", summary)

    assertions = [
        f"run_id={RUN_ID}",
        "nursery_status=incubation_only",
        f"branch_path={EXACT_BRANCH_PATH}",
        f"execution_blocker={EXECUTION_BLOCKER}",
        f"market_state={MARKET_STATE}",
        f"provider_status_exit_codes={provider_exits}",
        f"seeded_baseline_feedback_rows={seeded_baseline_feedback_rows}",
        f"auto_quant_seed_ingested={summary['auto_quant_seed_ingested']}",
        f"filter_probe_result={summary['filter_probe_result']}",
        f"bbn_probe_result={summary['bbn_probe_result']}",
        f"catboost_train_attempted={catboost_result['catboost_train_attempted']}",
        f"catboost_trained={catboost_result['catboost_trained']}",
        f"catboost_runtime_enabled={catboost_result['runtime_enabled']}",
        f"execution_candidate_payload_present={final_execution_ready}",
        "promotion_allowed=False",
        f"command_exits_ok={command_exits_ok}",
    ]
    assertion_path = CHECKS / "b2r_block_crowded_nursery_v1_assertions.out"
    assertion_path.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    report = [
        "# B2R Block-Crowded Nursery v1",
        "",
        f"Run id: `{RUN_ID}`",
        "",
        "## Decision",
        "",
        "`block_crowded` is recorded as `incubation_only` negative execution-admissibility feedback for the exact Crisis branch. It is not a profitability rejection and not a promotion.",
        "",
        "## Branch",
        "",
        f"- Accepted Board A context: `{ACCEPTED_REGIME_ID}`",
        f"- Branch path: `{EXACT_BRANCH_PATH}`",
        f"- Runtime context: `{MARKET_STATE}`",
        f"- Execution readiness: `{READINESS:.4f} < {READINESS_FLOOR:.2f}`",
        "",
        "## Runtime Probes",
        "",
        f"- Provider status exits: `{provider_exits}`",
        f"- Seeded baseline B5 feedback rows: `{seeded_baseline_feedback_rows}/{len(source_feedback_paths())}`",
        f"- Auto-Quant seed ingested: `{summary['auto_quant_seed_ingested']}`",
        f"- Pre-Bayes/filter probe: `{summary['filter_probe_result']}`",
        f"- BBN/update feedback probe: `{summary['bbn_probe_result']}`",
        f"- CatBoost trained: `{catboost_result['catboost_trained']}`",
        f"- CatBoost runtime enabled: `{catboost_result['runtime_enabled']}`",
        f"- Execution-candidate payload present: `{final_execution_ready}`",
        f"- Promotion allowed: `False`",
        "",
        "## Artifacts",
        "",
        f"- Summary JSON: `{rel(OUT / 'b2r_block_crowded_nursery_v1.json')}`",
        f"- Feedback JSON: `{rel(feedback_path)}`",
        f"- Assertions: `{rel(assertion_path)}`",
        f"- Command logs: `{rel(COMMANDS)}`",
        f"- Provider logs: `{rel(PROVIDER)}`",
        "",
        "## Next",
        "",
        "Accumulate more nursery observations for this exact branch under crowded and non-crowded contexts before promoting any Board A rule change. Rerun strict `220646` promotion only when execution readiness/context is compatible.",
    ]
    report_path = OUT / "b2r_block_crowded_nursery_v1.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
