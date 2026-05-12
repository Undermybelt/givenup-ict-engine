# YFinance Intraday Source-Label Attack Map v1

Run ID: `20260511T134237+0800-codex-yfinance-intraday-source-label-attack-map-v1`

This artifact attacks the v12 `336` native yfinance intraday requests by triage only.
It does not download provider bars and does not promote OHLCV/HMM/future-return/generated labels.

## Result

- Exact same-source daily-label attachable rows pending policy: `48`.
- Explicit crosswalk candidate rows pending owner approval: `168`.
- Unsupported rows with no current source label: `120`.
- Accepted confidence added: `0`.
- Full objective achieved: `false`.
- Gate result: `yfinance_intraday_attack_map_exact48_crosswalk168_unsupported120_no_confidence_gate`.

## Buckets

| Bucket | Rows | Meaning |
|---|---:|---|
| `explicit_crosswalk_candidate_pending_owner_approval` | 168 | Instrument has a plausible index/ETF/futures relation to a source ticker; still not accepted until approved and calibrated. |
| `unsupported_no_current_source_label` | 120 | No source ticker currently exists; needs native source-label rows or should leave the high-yield batch. |
| `exact_same_source_daily_label_attachable_pending_policy` | 48 | Instrument exists in the stock-market-regimes source panel; needs explicit daily-to-intraday attachment policy before calibration. |

## Next

- Start with the `48` exact same-source `^GSPC`/`^DJI` intraday rows.
- Required next artifact: daily-to-intraday source-label attachment policy plus calibration probe.
- Keep `Manipulation` FINRA matched-negative acquisition separate.
