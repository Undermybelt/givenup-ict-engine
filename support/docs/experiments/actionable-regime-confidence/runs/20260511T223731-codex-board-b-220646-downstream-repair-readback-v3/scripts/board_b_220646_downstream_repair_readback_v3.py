#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T223731-codex-board-b-220646-downstream-repair-readback-v3"
SOURCE_RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
GAP_RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T222129-codex-board-b-220646-branch-catboost-runtime-gap-v1"

CMD_DIR = RUN_ROOT / "command-output"
OUT_DIR = RUN_ROOT / "downstream-repair-readback"
CHECK_DIR = RUN_ROOT / "checks"
STATE_DIR = RUN_ROOT / "state"
EXACT_STATE_SRC = GAP_RUN_ROOT / "ict-engine-exact-branch-feedback-repair/state_exact_branch_feedback_v1"
EXACT_STATE_COPY = STATE_DIR / "state_exact_branch_feedback_readback_v3"
BEAR_PROBE_STATE = STATE_DIR / "root-probe-bear-current-bin"

ICT_ENGINE = REPO / "target/debug/ict-engine"
BEAR_BUNDLE = SOURCE_RUN_ROOT / "downstream-chain/regime-bundles/bear_regime_consumer_bundle_v1.json"
NQ_RUNTIME_TARGET = Path("/tmp/ict-engine-board-b-source-root-stop-carry-longhorizon-downstream-v1/NQ/policy_training/structural_path_ranking_target.csv")
NQ_RUNTIME_SCORES = SOURCE_RUN_ROOT / "downstream-chain/catboost/path_ranker_scores_for_ict_engine_v1.csv"
BRANCH_SCORES = GAP_RUN_ROOT / "catboost/branch_catboost_scores_v1.csv"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"


def repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_cmd(name: str, args: list[str]) -> dict[str, Any]:
    stdout_path = CMD_DIR / f"{name}.out"
    stderr_path = CMD_DIR / f"{name}.err"
    exit_path = CMD_DIR / f"{name}.exit"
    proc = subprocess.run(args, cwd=REPO, text=True, capture_output=True, check=False)
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed = None
    if proc.stdout.strip().startswith(("{", "[")):
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = None
    return {
        "name": name,
        "cmd": " ".join(args),
        "returncode": proc.returncode,
        "stdout_path": repo_rel(stdout_path),
        "stderr_path": repo_rel(stderr_path),
        "exit_path": repo_rel(exit_path),
        "parsed": parsed,
    }


def flatten_strings(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        found.append(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            found.append(str(key))
            found.extend(flatten_strings(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(flatten_strings(item))
    return found


def count_exact(rows: list[dict[str, str]], exact_paths: set[str]) -> int:
    return sum(1 for row in rows if row.get("path_id") in exact_paths or row.get("regime_profit_branch_path") in exact_paths)


def main() -> int:
    for directory in [CMD_DIR, OUT_DIR, CHECK_DIR, STATE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    if EXACT_STATE_COPY.exists():
        shutil.rmtree(EXACT_STATE_COPY)
    shutil.copytree(EXACT_STATE_SRC, EXACT_STATE_COPY)
    if BEAR_PROBE_STATE.exists():
        shutil.rmtree(BEAR_PROBE_STATE)

    branch_score_rows = read_csv(BRANCH_SCORES)
    exact_scores = {
        row["regime_profit_branch_path"]: row["raw_path_score"]
        for row in branch_score_rows
        if row.get("regime_profit_branch_path") and row.get("raw_path_score")
    }
    exact_paths = set(exact_scores)

    commands: list[dict[str, Any]] = []
    commands.append(
        run_cmd(
            "01_analyze_demo_bear_bundle_current_bin",
            [
                str(ICT_ENGINE),
                "analyze",
                "--symbol",
                "NQ",
                "--demo",
                "--state-dir",
                str(BEAR_PROBE_STATE),
                "--regime-consumer-bundle",
                str(BEAR_BUNDLE),
                "--regime-consumer-bundle-strict",
                "--apply-regime-bundle-bbn-soft-evidence",
                "--output-format",
                "json",
            ],
        )
    )
    bear_payload = commands[-1].get("parsed") or {}
    bear_strings = flatten_strings(bear_payload)
    bear_bbn_applied = any("regime_bundle_bbn_evidence_applied" in item for item in bear_strings)
    bear_bbn_skipped_no_supported_label = any("regime_bundle_bbn_evidence_skipped=no_supported_label" in item for item in bear_strings)
    bear_market_label_observed = any("regime_bundle_bbn_market_regime" in item or item == "bear" for item in bear_strings)

    commands.append(
        run_cmd(
            "02_export_exact_feedback_target_current_rows",
            [
                str(ICT_ENGINE),
                "export-structural-path-ranking-target",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(EXACT_STATE_COPY),
            ],
        )
    )
    exact_target_csv = EXACT_STATE_COPY / SYMBOL / "policy_training/structural_path_ranking_target.csv"
    exact_target_rows_before = read_csv(exact_target_csv)
    exact_rows_before = [row for row in exact_target_rows_before if row.get("path_id") in exact_paths]

    score_rows = [
        {
            "candidate_set_id": row["candidate_set_id"],
            "path_id": row["path_id"],
            "raw_path_score": exact_scores[row["path_id"]],
        }
        for row in exact_rows_before
        if row.get("path_id") in exact_scores
    ]
    exact_runtime_scores = OUT_DIR / "exact_branch_runtime_scores_v3.csv"
    write_csv(exact_runtime_scores, score_rows, ["candidate_set_id", "path_id", "raw_path_score"])

    commands.append(
        run_cmd(
            "03_apply_exact_branch_scores_current_rows",
            [
                str(ICT_ENGINE),
                "apply-structural-path-ranking-external-scores",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(EXACT_STATE_COPY),
                "--scores-file",
                str(exact_runtime_scores),
            ],
        )
    )
    commands.append(
        run_cmd(
            "04_enable_runtime_prefer_history_exact_feedback",
            [
                str(ICT_ENGINE),
                "enable-structural-path-ranking-runtime",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(EXACT_STATE_COPY),
                "--reuse-mode",
                "prefer_history",
            ],
        )
    )
    commands.append(
        run_cmd(
            "05_policy_training_status_exact_feedback",
            [
                str(ICT_ENGINE),
                "policy-training-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(EXACT_STATE_COPY),
                "--output-format",
                "json",
            ],
        )
    )
    commands.append(
        run_cmd(
            "06_workflow_status_execution_candidate_exact_feedback",
            [
                str(ICT_ENGINE),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(EXACT_STATE_COPY),
                "--phase",
                "execution-candidate",
                "--agent",
            ],
        )
    )

    exact_target_rows_after = read_csv(exact_target_csv)
    exact_rows_after = [row for row in exact_target_rows_after if row.get("path_id") in exact_paths]
    nq_runtime_rows = read_csv(NQ_RUNTIME_TARGET)
    nq_runtime_scores = read_csv(NQ_RUNTIME_SCORES)
    nq_exact_rows = [row for row in nq_runtime_rows if row.get("path_id") in exact_paths]
    nq_generic_score_rows = [
        row for row in nq_runtime_scores if row.get("candidate_set_id", "").startswith("structural-candidates:NQ:")
    ]
    nq_board_b_score_rows = [row for row in nq_runtime_scores if row.get("path_id") in exact_paths]

    structural_bijection_status = "fail_closed:no_exact_bijection_in_nq_runtime_target"
    if len(nq_runtime_rows) == len(exact_paths) and len(nq_exact_rows) == len(exact_paths):
        structural_bijection_status = "pass:exact_runtime_rows_present"

    apply_exit = next((cmd["returncode"] for cmd in commands if cmd["name"] == "03_apply_exact_branch_scores_current_rows"), None)
    export_exit = next((cmd["returncode"] for cmd in commands if cmd["name"] == "02_export_exact_feedback_target_current_rows"), None)

    command_index = [
        {key: value for key, value in command.items() if key != "parsed"}
        for command in commands
    ]

    summary = {
        "run_id": "20260511T223731+0800-codex-board-b-220646-downstream-repair-readback-v3",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_candidate": "SourceRootStopCarryLongHorizonV1",
        "source_run_root": repo_rel(SOURCE_RUN_ROOT),
        "runtime_code_changed_by_this_run": False,
        "thresholds_relaxed": False,
        "bear_bbn_repair_observed": {
            "analyze_exit": commands[0]["returncode"],
            "bbn_evidence_applied": bear_bbn_applied,
            "skipped_no_supported_label": bear_bbn_skipped_no_supported_label,
            "market_label_bear_observed": bear_market_label_observed,
            "bundle": repo_rel(BEAR_BUNDLE),
        },
        "exact_feedback_target_repair_observed_on_copied_state": {
            "state_dir": repo_rel(EXACT_STATE_COPY),
            "export_exit": export_exit,
            "current_rows_before_apply": len(exact_target_rows_before),
            "exact_branch_rows_before_apply": len(exact_rows_before),
            "score_rows_written": len(score_rows),
            "apply_scores_exit": apply_exit,
            "current_rows_after_apply": len(exact_target_rows_after),
            "exact_branch_rows_after_apply": len(exact_rows_after),
            "exact_branch_paths": sorted(exact_paths),
            "scores_file": repo_rel(exact_runtime_scores),
        },
        "nq_runtime_target_bijection_audit": {
            "runtime_target_csv": str(NQ_RUNTIME_TARGET),
            "runtime_target_rows": len(nq_runtime_rows),
            "exact_board_b_rows": len(nq_exact_rows),
            "branch_path_count": len(exact_paths),
            "generic_score_rows": len(nq_generic_score_rows),
            "board_b_score_rows_in_scores_file": len(nq_board_b_score_rows),
            "runtime_path_ids": [row.get("path_id", "") for row in nq_runtime_rows],
            "status": structural_bijection_status,
            "reason": "NQ runtime target exposes generic belief_regime_node paths, while exact Board B branch paths exist only as nonmatching score rows unless feedback rows are surfaced in current export.",
        },
        "promotion_status": "not_promoted:execution_tree_closed_loop_confidence_still_missing",
        "next_action": "Rerun B5 downstream on a state where exact Board B feedback rows are surfaced in the current structural target, then require Pre-Bayes, BBN, CatBoost/path-ranker, and execution tree to emit the same exact branch paths before promotion.",
        "commands": command_index,
    }
    write_json(OUT_DIR / "board_b_220646_downstream_repair_readback_v3.json", summary)

    assertions = [
        f"bear_bbn_applied={bear_bbn_applied}",
        f"bear_bbn_skipped_no_supported_label={bear_bbn_skipped_no_supported_label}",
        f"exact_feedback_current_rows_before_apply={len(exact_target_rows_before)}",
        f"exact_feedback_exact_branch_rows_before_apply={len(exact_rows_before)}",
        f"exact_branch_score_rows_written={len(score_rows)}",
        f"exact_branch_apply_exit={apply_exit}",
        f"nq_runtime_exact_board_b_rows={len(nq_exact_rows)}",
        f"nq_runtime_branch_path_count={len(exact_paths)}",
        f"structural_bijection_status={structural_bijection_status}",
        "promotion_allowed=false",
    ]
    (CHECK_DIR / "board_b_220646_downstream_repair_readback_v3_assertions.out").write_text(
        "\n".join(assertions) + "\n",
        encoding="utf-8",
    )

    md_lines = [
        "# Board B 220646 Downstream Repair Readback v3",
        "",
        "- Decision: `not_promoted:execution_tree_closed_loop_confidence_still_missing`",
        f"- Bear BBN current binary: applied `{bear_bbn_applied}`, skipped-no-supported-label `{bear_bbn_skipped_no_supported_label}`",
        f"- Exact feedback export copy: current rows `{len(exact_target_rows_before)}`, exact Board B rows `{len(exact_rows_before)}`, score rows `{len(score_rows)}`, apply exit `{apply_exit}`",
        f"- NQ runtime target: rows `{len(nq_runtime_rows)}`, exact Board B rows `{len(nq_exact_rows)}`, branch paths `{len(exact_paths)}`, status `{structural_bijection_status}`",
        "- Promotion: blocked until the actual B5 downstream state emits exact branch paths through Pre-Bayes, BBN, CatBoost/path-ranker, and execution tree.",
        "",
        "## Runtime Path IDs",
        "",
    ]
    md_lines.extend(f"- `{row.get('path_id', '')}`" for row in nq_runtime_rows)
    md_lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: `{repo_rel(OUT_DIR / 'board_b_220646_downstream_repair_readback_v3.json')}`",
            f"- Exact score file: `{repo_rel(exact_runtime_scores)}`",
            f"- Assertions: `{repo_rel(CHECK_DIR / 'board_b_220646_downstream_repair_readback_v3_assertions.out')}`",
            f"- Command outputs: `{repo_rel(CMD_DIR)}`",
        ]
    )
    (OUT_DIR / "board_b_220646_downstream_repair_readback_v3.md").write_text(
        "\n".join(md_lines) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
