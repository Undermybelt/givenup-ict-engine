# Stock Regime Upstream Refresh Audit v1

Run ID: `20260511T181454+0800-codex-stock-regime-upstream-refresh-audit-v1`

This audit checks the upstream Kaggle source package for source-owned labels newer than the local stock-market-regimes panel. It records metadata and file listings only; it does not download or commit raw source rows.

## Decision

`stock_regime_upstream_refresh_audit_v1=no_new_upstream_recency_extension`

- Dataset: `mafaqbhatti/stock-market-regimes-20002026`
- Dataset URL: `https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026`
- Local source max date: `2026-01-30`.
- Local rows / tickers: `245021` / `39`.
- Upstream CSV size matches local: `true`.
- Upstream parquet size matches local: `true`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Full objective achieved: `false`.
- `update_goal`: `false`.

## Why It Blocks

The upstream file listing does not expose a newer source-panel revision. The local CSV size is `37155794` bytes and the upstream CSV listing is `37155794` bytes. The local parquet size is `6583934` bytes and the upstream parquet listing is `6583934` bytes.

The source labels still end at `2026-01-30`, so the `2026-01-30` recency blocker remains live. Provider candles after that date cannot be promoted into source labels.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T181454-codex-stock-regime-upstream-refresh-audit-v1/upstream-refresh/stock_regime_upstream_refresh_audit_v1.json`
- Kaggle file listing: `docs/experiments/actionable-regime-confidence/runs/20260511T181454-codex-stock-regime-upstream-refresh-audit-v1/upstream-refresh/stock_regime_upstream_refresh_audit_v1_files.txt`
- Metadata JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T181454-codex-stock-regime-upstream-refresh-audit-v1/upstream-refresh/dataset-metadata.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T181454-codex-stock-regime-upstream-refresh-audit-v1/checks/stock_regime_upstream_refresh_audit_v1_assertions.out`

## Next

Keep `source_panel_recency_extension_manifest_v1` fail-closed until a source owner publishes post-`2026-01-30` rows or the required `/tmp/ict-engine-source-panel-recency-extension` intake files are supplied.
