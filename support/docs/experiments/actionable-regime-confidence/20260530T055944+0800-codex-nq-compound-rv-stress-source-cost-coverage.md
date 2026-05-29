# NQ Compound RV Stress Source Cost Coverage Packet

created_at: 2026-05-30T05:59:44+0800
agent_name: codex-nq-compound-rv-stress-source-cost-coverage
owner: codex
repo: /Users/thrill3r/projects-ict-engine/ict-engine
branch: main
run_root: /tmp/ict-engine-nq-compound-rv-stress-source-cost-coverage-20260530T055944+0800
claim: /tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T055944+0800-codex-nq-compound-rv-stress-source-cost-coverage.claim

## Scope

Build a no-launch source packet for the NQ compound RV-stress child practical lifecycle readback. This fills the previously explicit blockers for retained-session coverage and product-specific NQ futures cost model only; it does not run provider, IBKR historical, Auto-Quant, Freqtrade, paper, sim, live, or lifecycle commands.

## Factor

factor_id: nq_compound_trend_rrr_chopfilter_rv_stress_gate_rescore_v1
parent_factor_id: nq_compound_trend_rrr_chopfilter_v1
session_scope: ETH/full_retained_session
rth_filter_applied: false

branch_path: FUTURES -> equity_index -> NQ -> ETH/full_retained_session -> 1m parent execution + shifted 5m/15m/30m/1h/4h/1d context -> HtfTrendRegime -> ChopFilter(ER>=0.35,n40) -> MomentumResonance -> CompoundTrendRrrBreadth -> FixedRrrBracket -> child filter: TransitionRisk -> RealizedVolatilityStressGate(30m_abs_ret16_max <= 0.04174409724) -> source/cost/coverage packet -> practical lifecycle fail-closed readback

## Collision Guard

Current compact audit at 2026-05-30T05:58:15+0800 reports `status=needs_attention` because the MGC Kalman VWAP quality-hold-filter full-ladder claim is fresh and active. This slice is therefore restricted to file/source packet work and wrapper tests.

## Evidence Readbacks

- Retained session: local NQ 1m feather has `row_count=1770523`, `rth_rows=494940`, `non_rth_rows=1275583`, with sample non-RTH NY rows from `2021-01-03 18:00:00-05:00` onward.
- IBKR futures commission page: HTTP 200, low-volume US futures row `USD 0.85/contract`.
- IBKR CME fee page: HTTP 200, E-mini Equity Futures row includes `NQ` with exchange fee recovery `1.38`, and regulatory fee recovery `0.02`.
- IBKR NQ product search: HTTP 200, `E-mini NASDAQ 100 - CME`, `symbol=NQ`, `FUT` months present.
- IBKR NQ contract-details/secdef: HTTP 200, `assetClass=FUT`, `ticker=NQ`, `listingExchange=CME`, `currency=USD`, `multiplier=20.0`, tick increment `0.25`, implying `tick_value_usd=5.0`.

## Decision

status: terminalized_no_launch_source_cost_coverage_fail_closed
promotion_allowed: false
trade_usable: false
update_goal: false

## Artifacts

- Source packet: /tmp/ict-engine-nq-compound-rv-stress-source-cost-coverage-20260530T055944+0800/checks/source_cost_coverage_packet.json
- Lifecycle readback: /tmp/ict-engine-nq-compound-rv-stress-source-cost-coverage-20260530T055944+0800/lifecycle_readback/checks/terminal_metrics.json
- Repo mirror: support/docs/experiments/actionable-regime-confidence/runs/20260530T055944+0800-codex-nq-compound-rv-stress-source-cost-coverage-v1

Remaining practical blockers after this packet still include missing staged lifecycle command rows, exact execution candidate/actionable state, validation counters, policy lifecycle tuple, and same-tree practical closure.
