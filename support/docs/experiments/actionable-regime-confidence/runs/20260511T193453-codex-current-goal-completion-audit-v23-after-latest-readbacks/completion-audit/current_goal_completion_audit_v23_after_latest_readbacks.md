# Current Goal Completion Audit v23 After Latest Readbacks

Run ID: `20260511T193453-codex-current-goal-completion-audit-v23-after-latest-readbacks`

## Objective

Every active regime must have calibrated >=95% confidence and must retain suitable confidence on other markets/species and other cycles/timeframes.

## Success Criteria

- all active regimes have calibrated >=95 confidence
- validation transfers to other markets/species with source-owned or owner-approved labels
- validation transfers to other cycles/timeframes, including native sub-hour where claimed
- strict 1h remaining rows are supported by new source-owned rows, not duplicate counted support
- direct Manipulation has row-level positives, matched negatives, and provenance for missing species

## Decision

`current_goal_completion_audit_v23=latest_readbacks_confirm_full_objective_blocked`

- Strict full objective achieved: `false`; `update_goal=false`.
- Strict `1h`: fixed `41/156`, future protocol `45/156`.
- Strict contract targets: `4`; materializable from existing panel `0`; extra source rows `0`.
- Direct Manipulation intake missing files: `3`; direct species coverage closed `false`.
- Native sub-hour source overlap closed: `false`.
- Accepted rows added by this audit: `0`; new confidence gate: `false`.

## Blocking Requirements

- `strict exact 1h market/timeframe coverage is complete`: Strict exact 1h coverage remains partial; future-tail support is scoped and does not close the fixed gate.
- `strict 1h remaining rows have new source-owned intake rows and provenance`: The live strict intake files are absent, and the existing source panel has zero extra rows beyond already-counted gate support.
- `source recency tail can repair XOM/Sideways and next strict 1h targets`: The current stock-regime source still supplies no new XOM/Sideways tail rows and no extra source-owned sessions for the contract targets.
- `native sub-hour validation has source-owned native sub-hour labels`: Projected sub-hour rows remain quarantined, and targeted public searches found no ready source-owned native sub-hour labels.
- `other-market/source-label equivalence has suitable confidence`: Second-pass external screening still accepted zero owner-approved MainRegimeV2 equivalence rows.
- `direct Manipulation full species coverage has matched positives, negatives, and provenance`: Direct missing-species screening found no ready positive/control sources, and the direct Manipulation row-intake files are absent.

## Prompt-To-Artifact Checklist

- `pass_checked` `R0` `named board remains the execution contract` -> `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`: todo_sha256_before_audit=a54f7176a885bfbc688c348e34822b6e251b1cfff63a7a5b71f72a6afa904977
- `scoped_pass_not_full` `R1` `each active regime has scoped calibrated >=95 confidence` -> `docs/experiments/actionable-regime-confidence/runs/20260511T192655-codex-current-goal-completion-audit-v22-after-intake-and-subhour-readbacks/completion-audit/current_goal_completion_audit_v22_after_intake_and_subhour_readbacks.json`: v22_R1_status=scoped_pass_not_full; v22_gate=current_goal_completion_audit_v22=intake_and_subhour_readbacks_confirm_full_objective_blocked
- `fail_blocked` `R2` `strict exact 1h market/timeframe coverage is complete` -> `docs/experiments/actionable-regime-confidence/runs/20260511T192655-codex-current-goal-completion-audit-v22-after-intake-and-subhour-readbacks/completion-audit/current_goal_completion_audit_v22_after_intake_and_subhour_readbacks.json`: fixed_gate=41/156; future_protocol=45/156
- `fail_blocked` `R3` `strict 1h remaining rows have new source-owned intake rows and provenance` -> `docs/experiments/actionable-regime-confidence/runs/20260511T192900-codex-strict-1h-contract-panel-exhaustion-v1/strict-1h-contract-panel-exhaustion/strict_1h_contract_panel_exhaustion_v1.json`: source_intake_missing_files=2; live_intake_files=0; contract_targets=4; targets_materializable_from_existing_panel=0; extra_source_rows=0
- `fail_blocked` `R4` `source recency tail can repair XOM/Sideways and next strict 1h targets` -> `docs/experiments/actionable-regime-confidence/runs/20260511T192218-codex-stock-regime-kaggle-live-recency-check-v1/kaggle-live-recency/stock_regime_kaggle_live_recency_check_v1.json`: recency_gate=stock_regime_kaggle_live_recency_check_v1=upstream_current_file_no_xom_sideways_tail_repair; xom_panel_extra=0; xom_jan2026_tail=0
- `fail_blocked` `R5` `native sub-hour validation has source-owned native sub-hour labels` -> `docs/experiments/actionable-regime-confidence/runs/20260511T192750-codex-native-subhour-external-source-screen-v1/native-subhour-external-source-screen/native_subhour_external_source_screen_v1.json`: projection_quarantine=native_subhour_projection_quarantine_v1=projected_subhour_rows_not_native_source_labels; native_external=native_subhour_external_source_screen_v1=no_ready_native_subhour_source_labels; native_candidates=3; accepted_rows=0
- `fail_blocked` `R6` `other-market/source-label equivalence has suitable confidence` -> `docs/experiments/actionable-regime-confidence/runs/20260511T191623-codex-external-source-label-second-screen-v1/external-source-label-second-screen/external_source_label_second_screen_v1.json`: external_decision=external_source_label_second_screen_v1=no_promotable_source_label_equivalence; accepted_rows_added=0; full_equivalence=False
- `fail_blocked` `R7` `direct Manipulation full species coverage has matched positives, negatives, and provenance` -> `docs/experiments/actionable-regime-confidence/runs/20260511T193301-codex-direct-manipulation-intake-verifier-readback-v1/direct-manipulation-intake-verifier-readback/direct_manipulation_intake_verifier_readback_v1.json`: direct_screen_gate=direct_missing_species_source_screen_v2=no_ready_positive_control_source; ready_sources=0; direct_intake_decision=direct_manipulation_intake_verifier_readback_v1=blocked_missing_direct_intake_files; missing_direct_files=3; intake_root_exists=False
- `pass_guardrail` `R8` `proxy/generated labels and duplicate rows remain fail-closed` -> `docs/experiments/actionable-regime-confidence/runs/20260511T192750-codex-native-subhour-external-source-screen-v1/native-subhour-external-source-screen/native_subhour_external_source_screen_v1.json`: native_hmm_candidate_rejected=native_subhour_external_source_screen_v1=no_ready_native_subhour_source_labels; strict_duplicate_panel_rejected=strict_1h_contract_panel_exhaustion_v1=existing_source_panel_has_zero_extra_contract_rows; fixed_rows_added_by_future_tail=0
- `pass_guardrail` `R9` `do not call update_goal until strict full objective is achieved` -> `docs/experiments/actionable-regime-confidence/runs/20260511T193301-codex-direct-manipulation-intake-verifier-readback-v1/direct-manipulation-intake-verifier-readback/direct_manipulation_intake_verifier_readback_v1.json`: v22_update_goal=False; strict_exhaustion_update_goal=False; direct_verifier_update_goal=False

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T193453-codex-current-goal-completion-audit-v23-after-latest-readbacks/completion-audit/current_goal_completion_audit_v23_after_latest_readbacks.json`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T193453-codex-current-goal-completion-audit-v23-after-latest-readbacks/completion-audit/current_goal_completion_audit_v23_checklist.csv`
- Unmet requirements CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T193453-codex-current-goal-completion-audit-v23-after-latest-readbacks/completion-audit/current_goal_completion_audit_v23_unmet_requirements.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T193453-codex-current-goal-completion-audit-v23-after-latest-readbacks/checks/current_goal_completion_audit_v23_after_latest_readbacks_assertions.out`
