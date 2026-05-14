# Direct Missing Species Source Screen v2

Run ID: `20260511T191642-codex-direct-missing-species-source-screen-v2`

Incremental source screen after v20. It does not download raw rows, does not alter Current Cursor, and does not reclassify prior screens.

## Decision

`direct_missing_species_source_screen_v2=no_ready_positive_control_source`

- Incremental candidates screened: `7`.
- Ready real positive/control sources found: `0`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Required Contract

- row-level direct manipulation positives
- matched same-schema normal controls
- source-owned or owner-approved provenance
- venue/symbol/date/session fields sufficient for chronological validation
- no generated, proxy, synthetic, or OHLCV-only labels

## Candidate Disposition

- `FINRA Potential Manipulation Report` (spoofing_layering,quote_spoofing): `blocked_schema_target_rows_not_public`. Source: https://www.finra.org/compliance-tools/report-center/cross-market-equities-supervision/potential-manipulation-report. Official schema target for layering/quote-spoofing exceptions, but public page is not an exportable positive/control row panel.
- `Tardis historical crypto tick-level order book data` (spoofing_layering,quote_stuffing,pinging): `blocked_raw_order_book_no_direct_labels`. Source: https://tardis.dev/. Can supply raw direct order-book context, but it does not provide source-owned manipulation positives or matched negative groups.
- `LOBSTER / Level-3 order book sample mirrors` (spoofing_layering,quote_stuffing): `blocked_raw_lob_no_positive_labels`. Source: https://lobsterdata.com/. Useful for normal-market controls or feature prototyping, but no source-owned direct manipulation labels are attached.
- `Spoofing and pinging in foreign exchange markets` (spoofing_layering,pinging): `blocked_restricted_paper_no_public_row_export`. Source: https://www.sciencedirect.com/science/article/abs/pii/S1042443120301621. Paper-level evidence confirms relevance, but the public surface does not export replayable positives and matched controls.
- `lobflow order-book spoofing/market-event tooling` (spoofing_layering): `blocked_library_no_source_rows`. Source: https://pypi.org/project/lobflow/. May help design future probes, but a library without source-owned rows cannot satisfy Board A.
- `Quote stuffing research using TotalView-ITCH / US equities` (quote_stuffing): `blocked_method_definition_no_exported_rows`. Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1958281. Useful event-definition provenance, but the public paper page is not a source-owned row export with matched controls.
- `Statistical-physics spoofing study on LUNA and Bitcoin` (spoofing_layering): `blocked_method_case_study_no_labeled_controls`. Source: https://arxiv.org/abs/2306.08185. Market case-study/method source, but no Board A-ready positive/control rows or provenance manifest were found.

## Carry-Forward Blocker

The new screen still finds no Board A-ready row-level direct-manipulation positives plus matched normal controls. Raw LOB/order-book providers can support future control construction, and papers can support schema/probe design, but neither can be promoted into the strict direct `Manipulation` gate without source-owned labels, matched controls, and provenance.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T191642-codex-direct-missing-species-source-screen-v2/direct-missing-species-screen/direct_missing_species_source_screen_v2.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T191642-codex-direct-missing-species-source-screen-v2/direct-missing-species-screen/direct_missing_species_source_screen_v2_candidates.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T191642-codex-direct-missing-species-source-screen-v2/checks/direct_missing_species_source_screen_v2_assertions.out`
