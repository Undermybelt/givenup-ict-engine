# R5 Recency Yfinance Proxy Rejection v1

- Decision: `r5_recency_yfinance_proxy_rejection_v1=provider_ohlc_available_source_owned_rows_not_acquired`.
- Source panel date range: `2000-01-03..2026-01-30`; rows `245021`.
- Existing owner-request package remains rows-acquired `false`: `docs/experiments/actionable-regime-confidence/runs/20260511T201655-codex-stock-regime-owner-recency-request-package-v1/stock-regime-owner-recency-request-package/stock_regime_owner_recency_request_package_v1.json`.
- yfinance post-cutoff OHLC probe targets: `['AMD', 'XOM', 'UNH', '^DJI']`; all targets returned rows `true`.
- Raw yfinance rows were not written to repo and were not copied into the R5 intake.
- Recency verifier before/after: `blocked` / `blocked`.
- R5 source-owned rows acquired: `false`; extension files created: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.

## Provider Probe

| Symbol | Rows | Date Range | R5 Usable | Reason |
|---|---:|---|---|---|
| `AMD` | `68` | `2026-02-02..2026-05-08` | `false` | provider_ohlc_only_not_source_owned_regime_labels |
| `XOM` | `68` | `2026-02-02..2026-05-08` | `false` | provider_ohlc_only_not_source_owned_regime_labels |
| `UNH` | `68` | `2026-02-02..2026-05-08` | `false` | provider_ohlc_only_not_source_owned_regime_labels |
| `^DJI` | `68` | `2026-02-02..2026-05-08` | `false` | provider_ohlc_only_not_source_owned_regime_labels |

## Boundary

This slice proves current provider OHLC is reachable for the requested post-cutoff symbols, but it deliberately rejects those rows for R5 because the verifier contract requires source-owned regime labels and provenance, not derived or provider-only OHLC proxies.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T215547-codex-r5-recency-yfinance-proxy-rejection-v1/r5-recency-yfinance-proxy-rejection/r5_recency_yfinance_proxy_rejection_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T215547-codex-r5-recency-yfinance-proxy-rejection-v1/r5-recency-yfinance-proxy-rejection/r5_recency_yfinance_proxy_rejection_v1.md`
- Provider summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T215547-codex-r5-recency-yfinance-proxy-rejection-v1/r5-recency-yfinance-proxy-rejection/r5_recency_yfinance_proxy_rejection_provider_summary_v1.csv`
- Recency verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T215547-codex-r5-recency-yfinance-proxy-rejection-v1/command-output/source_panel_recency_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T215547-codex-r5-recency-yfinance-proxy-rejection-v1/checks/r5_recency_yfinance_proxy_rejection_v1_assertions.out`
