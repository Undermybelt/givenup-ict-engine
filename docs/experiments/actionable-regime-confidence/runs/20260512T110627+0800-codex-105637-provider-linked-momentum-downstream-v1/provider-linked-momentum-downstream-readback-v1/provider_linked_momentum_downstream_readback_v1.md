# Provider-Linked Momentum Downstream Readback v1

Run id: `20260512T110627+0800-codex-105637-provider-linked-momentum-downstream-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T105637+0800-codex-provider-linked-aq-provenance-probe-v1`

## Purpose

Read back the downstream ict-engine chain for the already-counted `105637` provider-linked AQ diagnostic without promoting it or counting `105637` again.

## Evidence Inspected

- Exit markers: `checks/*.exit`
- Missing trade artifact errors: `command-output/01_ingest_real_trades_dry_run.err`, `command-output/02_ingest_real_trades_force.err`
- Pre-Bayes status: `command-output/03_pre_bayes_status.out`
- Policy/CatBoost status: `command-output/04_policy_training_status_before_export.out`, `command-output/06_policy_training_status_after_export.out`
- Structural target summary: `state_ingest/B2R_PROVIDER_LINKED_MOMENTUM_105637/policy_training/structural_path_ranking_target_summary.json`
- Structural bundle, execution candidate, full workflow: `command-output/07_workflow_structural_bundle.out`, `command-output/08_workflow_execution_candidate.out`, `command-output/09_workflow_full.out`

## Result

The downstream chain is settled fail-closed.

- `01_ingest_real_trades_dry_run` and `02_ingest_real_trades_force` exited `1` because `derived/provider_linked_momentum_105637_real_trades.jsonl` was missing.
- `03_pre_bayes_status` exited `0`, but all latest Pre-Bayes fields were null or empty and no filtered assignments were present.
- `04_policy_training_status_before_export` exited `0`, but both entry models had `matched_rows=0` and were not ready for BBN or CatBoost.
- `05_export_structural_path_ranking_target` exited `0` and wrote one target row.
- `06_policy_training_status_after_export` exited `0`, but the target remained immature: `rows=1`, `mature_rows=0`, `raw_scored_mature=0/30`, `production_validation=0/30`, `observation_validation=0/30`, `trainer_artifact=missing`, and `runtime_selection=disabled`.
- `07_workflow_structural_bundle`, `08_workflow_execution_candidate`, and `09_workflow_full` exited `0`, but the branch stayed `observe` / `fail_closed` with `ready=false`, `actionable=false`, `current_posterior=0.0`, and `No workflow snapshot exists yet`.

## Artifact Integrity Note

The current board tail references `docs/experiments/actionable-regime-confidence/runs/20260512T110250+0800-codex-board-b-104703-provider-matrix-tomac-v1`, but that directory was not present under the local run root during this readback. Do not treat `110250` as artifact-backed provider-matrix evidence unless the missing root appears and is verified.

## Decision

Gate: `105637_provider_linked_momentum_downstream_v1=real_trade_artifact_missing_downstream_bootstrap_fail_closed_no_promotion`

Accepted rows added: `0`. Mature rooted branch observations promoted: `0`. Source/control evidence acquired: `false`. Explicit selected history: `false`. Canonical merge: `false`. Six-provider AQ matrix satisfied: `false`. Selected-data AutoQuant promotion: `false`. Downstream promotion: `false`. Strict full objective: `false`. Trade usable: `false`. Promotion allowed: `false`. `update_goal=false`.

## Next

Do not count `105637` again. The next useful slice is either a provider-matrix AQ repair that produces real same-run provider/TOMAC evidence, or a downstream repair that first materializes the exact real-trades artifact and then produces non-empty Pre-Bayes, BBN, CatBoost/path-ranker, and execution-tree evidence on the same rooted branch.
