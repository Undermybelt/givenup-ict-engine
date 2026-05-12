# R6 Bessembinder Control Cohort Source Delta v1

Run id: `20260512T051015-codex-r6-bessembinder-control-cohort-source-delta-v1`

Gate result: `r6_bessembinder_control_cohort_source_delta_v1=official_control_cohort_context_found_no_verifier_native_rows_no_promotion`

## Source Delta

This targeted web/source readback looked for a more precise R6 control-cohort basis after the Board A source/control roots remained absent and the latest qualifier screens accepted no labels.

Sources:
- Justia mirror of `CFTC v. Oystacher`, N.D. Ill. case `1:2015cv09196`, document `195`: `https://law.justia.com/cases/federal/district-courts/illinois/ilndce/1%3A2015cv09196/316889/195/`
- CFTC enforcement/news route for Oystacher spoofing context, surfaced by targeted search for the same matter.

Readback:
- The court opinion discusses Professor Bessembinder's analysis as a comparative/control-cohort style study over Oystacher flipping conduct and other market participants/non-flip activity.
- This refines the R6 owner-export ask: if the operator/source owner can provide the Bessembinder/CFTC comparison cohorts, request verifier-native rows for Oystacher flips, other flipping market participants, broader market-participant rows, and non-flip orders with provenance, product/date scope, and source-owner normal/control classification.
- This does not supply the row-level data itself. No downloadable verifier-native row file, source-owned broad normal controls, or explicit same-exhibit `FLIP` approval was acquired.

## Board Effect

Useful only as owner-export request refinement:
- Add "Bessembinder/CFTC comparison cohort" language to any renewed CME/CFTC/Court-source request.
- Preserve the existing requirement for verifier-native normal-control rows and provenance under `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- Do not populate target roots from opinion text, public summaries, or inferred control cohorts.

## Decision

Required target roots remain absent:
- `/tmp/ict-engine-board-a-r6-owner-export-v1`
- `/tmp/ict-engine-native-subhour-source-label-intake`
- `/tmp/ict-engine-source-panel-recency-extension`

Promotion status remains unchanged: accepted rows added `0`, accepted regime-confidence labels `0`, source/control evidence acquired false, new confidence gate false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Boundary

This source delta is routing/control-cohort context only. It is not accepted regime-confidence evidence, not source/control evidence, not canonical merge input, not downstream promotion evidence, not trade evidence, and not `update_goal` authorization.
