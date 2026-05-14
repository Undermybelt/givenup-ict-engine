# R6 CME Normal-Control Route Screen v1

Run ID: `20260511T205742-codex-r6-cme-normal-control-route-screen-v1`

- Gate result: `r6_cme_normal_control_route_screen_v1=official_route_identified_controls_not_acquired`.
- Positive rows currently present in `/tmp`: `2`.
- Provenance manifest present: `true`.
- Matched negative normal-control rows present: `true`.
- Official/public route records checked: `3`.
- Request sent: `false`; authenticated account used: `false`; rows acquired: `false`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.

## Route Judgment

CME Group is the direct source owner for the positive examples' venue/instrument family, so the official CME historical order-book route is a plausible acquisition path for matched NQ normal controls. It is not accepted evidence until an owner-approved export supplies same-schema normal rows.

## Required Control File

- Target: `/tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv`.
- Match group: `cftc_mohan_20131202_nq_example`.
- Required axes: CME venue, E-mini NASDAQ/NQ futures family, overnight Central Time session, normal non-manipulation activity, same CSV schema.

## Public Sources Checked

- `cme_datamine_landing`: status `None`, owner `CME Group`, URL `https://www.cmegroup.com/market-data/datamine-historical-data.html`.
- `cme_datamine_order_book`: status `None`, owner `CME Group`, URL `https://www.cmegroup.com/market-data/datamine-historical-data/datamine-order-book.html`.
- `cme_datamine_contact`: status `None`, owner `CME Group`, URL `https://www.cmegroup.com/market-data/datamine-historical-data/contact-us.html`.

## Boundary

This run identifies a source-owner route and writes a local no-send request draft only. It does not create `matched_negative_normal_activity_rows.csv`, does not use a CME account, and does not promote positive-only evidence.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T205742-codex-r6-cme-normal-control-route-screen-v1/r6-cme-normal-control-route-screen/r6_cme_normal_control_route_screen_v1.json`
- Route CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T205742-codex-r6-cme-normal-control-route-screen-v1/r6-cme-normal-control-route-screen/r6_cme_normal_control_route_screen_v1_routes.csv`
- Source CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T205742-codex-r6-cme-normal-control-route-screen-v1/r6-cme-normal-control-route-screen/r6_cme_normal_control_route_screen_v1_sources.csv`
- No-send request draft: `docs/experiments/actionable-regime-confidence/runs/20260511T205742-codex-r6-cme-normal-control-route-screen-v1/r6-cme-normal-control-route-screen/r6_cme_normal_control_request_draft_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T205742-codex-r6-cme-normal-control-route-screen-v1/checks/r6_cme_normal_control_route_screen_v1_assertions.out`
