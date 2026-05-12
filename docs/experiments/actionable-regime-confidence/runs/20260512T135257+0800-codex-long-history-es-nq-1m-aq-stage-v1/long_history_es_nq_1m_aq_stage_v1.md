# Long-History ES/NQ 1m Auto-Quant Stage v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T135257+0800-codex-long-history-es-nq-1m-aq-stage-v1`

## Scope

This is an isolated long-history Auto-Quant staging and measured TOMAC backtest over cleaned ES/NQ 1m-derived futures data. It does not edit repo runtime code, does not mutate `/Users/thrill3r/Auto-Quant/user_data/data`, does not update production BBN priors/CPDs, does not promote CatBoost/path-ranker or execution-tree state, does not make a trade-usable claim, and does not call `update_goal`.

## Evidence

- Staging script: `scripts/stage_long_history_es_nq_aq.py`
- Staging manifest: `long_history_es_nq_aq_stage_manifest.json`
- Staged row inventory: `long_history_es_nq_aq_stage_rows.csv`
- Isolated workspace: `workspace/auto-quant/`
- Auto-Quant command: `command-output/02_run_tomac_long_history_es_nq.cmd`
- Auto-Quant stdout/stderr: `command-output/02_run_tomac_long_history_es_nq.out`, `command-output/02_run_tomac_long_history_es_nq.err`
- Exit checks: `checks/01_stage_long_history_es_nq_aq.exit`, `checks/01b_stage_long_history_es_nq_aq_absolute.exit`, `checks/02_run_tomac_long_history_es_nq.exit`
- Metrics JSON: `long_history_es_nq_1m_aq_stage_v1.metrics.json`

## Decision

- The initial staging command failed with exit `2` because `uv --directory /Users/thrill3r/Auto-Quant` made the relative script path resolve under the Auto-Quant checkout. The corrected absolute-path staging command exited `0`.
- ES and NQ cleaned 1m JSON were staged into isolated Freqtrade feather data for `1m`, `5m`, `15m`, `1h`, `4h`, and `1d`.
- Staged NQ coverage: `301577` 1m rows from `2012-07-06T12:46:00Z` to `2023-10-26T16:19:00Z`; staged NQ 1h rows: `8880`.
- Staged ES coverage: `299107` 1m rows from `2012-04-23T13:38:00Z` to `2025-08-04T12:10:00Z`; staged ES 1h rows: `14036`.
- Real Auto-Quant/Freqtrade `run_tomac.py` exited `0` in the isolated workspace.
- TOMAC measured result: `224` total trades, total profit `2.00%`, win rate `58.0357%`, Sharpe `0.0192`, profit factor `1.0574`, max drawdown `-3.8626%`.
- NQ branch: `91` trades, total profit `3.44%`, win rate `70.3%`, Sharpe `0.0317`, profit factor `1.25`.
- ES branch: `133` trades, total profit `-1.45%`, win rate `49.6%`, Sharpe `-0.0145`, profit factor `0.93`.
- This is useful negative/weak evidence for the belief loop: the same TOMAC breakout idea is not cross-instrument stable on ES even though NQ is modestly positive.

## Board A Effect

Fail-closed. This root supplies a real long-history Auto-Quant candidate measurement and cross-instrument negative result, but it does not satisfy Board A acceptance:

- No per-regime calibrated posterior or path lower bound `>=0.95`.
- No chronological per-regime calibration packet.
- No Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree closure inside this run root.
- No production BBN prior/CPD mutation accepted.
- No execution readiness/actionability promotion.
- Accepted `>=95%` contexts remain `0`; strict full objective remains false; trade usable remains false; `update_goal=false`.

## Next

Use this run only as long-history Auto-Quant evidence. The next valid step is to feed the long-history NQ/ES evidence through the ordered downstream chain and treat the ES weakness as negative likelihood evidence for the TOMAC breakout branch rather than relaxing Board A acceptance.
