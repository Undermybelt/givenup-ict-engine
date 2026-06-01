# QQQ 5m PDA sequence-consistency reclaim Gate 1 cost-density failure

Session: 2026-05-19
Run root: `support/docs/experiments/actionable-regime-confidence/runs/20260519T142350+0800-hermes-ibkr-qqq-5m-pda-sequence-consistency-reclaim-v1`

## Branch

`US -> equity_etf -> QQQ -> 5m -> Trend -> SessionLiquidity -> pda_sequence_consistency_reclaim -> ibkr_qqq_5m_pda_sequence_consistency_reclaim_v1`

Provider: IBKR
Base timeframe: 5m
Context ladder covered: `5m/15m/30m/1h/4h/1d`
`local_cache_replay=false`

## Gate 1 result

Auto-Quant material compile, batch, dispatch, and rank all exited `0`.
Branch fields were preserved.
Rank rows: `3`.

Cost stress:

- `quality/QQQ/5m`: 1 trade, raw `+0.45%`, 2bps/side `+0.41%`; too sparse.
- `dense/QQQ/5m`: 24 trades, raw `+0.17%`, 2bps/side `-0.79%`; density exists but cost-fragile.
- `balanced/QQQ/5m`: 10 trades, raw `-0.00%`, 2bps/side `-0.40%`.

`survivors_2bps=[]`

Terminal decision: `drop_gate1_no_5m_cost_density`.

## Reusable lesson

A higher-timeframe sibling root that is restarted from a failed 1m/PDA overlay still needs its own real-cost density. Exact branch preservation and provider breadth are not enough.

If a PDA sequence-consistency reclaim overlay fails because the quality row is sparse and the dense row flips negative at 1-2bps/side, do not tighten the same reclaim shape or send it downstream. Treat it as same-root negative/suppression evidence and pivot the next candidate toward a materially different, wider-density PDA/factor-direction agreement family.

Do not run Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution tree from this packet.

Required booleans for this failure mode:

- `pre_bayes_allowed=false`
- `bbn_allowed=false`
- `catboost_allowed=false`
- `execution_tree_allowed=false`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
