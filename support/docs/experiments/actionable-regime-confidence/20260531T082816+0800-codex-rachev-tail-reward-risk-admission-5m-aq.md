# Rachev Tail Reward-Risk Admission 5m AQ

- created_at: `20260531T082816+0800`
- owner: `codex`
- agent_name: `codex-rachev-tail-reward-risk-admission-5m-aq-20260531T082816+0800`
- run_root: `/tmp/ict-engine-rachev-tail-reward-risk-admission-aq-20260531T082816+0800`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T082816+0800-codex-rachev-tail-reward-risk-admission-5m-aq.claim`
- factor_id: `tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_5m_v1`
- branch_path: `ValidationMaturity -> TailRewardRiskAsymmetry -> RachevExpectedTailGainLoss -> ParentSignalAdmissionFilter -> tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_5m_v1`
- timeframe: `5m`
- pair: `NQ/USD`
- timerange: `20210103-20251231`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- status: `terminalized_aq_backtest_exit0_fail_closed`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Objective

Run exactly one Auto-Quant/Freqtrade single-strategy backtest for the Rachev tail reward-risk admission filter on the independent 5m factor after compact audit cleared.

## Command

- `cd $HOME/Auto-Quant && .venv/bin/python /Users/thrill3r/projects-ict-engine/ict-engine/support/scripts/auto_quant_external/run_tomac_one.py TomacNq5mRachevTailRewardRiskAdmissionV1 5m /tmp/ict-engine-rachev-tail-reward-risk-admission-aq-20260531T082816+0800/checks/aq_trades_TomacNq5mRachevTailRewardRiskAdmissionV1.json NQ/USD 20210103-20251231`

## Evidence

- aq_exit: `/tmp/ict-engine-rachev-tail-reward-risk-admission-aq-20260531T082816+0800/checks/aq.exit`
- aq_export: `/tmp/ict-engine-rachev-tail-reward-risk-admission-aq-20260531T082816+0800/checks/aq_trades_TomacNq5mRachevTailRewardRiskAdmissionV1.json`
- aq_log: `/tmp/ict-engine-rachev-tail-reward-risk-admission-aq-20260531T082816+0800/logs/aq_stdout_stderr.log`
- terminal_metrics: `/tmp/ict-engine-rachev-tail-reward-risk-admission-aq-20260531T082816+0800/checks/terminal_metrics.json`
- terminal_summary: `/tmp/ict-engine-rachev-tail-reward-risk-admission-aq-20260531T082816+0800/summaries/terminal_summary.json`

## Terminal Readback

- command_exit: `0`
- total_trades: `2554`
- total_profit_pct: `15.507287664599998`
- profit_factor: `1.045204145367304`
- winrate_pct: `45.105716523101016`
- max_drawdown_pct: `27.625808870644182`
- config_fee: `0.0`
- cost_model_status: `zero_fee_config_not_promotion_cost_verified`
- data_fillup: `before=353842 after=524749 fillup_pct=48.3`
- provider_fetch_started: `false`
- ibkr_historical_started: `false`
- downstream_lifecycle_started: `false`
- paper_or_live_started: `false`
- accepted_execution_feedback: `false`
- same_tree_practical_closure: `null`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Decision

`aq_exit0_zero_fee_cost_unverified_no_downstream_no_promotion`

The AQ backtest completed and produced positive zero-fee gross evidence, but it is not trade-usable. The run used `fee=0.0`, did not verify the NQ futures promotion cost model, carried a 48.3% Freqtrade missing-data fillup warning, and did not run downstream practical lifecycle, paper/live feedback, or same-tree closure gates.
