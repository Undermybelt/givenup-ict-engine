# NQ Root-Adaptive Event Panel RC-SPA v1

Run id: `20260512T030356+0800-codex-board-b-b2r-repeat-nq-root-adaptive-v1`.

## Decision

- Gate result: `fail:required_root_or_scoped_manipulation_hard_gates_failed`
- Stable profit score: `89.9215`
- Minimum required branch score: `33.0000`
- Variant trade rows: `45463`
- Selected price-root rows: `13115`
- Price roots passed: `0/4`
- Direct Manipulation component: `pass:direct_manipulation_stop_tp_candidate`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: NQ long-history root-adaptive panel repaired row supply and combined the scoped Manipulation component, but at least one required price-root RC-SPA gate still failed.

## Inputs

- Auto-Quant data root: `/Users/thrill3r/Auto-Quant/user_data/data`
- Source-root labels: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` (`^IXIC`)
- Accepted regime artifact: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Scoped Manipulation component: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/checks/manipulation_stop_tp_grid_v2_assertions.out`

## Branch Summary

| Root | Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | Specificity | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `bull_low_vol_breakout_h36` | 8750 | 15 | 136 | 0.7333 | 0.000456 | 0.00 | 5.5338 | 999.000 | 65.1298 | `fail:reject_cost_fragile` |
| Bear | `bear_relief_fade_h12` | 2662 | 13 | 55 | 0.5385 | -0.000373 | 0.00 | 0.3911 | 999.000 | 43.9436 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60` |
| Sideways | `sideways_pop_fade_h12` | 1672 | 15 | 17 | 0.5333 | -0.000978 | 0.00 | -3.2489 | -8.612 | 33.0000 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | `crisis_flush_rebound_h24` | 31 | 2 | 6 | 1.0000 | 0.001588 | 0.00 | 1.9959 | 999.000 | 89.9215 | `fail:reject_thin_trades|reject_insufficient_test_folds` |
| Manipulation(scoped) | `short_tp120_sl060_h72` | 13535 | 12 | 1 | 0.7500 | 0.005609 | 0.00 | 0.0000 | 999.000 | 100.0000 | `pass:direct_manipulation_stop_tp_candidate` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T030356-codex-board-b-b2r-repeat-nq-root-adaptive-v1/nq-root-adaptive-panel/nq_root_adaptive_panel_rc_spa_v1.json`
- Input manifest: `docs/experiments/actionable-regime-confidence/runs/20260512T030356-codex-board-b-b2r-repeat-nq-root-adaptive-v1/nq-root-adaptive-panel/nq_root_adaptive_panel_inputs_v1.json`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260512T030356-codex-board-b-b2r-repeat-nq-root-adaptive-v1/nq-root-adaptive-panel/nq_root_adaptive_panel_branch_summary_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260512T030356-codex-board-b-b2r-repeat-nq-root-adaptive-v1/nq-root-adaptive-panel/nq_root_adaptive_panel_variant_rows_v1.csv`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260512T030356-codex-board-b-b2r-repeat-nq-root-adaptive-v1/nq-root-adaptive-panel/nq_root_adaptive_panel_selected_rows_v1.csv`
- Strategy library: `docs/experiments/actionable-regime-confidence/runs/20260512T030356-codex-board-b-b2r-repeat-nq-root-adaptive-v1/nq-root-adaptive-panel/strategy_library_nq_root_adaptive_panel_v1.json`
- Real-trade JSONL: `docs/experiments/actionable-regime-confidence/runs/20260512T030356-codex-board-b-b2r-repeat-nq-root-adaptive-v1/nq-root-adaptive-panel/nq_root_adaptive_panel_real_trades_v1.jsonl`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T030356-codex-board-b-b2r-repeat-nq-root-adaptive-v1/checks/nq_root_adaptive_panel_v1_assertions.out`

## Next

- Do not run downstream. Use this as nursery feedback: keep the NQ long-history source-root join, but repair the failing price-root gate(s) before another downstream attempt.
