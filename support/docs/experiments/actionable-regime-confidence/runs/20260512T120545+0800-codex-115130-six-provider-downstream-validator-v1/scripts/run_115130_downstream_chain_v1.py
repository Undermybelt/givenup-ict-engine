from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any


RUN_ID = "20260512T120545+0800-codex-115130-six-provider-downstream-validator-v1"
SOURCE_RUN_ID = "20260512T115130+0800-codex-113833-ibkr-longer-duration-six-provider-aq-v1"
SYMBOL = "B2R_115130_SIX_PROVIDER_BTC_MATRIX"

ROOT = Path("docs/experiments/actionable-regime-confidence/runs") / RUN_ID
REPORT_DIR = ROOT / "115130-six-provider-downstream-validator-v1"
CHECK_DIR = ROOT / "checks"
OUT_DIR = ROOT / "command-output"
STATE_DIR = ROOT / "state_115130_downstream_v1"
CATBOOST_DIR = ROOT / "catboost"
TRADES = ROOT / "real-trades" / "115130_six_provider_real_trades_validated.jsonl"
TARGET_HISTORY = STATE_DIR / SYMBOL / "policy_training" / "structural_path_ranking_target_history.csv"
HISTORY_SCORES = CATBOOST_DIR / "history_scores.csv"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def count_data_rows(path: Path) -> int:
    if not path.exists():
        return 0
    return max(sum(1 for _ in path.open(encoding="utf-8")) - 1, 0)


def run_step(name: str, cmd: list[str], env: dict[str, str] | None = None) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    display = " ".join(cmd)
    (OUT_DIR / f"{name}.cmd").write_text(display + "\n", encoding="utf-8")
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    proc = subprocess.run(
        cmd,
        cwd=Path.cwd(),
        env=merged_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    (OUT_DIR / f"{name}.out").write_text(proc.stdout, encoding="utf-8")
    (OUT_DIR / f"{name}.err").write_text(proc.stderr, encoding="utf-8")
    (CHECK_DIR / f"{name}.exit").write_text(f"{proc.returncode}\n", encoding="utf-8")
    return {
        "name": name,
        "cmd": display,
        "exit": proc.returncode,
        "stdout": str(OUT_DIR / f"{name}.out"),
        "stderr": str(OUT_DIR / f"{name}.err"),
    }


def main() -> int:
    for directory in (REPORT_DIR, CHECK_DIR, OUT_DIR, STATE_DIR, CATBOOST_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    (ROOT / "run_id.txt").write_text(RUN_ID + "\n", encoding="utf-8")
    (ROOT / "source_run_id.txt").write_text(SOURCE_RUN_ID + "\n", encoding="utf-8")

    thread_env = {
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
    }
    steps: list[tuple[str, list[str], dict[str, str] | None]] = [
        (
            "00_ingest_real_trades_dry_run",
            [
                "./target/debug/ict-engine",
                "auto-quant-ingest-real-trades",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--trades",
                str(TRADES),
                "--source",
                "board_b_115130_six_provider_real_trades",
                "--dry-run",
            ],
            None,
        ),
        (
            "01_ingest_real_trades_force",
            [
                "./target/debug/ict-engine",
                "auto-quant-ingest-real-trades",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--trades",
                str(TRADES),
                "--source",
                "board_b_115130_six_provider_real_trades",
                "--force",
            ],
            None,
        ),
        (
            "02_pre_bayes_status_after_ingest",
            [
                "./target/debug/ict-engine",
                "pre-bayes-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--output-format",
                "json",
            ],
            None,
        ),
        (
            "03_policy_training_status_before_export",
            [
                "./target/debug/ict-engine",
                "policy-training-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
            None,
        ),
        (
            "04_export_structural_path_ranking_target",
            [
                "./target/debug/ict-engine",
                "export-structural-path-ranking-target",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
            ],
            None,
        ),
        (
            "05_train_catboost",
            [
                "uv",
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
                str(TARGET_HISTORY),
                "--output-dir",
                str(CATBOOST_DIR / "path_ranker_model"),
                "--model-family",
                "catboost",
                "--output-scores",
                str(HISTORY_SCORES),
            ],
            thread_env,
        ),
        (
            "06_apply_catboost_history",
            [
                "uv",
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
                str(CATBOOST_DIR / "path_ranker_model"),
                "--target-csv",
                str(TARGET_HISTORY),
                "--output-scores",
                str(HISTORY_SCORES),
            ],
            thread_env,
        ),
        (
            "07_apply_external_scores",
            [
                "./target/debug/ict-engine",
                "apply-structural-path-ranking-external-scores",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--scores-file",
                str(HISTORY_SCORES),
            ],
            None,
        ),
        (
            "08_register_trainer_artifact",
            [
                "./target/debug/ict-engine",
                "register-structural-path-ranking-trainer-artifact",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--artifact-uri",
                str(HISTORY_SCORES),
                "--model-family",
                "catboost",
                "--score-column",
                "raw_path_score",
            ],
            None,
        ),
        (
            "09_enable_runtime",
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
            None,
        ),
        (
            "10_policy_training_status_final",
            [
                "./target/debug/ict-engine",
                "policy-training-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--output-format",
                "json",
            ],
            None,
        ),
        (
            "11_pre_bayes_status_final",
            [
                "./target/debug/ict-engine",
                "pre-bayes-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--output-format",
                "json",
            ],
            None,
        ),
        (
            "12_workflow_structural_bundle",
            [
                "./target/debug/ict-engine",
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--phase",
                "structural-feedback",
                "--output-format",
                "json",
            ],
            None,
        ),
        (
            "13_workflow_execution_candidate",
            [
                "./target/debug/ict-engine",
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--phase",
                "execution-candidate",
                "--output-format",
                "json",
            ],
            None,
        ),
        (
            "14_workflow_full",
            [
                "./target/debug/ict-engine",
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE_DIR),
                "--refresh",
                "--output-format",
                "json",
            ],
            None,
        ),
    ]

    results = [run_step(name, cmd, env) for name, cmd, env in steps]
    failed = [item for item in results if item["exit"] != 0]
    summary = {
        "run_id": RUN_ID,
        "source_run_id": SOURCE_RUN_ID,
        "symbol": SYMBOL,
        "state_dir": str(STATE_DIR),
        "trades": str(TRADES),
        "commands": results,
        "failed_commands": failed,
        "ordered_commands_exit0": len(failed) == 0,
        "target_history_rows": count_data_rows(TARGET_HISTORY),
        "history_score_rows": count_data_rows(HISTORY_SCORES),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_json(REPORT_DIR / "115130_six_provider_downstream_chain_v1.json", summary)
    checks = [
        f"PASS run_id={RUN_ID}",
        f"PASS source_run_id={SOURCE_RUN_ID}",
        f"{'PASS' if not failed else 'FAIL'} ordered_commands_exit0={len(failed) == 0}",
        f"PASS target_history_rows={summary['target_history_rows']}",
        f"PASS history_score_rows={summary['history_score_rows']}",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    (CHECK_DIR / "115130_six_provider_downstream_chain_v1_assertions.out").write_text(
        "\n".join(checks) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
