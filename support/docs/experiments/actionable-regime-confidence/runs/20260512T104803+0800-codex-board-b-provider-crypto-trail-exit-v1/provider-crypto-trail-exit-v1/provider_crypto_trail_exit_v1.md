# Provider Crypto Trail Exit Readback v1

Run id: `20260512T104803+0800-codex-board-b-provider-crypto-trail-exit-v1`

Purpose: close out the provider-owned BTC/ETH/SOL crypto trail/profit-gate follow-up without promoting a candidate. This is an additive Board B readback and does not edit the Current Cursor.

## Provider / AQ Provenance

- `aq_provider_invoked=true`.
- `provider_requested=Binance/Yahoo-provider-provenanced BTC/ETH/SOL 1h replay panel`.
- `provider_data_acquired=true`.
- `provider_unreachable=[]`.
- `local_cache_replay=provider-provenanced run-local feather replay`.
- Source workspace: `docs/experiments/actionable-regime-confidence/runs/20260512T103437+0800-codex-board-b-yahoo-crypto-momentum-market-aq-v1/workspace/auto-quant-yahoo-crypto-momentum`.

## Commands

- `00_run_provider_crypto_profit_gate_tomac`: exit `0`.
- `01_run_provider_crypto_tight_risk_tomac`: exit `0`.
- `02_run_provider_crypto_ema_rsi_long_panel_tomac`: exit `0`.

## Readback

| Strategy | Branch path | Trades | Profit % | Win % | PF | Max DD % | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| `ProviderBtcEmaRsiHold12LongPanelV1` | `Bull -> ProviderTrend -> EmaRsiContinuation -> ProviderBtcEmaRsiHold12LongPanelV1` | 474 | -10.34 | 45.3586 | 0.9156 | -18.3521 | `reject_no_positive_edge` |
| `ProviderCryptoMomentumProfitGateV1` | `Bull -> ProviderCryptoMomentum -> ProfitGatedExit -> ProviderCryptoMomentumProfitGateV1` | 180 | -12.82 | 70.0000 | 0.8303 | -19.8054 | `reject_no_positive_edge` |
| `ProviderCryptoMomentumTightRiskV1` | `Bull -> ProviderCryptoMomentum -> TightRiskExit -> ProviderCryptoMomentumTightRiskV1` | 246 | -14.49 | 61.7886 | 0.7905 | -19.1287 | `reject_no_positive_edge` |
| `ProviderCryptoPullbackProfitGateV1` | `Sideways -> ProviderCryptoPullback -> ProfitGatedExit -> ProviderCryptoPullbackProfitGateV1` | 93 | -1.76 | 75.2688 | 0.9377 | -6.2246 | `reject_no_positive_edge` |
| `ProviderCryptoPullbackTightRiskV1` | `Sideways -> ProviderCryptoPullback -> TightRiskExit -> ProviderCryptoPullbackTightRiskV1` | 100 | -8.08 | 62.0000 | 0.6847 | -9.6021 | `reject_no_positive_edge` |

## Gate

- `fail:all_104803_long_panel_variants_negative_net_return`.
- `fail_closed:no_positive_edge_for_downstream_promotion`.
- `downstream_consumption=not_started:blocked_by_no_positive_edge`.
- `promotion_allowed=false`.
- `update_goal=false`.

## Next

Do not promote or downstream-rerun `104803`. Use `104703` only as short-window incubation feedback; next Board B work needs a provider-owned rooted factor that keeps positive net edge at `>=100` trades or an explicit selected-history/source-control unlock.
