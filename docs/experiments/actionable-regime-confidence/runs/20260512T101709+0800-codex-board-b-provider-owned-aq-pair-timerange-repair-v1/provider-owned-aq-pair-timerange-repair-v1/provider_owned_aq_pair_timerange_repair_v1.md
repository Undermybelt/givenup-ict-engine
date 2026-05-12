# Provider-Owned AQ Pair Timerange Repair v1

Run id: `20260512T101709+0800-codex-board-b-provider-owned-aq-pair-timerange-repair-v1`

Mode: `incubation_only_provider_aq_repair`

## Scope

Provider-owned Auto-Quant pair/timerange repair for the Yahoo NQ provider-preseeded workspace. This packet does not edit Current Cursor, does not approve selected history, does not approve source/control evidence, does not run selected-data promotion, does not run downstream Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion, does not promote a candidate, and does not call `update_goal`.

This is a terminal closeout for the `101709` short-window repair only. It does not supersede the later `101833` long-history Yahoo NQ preseed readback.

## Command Evidence

- Command: `uv --directory /Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T101709+0800-codex-board-b-provider-owned-aq-pair-timerange-repair-v1/workspace/auto-quant run python run_tomac.py`
- Exit: `0`
- Raw stdout/stderr/exit: `docs/experiments/actionable-regime-confidence/runs/20260512T101709+0800-codex-board-b-provider-owned-aq-pair-timerange-repair-v1/command-output/00_run_tomac_provider_pair_timerange_repair.out`, `docs/experiments/actionable-regime-confidence/runs/20260512T101709+0800-codex-board-b-provider-owned-aq-pair-timerange-repair-v1/command-output/00_run_tomac_provider_pair_timerange_repair.err`, `docs/experiments/actionable-regime-confidence/runs/20260512T101709+0800-codex-board-b-provider-owned-aq-pair-timerange-repair-v1/command-output/00_run_tomac_provider_pair_timerange_repair.exit`

## Auto-Quant Readback

- Pair loaded: `NQ/USD`
- Strategy: `TomacNQ_KillzoneBreakout`
- Data range: `2026-04-01 00:00:00 -> 2026-05-11 23:00:00`
- Backtest window after startup candles: `2026-04-11 10:00:00 -> 2026-05-11 23:00:00`
- `1h` fillup: `642 -> 984`
- `4h` fillup: `173 -> 246`
- Succeeded strategies: `1`
- Failed strategies: `0`
- Trades: `0`
- Sharpe: `0.0000`
- Total profit: `0.0000%`
- Win rate: `0.0000%`
- Profit factor: `0.0000`

## Decision

Gate: `provider_owned_aq_pair_timerange_repair_v1=completed_zero_trades_no_promotion`.

The pair/timerange repair reached Freqtrade/TOMAC successfully and retired the immediate pairlist/timerange blocker for this short provider-preseeded shape. It produced no trades, no mature rooted branch observations, and no profitability signal. No downstream promotion chain was started.

Promotion allowed: `false`

`update_goal=false`

## Next

Do not rerun this same short-window Yahoo NQ TOMAC repair. The newer `101833` long-history Yahoo preseed already retires the short-window-only hypothesis for the same TOMAC shape. Continue only with a changed branch-specific strategy that can produce nonzero provider-owned observations, a different provider-provenanced market family, or explicit selected-history/source-control unlocks before any selected-data promotion chain.
