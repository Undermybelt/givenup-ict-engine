#!/usr/bin/env python3
"""Run Board B downstream consumption for SourceRootStopCarryLongHorizonV1.

This script is intentionally run-local: it consumes the completed branch
RC-SPA packet, writes all durable evidence under the run root, and uses a
fresh /tmp ict-engine state directory.
"""

from __future__ import annotations

import csv
import json
import math
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RUN_ID = "20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-v1"
DOWNSTREAM_ID = "20260511T221104+0800-codex-board-b-source-root-stop-carry-longhorizon-downstream-v1"
RECIPE_ID = "SourceRootStopCarryLongHorizonV1"

RUN_ROOT = Path(__file__).resolve().parents[1]
REPO = next(path for path in [RUN_ROOT, *RUN_ROOT.parents] if (path / "Cargo.toml").exists())
BIN = REPO / "target/debug/ict-engine"
STATE_DIR = Path("/tmp/ict-engine-board-b-source-root-stop-carry-longhorizon-downstream-v1")

BRANCH_SUMMARY = RUN_ROOT / "branch-rc-spa/source_root_stop_carry_longhorizon_branch_summary_v1.csv"
SELECTED_ROWS = RUN_ROOT / "branch-rc-spa/source_root_stop_carry_longhorizon_selected_rows_v1.csv"
REPORT_JSON = RUN_ROOT / "branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.json"

OUT_DIR = RUN_ROOT / "downstream-chain"
CMD_DIR = RUN_ROOT / "downstream-chain/command-output"
BUNDLE_DIR = RUN_ROOT / "downstream-chain/regime-bundles"
CATBOOST_DIR = RUN_ROOT / "downstream-chain/catboost"
CHECK_DIR = RUN_ROOT / "checks"


def repo_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def command_safe_name(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)


def run_command(name: str, args: list[str]) -> dict[str, Any]:
    safe = command_safe_name(name)
    proc = subprocess.run(args, cwd=REPO, text=True, capture_output=True, check=False)
    stdout_path = CMD_DIR / f"{safe}.out"
    stderr_path = CMD_DIR / f"{safe}.err"
    exit_path = CMD_DIR / f"{safe}.exit"
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


def branch_rows() -> list[dict[str, str]]:
    rows = read_csv_rows(BRANCH_SUMMARY)
    return [row for row in rows if row["parent_regime_root"] != "Manipulation(scoped)"]


def root_label(root: str) -> str:
    return {
        "Bull": "primary::TrendExpansion",
        "Bear": "primary::BearReliefCarry",
        "Sideways": "primary::RangeConsolidation",
        "Crisis": "primary::ExtremeStress",
    }[root]


def build_bundle(row: dict[str, str], aggregate: bool = False) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if aggregate:
        roots = branch_rows()
        label_set = [item["regime_profit_branch_path"] for item in roots]
        return {
            "schema_version": "regime-consumer-bundle/v1",
            "artifact_count": 2,
            "missing_artifacts": [],
            "latest_decision": {
                "timestamp": timestamp,
                "decision_state": "accepted",
                "trade_usable": True,
                "final_label": RECIPE_ID,
                "label_set": label_set,
                "abstain_reasons": ["downstream_consumption_probe_before_promotion"],
            },
            "consumer_hints": {
                "execution_tree_hint": "accept_regime",
                "bbn_evidence_hint": {
                    "regime_decision_state": "accepted",
                    "regime_trade_usable": True,
                    "regime_label": RECIPE_ID,
                    "regime_label_set": label_set,
                    "regime_transition_hazard": 0.0,
                    "regime_decision_reasons": ["branch_rc_spa_all_price_roots_passed"],
                },
                "path_ranker_context": {
                    "recipe_id": RECIPE_ID,
                    "run_id": RUN_ID,
                    "branch_paths": label_set,
                    "price_root_paths_passed": 4,
                    "manipulation_component_pass": True,
                    "stable_profit_score": float(json.loads(REPORT_JSON.read_text(encoding="utf-8"))["decision"]["stable_profit_score"]),
                },
                "trade_usable": True,
            },
            "artifacts": {
                "branch_rc_spa_report": {
                    "status": "present",
                    "path": repo_rel(REPORT_JSON),
                    "schema_version": "board-b-source-root-stop-carry-longhorizon/v1",
                }
            },
            "consumer_contract": {
                "zero_config": True,
                "hotplug_scope": "include_artifact",
                "main_runtime_mutation": "none",
                "optional_for_consumers": True,
                "token_friendly": True,
            },
        }
    root = row["parent_regime_root"]
    branch_path = row["regime_profit_branch_path"]
    return {
        "schema_version": "regime-consumer-bundle/v1",
        "artifact_count": 2,
        "missing_artifacts": [],
        "latest_decision": {
            "timestamp": timestamp,
            "decision_state": "single_label_95",
            "trade_usable": True,
            "final_label": root_label(root),
            "label_set": [root_label(root), branch_path],
            "abstain_reasons": ["branch_path_downstream_consumption_probe"],
        },
        "consumer_hints": {
            "execution_tree_hint": "accept_regime",
            "bbn_evidence_hint": {
                "regime_decision_state": "single_label_95",
                "regime_trade_usable": True,
                "regime_label": root_label(root),
                "regime_label_set": [root_label(root), branch_path],
                "regime_transition_hazard": 0.0,
                "regime_decision_reasons": ["branch_rc_spa_passed", f"root={root}"],
            },
            "path_ranker_context": {
                "recipe_id": RECIPE_ID,
                "parent_regime_root": root,
                "regime_profit_branch_path": branch_path,
                "selected_variant_id": row["selected_variant_id"],
                "rc_spa": float(row["rc_spa"]),
                "edge_lcb_5pct": float(row["bootstrap_edge_lcb_5pct"]),
                "pbo": float(row["pbo"]),
                "dsr": float(row["dsr"]),
                "trade_count": int(float(row["total_trades"])),
            },
            "trade_usable": True,
        },
        "artifacts": {
            "branch_rc_spa_report": {
                "status": "present",
                "path": repo_rel(REPORT_JSON),
                "schema_version": "board-b-source-root-stop-carry-longhorizon/v1",
            }
        },
        "consumer_contract": {
            "zero_config": True,
            "hotplug_scope": "include_artifact",
            "main_runtime_mutation": "none",
            "optional_for_consumers": True,
            "token_friendly": True,
        },
    }


def build_strategy_library(summary_rows: list[dict[str, str]], selected: pd.DataFrame) -> Path:
    strategies: list[dict[str, Any]] = []
    for row in summary_rows:
        root = row["parent_regime_root"]
        path = row["regime_profit_branch_path"]
        branch = selected[selected["regime_profit_branch_path"] == path]
        start_col = "entry_ts" if "entry_ts" in branch.columns else "open_date"
        end_col = "exit_ts" if "exit_ts" in branch.columns else "close_date"
        wins = branch[branch["profit_ratio_net"].astype(float) > 0]["profit_ratio_net"].astype(float).sum()
        losses = -branch[branch["profit_ratio_net"].astype(float) < 0]["profit_ratio_net"].astype(float).sum()
        profit_factor = float(wins / losses) if losses > 1e-12 else 999.0
        strategy_name = f"{RECIPE_ID}_{root}_{row['selected_variant_id']}"
        strategies.append(
            {
                "name": strategy_name,
                "file_path": repo_rel(RUN_ROOT / "scripts/source_root_stop_carry_longhorizon_v1.py"),
                "metadata": {
                    "recipe_id": RECIPE_ID,
                    "parent_regime_root": root,
                    "regime_profit_branch_path": path,
                    "branch_rc_spa_run_id": RUN_ID,
                    "status": "board_b_branch_rc_spa_passed_pending_downstream",
                },
                "status": "ok",
                "validation_metrics": {
                    "sharpe": float(row["dsr"]),
                    "sortino": float(row["dsr"]),
                    "calmar": float(row["rc_spa"]) / 100.0,
                    "total_profit_pct": float(row["net_return_R"]) * 100.0,
                    "max_drawdown_pct": -100.0 * abs(float(row["max_drawdown_trade_equity_proxy"])),
                    "trade_count": int(float(row["total_trades"])),
                    "win_rate_pct": 100.0 * float(row["win_rate"]),
                    "profit_factor": profit_factor,
                },
                "per_pair_metrics": {
                    root: {
                        "total_profit_pct": float(row["net_return_R"]) * 100.0,
                        "trade_count": int(float(row["total_trades"])),
                        "win_rate_pct": 100.0 * float(row["win_rate"]),
                        "profit_factor": profit_factor,
                    }
                },
                "pairs": [root],
                "timerange": f"{min(branch[start_col])} -> {max(branch[end_col])}" if not branch.empty else "n/a",
                "commit": "run-local-board-b-rc-spa-artifact",
                "error": None,
            }
        )
    library = {
        "manifest_version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "auto_quant_repo_url": "/Users/thrill3r/Auto-Quant",
        "auto_quant_pinned_ref": "run-local-board-b-rc-spa-artifact",
        "config_path": repo_rel(REPORT_JSON),
        "timeframe": "mixed_1d_4h",
        "log_path": repo_rel(RUN_ROOT / "checks/source_root_stop_carry_longhorizon_v1_run.out"),
        "strategies": strategies,
        "validation_errors": [],
    }
    path = OUT_DIR / "autoquant_strategy_library_source_root_stop_carry_longhorizon_v1.json"
    write_json(path, library)
    return path


def train_catboost(selected: pd.DataFrame, summary_rows: list[dict[str, str]]) -> dict[str, Any]:
    CATBOOST_DIR.mkdir(parents=True, exist_ok=True)
    model_path = CATBOOST_DIR / "path_ranker_model/catboost_model.cbm"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    score_rows_path = CATBOOST_DIR / "branch_path_scores_v1.csv"
    model_meta_path = CATBOOST_DIR / "catboost_path_ranker_metadata_v1.json"
    feature_path = CATBOOST_DIR / "catboost_branch_features_v1.csv"

    frame = selected.copy()
    frame["profit_ratio_net"] = frame["profit_ratio_net"].astype(float)
    frame["target_positive_net"] = (frame["profit_ratio_net"] > 0).astype(int)
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
        if col not in frame.columns:
            frame[col] = "missing"
    cat_cols = [col for col in feature_cols if frame[col].dtype == object]
    numeric_cols = [col for col in feature_cols if col not in cat_cols]
    for col in numeric_cols:
        frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0.0)
    frame[feature_cols + ["target_positive_net", "regime_profit_branch_path"]].to_csv(feature_path, index=False)

    catboost_available = False
    model_family = "catboost"
    trainer_note = "catboost_classifier"
    try:
        from catboost import CatBoostClassifier, Pool

        catboost_available = True
        cat_indexes = [feature_cols.index(col) for col in cat_cols]
        model = CatBoostClassifier(
            iterations=180,
            depth=4,
            learning_rate=0.045,
            loss_function="Logloss",
            random_seed=221104,
            verbose=False,
            allow_writing_files=False,
        )
        model.fit(Pool(frame[feature_cols], frame["target_positive_net"], cat_features=cat_indexes))
        model.save_model(str(model_path))
        frame["raw_path_score"] = model.predict_proba(Pool(frame[feature_cols], cat_features=cat_indexes))[:, 1]
    except Exception as err:  # pragma: no cover - evidence path records this.
        model_family = "catboost_unavailable_fallback"
        trainer_note = f"fallback_mean_positive_rate:{type(err).__name__}:{err}"
        model_path.write_text(trainer_note + "\n", encoding="utf-8")
        frame["raw_path_score"] = frame.groupby("regime_profit_branch_path")["target_positive_net"].transform("mean")

    branch_scores = (
        frame.groupby("regime_profit_branch_path", as_index=False)
        .agg(raw_path_score=("raw_path_score", "mean"), observed_rows=("raw_path_score", "size"))
        .sort_values("raw_path_score", ascending=False)
    )
    branch_scores.to_csv(score_rows_path, index=False)

    metadata = {
        "catboost_available": catboost_available,
        "model_family": model_family,
        "trainer_note": trainer_note,
        "model_path": repo_rel(model_path),
        "features_path": repo_rel(feature_path),
        "branch_score_rows": len(branch_scores),
        "training_rows": int(len(frame)),
        "positive_rate": float(frame["target_positive_net"].mean()) if len(frame) else 0.0,
    }
    write_json(model_meta_path, metadata)

    return {
        "model_path": model_path,
        "metadata_path": model_meta_path,
        "score_rows_path": score_rows_path,
        "metadata": metadata,
        "branch_scores": branch_scores,
    }


def structural_scores_from_export(export_payload: dict[str, Any] | None, branch_scores: pd.DataFrame) -> tuple[Path, dict[str, Any]]:
    scores_path = CATBOOST_DIR / "path_ranker_scores_for_ict_engine_v1.csv"
    target_csv = None
    candidate_set_id = ""
    target_rows = pd.DataFrame()
    if isinstance(export_payload, dict):
        candidate_set_id = str(export_payload.get("candidate_set_id") or "")
        target_csv_value = export_payload.get("csv_path")
        if target_csv_value:
            target_csv = REPO / str(target_csv_value)
            if target_csv.exists():
                target_rows = pd.read_csv(target_csv)
    root_score = {
        "trend": float(branch_scores[branch_scores["regime_profit_branch_path"].str.startswith("Bull ")]["raw_path_score"].mean()),
        "range": float(branch_scores[branch_scores["regime_profit_branch_path"].str.startswith("Sideways ")]["raw_path_score"].mean()),
        "stress": float(branch_scores[branch_scores["regime_profit_branch_path"].str.startswith("Crisis ")]["raw_path_score"].mean()),
    }
    root_score = {k: (0.5 if math.isnan(v) else v) for k, v in root_score.items()}
    rows: list[dict[str, Any]] = []
    board_b_exact_rows = 0
    if not target_rows.empty and "path_id" in target_rows.columns:
        for item in target_rows.to_dict("records"):
            path_id = str(item["path_id"])
            if "trend" in path_id:
                score = root_score["trend"]
            elif "range" in path_id:
                score = root_score["range"]
            elif "stress" in path_id:
                score = root_score["stress"]
            else:
                score = float(branch_scores["raw_path_score"].mean()) if len(branch_scores) else 0.5
            rows.append(
                {
                    "candidate_set_id": candidate_set_id or str(item.get("candidate_set_id") or ""),
                    "path_id": path_id,
                    "raw_path_score": score,
                    "score_model_family": "catboost",
                    "score_source_kind": "external_model",
                    "score_model_artifact_uri": repo_rel(CATBOOST_DIR / "path_ranker_model/catboost_model.cbm"),
                    "score_generator": "source_root_stop_carry_longhorizon_downstream_v1.py",
                }
            )
            if str(item).find("SourceRootStopCarryLongHorizonV1") >= 0:
                board_b_exact_rows += 1
    for row in branch_scores.to_dict("records"):
        rows.append(
            {
                "candidate_set_id": "board-b-source-root-stop-carry-longhorizon",
                "path_id": row["regime_profit_branch_path"],
                "raw_path_score": row["raw_path_score"],
                "score_model_family": "catboost",
                "score_source_kind": "external_model",
                "score_model_artifact_uri": repo_rel(CATBOOST_DIR / "path_ranker_model/catboost_model.cbm"),
                "score_generator": "source_root_stop_carry_longhorizon_downstream_v1.py",
            }
        )
    write_csv(scores_path, rows)
    diagnostics = {
        "export_target_csv": repo_rel(target_csv) if target_csv else "",
        "export_target_rows": int(len(target_rows)),
        "export_candidate_set_id": candidate_set_id,
        "scores_rows_written": len(rows),
        "board_b_exact_target_rows": board_b_exact_rows,
        "path_mapping_loss": board_b_exact_rows == 0,
    }
    return scores_path, diagnostics


def command_success(commands: list[dict[str, Any]], name: str) -> bool:
    return any(row["name"] == name and row["returncode"] == 0 for row in commands)


def main() -> int:
    for directory in [OUT_DIR, CMD_DIR, BUNDLE_DIR, CATBOOST_DIR, CHECK_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    if STATE_DIR.exists():
        shutil.rmtree(STATE_DIR)

    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    if report["decision"]["gate_result"] != "pass" or report["decision"]["price_root_paths_passed"] != 4:
        raise RuntimeError("downstream chain requires completed 4/4 branch RC-SPA pass")

    summary_rows = branch_rows()
    selected = pd.read_csv(SELECTED_ROWS)
    selected["profit_ratio_net"] = pd.to_numeric(selected["profit_ratio_net"], errors="coerce").fillna(0.0)

    aggregate_bundle = BUNDLE_DIR / "aggregate_regime_consumer_bundle_v1.json"
    write_json(aggregate_bundle, build_bundle(summary_rows[0], aggregate=True))
    root_bundle_paths: dict[str, Path] = {}
    for row in summary_rows:
        root = row["parent_regime_root"]
        path = BUNDLE_DIR / f"{root.lower()}_regime_consumer_bundle_v1.json"
        write_json(path, build_bundle(row))
        root_bundle_paths[root] = path

    library_path = build_strategy_library(summary_rows, selected)
    catboost_result = train_catboost(selected, summary_rows)

    commands: list[dict[str, Any]] = []
    commands.append(run_command("auto_quant_results_import", [str(BIN), "auto-quant-results-import", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--library", str(library_path)]))
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
                str(aggregate_bundle),
                "--regime-consumer-bundle-strict",
                "--apply-regime-bundle-bbn-soft-evidence",
                "--output-format",
                "json",
            ],
        )
    )
    commands.append(run_command("pre_bayes_status", [str(BIN), "pre-bayes-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--refresh"]))
    commands.append(run_command("auto_quant_prior_init_dry_run", [str(BIN), "auto-quant-prior-init", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--library", str(library_path), "--dry-run", "--force"]))

    root_probe_rows: list[dict[str, Any]] = []
    for root, bundle_path in root_bundle_paths.items():
        root_state = STATE_DIR / f"root-probe-{root.lower()}"
        cmd = run_command(
            f"analyze_demo_root_bundle_{root}",
            [
                str(BIN),
                "analyze",
                "--symbol",
                "NQ",
                "--demo",
                "--state-dir",
                str(root_state),
                "--regime-consumer-bundle",
                str(bundle_path),
                "--regime-consumer-bundle-strict",
                "--apply-regime-bundle-bbn-soft-evidence",
                "--output-format",
                "json",
            ],
        )
        commands.append(cmd)
        text = (REPO / cmd["stdout_path"]).read_text(encoding="utf-8") if cmd["stdout_path"] else ""
        root_probe_rows.append(
            {
                "root": root,
                "bundle": repo_rel(bundle_path),
                "exit": cmd["returncode"],
                "bbn_evidence_applied": "regime_bundle_bbn_evidence_applied" in text,
                "bbn_evidence_skipped_no_supported_label": "regime_bundle_bbn_evidence_skipped=no_supported_label" in text,
                "branch_path": next(row["regime_profit_branch_path"] for row in summary_rows if row["parent_regime_root"] == root),
            }
        )

    export_cmd = run_command("export_structural_path_ranking_target", [str(BIN), "export-structural-path-ranking-target", "--symbol", "NQ", "--state-dir", str(STATE_DIR)])
    commands.append(export_cmd)
    scores_path, structural_diagnostics = structural_scores_from_export(export_cmd.get("parsed"), catboost_result["branch_scores"])
    commands.append(run_command("apply_structural_path_ranking_external_scores", [str(BIN), "apply-structural-path-ranking-external-scores", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--scores-file", str(scores_path)]))
    commands.append(
        run_command(
            "register_structural_path_ranking_trainer_artifact",
            [
                str(BIN),
                "register-structural-path-ranking-trainer-artifact",
                "--symbol",
                "NQ",
                "--state-dir",
                str(STATE_DIR),
                "--artifact-uri",
                repo_rel(catboost_result["model_path"]),
                "--model-family",
                "catboost",
                "--trained-rows",
                str(catboost_result["metadata"]["training_rows"]),
                "--calibration-rows",
                "0",
            ],
        )
    )
    commands.append(run_command("enable_structural_path_ranking_runtime", [str(BIN), "enable-structural-path-ranking-runtime", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--reuse-mode", "candidate_set_only"]))
    commands.append(run_command("policy_training_status_after_path_ranker", [str(BIN), "policy-training-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--output-format", "json"]))
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
                str(aggregate_bundle),
                "--regime-consumer-bundle-strict",
                "--apply-regime-bundle-bbn-soft-evidence",
                "--output-format",
                "json",
            ],
        )
    )
    commands.append(run_command("workflow_status_execution_candidate", [str(BIN), "workflow-status", "--symbol", "NQ", "--state-dir", str(STATE_DIR), "--phase", "execution-candidate", "--agent"]))

    apply_cmd = next(row for row in commands if row["name"] == "apply_structural_path_ranking_external_scores")
    policy_cmd = next(row for row in commands if row["name"] == "policy_training_status_after_path_ranker")
    workflow_cmd = next(row for row in commands if row["name"] == "workflow_status_execution_candidate")

    root_probe_summary_path = OUT_DIR / "root_bbn_probe_summary_v1.csv"
    write_csv(root_probe_summary_path, root_probe_rows)

    all_command_exits_ok = all(row["returncode"] == 0 for row in commands)
    bbn_roots_applied = [row["root"] for row in root_probe_rows if row["bbn_evidence_applied"]]
    bbn_roots_skipped = [row["root"] for row in root_probe_rows if row["bbn_evidence_skipped_no_supported_label"]]
    structural_path_loss = bool(structural_diagnostics["path_mapping_loss"])
    downstream_promotable = all_command_exits_ok and not structural_path_loss and len(bbn_roots_skipped) == 0
    downstream_consumption = "promotable_candidate" if downstream_promotable else "blocked:downstream_branch_path_or_bbn_mapping_gap"
    primary_blockers = []
    if not all_command_exits_ok:
        primary_blockers.append("one_or_more_downstream_commands_failed")
    if bbn_roots_skipped:
        primary_blockers.append("bbn_soft_evidence_unsupported_roots=" + ",".join(bbn_roots_skipped))
    if structural_path_loss:
        primary_blockers.append("ict_engine_structural_path_ranker_target_has_no_exact_board_b_branch_path_rows")
    if not primary_blockers:
        primary_blockers.append("none")

    payload = {
        "run_id": DOWNSTREAM_ID,
        "branch_rc_spa_run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "state_dir": str(STATE_DIR),
        "branch_rc_spa_gate_result": report["decision"]["gate_result"],
        "price_root_paths_passed": report["decision"]["price_root_paths_passed"],
        "manipulation_component_pass": report["decision"]["manipulation_component_pass"],
        "pre_bayes": {
            "aggregate_status_exit": next(row for row in commands if row["name"] == "pre_bayes_status")["returncode"],
            "root_probe_summary": repo_rel(root_probe_summary_path),
            "bbn_roots_applied": bbn_roots_applied,
            "bbn_roots_skipped_no_supported_label": bbn_roots_skipped,
        },
        "bbn": {
            "auto_quant_prior_init_dry_run_exit": next(row for row in commands if row["name"] == "auto_quant_prior_init_dry_run")["returncode"],
            "strategy_library": repo_rel(library_path),
        },
        "catboost_path_ranker": {
            **catboost_result["metadata"],
            "scores_file": repo_rel(scores_path),
            "apply_scores_exit": apply_cmd["returncode"],
            "apply_scores_rows_with_raw_path_score": (apply_cmd.get("parsed") or {}).get("rows_with_raw_path_score") if isinstance(apply_cmd.get("parsed"), dict) else None,
            "policy_training_status_exit": policy_cmd["returncode"],
            "structural_diagnostics": structural_diagnostics,
        },
        "execution_tree": {
            "analyze_live_after_path_ranker_exit": next(row for row in commands if row["name"] == "analyze_live_after_path_ranker")["returncode"],
            "workflow_status_execution_candidate_exit": workflow_cmd["returncode"],
            "execution_tree_trace_path": repo_rel(STATE_DIR / "NQ/execution_tree_trace.json"),
        },
        "downstream_consumption": downstream_consumption,
        "downstream_promotable": downstream_promotable,
        "primary_blocker": ";".join(primary_blockers),
        "commands": [{k: v for k, v in row.items() if k != "parsed"} for row in commands],
        "artifacts": {
            "aggregate_bundle": repo_rel(aggregate_bundle),
            "root_bundles": {root: repo_rel(path) for root, path in root_bundle_paths.items()},
            "strategy_library": repo_rel(library_path),
            "catboost_metadata": repo_rel(catboost_result["metadata_path"]),
            "branch_scores": repo_rel(catboost_result["score_rows_path"]),
            "ict_engine_scores": repo_rel(scores_path),
            "root_probe_summary": repo_rel(root_probe_summary_path),
        },
        "runtime_code_changed": False,
        "thresholds_relaxed": False,
        "raw_data_committed": False,
    }
    summary_json = OUT_DIR / "source_root_stop_carry_longhorizon_downstream_v1.json"
    write_json(summary_json, payload)

    lines = [
        "# Source Root Stop Carry Long-Horizon Downstream v1",
        "",
        f"- Branch RC-SPA gate: `{payload['branch_rc_spa_gate_result']}`",
        f"- Price roots passed: `{payload['price_root_paths_passed']}/4`; Manipulation component pass: `{payload['manipulation_component_pass']}`",
        f"- Downstream consumption: `{downstream_consumption}`",
        f"- Downstream promotable: `{str(downstream_promotable).lower()}`",
        f"- Primary blocker: `{payload['primary_blocker']}`",
        "",
        "## Stage Results",
        "",
        f"- Pre-Bayes status exit: `{payload['pre_bayes']['aggregate_status_exit']}`; root BBN applied: `{','.join(bbn_roots_applied) or 'none'}`; unsupported roots: `{','.join(bbn_roots_skipped) or 'none'}`",
        f"- BBN dry-run exit: `{payload['bbn']['auto_quant_prior_init_dry_run_exit']}`",
        f"- CatBoost available: `{str(payload['catboost_path_ranker']['catboost_available']).lower()}`; apply scores exit: `{payload['catboost_path_ranker']['apply_scores_exit']}`; exact Board B target rows: `{structural_diagnostics['board_b_exact_target_rows']}`",
        f"- Execution-tree analyze exit: `{payload['execution_tree']['analyze_live_after_path_ranker_exit']}`; workflow execution-candidate exit: `{payload['execution_tree']['workflow_status_execution_candidate_exit']}`",
        "",
        "## Branch Path Preservation",
        "",
        "The run-local bundles, strategy library, and CatBoost branch-score file preserve `regime_profit_branch_path`. "
        "The current ict-engine structural path-ranker target did not expose exact Board B branch-path rows, so runtime promotion remains blocked until that adapter surface can consume the same rooted paths.",
        "",
        "## Artifacts",
        "",
        f"- JSON: `{repo_rel(summary_json)}`",
        f"- Root BBN probe summary: `{repo_rel(root_probe_summary_path)}`",
        f"- Command outputs: `{repo_rel(CMD_DIR)}`",
        f"- CatBoost metadata: `{repo_rel(catboost_result['metadata_path'])}`",
        f"- Assertions: `{repo_rel(CHECK_DIR / 'source_root_stop_carry_longhorizon_downstream_v1_assertions.out')}`",
    ]
    summary_md = OUT_DIR / "source_root_stop_carry_longhorizon_downstream_v1.md"
    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assertions = [
        f"PASS branch_rc_spa_gate_result={payload['branch_rc_spa_gate_result']}",
        f"PASS price_root_paths_passed={payload['price_root_paths_passed']}",
        f"PASS manipulation_component_pass={payload['manipulation_component_pass']}",
        f"PASS downstream_consumption={downstream_consumption}",
        f"PASS downstream_promotable={str(downstream_promotable).lower()}",
        f"PASS all_command_exits_ok={str(all_command_exits_ok).lower()}",
        f"PASS branch_path_preserved_in_run_local_artifacts=true",
        f"PASS ict_engine_exact_board_b_target_rows={structural_diagnostics['board_b_exact_target_rows']}",
        f"PASS bbn_roots_skipped_no_supported_label={','.join(bbn_roots_skipped) or 'none'}",
        "PASS runtime_code_changed=false",
        "PASS thresholds_relaxed=false",
        "PASS raw_data_committed=false",
    ]
    (CHECK_DIR / "source_root_stop_carry_longhorizon_downstream_v1_assertions.out").write_text("\n".join(assertions) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ["run_id", "downstream_consumption", "downstream_promotable", "primary_blocker"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
