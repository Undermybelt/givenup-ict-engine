# Source Label Cross-Timeframe Public Source Screen v1

- Decision: `source_label_cross_timeframe_public_source_screen_v1=no_ready_source_owned_cross_timeframe_labels_found`.
- Current cursor: `20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1`.
- Condition input: `source_label_bull_sideways_qualifying_condition_v1=conditions_drafted_cross_market_period_ok_timeframe_r6_baseline_blocked_no_acceptance`.
- Ready public cross-timeframe source-label exports found: `0`.
- R3/R5/R6 roots present: `False` / `False` / `False`.
- Accepted rows added: `0`; new confidence gate: `false`; canonical merge allowed: `false`; downstream chain rerun allowed: `false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; raw data downloaded: `false`; trade usable: `false`.

## Current Condition Timeframes

| Label | Timeframe Count | Multi-Timeframe Pass | Blockers |
|---|---:|---|---|
| `Bull` | `1` | `false` | `multi_timeframe_support_absent_only_1d;baseline_source_label_calibration_still_no_acceptance;r6_owner_control_blocker_still_active;canonical_merge_not_allowed` |
| `Sideways` | `1` | `false` | `multi_timeframe_support_absent_only_1d;baseline_source_label_calibration_still_no_acceptance;r6_owner_control_blocker_still_active;canonical_merge_not_allowed` |

## Public Source Screen

| Query | Surface | Assessment |
|---|---|---|
| `"market regime" intraday dataset "15 minute" labels` | [Kaggle dataset search](https://www.kaggle.com/search?q=%22market+regime%22+intraday+%2215+minute%22+labels+in%3Adatasets) | `dataset_search_no_ready_source_owned_native_label_rows` |
| `"stock market regimes" intraday "regime_confidence"` | [Kaggle regime-confidence search](https://www.kaggle.com/search?q=%22stock+market+regimes%22+intraday+%22regime_confidence%22+in%3Adatasets) | `daily_source_panel_only_no_intraday_confidence_extension` |
| `"regime labels" "15m" stock dataset` | [Hugging Face dataset search](https://huggingface.co/datasets?search=regime%20labels%2015m%20stock) | `generated_or_unverified_label_surface_not_board_a_source_owned` |
| `"market regime" "30m" "source confidence" dataset` | [Nasdaq Data Link search/contact route](https://data.nasdaq.com/search?query=market%20regime%2030m%20source%20confidence) | `vendor_route_only_rows_not_acquired` |
| `TradingView market regime 15m labels source-owned dataset` | [TradingView script search](https://www.tradingview.com/scripts/search/market%20regime/) | `indicator_script_not_source_owned_label_export` |

## Boundary

This packet is an acquisition screen only. It does not accept TradingView indicators, provider bars, generated labels, search-result pages, or vendor contact routes as source-owned cross-timeframe regime labels. It does not authorize canonical merge or downstream promotion.
