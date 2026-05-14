# Unified Source-Label Panel v1

Run ID: `20260511T124027+0800-codex-unified-source-label-panel-v1`

## Result

- Materialized panel rows: `818`.
- Deferred refresh-required rows: `21`.
- Price roots with materialized windows: `Bear, Bull, Crisis, Sideways`.
- Current missing/rejected slots covered: `67` / `564`.
- Still missing/out-of-scope slots: `497`.
- Full-objective gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.

## Covered Slots By Root

| Root | Covered | Still Missing |
|---|---:|---:|
| `Bull` | `21` | `120` |
| `Bear` | `21` | `120` |
| `Sideways` | `4` | `137` |
| `Crisis` | `21` | `120` |

## Boundary

- This unifies label-window artifacts; it does not claim held-out 95% completion for the full matrix.
- `Manipulation` remains direct-event scoped and separate.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
