# Factor Iteration Filter-Belief-CatBoost-Execution-Tree Board

> Authoritative execution board for factor iteration only.  
> This file is intentionally limited to the factor iteration path that must close the loop through pre-bayes filters, belief / BBN evidence, CatBoost-compatible path ranking, and execution-tree consumption.  
> Do not mix provider bootstrap, generic runtime closure, or unrelated repo UX work into this board.

**Goal:** produce factor candidate packs that can be iterated externally, evaluated across markets/timeframes, mapped explicitly into `pre_bayes -> belief / BBN -> structural path ranking -> execution tree`, and handed off only after they satisfy breadth, density, resonance, and structural-feedback requirements.

**Architecture:** keep `ict-engine` runtime generic and read-only. Factor iteration happens through external factor/strategy code and additive helper artifacts. Every promoted candidate must first exist as an explicit white-box factor pack, then prove which middle-layer surfaces it feeds, then prove breadth / density / resonance, and only then become eligible for the post-factor runtime-closure board.

**Tech Stack:** `scripts/research/factor_candidate_pack.py`, `scripts/research/path_rule_trainer.py`, `scripts/auto_quant_external/*`, `./target/debug/ict-engine factor-research --backend auto-quant`, `factor-autoresearch-status`, `workflow-status --phase structural-playbook`, `workflow-status --phase structural-recommended-path-bundle`, `policy-training-status`, explicit `/tmp/...` state dirs, JSON artifact packs.

**Hard Constraints**

- Only factor iteration content belongs here.
- No provider bootstrap, no generic workflow UX, no first-run remediation, no unrelated runtime refactors.
- Keep the runtime boundary explicit: `offline factor iteration -> explicit artifact -> runtime read-only consume`.
- Do not promote a factor family from one market or one thin trade cell alone.
- Do not treat regime F1, path-ranking readiness, or execution-tree movement as interchangeable; each layer needs its own evidence.
- Keep all promotion evidence explicit, reviewable, and `/tmp/...` isolated.

**Layer Contract**

Every candidate pack must declare all five of these:

1. `pre_bayes_targets`
2. `belief_targets`
3. `path_ranking_targets`
4. `execution_tree_targets`
5. `structural_feedback_required`

If any of the above is missing, the candidate is incomplete and cannot close the loop.

**Required Candidate Pack Artifacts**

- `factor_expression.json`
- `factor_eval_grid_summary.json`
- `transfer_score.json`

`factor_expression.json` must carry:

- `expression_text`
- `operator_set`
- `complexity`
- `target_market_hypothesis`
- `base_timeframe`
- `context_timeframes`
- `regime_role`
- `filter_belief_execution_mapping`

`filter_belief_execution_mapping` must carry:

- `pre_bayes_targets`
- `belief_targets`
- `path_ranking_targets`
- `execution_tree_targets`
- `structural_feedback_required`

**Promotion Rule**

A candidate may only move to the post-factor runtime-closure board after all of the following are true:

- `factor_eval_grid_summary.trade_density_summary.aggregate_label` is not `invalid` or `anecdotal`
- `transfer_score.status` is not `single_market_only` unless the lane is explicitly regime-only and still inside exploration
- resonance context is explicit for the base timeframe
- middle-layer mapping is explicit
- the lane states whether structural feedback lineage is required before honest runtime validation

---

## Current Todo Board

### Done

- [x] Locked the factor iteration board to factor content only.
- [x] Locked the loop boundary to `pre_bayes -> belief / BBN -> path ranking -> execution tree`.
- [x] Locked the candidate pack minimum artifact family:
  - `factor_expression.json`
  - `factor_eval_grid_summary.json`
  - `transfer_score.json`
- [x] Extended `scripts/research/factor_candidate_pack.py` so `factor_expression.json` now carries `filter_belief_execution_mapping`.
- [x] Added regression coverage in `scripts/research/tests/test_factor_candidate_pack.py` for:
  - populated middle-layer mapping
  - empty/default middle-layer mapping

### Next

- [ ] For each active factor family, write or refresh one candidate-spec JSON that explicitly fills:
  - `pre_bayes_targets`
  - `belief_targets`
  - `path_ranking_targets`
  - `execution_tree_targets`
  - `structural_feedback_required`
- [ ] For each active factor family, rebuild its candidate pack through `scripts/research/factor_candidate_pack.py`.
- [ ] Reject any candidate whose pack still lacks middle-layer mapping even if backtest metrics look good.
- [ ] For regime-only candidates:
  - require classifier / transition / resonance evidence first
  - do not force execution trade density as the primary gate
- [ ] For execution candidates:
  - require trade density, resonance, and cross-market evidence
  - require the candidate pack to state which execution-tree blockers it intends to move
- [ ] For any candidate expected to influence runtime recommendation support later:
  - set `structural_feedback_required=true`
  - explicitly note that non-demo runtime validation cannot be honest until structural lineage exists in the downstream real-trade source
- [ ] Hand off to `docs/plans/2026-05-07-auto-quant-post-factor-runtime-closure-todo.md` only after a candidate pack is explicit enough to answer all of the following from artifacts, not chat:
  - what this candidate expects the `pre-bayes / filter gate` to do
  - what BBN evidence/prior it expects to strengthen or weaken
  - what structural path-ranking surface it expects to move
  - what execution-tree blocker / branch / gate it is trying to affect
- [ ] Use `docs/plans/2026-05-09-factor-iteration-pre-bayes-bbn-catboost-execution-tree-todo.md` as the sequencing bridge once a candidate leaves pure factor iteration:
  - factor board owns candidate generation and pack truth
  - bridge board owns chain-level diagnosis and stopping-layer labeling
  - post-factor board owns runtime mutation and before/after evidence

### Not Yet

- [ ] Move any factor candidate to the post-factor runtime-closure board before its candidate pack exists
- [ ] Treat single-market thin proof as family closure
- [ ] Add new runtime-only factor ingestion code just to compensate for a missing external candidate pack
- [ ] Fold provider bootstrap or generic UX requirements into this board

---

## Ordered Execution Checklist

1. Choose one factor family from the active Auto-Quant lane.
2. State its intended role:
   - `regime_only`
   - `execution_only`
   - `mixed`
3. Write or update a candidate-spec JSON that includes explicit `filter_belief_execution_mapping`.
4. Build the candidate pack with:
   - `python3 scripts/research/factor_candidate_pack.py --manifest-json <strategy_library.json> --strategy-name <strategy> --candidate-spec-json <candidate_spec.json> --autoresearch-status-json <autoresearch_status.json> --output-dir /tmp/<candidate-pack>`
5. Inspect:
   - `factor_expression.json`
   - `factor_eval_grid_summary.json`
   - `transfer_score.json`
6. Reject immediately if:
   - mapping is incomplete
   - density is anecdotal/invalid
   - resonance is missing for the claimed base timeframe
7. Only after a candidate pack is explicit and reviewable may the lane continue toward runtime closure evidence.

---

## Success Standard

This board is successful only if all of the following are true:

- Every active factor family has an explicit candidate pack.
- Every candidate pack states exactly how it feeds:
  - pre-bayes filter
  - belief / BBN evidence
  - path ranking
  - execution tree
- Every candidate pack states whether structural feedback lineage is required for honest downstream validation.
- Promotion out of factor iteration is blocked by explicit artifact gates, not by chat-only judgment.
- Any downstream closure attempt can start from the emitted pack alone, without needing to reconstruct intent from older board prose.
