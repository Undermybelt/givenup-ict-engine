# Feasible-Window Same-Root AQ Packet v1

Run id: `20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1`

## Scope
Copies repaired provider-window CSVs into one run root and runs same-root AQ/TOMAC. No provider refetch and no downstream ict-engine gates.

## Provider Inputs
- `yfinance` (yfinance/YF): copied `True`, rows `17291`, first `2024-05-15 00:00:00+00:00`, last `2026-05-11 23:00:00+00:00`, window `2024-05-15_to_2026-05-12_730d_cap`.
- `ibkr_aggtrades` (IBKR): copied `True`, rows `6930`, first `2025-05-12T20:01:00+00:00`, last `2026-05-12T09:00:00+00:00`, window `2025-05-12_to_2026-05-12_1y_client144`.
- `kraken_public` (Kraken): copied `True`, rows `1993`, first `2026-02-18 00:00:00+00:00`, last `2026-05-12 00:00:00+00:00`, window `2026-02-18_to_2026-05-12_current_window`.
- `binance_public` (Binance): copied `True`, rows `46955`, first `2021-01-01 00:00:00+00:00`, last `2026-05-12 00:00:00+00:00`, window `2021-01-01_to_2026-05-12_broad_window`.
- `bybit_public` (Bybit): copied `True`, rows `1000`, first `2026-03-31 09:00:00+00:00`, last `2026-05-12 00:00:00+00:00`, window `2026-03-31_to_2026-05-12_capped_current`.
- `tvr_local_stdio` (TradingViewRemix/TVR): copied `True`, rows `720`, first `2026-04-12T09:00:00Z`, last `2026-05-12T08:59:51Z`, window `2026-04-12_to_2026-05-12_default_local_stdio`.

## AQ Results
- `yfinance`: rows `17291`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1/workspace/auto-quant-112315-yfinance`.
  - `ProviderCryptoMomentumStateV1`: trades `317`, profit_pct `-25.17`, win_rate_pct `23.974763406940063`, profit_factor `0.6030737112508623`.
  - `ProviderCryptoPullbackRevertV1`: trades `145`, profit_pct `4.75`, win_rate_pct `46.89655172413793`, profit_factor `1.2059353117408125`.
- `ibkr_aggtrades`: rows `6930`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1/workspace/auto-quant-112315-ibkr_aggtrades`.
  - `ProviderCryptoMomentumStateV1`: trades `276`, profit_pct `-21.68`, win_rate_pct `23.91304347826087`, profit_factor `0.5732222166410332`.
  - `ProviderCryptoPullbackRevertV1`: trades `150`, profit_pct `-4.66`, win_rate_pct `50.0`, profit_factor `0.8472423442015747`.
- `kraken_public`: rows `1993`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1/workspace/auto-quant-112315-kraken_public`.
  - `ProviderCryptoMomentumStateV1`: trades `76`, profit_pct `-3.48`, win_rate_pct `31.57894736842105`, profit_factor `0.7440064020125409`.
  - `ProviderCryptoPullbackRevertV1`: trades `30`, profit_pct `-2.25`, win_rate_pct `33.33333333333333`, profit_factor `0.611492759978`.
- `binance_public`: rows `46955`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1/workspace/auto-quant-112315-binance_public`.
  - `ProviderCryptoMomentumStateV1`: trades `624`, profit_pct `-43.34`, win_rate_pct `23.076923076923077`, profit_factor `0.5637237561972133`.
  - `ProviderCryptoPullbackRevertV1`: trades `268`, profit_pct `-13.25`, win_rate_pct `38.43283582089552`, profit_factor `0.7389778890096554`.
- `bybit_public`: rows `1000`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1/workspace/auto-quant-112315-bybit_public`.
  - `ProviderCryptoMomentumStateV1`: trades `34`, profit_pct `1.48`, win_rate_pct `41.17647058823529`, profit_factor `1.288511226299377`.
  - `ProviderCryptoPullbackRevertV1`: trades `17`, profit_pct `-1.71`, win_rate_pct `23.52941176470588`, profit_factor `0.45016637432495576`.
- `tvr_local_stdio`: rows `720`, compile exit `0`, TOMAC exit `0`, workspace `docs/experiments/actionable-regime-confidence/runs/20260512T172142+0800-codex-board-a-feasible-window-same-root-aq-packet-v1/workspace/auto-quant-112315-tvr_local_stdio`.
  - `ProviderCryptoMomentumStateV1`: trades `10`, profit_pct `-0.65`, win_rate_pct `40.0`, profit_factor `0.6867694918857996`.
  - `ProviderCryptoPullbackRevertV1`: trades `6`, profit_pct `-0.83`, win_rate_pct `16.666666666666664`, profit_factor `0.40539240394914555`.

## Gate
- Same-root six-provider AQ authority: `True`.
- AQ run success: `6/6`.
- Strategies with metrics: `12`.
- Total trades: `1953`.
- Positive-profit metric count: `2`.
- Workspace file count: `168`.
- Derived metric count: `24`.
- Old-root reference count: `0`.
- downstream_started=false.
- promotion_allowed=false.
- trade_usable=false.
- update_goal=false.
