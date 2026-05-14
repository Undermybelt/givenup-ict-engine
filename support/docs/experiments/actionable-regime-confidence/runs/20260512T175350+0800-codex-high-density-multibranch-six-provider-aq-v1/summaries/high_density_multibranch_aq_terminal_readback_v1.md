# 175350 High-Density Multibranch AQ Terminal Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T175350+0800-codex-high-density-multibranch-six-provider-aq-v1`

Source claim: `175350_high_density_multibranch_six_provider_aq_packet_v1`

State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T175350+0800-codex-high-density-multibranch-six-provider-aq-v1/state`

Branch paths preserved in material notes:
- `TrendExpansion -> NormalVolatility -> MomentumPullbackFast -> ema_rsi_pullback_density_v1`
- `TrendExpansion -> HighVolatility -> BreakoutContinuationFast -> donchian_volume_breakout_density_v1`
- `RangeConsolidation -> NormalVolatility -> MeanReversionFast -> rsi_bollinger_reversion_density_v1`
- `Transition -> VolatilityCompression -> CompressionBreakoutFast -> atr_compression_breakout_density_v1`

Provider/material preflight:
- Provider rows: `6`
- Material JSON files: `6`
- `provider_data_acquired_this_step=false`
- `same_root_replay_copy=true`
- IBKR source used the prior verified long-span `/tmp` raw CSV and normalized it into this run root because the prior repo run did not contain a normalized IBKR CSV.
- Current `provider-status --agent`: yfinance market data is ready; IBKR and public crypto adapters are blocked by Python dependency health; TradingView MCP is still unhealthy.

Auto-Quant execution:
- Batch: `auto_quant_agent_material_batch.20260512T105759.936Z.json`
- Dispatch: `auto_quant_agent_material_dispatch.20260512T105915.013Z.json`
- Rank: `auto_quant_agent_material_rank.20260512T110103.305Z.json`
- Totals: `6` jobs, `6` completed, `0` blocked, `0` failed.

AQ metrics:

| Unit | Status | Trades | Win rate | Sharpe | Return | Profit factor |
|---|---:|---:|---:|---:|---:|---:|
| yfinance/YF SPY 1h | completed | 1 | 100.0% | -100.0 | 1.86% | 0.0 |
| IBKR SPY 1h | completed | 19 | 26.3158% | -0.0621 | -4.6% | 0.4235 |
| TradingViewRemix/TVR BTCUSD 1h | completed | 0 | 0.0% | 0.0 | 0.0% | 0.0 |
| Kraken XBTUSD 1h | completed | 0 | 0.0% | 0.0 | 0.0% | 0.0 |
| Binance BTCUSDT 1h | completed | 0 | 0.0% | 0.0 | 0.0% | 0.0 |
| Bybit BTCUSDT 1h | completed | 0 | 0.0% | 0.0 | 0.0% | 0.0 |

Gate:
- `aq_dispatch_rank_completed=true`
- `branch_paths_preserved_in_material=true`
- `branch_keyed_profitability_observation=false`
- `adequate_trade_density=false`
- `regime_conditioned_win_rate=false`
- `pre_bayes_filter_allowed=false`
- `bbn_learning_allowed=false`
- `catboost_learning_allowed=false`
- `execution_tree_branch_weight_update_allowed=false`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

Interpretation:
- Fail closed. AQ consumed the same-root high-density multibranch provider material, but the output is only per-material aggregate metrics. It is not a branch-keyed or regime-conditioned profitability packet.
- The only positive return row is a one-trade yfinance sample, which is diagnostic only and not support.
- The highest-density row is IBKR with 19 trades, negative return, low win rate, and profit factor below 1.
- Four provider units produced zero trades.

Next:
- Do not feed this packet into Pre-Bayes/filter, BBN, CatBoost/path-ranker, execution tree, or feedback/update learning.
- Future work should either split the four branch paths into separately measured material units or add branch-tag extraction to the AQ readback so trade density and win rate are reported by `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`.
