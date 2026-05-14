# Per-Regime Factor Supply Map

Run ID: `20260511T121643+0800-codex-per-regime-factor-supply-map`

This map answers the narrower factor-supply question: every active `MainRegimeV2` regime now has an explicit accepted 95% scoped factor/evidence packet. It does not claim full-market/full-timeframe completion.

| Regime | Factor | Evidence | Gate | Scope | Consumer Use |
|---|---|---|---|---|---|
| `Bull` | `bull_sourcebacked_drawdown_volatility_v1` | `source_backed_scope_limited_parent_root_factor` | cal/test `0.952516` / `0.961931` | index, single_stock; 1d, 1w | allow_or_size_up_bull_continuation_candidates_inside_supported_scope |
| `Bear` | `bear_sourcebacked_drawdown_return_ratio_v1` | `source_backed_scope_limited_parent_root_factor` | cal/test `0.993968` / `0.992722` | crypto, equity_etf; 1d, 1w | allow_or_size_up_bear_defensive_or_short_bias_candidates_inside_supported_scope |
| `Sideways` | `sideways_sourcebacked_abs_return_range_v1` | `source_backed_scope_limited_parent_root_factor` | cal/test `0.988647` / `0.995568` | crypto, equity_etf; 1d, 1w | allow_mean_reversion_or_range_candidates_inside_supported_scope |
| `Crisis` | `crisis_range_ratio_intraday_v1` | `scope_limited_parent_root_factor` | cal/test `0.996248` / `0.995981` | CME_futures_local, IBKR_US_ETF, Kraken_crypto, yfinance_crypto, yfinance_futures; 15m, 1h | suppress_risk_or_size_down_execution_inside_supported_scope |
| `Manipulation` | `manipulation_telegram_pump_event_v1` | `direct_social_event_factor` | cal/test `0.999735` / `0.999701` | crypto_telegram_event, same_coin_non_event_controls; event_window | suppress_entry_or_route_to_abstain_cooldown_on_direct_event |
| `Manipulation` | `manipulation_multichain_wash_maker_v1` | `direct_onchain_order_lifecycle_wash_factor` | cal/test `0.967945` / `0.967945` | base, bsc, ethereum, solana; maker_token_day | suppress_or_abstain_on_direct_wash_maker_evidence |

## Guardrails

- These are scoped factors, not full-universe completion.
- The six older accepted subtype packets remain `sub_regime_evidence_only` and are not promoted here.
- `Manipulation` uses direct social/event and direct wash-maker evidence only; OHLCV/session/liquidity proxies remain rejected.
- Full completion still requires exact provider/instrument/timeframe labels or an owner-approved crosswalk for the missing matrix.

## Decision

- Per-regime scoped factor supply achieved: `true`.
- Full objective achieved: `false`.
- Gate result: `per_regime_scoped_factor_supply_mapped_full_matrix_still_blocked`.
