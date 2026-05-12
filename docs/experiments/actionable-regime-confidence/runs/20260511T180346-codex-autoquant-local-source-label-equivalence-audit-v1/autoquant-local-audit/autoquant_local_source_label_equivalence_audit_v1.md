# Auto-Quant Local Source Label Equivalence Audit v1

Run ID: `20260511T180346+0800-codex-autoquant-local-source-label-equivalence-audit-v1`

This audit checks whether `/Users/thrill3r/Auto-Quant/user_data/data` can satisfy the Board A source-label equivalence request. It reads local cache metadata and source-panel labels only; it does not write raw provider rows into the repo and does not create generated labels.

## Decision

`autoquant_local_source_label_equivalence_audit_v1=no_new_source_labels_exact_daily_aapl_only`

- Auto-Quant feather files inspected: `40`.
- Local Auto-Quant symbols: `15`.
- Exact source-panel symbols in the cache: `AAPL`.
- Exact source-panel sub-hour files: `0`.
- Files extending after source-panel tail `2026-01-30`: `25`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Full objective achieved: `false`.
- `update_goal`: `false`.

## Why It Blocks

The local Auto-Quant cache is OHLCV/provider data. It is not a source-owned `MainRegimeV2` label panel.

Only `AAPL_USD-1d.feather` exactly matches a ticker in the stock-market-regimes source panel. That is daily same-symbol overlap and is already covered by `daily_main_root_source_inventory_v1`; it adds no native sub-hour label, no futures/crypto/FX equivalence, no source-panel recency beyond `2026-01-30`, and no direct `Manipulation` rows.

Non-exact symbols such as `SPY`, `QQQ`, `NQ`, `ES`, `BTC`, `ETH`, `SOL`, `BNB`, `AVAX`, `GLD`, and `EUR` remain blocked unless a source owner supplies labels or an explicit equivalence policy. Their OHLCV bars are not promoted into labels.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T180346-codex-autoquant-local-source-label-equivalence-audit-v1/autoquant-local-audit/autoquant_local_source_label_equivalence_audit_v1.json`
- File inventory CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T180346-codex-autoquant-local-source-label-equivalence-audit-v1/autoquant-local-audit/autoquant_local_source_label_equivalence_audit_v1_files.csv`
- Exact root overlap CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T180346-codex-autoquant-local-source-label-equivalence-audit-v1/autoquant-local-audit/autoquant_local_source_label_equivalence_audit_v1_exact_root_overlap.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T180346-codex-autoquant-local-source-label-equivalence-audit-v1/checks/autoquant_local_source_label_equivalence_audit_v1_assertions.out`

## Next

Fulfill `source_label_equivalence_request_v1` with source-owned labels or owner-approved equivalence policy. Until then, keep local Auto-Quant cache as provider coverage only, not as Board A confidence-gate evidence.
