# Unified Source Label Panel v1

Run ID: `20260511T124000+0800-codex-unified-source-label-panel-v1`

## Result

- Unified label windows: `839`.
- Crosswalk source windows: `231`.
- Sideways scoped dated windows: `608`.
- Roots represented: `Bear, Bull, Crisis, Sideways`.
- Full objective gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.

## Counts

- By root: `{'Bear': 84, 'Bull': 84, 'Crisis': 63, 'Sideways': 608}`
- By source type: `{'sideways_scoped_dated_window': 608, 'source_window_crosswalk': 231}`
- By timeframe: `{'15m': 33, '1d': 442, '1h': 33, '1m': 33, '1mo': 33, '1w': 166, '30m': 33, '4h': 33, '5m': 33}`

## Guardrails

- This is a label-window panel and coverage audit, not a calibrated confidence gate.
- `Manipulation` is not represented because it requires direct event/order-flow/order-lifecycle rows.
- Unsupported Sideways intraday/monthly/full-species cells stay abstained.
- No runtime code changed, no thresholds relaxed, no raw data committed.

## Artifacts

- `unified_source_label_panel_v1.json`
- `unified_source_label_panel_v1.csv`
- `../checks/unified_source_label_panel_v1_assertions.out`
