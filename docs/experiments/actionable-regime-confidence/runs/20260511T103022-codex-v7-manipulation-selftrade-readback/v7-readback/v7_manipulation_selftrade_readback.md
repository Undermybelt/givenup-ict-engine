# V7 Manipulation Self-Trade Readback

Run ID: `20260511T103022+0800-codex-v7-manipulation-selftrade-readback`

## Result

- Active taxonomy: `ActionableRegimeRootV7`.
- Candidate root: `ManipulationIntegrityEvent`.
- Accepted direct slice: `wash_trade_self_trade` = `true`.
- Consecutive rows streamed in source gate: `200000`.
- Minimum calibration/test positive-or-negative Wilson95 LCB: `0.979218`.
- Minimum calibration/test positive support: `181`.
- Minimum calibration/test negative support: `32858`.
- Accepted V7 parent roots added: `0`.
- Accepted V7 root slices added: `1`.
- Gate result: `partial_v7_manipulation_integrity_event_selftrade_slice_95_full_root_blocked`.

## Boundary

This is a partial direct slice for `ManipulationIntegrityEvent`; it does not
complete the full root or any price-action V7 root.
