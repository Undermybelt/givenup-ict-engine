# Targeted Calibration Overlap v1

Run ID: `20260511T124600+0800-codex-targeted-calibration-overlap-v1`

## Result

- Label windows checked: `839`.
- Overlap-ready windows: `658`.
- No-overlap windows abstained: `181`.
- Overlap-ready by root: `{'Bear': 11, 'Bull': 30, 'Crisis': 9, 'Sideways': 608}`.
- Bar overlap by root: `{'Bear': 160, 'Bull': 61560, 'Crisis': 87, 'Sideways': 4049}`.
- Full objective gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.

## Policy

This run is a targeted calibration preflight. It does not count no-overlap cells as model failures and it does not claim 95% confidence. It narrows the next calibration to windows where source labels and bars actually overlap.

## Guardrails

- Only approved S&P 500 crosswalk instruments/timeframes were fetched.
- Raw provider data stayed under `/private/tmp`.
- No runtime code changed; no thresholds relaxed; no trade usability claimed.

## Artifacts

- `targeted_calibration_overlap_v1.json`
- `targeted_calibration_overlap_v1.csv`
- `../checks/targeted_calibration_overlap_v1_assertions.out`
