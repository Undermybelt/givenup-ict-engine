# AMD/CVX Exact Intraday Source Attachment v1

Run ID: `20260511T140643+0800-codex-amd-cvx-exact-intraday-source-attachment-v1`

This run corrects the attack direction after the ES/NQ crosswalk package produced mostly blocked rows.
It stays inside the active `MainRegimeV2` parent taxonomy and uses exact same-source stock tickers from the
`stock-market-regimes-20002026` panel rather than child/sub-regime labels or ETF/futures crosswalks.

## Result

- Selected exact source tickers: `AMD, CVX`.
- Provider/timeframe: `yfinance 1h` with actual provider rows `{'AMD': 5069, 'CVX': 5068}`.
- Scoped attachment slots: `8`.
- Accepted source-label attachment rows: `8`.
- Blocked source-label attachment rows: `0`.
- Accepted roots: `Bull, Bear, Sideways, Crisis`.
- Blocked roots: `none`.
- Full objective achieved: `false`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.
- Gate result: `amd_cvx_exact_intraday_source_attachment_v1=accepted8_blocked0_scoped_1h_2024_2025`.

## Policy

- Attach only the same ticker's source-panel daily `MainRegimeV2` root to 1h bars whose exchange-local session date matches the source date.
- Consumer meaning is `intraday_parent_day_context_not_intraday_micro_regime`.
- Do not derive labels from target intraday OHLCV, HMM states, strategy predictions, future returns, or generated labels.
- Do not use ETF/futures/index crosswalks in this exact-source run.
- `2026` source-tail support is reported but is not the acceptance gate because the source panel stops at `2026-01-30`.

## Root Support

| Root | 2024 Cal Support | 2024 Cal Wilson95 | 2025 Heldout Support | 2025 Heldout Wilson95 | 2026 Tail Support | 2026 Tail Wilson95 | Accepted |
|---|---:|---:|---:|---:|---:|---:|---|
| `Bull` | 173 | 0.978277 | 172 | 0.978154 | 32 | 0.892821 | `true` |
| `Bear` | 119 | 0.968728 | 105 | 0.964706 | 0 | 0.000000 | `true` |
| `Sideways` | 109 | 0.965957 | 116 | 0.967945 | 4 | 0.510109 | `true` |
| `Crisis` | 103 | 0.964045 | 107 | 0.965343 | 4 | 0.510109 | `true` |

## Why This Replaces The Immediate Crosswalk Direction

- The prior ES/NQ package spent the loop budget on relation risk and accepted only `2/16` rows.
- This run stays on exact same-source tickers and closes `8/8` scoped `1h` parent-root attachment rows.
- It does not promote child regimes, provider bars, or target OHLCV proxies.
- Remaining full-objective blockers are broader timeframe/species coverage and direct `Manipulation` variety coverage.

## Next

- Exhaust exact same-source ticker attachments from the stock-market-regimes panel before returning to ETF/futures/index crosswalks.
- If 2026 recency is required, extend the source panel beyond `2026-01-30`; do not lower gates or promote provider OHLCV bars as labels.
