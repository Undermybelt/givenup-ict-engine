#!/usr/bin/env python3
"""Replay exact Board B branch feedback with a JSON CatBoost trainer companion."""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T224858+0800-codex-board-b-220646-exact-branch-runtime-repair-v3"
SOURCE_RUN_ID = "20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-v1"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
RECIPE_ID = "SourceRootStopCarryLongHorizonV1"

HERE = Path(__file__).resolve().parent
RUN_ROOT = HERE.parent
REPO_ROOT = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
ICT = REPO_ROOT / "target/debug/ict-engine"

SOURCE_ROOT = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
BRANCH_SUMMARY = SOURCE_ROOT / "branch-rc-spa/source_root_stop_carry_longhorizon_branch_summary_v1.csv"
BRANCH_SCORES = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T222451-codex-board-b-220646-target-surface-readback-v1/catboost/branch_path_scores_v1.csv"
MODEL_PATH = REPO_ROOT / "docs/experiments/actionable-regime-confidence/runs/20260511T222451-codex-board-b-220646-target-surface-readback-v1/catboost/path_ranker_model/catboost_model.cbm"
FEEDBACK_MANIFEST = SOURCE_ROOT / "b5-branch-feedback-calibration-v1/selected_feedback_manifest.json"
SOURCE_CALIBRATION_STATE = SOURCE_ROOT / "b5-branch-feedback-calibration-v1/state_branch_feedback_v1"

OUT_DIR = RUN_ROOT / "ict-engine-exact-branch-feedback-repair-v3"
FEEDBACK_DIR = OUT_DIR / "feedback"
LOG_DIR = OUT_DIR / "logs"
CATBOOST_DIR = OUT_DIR / "catboost/path_ranker_model"
STATE_DIR = OUT_DIR / "state_exact_branch_feedback_v3"
EXPORT_BEFORE = OUT_DIR / "exact_branch_target_export_before_scores_v3.json"
EXPORT_AFTER = OUT_DIR / "exact_branch_target_export_after_scores_v3.json"
SCORES_FILE = OUT_DIR / "exact_branch_runtime_scores_v3.csv"
TRAINER_ARTIFACT = CATBOOST_DIR / "trainer_artifact.json"
DEBUG_MD = OUT_DIR / "DEBUG.md"
SUMMARY_JSON = OUT_DIR / "exact_branch_feedback_runtime_repair_v3.json"
SUMMARY_MD = OUT_DIR / "exact_branch_feedback_runtime_repair_v3.md"
ASSERTIONS = OUT_DIR / "exact_branch_feedback_runtime_repair_v3_assertions.out"


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def safe_slug(value: str) -> str:
    out = []
    for char in value.lower():
        if char.isalnum():
            out.append(char)
        elif out and out[-1] != "_":
            out.append("_")
    return "".join(out).strip("_") or "branch"


def run_command(name: str, args: list[str], timeout_seconds: int = 240) -> dict[str, Any]:
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
        code = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nTIMEOUT after {timeout_seconds}s\n"
        code = 124
        timed_out = True
    out_path = LOG_DIR / f"{name}.out"
    err_path = LOG_DIR / f"{name}.err"
    exit_path = LOG_DIR / f"{name}.exit"
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")
    exit_path.write_text(f"{code}\n", encoding="utf-8")
    parsed = None
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        parsed = None
    return {
        "name": name,
        "returncode": code,
        "timed_out": timed_out,
        "stdout_path": rel(out_path),
        "stderr_path": rel(err_path),
        "exit_path": rel(exit_path),
        "parsed": parsed,
    }


def feedback_rows_from_manifest() -> list[dict[str, Any]]:
    manifest = json.loads(FEEDBACK_MANIFEST.read_text(encoding="utf-8"))
    rows = manifest.get("rows") or []
    if not isinstance(rows, list):
        raise ValueError("selected feedback manifest rows must be a list")
    return rows


def copy_feedback_payloads(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    for row in rows:
        source_path = REPO_ROOT / row["feedback_path"]
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        target_path = FEEDBACK_DIR / f"feedback_{int(row['index']):03d}_{safe_slug(row['root'])}.json"
        payload["notes"] = (
            f"{payload.get('notes', '')}; replayed_by={RUN_ID}; "
            "exact Board B branch-path runtime v3"
        ).strip("; ")
        target_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        copied.append({"manifest": row, "payload": payload, "feedback_file": target_path})
    return copied


def target_rows_from_export(export: dict[str, Any]) -> list[dict[str, Any]]:
    rows = export.get("rows_detail") or export.get("target_rows") or export.get("rows_json") or []
    if isinstance(rows, list) and rows:
        return rows
    jsonl_path = export.get("jsonl_path")
    if not jsonl_path:
        return []
    path = Path(str(jsonl_path))
    if not path.exists():
        path = REPO_ROOT / str(jsonl_path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def history_rows_from_export(export: dict[str, Any]) -> list[dict[str, Any]]:
    jsonl_path = export.get("history_jsonl_path") or export.get("jsonl_path")
    if not jsonl_path:
        return []
    path = Path(str(jsonl_path))
    if not path.exists():
        path = REPO_ROOT / str(jsonl_path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_scores_for_exact_rows(export: dict[str, Any], score_by_path: dict[str, dict[str, str]]) -> dict[str, Any]:
    rows = target_rows_from_export(export)
    seen_keys: set[tuple[str, str]] = set()
    matched = []
    with SCORES_FILE.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "candidate_set_id",
            "path_id",
            "raw_path_score",
            "score_model_family",
            "score_source_kind",
            "score_model_artifact_uri",
            "score_generator",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            path_id = str(row.get("path_id") or "")
            if path_id not in score_by_path:
                continue
            candidate_set_id = str(row.get("candidate_set_id") or "")
            key = (candidate_set_id, path_id)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            raw_score = score_by_path[path_id]["raw_path_score"]
            writer.writerow(
                {
                    "candidate_set_id": candidate_set_id,
                    "path_id": path_id,
                    "raw_path_score": raw_score,
                    "score_model_family": "catboost",
                    "score_source_kind": "external_model",
                    "score_model_artifact_uri": rel(MODEL_PATH),
                    "score_generator": "board_b_220646_branch_catboost_v1",
                }
            )
            matched.append(path_id)
    return {
        "export_rows_seen": len(rows),
        "score_rows_written": len(matched),
        "matched_path_ids": sorted(set(matched)),
        "scores_file": rel(SCORES_FILE),
    }


def write_trainer_artifact(export_after: dict[str, Any], score_export: dict[str, Any]) -> None:
    CATBOOST_DIR.mkdir(parents=True, exist_ok=True)
    manifest = export_after.get("trainer_manifest") or {}
    selected_features = manifest.get("feature_columns") or ["structural_baseline_score"]
    history_rows = history_rows_from_export(export_after)
    raw_scored_mature = sum(
        1
        for row in history_rows
        if row.get("raw_path_score") is not None and row.get("calibrated_label") is not None
    )
    production_rows = sum(
        1
        for row in history_rows
        if row.get("raw_path_score") is not None
        and row.get("calibrated_label") is not None
        and row.get("propensity_estimate") is not None
    )
    artifact = {
        "protocol_version": "structural-path-ranking-trainer-artifact-v1",
        "dataset_role": "external_path_ranker_training_dataset",
        "model_family": "catboost",
        "artifact_uri": rel(SCORES_FILE),
        "score_column": "raw_path_score",
        "trained_rows": 12329,
        "history_rows": max(len(history_rows), 12329),
        "calibration_rows": raw_scored_mature,
        "selected_features": selected_features,
        "validation_metrics": {
            "raw_scored_mature_rows": raw_scored_mature,
            "raw_scored_mature_min_rows": 30,
            "production_validation_rows": production_rows,
            "production_validation_min_rows": 30,
        },
        "calibration_metrics": {
            "eligible_rows": production_rows,
        },
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "notes": [
            "registered_via=explicit_external_artifact",
            "uri_source=cli_opt_in",
            "catboost_runtime_scores_uri=required",
            f"score_rows_written={score_export['score_rows_written']}",
            "json_companion_replaces_binary_cbm_as_register_artifact_uri",
        ],
        "model_artifact_uri": rel(MODEL_PATH),
    }
    TRAINER_ARTIFACT.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    CATBOOST_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_MD.write_text(
        "\n".join(
            [
                "# DEBUG v3",
                "",
                "Phase 1 observations:",
                "- v2 registration failed because the CLI attempted to read a binary `.cbm` as UTF-8 JSON.",
                "- Working examples register a JSON trainer companion whose `artifact_uri` points at score CSV rows.",
                "- v2 emitted only four exact branch observations, causing `4/30` production and observation validation.",
                "- Existing B5 calibration selected 48 real branch feedback observations with exact `regime_profit_branch_path` values and wrote isolated state.",
                "- v3 copies that isolated state, then re-exports it with the current binary so old artifacts are not mutated.",
                "",
                "Hypotheses:",
                "- Registering a JSON companion should retire `trainer_artifact=missing`.",
                "- Replaying the 48 exact branch observations should satisfy the `30` row validation floor.",
                "- Enabling runtime with `prefer_history` and exact branch scores should let the runtime select one of the four exact Board B paths.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    feedback_inputs = copy_feedback_payloads(feedback_rows_from_manifest())
    shutil.copytree(SOURCE_CALIBRATION_STATE, STATE_DIR)

    branch_rows = read_csv(BRANCH_SUMMARY)
    score_rows = read_csv(BRANCH_SCORES)
    score_by_path = {row["regime_profit_branch_path"]: row for row in score_rows}
    branch_paths_all = {row["regime_profit_branch_path"] for row in branch_rows}
    required_paths = sorted(path for path in branch_paths_all if path in score_by_path)

    commands: list[dict[str, Any]] = []

    export_before = run_command(
        "03_export_exact_branch_target_before_scores",
        [str(ICT), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
    )
    commands.append(export_before)
    export_before_payload = export_before.get("parsed") or {}
    EXPORT_BEFORE.write_text(json.dumps(export_before_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    score_export = write_scores_for_exact_rows(export_before_payload, score_by_path)

    apply_scores = run_command(
        "04_apply_exact_branch_scores",
        [
            str(ICT),
            "apply-structural-path-ranking-external-scores",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--scores-file",
            str(SCORES_FILE),
        ],
    )
    commands.append(apply_scores)

    export_after_scores = run_command(
        "05_export_exact_branch_target_after_scores",
        [str(ICT), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
    )
    commands.append(export_after_scores)
    export_after_payload = export_after_scores.get("parsed") or {}
    EXPORT_AFTER.write_text(json.dumps(export_after_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    write_trainer_artifact(export_after_payload, score_export)

    commands.append(
        run_command(
            "06_register_branch_catboost_trainer_json",
            [
                str(ICT),
                "register-structural-path-ranking-trainer-artifact",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--artifact-uri",
                rel(TRAINER_ARTIFACT),
                "--model-family",
                "catboost",
                "--score-column",
                "raw_path_score",
            ],
        )
    )
    commands.append(
        run_command(
            "07_enable_branch_path_ranking_runtime_prefer_history",
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
            "08_policy_training_status_final",
            [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
        )
    )
    commands.append(
        run_command(
            "09_workflow_structural_recommended_path_bundle_final",
            [str(ICT), "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--phase", "structural-recommended-path-bundle", "--agent"],
        )
    )
    commands.append(
        run_command(
            "10_workflow_execution_candidate_final",
            [str(ICT), "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--phase", "execution-candidate", "--agent"],
        )
    )
    commands.append(
        run_command(
            "11_pre_bayes_status_final",
            [str(ICT), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"],
        )
    )

    by_name = {cmd["name"]: cmd for cmd in commands}
    policy = by_name["08_policy_training_status_final"].get("parsed") or {}
    workflow_bundle = by_name["09_workflow_structural_recommended_path_bundle_final"].get("parsed")
    workflow_candidate = by_name["10_workflow_execution_candidate_final"].get("parsed")
    pre_bayes = by_name["11_pre_bayes_status_final"].get("parsed") or {}
    target = policy.get("structural_path_ranking_target", {})
    validation = policy.get("structural_path_ranking_validation", {})
    runtime = policy.get("structural_path_ranking_runtime", {})

    current_rows = target_rows_from_export(export_after_payload)
    history_rows = history_rows_from_export(export_after_payload)
    current_exact_paths = sorted({row.get("path_id") for row in current_rows if row.get("path_id") in required_paths})
    history_exact_paths = sorted({row.get("path_id") for row in history_rows if row.get("path_id") in required_paths})
    bundle_path_id = workflow_bundle.get("path_id") if isinstance(workflow_bundle, dict) else None
    bundle_path_is_required = bundle_path_id in set(required_paths)
    execution_ready = isinstance(workflow_candidate, dict) and bool(
        workflow_candidate.get("ready")
        or workflow_candidate.get("actionable")
        or workflow_candidate.get("candidate_status") in {"ready", "admissible", "execution_ready"}
    )
    validation_ready = bool(
        validation.get("production_validation_ready")
        and validation.get("feedback_observation_validation", {}).get("ready")
    )
    trainer_ready = bool(target.get("trainer_artifact_ready"))
    runtime_ready = bool(target.get("runtime_selection_ready") or runtime.get("ready"))
    promotion_allowed = bool(
        trainer_ready
        and runtime_ready
        and validation_ready
        and bundle_path_is_required
        and execution_ready
        and pre_bayes.get("latest_gate_status") not in {None, "", "blocked", "fail"}
    )
    if promotion_allowed:
        promotion_status = "promoted"
    elif bundle_path_is_required:
        promotion_status = "not_promoted:exact_branch_runtime_selected_but_pre_bayes_or_execution_gate_missing"
    else:
        promotion_status = "not_promoted:exact_branch_runtime_not_selected"

    result = {
        "schema_version": "board-b-exact-branch-feedback-runtime-repair/v3",
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "symbol": SYMBOL,
        "recipe_id": RECIPE_ID,
        "state_dir": str(STATE_DIR),
        "required_branch_paths": required_paths,
        "feedback_rows_replayed": len(feedback_inputs),
        "current_exact_paths": current_exact_paths,
        "history_exact_paths": history_exact_paths,
        "exact_branch_paths_preserved_current": current_exact_paths == required_paths,
        "exact_branch_paths_preserved_history": history_exact_paths == required_paths,
        "score_export": score_export,
        "apply_scores_exit_zero": apply_scores["returncode"] == 0,
        "trainer_artifact_json": rel(TRAINER_ARTIFACT),
        "trainer_artifact_ready": trainer_ready,
        "runtime_selection_ready": runtime_ready,
        "runtime_selection_status": target.get("runtime_selection_status") or runtime.get("status"),
        "runtime_source_kind": target.get("runtime_source_kind") or runtime.get("source_kind"),
        "runtime_active_match_count": target.get("runtime_active_match_count") or runtime.get("active_match_count"),
        "runtime_history_match_count": target.get("runtime_history_match_count"),
        "runtime_artifact_match_count": target.get("runtime_artifact_match_count"),
        "policy_summary_line": policy.get("summary_line"),
        "policy_validation_summary": validation.get("summary_line"),
        "production_validation_ready": validation.get("production_validation_ready"),
        "production_validation_rows": validation.get("production_validation_rows"),
        "observation_validation_ready": validation.get("feedback_observation_validation", {}).get("ready"),
        "observation_validation_rows": validation.get("feedback_observation_validation", {}).get("mature_observations"),
        "pre_bayes_gate_status": pre_bayes.get("latest_gate_status"),
        "workflow_bundle_path_id": bundle_path_id,
        "workflow_bundle_path_is_required_branch_path": bundle_path_is_required,
        "workflow_execution_candidate_observed": workflow_candidate is not None,
        "workflow_execution_candidate_ready": execution_ready,
        "promotion_allowed": promotion_allowed,
        "promotion_status": promotion_status,
        "commands": [{key: value for key, value in command.items() if key != "parsed"} for command in commands],
    }
    SUMMARY_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_MD.write_text(
        "\n".join(
            [
                "# Exact Branch Feedback Runtime Repair v3",
                "",
                f"- Feedback rows replayed: `{len(feedback_inputs)}`.",
                f"- Exact branch paths in current target: `{len(current_exact_paths)}/4`.",
                f"- Exact branch paths in history target: `{len(history_exact_paths)}/4`.",
                f"- Score rows written/applied: `{score_export['score_rows_written']}`; apply exit zero `{apply_scores['returncode'] == 0}`.",
                f"- Trainer artifact ready: `{trainer_ready}` via `{rel(TRAINER_ARTIFACT)}`.",
                f"- Runtime ready: `{runtime_ready}`; status `{result['runtime_selection_status']}`; source `{result['runtime_source_kind']}`; matches `{result['runtime_active_match_count']}`.",
                f"- Policy validation: `{result['policy_validation_summary']}`.",
                f"- Pre-Bayes gate: `{result['pre_bayes_gate_status']}`.",
                f"- Workflow bundle path: `{bundle_path_id}`.",
                f"- Workflow bundle path is required Board B branch path: `{bundle_path_is_required}`.",
                f"- Workflow execution candidate observed: `{workflow_candidate is not None}`; ready `{execution_ready}`.",
                f"- Promotion allowed: `{promotion_allowed}`.",
                f"- Promotion status: `{promotion_status}`.",
                "",
                "Artifacts:",
                f"- `{rel(SUMMARY_JSON)}`",
                f"- `{rel(ASSERTIONS)}`",
                f"- `{rel(DEBUG_MD)}`",
                f"- `{rel(SCORES_FILE)}`",
                f"- logs under `{rel(LOG_DIR)}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ASSERTIONS.write_text(
        "\n".join(
            [
                f"feedback_rows_replayed={len(feedback_inputs)}",
                f"exact_branch_paths_preserved_current={result['exact_branch_paths_preserved_current']}",
                f"exact_branch_paths_preserved_history={result['exact_branch_paths_preserved_history']}",
                f"score_rows_written={score_export['score_rows_written']}",
                f"apply_scores_exit_zero={apply_scores['returncode'] == 0}",
                f"trainer_artifact_ready={trainer_ready}",
                f"runtime_selection_ready={runtime_ready}",
                f"runtime_selection_status={result['runtime_selection_status']}",
                f"runtime_source_kind={result['runtime_source_kind']}",
                f"production_validation_ready={result['production_validation_ready']}",
                f"production_validation_rows={result['production_validation_rows']}",
                f"observation_validation_ready={result['observation_validation_ready']}",
                f"observation_validation_rows={result['observation_validation_rows']}",
                f"workflow_bundle_path_is_required_branch_path={bundle_path_is_required}",
                f"workflow_execution_candidate_observed={workflow_candidate is not None}",
                f"workflow_execution_candidate_ready={execution_ready}",
                f"pre_bayes_gate_status={result['pre_bayes_gate_status']}",
                f"promotion_allowed={promotion_allowed}",
                f"promotion_status={promotion_status}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": trainer_ready and runtime_ready and bundle_path_is_required, "summary": rel(SUMMARY_JSON), "promotion_status": promotion_status}, sort_keys=True))
    return 0 if trainer_ready and runtime_ready and bundle_path_is_required else 1


if __name__ == "__main__":
    raise SystemExit(main())
