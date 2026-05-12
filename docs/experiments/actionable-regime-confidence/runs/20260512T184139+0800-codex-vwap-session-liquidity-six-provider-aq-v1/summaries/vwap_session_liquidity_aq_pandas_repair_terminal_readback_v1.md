# 184139 VWAP Session Liquidity AQ Pandas Repair Terminal Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T184139+0800-codex-vwap-session-liquidity-six-provider-aq-v1`

Repair claim: `1906xx_184139_isolated_aq_pandas_runtime_repair_v1`

Purpose:
- Repair only the isolated Auto-Quant runtime dependency blocker from the prior dispatch failure.
- Reuse the existing same-root material/batch artifacts.
- Do not fetch providers, create a new factor root, or run downstream Pre-Bayes/BBN/CatBoost/execution-tree.

Runtime probe:
- `command-output/12_aq_venv_pandas_probe_before.out`
- The run-root AQ venv imported pandas successfully: `pandas=2.3.3`.
- No new dependency install was required in this slice.

Auto-Quant artifacts:
- Batch source used by repaired dispatch: `state/auto-quant/PROVIDER_VWAP_184139/auto_quant_agent_material_batch.20260512T110647.346Z.json`
- Dispatch: `state/auto-quant/PROVIDER_VWAP_184139/auto_quant_agent_material_dispatch.20260512T111226.440Z.json`
- Rank: `state/auto-quant/PROVIDER_VWAP_184139/auto_quant_agent_material_rank.20260512T111650.279Z.json`

Branch paths preserved in material:
- `RangeConsolidation -> LiquidityMeanReversion -> vwap_reclaim -> vwap_reclaim_long_v1`
- `TrendExpansion -> SessionContinuation -> session_range_breakout -> session_range_breakout_long_v1`
- `VolatilityCompression -> LiquidityExpansion -> volume_zscore_expansion -> volume_zscore_expansion_long_v1`
- `Transition -> RiskSuppression -> low_liquidity_or_overextension_guard -> liquidity_guard_v1`

AQ metrics:

| Unit | Status | Trades | Win rate | Sharpe | Return | Profit factor |
|---|---:|---:|---:|---:|---:|---:|
| yfinance/YF SPY 1h | completed | 133 | 30.0752% | -0.0476 | -0.64% | 0.9581 |
| IBKR SPY 1h | completed | 54 | 29.6296% | -0.2784 | -0.81% | 0.8264 |
| Binance BTCUSDT 1h | completed | 0 | 0.0% | 0.0 | 0.0% | 0.0 |
| Bybit BTCUSDT 1h | completed | 0 | 0.0% | 0.0 | 0.0% | 0.0 |
| Kraken XBTUSD 1h | completed | 0 | 0.0% | 0.0 | 0.0% | 0.0 |
| TradingViewRemix/TVR BTC-USD 1h | completed | 0 | 0.0% | 0.0 | 0.0% | 0.0 |

Gate:
- `runtime_dependency_repair_status:passed_without_install_pandas_available`
- `aq_dispatch_completed=true`
- `aq_rank_completed=true`
- `provider_unit_profitability_observations_present=true`
- `branch_paths_preserved_in_material=true`
- `branch_keyed_profitability_observation=false`
- `aggregate_market_negative_sample=true`
- `market_factor_negative_sample=false`
- `identity_negative_sample=true`
- `adequate_branch_trade_density=false`
- `regime_conditioned_win_rate=false`
- `pre_bayes_filter_allowed=false`
- `bbn_learning_allowed=false`
- `catboost_learning_allowed=false`
- `execution_tree_branch_weight_update_allowed=false`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

Interpretation:
- The infrastructure blocker was cleared enough for dispatch/rank to run.
- The result is still fail-closed for the Board B objective because AQ reports provider/material aggregate metrics, not branch-keyed trade/outcome rows.
- The tradfi rows are meaningful aggregate negative observations, but they are not safe to feed into BBN/CatBoost/execution-tree as branch market labels because the four branch paths are collapsed into each provider unit.
- Four crypto/TVR provider units remain zero-trade diagnostics.

Next:
- Do not run downstream from this aggregate rank.
- Future work should extract branch-tagged trades from the AQ workspace or rerun as one material per branch path so negative evidence can be classified as branch-level market evidence instead of identity/aggregation failure.
