# 112315 Same-Root Six-Provider AQ Readback v1

Run id: `20260512T115108+0800-codex-112315-same-root-six-provider-aq-readback-v1`
Source provider root: `20260512T112315+0800-codex-board-b-six-provider-btc-matrix-probe-v1`

## Scope
This packet runs AQ/TOMAC from the single `112315` provider-acquisition root only.
It uses YF, Kraken, Binance, Bybit 1h rows plus the same-root TVR BTC-USD 1d and IBKR PAXOS AGGTRADES 1d rows.
It does not edit ict-engine runtime code, does not approve selected history, and does not promote a candidate.

## Provider Matrix
- `yfinance_btc_usd_1h`: rows `983`, exit `0`.
- `kraken_xbtusd_1h`: rows `721`, exit `0`.
- `binance_btcusdt_1h`: rows `985`, exit `0`.
- `bybit_btcusdt_linear_1h`: rows `985`, exit `0`.
- `tvr_btc_usd_1d`: rows `29`, exit `0`.
- `ibkr_btc_paxos_aggtrades_1d`: rows `30`, exit `0`.

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
- `tvr_btc_usd`: rows `29`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `4`, profit_pct `1.93`, win_rate_pct `75.0`, profit_factor `12.22561496453853`.
  - `ProviderCryptoPullbackRevertV1`: trades `2`, profit_pct `0.31`, win_rate_pct `50.0`, profit_factor `5.7072619935028674`.
- `ibkr_aggtrades`: rows `30`, compile exit `0`, TOMAC exit `0`.
  - `ProviderCryptoMomentumStateV1`: trades `7`, profit_pct `0.41`, win_rate_pct `57.14285714285714`, profit_factor `1.221546875920795`.
  - `ProviderCryptoPullbackRevertV1`: trades `0`, profit_pct `0.0`, win_rate_pct `0.0`, profit_factor `0.0`.

## Decision
- Gate result: `112315_same_root_six_provider_aq_readback=same_provider_root_aq_attempted_but_tvr_ibkr_daily_template_mismatch_no_promotion`.
- Successful AQ provider runs: `6/6`.
- Strategies with metrics: `12`.
- Total trades in AQ metrics: `170`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Fail-Closed Reason
- This is closer to same-root provider authority than `113833`, but TVR and IBKR are only daily rows inside a 1h TOMAC template.
- IBKR still lacks a successful 1h AQ lane; no accepted six-provider AQ authority is claimed.
- No Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution-tree promotion chain is run from this packet.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T115108+0800-codex-112315-same-root-six-provider-aq-readback-v1/112315-same-root-six-provider-aq-readback-v1/112315_same_root_six_provider_aq_readback_v1.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T115108+0800-codex-112315-same-root-six-provider-aq-readback-v1/112315-same-root-six-provider-aq-readback-v1/prompt_to_artifact_checklist_112315_same_root_six_provider_aq_readback_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T115108+0800-codex-112315-same-root-six-provider-aq-readback-v1/checks/112315_same_root_six_provider_aq_readback_v1_assertions.out`
- Provider CSVs: `docs/experiments/actionable-regime-confidence/runs/20260512T115108+0800-codex-112315-same-root-six-provider-aq-readback-v1/provider-csv`
- AQ workspaces: `docs/experiments/actionable-regime-confidence/runs/20260512T115108+0800-codex-112315-same-root-six-provider-aq-readback-v1/workspace`
