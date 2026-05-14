# Spoofing/Layering Matched Row Readiness v1

Run id: `20260511T151720+0800-codex-spoofing-layering-matched-row-readiness-v1`.

## Decision

- Gate result: `spoofing_layering_matched_row_readiness_v1_rows_not_acquired`
- Positive enforcement cases inventoried: `204`
- Matched negative cases available: `0`
- Confidence-gate eligible rows now: `0`
- Accepted direct `Manipulation` rows added: `0`
- Full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Source Readiness

| Source | Decision | Accepted Rows | Matched Negative Status | Reason |
|---|---|---:|---|---|
| `finra_potential_manipulation_report` | `schema_target_rows_not_public` | `0` | `not_acquired` | Public FINRA page is useful as field/schema target but does not provide exportable positive and matched negative rows. |
| `spoofing_appendix_case_inventory` | `positive_case_inventory_only` | `0` | `absent` | 204 positive enforcement cases exist, but matched_negative_available=0 and confidence_gate_eligible_now=0. |
| `trentmkelly/polymarket_crypto_derivatives` | `direct_input_source_unlabeled` | `0` | `not_labeled_or_not_matched` | direct order-book/order-lifecycle fields exist, but no explicit manipulation-positive/negative labels or event windows were found |
| `phobia76/pmxt-l2-dump` | `direct_input_source_unlabeled` | `0` | `not_labeled_or_not_matched` | direct order-book/order-lifecycle fields exist, but no explicit manipulation-positive/negative labels or event windows were found |
| `muhammetakkurt/pump-fun-meme-token-dataset` | `event_context_unlabeled` | `0` | `not_labeled_or_not_matched` | token/event context exists, but no explicit manipulation labels or order-lifecycle evidence were found |
| `Washedashore/thepower` | `rejected_metadata_false_positive` | `0` | `not_labeled_or_not_matched` | dataset card is a generic template and does not provide market event/order-flow labels |
| `navnoor_spoof_detection` | `rejected_code_not_replayable_direct_rows` | `0` | `absent` | Local checkout contains model/notebook logic but no exported timestamped positive/negative spoofing rows or same-venue negative controls. |
| `quantsingularity_spoofing` | `rejected_synthetic_framework_no_real_labeled_rows` | `0` | `absent` | Repository provides framework, adapters, expected data schema, and synthetic spoofing injection, but no replayable real timestamped positive/negative spoofing dataset in the local checkout. |
| `public_search_lobster_raw_lob` | `raw_lob_no_manipulation_labels` | `0` | `not_labeled` | Raw limit-order-book data can provide market context, but without source positive spoofing/layering windows and matched controls it is not an accepted direct Manipulation label source. |
| `public_search_spoofing_code_or_synthetic` | `method_provenance_only` | `0` | `synthetic_or_absent` | Public spoofing repos and synthetic benchmarks are method provenance unless they ship replayable real positive and matched negative rows. |

## Required Files To Unblock

| Required File | Status | Minimum Fields |
|---|---|---|
| `positive_spoofing_layering_rows.csv` | `missing` | label, source_report, trade_date, symbol, venue_or_market_center, side, earliest_order_received_time, latest_order_received_time, order_count, total_order_quantity, activity_description, matched_negative_group_id, source_row_id |
| `matched_negative_normal_activity_rows.csv` | `missing` | same schema as positives; matched venue/symbol/date/session/liquidity bucket; normal activity label |
| `provenance_manifest.json` | `missing` | source owner, export identity, pull date, redaction notes, row counts, schema version |

## Guardrail

Positive-only enforcement inventories, raw order books without labels, and synthetic detector rows remain fail-closed. The next acceptable artifact must contain source-owned positive spoofing/layering rows and matched normal controls under the same schema.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T151720-codex-spoofing-layering-matched-row-readiness-v1/matched-row-readiness/spoofing_layering_matched_row_readiness_v1.json`
- Sources CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T151720-codex-spoofing-layering-matched-row-readiness-v1/matched-row-readiness/spoofing_layering_matched_row_readiness_v1_sources.csv`
- Required files CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T151720-codex-spoofing-layering-matched-row-readiness-v1/matched-row-readiness/spoofing_layering_matched_row_readiness_v1_required_files.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T151720-codex-spoofing-layering-matched-row-readiness-v1/checks/spoofing_layering_matched_row_readiness_v1_assertions.out`
