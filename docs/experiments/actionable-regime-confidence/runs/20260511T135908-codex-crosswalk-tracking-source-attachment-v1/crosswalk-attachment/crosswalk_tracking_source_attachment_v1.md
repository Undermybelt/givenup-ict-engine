# Crosswalk Tracking Source Attachment v1

Run ID: `20260511T135908+0800-codex-crosswalk-tracking-source-attachment-v1`

## Result

- Candidate crosswalk rows: `168`.
- Tracking-pass targets: `DIA, SPY`.
- Accepted crosswalk source-attachment rows: `36`.
- Blocked crosswalk rows: `132`.
- Gate result: `crosswalk_tracking_source_attachment_v1_accepted36_blocked132_full_matrix_still_blocked`.
- Full objective achieved: `false`.

## Policy

- Use yfinance daily prices only to validate target/source tracking relation.
- Attach labels only from the stock-market-regimes source ticker daily `MainRegimeV2` panel.
- Require calibration and heldout-time same-sign Wilson95 LCB >= `0.95`, all-period return correlation >= `0.95`, and root support >= `50` with Wilson95 LCB >= `0.95`.
- Do not use target OHLCV, HMM/GMM, future returns, or strategy predictions as labels.

## Tracking Pairs

| Target | Source | Cal Sign LCB | Heldout Sign LCB | Corr | Pass | Blocker |
|---|---|---:|---:|---:|---|---|
| `DIA` | `^DJI` | 0.972714 | 0.974745 | 0.999244 | `true` | none |
| `ES=F` | `^GSPC` | 0.935557 | 0.965329 | 0.972415 | `false` | tracking_relation_below_fixed_95_sign_or_corr_gate |
| `NQ=F` | `^IXIC` | 0.899095 | 0.936141 | 0.971261 | `false` | tracking_relation_below_fixed_95_sign_or_corr_gate |
| `QQQ` | `^IXIC` | 0.922419 | 0.953916 | 0.991636 | `false` | tracking_relation_below_fixed_95_sign_or_corr_gate |
| `SPY` | `^GSPC` | 0.970828 | 0.965329 | 0.998503 | `true` | none |
| `YM=F` | `^DJI` | 0.930283 | 0.961872 | 0.973116 | `false` | tracking_relation_below_fixed_95_sign_or_corr_gate |
| `^NDX` | `^IXIC` | 0.922419 | 0.956175 | 0.993087 | `false` | tracking_relation_below_fixed_95_sign_or_corr_gate |

## Accepted Rows

- By instrument: `{'DIA': 18, 'SPY': 18}`.
- By root: `{'Bear': 12, 'Bull': 12, 'Sideways': 12}`.

## Remaining Blocker

- `SPY` and `DIA` accepted only for `Bull/Bear/Sideways`; `Crisis` remains blocked by source-root support.
- `ES=F`, `YM=F`, `QQQ`, `NQ=F`, and `^NDX` fail the fixed tracking gate and remain unsupported.
- Unsupported no-source rows, Kraken/full-species rows, non-same-source daily/weekly/monthly species rows, and direct `Manipulation` remain open.

## Guardrails

- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.
