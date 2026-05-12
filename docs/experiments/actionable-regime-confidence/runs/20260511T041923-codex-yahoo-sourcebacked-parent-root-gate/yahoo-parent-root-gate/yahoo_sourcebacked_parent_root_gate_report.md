# Yahoo Source-Backed Parent Root Gate

Run id: `20260511T041923+0800-codex-yahoo-sourcebacked-parent-root-gate`.

## Decision

- Gate result: `accepted_95`
- Accepted new roots: Bear, Sideways
- Missing roots after preserved accounting: Manipulation
- Thresholds relaxed: `false`
- Runtime code changed: `false`
- Trade usable: `false`

## Root Results

| Root | State | Rule | Cal LCB | Test LCB | Test Precision | Test Coverage | Test Contexts | Blockers |
|---|---|---|---:|---:|---:|---:|---|---|
| Bear | accepted_95 | `bear_drawdown_ratio >= 1 AND bear_return_ratio >= 1` | 0.993968 | 0.992722 | 1.000000 | 0.065582 | crypto, equity_etf / 1d, 1w | none |
| Sideways | accepted_95 | `sideways_abs_return_ratio <= 0.505204858191 AND sideways_range_ratio <= 0.357222193236` | 0.988647 | 0.995568 | 1.000000 | 0.108010 | crypto, equity_etf / 1d, 1w | none |

## Source And Policy

- External source review verdict: low risk; public market data and public regime-definition/method references only; no external code executed.
- Parent labels are observed current/trailing state definitions, not future-return labels and not vendor analyst predictions.
- Candidate thresholds are selected on the train split only; calibration/test are held out chronologically within each ticker/timeframe.
- `future_*`, `target_*`, and `next_*` predictors are absent.
- This does not reissue `Crisis` and does not evaluate `Manipulation` because Yahoo OHLCV is not direct event/order-lifecycle evidence.
