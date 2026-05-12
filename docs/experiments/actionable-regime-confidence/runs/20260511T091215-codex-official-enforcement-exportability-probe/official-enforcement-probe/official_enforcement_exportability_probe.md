# Official Enforcement Exportability Probe

Run ID: `20260511T091215+0800-codex-official-enforcement-exportability-probe`

## Objective

Find official/regulator/SRO sources that provide downloadable or authenticated exact-underlying parent-root labels, or timestamped direct Manipulation positive/negative rows.

## Candidate Classification

| Candidate | Organization | Decision | Reason | Needed Before Acceptance |
|---|---|---|---|---|
| SEC litigation releases | SEC | `positive_event_index_only_no_exportable_rows` | official enforcement document index; useful positive-event provenance, but no bulk timestamped positive/negative market row export or exact-underlying Board A label panel was obtained | structured enforcement row export with symbols, event windows, and matched non-event controls |
| SEC administrative proceedings | SEC | `positive_event_index_only_no_exportable_rows` | official proceeding document index; not an accepted direct Manipulation label source without parsed rows, timestamps, underlyings, and negative windows | downloadable parsed proceeding rows or authenticated structured API |
| FINRA disciplinary actions online | FINRA | `search_surface_no_bulk_market_rows` | public search surface for disciplinary documents; no direct bulk export of timestamped manipulation positive/negative windows was materialized in this environment | FINRA export/API access that returns row-level market manipulation cases with underlyings and dates |
| FINRA data catalog | FINRA | `catalog_surface_no_specific_manipulation_label_panel` | public data catalog surface; no accepted dataset was identified that directly exports Board A manipulation labels or parent-root regime labels | specific FINRA API dataset id plus access token/export path if such a dataset exists |
| CFTC enforcement actions | CFTC | `positive_event_index_only_no_negative_windows` | official enforcement action index can support positive-event research, but it is not a ready positive/negative row panel and does not cover MainRegimeV2 roots | structured CFTC case rows with instruments, dates, manipulation type, and controls |
| NFA BASIC search | NFA | `member_case_search_no_market_label_rows` | public member/case search surface; no exportable market-row label panel with direct manipulation positive/negative windows was obtained | bulk disciplinary export with instrument-level event windows and non-event controls |

## Result

- Official sources inspected: `6`.
- Accepted independent MainRegimeV2 parent-root label sources: `0`.
- New attached parent-root source-label slots: `0`.
- Accepted direct `Manipulation` label sources: `0`.
- Accepted direct `Manipulation` rows/windows: `0`.
- Accepted gate remains: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.
- Gate result: `blocked_official_enforcement_sources_no_exportable_label_rows`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

## Next Action

Provide or authenticate a structured export/API for direct Manipulation rows, or provide an exact-underlying parent-root label panel; document-index pages alone are not enough.
