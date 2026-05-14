# SourceRootStopCarryV1 Preliminary No-Artifact Readback

Run id: `20260511T220019+0800-codex-board-b-source-root-stop-carry-v1`.

## Decision

- Preliminary cursor state observed: `running:rc_spa_not_scored_yet`
- Matching process observed during preliminary readback: `false`
- Scored artifacts observed during preliminary readback: `false`
- Preliminary gate result: `fail:run_marked_running_without_process_or_artifacts`
- Final status: `superseded:later_scored_rc_spa_artifacts_observed`

## Readback

This preliminary no-artifact readback was superseded by later scored artifacts in the same run root:

- `branch-rc-spa/source_root_stop_carry_rc_spa_report_v1.json`
- `checks/source_root_stop_carry_v1_assertions.out`

Use the scored `SourceRootStopCarryV1` row for Board B state. Do not use this preliminary readback as the final outcome.
