# R5 Kaggle Stock Regime Recency Refresh v1

- Decision: `r5_kaggle_stock_regime_recency_refresh_v1=latest_public_dataset_no_post_2026_01_30_rows`.
- Dataset: `mafaqbhatti/stock-market-regimes-20002026`.
- Download root: `/tmp/ict-engine-kaggle-stock-regimes-live-refresh-20260511T215621`.
- Rows: `245021`; date range `2000-01-03` to `2026-01-30`.
- Download matches local reference: `true`.
- Post-cutoff root rows after `2026-01-30`: `0`.
- R5 verifier status: `blocked`; return code `2`.
- Intake rows written: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `true`; trade usable: `false`.

## Target Cells

| Symbol | Label | Split Role | Required New Sessions | Post-Cutoff Rows |
|---|---|---|---:|---:|
| `XOM` | `Sideways` | `heldout_time` | `5` | `0` |
| `UNH` | `Bear` | `calibration` | `7` | `0` |
| `^DJI` | `Sideways` | `calibration` | `7` | `0` |
| `AMD` | `Bear` | `calibration` | `10` | `0` |

## Interpretation

The current public Kaggle source-owned panel was fetched live into `/tmp` and compared against the local reference. It still ends at the accepted source cutoff, so this run cannot populate the R5 post-cutoff recency intake without generating proxy labels.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T215621-codex-r5-kaggle-stock-regime-recency-refresh-v1/r5-kaggle-stock-regime-recency-refresh/r5_kaggle_stock_regime_recency_refresh_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T215621-codex-r5-kaggle-stock-regime-recency-refresh-v1/r5-kaggle-stock-regime-recency-refresh/r5_kaggle_stock_regime_recency_refresh_v1.md`
- Target CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T215621-codex-r5-kaggle-stock-regime-recency-refresh-v1/r5-kaggle-stock-regime-recency-refresh/r5_kaggle_stock_regime_recency_refresh_targets_v1.csv`
- Kaggle files stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T215621-codex-r5-kaggle-stock-regime-recency-refresh-v1/command-output/kaggle_files.stdout.txt`
- Kaggle download stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T215621-codex-r5-kaggle-stock-regime-recency-refresh-v1/command-output/kaggle_download.stdout.txt`
- R5 verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T215621-codex-r5-kaggle-stock-regime-recency-refresh-v1/command-output/source_panel_recency_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T215621-codex-r5-kaggle-stock-regime-recency-refresh-v1/checks/r5_kaggle_stock_regime_recency_refresh_v1_assertions.out`
