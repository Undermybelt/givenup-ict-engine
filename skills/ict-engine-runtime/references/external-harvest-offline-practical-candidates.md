# External harvest -> offline practical candidates

Use when the user asks to move closer to practical trading factors by using papers, open-source strategy families, repositories, or social strategy ideas, especially when live provider/API surfaces are flaky. The goal is not to chat about ideas; convert sources into sidecar candidates, benchmark them on existing provider data, and push survivors through ICT Engine.

## Pattern

1. Keep repo docs/boards clean during multi-agent work.
   - Claim under `/tmp/ict-engine-agent-claims/board-b/`.
   - Do not use Board markdown as a lock table.
   - Write only terminal handoff/block rows to compact docs after evidence exists.

2. Use source families as formula inputs, not runtime dependencies.
   - Papers: trend following / TSMOM, volatility momentum, mean reversion, VRP.
   - Repos/frameworks: Alpha101, Qlib kline factors, public Freqtrade idioms.
   - Social/X ideas: treat as hypotheses only; reimplement minimal formula sidecar.
   - Do not copy GPL/AGPL strategy code into runtime.

3. If live source search is flaky, proceed with known source families and record probe status.
   - Example statuses: GitHub intermittent SSL after initial 200, arXiv 429, X timeout.
   - Do not encode these as durable tool failures; they are run evidence only.

4. Benchmark candidates offline on existing normalized provider CSVs.
   - Prefer the current run's `data/normalized/*` and provider provenance matrix.
   - Require provider-level rows for yfinance, TradingViewMCP, IBKR when available.
   - Kraken can be marked blocked only with fetch evidence; do not pretend portability passed.

5. Candidate evaluation should be simple, lookahead-safe, and harsh.
   - Generate signals using only past/current bars.
   - Enter next bar open; exit fixed horizon or deterministic rule.
   - Track total trades, win rate, avg return, profit factor, OOS avg return, provider portability count.
   - Promote no candidate directly; statuses should be `handoff_probe`, `incubate`, or `drop`.

6. Import survivors as an Auto-Quant-shaped strategy library.
   - Preserve branch fields in every strategy metadata:
     - `main_regime`
     - `sub_regime`
     - `sub_sub_regime_or_profit_factor`
     - `profit_factor`
     - `branch_path`
     - `regime_profit_branch_path`
     - `provider_provenance`
     - `source_refs`
   - For selected candidates, set strategy status `ok` for import, while keeping `admission_status` as original `handoff_probe`/`incubate`.

7. Push through the same ICT Engine chain.

```bash
ict-engine auto-quant-results-import --symbol <SYM> --state-dir <RUN>/state --library <library.json>
ict-engine auto-quant-prior-init --symbol <SYM> --state-dir <RUN>/state --library <library.json>
ict-engine analyze --symbol <SYM> --demo --state-dir <RUN>/state --agent
ict-engine pre-bayes-status --symbol <SYM> --state-dir <RUN>/state --refresh --output-format json
ict-engine workflow-status --symbol <SYM> --state-dir <RUN>/state --refresh --agent
ict-engine export-structural-path-ranking-target --symbol <SYM> --state-dir <RUN>/state
python3 support/scripts/auto_quant_external/pandas_path_ranker_trainer.py --target-csv <target.csv> --output-dir <model-dir> --model-family catboost --allow-direct-fallback
python3 support/scripts/auto_quant_external/pandas_path_ranker_trainer.py --apply --model-dir <model-dir> --target-csv <target.csv> --output-scores <scores.csv> --allow-direct-fallback
ict-engine apply-structural-path-ranking-external-scores --symbol <SYM> --state-dir <RUN>/state --scores-file <scores.csv>
ict-engine register-structural-path-ranking-trainer-artifact --symbol <SYM> --state-dir <RUN>/state --artifact-uri file://<model-dir>/trainer_artifact.json --model-family catboost --score-column raw_path_score
ict-engine enable-structural-path-ranking-runtime --symbol <SYM> --state-dir <RUN>/state
ict-engine analyze --symbol <SYM> --demo --state-dir <RUN>/state --agent
ict-engine workflow-status --symbol <SYM> --state-dir <RUN>/state --refresh --agent
ict-engine policy-training-status --symbol <SYM> --state-dir <RUN>/state --output-format agent
```

## Example candidate set from the session

- `paper_tsmom_convexity_pullback_v1` — TSMOM/pullback source refs; reached `handoff_probe` with provider portability across yfinance, TradingViewMCP, and IBKR in the offline benchmark.
- `connors_rsi2_ibs_reclaim_v1` — RSI(2)/IBS mean-reversion; `incubate` when portability is mixed but OOS is non-hostile.
- `atr_expansion_continuation_v1` — ATR expansion continuation; `incubate` when it improves over pure Bollinger/VWAP reclaim but lacks full portability.

Generate Auto-Quant/Freqtrade scripts under `/tmp/.../auto_quant_strategy_scripts/` and verify syntax with `python3 -m py_compile`. These are handoff artifacts, not promotion proof.

## Acceptance readback

Read artifacts, not only exit codes:

- `summary.json` ranks candidates and records source/network probe status.
- `candidate_benchmark_rows.csv` has per-provider rows.
- `strategy_library_import_selected.json` preserves branch fields and `source_refs`.
- `execution_tree_trace.json` has:
  - `path_ranker_score_visible_to_execution_tree=true`
  - `path_ranker_score_used_by_execution_tree=true`
  - `path_ranker_model_family=catboost`
- `workflow-status` exposes the new `regime_profit_branch_path`.
- `policy-training-status` is checked for mature rows and training weights.

## Fail-closed rules

Even a good offline harvest remains not trade-ready if any of these hold:

- Kraken or another required provider is missing/blocked for the stated portability goal.
- `mature_rows=0` or `rows_with_training_weight=0`.
- `ranker=candidate_set/catboost/not_ready`.
- execution tree remains `observe`, `guarded`, or `transition_guardrail`.
- only demo/analyze prior exists without real feedback replay or validated Auto-Quant/Freqtrade backtest.

When blocked, next step is not more idea generation. Next step is to bridge top candidate into offline Auto-Quant/Freqtrade data or real-trade feedback replay so mature target rows and training weights exist.
