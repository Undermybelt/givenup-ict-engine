# QQQ opening impulse zero-trade density pivot - 2026-05-19

## Trigger
Use when a regime-rooted opening-drive / opening-impulse / pullback-retest factor preserves branch metadata and Auto-Quant runs cleanly, but AQ ranking returns zero trades across the 1m origin and sibling ladder.

## Session pattern
Branch tested:

`US -> equity_etf -> QQQ -> 1m -> Trend -> OpeningDriveLiquidity -> opening_impulse_pullback_retest -> yf_qqq_opening_impulse_pullback_retest_1m_mtf_v2`

Provider/AQ evidence:

- provider rows existed for `1m/5m/15m/30m/1h/1d`; `4h` was unavailable and not synthesized.
- material generation, dispatch, and rank exited 0.
- branch fields were preserved in ranked rows.
- all 18 ranked materials had `trade_count=0`.
- `origin_survivors_2bps=[]` and `origin_survivors_5bps=[]`.

## Decision rule
This is a factor Gate 1 density failure, not a provider failure and not downstream material.

Set:

- `decision=drop_gate1_no_cost_density`
- `pre_bayes_allowed=false`
- `bbn_allowed=false`
- `catboost_allowed=false`
- `execution_tree_allowed=false`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Next move
Do not tighten or overlay the same zero-trade branch. Pivot to a materially denser 1m entry family under a fresh rooted branch, or choose a sibling exact timeframe root only if that timeframe itself has real cost-stressed density.
