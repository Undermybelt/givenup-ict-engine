# R6 Tower Linked Order Fetch Screen v1

## Scope

Fetched the official CFTC Tower order linked from the cached Tower press release and screened it for row-level R6 direct Manipulation materialization. Raw PDF/text stayed under `/tmp/ict-engine-r6-tower-order-fetch-screen-v1/raw`.

## Result

- Source fetched: HTTP `200`, content type `application/pdf`.
- PDF SHA256: `c3a7fb2c5824219bc016c42b8075a243cc0b241a6b3abd93367713c7cbc58d8f`.
- Text chars: `45856`.
- Row-materializable candidates: `0`.
- Positive rows added: `0`.
- Matched controls added: `0`.
- Intake changed: `false`.
- Direct verifier status after screen: `schema_ready_unscored`, positives `24`, matched negatives `24`.
- Gate result: `r6_tower_linked_order_fetch_screen_v1=official_order_fetched_no_row_level_events`.

## Fail-Closed Reason

The official order confirms the relevant period, E-mini S&P 500 / E-mini NASDAQ 100 / E-mini Dow markets, generic Genuine Order and Spoof Order mechanics, and thousands-of-occasions conduct. It does not expose a single event with row-level trade date, order timestamp, side, quantity, and matched genuine-control leg. No R6 rows were materialized.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212840-codex-r6-tower-linked-order-fetch-screen-v1/r6-tower-linked-order-fetch-screen/r6_tower_linked_order_fetch_screen_v1.json`
- Candidate CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212840-codex-r6-tower-linked-order-fetch-screen-v1/r6-tower-linked-order-fetch-screen/r6_tower_linked_order_fetch_screen_v1_candidates.csv`
- Gates CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212840-codex-r6-tower-linked-order-fetch-screen-v1/r6-tower-linked-order-fetch-screen/r6_tower_linked_order_fetch_screen_v1_gates.csv`
- Verifier stdout: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212840-codex-r6-tower-linked-order-fetch-screen-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212840-codex-r6-tower-linked-order-fetch-screen-v1/checks/r6_tower_linked_order_fetch_screen_v1_assertions.out`

## Non-Completion

This run does not close R6 or the full Board A objective. It prevents the Tower linked order from being promoted as row-level confidence evidence.
