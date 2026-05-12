# Root Repair Panel RC-SPA v1

Run id: `20260512T030058+0800-codex-board-b-b2r-root-repair-panel-v1`

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `31.2705`
- Variant trade rows: `20347`
- Selected trade rows: `10444`
- Price roots passed: `0/4`
- Selected root counts: `{'Bull': 4365, 'Bear': 340, 'Sideways': 5722, 'Crisis': 17}`
- Downstream: `not_started:blocked_by_branch_rc_spa_hard_gates`

## Selected Branch Summary

| Root | Variant | Trades | Folds | Fold + | LCB5 | 2x LCB5 | DSR | PBO | Specificity | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `nq_crypto_trend_followthrough_h24` | 4365 | 5 | 0.400 | -0.000844 | -0.001644 | -2.3816 | 0.600 | -0.357 | 26.7388 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Bear | `btc_deleveraging_short_h12` | 340 | 5 | 0.200 | -0.002930 | -0.003730 | 0.5514 | 0.800 | 999.000 | 31.2705 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60` |
| Sideways | `nq_lowvol_range_fade_h12` | 5722 | 5 | 0.200 | -0.001178 | -0.001978 | -8.5033 | 0.800 | -0.976 | 25.4636 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | `nq_tail_short_h12` | 17 | 3 | 0.333 | -0.015853 | -0.016653 | -3.7892 | 0.667 | -10.416 | 13.7749 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Provider / Inputs

- Local Auto-Quant panel rows: `29294` from `2021-01-14T06:00:00Z` to `2025-12-30T20:00:00Z`
- Options auxiliary rows: `1038`
- Direct Manipulation component present: `True`

## Artifacts

- Report JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T030058-codex-board-b-b2r-root-repair-panel-v1/branch-rc-spa/root_repair_panel_rc_spa_report_v1.json`
- Selected rows: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T030058-codex-board-b-b2r-root-repair-panel-v1/branch-rc-spa/root_repair_panel_selected_trades_v1.csv`
- Variant rows: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T030058-codex-board-b-b2r-root-repair-panel-v1/branch-rc-spa/root_repair_panel_variant_trades_v1.csv`
- Strategy library: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T030058-codex-board-b-b2r-root-repair-panel-v1/branch-rc-spa/strategy_library_root_repair_panel_v1.json`
- Real-trade JSONL: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T030058-codex-board-b-b2r-root-repair-panel-v1/branch-rc-spa/root_repair_panel_real_trades_v1.jsonl`
- Path scores: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T030058-codex-board-b-b2r-root-repair-panel-v1/branch-rc-spa/root_repair_panel_path_scores_v1.csv`

## Next

Do not run promotion downstream for this packet; use the root failure tags as nursery feedback for the next B2R repair.
