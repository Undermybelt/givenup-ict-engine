# NQ Compound RV Stress Lifecycle Driver

created_at: 2026-05-30T06:24:01+0800
agent_name: codex-nq-compound-rv-stress-lifecycle-driver
owner: codex
repo: /Users/thrill3r/projects-ict-engine/ict-engine
branch: main
run_root: /tmp/ict-engine-nq-compound-rv-stress-lifecycle-driver-20260530T062401+0800
claim: /tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T062401+0800-codex-nq-compound-rv-stress-lifecycle-driver.claim

## Scope

Repair and run the NQ compound RV-stress practical lifecycle wrapper so it can actually stage the provider/import, Pre-Bayes, BBN workflow, path-ranker, execution-tree, feedback-update, and policy-training command rows. This builds on the prior source/cost/coverage packet and keeps all practical flags false unless canonical same-tree closure is produced.

## Factor

factor_id: nq_compound_trend_rrr_chopfilter_rv_stress_gate_rescore_v1
parent_factor_id: nq_compound_trend_rrr_chopfilter_v1
session_scope: ETH/full_retained_session
rth_filter_applied: false

branch_path: FUTURES -> equity_index -> NQ -> ETH/full_retained_session -> 1m parent execution + shifted 5m/15m/30m/1h/4h/1d context -> HtfTrendRegime -> ChopFilter(ER>=0.35,n40) -> MomentumResonance -> CompoundTrendRrrBreadth -> FixedRrrBracket -> child filter: TransitionRisk -> RealizedVolatilityStressGate(30m_abs_ret16_max <= 0.04174409724) -> PracticalLifecycleContinuation

## Starting Evidence

- Source/cost/coverage commit: `fd59751c Add NQ RV-stress source cost coverage packet`.
- Source packet: /tmp/ict-engine-nq-compound-rv-stress-source-cost-coverage-20260530T055944+0800/checks/source_cost_coverage_packet.json
- Materialization root: /tmp/ict-engine-nq-compound-rv-stress-feedback-materialization-20260530T043351+0800
- Strategy library: /tmp/ict-engine-nq-compound-rv-stress-feedback-materialization-20260530T043351+0800/materials/tomac_nq_compound_rv_stress_gate_strategy_library.json
- Feedback JSONL: /tmp/ict-engine-nq-compound-rv-stress-feedback-materialization-20260530T043351+0800/feedback/tomac_nq_compound_rv_stress_gate_simulated_feedback.jsonl

## Decision

status: terminalized_no_launch_blocked_by_fresh_claim
promotion_allowed: false
trade_usable: false
update_goal: false

## Terminal Readback

- 2026-05-30T06:38:16+0800: Wrapper driver plan support was added and focused tests passed, but runtime execution was not launched because compact claim audit reported a fresh active EWZ source/cost prep claim while this NQ claim was still fresh. This slice therefore terminalizes as no-launch/fail-closed.
- Blocking audit evidence: `fresh_active_claims_without_live_process=2`, `live_factor_processes=0`, blocking claims `20260530T062401+0800-codex-nq-compound-rv-stress-lifecycle-driver.claim` and `20260530T063159+0800-codex-ewz-brazil-policyflow-vwap-reclaim-prep.claim`.
- No-launch terminal metrics: `/tmp/ict-engine-nq-compound-rv-stress-lifecycle-driver-20260530T062401+0800/checks/terminal_metrics.json`.
- Repo run mirror: `support/docs/experiments/actionable-regime-confidence/runs/20260530T062401+0800-codex-nq-compound-rv-stress-lifecycle-driver-v1/`.
- Terminal result: `status=practical_lifecycle_fail_closed`, `command_results=[]`, `all_command_exits_zero=false`, `same_tree_practical_closure=null`, `promotion_allowed=false`, `trade_usable=false`, `update_goal=false`.
- Source/cost/coverage remains repaired: `session_scope=ETH/full_retained_session`, `rth_filter_applied=false`, retained NQ non-RTH rows proven, and IBKR NQ futures cost model verified from official source readbacks.
- Final audit after terminalization: `active_claims=0`, `fresh_active_claims_without_live_process=0`, `live_factor_processes=1` under `/tmp/ict-engine-tomac-h4-midnight-macd-rsi-session-cadence-aq-20260530T063700+0800`; no NQ lifecycle/runtime launch was attempted.
