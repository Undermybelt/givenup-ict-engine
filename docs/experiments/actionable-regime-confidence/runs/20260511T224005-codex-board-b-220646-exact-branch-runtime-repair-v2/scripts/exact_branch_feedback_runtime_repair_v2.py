#!/usr/bin/env python3
"""Probe exact Board B branch paths through structural feedback runtime state."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T224005+0800-codex-board-b-220646-exact-branch-runtime-repair-v2"
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

OUT_DIR = RUN_ROOT / "ict-engine-exact-branch-feedback-repair-v2"
FEEDBACK_DIR = OUT_DIR / "feedback"
LOG_DIR = OUT_DIR / "logs"
STATE_DIR = OUT_DIR / "state_exact_branch_feedback_v2"
EXPORT_BEFORE = OUT_DIR / "exact_branch_target_export_before_scores_v2.json"
SCORES_FILE = OUT_DIR / "exact_branch_runtime_scores_v2.csv"
SUMMARY_JSON = OUT_DIR / "exact_branch_feedback_runtime_repair_v2.json"
SUMMARY_MD = OUT_DIR / "exact_branch_feedback_runtime_repair_v2.md"
ASSERTIONS = OUT_DIR / "exact_branch_feedback_runtime_repair_v2_assertions.out"


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


def run_command(name: str, args: list[str], timeout_seconds: int = 180) -> dict[str, Any]:
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


def build_feedback_files(branch_rows: list[dict[str, str]], score_by_path: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    built: list[dict[str, Any]] = []
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    for row in branch_rows:
        path_id = row["regime_profit_branch_path"]
        if path_id not in score_by_path:
            continue
        score = score_by_path[path_id]
        root = row["parent_regime_root"]
        selected_variant = row["selected_variant_id"]
        mean_pnl = float(row["mean_profit_ratio_net"])
        raw_score = float(score["raw_path_score"])
        realized_outcome = "win" if mean_pnl > 0.0 else "loss"
        payload = {
            "protocol_version": "board-b-exact-branch-feedback/v1",
            "recommendation_id": f"board-b-220646:{root}:{selected_variant}",
            "recommended_at": now,
            "symbol": SYMBOL,
            "node_id": root,
            "branch_id": path_id,
            "scenario_id": f"scenario:{root}:{selected_variant}",
            "path_id": path_id,
            "direction": "long" if root in {"Bull", "Sideways", "Crisis"} else "short",
            "entry_style": selected_variant,
            "candidate_set_id": SOURCE_RUN_ID,
            "candidate_set_size": len(branch_rows),
            "selected_path_probability": raw_score,
            "selected_entry_quality": "medium",
            "selected_entry_quality_probability": raw_score,
            "pre_bayes_gate_status": "board_b_rc_spa_pass_pending_runtime_filter",
            "path_posterior": raw_score,
            "bbn_support_score": float(row["rc_spa"]) / 100.0,
            "followed_path": True,
            "realized_outcome": realized_outcome,
            "realized_pnl": mean_pnl,
            "exit_reason": "branch_summary_aggregate",
            "notes": (
                "aggregate Board B strict-pass branch feedback; "
                "used only to test exact regime_profit_branch_path runtime preservation"
            ),
        }
        path = FEEDBACK_DIR / f"{safe_slug(root)}_{safe_slug(selected_variant)}.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        built.append({"root": root, "path_id": path_id, "feedback_file": path, "payload": payload})
    return built


def write_scores_for_export(export: dict[str, Any], score_by_path: dict[str, dict[str, str]]) -> dict[str, Any]:
    rows = export.get("rows_detail") or export.get("target_rows") or export.get("rows_json") or []
    if not isinstance(rows, list):
        rows = []
    # The command output summary does not embed row detail on this build; read JSONL if needed.
    if not rows and export.get("jsonl_path"):
        jsonl_path = Path(export["jsonl_path"])
        if jsonl_path.exists():
            rows = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    matched = []
    with SCORES_FILE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["candidate_set_id", "path_id", "raw_path_score"])
        writer.writeheader()
        for row in rows:
            path_id = str(row.get("path_id") or "")
            if path_id not in score_by_path:
                continue
            candidate_set_id = str(row.get("candidate_set_id") or export.get("candidate_set_id") or "")
            raw_score = score_by_path[path_id]["raw_path_score"]
            writer.writerow(
                {
                    "candidate_set_id": candidate_set_id,
                    "path_id": path_id,
                    "raw_path_score": raw_score,
                }
            )
            matched.append(path_id)
    return {
        "export_rows_seen": len(rows),
        "score_rows_written": len(matched),
        "matched_path_ids": sorted(matched),
        "scores_file": rel(SCORES_FILE),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    branch_rows = read_csv(BRANCH_SUMMARY)
    score_rows = read_csv(BRANCH_SCORES)
    score_by_path = {row["regime_profit_branch_path"]: row for row in score_rows}
    branch_paths_all = {row["regime_profit_branch_path"] for row in branch_rows}
    branch_paths = branch_paths_all & set(score_by_path)
    missing_scores = sorted(branch_paths_all - set(score_by_path))
    feedback_files = build_feedback_files(branch_rows, score_by_path)

    commands: list[dict[str, Any]] = []
    for idx, item in enumerate(feedback_files, start=1):
        payload = item["payload"]
        commands.append(
            run_command(
                f"{idx:02d}_update_{safe_slug(item['root'])}",
                [
                    str(ICT),
                    "update",
                    "--symbol",
                    SYMBOL,
                    "--state-dir",
                    str(STATE_DIR),
                    "--outcome",
                    payload["realized_outcome"],
                    "--entry-signal",
                    payload["entry_style"],
                    "--pnl",
                    str(payload["realized_pnl"]),
                    "--regime",
                    item["root"],
                    "--direction",
                    payload["direction"],
                    "--feedback-file",
                    str(item["feedback_file"]),
                    "--ensemble",
                ],
            )
        )

    export_before = run_command(
        "05_export_exact_branch_target_before_scores",
        [str(ICT), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
    )
    commands.append(export_before)
    export_payload = export_before.get("parsed") or {}
    EXPORT_BEFORE.write_text(json.dumps(export_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    score_export = write_scores_for_export(export_payload, score_by_path)

    commands.append(
        run_command(
            "06_register_branch_catboost_artifact",
            [
                str(ICT),
                "register-structural-path-ranking-trainer-artifact",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--artifact-uri",
                rel(MODEL_PATH),
                "--model-family",
                "catboost",
                "--trained-rows",
                "9551",
                "--calibration-rows",
                "2778",
            ],
        )
    )
    commands.append(
        run_command(
            "07_enable_branch_path_ranking_runtime",
            [
                str(ICT),
                "enable-structural-path-ranking-runtime",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--reuse-mode",
                "candidate_set_only",
            ],
        )
    )
    commands.append(
        run_command(
            "08_apply_exact_branch_scores",
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
    )
    commands.append(
        run_command(
            "09_export_exact_branch_target_after_scores",
            [str(ICT), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
        )
    )
    commands.append(
        run_command(
            "10_policy_training_status_after_scores",
            [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
        )
    )
    commands.append(
        run_command(
            "11_workflow_execution_candidate_after_scores",
            [str(ICT), "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--phase", "execution-candidate", "--agent"],
        )
    )
    commands.append(
        run_command(
            "12_pre_bayes_status_after_scores",
            [str(ICT), "pre-bayes-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"],
        )
    )

    by_name = {cmd["name"]: cmd for cmd in commands}
    export_after = by_name["09_export_exact_branch_target_after_scores"].get("parsed") or {}
    policy = by_name["10_policy_training_status_after_scores"].get("parsed") or {}
    workflow = by_name["11_workflow_execution_candidate_after_scores"].get("parsed")
    pre_bayes = by_name["12_pre_bayes_status_after_scores"].get("parsed") or {}
    target = policy.get("structural_path_ranking_target", {})
    validation = policy.get("structural_path_ranking_validation", {})

    exact_paths_preserved = score_export["score_rows_written"] == len(branch_paths)
    apply_exit_zero = by_name["08_apply_exact_branch_scores"]["returncode"] == 0
    rows_with_raw = int(export_after.get("rows_with_raw_path_score") or target.get("rows_with_raw_path_score") or 0)
    runtime_ready = bool(
        target.get("runtime_selection_ready")
        or "runtime_selection=enabled" in str(policy.get("summary_line") or "")
        or "runtime_selection=enabled" in str(policy.get("structural_path_ranking_runtime_summary") or "")
    )
    promotion_status = (
        "not_promoted:exact_branch_paths_preserved_scores_applied_but_validation_or_execution_gate_missing"
        if exact_paths_preserved and apply_exit_zero
        else "not_promoted:exact_branch_path_runtime_repair_failed"
    )

    result = {
        "schema_version": "board-b-exact-branch-feedback-runtime-repair/v1",
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "symbol": SYMBOL,
        "state_dir": str(STATE_DIR),
        "branch_paths": sorted(branch_paths),
        "missing_scores": missing_scores,
        "feedback_files": [{"root": item["root"], "path_id": item["path_id"], "feedback_file": rel(item["feedback_file"])} for item in feedback_files],
        "score_export": score_export,
        "exact_branch_paths_preserved": exact_paths_preserved,
        "apply_scores_exit_zero": apply_exit_zero,
        "export_rows_after_scores": export_after.get("rows"),
        "rows_with_raw_path_score_after_scores": rows_with_raw,
        "policy_runtime_ready": runtime_ready,
        "policy_summary_line": policy.get("summary_line"),
        "policy_validation_summary": (validation or {}).get("summary_line"),
        "pre_bayes_gate_status": pre_bayes.get("latest_gate_status"),
        "workflow_execution_candidate_observed": workflow is not None,
        "workflow_actionable": workflow.get("actionable") if isinstance(workflow, dict) else None,
        "workflow_candidate_status": workflow.get("candidate_status") if isinstance(workflow, dict) else None,
        "promotion_status": promotion_status,
        "commands": [{key: value for key, value in command.items() if key != "parsed"} for command in commands],
    }
    SUMMARY_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_MD.write_text(
        "\n".join(
            [
                "# Exact Branch Feedback Runtime Repair v1",
                "",
                f"- Feedback paths emitted: `{len(feedback_files)}`.",
                f"- Exact branch paths preserved into exported target: `{exact_paths_preserved}`.",
                f"- Score rows written/applied: `{score_export['score_rows_written']}`; apply exit zero `{apply_exit_zero}`.",
                f"- Rows with raw path score after apply: `{rows_with_raw}`.",
                f"- Policy runtime ready: `{runtime_ready}`.",
                f"- Policy validation: `{result['policy_validation_summary']}`.",
                f"- Pre-Bayes gate: `{result['pre_bayes_gate_status']}`.",
                f"- Workflow candidate observed: `{result['workflow_execution_candidate_observed']}`; actionable `{result['workflow_actionable']}`; status `{result['workflow_candidate_status']}`.",
                f"- Promotion status: `{promotion_status}`.",
                "",
                "Artifacts:",
                f"- `{rel(SUMMARY_JSON)}`",
                f"- `{rel(ASSERTIONS)}`",
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
                f"exact_branch_paths_preserved={exact_paths_preserved}",
                f"score_rows_written={score_export['score_rows_written']}",
                f"apply_scores_exit_zero={apply_exit_zero}",
                f"rows_with_raw_path_score_after_scores={rows_with_raw}",
                f"policy_runtime_ready={runtime_ready}",
                f"workflow_execution_candidate_observed={result['workflow_execution_candidate_observed']}",
                f"promotion_status={promotion_status}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": exact_paths_preserved and apply_exit_zero, "summary": rel(SUMMARY_JSON), "promotion_status": promotion_status}, sort_keys=True))
    return 0 if exact_paths_preserved and apply_exit_zero else 1


if __name__ == "__main__":
    raise SystemExit(main())
