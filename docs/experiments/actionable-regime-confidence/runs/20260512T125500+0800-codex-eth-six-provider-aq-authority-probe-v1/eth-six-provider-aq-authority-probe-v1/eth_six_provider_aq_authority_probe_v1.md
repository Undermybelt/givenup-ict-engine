# ETH Six-Provider AQ Authority Probe v1

Run id: `20260512T125500+0800-codex-eth-six-provider-aq-authority-probe-v1`

## Scope
Provider-provenanced ETH 1h matrix across TradingViewRemix/TVR, yfinance/YF, Kraken, Binance, Bybit, and IBKR PAXOS, followed by isolated Auto-Quant/TOMAC execution per provider when enough 1h rows exist.
This does not modify ict-engine runtime code, production BBN CPDs, production CatBoost/path-ranker state, or execution-tree gates.

## Provider Matrix
- `tradingview_mcp` / `tvr_eth_usd_1h`: exit `0`, rows `708`, first `2026-04-12T05:00:00Z`, last `2026-05-12T04:58:50Z`.
- `yfinance` / `yfinance_eth_usd_1h`: exit `1`, rows `0`, first `None`, last `None`.
- `kraken` / `kraken_ethusd_1h`: exit `0`, rows `721`, first `2026-04-12T05:00:00Z`, last `2026-05-12T05:00:00Z`.
- `binance` / `binance_ethusdt_1h`: exit `0`, rows `990`, first `2026-04-01T00:00:00Z`, last `2026-05-12T05:00:00Z`.
- `bybit` / `bybit_ethusdt_linear_1h`: exit `0`, rows `990`, first `2026-04-01T00:00:00Z`, last `2026-05-12T05:00:00Z`.
- `ibkr` / `ibkr_eth_paxos_aggtrades_1h`: exit `0`, rows `784`, first `2026-03-31 16:01:00-04:00`, last `2026-05-12 01:00:00-04:00`.

## AQ Results
- `tradingview_mcp`: rows `708`, compile exit `0`, TOMAC exit `0`, real_trade_rows `19`.
  - ProviderCryptoMomentumStateV1: trades=14 profit_pct=0.88 sharpe=1.4401270367771482 pf=1.4235383800476185
  - ProviderCryptoPullbackRevertV1: trades=5 profit_pct=-1.3 sharpe=-2.3770608113074574 pf=0.2084833870690368
- `yfinance`: rows `0`, compile exit `None`, TOMAC exit `None`, real_trade_rows `0`.
  - skipped: provider_rows_below_120_or_missing_csv
- `kraken`: rows `721`, compile exit `0`, TOMAC exit `0`, real_trade_rows `34`.
  - ProviderCryptoMomentumStateV1: trades=20 profit_pct=0.31 sharpe=0.5593725027192263 pf=1.0986393316703826
  - ProviderCryptoPullbackRevertV1: trades=14 profit_pct=-2.52 sharpe=-5.997652729406005 pf=0.2889546244656568
- `binance`: rows `990`, compile exit `0`, TOMAC exit `0`, real_trade_rows `54`.
  - ProviderCryptoMomentumStateV1: trades=34 profit_pct=1.6 sharpe=1.602132735541575 pf=1.2727521145789806
  - ProviderCryptoPullbackRevertV1: trades=20 profit_pct=-3.41 sharpe=-4.90788934576029 pf=0.3438922381605806
- `bybit`: rows `990`, compile exit `0`, TOMAC exit `0`, real_trade_rows `53`.
  - ProviderCryptoMomentumStateV1: trades=34 profit_pct=1.62 sharpe=1.6059422609111882 pf=1.2731908285700428
  - ProviderCryptoPullbackRevertV1: trades=19 profit_pct=-3.45 sharpe=-4.817452087414439 pf=0.34268285102471957
- `ibkr`: rows `784`, compile exit `0`, TOMAC exit `0`, real_trade_rows `46`.
  - ProviderCryptoMomentumStateV1: trades=32 profit_pct=1.19 sharpe=1.0758916953973414 pf=1.1810934260535257
  - ProviderCryptoPullbackRevertV1: trades=14 profit_pct=-1.54 sharpe=-2.069065100008619 pf=0.5245622776678557

## Decision
- Gate result: `eth_six_provider_aq_authority_probe=provider_rows_and_aq_nonzero_incubation_but_no_mature_rooted_calibration_or_execution_promotion`.
- Providers with raw rows: `5/6`.
- Providers with AQ execution: `5/6`.
- Nonzero AQ trade providers: `5/6`.
- This is provider-authority incubation evidence only. It does not supply calibrated mature rooted observations, accepted `>=95%` regime context, or execution-tree non-observe release.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T125500+0800-codex-eth-six-provider-aq-authority-probe-v1/eth-six-provider-aq-authority-probe-v1/eth_six_provider_aq_authority_probe_v1.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T125500+0800-codex-eth-six-provider-aq-authority-probe-v1/eth-six-provider-aq-authority-probe-v1/prompt_to_artifact_checklist_eth_six_provider_aq_authority_probe_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T125500+0800-codex-eth-six-provider-aq-authority-probe-v1/checks/eth_six_provider_aq_authority_probe_v1_assertions.out`
- Provider CSVs: `docs/experiments/actionable-regime-confidence/runs/20260512T125500+0800-codex-eth-six-provider-aq-authority-probe-v1/provider-csv`
- AQ workspaces: `docs/experiments/actionable-regime-confidence/runs/20260512T125500+0800-codex-eth-six-provider-aq-authority-probe-v1/workspace`
