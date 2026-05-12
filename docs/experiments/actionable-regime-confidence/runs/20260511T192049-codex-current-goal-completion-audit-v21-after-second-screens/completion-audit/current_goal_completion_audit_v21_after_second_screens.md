# Current Goal Completion Audit v21 After Second Screens

Run ID: `20260511T192049-codex-current-goal-completion-audit-v21-after-second-screens`

## Objective

Every active regime must have calibrated >=95% confidence and must retain suitable confidence on other markets/species and other cycles/timeframes.

## Decision

`current_goal_completion_audit_v21=second_screens_and_post_future_triage_confirm_full_objective_blocked`

- Strict full objective achieved: `false`; `update_goal=false`.
- Scoped active-lane `>=95%` evidence remains present, but transfer validation is still incomplete.
- Strict `1h`: fixed gate `41/156`, future protocol `45/156`.
- Post-future near-miss targets remaining: `9`; ready with existing tail `0`; minimum new source-owned sessions needed `5`.
- External source-label second screen accepted rows: `0`.
- Direct missing-species v2 ready sources: `0`.
- Live `/tmp` intake files across required roots: `0`.

## Blocking Requirements

- `other-market/source-label equivalence has suitable confidence`: Second-pass Kaggle/Hugging Face screen found no owner-approved MainRegimeV2 crosswalk or source-owned other-market rows.
- `other-cycle/timeframe validation has suitable confidence`: Future-tail protocol progressed strict 1h to 45/156, but fixed gate remains 41/156, nine near-miss targets remain, no existing tail is ready, and native sub-hour remains 0/4.
- `direct Manipulation full species coverage has matched controls`: Incremental direct species screen found zero ready positive/control sources; scoped accepted varieties do not cover missing spoofing/layering, quote stuffing, pinging, and related varieties.
- `external/local intake rows match required schemas and provenance`: No live intake files are present in the required roots, and the latest schema sweep found no exact or strong partial matches.

## Prompt-To-Artifact Checklist

- `pass_checked` `R0` `named board remains the execution contract` -> `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`: todo_sha256_before_audit=e7d58a1bc95d8cd8eb1a329024162f374a2e62afa48dc7d4b879661cf42f8987
- `scoped_pass_not_full` `R1` `active regimes have calibrated >=95 confidence` -> `docs/experiments/actionable-regime-confidence/runs/20260511T190911-codex-current-goal-completion-audit-v20-after-future-tail/completion-audit/current_goal_completion_audit_v20_after_future_tail.json`: v20 preserves scoped active-lane accepted_95 evidence; no new evidence removes it
- `fail_blocked` `R2` `other-market/source-label equivalence has suitable confidence` -> `docs/experiments/actionable-regime-confidence/runs/20260511T191623-codex-external-source-label-second-screen-v1/external-source-label-second-screen/external_source_label_second_screen_v1.json`: second_screen_decision=external_source_label_second_screen_v1=no_promotable_source_label_equivalence; accepted_rows_added=0; full_other_market_source_label_equivalence=False; prior_gate=source_label_other_market_readback_v1=partial_sources_no_full_equivalence; prior_accepted_total=0
- `fail_blocked_progress_only` `R3` `other-cycle/timeframe validation has suitable confidence` -> `docs/experiments/actionable-regime-confidence/runs/20260511T191552-codex-strict-1h-post-future-gap-triage-v1/strict-1h-post-future-gap-triage/strict_1h_post_future_gap_triage_v1.json`: fixed_1h=41/156; future_protocol_1h=45/156; remaining_near_miss_after_future=9; existing_tail_ready=0; native_subhour=0/4
- `fail_blocked` `R4` `direct Manipulation full species coverage has matched controls` -> `docs/experiments/actionable-regime-confidence/runs/20260511T191642-codex-direct-missing-species-source-screen-v2/direct-missing-species-screen/direct_missing_species_source_screen_v2.json`: direct_v2_gate=direct_missing_species_source_screen_v2=no_ready_positive_control_source; candidates_screened=7; ready_sources=0; direct_cov_gate=direct_manipulation_coverage_readback_v2=scoped_varieties_present_full_species_blocked; remaining_unaccepted=6
- `fail_blocked` `R5` `external/local intake rows match required schemas and provenance` -> `docs/experiments/actionable-regime-confidence/runs/20260511T185420-codex-local-intake-schema-sweep-v1/local-intake-schema-sweep/local_intake_schema_sweep_v1.json`: live_tmp_intake_files=0; exact_schema_matches=0; strong_partial_schema_matches=0
- `pass_guardrail` `R6` `future-tail rows are not counted as fixed 2024/2025 strict gate rows` -> `docs/experiments/actionable-regime-confidence/runs/20260511T190440-codex-strict-1h-future-tail-gate-rerun-v1/future-tail-gate-rerun/strict_1h_future_tail_gate_rerun_v1.json`: future_rows_added=4; fixed_gate_rows_added=0; scope=future_tail_chronological_protocol_only
- `pass_guardrail` `R7` `proxy/generated/OHLCV-only labels remain rejected` -> `docs/experiments/actionable-regime-confidence/runs/20260511T191623-codex-external-source-label-second-screen-v1/external-source-label-second-screen/external_source_label_second_screen_v1.json`: HMM/generated BTCUSD labels, raw OHLCV/external-factor panels, and structural sidecars were blocked rather than promoted
- `pass_guardrail` `R8` `do not call update_goal unless strict full objective is achieved` -> `docs/experiments/actionable-regime-confidence/runs/20260511T190911-codex-current-goal-completion-audit-v20-after-future-tail/completion-audit/current_goal_completion_audit_v20_after_future_tail.json`: v20_update_goal=False; new_screens_update_goal=False,False,False

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T192049-codex-current-goal-completion-audit-v21-after-second-screens/completion-audit/current_goal_completion_audit_v21_after_second_screens.json`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T192049-codex-current-goal-completion-audit-v21-after-second-screens/completion-audit/current_goal_completion_audit_v21_checklist.csv`
- Unmet requirements CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T192049-codex-current-goal-completion-audit-v21-after-second-screens/completion-audit/current_goal_completion_audit_v21_unmet_requirements.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T192049-codex-current-goal-completion-audit-v21-after-second-screens/checks/current_goal_completion_audit_v21_after_second_screens_assertions.out`
