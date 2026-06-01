# Futures symbol sanitization and exact timeframe-root Gate 1

## Trigger
Use when YF/Yahoo futures symbols such as `GC=F`, `SI=F`, `ES=F`, or `NQ=F` have real OHLCV rows but Auto-Quant/FreqTrade reports `No pair in whitelist` or returns all failed rank rows before any factor verdict.

## Durable lesson
The failure is a material/AQ pair-contract blocker, not a factor verdict. Keep the raw provider symbol in provenance, but map it to an Auto-Quant/FreqTrade-safe pseudo pair before Gate 1:

- `GC=F` -> `GCF/USD`
- `SI=F` -> `SIF/USD`
- `ES=F` -> `ESF/USD`
- `NQ=F` -> `NQF/USD`

The material should carry both:

- `symbol` / `pair`: sanitized pair used by Auto-Quant
- `consumer_evidence_profile.symbol`: raw provider symbol
- `consumer_evidence_profile.auto_quant_pair`: sanitized pair
- `provider_provenance`: raw symbol, provider, timeframe, and window

## Workflow
1. Fetch or reuse real provider rows for each timeframe; do not fabricate missing frames.
2. Copy normalized CSVs into the new run with sanitized file names only for AQ ingestion.
3. Generate strategy/material names and `package_id` from sanitized pairs.
4. Preserve full branch identity:
   `market -> instrument_kind -> raw_symbol_or_pair -> timeframe -> main_regime -> sub_regime -> first_profit_factor -> overlays...`
5. Run AQ Gate 1 and inspect `ranking[]`, not helper counters.
6. Cost-stress every positive row at `0/1/2/5bps` per side.
7. If the intended root timeframe fails cost/density, stop before Pre-Bayes/BBN/CatBoost/tree.
8. If a sibling timeframe survives, restart it as its own exact timeframe root; do not let it rescue the failed root.
9. If downstream reaches policy export but `mature_rows=0` or `history_mature_rows=0`, keep `catboost_allowed=false`, `execution_tree_allowed=false`, `promotion_allowed=false`, and `trade_usable=false`.

## Session evidence pattern
A futures metals run with raw `GC=F/SI=F` fetched `1m/5m/15m/30m/1h/1d` successfully but all AQ rows failed with `No pair in whitelist`. Re-running with `GCF/USD/SIF/USD` produced completed AQ rows. `SIF/USD 1h` survived Gate 1 and 5bps cost stress (`23` trades, raw `+3.52%`, 5bps `+1.22%`), but downstream remained a seed only because policy maturity was `mature_rows=0`, `history_mature_rows=0`.

## Classification
- Raw futures symbol whitelist failure: `material_contract_blocker`, not `factor_failed`.
- Sanitized pair Gate 1 positive but no mature rows: `downstream_seed_maturity_blocked`.
- Positive higher timeframe after failed 1m/5m root: `new_exact_timeframe_root_candidate`, not promotion.
