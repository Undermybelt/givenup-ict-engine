# Provider-quartet regime-rooted AQ chain

Use when Board B asks for a profitability factor to be rooted by regime and carried through provider data, Auto-Quant, BBN/prior/filter, CatBoost/path-ranker, and execution tree with IBKR, TradingViewRemix/tradingview_mcp, yfinance, and Kraken evidence.

## Why this exists

A user correction made the acceptance shape stricter than a readback/audit: do not infer from docs. Run the providers and the chain, and preserve the branch path as data.

Required branch shape:

```text
<main_regime> -> <sub_regime> -> <sub_sub_regime_or_profit_factor> -> <profit_factor>
```

Minimum first-class fields in every material/rank/manifest handoff:

- `main_regime`
- `sub_regime`
- `sub_sub_regime_or_profit_factor`
- `profit_factor`
- `branch_path`
- `regime_profit_branch_path`
- provider provenance

## Run shape

1. Create only an external claim under `/tmp/ict-engine-agent-claims/board-b/`; do not use the board markdown as a lock table.
2. Probe provider readiness with direct binary `provider-status --provider ... --agent`, then perform actual fetches. Provider ready is not enough.
3. Fetch each provider as its own evidence row:
   - yfinance via `market-data-harness` where possible.
   - TradingViewRemix via `tradingview_mcp` local stdio where available.
   - IBKR via full request JSON with explicit contract, e.g. `symbol/sec_type/exchange/currency`.
   - Kraken via `support/scripts/auto_quant_external/fetch_external.py kraken-kline` when harness role mapping lacks `kraken_public`.
4. Normalize provider outputs to `timestamp,open,high,low,close,volume` CSV before material creation. Kraken CSV may emit `date`; rewrite to `timestamp`.
5. Build one Auto-Quant material JSON per provider. Use a valid `YYYYMMDD-YYYYMMDD` `timerange` derived from data, not prose.
6. Run:

```bash
ict-engine auto-quant-agent-material-batch --symbol <SYM> --state-dir <RUN>/state --repo-url <local-aq-if-needed> --material ...
ict-engine auto-quant-agent-material-dispatch --symbol <SYM> --state-dir <RUN>/state
ict-engine auto-quant-agent-material-rank --symbol <SYM> --state-dir <RUN>/state
```

7. Stop if rank rows lose branch fields.
8. Build/import a strategy-library manifest that copies the branch fields into strategy metadata, then run:

```bash
ict-engine auto-quant-results-import --symbol <SYM> --state-dir <RUN>/state --library <library.json>
ict-engine auto-quant-prior-init --symbol <SYM> --state-dir <RUN>/state --library <library.json>
```

9. Run analyze/filter/readbacks, then export target and do a two-pass CatBoost path-ranker:

```bash
ict-engine analyze --symbol <SYM> --demo --state-dir <RUN>/state --human
ict-engine pre-bayes-status --symbol <SYM> --state-dir <RUN>/state --refresh --output-format json
ict-engine workflow-status --symbol <SYM> --state-dir <RUN>/state --refresh --agent
ict-engine export-structural-path-ranking-target --symbol <SYM> --state-dir <RUN>/state
python3 support/scripts/auto_quant_external/pandas_path_ranker_trainer.py --target-csv <target.csv> --output-dir <model-dir> --model-family catboost --allow-direct-fallback
python3 support/scripts/auto_quant_external/pandas_path_ranker_trainer.py --apply --model-dir <model-dir> --target-csv <target.csv> --output-scores <scores.csv> --allow-direct-fallback
ict-engine apply-structural-path-ranking-external-scores --symbol <SYM> --state-dir <RUN>/state --scores-file <scores.csv>
ict-engine register-structural-path-ranking-trainer-artifact --symbol <SYM> --state-dir <RUN>/state --artifact-uri file://$PWD/<model-dir>/trainer_artifact.json --model-family catboost --score-column raw_path_score
ict-engine enable-structural-path-ranking-runtime --symbol <SYM> --state-dir <RUN>/state
ict-engine analyze --symbol <SYM> --demo --state-dir <RUN>/state --human
ict-engine workflow-status --symbol <SYM> --state-dir <RUN>/state --refresh --agent
ict-engine policy-training-status --symbol <SYM> --state-dir <RUN>/state --output-format agent
```

If `uv run --with pandas --with numpy --with catboost ...` fails on PyPI/TLS/DNS but CatBoost is already installed in the user Python, use `<operator-python>` for both train and apply passes. This host has CatBoost under `<operator-python-site-packages>`; do not stop at uv network failure.

## Acceptance readback

Read artifacts, do not trust command exit alone:

- `auto_quant_agent_material_rank` has all branch fields for every provider row.
- `auto-quant-prior-init` exits 0 and writes BBN prior evidence.
- `structural_path_ranking_target_summary.json` reports target rows and score rows.
- `execution_tree_trace.json` under `output` has:
  - `path_ranker_score_visible_to_execution_tree=true`
  - `path_ranker_score_used_by_execution_tree=true`
  - `path_ranker_model_family=catboost`
  - `consumer_reason` includes market state, execution state, and ranker readiness.

## Fail-closed decision rules

Even when the full chain runs, do not promote if:

- provider portability is mixed or negative on any required leg;
- `mature_rows=0` or `rows_with_training_weight=0`;
- ranker is consumed but marked `not_ready`;
- execution remains `observe`, `guarded`, or `transition_guardrail`.

Write a terminal `handoff`, `blocked`, `drop`, or `incubate` row to the compact Board B current doc only after evidence exists.
