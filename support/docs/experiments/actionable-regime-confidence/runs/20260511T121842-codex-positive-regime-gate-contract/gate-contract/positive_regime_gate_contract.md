# Positive Regime Gate Contract

Run ID: `20260511T121842+0800-codex-positive-regime-gate-contract`

This is the positive contract: every active regime has at least one verified 95% scoped gate with an existing source artifact. It does not claim full-matrix completion.

| Regime | Gate | Cal LCB | Test LCB | Scope | Consumer Action |
|---|---|---:|---:|---|---|
| `Bull` | `bull_sourcebacked_drawdown_volatility_v1` | `0.952516` | `0.961931` | index, single_stock; 1d, 1w | allow_or_size_up_bull_continuation_inside_supported_scope |
| `Bear` | `bear_sourcebacked_drawdown_return_ratio_v1` | `0.993968` | `0.992722` | crypto, equity_etf; 1d, 1w | allow_bear_defensive_or_short_bias_inside_supported_scope |
| `Sideways` | `sideways_sourcebacked_abs_return_range_v1` | `0.988647` | `0.995568` | crypto, equity_etf; 1d, 1w | allow_mean_reversion_or_range_logic_inside_supported_scope |
| `Crisis` | `crisis_range_ratio_intraday_v1` | `0.996248` | `0.995981` | CME_futures_local, IBKR_US_ETF, Kraken_crypto, yfinance_crypto, yfinance_futures; 15m, 1h | suppress_risk_or_size_down_execution_inside_supported_scope |
| `Manipulation` | `manipulation_telegram_pump_event_v1` | `0.999735` | `0.999701` | crypto_telegram_event, same_coin_non_event_controls; event_window | suppress_entry_or_route_to_abstain_cooldown_on_direct_event |
| `Manipulation` | `manipulation_multichain_wash_maker_v1` | `0.967945` | `0.967945` | base, bsc, ethereum, solana; maker_token_day | suppress_or_abstain_on_direct_wash_maker_evidence |

## Decision

- Positive scoped gate contract ready: `true`.
- Missing regimes: `[]`.
- Broken source artifact refs: `[]`.
- Full objective achieved: `false`.
- Gate result: `positive_scoped_regime_gate_contract_ready_full_matrix_still_blocked`.

## Guardrails

- Use only inside each gate's supported context/timeframe scope.
- Keep `Manipulation` direct-event/direct-onchain only; no OHLCV proxy promotion.
- Full-market/full-timeframe completion still needs targeted matrix expansion or an owner-approved crosswalk.
