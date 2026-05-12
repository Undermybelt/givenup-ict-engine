# RootAwareMultiBranchV1 ict-engine Fail-Closed Readback v1

Run id: `20260511T182854+0800-codex-board-b-rootaware-multibranch-ict-engine-fail-closed-v1`.

Parent run root: `docs/experiments/actionable-regime-confidence/runs/20260511T182222-codex-board-b-rootaware-multibranch-rc-spa-v1`.

## Purpose

Verify that the current `RootAwareMultiBranchV1` branch-path artifact can be read by ict-engine surfaces without promoting it after RC-SPA rejection.

This is a fail-closed downstream readback. It does not mark the candidate as pre-Bayes, BBN, CatBoost, execution-tree, or feedback eligible.

## Inputs

- RC-SPA report: `../branch-rc-spa/rootaware_multibranch_rc_spa_report_v1.json`
- Source branch trade rows: `../branch-rc-spa/rootaware_multibranch_trades_v1.jsonl`
- Strategy library import manifest: `../branch-rc-spa/rootaware_multibranch_strategy_library_for_import_v1.json`
- Converted ict-engine trade wire: `rootaware_multibranch_real_trades_wire_v1.jsonl`
- Isolated state dir: `state/`

## ict-engine Readback

| Surface | Command output | Result |
|---|---|---|
| Auto-Quant import | `logs/auto_quant_results_import.out` | Parsed `1/1` strategy, `n_ok=1`, persisted only to isolated run-local state. |
| BBN prior init | `logs/auto_quant_prior_init_dry_run.out` | Dry-run only for `RootAwareMultiBranchV1`; counts were `362` wins / `702` losses. |
| Real-trade ingest | `logs/auto_quant_ingest_real_trades_dry_run.out` | Dry-run only; parsed `1064/1064` records, `trades_invalid=0`, `feedback_records_inserted=0`. |
| Pre-Bayes status | `logs/pre_bayes_status_human.out` | `gate=unavailable`; no promoted workflow state exists for this rejected candidate. |
| Policy training status | `logs/policy_training_status_human.out` | Structural path-ranking target export is missing; runtime selection remains disabled. |
| Workflow status | `logs/workflow_status_human.out` | `no_workflow_state`; next route is replay/factor/live bootstrap, not execution promotion. |

## Decision

`RootAwareMultiBranchV1` remains rejected because RC-SPA hard gates failed before downstream promotion:

- RC-SPA: `80.0`
- Failure reasons: `pbo`, `branch_min_total_trades_for_claimed_roots`
- Branch distribution: `Bull=1063`, `Bear=0`, `Sideways=1`, `Crisis=0`
- Downstream status: `not_consumed_rc_spa_rejected_ict_engine_fail_closed`

Next action remains: fix root-transition bleed and the PBO overfit blocker before any downstream branch promotion.
