# Yahoo BTC Pullback Precision AQ v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T104902+0800-codex-board-b-yahoo-btc-pullback-precision-aq-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T104610+0800-codex-board-b-yahoo-crypto-precision-fix-aq-v1`

## Scope

This is a standalone BTC-only rerun of the Yahoo crypto pullback/momentum AQ workspace. It is not the later `105014` filtered-trade downstream readback, and it is not a provider-matrix proof packet.

The run-local TOMAC config uses `BTC/USDT`, `1h`, `20240601-20260512`, spot mode, `entry_pricing.price_side=other`, `exit_pricing.price_side=other`, and tick-size synthetic market metadata.

## Evidence

- Compile exit: `checks/00_compile.exit` = `0`
- TOMAC exit: `checks/01_run_tomac_yahoo_btc_pullback_precision.exit` = `0`
- TOMAC stdout: `command-output/01_run_tomac_yahoo_btc_pullback_precision.out`
- Strategy metadata: `workspace/auto-quant-yahoo-btc-pullback-precision/run_tomac.py`
- Config: `workspace/auto-quant-yahoo-btc-pullback-precision/config.tomac.json`
- Pullback metrics: `workspace/auto-quant-yahoo-btc-pullback-precision/derived/ProviderCryptoPullbackRevertV1.metrics.json`
- Pullback real trades: `workspace/auto-quant-yahoo-btc-pullback-precision/derived/ProviderCryptoPullbackRevertV1.real_trades.jsonl`
- Momentum metrics: `workspace/auto-quant-yahoo-btc-pullback-precision/derived/ProviderCryptoMomentumStateV1.metrics.json`
- Momentum real trades: `workspace/auto-quant-yahoo-btc-pullback-precision/derived/ProviderCryptoMomentumStateV1.real_trades.jsonl`

## Readback

`ProviderCryptoPullbackRevertV1` is the only positive branch:

- Path: `Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1`
- Pair: `BTC/USDT`
- Trades: `146`
- Total profit: `+2.83%`
- Sharpe: `0.1875`
- Win rate: `45.2055%`
- Profit factor: `1.1186`
- Max drawdown: `-4.2915%`

`ProviderCryptoMomentumStateV1` is negative:

- Path: `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1`
- Pair: `BTC/USDT`
- Trades: `315`
- Total profit: `-21.96%`
- Sharpe: `-1.5339`
- Win rate: `23.8095%`
- Profit factor: `0.6357`
- Max drawdown: `-23.3992%`

The real-trade rows preserve source-side branch fields for both strategies:

- `main_regime`
- `sub_regime`
- `sub_sub_regime_or_profit_factor`
- `profit_factor`
- `regime_profit_branch_path`

## Gate

- `pass:compile_exit0`
- `pass:tomac_exit0`
- `pass:standalone_btc_only_aq_recipe_not_filtered_trade_slice`
- `pass:positive_noncanary_pullback_branch_146_trades_profit_2_83`
- `pass:source_side_regime_profit_branch_path_present`
- `fail_closed:momentum_sibling_negative_profit_minus_21_96`
- `fail_closed:provider_matrix_rows_absent_under_105234_hard_gate`
- `fail_closed:single_provider_single_instrument_yahoo_btc_only`
- `fail_closed:no_selected_history_or_source_control_unlock`
- `fail_closed:downstream_promotion_readback_not_run_due_provider_matrix_gate`
- `promotion_allowed=false`
- `update_goal=false`

## Decision

Register `104902` once as a positive standalone BTC-only AQ measurement, but do not promote it and do not use it as a downstream promotion seed unless a later packet supplies the required provider-matrix authority evidence or explicitly rescopes the gate.
