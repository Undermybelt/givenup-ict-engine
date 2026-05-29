# NQ Compound RV Stress Provenance Repair

created_at: 2026-05-30T05:35:39+0800
agent_name: codex-nq-compound-rv-stress-provenance-repair
owner: codex
repo: /Users/thrill3r/projects-ict-engine/ict-engine
branch: main
run_root: /tmp/ict-engine-nq-compound-rv-stress-provenance-repair-20260530T053539+0800
claim: /tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T053539+0800-codex-nq-compound-rv-stress-provenance-repair.claim
compact_root: support/docs/experiments/actionable-regime-confidence/runs/20260530T053539+0800-codex-nq-compound-rv-stress-provenance-repair-v1

## Scope

Repair the NQ compound RV-stress child-gate practical lifecycle readback so market-data provenance and return sanity are explicit, source-derived, and fail-closed. This slice does not run provider, IBKR historical, Auto-Quant, Freqtrade, paper, sim, or live commands.

## Factor

factor_id: nq_compound_trend_rrr_chopfilter_rv_stress_gate_rescore_v1
parent_factor_id: nq_compound_trend_rrr_chopfilter_v1
session_scope: ETH/full_retained_session
rth_filter_applied: false

branch_path: FUTURES -> equity_index -> NQ -> ETH/full_retained_session -> 1m parent execution + shifted 5m/15m/30m/1h/4h/1d context -> HtfTrendRegime -> ChopFilter(ER>=0.35,n40) -> MomentumResonance -> CompoundTrendRrrBreadth -> FixedRrrBracket -> child filter: TransitionRisk -> RealizedVolatilityStressGate(30m_abs_ret16_max <= 0.04174409724) -> nq_compound_trend_rrr_chopfilter_rv_stress_gate_rescore_v1

## Evidence Inputs

- Materialization root: /tmp/ict-engine-nq-compound-rv-stress-feedback-materialization-20260530T043351+0800
- Materialization metrics: /tmp/ict-engine-nq-compound-rv-stress-feedback-materialization-20260530T043351+0800/checks/terminal_metrics.json
- Child rescore root: /tmp/ict-engine-nq-compound-rv-stress-gate-rescore-20260530T042109+0800
- Parent root: /tmp/ict-engine-tomac-nq-compound-trend-rrr-chopfilter-cont-20260529T213117+0800

## Non Goals

- Do not claim practical readiness from local simulated feedback, cross-engine evidence, or provenance readback alone.
- Do not hand-write same_tree_practical_closure packets.
- Do not relax command stage, session scope, cost model, validation, policy lifecycle, or execution-tree gates.
- Do not edit Board/current/coverage docs or use them as active state.

## Progress

- 2026-05-30T05:31:59+0800: Compact claim audit returned pass with active_claims=0, live_factor_processes=0, promotion_allowed_true=0, trade_usable_true=0.
- 2026-05-30T05:35:39+0800: Created this repo tracking doc, /tmp workdoc, and /tmp claim before substantive wrapper edits.
- 2026-05-30T05:36:xx+0800: Baseline lifecycle unit test is currently RED: the full-chain fixture expects a same_tree_practical_closure packet, but the canonical helper now also requires explicit ETH/full retained session coverage and verified promotion cost model fields.
- 2026-05-30T05:48:02+0800: Updated the child-gate practical lifecycle wrapper to inherit explicit market-data provenance and return sanity from the child rescore metrics when materialization metrics only point at the child rescore root. The wrapper now also emits session scope, retained-session coverage, and cost-model fields explicitly instead of leaving those gates implicit.
- 2026-05-30T05:48:02+0800: Real readback exited `2` fail-closed at `/tmp/ict-engine-nq-compound-rv-stress-provenance-repair-20260530T053539+0800`: `market_data_provenance.status=pass`, `return_sanity.status=pass`, `session_scope=ETH/full_retained_session`, `rth_filter_applied=false`, `retained_session_coverage.status=missing_explicit_retained_session_coverage`, `promotion_cost_verified=false`, `cost_model.status=missing_explicit_verified_cost_model`, `command_results=[]`, and all practical flags false.

## Current Decision

status: terminalized_provenance_repaired_lifecycle_fail_closed
promotion_allowed: false
trade_usable: false
update_goal: false
