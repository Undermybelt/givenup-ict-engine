# Session Liquidity Intraday RC-SPA v1

Run id: `20260511T213155+0800-codex-board-b-session-liquidity-intraday-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `70.5092`
- Price-root paths passed: `0/4`
- Scoped Manipulation component pass consumed: `True`
- Variant rows: `19959`
- Selected rows: `2580`
- Selected root counts: `{'Bull': 1056, 'Bear': 255, 'Sideways': 1108, 'Crisis': 161, 'Manipulation(scoped)': 13535}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Bear=fail:reject_fold_trade_depth|reject_cost_fragile; Sideways=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60

## Panel / Variant Summary

| Market | TF | Variant | Trades | Mean | Win Rate | Net R |
|---|---:|---|---:|---:|---:|---:|
| NQ/USD | 15m | `london_breakout_follow` | 1896 | -0.000599 | 0.3982 | -1.135503 |
| NQ/USD | 15m | `ny_open_pullback_reclaim` | 318 | -0.000196 | 0.4403 | -0.062400 |
| NQ/USD | 15m | `late_session_momentum` | 1455 | -0.000875 | 0.2502 | -1.273463 |
| NQ/USD | 15m | `ny_open_breakdown_short` | 453 | -0.000282 | 0.4857 | -0.127670 |
| NQ/USD | 15m | `failed_reclaim_short` | 119 | -0.000342 | 0.4622 | -0.040716 |
| NQ/USD | 15m | `liquidity_drain_short` | 1814 | -0.000495 | 0.4322 | -0.898602 |
| NQ/USD | 15m | `asia_range_reversion` | 330 | -0.000814 | 0.3576 | -0.268541 |
| NQ/USD | 15m | `midday_liquidity_reversion` | 1278 | -0.001498 | 0.3435 | -1.914981 |
| NQ/USD | 15m | `range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| NQ/USD | 15m | `crisis_session_tail_short` | 208 | -0.000624 | 0.4663 | -0.129756 |
| NQ/USD | 15m | `crisis_panic_reversal` | 84 | 0.000522 | 0.4405 | 0.043809 |
| NQ/USD | 15m | `crisis_late_short` | 41 | -0.000758 | 0.4146 | -0.031093 |
| NQ/USD | 1h | `london_breakout_follow` | 103 | 0.000661 | 0.4951 | 0.068054 |
| NQ/USD | 1h | `ny_open_pullback_reclaim` | 329 | -0.000365 | 0.5046 | -0.120165 |
| NQ/USD | 1h | `late_session_momentum` | 1334 | -0.000600 | 0.3201 | -0.799919 |
| NQ/USD | 1h | `ny_open_breakdown_short` | 338 | 0.001248 | 0.5296 | 0.421744 |
| NQ/USD | 1h | `failed_reclaim_short` | 49 | 0.001328 | 0.5918 | 0.065057 |
| NQ/USD | 1h | `liquidity_drain_short` | 816 | -0.000048 | 0.4718 | -0.039370 |
| NQ/USD | 1h | `asia_range_reversion` | 65 | -0.001366 | 0.3385 | -0.088811 |
| NQ/USD | 1h | `midday_liquidity_reversion` | 606 | -0.001460 | 0.3861 | -0.884873 |
| NQ/USD | 1h | `range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| NQ/USD | 1h | `crisis_session_tail_short` | 90 | -0.004220 | 0.4000 | -0.379776 |
| NQ/USD | 1h | `crisis_panic_reversal` | 30 | 0.002968 | 0.5333 | 0.089030 |
| NQ/USD | 1h | `crisis_late_short` | 31 | -0.003109 | 0.4516 | -0.096380 |
| NQ/USD | 4h | `london_breakout_follow` | 1106 | -0.000000 | 0.5325 | -0.000477 |
| NQ/USD | 4h | `ny_open_pullback_reclaim` | 75 | -0.000508 | 0.4533 | -0.038135 |
| NQ/USD | 4h | `late_session_momentum` | 0 | 0.000000 | 0.0000 | 0.000000 |
| NQ/USD | 4h | `ny_open_breakdown_short` | 230 | -0.000667 | 0.4304 | -0.153330 |
| NQ/USD | 4h | `failed_reclaim_short` | 21 | 0.000068 | 0.4286 | 0.001438 |
| NQ/USD | 4h | `liquidity_drain_short` | 399 | 0.001088 | 0.5238 | 0.434071 |
| NQ/USD | 4h | `asia_range_reversion` | 15 | -0.001562 | 0.4000 | -0.023433 |
| NQ/USD | 4h | `midday_liquidity_reversion` | 49 | -0.002954 | 0.3265 | -0.144742 |
| NQ/USD | 4h | `range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| NQ/USD | 4h | `crisis_session_tail_short` | 38 | -0.008269 | 0.3947 | -0.314207 |
| NQ/USD | 4h | `crisis_panic_reversal` | 6 | -0.001383 | 0.5000 | -0.008299 |
| NQ/USD | 4h | `crisis_late_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 15m | `london_breakout_follow` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 15m | `ny_open_pullback_reclaim` | 35 | -0.000641 | 0.4286 | -0.022424 |
| SPY/USD | 15m | `late_session_momentum` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 15m | `ny_open_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 15m | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 15m | `liquidity_drain_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 15m | `asia_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 15m | `midday_liquidity_reversion` | 37 | 0.000158 | 0.5135 | 0.005855 |
| SPY/USD | 15m | `range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 15m | `crisis_session_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 15m | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 15m | `crisis_late_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1h | `london_breakout_follow` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1h | `ny_open_pullback_reclaim` | 16 | -0.002098 | 0.4375 | -0.033567 |
| SPY/USD | 1h | `late_session_momentum` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1h | `ny_open_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1h | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1h | `liquidity_drain_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1h | `asia_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1h | `midday_liquidity_reversion` | 15 | -0.000965 | 0.4667 | -0.014476 |
| SPY/USD | 1h | `range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1h | `crisis_session_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1h | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1h | `crisis_late_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `london_breakout_follow` | 6 | -0.001648 | 0.5000 | -0.009889 |
| SPY/USD | 4h | `ny_open_pullback_reclaim` | 6 | 0.007360 | 0.8333 | 0.044157 |
| SPY/USD | 4h | `late_session_momentum` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `ny_open_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `liquidity_drain_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `asia_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `midday_liquidity_reversion` | 3 | 0.000979 | 0.6667 | 0.002938 |
| SPY/USD | 4h | `range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `crisis_session_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 4h | `crisis_late_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 15m | `london_breakout_follow` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 15m | `ny_open_pullback_reclaim` | 25 | -0.000904 | 0.4800 | -0.022597 |
| IWM/USD | 15m | `late_session_momentum` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 15m | `ny_open_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 15m | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 15m | `liquidity_drain_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 15m | `asia_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 15m | `midday_liquidity_reversion` | 32 | -0.003001 | 0.4062 | -0.096035 |
| IWM/USD | 15m | `range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 15m | `crisis_session_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 15m | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 15m | `crisis_late_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 1h | `london_breakout_follow` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 1h | `ny_open_pullback_reclaim` | 8 | -0.001896 | 0.5000 | -0.015166 |
| IWM/USD | 1h | `late_session_momentum` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 1h | `ny_open_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 1h | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 1h | `liquidity_drain_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 1h | `asia_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 1h | `midday_liquidity_reversion` | 15 | -0.002564 | 0.4000 | -0.038461 |
| IWM/USD | 1h | `range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 1h | `crisis_session_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 1h | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 1h | `crisis_late_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 15m | `london_breakout_follow` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 15m | `ny_open_pullback_reclaim` | 36 | -0.001588 | 0.2222 | -0.057182 |
| DIA/USD | 15m | `late_session_momentum` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 15m | `ny_open_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 15m | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 15m | `liquidity_drain_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 15m | `asia_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 15m | `midday_liquidity_reversion` | 38 | 0.000434 | 0.5789 | 0.016497 |
| DIA/USD | 15m | `range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 15m | `crisis_session_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 15m | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 15m | `crisis_late_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 1h | `london_breakout_follow` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 1h | `ny_open_pullback_reclaim` | 14 | 0.000906 | 0.5714 | 0.012679 |
| DIA/USD | 1h | `late_session_momentum` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 1h | `ny_open_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 1h | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 1h | `liquidity_drain_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 1h | `asia_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 1h | `midday_liquidity_reversion` | 13 | 0.001745 | 0.6154 | 0.022684 |
| DIA/USD | 1h | `range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 1h | `crisis_session_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 1h | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 1h | `crisis_late_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 15m | `london_breakout_follow` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 15m | `ny_open_pullback_reclaim` | 17 | -0.001595 | 0.5294 | -0.027119 |
| GLD/USD | 15m | `late_session_momentum` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 15m | `ny_open_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 15m | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 15m | `liquidity_drain_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 15m | `asia_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 15m | `midday_liquidity_reversion` | 33 | 0.000036 | 0.5455 | 0.001201 |
| GLD/USD | 15m | `range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 15m | `crisis_session_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 15m | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 15m | `crisis_late_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 1h | `london_breakout_follow` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 1h | `ny_open_pullback_reclaim` | 5 | 0.005079 | 0.6000 | 0.025394 |
| GLD/USD | 1h | `late_session_momentum` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 1h | `ny_open_breakdown_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 1h | `failed_reclaim_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 1h | `liquidity_drain_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 1h | `asia_range_reversion` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 1h | `midday_liquidity_reversion` | 6 | -0.002539 | 0.5000 | -0.015232 |
| GLD/USD | 1h | `range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 1h | `crisis_session_tail_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 1h | `crisis_panic_reversal` | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 1h | `crisis_late_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1h | `london_breakout_follow` | 338 | -0.002145 | 0.4438 | -0.725069 |
| BTC/USDT | 1h | `ny_open_pullback_reclaim` | 74 | -0.000604 | 0.4730 | -0.044726 |
| BTC/USDT | 1h | `late_session_momentum` | 605 | -0.002021 | 0.3521 | -1.222849 |
| BTC/USDT | 1h | `ny_open_breakdown_short` | 176 | -0.001022 | 0.4432 | -0.179943 |
| BTC/USDT | 1h | `failed_reclaim_short` | 26 | 0.004324 | 0.5769 | 0.112416 |
| BTC/USDT | 1h | `liquidity_drain_short` | 545 | -0.000833 | 0.4018 | -0.453902 |
| BTC/USDT | 1h | `asia_range_reversion` | 274 | -0.001683 | 0.4197 | -0.461117 |
| BTC/USDT | 1h | `midday_liquidity_reversion` | 132 | -0.000798 | 0.4470 | -0.105351 |
| BTC/USDT | 1h | `range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 1h | `crisis_session_tail_short` | 36 | 0.000744 | 0.3889 | 0.026792 |
| BTC/USDT | 1h | `crisis_panic_reversal` | 12 | -0.005895 | 0.2500 | -0.070738 |
| BTC/USDT | 1h | `crisis_late_short` | 17 | -0.000921 | 0.2353 | -0.015652 |
| BTC/USDT | 4h | `london_breakout_follow` | 277 | -0.001286 | 0.4296 | -0.356342 |
| BTC/USDT | 4h | `ny_open_pullback_reclaim` | 21 | 0.000130 | 0.4286 | 0.002737 |
| BTC/USDT | 4h | `late_session_momentum` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 4h | `ny_open_breakdown_short` | 80 | 0.003767 | 0.5250 | 0.301384 |
| BTC/USDT | 4h | `failed_reclaim_short` | 7 | 0.007777 | 0.7143 | 0.054439 |
| BTC/USDT | 4h | `liquidity_drain_short` | 213 | 0.000435 | 0.4507 | 0.092651 |
| BTC/USDT | 4h | `asia_range_reversion` | 88 | -0.002460 | 0.4318 | -0.216471 |
| BTC/USDT | 4h | `midday_liquidity_reversion` | 25 | -0.010708 | 0.2400 | -0.267693 |
| BTC/USDT | 4h | `range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| BTC/USDT | 4h | `crisis_session_tail_short` | 12 | 0.003361 | 0.5833 | 0.040336 |
| BTC/USDT | 4h | `crisis_panic_reversal` | 5 | 0.011479 | 0.4000 | 0.057397 |
| BTC/USDT | 4h | `crisis_late_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ETH/USDT | 1h | `london_breakout_follow` | 363 | 0.000364 | 0.4766 | 0.132265 |
| ETH/USDT | 1h | `ny_open_pullback_reclaim` | 58 | 0.000699 | 0.4483 | 0.040538 |
| ETH/USDT | 1h | `late_session_momentum` | 570 | -0.001489 | 0.4140 | -0.848887 |
| ETH/USDT | 1h | `ny_open_breakdown_short` | 178 | 0.000207 | 0.4157 | 0.036927 |
| ETH/USDT | 1h | `failed_reclaim_short` | 21 | 0.006052 | 0.5714 | 0.127089 |
| ETH/USDT | 1h | `liquidity_drain_short` | 556 | 0.000627 | 0.4371 | 0.348367 |
| ETH/USDT | 1h | `asia_range_reversion` | 248 | -0.003638 | 0.4194 | -0.902165 |
| ETH/USDT | 1h | `midday_liquidity_reversion` | 112 | -0.007030 | 0.4107 | -0.787350 |
| ETH/USDT | 1h | `range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ETH/USDT | 1h | `crisis_session_tail_short` | 34 | 0.001487 | 0.5588 | 0.050566 |
| ETH/USDT | 1h | `crisis_panic_reversal` | 16 | -0.003287 | 0.4375 | -0.052591 |
| ETH/USDT | 1h | `crisis_late_short` | 20 | -0.005282 | 0.3000 | -0.105632 |
| ETH/USDT | 4h | `london_breakout_follow` | 280 | 0.004269 | 0.4929 | 1.195258 |
| ETH/USDT | 4h | `ny_open_pullback_reclaim` | 19 | 0.005614 | 0.6316 | 0.106671 |
| ETH/USDT | 4h | `late_session_momentum` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ETH/USDT | 4h | `ny_open_breakdown_short` | 71 | 0.006823 | 0.5352 | 0.484464 |
| ETH/USDT | 4h | `failed_reclaim_short` | 12 | 0.018633 | 0.7500 | 0.223595 |
| ETH/USDT | 4h | `liquidity_drain_short` | 217 | -0.000492 | 0.4700 | -0.106686 |
| ETH/USDT | 4h | `asia_range_reversion` | 88 | -0.006043 | 0.4205 | -0.531741 |
| ETH/USDT | 4h | `midday_liquidity_reversion` | 22 | -0.006571 | 0.3636 | -0.144561 |
| ETH/USDT | 4h | `range_breakout_failure` | 0 | 0.000000 | 0.0000 | 0.000000 |
| ETH/USDT | 4h | `crisis_session_tail_short` | 17 | -0.006367 | 0.4706 | -0.108244 |
| ETH/USDT | 4h | `crisis_panic_reversal` | 8 | 0.012517 | 0.5000 | 0.100137 |
| ETH/USDT | 4h | `crisis_late_short` | 0 | 0.000000 | 0.0000 | 0.000000 |

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `ny_open_pullback_reclaim` | 1056 | 16 | 10 | 0.5625 | -0.000603 | 0.062 | -0.8862 | 30.9375 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Bear | `failed_reclaim_short` | 255 | 13 | 2 | 0.8462 | 0.000584 | 0.091 | 2.2620 | 70.5092 | `fail:reject_fold_trade_depth|reject_cost_fragile` |
| Sideways | `asia_range_reversion` | 1108 | 16 | 2 | 0.1875 | -0.003043 | 1.000 | -4.7902 | 17.8125 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | `crisis_panic_reversal` | 161 | 5 | 5 | 0.6000 | -0.001031 | 0.200 | 0.7691 | 46.1972 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60` |
| Manipulation(scoped) | `short_tp120_sl060_h72` | 13535 | 12 | 1127 | 0.7500 | 0.005609 | 0.000 | 1.0000 | 100.0000 | `pass` |

## Inputs

- Local Auto-Quant feathers: `/Users/thrill3r/Auto-Quant/user_data/data`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^IXIC`
- Scoped Manipulation component: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2.md`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T213155-codex-board-b-session-liquidity-intraday-v1/branch-rc-spa/session_liquidity_intraday_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T213155-codex-board-b-session-liquidity-intraday-v1/branch-rc-spa/session_liquidity_intraday_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T213155-codex-board-b-session-liquidity-intraday-v1/branch-rc-spa/session_liquidity_intraday_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T213155-codex-board-b-session-liquidity-intraday-v1/branch-rc-spa/session_liquidity_intraday_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T213155-codex-board-b-session-liquidity-intraday-v1/branch-rc-spa/session_liquidity_intraday_panel_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T213155-codex-board-b-session-liquidity-intraday-v1/ict-engine-fail-closed/session_liquidity_intraday_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T213155-codex-board-b-session-liquidity-intraday-v1/checks/session_liquidity_intraday_v1_assertions.out`

## Next

- B2R-repeat: keep the 205047 scoped Manipulation component, but repair Bull/Bear/Sideways/Crisis with a different root family or panel; do not relax RC-SPA.
