# Current Goal Completion Audit v22 After Intake And Subhour Readbacks

Run ID: `20260511T192655-codex-current-goal-completion-audit-v22-after-intake-and-subhour-readbacks`

## Objective

Every active regime must have calibrated >=95% confidence and must retain suitable confidence on other markets/species and other cycles/timeframes.

## Decision

`current_goal_completion_audit_v22=intake_and_subhour_readbacks_confirm_full_objective_blocked`

- Strict full objective achieved: `false`; `update_goal=false`.
- Strict `1h`: fixed `41/156`, future protocol `45/156`.
- Strict `1h` intake verifier: missing files `2`, live files `0`, contract target rows `4`.
- Native sub-hour: eligible source-label rows `0`, quarantined projection rows `264`.
- Accepted rows added by this audit: `0`; new confidence gate: `false`.

## Blocking Requirements

- `strict 1h remaining rows have source-owned intake files`: The strict 1h next-source contract is executable, but the live source-label equivalence rows and provenance files are still absent.
- `XOM/Sideways recency tail can repair the next strict 1h target`: Live Kaggle source still ends at 2026-01-30 and supplies no XOM/Sideways tail repair rows.
- `native sub-hour validation has source-owned native sub-hour labels`: Sub-hour-looking rows were projections from day/month windows, not source-owned native sub-hour labels.
- `other-market/source-label equivalence has suitable confidence`: Second-pass external screen accepted zero owner-approved MainRegimeV2 equivalence rows.
- `direct Manipulation full species coverage has matched controls`: Direct missing-species v2 found zero ready positive/control sources.

## Prompt-To-Artifact Checklist

- `pass_checked` `R0` `named board remains the execution contract` -> `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`: todo_sha256_before_audit=0eb6413068a91426297973904bc12d6a5e7da40ad497f5691127767ed74cdb50
- `scoped_pass_not_full` `R1` `scoped active regimes retain calibrated >=95 confidence` -> `docs/experiments/actionable-regime-confidence/runs/20260511T192049-codex-current-goal-completion-audit-v21-after-second-screens/completion-audit/current_goal_completion_audit_v21_after_second_screens.json`: v21_gate=current_goal_completion_audit_v21=second_screens_and_post_future_triage_confirm_full_objective_blocked; scoped_95_present=true
- `fail_blocked` `R2` `strict 1h remaining rows have source-owned intake files` -> `docs/experiments/actionable-regime-confidence/runs/20260511T192432-codex-strict-1h-source-intake-verifier-readback-v1/source-intake-verifier-readback/strict_1h_source_intake_verifier_readback_v1.json`: verifier_status=blocked; reason=missing_required_files; missing_files=2; live_intake_file_count=0; contract_targets=4
- `fail_blocked` `R3` `XOM/Sideways recency tail can repair the next strict 1h target` -> `docs/experiments/actionable-regime-confidence/runs/20260511T192218-codex-stock-regime-kaggle-live-recency-check-v1/kaggle-live-recency/stock_regime_kaggle_live_recency_check_v1.json`: gate=stock_regime_kaggle_live_recency_check_v1=upstream_current_file_no_xom_sideways_tail_repair; xom_sideways_after_2026_01_30=None; xom_sideways_tail=None; source_end=None
- `fail_blocked` `R4` `native sub-hour validation has source-owned native sub-hour labels` -> `docs/experiments/actionable-regime-confidence/runs/20260511T192248-codex-native-subhour-projection-quarantine-v1/native-subhour-projection-quarantine/native_subhour_projection_quarantine_v1.json`: gate=native_subhour_projection_quarantine_v1=projected_subhour_rows_not_native_source_labels; subhour_looking_rows=264; native_subhour_eligible_rows=0; quarantined_rows=264
- `fail_blocked` `R5` `other-market/source-label equivalence has suitable confidence` -> `docs/experiments/actionable-regime-confidence/runs/20260511T191623-codex-external-source-label-second-screen-v1/external-source-label-second-screen/external_source_label_second_screen_v1.json`: external_decision=external_source_label_second_screen_v1=no_promotable_source_label_equivalence; accepted_rows_added=0; full_equivalence=False
- `fail_blocked` `R6` `direct Manipulation full species coverage has matched controls` -> `docs/experiments/actionable-regime-confidence/runs/20260511T191642-codex-direct-missing-species-source-screen-v2/direct-missing-species-screen/direct_missing_species_source_screen_v2.json`: direct_gate=direct_missing_species_source_screen_v2=no_ready_positive_control_source; ready_sources=0; candidates_screened=7
- `pass_guardrail` `R7` `future-tail accepted rows are scoped and not fixed-gate acceptance` -> `docs/experiments/actionable-regime-confidence/runs/20260511T190440-codex-strict-1h-future-tail-gate-rerun-v1/future-tail-gate-rerun/strict_1h_future_tail_gate_rerun_v1.json`: future_rows=4; fixed_rows_added=0; scope=future_tail_chronological_protocol_only
- `pass_guardrail` `R8` `do not call update_goal until strict full objective is achieved` -> `docs/experiments/actionable-regime-confidence/runs/20260511T192049-codex-current-goal-completion-audit-v21-after-second-screens/completion-audit/current_goal_completion_audit_v21_after_second_screens.json`: v21_update_goal=False; verifier_update_goal=False; subhour_update_goal=None

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T192655-codex-current-goal-completion-audit-v22-after-intake-and-subhour-readbacks/completion-audit/current_goal_completion_audit_v22_after_intake_and_subhour_readbacks.json`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T192655-codex-current-goal-completion-audit-v22-after-intake-and-subhour-readbacks/completion-audit/current_goal_completion_audit_v22_checklist.csv`
- Unmet requirements CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T192655-codex-current-goal-completion-audit-v22-after-intake-and-subhour-readbacks/completion-audit/current_goal_completion_audit_v22_unmet_requirements.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T192655-codex-current-goal-completion-audit-v22-after-intake-and-subhour-readbacks/checks/current_goal_completion_audit_v22_after_intake_and_subhour_readbacks_assertions.out`
