# Source Label Equivalence Contact Leads v1

Run ID: `20260511T202712-codex-source-label-equivalence-contact-leads-v1`

- Gate result: `source_label_equivalence_contact_leads_v1=public_contact_paths_ready_rows_not_acquired`.
- Purpose: convert the R2 source-label equivalence request into concrete public contact/licensing leads without promoting proxy data.
- Contact leads recorded: `9`.
- URL probes ok: `6`; blocked/error probes: `3`.
- Request sent: `false`; rows acquired: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Package Coverage

| Package | Leads |
|---|---:|
| `price_root_equivalence_crypto` | `2` |
| `price_root_equivalence_fx_rates_commodities` | `1` |
| `price_root_equivalence_us_index_futures` | `6` |

## Contact Leads

- `kaggle_stock_regime_owner_discussion` / `price_root_equivalence_us_index_futures`: Kaggle stock-regime dataset discussion/comments route (https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026/discussion) -> `ready_public_surface_no_rows_acquired`, probe `ok_get_fallback` `200`. Request owner-approved equivalence policy or source-native rows for QQQ/NQ/NDX/futures extensions.
- `kaggle_stock_regime_owner_profile` / `price_root_equivalence_us_index_futures`: Kaggle owner profile for stock-market-regimes source labels (https://www.kaggle.com/mafaqbhatti) -> `ready_public_surface_no_rows_acquired`, probe `ok_get_fallback` `200`. Owner identity route for the R2 source-label equivalence request.
- `nasdaq_indexes_contact` / `price_root_equivalence_us_index_futures`: Nasdaq indexes contact page (https://indexes.nasdaq.com/contactus) -> `public_contact_surface_no_rows_acquired`, probe `ok` `200`. Ask whether Nasdaq-100/NDX equivalence policy or source-native index label documentation can be approved for QQQ/NQ/NDX use.
- `nasdaq_global_indexes_licensing` / `price_root_equivalence_us_index_futures`: Nasdaq global indexes licensing and ETPs page (https://www.nasdaq.com/solutions/global-indexes/licensing-and-etps) -> `public_licensing_surface_no_rows_acquired`, probe `ok` `200`. Index licensing route for explicit crosswalk/equivalence approval, not a label source by itself.
- `sp_dji_contact` / `price_root_equivalence_us_index_futures`: S&P Dow Jones Indices contact page (https://www.spglobal.com/spdji/en/contact-us/) -> `public_contact_surface_no_rows_acquired`, probe `blocked_or_error` ``. Potential route for S&P/Dow Jones index family source/equivalence approval; WAF may block unauthenticated probes.
- `cme_market_data_contacts` / `price_root_equivalence_us_index_futures`: CME Group tools/contact list (https://www.cmegroup.com/tools-information/contacts-list.html) -> `public_contact_surface_no_rows_acquired`, probe `blocked_or_error` ``. Potential route for ES/NQ/MNQ futures market-data licensing or source equivalence policy.
- `kraken_public_api_examples` / `price_root_equivalence_crypto`: Kraken public API examples/support page (https://support.kraken.com/hc/articles/360000919986-Public-endpoint-examples-you-can-try-them-directly-in-a-web-browser-) -> `venue_data_surface_not_label_rows`, probe `ok` `200`. Venue/public-data route for crypto source provenance; not accepted as regime labels without owner-approved labels.
- `kraken_futures_market_history_docs` / `price_root_equivalence_crypto`: Kraken futures market-history API docs (https://docs.kraken.com/api/docs/futures-api/history/market-history/) -> `venue_data_surface_not_label_rows`, probe `ok` `200`. Venue-native crypto market-history route; can support provenance only, not MainRegimeV2 labels by itself.
- `cme_fx_rates_commodities_contacts` / `price_root_equivalence_fx_rates_commodities`: CME Group tools/contact list for FX/rates/commodities futures (https://www.cmegroup.com/tools-information/contacts-list.html) -> `public_contact_surface_no_rows_acquired`, probe `blocked_or_error` ``. Potential route for GC/CL/ZN or FX/rates/commodities futures data/equivalence policy.

## Boundary

This run does not send a request, download rows, or create `/tmp/ict-engine-source-label-equivalence-intake` files. R2 remains blocked until source-owned or owner-approved rows plus provenance pass the existing source-label equivalence verifier.

## Artifacts

- JSON: `source_label_equivalence_contact_leads_v1.json`
- Contact CSV: `source_label_equivalence_contact_leads_v1.csv`
- Assertions: `../checks/source_label_equivalence_contact_leads_v1_assertions.out`
