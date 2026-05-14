# Six Provider AQ First-Class IBKR v1

Run id: `20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1`

## Scope
This packet fetches all six provider lanes inside this run root, then runs the existing AQ/TOMAC provider strategy template.
It does not edit ict-engine runtime code, does not approve selected history, and does not promote a downstream candidate.

## Provider Fetches
- `11_yfinance_btc_usd_1h`: rows `0`, exit `2`, csv `docs/experiments/actionable-regime-confidence/runs/20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1/provider-csv/yfinance_btc_usd_1h.csv`.
- `12_kraken_xbtusd_1h`: rows `721`, exit `0`, csv `docs/experiments/actionable-regime-confidence/runs/20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1/provider-csv/kraken_xbtusd_1h.csv`.
- `13_binance_btcusdt_1h`: rows `985`, exit `0`, csv `docs/experiments/actionable-regime-confidence/runs/20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1/provider-csv/binance_btcusdt_1h.csv`.
- `14_bybit_btcusdt_linear_1h`: rows `985`, exit `0`, csv `docs/experiments/actionable-regime-confidence/runs/20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1/provider-csv/bybit_btcusdt_linear_1h.csv`.
- `20_tvr_binance_btcusdt_1h`: rows `0`, exit `1`, csv `docs/experiments/actionable-regime-confidence/runs/20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1/provider-csv/tvr_binance_btcusdt_1h.csv`.
- `ibkr`: exit `0`, selected `AGGTRADES`, selected_rows `250`, aggtrades_rows `250`, midpoint_rows `250`.

## AQ Results
- `kraken_public`: rows `721`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `23`, profit_pct `-0.55`, win_rate_pct `34.78260869565217`, profit_factor `0.8609310567518771`.
  - `ProviderCryptoPullbackRevertV1`: trades `9`, profit_pct `-0.71`, win_rate_pct `22.22222222222222`, profit_factor `0.5831340534022595`.
- `binance_public`: rows `985`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `37`, profit_pct `0.77`, win_rate_pct `37.83783783783784`, profit_factor `1.1326410355009617`.
  - `ProviderCryptoPullbackRevertV1`: trades `15`, profit_pct `-0.98`, win_rate_pct `26.666666666666668`, profit_factor `0.5850842589000907`.
- `bybit_public`: rows `985`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `34`, profit_pct `1.48`, win_rate_pct `41.17647058823529`, profit_factor `1.288511226299377`.
  - `ProviderCryptoPullbackRevertV1`: trades `17`, profit_pct `-1.71`, win_rate_pct `23.52941176470588`, profit_factor `0.45016637432495576`.
- `ibkr_paxos`: rows `250`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `10`, profit_pct `-0.63`, win_rate_pct `40.0`, profit_factor `0.7061755299303044`.
  - `ProviderCryptoPullbackRevertV1`: trades `3`, profit_pct `-0.18`, win_rate_pct `33.33333333333333`, profit_factor `0.675612526789749`.

## Decision
- Gate result: `115431_six_provider_aq_first_class_ibkr_v1=provider_or_aq_gate_incomplete_no_downstream_promotion`.
- Same-root six-provider AQ authority: `False`.
- Successful AQ provider runs: `4/4`.
- Strategies with metrics: `8`.
- Total trades: `148`.
- Mature rooted branch observations added: `0`.
- Downstream Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree promotion chain: `not_run`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1/six-provider-aq-first-class-ibkr-v1/six_provider_aq_first_class_ibkr_v1.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1/six-provider-aq-first-class-ibkr-v1/prompt_to_artifact_checklist_six_provider_aq_first_class_ibkr_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1/checks/six_provider_aq_first_class_ibkr_v1_assertions.out`
- Provider CSVs: `docs/experiments/actionable-regime-confidence/runs/20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1/provider-csv`
- AQ workspaces: `docs/experiments/actionable-regime-confidence/runs/20260512T115431+0800-codex-six-provider-aq-first-class-ibkr-v1/workspace`
