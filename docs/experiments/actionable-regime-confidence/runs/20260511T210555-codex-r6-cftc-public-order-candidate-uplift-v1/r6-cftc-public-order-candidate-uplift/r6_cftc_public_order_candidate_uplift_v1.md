# R6 CFTC Public Order Candidate Uplift v1

Decision: `r6_cftc_public_order_candidate_uplift_v1=candidates_found_rows_not_extracted`.

Result:
- Sources checked: `6`.
- Downloaded successfully: `6`.
- Row-extract candidates: `6`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

| Source | Download | Row Extract Candidate | Dates | Times |
|---|---:|---:|---:|---:|
| `cftc_mohan_complaint_2018` | `true` | `true` | 6 | 30 |
| `cftc_geneva_order_2018` | `true` | `true` | 8 | 0 |
| `cftc_arab_trading_group_order_2020` | `true` | `true` | 2 | 0 |
| `cftc_fny_order_2020` | `true` | `true` | 1 | 0 |
| `cftc_shak_complaint_2022` | `true` | `true` | 3 | 10 |
| `cftc_tower_press_release_2019` | `true` | `true` | 1 | 0 |

Next:
Extract only source-owned row-level positives/controls from candidates that expose dates/times/sides; do not infer labels from raw market data or generated methods.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T210555-codex-r6-cftc-public-order-candidate-uplift-v1/r6-cftc-public-order-candidate-uplift/r6_cftc_public_order_candidate_uplift_v1.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T210555-codex-r6-cftc-public-order-candidate-uplift-v1/r6-cftc-public-order-candidate-uplift/r6_cftc_public_order_candidate_uplift_v1_candidates.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T210555-codex-r6-cftc-public-order-candidate-uplift-v1/checks/r6_cftc_public_order_candidate_uplift_v1_assertions.out`
