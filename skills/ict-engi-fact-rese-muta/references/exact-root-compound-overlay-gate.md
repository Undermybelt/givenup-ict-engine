# Exact-root compound overlay Gate 1

Use this when a single rooted profitability factor has already passed Gate 1 and the next step is to stack an additional profit factor as a compound strategy.

## Pattern

Root identity must remain explicit through the compound overlay:

`provider -> market -> species -> symbol -> timeframe -> main_regime -> sub_regime -> base_profit_factor -> overlay_profit_factor`

Run the overlay as its own Auto-Quant material on the same exact provider/symbol/timeframe/root. Do not flatten it into a sibling factor or treat it as a new root.

## Required comparison

A compound overlay only earns downstream handoff if it passes both tests:

1. Its own Gate 1 is positive after cost stress.
2. It improves the exact-root base factor it is stacked on.

Minimum fields to record:

- `base_profit_factor`
- `profit_factor` / overlay id
- `branch_path`
- `local_cache_replay`
- `trade_count`
- `total_profit_pct`
- `cost_survives_2bps_side`
- `cost_survives_5bps_side`
- `incremental_improvement_over_base`
- `downstream_allowed`

## Fail-closed rule

If the overlay reduces trade density or flips the branch negative, classify it as:

`compound_overlay_gate_failed_sparse_negative`

Do not send it to Pre-Bayes, BBN, CatBoost, or execution-tree handoff. Keep the prior base factor as the better seed and try either a less restrictive overlay or add real mature feedback rows.

## Session example

Prior base:

- `YF NRG 5m ORB/RVOL`
- `trade_count=24`
- `total_profit_pct=3.58`
- survived `2bps/side`

Overlay tested:

- `yf_nrg_5m_orb_rvol_cmf_adx_compound_v1`
- fresh YF rows: `2965`
- batch/dispatch/rank: exit `0`
- `trade_count=3`
- `total_profit_pct=-0.01`
- `cost_survives_2bps_side=false`
- `incremental_improvement_over_base=false`
- `downstream_allowed=false`

Verdict: overlay over-filtered the profitable base branch; terminalize the overlay, preserve the base seed.
