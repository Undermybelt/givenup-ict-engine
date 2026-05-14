# Tomac NQ Nonzero Candidate Probe v1

Run id: `20260512T002251+0800-codex-board-b-local-nq-nonzero-candidate-probe-v1`

## Decision

This run resolves the prior `zero_trade_auto_quant_candidate` blocker only at the measurement layer: the local Auto-Quant/Freqtrade path emitted real NQ trades. It does not promote a profitability factor.

- Gate result: `fail:measured_nonzero_but_branch_rc_spa_rejected`
- Stable profit score: `17.1500`
- Trade rows: `9`
- Root trade counts: `{'Bull': 0, 'Bear': 6, 'Sideways': 3, 'Crisis': 0}`
- Downstream consumption: `fail_closed:parse_and_status_probe_only`
- Primary blocker: Local NQ Auto-Quant produced nonzero trades, but the candidate is negative overall and far below root-first support/fold/edge gates.

## Branch Summary

| Root | Trades | Folds | Win Rate | Mean PnL | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | 0 | 0 | 0.0000 | 0.000000 | 0.000000 | 1.00 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Bear | 6 | 2 | 0.3333 | -0.008651 | -0.016244 | 1.00 | -1.7284 | 8.6235 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Sideways | 3 | 2 | 0.6667 | -0.003554 | -0.012653 | 1.00 | -0.4250 | 17.1500 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | 0 | 0 | 0.0000 | 0.000000 | 0.000000 | 1.00 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Artifacts

- Auto-Quant log: `docs/experiments/actionable-regime-confidence/runs/20260512T002251-codex-board-b-local-nq-nonzero-candidate-probe-v1/logs/01_tomac_nq_killzone_breakout.out`
- Source zip: `/Users/thrill3r/Auto-Quant/user_data/backtest_results/backtest-result-2026-05-12_00-27-36.zip`
- Trade rows: `docs/experiments/actionable-regime-confidence/runs/20260512T002251-codex-board-b-local-nq-nonzero-candidate-probe-v1/branch-rc-spa/tomac_nq_nonzero_candidate_trade_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260512T002251-codex-board-b-local-nq-nonzero-candidate-probe-v1/branch-rc-spa/tomac_nq_nonzero_candidate_branch_summary_v1.csv`
- ict-engine wire JSONL: `docs/experiments/actionable-regime-confidence/runs/20260512T002251-codex-board-b-local-nq-nonzero-candidate-probe-v1/ict-engine-downstream/tomac_nq_nonzero_candidate_real_trades_v1.jsonl`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T002251-codex-board-b-local-nq-nonzero-candidate-probe-v1/checks/tomac_nq_nonzero_candidate_assertions_v1.out`

## Next

- Keep this as fail-closed measurement evidence; next switch to a denser NQ/local-feather family or user-selected dataset before promotion probes.
