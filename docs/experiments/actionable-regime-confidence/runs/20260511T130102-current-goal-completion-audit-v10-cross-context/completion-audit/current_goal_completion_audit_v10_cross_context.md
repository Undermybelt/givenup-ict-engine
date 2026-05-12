# Current Goal Completion Audit v10: Cross-Context

Run ID: `20260511T130102+0800-current-goal-completion-audit-v10-cross-context`

## Objective Restatement

- Every active `MainRegimeV2` price root needs 95% confidence.
- The evidence must survive other markets/contexts and other timeframes.
- Child/sub-regime packets must not complete parent roots.
- `Manipulation` remains separate direct evidence.
- Full objective completion requires the expanded full-market/full-timeframe/full-species gate, not just scoped evidence.

## Price Root Matrix

| Root | Parent 95 Gate | Stock Min LCB | Contexts | Timeframes | Supply Min LCB | Scoped Cross-Context |
|---|---|---:|---|---|---:|---|
| `Bull` | `True` | 0.979723 | index, single_stock | 1d, 1w | 0.952516 | `accepted_scoped` |
| `Bear` | `True` | 0.963920 | crypto, equity_etf | 1d, 1w | 0.992722 | `accepted_scoped` |
| `Sideways` | `True` | 0.993711 | crypto, equity_etf | 1d, 1w | 0.988647 | `accepted_scoped` |
| `Crisis` | `True` | 0.961906 | CME_futures_local, IBKR_US_ETF, Kraken_crypto, yfinance_crypto, yfinance_futures | 15m, 1h | 0.995981 | `accepted_scoped` |

## Checklist

- `pass`: Every active MainRegimeV2 price root has a direct parent-root 95% confidence gate. Evidence: `docs/experiments/actionable-regime-confidence/runs/20260511T125122-codex-stock-market-regimes-parent-root-abstain/parent-root-abstain/stock_market_regimes_parent_root_abstain.json`. Uses stock-market-regimes parent labels; all roots target Bull/Bear/Sideways/Crisis directly.
- `pass`: Accepted gates are not child/sub-regime packets. Evidence: `docs/experiments/actionable-regime-confidence/runs/20260511T125122-codex-stock-market-regimes-parent-root-abstain/parent-root-abstain/stock_market_regimes_parent_root_abstain.json`. Checks taxonomy_role for all four stock-panel gates.
- `pass`: Each price root has scoped validation on more than one market/context and more than one timeframe. Evidence: `docs/experiments/actionable-regime-confidence/runs/20260511T121643-codex-per-regime-factor-supply-map/factor-supply/per_regime_factor_supply_map.json`. This is a scoped floor, not the expanded full-matrix objective.
- `pass`: Unsupported full-market/full-timeframe cells are not treated as complete. Evidence: `docs/experiments/actionable-regime-confidence/runs/20260511T124107-codex-source-window-slot-calibration-v1/source-window-slot-calibration/source_window_slot_calibration_v1.json`. Source-window slot calibration accepted 0 crosswalk slots and remains blocked.
- `pass`: Manipulation is direct evidence only and not represented by OHLCV proxy price roots. Evidence: `docs/experiments/actionable-regime-confidence/runs/20260511T121643-codex-per-regime-factor-supply-map/factor-supply/per_regime_factor_supply_map.json`. Direct social/event and direct on-chain wash-maker slices are present, but full variety coverage is not complete.
- `pass`: Do not call the active goal complete unless the full objective gate is closed. Evidence: `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`. Board still records full objective gate as none.

## Decision

- Scoped cross-market/timeframe price roots pass: `true`.
- Full objective achieved: `false`.
- `update_goal`: `false`.
- Gate result: `scoped_cross_context_price_roots_pass_full_matrix_still_blocked`.

## Remaining Blockers

- Expanded full-market/full-timeframe/full-species matrix remains incomplete.
- Source-window slot calibration accepted 0 crosswalk slots for monthly S&P-linked Bull/Bear/Crisis cells.
- The stock-market-regimes parent-root panel is daily US equities/indices only.
- Sideways stock-panel gate depends on the source regime_confidence field.
- Manipulation direct evidence remains scoped to known social/event and wash-maker varieties, not full spoofing/layering/quote-stuffing/order-book coverage.
