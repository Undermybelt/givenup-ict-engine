# R5 Redownload Readback Current Unlock Audit v1

Run id: `20260512T065134+0800-codex-r5-redownload-readback-current-unlock-audit-v1`

Gate result: `r5_redownload_readback_current_unlock_audit_v1=redownload_has_no_post_cutoff_rows_no_valid_unlock_no_downstream`

## Scope

Read-only audit of the loose `064908` Kaggle redownload and the current Board A required roots. This did not mutate `/tmp/ict-engine-source-panel-recency-extension`, approve TSIE, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## R5 Redownload Readback

- Path: `/tmp/ict-engine-board-a-r5-kaggle-stock-regimes-recency-redownload-v1/stock_market_regimes_2000_2026.csv`
- Exists: `True`
- Rows: `245021`
- Date range: `2000-01-03` to `2026-01-30`
- Rows after `2026-01-30`: `0`
- Ticker count: `39`

The redownloaded source panel is the same cutoff shape as the prior source package, so it does not supply the required R5 post-cutoff recency extension rows.

## Required Root Decision

- R6 owner/export root accepted: `false`
- R5 source-panel recency root accepted: `false`
- R3 native-subhour root accepted: `false`
- Valid required-root unlock: `false`

The R5 verifier was run against `/tmp/ict-engine-source-panel-recency-extension` and returned exit `2`. Its output is stored under `command-output/`.

## Accounting

- Accepted rows added: `0`
- Canonical merge: `false`
- Downstream promotion rerun: `false`
- Strict full objective: `false`
- Trade usable: `false`
- `update_goal=false`

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T065134+0800-codex-r5-redownload-readback-current-unlock-audit-v1/r5-redownload-readback-current-unlock-audit-v1/r5_redownload_readback_current_unlock_audit_v1.json`
- Required roots CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T065134+0800-codex-r5-redownload-readback-current-unlock-audit-v1/r5-redownload-readback-current-unlock-audit-v1/required_root_status_v1.csv`
- R5 redownload summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T065134+0800-codex-r5-redownload-readback-current-unlock-audit-v1/r5-redownload-readback-current-unlock-audit-v1/r5_redownload_summary_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T065134+0800-codex-r5-redownload-readback-current-unlock-audit-v1/checks/r5_redownload_readback_current_unlock_audit_v1_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 post-2026-01-30 recency rows, verifier-native Crisis-capable R3 MainRegimeV2 labels, or a genuinely new accepted cross-timeframe MainRegimeV2 source export before rerunning direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback.
