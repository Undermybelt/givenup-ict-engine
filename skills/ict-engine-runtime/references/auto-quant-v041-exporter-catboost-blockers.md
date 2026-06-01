# Auto-Quant v0.4.1 exporter + CatBoost blocker fixes

Use when Auto-Quant strategies run successfully but ICT-Engine BBN prior init skips them, or when CatBoost training falls back / fails during structural path ranking.

## Symptoms

1. Auto-Quant exporter emits strategies with empty `validation_metrics` even though `run.py` log contains trades.
2. `ict-engine auto-quant-prior-init` reports:
   - `strategies_applied: []`
   - `strategies_skipped: [[..., "trade_count=0"], ...]`
3. `pandas_path_ranker_trainer.py` reports CatBoost missing or crashes after install with:
   - `CatBoostError: NaN values are not supported for target`
4. Trainer emits `path_ranker_direct_model.json` and registration metadata chooses `weighted_feature_sum_v1` even after a real `catboost_model.cbm` exists.

## Root causes

### Exporter root cause

Auto-Quant v0.4.1 emits multiple blocks per strategy:
- one `---` block per timerange (`bull_2021`, `winter_2022`, `recovery_23_25`, `full_5y`)
- one final `timerange_label: SUMMARY` block

Old `export_strategy_library.py` keyed blocks by `strategy` and overwrote earlier blocks with the final `SUMMARY`. That block has `robust_sharpe` but no `trade_count`, so exported `validation_metrics` was empty and BBN prior init skipped every strategy.

### CatBoost root cause

Fresh structural path targets can have:
- `mature_rows=0`
- `calibrated_label=NaN`
- `training_weight` missing/empty

CatBoost cannot train on NaN targets. The trainer also writes a direct fallback artifact before CatBoost training; metadata code must prefer `catboost_model.cbm` when it exists.

## Working fixes

### Exporter patch pattern

Patch `state/.deps/auto-quant/export_strategy_library.py` to:
1. Parse `timerange_label` and `basket` as block-level keys.
2. Parse float values by first token so trailing comments work:
   - `robust_sharpe: 0.1000 # ...`
3. Collect `timerange_blocks[strategy]` separately from `summary_blocks[strategy]`.
4. For v0.4.1 summary + timeranges, export:
   - `trade_count`: sum over timeranges
   - `win_rate_pct`: trade-count-weighted average
   - `profit_factor`: worst positive timerange PF
   - `total_profit_pct`: sum over timeranges
   - `robust_sharpe`: from SUMMARY
   - `worst_profit_pct`: from SUMMARY
   - `max_drawdown_pct`: from SUMMARY `worst_dd_pct`
   - `avg_position_pct`: from SUMMARY
   - `timerange_count`
   - `timerange_metrics`: list of per-regime aggregates and per-pair metrics

Verification command:
```bash
python3 state/.deps/auto-quant/export_strategy_library.py --selftest
```

Expected downstream check:
```bash
./target/debug/ict-engine auto-quant-prior-init \
  --symbol NQ --state-dir /tmp/<run>/repo-state \
  --library /tmp/<run>/strategy_library_after_exporter_fix.json
```

Pass criteria:
- `strategies_applied` non-empty
- `strategies_skipped: []`
- final CPT probabilities changed from initial prior

## CatBoost install/source check

If user asks to get CatBoost from GitHub, verify upstream tags before relying on package:
```bash
git ls-remote --tags https://github.com/catboost/catboost.git | tail -20
python3 - <<'PY'
import catboost
print(catboost.__version__)
PY
```

Known-good observed package:
- GitHub tag: `v1.2.10`
- Python package: `catboost==1.2.10`

Install layer that worked in this repo session:
```bash
python3 -m pip install catboost scikit-learn --break-system-packages
```

Then verify:
```bash
python3 - <<'PY'
import sys, importlib.util, catboost
print(sys.executable)
print(catboost.__version__)
print(importlib.util.find_spec('catboost').origin)
PY
```

## Trainer patch pattern

Patch `scripts/auto_quant_external/pandas_path_ranker_trainer.py`:

1. In `prepare_features()`, if labels are NaN or single-class, derive deterministic pseudo-labels from the best available score column:
   - `structural_baseline_score`
   - else `current_posterior`
   - else `experience_prior`
   - else alternating labels

This allows a real CatBoost model on fresh targets while preserving the warning semantics that calibration is not production-ready.

2. In `build_registered_artifact_metadata()`, prefer real CatBoost if present:
```python
catboost_path = output_dir / "catboost_model.cbm"
direct_model_path = output_dir / "path_ranker_direct_model.json"
if catboost_path.exists():
    model_family = "catboost"
    artifact_uri = str(output_dir)
elif direct_model_path.exists():
    model_family = DIRECT_MODEL_FAMILY
    artifact_uri = str(direct_model_path)
```

Regression test to add:
- direct-only artifact -> `model_family == weighted_feature_sum_v1`
- directory with `catboost_model.cbm` -> `model_family == catboost`

Verification commands:
```bash
python3 scripts/auto_quant_external/tests/test_path_ranker_hotplug.py
python3 -m py_compile \
  state/.deps/auto-quant/export_strategy_library.py \
  scripts/auto_quant_external/pandas_path_ranker_trainer.py \
  scripts/auto_quant_external/tests/test_path_ranker_hotplug.py
```

End-to-end CatBoost check:
```bash
python3 scripts/auto_quant_external/pandas_path_ranker_trainer.py \
  --target-csv /tmp/<run>/repo-state/NQ/policy_training/structural_path_ranking_target.csv \
  --output-dir /tmp/<run>/catboost_path_ranker \
  --model-family catboost

python3 scripts/auto_quant_external/pandas_path_ranker_trainer.py \
  --apply \
  --model-dir /tmp/<run>/catboost_path_ranker \
  --target-csv /tmp/<run>/repo-state/NQ/policy_training/structural_path_ranking_target.csv \
  --output-scores /tmp/<run>/path_scores_catboost.csv
```

Pass criteria:
- `catboost_model.cbm` exists and is non-empty
- trainer artifact says `model_family: catboost`
- apply log says `[apply] CatBoost predictions: <n>`
- ICT Engine status says `trainer_artifact_model_family: catboost`

## Important caveat

These fixes unblock mechanics only. They do not prove calibrated 95% or production readiness. If target state still says:
- `mature_rows=0`
- `production_validation_ready=false`
- `calibration=not_fitted`

then report that production validation is still not ready even though BBN ingestion and CatBoost mechanics are fixed.
