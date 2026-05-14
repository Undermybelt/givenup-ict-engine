# Crypto Options Breadth RC-SPA v1

Run id: `20260512T024354+0800-codex-board-b-b2r-repeat-crypto-options-breadth-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `82.3463`
- Variant trade rows: `859`
- Selected trade rows: `492`
- Price roots passed: `0/4`
- Options auxiliary rows: `1038` from `binance,bybit`
- Downstream: `not_started:blocked_by_branch_rc_spa_hard_gates`

## Branch Summary

| Root | Variant | Trades | Win % | LCB95 | Sharpe | PF | Specificity | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `crypto_equity_risk_on_h12` | 183 | 40.984 | -0.007840 | -1.7801 | 0.716 | -0.001936 | 41.0270 | `fail:reject_insufficient_test_folds|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Bear | `equity_crypto_breakdown_h16` | 2 | 0.000 | -0.091411 | -26.7743 | 0.000 | -0.082457 | 0.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Sideways | `low_vol_range_fade_h6` | 307 | 51.466 | -0.001836 | 0.5378 | 1.080 | 0.005546 | 82.3463 | `fail:reject_insufficient_test_folds|reject_no_positive_edge` |

## Artifacts

- Report JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T024354-codex-board-b-b2r-repeat-crypto-options-breadth-v1/branch-rc-spa/crypto_options_breadth_rc_spa_report_v1.json`
- Selected rows: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T024354-codex-board-b-b2r-repeat-crypto-options-breadth-v1/branch-rc-spa/crypto_options_breadth_selected_trades_v1.csv`
- Variant rows: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T024354-codex-board-b-b2r-repeat-crypto-options-breadth-v1/branch-rc-spa/crypto_options_breadth_variant_trades_v1.csv`
- Strategy library: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T024354-codex-board-b-b2r-repeat-crypto-options-breadth-v1/branch-rc-spa/strategy_library_crypto_options_breadth_v1.json`
- Real-trade JSONL: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T024354-codex-board-b-b2r-repeat-crypto-options-breadth-v1/branch-rc-spa/crypto_options_breadth_real_trades_v1.jsonl`

## Next

Do not run downstream for this packet; use as nursery feedback for root coverage and options-breadth data repair.
