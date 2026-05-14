# Crypto Liquidity Root Family RC-SPA v2

Run id: `20260511T210508+0800-codex-board-b-crypto-liquidity-root-family-v2`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `72.5000`
- Price-root paths passed: `0/4`
- Scoped Manipulation component pass consumed: `True`
- Variant rows: `33059`
- Selected rows: `11387`
- Selected root counts: `{'Bull': 6662, 'Bear': 3338, 'Sideways': 1011, 'Crisis': 376, 'Manipulation(scoped)': 13535}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_fold_inconsistency|reject_overfit_risk; Bear=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_tail_risk|reject_rc_spa_below_60; Sideways=fail:reject_fold_inconsistency|reject_cost_fragile|reject_rc_spa_below_60; Crisis=fail:reject_insufficient_test_folds|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_tail_risk|reject_no_regime_specificity|reject_rc_spa_below_60

## Panel / Variant Summary

| Market | TF | Variant | Trades | Mean | Win Rate | Net R |
|---|---:|---|---:|---:|---:|---:|
| BTC/USDT | 1h | `liq_expansion_momentum_fast` | 855 | -0.001222 | 0.4140 | -1.045001 |
| BTC/USDT | 1h | `liq_expansion_momentum_slow` | 677 | -0.000779 | 0.4210 | -0.527338 |
| BTC/USDT | 1h | `bull_pullback_reclaim` | 82 | -0.003597 | 0.3780 | -0.294975 |
| BTC/USDT | 1h | `liq_drain_breakdown` | 435 | -0.000855 | 0.4345 | -0.371904 |
| BTC/USDT | 1h | `relief_fade_short` | 36 | -0.001102 | 0.3611 | -0.039689 |
| BTC/USDT | 1h | `range_liq_reversion` | 705 | -0.001640 | 0.4511 | -1.156270 |
| BTC/USDT | 1h | `squeeze_breakout` | 213 | -0.003178 | 0.4178 | -0.676974 |
| BTC/USDT | 1h | `panic_rebound` | 99 | -0.005815 | 0.3939 | -0.575694 |
| BTC/USDT | 1h | `liq_cliff_short` | 46 | -0.005607 | 0.3478 | -0.257932 |
| BTC/USDT | 1h | `low_impact_carry` | 1565 | -0.001435 | 0.4179 | -2.245541 |
| BTC/USDT | 4h | `liq_expansion_momentum_fast` | 311 | -0.000065 | 0.4437 | -0.020261 |
| BTC/USDT | 4h | `liq_expansion_momentum_slow` | 265 | 0.000397 | 0.4528 | 0.105281 |
| BTC/USDT | 4h | `bull_pullback_reclaim` | 27 | -0.011141 | 0.2963 | -0.300798 |
| BTC/USDT | 4h | `liq_drain_breakdown` | 176 | 0.000105 | 0.4716 | 0.018564 |
| BTC/USDT | 4h | `relief_fade_short` | 9 | -0.001290 | 0.7778 | -0.011606 |
| BTC/USDT | 4h | `range_liq_reversion` | 159 | -0.003438 | 0.4403 | -0.546663 |
| BTC/USDT | 4h | `squeeze_breakout` | 38 | 0.002700 | 0.5000 | 0.102599 |
| BTC/USDT | 4h | `panic_rebound` | 20 | -0.006010 | 0.3500 | -0.120195 |
| BTC/USDT | 4h | `liq_cliff_short` | 18 | 0.000944 | 0.5000 | 0.016994 |
| BTC/USDT | 4h | `low_impact_carry` | 532 | -0.001843 | 0.4323 | -0.980437 |
| BTC/USDT | 1d | `liq_expansion_momentum_fast` | 51 | 0.001563 | 0.4510 | 0.079701 |
| BTC/USDT | 1d | `liq_expansion_momentum_slow` | 49 | 0.004931 | 0.4898 | 0.241611 |
| BTC/USDT | 1d | `bull_pullback_reclaim` | 4 | -0.053938 | 0.2500 | -0.215752 |
| BTC/USDT | 1d | `liq_drain_breakdown` | 40 | 0.007877 | 0.5750 | 0.315094 |
| BTC/USDT | 1d | `relief_fade_short` | 6 | 0.046270 | 0.6667 | 0.277617 |
| BTC/USDT | 1d | `range_liq_reversion` | 27 | -0.000442 | 0.4815 | -0.011947 |
| BTC/USDT | 1d | `squeeze_breakout` | 5 | 0.017822 | 0.6000 | 0.089112 |
| BTC/USDT | 1d | `panic_rebound` | 9 | 0.001820 | 0.5556 | 0.016383 |
| BTC/USDT | 1d | `liq_cliff_short` | 4 | -0.014520 | 0.2500 | -0.058082 |
| BTC/USDT | 1d | `low_impact_carry` | 98 | 0.006695 | 0.4898 | 0.656086 |
| ETH/USDT | 1h | `liq_expansion_momentum_fast` | 921 | 0.000178 | 0.4528 | 0.164271 |
| ETH/USDT | 1h | `liq_expansion_momentum_slow` | 720 | 0.000350 | 0.4667 | 0.252333 |
| ETH/USDT | 1h | `bull_pullback_reclaim` | 82 | -0.001721 | 0.4268 | -0.141125 |
| ETH/USDT | 1h | `liq_drain_breakdown` | 444 | 0.000415 | 0.4595 | 0.184374 |
| ETH/USDT | 1h | `relief_fade_short` | 23 | -0.002794 | 0.3913 | -0.064251 |
| ETH/USDT | 1h | `range_liq_reversion` | 638 | -0.003228 | 0.4404 | -2.059516 |
| ETH/USDT | 1h | `squeeze_breakout` | 168 | -0.000167 | 0.3988 | -0.028053 |
| ETH/USDT | 1h | `panic_rebound` | 95 | -0.006229 | 0.4421 | -0.591736 |
| ETH/USDT | 1h | `liq_cliff_short` | 46 | -0.000305 | 0.4783 | -0.014048 |
| ETH/USDT | 1h | `low_impact_carry` | 1537 | -0.000213 | 0.4548 | -0.326662 |
| ETH/USDT | 4h | `liq_expansion_momentum_fast` | 327 | 0.002376 | 0.4740 | 0.777066 |
| ETH/USDT | 4h | `liq_expansion_momentum_slow` | 285 | 0.002323 | 0.4807 | 0.661920 |
| ETH/USDT | 4h | `bull_pullback_reclaim` | 29 | 0.010240 | 0.6552 | 0.296962 |
| ETH/USDT | 4h | `liq_drain_breakdown` | 173 | 0.002448 | 0.5029 | 0.423555 |
| ETH/USDT | 4h | `relief_fade_short` | 8 | 0.023352 | 0.5000 | 0.186814 |
| ETH/USDT | 4h | `range_liq_reversion` | 156 | -0.006933 | 0.3974 | -1.081543 |
| ETH/USDT | 4h | `squeeze_breakout` | 37 | 0.008589 | 0.5405 | 0.317807 |
| ETH/USDT | 4h | `panic_rebound` | 30 | -0.003430 | 0.4667 | -0.102892 |
| ETH/USDT | 4h | `liq_cliff_short` | 22 | 0.000222 | 0.6364 | 0.004884 |
| ETH/USDT | 4h | `low_impact_carry` | 552 | -0.000236 | 0.4493 | -0.130176 |
| ETH/USDT | 1d | `liq_expansion_momentum_fast` | 54 | 0.015557 | 0.4815 | 0.840094 |
| ETH/USDT | 1d | `liq_expansion_momentum_slow` | 48 | 0.015868 | 0.4792 | 0.761647 |
| ETH/USDT | 1d | `bull_pullback_reclaim` | 4 | -0.001782 | 0.5000 | -0.007127 |
| ETH/USDT | 1d | `liq_drain_breakdown` | 41 | 0.007789 | 0.4878 | 0.319332 |
| ETH/USDT | 1d | `relief_fade_short` | 5 | -0.038779 | 0.6000 | -0.193896 |
| ETH/USDT | 1d | `range_liq_reversion` | 34 | 0.007600 | 0.5588 | 0.258407 |
| ETH/USDT | 1d | `squeeze_breakout` | 7 | 0.025235 | 0.5714 | 0.176648 |
| ETH/USDT | 1d | `panic_rebound` | 9 | -0.015334 | 0.4444 | -0.138009 |
| ETH/USDT | 1d | `liq_cliff_short` | 4 | -0.007243 | 0.2500 | -0.028970 |
| ETH/USDT | 1d | `low_impact_carry` | 103 | 0.009648 | 0.4660 | 0.993756 |
| BNB/USDT | 1h | `liq_expansion_momentum_fast` | 950 | 0.000718 | 0.4537 | 0.682515 |
| BNB/USDT | 1h | `liq_expansion_momentum_slow` | 745 | 0.002304 | 0.4456 | 1.716374 |
| BNB/USDT | 1h | `bull_pullback_reclaim` | 78 | -0.004453 | 0.4231 | -0.347343 |
| BNB/USDT | 1h | `liq_drain_breakdown` | 440 | -0.000936 | 0.4545 | -0.412025 |
| BNB/USDT | 1h | `relief_fade_short` | 28 | 0.002839 | 0.5000 | 0.079483 |
| BNB/USDT | 1h | `range_liq_reversion` | 714 | -0.003252 | 0.4384 | -2.321665 |
| BNB/USDT | 1h | `squeeze_breakout` | 201 | -0.001222 | 0.3980 | -0.245588 |
| BNB/USDT | 1h | `panic_rebound` | 86 | -0.003239 | 0.4535 | -0.278572 |
| BNB/USDT | 1h | `liq_cliff_short` | 53 | -0.002629 | 0.3962 | -0.139336 |
| BNB/USDT | 1h | `low_impact_carry` | 1628 | 0.000183 | 0.4478 | 0.298332 |
| BNB/USDT | 4h | `liq_expansion_momentum_fast` | 327 | 0.005276 | 0.4771 | 1.725398 |
| BNB/USDT | 4h | `liq_expansion_momentum_slow` | 295 | 0.005058 | 0.4780 | 1.492199 |
| BNB/USDT | 4h | `bull_pullback_reclaim` | 20 | 0.000433 | 0.5000 | 0.008656 |
| BNB/USDT | 4h | `liq_drain_breakdown` | 167 | -0.000457 | 0.4671 | -0.076248 |
| BNB/USDT | 4h | `relief_fade_short` | 6 | 0.020866 | 0.6667 | 0.125195 |
| BNB/USDT | 4h | `range_liq_reversion` | 175 | -0.002620 | 0.4514 | -0.458536 |
| BNB/USDT | 4h | `squeeze_breakout` | 32 | 0.003357 | 0.5938 | 0.107422 |
| BNB/USDT | 4h | `panic_rebound` | 20 | -0.009433 | 0.5500 | -0.188665 |
| BNB/USDT | 4h | `liq_cliff_short` | 24 | -0.007237 | 0.4583 | -0.173676 |
| BNB/USDT | 4h | `low_impact_carry` | 602 | 0.002019 | 0.4734 | 1.215718 |
| BNB/USDT | 1d | `liq_expansion_momentum_fast` | 70 | 0.043780 | 0.5714 | 3.064623 |
| BNB/USDT | 1d | `liq_expansion_momentum_slow` | 56 | 0.078928 | 0.5357 | 4.419952 |
| BNB/USDT | 1d | `bull_pullback_reclaim` | 4 | -0.011365 | 0.2500 | -0.045460 |
| BNB/USDT | 1d | `liq_drain_breakdown` | 36 | 0.008566 | 0.5556 | 0.308359 |
| BNB/USDT | 1d | `relief_fade_short` | 4 | 0.008280 | 0.5000 | 0.033121 |
| BNB/USDT | 1d | `range_liq_reversion` | 36 | -0.014761 | 0.4444 | -0.531400 |
| BNB/USDT | 1d | `squeeze_breakout` | 4 | 0.107799 | 0.7500 | 0.431196 |
| BNB/USDT | 1d | `panic_rebound` | 6 | -0.018106 | 0.5000 | -0.108635 |
| BNB/USDT | 1d | `liq_cliff_short` | 6 | 0.004394 | 0.3333 | 0.026363 |
| BNB/USDT | 1d | `low_impact_carry` | 112 | 0.015708 | 0.5089 | 1.759277 |
| SOL/USDT | 1h | `liq_expansion_momentum_fast` | 979 | 0.001322 | 0.4688 | 1.293892 |
| SOL/USDT | 1h | `liq_expansion_momentum_slow` | 741 | 0.002653 | 0.4696 | 1.965764 |
| SOL/USDT | 1h | `bull_pullback_reclaim` | 75 | -0.002810 | 0.4533 | -0.210751 |
| SOL/USDT | 1h | `liq_drain_breakdown` | 474 | 0.000189 | 0.4852 | 0.089640 |
| SOL/USDT | 1h | `relief_fade_short` | 37 | -0.003335 | 0.3243 | -0.123406 |
| SOL/USDT | 1h | `range_liq_reversion` | 566 | -0.003185 | 0.4523 | -1.802963 |
| SOL/USDT | 1h | `squeeze_breakout` | 126 | 0.000073 | 0.4762 | 0.009231 |
| SOL/USDT | 1h | `panic_rebound` | 88 | -0.010262 | 0.3864 | -0.903015 |
| SOL/USDT | 1h | `liq_cliff_short` | 51 | -0.004792 | 0.5490 | -0.244375 |
| SOL/USDT | 1h | `low_impact_carry` | 1453 | 0.001177 | 0.4866 | 1.709785 |
| SOL/USDT | 4h | `liq_expansion_momentum_fast` | 350 | 0.010663 | 0.5400 | 3.732114 |
| SOL/USDT | 4h | `liq_expansion_momentum_slow` | 288 | 0.015546 | 0.5347 | 4.477240 |
| SOL/USDT | 4h | `bull_pullback_reclaim` | 26 | 0.009806 | 0.5385 | 0.254960 |
| SOL/USDT | 4h | `liq_drain_breakdown` | 171 | 0.008737 | 0.5556 | 1.493983 |
| SOL/USDT | 4h | `relief_fade_short` | 14 | 0.015569 | 0.6429 | 0.217961 |
| SOL/USDT | 4h | `range_liq_reversion` | 143 | -0.010396 | 0.3776 | -1.486698 |
| SOL/USDT | 4h | `squeeze_breakout` | 20 | 0.009954 | 0.7000 | 0.199084 |
| SOL/USDT | 4h | `panic_rebound` | 28 | -0.023458 | 0.3929 | -0.656829 |
| SOL/USDT | 4h | `liq_cliff_short` | 25 | 0.005283 | 0.4000 | 0.132081 |
| SOL/USDT | 4h | `low_impact_carry` | 533 | 0.002757 | 0.4878 | 1.469577 |
| SOL/USDT | 1d | `liq_expansion_momentum_fast` | 65 | 0.056546 | 0.6462 | 3.675497 |
| SOL/USDT | 1d | `liq_expansion_momentum_slow` | 54 | 0.074389 | 0.5926 | 4.016996 |
| SOL/USDT | 1d | `bull_pullback_reclaim` | 2 | 0.049333 | 0.5000 | 0.098665 |
| SOL/USDT | 1d | `liq_drain_breakdown` | 41 | 0.024724 | 0.5610 | 1.013687 |
| SOL/USDT | 1d | `relief_fade_short` | 0 | 0.000000 | 0.0000 | 0.000000 |
| SOL/USDT | 1d | `range_liq_reversion` | 30 | -0.007258 | 0.4667 | -0.217749 |
| SOL/USDT | 1d | `squeeze_breakout` | 1 | 0.297531 | 1.0000 | 0.297531 |
| SOL/USDT | 1d | `panic_rebound` | 7 | 0.020575 | 0.5714 | 0.144027 |
| SOL/USDT | 1d | `liq_cliff_short` | 5 | 0.032155 | 0.6000 | 0.160774 |
| SOL/USDT | 1d | `low_impact_carry` | 101 | 0.037033 | 0.5149 | 3.740320 |
| AVAX/USDT | 1h | `liq_expansion_momentum_fast` | 989 | 0.000393 | 0.4510 | 0.388915 |
| AVAX/USDT | 1h | `liq_expansion_momentum_slow` | 729 | 0.000185 | 0.4527 | 0.135137 |
| AVAX/USDT | 1h | `bull_pullback_reclaim` | 51 | -0.006643 | 0.4510 | -0.338798 |
| AVAX/USDT | 1h | `liq_drain_breakdown` | 482 | -0.000092 | 0.4896 | -0.044118 |
| AVAX/USDT | 1h | `relief_fade_short` | 28 | -0.001464 | 0.3929 | -0.041003 |
| AVAX/USDT | 1h | `range_liq_reversion` | 538 | -0.001534 | 0.4480 | -0.825031 |
| AVAX/USDT | 1h | `squeeze_breakout` | 131 | 0.002062 | 0.4809 | 0.270064 |
| AVAX/USDT | 1h | `panic_rebound` | 94 | -0.012419 | 0.3723 | -1.167360 |
| AVAX/USDT | 1h | `liq_cliff_short` | 47 | 0.001840 | 0.4894 | 0.086495 |
| AVAX/USDT | 1h | `low_impact_carry` | 1502 | 0.000308 | 0.4547 | 0.462338 |
| AVAX/USDT | 4h | `liq_expansion_momentum_fast` | 346 | 0.006744 | 0.4884 | 2.333390 |
| AVAX/USDT | 4h | `liq_expansion_momentum_slow` | 290 | 0.008353 | 0.4724 | 2.422461 |
| AVAX/USDT | 4h | `bull_pullback_reclaim` | 21 | 0.003269 | 0.3333 | 0.068654 |
| AVAX/USDT | 4h | `liq_drain_breakdown` | 178 | 0.000403 | 0.4551 | 0.071720 |
| AVAX/USDT | 4h | `relief_fade_short` | 10 | -0.019724 | 0.3000 | -0.197242 |
| AVAX/USDT | 4h | `range_liq_reversion` | 141 | -0.004537 | 0.4681 | -0.639671 |
| AVAX/USDT | 4h | `squeeze_breakout` | 26 | 0.019979 | 0.6154 | 0.519452 |
| AVAX/USDT | 4h | `panic_rebound` | 26 | -0.030042 | 0.4615 | -0.781102 |
| AVAX/USDT | 4h | `liq_cliff_short` | 21 | -0.013585 | 0.4762 | -0.285280 |
| AVAX/USDT | 4h | `low_impact_carry` | 533 | 0.002170 | 0.4578 | 1.156549 |
| AVAX/USDT | 1d | `liq_expansion_momentum_fast` | 67 | 0.066556 | 0.5970 | 4.459271 |
| AVAX/USDT | 1d | `liq_expansion_momentum_slow` | 49 | 0.112165 | 0.5918 | 5.496088 |
| AVAX/USDT | 1d | `bull_pullback_reclaim` | 2 | 0.136074 | 1.0000 | 0.272147 |
| AVAX/USDT | 1d | `liq_drain_breakdown` | 40 | 0.023342 | 0.6000 | 0.933678 |
| AVAX/USDT | 1d | `relief_fade_short` | 4 | -0.052415 | 0.2500 | -0.209661 |
| AVAX/USDT | 1d | `range_liq_reversion` | 29 | -0.019413 | 0.5172 | -0.562963 |
| AVAX/USDT | 1d | `squeeze_breakout` | 2 | 0.188163 | 1.0000 | 0.376325 |
| AVAX/USDT | 1d | `panic_rebound` | 7 | -0.064230 | 0.2857 | -0.449611 |
| AVAX/USDT | 1d | `liq_cliff_short` | 4 | 0.021377 | 0.5000 | 0.085507 |
| AVAX/USDT | 1d | `low_impact_carry` | 90 | 0.070358 | 0.6222 | 6.332216 |

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `liq_expansion_momentum_fast` | 6662 | 6 | 97 | 0.5000 | 0.002345 | 0.500 | 5.7474 | 72.5000 | `fail:reject_fold_inconsistency|reject_overfit_risk` |
| Bear | `liq_drain_breakdown` | 3338 | 5 | 141 | 0.4000 | -0.000017 | 0.000 | 1.5512 | 51.0000 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_tail_risk|reject_rc_spa_below_60` |
| Sideways | `squeeze_breakout` | 1011 | 6 | 44 | 0.6667 | 0.000160 | 0.000 | 1.7883 | 58.2082 | `fail:reject_fold_inconsistency|reject_cost_fragile|reject_rc_spa_below_60` |
| Crisis | `liq_cliff_short` | 376 | 2 | 84 | 0.5000 | -0.005197 | 1.000 | -0.8725 | 22.5000 | `fail:reject_insufficient_test_folds|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_tail_risk|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Manipulation(scoped) | `short_tp120_sl060_h72` | 13535 | 12 | 1127 | 0.7500 | 0.005609 | 0.000 | 1.0000 | 100.0000 | `pass` |

## Inputs

- Local Auto-Quant feathers: `/Users/thrill3r/Auto-Quant/user_data/data`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^IXIC`
- Scoped Manipulation component: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2.md`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T210508-codex-board-b-crypto-liquidity-root-family-v2/branch-rc-spa/crypto_liquidity_root_family_rc_spa_report_v2.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T210508-codex-board-b-crypto-liquidity-root-family-v2/branch-rc-spa/crypto_liquidity_root_family_selected_rows_v2.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T210508-codex-board-b-crypto-liquidity-root-family-v2/branch-rc-spa/crypto_liquidity_root_family_variant_rows_v2.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T210508-codex-board-b-crypto-liquidity-root-family-v2/branch-rc-spa/crypto_liquidity_root_family_branch_summary_v2.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T210508-codex-board-b-crypto-liquidity-root-family-v2/branch-rc-spa/crypto_liquidity_root_family_panel_summary_v2.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T210508-codex-board-b-crypto-liquidity-root-family-v2/ict-engine-fail-closed/crypto_liquidity_root_family_fail_closed_summary_v2.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T210508-codex-board-b-crypto-liquidity-root-family-v2/checks/crypto_liquidity_root_family_v2_assertions.out`

## Next

- B2R-repeat: keep the 205047 scoped Manipulation component, but repair Bull/Bear/Sideways/Crisis with a different root family or panel; do not relax RC-SPA.
