# R6 Additional CFTC Public Order Screen v1

Run ID: `20260511T210228-codex-r6-additional-cftc-public-order-screen-v1`

- Gate result: `r6_additional_cftc_public_order_screen_v1=official_case_routes_found_rows_not_extracted`.
- Official CFTC cases screened: `5`.
- Public pages fetched with status 200: `4`.
- Cases with related order/download links on the public page: `4`.
- Row-extraction-ready public pages: `0`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.

## Case Routes

| Case | Status | Markets | Period | Signals | Accepted |
|---|---:|---|---|---|---:|
| `falloon_2025` | `200` | E-mini S&P 500;E-mini Nasdaq 100 | 2022 | spoof, order, genuine, cancel | `false` |
| `cox_2019` | `None` | E-mini S&P 500;E-mini Nasdaq 100;E-mini Dow | 2014-2018 |  | `false` |
| `mirae_2020` | `200` | E-mini S&P 500 | 2014-2016 | order | `false` |
| `sarao_2016` | `200` | E-mini S&P 500 | 2010-2015 |  | `false` |
| `panther_2013` | `200` | futures contracts across exchanges | 2011 | order | `false` |

## Boundary

This run only records official public CFTC acquisition routes. Press-page summaries are not row-level Board A evidence; no additional positives or controls were materialized into `/tmp/ict-engine-direct-manipulation-row-intake`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T210228-codex-r6-additional-cftc-public-order-screen-v1/r6-additional-cftc-public-order-screen/r6_additional_cftc_public_order_screen_v1.json`
- Case CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T210228-codex-r6-additional-cftc-public-order-screen-v1/r6-additional-cftc-public-order-screen/r6_additional_cftc_public_order_screen_v1_cases.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T210228-codex-r6-additional-cftc-public-order-screen-v1/checks/r6_additional_cftc_public_order_screen_v1_assertions.out`
