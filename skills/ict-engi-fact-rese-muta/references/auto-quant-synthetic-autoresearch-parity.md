# Auto-Quant synthetic autoresearch and downstream parity notes

Use for ict-engine Board B profitability-factor runs where Auto-Quant's managed `factor-autoresearch --auto-quant-profile synthetic_ohlcv` is used after a real provider/AQ Gate 1 packet.

## Durable lesson

- Treat `factor-autoresearch --backend auto-quant` as a control-plane handoff unless it runs on the exact provider/symbol/timeframe contract being claimed.
- If `auto-quant-profile=synthetic_ohlcv` maps multiple real symbols/timeframes into synthetic `ETF/USD` (often 1h), positive `run_tomac.py` results are seed/mechanical evidence only.
- Do not promote synthetic profile results to live parity, even if all strategies show positive returns, high Sharpe, or zero failures.
- Preserve the distinction in terminal summaries:
  - real provider Gate 1 evidence
  - downstream ict-engine parity evidence
  - synthetic Auto-Quant autoresearch evidence
  - live-readiness verdict

## Minimum report fields

- `source_run_root`
- `downstream_run_root`
- `autoresearch_workspace`
- rooted `branch_path`
- provider/symbol/timeframe of real Gate 1 rows
- whether exact branch survived downstream
- `path_ranker_score_visible_to_execution_tree`
- `path_ranker_score_used_by_execution_tree`
- `ranker_validation_ready`
- `closed_loop_branch_admission.status`
- `execution_tree_branch`
- `promotion_allowed`
- `trade_usable`
- explicit note if synthetic profile collapsed symbol/timeframe

## Pattern from 2026-05-18 TOD slot-alpha run

A YF SPY/QQQ/IWM 15m same-time-slot factor had real Gate 1 positives and downstream CatBoost visibility, but execution stayed fail-closed:

- Branch: `Range -> IntradaySeasonality -> same_time_slot_alpha -> yf_etf_tod_slot_alpha_15m_cost_gate_v2`
- AQ rank: `3/3` positive rows, `18` trades
- Downstream: all commands exited `0`; exact branch survived; path-ranker visible/used `true/true`
- Blocker: `closed_loop_branch_admission.status=fail_closed`, `execution_tree_branch=transition_guardrail`, `ranker_validation_ready=false`, candidate `actionable=false`
- Synthetic Auto-Quant `run_tomac.py`: `3 succeeded, 0 failed`, each seed `4` trades, `15.63%`, Sharpe `6.2451` on synthetic `ETF/USD` 1h
- Verdict: keep as seed/incubate evidence only; not live-ready and not trade-usable.
