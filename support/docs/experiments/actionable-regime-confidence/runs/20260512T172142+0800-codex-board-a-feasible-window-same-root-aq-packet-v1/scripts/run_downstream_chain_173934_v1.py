#!/usr/bin/env python3
"""Run Board A 173934 downstream readback from the terminal 172142 AQ packet."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[4]
BIN = REPO / "target" / "debug" / "ict-engine"
SYMBOL = "BTCUSD"
STATE = ROOT / "state_downstream_v1"
CMD_DIR = ROOT / "command-output" / "downstream-v1"
CHECK_DIR = ROOT / "checks" / "downstream-v1"
REPORT_DIR = ROOT / "downstream-chain-readback-v1"
LIBRARY = ROOT / "provider_btc_172142_strategy_library_v1.json"
CANDLES = ROOT / "data" / "cleaned" / "btc_usd_1h_yfinance_candles.json"
BUILDER = ROOT / "scripts" / "build_downstream_inputs_172142_v1.py"
TRAINER = REPO / "scripts" / "auto_quant_external" / "pandas_path_ranker_trainer.py"
MODEL_DIR = ROOT / "path-ranker" / "downstream-v1-catboost"
SCORES = ROOT / "path-ranker" / "downstream-v1-catboost-scores.csv"
SUMMARY_JSON = REPORT_DIR / "downstream_chain_readback_173934_v1.json"
SUMMARY_MD = REPORT_DIR / "downstream_chain_readback_173934_v1.md"
ASSERTIONS = CHECK_DIR / "downstream_chain_readback_173934_v1_assertions.out"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def run_step(name: str, argv: list[str], env_extra: dict[str, str] | None = None) -> dict:
    CMD_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    write_text(CMD_DIR / f"{name}.cmd", " ".join(argv) + "\n")
    proc = subprocess.run(
        argv,
        cwd=REPO,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    write_text(CMD_DIR / f"{name}.out", proc.stdout)
    write_text(CMD_DIR / f"{name}.err", proc.stderr)
    write_text(CHECK_DIR / f"{name}.exit", f"{proc.returncode}\n")
    return {
        "name": name,
        "argv": argv,
        "exit": proc.returncode,
        "stdout_path": str(CMD_DIR / f"{name}.out"),
        "stderr_path": str(CMD_DIR / f"{name}.err"),
    }


def latest_target_csv() -> Path | None:
    candidates = sorted(
        STATE.glob("**/*structural_path_ranking*target*.csv"),
        key=lambda path: path.stat().st_mtime,
    )
    if candidates:
        return candidates[-1]
    candidates = sorted(
        STATE.glob("**/*path*ranking*.csv"),
        key=lambda path: path.stat().st_mtime,
    )
    return candidates[-1] if candidates else None


def csv_row_count(path: Path | None) -> int:
    if path is None or not path.exists():
        return 0
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    return max(0, len(rows) - 1)


def json_file(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def read_exit(name: str) -> int | None:
    path = CHECK_DIR / f"{name}.exit"
    if not path.exists():
        return None
    try:
        return int(path.read_text().strip())
    except ValueError:
        return None


def collect_score_families(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    return sorted({row.get("score_model_family", "") for row in rows if row.get("score_model_family")})


def main() -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    steps: list[dict] = []
    steps.append(run_step("00_build_downstream_inputs", ["python3", str(BUILDER)]))
    steps.append(
        run_step(
            "01_auto_quant_results_import",
            [
                str(BIN),
                "auto-quant-results-import",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE),
                "--library",
                str(LIBRARY),
            ],
        )
    )
    steps.append(
        run_step(
            "02_auto_quant_prior_init",
            [
                str(BIN),
                "auto-quant-prior-init",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE),
                "--library",
                str(LIBRARY),
                "--temper",
                "0.25",
            ],
        )
    )
    steps.append(
        run_step(
            "03_analyze",
            [
                str(BIN),
                "analyze",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE),
                "--data-htf",
                str(CANDLES),
                "--data-mtf",
                str(CANDLES),
                "--data-ltf",
                str(CANDLES),
                "--agent",
            ],
        )
    )
    steps.append(
        run_step(
            "04_pre_bayes_status",
            [
                str(BIN),
                "pre-bayes-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE),
                "--refresh",
                "--output-format",
                "json",
            ],
        )
    )
    steps.append(
        run_step(
            "05_policy_training_status",
            [
                str(BIN),
                "policy-training-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE),
                "--output-format",
                "json",
            ],
        )
    )
    steps.append(
        run_step(
            "06_workflow_status",
            [
                str(BIN),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE),
                "--refresh",
                "--agent",
            ],
        )
    )
    steps.append(
        run_step(
            "07_workflow_execution_candidate",
            [
                str(BIN),
                "workflow-status",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE),
                "--phase",
                "execution-candidate",
                "--agent",
            ],
        )
    )
    steps.append(
        run_step(
            "08_export_structural_path_ranking_target",
            [
                str(BIN),
                "export-structural-path-ranking-target",
                "--symbol",
                SYMBOL,
                "--state-dir",
                str(STATE),
            ],
        )
    )

    target_csv = latest_target_csv()
    target_rows = csv_row_count(target_csv)
    uv = Path.home() / ".local" / "bin" / "uv"
    if target_csv is not None:
        catboost_env = {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
        }
        steps.append(
            run_step(
                "09_catboost_path_ranker_train",
                [
                    str(uv),
                    "run",
                    "--offline",
                    "--with",
                    "pandas",
                    "--with",
                    "numpy",
                    "--with",
                    "catboost",
                    "python",
                    str(TRAINER),
                    "--target-csv",
                    str(target_csv),
                    "--output-dir",
                    str(MODEL_DIR),
                    "--model-family",
                    "catboost",
                ],
                env_extra=catboost_env,
            )
        )
        if read_exit("09_catboost_path_ranker_train") == 0:
            steps.append(
                run_step(
                    "10_catboost_path_ranker_apply",
                    [
                        str(uv),
                        "run",
                        "--offline",
                        "--with",
                        "pandas",
                        "--with",
                        "numpy",
                        "--with",
                        "catboost",
                        "python",
                        str(TRAINER),
                        "--apply",
                        "--model-dir",
                        str(MODEL_DIR),
                        "--target-csv",
                        str(target_csv),
                        "--output-scores",
                        str(SCORES),
                    ],
                    env_extra=catboost_env,
                )
            )
        if read_exit("10_catboost_path_ranker_apply") == 0:
            trainer_artifact = MODEL_DIR / "trainer_artifact.json"
            trainer_meta = json_file(trainer_artifact)
            trained_rows = str(trainer_meta.get("trained_rows", target_rows))
            calibration_rows = str(trainer_meta.get("calibration_rows", target_rows))
            steps.append(
                run_step(
                    "11_register_structural_path_ranking_trainer_artifact",
                    [
                        str(BIN),
                        "register-structural-path-ranking-trainer-artifact",
                        "--symbol",
                        SYMBOL,
                        "--state-dir",
                        str(STATE),
                        "--artifact-uri",
                        str(trainer_artifact),
                        "--model-family",
                        "catboost",
                        "--score-column",
                        "raw_path_score",
                        "--trained-rows",
                        trained_rows,
                        "--calibration-rows",
                        calibration_rows,
                    ],
                )
            )
            steps.append(
                run_step(
                    "12_apply_structural_path_ranking_external_scores",
                    [
                        str(BIN),
                        "apply-structural-path-ranking-external-scores",
                        "--symbol",
                        SYMBOL,
                        "--state-dir",
                        str(STATE),
                        "--scores-file",
                        str(SCORES),
                    ],
                )
            )
            steps.append(
                run_step(
                    "13_enable_structural_path_ranking_runtime",
                    [
                        str(BIN),
                        "enable-structural-path-ranking-runtime",
                        "--symbol",
                        SYMBOL,
                        "--state-dir",
                        str(STATE),
                        "--reuse-mode",
                        "candidate_set_only",
                    ],
                )
            )
            steps.append(
                run_step(
                    "14_policy_training_status_after_catboost",
                    [
                        str(BIN),
                        "policy-training-status",
                        "--symbol",
                        SYMBOL,
                        "--state-dir",
                        str(STATE),
                        "--output-format",
                        "json",
                    ],
                )
            )
            steps.append(
                run_step(
                    "15_workflow_status_after_catboost",
                    [
                        str(BIN),
                        "workflow-status",
                        "--symbol",
                        SYMBOL,
                        "--state-dir",
                        str(STATE),
                        "--refresh",
                        "--agent",
                    ],
                )
            )
            steps.append(
                run_step(
                    "16_workflow_execution_candidate_after_catboost",
                    [
                        str(BIN),
                        "workflow-status",
                        "--symbol",
                        SYMBOL,
                        "--state-dir",
                        str(STATE),
                        "--phase",
                        "execution-candidate",
                        "--agent",
                    ],
                )
            )

    scores_rows = csv_row_count(SCORES)
    trainer_meta = json_file(MODEL_DIR / "trainer_artifact.json")
    score_families = collect_score_families(SCORES)
    all_core_zero = all(step["exit"] == 0 for step in steps[:9])
    catboost_train_exit = read_exit("09_catboost_path_ranker_train")
    catboost_apply_exit = read_exit("10_catboost_path_ranker_apply")
    register_exit = read_exit("11_register_structural_path_ranking_trainer_artifact")
    apply_scores_exit = read_exit("12_apply_structural_path_ranking_external_scores")
    enable_exit = read_exit("13_enable_structural_path_ranking_runtime")
    calibration_rows = int(trainer_meta.get("calibration_rows", 0) or 0)
    maturity_ready = calibration_rows >= 30 and scores_rows >= 30

    summary = {
        "run_id": ROOT.name,
        "source_packet": "172142_feasible_window_same_root_aq_packet",
        "generated_at": utc_now(),
        "symbol": SYMBOL,
        "state_dir": str(STATE),
        "library": str(LIBRARY),
        "candles": str(CANDLES),
        "target_csv": str(target_csv) if target_csv else None,
        "target_rows": target_rows,
        "scores": str(SCORES) if SCORES.exists() else None,
        "scores_rows": scores_rows,
        "score_families": score_families,
        "trainer_artifact": str(MODEL_DIR / "trainer_artifact.json")
        if (MODEL_DIR / "trainer_artifact.json").exists()
        else None,
        "trainer_model_family": trainer_meta.get("model_family"),
        "trainer_trained_rows": trainer_meta.get("trained_rows"),
        "trainer_calibration_rows": trainer_meta.get("calibration_rows"),
        "maturity_ready_min30": maturity_ready,
        "steps": steps,
        "gate_result": (
            "downstream_chain_ran_catboost_registered_fail_closed_maturity_below_30"
            if all_core_zero and catboost_train_exit == 0 and register_exit == 0 and not maturity_ready
            else "downstream_chain_failed_before_registered_path_ranker"
        ),
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
    }
    write_text(SUMMARY_JSON, json.dumps(summary, indent=2, sort_keys=True) + "\n")

    assertions = [
        f"PASS run_id={ROOT.name}",
        f"PASS core_steps_zero={all_core_zero}",
        f"PASS target_rows={target_rows}",
        f"PASS catboost_train_exit={catboost_train_exit}",
        f"PASS catboost_apply_exit={catboost_apply_exit}",
        f"PASS register_exit={register_exit}",
        f"PASS apply_scores_exit={apply_scores_exit}",
        f"PASS enable_exit={enable_exit}",
        f"PASS scores_rows={scores_rows}",
        f"FAIL_CLOSED maturity_ready_min30={maturity_ready}",
        "FAIL_CLOSED calibrated_95_regime_acceptance_not_proven",
        "FAIL_CLOSED cross_market_timeframe_validation_not_run",
        "PASS promotion_allowed=false",
        "PASS trade_usable=false",
        "PASS update_goal=false",
    ]
    write_text(ASSERTIONS, "\n".join(assertions) + "\n")

    md = [
        "# Downstream Chain Readback 173934 v1",
        "",
        f"Source packet: `172142_feasible_window_same_root_aq_packet`.",
        f"State dir: `{STATE}`.",
        f"Strategy library: `{LIBRARY}`.",
        f"Candles: `{CANDLES}`.",
        "",
        "## Command Exits",
    ]
    for step in steps:
        md.append(f"- `{step['name']}` exit `{step['exit']}`.")
    md.extend(
        [
            "",
            "## Path-Ranker Readback",
            f"- Target CSV: `{target_csv}`.",
            f"- Target rows: `{target_rows}`.",
            f"- Scores CSV: `{SCORES if SCORES.exists() else ''}`.",
            f"- Scores rows: `{scores_rows}`.",
            f"- Score families: `{', '.join(score_families) if score_families else ''}`.",
            f"- Trainer model family: `{trainer_meta.get('model_family')}`.",
            f"- Trainer rows: `{trainer_meta.get('trained_rows')}`.",
            f"- Calibration rows: `{trainer_meta.get('calibration_rows')}`.",
            f"- Mature min30 ready: `{maturity_ready}`.",
            "",
            "## Gate",
            f"- Gate result: `{summary['gate_result']}`.",
            "- `promotion_allowed=false`.",
            "- `trade_usable=false`.",
            "- `update_goal=false`.",
        ]
    )
    write_text(SUMMARY_MD, "\n".join(md) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if all_core_zero else 1


if __name__ == "__main__":
    raise SystemExit(main())
