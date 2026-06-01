# IBKR cross-asset options-proxy Auto-Quant: offline parity refinement

Trigger
- User asks ICT-Engine/Auto-Quant to run profitability factors on IBKR-derived index futures, gold futures, or US stocks using volatility, gamma wall, IV, open interest, or Greeks signals.
- Cached IBKR/Freqtrade feather data exists, but Freqtrade backtesting attempts exchange market reload and fails on CCXT network/market metadata.

Core lesson
- Do not treat a CCXT market reload failure as strategy failure when local feather bars are present.
- Preserve the failure evidence, then run an offline parity evaluator over the cached feather rows to separate factor logic quality from exchange metadata connectivity.
- Append offline candidates to the same `strategy_library.json` only with explicit provenance and fail-closed promotion flags.

Workflow
1. Isolate a fresh run directory under `/tmp/<run>`; copy only cached data/config/strategy artifacts needed for this refinement.
2. Verify cached feathers exist, e.g. `user_data/data/ES_USD-5m.feather`, `GC_USD-5m.feather`, stock proxies.
3. If Freqtrade fails before backtest with `Could not load markets` / `api.binance.com` / `RequestTimeout`, record it as a market metadata blocker, not a signal verdict.
4. Build a small offline evaluator that:
   - reads feather rows sorted by timestamp/date,
   - recomputes the same indicators as the strategy,
   - simulates one position at a time with the strategy stop/ROI/exit rules,
   - reports trades, total profit %, win rate, profit factor, max drawdown, side counts, and sample trades.
5. Promotion gate for offline proxy candidates:
   - require `trades >= 10`,
   - require `profit_factor >= 1.2`,
   - require `max_drawdown_pct > -1.0`,
   - set `trade_usable=false` until broker-native OI/Greeks or normal backtest path verifies.
6. Append candidate entries to `strategy_library.json` with metadata fields:
   - `provider_provenance: ibkr_cached_feather`,
   - `data_scope`,
   - `true_oi_greeks_note`,
   - full regime branch path,
   - `promotion_allowed` boolean,
   - per-pair metrics.
7. Continue closure through Auto-Quant import / BBN prior / CatBoost / execution trace only after the candidate library has clear provenance and fail-closed flags.

Interpretation rules
- Volume/ATR/round-range gamma/OI/Greek proxies are acceptable for incubation, not live trading claims.
- Direct broker option chain OI/Greeks absence must be stated in `true_oi_greeks_note`.
- A high profit factor on few trades is a candidate for more timerange/assets, not a final strategy.
- Prefer splitting winners by asset/timeframe rather than promoting an aggregate packet that hides weak legs.

Example result pattern
- `EsGammaWallBreakout`: 12 trades, PF 3.6, DD < 0.2% -> promote to candidate library, `trade_usable=false`.
- `EsIvOlGreekReversal`: many trades but PF near 1.0 -> keep as weak/incubate, not primary.
