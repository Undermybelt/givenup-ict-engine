#!/usr/bin/env python3
import csv
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO = Path("/Users/thrill3r/projects-ict-engine/ict-engine")
RUN_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T193452+0800-codex-191941-structural-path-ranker-extension-v1"
SRC_ROOT = REPO / "docs/experiments/actionable-regime-confidence/runs/20260512T191941+0800-codex-independent-market-timeframe-downstream-smoke-v1"
STATE_DIR = SRC_ROOT / "state"
COMMAND_DIR = RUN_ROOT / "command-output"
CHECK_DIR = RUN_ROOT / "checks"
AGG_DIR = RUN_ROOT / "aggregate"

SYMBOLS = [
    "BOARD_A_SPY_YF_191941",
    "BOARD_A_SPY_IBKR_191941",
    "BOARD_A_BTC_BINANCE_191941",
    "BOARD_A_BTC_BYBIT_191941",
    "BOARD_A_BTC_KRAKEN_191941",
    "BOARD_A_BTC_TVR_191941",
]


def safe_name(name: str) -> str:
    return name.lower().replace("/", "_").replace(" ", "_")


def run_step(name, argv, env=None):
    cmd_path = COMMAND_DIR / f"{name}.cmd"
    out_path = COMMAND_DIR / f"{name}.out"
    err_path = COMMAND_DIR / f"{name}.err"
    exit_path = CHECK_DIR / f"{name}.exit"
    cmd_path.write_text(" ".join(str(x) for x in argv) + "\n")
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    proc = subprocess.run(
        [str(x) for x in argv],
        cwd=REPO,
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out_path.write_text(proc.stdout)
    err_path.write_text(proc.stderr)
    exit_path.write_text(str(proc.returncode) + "\n")
    return {
        "name": name,
        "argv": [str(x) for x in argv],
        "exit": proc.returncode,
        "stdout": str(out_path.relative_to(REPO)),
        "stderr": str(err_path.relative_to(REPO)),
    }


def read_csv_rows(path: Path, symbol: str):
    if not path.exists():
        return []
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for row in reader:
            row = dict(row)
            row["source_symbol"] = symbol
            rows.append(row)
        return rows


def write_rows(path: Path, rows):
    if not rows:
        path.write_text("")
        return
    fields = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fields.append(key)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def main():
    COMMAND_DIR.mkdir(parents=True, exist_ok=True)
    CHECK_DIR.mkdir(parents=True, exist_ok=True)
    AGG_DIR.mkdir(parents=True, exist_ok=True)

    steps = []
    contexts = []
    history_rows = []
    current_rows = []

    for symbol in SYMBOLS:
        name = safe_name(symbol)
        steps.append(run_step(
            f"01_export_target_{name}",
            ["./target/debug/ict-engine", "export-structural-path-ranking-target", "--symbol", symbol, "--state-dir", STATE_DIR],
        ))
        policy_dir = STATE_DIR / symbol / "policy_training"
        hist_path = policy_dir / "structural_path_ranking_target_history.csv"
        cur_path = policy_dir / "structural_path_ranking_target.csv"
        hrows = read_csv_rows(hist_path, symbol)
        crows = read_csv_rows(cur_path, symbol)
        history_rows.extend(hrows)
        current_rows.extend(crows)
        contexts.append({
            "symbol": symbol,
            "history_rows": len(hrows),
            "current_rows": len(crows),
            "history_path": str(hist_path.relative_to(REPO)) if hist_path.exists() else None,
            "current_path": str(cur_path.relative_to(REPO)) if cur_path.exists() else None,
        })

    agg_history = AGG_DIR / "aggregate_structural_path_ranking_target_history.csv"
    agg_current = AGG_DIR / "aggregate_structural_path_ranking_target_current.csv"
    write_rows(agg_history, history_rows)
    write_rows(agg_current, current_rows)

    train_dir = AGG_DIR / "catboost_191941_structural_path_ranker_v1"
    scores_file = AGG_DIR / "aggregate_scores.csv"
    if history_rows:
        steps.append(run_step(
            "20_train_catboost_aggregate",
            [
                "/Users/thrill3r/.local/bin/uv", "run", "--offline",
                "--with", "pandas", "--with", "numpy", "--with", "catboost",
                "python", "scripts/auto_quant_external/pandas_path_ranker_trainer.py",
                "--target-csv", agg_history,
                "--output-dir", train_dir,
                "--model-family", "catboost",
            ],
            env={"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1"},
        ))
    if current_rows and train_dir.exists():
        steps.append(run_step(
            "21_apply_catboost_aggregate_current",
            [
                "/Users/thrill3r/.local/bin/uv", "run", "--offline",
                "--with", "pandas", "--with", "numpy", "--with", "catboost",
                "python", "scripts/auto_quant_external/pandas_path_ranker_trainer.py",
                "--apply",
                "--model-dir", train_dir,
                "--target-csv", agg_current,
                "--output-scores", scores_file,
            ],
            env={"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1"},
        ))

    score_rows = read_csv_rows(scores_file, "aggregate") if scores_file.exists() else []
    per_symbol_scores = {}
    if score_rows:
        for symbol in SYMBOLS:
            rows = [row for row in score_rows if row.get("source_symbol") == symbol]
            path = AGG_DIR / f"{safe_name(symbol)}_scores.csv"
            write_rows(path, rows)
            per_symbol_scores[symbol] = path

    trainer_artifact = train_dir / "trainer_artifact.json"
    trainer_json = load_json(trainer_artifact) or {}
    trained_rows = trainer_json.get("trained_rows")
    calibration_rows = trainer_json.get("calibration_rows")

    for symbol in SYMBOLS:
        name = safe_name(symbol)
        score_path = per_symbol_scores.get(symbol)
        if score_path and score_path.exists() and score_path.stat().st_size > 0:
            steps.append(run_step(
                f"30_apply_scores_{name}",
                ["./target/debug/ict-engine", "apply-structural-path-ranking-external-scores", "--symbol", symbol, "--state-dir", STATE_DIR, "--scores-file", score_path],
            ))
        if trainer_artifact.exists():
            register = [
                "./target/debug/ict-engine", "register-structural-path-ranking-trainer-artifact",
                "--symbol", symbol,
                "--state-dir", STATE_DIR,
                "--artifact-uri", trainer_artifact,
                "--model-family", "catboost",
                "--score-column", "raw_path_score",
            ]
            if trained_rows is not None:
                register.extend(["--trained-rows", str(trained_rows)])
            if calibration_rows is not None:
                register.extend(["--calibration-rows", str(calibration_rows)])
            steps.append(run_step(f"31_register_trainer_{name}", register))
            steps.append(run_step(
                f"32_enable_runtime_{name}",
                ["./target/debug/ict-engine", "enable-structural-path-ranking-runtime", "--symbol", symbol, "--state-dir", STATE_DIR, "--reuse-mode", "candidate_set_only"],
            ))
        steps.append(run_step(
            f"40_policy_training_status_{name}",
            ["./target/debug/ict-engine", "policy-training-status", "--symbol", symbol, "--state-dir", STATE_DIR, "--output-format", "json"],
        ))
        steps.append(run_step(
            f"41_workflow_execution_candidate_{name}",
            ["./target/debug/ict-engine", "workflow-status", "--symbol", symbol, "--state-dir", STATE_DIR, "--refresh", "--phase", "execution-candidate", "--output-format", "json"],
        ))

    readbacks = []
    for symbol in SYMBOLS:
        name = safe_name(symbol)
        policy = load_json(COMMAND_DIR / f"40_policy_training_status_{name}.out") or {}
        workflow = load_json(COMMAND_DIR / f"41_workflow_execution_candidate_{name}.out") or {}
        readbacks.append({
            "symbol": symbol,
            "raw_scored_mature": policy.get("path_ranker", {}).get("raw_scored_mature"),
            "production_validation": policy.get("path_ranker", {}).get("production_validation"),
            "observation_validation": policy.get("path_ranker", {}).get("observation_validation"),
            "runtime_selection": policy.get("path_ranker", {}).get("runtime_selection"),
            "candidate_status": workflow.get("candidate_status"),
            "execution_gate_status": workflow.get("execution_gate_status"),
            "execution_readiness": workflow.get("execution_readiness"),
            "actionable": workflow.get("actionable"),
            "ready": workflow.get("ready"),
            "review_status": workflow.get("review_status"),
            "path_ranker_calibrated_path_prob": workflow.get("path_ranker_calibrated_path_prob"),
            "path_ranker_runtime_source": workflow.get("path_ranker_runtime_source"),
        })

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(SRC_ROOT.relative_to(REPO)),
        "state_dir": str(STATE_DIR.relative_to(REPO)),
        "symbols": SYMBOLS,
        "steps_total": len(steps),
        "steps_exit_zero": sum(1 for step in steps if step["exit"] == 0),
        "steps_all_zero": all(step["exit"] == 0 for step in steps),
        "contexts": contexts,
        "aggregate_history_rows": len(history_rows),
        "aggregate_current_rows": len(current_rows),
        "score_rows": len(score_rows),
        "trainer_artifact": str(trainer_artifact.relative_to(REPO)) if trainer_artifact.exists() else None,
        "trained_rows": trained_rows,
        "calibration_rows": calibration_rows,
        "readbacks": readbacks,
        "accepted_95_contexts_added": 0,
        "promotion_allowed": False,
        "trade_usable": False,
        "update_goal": False,
        "steps": steps,
    }
    (AGG_DIR / "191941_structural_path_ranker_extension_v1.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (AGG_DIR / "191941_structural_path_ranker_extension_v1.md").write_text(
        "# 191941 Structural Path-Ranker Extension v1\n\n"
        f"Steps: `{summary['steps_exit_zero']}/{summary['steps_total']}` zero exits.\n\n"
        f"Aggregate history rows: `{len(history_rows)}`.\n\n"
        f"Aggregate current rows: `{len(current_rows)}`.\n\n"
        f"Score rows: `{len(score_rows)}`.\n\n"
        f"Accepted >=95 contexts added: `0`.\n\n"
        "Gate: fail-closed unless mature CatBoost/path-ranker rows, per-regime >=95 confidence, and execution admission all pass.\n"
    )
    print(json.dumps({
        "steps_total": summary["steps_total"],
        "steps_exit_zero": summary["steps_exit_zero"],
        "aggregate_history_rows": len(history_rows),
        "aggregate_current_rows": len(current_rows),
        "score_rows": len(score_rows),
        "accepted_95_contexts_added": 0,
        "promotion_allowed": False,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
