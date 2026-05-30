# Fee Model Miscarriage Rescue Audit

- created_at: `2026-05-30T12:54:58+0800`
- owner: `codex`
- route: `sd/ict-engi-fact-rese-muta`
- workdoc: `/tmp/ict-engine-fee-model-miscarriage-rescue-20260530T125458+0800/workdoc.md`
- claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260530T125458+0800-codex-fee-model-miscarriage-rescue.claim`
- run_root: `/tmp/ict-engine-fee-model-miscarriage-rescue-20260530T125458+0800`
- factor_id: `fee_model_miscarriage_rescue_audit_v1`
- branch_path: `ProfitabilityGateRepair -> FuturesCostModelCorrection -> FeeModelMiscarriageRescue -> fee_model_miscarriage_rescue_audit_v1`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

## Objective

The futures fee model changed: `5bps/side` is stress telemetry, not the real futures commission model. This audit rechecks prior apparent losers so profitable futures factors are not buried by an over-harsh synthetic cost gate.

## Method

- Parse available terminal metrics, summaries, and trade rows under `/tmp`, `/private/tmp`, and repo experiment runs.
- Prefer per-trade rows with `entry_price` and raw return fields; recompute with `support/scripts/research/instrument_cost_model.py`.
- Classify aggregate-only cases as `needs_exact_replay_for_fee_rescue`, not exonerated.
- Keep `promotion_allowed=false`, `trade_usable=false`, and `update_goal=false` until downstream practical closure is rerun on a rescued candidate.

## Terminal Update

- status: `terminal_readonly_rescue_tooling_and_evidence_readback`
- public helper added: `support/scripts/research/futures_real_cost_rescue_audit.py`
- public helper test: `support/scripts/research/tests/test_futures_real_cost_rescue_audit.py`
- script inventory updated: `support/scripts/SCRIPTS.md`, `support/scripts/script_manifest.json`
- primary rehearing packet: `/tmp/ict-engine-futures-real-cost-rehearing-20260530T125637+0800/checks/terminal_metrics.json`
- strict_rescue_count: `40`
- fee_only_rescue_needs_slippage_review_count: `0`
- insufficient_evidence_count: `11844`
- fee_model_rescue_audit: `/tmp/ict-engine-fee-model-rescue-audit-20260530T125701+0800/checks/terminal_metrics.json`
- fee_model_rescue_counts: `artifacts_scanned=2500`, `fee_stress_rejected_rows_evaluated=286`, `rescued_to_next_stage_queue=0`, `still_blocked_non_cost=5`, `still_cost_blocked_or_unverified=281`
- latest claim audit: `status=needs_attention`, `active_claims=2`, `fresh_active_claims_without_live_process=2`, `live_factor_processes=0`, blockers `20260530T132455+0800-codex-futures-fee-rescue-exact-replay-queue.claim` and `20260530T132622+0800-codex-variance-ratio-serial-dependence-5m-aq.claim`
- promotion_allowed: `false`
- trade_usable: `false`
- update_goal: `false`

The audit rescued candidates back into an exact-AQ/provider/downstream replay queue only. It did not exonerate any factor into practical or live trading status, and no new replay was launched while a fresh active claim remains.
