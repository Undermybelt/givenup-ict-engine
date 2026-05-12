# Provider-Window-Aware Same-Root AQ v1

Run id: `20260512T172214+0800-codex-board-a-provider-window-aware-same-root-aq-v1`

## Scope
Fresh same-root Board A provider/AQ packet using provider-specific feasible BTC 1h windows after `170852` and `171227`.
This packet runs provider materialization and Auto-Quant only. It does not run downstream promotion gates.

## Provider Matrix
- `yfinance`: requested `2024-05-15_to_2026-05-12_supported_730d_cap`, rows `17415`, first `2024-05-15 00:00:00+00:00`, last `2026-05-11 23:00:00+00:00`.
- `kraken`: requested `2026-02-18_to_2026-05-12_current_window_repair`, rows `1993`, first `2026-02-18 00:00:00+00:00`, last `2026-05-12 00:00:00+00:00`.
- `binance`: requested `2021-01-01_to_2026-05-12_broad_window`, rows `46955`, first `2021-01-01 00:00:00+00:00`, last `2026-05-12 00:00:00+00:00`.
- `bybit`: requested `2021-01-01_to_2026-05-12_provider_cap_observed`, rows `1000`, first `2026-03-31 09:00:00+00:00`, last `2026-05-12 00:00:00+00:00`.
- `tvr`: requested `provider_default_local_stdio_current_window`, rows `720`, first `2026-04-12T10:00:00Z`, last `2026-05-12T09:36:55Z`.
- `ibkr`: requested `1Y_duration_via_ibkr_bulk_client146`, rows `6930`, first ``, last ``.

## Auto-Quant Results
- `yfinance`: rows `17415`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T172214+0800-codex-board-a-provider-window-aware-same-root-aq-v1/workspace/auto-quant-112315-yfinance`.
  - `ProviderCryptoMomentumStateV1`: trades `319`, profit_pct `-21.99`, win_rate_pct `23.824451410658305`, profit_factor `0.6392898888632508`.
  - `ProviderCryptoPullbackRevertV1`: trades `146`, profit_pct `2.83`, win_rate_pct `45.20547945205479`, profit_factor `1.1185755311888328`.
- `kraken_public`: rows `1993`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T172214+0800-codex-board-a-provider-window-aware-same-root-aq-v1/workspace/auto-quant-112315-kraken_public`.
  - `ProviderCryptoMomentumStateV1`: trades `76`, profit_pct `-3.48`, win_rate_pct `31.57894736842105`, profit_factor `0.7440064020125409`.
  - `ProviderCryptoPullbackRevertV1`: trades `30`, profit_pct `-2.25`, win_rate_pct `33.33333333333333`, profit_factor `0.611492759978`.
- `binance_public`: rows `46955`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T172214+0800-codex-board-a-provider-window-aware-same-root-aq-v1/workspace/auto-quant-112315-binance_public`.
  - `ProviderCryptoMomentumStateV1`: trades `624`, profit_pct `-43.34`, win_rate_pct `23.076923076923077`, profit_factor `0.5637237561972133`.
  - `ProviderCryptoPullbackRevertV1`: trades `268`, profit_pct `-13.25`, win_rate_pct `38.43283582089552`, profit_factor `0.7389778890096554`.
- `bybit_public`: rows `1000`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T172214+0800-codex-board-a-provider-window-aware-same-root-aq-v1/workspace/auto-quant-112315-bybit_public`.
  - `ProviderCryptoMomentumStateV1`: trades `34`, profit_pct `1.48`, win_rate_pct `41.17647058823529`, profit_factor `1.288511226299377`.
  - `ProviderCryptoPullbackRevertV1`: trades `17`, profit_pct `-1.71`, win_rate_pct `23.52941176470588`, profit_factor `0.45016637432495576`.
- `tvr_binance`: rows `720`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T172214+0800-codex-board-a-provider-window-aware-same-root-aq-v1/workspace/auto-quant-112315-tvr_binance`.
  - `ProviderCryptoMomentumStateV1`: trades `10`, profit_pct `-0.65`, win_rate_pct `40.0`, profit_factor `0.6867694918857996`.
  - `ProviderCryptoPullbackRevertV1`: trades `6`, profit_pct `-0.83`, win_rate_pct `16.666666666666664`, profit_factor `0.40539240394914555`.
- `ibkr_aggtrades`: rows `6930`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T172214+0800-codex-board-a-provider-window-aware-same-root-aq-v1/workspace/auto-quant-112315-ibkr_aggtrades`.
  - `ProviderCryptoMomentumStateV1`: trades `276`, profit_pct `-21.68`, win_rate_pct `23.91304347826087`, profit_factor `0.5732222166410332`.
  - `ProviderCryptoPullbackRevertV1`: trades `150`, profit_pct `-4.66`, win_rate_pct `50.0`, profit_factor `0.8472423442015747`.

## Gate
- Same-root six-provider AQ authority: `True`.
- Successful provider AQ runs: `6/6`.
- Strategies with metrics: `12`.
- Total AQ trades: `1956`.
- Gate result: `172214_provider_window_aware_same_root_aq=same_root_provider_aq_present_downstream_not_started_no_promotion`.
- Downstream chain not started in this packet.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T172214+0800-codex-board-a-provider-window-aware-same-root-aq-v1/provider-window-aware-same-root-aq-v1/provider_window_aware_same_root_aq_v1.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T172214+0800-codex-board-a-provider-window-aware-same-root-aq-v1/provider-window-aware-same-root-aq-v1/prompt_to_artifact_checklist_provider_window_aware_same_root_aq_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T172214+0800-codex-board-a-provider-window-aware-same-root-aq-v1/checks/provider_window_aware_same_root_aq_v1_assertions.out`
- Provider CSVs: `docs/experiments/actionable-regime-confidence/runs/20260512T172214+0800-codex-board-a-provider-window-aware-same-root-aq-v1/provider-csv`
- AQ workspaces: `docs/experiments/actionable-regime-confidence/runs/20260512T172214+0800-codex-board-a-provider-window-aware-same-root-aq-v1/workspace`
