# RootTransitionTriad ict-engine Fail-Closed Summary v1

Run id: `20260511T192018+0800-codex-board-b-root-transition-triad-v1`.

- Branch RC-SPA gate: `fail:required_root_branch_hard_gates_failed`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Board cursor metric pack: final `uv_run` report `branch-rc-spa/root_transition_triad_rc_spa_report_v1.md`; stable profit score `76.25`, variant rows `61,896`, selected rows `11,633`, branch paths passed `0/5`.
- Final selected root counts: `Bull=6,548`, `Bear=2,161`, `Sideways=2,896`, `Crisis=28`, `Manipulation(scoped)=0`.
- Supplemental real-trade wire: `ict-engine-fail-closed/root_transition_triad_real_trades_wire_v1.jsonl` from the concurrent earlier pack, `3,358` rows; it is not the active cursor metric pack.
- Real-trade ingest dry-run: `3358/3358` parsed, `trades_invalid=0`, `force=true` used only to refresh logs after an earlier same-content dry-run ledger entry.
- Pre-Bayes status: `gate=unavailable`, `policy=unavailable`, `soft_evidence=unavailable`.
- CatBoost/path-ranker status: `runtime_selection=disabled`, `runtime_matches=0`, `ready=false`.
- Workflow status: `no_workflow_state`.
- Pre-Bayes / BBN / CatBoost / execution-tree remain fail-closed because not every required branch hard gate passed.
- This is a fail-closed readback, not a promoted profitability packet.

Primary blocker: Bull=fail:reject_overfit_risk; Bear=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60; Sideways=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60; Manipulation(scoped)=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60
