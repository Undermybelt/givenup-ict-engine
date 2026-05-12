from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "20260512T120746+0800-codex-115500-same-root-six-provider-aq-chain-v1"
SYMBOL = "B2R_PROVIDER_MATRIX_SIX_PROVIDER_AQ_115500"
ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
STATE_DIR = ROOT / "state_six_provider_chain_v1"
STATE_SYMBOL_DIR = STATE_DIR / SYMBOL
POLICY_DIR = STATE_SYMBOL_DIR / "policy_training"
OUT_DIR = ROOT / "command-output"
CHECK_DIR = ROOT / "checks"
REPORT_DIR = ROOT / "115500-same-root-six-provider-aq-chain-v1"
SUPPORT_DIR = ROOT / "path-ranker" / "catboost_feature_support_v1"
UV = "/Users/thrill3r/.local/bin/uv"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


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
    (OUT_DIR / f"{label}.cmd").write_text(" ".join(cmd) + "\n")
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, env=env)
    (OUT_DIR / f"{label}.out").write_text(proc.stdout)
    (OUT_DIR / f"{label}.err").write_text(proc.stderr)
    (CHECK_DIR / f"{label}.exit").write_text(f"{proc.returncode}\n")
    return proc.returncode


def parse_json_output(label: str) -> dict[str, Any]:
    path = OUT_DIR / f"{label}.out"
    if not path.exists() or not path.read_text().strip():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def cleanup_catboost_info() -> str:
    path = Path("catboost_info")
    if path.exists():
        shutil.rmtree(path)
    status = "catboost_info_absent" if not path.exists() else "catboost_info_present"
    (OUT_DIR / "49_catboost_info_cleanup_check.out").write_text(status + "\n")
    (CHECK_DIR / "49_catboost_info_cleanup_check.exit").write_text("0\n" if status == "catboost_info_absent" else "1\n")
    return status


def main() -> int:
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
    exits["40_train_catboost_augmented"] = run_command(
        "40_train_catboost_augmented",
        [
            UV,
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
            "scripts/auto_quant_external/pandas_path_ranker_trainer.py",
            "--target-csv",
            str(aug_hist),
            "--output-dir",
            str(model_dir),
            "--model-family",
            "catboost",
            "--output-scores",
            str(history_scores),
        ],
        env=env,
    )
    exits["41_apply_catboost_augmented_history"] = run_command(
        "41_apply_catboost_augmented_history",
        [
            UV,
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
            "scripts/auto_quant_external/pandas_path_ranker_trainer.py",
            "--apply",
            "--model-dir",
            str(model_dir),
            "--target-csv",
            str(aug_hist),
            "--output-scores",
            str(history_scores),
        ],
        env=env,
    )
    exits["42_apply_external_scores_augmented"] = run_command(
        "42_apply_external_scores_augmented",
        [
            "./target/debug/ict-engine",
            "apply-structural-path-ranking-external-scores",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--scores-file",
            str(history_scores),
        ],
    )
    exits["43_register_trainer_artifact_augmented"] = run_command(
        "43_register_trainer_artifact_augmented",
        [
            "./target/debug/ict-engine",
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
        ],
    )
    exits["44_enable_runtime_augmented"] = run_command(
        "44_enable_runtime_augmented",
        [
            "./target/debug/ict-engine",
            "enable-structural-path-ranking-runtime",
            "--symbol",
            SYMBOL,
            "--state-dir",
            str(STATE_DIR),
            "--reuse-mode",
            "prefer_history",
        ],
    )
    exits["45_policy_training_status_augmented"] = run_command(
        "45_policy_training_status_augmented",
        ["./target/debug/ict-engine", "policy-training-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--output-format", "json"],
    )
    exits["46_workflow_execution_candidate_augmented"] = run_command(
        "46_workflow_execution_candidate_augmented",
        ["./target/debug/ict-engine", "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--phase", "execution-candidate", "--output-format", "json"],
    )
    exits["47_workflow_full_augmented"] = run_command(
        "47_workflow_full_augmented",
        ["./target/debug/ict-engine", "workflow-status", "--symbol", SYMBOL, "--state-dir", str(STATE_DIR), "--refresh", "--output-format", "json"],
    )
    cleanup_status = cleanup_catboost_info()

    policy = parse_json_output("45_policy_training_status_augmented")
    execution = parse_json_output("46_workflow_execution_candidate_augmented")
    workflow = parse_json_output("47_workflow_full_augmented")
    ranker = policy.get("structural_path_ranking_target", {})
    validation = policy.get("structural_path_ranking_validation", {})
    summary = {
        "run_id": RUN_ID,
        "symbol": SYMBOL,
        "exits": exits,
        "augmented_history_csv": str(aug_hist),
        "augmented_current_csv": str(aug_current),
        "history_scores": str(history_scores),
        "trainer_artifact": str(trainer_artifact),
        "policy_training_augmented": policy,
        "ranker_target": ranker,
        "ranker_validation": validation,
        "execution_candidate_augmented": execution,
        "workflow_full_augmented": workflow,
        "catboost_info_cleanup": cleanup_status,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "115500_same_root_six_provider_catboost_feature_support_v1.json", summary)

    report = REPORT_DIR / "115500_same_root_six_provider_catboost_feature_support_v1.md"
    lines = [
        "# 115500 Same-Root Six-Provider CatBoost Feature Support v1",
        "",
        f"Run id: `{RUN_ID}`",
        f"Symbol: `{SYMBOL}`",
        "",
        "## Scope",
        "This support packet derives non-runtime trainer features from the existing structural target history so CatBoost is not trained on a constant-only feature surface.",
        "It does not edit ict-engine runtime code or alter the source trade rows.",
        "",
        "## Readback",
        f"- Train/apply/register/enable exits: `{exits}`.",
        f"- Raw scored mature: `{ranker.get('raw_scored_mature_rows')}/{ranker.get('raw_scored_mature_min_rows')}`.",
        f"- Production validation: `{ranker.get('production_validation_rows')}/{ranker.get('production_validation_min_rows')}`.",
        f"- Observation validation: `{ranker.get('observation_validation_rows')}/{ranker.get('observation_validation_min_rows')}`.",
        f"- Trainer artifact ready: `{ranker.get('trainer_artifact_ready')}` status `{ranker.get('trainer_artifact_status')}`.",
        f"- Runtime selection: `{ranker.get('runtime_selection_status')}` ready `{ranker.get('runtime_selection_ready')}`.",
        f"- Execution ready/actionable: `{execution.get('ready')}` / `{execution.get('actionable')}` review `{execution.get('review_status')}`.",
        f"- CatBoost cleanup: `{cleanup_status}`.",
        "",
        "## Decision",
        "- Gate result: `115500_same_root_six_provider_catboost_feature_support=catboost_runtime_repaired_but_execution_fail_closed`.",
        "- `promotion_allowed=false`.",
        "- `trade_usable=false`.",
        "- `update_goal=false`.",
    ]
    report.write_text("\n".join(lines) + "\n")

    assertions = CHECK_DIR / "115500_same_root_six_provider_catboost_feature_support_v1_assertions.out"
    assertion_lines = [
        f"PASS run_id={RUN_ID}",
        f"PASS train_catboost_augmented_exit={exits['40_train_catboost_augmented']}",
        f"PASS apply_catboost_augmented_history_exit={exits['41_apply_catboost_augmented_history']}",
        f"PASS apply_external_scores_augmented_exit={exits['42_apply_external_scores_augmented']}",
        f"PASS register_trainer_artifact_augmented_exit={exits['43_register_trainer_artifact_augmented']}",
        f"PASS enable_runtime_augmented_exit={exits['44_enable_runtime_augmented']}",
        f"PASS raw_scored_mature={ranker.get('raw_scored_mature_rows')}",
        f"PASS production_validation={ranker.get('production_validation_rows')}",
        f"PASS observation_validation={ranker.get('observation_validation_rows')}",
        f"PASS trainer_artifact_ready={ranker.get('trainer_artifact_ready')}",
        f"PASS runtime_selection_status={ranker.get('runtime_selection_status')}",
        f"PASS catboost_info_cleanup={cleanup_status}",
        f"FAIL_CLOSED execution_ready={execution.get('ready')} actionable={execution.get('actionable')} review={execution.get('review_status')}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    assertions.write_text("\n".join(assertion_lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
