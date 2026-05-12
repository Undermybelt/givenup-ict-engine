# 112315 Provider Matrix AQ Readback v1

Run id: `20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1`
Source provider matrix: `20260512T112315+0800-codex-board-b-six-provider-btc-matrix-probe-v1`

## Scope
This packet reads the fresh 112315 provider matrix, runs AQ only on providers with BTC rows, and keeps failed TVR/IBKR provider gates explicit.
It does not change ict-engine runtime code and does not substitute another provider for TVR or IBKR.

## Provider Matrix
- `yfinance_btc_usd_1h`: rows `983`, exit `0`.
- `kraken_xbtusd_1h`: rows `721`, exit `0`.
- `binance_btcusdt_1h`: rows `985`, exit `0`.
- `bybit_btcusdt_linear_1h`: rows `985`, exit `0`.
- `ibkr_btc_paxos_1d`: rows `0`, exit `0`.
- `tradingview_mcp_btcusdt_1d`: exit `1`.

## AQ Results
- `yfinance`: rows `983`, compile exit `0`, TOMAC exit `0`.
  - ProviderCryptoMomentumStateV1: trades=14 profit_pct=1.69 sharpe=1.7293965722332505 pf=1.7314733582840918
  - ProviderCryptoPullbackRevertV1: trades=8 profit_pct=-0.21 sharpe=-0.2935183357387061 pf=0.8505535234732061
- `kraken_public`: rows `721`, compile exit `0`, TOMAC exit `0`.
  - ProviderCryptoMomentumStateV1: trades=23 profit_pct=-0.55 sharpe=-1.1266214858050265 pf=0.8609310567518771
  - ProviderCryptoPullbackRevertV1: trades=9 profit_pct=-0.71 sharpe=-1.627366200080825 pf=0.5831340534022595
- `binance_public`: rows `985`, compile exit `0`, TOMAC exit `0`.
  - ProviderCryptoMomentumStateV1: trades=37 profit_pct=0.77 sharpe=1.0089262848650395 pf=1.1326410355009617
  - ProviderCryptoPullbackRevertV1: trades=15 profit_pct=-0.98 sharpe=-1.8226824759876528 pf=0.5850842589000907
- `bybit_public`: rows `985`, compile exit `0`, TOMAC exit `0`.
  - ProviderCryptoMomentumStateV1: trades=34 profit_pct=1.48 sharpe=1.8613380661422825 pf=1.288511226299377
  - ProviderCryptoPullbackRevertV1: trades=17 profit_pct=-1.71 sharpe=-3.1115433239784096 pf=0.45016637432495576

## Decision
- Gate result: `112315_provider_matrix_aq_readback=public_provider_aq_ran_but_tvr_ibkr_fail_closed_no_six_provider_authority_no_promotion`.
- Four public BTC providers have same-root rows and AQ execution, but TVR fetch failed and IBKR PAXOS BTC returned zero rows.
- This is not a six-provider AQ authority packet and cannot unlock Pre-Bayes/BBN/CatBoost/execution-tree promotion.
- Accepted rows added: `0`.
- Mature rooted branch observations added: `0`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1/112315-provider-matrix-aq-readback-v1/112315_provider_matrix_aq_readback_v1.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1/112315-provider-matrix-aq-readback-v1/prompt_to_artifact_checklist_112315_provider_matrix_aq_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1/checks/112315_provider_matrix_aq_readback_v1_assertions.out`
- Provider CSVs: `docs/experiments/actionable-regime-confidence/runs/20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1/provider-csv`
- AQ workspaces: `docs/experiments/actionable-regime-confidence/runs/20260512T112904+0800-codex-112315-provider-matrix-aq-readback-v1/workspace`
