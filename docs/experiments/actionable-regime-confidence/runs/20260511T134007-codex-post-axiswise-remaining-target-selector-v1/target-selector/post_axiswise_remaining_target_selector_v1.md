# Post-Axiswise Remaining Target Selector v1

Run ID: `20260511T134007+0800-codex-post-axiswise-remaining-target-selector-v1`

This selector starts after the `131922` axiswise gate: same-source `1w/1mo` MainRegimeV2 cells are already closed. It chooses the next unsupported slice without reopening closed monthly/weekly work.

## Already Closed

- Daily parent roots accepted 95: `true`.
- Same-source weekly/monthly cells accepted 95: `true`.
- Axiswise gate result: `accepted_95_source_consensus_axiswise_8of8_same_source_timeframe_cells_full_matrix_still_blocked`.
- Monthly Sideways support probe: `pure_month_1_00_two_axis_validation_split`.

## Remaining Missing-Slot Shape

- Missing/requested root-label rows from v3 package: `564`.
- By provider: `{'kraken_public_lowpollution_http': 108, 'yfinance': 456}`.
- By timeframe: `{'15m': 68, '1d': 44, '1h': 68, '1m': 68, '1mo': 68, '1w': 44, '30m': 68, '4h': 68, '5m': 68}`.
- By root: `{'Bear': 141, 'Bull': 141, 'Crisis': 141, 'Sideways': 141}`.
- By reason: `{'missing_instrument_source_label': 40, 'missing_intraday_or_monthly_source_label': 392, 'missing_non_yfinance_source_label': 108, 'rejected_near_underlying_proxy_not_accepted': 24}`.

## Provider Reality Check

- `tradingview_mcp` is ready for OHLCV, but the repo allowlist exposes `get_ohlcv`, `yahoo_price`, `get_option_expirations`, and `get_option_chain` only.
- Therefore TradingViewRemix, Yahoo, IBKR, Kraken, and local HMM outputs can help with bar overlap or later validation, but cannot by themselves close independent root-label requirements.
- Do not count OHLCV, HMM/GMM state ids, strategy predictions, or future-return labels as completion evidence.

## Selected Next Target

| Rank | Request | Target | Next Small Action |
|---:|---|---|---|
| 1 | `v4-price-root-exact-label-panel` | Exact provider/instrument/timeframe MainRegimeV2 labels | Obtain or point to a dated independent label panel for one high-liquidity slice such as SPY/QQQ/^GSPC/^NDX/ES/NQ 15m/1h/4h or Kraken XBTUSD/ETHUSD 1d/1w/1mo, then run chronological calibration/test. |
| 2 | `v4-direct-manipulation-variety-rows` | Direct Manipulation positives/negatives across more varieties | Export replayable spoofing/layering or quote-stuffing positive rows with matched same-venue/same-period negative controls; keep raw rows outside the repo and commit only compact evidence. |
| 3 | `v4-historical-source-window-bar-overlap` | Historical bar overlap for approved source-window labels | Use provider bars only after source windows are approved for exact instrument/provider/timeframe routing. |

## Decision

- Selected next target: `v4-price-root-exact-label-panel`.
- Fallback target: `v4-direct-manipulation-variety-rows`.
- Full objective achieved: `false`.
- `update_goal`: `false`.
- Gate result: `post_axiswise_remaining_targets_selected_full_matrix_still_blocked`.

## Guardrails

- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.
