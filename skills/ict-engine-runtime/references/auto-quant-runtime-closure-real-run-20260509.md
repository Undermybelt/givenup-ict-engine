# Auto-Quant real runtime closure run — 2026-05-09

Use as a concrete replay reference when the user rejects sidecar-only work and asks to personally drive Auto-Quant -> filter/analyze -> BBN -> ranker -> execution tree.

## Run root

`/tmp/ict-high-sharpe-real-20260509-234554`

## Decisive command sequence

1. Baseline and provider status:
```bash
./target/debug/ict-engine provider-status --compact
./target/debug/ict-engine analyze \
  --symbol NQ \
  --data-htf examples/demo/demo-15m.json \
  --data-mtf examples/demo/demo-15m.json \
  --data-ltf examples/demo/demo-15m.json \
  --state-dir "$RUN/repo-state" --human
```
Observed: `TrendExpansion/BullTrendAcceleration`, execution `observe/transition_guardrail/guarded`.

2. Bootstrap/prepare Auto-Quant:
```bash
./target/debug/ict-engine auto-quant-bootstrap --state-dir "$RUN/auto-quant"
./target/debug/ict-engine auto-quant-prepare --state-dir "$RUN/auto-quant"
```
Observed prepared workspace root: `$RUN/auto-quant/auto-quant/.deps/auto-quant`.

3. Seed active strategies manually from versioned archive when status says seed required:
```bash
AQ="$RUN/auto-quant/auto-quant/.deps/auto-quant"
cp "$AQ/versions/0.4.1/strategies/RegimeAdaptiveBNB.py" "$AQ/user_data/strategies/RegimeAdaptiveBNB.py"
cp "$AQ/versions/0.4.0/strategies/MomentumMTFConfluence.py" "$AQ/user_data/strategies/MomentumMTFConfluence.py"
```
Inject `# AUTO_QUANT_META v1` if missing before importing to ICT-Engine.

4. Run Auto-Quant directly:
```bash
cd "$AQ"
uv run --with ta-lib run.py > "$RUN/logs/11_auto_quant_run.log" 2>&1
```
Observed strategies:
- `MomentumMTFConfluence`: 854 trades, Sharpe 0.3993, win_rate 34.7775, profit 53.24%, max_dd -23.1801%, pf 1.1682
- `RegimeAdaptiveBNB`: 115 trades, Sharpe 0.1380, win_rate 69.5652, profit 16.41%, max_dd -4.6742%, pf 1.4262

5. Build/import manifest. In this run there was no `export_strategy_library.py` in the managed Auto-Quant checkout. Manual manifest generation had to parse final metric blocks from `run.py` output and emit schema `manifest_version=1.0` with `strategies[]` entries.

Accepted manifest: `$RUN/strategy_library_after_real_auto_quant_run_v3.json`.
Rejected attempts: v1/v2 parsed zero entries; import showed `n_ok=0`; prior-init showed `strategies_applied=[]`.

6. Import and prior-init:
```bash
./target/debug/ict-engine auto-quant-results-import \
  --symbol NQ --state-dir "$RUN/repo-state-v3" \
  --library "$RUN/strategy_library_after_real_auto_quant_run_v3.json" \
  --log "$RUN/logs/11_auto_quant_run.log"

./target/debug/ict-engine analyze \
  --symbol NQ \
  --data-htf examples/demo/demo-15m.json \
  --data-mtf examples/demo/demo-15m.json \
  --data-ltf examples/demo/demo-15m.json \
  --state-dir "$RUN/repo-state-v3" --human

./target/debug/ict-engine auto-quant-prior-init \
  --symbol NQ --state-dir "$RUN/repo-state-v3" \
  --library "$RUN/strategy_library_after_real_auto_quant_run_v3.json"
```
Observed: import `n_ok=2`; `strategies_applied=[MomentumMTFConfluence, RegimeAdaptiveBNB]`; prior changed from `[0.999956,0.000022,0.000022]` to `[0.6734197006771924,0.000000013279761567917304,0.326580286043046]`.

7. Path ranker and execution tree:
```bash
./target/debug/ict-engine export-structural-path-ranking-target \
  --symbol NQ --state-dir "$RUN/repo-state-v3"

python3 scripts/auto_quant_external/pandas_path_ranker_trainer.py \
  --target-csv "$RUN/repo-state-v3/NQ/policy_training/structural_path_ranking_target.csv" \
  --output-dir "$RUN/path_ranker"

python3 scripts/auto_quant_external/pandas_path_ranker_trainer.py \
  --apply --model-dir "$RUN/path_ranker" \
  --target-csv "$RUN/repo-state-v3/NQ/policy_training/structural_path_ranking_target.csv" \
  --output-scores "$RUN/path_scores.csv"

./target/debug/ict-engine apply-structural-path-ranking-external-scores \
  --symbol NQ --state-dir "$RUN/repo-state-v3" \
  --scores-file "$RUN/path_scores.csv"

./target/debug/ict-engine register-structural-path-ranking-trainer-artifact \
  --symbol NQ --state-dir "$RUN/repo-state-v3" \
  --artifact-uri "file://$RUN/path_ranker/path_ranker_direct_model.json" \
  --model-family weighted_feature_sum_v1 \
  --trained-rows 1 --calibration-rows 1

./target/debug/ict-engine enable-structural-path-ranking-runtime \
  --symbol NQ --state-dir "$RUN/repo-state-v3" \
  --reuse-mode candidate_set_only

./target/debug/ict-engine analyze \
  --symbol NQ \
  --data-htf examples/demo/demo-15m.json \
  --data-mtf examples/demo/demo-15m.json \
  --data-ltf examples/demo/demo-15m.json \
  --state-dir "$RUN/repo-state-v3" --human

./target/debug/ict-engine workflow-status \
  --symbol NQ --state-dir "$RUN/repo-state-v3" \
  --phase structural-recommended-path-bundle --human
```
Observed: CatBoost not installed, actual model family `weighted_feature_sum_v1`; target rows 3; mature rows 0; raw scored rows 3; runtime `enabled_registered_model_ready`; final workflow ranker line `using_registered_model_artifact ... applied=3 ... lb=0.489 gate=observe`.

## Pitfalls captured

- Do not count a manifest import as BBN closure until `auto-quant-prior-init` shows non-empty `strategies_applied`.
- A generated manifest with `strategies=[]` can still import cleanly with `n_ok=0`; this is rejected evidence.
- Managed Auto-Quant may not include `export_strategy_library.py`; be ready to build a schema-compatible manifest from `run.py` metric blocks.
- `--log` cross-check can report mismatches due parser limitations (e.g. log values 0) while import `n_ok=2` and prior-init counts are decisive. Record the mismatch, but trust `strategies_applied` for BBN consumption.
- `catboost not installed` means the trainer used `weighted_feature_sum_v1`; never label it CatBoost.
- `runtime_selection` JSON may not expose simple `status/source_kind` top-level keys; verify with CLI logs (`enable...` output and `workflow-status`) rather than a brittle JSON key probe.
- Real closure here does not imply production confidence: mature rows remained `0/30`.
