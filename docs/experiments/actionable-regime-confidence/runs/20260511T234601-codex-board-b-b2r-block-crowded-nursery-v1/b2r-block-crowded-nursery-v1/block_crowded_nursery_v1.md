# B2R Block Crowded Nursery v1

Run id: `20260511T234601+0800-codex-board-b-b2r-block-crowded-nursery-v1`

This is an additive Board B nursery packet. It does not promote `220646`.

## Result

- Branch path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- Nursery status: `incubation_only`
- RC-SPA source remains pass for the source-root family; Crisis branch RC-SPA is `83.0` over `532` trades.
- Earlier exact readback: execution tree branch `block_crowded`, gate `blocked`, readiness `0.4433`.
- Latest live replay: execution tree branch `fill_viable`, gate `observe`, readiness `0.4504`.
- Pre-Bayes latest gate: `pass_neutralized` quality `0.5619249343265972`.
- CatBoost/path-ranker: exact Crisis branch score is `0.9732088635185723`, and execution tree reports ranker score used: `True`.

## Interpretation

`block_crowded` is now a nursery execution-admissibility feature, not a profitability rejection. The same exact Crisis branch crossed from blocked to observe/passive when readiness moved around the `0.45` floor, but promotion remains blocked because the latest replay is `observe`, Pre-Bayes is only `pass_neutralized`, the data fingerprint is not comparable to the previous replay, and no explicit closed-loop confidence promotion exists.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T234601-codex-board-b-b2r-block-crowded-nursery-v1/b2r-block-crowded-nursery-v1/block_crowded_nursery_v1.json`
- Features CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T234601-codex-board-b-b2r-block-crowded-nursery-v1/b2r-block-crowded-nursery-v1/block_crowded_nursery_features_v1.csv`
- Feedback rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T234601-codex-board-b-b2r-block-crowded-nursery-v1/b2r-block-crowded-nursery-v1/block_crowded_nursery_feedback_rows_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T234601-codex-board-b-b2r-block-crowded-nursery-v1/checks/block_crowded_nursery_v1_assertions.out`
- Command logs: `docs/experiments/actionable-regime-confidence/runs/20260511T234601-codex-board-b-b2r-block-crowded-nursery-v1/command-output`
