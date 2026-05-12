# Long-History NQ 1m AQ TOMAC First Slice v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T135807+0800-codex-long-history-nq-1m-aq-tomac-first-slice-v1`

## Purpose

Stage a bounded, isolated Auto-Quant TOMAC smoke over NQ long-history data from `/Users/thrill3r/Downloads/Tomac/ict-cleaned-mtf/` without editing repo runtime code, the shared Auto-Quant checkout, or Board A.

This is support-only evidence. It is not a Board A acceptance packet, not a calibrated regime-confidence result, not a provider-context matrix, and not an execution promotion.

## Evidence

- Stage summary: `nq_long_history_stage_summary_ms.json`
- Isolated workspace: `auto_quant_workspace/`
- Command outputs/checks: `command-output/`, `checks/`
- Corrected TOMAC run: `command-output/04_run_tomac_nq_long_history_abs.out`

## Staging

The first staging pass wrote Freqtrade `date` values in seconds, so it was corrected in `03_restage_nq_long_history_feathers_ms`.

Corrected staged files:

| Timeframe | Rows | First ms | Last ms |
|---|---:|---:|---:|
| 1m | 301577 | 1341578760000 | 1698337140000 |
| 1h | 8880 | 1341576000000 | 1698336000000 |
| 4h | 2912 | 1341576000000 | 1698336000000 |
| 1d | 724 | 1341532800000 | 1698278400000 |

The first TOMAC invocation used a relative script path under `uv --directory` and exited `2`; `04_run_tomac_nq_long_history_abs` reran with the absolute isolated script path and exited `0`.

## TOMAC Result

Strategy: `TomacNQ_KillzoneBreakout`

Backtest window: `2012-07-16 22:00:00` to `2023-09-01 17:00:00`

Metrics:

- Trades: `91`
- Win rate: `70.3297%`
- Total profit: `10.2700%`
- Profit factor: `1.3274`
- Sharpe: `0.0468`
- Sortino: `0.0659`
- Calmar: `0.6800`
- Max drawdown: `-7.1020%`

## Decision

This is a real long-span NQ TOMAC backtest packet and confirms that an isolated Auto-Quant-style run can consume the staged long-history data. It still fails Board A promotion because it has not yet passed provider-context validation, chronological calibration, Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution-tree admission.

Net Board A effect remains fail-closed:

- accepted `>=0.95` contexts: `0`
- strict full objective: `false`
- trade usable: `false`
- promotion allowed: `false`
- `update_goal=false`

## Next

Do not register this packet ahead of the active richer long-history chains. Use it only as support evidence for the NQ TOMAC staging path if those chains need a standalone Auto-Quant smoke artifact.
