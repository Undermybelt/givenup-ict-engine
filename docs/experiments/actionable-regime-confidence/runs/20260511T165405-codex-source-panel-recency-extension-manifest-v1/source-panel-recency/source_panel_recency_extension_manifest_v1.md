# Source Panel Recency Extension Manifest v1

Run ID: `20260511T165405+0800-codex-source-panel-recency-extension-manifest-v1`

This turns the post-`2026-01-30` source-label recency gap into an executable intake package. It does not generate labels.

## Result

- Current source panel max date: `2026-01-30`.
- Audit date: `2026-05-11`.
- Weekday sessions after max date: `71`.
- Estimated extension rows for the existing `39` tickers: `2769`.
- Extension rows added: `0`.
- Gate result: `source_panel_recency_extension_manifest_v1=ready_rows_not_acquired`.
- Full objective achieved: `false`; `update_goal=false`.

## Required Files

| File | Destination | Purpose |
|---|---|---|
| `stock_market_regimes_2026_extension.csv` | `/tmp/ict-engine-source-panel-recency-extension/stock_market_regimes_2026_extension.csv` | source-owned MainRegimeV2 rows after 2026-01-30 using the existing source-panel columns |
| `source_panel_recency_provenance.json` | `/tmp/ict-engine-source-panel-recency-extension/source_panel_recency_provenance.json` | source identity, owner, pull date, generation/export notes, and non-proxy attestation |

## Verifier

```bash
python3 docs/experiments/actionable-regime-confidence/runs/20260511T165405-codex-source-panel-recency-extension-manifest-v1/source-panel-recency/source_panel_recency_extension_verifier_v1.py --intake-root /tmp/ict-engine-source-panel-recency-extension
```

The verifier is fail-closed for missing files, schema drift, non-recency dates, unknown tickers, duplicate date/ticker rows, and non-root labels.
