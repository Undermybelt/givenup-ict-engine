# Factor Iteration -> Pre-Bayes -> BBN -> CatBoost -> Execution-Tree TODO

> Authoritative bridge board for the next pure-iteration loop.  
> This board does **not** replace the existing factor board or the post-factor runtime-closure board.  
> It exists to sequence them correctly so factor iteration does not stop at backtest metrics and runtime closure does not begin from a vague handoff.

**Goal:** run the next iteration as one explicit chain:

1. factor iteration candidate
2. pre-bayes / filter gate (`绿波` in user shorthand)
3. BBN prior/posterior evidence
4. CatBoost / structural path-ranking surface
5. execution-tree / workflow outcome

and make every handoff explicit, reviewable, and `/tmp/...` isolated.

**Architecture:** keep runtime code unchanged unless a real middle-layer defect is proven. Use existing public CLI/runtime surfaces first. Treat factor iteration as external/additive work, then push only explicit artifacts downstream. Do not mix new factor search, provider bootstrap, and runtime-surface refactors into one pass.

**Tech Stack:** `docs/plans/2026-05-08-factor-iteration-filter-belief-catboost-execution-tree-board.md`, `docs/plans/2026-05-07-auto-quant-post-factor-runtime-closure-todo.md`, `docs/plans/2026-05-05-execution-tree-factor-auto-quant-todo.md`, `docs/202605071246nextstep`, `./target/debug/ict-engine factor-research`, `auto-quant-results-import`, `auto-quant-prior-init`, `auto-quant-ingest-real-trades`, `pre-bayes-status`, `policy-training-status`, `export-structural-path-ranking-target`, `workflow-status`, `execution_tree_trace.json`, explicit `/tmp/...` state dirs, Auto-Quant `strategy_library.json`, realized-trades JSONL.

**Baseline / Authority Refs:**
- `docs/plans/2026-05-08-factor-iteration-filter-belief-catboost-execution-tree-board.md`
- `docs/plans/2026-05-07-auto-quant-post-factor-runtime-closure-todo.md`
- `docs/plans/2026-05-05-execution-tree-factor-auto-quant-todo.md`
- `docs/202605071246nextstep`
- `/tmp/vrp-v2-runtime-closure/`
- `/tmp/vrp_v2_strategy_library.json`
- `/tmp/vrp_v2_realized_trades.jsonl`

**Compatibility Boundary:** pure iteration first. No repo runtime edits unless a public command or persisted artifact surface is actually broken on `green-baseline`. Use repo-native terms in this board:
- `绿波` = `pre-bayes / filter gate`
- `信念网络` = `BBN prior/posterior evidence`
- `cat boost` = `structural path-ranking / external ranker surface`
- `执行树` = `execution_tree_trace.json` + `workflow-status` downstream outcome

**Verification:** all claims on this board must be backed by a fresh command or a persisted artifact from the same `/tmp/...` state dir.

---

## Decision Lock

- [x] This board is orchestration/guidance only. It should tell the next agent exactly how to move a candidate through the full chain.
- [x] Factor iteration still starts on the factor board, not here.
- [x] Runtime closure still lands on the post-factor board, not here.
- [x] This board is the sequencing contract between the two.
- [x] This board is not allowed to become a third competing execution owner:
  - factor generation / candidate-pack truth stays on `2026-05-08-factor-iteration-filter-belief-catboost-execution-tree-board.md`
  - runtime mutation / before-after closure stays on `2026-05-07-auto-quant-post-factor-runtime-closure-todo.md`
  - this board only labels the chain, the stopping layer, and the exact next handoff
- [x] No code reopening is justified yet just from this audit.
- [x] One real surface drift was found and normalized here:
  - `docs/plans/2026-05-07-auto-quant-post-factor-runtime-closure-todo.md` still mentions `auto-quant-results-import --dry-run`
  - current `green-baseline` binary does **not** support `--dry-run` on that command
  - therefore import rehearsal on current mainline must use an isolated copied `/tmp/...` state dir instead of a non-existent dry-run flag

## Current Closed-Loop Diagnosis

### What is alive on `green-baseline`

- [x] `pre-bayes-status` is alive and readable.
  - latest checked state:
    - `Pre-Bayes | gate=pass_neutralized | soft_evidence=yes`
    - `Bridge: long=0.551 | short=0.530 | mtf=bullish | align=1.000 | entry_align=0.860`
- [x] `auto-quant-prior-init` is alive and still consumes imported strategy-library evidence.
  - latest checked state:
    - `trade_count=815`
    - `final_probs=[0.3462936184690158, 0.00000021385176184690159, 0.6537061676792224]`
- [x] `auto-quant-ingest-real-trades` is alive and still parses the realized-trades artifact.
  - latest checked state:
    - `trades_total=815`
    - `trades_applied=815`
    - `trades_invalid=0`
- [x] `export-structural-path-ranking-target` is alive and still exports the same target surface.
  - latest checked state:
    - `rows=3`
    - `mature_rows=0`
    - `rows_with_raw_path_score=3`
    - `rows_with_calibrated_path_prob=0`
    - `production_validation=0/30`
- [x] `policy-training-status` is alive and reports the current CatBoost/path-ranking state honestly.
  - latest checked state:
    - `trainer_artifact=ready`
    - `trainer_status=present_validation_insufficient`
    - `runtime_selection=enabled_candidate_set_ready`
    - `runtime_source=candidate_set`
    - `runtime_matches=3`
- [x] `workflow-status` and `execution_tree_trace.json` are alive and still close the chain.
  - latest checked state:
    - `workflow-status`: `current_focus_phase=analyze`
    - `workflow-status`: `recommended_next_command=ict-engine factor-research --symbol NQ --data examples/demo/demo-15m.json --state-dir /tmp/vrp-v2-runtime-closure --backend native`
    - execution tree:
      - `branch=transition_guardrail`
      - `execution_bias=guarded`
      - `gate_status=observe`
      - `execution_score=0.5806074494341393`

### What is not broken, but still not closed

- [x] The factor -> pre-bayes -> BBN -> execution-tree path is not dead.
- [x] The actual current blocker is **not** “command missing” or “binary crashed”.
- [x] The actual current blocker is that the CatBoost / structural path-ranking layer still lacks mature, structural-lineage-backed rows:
  - `mature_rows=0`
  - `raw_scored_mature=0/30`
  - `production_validation=0/30`
- [x] The execution tree is therefore still running from candidate-set scores / current evidence, not from a validated mature external ranker loop.

### What is the only confirmed surface mismatch

- [x] `auto-quant-results-import --dry-run` is documented in the older runtime-closure board, but unsupported by the current mainline binary.
- [x] Treat this as a guidance mismatch, not yet a code-reopen trigger by itself.
- [x] For pure iteration on current mainline:
  - rehearse import on a copied `/tmp/...` state dir
  - then run the real import only in an isolated throwaway state

## Current Todo Board

### Done

- [x] Normalized user shorthand into repo terms:
  - `濾波` -> `pre-bayes / filter gate`
  - `信念网络` -> `BBN prior/posterior evidence`
  - `cat boost` -> `structural path ranking / external ranker surface`
  - `执行树` -> `workflow-status` + `execution_tree_trace.json`
- [x] Re-read the existing factor board, runtime-closure board, and next-step diagnosis doc.
- [x] Audited the current mainline public command surface.
- [x] Confirmed the middle layers are alive on `green-baseline`.
- [x] Isolated the actual current closure blocker to the CatBoost/path-ranking maturity layer, not to factor import, BBN prior-init, or execution-tree readback.
- [x] Confirmed one guidance drift:
  - `auto-quant-results-import` has no `--dry-run` on current mainline

### Next Slice

- [x] Run the next candidate through the chain in this order, without skipping layers:
  - build/refresh explicit factor candidate artifact
  - check pre-bayes / bridge state from the same `/tmp/...` state
  - apply or inspect BBN prior-init effect
  - inspect whether structural path-ranking target rows grew in a meaningful way
  - inspect whether execution-tree / workflow output changed
  - evidence: `docs/plans/2026-05-09-vrp-v2-loop-handoff-todo.md`
- [x] Do not call a factor “closed” just because its standalone backtest is good.
  - Slice result: `VRPCompression_V2_NQ_15m` is chain-readable, but not mature external-ranker closed.
- [x] Do not hand off to runtime closure until the candidate artifact explicitly states:
  - `pre_bayes_targets`
  - `belief_targets`
  - `path_ranking_targets`
  - `execution_tree_targets`
  - `structural_feedback_required`
  - evidence: `/tmp/vrp-v2-loop-20260509-candidate-pack/factor_expression.json`
- [x] For each next candidate, write one explicit chain-level judgment:
  - `stopped_at_factor_iteration`
  - `stopped_at_pre_bayes`
  - `stopped_at_bbn`
  - `stopped_at_path_ranking`
  - `stopped_at_execution_tree`
  - `closed_loop_changed`
  - Slice verdict: `stopped_at_path_ranking` because `mature_rows=0`, `raw_scored_mature=0/30`, `production_validation=0/30`, while workflow still uses `candidate_set_only` scores.
- [x] Next practical slice: generate or import structural feedback rows / hot-plug ranker evidence so path-ranking can move beyond candidate-set scoring without breaking zero-config fallback.
  - hot-plug evidence: `runtime_selection=enabled_registered_model_ready`, `runtime_source=registered_model_artifact`, `runtime_matches=3` after `path_ranker_integration.py --register-runtime-artifact`.
  - structural feedback evidence: `structural_feedback_trade_enricher.py emit-probe` generated `structural-feedback-v1` from the rank-1 target row; `ict-engine update --feedback-file` consumed it; target export moved to `mature_rows=1`, `raw_scored_mature=1/30`.
  - remaining stop layer: `stopped_at_path_ranking_validation_floor` until 29 more honest structural-feedback observations exist.

### Not Yet

- [ ] Reopening runtime code just to make the loop look cleaner
- [ ] Treating `trainer_artifact=ready` as equivalent to a validated path-ranker loop
- [ ] Treating `candidate_set` runtime scoring as equivalent to mature external CatBoost closure
- [ ] Mixing new provider bootstrap or generic UX work into this loop board

## Ordered Execution Checklist

1. Pick one already-explicit factor candidate from the factor board.
2. Materialize or refresh its explicit candidate artifact pack in `/tmp/...`.
3. Record the factor-stage truth:
   - trade-density bucket
   - breadth / market coverage
   - resonance stack
   - claimed downstream targets
4. Push it into the `pre-bayes` stage and record:
   - `pre-bayes-status --human`
   - `bridge` line
   - whether the gate is blocked, neutralized, or supportive
5. Push it into the `BBN` stage and record:
   - `auto-quant-prior-init` diff or applied result
   - if real trades exist, `auto-quant-ingest-real-trades`
   - whether the BBN layer actually changed any downstream prior/posterior belief worth keeping
6. Push it into the `CatBoost / path-ranking` stage and record:
   - `export-structural-path-ranking-target`
   - `policy-training-status --human`
   - whether the lane is blocked by:
     - no target rows
     - no mature rows
     - no calibration
     - no structural lineage
7. Push it into the `execution-tree` stage and record:
   - `workflow-status --human`
   - `workflow-status --phase ensemble-vote --human`
   - `workflow-status --phase structural-playbook --human`
   - `workflow-status --phase structural-recommended-path-bundle --human`
   - `execution_tree_trace.json`
8. Write one final chain verdict:
   - where the candidate stopped
   - what exact artifact/metric blocked it
   - whether the blocker is:
     - candidate quality
     - regime / pre-bayes
     - BBN evidence
     - path-ranking maturity
     - execution-tree behavior

## Real Command Floor

Use these exact current-mainline commands as the minimal closure floor.

### Factor / candidate handoff

```bash
python3 scripts/research/factor_candidate_pack.py \
  --manifest-json <strategy_library.json> \
  --strategy-name <strategy> \
  --candidate-spec-json <candidate_spec.json> \
  --autoresearch-status-json <autoresearch_status.json> \
  --output-dir /tmp/<candidate-pack>
```

### Pre-Bayes / 濾波

```bash
./target/debug/ict-engine pre-bayes-status \
  --symbol <SYMBOL> \
  --state-dir /tmp/<state> \
  --human
```

### BBN

```bash
./target/debug/ict-engine auto-quant-prior-init \
  --symbol <SYMBOL> \
  --state-dir /tmp/<state> \
  --library <strategy_library.json> \
  --dry-run
```

```bash
./target/debug/ict-engine auto-quant-ingest-real-trades \
  --symbol <SYMBOL> \
  --state-dir /tmp/<state> \
  --trades <realized_trades.jsonl> \
  --dry-run
```

### CatBoost / structural path-ranking

```bash
./target/debug/ict-engine export-structural-path-ranking-target \
  --symbol <SYMBOL> \
  --state-dir /tmp/<state>
```

```bash
./target/debug/ict-engine policy-training-status \
  --symbol <SYMBOL> \
  --state-dir /tmp/<state> \
  --human
```

### Execution tree

```bash
./target/debug/ict-engine workflow-status \
  --symbol <SYMBOL> \
  --state-dir /tmp/<state> \
  --human
```

```bash
./target/debug/ict-engine workflow-status \
  --symbol <SYMBOL> \
  --state-dir /tmp/<state> \
  --phase structural-playbook \
  --human
```

```bash
./target/debug/ict-engine workflow-status \
  --symbol <SYMBOL> \
  --state-dir /tmp/<state> \
  --phase structural-recommended-path-bundle \
  --human
```

## Current Known Blockers

### Blocker A: import rehearsal surface drift

- `auto-quant-results-import` on current `green-baseline` does **not** support `--dry-run`.
- Therefore this board must treat import rehearsal as:
  - copy a `/tmp/...` state dir
  - run the real import there
  - discard that state if the manifest/handoff is wrong

### Blocker B: path-ranking maturity gap

- The current live VRP state still reports:
  - `mature_rows=0`
  - `raw_scored_mature=0/30`
  - `production_validation=0/30`
- This means the CatBoost/path-ranking surface is present but not yet mature enough to claim a validated external-ranker loop.

### Blocker C: execution tree still reads candidate-set-level path support

- Current `policy-training-status` still reports:
  - `runtime_selection=enabled_candidate_set_ready`
  - `runtime_source=candidate_set`
- So the loop is not blocked at the execution-tree reader.
- It is blocked because the upstream path-ranking evidence is not yet mature enough to replace candidate-set support.

## Success Standard

This board is successful only if a later iteration can say all of the following with explicit artifacts:

- the factor candidate is explicit and reviewable
- the pre-bayes / filter gate result is explicit
- the BBN prior/posterior effect is explicit
- the structural path-ranking maturity state is explicit
- the execution-tree outcome is explicit
- the exact stopping layer is explicit

If a candidate stops before the execution tree changes, that still counts as a successful iteration **only if the stopping layer is honestly identified and recorded**.
