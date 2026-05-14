# Provider Portability Probe: Crisis Volatility Expansion Fade v1

Run root: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T145305+0800-codex-long-history-esnq-factor-density-screen-v1`

Selected branch: `Crisis -> VolatilityShock -> SixHourExhaustionFade -> VolatilityExpansionFadeV1`

## Provider Readback

- binance_public BTCUSDT: trades `4264`, win_rate `0.554644`, PF `1.269985`, mean `0.00280561`
- ibkr SPY: trades `1146`, win_rate `0.503490`, PF `1.108814`, mean `0.00043429`
- yfinance ES=F: trades `626`, win_rate `0.511182`, PF `0.889566`, mean `-0.00040020`
- kraken_public PF_XBTUSD: trades `115`, win_rate `0.478261`, PF `0.804931`, mean `-0.00269056`
- kraken_public PF_SPXUSD: trades `92`, win_rate `0.456522`, PF `0.890054`, mean `-0.00409903`
- bybit_public BTCUSDT_LINEAR: trades `13`, win_rate `0.615385`, PF `3.215907`, mean `0.00341248`

## Gate

- `evidence_class:provider_backed_branch_portability_probe_not_promotion`
- `total_provider_branch_trades:6256`
- `pass:branch_path_fields_emitted`
- `partial:provider_backed_rows_present`
- `fail_closed:tradingview_mcp_fetch_failed_no_rows`
- `fail_closed:not_auto_quant_provider_routed_recipe`
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_chain`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Next

If a provider-backed row survives profitability checks, convert the branch into an Auto-Quant material recipe and then run Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree. Otherwise keep this as provider-portability negative evidence.
