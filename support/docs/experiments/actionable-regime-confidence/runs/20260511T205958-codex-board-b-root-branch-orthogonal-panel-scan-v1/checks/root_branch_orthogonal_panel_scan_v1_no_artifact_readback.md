# RootBranchOrthogonalPanelScanV1 Preliminary No-Artifact Readback

Observed at: `20260511T210434+0800`

Superseded at: `20260511T211241+0800`

Status: `superseded:later_rc_spa_report_observed`

Do not use this preliminary readback as final rejection evidence. A later readback observed a completed RC-SPA report for the same `RootBranchOrthogonalPanelScanV1` run:

- `docs/experiments/actionable-regime-confidence/runs/20260511T205958-codex-board-b-root-branch-orthogonal-panel-scan-v1/branch-rc-spa/root_branch_orthogonal_panel_scan_rc_spa_report_v1.md`

Board cursor at readback:
- `last_loop_id`: `20260511T205958+0800-codex-board-b-root-branch-orthogonal-panel-scan-v1`
- `auto_quant_recipe`: `RootBranchOrthogonalPanelScanV1`
- `backtest_run_root`: `docs/experiments/actionable-regime-confidence/runs/20260511T205958-codex-board-b-root-branch-orthogonal-panel-scan-v1`

Readback result:
- The active Python scorer process tied to the `205958` root-branch scan had exited before this readback.
- No branch RC-SPA report, branch rows, provider packet, or downstream consumption artifact existed under the declared run root before this fail-closed check directory was created.
- No Pre-Bayes, BBN, CatBoost/path-ranker, or execution-tree promotion was started from this run.

Preliminary gate state at readback:
- `hard_gate_result`: `fail:run_exited_before_report`
- `downstream_consumption`: `not_started:no_rc_spa_report`
- `promotion_state`: `rejected`

Next action:
- Repair or replace `RootBranchOrthogonalPanelScanV1` with a materially different Bull/Bear/Sideways/Crisis root-branch candidate.
- Keep the `20260511T205047` scoped direct `Manipulation` component pass as a component only until a separate root-branch candidate passes unchanged RC-SPA.
