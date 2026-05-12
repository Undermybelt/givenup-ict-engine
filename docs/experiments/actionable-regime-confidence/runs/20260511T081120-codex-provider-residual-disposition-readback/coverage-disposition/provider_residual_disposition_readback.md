# Provider Residual Disposition Readback

Run id: `20260511T081120+0800-codex-provider-residual-disposition-readback`

Goal achieved: `false`

- Bar cells represented: `396`
- Ready-not-yet-attempted cells: `0`
- Direct source-label slots attached: `16` / `612`
- Full four-root source-label cells: `4`
- IBKR attempted cells: `1`; OK `0`; failed `1`
- Polymarket catalog rows: `20`

## Disposition Counts

| Disposition | Count |
|---|---:|
| `accepted_overlay` | 1 |
| `blocked_operator_runtime_fetch` | 90 |
| `blocked_or_diagnostic` | 8 |
| `blocked_provider_unavailable` | 99 |
| `sidecar_catalog_materialized_root_confidence_pending` | 1 |
| `unsupported_for_accepted_confidence` | 204 |
| `unsupported_timeframe` | 3 |

## Decision

- Gate result: `provider_residuals_dispositioned_full_universe_labels_still_blocked`
- No OHLCV/proxy score is counted as accepted confidence.
- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

## Next Action

Acquire or provide an independent MainRegimeV2 source-label panel for the non-index, intraday/monthly, crypto, and provider-specific cells; only restart IBKR Gateway/TWS if bar coverage is needed after label coverage exists.
