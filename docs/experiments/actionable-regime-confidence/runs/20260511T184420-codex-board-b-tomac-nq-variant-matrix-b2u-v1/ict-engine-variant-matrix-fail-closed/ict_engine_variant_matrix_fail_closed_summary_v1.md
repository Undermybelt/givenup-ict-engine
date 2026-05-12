# Tomac NQ Variant Matrix ict-engine Fail-Closed Readback v1

Run id: `20260511T185313+0800-codex-board-b-tomac-nq-variant-matrix-ict-engine-fail-closed-v1`.

Parent run root: `docs/experiments/actionable-regime-confidence/runs/20260511T184420-codex-board-b-tomac-nq-variant-matrix-b2u-v1`.

## Purpose

Verify that the active-cursor `TomacNQRootAwareVariantMatrixB2U` branch/variant matrix artifact can be parsed by ict-engine real-trade ingestion without promoting it after RC-SPA rejection.

This is a fail-closed downstream readback. It does not mark the candidate as pre-Bayes, BBN, CatBoost, execution-tree, or feedback eligible.

## Inputs

- Branch RC-SPA report: `../branch-rc-spa/tomac_nq_variant_matrix_branch_rc_spa_report_v1.json`
- Source variant branch rows: `../branch-rc-spa/tomac_nq_variant_matrix_all_variant_branch_rows_v1.csv`
- Converted ict-engine trade wire: `tomac_nq_variant_matrix_real_trades_wire_v1.jsonl`
- Direction normalization: Sideways/Crisis root context is preserved in `regime_at_entry` and structural path refs, while wire factor directions use `Neutral` for non-Bull/Bear roots and PnL-derived `Bull|Bear|Neutral` for branch-path edge factors.
- Isolated state dir: `state/`

## ict-engine Readback

| Surface | Command output | Result |
|---|---|---|
| Real-trade ingest | `logs/auto_quant_ingest_real_trades_dry_run.out` | Dry-run only; parsed `5109/5109` records, `trades_invalid=0`, `feedback_records_inserted=0`. |
| Pre-Bayes status | `logs/pre_bayes_status_human.out` | `gate=unavailable`; no promoted workflow state exists for this rejected candidate. |
| Policy training status | `logs/policy_training_status_human.out` | Structural path-ranking target export is missing; runtime selection remains disabled. |
| Workflow status | `logs/workflow_status_human.out` | `no_workflow_state`; next route is replay/factor/live bootstrap, not execution promotion. |

## Decision

`TomacNQRootAwareVariantMatrixB2U` remains rejected because every required branch path failed RC-SPA hard gates before downstream promotion:

- Stable profit score: `66.0472`
- Branches passed: `0/5`
- Selected branch rows: `Bull=431`, `Bear=522`, `Sideways=1119`, `Crisis=63`, `Manipulation(scoped)=0`
- Variant matrix rows: `5109`
- Downstream status: `not_consumed_tomac_nq_variant_matrix_rc_spa_rejected_ict_engine_fail_closed`

Next action remains: add real crisis/direct-event rows for scoped Manipulation or synthesize another NQ/root-aware recipe that improves Bear/Sideways/Crisis without relaxing RC-SPA gates.
