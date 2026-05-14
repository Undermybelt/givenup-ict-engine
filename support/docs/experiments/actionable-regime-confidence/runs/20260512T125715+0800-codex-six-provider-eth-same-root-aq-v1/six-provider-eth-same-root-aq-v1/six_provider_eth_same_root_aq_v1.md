# Six-Provider ETH Same-Root AQ v1

Run id: `20260512T125715+0800-codex-six-provider-eth-same-root-aq-v1`

## Scope
Fresh non-BTC same-root provider/AQ diagnostic for the Board A six-provider authority blocker.
This run attempts ETH across yfinance, Kraken, Binance, Bybit, TradingViewRemix/TVR, and IBKR PAXOS AGGTRADES.
It does not approve selected historical data, mutate canonical source/control roots, promote execution, or call `update_goal`.

## Provider Fetches
- `yfinance_eth_usd_1h`: rows `983`, exit `0`.
- `kraken_ethusd_1h`: rows `721`, exit `0`.
- `binance_ethusdt_1h`: rows `985`, exit `0`.
- `bybit_ethusdt_linear_1h`: rows `985`, exit `0`.
- `tvr_binance_ethusdt_1h`: rows `720`, exit `0`.
- `tvr_eth_usd_1h_local_stdio`: rows `0`, exit `None`.
- `tvr_selected_1h`: rows `720`, exit `None`.
- `ibkr_eth_paxos_aggtrades_1h`: rows `784`, exit `0`.

## AQ Results
- `yfinance`: rows `983`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `21`, profit_pct `3.27`, win_rate_pct `47.61904761904761`, profit_factor `1.9266710378132572`.
  - `ProviderCryptoPullbackRevertV1`: trades `8`, profit_pct `-2.38`, win_rate_pct `25.0`, profit_factor `0.1242874475712799`.
- `kraken_public`: rows `721`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `20`, profit_pct `0.31`, win_rate_pct `35.0`, profit_factor `1.0986393316703826`.
  - `ProviderCryptoPullbackRevertV1`: trades `14`, profit_pct `-2.52`, win_rate_pct `28.57142857142857`, profit_factor `0.2889546244656568`.
- `binance_public`: rows `985`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `34`, profit_pct `1.6`, win_rate_pct `32.35294117647059`, profit_factor `1.2727521145789806`.
  - `ProviderCryptoPullbackRevertV1`: trades `20`, profit_pct `-3.41`, win_rate_pct `25.0`, profit_factor `0.3438922381605806`.
- `bybit_public`: rows `985`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `34`, profit_pct `1.62`, win_rate_pct `32.35294117647059`, profit_factor `1.2731908285700428`.
  - `ProviderCryptoPullbackRevertV1`: trades `19`, profit_pct `-3.45`, win_rate_pct `26.31578947368421`, profit_factor `0.34268285102471957`.
- `tvr_binance`: rows `720`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `21`, profit_pct `0.41`, win_rate_pct `33.33333333333333`, profit_factor `1.1319655708058605`.
  - `ProviderCryptoPullbackRevertV1`: trades `16`, profit_pct `-3.35`, win_rate_pct `25.0`, profit_factor `0.23674688056756404`.
- `ibkr_aggtrades`: rows `784`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `32`, profit_pct `1.19`, win_rate_pct `31.25`, profit_factor `1.1810934260535257`.
  - `ProviderCryptoPullbackRevertV1`: trades `14`, profit_pct `-1.54`, win_rate_pct `35.714285714285715`, profit_factor `0.5245622776678557`.

## Decision
- Gate result: `six_provider_eth_same_root_aq_v1=same_root_six_provider_eth_aq_present_downstream_not_run_no_promotion`.
- Successful AQ provider runs: `6/6`.
- Strategies with metrics: `12`.
- Total trades in AQ metrics: `253`.
- Same-root six-provider ETH AQ authority: `True`.
- IBKR first-class ETH AQ success: `True`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T125715+0800-codex-six-provider-eth-same-root-aq-v1/six-provider-eth-same-root-aq-v1/six_provider_eth_same_root_aq_v1.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T125715+0800-codex-six-provider-eth-same-root-aq-v1/six-provider-eth-same-root-aq-v1/prompt_to_artifact_checklist_six_provider_eth_same_root_aq_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T125715+0800-codex-six-provider-eth-same-root-aq-v1/checks/six_provider_eth_same_root_aq_v1_assertions.out`
- Provider CSVs: `docs/experiments/actionable-regime-confidence/runs/20260512T125715+0800-codex-six-provider-eth-same-root-aq-v1/provider-csv`
- AQ workspaces: `docs/experiments/actionable-regime-confidence/runs/20260512T125715+0800-codex-six-provider-eth-same-root-aq-v1/workspace`
