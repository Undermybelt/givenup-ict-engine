# Provider-quartet retry + fail-closed CatBoost handoff

Use when a regime-rooted profitability factor must be carried through provider evidence, Auto-Quant, BBN/prior/filter, path ranking, and execution tree, but one or more provider fetches or CatBoost setup steps are flaky.

## Durable lesson

Do not stop at provider-status and do not stop at the first failed fetch. Provider readiness and provider fetch success are separate gates.

Run commands from the operator-like zsh environment or an explicit provider Python when provider dependencies matter:

```bash
zsh -lc 'cd <ict-engine-repo> && .local-artifacts/cargo-target/debug/ict-engine provider-status --compact'
<provider-python> support/scripts/auto_quant_external/fetch_external.py ...
```

If a public provider fails with TLS/EOF/429 on the first attempt, retry with a narrower window or the local stdio route before marking the provider axis blocked. Capture both attempts as evidence.

## Evidence acceptance pattern

For each provider row, record:

- provider id
- symbol / timeframe
- exact command
- exit code
- row count
- normalized CSV path
- `provider_data_acquired=true|false`
- blocker class when false, e.g. `blocked_ssl`, `rate_limited`, `dependency_missing`, `gateway_offline`

Only material rows with actual candles should enter Auto-Quant. Missing provider rows are provider-axis blockers, not factor failures.

## Branch-path invariants

Every material, rank row, strategy-library metadata, and downstream readback must preserve:

```text
main_regime
sub_regime
sub_sub_regime_or_profit_factor
profit_factor
branch_path
regime_profit_branch_path
provider_provenance
```

If any handoff drops these fields, stop before BBN/CatBoost/execution-tree.

## Downstream fail-closed rule

When Auto-Quant rank is positive and branch fields survive:

1. Build a strategy-library manifest copying the branch fields into each strategy `metadata`.
2. Run `auto-quant-results-import` and `auto-quant-prior-init`.
3. Run `analyze`, `pre-bayes-status`, `workflow-status`, and `export-structural-path-ranking-target`.
4. Attempt real CatBoost training with `uv run --with pandas --with numpy --with catboost ...`.
5. If CatBoost install/fetch is blocked, do not claim CatBoost. Record the blocker and let weighted fallback remain explicitly marked as fallback.
6. Apply/register/enable ranker outputs only if the artifacts exist.
7. Rerun analyze/workflow/policy and inspect `execution_tree_trace.json`.

Promotion is forbidden if any of these remain true:

- `path_ranker_model_family` is `weighted_feature_sum_v1` or otherwise not real CatBoost when the task required CatBoost.
- `ranker_validation_ready=false`.
- `mature_rows=0` or `rows_with_training_weight=0`.
- execution tree is `observe`, `guarded`, or `transition_guardrail`.
- closed-loop branch admission is `fail_closed`.

## Minimal terminal decision vocabulary

Use:

```text
incubate_gate1_needs_downstream
handoff_confirmed_fail_closed
blocked_provider_axis
blocked_catboost_setup
promotion_forbidden
```

Never convert a positive AQ rank into a trade-ready claim without BBN/ranker/execution-tree readback.