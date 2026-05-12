from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[6]
ICT_ENGINE = REPO_ROOT / "target" / "debug" / "ict-engine"
ENRICHER = REPO_ROOT / "scripts" / "auto_quant_external" / "structural_feedback_trade_enricher.py"

RUN_ID = "20260511T234658+0800-codex-board-b-b2r-block-crowded-nursery-feedback-v1"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
BRANCH_PATH = (
    "Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> "
    "SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12"
)
SOURCE_READBACK_ID = "20260511T231800+0800-codex-board-b-220646-exact-branch-closed-loop-readback-v4"
SOURCE_DIAGNOSIS_ID = "20260511T233045+0800-codex-board-b-220646-execution-tree-block-crowded-diagnosis-v1"
SOURCE_FEEDBACK_ID = "20260511T233358+0800-codex-board-b-220646-block-crowded-feedback-packet-v1"

RUN_ROOT = (
    REPO_ROOT
    / "docs"
    / "experiments"
    / "actionable-regime-confidence"
    / "runs"
    / "20260511T234658-codex-board-b-b2r-block-crowded-nursery-feedback-v1"
)
SOURCE_ROOT = (
    REPO_ROOT
    / "docs"
    / "experiments"
    / "actionable-regime-confidence"
    / "runs"
    / "20260511T231800-codex-board-b-220646-exact-branch-closed-loop-readback-v4"
    / "exact-branch-closed-loop-readback-v4"
)
SOURCE_STATE = SOURCE_ROOT / "state_exact_branch_closed_loop_v4"
STATE_DIR = RUN_ROOT / "state_b2r_block_crowded_nursery_v1"
SUMMARY_DIR = RUN_ROOT / "b2r-block-crowded-nursery-feedback-v1"
LOG_DIR = RUN_ROOT / "command-output"
FEEDBACK_PATH = SUMMARY_DIR / "block_crowded_nursery_structural_feedback_v1.json"
SUMMARY_JSON = SUMMARY_DIR / "block_crowded_nursery_feedback_v1.json"
SUMMARY_MD = SUMMARY_DIR / "block_crowded_nursery_feedback_v1.md"
ASSERTIONS = RUN_ROOT / "checks" / "block_crowded_nursery_feedback_v1_assertions.out"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_command(name: str, cmd: list[str], *, timeout: int = 120) -> dict[str, Any]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    stdout_path = LOG_DIR / f"{name}.out"
    stderr_path = LOG_DIR / f"{name}.err"
    exit_path = LOG_DIR / f"{name}.exit"
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


def load_json_from_command(command: dict[str, Any]) -> Any:
    return json.loads((REPO_ROOT / command["stdout_path"]).read_text(encoding="utf-8"))


def refresh_state_copy() -> None:
    if STATE_DIR.exists():
        shutil.rmtree(STATE_DIR)
    shutil.copytree(SOURCE_STATE, STATE_DIR)


def emit_feedback() -> dict[str, Any]:
    target_csv = STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target.csv"
    return run_command(
        "01_emit_block_crowded_nursery_feedback",
        [
            "python3",
            str(ENRICHER),
            "emit-probe",
            "--target-csv",
            str(target_csv),
            "--output",
            str(FEEDBACK_PATH),
            "--path-id",
            BRANCH_PATH,
            "--realized-outcome",
            "not_followed",
            "--not-followed",
            "--pnl",
            "0.0",
            "--exit-reason",
            "execution_tree_block_crowded",
            "--notes",
            "B2R nursery feedback: exact Crisis branch was selected, but execution tree blocked block_crowded under RangeConsolidation/WideRange; record as execution-admissibility not-followed context, not profitability rejection.",
        ],
    )


def extract_statuses(commands: list[dict[str, Any]]) -> dict[str, Any]:
    policy = load_json_from_command(commands_by_name(commands)["05_policy_training_status_json"])
    pre_bayes = load_json_from_command(commands_by_name(commands)["08_pre_bayes_status_json"])
    target = policy.get("structural_path_ranking_target", {})
    validation = policy.get("structural_path_ranking_validation", {})
    feedback_validation = validation.get("feedback_observation_validation", {})
    return {
        "feedback_rows_total": target.get("feedback_rows_total"),
        "feedback_rows_with_structural_feedback": target.get("feedback_rows_with_structural_feedback"),
        "observation_total": feedback_validation.get("total_observations"),
        "observation_outcomes": feedback_validation.get("outcome_distribution"),
        "runtime_ready": policy.get("structural_path_ranking_runtime", {}).get("ready"),
        "production_validation_ready": validation.get("production_validation_ready"),
        "observation_validation_ready": validation.get("observation_validation_ready"),
        "pre_bayes_gate": pre_bayes.get("gating_status")
        or pre_bayes.get("pre_bayes_gate_status")
        or pre_bayes.get("latest_gate_status")
        or pre_bayes.get("status"),
        "pre_bayes_branch_path_gate": pre_bayes.get("latest_filtered_assignments", {}).get(
            "pre_bayes_branch_path_gate"
        ),
        "policy_summary": policy.get("summary_line"),
    }


def commands_by_name(commands: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {command["name"]: command for command in commands}


def write_summary(commands: list[dict[str, Any]], status: dict[str, Any]) -> dict[str, Any]:
    feedback = json.loads(FEEDBACK_PATH.read_text(encoding="utf-8"))
    structural = feedback.get("structural_feedback", feedback)
    summary = {
        "schema_version": "board-b-b2r-block-crowded-nursery-feedback/v1",
        "run_id": RUN_ID,
        "generated_at": now_utc(),
        "source_readback_id": SOURCE_READBACK_ID,
        "source_diagnosis_id": SOURCE_DIAGNOSIS_ID,
        "source_feedback_id": SOURCE_FEEDBACK_ID,
        "accepted_regime_id": "BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation",
        "recipe_id": "SourceRootStopCarryLongHorizonV1",
        "nursery_branch_id": "B2R-220646-crisis-block-crowded-admissibility-v1",
        "nursery_status": "incubation_only",
        "branch_path": BRANCH_PATH,
        "feedback_realized_outcome": feedback.get("realized_outcome") or structural.get("realized_outcome"),
        "feedback_followed_path": structural.get("followed_path"),
        "feedback_exit_reason": structural.get("exit_reason"),
        "feedback_file": str(FEEDBACK_PATH.relative_to(REPO_ROOT)),
        "state_dir": str(STATE_DIR.relative_to(REPO_ROOT)),
        "status": status,
        "commands": commands,
        "promotion_allowed": False,
        "feedback_to_board_a": "nursery_feedback_only: block_crowded should be tested as a negative execution-admissibility condition for this exact Crisis branch across repeat contexts before Board A changes.",
        "next_action": "Run a compatible-context replay or live readback only when execution readiness is not crowded; keep this row incubation_only until repeated.",
    }
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    SUMMARY_MD.write_text(
        "\n".join(
            [
                "# B2R Block-Crowded Nursery Feedback v1",
                "",
                f"Run id: `{RUN_ID}`",
                "",
                "## Scope",
                "",
                "This is nursery feedback only. It consumes the verified exact Crisis branch `block_crowded` execution-tree block and records it as a not-followed execution-admissibility observation, not as a profitability rejection.",
                "",
                "## Branch",
                "",
                f"- Branch path: `{BRANCH_PATH}`",
                "- Nursery status: `incubation_only`",
                "- Feedback outcome: `not_followed`",
                "- Exit reason: `execution_tree_block_crowded`",
                "",
                "## Runtime Readback",
                "",
                f"- Structural feedback rows: `{status.get('feedback_rows_with_structural_feedback')}` / total `{status.get('feedback_rows_total')}`",
                f"- Observation outcomes: `{status.get('observation_outcomes')}`",
                f"- Ranker runtime ready: `{status.get('runtime_ready')}`",
                f"- Production validation ready: `{status.get('production_validation_ready')}`",
                f"- Observation validation ready: `{status.get('observation_validation_ready')}`",
                f"- Pre-Bayes gate readback: `{status.get('pre_bayes_gate')}`",
                f"- Pre-Bayes branch-path gate: `{status.get('pre_bayes_branch_path_gate')}`",
                "",
                "## Board A Feedback",
                "",
                "Candidate feedback only: require non-crowded execution readiness or compatible context before replaying the exact Crisis carry branch for promotion. Do not treat this single row as an accepted Board A replacement rule.",
                "",
                "## Artifacts",
                "",
                f"- `{FEEDBACK_PATH.relative_to(REPO_ROOT)}`",
                f"- `{SUMMARY_JSON.relative_to(REPO_ROOT)}`",
                f"- `{ASSERTIONS.relative_to(REPO_ROOT)}`",
                "",
                "## Next",
                "",
                "Run a compatible-context replay or live readback only when execution readiness is not crowded; keep promotion blocked.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return summary


def write_assertions(summary: dict[str, Any]) -> None:
    status = summary["status"]
    command_failures = [c for c in summary["commands"] if c["returncode"] != 0]
    lines = [
        f"run_id={summary['run_id']}",
        f"command_failures={len(command_failures)}",
        f"branch_path_preserved={summary['branch_path'] == BRANCH_PATH}",
        f"nursery_status={summary['nursery_status']}",
        f"feedback_realized_outcome={summary['feedback_realized_outcome']}",
        f"feedback_followed_path={str(summary['feedback_followed_path']).lower()}",
        f"feedback_exit_reason={summary['feedback_exit_reason']}",
        f"feedback_rows_total={status.get('feedback_rows_total')}",
        f"feedback_rows_with_structural_feedback={status.get('feedback_rows_with_structural_feedback')}",
        f"runtime_ready={str(status.get('runtime_ready')).lower()}",
        f"production_validation_ready={str(status.get('production_validation_ready')).lower()}",
        f"observation_validation_ready={str(status.get('observation_validation_ready')).lower()}",
        f"promotion_allowed={str(summary['promotion_allowed']).lower()}",
    ]
    ASSERTIONS.parent.mkdir(parents=True, exist_ok=True)
    ASSERTIONS.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    refresh_state_copy()
    commands: list[dict[str, Any]] = []
    commands.append(run_command("00_provider_status_agent", [str(ICT_ENGINE), "provider-status", "--agent"]))
    commands.append(
        run_command(
            "00b_auto_quant_status_json",
            [str(ICT_ENGINE), "auto-quant-status", "--state-dir", str(STATE_DIR / "auto-quant")],
        )
    )
    commands.append(emit_feedback())
    commands.append(
        run_command(
            "02_update_not_followed_block_crowded",
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
                str(FEEDBACK_PATH),
            ],
        )
    )
    commands.append(
        run_command(
            "03_export_structural_path_ranking_target",
            [str(ICT_ENGINE), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
        )
    )
    commands.append(
        run_command(
            "04_workflow_structural_bundle_agent",
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
            "05_policy_training_status_json",
            [str(ICT_ENGINE), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
        )
    )
    commands.append(
        run_command(
            "06_workflow_execution_candidate_agent",
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
    commands.append(
        run_command(
            "07_workflow_full_json",
            [str(ICT_ENGINE), "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
        )
    )
    commands.append(
        run_command(
            "08_pre_bayes_status_json",
            [str(ICT_ENGINE), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"],
        )
    )
    status = extract_statuses(commands)
    summary = write_summary(commands, status)
    write_assertions(summary)
    print(json.dumps(summary, indent=2))
    return 0 if all(command["returncode"] == 0 for command in commands) else 1


if __name__ == "__main__":
    raise SystemExit(main())
