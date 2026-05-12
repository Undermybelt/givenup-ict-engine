#!/usr/bin/env bash
set -u

RUN_ROOT="docs/experiments/actionable-regime-confidence/runs/20260512T150654+0800-codex-145809-volatility-breakout-aq-route-v1"
SYMBOL="B2R_VOL_BREAKOUT_150654"
STATE_DIR="$RUN_ROOT/state_volatility_breakout_v1"
MANIFEST="$RUN_ROOT/derived/strategy_library_volatility_breakout_v1.json"
TRADES="$RUN_ROOT/derived/volatility_breakout_real_trades.jsonl"
TARGET_CSV="$STATE_DIR/$SYMBOL/policy_training/structural_path_ranking_target.csv"
HISTORY_CSV="$STATE_DIR/$SYMBOL/policy_training/structural_path_ranking_target_history.csv"
MODEL_DIR="$RUN_ROOT/path-ranker/catboost_model"
HISTORY_SCORES="$RUN_ROOT/path-ranker/history_scores.csv"
CURRENT_SCORES="$RUN_ROOT/path-ranker/current_scores.csv"

mkdir -p "$RUN_ROOT/command-output" "$RUN_ROOT/checks" "$RUN_ROOT/derived" "$STATE_DIR" "$MODEL_DIR"
printf '%s\n' "$RUN_ROOT" > "$RUN_ROOT/run_root.txt"

run_step() {
  label="$1"
  shift
  printf '%s\n' "$*" > "$RUN_ROOT/command-output/${label}.cmd"
  set +e
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 "$@" \
    > "$RUN_ROOT/command-output/${label}.out" \
    2> "$RUN_ROOT/command-output/${label}.err"
  rc=$?
  set -u
  printf '%s\n' "$rc" > "$RUN_ROOT/checks/${label}.exit"
  return 0
}

run_step 01_build_volatility_breakout_packet \
  /usr/bin/env python3 "$RUN_ROOT/scripts/build_volatility_breakout_packet.py"

run_step 02_auto_quant_results_import \
  ./target/debug/ict-engine auto-quant-results-import \
  --symbol "$SYMBOL" \
  --state-dir "$STATE_DIR" \
  --library "$MANIFEST"

run_step 03_auto_quant_prior_init \
  ./target/debug/ict-engine auto-quant-prior-init \
  --symbol "$SYMBOL" \
  --state-dir "$STATE_DIR" \
  --library "$MANIFEST" \
  --temper 0.5 \
  --prior-strength 4.0

run_step 04_auto_quant_ingest_real_trades \
  ./target/debug/ict-engine auto-quant-ingest-real-trades \
  --symbol "$SYMBOL" \
  --state-dir "$STATE_DIR" \
  --trades "$TRADES" \
  --force

run_step 05_pre_bayes_status \
  ./target/debug/ict-engine pre-bayes-status \
  --symbol "$SYMBOL" \
  --state-dir "$STATE_DIR" \
  --output-format json

run_step 06_policy_training_status_before_export \
  ./target/debug/ict-engine policy-training-status \
  --symbol "$SYMBOL" \
  --state-dir "$STATE_DIR" \
  --output-format json

run_step 07_export_structural_path_target \
  ./target/debug/ict-engine export-structural-path-ranking-target \
  --symbol "$SYMBOL" \
  --state-dir "$STATE_DIR"

run_step 08_policy_training_status_after_export \
  ./target/debug/ict-engine policy-training-status \
  --symbol "$SYMBOL" \
  --state-dir "$STATE_DIR" \
  --output-format json

run_step 09_train_catboost_history \
  /Users/thrill3r/.local/bin/uv run --offline --python 3.11 --with pandas --with numpy --with catboost \
  python scripts/auto_quant_external/pandas_path_ranker_trainer.py \
  --target-csv "$HISTORY_CSV" \
  --output-dir "$MODEL_DIR" \
  --model-family catboost \
  --output-scores "$HISTORY_SCORES"

run_step 10_apply_catboost_current_target \
  /Users/thrill3r/.local/bin/uv run --offline --python 3.11 --with pandas --with numpy --with catboost \
  python scripts/auto_quant_external/pandas_path_ranker_trainer.py \
  --apply \
  --model-dir "$MODEL_DIR" \
  --target-csv "$TARGET_CSV" \
  --output-scores "$CURRENT_SCORES"

run_step 11_apply_external_scores \
  ./target/debug/ict-engine apply-structural-path-ranking-external-scores \
  --symbol "$SYMBOL" \
  --state-dir "$STATE_DIR" \
  --scores-file "$CURRENT_SCORES"

run_step 12_register_catboost_trainer_artifact \
  ./target/debug/ict-engine register-structural-path-ranking-trainer-artifact \
  --symbol "$SYMBOL" \
  --state-dir "$STATE_DIR" \
  --artifact-uri "$MODEL_DIR/trainer_artifact.json" \
  --model-family catboost \
  --score-column raw_path_score

run_step 13_enable_path_ranker_runtime \
  ./target/debug/ict-engine enable-structural-path-ranking-runtime \
  --symbol "$SYMBOL" \
  --state-dir "$STATE_DIR" \
  --reuse-mode candidate_set_only

run_step 14_policy_training_status_after_runtime \
  ./target/debug/ict-engine policy-training-status \
  --symbol "$SYMBOL" \
  --state-dir "$STATE_DIR" \
  --output-format json

run_step 15_workflow_structural_bundle \
  ./target/debug/ict-engine workflow-status \
  --symbol "$SYMBOL" \
  --state-dir "$STATE_DIR" \
  --phase structural-recommended-path-bundle \
  --agent

run_step 16_workflow_execution_candidate \
  ./target/debug/ict-engine workflow-status \
  --symbol "$SYMBOL" \
  --state-dir "$STATE_DIR" \
  --phase execution-candidate \
  --output-format json

run_step 17_workflow_full \
  ./target/debug/ict-engine workflow-status \
  --symbol "$SYMBOL" \
  --state-dir "$STATE_DIR" \
  --refresh \
  --output-format json

for f in "$RUN_ROOT"/checks/*.exit; do
  printf '%s=' "$(basename "$f")"
  tr -d '\n' < "$f"
  printf '\n'
done | sort
