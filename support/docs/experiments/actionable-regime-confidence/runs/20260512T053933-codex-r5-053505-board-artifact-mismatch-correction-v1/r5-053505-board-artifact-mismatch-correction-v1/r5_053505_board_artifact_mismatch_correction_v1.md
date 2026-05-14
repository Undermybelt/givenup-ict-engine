# R5 053505 Board/Artifact Mismatch Correction v1

Run id: `20260512T053933-codex-r5-053505-board-artifact-mismatch-correction-v1`

Gate result: `r5_053505_board_artifact_mismatch_correction_v1=board_entry_mismatch_corrected_no_promotion`

## Scope

Append-only reconciliation for the `053505` R5 candidate-screen root. The latest board tail registered the root with a gate and decision text for unrelated candidate datasets, but the actual artifact files now present on disk are the current `mafaqbhatti/stock-market-regimes-20002026` Kaggle source-panel screen.

This correction does not mutate `/tmp/ict-engine-source-panel-recency-extension`, copy source rows, generate proxy labels, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Verified Artifact State

- Root: `docs/experiments/actionable-regime-confidence/runs/20260512T053505-codex-r5-current-kaggle-recency-candidate-screen-v1`
- Actual report: `docs/experiments/actionable-regime-confidence/runs/20260512T053505-codex-r5-current-kaggle-recency-candidate-screen-v1/r5-current-kaggle-recency-candidate-screen-v1/r5_current_kaggle_recency_candidate_screen_v1.md`
- Actual JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T053505-codex-r5-current-kaggle-recency-candidate-screen-v1/r5-current-kaggle-recency-candidate-screen-v1/r5_current_kaggle_recency_candidate_screen_v1.json`
- Actual assertion file: `docs/experiments/actionable-regime-confidence/runs/20260512T053505-codex-r5-current-kaggle-recency-candidate-screen-v1/checks/r5_current_kaggle_recency_candidate_screen_v1_assertions.out`
- Actual gate: `r5_current_kaggle_recency_candidate_screen_v1=no_current_post_cutoff_target_rows_no_promotion`
- Actual dataset: `mafaqbhatti/stock-market-regimes-20002026`
- Actual date max: `2026-01-30`
- Actual R5 target rows found: `0`

## Decision

Count the `053505` root once using its verified artifact gate: `r5_current_kaggle_recency_candidate_screen_v1=no_current_post_cutoff_target_rows_no_promotion`.

Treat the earlier board sentence that names `igormerlinicomposer/herding-based-market-regime-dataset`, `kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes`, or gate `r5_current_kaggle_recency_candidate_screen_v1=current_candidates_screened_no_r5_compatible_rows_no_promotion` as stale/mismatched for this root unless matching artifact files are later materialized separately.

R5 remains blocked: the current source-owned Kaggle panel still ends at `2026-01-30`, exact post-cutoff rows for `XOM/Sideways`, `UNH/Bear`, `^DJI/Sideways`, and `AMD/Bear` are `0`, `/tmp/ict-engine-source-panel-recency-extension` remains absent, accepted rows added `0`, source/control evidence acquired false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Next

Preserve the Current Cursor next action. Continue only after a source owner publishes or approves valid post-cutoff R5 `MainRegimeV2` rows with provenance, or after another required target root is unlocked.
