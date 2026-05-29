# IBKR QQQ Micro Trend Reclaim Density Training

- created_at: `2026-05-29T13:39:42+0800`
- owner: `codex`
- route: `ict-engine/ict-engine-runtime`
- repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- branch: `main`
- run_root: `/tmp/ict-engine-ibkr-qqq-intraday-micro-trend-reclaim-density-20260529T133942+0800`
- tmp_workdoc: `/tmp/ict-engine-ibkr-qqq-intraday-micro-trend-reclaim-density-20260529T133942+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260529T133942+0800-codex-ibkr-qqq-micro-trend-reclaim-density-training.claim`
- factor_id: `ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1`
- branch_path: `US -> equity_etf -> QQQ -> 1m -> Trend -> SessionLiquidity -> intraday_micro_trend_reclaim_density -> ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1`

## Profit Idea

Use QQQ as a high-liquidity equity-index ETF proxy and test a trend-rooted intraday micro-reclaim branch. The regime root is market/product/symbol/timeframe first, then `Trend -> SessionLiquidity`, then the profit factor `intraday_micro_trend_reclaim_density`. The signal requires short-term EMA trend persistence, session VWAP reclaim, RVOL participation, RSI sanity bounds, and bounded VWAP/ATR extension so it does not buy late exhaustion.

## Gate Plan

1. Preserve `/tmp` run state by launching `run_ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1.py` with `ICT_ENGINE_RUN_ROOT_OVERRIDE`.
2. Prefer direct IBKR historical rows: `1m` origin plus `5m/15m/30m/1h/4h/1d` context.
3. Generate Auto-Quant material only from nonzero provider rows; material rows must keep `branch_path`, `main_regime`, `sub_regime`, profit factor, provider, symbol, and timeframe fields.
4. Apply hard cost stress. Downstream is blocked unless the exact `1m` origin survives cost/density and branch fields are preserved.
5. If Gate 1 passes, continue same-root Auto-Quant import/prior, Pre-Bayes, BBN, CatBoost/path-ranker, execution-tree, and policy-status readback. Do not relax gates.

## Non-Duplicate Readback

- Current compact audit before this doc showed one unrelated live KST/Coppock Python prescreen claim: `/tmp/ict-engine-tomac-kst-coppock-portfolio-density-lift-pybacktest-20260529T133157+0800`.
- DailyDonchian `HoldCompressionCadenceLift` and `HoldCompressionSymbolBalanceGuard` were already terminalized fail-closed; DailyDonchian `RVOLAccelerationFilter` was freshly prepped this turn and remains non-launch.
- InitialBalance `SessionFilteredCadenceLift` was already terminalized with no 5bps survivor and explicitly should not be rerun unchanged.
- No QQQ micro-trend claim existed under `/tmp/ict-engine-agent-claims/board-b-factor-refinement` at claim time.

## Evidence

- `python3 -m unittest support/docs/experiments/actionable-regime-confidence/scripts/test_ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1.py -v` -> pass.
- `python3 -m py_compile support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1.py support/docs/experiments/actionable-regime-confidence/scripts/test_ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1.py` -> pass.
- Compact claim audit at `2026-05-29T13:48:16+0800`: `active_claims=1`, `live_factor_processes=1`, live root is the unrelated KST/Coppock prescreen; `promotion_allowed_true=0`, `trade_usable_true=0`.
- Launch readback: `/tmp/ict-engine-ibkr-qqq-intraday-micro-trend-reclaim-density-20260529T133942+0800/checks/terminal_metrics.json` reported zero provider rows, zero materials, zero rank rows, and no downstream gates.
- Provider status readback: `command-output/00_provider_status_ibkr.out` reported `market_data:0/1 ready`, `status=configured_runtime_unhealthy`, `reason=ibkr_gateway_unreachable`.
- Direct IBKR fetch readback: `command-output/01` through `07` all exited `1`; stderr shows `ConnectionRefusedError(61, "Connect call failed ('127.0.0.1', 4002)")` and `Cannot reach IBKR Gateway at 127.0.0.1:4002`.
- Local port readback at `2026-05-29T14:00:06+0800`: `nc -vz -w 2 127.0.0.1 4002` returned connection refused.
- Corrected runner classification: zero provider rows with failed provider fetch is now `provider_acquisition_blocked_no_gate1_verdict`, not a factor-quality `drop_gate1_no_ibkr_cost_density` verdict.
- Corrected runner no-material compile behavior: when no provider rows generate strategies, `08_strategy_py_compile` is skipped with exit `0` instead of invoking `py_compile` with no filenames.
- Post-correction verification: `python3 -m unittest support/docs/experiments/actionable-regime-confidence/scripts/test_ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1.py -v` -> pass at `2026-05-29T14:00+0800`.
- Post-correction verification: `python3 -m py_compile support/docs/experiments/actionable-regime-confidence/scripts/run_ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1.py support/docs/experiments/actionable-regime-confidence/scripts/test_ibkr_qqq_intraday_micro_trend_reclaim_density_1m_mtf_v1.py` -> pass at `2026-05-29T14:00+0800`.

## Current Decision

`provider_acquisition_blocked_no_gate1_verdict`: the QQQ lane launched, but IBKR gateway/API was unreachable and all direct fetches returned zero rows. This is not a Gate 1 cost/density factor verdict. No Auto-Quant, BBN, CatBoost, execution-tree, promotion, or trade-usable claim is allowed. A retry may use the same run root after compact audit clears live runtime occupancy and IB Gateway/TWS API is reachable on the configured local port.
