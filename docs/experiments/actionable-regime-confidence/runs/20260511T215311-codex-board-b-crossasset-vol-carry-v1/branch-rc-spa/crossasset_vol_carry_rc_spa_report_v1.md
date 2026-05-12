# CrossAssetVolCarry RC-SPA v1

Run id: `20260511T215311+0800-codex-board-b-crossasset-vol-carry-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `80.0000`
- Price-root paths passed: `0/4`
- Scoped Manipulation component pass consumed: `True`
- Variant rows: `1666`
- Selected rows: `635`
- Selected root counts: `{'Bull': 569, 'Bear': 6, 'Sideways': 33, 'Crisis': 27, 'Manipulation(scoped)': 13535}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_fold_trade_depth|reject_overfit_risk|reject_tail_risk; Bear=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk; Sideways=fail:reject_thin_trades|reject_fold_trade_depth|reject_overfit_risk; Crisis=fail:reject_thin_trades|reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60

## Panel / Variant Summary

| Market | TF | Variant | Trades | Mean | Win Rate | Net R |
|---|---:|---|---:|---:|---:|---:|
| SPY/USD | 1d | `risk_carry_momentum` | 52 | 0.004538 | 0.5962 | 0.235970 |
| SPY/USD | 1d | `crypto_beta_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1d | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1d | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1d | `risk_breakdown_short` | 11 | -0.004879 | 0.3636 | -0.053665 |
| SPY/USD | 1d | `relief_fade_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1d | `spread_reversion` | 5 | 0.003710 | 0.6000 | 0.018552 |
| SPY/USD | 1d | `dispersion_breakout` | 7 | -0.014823 | 0.2857 | -0.103760 |
| SPY/USD | 1d | `defensive_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1d | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1d | `risk_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1d | `panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 1d | `risk_carry_momentum` | 24 | 0.003540 | 0.5833 | 0.084954 |
| QQQ/USD | 1d | `crypto_beta_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 1d | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 1d | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 1d | `risk_breakdown_short` | 6 | 0.007274 | 0.5000 | 0.043643 |
| QQQ/USD | 1d | `relief_fade_short` | 1 | -0.029474 | 0.0000 | -0.029474 |
| QQQ/USD | 1d | `spread_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 1d | `dispersion_breakout` | 4 | -0.002238 | 0.5000 | -0.008953 |
| QQQ/USD | 1d | `defensive_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 1d | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 1d | `risk_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 1d | `panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| NQ/USD | 1d | `risk_carry_momentum` | 66 | 0.003441 | 0.5909 | 0.227076 |
| NQ/USD | 1d | `crypto_beta_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| NQ/USD | 1d | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| NQ/USD | 1d | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| NQ/USD | 1d | `risk_breakdown_short` | 96 | -0.007072 | 0.4375 | -0.678915 |
| NQ/USD | 1d | `relief_fade_short` | 4 | -0.009697 | 0.5000 | -0.038789 |
| NQ/USD | 1d | `spread_reversion` | 2 | 0.039520 | 1.0000 | 0.079040 |
| NQ/USD | 1d | `dispersion_breakout` | 15 | 0.003986 | 0.5333 | 0.059786 |
| NQ/USD | 1d | `defensive_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| NQ/USD | 1d | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| NQ/USD | 1d | `risk_tail_short` | 8 | -0.024571 | 0.5000 | -0.196569 |
| NQ/USD | 1d | `panic_reversal` | 1 | 0.026778 | 1.0000 | 0.026778 |
| ES/USD | 1d | `risk_carry_momentum` | 53 | 0.003951 | 0.6415 | 0.209426 |
| ES/USD | 1d | `crypto_beta_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ES/USD | 1d | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ES/USD | 1d | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ES/USD | 1d | `risk_breakdown_short` | 11 | -0.008776 | 0.2727 | -0.096536 |
| ES/USD | 1d | `relief_fade_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ES/USD | 1d | `spread_reversion` | 5 | 0.009337 | 0.8000 | 0.046686 |
| ES/USD | 1d | `dispersion_breakout` | 7 | -0.015236 | 0.1429 | -0.106655 |
| ES/USD | 1d | `defensive_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ES/USD | 1d | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ES/USD | 1d | `risk_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ES/USD | 1d | `panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPL/USD | 1d | `risk_carry_momentum` | 43 | 0.003680 | 0.5349 | 0.158249 |
| AAPL/USD | 1d | `crypto_beta_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPL/USD | 1d | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPL/USD | 1d | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPL/USD | 1d | `risk_breakdown_short` | 10 | -0.029200 | 0.3000 | -0.291995 |
| AAPL/USD | 1d | `relief_fade_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPL/USD | 1d | `spread_reversion` | 5 | 0.008378 | 0.6000 | 0.041890 |
| AAPL/USD | 1d | `dispersion_breakout` | 7 | -0.009759 | 0.5714 | -0.068312 |
| AAPL/USD | 1d | `defensive_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPL/USD | 1d | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPL/USD | 1d | `risk_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AAPL/USD | 1d | `panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `risk_carry_momentum` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `crypto_beta_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `defensive_carry_long` | 6 | 0.016969 | 0.6667 | 0.101816 |
| EUR/USD | 1d | `risk_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `relief_fade_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `spread_reversion` | 1 | 0.005802 | 1.0000 | 0.005802 |
| EUR/USD | 1d | `dispersion_breakout` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `defensive_range_reversion` | 15 | 0.002859 | 0.6667 | 0.042883 |
| EUR/USD | 1d | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `risk_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| EUR/USD | 1d | `panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1d | `risk_carry_momentum` | 47 | 0.002652 | 0.4894 | 0.124658 |
| BTC/USDT | 1d | `crypto_beta_carry` | 37 | 0.018845 | 0.6216 | 0.697266 |
| BTC/USDT | 1d | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1d | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1d | `risk_breakdown_short` | 43 | 0.000927 | 0.4651 | 0.039846 |
| BTC/USDT | 1d | `relief_fade_short` | 6 | 0.022680 | 0.6667 | 0.136082 |
| BTC/USDT | 1d | `spread_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1d | `dispersion_breakout` | 12 | 0.009085 | 0.4167 | 0.109014 |
| BTC/USDT | 1d | `defensive_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1d | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1d | `risk_tail_short` | 4 | -0.036385 | 0.5000 | -0.145540 |
| BTC/USDT | 1d | `panic_reversal` | 3 | 0.020734 | 0.6667 | 0.062201 |
| ETH/USDT | 1d | `risk_carry_momentum` | 43 | -0.003665 | 0.4651 | -0.157577 |
| ETH/USDT | 1d | `crypto_beta_carry` | 33 | 0.001648 | 0.5758 | 0.054388 |
| ETH/USDT | 1d | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ETH/USDT | 1d | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ETH/USDT | 1d | `risk_breakdown_short` | 43 | -0.003652 | 0.4884 | -0.157020 |
| ETH/USDT | 1d | `relief_fade_short` | 6 | -0.038903 | 0.3333 | -0.233416 |
| ETH/USDT | 1d | `spread_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ETH/USDT | 1d | `dispersion_breakout` | 6 | 0.025018 | 0.6667 | 0.150110 |
| ETH/USDT | 1d | `defensive_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ETH/USDT | 1d | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ETH/USDT | 1d | `risk_tail_short` | 4 | -0.022858 | 0.5000 | -0.091431 |
| ETH/USDT | 1d | `panic_reversal` | 4 | 0.025073 | 0.7500 | 0.100293 |
| BNB/USDT | 1d | `risk_carry_momentum` | 43 | 0.029550 | 0.5581 | 1.270636 |
| BNB/USDT | 1d | `crypto_beta_carry` | 33 | 0.027076 | 0.6364 | 0.893524 |
| BNB/USDT | 1d | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BNB/USDT | 1d | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BNB/USDT | 1d | `risk_breakdown_short` | 39 | 0.007902 | 0.4872 | 0.308167 |
| BNB/USDT | 1d | `relief_fade_short` | 5 | -0.035480 | 0.2000 | -0.177401 |
| BNB/USDT | 1d | `spread_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BNB/USDT | 1d | `dispersion_breakout` | 8 | 0.050953 | 0.7500 | 0.407627 |
| BNB/USDT | 1d | `defensive_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BNB/USDT | 1d | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BNB/USDT | 1d | `risk_tail_short` | 5 | 0.004155 | 0.6000 | 0.020776 |
| BNB/USDT | 1d | `panic_reversal` | 3 | -0.006773 | 0.6667 | -0.020320 |
| SOL/USDT | 1d | `risk_carry_momentum` | 39 | 0.026726 | 0.4359 | 1.042305 |
| SOL/USDT | 1d | `crypto_beta_carry` | 27 | 0.014049 | 0.4444 | 0.379316 |
| SOL/USDT | 1d | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SOL/USDT | 1d | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SOL/USDT | 1d | `risk_breakdown_short` | 42 | 0.001174 | 0.6429 | 0.049298 |
| SOL/USDT | 1d | `relief_fade_short` | 7 | -0.008158 | 0.5714 | -0.057105 |
| SOL/USDT | 1d | `spread_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SOL/USDT | 1d | `dispersion_breakout` | 1 | 0.254926 | 1.0000 | 0.254926 |
| SOL/USDT | 1d | `defensive_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SOL/USDT | 1d | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SOL/USDT | 1d | `risk_tail_short` | 5 | 0.010998 | 0.6000 | 0.054990 |
| SOL/USDT | 1d | `panic_reversal` | 4 | -0.015772 | 0.5000 | -0.063089 |
| AVAX/USDT | 1d | `risk_carry_momentum` | 38 | 0.045452 | 0.6316 | 1.727190 |
| AVAX/USDT | 1d | `crypto_beta_carry` | 23 | -0.001456 | 0.3913 | -0.033487 |
| AVAX/USDT | 1d | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AVAX/USDT | 1d | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AVAX/USDT | 1d | `risk_breakdown_short` | 40 | 0.017029 | 0.6750 | 0.681147 |
| AVAX/USDT | 1d | `relief_fade_short` | 4 | -0.015550 | 0.5000 | -0.062201 |
| AVAX/USDT | 1d | `spread_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AVAX/USDT | 1d | `dispersion_breakout` | 1 | 0.053685 | 1.0000 | 0.053685 |
| AVAX/USDT | 1d | `defensive_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AVAX/USDT | 1d | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| AVAX/USDT | 1d | `risk_tail_short` | 4 | -0.024381 | 0.5000 | -0.097526 |
| AVAX/USDT | 1d | `panic_reversal` | 1 | -0.149660 | 0.0000 | -0.149660 |
| BTCY/USD | 1d | `risk_carry_momentum` | 44 | 0.002357 | 0.4773 | 0.103710 |
| BTCY/USD | 1d | `crypto_beta_carry` | 36 | 0.020134 | 0.6667 | 0.724824 |
| BTCY/USD | 1d | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTCY/USD | 1d | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTCY/USD | 1d | `risk_breakdown_short` | 12 | -0.040339 | 0.3333 | -0.484066 |
| BTCY/USD | 1d | `relief_fade_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTCY/USD | 1d | `spread_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTCY/USD | 1d | `dispersion_breakout` | 9 | -0.014227 | 0.4444 | -0.128045 |
| BTCY/USD | 1d | `defensive_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTCY/USD | 1d | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTCY/USD | 1d | `risk_tail_short` | 1 | -0.128471 | 0.0000 | -0.128471 |
| BTCY/USD | 1d | `panic_reversal` | 1 | 0.078334 | 1.0000 | 0.078334 |
| SPY/USD | 4h | `risk_carry_momentum` | 14 | -0.000072 | 0.5714 | -0.001006 |
| SPY/USD | 4h | `crypto_beta_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `risk_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `relief_fade_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `spread_reversion` | 4 | 0.004648 | 0.5000 | 0.018592 |
| SPY/USD | 4h | `dispersion_breakout` | 1 | -0.008168 | 0.0000 | -0.008168 |
| SPY/USD | 4h | `defensive_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `risk_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 4h | `risk_carry_momentum` | 12 | 0.001601 | 0.5833 | 0.019215 |
| QQQ/USD | 4h | `crypto_beta_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 4h | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 4h | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 4h | `risk_breakdown_short` | 9 | -0.001825 | 0.6667 | -0.016421 |
| QQQ/USD | 4h | `relief_fade_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 4h | `spread_reversion` | 1 | 0.036417 | 1.0000 | 0.036417 |
| QQQ/USD | 4h | `dispersion_breakout` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 4h | `defensive_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 4h | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 4h | `risk_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| QQQ/USD | 4h | `panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| NQ/USD | 4h | `risk_carry_momentum` | 25 | 0.000912 | 0.5200 | 0.022795 |
| NQ/USD | 4h | `crypto_beta_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| NQ/USD | 4h | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| NQ/USD | 4h | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| NQ/USD | 4h | `risk_breakdown_short` | 243 | 0.001923 | 0.5473 | 0.467169 |
| NQ/USD | 4h | `relief_fade_short` | 30 | -0.001927 | 0.4000 | -0.057798 |
| NQ/USD | 4h | `spread_reversion` | 4 | 0.004970 | 0.5000 | 0.019881 |
| NQ/USD | 4h | `dispersion_breakout` | 3 | 0.001538 | 0.6667 | 0.004613 |
| NQ/USD | 4h | `defensive_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| NQ/USD | 4h | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| NQ/USD | 4h | `risk_tail_short` | 32 | -0.010102 | 0.4375 | -0.323259 |
| NQ/USD | 4h | `panic_reversal` | 10 | 0.009778 | 0.7000 | 0.097777 |
| DIA/USD | 4h | `risk_carry_momentum` | 14 | 0.001503 | 0.4286 | 0.021037 |
| DIA/USD | 4h | `crypto_beta_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 4h | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 4h | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 4h | `risk_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 4h | `relief_fade_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 4h | `spread_reversion` | 3 | 0.004503 | 0.6667 | 0.013508 |
| DIA/USD | 4h | `dispersion_breakout` | 1 | -0.019530 | 0.0000 | -0.019530 |
| DIA/USD | 4h | `defensive_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 4h | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 4h | `risk_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 4h | `panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 4h | `risk_carry_momentum` | 12 | 0.001894 | 0.5000 | 0.022725 |
| IWM/USD | 4h | `crypto_beta_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 4h | `gold_lag_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 4h | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 4h | `risk_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 4h | `relief_fade_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 4h | `spread_reversion` | 3 | 0.005469 | 0.3333 | 0.016406 |
| IWM/USD | 4h | `dispersion_breakout` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 4h | `defensive_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 4h | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 4h | `risk_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 4h | `panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 4h | `risk_carry_momentum` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 4h | `crypto_beta_carry` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 4h | `gold_lag_short` | 12 | -0.010772 | 0.3333 | -0.129265 |
| GLD/USD | 4h | `defensive_carry_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 4h | `risk_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 4h | `relief_fade_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 4h | `spread_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 4h | `dispersion_breakout` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 4h | `defensive_range_reversion` | 2 | -0.006557 | 0.0000 | -0.013115 |
| GLD/USD | 4h | `tail_hedge_long` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 4h | `risk_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 4h | `panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `risk_carry_momentum` | 569 | 4 | 3 | 1.0000 | 0.004289 | 1.000 | 3.0428 | 80.0000 | `fail:reject_fold_trade_depth|reject_overfit_risk|reject_tail_risk` |
| Bear | `defensive_carry_long` | 6 | 3 | 1 | 1.0000 | 0.003084 | 1.000 | 1.7685 | 75.5846 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk` |
| Sideways | `spread_reversion` | 33 | 4 | 4 | 1.0000 | 0.003685 | 1.000 | 2.6955 | 78.5102 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_overfit_risk` |
| Crisis | `panic_reversal` | 27 | 4 | 1 | 0.7500 | -0.021537 | 1.000 | 0.3492 | 25.5382 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60` |
| Manipulation(scoped) | `short_tp120_sl060_h72` | 13535 | 12 | 1127 | 0.7500 | 0.005609 | 0.000 | 1.0000 | 100.0000 | `pass` |

## Inputs

- Local Auto-Quant feathers: `/Users/thrill3r/Auto-Quant/user_data/data`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^IXIC`
- Scoped Manipulation component: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2.md`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T215311-codex-board-b-crossasset-vol-carry-v1/branch-rc-spa/crossasset_vol_carry_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T215311-codex-board-b-crossasset-vol-carry-v1/branch-rc-spa/crossasset_vol_carry_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T215311-codex-board-b-crossasset-vol-carry-v1/branch-rc-spa/crossasset_vol_carry_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T215311-codex-board-b-crossasset-vol-carry-v1/branch-rc-spa/crossasset_vol_carry_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T215311-codex-board-b-crossasset-vol-carry-v1/branch-rc-spa/crossasset_vol_carry_panel_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T215311-codex-board-b-crossasset-vol-carry-v1/ict-engine-fail-closed/crossasset_vol_carry_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T215311-codex-board-b-crossasset-vol-carry-v1/checks/crossasset_vol_carry_v1_assertions.out`

## Next

- B2R-repeat: keep the 205047 scoped Manipulation component, but repair Bull/Bear/Sideways/Crisis with a different root family or panel; do not relax RC-SPA.
