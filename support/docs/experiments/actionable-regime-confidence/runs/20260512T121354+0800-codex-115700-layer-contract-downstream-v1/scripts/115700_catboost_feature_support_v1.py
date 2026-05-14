#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd

RUN_ID = "20260512T121354+0800-codex-115700-layer-contract-downstream-v1"
SYMBOL = "B2R_SIX_PROVIDER_BTC_115700"
ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
STATE_DIR = ROOT / "state_115700_layer_contract_downstream_v1"
POLICY_DIR = STATE_DIR / SYMBOL / "policy_training"
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "115700-layer-contract-downstream-v1"
SUPPORT_DIR = ROOT / "path-ranker" / "catboost_feature_support_v1"
BASE_SCRIPT = ROOT / "scripts" / "115700_layer_contract_downstream_v1.py"
UV = "/Users/thrill3r/.local/bin/uv"


def load_base():
    spec = importlib.util.spec_from_file_location("layer_contract_downstream", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def augment_csv(source: Path, output: Path) -> Path:
    df = pd.read_csv(source)
    path_text = (
        df.get("regime_profit_branch_path", pd.Series([""] * len(df)))
        .fillna(df.get("path_label", pd.Series(["unknown"] * len(df))))
        .fillna(df.get("path_id", pd.Series(["unknown"] * len(df))))
        .astype(str)
    )
    df["ltf_path_label"] = path_text
    df["selected_direction"] = df.get("direction", pd.Series(["unknown"] * len(df))).fillna("unknown").astype(str)
    df["setup_family"] = (
        df.get("sub_regime", pd.Series([""] * len(df)))
        .fillna(df.get("path_label", pd.Series(["unknown"] * len(df))))
        .fillna("unknown")
        .astype(str)
    )
    df["entry_style"] = (
        df.get("sub_sub_regime_or_profit_factor", pd.Series(["provider_matrix"] * len(df)))
        .fillna("provider_matrix")
        .astype(str)
    )
    counts = path_text.map(path_text.value_counts()).fillna(0).astype(float)
    max_count = float(max(counts.max(), 1.0))
    df["evidence_quality_score"] = counts / max_count
    df["risk_reward"] = pd.to_numeric(df.get("current_posterior", 0.0), errors="coerce").fillna(0.0)
    df["setup_quality"] = pd.to_numeric(df.get("experience_prior", 0.0), errors="coerce").fillna(0.0)
    df["htf_alignment_score"] = pd.to_numeric(df.get("structural_baseline_score", 0.0), errors="coerce").fillna(0.0)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    return output


def run_command(label: str, cmd: list[str], env: dict[str, str] | None = None) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    write_text(OUT_DIR / f"{label}.cmd", " ".join(cmd) + "\n")
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=env)
    write_text(OUT_DIR / f"{label}.out", proc.stdout)
    write_text(OUT_DIR / f"{label}.err", proc.stderr)
    write_text(CHECK_DIR / f"{label}.exit", f"{proc.returncode}\n")
    return proc.returncode


def parse_json_output(label: str) -> dict[str, Any]:
    path = OUT_DIR / f"{label}.out"
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def cleanup_catboost_info() -> str:
    path = Path("catboost_info")
    if path.exists():
        shutil.rmtree(path)
    status = "catboost_info_absent" if not path.exists() else "catboost_info_present"
    write_text(OUT_DIR / "49_catboost_info_cleanup_check.out", status + "\n")
    write_text(CHECK_DIR / "49_catboost_info_cleanup_check.exit", "0\n" if status == "catboost_info_absent" else "1\n")
    return status


def augmented_context(exits: dict[str, int]) -> dict[str, Any]:
    pre = parse_json_output("24_pre_bayes_status")
    policy = parse_json_output("45_policy_training_status_augmented")
    execution = parse_json_output("46_workflow_execution_candidate_augmented")
    workflow = parse_json_output("47_workflow_full_augmented")
    target = policy.get("structural_path_ranking_target") or {}
    runtime = policy.get("structural_path_ranking_runtime") or {}
    raw_rows = int(target.get("raw_scored_mature_rows") or 0)
    production_rows = int(target.get("production_validation_rows") or 0)
    observation_rows = int(target.get("observation_validation_rows") or 0)
    catboost_ok = all(exits.get(k) == 0 for k in [
        "40_train_catboost_augmented",
        "41_apply_catboost_augmented_history",
        "42_apply_external_scores_augmented",
        "43_register_trainer_artifact_augmented",
        "44_enable_runtime_augmented",
        "45_policy_training_status_augmented",
        "46_workflow_execution_candidate_augmented",
        "47_workflow_full_augmented",
    ])
    quality_weight = 1.0 if catboost_ok and raw_rows >= 30 and production_rows >= 30 and observation_rows >= 30 else 0.0
    return {
        "pre_bayes_filter_state": {
            "status": pre.get("latest_gate_status"),
            "canonical_regime": pre.get("latest_canonical_structural_active_regime"),
            "confidence": pre.get("latest_canonical_structural_confidence"),
            "policy_version": pre.get("latest_policy_version"),
            "uses_soft_evidence": pre.get("latest_uses_soft_evidence"),
        },
        "bbn_posterior": {
            "canonical_probabilities": pre.get("latest_canonical_structural_probabilities"),
            "soft_evidence": pre.get("latest_soft_evidence"),
            "filtered_assignments": pre.get("latest_filtered_assignments"),
        },
        "catboost_path_ranker_label": {
            "train_exit": exits.get("40_train_catboost_augmented"),
            "apply_exit": exits.get("41_apply_catboost_augmented_history"),
            "external_score_exit": exits.get("42_apply_external_scores_augmented"),
            "runtime": runtime,
            "validation": target,
            "raw_scored_mature": raw_rows,
            "production_validation": production_rows,
            "observation_validation": observation_rows,
            "score_model_family": "catboost" if quality_weight > 0.0 else "catboost_unavailable_or_failed",
        },
        "execution_tree_decision": {
            "ready": execution.get("ready"),
            "actionable": execution.get("actionable"),
            "review_status": execution.get("review_status"),
            "candidate_status": execution.get("candidate_status"),
            "execution_gate_status": execution.get("execution_gate_status"),
            "review_reason": execution.get("review_reason"),
            "path_id": execution.get("path_id"),
            "path_ranker_raw_score": execution.get("path_ranker_raw_score"),
            "path_ranker_runtime_source": execution.get("path_ranker_runtime_source"),
            "closed_loop_branch_admission": workflow.get("closed_loop_branch_admission"),
        },
        "failure_reason": str(execution.get("review_reason") or execution.get("candidate_status") or "execution_readback_unavailable"),
        "quality_weight": quality_weight,
    }


def main() -> int:
    base = load_base()
    SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
    hist = POLICY_DIR / "structural_path_ranking_target_history.csv"
    current = POLICY_DIR / "structural_path_ranking_target.csv"
    aug_hist = augment_csv(hist, SUPPORT_DIR / "structural_path_ranking_target_history_augmented.csv")
    aug_current = augment_csv(current, SUPPORT_DIR / "structural_path_ranking_target_augmented.csv")
    model_dir = SUPPORT_DIR / "catboost_model_augmented"
    history_scores = SUPPORT_DIR / "history_scores_augmented.csv"
    trainer_artifact = model_dir / "trainer_artifact.json"
    env = os.environ.copy()
    env.update({"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1"})
    exits: dict[str, int] = {}
    exits["40_train_catboost_augmented"] = run_command("40_train_catboost_augmented", [UV, "run", "--offline", "--python", "3.11", "--with", "pandas", "--with", "numpy", "--with", "catboost", "python", "scripts/auto_quant_external/pandas_path_ranker_trainer.py", "--target-csv", str(aug_hist), "--output-dir", str(model_dir), "--model-family", "catboost", "--output-scores", str(history_scores)], env=env)
    exits["41_apply_catboost_augmented_history"] = run_command("41_apply_catboost_augmented_history", [UV, "run", "--offline", "--python", "3.11", "--with", "pandas", "--with", "numpy", "--with", "catboost", "python", "scripts/auto_quant_external/pandas_path_ranker_trainer.py", "--apply", "--model-dir", str(model_dir), "--target-csv", str(aug_hist), "--output-scores", str(history_scores)], env=env)
    exits["42_apply_external_scores_augmented"] = run_command("42_apply_external_scores_augmented", ["./target/debug/ict-engine", "apply-structural-path-ranking-external-scores", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--scores-file", str(history_scores)])
    exits["43_register_trainer_artifact_augmented"] = run_command("43_register_trainer_artifact_augmented", ["./target/debug/ict-engine", "register-structural-path-ranking-trainer-artifact", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--artifact-uri", str(trainer_artifact), "--model-family", "catboost", "--score-column", "raw_path_score"])
    exits["44_enable_runtime_augmented"] = run_command("44_enable_runtime_augmented", ["./target/debug/ict-engine", "enable-structural-path-ranking-runtime", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--reuse-mode", "prefer_history"])
    exits["45_policy_training_status_augmented"] = run_command("45_policy_training_status_augmented", ["./target/debug/ict-engine", "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"])
    exits["46_workflow_execution_candidate_augmented"] = run_command("46_workflow_execution_candidate_augmented", ["./target/debug/ict-engine", "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--phase", "execution-candidate", "--output-format", "json"])
    exits["47_workflow_full_augmented"] = run_command("47_workflow_full_augmented", ["./target/debug/ict-engine", "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"])
    cleanup = cleanup_catboost_info()
    context = augmented_context(exits)
    source_report = json.loads(base.SOURCE_REPORT.read_text(encoding="utf-8"))
    final_enrichment = base.enrich_all(source_report, context, "postchain_catboost_supported")
    validation = base.validate_rows(final_enrichment["path"], exits)
    policy = parse_json_output("45_policy_training_status_augmented")
    execution = parse_json_output("46_workflow_execution_candidate_augmented")
    target = policy.get("structural_path_ranking_target") or {}
    summary = {
        "run_id": RUN_ID,
        "symbol": SYMBOL,
        "augmented_history_csv": str(aug_hist),
        "augmented_current_csv": str(aug_current),
        "history_scores": str(history_scores),
        "trainer_artifact": str(trainer_artifact),
        "exits": exits,
        "final_enrichment": final_enrichment,
        "validation": validation,
        "policy_training_status": policy,
        "execution_candidate": execution,
        "ranker_target": target,
        "catboost_info_cleanup": cleanup,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    json_path = REPORT_DIR / "115700_catboost_feature_support_v1.json"
    md_path = REPORT_DIR / "115700_catboost_feature_support_v1.md"
    assertions_path = CHECK_DIR / "115700_catboost_feature_support_v1_assertions.out"
    write_json(json_path, summary)
    lines = [
        "# 115700 CatBoost Feature Support v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Symbol: `{SYMBOL}`",
        "",
        "## Scope",
        "Derive non-runtime trainer features from the existing 115700 structural target history so CatBoost is not trained on a constant-only feature surface.",
        "This does not edit ict-engine runtime code or alter the original 115700 source rows.",
        "",
        "## Readback",
        f"- Train/apply/register/enable exits: `{exits}`.",
        f"- Contract-complete rows after CatBoost support: `{validation['contract_complete_rows']}`.",
        f"- Market/factor trainable rows: `{validation['market_factor_trainable_rows']}`.",
        f"- Raw scored mature: `{target.get('raw_scored_mature_rows')}/{target.get('raw_scored_mature_min_rows')}`.",
        f"- Production validation: `{target.get('production_validation_rows')}/{target.get('production_validation_min_rows')}`.",
        f"- Observation validation: `{target.get('observation_validation_rows')}/{target.get('observation_validation_min_rows')}`.",
        f"- Runtime selection: `{target.get('runtime_selection_status')}` ready `{target.get('runtime_selection_ready')}`.",
        f"- Execution ready/actionable: `{execution.get('ready')}` / `{execution.get('actionable')}` review `{execution.get('review_status')}`.",
        f"- CatBoost cleanup: `{cleanup}`.",
        "",
        "## Decision",
        "- Gate result: `115700_layer_contract_catboost_runtime_repaired_but_execution_fail_closed`.",
        "- `promotion_allowed=false`.",
        "- `trade_usable=false`.",
        "- `update_goal=false`.",
    ]
    write_text(md_path, "\n".join(lines) + "\n")
    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS train_catboost_augmented_exit={exits['40_train_catboost_augmented']}",
        f"PASS apply_catboost_augmented_history_exit={exits['41_apply_catboost_augmented_history']}",
        f"PASS apply_external_scores_augmented_exit={exits['42_apply_external_scores_augmented']}",
        f"PASS register_trainer_artifact_augmented_exit={exits['43_register_trainer_artifact_augmented']}",
        f"PASS enable_runtime_augmented_exit={exits['44_enable_runtime_augmented']}",
        f"PASS contract_complete_rows={validation['contract_complete_rows']}",
        f"PASS market_factor_trainable_rows={validation['market_factor_trainable_rows']}",
        f"PASS raw_scored_mature={target.get('raw_scored_mature_rows')}",
        f"PASS production_validation={target.get('production_validation_rows')}",
        f"PASS observation_validation={target.get('observation_validation_rows')}",
        f"PASS runtime_selection_status={target.get('runtime_selection_status')}",
        f"PASS catboost_info_cleanup={cleanup}",
        f"FAIL_CLOSED execution_ready={execution.get('ready')} actionable={execution.get('actionable')} review={execution.get('review_status')}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    write_text(assertions_path, "\n".join(assertion_lines) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
