# Kaggle Stock Regime Live Refresh v1

- Decision: `kaggle_stock_regime_live_refresh_v1=downloaded_latest_public_dataset_no_post_2026_01_30_rows`
- Dataset: `mafaqbhatti/stock-market-regimes-20002026`
- Dataset URL: `https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026`
- Pull commands: `kaggle datasets files ... -v` and `kaggle datasets download ... --unzip`
- Download root: `/tmp/ict-engine-kaggle-stock-regimes-live-refresh-v1`
- Rows: `245021`
- Date range: `2000-01-03` to `2026-01-30`
- Downloaded CSV SHA256: `2c8a3d8bc3c834f89eb776cf69930c041f1059a895e115b623d4427f67193cd0`
- Matches local reference CSV: `True`
- Post-cutoff target rows after `2026-01-30`: `0`
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Target Cells

| Symbol | Label | Split Role | Required New Sessions | Post-Cutoff Rows |
|---|---|---|---:|---:|
| `XOM` | `Sideways` | `heldout_time` | 5 | 0 |
| `UNH` | `Bear` | `calibration` | 7 | 0 |
| `^DJI` | `Sideways` | `calibration` | 7 | 0 |
| `AMD` | `Bear` | `calibration` | 10 | 0 |

## Decision

The latest public Kaggle dataset was acquired into `/tmp` and analyzed without committing raw rows. It is byte-identical to the local reference CSV and still ends at `2026-01-30`, so it cannot populate the post-cutoff recency extension intake or close R5.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T202501-codex-kaggle-stock-regime-live-refresh-v1/kaggle-stock-regime-live-refresh/kaggle_stock_regime_live_refresh_v1.json`
- Target CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T202501-codex-kaggle-stock-regime-live-refresh-v1/kaggle-stock-regime-live-refresh/kaggle_stock_regime_live_refresh_v1_targets.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T202501-codex-kaggle-stock-regime-live-refresh-v1/checks/kaggle_stock_regime_live_refresh_v1_assertions.out`
