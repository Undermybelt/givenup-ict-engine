# 2026-05-09 Regime -> Execution Mainline Audit Handoff TODO

## Mission

继续审计并补齐 ICT Engine 从 regime 主/子分类到实战建议的主链闭环。

范围：
- regime 主分类 / 子分类
- BBN / Pre-Bayes 证据
- CatBoost / structural path ranker
- execution tree
- analyze / analyze-live / recommended command

硬约束：
- 不混入无关脏改。
- 实验状态只写 `/tmp/...`。
- 先证明 runtime 消费，再谈源码定义。
- 输出必须能给下个 agent 直接接手。

## Route / Skill

- Route alias: `ict-engine-runtime`
- Skill loaded: `~/.hermes/skills/ict-engine/ict-engine-runtime/SKILL.md`
- Reference used: `references/repo-audit-factor-to-execution-closure.md`
- Repo guide read: `AGENTS.md`

## Current git state warning

本 handoff 创建前，repo 已有外部/既有脏改；本审计没有修改代码。

Observed dirty files/untracked:
- `docs/plans/2026-05-09-regime-classifier-research-and-99-confidence-todo.md`
- `src/auto_quant_command.rs`
- `src/validate_market_state_command.rs`
- `scripts/research/regime_discovery_cluster.py`
- `scripts/research/regime_discovery_hmm.py`
- `scripts/research/regime_feature_builder.py`
- `scripts/research/regime_ontology_manifest.py`
- `scripts/research/tests/test_regime_discovery.py`
- `scripts/research/tests/test_regime_feature_builder.py`
- `scripts/research/tests/test_regime_ontology_manifest.py`

Do not commit/revert these unless explicitly scoped.

## What was done

### 1. Previous implementation slice committed

Commit:
- `a0e9b4f thread 30m multi-timeframe PDA evidence`

Validated:
- `cargo check`
- `cargo test --bin ict-engine multi_timeframe -- --nocapture`
- `factor-research` / `factor-backtest` with `cleaned-30m`

Key runtime evidence from previous slice:
- `covered_intervals=1m,5m,15m,30m,1h,4h,1d`
- `structure_ict_pda_context_events=m1:239|m5:239|m15:239|m30:239|h1:239|h4:239|d1:239|w1:0`

### 2. Mainline audit replayed in isolated state

Audit root:
- `/tmp/ict-mainline-regime-audit`

Commands run and passed:
- `cargo check`
- `./target/debug/ict-engine validate-market-state --data /tmp/ict-mainline-regime-audit/cleaned-15m/nq.continuous-15m.json --window-size 40 --step-size 5 --profile high_confidence --compact`
- `./target/debug/ict-engine factor-research --symbol NQ ... --backend native --state-dir /tmp/ict-mainline-regime-audit/state --output-format json`
- `./target/debug/ict-engine factor-backtest --symbol NQ ... --state-dir /tmp/ict-mainline-regime-audit/state --output-format json`
- `./target/debug/ict-engine analyze --symbol NQ --data-root /tmp/ict-mainline-regime-audit --state-dir /tmp/ict-mainline-regime-audit/state --output-format json --inline-ledger`
- `./target/debug/ict-engine export-structural-path-ranking-target --symbol NQ --state-dir /tmp/ict-mainline-regime-audit/state`
- `./target/debug/ict-engine apply-structural-path-ranking-external-scores --symbol NQ --state-dir /tmp/ict-mainline-regime-audit/state --scores-file /tmp/ict-mainline-regime-audit/scores.csv`
- `./target/debug/ict-engine register-structural-path-ranking-trainer-artifact --symbol NQ --state-dir /tmp/ict-mainline-regime-audit/state --artifact-uri file:///tmp/ict-mainline-regime-audit/trainer_artifact.json --model-family catboost --score-column raw_path_score --trained-rows 3 --calibration-rows 0`
- `./target/debug/ict-engine enable-structural-path-ranking-runtime --symbol NQ --state-dir /tmp/ict-mainline-regime-audit/state --reuse-mode prefer_history`
- `./target/debug/ict-engine policy-training-status --symbol NQ --state-dir /tmp/ict-mainline-regime-audit/state --output-format json`
- `./target/debug/ict-engine workflow-status --symbol NQ --state-dir /tmp/ict-mainline-regime-audit/state --output-format json`
- `./target/debug/ict-engine analyze-live --symbol NQ --state-dir /tmp/ict-mainline-regime-audit/state --output-format json`

Generated audit files:
- `/tmp/ict-mainline-regime-audit/validate-market-state.txt`
- `/tmp/ict-mainline-regime-audit/factor-research.json`
- `/tmp/ict-mainline-regime-audit/factor-backtest.json`
- `/tmp/ict-mainline-regime-audit/analyze.json`
- `/tmp/ict-mainline-regime-audit/analyze-after-ranker.json`
- `/tmp/ict-mainline-regime-audit/analyze-live.json`
- `/tmp/ict-mainline-regime-audit/policy-status-after-ranker.json`
- `/tmp/ict-mainline-regime-audit/workflow-status-after-ranker.json`
- `/tmp/ict-mainline-regime-audit/state/NQ/execution_tree_trace.json`

### 3. Field coverage result

| Stage | Evidence | Diagnostics | Lineage | Verdict |
|---|---:|---:|---:|---|
| regime primary/secondary | yes | yes | yes | reaches analyze/live/execution_tree |
| BBN / Pre-Bayes | yes | yes | partial | primary/secondary regime in filtered assignments |
| factor-research | partial | partial | weak | does not consume market_state primary/secondary |
| factor-backtest | partial | partial | weak | does not consume market_state primary/secondary |
| CatBoost/path ranker | yes | yes | yes | policy-status + execution_tree lineage visible |
| execution tree | yes | yes | yes | market_state + path_ranker reach trace |
| recommendation | yes | partial | weak | command exists, reasons not deeply surfaced |

### 4. Runtime evidence found

`validate-market-state.txt`:
- `samples=9 avg_confidence=74.00% high_confidence=33.33% tradeable=100.00% primary_top=RangeConsolidation:6 secondary_top=WideRange:5`

`analyze-after-ranker.json`:
- `market_state_primary_regime=RangeConsolidation`
- `market_state_secondary_regime=WideRange`
- `pre_bayes_filtered_assignments.market_regime=range`
- `pre_bayes_filtered_assignments.liquidity_context=favorable`
- `pre_bayes_gate_status=pass_neutralized`

`analyze-live.json`:
- `market_state_primary_regime=TrendExpansion`
- `market_state_secondary_regime=BullTrendExhaustion`
- `pre_bayes_filtered_assignments.market_regime=bull`
- `pre_bayes_filtered_assignments.liquidity_context=neutral`
- execution triage:
  - `branch=transition_guardrail`
  - `gate_status=observe`
  - `execution_bias=guarded`
  - `decision_hint=execution_guarded_due_to_high_transition_hazard`

`policy-status-after-ranker.json`:
- `structural_path_ranking_runtime.enabled=true`
- `ready=true`
- `model_family=catboost`
- `active_match_count=3`
- `status=enabled_candidate_set_ready`
- validation still not mature:
  - `raw_scored_mature=0/30`
  - `production_validation=0/30`
  - `observation_validation=0/30`
  - `calibration=not_fitted`

`execution_tree_trace.json` lineage:
- `market_state=primary_regime=TrendExpansion secondary_regime=BullTrendExhaustion overall_confidence=0.553`
- `market_state=volatility=LowVol:0.779 liquidity=NormalLiquidity:0.363 structure=Trending:0.634 behavior=Neutral:0.450`
- `path_ranker=Ranker runtime: ... trainer_artifact=ready ... runtime_selection=enabled_candidate_set_ready runtime_mode=prefer_history runtime_source=candidate_set runtime_matches=3`
- `path_ranker=Ranker validation: calibration=false ... raw_scored_mature=0/30 ... ready=false`
- `hmm_posterior=(acc=0.286, manip=0.429, dist=0.286)`
- `hybrid_transition_hazard=0.607`

### 5. Source trace confirmed

Regime classification and BBN/Pre-Bayes bridge:
- `src/main.rs:4084-4094` classifies `MarketStateClassifier` and maps market state to BBN regime/liquidity labels.
- `src/main.rs:4177-4189` inserts `market_state_primary_regime` and `market_state_secondary_regime` into `pre_bayes_evidence_filter.evidence_assignments` and rationale.
- `src/main.rs:4191` converts Pre-Bayes filter into BBN evidence via `trade_evidence_from_pre_bayes_filter(...)`.

Execution tree bridge:
- `src/main.rs:4624-4634` reads path-ranker runtime/validation lineage from `policy_training_status`.
- `src/main.rs:4636-4644` passes `market_state_lineage` and `path_ranker_lineage` into `ExecutionTreeInput`.
- `src/application/orchestration/execution_tree.rs:344-352` writes market_state and path_ranker lineage into execution tree split reasons.

## Current verdict

Mainline status: runnable and mostly connected.

Closed enough:
- regime primary/secondary reaches analyze/live Pre-Bayes assignments.
- regime evidence reaches BBN soft evidence path through Pre-Bayes.
- regime and path-ranker lineage reaches execution_tree_trace.
- CatBoost-labeled external ranker artifact can be registered, enabled, and surfaced in execution tree lineage.

Not closed enough:
- `factor-research` and `factor-backtest` do not consume/report market_state primary/secondary classification.
- CatBoost path is external-score/registered-artifact integration, not proven Rust-native CatBoost inference.
- Ranker validation remains immature with `0/30` mature rows in this audit state.
- Final recommendation is command-oriented; it does not yet summarize regime + CatBoost + execution-tree reasons in the practical advice text.

## TODO - should do next

### P0 - Do not pollute repo state

- [ ] Re-run `git status --short` before any edit.
- [ ] Confirm ownership of existing dirty/untracked files listed above.
- [ ] Do not format whole repo unless explicitly asked.
- [ ] If editing, only stage files touched in this slice.

### P1 - Close factor-research / factor-backtest market_state gap

- [ ] Add market_state classification to `factor-research` runtime.
- [ ] Add market_state classification to `factor-backtest` runtime.
- [ ] Emit `market_state_primary_regime` / `market_state_secondary_regime` in:
  - [ ] `report.multi_timeframe_summary` or equivalent compact evidence field
  - [ ] `agent_context_bundle.pre_bayes_filtered_assignments` when applicable
  - [ ] `reflection_bundle` / postmortem evidence if present
- [ ] Add tests proving `factor-research` output contains primary/secondary regime.
- [ ] Add tests proving `factor-backtest` output contains primary/secondary regime.
- [ ] Re-run:
  - [ ] `cargo check`
  - [ ] `cargo test --bin ict-engine multi_timeframe -- --nocapture`
  - [ ] targeted test filter for new market_state report tests

### P2 - Make recommendation explain why, not only what command

- [ ] Add execution-tree reason summary to `recommended_next_command_meta` or adjacent field.
- [ ] Include at least:
  - [ ] `market_state_primary_regime`
  - [ ] `market_state_secondary_regime`
  - [ ] execution tree branch/gate/bias
  - [ ] path-ranker runtime status and source
  - [ ] ranker validation readiness
- [ ] Ensure `--human` / `--agent` output remains compact.
- [ ] Verify `analyze --human` and `analyze-live --human` show the reason line.

### P3 - Make CatBoost/path-ranker consumption explicit

- [ ] Add machine fields, not only text lineage:
  - [ ] `path_ranker_score_used_by_execution_tree: bool`
  - [ ] `path_ranker_model_family`
  - [ ] `path_ranker_runtime_source`
  - [ ] `candidate_set_id`
  - [ ] `path_id` if selected
  - [ ] `ranker_validation_ready`
- [ ] Surface these fields in `execution_tree_trace.json`.
- [ ] Surface compact summary in `workflow-status`.
- [ ] Add test proving CatBoost-registered artifact appears in execution tree trace.

### P4 - Validate mature ranker path separately

- [x] Reuse mature state if available, e.g. prior handoff mentioned `/tmp/ict-engine-structural-replay-29/state`.
- [x] Run:
  - [x] `policy-training-status --symbol NQ --state-dir <mature-state> --human`
  - [x] `workflow-status --symbol NQ --state-dir <mature-state> --human`
  - [x] `workflow-status --phase structural-recommended-path-bundle --human`
- [x] Confirm whether registered-model artifact changes execution recommendation vs candidate-set fallback.
- [x] Record whether validation floor is target-row or observation-row.

P4 result (2026-05-09):
- Mature state exists: `/tmp/ict-engine-structural-replay-29/state`.
- Copied for comparison:
  - registered: `/tmp/ict-mainline-regime-audit/state-mature-ranker-registered`
  - disabled: `/tmp/ict-mainline-regime-audit/state-mature-ranker-disabled`
- Runtime registered-model status:
  - `runtime_selection=enabled_registered_model_ready`
  - `runtime_mode=candidate_set_only`
  - `runtime_source=registered_model_artifact`
  - `runtime_matches=1`
- Validation:
  - `raw_scored_mature=2/30`
  - `production_validation=2/30`
  - `observation_validation=30/30`
  - `calibration=evaluated`
  - `ready=true`
- Interpretation: readiness is satisfied by observation validation despite target-row / production validation remaining `2/30`. The `raw_scored_mature` floor is target-row style, but `quality_ready=true` and `ready=true` can pass when observation validation reaches `30/30`.
- Registered-model vs disabled runtime recommendation:
  - `workflow-status --phase structural-recommended-path-bundle --human` produced the same selected path and next command in this state.
  - Difference is visible in policy status/runtime source, not in the structural path bundle recommendation text.
- Evidence files:
  - `/tmp/ict-mainline-regime-audit/policy-status-mature-registered-human.txt`
  - `/tmp/ict-mainline-regime-audit/policy-status-mature-disabled-human.txt`
  - `/tmp/ict-mainline-regime-audit/path-bundle-mature-registered-human.txt`
  - `/tmp/ict-mainline-regime-audit/path-bundle-mature-disabled-human.txt`

### P5 - Optional cleanup / documentation

- [ ] Update `AGENTS.md` only if factor/regime routing changed.
- [ ] Add this audit result to a stable docs/audits file if needed.
- [ ] If implementation done, commit with narrow message, e.g. `thread market-state regime through factor reports`.

## Reproduction notes

To rerun current audit quickly:

1. Use sample root:
   - `/tmp/ict-mainline-regime-audit`
2. If missing, recreate from prior synthetic sample:
   - `/tmp/ict-mtf-30m-pda-verify`
3. Re-run chain in order:
   - validate market state
   - factor-research
   - factor-backtest
   - analyze
   - export structural path target
   - generate `scores.csv`
   - apply scores
   - register trainer artifact as `catboost`
   - enable runtime
   - analyze again
   - workflow-status
   - analyze-live if network/backend available

Important: `cargo check` is currently passing despite dirty files.
