# SystemsLab Direct Pump/Dump Manipulation Gate

Run id: `20260511T030031+0800-codex-systemslab-direct-pump-gate`

## Source

- Repo: `https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset`
- Commit: `d71250d4cb055dde2d415c8cba38a0dcd6eb6e16`
- Source root: `/private/tmp/ict-regime-systemslab-pump-dump`
- Raw data committed to repo: false
- Label polarity: `gt=1` labeled pump/dump chunk, `gt=0` non-pump chunk.
- Predictors used: transaction-derived market features only; timestamps, pump ids, symbols, labels, and cyclic clock fields blocked.

## Gate Results

### 5S

- Rows train/cal/test: 492,784 / 164,261 / 164,262.
- Positives train/cal/test: 148 / 98 / 71.
- Selected train-only rule: `std_rush_order >= 0.041`.
- Train Wilson95 LCB: `0.244633` with support 507.
- Calibration Wilson95 LCB: `0.230445` with support 318.
- Test Wilson95 LCB: `0.212055` with support 264.
- Accepted 95: False.

### 25S

- Rows train/cal/test: 289,294 / 96,431 / 96,432.
- Positives train/cal/test: 157 / 90 / 70.
- Selected train-only rule: `std_rush_order >= 0.062707`.
- Train Wilson95 LCB: `0.473568` with support 290.
- Calibration Wilson95 LCB: `0.477081` with support 147.
- Test Wilson95 LCB: `0.546742` with support 106.
- Accepted 95: False.

## Decision

- Accepted 95 `Manipulation` root: False.
- Gate: `blocked_systemslab_direct_pump_gate_below_95`.
- Thresholds relaxed: false.
- Runtime code changed: false.
- Trade usable: false.

The source supplies a second direct manipulation context with explicit timestamps and positive/negative labels, but the unchanged chronological held-out gate must pass before `Manipulation` can count as an accepted MainRegimeV2 root.
