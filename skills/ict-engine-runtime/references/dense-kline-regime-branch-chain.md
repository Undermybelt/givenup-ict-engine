# Dense K-line regime-branch chain

Use this reference when the user asks to increase samples with `1m/5m/15m/30m` candles while preserving regime-rooted profitability branch paths through Auto-Quant -> BBN -> CatBoost -> execution tree.

## Shape

Keep one branch lane narrow:

```text
<main_regime> -> <sub_regime> -> <sub_sub_regime_or_profit_factor> -> <profit_factor>
```

Every material must carry:

- `branch_path`
- `regime_profit_branch_path`
- `main_regime`
- `sub_regime`
- `sub_sub_regime_or_profit_factor`
- `profit_factor`
- provider label and timeframe (`1m/5m/15m/30m`)
- source row count

## Run pattern

1. Claim the lane in the Board doc before touching data or Auto-Quant.
2. Fetch or reuse dense K-line data per provider/timeframe. Record failed provider attempts as evidence, but do not hard-code the provider as broken.
3. Normalize OHLCV to CSV with `timestamp,open,high,low,close,volume`.
4. Set material `timerange` to a valid `YYYYMMDD-YYYYMMDD` derived from the data. Do not use prose like `source_artifact_window`; Freqtrade rejects it before backtest.
5. Run:

```bash
./target/debug/ict-engine auto-quant-agent-material-batch --symbol <SYM> --state-dir <RUN>/state --repo-url <local-auto-quant-if-needed> --max-parallel 4 --material ...
./target/debug/ict-engine auto-quant-agent-material-dispatch --symbol <SYM> --state-dir <RUN>/state
./target/debug/ict-engine auto-quant-agent-material-rank --symbol <SYM> --state-dir <RUN>/state
```

If GitHub clone fails but a recent Auto-Quant checkout exists under another run's `state/auto-quant/.deps/auto-quant`, pass it via `--repo-url <local-path>`.

6. Build a strategy-library manifest from completed rank rows only, preserving branch metadata, then run:

```bash
./target/debug/ict-engine auto-quant-results-import --symbol <SYM> --state-dir <RUN>/state --library <library.json>
./target/debug/ict-engine auto-quant-prior-init --symbol <SYM> --state-dir <RUN>/state --library <library.json>
```

7. Run analyze/workflow/pre-bayes/export target.
8. Train CatBoost, then apply it. Training alone writes model/artifact, not score CSV:

```bash
python3 scripts/auto_quant_external/pandas_path_ranker_trainer.py --target-csv <target.csv> --output-dir <model-dir> --model-family catboost
python3 scripts/auto_quant_external/pandas_path_ranker_trainer.py --apply --model-dir <model-dir> --target-csv <target.csv> --output-scores <scores.csv>
```

9. Apply/register/enable scores, rerun analyze, then inspect `state/<SYM>/execution_tree_trace.json`.

## Validation

Read `execution_tree_trace.json` under the nested `output` object. Required fields:

- `output.path_ranker_score_visible_to_execution_tree=true`
- `output.path_ranker_score_used_by_execution_tree=true`
- `output.path_ranker_model_family=catboost`
- `output.consumer_reason` includes market state, execution state, and ranker readiness

Do not promote when:

- 1m/5m are positive but 15m/30m are negative in the same mixed packet
- TVR or another provider failed fetch and no comparable slice exists
- `raw_scored_mature=0/30`, `production_validation=0/30`, or `observation_validation=0/30`
- execution remains `observe`, `transition_guardrail`, or `guarded`

## Readback

Summarize by provider/timeframe table and state a terminal decision (`incubate`, `blocked`, `handoff`, `drop`, or `promote`). Mention that dense K-lines increased sample count only if the rank rows show materially higher trade counts.