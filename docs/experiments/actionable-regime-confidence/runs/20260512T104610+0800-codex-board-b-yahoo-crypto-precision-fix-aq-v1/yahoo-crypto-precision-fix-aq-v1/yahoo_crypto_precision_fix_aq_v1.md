# Yahoo Crypto Precision Fix AQ v1

Run id: `20260512T104610+0800-codex-board-b-yahoo-crypto-precision-fix-aq-v1`

Gate result: `yahoo_crypto_precision_fix_aq_v1=precision_fixed_nonzero_trades_unprofitable_no_promotion`

## Scope

This is a Board B provider-owned AQ/TOMAC rerun derived from source root `20260512T102500+0800-codex-board-b-yahoo-crypto-momentum-aq-v1`.

It does not approve selected history, source/control evidence, canonical intake mutation, selected-data AutoQuant promotion, Pre-Bayes/filter, BBN, CatBoost/path-ranking, execution-tree promotion, live trading use, completion, or `update_goal`.

## Provider Readback

- `aq_provider_invoked=true`.
- Source provider acquisition is inherited from `102500`: Yahoo/yfinance crypto 1h data for `BTC-USD`, `ETH-USD`, and `SOL-USD`.
- `provider_data_acquired=true` through the source root and prepared into Freqtrade-compatible `BTC/USDT`, `ETH/USDT`, and `SOL/USDT` data.
- `provider_unreachable=[]` for the source Yahoo/yfinance slice.
- `providers_not_invoked_this_slice=[IBKR,TradingViewRemix/TVR,Kraken,Binance,Bybit]`.
- `local_cache_replay=true_provider_tied`: this rerun used the source provider-acquired workspace, not a standalone local-only dataset.

## Readback

- Compile/preflight exit: `0`.
- TOMAC/Freqtrade run exit: `0`.
- `ProviderCryptoMomentumStateV1`: `944` trades, `-57.4100%` total profit, Sharpe `-3.8948`, win rate `30.1907%`, profit factor `0.6793`, max drawdown `-60.0640%`.
- `ProviderCryptoPullbackRevertV1`: `382` trades, `-9.6400%` total profit, Sharpe `-0.5777`, win rate `42.4084%`, profit factor `0.8775`, max drawdown `-10.0987%`.
- Per-pair detail for `ProviderCryptoPullbackRevertV1` had one BTC sub-slice with `146` trades and `+2.65%`, but the aggregate strategy was negative after ETH and SOL.
- Real-trade JSONL rows exported: `944` for `ProviderCryptoMomentumStateV1`, `382` for `ProviderCryptoPullbackRevertV1`.

## Gate

- `pass:compile_exit0`.
- `pass:tomac_exit0`.
- `pass:nonzero_provider_tied_trades_1326_total`.
- `fail_closed:momentum_strategy_negative_profit_minus_57_41`.
- `fail_closed:pullback_strategy_negative_profit_minus_9_64`.
- `fail_closed:no_rc_spa_profitability_pass`.
- `fail_closed:full_six_provider_matrix_not_invoked_this_slice`.
- `fail_closed:no_selected_history_approval`.
- `fail_closed:no_source_control_unlock`.
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_promotion_rerun`.
- `promotion_allowed=false`.
- `update_goal=false`.

## Next

Do not rerun this same Yahoo crypto precision-fix shape. The next useful slice needs a different provider-owned branch that is profitable at aggregate strategy level and can survive selected-history/source-control gates before the ordered downstream promotion chain.

