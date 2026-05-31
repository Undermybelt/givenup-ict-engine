# TOMAC Sequential Betting Trend Admission Local Screen

- agent_name: `codex-tomac-sequential-betting-trend-admission-local-screen-20260531T092549+0800`
- run_root: `/tmp/ict-engine-tomac-sequential-betting-trend-admission-local-screen-20260531T092549+0800`
- workdoc: `/tmp/ict-engine-tomac-sequential-betting-trend-admission-local-screen-20260531T092549+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T092549+0800-codex-tomac-sequential-betting-trend-admission-local-screen.claim`
- factor_id: `tomac_sequential_betting_trend_admission_filter_v1`
- branch_path: `TrendExpansion -> SequentialBettingMartingale -> TrendAdmissionFilter -> tomac_sequential_betting_trend_admission_filter_v1`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- status: `terminalized_no_launch_blocked_by_foreign_live_runtime`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Current-State Guard

Same-turn collision guard before creating this lane:

- `python3 support/scripts/factor_claim_terminalization_audit.py --compact`
  returned `status=pass`, `active_claims=0`, `valid_active_claims=0`,
  `live_factor_processes=0`, `promotion_allowed_true=0`,
  `trade_usable_true=0`.
- Focused `ps` found no AQ/TOMAC/provider/IBKR runtime process.
- `git status --short` is extremely dirty; only this tracking doc belongs to
  this slice.

## Duplicate Search

Focused same-turn search over active `/tmp` claims, top-level experiment docs,
and scripts found no exact `martingale`, `testing by betting`, `sequential
betting`, or `change-of-measure` candidate. Nearby axes already covered and
excluded: asymmetric capture/drawup, LPPL drawup exhaustion, macro event
windows, pre-FOMC, GSCPI/macro uncertainty, volume clock, VPT/OBV/CMF/Klinger,
and pair relative-value.

## Source Basis

- Waudby-Smith and Ramdas, "Estimating means of bounded random variables by betting", JRSSB 2024.
- Oxford page: `https://academic.oup.com/jrsssb/article/86/1/1/7043257`
- arXiv preprint: `https://arxiv.org/abs/2010.09686`

This packet translates the source family into a completed-bar trend-admission
filter: bounded lagged returns update a rolling log-wealth score for long/short
alternatives; entries are allowed only when wealth exceeds a threshold and
shifted `15m/1h/4h` slope context agrees with side. This is source-backed idea
translation, not statistical proof of alpha.

## Planned Local Screen

Script:

`/tmp/ict-engine-tomac-sequential-betting-trend-admission-local-screen-20260531T092549+0800/scripts/run_sequential_betting_trend_admission_screen.py`

Data:

- `/Users/thrill3r/Downloads/Tomac/factor_training/cache/NQ_1m.parquet`
- `/Users/thrill3r/Downloads/Tomac/factor_training/cache/YM_1m.parquet`
- `/Users/thrill3r/Downloads/Tomac/factor_training/cache/XAU_1m.parquet`
- shifted context from matching `15m/1h/4h` cache files

Classification rules:

- local stress telemetry uses `5bps/side`; it is not verified cost authority.
- candidate rows still require exact AQ/provider replay and verified instrument
  cost before any downstream or practical claim.
- all practical flags remain false in this slice.

## Terminal Readback

- terminal_decision: `terminalized_no_launch_blocked_by_foreign_live_runtime`
- reason: a fresh foreign local screen became live before this screen was
  launched.
- live blocker: `/tmp/ict-engine-trend-magic-cci-atr-mtf-continuation-local-screen-20260531T092345+0800`
- blocker pid: `23409`
- blocker claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T092345+0800-codex-trend-magic-local-screen.claim`
- py_compile: `exit=0`
- local_screen_started: `false`
- provider_fetch_started: `false`
- ibkr_historical_started: `false`
- auto_quant_started: `false`
- tomac_freqtrade_started: `false`
- paper_sim_live_started: `false`
- downstream_lifecycle_started: `false`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

Terminal artifacts:

- `/tmp/ict-engine-tomac-sequential-betting-trend-admission-local-screen-20260531T092549+0800/checks/terminal_metrics.json`
- `/tmp/ict-engine-tomac-sequential-betting-trend-admission-local-screen-20260531T092549+0800/summaries/terminal_decision_summary.md`
