# Bear/Sideways/Crisis Cost Repair RC-SPA v1

Run id: `20260512T031036+0800-codex-board-b-b2r-bear-sideways-crisis-cost-repair-v1`.

## Decision

- Gate result: `fail:required_root_or_scoped_manipulation_hard_gates_failed`
- Stable profit score: `90.0000`
- Minimum required branch score: `50.0000`
- Variant trade rows: `57833`
- Selected price-root rows: `19702`
- Price roots passed: `2/4`
- Direct Manipulation component: `pass:direct_manipulation_stop_tp_candidate`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bear/Sideways/Crisis cost-repair panel repaired the missing fwd3 horizon, kept the NQ long-history source-root join, and combined the scoped Manipulation component, but at least one required branch RC-SPA gate still failed.

## Inputs

- Auto-Quant data root: `/Users/thrill3r/Auto-Quant/user_data/data`
- Source-root labels: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` (`^IXIC`)
- Accepted regime artifact: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Scoped Manipulation component: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/checks/manipulation_stop_tp_grid_v2_assertions.out`

## Branch Summary

| Root | Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | Specificity | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `bull_cost_breakout_h72_r100_v12` | 10100 | 15 | 195 | 0.9333 | 0.001665 | 0.00 | 12.4617 | 0.578 | 84.0000 | `fail:reject_no_regime_specificity` |
| Bear | `bear_cap_rebound_h72_r120` | 3032 | 13 | 52 | 0.7692 | 0.003187 | 0.00 | 6.2092 | 1.936 | 86.5385 | `pass` |
| Sideways | `side_band_revert_h24_z6_a12` | 6064 | 15 | 108 | 0.6667 | -0.000080 | 0.00 | 1.1659 | 0.064 | 50.0000 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | `crisis_rebound_h72_r80` | 506 | 5 | 16 | 1.0000 | 0.016424 | 0.00 | 11.5228 | 9.941 | 90.0000 | `pass` |
| Manipulation(scoped) | `short_tp120_sl060_h72` | 13535 | 12 | 1 | 0.7500 | 0.005609 | 0.00 | 0.0000 | 999.000 | 100.0000 | `pass:direct_manipulation_stop_tp_candidate` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T031036-codex-board-b-b2r-bear-sideways-crisis-cost-repair-v1/bear-sideways-crisis-cost-repair/bear_sideways_crisis_cost_repair_rc_spa_v1.json`
- Input manifest: `docs/experiments/actionable-regime-confidence/runs/20260512T031036-codex-board-b-b2r-bear-sideways-crisis-cost-repair-v1/bear-sideways-crisis-cost-repair/bear_sideways_crisis_cost_repair_inputs_v1.json`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260512T031036-codex-board-b-b2r-bear-sideways-crisis-cost-repair-v1/bear-sideways-crisis-cost-repair/bear_sideways_crisis_cost_repair_branch_summary_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260512T031036-codex-board-b-b2r-bear-sideways-crisis-cost-repair-v1/bear-sideways-crisis-cost-repair/bear_sideways_crisis_cost_repair_variant_rows_v1.csv`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260512T031036-codex-board-b-b2r-bear-sideways-crisis-cost-repair-v1/bear-sideways-crisis-cost-repair/bear_sideways_crisis_cost_repair_selected_rows_v1.csv`
- Strategy library: `docs/experiments/actionable-regime-confidence/runs/20260512T031036-codex-board-b-b2r-bear-sideways-crisis-cost-repair-v1/bear-sideways-crisis-cost-repair/strategy_library_bear_sideways_crisis_cost_repair_v1.json`
- Real-trade JSONL: `docs/experiments/actionable-regime-confidence/runs/20260512T031036-codex-board-b-b2r-bear-sideways-crisis-cost-repair-v1/bear-sideways-crisis-cost-repair/bear_sideways_crisis_cost_repair_real_trades_v1.jsonl`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T031036-codex-board-b-b2r-bear-sideways-crisis-cost-repair-v1/checks/bear_sideways_crisis_cost_repair_v1_assertions.out`

## Next

- Do not run downstream. Use this as nursery feedback: keep the fwd3-capable NQ source-root join and repair the failing branch gate(s), especially Sideways/Crisis edge and source-owned Manipulation PnL, before another downstream attempt.
