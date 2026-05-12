# Source Root Stop Carry Long-Horizon RC-SPA v1

Run id: `20260511T220646+0800-codex-board-b-source-root-stop-carry-longhorizon-v1`.

## Decision

- Gate result: `pass`
- Stable profit score: `85.7407`
- Price-root paths passed: `4/4`
- Scoped Manipulation component pass consumed: `True`
- Variant rows: `53916`
- Selected rows: `12329`
- Selected root counts: `{'Bull': 4948, 'Bear': 1349, 'Sideways': 5500, 'Crisis': 532, 'Manipulation(scoped)': 13535}`
- Downstream consumption: `eligible_for_pre_bayes_bbn_catboost_execution_tree_probe`
- Primary blocker: all required branch hard gates passed; downstream chain still required before promotion

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `bull_carry_h12_sl040_tp12` | 4948 | 27 | 15 | 0.8148 | 0.002296 | 0.037 | 7.8107 | 85.7407 | `pass` |
| Bear | `bear_carry_h20_sl048_tp12` | 1349 | 22 | 17 | 0.7727 | 0.003172 | 0.227 | 4.0007 | 77.5000 | `pass` |
| Sideways | `sideways_carry_h8_sl040_tp12` | 5500 | 27 | 13 | 0.7778 | 0.002262 | 0.074 | 7.5990 | 83.7037 | `pass` |
| Crisis | `crisis_carry_h8_sl048_tp12` | 532 | 10 | 15 | 0.8000 | 0.002745 | 0.100 | 3.2177 | 83.0000 | `pass` |
| Manipulation(scoped) | `short_tp120_sl060_h72` | 13535 | 12 | 1127 | 0.7500 | 0.005609 | 0.000 | 1.0000 | 100.0000 | `pass` |

## Inputs

- Provider cache: `docs/experiments/actionable-regime-confidence/runs/20260511T212211-codex-board-b-yfinance-defensive-crossasset-v1-repaired/provider-cache`
- Local 4h panels: `/Users/thrill3r/Auto-Quant/user_data/data`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^GSPC`
- Scoped Manipulation component: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2.md`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/branch-rc-spa/source_root_stop_carry_longhorizon_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/branch-rc-spa/source_root_stop_carry_longhorizon_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/branch-rc-spa/source_root_stop_carry_longhorizon_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/branch-rc-spa/source_root_stop_carry_longhorizon_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/branch-rc-spa/source_root_stop_carry_longhorizon_panel_summary_v1.csv`
- Candidate summary: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/ict-engine-candidate/source_root_stop_carry_longhorizon_candidate_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1/checks/source_root_stop_carry_longhorizon_v1_assertions.out`

## Next

- B5: run Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree branch consumption with the same branch paths.
