# Root Transition Triad RC-SPA v1

Run id: `20260511T195624+0800-codex-board-b-root-branch-rescue-predeclared-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `76.2500`
- Variant rows: `115421`
- Selected rows: `12628`
- Branch paths evaluated: `5`
- Branch paths passed: `1`
- Selected root counts: `{'Bull': 6548, 'Bear': 2458, 'Sideways': 3594, 'Crisis': 28, 'Manipulation(scoped)': 0}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bear=fail:reject_fold_inconsistency|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60; Sideways=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60; Manipulation(scoped)=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60

## Panel / Variant Summary

| Market | TF | Variant | Trades | Mean | Win Rate | Net R |
|---|---:|---|---:|---:|---:|---:|
| NQ/USD | 1h | `bull_trend_slow_anchor` | 3923 | -0.000209 | 0.4978 | -0.818004 |
| NQ/USD | 1h | `bear_breakdown_short_strict` | 6815 | -0.000442 | 0.4533 | -3.012630 |
| NQ/USD | 1h | `bear_relief_reversal_fast` | 7844 | -0.000631 | 0.4271 | -4.948043 |
| NQ/USD | 1h | `sideways_breakout_follow` | 7112 | -0.000198 | 0.4591 | -1.408909 |
| NQ/USD | 1h | `sideways_reversion_control` | 3650 | -0.000737 | 0.4364 | -2.688379 |
| NQ/USD | 1h | `crisis_relief_long_confirmed` | 8076 | -0.000442 | 0.4321 | -3.566359 |
| NQ/USD | 1h | `crisis_tail_short_strict` | 7042 | -0.000486 | 0.4507 | -3.424956 |
| NQ/USD | 1h | `crisis_defensive_rotation` | 5216 | -0.000220 | 0.4781 | -1.146701 |
| NQ/USD | 4h | `bull_trend_slow_anchor` | 1885 | -0.000200 | 0.5125 | -0.376841 |
| NQ/USD | 4h | `bear_breakdown_short_strict` | 2562 | -0.000170 | 0.4961 | -0.434792 |
| NQ/USD | 4h | `bear_relief_reversal_fast` | 2796 | -0.000494 | 0.4886 | -1.382508 |
| NQ/USD | 4h | `sideways_breakout_follow` | 2806 | -0.000053 | 0.5046 | -0.149872 |
| NQ/USD | 4h | `sideways_reversion_control` | 1334 | -0.000446 | 0.4865 | -0.594586 |
| NQ/USD | 4h | `crisis_relief_long_confirmed` | 2892 | -0.000188 | 0.4945 | -0.544253 |
| NQ/USD | 4h | `crisis_tail_short_strict` | 2646 | -0.000059 | 0.5068 | -0.155338 |
| NQ/USD | 4h | `crisis_defensive_rotation` | 2369 | -0.000254 | 0.5082 | -0.602231 |
| NQ/USD | 1d | `bull_trend_slow_anchor` | 373 | 0.002319 | 0.5845 | 0.864838 |
| NQ/USD | 1d | `bear_breakdown_short_strict` | 601 | 0.001774 | 0.5557 | 1.066221 |
| NQ/USD | 1d | `bear_relief_reversal_fast` | 647 | 0.001503 | 0.5595 | 0.972262 |
| NQ/USD | 1d | `sideways_breakout_follow` | 640 | -0.000660 | 0.5312 | -0.422584 |
| NQ/USD | 1d | `sideways_reversion_control` | 284 | -0.000163 | 0.4965 | -0.046211 |
| NQ/USD | 1d | `crisis_relief_long_confirmed` | 677 | 0.000380 | 0.5451 | 0.257007 |
| NQ/USD | 1d | `crisis_tail_short_strict` | 601 | 0.001193 | 0.5491 | 0.716851 |
| NQ/USD | 1d | `crisis_defensive_rotation` | 438 | 0.001985 | 0.5502 | 0.869623 |
| BTC/USDT | 4h | `bull_trend_slow_anchor` | 708 | -0.001359 | 0.4675 | -0.961917 |
| BTC/USDT | 4h | `bear_breakdown_short_strict` | 997 | -0.000678 | 0.4413 | -0.676069 |
| BTC/USDT | 4h | `bear_relief_reversal_fast` | 1000 | -0.000940 | 0.4520 | -0.940214 |
| BTC/USDT | 4h | `sideways_breakout_follow` | 1061 | 0.000101 | 0.4515 | 0.107129 |
| BTC/USDT | 4h | `sideways_reversion_control` | 484 | -0.002528 | 0.4545 | -1.223719 |
| BTC/USDT | 4h | `crisis_relief_long_confirmed` | 1110 | -0.001237 | 0.4423 | -1.372860 |
| BTC/USDT | 4h | `crisis_tail_short_strict` | 1030 | -0.000526 | 0.4563 | -0.542031 |
| BTC/USDT | 4h | `crisis_defensive_rotation` | 928 | -0.001871 | 0.4353 | -1.735900 |
| BTC/USDT | 1d | `bull_trend_slow_anchor` | 118 | 0.009419 | 0.5424 | 1.111390 |
| BTC/USDT | 1d | `bear_breakdown_short_strict` | 191 | 0.001337 | 0.4503 | 0.255372 |
| BTC/USDT | 1d | `bear_relief_reversal_fast` | 186 | 0.004642 | 0.5000 | 0.863349 |
| BTC/USDT | 1d | `sideways_breakout_follow` | 202 | -0.003777 | 0.4257 | -0.762984 |
| BTC/USDT | 1d | `sideways_reversion_control` | 92 | -0.006496 | 0.4565 | -0.597614 |
| BTC/USDT | 1d | `crisis_relief_long_confirmed` | 212 | 0.005633 | 0.5047 | 1.194210 |
| BTC/USDT | 1d | `crisis_tail_short_strict` | 193 | 0.004812 | 0.4456 | 0.928808 |
| BTC/USDT | 1d | `crisis_defensive_rotation` | 145 | 0.004234 | 0.4966 | 0.613901 |
| ETH/USDT | 4h | `bull_trend_slow_anchor` | 726 | -0.000294 | 0.4573 | -0.213766 |
| ETH/USDT | 4h | `bear_breakdown_short_strict` | 1009 | -0.000837 | 0.4797 | -0.844114 |
| ETH/USDT | 4h | `bear_relief_reversal_fast` | 1033 | -0.000006 | 0.4705 | -0.006393 |
| ETH/USDT | 4h | `sideways_breakout_follow` | 1064 | 0.001893 | 0.4765 | 2.014184 |
| ETH/USDT | 4h | `sideways_reversion_control` | 504 | -0.003110 | 0.4762 | -1.567612 |
| ETH/USDT | 4h | `crisis_relief_long_confirmed` | 1130 | -0.000163 | 0.4717 | -0.184600 |
| ETH/USDT | 4h | `crisis_tail_short_strict` | 1031 | -0.000697 | 0.4704 | -0.719075 |
| ETH/USDT | 4h | `crisis_defensive_rotation` | 911 | -0.000346 | 0.4863 | -0.315510 |
| ETH/USDT | 1d | `bull_trend_slow_anchor` | 118 | 0.017529 | 0.5339 | 2.068460 |
| ETH/USDT | 1d | `bear_breakdown_short_strict` | 195 | 0.005991 | 0.5077 | 1.168235 |
| ETH/USDT | 1d | `bear_relief_reversal_fast` | 191 | 0.003204 | 0.4974 | 0.611990 |
| ETH/USDT | 1d | `sideways_breakout_follow` | 208 | 0.004095 | 0.5000 | 0.851746 |
| ETH/USDT | 1d | `sideways_reversion_control` | 95 | -0.008059 | 0.4947 | -0.765633 |
| ETH/USDT | 1d | `crisis_relief_long_confirmed` | 216 | 0.005519 | 0.4861 | 1.192048 |
| ETH/USDT | 1d | `crisis_tail_short_strict` | 198 | 0.008116 | 0.4848 | 1.606998 |
| ETH/USDT | 1d | `crisis_defensive_rotation` | 148 | 0.022193 | 0.5676 | 3.284550 |
| BNB/USDT | 4h | `bull_trend_slow_anchor` | 730 | 0.003020 | 0.4822 | 2.204891 |
| BNB/USDT | 4h | `bear_breakdown_short_strict` | 1032 | 0.001991 | 0.4777 | 2.054345 |
| BNB/USDT | 4h | `bear_relief_reversal_fast` | 1054 | 0.001538 | 0.4772 | 1.621414 |
| BNB/USDT | 4h | `sideways_breakout_follow` | 1093 | 0.002419 | 0.4785 | 2.644466 |
| BNB/USDT | 4h | `sideways_reversion_control` | 482 | -0.001378 | 0.4959 | -0.663966 |
| BNB/USDT | 4h | `crisis_relief_long_confirmed` | 1147 | 0.001582 | 0.4629 | 1.814665 |
| BNB/USDT | 4h | `crisis_tail_short_strict` | 1061 | 0.002558 | 0.4675 | 2.714007 |
| BNB/USDT | 4h | `crisis_defensive_rotation` | 946 | 0.001180 | 0.4810 | 1.116750 |
| SOL/USDT | 4h | `bull_trend_slow_anchor` | 706 | 0.006111 | 0.5127 | 4.314119 |
| SOL/USDT | 4h | `bear_breakdown_short_strict` | 982 | 0.004223 | 0.5112 | 4.146964 |
| SOL/USDT | 4h | `bear_relief_reversal_fast` | 1010 | 0.002700 | 0.4931 | 2.727103 |
| SOL/USDT | 4h | `sideways_breakout_follow` | 1053 | 0.004604 | 0.5109 | 4.848336 |
| SOL/USDT | 4h | `sideways_reversion_control` | 503 | -0.000619 | 0.4831 | -0.311533 |
| SOL/USDT | 4h | `crisis_relief_long_confirmed` | 1115 | 0.002879 | 0.5013 | 3.209799 |
| SOL/USDT | 4h | `crisis_tail_short_strict` | 1010 | 0.005991 | 0.5198 | 6.050830 |
| SOL/USDT | 4h | `crisis_defensive_rotation` | 903 | 0.003749 | 0.4828 | 3.385169 |
| AVAX/USDT | 4h | `bull_trend_slow_anchor` | 674 | 0.004549 | 0.4896 | 3.066344 |
| AVAX/USDT | 4h | `bear_breakdown_short_strict` | 955 | 0.004253 | 0.4817 | 4.061384 |
| AVAX/USDT | 4h | `bear_relief_reversal_fast` | 966 | 0.002801 | 0.4752 | 2.705559 |
| AVAX/USDT | 4h | `sideways_breakout_follow` | 997 | 0.003078 | 0.4945 | 3.068661 |
| AVAX/USDT | 4h | `sideways_reversion_control` | 504 | -0.005035 | 0.4484 | -2.537548 |
| AVAX/USDT | 4h | `crisis_relief_long_confirmed` | 1068 | 0.003776 | 0.4944 | 4.032852 |
| AVAX/USDT | 4h | `crisis_tail_short_strict` | 979 | 0.003002 | 0.4934 | 2.938534 |
| AVAX/USDT | 4h | `crisis_defensive_rotation` | 871 | 0.003534 | 0.4948 | 3.077999 |
| SPY/USD | 1d | `bull_trend_slow_anchor` | 62 | 0.001464 | 0.5484 | 0.090737 |
| SPY/USD | 1d | `bear_breakdown_short_strict` | 100 | 0.001288 | 0.5600 | 0.128775 |
| SPY/USD | 1d | `bear_relief_reversal_fast` | 112 | -0.000078 | 0.5268 | -0.008735 |
| SPY/USD | 1d | `sideways_breakout_follow` | 107 | 0.001917 | 0.5888 | 0.205141 |
| SPY/USD | 1d | `sideways_reversion_control` | 42 | 0.000671 | 0.5238 | 0.028182 |
| SPY/USD | 1d | `crisis_relief_long_confirmed` | 116 | 0.000020 | 0.5259 | 0.002363 |
| SPY/USD | 1d | `crisis_tail_short_strict` | 102 | 0.002021 | 0.5784 | 0.206175 |
| SPY/USD | 1d | `crisis_defensive_rotation` | 74 | 0.004885 | 0.5946 | 0.361527 |
| ES/USD | 1d | `bull_trend_slow_anchor` | 62 | 0.006127 | 0.6452 | 0.379859 |
| ES/USD | 1d | `bear_breakdown_short_strict` | 100 | 0.000520 | 0.6000 | 0.052006 |
| ES/USD | 1d | `bear_relief_reversal_fast` | 109 | 0.000198 | 0.5229 | 0.021569 |
| ES/USD | 1d | `sideways_breakout_follow` | 106 | 0.000512 | 0.5472 | 0.054292 |
| ES/USD | 1d | `sideways_reversion_control` | 38 | 0.001125 | 0.5000 | 0.042734 |
| ES/USD | 1d | `crisis_relief_long_confirmed` | 115 | -0.000531 | 0.5043 | -0.061104 |
| ES/USD | 1d | `crisis_tail_short_strict` | 101 | 0.001506 | 0.5941 | 0.152135 |
| ES/USD | 1d | `crisis_defensive_rotation` | 73 | 0.004882 | 0.5753 | 0.356375 |
| AAPL/USD | 1d | `bull_trend_slow_anchor` | 53 | 0.003545 | 0.6226 | 0.187885 |
| AAPL/USD | 1d | `bear_breakdown_short_strict` | 87 | 0.004511 | 0.5172 | 0.392435 |
| AAPL/USD | 1d | `bear_relief_reversal_fast` | 92 | 0.003279 | 0.5978 | 0.301697 |
| AAPL/USD | 1d | `sideways_breakout_follow` | 88 | 0.003093 | 0.5568 | 0.272207 |
| AAPL/USD | 1d | `sideways_reversion_control` | 34 | -0.000352 | 0.4412 | -0.011979 |
| AAPL/USD | 1d | `crisis_relief_long_confirmed` | 97 | 0.001366 | 0.5567 | 0.132472 |
| AAPL/USD | 1d | `crisis_tail_short_strict` | 82 | 0.006192 | 0.5488 | 0.507777 |
| AAPL/USD | 1d | `crisis_defensive_rotation` | 62 | 0.003271 | 0.5645 | 0.202801 |
| GLD/USD | 1h | `bull_trend_slow_anchor` | 50 | 0.005790 | 0.5600 | 0.289511 |
| GLD/USD | 1h | `bear_breakdown_short_strict` | 92 | 0.001134 | 0.4891 | 0.104323 |
| GLD/USD | 1h | `bear_relief_reversal_fast` | 114 | 0.000665 | 0.5965 | 0.075831 |
| GLD/USD | 1h | `sideways_breakout_follow` | 100 | 0.001213 | 0.5300 | 0.121306 |
| GLD/USD | 1h | `sideways_reversion_control` | 41 | 0.000560 | 0.5610 | 0.022970 |
| GLD/USD | 1h | `crisis_relief_long_confirmed` | 111 | 0.000625 | 0.5856 | 0.069415 |
| GLD/USD | 1h | `crisis_tail_short_strict` | 94 | 0.001644 | 0.5000 | 0.154511 |
| GLD/USD | 1h | `crisis_defensive_rotation` | 10 | -0.000165 | 0.3000 | -0.001654 |
| GLD/USD | 4h | `bull_trend_slow_anchor` | 33 | 0.009341 | 0.6364 | 0.308255 |
| GLD/USD | 4h | `bear_breakdown_short_strict` | 43 | 0.003347 | 0.6279 | 0.143909 |
| GLD/USD | 4h | `bear_relief_reversal_fast` | 50 | -0.000318 | 0.5200 | -0.015893 |
| GLD/USD | 4h | `sideways_breakout_follow` | 50 | 0.002777 | 0.6400 | 0.138831 |
| GLD/USD | 4h | `sideways_reversion_control` | 18 | -0.003677 | 0.4444 | -0.066194 |
| GLD/USD | 4h | `crisis_relief_long_confirmed` | 50 | -0.000318 | 0.5200 | -0.015893 |
| GLD/USD | 4h | `crisis_tail_short_strict` | 44 | 0.002138 | 0.5909 | 0.094075 |
| GLD/USD | 4h | `crisis_defensive_rotation` | 3 | -0.007762 | 0.3333 | -0.023285 |

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `bull_trend_slow_anchor` | 6548 | 16 | 49 | 0.7500 | 0.001899 | 0.250 | 5.6708 | 76.2500 | `pass` |
| Bear | `crisis_tail_short_strict` | 2458 | 13 | 34 | 0.6154 | 0.000118 | 0.769 | 1.7060 | 46.5861 | `fail:reject_fold_inconsistency|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60` |
| Sideways | `sideways_breakout_follow` | 3594 | 16 | 20 | 0.3750 | -0.001076 | 0.250 | -0.9468 | 20.6250 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | `sideways_reversion_control` | 28 | 4 | 1 | 0.7500 | -0.003683 | 0.200 | 0.6592 | 39.5710 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60` |
| Manipulation(scoped) | `no_direct_event_rows` | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.000 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Inputs

- Local Auto-Quant feathers: `/Users/thrill3r/Auto-Quant/user_data/data`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^IXIC`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T195624-codex-board-b-root-branch-rescue-predeclared-v1/branch-rc-spa/root_branch_rescue_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T195624-codex-board-b-root-branch-rescue-predeclared-v1/branch-rc-spa/root_branch_rescue_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T195624-codex-board-b-root-branch-rescue-predeclared-v1/branch-rc-spa/root_branch_rescue_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T195624-codex-board-b-root-branch-rescue-predeclared-v1/branch-rc-spa/root_branch_rescue_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T195624-codex-board-b-root-branch-rescue-predeclared-v1/branch-rc-spa/root_branch_rescue_panel_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T195624-codex-board-b-root-branch-rescue-predeclared-v1/ict-engine-fail-closed/root_branch_rescue_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T195624-codex-board-b-root-branch-rescue-predeclared-v1/checks/root_branch_rescue_v1_assertions.out`

## Next

- B2R-repeat: keep RootTransitionTriad as fail-closed evidence; direct Manipulation still needs trade/PnL rows, and failed roots need a different family or provider panel without relaxing RC-SPA.
