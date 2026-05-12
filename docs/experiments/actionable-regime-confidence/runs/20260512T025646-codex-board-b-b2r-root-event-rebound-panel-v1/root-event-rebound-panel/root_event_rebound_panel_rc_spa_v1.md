# B2R Root Event Rebound Provider Panel v1

Run id: `20260512T025646+0800-codex-board-b-b2r-root-event-rebound-panel-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `85.0000`
- Selected trade rows: `11075`
- Variant trade rows: `38750`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Root trade counts: `{'Bull': 5211, 'Bear': 3618, 'Sideways': 1876, 'Crisis': 370, 'Manipulation(scoped)': 3211}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: RootEventReboundCarryV1 repaired root coverage and positive-edge depth for the four price roots, but unchanged RC-SPA hard gates still fail on fold inconsistency, overfit/specificity, and the existing scoped Manipulation component.

## Inputs

- Auto-Quant data root: `/Users/thrill3r/Auto-Quant/user_data/data`
- Board A source roots: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv`
- Accepted regime artifact: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Existing scoped Manipulation component: `docs/experiments/actionable-regime-confidence/runs/20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/branch-rc-spa/root_plus_manip_bridge_branch_summary_v1.csv`

## Branch Summary

| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | Specificity | RC-SPA | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | 5211 | 6 | 96 | 0.8333 | 0.022079 | 0.25 | 16.0905 | 1.044 | 72.9366 | `fail:reject_tail_risk|reject_no_regime_specificity` |
| Bear | 3618 | 5 | 33 | 0.8000 | 0.018458 | 0.00 | 13.1743 | 0.842 | 82.0000 | `fail:reject_tail_risk|reject_no_regime_specificity` |
| Sideways | 1876 | 6 | 34 | 0.8333 | 0.022451 | 0.00 | 8.6503 | 1.203 | 84.5305 | `fail:reject_tail_risk` |
| Crisis | 370 | 5 | 4 | 1.0000 | 0.019406 | 0.00 | 10.6410 | 0.949 | 85.0000 | `fail:reject_no_regime_specificity` |
| Manipulation(scoped) | 3211 | 13 | 1 | 0.5385 | -0.001004 | 1.00 | 0.6958 | -0.020 | 30.0000 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T025646-codex-board-b-b2r-root-event-rebound-panel-v1/root-event-rebound-panel/root_event_rebound_panel_rc_spa_v1.json`
- Provider panel inputs: `docs/experiments/actionable-regime-confidence/runs/20260512T025646-codex-board-b-b2r-root-event-rebound-panel-v1/root-event-rebound-panel/root_event_rebound_panel_inputs_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260512T025646-codex-board-b-b2r-root-event-rebound-panel-v1/root-event-rebound-panel/root_event_rebound_panel_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260512T025646-codex-board-b-b2r-root-event-rebound-panel-v1/root-event-rebound-panel/root_event_rebound_panel_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260512T025646-codex-board-b-b2r-root-event-rebound-panel-v1/root-event-rebound-panel/root_event_rebound_panel_branch_summary_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T025646-codex-board-b-b2r-root-event-rebound-panel-v1/checks/root_event_rebound_panel_v1_assertions.out`

## Next

- Keep fail-closed. The useful nursery signal is that NQ long-history Crisis rebound and crypto shock-rebound/low-vol branches fix zero/thin root coverage; the next repair must either improve rule-level fold consistency/specificity without relaxing gates or provide a source-owned direct Manipulation PnL component instead of reusing the failing bridge.
