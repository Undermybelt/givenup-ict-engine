# Native Sub-hour Contact Leads v1

Run ID: `20260511T203505-codex-native-subhour-contact-leads-v1`

- Gate result: `native_subhour_contact_leads_v1=public_contact_paths_ready_rows_not_acquired`.
- Purpose: convert the R3 native sub-hour intake request into public contact/licensing leads without accepting proxy labels.
- Prior native request rows: `336`.
- Focus blocker cells: `4`.
- Contact leads recorded: `9`.
- URL probes ok: `7`; blocked/error probes: `2`.
- Request sent: `false`; rows acquired: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Lead Type Coverage

| Lead Type | Leads |
|---|---:|
| `exchange_contact_route` | `1` |
| `futures_market_data_contact_route` | `1` |
| `index_owner_contact_route` | `1` |
| `market_data_vendor_contact_route` | `2` |
| `provider_terms_contact_route` | `2` |
| `source_label_owner_extension` | `1` |
| `source_label_owner_identity_route` | `1` |

## Contact Leads

- `kaggle_stock_regime_owner_discussion_intraday_extension` / `source_label_owner_extension`: Kaggle stock-regime dataset discussion/comments route (https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026/discussion) -> `ready_public_surface_no_rows_acquired`, probe `ok_get_fallback` `200`. Ask the existing source-label owner whether native 1m/5m/15m/30m/1h/4h regime-label exports exist or can be approved.
- `kaggle_stock_regime_owner_profile_intraday_extension` / `source_label_owner_identity_route`: Kaggle owner profile for the source-label dataset (https://www.kaggle.com/mafaqbhatti) -> `ready_public_surface_no_rows_acquired`, probe `ok_get_fallback` `200`. Owner identity route for the R3 native sub-hour source-label request.
- `yahoo_finance_help_surface` / `provider_terms_contact_route`: Yahoo Finance help surface (https://help.yahoo.com/kb/finance-for-web) -> `provider_data_surface_not_label_rows`, probe `ok` `200`. Clarify source provenance/licensing for yfinance-visible intraday panels; not accepted as regime labels by itself.
- `yahoo_terms_surface` / `provider_terms_contact_route`: Yahoo terms/legal surface (https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html) -> `provider_terms_surface_not_label_rows`, probe `ok` `200`. Terms/provenance route for Yahoo-origin intraday data; cannot close R3 without source-native labels.
- `nasdaq_data_link_contact` / `market_data_vendor_contact_route`: Nasdaq Data Link contact/support route (https://data.nasdaq.com/contact) -> `public_contact_surface_no_rows_acquired`, probe `blocked_or_error` ``. Potential route for index/ETF/futures intraday labeled data licensing or source-native regime-label availability.
- `nasdaq_indexes_contact` / `index_owner_contact_route`: Nasdaq indexes contact route (https://indexes.nasdaq.com/contactus) -> `public_contact_surface_no_rows_acquired`, probe `ok` `200`. Ask for index-family intraday source/equivalence approval; not a label source unless source-native labels are provided.
- `cme_market_data_contacts` / `futures_market_data_contact_route`: CME Group tools/contact list (https://www.cmegroup.com/tools-information/contacts-list.html) -> `public_contact_surface_no_rows_acquired`, probe `blocked_or_error` ``. Potential route for CL/ES/NQ intraday futures source data and any source-native label or provenance approval.
- `cboe_contact` / `exchange_contact_route`: Cboe contact route (https://www.cboe.com/contact/) -> `public_contact_surface_no_rows_acquired`, probe `ok` `200`. Potential route for exchange-native intraday context; cannot close R3 without owner-approved regime-label rows.
- `polygon_contact` / `market_data_vendor_contact_route`: Polygon.io contact route (https://polygon.io/contact) -> `vendor_data_surface_not_label_rows`, probe `ok` `200`. Potential market-data licensing route for intraday panels; not accepted as source-native regime labels by itself.

## Boundary

This run does not send a request, download rows, or create `/tmp/ict-engine-native-subhour-source-label-intake` files. R3 remains blocked until owner-approved or source-native sub-hour labels plus provenance pass the native-subhour intake contract. Provider OHLCV, yfinance-visible bars, generated HMM/KMeans labels, future-return labels, and daily/monthly projections remain rejected.

## Artifacts

- JSON: `native_subhour_contact_leads_v1.json`
- Contact CSV: `native_subhour_contact_leads_v1.csv`
- Assertions: `../checks/native_subhour_contact_leads_v1_assertions.out`
