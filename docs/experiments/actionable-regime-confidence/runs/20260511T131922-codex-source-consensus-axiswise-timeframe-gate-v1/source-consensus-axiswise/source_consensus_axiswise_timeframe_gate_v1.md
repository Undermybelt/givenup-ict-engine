# Source Consensus Axiswise Timeframe Gate v1

Run ID: `20260511T131922+0800-codex-source-consensus-axiswise-timeframe-gate-v1`

## Result

- Accepted 95 source-consensus axiswise timeframe/root cells: `1w:Bull, 1w:Bear, 1w:Sideways, 1w:Crisis, 1mo:Bull, 1mo:Bear, 1mo:Sideways, 1mo:Crisis`.
- Blocked timeframe/root cells: `none`.
- Newly closed cell versus the disjoint source-consensus gate: `1mo:Sideways`.
- Gate result: `accepted_95_source_consensus_axiswise_8of8_same_source_timeframe_cells_full_matrix_still_blocked`.
- Full objective achieved: `false`.

## Policy

- Fixed source-consensus threshold: `label_share >= 0.95`.
- Validation support unit: daily source-label agreement days; minimum `50` per validation axis.
- Confidence: Wilson95 lower bound of source-day agreement inside emitted weekly/monthly windows.
- Axiswise validation: calibration uses non-heldout tickers in 2017-2021, heldout-time uses all tickers in 2022+, and heldout-ticker uses heldout tickers across all dates.
- This is a source-label consistency gate, not an OHLCV predictive rule search.

## Cells

| Timeframe | Root | Accepted | Cal LCB | Heldout-Time Axis LCB | Heldout-Ticker Axis LCB | Blockers |
|---|---|---|---:|---:|---:|---|
| 1w | Bull | `true` | 0.999716 | 0.999685 | 0.999821 | none |
| 1w | Bear | `true` | 0.999131 | 0.999474 | 0.999513 | none |
| 1w | Sideways | `true` | 0.998897 | 0.998718 | 0.999442 | none |
| 1w | Crisis | `true` | 0.997751 | 0.998401 | 0.998897 | none |
| 1mo | Bull | `true` | 0.987521 | 0.988397 | 0.989224 | none |
| 1mo | Bear | `true` | 0.986557 | 0.981381 | 0.982684 | none |
| 1mo | Sideways | `true` | 0.959409 | 0.952936 | 0.966575 | none |
| 1mo | Crisis | `true` | 0.974424 | 0.975305 | 0.981735 | none |

## Guardrails

- Uses only the already materialized same-source stock-market-regimes weekly/monthly rollup.
- Does not use S&P source-window projection.
- Does not promote child/sub-regime packets.
- Axiswise validation closes same-source weekly/monthly cells only; unsupported intraday/full-species cells and full direct `Manipulation` variety coverage remain open.
- No runtime code changed; no thresholds relaxed; no raw data committed; not trade usable.
