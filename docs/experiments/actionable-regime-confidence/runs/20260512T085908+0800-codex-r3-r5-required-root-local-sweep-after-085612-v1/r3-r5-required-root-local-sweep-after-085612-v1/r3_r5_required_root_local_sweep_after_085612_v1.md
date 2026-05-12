# R3/R5 Required Root Local Sweep After 085612 v1

Gate result: `r3_r5_required_root_local_sweep_after_085612_v1=no_crisis_r3_or_r5_mainregimev2_unlock`

## Scope

Read-only target-root sweep for Crisis-capable R3 native-subhour labels and post-2026-01-30 R5 MainRegimeV2 rows. This artifact does not copy files, populate roots, approve local labels as source/control evidence, run verifier, selected-data AutoQuant, Pre-Bayes, BBN, CatBoost, execution-tree promotion, trade claims, or `update_goal`.

## Readback

- Target roots scanned: `6`.
- R3 native-subhour roots present: `true`.
- R3 native-subhour data rows: `5032903`.
- R3 native-subhour labels: `0, 1, 3, 5, 6, Bear, Bull, FLAT / NOISE, STRONG BUY, STRONG SELL, Sideways, WEAK BUY, WEAK SELL`.
- R3 Crisis label present: `false`.
- R5 recency roots present: `false`.
- R5 MainRegimeV2 post-2026-01-30 rows: `0`.

## Decision

No Crisis-capable R3 label set or source-owned post-2026-01-30 R5 MainRegimeV2 rows were found in the required local target roots. The R3 native-subhour root remains present but non-unlocking, and the R5 recency roots remain absent.

Accepted rows added `0`; valid required-root unlock false; source/control evidence acquired false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; promotion allowed false; `update_goal=false`.

## Next

Continue source/control acquisition only. Do not run verifier, selected-data AutoQuant, Pre-Bayes/BBN, CatBoost/path-ranking, execution-tree promotion, trade claims, or `update_goal` until a valid required root unlock and selected-history gate both pass.
