# NQ Compound RV Stress Source Cost Coverage V1

created_at: 2026-05-30T05:59:44+0800
agent_name: codex-nq-compound-rv-stress-source-cost-coverage
factor_id: nq_compound_trend_rrr_chopfilter_rv_stress_gate_rescore_v1
parent_factor_id: nq_compound_trend_rrr_chopfilter_v1
session_scope: ETH/full_retained_session
rth_filter_applied: false

## Purpose

No-launch repair packet for the NQ compound RV-stress practical lifecycle readback. It fills two explicit blockers from the prior terminalized wrapper: retained-session coverage and product-specific NQ futures cost model.

## Evidence

- `checks/source_cost_coverage_packet.json`: retained-session coverage plus IBKR official-source NQ futures cost model.
- `checks/terminal_metrics.json`: lifecycle wrapper readback with source packet consumed.
- `summaries/terminal_summary.json`: fail-closed lifecycle decision.
- `summaries/source_packet_summary.json`: compact source packet summary.

## Decision

status: practical_lifecycle_fail_closed
retained_session_coverage.status: pass
promotion_cost_verified: true
cost_model.status: verified
promotion_allowed: false
trade_usable: false
update_goal: false

Remaining blockers are staged lifecycle command rows, exact execution-candidate/actionable state, validation counters, policy lifecycle tuple, and canonical same-tree practical closure.
