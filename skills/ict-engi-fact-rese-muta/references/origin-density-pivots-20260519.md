# 2026-05-19 origin-density pivots: Kraken/Bybit full-ladder Gate 1

## Context
Continuation of regime-rooted profitability-factor training. The active contract was:

`market -> product -> symbol -> base_timeframe -> main_regime -> sub_regime -> ... -> first_profit_factor -> optional_profit_factor_overlays...`

Start from `1m`, cover `5m/15m/30m/1h/4h/1d`, cost-stress at `0/1/2/5 bps/side`, and stop before Pre-Bayes/BBN/CatBoost/execution-tree unless the exact 1m root has enough real-cost trade density.

## Runs observed

### Kraken COMP/ZEC VWAP compression-expansion density
Root:
`VolatilityCompression -> MixedDeFiPrivacyAltcoinVwapExpansion -> one_minute_vwap_compression_expansion_density_full_ladder -> kraken_comp_zec_vwap_compression_expansion_density_1m_full_ladder_v1`

Result:
- Provider/AQ completed: `COMPUSD/ZECUSD x 1m/5m/15m/30m/1h/4h/1d`.
- Branch fields preserved.
- `rank_rows=14`, `rank_total_trade_count=158`.
- 1m origin: `ZECUSD 1m` only 3 trades; `COMPUSD 1m` zero trades.
- Some HTF rows were positive, e.g. `ZECUSD 1h`, but 1m origin did not meet density.
- Decision: `drop_or_block_gate1_practical`; downstream skipped.

### Kraken LTCUSD VWAP/RSI reclaim
Root:
`RangeReversion -> CryptoVWAPCompression -> ltc_vwap_rsi_reclaim -> kraken_ltcusd_vwap_rsi_reclaim_1m_full_ladder_v1`

Result:
- Provider/AQ completed across full ladder.
- 1m origin: zero trades.
- HTF had tiny one-trade positives only.
- Decision: `keep_negative_sample`; downstream skipped.

### Bybit MNT/HBAR CMF/OBV accumulation breakout
Root:
`TrendExpansion -> BybitMidcapAccumulationBreakout -> cmf_obv_accumulation_breakout_1m_mtf -> bybit_mnt_hbar_cmf_obv_breakout_1m_mtf_v1`

Result:
- Provider/AQ completed for `MNTUSDT/HBARUSDT x 1m/5m/15m/30m/1h/4h/1d`.
- Branch fields preserved.
- 1m origin failed: `MNTUSDT 1m` had 3 losing trades; `HBARUSDT 1m` zero trades.
- `MNTUSDT 30m` survived 2bps and 5bps, but this is a separate exact timeframe root candidate, not rescue evidence for the failed 1m root.
- Decision: `higher_timeframe_subclass_only_origin_blocked`; downstream skipped.

## Durable lessons

1. A materially different entry family can still fail the same 1m-origin gate. After several clean full-ladder failures, do not keep rotating near-equivalent 1m variants just because HTF siblings look better.
2. HTF positives should be promoted only by restarting under their own exact timeframe root, e.g. `... -> 30m -> ...`, with 1m retained as context/microstructure if useful.
3. If 1m origin repeatedly yields zero to three trades or flips negative at 1-2bps/side, next work should target either:
   - a looser, explicitly denser 1m signal with a pre-AQ density diagnostic; or
   - a new exact HTF root for the surviving sibling.
4. Do not run Pre-Bayes/BBN/CatBoost/execution-tree to "see what happens" when Gate 1 already says origin density/cost failed.

## Closure rule
When a full-ladder packet has successful provider fetch, strategy compile, AQ batch/dispatch/rank, and preserved branch fields but no dense cost-positive 1m origin, classify as a factor-gate failure or observation sample. The correct next step is root selection or signal family pivot, not downstream admission.
