# Non-R6 Source Intake Outbound Request Messages v1

- Run id: `20260512T010201-codex-non-r6-source-intake-outbound-request-messages-v1`.
- Gate result: `non_r6_source_intake_outbound_request_messages_v1=outbound_messages_ready_not_sent_rows_not_acquired`.
- Request branches: `3` source-label equivalence, R3 native sub-hour, and R5 recency.
- External requests sent: `false`; source rows acquired: `0`; accepted rows added: `0`.
- Canonical merge allowed: `false`; downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: `false`.
- Strict full objective achieved: false. `update_goal=false`.
- Runtime code changed: false. Shared intake mutated: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Messages
- `source_label_equivalence`: `source_label_equivalence_owner_request_message_v1.md`
- `r3_native_subhour_source_labels`: `r3_native_subhour_source_label_request_message_v1.md`
- `r5_source_panel_recency_extension`: `r5_source_panel_recency_extension_request_message_v1.md`

## Required Roots
- `/tmp/ict-engine-source-label-equivalence-intake` -> `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json`
- `/tmp/ict-engine-native-subhour-source-label-intake` -> `native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json`
- `/tmp/ict-engine-source-panel-recency-extension` -> `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json`

## Boundary

This packet only materializes outbound-ready messages. It does not send external requests, create `/tmp` intake files, accept rows, rerun promotion gates, or treat provider/OHLCV/generated labels as source-owned evidence.

## Next

Send or otherwise satisfy these three non-R6 source-intake requests. After exact files appear under their target roots, rerun the fail-closed verifiers and only then run the unchanged downstream chain in the Board A order.
