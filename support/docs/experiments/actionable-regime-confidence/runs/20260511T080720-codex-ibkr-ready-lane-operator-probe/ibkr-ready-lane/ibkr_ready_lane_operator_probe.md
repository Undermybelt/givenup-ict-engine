# IBKR Ready Lane Operator Probe

Run id: `20260511T080720+0800-codex-ibkr-ready-lane-operator-probe`

Goal achieved: `false`

- IBKR manifest cells: `90`
- Attempted cells: `1`
- OK cells: `0`
- Failed/timeout cells: `1`
- Raw OHLCV committed: `false`

## Status Counts

| Status | Count |
|---|---:|
| `fetch_failed` | 1 |
| `not_attempted_after_operator_fetch_blocker` | 89 |

## Accounting

- IBKR bars are provider coverage only; every IBKR cell remains `missing_independent_root_labels`.
- No threshold was relaxed and no runtime code changed.
- Gate result: `ibkr_ready_lane_blocked_by_operator_runtime_fetch`

## Next Action

Fix the concrete IBKR operator-runtime fetch blocker or use another independent source-label panel; do not treat IBKR ready status as fetched coverage.
