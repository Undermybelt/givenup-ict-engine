# 123227 Selected-History TOMAC Run v1

Run id: `20260512T123704+0800-codex-123227-selected-history-tomac-run-v1`
Source selected-history root: `20260512T123227+0800-codex-115700-selected-history-btc-alias-aq-v1`

## Scope
Run the selected-history `123227` Auto-Quant/TOMAC handoff in its isolated workspace and tie the measured result back to ict-engine status/review surfaces.
This does not mutate BBN CPDs, CatBoost models, or execution-tree gates.

## Readback
- Initial wrapper command failed before backtest because `freqtrade` was missing from the outer `uv --with ta-lib` environment; the isolated Auto-Quant `.venv` contains `freqtrade`, `talib`, and `pandas`.
- TOMAC via the isolated `.venv` exited `0`.
- Strategies succeeded/failed: `3` / `0`.
- Strategies measured: `['TomacAggressiveBE', 'TomacKillzoneBreakout', 'TomacRRWinRate']`.
- Total measured trades: `0`.
- Max strategy win rate pct: `0.0`; max Sharpe: `0.0`.
- ict-engine auto-quant status: `dependency_ready_data_ready`.
- ict-engine adoption review: `ready_for_external_execution` / `handoff is ready for Auto-Quant execution and candidate export`.
- workflow-status blocker: `insufficient_state` / `no workflow phase snapshots available`.

## Decision
- Gate: `selected_history_tomac_measured_zero_trades_no_downstream_promotion`.
- The selected-history data-ready unlock is real, and TOMAC ran, but all three TOMAC-derived strategies produced zero trades on this BTC-only selected window.
- Because there is no measured candidate package, this root cannot advance into Pre-Bayes/BBN/CatBoost/execution promotion.
- `production_likelihood_mutation=false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T123704+0800-codex-123227-selected-history-tomac-run-v1/123227-selected-history-tomac-run-v1/123227_selected_history_tomac_run_v1.json`
- Strategy metrics CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T123704+0800-codex-123227-selected-history-tomac-run-v1/123227-selected-history-tomac-run-v1/123227_selected_history_tomac_strategy_metrics_v1.csv`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T123704+0800-codex-123227-selected-history-tomac-run-v1/123227-selected-history-tomac-run-v1/prompt_to_artifact_checklist_123227_selected_history_tomac_run_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T123704+0800-codex-123227-selected-history-tomac-run-v1/checks/123227_selected_history_tomac_run_v1_assertions.out`
