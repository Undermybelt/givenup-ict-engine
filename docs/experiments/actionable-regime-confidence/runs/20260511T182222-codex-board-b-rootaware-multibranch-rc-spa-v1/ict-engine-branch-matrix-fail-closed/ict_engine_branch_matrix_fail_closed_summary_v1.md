# RootAwareMultiBranchV1 Branch-Matrix ict-engine Fail-Closed Readback v1

Run id: `20260511T183429+0800-codex-board-b-rootaware-multibranch-branch-matrix-ict-engine-fail-closed-v1`.

Parent run root: `docs/experiments/actionable-regime-confidence/runs/20260511T182222-codex-board-b-rootaware-multibranch-rc-spa-v1`.

## Purpose

Verify that the latest `RootAwareMultiBranchV1` branch/variant matrix artifact can be parsed by ict-engine real-trade ingestion without promoting it after RC-SPA rejection.

This is a fail-closed downstream readback. It does not mark the candidate as pre-Bayes, BBN, CatBoost, execution-tree, or feedback eligible.

## Inputs

- Branch-matrix RC-SPA report: `../branch-rc-spa/rootaware_multibranch_branch_rc_spa_report_v1.json`
- Source branch trade rows: `../branch-rc-spa/rootaware_multibranch_branch_path_trades_v1.csv`
- Converted ict-engine trade wire: `rootaware_multibranch_branch_matrix_real_trades_wire_v1.jsonl`
- Isolated state dir: `state/`

## ict-engine Readback

| Surface | Command output | Result |
|---|---|---|
| Real-trade ingest | `logs/auto_quant_ingest_real_trades_dry_run.out` | Dry-run only; parsed `5198/5198` records, `trades_invalid=0`, `feedback_records_inserted=0`. |
| Pre-Bayes status | `logs/pre_bayes_status_human.out` | `gate=unavailable`; no promoted workflow state exists for this rejected candidate. |
| Policy training status | `logs/policy_training_status_human.out` | Structural path-ranking target export is missing; runtime selection remains disabled. |
| Workflow status | `logs/workflow_status_human.out` | `no_workflow_state`; next route is replay/factor/live bootstrap, not execution promotion. |

## Decision

`RootAwareMultiBranchV1` branch/variant matrix remains rejected because every branch path failed RC-SPA hard gates before downstream promotion:

- Stable profit score: `34.8283`
- Branches passed: `0/5`
- Branch counts: `Bull=2550`, `Bear=1420`, `Sideways=1134`, `Crisis=94`, `Manipulation(scoped)=0`
- Downstream status: `not_consumed_branch_matrix_rc_spa_rejected_ict_engine_fail_closed`

Next action remains: acquire a broader crisis-capable Board A root panel / market set, or synthesize a second root-aware recipe with enough Bear/Sideways/Crisis trade and fold depth before attempting downstream branch consumption.
