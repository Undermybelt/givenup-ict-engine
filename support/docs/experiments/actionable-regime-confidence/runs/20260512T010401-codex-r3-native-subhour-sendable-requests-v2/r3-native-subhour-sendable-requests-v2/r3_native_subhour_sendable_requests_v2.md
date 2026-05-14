# R3 Native Sub-hour Sendable Requests v2

- Run id: `20260512T010401-codex-r3-native-subhour-sendable-requests-v2`.
- Gate result: `r3_native_subhour_sendable_requests_v2=sendable_requests_created_rows_not_acquired_no_downstream`.
- Board cursor observed: `20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1`.
- Request package: `docs/experiments/actionable-regime-confidence/runs/20260511T203100-codex-native-subhour-intake-request-package-v1`.
- Contact leads: `docs/experiments/actionable-regime-confidence/runs/20260511T203505-codex-native-subhour-contact-leads-v1`.
- Active native intraday request rows: `336`.
- Focus blocker cells: `4`.
- Sendable request drafts created: `4`.
- Required intake root: `/tmp/ict-engine-native-subhour-source-label-intake`.
- Required files: `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv` and `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_provenance.json`.
- Rows acquired: `false`; requests sent: `false`; accepted rows added: `0`.
- Canonical merge allowed: `false`; downstream chain rerun allowed: `false`; strict full objective achieved: false. `update_goal=false`.
- Runtime code changed: false. Shared intake mutated: false. Raw data committed: false. External requests sent: false.

## Focus Cells

| symbol | timeframe | provider_date_min | provider_date_max | source_date_max | source_overlap_sessions | blocker |
| --- | --- | --- | --- | --- | --- | --- |
| AAPL | 15m | 2026-02-12 | 2026-05-08 | 2026-01-30 | 0 | no_provider_session_overlap_with_source_panel_tail |
| AAPL | 30m | 2026-02-12 | 2026-05-08 | 2026-01-30 | 0 | no_provider_session_overlap_with_source_panel_tail |
| ^IXIC | 15m | 2026-02-12 | 2026-05-08 | 2026-01-30 | 0 | no_provider_session_overlap_with_source_panel_tail |
| ^IXIC | 30m | 2026-02-12 | 2026-05-08 | 2026-01-30 | 0 | no_provider_session_overlap_with_source_panel_tail |

## Request Drafts

- `kaggle_source_label_owner_native_subhour_request_v2.md`: Ask existing source-label owner for post-2026-01-30 native 15m/30m AAPL and IXIC regime-label export or approval.
- `nasdaq_indexes_ixic_native_subhour_request_v2.md`: Ask index owner for IXIC native source-label availability or explicit context-only limitation.
- `yahoo_finance_intraday_provenance_request_v2.md`: Clarify whether Yahoo can provide source-native labels; OHLCV-only provenance does not close R3.
- `market_data_vendor_native_subhour_label_availability_request_v2.md`: Ask vendors for true source-native or owner-approved sub-hour regime-label products, not derived labels.

## Boundary

This packet only turns the existing R3 request/contact artifacts into sendable request drafts. It does not create source labels, does not download rows, does not create `/tmp/ict-engine-native-subhour-source-label-intake`, and does not run provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree promotion.
