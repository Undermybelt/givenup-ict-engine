# Rachev Tail Reward-Risk Admission Training Prep

- created_at: `20260531T075808+0800`
- owner: `codex`
- agent_name: `codex-rachev-tail-reward-risk-admission-training-prep-20260531T075808+0800`
- run_root: `/tmp/ict-engine-rachev-tail-reward-risk-admission-training-prep-20260531T075808+0800`
- compact_root: `support/docs/experiments/actionable-regime-confidence/runs/20260531T075808+0800-codex-rachev-tail-reward-risk-admission-training-prep-v1`
- repo_doc: `support/docs/experiments/actionable-regime-confidence/20260531T075808+0800-codex-rachev-tail-reward-risk-admission-training-prep.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T075808+0800-codex-rachev-tail-reward-risk-admission-training-prep.claim`
- source_packet: `support/docs/experiments/actionable-regime-confidence/20260531T073131+0800-codex-rachev-tail-reward-risk-admission-source-prep.md`
- factor_family: `rachev_tail_reward_risk_admission_filter`
- branch_path: `ValidationMaturity -> TailRewardRiskAsymmetry -> RachevExpectedTailGainLoss -> ParentSignalAdmissionFilter`
- session_scope: `ETH/full_retained_session`
- rth_filter_applied: `false`
- status: `terminalized_training_prep_no_launch`
- coordination_only: `true`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Objective

Turn the Rachev source packet into a launch-ready training prep packet while a fresh active Board B claim blocks shared runtime. This writes exact strategy materials and commands only; it does not fetch, backtest, launch AutoQuant, or downstream lifecycle.

## Independent Factors

- `tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_5m_v1` -> `/tmp/ict-engine-rachev-tail-reward-risk-admission-training-prep-20260531T075808+0800/materials/TomacNq5mRachevTailRewardRiskAdmissionV1.py`
- `tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_15m_v1` -> `/tmp/ict-engine-rachev-tail-reward-risk-admission-training-prep-20260531T075808+0800/materials/TomacNq15mRachevTailRewardRiskAdmissionV1.py`
- `tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_30m_v1` -> `/tmp/ict-engine-rachev-tail-reward-risk-admission-training-prep-20260531T075808+0800/materials/TomacNq30mRachevTailRewardRiskAdmissionV1.py`
- `tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_1h_v1` -> `/tmp/ict-engine-rachev-tail-reward-risk-admission-training-prep-20260531T075808+0800/materials/TomacNq1hRachevTailRewardRiskAdmissionV1.py`
- `tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_4h_v1` -> `/tmp/ict-engine-rachev-tail-reward-risk-admission-training-prep-20260531T075808+0800/materials/TomacNq4hRachevTailRewardRiskAdmissionV1.py`
- `tomac_idxfut_clean_rachev_tail_reward_risk_admission_filter_1d_v1` -> `/tmp/ict-engine-rachev-tail-reward-risk-admission-training-prep-20260531T075808+0800/materials/TomacNq1dRachevTailRewardRiskAdmissionV1.py`

## Runtime Boundary

- No provider fetch.
- No IBKR historical.
- No AutoQuant, Freqtrade, or TOMAC runtime launch.
- No retained-cache local screen or local backtest launch.
- No paper, simulated, or live execution.
- No downstream lifecycle launch.
- No same_tree_practical_closure packet.
- No promotion_allowed=true, trade_usable=true, or update_goal=true.

## Feature Contract

Use only completed, shifted return windows. Rachev admission compares rolling upper-tail gain with lower-tail loss before entry, then gates an existing parent trend/pullback signal. The first runnable slice must compare parent-only versus parent-plus-Rachev under ETH/full-retained coverage, verified instrument cost, sample, density, year split, accepted execution feedback, and lifecycle gates.

## Commands When Claim Audit Clears

- `${AUTO_QUANT_PY:-$HOME/Auto-Quant/.venv/bin/python} support/scripts/auto_quant_external/run_tomac_one.py TomacNq5mRachevTailRewardRiskAdmissionV1 5m /tmp/ict-engine-rachev-tail-reward-risk-admission-training-prep-20260531T075808+0800/checks/aq_trades_TomacNq5mRachevTailRewardRiskAdmissionV1.json NQ/USD 20210103-20251231`
- `${AUTO_QUANT_PY:-$HOME/Auto-Quant/.venv/bin/python} support/scripts/auto_quant_external/run_tomac_one.py TomacNq15mRachevTailRewardRiskAdmissionV1 15m /tmp/ict-engine-rachev-tail-reward-risk-admission-training-prep-20260531T075808+0800/checks/aq_trades_TomacNq15mRachevTailRewardRiskAdmissionV1.json NQ/USD 20210103-20251231`
- `${AUTO_QUANT_PY:-$HOME/Auto-Quant/.venv/bin/python} support/scripts/auto_quant_external/run_tomac_one.py TomacNq30mRachevTailRewardRiskAdmissionV1 30m /tmp/ict-engine-rachev-tail-reward-risk-admission-training-prep-20260531T075808+0800/checks/aq_trades_TomacNq30mRachevTailRewardRiskAdmissionV1.json NQ/USD 20210103-20251231`
- `${AUTO_QUANT_PY:-$HOME/Auto-Quant/.venv/bin/python} support/scripts/auto_quant_external/run_tomac_one.py TomacNq1hRachevTailRewardRiskAdmissionV1 1h /tmp/ict-engine-rachev-tail-reward-risk-admission-training-prep-20260531T075808+0800/checks/aq_trades_TomacNq1hRachevTailRewardRiskAdmissionV1.json NQ/USD 20210103-20251231`
- `${AUTO_QUANT_PY:-$HOME/Auto-Quant/.venv/bin/python} support/scripts/auto_quant_external/run_tomac_one.py TomacNq4hRachevTailRewardRiskAdmissionV1 4h /tmp/ict-engine-rachev-tail-reward-risk-admission-training-prep-20260531T075808+0800/checks/aq_trades_TomacNq4hRachevTailRewardRiskAdmissionV1.json NQ/USD 20210103-20251231`
- `${AUTO_QUANT_PY:-$HOME/Auto-Quant/.venv/bin/python} support/scripts/auto_quant_external/run_tomac_one.py TomacNq1dRachevTailRewardRiskAdmissionV1 1d /tmp/ict-engine-rachev-tail-reward-risk-admission-training-prep-20260531T075808+0800/checks/aq_trades_TomacNq1dRachevTailRewardRiskAdmissionV1.json NQ/USD 20210103-20251231`

## Status

- decision: `prep_packet_complete_no_launch_runtime_blocked`
- next_gate: `run_one_timeframe_after_claim_audit_clears`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`
