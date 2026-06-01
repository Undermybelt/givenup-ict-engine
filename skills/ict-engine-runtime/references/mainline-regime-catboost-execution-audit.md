# ICT-Engine mainline regime closure audit

Use when auditing whether `regime -> factor-research -> factor-backtest -> analyze/live -> recommendation` is truly connected, especially primary/secondary market-state regime, BBN/Pre-Bayes, CatBoost/path ranker, and execution-tree trace.

## Proven isolated run pattern

Use an isolated state dir; do not modify repo files while auditing dirty worktrees.

```bash
BASE=/tmp/ict-mainline-regime-audit
STATE=$BASE/state

./target/debug/ict-engine validate-market-state \
  --data $BASE/cleaned-15m/nq.continuous-15m.json \
  --window-size 40 --step-size 5 --profile high_confidence --compact

./target/debug/ict-engine factor-research \
  --symbol NQ --data $BASE/cleaned-15m/nq.continuous-15m.json \
  --data-1m $BASE/cleaned-1m/nq.continuous-1m.json \
  --data-5m $BASE/cleaned-5m/nq.continuous-5m.json \
  --data-15m $BASE/cleaned-15m/nq.continuous-15m.json \
  --data-30m $BASE/cleaned-30m/nq.continuous-30m.json \
  --data-1h $BASE/cleaned-1h/nq.continuous-1h.json \
  --data-4h $BASE/cleaned-4h/nq.continuous-4h.json \
  --data-1d $BASE/cleaned-1d/nq.continuous-1d.json \
  --backend native --state-dir $STATE --output-format json

./target/debug/ict-engine factor-backtest \
  --symbol NQ --data $BASE/cleaned-15m/nq.continuous-15m.json \
  --data-1m $BASE/cleaned-1m/nq.continuous-1m.json \
  --data-5m $BASE/cleaned-5m/nq.continuous-5m.json \
  --data-15m $BASE/cleaned-15m/nq.continuous-15m.json \
  --data-30m $BASE/cleaned-30m/nq.continuous-30m.json \
  --data-1h $BASE/cleaned-1h/nq.continuous-1h.json \
  --data-4h $BASE/cleaned-4h/nq.continuous-4h.json \
  --data-1d $BASE/cleaned-1d/nq.continuous-1d.json \
  --state-dir $STATE --output-format json

./target/debug/ict-engine analyze \
  --symbol NQ --data-root $BASE --state-dir $STATE \
  --output-format json --inline-ledger

./target/debug/ict-engine export-structural-path-ranking-target \
  --symbol NQ --state-dir $STATE

./target/debug/ict-engine apply-structural-path-ranking-external-scores \
  --symbol NQ --state-dir $STATE --scores-file $BASE/scores.csv

./target/debug/ict-engine register-structural-path-ranking-trainer-artifact \
  --symbol NQ --state-dir $STATE \
  --artifact-uri file://$BASE/trainer_artifact.json \
  --model-family catboost --score-column raw_path_score

./target/debug/ict-engine enable-structural-path-ranking-runtime \
  --symbol NQ --state-dir $STATE --reuse-mode prefer_history

./target/debug/ict-engine policy-training-status \
  --symbol NQ --state-dir $STATE --output-format json

./target/debug/ict-engine workflow-status \
  --symbol NQ --state-dir $STATE --output-format json

./target/debug/ict-engine analyze-live \
  --symbol NQ --state-dir $STATE --output-format json
```

## What must be checked

### Regime -> BBN / Pre-Bayes

Positive evidence:
- `analyze*.json.report.supporting.pre_bayes_evidence_filter.evidence_assignments` or agent context bundle contains:
  - `market_state_primary_regime`
  - `market_state_secondary_regime`
  - `market_regime`
  - `liquidity_context`
- `market_state_evidence` contains the full primary/secondary line and dimension line.

Source checkpoints:
- `src/main.rs`: classify with `MarketStateClassifier::new().classify(...)`
- map to BBN labels with `market_state_to_bbn_regime_label` / `market_state_to_bbn_liquidity_label`
- insert `market_state_primary_regime` / `market_state_secondary_regime` into Pre-Bayes assignments
- call `trade_evidence_from_pre_bayes_filter(...)`

### Regime -> execution tree

Positive evidence in `state/<SYM>/execution_tree_trace.json`:
- `output.split_reason_lineage[]` includes lines starting with `market_state=`
- those lines include primary and secondary regime, e.g. `primary_regime=TrendExpansion secondary_regime=BullTrendExhaustion`

Source checkpoints:
- `ExecutionTreeInput.market_state_lineage`
- `DefaultExecutionTreeScorer.score()` copies `market_state_lineage` into `split_reason_lineage`

### CatBoost/path ranker -> execution tree

Positive evidence:
- `policy-training-status` says `structural_path_ranking_runtime.enabled=true`, `ready=true`, `model_family=catboost`, and `active_match_count>0`
- `execution_tree_trace.json.output.split_reason_lineage[]` contains `path_ranker=Ranker runtime: ... trainer_artifact=ready ... runtime_selection=enabled_candidate_set_ready ... runtime_matches=N`

Important nuance:
- Registering `--model-family catboost` proves the external artifact family and explicit score reuse path, not Rust-native CatBoost inference.
- If `raw_scored_mature=0/30` and `calibration=not_fitted`, treat it as wired-but-not-mature, not production-validated.

### Recommendation layer

Positive evidence:
- `analyze*.json.report.supporting.recommended_next_command` exists
- `execution_triage` or supporting execution fields include branch/gate/bias/hint

Known weak point:
- Final `recommended_next_command` may only provide the next CLI command and may not summarize why regime/CatBoost/execution tree chose it. If the task asks for practical advice, inspect and report this as a weak closure unless natural-language reason text includes those lineage causes.

## Coverage table shape

Return compact stage coverage:

| Stage | evidence | diagnostics | lineage | verdict |
|---|---:|---:|---:|---|
| regime primary/secondary | yes/no | yes/no | yes/no | closed/partial/open |
| BBN / Pre-Bayes | yes/no | yes/no | yes/no | closed/partial/open |
| factor-research | yes/no | yes/no | yes/no | closed/partial/open |
| factor-backtest | yes/no | yes/no | yes/no | closed/partial/open |
| CatBoost/path ranker | yes/no | yes/no | yes/no | closed/partial/open |
| execution tree | yes/no | yes/no | yes/no | closed/partial/open |
| recommendation | yes/no | yes/no | yes/no | closed/partial/open |

## Known findings from the mainline audit

- `analyze` and `analyze-live` carry market-state primary/secondary regime into Pre-Bayes and execution-tree trace.
- `factor-research` and `factor-backtest` can have MTF/PDA/factor evidence while not carrying `primary_regime` / `secondary_regime` strings; mark them partial for market-state closure.
- Execution tree lineage can include both `market_state=` and `path_ranker=` lines.
- Path ranker can be enabled and matched with `model_family=catboost` while validation remains insufficient due to `raw_scored_mature=0/30`.
- Recommendation commands exist, but final advice may not explain regime/CatBoost reasons unless execution triage or lineage is explicitly surfaced.