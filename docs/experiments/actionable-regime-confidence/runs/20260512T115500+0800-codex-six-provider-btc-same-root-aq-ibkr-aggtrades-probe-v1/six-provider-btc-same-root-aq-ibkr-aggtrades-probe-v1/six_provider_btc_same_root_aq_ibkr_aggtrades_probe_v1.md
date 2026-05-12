# Six-Provider BTC Same-Root AQ IBKR AGGTRADES Probe v1

Run id: `20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1`

## Scope
Fresh same-root provider/AQ diagnostic for the Board A six-provider authority blocker.
This run attempts to make IBKR a first-class 1h AQ input by using PAXOS `AGGTRADES` over the same BTC root.
It does not approve selected historical data, mutate canonical source/control roots, run downstream promotion, or call `update_goal`.

## Provider Fetches
- `yfinance_btc_usd_1h`: rows `983`, exit `0`.
- `kraken_xbtusd_1h`: rows `721`, exit `0`.
- `binance_btcusdt_1h`: rows `985`, exit `0`.
- `bybit_btcusdt_linear_1h`: rows `985`, exit `0`.
- `tvr_binance_btcusdt_1h`: rows `720`, exit `0`.
- `tvr_btc_usd_1h_local_stdio`: rows `0`, exit `None`.
- `tvr_selected_1h`: rows `720`, exit `None`.
- `ibkr_btc_paxos_aggtrades_1h`: rows `783`, exit `0`.

## AQ Results
- `yfinance`: rows `983`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `14`, profit_pct `1.69`, win_rate_pct `50.0`, profit_factor `1.7314733582840918`.
  - `ProviderCryptoPullbackRevertV1`: trades `8`, profit_pct `-0.21`, win_rate_pct `37.5`, profit_factor `0.8505535234732061`.
- `kraken_public`: rows `721`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `23`, profit_pct `-0.55`, win_rate_pct `34.78260869565217`, profit_factor `0.8609310567518771`.
  - `ProviderCryptoPullbackRevertV1`: trades `9`, profit_pct `-0.71`, win_rate_pct `22.22222222222222`, profit_factor `0.5831340534022595`.
- `binance_public`: rows `985`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `37`, profit_pct `0.77`, win_rate_pct `37.83783783783784`, profit_factor `1.1326410355009617`.
  - `ProviderCryptoPullbackRevertV1`: trades `15`, profit_pct `-0.98`, win_rate_pct `26.666666666666668`, profit_factor `0.5850842589000907`.
- `bybit_public`: rows `985`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `34`, profit_pct `1.48`, win_rate_pct `41.17647058823529`, profit_factor `1.288511226299377`.
  - `ProviderCryptoPullbackRevertV1`: trades `17`, profit_pct `-1.71`, win_rate_pct `23.52941176470588`, profit_factor `0.45016637432495576`.
- `tvr_binance`: rows `720`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `25`, profit_pct `-1.03`, win_rate_pct `32.0`, profit_factor `0.765930096934388`.
  - `ProviderCryptoPullbackRevertV1`: trades `12`, profit_pct `-1.47`, win_rate_pct `16.666666666666664`, profit_factor `0.34369888998507653`.
- `ibkr_aggtrades`: rows `783`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `34`, profit_pct `0.08`, win_rate_pct `38.23529411764706`, profit_factor `1.0144516414659697`.
  - `ProviderCryptoPullbackRevertV1`: trades `17`, profit_pct `1.31`, win_rate_pct `52.94117647058824`, profit_factor `1.6850347091222428`.

## Decision
- Gate result: `six_provider_btc_same_root_aq_ibkr_aggtrades_probe_v1=same_root_six_provider_aq_present_but_selected_history_and_downstream_not_run_no_promotion`.
- Successful AQ provider runs: `6/6`.
- Strategies with metrics: `12`.
- Total trades in AQ metrics: `245`.
- Same-root six-provider AQ authority: `True`.
- IBKR first-class AQ success: `True`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1/six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1/six_provider_btc_same_root_aq_ibkr_aggtrades_probe_v1.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1/six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1/prompt_to_artifact_checklist_six_provider_btc_same_root_aq_ibkr_aggtrades_probe_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1/checks/six_provider_btc_same_root_aq_ibkr_aggtrades_probe_v1_assertions.out`
- Provider CSVs: `docs/experiments/actionable-regime-confidence/runs/20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1/provider-csv`
- AQ workspaces: `docs/experiments/actionable-regime-confidence/runs/20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1/workspace`
