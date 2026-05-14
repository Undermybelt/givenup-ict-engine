# R6 Oystacher GovInfo Date-Row Screen v1

- Run id: `20260512T001853-codex-r6-oystacher-govinfo-date-row-screen-v1`.
- Official govinfo source fetched: `True`; content type `application/pdf`; PDF bytes `556530`.
- Extracted marker check all-pass: `True`.
- Date-level candidate contexts: `51` across `5` market blocks.
- Aggregates: spoof orders `5207`, flip sequences `1316`, trading days `51`.
- Materialization status: `date_level_context_only_not_accepted`; no Exhibit A timestamp/order-leg appendix was exposed in this public govinfo PDF.
- Gate result: `r6_oystacher_govinfo_date_row_screen_v1=official_date_contexts_materialized_exhibit_a_or_owner_export_still_required`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; shared intake mutated: `false`; trade usable: `false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T001853-codex-r6-oystacher-govinfo-date-row-screen-v1/r6-oystacher-govinfo-date-row-screen/r6_oystacher_govinfo_date_row_screen_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260512T001853-codex-r6-oystacher-govinfo-date-row-screen-v1/r6-oystacher-govinfo-date-row-screen/r6_oystacher_govinfo_date_row_screen_v1.md`
- Date-context CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T001853-codex-r6-oystacher-govinfo-date-row-screen-v1/r6-oystacher-govinfo-date-row-screen/r6_oystacher_govinfo_date_context_candidates_v1.csv`
- Market-block CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T001853-codex-r6-oystacher-govinfo-date-row-screen-v1/r6-oystacher-govinfo-date-row-screen/r6_oystacher_govinfo_market_blocks_v1.csv`
- Command outputs: `docs/experiments/actionable-regime-confidence/runs/20260512T001853-codex-r6-oystacher-govinfo-date-row-screen-v1/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T001853-codex-r6-oystacher-govinfo-date-row-screen-v1/checks/r6_oystacher_govinfo_date_row_screen_v1_assertions.out`

## Interpretation

The official court document gives exact charged dates and market blocks for Oystacher/3Red, which is useful for an acquisition request. It still cannot be accepted as R6 split evidence because Board A needs timestamped order-lifecycle rows and matched controls, not date-level aggregate counts.

## Next

Acquire Oystacher Exhibit A or an owner-approved equivalent order-lifecycle export with timestamped spoof rows and matched normal controls; date-level court context is not enough for R6 split acceptance.
