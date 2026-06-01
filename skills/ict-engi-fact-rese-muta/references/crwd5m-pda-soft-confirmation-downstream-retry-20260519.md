# CRWD 5m PDA/MTF soft-confirmation downstream admission pattern

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Session: 2026-05-19 ict-engine profitability-factor continuation.

## Branch

`US_EQ -> single_stock -> CRWD -> 5m -> RangeReversion -> AiSecuritySoftwareOversoldReclaim -> rsi_vwap_reclaim_dense -> yf_ai_security_software_rsi_vwap_reclaim_crwd_5m_v1 -> session_liquidity_transition_stability_v1 -> pda_mtf_soft_confirmation_v1`

## What worked

Gate 1 was strong enough to justify exact downstream replay:

- exact 5m row: 43 trades
- raw total profit: +5.81%
- 2 bps/side stress: +4.09%
- 5 bps/side stress: +1.51%
- branch fields survived into downstream artifacts

When initial downstream readback showed path-ranker not visible/used, the useful retry was:

1. Run `path_ranker_integration.py` on the current post-analyze structural target with:
   - `--python-runner system`
   - `--allow-direct-fallback`
   - `--register-runtime-artifact`
2. Run `apply-structural-path-ranking-external-scores` with emitted scores.
3. Run `enable-structural-path-ranking-runtime --reuse-mode candidate_set_only`.
4. Rerun `analyze` on the exact same LTF/MTF/HTF files.
5. Rerun `workflow-status --refresh`.
6. Append the post-ranker retry readback to the packet summary.

## Corrected final readback

A later exact rerun corrected the admission owner and mature-row gate:

- run root: `support/docs/experiments/actionable-regime-confidence/runs/20260519T102243+0800-codex-yf-ai-security-crwd5m-pda-mtf-soft-confirmation-gate1-v1/downstream-exact-crwd-5m-pda-mtf-soft-confirmation-20260519T163430+0800`
- decision: `exact_crwd_5m_execution_admitted`
- all command exits: `0`
- exact branch survived: `true`
- Gate 1: `43` real trades, `27` wins, `16` losses, `0` breakevens, `62.7907%` win rate, `+5.81%` raw, Sharpe `6.0837`
- cost stress: `+4.95%` after `1bps/side`, `+4.09%` after `2bps/side`, `+1.51%` after `5bps/side`
- `ranker_validation_ready=true`
- `path_ranker_score_visible_to_execution_tree=true`
- `path_ranker_score_used_by_execution_tree=true`
- `workflow_closed_loop_branch_admission.status=admitted`
- `workflow_closed_loop_branch_admission.actionable=true`
- `workflow_closed_loop_branch_admission.ready=true`
- `workflow_closed_loop_branch_admission.candidate_status=execution_ready`
- `execution_tree_gate_status=ready`
- `execution_tree_branch=fill_viable`
- `execution_readiness=0.67`
- `transition_hazard=0.5950369253623637`
- `pda_hybrid_alignment=true`
- `history_mature_rows=46`
- current target `mature_rows=3`
- `promotion_allowed=true`
- `trade_usable=true`
- `update_goal=true`

The important distinction: the persisted current `execution_candidate.json`
still reported `actionable=false` and `candidate_status=no_trade`, but it was a
stale current-plan owner. The canonical admission owner for this exact structural
recommended path was the closed-loop branch admission in workflow/execution-tree
readback. Runner tests were updated to cover both stale-candidate override and
history-mature validation admission.

## Rule to reuse

If Gate 1 is cost-positive but downstream is blocked by path-ranker invisibility,
do one post-ranker retry before terminalizing. If the retry still leaves ranker
validation below 30-row gates or `execution_readiness < 0.65`, classify as
observation/scoped candidate only. Do not lower gates.

If a later exact rerun has mature history validation and closed-loop branch
admission on the same rooted path, classify from the closed-loop branch owner,
not from stale current `execution_candidate.json`, provided all of these hold:
`status=admitted`, `ready=true`, `actionable=true`,
`candidate_status=execution_ready`, `ranker_validation_ready=true`,
`history_mature_rows >= 30`, `execution_tree_gate_status=ready`,
`execution_tree_branch=fill_viable`, `transition_hazard < 0.60`,
`pda_hybrid_alignment=true`, `execution_readiness >= 0.65`, and cost stress
survives at least `2bps/side` and preferably `5bps/side`. Preserve the caveat
that current target rows may be sparse, and require a unit test around the
override before writing `promotion_allowed=true` or `trade_usable=true`.
