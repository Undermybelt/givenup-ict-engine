# IBKR Longer Duration Six-Provider AQ v1

Run id: `20260512T115130+0800-codex-113833-ibkr-longer-duration-six-provider-aq-v1`
Source repair root: `20260512T113833+0800-codex-112904-provider-matrix-aq-date-contract-repair-v1`

## Scope
Rerun the six provider AQ matrix with the same date-contract repair as 113833, but replace the thin 2D IBKR 1h MIDPOINT input with a 14D IBKR 1h MIDPOINT fetch.
This does not edit ict-engine runtime code, rewrite older roots, or promote a candidate.

## Fetch
- IBKR 14D fetch exit `0`, rows `359`.

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
- `ibkr_midpoint_14d`: rows `359`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `10`, profit_pct `0.37`, win_rate_pct `40.0`, profit_factor `1.2232978343167065`.
  - `ProviderCryptoPullbackRevertV1`: trades `7`, profit_pct `-1.64`, win_rate_pct `0.0`, profit_factor `0.0`.

## Decision
- Gate result: `ibkr_longer_duration_six_provider_aq_v1=six_provider_aq_ran_no_downstream_promotion`.
- Successful AQ provider runs: `6/6`.
- Strategies with metrics: `12`.
- Total trades in AQ metrics: `211`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T115130+0800-codex-113833-ibkr-longer-duration-six-provider-aq-v1/ibkr-longer-duration-six-provider-aq-v1/ibkr_longer_duration_six_provider_aq_v1.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T115130+0800-codex-113833-ibkr-longer-duration-six-provider-aq-v1/ibkr-longer-duration-six-provider-aq-v1/prompt_to_artifact_checklist_ibkr_longer_duration_six_provider_aq_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T115130+0800-codex-113833-ibkr-longer-duration-six-provider-aq-v1/checks/ibkr_longer_duration_six_provider_aq_v1_assertions.out`
- Provider CSVs: `docs/experiments/actionable-regime-confidence/runs/20260512T115130+0800-codex-113833-ibkr-longer-duration-six-provider-aq-v1/provider-csv`
- AQ workspaces: `docs/experiments/actionable-regime-confidence/runs/20260512T115130+0800-codex-113833-ibkr-longer-duration-six-provider-aq-v1/workspace`
