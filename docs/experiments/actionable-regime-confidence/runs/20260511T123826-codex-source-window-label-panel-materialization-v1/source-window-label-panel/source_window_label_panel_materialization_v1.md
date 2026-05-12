# Source-Window Label Panel Materialization v1

Run ID: `20260511T123826+0800-codex-source-window-label-panel-materialization-v1`

## Result

- Approved crosswalk slots consumed: `63`.
- Slots with closed dated windows materialized: `63`.
- Closed dated label-panel window rows: `210`.
- Deferred refresh-required rows: `21`.
- Roots covered by closed windows: `Bear, Bull, Crisis`.
- Instruments covered: `ES=F, SPY, ^GSPC`.
- Timeframes covered: `15m, 1h, 1m, 1mo, 30m, 4h, 5m`.

## Counts By Root And Status

| Root/Status | Count |
|---|---:|
| `Bear:materialized_closed_window` | `84` |
| `Bull:deferred_refresh_required` | `21` |
| `Bull:materialized_closed_window` | `63` |
| `Crisis:materialized_closed_window` | `63` |

## Boundary

- This is source-label panel materialization, not a calibrated prediction gate.
- Open-ended Yardeni Bull rows are deferred until refresh.
- No Sideways or Manipulation completion is claimed here.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Trade usable: false.
