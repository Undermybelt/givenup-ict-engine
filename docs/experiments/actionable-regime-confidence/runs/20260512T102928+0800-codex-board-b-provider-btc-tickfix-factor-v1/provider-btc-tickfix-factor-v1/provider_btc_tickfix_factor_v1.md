# Provider BTC Tickfix Factor v1

Run id: `20260512T102928+0800-codex-board-b-provider-btc-tickfix-factor-v1`

Gate result: `provider_btc_tickfix_factor_v1=nonzero_provider_btc_factor_trades_incubation_only_no_promotion`

## Readback

- Source provider CSV lineage: Binance `BTCUSDT` 1h provider CSV from `20260512T100419+0800-codex-board-b-provider-owned-aq-acquisition-v1`, copied through the earlier `101623` prepared BTC workspace.
- This rerun uses the same run-local provider BTC strategy set as `101623`, with only the copied TOMAC harness synthetic precision fixed from `amount=8` to `amount=0.00000001` for ccxt `TICK_SIZE` mode.
- All three Freqtrade/TOMAC strategy runs exited `0`.
- `ProviderBtcMomentumCross` path: `Bull -> Momentum -> Pullback -> ProviderBtcMomentumCross`; trades `9`, total profit `2.1400%`, Sharpe `1.2260`, win rate `55.5556%`, profit factor `1.7770`, max drawdown `-1.6264%`.
- `ProviderBtcMomentumPulse` path: `Bull -> ProviderTrend -> MomentumPulse -> ProviderBtcMomentumPulse`; trades `57`, total profit `-3.6100%`, Sharpe `-2.1249`, win rate `38.5965%`, profit factor `0.8418`, max drawdown `-6.5240%`.
- `ProviderBtcTrendPullback` path: `Bull -> ProviderTrend -> PullbackReclaim -> ProviderBtcTrendPullback`; trades `16`, total profit `-5.2100%`, Sharpe `-4.0764`, win rate `31.2500%`, profit factor `0.2877`, max drawdown `-5.5521%`.

## Decision

- The provider-owned BTC factor lane now has nonzero executed trades after the run-local tick-size fix.
- It still does not satisfy mature promotion criteria: the only profitable strategy has `9` trades, while the higher-count `57`-trade strategy is unprofitable.
- No selected-history approval, source/control unlock, canonical merge input, Pre-Bayes/filter, BBN, CatBoost/path-ranker, execution-tree promotion, or trade-usable evidence was produced in this slice.
- Accepted production rows added: `0`.
- Promotion allowed: `false`.
- `update_goal=false`.

## Artifacts

- TOMAC stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T102928+0800-codex-board-b-provider-btc-tickfix-factor-v1/command-output/00_run_provider_btc_tickfix_factors.out`
- TOMAC stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T102928+0800-codex-board-b-provider-btc-tickfix-factor-v1/command-output/00_run_provider_btc_tickfix_factors.err`
- Run-local harness: `docs/experiments/actionable-regime-confidence/runs/20260512T102928+0800-codex-board-b-provider-btc-tickfix-factor-v1/workspace/auto-quant-provider-btc-tickfix-factor/run_tomac.py`
- Strategies: `docs/experiments/actionable-regime-confidence/runs/20260512T102928+0800-codex-board-b-provider-btc-tickfix-factor-v1/workspace/auto-quant-provider-btc-tickfix-factor/user_data/strategies_external/`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T102928+0800-codex-board-b-provider-btc-tickfix-factor-v1/provider-btc-tickfix-factor-v1/provider_btc_tickfix_factor_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T102928+0800-codex-board-b-provider-btc-tickfix-factor-v1/checks/provider_btc_tickfix_factor_v1_assertions.out`
