# CME Group R6 Oystacher Normal-Control Export Request v3

Purpose: request source-owned normal/non-manipulation order-lifecycle controls for the Board A R6 Oystacher verifier. This is a request draft only; it is not approval, not acquired data, and not a canonical merge.

Delivery root after approval/export: `/tmp/ict-engine-board-a-r6-owner-export-v1`

Required verifier-native files:
- `positive_spoofing_layering_rows.csv`
- `matched_negative_normal_activity_rows.csv`
- `provenance_manifest.json`

Controls must be source-owned normal/non-manipulation rows. Do not use same-exhibit `FLIP` rows unless the user/board explicitly approves that exception.

Official route references:
- CME DataMine historical data: https://www.cmegroup.com/market-data/datamine-historical-data/index.html
- CME Market Depth Files FAQ: https://www.cmegroup.com/market-data/files/cme-group-market-depth-faq.pdf

Requested cells:

| axis | bucket | positive_spoof_support | invalid_flip_candidate_support | required_valid_normal_control_support | date_fit_status | requested_product_scope | requested_date_scope |
| --- | --- | --- | --- | --- | --- | --- | --- |
| contract_family | energy | 2657 | 793 | 73 | needs_product_start_confirmation | all Oystacher energy contract-family symbols | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |
| contract_family | equity_index | 614 | 285 | 73 | needs_product_start_confirmation | all Oystacher equity_index contract-family symbols | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |
| contract_family | metals | 1633 | 388 | 73 | needs_product_start_confirmation | all Oystacher metals contract-family symbols | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |
| venue_exact | CME Globex | 614 | 285 | 73 | needs_product_start_confirmation | all Oystacher symbols on CME Globex | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |
| venue_exact | COMEX/CME Globex | 1633 | 388 | 73 | needs_product_start_confirmation | all Oystacher symbols on COMEX/CME Globex | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |
| venue_exact | NYMEX/CME Globex | 2657 | 793 | 73 | needs_product_start_confirmation | all Oystacher symbols on NYMEX/CME Globex | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |
| symbol_exact | Crude Oil futures | 1101 | 324 | 73 | needs_2012_product_start_confirmation | Crude Oil futures | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |
| symbol_exact | E-mini S&P 500 futures | 614 | 285 | 73 | needs_2013_product_start_confirmation | E-mini S&P 500 futures | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |
| symbol_exact | High-Grade Copper futures | 1633 | 388 | 73 | needs_2011_product_start_confirmation | High-Grade Copper futures | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |
| symbol_exact | Natural Gas futures | 1556 | 469 | 73 | needs_2012_product_start_confirmation | Natural Gas futures | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |
| chronological_year | 2011 | 1633 | 388 | 73 | needs_product_start_confirmation | all Oystacher required symbols active in 2011 | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |
| chronological_year | 2012 | 2657 | 793 | 73 | needs_product_start_confirmation | all Oystacher required symbols active in 2012 | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |
| chronological_year | 2013 | 542 | 187 | 73 | needs_product_start_confirmation | all Oystacher required symbols active in 2013 | 2011-2014 Oystacher Exhibit A date coverage; exact rows must map to the requested axis/bucket and be outside same-exhibit FLIP promotion unless approved |

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
3. Only if accepted, rerun provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback.
4. Keep R5/R3/source-label roots blocked until their exact source-owned inputs exist.
