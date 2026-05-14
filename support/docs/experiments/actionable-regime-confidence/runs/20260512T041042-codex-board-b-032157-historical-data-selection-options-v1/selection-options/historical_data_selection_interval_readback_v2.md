# Historical Data Selection Interval Readback v2

This is an append-only correction for Board B historical-data selection labels.
It does not select a dataset, does not edit the current cursor, and does not
run factor-research or Auto-Quant.

## Direct File Readback

The actual candidate JSON files in both the combined state and the source state
have these first, second, and last candle timestamps:

| Option | State | First | Second | Last | Candles | Actual cadence from timestamps |
|---|---|---|---|---|---:|---|
| `htf` | combined | `2025-03-03T00:00:00Z` | `2025-03-04T00:00:00Z` | `2025-12-31T00:00:00Z` | 260 | 1d |
| `mtf` | combined | `2025-10-31T16:00:00Z` | `2025-10-31T20:00:00Z` | `2025-12-31T20:00:00Z` | 260 | 4h |
| `ltf` | combined | `2025-12-15T12:00:00Z` | `2025-12-15T13:00:00Z` | `2025-12-31T21:00:00Z` | 260 | 1h |
| `htf` | source | `2025-03-03T00:00:00Z` | `2025-03-04T00:00:00Z` | `2025-12-31T00:00:00Z` | 260 | 1d |
| `mtf` | source | `2025-10-31T16:00:00Z` | `2025-10-31T20:00:00Z` | `2025-12-31T20:00:00Z` | 260 | 4h |
| `ltf` | source | `2025-12-15T12:00:00Z` | `2025-12-15T13:00:00Z` | `2025-12-31T21:00:00Z` | 260 | 1h |

## Correction

The `041042` candidate list remains useful for the three option names and file
paths, but its interval labels should not override the data-file timestamp
cadence. For the next user selection prompt, use:

- `HTF`: `analyze_nq_htf.json`, actual cadence `1d`
- `MTF`: `analyze_nq_mtf.json`, actual cadence `4h`
- `LTF`: `analyze_nq_ltf.json`, actual cadence `1h`

## Gate

- `blocked:user_selected_historical_data_missing`

The user must still explicitly select exactly one of `HTF`, `MTF`, or `LTF`.
