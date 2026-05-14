# Native Subhour Projection Quarantine v1

Run ID: `20260511T192248+0800-codex-native-subhour-projection-quarantine-v1`

This audit checks whether old unified source-label panel rows that carry `1m`, `5m`, `15m`, or `30m` timeframes can satisfy Board A native sub-hour validation. They cannot: every such row is a dated source-window projection, not a source-owned native sub-hour label panel.

## Decision

`native_subhour_projection_quarantine_v1=projected_subhour_rows_not_native_source_labels`

- Panels read: `2`.
- Total panel rows read: `1678`.
- Sub-hour-looking rows read: `264`.
- Native sub-hour eligible rows: `0`.
- Quarantined sub-hour rows: `264`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Native sub-hour source overlap closed: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Counts

- Sub-hour timeframes: `{'1m': 66, '5m': 66, '15m': 66, '30m': 66}`.
- Sub-hour roots: `{'Bull': 96, 'Bear': 96, 'Crisis': 72}`.
- Sub-hour crosswalk layers: `{'same_underlying_spx_to_gspc_time_projection': 64, 'macro_crisis_to_gspc_time_projection': 24, 'spx_tradable_proxy_time_projection': 128, 'macro_crisis_to_spx_tradable_proxy': 48}`.
- Quarantine reasons: `{'projected_day_or_month_source_window_to_subhour_target': 216, 'dated_window_materialization_not_native_subhour_rows': 48}`.

## Why It Still Blocks

The sub-hour-looking rows are `Bull` / `Bear` / `Crisis` windows projected from S&P 500/Yardeni day windows or NBER month windows into `1m`, `5m`, `15m`, and `30m` targets. Projection can preserve provenance as a source-window attachment, but it is not a native source-owned sub-hour label. Board A still needs a real native sub-hour source panel or owner-approved rows before this gate can move.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T192248-codex-native-subhour-projection-quarantine-v1/native-subhour-projection-quarantine/native_subhour_projection_quarantine_v1.json`
- Quarantine rows CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T192248-codex-native-subhour-projection-quarantine-v1/native-subhour-projection-quarantine/native_subhour_projection_quarantine_v1_rows.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T192248-codex-native-subhour-projection-quarantine-v1/checks/native_subhour_projection_quarantine_v1_assertions.out`
