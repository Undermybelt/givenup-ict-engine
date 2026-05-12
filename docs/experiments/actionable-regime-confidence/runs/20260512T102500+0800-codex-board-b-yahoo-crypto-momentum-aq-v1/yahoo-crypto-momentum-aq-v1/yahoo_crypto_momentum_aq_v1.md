# Yahoo Crypto Momentum AQ v1

Run root: `20260512T102500+0800-codex-board-b-yahoo-crypto-momentum-aq-v1`

This is a provider-owned Yahoo/yfinance crypto incubation slice for `BTC-USD`, `ETH-USD`, and `SOL-USD` 1h bars over `2024-06-01 00:00:00+00:00 -> 2026-05-11 23:00:00+00:00`.

## Provider And Prepare

- `aq_provider_invoked=true`
- `provider_requested=[yfinance/Yahoo:BTC-USD:1h, yfinance/Yahoo:ETH-USD:1h, yfinance/Yahoo:SOL-USD:1h]`
- `provider_unreachable=[]`
- `providers_not_invoked_this_slice=[IBKR, TradingViewRemix/TVR, Kraken, Binance, Bybit]`
- `local_cache_replay=false`

Provider fetch and prepare all exited `0`.

| Pair | Provider rows | 1h bars | 4h bars | 1d bars | Bad date | Duplicate ts | NaN OHLC |
|---|---:|---:|---:|---:|---:|---:|---:|
| BTC/USDT | 17,007 | 17,007 | 4,254 | 710 | 0 | 0 | 0 |
| ETH/USDT | 17,004 | 17,004 | 4,254 | 710 | 0 | 0 | 0 |
| SOL/USDT | 17,006 | 17,006 | 4,254 | 710 | 0 | 0 | 0 |

## Signal Density

The precheck used the strategy entry conditions directly on the prepared 1h feathers, with millisecond-aware timestamp decoding.

| Strategy | Branch path | Entry candidates |
|---|---|---:|
| `ProviderCryptoMomentumStateV1` | `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1` | 1,085 |
| `ProviderCryptoPullbackRevertV1` | `Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1` | 931 |

## TOMAC / Freqtrade Readback

The concurrent lane had already produced `07_run_provider_crypto_momentum.*`. A later duplicate readback `04_run_tomac_yahoo_crypto_momentum.*` used the same workspace and matched the same metrics. Count this run once.

| Strategy | Trades | Total profit % | Sharpe | Win rate % | Profit factor | Max drawdown % | Fills |
|---|---:|---:|---:|---:|---:|---:|---|
| `ProviderCryptoMomentumStateV1` | 295 | -18.73 | -1.0287 | 34.9153 | 0.7350 | -23.4587 | SOL only |
| `ProviderCryptoPullbackRevertV1` | 109 | -7.08 | -0.4663 | 40.3670 | 0.6898 | -8.6498 | SOL only |

## Gate

- `count_once:102500_provider_yahoo_crypto_momentum_aq`
- `pass:provider_yahoo_btc_eth_sol_fetch_exit0`
- `pass:prepare_external_exit0_btc_eth_sol_1h_4h_1d_feathers`
- `pass:signal_density_nonzero_momentum_1085_pullback_931`
- `pass:tomac_exit0_two_provider_crypto_strategies`
- `pass:nonzero_freqtrade_trades_momentum_295_pullback_109`
- `fail_closed:momentum_negative_profit_minus_18_73_winrate_34_9153_pf_0_7350`
- `fail_closed:pullback_negative_profit_minus_7_08_winrate_40_3670_pf_0_6898`
- `fail_closed:btc_eth_no_fills_only_sol_filled`
- `fail_closed:no_rc_spa_profitability_pass`
- `fail_closed:downstream_promotion_rerun_false`
- `promotion_allowed=false`
- `update_goal=false`

## Evidence

- Summary JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T102500+0800-codex-board-b-yahoo-crypto-momentum-aq-v1/yahoo-crypto-momentum-aq-v1/yahoo_crypto_momentum_aq_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T102500+0800-codex-board-b-yahoo-crypto-momentum-aq-v1/checks/yahoo_crypto_momentum_aq_v1_assertions.out`
- Signal-density precheck: `docs/experiments/actionable-regime-confidence/runs/20260512T102500+0800-codex-board-b-yahoo-crypto-momentum-aq-v1/command-output/03_signal_density_precheck.out`
- Primary TOMAC output: `docs/experiments/actionable-regime-confidence/runs/20260512T102500+0800-codex-board-b-yahoo-crypto-momentum-aq-v1/command-output/07_run_provider_crypto_momentum.out`
- Duplicate TOMAC readback: `docs/experiments/actionable-regime-confidence/runs/20260512T102500+0800-codex-board-b-yahoo-crypto-momentum-aq-v1/command-output/04_run_tomac_yahoo_crypto_momentum.out`
