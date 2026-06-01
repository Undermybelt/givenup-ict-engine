# Regime-rooted provider Auto-Quant chain

Use when a profit-factor task requires regime roots to survive through Auto-Quant, BBN, CatBoost/path-ranker, and execution tree, especially in multi-agent Board B style work.

## Non-negotiable shape

Every material package must carry the branch ontology in `consumer_evidence_profile`:

- `branch_path`
- `regime_profit_branch_path`
- `main_regime`
- `sub_regime`
- `sub_sub_regime_or_profit_factor`
- `profit_factor`
- `provider`

Expected branch shape:

```text
<main_regime> -> <sub_regime> -> <sub_sub_regime_or_profit_factor> -> <profit_factor>
```

Example:

```text
TrendExpansion -> SessionLiquidity -> runtime_density_upbar_reclaim -> runtime_density_upbar_reclaim_long_v1
```

## Run pattern

1. Before touching Board docs, claim a unique lane in the authoritative plan/doc. Do not reuse an active or completed factor branch.
2. Build one material JSON per provider. Include `source_provider=...` and `branch_path=...` notes.
3. Run Auto-Quant material batch/dispatch/rank:

```bash
./target/debug/ict-engine auto-quant-agent-material-batch \
  --symbol <SYM> --state-dir <RUN>/state --max-parallel 4 \
  --material <provider-a.material.json> \
  --material <provider-b.material.json>

./target/debug/ict-engine auto-quant-agent-material-dispatch \
  --symbol <SYM> --state-dir <RUN>/state

./target/debug/ict-engine auto-quant-agent-material-rank \
  --symbol <SYM> --state-dir <RUN>/state
```

4. Verify rank rows still contain all branch fields. If fields are absent, stop; do not continue into BBN/CatBoost.
5. Convert the rank artifact into a strategy-library manifest only if it has usable trade counts and metrics, then import and prior-init:

```bash
./target/debug/ict-engine auto-quant-results-import \
  --symbol <SYM> --state-dir <RUN>/state --library <strategy_library.json>

./target/debug/ict-engine auto-quant-prior-init \
  --symbol <SYM> --state-dir <RUN>/state --library <strategy_library.json>
```

6. Run `analyze`, `factor-research`, and `factor-backtest` on explicit persisted market-data paths, not guessed source paths.
7. Export structural path target, train/apply/register CatBoost, enable runtime, then rerun `analyze` so execution tree consumes the ranker score.
8. Validate by reading `execution_tree_trace.json`, not just `workflow-status`.

## Acceptance evidence

Minimum evidence bundle:

- `checks/02_agent_material_dispatch.json`
- `checks/03_agent_material_rank.json`
- `checks/05_auto_quant_prior_init.json`
- `checks/10_path_ranker_train.stdout`
- `checks/15_policy_training_status.json`
- `<state>/<SYM>/execution_tree_trace.json`

Required fields in execution trace:

- `path_ranker_score_visible_to_execution_tree=true`
- `path_ranker_score_used_by_execution_tree=true`
- `path_ranker_model_family=catboost`
- `consumer_reason` includes market state + execution + ranker status

## Promotion vs incubate

Do not promote merely because the chain runs. Incubate/block when any of these remain true:

- provider portability is negative or only one provider is weakly positive
- `raw_scored_mature < 30`
- `production_validation < 30`
- `observation_validation < 30`
- execution tree remains `observe`, `guarded`, or `transition_guardrail`
- ranker validation is `not_ready` / `present_validation_insufficient`

## Repo hygiene

Auto-Quant may bootstrap a large `.deps/auto-quant/.venv` under experiment state. If the evidence files do not need the dependency checkout, remove `<RUN>/state/auto-quant/.deps` before final handoff and verify the run directory size.

Never delete the state artifacts, logs, ranker outputs, or execution traces that support the readback.
