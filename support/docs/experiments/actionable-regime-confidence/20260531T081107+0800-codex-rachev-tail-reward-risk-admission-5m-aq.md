# Rachev Tail Reward-Risk Admission 5m AQ Launch

- created_at: `20260531T081107+0800`
- owner: `codex`
- agent_name: `codex-rachev-tail-reward-risk-admission-5m-aq-20260531T081107+0800`
- run_root: `/tmp/ict-engine-rachev-tail-reward-risk-admission-aq-20260531T081107+0800`
- compact_root: `support/docs/experiments/actionable-regime-confidence/runs/20260531T081107+0800-codex-rachev-tail-reward-risk-admission-5m-aq-v1`
- repo_doc: `support/docs/experiments/actionable-regime-confidence/20260531T081107+0800-codex-rachev-tail-reward-risk-admission-5m-aq.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T081107+0800-codex-rachev-tail-reward-risk-admission-5m-aq.claim`
- factor_id: `tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_5m_v1`
- branch_path: `ValidationMaturity -> TailRewardRiskAsymmetry -> RachevExpectedTailGainLoss -> ParentSignalAdmissionFilter -> tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_5m_v1`
- timeframe: `5m`
- pair: `NQ/USD`
- timerange: `20210103-20251231`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- status: `terminalized_no_launch_blocked_by_foreign_fresh_claim`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Objective

Attempt the first real Auto-Quant slice for the Rachev tail reward-risk admission filter on the independent 5m factor only. The final self-claim guard found a foreign fresh active claim before Auto-Quant started, so this slice terminalized no-launch.

## Runtime Boundary

- AutoQuant/Freqtrade single-strategy backtest only.
- No provider fetch.
- No IBKR historical.
- No paper, simulated, or live execution.
- No Pre-Bayes, BBN, CatBoost, execution-tree, policy, or same_tree_practical_closure launch in this slice.
- Keep promotion_allowed=false, trade_usable=false, update_goal=false unless a later same-root practical lifecycle packet proves otherwise.

## Command

- `cd $HOME/Auto-Quant && .venv/bin/python /Users/thrill3r/projects-ict-engine/ict-engine/support/scripts/auto_quant_external/run_tomac_one.py TomacNq5mRachevTailRewardRiskAdmissionV1 5m /tmp/ict-engine-rachev-tail-reward-risk-admission-aq-20260531T081107+0800/checks/aq_trades_TomacNq5mRachevTailRewardRiskAdmissionV1.json NQ/USD 20210103-20251231`

## Evidence

- strategy_source: `/tmp/ict-engine-rachev-tail-reward-risk-admission-training-prep-20260531T075808+0800/materials/TomacNq5mRachevTailRewardRiskAdmissionV1.py`
- strategy_destination: `/Users/thrill3r/Auto-Quant/user_data/strategies_external/TomacNq5mRachevTailRewardRiskAdmissionV1.py`
- aq_export: not created; Auto-Quant did not start
- terminal_metrics: `/tmp/ict-engine-rachev-tail-reward-risk-admission-aq-20260531T081107+0800/checks/terminal_metrics.json`
- terminal_summary: `/tmp/ict-engine-rachev-tail-reward-risk-admission-aq-20260531T081107+0800/summaries/terminal_summary.json`

## Status

- decision: `launch_blocked_by_foreign_fresh_claim_before_aq_start`

## Terminal Readback

- terminal_status: `terminalized_no_launch_blocked_by_foreign_fresh_claim`
- terminal_decision: `launch_blocked_by_foreign_fresh_claim_before_aq_start`
- foreign_claim_blocker: `20260531T081025+0800-codex-k-ratio-equity-curve-consistency-aq.claim`
- provider_fetch_started: `false`
- ibkr_historical_started: `false`
- autoquant_started: `false`
- freqtrade_started: `false`
- downstream_lifecycle_started: `false`
- local_backtest_started: `false`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`
- terminal_metrics: `/tmp/ict-engine-rachev-tail-reward-risk-admission-aq-20260531T081107+0800/checks/terminal_metrics.json`
- terminal_summary: `/tmp/ict-engine-rachev-tail-reward-risk-admission-aq-20260531T081107+0800/summaries/terminal_summary.json`
