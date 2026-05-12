# Source Label Acquisition Package V2

Run id: `20260511T081715+0800-codex-source-label-acquisition-package-v2`

Goal achieved: `false`

- Current attached slots: `48` / `612`
- Current missing/rejected slots: `564`
- Full four-root cells: `12`
- Ready-not-yet-attempted provider cells after residual readback: `0`
- IBKR gate: `ibkr_ready_lane_blocked_by_operator_runtime_fetch`
- Polymarket gate: `polymarket_catalog_materialized_root_confidence_pending`
- Direct Manipulation schema audit: `blocked_direct_manipulation_sources_unlabeled_no_accepted_label_windows`; accepted label sources `0`

## Missing / Rejected Reasons

| Reason | Slots |
|---|---:|
| `missing_instrument_source_label` | 40 |
| `missing_intraday_or_monthly_source_label` | 392 |
| `missing_non_yfinance_source_label` | 108 |
| `rejected_near_underlying_proxy_not_accepted` | 24 |

## Decision

- Gate result: `blocked_acquisition_package_v2_created_missing_564_external_source_labels`
- The older 596-slot acquisition package is stale because exact-underlying labels now attach 48 slots.
- Provider bars/catalogs remain sidecar until source labels attach.
- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

## Next Action

Use the v2 acquisition CSV to obtain independent labels for the 564 missing/rejected price-root slots plus explicit labeled Manipulation positive/negative windows; do not spend more cycles on provider bar fetches until label coverage exists.
