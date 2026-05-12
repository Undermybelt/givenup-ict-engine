# R6 Staging Triplet Readonly Verifier After 035049 v1

Run id: `20260512T035233-codex-r6-staging-triplet-readonly-verifier-after-035049-v1`

Gate result: `r6_staging_triplet_readonly_verifier_after_035049_v1=staging_schema_ready_required_owner_export_absent_split_gates_failed_no_promotion`

## Readback

- Required owner-export verifier on `/tmp/ict-engine-board-a-r6-owner-export-v1` exited `2` with `missing_required_files`.
- Required source/control roots remained absent:
  - `/tmp/ict-engine-board-a-r6-owner-export-v1`
  - `/tmp/ict-engine-native-subhour-source-label-intake`
  - `/tmp/ict-engine-source-panel-recency-extension`
- The staging candidate `/private/tmp/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1.staging` verified as `schema_ready_unscored` with `77` positive rows, `77` matched negative rows, and `74` matched groups.
- The staging provenance says it is an isolated projection under `/tmp/ict-engine-direct-manipulation-row-intake.lock`, with `runtime_code_changed=false`, `raw_data_committed=false`, and `thresholds_relaxed=false`.
- The original `000803` calibration for the same projection had pooled direct Wilson95 LCB `0.952479911333`, but chronological, heldout-symbol, and heldout-venue split gates were all `false`.

## Decision

This is useful read-only diagnostics only. The staging triplet is not the required owner-export root, was not copied into the target root, does not approve `FLIP` controls, does not unlock canonical merge, and does not allow downstream provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion.

Promotion status: accepted rows added `0`; new confidence gate `false`; canonical merge `false`; downstream promotion rerun `false`; strict full objective `false`; trade usable `false`; `update_goal=false`.

## Artifacts

- Required root verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T035233-codex-r6-staging-triplet-readonly-verifier-after-035049-v1/command-output/direct_verifier_required_owner_export.stdout.txt`
- Staging verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T035233-codex-r6-staging-triplet-readonly-verifier-after-035049-v1/command-output/direct_verifier_staging_candidate.stdout.txt`
- Staging provenance: `docs/experiments/actionable-regime-confidence/runs/20260512T035233-codex-r6-staging-triplet-readonly-verifier-after-035049-v1/command-output/staging_candidate_provenance.pretty.json`
- Prior split metrics: `docs/experiments/actionable-regime-confidence/runs/20260512T000803-codex-r6-jpm-cbot-treasury-control-uplift-v1/r6-jpm-cbot-treasury-control-uplift/r6_jpm_cbot_treasury_split_metrics_v1.csv`

## Next

Preserve the Current Cursor next action. Continue only from explicit approval, verifier-native owner/export rows/source-owned normal controls, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before canonical merge and downstream promotion.
