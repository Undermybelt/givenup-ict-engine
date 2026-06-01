# Kraken crypto full-ladder origin-density gate

Session lesson: A fresh Kraken public REST full-ladder Gate 1 can execute cleanly and still fail as a profitability factor when the `1m` origin is sparse.

Observed pattern:
- Branch: `VolatilityCompression -> MixedDeFiPrivacyAltcoinVwapExpansion -> one_minute_vwap_compression_expansion_density_full_ladder -> kraken_comp_zec_vwap_compression_expansion_density_1m_full_ladder_v1`.
- Provider/AQ chain: all fetch, strategy compile, `auto-quant-agent-material-batch`, dispatch, and rank exited `0`.
- Coverage: `COMPUSD` and `ZECUSD` across `1m/5m/15m/30m/1h/4h/1d`, `local_cache_replay=false`.
- Rank: `14` rows, `158` trades, branch fields preserved.
- Gate failure: `ZECUSD 1m` had only `3` trades; `COMPUSD 1m` had `0` trades. Positive `ZECUSD 15m/1h` and weak `COMPUSD 1h` did not rescue the `1m` root.

Durable rule:
- If the active root is `1m`, require real-cost 1m trade density before downstream.
- Positive `15m`/`1h` siblings are observation samples or new exact timeframe roots, not proof for the failed `1m` branch.
- Do not run Pre-Bayes, BBN, CatBoost/path-ranker, or execution tree after this Gate 1 failure.
- Next useful action is a materially denser 1m entry family inside the same market/regime class, not a stricter overlay on the sparse shape.

Decision vocabulary:
- `drop_or_block_gate1_practical`
- `cost_fragile_or_no_dense_origin`
- `positive_htf_observation_only`
- `restart_as_exact_timeframe_root` when intentionally moving a positive HTF sibling to its own root.
