# R6 Arab/FNY/Tower Cached Screen v1

## Scope

Read-only screen of the cached Arab Trading Group, FNY, and Tower CFTC candidate sources from the earlier public-order candidate run. No network requests were sent and the direct-Manipulation intake files were not changed.

## Result

- Candidate sources checked: `3`.
- Row-materializable candidates: `0`.
- Positive rows added: `0`.
- Matched controls added: `0`.
- Intake unchanged: `true`.
- Direct verifier return code: `0`.
- Gate result: `r6_arab_fny_tower_cached_screen_v1=cached_candidates_fail_closed_no_row_level_events`.

## Candidate Decisions

### cftc_arab_trading_group_order_2020

- Source kind: `official_cftc_order_cached_pdf_text`.
- Cached text chars: `28900`; date hits: `3`.
- Summary: The cached order gives respondent/trader groups, product families, date ranges, and generic genuine/spoof order patterns.
- Fail-closed reason: No row-level trade date, side, exact contract, order timestamp, or single matched genuine order is exposed for any one event.
- Rows materialized: `0`.

### cftc_fny_order_2020

- Source kind: `official_cftc_order_cached_pdf_text`.
- Cached text chars: `22197`; date hits: `2`.
- Summary: The cached order gives a former trader, broad product families, the relevant period, and a generic genuine/spoof pattern.
- Fail-closed reason: No event-level date, side, exact order quantity, timestamp, or matched source-described genuine control row is present.
- Rows materialized: `0`.

### cftc_tower_press_release_2019

- Source kind: `official_cftc_press_release_cached_html`.
- Cached text chars: `9500`; date hits: `1`.
- Summary: The cached press release gives an official order link, the broad 2012-2013 period, equity-index futures venue context, and the generic genuine/spoof order pattern.
- Fail-closed reason: The cached HTML is a press release, not the linked order; it lacks row-level dates, symbols, sides, quantities, and matched controls. The linked order was not fetched in this no-network slice.
- Rows materialized: `0`.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212521-codex-r6-arab-fny-tower-cached-screen-v1/r6-arab-fny-tower-cached-screen/r6_arab_fny_tower_cached_screen_v1.json`
- Candidate CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212521-codex-r6-arab-fny-tower-cached-screen-v1/r6-arab-fny-tower-cached-screen/r6_arab_fny_tower_cached_screen_v1_candidates.csv`
- Gates CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212521-codex-r6-arab-fny-tower-cached-screen-v1/r6-arab-fny-tower-cached-screen/r6_arab_fny_tower_cached_screen_v1_gates.csv`
- Verifier stdout: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212521-codex-r6-arab-fny-tower-cached-screen-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212521-codex-r6-arab-fny-tower-cached-screen-v1/checks/r6_arab_fny_tower_cached_screen_v1_assertions.out`

## Non-Completion

This run does not close R6 or the full Board A objective. It only prevents broad-order summaries from being promoted as row-level confidence evidence.
