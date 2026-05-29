# NQ Compound RV Stress Provenance Repair Run

This compact run packet mirrors the local provenance-repair slice for `nq_compound_trend_rrr_chopfilter_rv_stress_gate_rescore_v1`.

- run_root: `/tmp/ict-engine-nq-compound-rv-stress-provenance-repair-20260530T053539+0800`
- workdoc: `/tmp/ict-engine-nq-compound-rv-stress-provenance-repair-20260530T053539+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T053539+0800-codex-nq-compound-rv-stress-provenance-repair.claim`
- source materialization root: `/tmp/ict-engine-nq-compound-rv-stress-feedback-materialization-20260530T043351+0800`

No provider, IBKR historical, Auto-Quant, Freqtrade, paper, sim, or live command is launched by this slice.

## Terminal Readback

- terminal_metrics: `checks/terminal_metrics.json`
- terminal_summary: `summaries/terminal_summary.json`
- decision: `terminalized_provenance_repaired_lifecycle_fail_closed`
- market_data_provenance.status: `pass`
- return_sanity.status: `pass`
- retained_session_coverage.status: `missing_explicit_retained_session_coverage`
- promotion_cost_verified: `false`
- cost_model.status: `missing_explicit_verified_cost_model`
- promotion_allowed/trade_usable/update_goal: `false` / `false` / `false`
