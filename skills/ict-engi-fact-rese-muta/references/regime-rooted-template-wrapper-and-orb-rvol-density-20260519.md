# Regime-rooted template wrapper and ORB/RVOL density notes — 2026-05-19

## Trigger
Use when continuing ict-engine profitability-factor training with template-based Gate 1 runners or ORB/RVOL expansion families.

## Session evidence
Two real-provider Auto-Quant Gate 1 continuations were run after the user reasserted the rooted-branch contract:

1. `codex-yf-aerospace-components-orb-rvol-expansion-1m-mtf-1d-v1`
   - Run root: `support/docs/experiments/actionable-regime-confidence/runs/20260519T134021+0800-codex-yf-aerospace-components-orb-rvol-expansion-1m-mtf-1d-v1`
   - Provider: yfinance/YF; `local_cache_replay=false`
   - Requested ladder: `1m/5m/15m/30m/1h/1d`; `4h` unavailable via Yahoo and not fabricated
   - Branch shape preserved per material, e.g. `US_EQ -> single_stock -> TDG -> 1m -> TrendExpansion -> AerospaceComponentsOpeningRangeExpansion -> orb_rvol_expansion -> yf_aerospace_components_orb_rvol_expansion_1m_mtf_1d_v1`
   - Result: `rank_rows=17`, `rank_total_trade_count=8`, `one_minute_trades=0`, `positive_1m=[]`, `dense_positive_gate=false`
   - Decision: `keep_subclass_evidence_or_drop_gate1_no_downstream`

2. `codex-yf-ai-infra-hardware-orb-rvol-expansion-1m-mtf-v1`
   - Run root: `support/docs/experiments/actionable-regime-confidence/runs/20260519T135257+0800-codex-yf-ai-infra-hardware-orb-rvol-expansion-1m-mtf-v1`
   - Provider: yfinance/YF; `local_cache_replay=false`
   - Requested ladder: `1m/5m/15m/30m/1h`
   - Result: `rank_rows=12`, `rank_total_trade_count=6`, `one_minute_trades=0`, `positive_1m=[]`, `dense_positive_gate=false`
   - Decision: `keep_subclass_evidence_or_drop_gate1_no_downstream`

## Durable lessons

### ORB/RVOL expansion density gate
If a fresh ORB/RVOL expansion family produces `one_minute_trades=0` and no positive 1m rows after a real provider/AQ ladder, stop before downstream.

Do not add same-root overlays to rescue that root. Classify as subclass/negative evidence and pivot to a denser 1m entry family. Sparse 5m/15m or higher-timeframe rows are not enough to open Pre-Bayes, BBN, CatBoost, or execution-tree.

### Template wrapper branch parity
When cloning a template runner, overriding only top-level `BRANCH_PATH` is not enough. The wrapper must also override material-level branch helpers such as:

- `branch_path_for_spec(spec_item)`
- `branch_identity_for_spec(spec_item)`
- package/material namespace and `consumer_evidence_profile` fields

Otherwise summaries can show a generic family branch like `TrendExpansion -> ... -> factor_id` instead of the required full root:

`provider/market -> product -> symbol -> timeframe -> main_regime -> sub_regime -> first_profit_factor`

Treat missing material-level market/product/symbol/timeframe branch identity as a parity defect even when helper counters say `branch_fields_preserved=true`.

## Gate mapping
For both runs, downstream gates correctly stayed false:

- `pre_bayes_allowed=false`
- `bbn_allowed=false`
- `catboost_allowed=false`
- `execution_tree_allowed=false`
- `promotion_allowed=false`
- `trade_usable=false`

This is a correct Gate 1 stop, not a downstream failure.
