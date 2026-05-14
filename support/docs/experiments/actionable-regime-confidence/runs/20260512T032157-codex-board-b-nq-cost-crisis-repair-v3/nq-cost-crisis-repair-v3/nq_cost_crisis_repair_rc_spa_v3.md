# NQ Cost/Crisis Repair RC-SPA v3

Run id: `20260512T032157+0800-codex-board-b-nq-cost-crisis-repair-v3`.

## Decision

- Gate result: `pass`
- Stable profit score: `90.0000`
- Minimum required branch score: `85.8501`
- Variant trade rows: `75768`
- Selected price-root rows: `15415`
- Price roots passed: `4/4`
- Direct Manipulation component: `pass:direct_manipulation_stop_tp_candidate`
- Downstream consumption: `ready_for_pre_bayes_bbn_catboost_execution_tree`
- Primary blocker: All price roots plus scoped Manipulation passed; run ordered downstream before any promotion claim.

## Inputs

- Auto-Quant data root: `/Users/thrill3r/Auto-Quant/user_data/data`
- Source-root labels: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` (`^IXIC`)
- Accepted regime artifact: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Scoped Manipulation component: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/checks/manipulation_stop_tp_grid_v2_assertions.out`

## Branch Summary

| Root | Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | Specificity | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `bull_source_root_carry_h72` | 10663 | 15 | 129 | 0.8000 | 0.001661 | 0.00 | 12.2827 | 1.385 | 85.8501 | `pass` |
| Bear | `bear_oversold_high_vix_rebound_h72` | 762 | 7 | 22 | 0.8571 | 0.008531 | 0.00 | 6.4649 | 10.472 | 87.8571 | `pass` |
| Sideways | `sideways_calm_vix_z_revert_h72` | 3406 | 10 | 23 | 0.8000 | 0.003278 | 0.00 | 13.4757 | 3.068 | 87.0000 | `pass` |
| Crisis | `crisis_flush_rebound_h72` | 584 | 5 | 19 | 1.0000 | 0.016401 | 0.00 | 12.1967 | 21.011 | 90.0000 | `pass` |
| Manipulation(scoped) | `short_tp120_sl060_h72` | 13535 | 12 | 1 | 0.7500 | 0.005609 | 0.00 | 0.0000 | 999.000 | 100.0000 | `pass:direct_manipulation_stop_tp_candidate` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/nq-cost-crisis-repair-v3/nq_cost_crisis_repair_rc_spa_v3.json`
- Input manifest: `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/nq-cost-crisis-repair-v3/nq_cost_crisis_repair_inputs_v3.json`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/nq-cost-crisis-repair-v3/nq_cost_crisis_repair_branch_summary_v3.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/nq-cost-crisis-repair-v3/nq_cost_crisis_repair_variant_rows_v3.csv`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/nq-cost-crisis-repair-v3/nq_cost_crisis_repair_selected_rows_v3.csv`
- Strategy library: `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/nq-cost-crisis-repair-v3/strategy_library_nq_cost_crisis_repair_v3.json`
- Real-trade JSONL: `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/nq-cost-crisis-repair-v3/nq_cost_crisis_repair_real_trades_v3.jsonl`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/checks/nq_cost_crisis_repair_v3_assertions.out`

## Next

- Run ict-engine Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree using the same rooted branch paths; promotion remains forbidden until downstream admits the branch.
