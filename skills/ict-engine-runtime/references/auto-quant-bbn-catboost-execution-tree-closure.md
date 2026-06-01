# Auto-Quant -> BBN -> path ranker -> execution tree closure

Use when the user demands a real end-to-end ICT-Engine runtime closure, especially with language like "不要意淫", "亲自操控", "过过滤波/信念网络/CatBoost/执行树".

## Required posture

Do not summarize existing artifacts as if they were freshly run. Run the actual chain and preserve logs under a no-pollution state root such as `/tmp/ict-regime-verified-<timestamp>`.

Report three things separately:
- regime coverage: which regimes/timeranges had samples
- empirical performance: win rate / sharpe / profit / drawdown
- calibrated 95% confidence: Wilson/lower-bound or other explicit calibration evidence

If coverage is present but calibrated 95% is absent, say so directly.

## Working closure sequence

1. Establish ICT-Engine baseline:
```bash
./target/debug/ict-engine analyze \
  --symbol NQ \
  --data-htf <candles.json> \
  --data-mtf <candles.json> \
  --data-ltf <candles.json> \
  --state-dir /tmp/<run>/repo-state \
  --human | tee /tmp/<run>/01_analyze.log
```

2. Bootstrap/prepare Auto-Quant in an isolated state dir:
```bash
./target/debug/ict-engine auto-quant-bootstrap --state-dir /tmp/<run>/auto-quant
./target/debug/ict-engine auto-quant-prepare --state-dir /tmp/<run>/auto-quant
```

3. Seed active strategy files under Auto-Quant `user_data/strategies/` if status says `auto_quant_seed_strategies_required`. Existing versioned strategies can be copied from `versions/<ver>/strategies/`, but they may lack `AUTO_QUANT_META`.

4. If exporting to ICT-Engine, strategy files need an `AUTO_QUANT_META v1` block with required fields:
`Strategy`, `Mutation_id`, `Base_factor`, `Hypothesis`, `Paradigm`, `Expected_regime`, `Factors_used`, `Parent`, `Asset_class`, `Status`.

5. Run Auto-Quant directly and capture the complete log:
```bash
cd /tmp/<run>/auto-quant/auto-quant/.deps/auto-quant
uv run --with ta-lib run.py > /tmp/<run>/08_auto_quant_run.log 2>&1
```

6. Export strategy library and import it:
```bash
python3 state/.deps/auto-quant/export_strategy_library.py \
  --strategies-dir /tmp/<run>/auto-quant/auto-quant/.deps/auto-quant/user_data/strategies \
  --log /tmp/<run>/08_auto_quant_run.log \
  --config /tmp/<run>/auto-quant/auto-quant/.deps/auto-quant/config.json \
  --output /tmp/<run>/strategy_library_after_run.json

./target/debug/ict-engine auto-quant-results-import \
  --symbol NQ --state-dir /tmp/<run>/repo-state \
  --library /tmp/<run>/strategy_library_after_run.json
```

7. Apply BBN prior init, but verify `strategies_applied`; do not assume import means BBN consumed it:
```bash
./target/debug/ict-engine auto-quant-prior-init \
  --symbol NQ --state-dir /tmp/<run>/repo-state \
  --library /tmp/<run>/strategy_library_after_run.json
```

8. Export structural path target, train/apply ranker, then inspect execution tree:
```bash
./target/debug/ict-engine export-structural-path-ranking-target \
  --symbol NQ --state-dir /tmp/<run>/repo-state

python3 scripts/auto_quant_external/pandas_path_ranker_trainer.py \
  --target-csv /tmp/<run>/repo-state/NQ/policy_training/structural_path_ranking_target.csv \
  --output-dir /tmp/<run>/path_ranker

python3 scripts/auto_quant_external/pandas_path_ranker_trainer.py \
  --apply --model-dir /tmp/<run>/path_ranker \
  --target-csv /tmp/<run>/repo-state/NQ/policy_training/structural_path_ranking_target.csv \
  --output-scores /tmp/<run>/path_scores.csv

./target/debug/ict-engine apply-structural-path-ranking-external-scores \
  --symbol NQ --state-dir /tmp/<run>/repo-state \
  --scores-file /tmp/<run>/path_scores.csv

./target/debug/ict-engine workflow-status \
  --symbol NQ --state-dir /tmp/<run>/repo-state \
  --phase structural-recommended-path-bundle --human
```

## Known pitfalls

- `factor-research --auto-quant-profile synthetic_ohlcv` can create a handoff but still report `dependency_ready_data_missing`; check `auto-quant-status` and prepare/bootstrap as directed.
- Passing nested `--state-dir` values can create repeated `/auto-quant/auto-quant/...` paths. Follow the CLI's returned state path, but keep the run root clear.
- Versioned Auto-Quant strategies may run fine but lack `AUTO_QUANT_META`; exporter then marks `meta_invalid` and emits zero strategies.
- Managed Auto-Quant checkouts may not contain `export_strategy_library.py`; if missing, generate a schema-compatible `manifest_version=1.0` strategy library from the final `run.py` metric blocks, then validate with `auto-quant-results-import`.
- A manifest with `strategies=[]` can still import with `n_ok=0`; this is rejected evidence, not closure.
- The exporter/log cross-check may parse v0.4.1 timerange logs poorly: `validation_metrics` can be `{}` or log values can appear as zero even when the run log has trades. The decisive BBN check is `auto-quant-prior-init` showing non-empty `strategies_applied` with non-zero `trade_count`.
- `pandas_path_ranker_trainer.py` falls back to `weighted_feature_sum_v1` when `catboost` is not installed. Do not call that CatBoost. Register with the actual `model_family` reported by `trainer_artifact.json`.
- A structural path target with `mature_rows=0` and `production_validation_ready=false` cannot support production/calibrated 95% claims.
- Execution-tree output such as `posterior=0.391 selected_prob=0.376` is the final runtime decision, not a 95% regime acceptance.

## Concrete replay reference

See `references/auto-quant-runtime-closure-real-run-20260509.md` for a full real run where Auto-Quant was bootstrapped/prepared, archived strategies were seeded, `run.py` was executed, a manual v3 manifest was accepted (`n_ok=2`), BBN consumed two strategies, ranker fallback was registered, and workflow-status surfaced the execution-tree/ranker result.

## 95% audit pattern

For regime/outcome claims, compute lower bounds rather than quoting raw win rate:
```python
z = 1.96
ph = wins / n
denom = 1 + z*z/n
center = ph + z*z/(2*n)
margin = z * ((ph*(1-ph) + z*z/(4*n))/n) ** 0.5
wilson95_lower = (center - margin) / denom
```

If the best raw slice is below 95%, or the Wilson 95% lower bound is below 95%, the answer is "not 95%" even if every regime has coverage.
