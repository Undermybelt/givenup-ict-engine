# NQ Root-Adaptive Event Panel RC-SPA v1

Run id: `20260512T031912+0800-codex-board-b-nq-cost-crisis-repair-v2`.

## Decision

- Gate result: `fail:required_root_or_scoped_manipulation_hard_gates_failed`
- Stable profit score: `90.0000`
- Minimum required branch score: `85.1206`
- Variant trade rows: `72362`
- Selected price-root rows: `12283`
- Price roots passed: `3/4`
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
| Bull | `bull_source_root_carry_h72` | 10663 | 15 | 129 | 0.8000 | 0.001661 | 0.00 | 12.2827 | 1.684 | 87.0000 | `pass` |
| Bear | `bear_oversold_high_vix_rebound_h72` | 762 | 7 | 22 | 0.8571 | 0.008531 | 0.00 | 6.4649 | 12.278 | 87.8571 | `pass` |
| Sideways | `sideways_deep_low_z_low_conf_rebound_h48` | 274 | 5 | 20 | 1.0000 | 0.005217 | 1.00 | 7.0102 | 5.622 | 85.1206 | `fail:reject_overfit_risk` |
| Crisis | `crisis_flush_rebound_h72` | 584 | 5 | 19 | 1.0000 | 0.016401 | 0.00 | 12.1967 | 24.857 | 90.0000 | `pass` |
| Manipulation(scoped) | `short_tp120_sl060_h72` | 13535 | 12 | 1 | 0.7500 | 0.005609 | 0.00 | 0.0000 | 999.000 | 100.0000 | `pass:direct_manipulation_stop_tp_candidate` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T031912-codex-board-b-nq-cost-crisis-repair-v2/nq-cost-crisis-repair-v2/nq_cost_crisis_repair_rc_spa_v2.json`
- Input manifest: `docs/experiments/actionable-regime-confidence/runs/20260512T031912-codex-board-b-nq-cost-crisis-repair-v2/nq-cost-crisis-repair-v2/nq_cost_crisis_repair_inputs_v2.json`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260512T031912-codex-board-b-nq-cost-crisis-repair-v2/nq-cost-crisis-repair-v2/nq_cost_crisis_repair_branch_summary_v2.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260512T031912-codex-board-b-nq-cost-crisis-repair-v2/nq-cost-crisis-repair-v2/nq_cost_crisis_repair_variant_rows_v2.csv`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260512T031912-codex-board-b-nq-cost-crisis-repair-v2/nq-cost-crisis-repair-v2/nq_cost_crisis_repair_selected_rows_v2.csv`
- Strategy library: `docs/experiments/actionable-regime-confidence/runs/20260512T031912-codex-board-b-nq-cost-crisis-repair-v2/nq-cost-crisis-repair-v2/strategy_library_nq_cost_crisis_repair_v2.json`
- Real-trade JSONL: `docs/experiments/actionable-regime-confidence/runs/20260512T031912-codex-board-b-nq-cost-crisis-repair-v2/nq-cost-crisis-repair-v2/nq_cost_crisis_repair_real_trades_v2.jsonl`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T031912-codex-board-b-nq-cost-crisis-repair-v2/checks/nq_cost_crisis_repair_v2_assertions.out`

## Next

- Do not run downstream. Use this as nursery feedback: keep the NQ long-history source-root join, but repair the failing price-root gate(s) before another downstream attempt.
