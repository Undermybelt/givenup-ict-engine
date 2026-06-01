# Rooted Gate1 cost-stable training lesson (2026-05-19)

> 2026-05-24 schema note: `pda_hybrid_alignment` is historical telemetry only unless the current ict-engine source or readback contract still declares it active. Do not use old `pda_hybrid_alignment=true` or `false` lines in this reference as a current hard gate; classify with the live actionable/status/readiness/transition/ranker/mature-row fields.

Use when continuing ict-engine profitability-factor training where the user wants practical, stable profit rather than raw profit-factor spikes.

## Session learning

The user reiterated that every profitability factor must be rooted by full branch identity before any Auto-Quant, filtering, BBN, CatBoost, or execution-tree step:

`market -> product -> symbol -> base_timeframe -> main_regime -> sub_regime -> ... -> first_profit_factor -> optional_profit_factor_overlays...`

Grammar:
- `main_regime` may branch to `sub_regime`.
- `sub_regime` may branch to more regimes or the first profit factor.
- A `profit_factor` may only branch to later profit-factor overlays.
- Do not flatten a branch to the factor name after Gate1.
- Do not let downstream select or report a sibling path as if it validated the tested branch.

## Gate order

1. Build exact rooted material fields first.
2. Start from a `1m` origin where feasible.
3. Cover `5m`, `15m`, `30m`, `1h`, `4h`, and `1d` where real provider rows exist.
4. If a provider cannot serve a timeframe, mark it missing; do not synthesize it.
5. Run Auto-Quant Gate1 and inspect the actual `ranking[]` rows.
6. Run cost stress at 0/1/2/5 bps per side.
7. Only then allow Pre-Bayes/filtering, BBN, CatBoost/path-ranker, and execution tree.

## Promotion constraints

Promote only if all hold:
- Real-cost edge survives, especially at 2 bps/side; 5 bps/side survival is stronger.
- 1m-origin trade density is sufficient for the requested style, normally around 1-3 trades/day unless a slower strategy is explicitly chosen.
- Direction remains consistent from AQ through Pre-Bayes/BBN/CatBoost/execution tree.
- `transition_hazard < 0.60`.
- `pda_hybrid_alignment=true`.
- `execution_readiness >= 0.65` stably.
- `promotion_allowed=true` and `trade_usable=true` must be earned, not forced by lowering gates.

If any of these fail, classify the branch as observation/incubate/negative sample. Do not tune thresholds merely to avoid outputs like:

`pre_bayes_allowed=false, bbn_allowed=false, catboost_allowed=false, execution_tree_allowed=false, promotion_allowed=false, trade_usable=false, update_goal=false`

Instead, use those gate failures to infer the next required factor shape.

## Concrete session evidence

Two Gate1 runs were useful but not promotable:

1. Inverse leveraged stress trend continuation:
- Path: `StressTrend -> InverseLeveragedEtfStressContinuation -> inverse_leveraged_stress_trend_continuation_dense -> yf_inverse_leveraged_stress_trend_continuation_dense_1m_mtf_1d_v1`
- Covered real `1m/5m/15m/30m/1h/1d`; `4h` missing/unsupported.
- TZA/1m: 26 trades, raw +0.77%, but 2 bps/side -0.27% and 5 bps/side -1.83%.
- Verdict: cost-fragile negative sample; no downstream.

2. Broad ETF PDA trend continuation:
- Path: `Trend -> SessionLiquidity -> pda_aligned_trend_continuation_dense -> yf_broad_etf_pda_trend_continuation_dense_1m_mtf_v2`
- QQQ/1m: 6 trades, raw +0.62%, 2 bps/side +0.38%, 5 bps/side +0.02%.
- Verdict: not live-ready because sample is too small, but it is a better seed than cost-fragile high-trade rows.

## Next training shape inferred from gates

If continuing from this session, prefer a new exact rooted QQQ branch rather than rescuing the failed inverse-leveraged family:

`US -> equity_etf -> QQQ -> 1m -> Trend -> SessionLiquidity -> pda_aligned_trend_continuation_dense -> qqq_cost_stable_vwap_reclaim_v1`

Required improvements:
- Preserve QQQ/1m cost survival while increasing 1m trade count to at least the Gate1 threshold.
- Add real provider parity, preferably IBKR first, then TVR/YF as supporting evidence.
- Include 5m/15m/30m/1h/1d context; attempt 4h and mark missing if unavailable.
- Only hand off downstream after Gate1 density and 2 bps/side cost survival pass.
