# BBN / Execution-tree stagnation diagnostic

Use when the operator says factor training has "no breakthrough" or asks whether BBN evidence / execution-tree nodes explain stalled progress.

## Diagnostic order

1. Prove the factor should be downstream at all.
   - Gate 1 negative AQ/profit floor, `downstream_allowed=false`, `strict_training_rows=0`, or observation-only packets are candidate-quality failures. Stop before blaming BBN.
2. Check BBN evidence application, not just artifact existence.
   - Look for `prior.strategies_applied`, `evidence_value_gate_passed`, `bbn_entropy_reduction`, `bbn_log_loss_delta`, posterior changes, and `regime_bundle_bbn_application_status`.
   - If `strategies_applied` exists and value gates pass, BBN is probably not the primary blocker.
3. Check path-ranker / CatBoost runtime consumption.
   - `workflow.path_ranker_summary`, `latest_structural_execution_candidate.*path_ranker*`, and `execution_tree_trace.json` are all needed.
   - For execution tree traces, inspect nested `output.*`: `output.path_ranker_score_visible_to_execution_tree`, `output.path_ranker_score_used_by_execution_tree`, `output.path_ranker_model_family`, `output.path_ranker_runtime_source`, `output.ranker_validation_ready`.
4. Check mature target / training-weight surface.
   - `structural_path_ranking_target.rows` may be nonzero while `mature_rows=0`, `rows_with_training_weight=0`, or `raw_scored_mature=0/30` keeps the lane non-promotable.
5. Check entry-model and closed-loop admission.
   - `entry_models[*].matched_rows=0`, `closed_loop_branch_admission.status=fail_closed`, `candidate_status=execution_observe_only`, `review_status=observe`, or `blocking_truth.status=bridge_needs_confirmation` usually explain why a visible ranker score still cannot promote.
6. Interpret execution-tree branch/gate.
   - `gate_status=observe`, `branch=transition_guardrail`, `execution_bias=guarded`, or `hybrid_transition_hazard > threshold` means branch consumption happened but execution was fail-closed.

## Common conclusions

- BBN healthy, no breakthrough: `strategies_applied` and BBN deltas exist, but downstream target maturity or entry-model rows are zero.
- Ranker healthy, no breakthrough: execution tree has `visible=true` and `used=true`, but `ranker_validation_ready=false` or execution gate stays observe.
- Real-trade feedback not helping: `auto_quant_real_trades_ingested` ledger exists, but policy target still has `mature_rows=0`, `rows_with_training_weight=0`, and entry models have `matched_rows=0`; the missing bridge is feedback -> policy/entry training rows.
- Candidate-quality failure: AQ variants fail profit floor or packet says `downstream_allowed=false`; do not run BBN/CatBoost just to create activity.

## Minimal evidence block

Report compactly:

```text
BBN: strategies_applied=?, evidence_gate=?, entropy_delta=?, log_loss_delta=?
Ranker: model=?, source=?, runtime_matches=?, visible=?, used=?, validation_ready=?
Target: rows=?, mature_rows=?, rows_with_training_weight=?, raw_scored_mature=?/30
Entry/closed-loop: matched_rows=?, candidate_status=?, closed_loop=?, blocking_truth=?
Execution tree: gate=?, branch=?, bias=?, transition_hazard=?/threshold
Verdict: candidate quality | BBN gate | ranker runtime | target maturity | entry bridge | execution guardrail
```

## Pitfalls

- Do not conclude "BBN failed" from observe-only execution; BBN may have updated posterior correctly.
- Do not conclude "CatBoost failed" from lack of promotion; execution tree may have used the score and still chosen guardrail.
- Do not trust top-level keys only in `execution_tree_trace.json`; important fields are often under `output.*`.
- Do not treat provider/AQ evidence shape completion as `trade_usable=true`; promotion needs target maturity, entry-model matches, and non-observe execution gates.
- When replaying from a copied state dir, rerunning `auto-quant-results-import`,
  `auto-quant-prior-init`, or `analyze` can mint a new candidate set and drop a
  previously registered CatBoost runtime back to `candidate_set_only` or
  `enabled_no_matching_scores`. Re-export the current structural target,
  reapply/register external scores for the copied symbol, then rerun `analyze`
  before claiming CatBoost/path-ranker parity.
