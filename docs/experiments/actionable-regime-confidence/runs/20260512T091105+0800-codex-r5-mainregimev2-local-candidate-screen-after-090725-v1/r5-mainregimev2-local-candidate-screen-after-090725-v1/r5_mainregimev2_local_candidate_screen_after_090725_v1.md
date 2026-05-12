# R5 MainRegimeV2 Local Candidate Screen After 090725 v1

Gate result: `r5_mainregimev2_local_candidate_screen_after_090725_v1=no_source_owned_post_2026_01_30_mainregimev2_unlock`

## Scope

Read-only local screen for post-2026-01-30 R5 MainRegimeV2 evidence and source-owned provenance hints. This artifact does not copy files, populate roots, approve local hits as source/control evidence, run verifier, selected-data AutoQuant, Pre-Bayes, BBN, CatBoost, execution-tree promotion, trade claims, or `update_goal`.

## Readback

- Candidate files scanned: `2365`.
- Unlock candidates: `0`.
- Source/control evidence acquired: `false`.
- Required-root unlock: `false`.
- Selected history: `false`.
- Canonical merge: `false`.
- Selected-data AutoQuant promotion: `false`.
- Downstream promotion rerun: `false`.
- Promotion allowed: `false`.

## Decision

No source-owned post-2026-01-30 MainRegimeV2 candidate was unlocked in the local screen. The gate remains fail-closed.

## Next

Continue source/control acquisition only. Do not run selected-data AutoQuant or downstream promotion until a valid required-root unlock and selected-history gate both pass.
