# Board A Positive/Negative Feedback Ingress Packet - 2026-05-23

## Scope

- Board: A, regime/subclass evidence only.
- Source branch: `RangeConsolidation -> InsuranceDefensivePremiumCycle -> rsi_vwap_reclaim -> yf_insurance_defensive_range_reclaim_1m_mtf_board_a_v1`.
- Source run: `support/docs/experiments/actionable-regime-confidence/runs/20260518T123234+0800-codex-board-a-yf-insurance-defensive-range-reclaim-1m-mtf-v1/`.
- Replay run, sampled: `support/docs/experiments/actionable-regime-confidence/runs/20260523T062847Z-codex-board-a-positive-negative-feedback-ingress-v1/`.
- Replay run, full available row set: `support/docs/experiments/actionable-regime-confidence/runs/20260523T063349Z-codex-board-a-positive-negative-feedback-ingress-v1/`.
- Runner: `support/docs/experiments/actionable-regime-confidence/scripts/run_board_a_positive_negative_feedback_ingress_v1.py`.

The replay consumes existing Board A Auto-Quant rank rows. It does not open a
Board B profitability lane and does not promote a tradeable factor.

## Result

- Terminal decision: `feedback_ingress_repaired_observation_only`.
- AQ rank target rows: `15`.
- Positive target rows: `2`.
- Negative boundary target rows: `13`.
- Sampled ingested feedback rows: `8` (`2` positive / `6` negative boundary samples).
- Full ingested feedback rows: `15` (`2` positive / `13` negative boundary samples).
- Feedback emit exits: all `0`.
- `ict-engine update --feedback-file` exits: all `0`.
- Readbacks exited `0`: `workflow-status`, `pre-bayes-status`, `policy-training-status`, and `export-structural-path-ranking-target`.
- Promotion allowed: `false`.
- Trade usable: `false`.

## Readback Evidence

The sampled replay's `learning_state.json` contains `8` structural feedback
records for the source branch:

- `win`: `2`
- `loss`: `6`

`policy-training-status` exposed the intended feedback surface:

- `auto_quant_real_trade_entry_v1.matched_rows=8`
- `structural_feedback_rows=8`
- `outcomes=loss=6,win=2`
- warning: `matched_rows_below_minimum: 8`

`export-structural-path-ranking-target` emitted a usable target bundle but not a
ready ranker gate:

- `rows=11`
- `history_rows=32`
- `mature_rows=11`
- `history_mature_rows=29`
- `rows_with_raw_path_score=8`
- `raw_scored_mature=8/30`
- `production_validation=0/30`
- `observation_validation=8/30`
- `calibration=not_fitted`

The full replay then ingested every available AQ rank row from the same source
artifact. Its `learning_state.json` contains `15` structural feedback records
with `15` distinct `path_id` values:

- `win`: `2`
- `loss`: `13`

Full replay `policy-training-status` improved the same training surface but did
not close validation:

- `auto_quant_real_trade_entry_v1.matched_rows=15`
- `structural_feedback_rows=15`
- `outcomes=loss=13,win=2`
- warning: `matched_rows_below_minimum: 15`

Full replay `export-structural-path-ranking-target`:

- `rows=18`
- `history_rows=60`
- `mature_rows=18`
- `history_mature_rows=57`
- `rows_with_raw_path_score=15`
- `raw_scored_mature=15/30`
- `production_validation=0/30`
- `observation_validation=15/30`
- `calibration=not_fitted`
- `runtime_selection=disabled`
- `trainer_artifact=missing`

## Repair Notes

Two implementation fixes were needed to make the feedback loop truthful:

- The runner passes negative PnL as `--pnl=<value>` so Clap does not parse a
  value like `-0.001` as a new option.
- `structural_feedback_trade_enricher.py` now prefers an explicit `path_id` from
  the target row before falling back to the branch path. This keeps positive and
  negative rank rows as distinct feedback identities instead of collapsing them
  into one branch-level key.

## Consumer Decision

Positive rows now feed rooted-branch Bayesian evidence through existing
`structural-feedback-v1` and `update --feedback-file` surfaces. Negative and
zero rows now feed the same rooted branch as `loss` feedback with
`exit_reason=negative_boundary_sample`, strengthening the boundary instead of
being discarded.

This is still not Board A completion. The full replay doubled the observation
surface from `8/30` to `15/30`, but it remains below the `30/30` validation
floor, has no fitted calibration, has no production validation, and does not
satisfy the user's `95%` bull/bear/root-regime confidence requirement.

Allowed use:

- rooted branch evidence feedback
- negative boundary sample preservation
- future CatBoost/path-ranker training substrate after more mature observations
- Board A subclass/regime evidence readback

Disallowed use:

- root-regime registration
- `95%` confidence claim
- tradeable factor claim
- Board B profitability promotion
- execution-tree promotion
- goal completion

`update_goal=false`.
