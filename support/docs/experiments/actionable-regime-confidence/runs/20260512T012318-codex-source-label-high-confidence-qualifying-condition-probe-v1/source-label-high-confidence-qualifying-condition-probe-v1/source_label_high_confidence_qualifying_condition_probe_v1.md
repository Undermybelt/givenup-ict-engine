# Source Label High-Confidence Qualifying-Condition Probe v1

Run id: `20260512T012318-codex-source-label-high-confidence-qualifying-condition-probe-v1`
Gate result: `source_label_high_confidence_qualifying_condition_probe_v1=bull_sideways_split_market_support_ready_timeframe_blocked_no_acceptance`

This packet materializes the `011819` Bull/Sideways lead as an explicit fail-closed qualifying-condition probe. It is not an acceptance packet.

| Label | Qualifying Condition ID | High-Confidence Rows | Split Support Pass | Market Contexts | Timeframes | Timeframe Variety Pass | Accepted 95 | Blockers |
|---|---|---:|---|---|---|---|---|---|
| Bear |  | 52 | False | us_index;us_single_stock | 1d | False | False | split_support_below_50;timeframe_variety_below_other_cycle_requirement;not_triage_candidate |
| Bull | bull_source_confidence_ge_0_95_daily_source_panel_v1 | 10193 | True | india_equity_index;us_index;us_single_stock | 1d | False | False | timeframe_variety_below_other_cycle_requirement |
| Crisis |  | 276 | False | india_equity_index | 1d | False | False | split_support_below_50;cross_market_family_coverage_below_2;timeframe_variety_below_other_cycle_requirement;not_triage_candidate |
| Sideways | sideways_source_confidence_ge_0_95_daily_source_panel_v1 | 8686 | True | india_equity_index;us_index;us_single_stock | 1d | False | False | timeframe_variety_below_other_cycle_requirement |

Result:
- Bull and Sideways have enough high-confidence source-label support across required splits and market families.
- Both remain daily-only (`1d`) source-panel conditions, so the other-cycle/timeframe requirement is not satisfied.
- Bear and Crisis remain blocked before this probe because their high-confidence subset support is incomplete.
- This packet does not override the failed `011056` full source-confidence gate and does not allow downstream promotion.

