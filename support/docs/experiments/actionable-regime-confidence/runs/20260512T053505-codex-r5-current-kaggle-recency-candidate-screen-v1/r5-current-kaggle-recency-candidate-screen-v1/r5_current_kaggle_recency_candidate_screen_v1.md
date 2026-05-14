# R5 Current Kaggle Recency Candidate Screen v1

Run id: `20260512T053505-codex-r5-current-kaggle-recency-candidate-screen-v1`

Gate result: `r5_current_kaggle_recency_candidate_screen_v1=no_current_post_cutoff_target_rows_no_promotion`

## Scope

Read-only current-source screen for the R5 source-panel recency blocker. This run downloads the current Kaggle source package into `/tmp` and checks exact post-cutoff target cells. It does not copy rows into `/tmp/ict-engine-source-panel-recency-extension`, generate proxy labels, mutate target roots, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Result

- Dataset: `mafaqbhatti/stock-market-regimes-20002026`.
- Rows: `245021`; date range `2000-01-03` to `2026-01-30`.
- Download matches local reference: `true`.
- Post-cutoff root rows after `2026-01-30`: `0`.
- Required R5 target files already present: `false`.
- Target root mutated: `false`.

| Ticker | Label | Split Role | Required New Sessions | Post-Cutoff Rows | Meets Min |
|---|---|---|---:|---:|---|
| `XOM` | `Sideways` | `heldout_time` | `5` | `0` | `false` |
| `UNH` | `Bear` | `calibration` | `7` | `0` | `false` |
| `^DJI` | `Sideways` | `calibration` | `7` | `0` | `false` |
| `AMD` | `Bear` | `calibration` | `10` | `0` | `false` |

## Decision

R5 remains blocked unless a source owner publishes or approves post-cutoff source rows with provenance. This screen found no qualifying post-cutoff target rows in the current public Kaggle source package, so it is not accepted regime-confidence evidence, not source/control evidence, not canonical merge input, not downstream promotion evidence, not trade evidence, and not `update_goal` authorization.
