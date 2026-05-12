# OB/FVG Regime Branch Screen v1

This is a lightweight provider-backed screen, not an AQ promotion packet.

- total_trades: `5276`
- branch_count: `24`
- provider_rows: `6`
- same_root_aq_provider_authority: `false`
- promotion_allowed: `false`
- trade_usable: `false`

## Top Branch Hints
- `TrendTransition->LowVolatility->up_momentum->order_block_pullback_v1` trades=`33` win_rate=`0.454545` pf=`2.129562` mean_net=`0.001668700079` folds=`test,train,validation`
- `TrendTransition->HighVolatility->up_momentum->fair_value_gap_pullback_v1` trades=`119` win_rate=`0.378151` pf=`1.209620` mean_net=`0.001004149126` folds=`test,train,validation`
- `TrendExpansion->HighVolatility->up_momentum->order_block_pullback_v1` trades=`85` win_rate=`0.423529` pf=`1.145204` mean_net=`0.00126682062` folds=`test,train,validation`
- `TrendTransition->HighVolatility->down_momentum->fair_value_gap_pullback_v1` trades=`152` win_rate=`0.388158` pf=`1.083376` mean_net=`0.0004529254227` folds=`test,train,validation`
- `TrendExpansion->HighVolatility->up_momentum->fair_value_gap_pullback_v1` trades=`349` win_rate=`0.409742` pf=`0.971380` mean_net=`-0.0001680977475` folds=`test,train,validation`
- `TrendTransition->NormalVolatility->up_momentum->order_block_pullback_v1` trades=`80` win_rate=`0.387500` pf=`0.970513` mean_net=`-0.0001092460013` folds=`test,train,validation`
- `TrendTransition->NormalVolatility->up_momentum->fair_value_gap_pullback_v1` trades=`374` win_rate=`0.355615` pf=`0.950775` mean_net=`-0.0001419224847` folds=`test,train,validation`
- `TrendTransition->HighVolatility->up_momentum->order_block_pullback_v1` trades=`28` win_rate=`0.500000` pf=`0.938828` mean_net=`-0.0005611449555` folds=`test,train,validation`
- `TrendExpansion->HighVolatility->down_momentum->fair_value_gap_pullback_v1` trades=`447` win_rate=`0.375839` pf=`0.923067` mean_net=`-0.000548528006` folds=`test,train,validation`
- `TrendExpansion->NormalVolatility->down_momentum->fair_value_gap_pullback_v1` trades=`581` win_rate=`0.358003` pf=`0.902100` mean_net=`-0.0003207654961` folds=`test,train,validation`

## Fail-Closed Notes
- TVR is missing in this local provider file set.
- All acquired provider rows are replayed from prior normalized provider artifacts, not same-root AQ/provider acquisition.
- No Auto-Quant backtest, Pre-Bayes, BBN, CatBoost runtime registration, or execution-tree admission is claimed by this root.
