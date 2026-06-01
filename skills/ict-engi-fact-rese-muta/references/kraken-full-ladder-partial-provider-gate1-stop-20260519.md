# Kraken full-ladder partial-provider and Gate 1 stop pattern (2026-05-19)

## Context

Regime-rooted profit-factor continuation used Kraken public OHLCV full ladders with branch-first material fields:

```text
market -> product -> symbol -> timeframe -> main_regime -> sub_regime -> first_profit_factor
```

Two concrete slices mattered:

1. `RangeReversion -> CryptoVWAPDeviation -> obv_rsi_vwap_snapback_cost_tight -> kraken_btc_eth_sol_vwapdev_obvrsi_cost_tight_1m_full_ladder_v1`
2. `VolatilityCompression -> LegacySmartContractAltcoinVwapExpansion -> one_minute_vwap_compression_expansion_density_full_ladder -> kraken_eos_flow_vwap_compression_expansion_density_1m_full_ladder_v1`

## Durable lessons

- Treat each provider symbol/timeframe leg independently. A bad Kraken pair such as `EOSUSD` returning `EQuery:Invalid asset pair` is a provider-symbol downgrade, not a verdict on sibling `FLOWUSD` if FLOW fetches and AQ ranking complete.
- If at least one symbol completes a full real ladder (`1m/5m/15m/30m/1h/4h/1d`) with `local_cache_replay=false`, evaluate Gate 1 from the completed symbol while clearly reporting the missing/invalid sibling.
- Do not move downstream when the completed ladder has no positive 1m origin. Examples:
  - BTC/ETH/SOL vwapdev/OBV/RSI cost-tight: 21/21 provider legs fetched, AQ rank completed, but total trades were only 4 and `positive_origin_1m=[]`.
  - FLOW vwap compression-expansion density: FLOW full ladder fetched and AQ rank completed, but 1m had 0 trades, 5m was negative, 15m was only thin/micro-positive, and 4h/1d were negative.
- For these cases, terminalize as `drop_or_block_gate1_practical` / `no_downstream`: `pre_bayes_allowed=false`, `bbn_allowed=false`, `catboost_allowed=false`, `execution_tree_allowed=false`, `promotion_allowed=false`, `trade_usable=false`, `update_goal=false` are correct consequences of failed 1m density/cost gates, not problems to bypass.
- If a wrapper script returns non-zero solely because one sibling provider pair was invalid while another sibling fully ranked, read `checks/terminal_metrics.json` and `summaries/terminal_decision_summary.md` before declaring the whole run blocked. Preserve the partial-provider caveat in the final verdict.

## Verification pattern

After each run, inspect:

```text
checks/terminal_metrics.json
summaries/terminal_decision_summary.md
summaries/provider_provenance_matrix.csv
command-output/*_fetch.err for invalid pair/provider-window downgrades
```

Required fields before any downstream handoff:

```text
branch_fields_preserved=true
positive_origin_1m non-empty
cost_gate_survives=true or explicit 0/1/2/5bps stress survives
rank_total_trade_count sufficient for target density
local_cache_replay=false for live-provider evidence
```

If any is missing, stop at Gate 1 and choose a materially denser 1m entry family rather than adding overlays or running BBN/CatBoost/execution-tree.
