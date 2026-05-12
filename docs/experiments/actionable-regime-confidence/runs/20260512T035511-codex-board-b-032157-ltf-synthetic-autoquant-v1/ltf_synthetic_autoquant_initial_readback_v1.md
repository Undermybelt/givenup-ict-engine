# LTF Synthetic Auto-Quant Initial Readback v1

Run root:
`docs/experiments/actionable-regime-confidence/runs/20260512T035511-codex-board-b-032157-ltf-synthetic-autoquant-v1`

This is an append-only readback of the initial `035511` LTF synthetic Auto-Quant attempt for Board B. It does not edit the Board B Current Cursor and does not supersede concurrent repair runs under `035139`, `035427`, or later `035511` diagnostics.

## Command Results

| Command | Exit | Evidence |
|---|---:|---|
| `00_factor_research_synthetic_profile` | 0 | `command-output/00_factor_research_synthetic_profile.out` |
| `01_auto_quant_prepare_synthetic_env` | 0 | `command-output/01_auto_quant_prepare_synthetic_env.out` |
| `02_factor_research_after_prepare` | 0 | `command-output/02_factor_research_after_prepare.out` |
| `03_auto_quant_run_tomac` | 1 | `command-output/03_auto_quant_run_tomac.out`, `command-output/03_auto_quant_run_tomac.err` |

## Readback

- Factor-research and synthetic Auto-Quant prepare ran successfully.
- The final handoff state became `dependency_ready_data_ready` with one active strategy.
- The actual Auto-Quant backtest did not produce a profitability packet. It failed with `OperationalException: No pair in whitelist.`
- No RC-SPA, Pre-Bayes, BBN, CatBoost/path-ranker, or execution-tree promotion step can be credited from this initial slice.

## Decision

Gate: `fail:auto_quant_backtest_no_pair_whitelist`.

Promotion: `false`.

Next: repair the Auto-Quant pair/market construction in the active repair lane, then rerun the measured backtest before any downstream promotion readback.
