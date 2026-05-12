# R5 Kaggle Stock Regimes Recency Redownload v1

Run id: `20260512T064908+0800-codex-r5-kaggle-stock-regimes-recency-redownload-v1`

Gate result: `r5_kaggle_stock_regimes_recency_redownload_v1=download_ok_no_post_2026_01_30_recency_no_unlock`

## Scope

Corrected Kaggle download/readback for `mafaqbhatti/stock-market-regimes-20002026` after prior evidence showed the candidate as known daily/no post-cutoff. This packet verifies the actual downloaded file and does not mutate `/tmp/ict-engine-source-panel-recency-extension`, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Readback

- CSV: `/tmp/ict-engine-board-a-r5-kaggle-stock-regimes-recency-redownload-v1/stock_market_regimes_2000_2026.csv`
- Rows: `245021`
- Tickers: `39`
- Date range: `2000-01-03` to `2026-01-30`
- Labels: `Bear=54939, Bull=103766, Crisis=29632, High-volatility=16, Sideways=56668`
- Core Bull/Bear/Sideways/Crisis labels present: `True`
- Rows after `2026-01-30`: `0`

## Decision

The corrected download confirms the dataset is real and contains Bull/Bear/Sideways/Crisis-style daily labels, but it still ends on `2026-01-30`. It does not unlock the R5 post-cutoff recency root, does not satisfy R3 native-subhour evidence, and does not provide R6 owner/export controls. Promotion remains blocked: accepted rows added `0`, valid required root unlock false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T064908+0800-codex-r5-kaggle-stock-regimes-recency-redownload-v1/r5-kaggle-stock-regimes-recency-redownload-v1/r5_kaggle_stock_regimes_recency_redownload_v1.json`
- Label counts CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T064908+0800-codex-r5-kaggle-stock-regimes-recency-redownload-v1/r5-kaggle-stock-regimes-recency-redownload-v1/r5_kaggle_stock_regimes_label_counts_v1.csv`
- Recent dates CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T064908+0800-codex-r5-kaggle-stock-regimes-recency-redownload-v1/r5-kaggle-stock-regimes-recency-redownload-v1/r5_kaggle_stock_regimes_recent_dates_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T064908+0800-codex-r5-kaggle-stock-regimes-recency-redownload-v1/checks/r5_kaggle_stock_regimes_recency_redownload_v1_assertions.out`

## Next

Do not materialize this file into `/tmp/ict-engine-source-panel-recency-extension` as an R5 unlock. Continue looking for source-owned post-`2026-01-30` recency rows, verifier-native R3 `MainRegimeV2` labels, R6 owner/export controls, or explicit source/control approval before canonical merge and downstream readback.
