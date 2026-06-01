# IBKR dense K-line practical gates

Use when the operator wants profitability-factor training to move toward practical trading with IBKR-first dense data.

## Operator preference captured

Default direction for this class of run:

- Prefer IBKR as the primary provider when available.
- Prefer trend-following factors for fresh lanes. Add multi-timeframe resonance before trying unrelated factor families.
- Probe the largest usable window per bar size, rather than assuming one duration works for every frame.
- Start from `1min`, then cover `5min`, `15min`, `30min`, and `1h`.
- Let each downstream gate decide: provider acquisition, trend/MTF resonance, Auto-Quant rank when used, IBKR simulated/paper feedback when used, pre-Bayes/filter, BBN/prior, CatBoost/path-ranker, execution tree, mature feedback rows.
- The goal is practical profitability, not a pretty single-stage metric.

## Run pattern

1. Keep the work outside repo docs/state unless the user explicitly asks otherwise.
2. Create an external Board B claim under `/tmp/ict-engine-agent-claims/board-b/`.
3. Probe IBKR runtime and open API port. If the default paper port is refused, inspect likely IBKR ports and use the active one instead of declaring IBKR broken.
4. Fetch QQQ or target symbol in this order:
   - `1 min`: start with max desired window (e.g. `1 M`), then reduce only if IBKR times out.
   - `5 mins`: try quarter/month scale, then reduce if needed.
   - `15 mins`, `30 mins`, `1 hour`: try quarter-scale where possible.
5. Normalize each CSV to `timestamp,open,high,low,close,volume`.
6. Build one Auto-Quant material per timeframe. Every material must carry:
   - `branch_path`
   - `regime_profit_branch_path`
   - `main_regime`
   - `sub_regime`
   - `sub_sub_regime_or_profit_factor`
   - `profit_factor`
   - `provider=ibkr`
   - timeframe and source row count
7. Run material batch/dispatch/rank when Auto-Quant is the chosen validator, then import/prior/analyze/pre-bayes/workflow/export target/CatBoost/apply/register/enable/analyze/workflow/policy-status.
8. When the chosen validator is IBKR simulation/paper feedback instead, first prove the same rooted trend branch has Gate 1 learning viability, then ingest the simulated fills as execution feedback and rerun target export, ranker, execution tree, and policy status. Do not treat simulated fills as live-trade proof.

## Practical decision rule

Do not promote merely because `1min` or `5min` is strong.

- If `5min` is strong but `15min/30min/1h` are negative, mark `incubate` and reshape the branch as:
  - `5min` = primary signal candidate
  - `1min` = entry timing / microstructure confirmation
  - `15min/30min/1h` = higher-timeframe gate, not a co-equal profit signal
- If HTF frames contradict the entry frame, keep execution fail-closed even when CatBoost is visible to the execution tree.
- Promotion remains blocked while any of these hold:
  - `mature_rows=0`
  - `rows_with_training_weight=0`
  - `raw_scored_mature < 30`
  - `production_validation < 30`
  - `observation_validation < 30`
  - execution tree is `observe`, `guarded`, or `transition_guardrail`

## Session evidence shape to preserve

A useful readback table has rows like:

```text
frame rows window auto_quant_status sharpe trades win_rate total_profit gate_decision
1min ... completed ... ... ... ... timing_only/incubate
5min ... completed ... ... ... ... primary_candidate
15min ... completed ... ... ... ... htf_gate
30min ... completed ... ... ... ... htf_gate
1h ... completed ... ... ... ... htf_gate
```

Then read execution-tree machine fields:

- `output.path_ranker_score_visible_to_execution_tree`
- `output.path_ranker_score_used_by_execution_tree`
- `output.path_ranker_model_family`
- `output.consumer_reason`
- `output.gate_status`
- `output.branch`
- `output.execution_bias`

## Pitfalls

- Provider-status ready is not enough; perform actual IBKR fetches for each timeframe.
- IBKR can time out on dense windows. The lesson is to reduce duration per bar size while recording the ceiling, not to abandon IBKR.
- Auto-Quant material rank may preserve branch fields even when the strategy fails. Do not import failed rank rows as strategy-library winners.
- If Python-generated Freqtrade strategy files are used, run `py_compile` before material dispatch; unquoted dataframe column names can make every frame fail.
- Do not mutate compact Board docs during multi-agent work. Record terminal decisions only after evidence exists.
