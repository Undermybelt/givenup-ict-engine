# Cboe/CFE R6 Oystacher Normal-Control Export Request v4

Purpose: request source-owned normal/non-manipulation controls for the Board A R6 Oystacher verifier, using the current Cboe/CFE route evidence from `014314`. This is a request draft only; it is not approval, not acquired data, and not a canonical merge.

Delivery root after approval/export: `/tmp/ict-engine-board-a-r6-owner-export-v1`

Required verifier-native files:
- `positive_spoofing_layering_rows.csv`
- `matched_negative_normal_activity_rows.csv`
- `provenance_manifest.json`

Controls must be source-owned normal/non-manipulation rows. Do not use same-exhibit `FLIP` rows unless the user/board explicitly approves that exception.

Official current route references:
- Cboe DataShop CFE VIX futures trades and quotes: https://datashop.cboe.com/cfe-vix-volatility-index-futures-trades-quotes
- Cboe U.S. Futures Market Data Services: https://ww2.cboe.com/market_data_services/us/futures/

Request ask:
- Please confirm licensed historical coverage and export path for the Oystacher 2014 CFE/VIX cells below.
- The DataShop CFE VIX futures trades/quotes route is acceptable for trade/quote rows if it can produce verifier-native normal-control rows with provenance.
- If the verifier requires deeper controls, please route to Cboe/CFE market-data services for Top-of-Book, Depth-of-Book, or custom historical order-lifecycle support for the 2014 CFE/VIX window.
- Required support is `73` valid source-owned normal-control rows per cell, outside same-exhibit `FLIP` promotion unless that exception is explicitly approved.

Requested cells:

| axis | bucket | positive_spoof_support | invalid_flip_candidate_support | required_valid_normal_control_support | date_fit_status | requested_product_scope | requested_date_scope |
| --- | --- | --- | --- | --- | --- | --- | --- |
| contract_family | volatility_index | 278 | 87 | 73 | 2014_custom_export_required | all Oystacher volatility_index contract-family symbols | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |
| venue_exact | CFE/CBOE Futures Exchange | 278 | 87 | 73 | 2014_custom_export_required | all Oystacher symbols on CFE/CBOE Futures Exchange | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |
| symbol_exact | VIX futures | 278 | 87 | 73 | needs_2014_historical_depth_export_confirmation | VIX futures | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |
| chronological_year | 2014 | 350 | 185 | 73 | needs_cfe_depth_export_confirmation | all Oystacher required symbols active in 2014 | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |

Required row fields:
- label
- source_report
- source_section
- trade_date
- symbol
- venue_or_market_center
- participant_type_code
- participant_identifier
- side
- earliest_order_received_time
- latest_order_received_time
- order_count
- total_order_quantity
- activity_description
- matched_negative_group_id
- session_bucket
- source_row_id

Post-delivery chain:
1. Place owner-approved files under `/tmp/ict-engine-board-a-r6-owner-export-v1`.
2. Rerun direct verifier and split calibration under the shared lock.
3. Only if accepted, rerun provider, Auto-Quant, Pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback.
4. Keep R5/R3/source-label roots blocked until their exact source-owned inputs exist.
