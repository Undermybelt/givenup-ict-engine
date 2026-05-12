# Board B Provider YF NQ TrendPulse AQ v1

Run id: `20260512T102332+0800-codex-board-b-provider-yf-nq-trendpulse-aq-v1`

Mode: `incubation_only`

## Scope

Provider-owned Yahoo NQ long-history Auto-Quant run using a changed `ProviderNqTrendPulse` strategy. This packet tests whether a materially different branch-specific strategy can produce nonzero provider-owned observations after the earlier TOMAC and alias/MS repairs produced zero trades.

This packet does not edit Current Cursor, does not approve selected history or source/control evidence, does not run selected-data promotion, does not advance Pre-Bayes/BBN/CatBoost/execution-tree promotion, does not promote a candidate, and does not call `update_goal`.

## Command Evidence

- `00_run_provider_yf_nq_trendpulse`: exited `0`.
- `01_probe_provider_yf_nq_trendpulse_conditions`: exited `0`.
- `02_probe_strategy_method_entries`: exited `0`.
- `03_probe_entry_exit_overlap`: exited `0`.

Raw command outputs:
- `command-output/00_run_provider_yf_nq_trendpulse.out`
- `command-output/01_probe_provider_yf_nq_trendpulse_conditions.out`
- `command-output/02_probe_strategy_method_entries.out`
- `command-output/03_probe_entry_exit_overlap.out`

## Probe Readback

The direct strategy-method probe found nonzero entry conditions on the prepared provider-owned NQ data:

- rows: `11086`
- `trend_count=3963`
- `pulse_count=3962`
- `tradable_count=11080`
- `all_count_with_volume=1945`
- `all_count_no_volume=2024`
- strategy-method `enter_long_sum=3080`
- strategy-method `exit_long_sum=5011`
- entry/exit overlap: `0`
- entry without same-row exit: `3080`

This means the strategy logic can emit entry labels in an offline probe, but that signal did not translate into Freqtrade executed trades.

## Auto-Quant Readback

The Freqtrade/TOMAC run loaded `NQ/USD`, backtested `2024-06-07 22:00:00 -> 2026-05-11 23:00:00`, and completed:

- Strategy: `ProviderNqTrendPulse`
- Succeeded strategies: `1`
- Failed strategies: `0`
- Trade count: `0`
- Sharpe: `0.0000`
- Total profit: `0.0000%`
- Win rate: `0.0000%`
- Profit factor: `0.0000`

## Decision

Gate: `provider_yf_nq_trendpulse_aq_v1=offline_entries_present_but_freqtrade_zero_trades_no_promotion`.

The useful result is a narrowed runtime translation blocker, not a profitability signal: offline entry labels exist, but the Auto-Quant/Freqtrade backtest still records zero trades.

Promotion allowed: `false`

`update_goal=false`

## Next

Do not treat offline entry labels as mature rooted branch observations. The next non-duplicative provider-owned strategy slice must either explain why Freqtrade ignores these entries or produce nonzero executed trades before any Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree promotion rerun.
