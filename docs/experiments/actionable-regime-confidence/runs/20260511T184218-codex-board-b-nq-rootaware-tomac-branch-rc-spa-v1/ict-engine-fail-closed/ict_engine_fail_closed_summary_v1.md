# NQ Root-Aware Tomac ict-engine Fail-Closed Readback v1

Run id: `20260511T184218+0800-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1`.

Parent run root: `docs/experiments/actionable-regime-confidence/runs/20260511T184218-codex-board-b-nq-rootaware-tomac-branch-rc-spa-v1`.

## Purpose

Verify that the completed `TomacNQRootAwareBranchMatrixV1` branch-path artifact can be parsed by ict-engine real-trade ingestion without promoting it after RC-SPA rejection.

This is a fail-closed downstream readback. It does not mark the candidate as pre-Bayes, BBN, CatBoost/path-ranker, execution-tree, or feedback eligible.

## Inputs

- Branch RC-SPA report: `../branch-rc-spa/nq_rootaware_tomac_branch_rc_spa_report_v1.json`
- Source selected branch rows: `../branch-rc-spa/nq_rootaware_tomac_branch_path_trades_v1.csv`
- Converted ict-engine trade wire: `nq_rootaware_tomac_real_trades_wire_v1.jsonl`
- Isolated state dir: `state/`
- Converter: `nq_rootaware_tomac_real_trades_wire_v1.py`

## ict-engine Readback

| Surface | Command output | Result |
|---|---|---|
| Real-trade ingest | `logs/auto_quant_ingest_real_trades_dry_run.out` | Dry-run only; parsed `6174/6174` records, `trades_invalid=0`, `feedback_records_inserted=0`. |
| Pre-Bayes status | `logs/pre_bayes_status_human.out` | `gate=unavailable`; no promoted workflow state exists for this rejected candidate. |
| Policy training status | `logs/policy_training_status_human.out` | Structural path-ranking target export is missing; runtime selection remains disabled. |
| Workflow status | `logs/workflow_status_human.out` | `no_workflow_state`; next route is replay/factor/live bootstrap, not execution promotion. |

## Decision

`TomacNQRootAwareBranchMatrixV1` remains rejected because every branch path failed RC-SPA hard gates before downstream promotion:

- Stable profit score: `61.0545`
- Branches passed: `0/5`
- Selected branch rows: `Bull=4080`, `Bear=803`, `Sideways=1109`, `Crisis=182`, `Manipulation(scoped)=0`
- Variant branch rows: `23300`
- Downstream status: `not_consumed_nq_rootaware_tomac_rc_spa_rejected_ict_engine_fail_closed`

Next action remains: add real crisis/direct-event rows for scoped Manipulation or synthesize another root-aware recipe that improves Bear/Sideways/Crisis without relaxing RC-SPA gates.
