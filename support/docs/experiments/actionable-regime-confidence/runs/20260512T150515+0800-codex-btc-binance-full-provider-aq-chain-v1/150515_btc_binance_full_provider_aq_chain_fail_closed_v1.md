# 150515 BTC Binance Full Provider AQ Chain Fail-Closed v1

Run root:
`docs/experiments/actionable-regime-confidence/runs/20260512T150515+0800-codex-btc-binance-full-provider-aq-chain-v1`

Source:
- Primary AQ provider lane: Binance BTCUSDT 1h full listing from the `143900` normalized provider data.
- State symbol: `B2R_BTC_BINANCE_FULL_MOMENTUM_150515`.
- Strategies: `ProviderCryptoMomentumStateV1` and `ProviderCryptoPullbackRevertV1`.

Command exits:
- `01_auto_quant_compile.exit=0`
- `02_auto_quant_run_tomac_binance_full.exit=0`
- `03_ingest_real_trades.exit=0`
- `04_analyze_binance_full.exit` is absent.

Readback:
- `04_analyze_binance_full.cmd` was written, but no corresponding stdout, stderr, or exit file exists.
- No `150515` process was active at readback, so the downstream analyze leg is incomplete rather than in-flight.
- Provider provenance matrix contains six provider rows, but only Binance was `used_for_current_aq=True`. IBKR, TVR, YF, Kraken, and Bybit were retained as context/provenance rows from prior roots and were not used by the current full-listing AQ run.
- `ProviderCryptoMomentumStateV1` produced `2758` real-trade rows with win rate `26.6860%`, PF `0.6725`, Sharpe `-1.9852`, max drawdown `-90.3853%`, and total profit `-89.97%`.
- `ProviderCryptoPullbackRevertV1` produced `1353` real-trade rows with win rate `39.6896%`, PF `0.6078`, Sharpe `-1.3369`, max drawdown `-74.4434%`, and total profit `-74.31%`.
- `ProviderCryptoMomentumStateV1.real_trades.normalized.jsonl` contains `2758` rows and was ingested before the missing analyze leg.

Acceptance decision:
- This is negative AQ full-listing evidence for Binance BTCUSDT only.
- It does not satisfy same-root six-provider AQ authority because only Binance was used for the current AQ run.
- It does not complete the ordered downstream chain because analyze did not produce an exit/readback, and there is no Pre-Bayes, BBN, CatBoost/path-ranker, calibrated lower-bound, or execution-tree admission readback for this root.
- The AQ strategy results are strongly negative and not promotable.
- Board A remains fail-closed: accepted `>=95%` contexts `0`, `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false`.
