# Trend Expansion Harness Alignment - 2026-06-01

## Current goal

Optimize the ict-engine Auto-Quant handoff harness so entry work is restricted
to trend / expansion regimes. Non-trend factors should function as exclusion,
conflict, or counter-evidence signals that help identify whether the current
regime is truly trend / expansion.

## Scope

- Repo: `/Users/thrill3r/projects-ict-engine/ict-engine`
- Branch: inspect with `git branch --show-current`
- Primary runtime surface: `src/application/auto_quant/handoff.rs`
- Expected tests: focused Auto-Quant handoff contract tests, plus formatting or
  diff checks as needed.

## Constraints

- Preserve unrelated dirty work.
- Do not relax promotion, `trade_usable`, provider, or evidence gates.
- Do not make runtime code parse this plan.
- Keep generated state and claims under `/tmp`.
- Treat Auto-Quant success as candidate evidence only.

## Workdoc And Claim

- Workdoc: `/tmp/ict-engine-trend-expansion-harness-20260601T154624+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/trend-expansion-harness/20260601T154624+0800-codex-trend-expansion-harness.claim`

## Progress

- 2026-06-01T15:46:24+0800: Routed through `sd/ict-engine-maintenance-loop`,
  read repo agent contracts, and identified the Auto-Quant handoff workflow as
  the narrow runtime surface for the harness behavior.
- 2026-06-01T15:55+0800: Added machine-readable
  `agent_workflow.entry_regime_contract` to Auto-Quant handoffs. The contract
  permits entry only for `TrendExpansion` evidence with labels `expansion` or
  `trend_continuation`; all other regime labels are exclusion/counter-evidence.
- 2026-06-01T15:58+0800: Verification passed:
  `cargo fmt --check`;
  `cargo test auto_quant_handoff_output_includes_harness_agent_workflow_contract -- --nocapture`;
  `cargo run --quiet -- factor-research --symbol DEMO --data support/examples/demo/demo-15m.json --state-dir /tmp/ict-engine-trend-expansion-harness-smoke-20260601/state --output-format json`.
  CLI smoke output was written to
  `/tmp/ict-engine-trend-expansion-harness-smoke-20260601/factor_research.json`.
- 2026-06-01T16:04+0800: Extended the same contract to
  `config/factor_candidate_harness_presets.json`, the candidate resolver, and
  generated factor-expression packs. Verification passed:
  `python3 -m unittest support.scripts.research.tests.test_factor_candidate_resolver -v`;
  `python3 -m unittest support.scripts.research.tests.test_factor_candidate_pack -v`.
  Candidate resolver smoke output was written to
  `/tmp/ict-engine-trend-expansion-harness-smoke-20260601/candidate_resolver_buildable.json`.
- 2026-06-01T16:38:37+0800: Commit-prep re-verification passed:
  `cargo fmt --check`;
  `git diff --check`;
  `git diff --cached --check`;
  `cargo test auto_quant_handoff_output_includes_harness_agent_workflow_contract -- --nocapture`;
  `python3 -m unittest support.scripts.research.tests.test_factor_candidate_resolver -v`;
  `python3 -m unittest support.scripts.research.tests.test_factor_candidate_pack -v`.
  Smoke rerun output was written to
  `/tmp/ict-engine-trend-expansion-harness-smoke-20260601-rerun/factor_research.json`
  and confirmed `entry_regime_contract.primary_entry_regime=TrendExpansion`.
