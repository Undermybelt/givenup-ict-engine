# Root Transition Triad ict-engine Fail-Closed Summary v1

Run id: `20260511T193803+0800-codex-board-b-root-transition-triad-clean-v1`.

- Branch RC-SPA gate: `fail:required_root_branch_hard_gates_failed`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Clean RC-SPA pack: stable profit score `76.25`, variant rows `61,896`, selected rows `11,633`, branch paths passed `0/5`.
- Selected root counts: `Bull=6,548`, `Bear=2,161`, `Sideways=2,896`, `Crisis=28`, `Manipulation(scoped)=0`.
- Real-trade wire: `ict-engine-fail-closed/root_transition_triad_clean_real_trades_wire_v1.jsonl`, `11,633` records.
- Real-trade ingest dry-run: latest preview parsed `11,633/11,633` with `trades_invalid=0`, `force=true`, `dry_run=true`, and `feedback_records_inserted=0`; an earlier same-hash preview parsed `11,633/11,633` with `trades_invalid=0`.
- Pre-Bayes status: `gate=unavailable`, `policy=unavailable`, `soft_evidence=unavailable`.
- CatBoost/path-ranker status: `runtime_selection=disabled`, `runtime_matches=0`, `ready=false`.
- Workflow status: `no_workflow_state`.
- Provider status snapshot: `entry_model=2/2`, `live_runtime=1/3`, `local_runtime=1/2`, `market_data=2/7`; ready providers include `yfinance`, `kraken_cli`, and `tradingview_mcp`; `ibkr`, `ibkr_bridge`, and `kraken_public` are configured but unhealthy in this runtime.
- Pre-Bayes / BBN / CatBoost / execution-tree remain fail-closed because not every required branch hard gate passed.
- This is a fail-closed readback, not a promoted profitability packet.

Primary blocker: Bull=fail:reject_overfit_risk; Bear=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60; Sideways=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60; Manipulation(scoped)=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60
