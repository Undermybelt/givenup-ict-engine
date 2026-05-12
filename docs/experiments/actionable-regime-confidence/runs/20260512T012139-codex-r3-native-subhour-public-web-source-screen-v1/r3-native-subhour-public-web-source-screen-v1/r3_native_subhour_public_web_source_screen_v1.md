# R3 Native Sub-hour Public Web Source Screen v1

- Decision: `r3_native_subhour_public_web_source_screen_v1=no_ready_source_owned_native_subhour_rows_found`.
- Scope: AAPL and IXIC native 15m/30m source-owned regime-label rows after `2026-01-30`.
- Ready public source-native sub-hour exports found: `0`.
- Required intake root: `/tmp/ict-engine-native-subhour-source-label-intake`.
- Required files present: rows `False`, provenance `False`.
- Accepted rows added: `0`; canonical merge allowed: `false`; downstream chain rerun allowed: `false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; raw data downloaded: `false`; trade usable: `false`.

## Focus Cells

| Symbol | Timeframe | Required After | Public Source Rows Found | Blocker |
|---|---|---|---|---|
| `AAPL` | `15m` | `2026-01-30` | `false` | `no_ready_source_owned_native_subhour_label_export_after_public_web_screen` |
| `AAPL` | `30m` | `2026-01-30` | `false` | `no_ready_source_owned_native_subhour_label_export_after_public_web_screen` |
| `^IXIC` | `15m` | `2026-01-30` | `false` | `no_ready_source_owned_native_subhour_label_export_after_public_web_screen` |
| `^IXIC` | `30m` | `2026-01-30` | `false` | `no_ready_source_owned_native_subhour_label_export_after_public_web_screen` |

## Public Search Readback

| Query | Surface | Assessment |
|---|---|---|
| `AAPL 15 minute regime label dataset source confidence 2026` | [Kaggle: Stock Market Regimes 2000-2026](https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026) | `daily_source_panel_not_native_subhour_after_2026_01_30` |
| `site:kaggle.com/datasets AAPL intraday 15 minute data regime label` | [Kaggle dataset search: AAPL intraday regime label](https://www.kaggle.com/search?q=AAPL+intraday+15+minute+regime+label+in%3Adatasets) | `ohlcv_or_search_surface_only_no_source_label_rows` |
| `site:kaggle.com/datasets "AAPL" "15m" "regime"` | [Kaggle dataset search: AAPL 15m regime](https://www.kaggle.com/search?q=%22AAPL%22+%2215m%22+%22regime%22+in%3Adatasets) | `no_ready_source_owned_native_subhour_label_export` |
| `site:kaggle.com/datasets "IXIC" "15m" "regime"` | [Kaggle dataset search: IXIC 15m regime](https://www.kaggle.com/search?q=%22IXIC%22+%2215m%22+%22regime%22+in%3Adatasets) | `no_ready_source_owned_native_subhour_label_export` |
| `NASDAQ Composite IXIC 15m 30m regime labels dataset` | [Nasdaq Data Link contact](https://data.nasdaq.com/contact) | `contact_route_only_rows_not_acquired` |
| `NASDAQ Composite IXIC 15m 30m regime labels dataset` | [Nasdaq Indexes contact](https://indexes.nasdaq.com/contactus) | `contact_route_only_rows_not_acquired` |
| `Yahoo Finance intraday provenance AAPL 15m labels` | [Yahoo Finance Help](https://help.yahoo.com/kb/finance-for-web) | `provider_bars_not_source_labels` |

## Boundary

This packet records public search and contact-route evidence only. It does not treat OHLCV bars, provider help pages, search result pages, or vendor contact routes as source-owned native sub-hour regime labels. It does not create the R3 intake root or authorize provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree promotion.
