# Accepted Root Dated Window Inventory v1

Run ID: `20260511T125200+0800-codex-accepted-root-dated-window-inventory-v1`

## Result

- Materialized accepted-root dated windows: `5968`.
- Windows by root: `{'Bear': 325, 'Bull': 5035, 'Sideways': 608}`.
- Selected rows by root: `{'Bear': 3465, 'Bull': 14134, 'Sideways': 4049}`.
- Crisis remains report-backed only; dated windows were not invented after the raw feature table was pruned.
- Full objective gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.

## Gate References

- Bull LCB calibration/test: `0.952516` / `0.961931`.
- Bear LCB calibration/test: `0.993968` / `0.992722`.
- Sideways LCB calibration/test: `0.988647` / `0.995568`.
- Crisis LCB calibration/test: `0.996248` / `0.995981` report-backed only.

## Guardrails

- Existing local tables/cache only.
- No runtime code change.
- No threshold relaxation.
- No raw feature table committed.
- No trade usability claimed.

## Artifacts

- `accepted_root_dated_window_inventory_v1.json`
- `accepted_root_dated_windows_v1.csv`
- `../checks/accepted_root_dated_window_inventory_v1_assertions.out`
