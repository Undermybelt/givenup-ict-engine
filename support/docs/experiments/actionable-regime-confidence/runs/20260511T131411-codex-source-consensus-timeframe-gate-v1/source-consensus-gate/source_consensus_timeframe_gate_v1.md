# Source Consensus Timeframe Gate v1

Run ID: `20260511T131411+0800-codex-source-consensus-timeframe-gate-v1`

## Result

- Accepted 95 source-consensus timeframe/root cells: `1w:Bull, 1w:Bear, 1w:Sideways, 1w:Crisis, 1mo:Bull, 1mo:Bear, 1mo:Crisis`.
- Blocked timeframe/root cells: `1mo:Sideways`.
- Newly closed cells versus the prior derived probe: `1w:Bear`, `1w:Crisis`, `1mo:Bull`, `1mo:Bear`, `1mo:Crisis`.
- Remaining same-source timeframe blocker: `1mo:Sideways`.
- Gate result: `accepted_95_source_consensus_7of8_same_source_timeframe_cells_full_matrix_still_blocked`.
- Full objective achieved: `false`.

## Policy

- Fixed source-consensus threshold: `label_share >= 0.95`.
- Validation support unit: daily source-label agreement days; minimum `50` per validation split.
- Confidence: Wilson95 lower bound of source-day agreement inside emitted weekly/monthly windows.
- This is a source-label consistency gate, not an OHLCV predictive rule search.

## Cells

| Timeframe | Root | Accepted | Cal LCB | Heldout-Time LCB | Heldout-Ticker LCB | Blockers |
|---|---|---|---:|---:|---:|---|
| 1w | Bull | `true` | 0.999716 | 0.999555 | 0.999821 | none |
| 1w | Bear | `true` | 0.999131 | 0.999338 | 0.999513 | none |
| 1w | Sideways | `true` | 0.998897 | 0.998130 | 0.999442 | none |
| 1w | Crisis | `true` | 0.997751 | 0.997895 | 0.998897 | none |
| 1mo | Bull | `true` | 0.987521 | 0.987775 | 0.989224 | none |
| 1mo | Bear | `true` | 0.986557 | 0.984396 | 0.982684 | none |
| 1mo | Sideways | `false` | 0.959409 | 0.931307 | 0.966575 | heldout_time_source_consensus_wilson95_below_0_95 |
| 1mo | Crisis | `true` | 0.974424 | 0.967675 | 0.981735 | none |

## Guardrails

- Uses only the already materialized same-source stock-market-regimes weekly/monthly rollup.
- Does not use S&P source-window projection.
- Does not promote child/sub-regime packets.
- Does not close unsupported intraday/full-species cells or direct `Manipulation` variety coverage.
- No runtime code changed; no thresholds relaxed; no raw data committed; not trade usable.
