# Intraday Rotation Repaired Run Artifact Integrity Readback

Run id: `20260511T214849+0800-codex-board-b-intraday-risk-defensive-rotation-v1-repaired`.

## Decision

- Referenced run root observed before correction: `false`
- Matching process observed: `false`
- RC-SPA report exists: `false`
- Variant rows emitted: `0`
- Selected rows emitted: `0`
- Gate result: `fail:referenced_artifacts_missing_at_readback`
- Downstream consumption: `not_started:no_verifiable_rc_spa_report`

## Readback

The board contained a `214849` operational-failure row, but the declared run root and the referenced error files were absent at readback. This correction does not promote the run and does not rely on the missing error files as evidence.

The only verified fact for this correction is that no verifiable run artifacts were present when checked. Pre-Bayes / BBN / CatBoost / execution tree were not started from this run.

## Next

Use the completed `214454` RC-SPA row as the latest verified scored state. Any future repaired retry must write a self-contained script and concrete run artifacts before it can supersede the board cursor.
