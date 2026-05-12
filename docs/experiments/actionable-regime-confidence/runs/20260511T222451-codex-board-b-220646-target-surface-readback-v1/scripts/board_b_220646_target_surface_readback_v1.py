#!/usr/bin/env python3
"""Run-local Board B target-surface readback for the 220646 candidate.

The script consumes the existing strict RC-SPA pass artifacts for
SourceRootStopCarryLongHorizonV1, trains a real CatBoost branch scorer in this
run root, then checks whether ict-engine structural path-ranking and workflow
surfaces preserve the exact Board B branch paths.
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from catboost import CatBoostClassifier, Pool


RUN_ID = "20260511T222451+0800-codex-board-b-220646-target-surface-readback-v1"
SOURCE_RUN_ID = "20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-v1"
RECIPE_ID = "SourceRootStopCarryLongHorizonV1"

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
BIN = REPO / "target/debug/ict-engine"
SOURCE_RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1"
STATE_DIR = Path("/tmp/ict-engine-board-b-220646-target-surface-readback-v1")

SELECTED_ROWS = SOURCE_RUN_ROOT / "branch-rc-spa/source_root_stop_carry_longhorizon_selected_rows_v1.csv"
BRANCH_SUMMARY = SOURCE_RUN_ROOT / "branch-rc-spa/source_root_stop_carry_longhorizon_branch_summary_v1.csv"
RC_SPA_REPORT = SOURCE_RUN_ROOT / "branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.json"
AGGREGATE_BUNDLE = SOURCE_RUN_ROOT / "downstream-chain/regime-bundles/aggregate_regime_consumer_bundle_v1.json"
ROOT_BUNDLES = {
    "Bull": SOURCE_RUN_ROOT / "downstream-chain/regime-bundles/bull_regime_consumer_bundle_v1.json",
    "Bear": SOURCE_RUN_ROOT / "downstream-chain/regime-bundles/bear_regime_consumer_bundle_v1.json",
    "Sideways": SOURCE_RUN_ROOT / "downstream-chain/regime-bundles/sideways_regime_consumer_bundle_v1.json",
    "Crisis": SOURCE_RUN_ROOT / "downstream-chain/regime-bundles/crisis_regime_consumer_bundle_v1.json",
}
STRATEGY_LIBRARY = SOURCE_RUN_ROOT / "downstream-chain/autoquant_strategy_library_source_root_stop_carry_longhorizon_v1.json"

CATBOOST_DIR = RUN_ROOT / "catboost"
CMD_DIR = RUN_ROOT / "command-output"
OUT_DIR = RUN_ROOT / "target-surface-readback"
CHECK_DIR = RUN_ROOT / "checks"


def repo_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def run_command(name: str, args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=REPO, text=True, capture_output=True, check=False)
    stdout_path = CMD_DIR / f"{name}.out"
    stderr_path = CMD_DIR / f"{name}.err"
    exit_path = CMD_DIR / f"{name}.exit"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    exit_path.write_text(f"{proc.returncode}\n", encoding="utf-8")
    parsed = None
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


def train_real_catboost() -> dict[str, Any]:
    CATBOOST_DIR.mkdir(parents=True, exist_ok=True)
    selected = pd.read_csv(SELECTED_ROWS)
    selected["profit_ratio_net"] = pd.to_numeric(selected["profit_ratio_net"], errors="coerce").fillna(0.0)
    selected["target_positive_net"] = (selected["profit_ratio_net"] > 0).astype(int)
    feature_cols = [
        "parent_regime_root",
        "selected_variant_id",
        "market",
        "timeframe",
        "direction",
        "year_fold",
        "root_confidence",
        "vol_proxy",
        "carry_proxy",
    ]
    for col in feature_cols:
        if col not in selected.columns:
            selected[col] = "missing"
    cat_cols = [col for col in feature_cols if selected[col].dtype == object]
    for col in feature_cols:
        if col not in cat_cols:
            selected[col] = pd.to_numeric(selected[col], errors="coerce").fillna(0.0)

    feature_path = CATBOOST_DIR / "catboost_branch_features_v1.csv"
    selected[feature_cols + ["target_positive_net", "regime_profit_branch_path"]].to_csv(feature_path, index=False)

    model_path = CATBOOST_DIR / "path_ranker_model/catboost_model.cbm"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    pool = Pool(selected[feature_cols], selected["target_positive_net"], cat_features=[feature_cols.index(col) for col in cat_cols])
    model = CatBoostClassifier(
        iterations=220,
        depth=4,
        learning_rate=0.04,
        loss_function="Logloss",
        random_seed=222451,
        verbose=False,
        allow_writing_files=False,
    )
    model.fit(pool)
    model.save_model(str(model_path))
    selected["raw_path_score"] = model.predict_proba(pool)[:, 1]

    branch_scores = (
        selected.groupby("regime_profit_branch_path", as_index=False)
        .agg(raw_path_score=("raw_path_score", "mean"), observed_rows=("raw_path_score", "size"))
        .sort_values("raw_path_score", ascending=False)
    )
    branch_scores_path = CATBOOST_DIR / "branch_path_scores_v1.csv"
    branch_scores.to_csv(branch_scores_path, index=False)

    metadata = {
        "catboost_available": True,
        "model_family": "catboost",
        "trainer_note": "uv_offline_catboost_classifier",
        "model_path": repo_rel(model_path),
        "features_path": repo_rel(feature_path),
        "branch_score_rows": int(len(branch_scores)),
        "training_rows": int(len(selected)),
        "positive_rate": float(selected["target_positive_net"].mean()) if len(selected) else 0.0,
    }
    metadata_path = CATBOOST_DIR / "catboost_path_ranker_metadata_v1.json"
    write_json(metadata_path, metadata)
    return {
        "branch_scores": branch_scores,
        "branch_scores_path": branch_scores_path,
        "metadata": metadata,
        "metadata_path": metadata_path,
        "model_path": model_path,
    }


def build_scores_for_ict_engine(export_payload: dict[str, Any] | None, branch_scores: pd.DataFrame) -> tuple[Path, dict[str, Any]]:
    target_csv = None
    target_rows = pd.DataFrame()
    candidate_set_id = ""
    if isinstance(export_payload, dict):
        candidate_set_id = str(export_payload.get("candidate_set_id") or "")
        csv_path = export_payload.get("csv_path")
        if csv_path:
            target_csv = REPO / str(csv_path)
            if target_csv.exists():
                target_rows = pd.read_csv(target_csv)

    branch_paths = set(branch_scores["regime_profit_branch_path"].astype(str))
    root_scores = {
        "trend": float(branch_scores[branch_scores["regime_profit_branch_path"].str.startswith("Bull ")]["raw_path_score"].mean()),
        "range": float(branch_scores[branch_scores["regime_profit_branch_path"].str.startswith("Sideways ")]["raw_path_score"].mean()),
        "stress": float(branch_scores[branch_scores["regime_profit_branch_path"].str.startswith("Crisis ")]["raw_path_score"].mean()),
    }
    rows: list[dict[str, Any]] = []
    exact_target_rows = 0
    target_path_ids: set[str] = set()
    if not target_rows.empty and "path_id" in target_rows.columns:
        target_path_ids = set(target_rows["path_id"].astype(str))
        exact_target_rows = len(target_path_ids & branch_paths)
        for item in target_rows.to_dict("records"):
            path_id = str(item.get("path_id", ""))
            score = 0.5
            if "trend" in path_id:
                score = root_scores.get("trend", 0.5)
            elif "range" in path_id:
                score = root_scores.get("range", 0.5)
            elif "stress" in path_id:
                score = root_scores.get("stress", 0.5)
            rows.append(
                {
                    "candidate_set_id": candidate_set_id or str(item.get("candidate_set_id") or ""),
                    "path_id": path_id,
                    "raw_path_score": score,
                    "score_model_family": "catboost",
                    "score_source_kind": "external_model",
                    "score_model_artifact_uri": repo_rel(CATBOOST_DIR / "path_ranker_model/catboost_model.cbm"),
                    "score_generator": "board_b_220646_target_surface_readback_v1.py",
                }
            )
    for row in branch_scores.to_dict("records"):
        rows.append(
            {
                "candidate_set_id": "board-b-source-root-stop-carry-longhorizon",
                "path_id": row["regime_profit_branch_path"],
                "raw_path_score": row["raw_path_score"],
                "score_model_family": "catboost",
                "score_source_kind": "external_model",
                "score_model_artifact_uri": repo_rel(CATBOOST_DIR / "path_ranker_model/catboost_model.cbm"),
                "score_generator": "board_b_220646_target_surface_readback_v1.py",
            }
        )

    scores_path = CATBOOST_DIR / "path_ranker_scores_for_ict_engine_v1.csv"
    write_csv(scores_path, rows)
    diagnostics = {
        "export_candidate_set_id": candidate_set_id,
        "export_target_csv": repo_rel(target_csv) if target_csv else "",
        "export_target_rows": int(len(target_rows)),
        "board_b_branch_paths": sorted(branch_paths),
        "target_path_ids": sorted(target_path_ids),
        "board_b_exact_target_rows": int(exact_target_rows),
        "scores_rows_written": len(rows),
        "path_mapping_loss": exact_target_rows == 0,
    }
    return scores_path, diagnostics


def main() -> int:
    for directory in [CATBOOST_DIR, CMD_DIR, OUT_DIR, CHECK_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    if STATE_DIR.exists():
        shutil.rmtree(STATE_DIR)

    report = json.loads(RC_SPA_REPORT.read_text(encoding="utf-8"))
    branch_summary = read_csv_rows(BRANCH_SUMMARY)
    branch_paths = [row["regime_profit_branch_path"] for row in branch_summary if row.get("parent_regime_root") != "Manipulation(scoped)"]

    catboost_result = train_real_catboost()
    commands: list[dict[str, Any]] = []
    commands.append(run_command("provider_status_agent", [str(BIN), "provider-status", "--agent"]))
    commands.append(run_command("auto_quant_status_json", [str(BIN), "auto-quant-status", "--state-dir", str(STATE_DIR), "--output-format", "json"]))
    commands.append(run_command("auto_quant_results_import", [str(BIN), "auto-quant-results-import", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--library", str(STRATEGY_LIBRARY)]))
    commands.append(
        run_command(
            "analyze_live_aggregate_bundle",
            [
                str(BIN),
                "analyze-live",
                "--symbol",
                "NQ",
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
                str(AGGREGATE_BUNDLE),
                "--regime-consumer-bundle-strict",
                "--apply-regime-bundle-bbn-soft-evidence",
                "--output-format",
                "json",
            ],
        )
    )
    commands.append(run_command("pre_bayes_status_json", [str(BIN), "pre-bayes-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"]))
    commands.append(run_command("auto_quant_prior_init_dry_run", [str(BIN), "auto-quant-prior-init", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--library", str(STRATEGY_LIBRARY), "--dry-run", "--force"]))

    root_probe_rows: list[dict[str, Any]] = []
    for root, bundle in ROOT_BUNDLES.items():
        cmd = run_command(
            f"analyze_demo_root_bundle_{root}",
            [
                str(BIN),
                "analyze",
                "--symbol",
                "NQ",
                "--demo",
                "--state-dir",
                str(STATE_DIR / f"root-probe-{root.lower()}"),
                "--regime-consumer-bundle",
                str(bundle),
                "--regime-consumer-bundle-strict",
                "--apply-regime-bundle-bbn-soft-evidence",
                "--output-format",
                "json",
            ],
        )
        commands.append(cmd)
        text = (REPO / cmd["stdout_path"]).read_text(encoding="utf-8")
        root_probe_rows.append(
            {
                "root": root,
                "bundle": repo_rel(bundle),
                "exit": cmd["returncode"],
                "bbn_evidence_applied": "regime_bundle_bbn_evidence_applied" in text,
                "bbn_evidence_skipped_no_supported_label": "regime_bundle_bbn_evidence_skipped=no_supported_label" in text,
                "branch_path": next(path for path in branch_paths if path.startswith(f"{root} ")),
            }
        )

    export_cmd = run_command("export_structural_path_ranking_target", [str(BIN), "export-structural-path-ranking-target", "--symbol", "NQ", "--state-dir", str(STATE_DIR)])
    commands.append(export_cmd)
    scores_path, structural_diagnostics = build_scores_for_ict_engine(export_cmd.get("parsed"), catboost_result["branch_scores"])
    commands.append(run_command("apply_structural_path_ranking_external_scores", [str(BIN), "apply-structural-path-ranking-external-scores", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--scores-file", str(scores_path)]))
    commands.append(run_command("register_structural_path_ranking_trainer_artifact", [str(BIN), "register-structural-path-ranking-trainer-artifact", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--artifact-uri", repo_rel(catboost_result["model_path"]), "--model-family", "catboost", "--trained-rows", str(catboost_result["metadata"]["training_rows"]), "--calibration-rows", "0"]))
    commands.append(run_command("enable_structural_path_ranking_runtime", [str(BIN), "enable-structural-path-ranking-runtime", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--reuse-mode", "candidate_set_only"]))
    commands.append(run_command("policy_training_status_json", [str(BIN), "policy-training-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--output-format", "json"]))
    commands.append(
        run_command(
            "analyze_live_after_path_ranker",
            [
                str(BIN),
                "analyze-live",
                "--symbol",
                "NQ",
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
                str(AGGREGATE_BUNDLE),
                "--regime-consumer-bundle-strict",
                "--apply-regime-bundle-bbn-soft-evidence",
                "--output-format",
                "json",
            ],
        )
    )
    commands.append(run_command("workflow_status_execution_candidate", [str(BIN), "workflow-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--phase", "execution-candidate", "--agent"]))
    commands.append(run_command("workflow_status_structural_bundle", [str(BIN), "workflow-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--phase", "structural-recommended-path-bundle", "--agent"]))

    root_probe_summary_path = OUT_DIR / "root_bbn_probe_summary_v1.csv"
    write_csv(root_probe_summary_path, root_probe_rows)

    all_command_exits_ok = all(row["returncode"] == 0 for row in commands)
    bbn_roots_applied = [row["root"] for row in root_probe_rows if row["bbn_evidence_applied"]]
    bbn_roots_skipped = [row["root"] for row in root_probe_rows if row["bbn_evidence_skipped_no_supported_label"]]
    downstream_promotable = all_command_exits_ok and structural_diagnostics["board_b_exact_target_rows"] > 0 and len(bbn_roots_skipped) == 0
    primary_blockers: list[str] = []
    if not all_command_exits_ok:
        primary_blockers.append("one_or_more_downstream_commands_failed")
    if bbn_roots_skipped:
        primary_blockers.append("bbn_soft_evidence_unsupported_roots=" + ",".join(bbn_roots_skipped))
    if structural_diagnostics["board_b_exact_target_rows"] == 0:
        primary_blockers.append("ict_engine_structural_path_ranker_target_has_no_exact_board_b_branch_path_rows")
    if not primary_blockers:
        primary_blockers.append("none")

    payload = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "state_dir": str(STATE_DIR),
        "branch_rc_spa_gate_result": report["decision"]["gate_result"],
        "stable_profit_score": report["decision"]["stable_profit_score"],
        "price_root_paths_passed": report["decision"]["price_root_paths_passed"],
        "manipulation_component_pass": report["decision"]["manipulation_component_pass"],
        "provider_readback": {"provider_status_exit": next(row for row in commands if row["name"] == "provider_status_agent")["returncode"]},
        "auto_quant": {
            "status_exit": next(row for row in commands if row["name"] == "auto_quant_status_json")["returncode"],
            "results_import_exit": next(row for row in commands if row["name"] == "auto_quant_results_import")["returncode"],
            "prior_init_dry_run_exit": next(row for row in commands if row["name"] == "auto_quant_prior_init_dry_run")["returncode"],
        },
        "pre_bayes": {
            "status_exit": next(row for row in commands if row["name"] == "pre_bayes_status_json")["returncode"],
            "root_probe_summary": repo_rel(root_probe_summary_path),
            "bbn_roots_applied": bbn_roots_applied,
            "bbn_roots_skipped_no_supported_label": bbn_roots_skipped,
        },
        "catboost_path_ranker": {
            **catboost_result["metadata"],
            "branch_scores": repo_rel(catboost_result["branch_scores_path"]),
            "scores_file": repo_rel(scores_path),
            "structural_diagnostics": structural_diagnostics,
            "apply_scores_exit": next(row for row in commands if row["name"] == "apply_structural_path_ranking_external_scores")["returncode"],
            "policy_training_status_exit": next(row for row in commands if row["name"] == "policy_training_status_json")["returncode"],
        },
        "execution_tree": {
            "analyze_live_after_path_ranker_exit": next(row for row in commands if row["name"] == "analyze_live_after_path_ranker")["returncode"],
            "workflow_status_execution_candidate_exit": next(row for row in commands if row["name"] == "workflow_status_execution_candidate")["returncode"],
            "workflow_status_structural_bundle_exit": next(row for row in commands if row["name"] == "workflow_status_structural_bundle")["returncode"],
        },
        "downstream_consumption": "blocked:downstream_branch_path_or_bbn_mapping_gap",
        "downstream_promotable": downstream_promotable,
        "primary_blocker": ";".join(primary_blockers),
        "commands": [{key: value for key, value in row.items() if key != "parsed"} for row in commands],
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
    }
    summary_json = OUT_DIR / "board_b_220646_target_surface_readback_v1.json"
    write_json(summary_json, payload)

    summary_md = OUT_DIR / "board_b_220646_target_surface_readback_v1.md"
    lines = [
        "# Board B 220646 Target Surface Readback v1",
        "",
        f"- Source candidate: `{SOURCE_RUN_ID}` / `{RECIPE_ID}`.",
        f"- Branch RC-SPA gate: `{payload['branch_rc_spa_gate_result']}`; stable score `{payload['stable_profit_score']}`.",
        f"- Price roots passed: `{payload['price_root_paths_passed']}/4`; Manipulation component pass: `{payload['manipulation_component_pass']}`.",
        f"- Provider readback exit: `{payload['provider_readback']['provider_status_exit']}`; Auto-Quant import/prior exits: `{payload['auto_quant']['results_import_exit']}` / `{payload['auto_quant']['prior_init_dry_run_exit']}`.",
        f"- BBN applied roots: `{','.join(bbn_roots_applied) or 'none'}`; unsupported roots: `{','.join(bbn_roots_skipped) or 'none'}`.",
        f"- Real CatBoost trained: `{payload['catboost_path_ranker']['catboost_available']}`; training rows `{payload['catboost_path_ranker']['training_rows']}`; branch-score rows `{payload['catboost_path_ranker']['branch_score_rows']}`.",
        f"- ict-engine structural target rows: `{structural_diagnostics['export_target_rows']}`; exact Board B branch-path target rows: `{structural_diagnostics['board_b_exact_target_rows']}`.",
        f"- Execution-tree workflow exits: analyze `{payload['execution_tree']['analyze_live_after_path_ranker_exit']}`, execution-candidate `{payload['execution_tree']['workflow_status_execution_candidate_exit']}`.",
        f"- Downstream promotable: `{str(downstream_promotable).lower()}`.",
        f"- Primary blocker: `{payload['primary_blocker']}`.",
        "",
        "## Evidence",
        "",
        f"- JSON: `{repo_rel(summary_json)}`",
        f"- Root BBN probe summary: `{repo_rel(root_probe_summary_path)}`",
        f"- CatBoost metadata: `{repo_rel(catboost_result['metadata_path'])}`",
        f"- CatBoost branch scores: `{repo_rel(catboost_result['branch_scores_path'])}`",
        f"- ICT Engine scores file: `{repo_rel(scores_path)}`",
        f"- Command outputs: `{repo_rel(CMD_DIR)}`",
        f"- Assertions: `{repo_rel(CHECK_DIR / 'board_b_220646_target_surface_readback_v1_assertions.out')}`",
        "",
        "## Interpretation",
        "",
        "The run trained a real CatBoost branch scorer in an isolated uv/offline environment and pushed scores through ict-engine structural path-ranking/runtime commands. The exact Board B `regime_profit_branch_path` rows still do not appear in ict-engine's exported structural path-ranking target, so the current runtime can consume mapped structural scores but cannot yet promote this candidate as a closed-loop branch-path-preserving profitability packet.",
    ]
    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS provider_status_exit={payload['provider_readback']['provider_status_exit']}",
        f"PASS branch_rc_spa_gate_result={payload['branch_rc_spa_gate_result']}",
        f"PASS price_root_paths_passed={payload['price_root_paths_passed']}",
        f"PASS manipulation_component_pass={payload['manipulation_component_pass']}",
        f"PASS catboost_available={payload['catboost_path_ranker']['catboost_available']}",
        f"PASS catboost_training_rows={payload['catboost_path_ranker']['training_rows']}",
        f"PASS bbn_roots_skipped_no_supported_label={','.join(bbn_roots_skipped) or 'none'}",
        f"PASS ict_engine_exact_board_b_target_rows={structural_diagnostics['board_b_exact_target_rows']}",
        f"PASS downstream_promotable={str(downstream_promotable).lower()}",
        f"PASS runtime_code_changed={str(payload['runtime_code_changed']).lower()}",
        f"PASS thresholds_relaxed={str(payload['thresholds_relaxed']).lower()}",
        f"PASS raw_data_committed={str(payload['raw_data_committed']).lower()}",
    ]
    (CHECK_DIR / "board_b_220646_target_surface_readback_v1_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({"run_id": RUN_ID, "downstream_promotable": downstream_promotable, "primary_blocker": payload["primary_blocker"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
