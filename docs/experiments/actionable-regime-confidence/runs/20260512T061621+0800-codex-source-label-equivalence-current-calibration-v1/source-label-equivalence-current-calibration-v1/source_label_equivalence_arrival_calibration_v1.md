# Source Label Equivalence Current Calibration v1

Run id: `20260512T061621+0800-codex-source-label-equivalence-current-calibration-v1`

Gate result: `source_label_equivalence_arrival_calibration_v1=source_confidence_scored_no_acceptance`

## Scope

This is a compact readback for the repeated current calibration over `/tmp/ict-engine-source-label-equivalence-intake`. It materializes the board-referenced `061621` files from the registered `061421` calibration metrics. It does not copy files into R3/R5/R6 target roots, approve source/control evidence, mutate shared intake roots, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Readback

- Source-label equivalence root: present.
- Verifier status: `schema_ready_unscored`.
- Row count: `248440`.
- Missing confidence rows: `0`.
- Accepted source-confidence labels: `0/4`.
- Accepted labels: `[]`.
- Blocked labels: `Bear`, `Bull`, `Crisis`, and `Sideways`.

All four labels remain below the `>=0.95` Wilson95 lower-bound gate across required chronological and heldout splits in the registered `061421` calibration.

## Decision

This is non-promoting repeated calibration evidence. Accepted rows added `0`, new confidence gate false, source/control evidence acquired false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

Required promotion roots remain absent:

- `/tmp/ict-engine-board-a-r6-owner-export-v1`
- `/tmp/ict-engine-native-subhour-source-label-intake`
- `/tmp/ict-engine-source-panel-recency-extension`

## Next

Do not promote repeated source-label equivalence calibration evidence. Continue only after explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 recency rows, or source-owned R3 native sub-hour labels unlock a required target root before rerunning direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order.
