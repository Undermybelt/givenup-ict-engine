# R6 JPMorgan Order Positive Row Candidate Screen v1

- Run id: `20260511T235048-codex-r6-jpmorgan-order-positive-row-candidate-screen-v1`.
- Official source: `https://www.cftc.gov/media/4826/enfjpmorganchaseorder092920/download`.
- Shared live intake present: `false`.
- JPM control-complete candidates: `8` positives plus `8` matched controls.
- Candidate stack: Sarao control-complete `2`, Nowak/Smith `6`, JPM `8`; total `16` positive/control pairs.
- Composite rows from V54 baseline plus candidate stack: positives `73`, matched controls `73`, sidecar controls `80`.
- Composite min Wilson95 LCB: `0.950006`; pooled 95 pass: `true`.
- Chronological/symbol/venue split support remains blocked and direct species coverage remains open.
- Gate result: `r6_jpmorgan_order_positive_row_candidate_screen_v1=control_complete_candidate_stack_pooled95_pass_live_intake_missing_split_still_blocked`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T235048-codex-r6-jpmorgan-order-positive-row-candidate-screen-v1/r6-jpmorgan-order-positive-row-candidate-screen/r6_jpmorgan_order_positive_row_candidate_screen_v1.json`
- JPM positives CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T235048-codex-r6-jpmorgan-order-positive-row-candidate-screen-v1/r6-jpmorgan-order-positive-row-candidate-screen/r6_jpmorgan_order_positive_row_candidates_v1.csv`
- JPM matched controls CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T235048-codex-r6-jpmorgan-order-positive-row-candidate-screen-v1/r6-jpmorgan-order-positive-row-candidate-screen/r6_jpmorgan_order_matched_controls_v1.csv`
- Control-complete stack positives CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T235048-codex-r6-jpmorgan-order-positive-row-candidate-screen-v1/r6-jpmorgan-order-positive-row-candidate-screen/r6_control_complete_candidate_stack_positives_v1.csv`
- Control-complete stack controls CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T235048-codex-r6-jpmorgan-order-positive-row-candidate-screen-v1/r6-jpmorgan-order-positive-row-candidate-screen/r6_control_complete_candidate_stack_matched_controls_v1.csv`
- Delta verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T235048-codex-r6-jpmorgan-order-positive-row-candidate-screen-v1/command-output/delta_direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T235048-codex-r6-jpmorgan-order-positive-row-candidate-screen-v1/checks/r6_jpmorgan_order_positive_row_candidate_screen_v1_assertions.out`
