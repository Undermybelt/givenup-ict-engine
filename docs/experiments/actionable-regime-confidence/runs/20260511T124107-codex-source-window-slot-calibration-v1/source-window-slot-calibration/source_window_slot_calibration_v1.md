# Source-Window Slot Calibration v1

Run ID: `20260511T124107+0800-codex-source-window-slot-calibration-v1`

## Result

- Supported bar-overlap slots calibrated: `3`.
- Unsupported crosswalk timeframe slots abstained: `{'15m': 33, '1h': 33, '1m': 33, '30m': 33, '4h': 33, '5m': 33}`.
- Accepted 95 crosswalk slots: `[]`.
- Sideways carried forward as scoped accepted gate: `0.988647` / `0.995568`.
- Full objective achieved: `false`.

## Boundary

- Bull/Bear/Crisis source-window rows were calibrated only where yfinance historical bars overlap `1d`, `1w`, or `1mo`.
- Intraday crosswalk slots remain abstained because long historical yfinance intraday bars are unavailable for those source windows.
- Sideways remains scoped to Yahoo crypto/equity ETF `1d`/`1w`; no intraday/monthly/full-species projection was made.
- Manipulation is not part of this price-root panel and still requires direct event/order-flow/order-lifecycle rows.

## Artifacts

- `docs/experiments/actionable-regime-confidence/runs/20260511T124107-codex-source-window-slot-calibration-v1/source-window-slot-calibration/source_window_slot_calibration_v1.json`
- `docs/experiments/actionable-regime-confidence/runs/20260511T124107-codex-source-window-slot-calibration-v1/source-window-slot-calibration/source_window_slot_calibration_v1_summary.csv`
- `docs/experiments/actionable-regime-confidence/runs/20260511T124107-codex-source-window-slot-calibration-v1/checks/source_window_slot_calibration_v1_assertions.out`
