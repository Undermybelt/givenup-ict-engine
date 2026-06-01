# Exact timeframe root restart and maturity blocker (2026-05-19)

## When this applies
Use this note when a 1m-origin regime-rooted ladder fails Gate 1, but a higher-timeframe sibling has real positive cost-stressed evidence and may deserve its own independent exact root.

## Pattern observed
- Original 1m-root Binance altcoin branches failed because `positive_origin_1m=[]` even though a 5m XRPUSDT sibling was positive.
- Correct move was not to rescue the failed 1m root with higher-timeframe evidence.
- Correct move was to restart the survivor as a new exact root:
  `Binance -> crypto -> XRPUSDT -> 5m -> TrendExpansion -> AltcoinBreakoutMomentum -> five_minute_donchian_rvol_breakout -> binance_xrpusdt_5m_altcoin_donchian_rvol_exact_root_v1`

## Gate 1 result
- Auto-Quant compile/batch/dispatch/rank all exited `0`.
- Rank rows: `1`.
- Trades: `21`.
- Win rate: `38.0952%`.
- Total profit: `+1.20%`.
- Estimated per-side cost stress:
  - `0bps`: `+1.20%`
  - `1bps`: `+0.78%`
  - `2bps`: `+0.36%`
  - `5bps`: `-0.90%`

## Downstream result
- Auto-Quant import, prior init, analyze, workflow-status, pre-bayes-status, structural target export, and policy-training-status all exited `0`.
- Policy rows: `4`.
- `mature_rows=0`.
- `history_mature_rows=0`.
- CatBoost/path-ranker must remain blocked because supervised labels are not mature.
- Execution tree must remain blocked because CatBoost/path-ranker is not admitted.

## Durable rule
A higher-timeframe sibling can become its own exact root only after restating the full market/product/symbol/timeframe/regime/profit-factor path. Gate 1 cost survival may justify Pre-Bayes/BBN readback, but it is not promotion. If policy target maturity is zero, set:

```json
{
  "catboost_allowed": false,
  "execution_tree_allowed": false,
  "promotion_allowed": false,
  "trade_usable": false,
  "update_goal": false
}
```

## Cache replay caveat
If retained provider rows are reused, mark the result as exact-root replay/incubation evidence. Do not claim fresh provider parity or live-readiness until a fresh provider full-ladder rerun passes the same gates.
