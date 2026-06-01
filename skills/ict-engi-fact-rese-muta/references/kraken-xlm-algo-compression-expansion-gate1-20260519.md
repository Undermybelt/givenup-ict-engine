# Kraken XLM/ALGO compression-expansion Gate 1 terminal sample - 2026-05-19

## Scope
- Repo: `<ict-engine-repo>`
- Script: `support/docs/experiments/actionable-regime-confidence/scripts/run_kraken_xlm_algo_vwap_compression_expansion_density_1m_mtf_v1.py`
- Run root: `support/docs/experiments/actionable-regime-confidence/runs/20260519T134042+0800-codex-kraken-xlm-algo-vwap-compression-expansion-density-1m-mtf-v1`
- Branch path: `VolatilityCompression -> MidCapCryptoVwapExpansion -> one_minute_vwap_compression_expansion_density -> kraken_xlm_algo_vwap_compression_expansion_density_1m_mtf_v1`

## What worked
- Kraken provider fetch succeeded for `XLMUSD` and `ALGOUSD` across `1m/5m/15m/30m/1h`.
- Auto-Quant material batch, dispatch, and rank all exited `0`.
- Branch metadata survived into rank rows (`branch_fields_preserved=true`).

## Gate 1 result
- `rank_rows=10`
- `rank_completed_rows=10`
- `rank_failed_rows=0`
- `rank_total_trade_count=26`
- `rank_positive_rows=3`
- `positive_origin_1m=[]`
- `positive_higher_timeframes=[]`
- `decision=drop_or_block_gate1_practical`
- `downstream_allowed=false`
- `promotion_allowed=false`
- `trade_usable=false`

## Durable lesson
A sparse compression-expansion density branch with only 0-1 positive trades on the 1m origin is a Gate 1 terminal sample even when provider fetch, material generation, dispatch, ranking, and branch metadata are clean. Do not move it into Pre-Bayes/BBN/CatBoost/execution tree, and do not use 15m/1h single-digit positive rows to rescue it. The next candidate should switch to a materially denser 1m entry family under a new rooted branch, not tighten or re-run the same compression-expansion shape.

## Future check
Before downstream handoff, require a true 1m-origin survivor with enough real-cost trade density for the claimed market/timeframe lane. A one-trade positive row is observation only.
