# R6 Broad Normal Order-Lifecycle Screen v1

- Decision: `r6_broad_normal_order_lifecycle_screen_v1=sidecar_controls_acquired_shared_intake_not_mutated_confidence_still_blocked`.
- Independent broad-normal sidecar controls acquired: `80`.
- Shared R6 intake mutated: `false`; live calibration accepted: `false`.
- Strict full objective achieved: `false`; new confidence gate: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.

## Source Result

- Nasdaq ITCH directory URL: `https://emi.nasdaq.com/ITCH/Nasdaq%20ITCH/`.
- Nasdaq ITCH sample URL: `https://emi.nasdaq.com/ITCH/Nasdaq%20ITCH/S010303-v2.zip`.
- Nasdaq ITCH spec HEAD: status `200`, content length `1200722`.
- Sample zip bytes: `58907174`; SHA256 `eb67a239cf09b7de1843f6b0ede3c473616cc5cac777b293bbe15608bf51794d`.
- Parsed messages: `250000`; orders seen `136210`; controls materialized `80`.
- Sidecar CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1/r6-broad-normal-order-lifecycle-screen/broad_normal_market_order_lifecycle_controls_v1.csv`.
- Live R6 verifier readback: positives `57`, matched negatives `57`, matched groups `56`.

## Provider Screen

| Source | Status | R6 Control Value | Reason |
|---|---|---|---|
| `ibkr` | `screened_not_accepted` | `blocked` | current provider-status reports missing ibkr runtime dependencies; even healthy IBKR historical ticks are bid/ask/trade data, not public participant/order-lifecycle controls. |
| `tradingview_mcp_or_remix` | `screened_not_accepted` | `blocked` | TradingView surfaces are OHLCV/chart-feature sources in this workflow, not order add/cancel/execute lifecycle feeds. |
| `yfinance` | `screened_not_accepted` | `blocked` | Yahoo/yfinance is OHLCV/chart data; even when the chart probe is reachable, the surface is not order-lifecycle evidence. |
| `kraken_public_depth` | `screened_not_accepted` | `blocked` | Kraken public depth is a live aggregated book snapshot with price/size/time levels, not durable order IDs or add/cancel/execute lifecycles. |
| `nasdaq_itch_s010303` | `accepted_sidecar_control_source` | `independent_broad_normal_order_lifecycle_controls_sidecar` | Nasdaq ITCH sample provides direct add/execute/cancel/delete order lifecycle messages from an exchange-feed background day. |

## Boundary

The sidecar is independent exchange-feed order-lifecycle background data. It is not a positive spoofing/layering source and was not appended to the shared `/tmp/ict-engine-direct-manipulation-row-intake` CSVs during concurrent work.

This closes only the source-screen/acquisition part of the broad-normal blocker. The R6 confidence gate remains blocked because positive direct rows are still below the Wilson95 support needed for `>=0.95`, split gates still lack support, and direct species coverage is incomplete.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1/r6-broad-normal-order-lifecycle-screen/r6_broad_normal_order_lifecycle_screen_v1.json`
- Sidecar controls CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1/r6-broad-normal-order-lifecycle-screen/broad_normal_market_order_lifecycle_controls_v1.csv`
- Provider/source screen CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1/r6-broad-normal-order-lifecycle-screen/r6_broad_normal_source_screen_v1.csv`
- Command outputs: `docs/experiments/actionable-regime-confidence/runs/20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1/command-output/`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T222000-codex-r6-broad-normal-order-lifecycle-screen-v1/checks/r6_broad_normal_order_lifecycle_screen_v1_assertions.out`

## Raw Data Boundary

Raw downloads are under `/tmp/ict-engine-r6-broad-normal-order-lifecycle-screen-v1` and are not committed.
