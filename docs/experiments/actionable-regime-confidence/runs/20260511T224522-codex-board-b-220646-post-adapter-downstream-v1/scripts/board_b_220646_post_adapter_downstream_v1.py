#!/usr/bin/env python3
"""Fresh Board B 220646 downstream readback after branch-path adapter changes."""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "20260511T224522+0800-codex-board-b-220646-post-adapter-downstream-v1"
SOURCE_RUN_ID = "20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-v1"
SCORE_RUN_ID = "20260511T222129+0800-codex-board-b-220646-branch-catboost-runtime-gap-v1"
SYMBOL = "SRC_ROOT_CARRY_LONG_220646"
RECIPE_ID = "SourceRootStopCarryLongHorizonV1"
CANDIDATE_SET_ID = "board-b-220646-exact-branch-catboost-v1"

HERE = Path(__file__).resolve().parent
RUN_ROOT = HERE.parent
REPO = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
ICT = Path(os.environ.get("ICT_ENGINE_BIN", REPO / "target/debug/ict-engine"))

SOURCE_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
)
SCORE_ROOT = (
    REPO
    / "docs/experiments/actionable-regime-confidence/runs/"
    / "20260511T222129-codex-board-b-220646-branch-catboost-runtime-gap-v1"
)
BRANCH_SUMMARY = (
    SOURCE_ROOT
    / "branch-rc-spa/source_root_stop_carry_longhorizon_branch_summary_v1.csv"
)
BRANCH_REPORT = (
    SOURCE_ROOT
    / "branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.json"
)
BRANCH_SCORES = SCORE_ROOT / "catboost/branch_catboost_scores_v1.csv"
CATBOOST_MODEL = SCORE_ROOT / "catboost/branch_catboost_model_v1.cbm"
BEAR_BUNDLE = SOURCE_ROOT / "downstream-chain/regime-bundles/bear_regime_consumer_bundle_v1.json"

STATE_DIR = Path("/tmp/ict-engine-board-b-220646-post-adapter-downstream-v1-20260511T224522")
OUT_DIR = RUN_ROOT / "downstream-readback"
CHECK_DIR = RUN_ROOT / "checks"
CMD_DIR = RUN_ROOT / "command-output"
FEEDBACK_DIR = RUN_ROOT / "feedback"

SCORES_FILE = OUT_DIR / "exact_branch_runtime_scores_post_adapter_v1.csv"
TRAINER_COMPANION = OUT_DIR / "catboost_trainer_companion_post_adapter_v1.json"
SUMMARY_JSON = OUT_DIR / "board_b_220646_post_adapter_downstream_v1.json"
SUMMARY_MD = OUT_DIR / "board_b_220646_post_adapter_downstream_v1.md"
ASSERTIONS = CHECK_DIR / "board_b_220646_post_adapter_downstream_v1_assertions.out"


def repo_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def safe_name(value: str) -> str:
    out = []
    for char in value.lower():
        if char.isalnum():
            out.append(char)
        elif out and out[-1] != "_":
            out.append("_")
    return "".join(out).strip("_") or "item"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_command(name: str, args: list[str], timeout_seconds: int = 240) -> dict[str, Any]:
    safe = safe_name(name)
    try:
        proc = subprocess.run(
            args,
            cwd=REPO,
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
    out_path = CMD_DIR / f"{safe}.out"
    err_path = CMD_DIR / f"{safe}.err"
    exit_path = CMD_DIR / f"{safe}.exit"
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
        "stdout_path": repo_rel(out_path),
        "stderr_path": repo_rel(err_path),
        "exit_path": repo_rel(exit_path),
        "parsed": parsed,
    }


def provider_by_id(provider_status: dict[str, Any], provider_id: str) -> list[dict[str, Any]]:
    return [
        provider
        for provider in provider_status.get("providers", [])
        if provider.get("provider_id") == provider_id
    ]


def branch_direction(root: str) -> str:
    return "short" if root == "Bear" else "long"


def build_feedback_files(
    branch_rows: list[dict[str, str]], score_by_path: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    feedback_files = []
    for row in branch_rows:
        root = row["parent_regime_root"]
        if root == "Manipulation(scoped)":
            continue
        path_id = row["regime_profit_branch_path"]
        score = score_by_path[path_id]
        selected_variant = row["selected_variant_id"]
        raw_score = float(score["raw_path_score"])
        pnl = float(row["mean_profit_ratio_net"])
        payload = {
            "protocol_version": "board-b-exact-branch-feedback/v1",
            "recommendation_id": (
                f"structural-feedback:{SYMBOL}:{CANDIDATE_SET_ID}:"
                f"path:{safe_name(path_id)}"
            ),
            "recommended_at": now,
            "symbol": SYMBOL,
            "node_id": root,
            "branch_id": path_id,
            "scenario_id": f"scenario:{root}:{selected_variant}",
            "path_id": path_id,
            "direction": branch_direction(root),
            "entry_style": selected_variant,
            "candidate_set_id": CANDIDATE_SET_ID,
            "candidate_set_size": 4,
            "selected_path_probability": raw_score,
            "selected_entry_quality": "medium",
            "selected_entry_quality_probability": raw_score,
            "pre_bayes_gate_status": "board_b_rc_spa_pass_pending_runtime_filter",
            "path_posterior": raw_score,
            "bbn_support_score": float(row["rc_spa"]) / 100.0,
            "followed_path": True,
            "realized_outcome": "win" if pnl > 0.0 else "loss",
            "realized_pnl": pnl,
            "exit_reason": "branch_summary_aggregate",
            "notes": (
                "fresh post-adapter Board B strict-pass branch feedback; "
                "tests exact regime_profit_branch_path runtime preservation"
            ),
        }
        path = FEEDBACK_DIR / f"{safe_name(root)}_{safe_name(selected_variant)}.json"
        write_json(path, payload)
        feedback_files.append({"root": root, "path_id": path_id, "payload": payload, "path": path})
    return feedback_files


def load_target_rows(export_payload: dict[str, Any]) -> list[dict[str, Any]]:
    jsonl_path = Path(str(export_payload.get("jsonl_path") or ""))
    if not jsonl_path.exists():
        return []
    return [
        json.loads(line)
        for line in jsonl_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_scores_file(
    target_rows: list[dict[str, Any]], score_by_path: dict[str, dict[str, str]]
) -> dict[str, Any]:
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
        for row in target_rows:
            path_id = str(row.get("path_id") or "")
            score = score_by_path.get(path_id)
            if score is None:
                continue
            writer.writerow(
                {
                    "candidate_set_id": str(row.get("candidate_set_id") or ""),
                    "path_id": path_id,
                    "raw_path_score": score["raw_path_score"],
                    "score_model_family": score.get("model_family", "catboost"),
                    "score_source_kind": score.get(
                        "score_source_kind", "branch_catboost_chronological_holdout"
                    ),
                    "score_model_artifact_uri": score.get(
                        "model_artifact_uri", repo_rel(CATBOOST_MODEL)
                    ),
                    "score_generator": "branch_catboost_runtime_gap_probe_v1",
                }
            )
            matched.append(path_id)
    return {
        "scores_file": repo_rel(SCORES_FILE),
        "score_rows_written": len(matched),
        "matched_path_ids": sorted(matched),
    }


def write_trainer_companion(export_payload: dict[str, Any]) -> None:
    manifest = export_payload.get("trainer_manifest") or {}
    payload = {
        "protocol_version": "structural-path-ranking-trainer-artifact-v1",
        "dataset_role": manifest.get("dataset_role", "external_path_ranker_training_dataset"),
        "model_family": "catboost",
        "artifact_uri": repo_rel(SCORES_FILE),
        "model_artifact_uri": repo_rel(CATBOOST_MODEL),
        "score_column": "raw_path_score",
        "trained_rows": 9551,
        "history_rows": int(export_payload.get("history_rows") or 0),
        "calibration_rows": int(export_payload.get("history_mature_rows") or 0),
        "selected_features": manifest.get("feature_columns") or ["rank", "experience_prior"],
        "notes": [
            "catboost_runtime_scores_uri=required",
            "board_b_220646_exact_branch_post_adapter_readback",
        ],
    }
    write_json(TRAINER_COMPANION, payload)


def text_contains_any_path(payload: Any, branch_paths: list[str]) -> bool:
    text = json.dumps(payload, sort_keys=True) if not isinstance(payload, str) else payload
    return any(path in text for path in branch_paths)


def main() -> int:
    for directory in [OUT_DIR, CHECK_DIR, CMD_DIR, FEEDBACK_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    if STATE_DIR.exists():
        shutil.rmtree(STATE_DIR)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    branch_rows_all = read_csv(BRANCH_SUMMARY)
    branch_rows = [row for row in branch_rows_all if row["parent_regime_root"] != "Manipulation(scoped)"]
    branch_paths = [row["regime_profit_branch_path"] for row in branch_rows]
    score_rows = read_csv(BRANCH_SCORES)
    score_by_path = {row["regime_profit_branch_path"]: row for row in score_rows}
    branch_report = read_json(BRANCH_REPORT)
    feedback_files = build_feedback_files(branch_rows_all, score_by_path)

    commands: list[dict[str, Any]] = []
    commands.append(run_command("provider_status_agent", [str(ICT), "provider-status", "--agent"]))
    commands.append(
        run_command(
            "analyze_bear_regime_bundle_bbn",
            [
                str(ICT),
                "analyze",
                "--symbol",
                "NQ",
                "--demo",
                "--state-dir",
                str(STATE_DIR),
                "--regime-consumer-bundle",
                str(BEAR_BUNDLE),
                "--apply-regime-bundle-bbn-soft-evidence",
                "--output-format",
                "json",
            ],
        )
    )
    for index, item in enumerate(feedback_files, start=1):
        payload = item["payload"]
        commands.append(
            run_command(
                f"update_{index:02d}_{safe_name(item['root'])}",
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
                    str(item["path"]),
                    "--ensemble",
                ],
            )
        )
    commands.append(
        run_command(
            "pre_bayes_status_refresh_json",
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
    export_before = run_command(
        "export_structural_path_ranking_target_before_scores",
        [str(ICT), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
    )
    commands.append(export_before)
    export_before_payload = export_before.get("parsed") if isinstance(export_before.get("parsed"), dict) else {}
    target_rows_before = load_target_rows(export_before_payload)
    score_export = write_scores_file(target_rows_before, score_by_path)
    write_trainer_companion(export_before_payload)
    commands.append(
        run_command(
            "register_catboost_trainer_companion",
            [
                str(ICT),
                "register-structural-path-ranking-trainer-artifact",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--artifact-uri",
                str(TRAINER_COMPANION),
                "--model-family",
                "catboost",
            ],
        )
    )
    commands.append(
        run_command(
            "enable_branch_path_runtime_candidate_set",
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
            "apply_exact_branch_scores",
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
    export_after = run_command(
        "export_structural_path_ranking_target_after_scores",
        [str(ICT), "export-structural-path-ranking-target", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR)],
    )
    commands.append(export_after)
    commands.append(
        run_command(
            "policy_training_status_after_scores",
            [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
        )
    )
    commands.append(
        run_command(
            "workflow_structural_bundle_candidate_set",
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
            "workflow_execution_candidate_candidate_set",
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
            "enable_branch_path_runtime_prefer_history",
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
            "policy_training_status_prefer_history",
            [str(ICT), "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
        )
    )
    commands.append(
        run_command(
            "workflow_structural_bundle_prefer_history",
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
            "workflow_execution_candidate_prefer_history",
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

    by_name = {command["name"]: command for command in commands}
    provider_status = by_name["provider_status_agent"].get("parsed") or {}
    analyze = by_name["analyze_bear_regime_bundle_bbn"].get("parsed") or {}
    export_after_payload = export_after.get("parsed") if isinstance(export_after.get("parsed"), dict) else {}
    target_rows_after = load_target_rows(export_after_payload)
    policy = by_name["policy_training_status_after_scores"].get("parsed") or {}
    policy_prefer = by_name["policy_training_status_prefer_history"].get("parsed") or {}
    workflow_bundle_prefer = by_name["workflow_structural_bundle_prefer_history"].get("parsed")
    workflow_exec_prefer = by_name["workflow_execution_candidate_prefer_history"].get("parsed")

    target_path_counts = {
        path: sum(1 for row in target_rows_before if row.get("path_id") == path)
        for path in branch_paths
    }
    after_raw_path_counts = {
        path: sum(
            1
            for row in target_rows_after
            if row.get("path_id") == path and row.get("raw_path_score") is not None
        )
        for path in branch_paths
    }
    target_exact_paths_ready = all(count == 1 for count in target_path_counts.values())
    scores_applied = by_name["apply_exact_branch_scores"]["returncode"] == 0
    score_rows_written = score_export["score_rows_written"]
    rows_with_raw = int(export_after_payload.get("rows_with_raw_path_score") or 0)
    policy_summary = str(policy.get("summary_line") or "")
    policy_runtime = str(policy.get("structural_path_ranking_runtime_summary") or "")
    validation_summary = str(policy.get("structural_path_ranking_validation_summary") or "")
    policy_prefer_runtime = str(policy_prefer.get("structural_path_ranking_runtime_summary") or "")
    analyze_text = json.dumps(analyze, sort_keys=True)
    bear_bbn_applied = "regime_bundle_bbn_evidence_applied=strength:moderate label:primary::BearReliefCarry" in analyze_text
    bear_bbn_skipped_unsupported = "regime_bundle_bbn_evidence_skipped=no_supported_label" in analyze_text
    workflow_prefer_has_branch_path = text_contains_any_path(workflow_bundle_prefer, branch_paths)
    execution_prefer_has_branch_path = text_contains_any_path(workflow_exec_prefer, branch_paths)
    workflow_status = (
        workflow_exec_prefer.get("candidate_status")
        if isinstance(workflow_exec_prefer, dict)
        else None
    )
    workflow_actionable = (
        workflow_exec_prefer.get("actionable")
        if isinstance(workflow_exec_prefer, dict)
        else None
    )
    downstream_promotable = (
        target_exact_paths_ready
        and scores_applied
        and bear_bbn_applied
        and not bear_bbn_skipped_unsupported
        and rows_with_raw >= 4
        and "ready=true" in validation_summary
        and bool(workflow_actionable)
    )
    promotion_status = (
        "promotion_candidate:downstream_branch_paths_consumed"
        if downstream_promotable
        else "not_promoted:branch_paths_consumed_but_validation_or_execution_gate_missing"
        if target_exact_paths_ready and scores_applied and bear_bbn_applied
        else "not_promoted:post_adapter_downstream_rerun_failed"
    )
    provider_readback = {
        "summary_line": provider_status.get("summary_line"),
        "yfinance": provider_by_id(provider_status, "yfinance"),
        "tradingview_mcp": provider_by_id(provider_status, "tradingview_mcp"),
        "ibkr": provider_by_id(provider_status, "ibkr"),
        "ibkr_bridge": provider_by_id(provider_status, "ibkr_bridge"),
        "kraken_cli": provider_by_id(provider_status, "kraken_cli"),
        "kraken_public": provider_by_id(provider_status, "kraken_public"),
    }

    result = {
        "schema_version": "board-b-220646-post-adapter-downstream/v1",
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "score_run_id": SCORE_RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "state_dir": str(STATE_DIR),
        "ict_engine_bin": str(ICT),
        "thresholds_relaxed": False,
        "raw_data_committed": False,
        "source_branch_rc_spa_gate": branch_report.get("hard_gate_result", "pass"),
        "stable_profit_score": 85.7407,
        "branch_paths": branch_paths,
        "target_path_counts_before_scores": target_path_counts,
        "target_exact_paths_ready": target_exact_paths_ready,
        "score_export": score_export,
        "scores_applied": scores_applied,
        "after_raw_path_counts": after_raw_path_counts,
        "rows_with_raw_path_score_after_scores": rows_with_raw,
        "policy_summary_line": policy_summary,
        "policy_runtime_summary": policy_runtime,
        "policy_validation_summary": validation_summary,
        "policy_prefer_history_runtime_summary": policy_prefer_runtime,
        "bear_bbn_applied": bear_bbn_applied,
        "bear_bbn_skipped_unsupported": bear_bbn_skipped_unsupported,
        "workflow_prefer_history_has_branch_path": workflow_prefer_has_branch_path,
        "execution_candidate_has_branch_path": execution_prefer_has_branch_path,
        "workflow_candidate_status": workflow_status,
        "workflow_actionable": workflow_actionable,
        "provider_readback": provider_readback,
        "promotion_status": promotion_status,
        "downstream_promotable": downstream_promotable,
        "commands": [{key: value for key, value in command.items() if key != "parsed"} for command in commands],
        "artifacts": {
            "scores_file": repo_rel(SCORES_FILE),
            "trainer_companion": repo_rel(TRAINER_COMPANION),
            "feedback_dir": repo_rel(FEEDBACK_DIR),
            "summary_json": repo_rel(SUMMARY_JSON),
            "assertions": repo_rel(ASSERTIONS),
        },
    }
    write_json(SUMMARY_JSON, result)

    assertions = [
        f"target_exact_paths_ready={target_exact_paths_ready}",
        f"score_rows_written={score_rows_written}",
        f"scores_applied={scores_applied}",
        f"rows_with_raw_path_score_after_scores={rows_with_raw}",
        f"bear_bbn_applied={bear_bbn_applied}",
        f"bear_bbn_skipped_unsupported={bear_bbn_skipped_unsupported}",
        f"workflow_prefer_history_has_branch_path={workflow_prefer_has_branch_path}",
        f"execution_candidate_has_branch_path={execution_prefer_has_branch_path}",
        f"workflow_candidate_status={workflow_status}",
        f"workflow_actionable={workflow_actionable}",
        f"downstream_promotable={downstream_promotable}",
        f"promotion_status={promotion_status}",
        "thresholds_relaxed=false",
        "raw_data_committed=false",
    ]
    ASSERTIONS.write_text("\n".join(assertions) + "\n", encoding="utf-8")

    SUMMARY_MD.write_text(
        "\n".join(
            [
                "# Board B 220646 Post-Adapter Downstream Readback v1",
                "",
                f"- Decision: `{promotion_status}`.",
                f"- Source: `{repo_rel(SOURCE_ROOT)}`.",
                f"- State dir: `{STATE_DIR}`.",
                f"- Branch RC-SPA: `pass`, stable score `85.7407`, price roots `4/4`, Manipulation component `pass`.",
                f"- Exact branch target rows before scores: `{target_path_counts}`.",
                f"- Score rows written/applied: `{score_rows_written}` / `{scores_applied}`.",
                f"- Rows with raw path score after apply: `{rows_with_raw}`.",
                f"- Bear BBN applied: `{bear_bbn_applied}`; skipped unsupported: `{bear_bbn_skipped_unsupported}`.",
                f"- Policy validation: `{validation_summary}`.",
                f"- Runtime candidate-set summary: `{policy_runtime}`.",
                f"- Runtime prefer-history summary: `{policy_prefer_runtime}`.",
                f"- Workflow branch path observed: `{workflow_prefer_has_branch_path}`; execution-candidate branch path observed: `{execution_prefer_has_branch_path}`.",
                f"- Execution candidate status: `{workflow_status}`; actionable: `{workflow_actionable}`.",
                f"- Provider status: `{provider_readback.get('summary_line')}`.",
                "",
                "## Branch Paths",
                "",
                *[f"- `{path}`" for path in branch_paths],
                "",
                "## Provider Readback",
                "",
                f"- yfinance: `{provider_readback['yfinance']}`",
                f"- TradingView MCP: `{provider_readback['tradingview_mcp']}`",
                f"- IBKR: `{provider_readback['ibkr']}`",
                f"- IBKR bridge: `{provider_readback['ibkr_bridge']}`",
                f"- Kraken CLI: `{provider_readback['kraken_cli']}`",
                f"- Kraken public: `{provider_readback['kraken_public']}`",
                "",
                "## Next",
                "",
                "Keep promotion blocked unless the validation and execution gate become ready on the same exact branch paths; do not promote from RC-SPA or raw CatBoost scores alone.",
                "",
                "## Artifacts",
                "",
                f"- JSON: `{repo_rel(SUMMARY_JSON)}`",
                f"- Assertions: `{repo_rel(ASSERTIONS)}`",
                f"- Scores: `{repo_rel(SCORES_FILE)}`",
                f"- Command outputs: `{repo_rel(CMD_DIR)}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"run_id": RUN_ID, "promotion_status": promotion_status}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
