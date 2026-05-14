# 104610 Yahoo Crypto Precision-Fix Registration v1

Run id: `20260512T104851+0800-codex-104610-yahoo-crypto-precision-fix-registration-v1`

Mode: `append_only_provider_aq_readback_registration_non_promoting`

## Scope

This packet registers the completed provider-owned Yahoo crypto precision-fix Auto-Quant/TOMAC run at `20260512T104610+0800-codex-board-b-yahoo-crypto-precision-fix-aq-v1`. It consumes existing command outputs and derived trade artifacts only. It does not rerun Auto-Quant, edit Current Cursor, approve selected history, approve source/control evidence, mutate canonical intake, promote Pre-Bayes/filter, BBN, CatBoost/path-ranking, or execution-tree output, make a trade claim, or call `update_goal`.

## Source Evidence

- Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T104610+0800-codex-board-b-yahoo-crypto-precision-fix-aq-v1`
- Compile exit: `checks/00_compile.exit`
- TOMAC run exit: `checks/01_run_tomac_yahoo_crypto_precision_fix.exit`
- TOMAC output: `command-output/01_run_tomac_yahoo_crypto_precision_fix.out`
- Metrics: `workspace/auto-quant-yahoo-crypto-precision-fix/derived/ProviderCryptoMomentumStateV1.metrics.json`, `workspace/auto-quant-yahoo-crypto-precision-fix/derived/ProviderCryptoPullbackRevertV1.metrics.json`
- Real trades: `workspace/auto-quant-yahoo-crypto-precision-fix/derived/ProviderCryptoMomentumStateV1.real_trades.jsonl`, `workspace/auto-quant-yahoo-crypto-precision-fix/derived/ProviderCryptoPullbackRevertV1.real_trades.jsonl`

## Readback

- Compile and TOMAC run exited `0`.
- `ProviderCryptoMomentumStateV1` wrote `944` real-trade rows across BTC/USDT, ETH/USDT, and SOL/USDT 1h. Aggregate result: `-57.41%` total profit, Sharpe `-3.8948`, win rate `30.1907%`, profit factor `0.6793`, max drawdown `-60.0640%`.
- `ProviderCryptoPullbackRevertV1` wrote `382` real-trade rows across BTC/USDT, ETH/USDT, and SOL/USDT 1h. Aggregate result: `-9.64%` total profit, Sharpe `-0.5777`, win rate `42.4084%`, profit factor `0.8775`, max drawdown `-10.0987%`.
- The BTC/USDT subslice for `ProviderCryptoPullbackRevertV1` was positive (`146` trades, `+2.65%`, Sharpe `0.1930`, profit factor `1.1218`), but ETH/USDT and SOL/USDT were negative and the aggregate strategy failed.
- Both strategies are branch-labelled and non-canary, but the aggregate provider-owned evidence is unprofitable and no downstream Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution-tree promotion chain exists for this root.

## Decision

This is useful provider-owned AQ/trade plumbing evidence because it preserved the precision repair and generated nonzero real-trade artifacts. It is not Board A promotion evidence. The aggregate strategies fail profitability, the only positive slice is not cross-pair validated, and the ordered downstream chain was not run on a promotable rooted branch.

## Gate

- `count_once:104610_yahoo_crypto_precision_fix_aq`.
- `pass:compile_exit0`.
- `pass:tomac_run_exit0`.
- `pass:real_trade_rows_total_1326`.
- `fail_closed:momentum_aggregate_profit_negative`.
- `fail_closed:pullback_aggregate_profit_negative`.
- `fail_closed:btc_positive_subslice_not_cross_pair_validated`.
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_chain`.
- `promotion_allowed=false`.
- `update_goal=false`.

## Next

Do not promote or repeat this exact Yahoo crypto precision-fix aggregate as Board A evidence. If the BTC pullback subslice is reused, it needs a new branch-specific hypothesis with cross-pair/timeframe controls, source/control provenance, and the ordered Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree readback.
