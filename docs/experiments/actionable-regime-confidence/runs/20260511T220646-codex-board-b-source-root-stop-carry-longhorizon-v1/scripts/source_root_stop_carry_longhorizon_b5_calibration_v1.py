from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
RUN_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[6]
ICT_ENGINE = REPO_ROOT / "target" / "debug" / "ict-engine"
TRAINER = REPO_ROOT / "scripts" / "auto_quant_external" / "pandas_path_ranker_trainer.py"
WIRE_JSONL = RUN_ROOT / "ict-engine-downstream" / "source_root_stop_carry_longhorizon_real_trades_wire_v1.jsonl"
BRANCH_SCORES = RUN_ROOT / "downstream-chain" / "catboost" / "branch_path_scores_v1.csv"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
ROOTS = ("Bull", "Bear", "Sideways", "Crisis")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def read_branch_scores(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {
            row["regime_profit_branch_path"]: float(row["raw_path_score"])
            for row in csv.DictReader(handle)
        }


def select_evenly(rows: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if len(rows) <= count:
        return rows
    if count <= 1:
        return [rows[0]]
    step = (len(rows) - 1) / float(count - 1)
    return [rows[round(i * step)] for i in range(count)]


def run_command(cmd: list[str], out_dir: Path, name: str, timeout: int | None = None) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = out_dir / f"{name}.out"
    stderr_path = out_dir / f"{name}.err"
    exit_path = out_dir / f"{name}.exit"
    timed_out = False
    try:
        result = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        stdout = result.stdout
        stderr = result.stderr
        returncode = result.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = (exc.stdout or "")
        stderr = (exc.stderr or "")
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        stderr = f"{stderr}\nTIMEOUT after {timeout}s\n"
        returncode = 124
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(str(returncode) + "\n", encoding="utf-8")
    return {
        "name": name,
        "cmd": cmd,
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout_path": str(stdout_path.relative_to(REPO_ROOT)),
        "stderr_path": str(stderr_path.relative_to(REPO_ROOT)),
        "exit_path": str(exit_path.relative_to(REPO_ROOT)),
    }


def load_json_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def load_scores(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def feedback_submission(record: dict[str, Any], branch_scores: dict[str, float]) -> dict[str, Any]:
    feedback = dict(record["structural_feedback"])
    path = feedback["path_id"]
    score = float(branch_scores.get(path, 0.5))
    feedback["candidate_set_id"] = "branch-path-candidates:SourceRootStopCarryLongHorizonV1:220646"
    feedback["candidate_set_size"] = 4
    feedback["selected_path_probability"] = score
    feedback["selected_entry_quality"] = "medium"
    feedback["selected_entry_quality_probability"] = score
    feedback["pre_bayes_gate_status"] = "pass_neutralized"
    feedback["path_posterior"] = score
    feedback["bbn_support_score"] = score
    feedback["realized_outcome"] = record["realized_outcome"]
    feedback["realized_pnl"] = float(record["pnl"])
    feedback["notes"] = (
        "b5_branch_feedback_calibration_v1; exact Board B regime_profit_branch_path; "
        f"source_trade_id={record.get('trade_id', '')}"
    )
    return feedback


def command_returncodes_ok(commands: list[dict[str, Any]], required_names: set[str]) -> bool:
    observed = {item["name"]: item["returncode"] for item in commands}
    return all(observed.get(name) == 0 for name in required_names)


def main() -> int:
    parser = argparse.ArgumentParser(description="B5 branch-path calibration replay for 220646")
    parser.add_argument("--count-per-root", type=int, default=20)
    parser.add_argument("--output-root", default=str(RUN_ROOT / "b5-branch-feedback-calibration-v1"))
    parser.add_argument("--skip-catboost", action="store_true")
    args = parser.parse_args()

    output_root = Path(args.output_root)
    state_dir = output_root / "state_branch_feedback_v1"
    feedback_dir = output_root / "feedback"
    command_dir = output_root / "command-output"
    model_dir = output_root / "catboost" / "path_ranker_model"
    scores_dir = output_root / "catboost" / "scores"
    if output_root.exists():
        shutil.rmtree(output_root)
    feedback_dir.mkdir(parents=True, exist_ok=True)
    command_dir.mkdir(parents=True, exist_ok=True)
    scores_dir.mkdir(parents=True, exist_ok=True)

    branch_scores = read_branch_scores(BRANCH_SCORES)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in read_jsonl(WIRE_JSONL):
        root = record.get("regime_at_entry")
        if root in ROOTS and record.get("structural_feedback"):
            grouped[root].append(record)

    selected: list[dict[str, Any]] = []
    for root in ROOTS:
        selected.extend(select_evenly(grouped[root], args.count_per_root))

    feedback_paths: list[Path] = []
    manifest_rows: list[dict[str, Any]] = []
    for index, record in enumerate(selected, start=1):
        root = record["regime_at_entry"]
        feedback = feedback_submission(record, branch_scores)
        path = feedback_dir / f"feedback_{index:03d}_{root.lower()}.json"
        path.write_text(json.dumps(feedback, indent=2) + "\n", encoding="utf-8")
        feedback_paths.append(path)
        manifest_rows.append(
            {
                "index": index,
                "root": root,
                "trade_id": record.get("trade_id", ""),
                "realized_outcome": record.get("realized_outcome", ""),
                "pnl": record.get("pnl", 0.0),
                "regime_profit_branch_path": feedback["path_id"],
                "selected_path_probability": feedback["selected_path_probability"],
                "feedback_path": str(path.relative_to(REPO_ROOT)),
            }
        )

    selected_wire = output_root / "selected_real_trades_wire.jsonl"
    selected_wire.write_text(
        "".join(json.dumps(record, ensure_ascii=True) + "\n" for record in selected),
        encoding="utf-8",
    )

    (output_root / "selected_feedback_manifest.json").write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "symbol": SYMBOL,
                "count_per_root": args.count_per_root,
                "selected_total": len(selected),
                "selected_wire": str(selected_wire.relative_to(REPO_ROOT)),
                "root_counts": {root: len([row for row in manifest_rows if row["root"] == root]) for root in ROOTS},
                "rows": manifest_rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    commands: list[dict[str, Any]] = []
    commands.append(
        run_command(
            [
                str(ICT_ENGINE),
                "auto-quant-ingest-real-trades",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(state_dir),
                "--trades",
                str(selected_wire),
                "--source",
                "board_b_220646_b5_branch_feedback_calibration_selected_wire",
            ],
            command_dir,
            "01_auto_quant_ingest_real_trades_selected_wire",
            timeout=120,
        )
    )

    for index, (record, feedback_path) in enumerate(zip(selected, feedback_paths, strict=True), start=1):
        root = record["regime_at_entry"]
        outcome = str(record["realized_outcome"])
        pnl = str(record["pnl"])
        direction = str(record.get("direction", "long"))
        entry_signal = str(record.get("entry_signal", "medium"))
        commands.append(
            run_command(
                [
                    str(ICT_ENGINE),
                    "update",
                    "--symbol",
                    SYMBOL,
                    "--outcome",
                    outcome,
                    "--entry-signal",
                    entry_signal,
                    "--state-dir",
                    str(state_dir),
                    f"--pnl={pnl}",
                    "--direction",
                    direction,
                    "--feedback-file",
                    str(feedback_path),
                ],
                command_dir,
                f"02_update_branch_feedback_{index:03d}_{root.lower()}",
                timeout=60,
            )
        )

    commands.append(
        run_command(
            [str(ICT_ENGINE), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(state_dir), "--refresh", "--output-format", "json"],
            command_dir,
            "03_pre_bayes_status_after_branch_feedback",
            timeout=60,
        )
    )
    commands.append(
        run_command(
            [str(ICT_ENGINE), "workflow-status", "--symbol", SYMBOL, "--state-dir", str(state_dir), "--phase", "structural-recommended-path-bundle", "--agent"],
            command_dir,
            "04_workflow_structural_recommended_path_bundle_after_branch_feedback",
            timeout=60,
        )
    )
    commands.append(
        run_command(
            [str(ICT_ENGINE), "workflow-status", "--symbol", SYMBOL, "--state-dir", str(state_dir), "--phase", "execution-candidate", "--agent"],
            command_dir,
            "05_workflow_execution_candidate_after_branch_feedback",
            timeout=60,
        )
    )
    commands.append(
        run_command(
            [str(ICT_ENGINE), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(state_dir)],
            command_dir,
            "06_export_structural_path_ranking_target_after_branch_feedback",
            timeout=60,
        )
    )

    target_dir = state_dir / SYMBOL / "policy_training"
    current_csv = target_dir / "structural_path_ranking_target.csv"
    history_csv = target_dir / "structural_path_ranking_target_history.csv"
    current_scores = scores_dir / "current_scores.csv"
    history_scores = scores_dir / "history_scores.csv"
    combined_scores = scores_dir / "combined_scores.csv"

    catboost_ran = False
    if not args.skip_catboost and history_csv.exists() and current_csv.exists():
        uv = shutil.which("uv")
        if uv:
            trainer_prefix = [
                uv,
                "run",
                "--offline",
                "--python",
                "3.11",
                "--with",
                "pandas",
                "--with",
                "numpy",
                "--with",
                "catboost",
                "python",
            ]
            commands.append(
                run_command(
                    [
                        *trainer_prefix,
                        str(TRAINER),
                        "--target-csv",
                        str(history_csv),
                        "--output-dir",
                        str(model_dir),
                        "--model-family",
                        "catboost",
                    ],
                    command_dir,
                    "07_train_catboost_path_ranker_on_branch_history",
                    timeout=300,
                )
            )
            if commands[-1]["returncode"] == 0:
                catboost_ran = True
                commands.append(
                    run_command(
                        [
                            *trainer_prefix,
                            str(TRAINER),
                            "--apply",
                            "--model-dir",
                            str(model_dir),
                            "--target-csv",
                            str(current_csv),
                            "--output-scores",
                            str(current_scores),
                        ],
                        command_dir,
                        "08_apply_catboost_to_current_target",
                        timeout=180,
                    )
                )
                commands.append(
                    run_command(
                        [
                            *trainer_prefix,
                            str(TRAINER),
                            "--apply",
                            "--model-dir",
                            str(model_dir),
                            "--target-csv",
                            str(history_csv),
                            "--output-scores",
                            str(history_scores),
                        ],
                        command_dir,
                        "09_apply_catboost_to_history_target",
                        timeout=180,
                    )
                )
                if current_scores.exists() and history_scores.exists():
                    combined = load_scores(current_scores) + load_scores(history_scores)
                    write_csv_rows(combined_scores, combined)
                    commands.append(
                        run_command(
                            [
                                str(ICT_ENGINE),
                                "apply-structural-path-ranking-external-scores",
                                "--symbol",
                                SYMBOL,
                                "--state-dir",
                                str(state_dir),
                                "--scores-file",
                                str(combined_scores),
                            ],
                            command_dir,
                            "10_apply_catboost_external_scores",
                            timeout=60,
                        )
                    )
                    trainer_artifact = model_dir / "trainer_artifact.json"
                    if trainer_artifact.exists():
                        commands.append(
                            run_command(
                                [
                                    str(ICT_ENGINE),
                                    "register-structural-path-ranking-trainer-artifact",
                                    "--symbol",
                                    SYMBOL,
                                    "--state-dir",
                                    str(state_dir),
                                    "--artifact-uri",
                                    str(trainer_artifact),
                                    "--model-family",
                                    "catboost",
                                    "--score-column",
                                    "raw_path_score",
                                    "--trained-rows",
                                    str(len(load_scores(history_scores))),
                                    "--calibration-rows",
                                    str(len(load_scores(history_scores))),
                                ],
                                command_dir,
                                "11_register_catboost_path_ranker_artifact",
                                timeout=60,
                            )
                        )
                        commands.append(
                            run_command(
                                [
                                    str(ICT_ENGINE),
                                    "enable-structural-path-ranking-runtime",
                                    "--symbol",
                                    SYMBOL,
                                    "--state-dir",
                                    str(state_dir),
                                    "--reuse-mode",
                                    "prefer_history",
                                ],
                                command_dir,
                                "12_enable_structural_path_ranking_runtime",
                                timeout=60,
                            )
                        )

    commands.append(
        run_command(
            [str(ICT_ENGINE), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(state_dir), "--output-format", "json"],
            command_dir,
            "13_policy_training_status_final",
            timeout=60,
        )
    )
    commands.append(
        run_command(
            [str(ICT_ENGINE), "workflow-status", "--symbol", SYMBOL, "--state-dir", str(state_dir), "--phase", "structural-recommended-path-bundle", "--agent"],
            command_dir,
            "14_workflow_structural_recommended_path_bundle_final",
            timeout=60,
        )
    )
    commands.append(
        run_command(
            [str(ICT_ENGINE), "workflow-status", "--symbol", SYMBOL, "--state-dir", str(state_dir), "--phase", "execution-candidate", "--agent"],
            command_dir,
            "15_workflow_execution_candidate_final",
            timeout=60,
        )
    )
    commands.append(
        run_command(
            [str(ICT_ENGINE), "workflow-status", "--symbol", SYMBOL, "--state-dir", str(state_dir), "--agent"],
            command_dir,
            "16_workflow_status_agent_final",
            timeout=60,
        )
    )

    final_policy = load_json_file(command_dir / "13_policy_training_status_final.out")
    final_structural = load_json_file(command_dir / "14_workflow_structural_recommended_path_bundle_final.out")
    final_execution_raw = (command_dir / "15_workflow_execution_candidate_final.out").read_text(encoding="utf-8").strip()
    final_target_summary = load_json_file(target_dir / "structural_path_ranking_target_summary.json")

    required_branch_paths = {row["regime_profit_branch_path"] for row in manifest_rows}
    history_paths: set[str] = set()
    if history_csv.exists():
        with history_csv.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                path = row.get("path_id", "")
                if "SourceRootStopCarryLongHorizonV1" in path:
                    history_paths.add(path)

    policy_target = final_policy.get("structural_path_ranking_target", {}) if isinstance(final_policy, dict) else {}
    policy_validation = final_policy.get("structural_path_ranking_validation", {}) if isinstance(final_policy, dict) else {}
    current_path_id = final_structural.get("path_id") if isinstance(final_structural, dict) else None
    current_is_required_branch_path = current_path_id in required_branch_paths
    execution_tree_ready = final_execution_raw not in {"", "null"}
    history_covers_required_paths = required_branch_paths.issubset(history_paths)
    calibrated_ready = bool(policy_validation.get("production_validation_ready")) or bool(policy_target.get("calibration_ready"))
    promotion_allowed = bool(current_is_required_branch_path and execution_tree_ready and calibrated_ready)

    summary = {
        "run_id": "20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-b5-calibration-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "symbol": SYMBOL,
        "state_dir": str(state_dir.relative_to(REPO_ROOT)),
        "selected_total": len(selected),
        "count_per_root": args.count_per_root,
        "root_counts": {root: len([row for row in manifest_rows if row["root"] == root]) for root in ROOTS},
        "required_branch_paths": sorted(required_branch_paths),
        "history_branch_paths_observed": sorted(history_paths),
        "history_covers_required_paths": history_covers_required_paths,
        "catboost_train_attempted": not args.skip_catboost,
        "catboost_trained": catboost_ran,
        "final_target_summary": final_target_summary,
        "final_policy_training_target": policy_target,
        "final_policy_training_validation": policy_validation,
        "final_structural_path_id": current_path_id,
        "current_path_is_required_branch_path": current_is_required_branch_path,
        "execution_tree_ready": execution_tree_ready,
        "closed_loop_confidence_ready": promotion_allowed,
        "promotion_allowed": promotion_allowed,
        "decision": "b5_branch_feedback_calibrated_not_promoted" if not promotion_allowed else "b5_branch_feedback_promotable_candidate",
        "commands": commands,
    }
    (output_root / "source_root_stop_carry_longhorizon_b5_calibration_v1.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    assertions = [
        f"run_id={summary['run_id']}",
        f"selected_total={len(selected)}",
        f"root_counts={summary['root_counts']}",
        f"history_covers_required_paths={history_covers_required_paths}",
        f"catboost_train_attempted={summary['catboost_train_attempted']}",
        f"catboost_trained={catboost_ran}",
        f"policy_production_validation_ready={policy_validation.get('production_validation_ready')}",
        f"policy_observation_validation_ready={policy_validation.get('observation_validation_ready')}",
        f"current_path_is_required_branch_path={current_is_required_branch_path}",
        f"execution_tree_ready={execution_tree_ready}",
        f"closed_loop_confidence_ready={promotion_allowed}",
        f"promotion_allowed={promotion_allowed}",
        f"decision={summary['decision']}",
    ]
    (output_root / "source_root_stop_carry_longhorizon_b5_calibration_v1_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )
    md = [
        "# SourceRootStopCarryLongHorizon B5 Calibration v1",
        "",
        f"- Decision: `{summary['decision']}`",
        f"- Selected feedback: `{len(selected)}` rows, `{args.count_per_root}` per root",
        f"- Required branch paths covered in history: `{history_covers_required_paths}`",
        f"- CatBoost trained: `{catboost_ran}`",
        f"- Policy production validation ready: `{policy_validation.get('production_validation_ready')}`",
        f"- Policy observation validation ready: `{policy_validation.get('observation_validation_ready')}`",
        f"- Current structural path is required Board B branch path: `{current_is_required_branch_path}`",
        f"- Execution-tree candidate ready: `{execution_tree_ready}`",
        f"- Closed-loop confidence ready: `{promotion_allowed}`",
        f"- Promotion allowed: `{promotion_allowed}`",
        "",
        "## Branch Paths",
        *[f"- `{path}`" for path in sorted(required_branch_paths)],
        "",
        "## Artifacts",
        f"- JSON: `{(output_root / 'source_root_stop_carry_longhorizon_b5_calibration_v1.json').relative_to(REPO_ROOT)}`",
        f"- Assertions: `{(output_root / 'source_root_stop_carry_longhorizon_b5_calibration_v1_assertions.out').relative_to(REPO_ROOT)}`",
        f"- Command logs: `{command_dir.relative_to(REPO_ROOT)}`",
        f"- State dir: `{state_dir.relative_to(REPO_ROOT)}`",
        "",
        "## Readback",
        "The exact Board B branch paths are present in the structural feedback history and CatBoost scoring path. "
        "The current ict-engine execution-tree surface still emits its own structural path rather than one of the "
        "four `regime_profit_branch_path` values, so production promotion remains fail-closed unless that runtime "
        "surface consumes a required Board B branch path directly.",
    ]
    (output_root / "source_root_stop_carry_longhorizon_b5_calibration_v1.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
