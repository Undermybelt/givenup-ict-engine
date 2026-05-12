# Daily to Intraday Source Attachment v1

Run ID: `20260511T134756+0800-codex-daily-to-intraday-source-attachment-v1`

This run stops asking yfinance for native intraday regime labels. It tests the narrower exact-source policy: attach an already source-backed daily parent root to intraday bars as parent-day context only.

## Result

- Exact same-source input slots: `48`.
- Accepted source-label attachment rows: `36`.
- Blocked exact attachment rows: `12`.
- Accepted roots: `Bear, Bull, Sideways`.
- Blocked roots: `Crisis`.
- Full objective achieved: `false`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.
- Gate result: `daily_to_intraday_source_attachment_v1_accepted36_blocked12_crisis_support_short`.

## Policy

- Attach only same-ticker daily source labels to intraday bars whose exchange-local session date equals the source date.
- Consumer meaning is `intraday_parent_day_context_not_intraday_micro_regime`.
- Abstain for missing dates, residual labels, out-of-range dates, or consumers that need intraday transition timing.
- Do not derive labels from intraday OHLCV, HMM states, strategy predictions, or future returns.
- Do not use ETF/futures/index crosswalks here; they need a separate crosswalk package.

## Root Support

| Root | Cal Support | Cal Wilson95 | Heldout-Time Support | Heldout-Time Wilson95 | Heldout-Ticker Support | Heldout-Ticker Wilson95 | Accepted |
|---|---:|---:|---:|---:|---:|---:|---|
| `Bull` | 1665 | 0.997698 | 1135 | 0.996627 | 6490 | 0.999408 | `true` |
| `Bear` | 125 | 0.970185 | 293 | 0.987059 | 1906 | 0.997989 | `true` |
| `Sideways` | 700 | 0.994542 | 616 | 0.993803 | 3928 | 0.999023 | `true` |
| `Crisis` | 28 | 0.879357 | 2 | 0.342380 | 290 | 0.986927 | `false` |

## Next

- Use local ES/NQ 15m/1h history for a separate crosswalk calibration package.
- Keep exact `^GSPC/^DJI` attachment separate from crosswalk candidates.
- `Crisis` needs broader exact-source support or new source-label rows before this exact lane can close it.
