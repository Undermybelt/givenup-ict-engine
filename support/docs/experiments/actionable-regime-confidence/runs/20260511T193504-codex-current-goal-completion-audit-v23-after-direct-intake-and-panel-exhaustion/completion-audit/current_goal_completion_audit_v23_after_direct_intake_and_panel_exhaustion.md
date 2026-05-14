# Current Goal Completion Audit v23 After Direct Intake And Panel Exhaustion

Run ID: `20260511T193504+0800-codex-current-goal-completion-audit-v23-after-direct-intake-and-panel-exhaustion`

## Objective

Every regime must have calibrated >=95% confidence, and the confidence must remain suitable on other markets and other cycles/timeframes.

## Decision

`current_goal_completion_audit_v23=direct_intake_and_panel_exhaustion_confirm_full_objective_blocked`

- Strict full objective achieved: `false`; `update_goal=false`.
- Blocking requirements: `7`.
- Strict `1h`: fixed `41/156`, future protocol `45/156`.
- Strict source intake missing files: `2`; existing panel extra rows: `0`.
- Native sub-hour eligible source rows: `0`.
- Direct Manipulation intake missing files: `3`.
- Accepted rows added by this audit: `0`; new confidence gate: `false`.

## Blocking Requirements

- `R2` Other-cycle/timeframe validation has suitable confidence. -> Fixed strict 1h remains 41/156, future protocol remains 45/156, and native sub-hour remains 0/4.
- `R3` Strict 1h next-source intake has source-owned rows and provenance. -> The source-label equivalence intake files are absent.
- `R4` Existing source panel can supply the strict 1h contract gaps without duplicate evidence. -> The current source panel has zero extra rows beyond already-counted strict-gate support.
- `R5` XOM/Sideways has recency-tail repair rows for the next strict 1h gap. -> The live source file has no XOM/Sideways Jan-2026 tail or post-2026-01-30 rows.
- `R6` Native sub-hour source labels exist for cross-timeframe validation. -> Projection rows were quarantined and targeted external search found zero ready native sub-hour source labels.
- `R7` Other-market/source-label equivalence has suitable confidence. -> No owner-approved MainRegimeV2 equivalence rows were promoted.
- `R8` Direct Manipulation has full species coverage with real positives and matched controls. -> Direct species source screen found zero ready sources, and direct intake files are absent.

## Prompt-To-Artifact Checklist

- `pass_checked` `R0` Use the named Board A markdown as the execution contract. | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` | board_sha256_before_audit=a54f7176a885bfbc688c348e34822b6e251b1cfff63a7a5b71f72a6afa904977
- `scoped_pass_not_full` `R1` Every active regime has calibrated >=95% confidence. | `docs/experiments/actionable-regime-confidence/runs/20260511T192655-codex-current-goal-completion-audit-v22-after-intake-and-subhour-readbacks/completion-audit/current_goal_completion_audit_v22_after_intake_and_subhour_readbacks.json` | v22_gate=current_goal_completion_audit_v22=intake_and_subhour_readbacks_confirm_full_objective_blocked; scoped_active_lane_95_present=true
- `fail_blocked` `R2` Other-cycle/timeframe validation has suitable confidence. | `docs/experiments/actionable-regime-confidence/runs/20260511T185126-codex-timeframe-cycle-coverage-readback-v1/timeframe-cycle-readback/timeframe_cycle_coverage_readback_v1.json` | strict_1h_fixed=41/156; future_protocol=45/156; native_subhour=0/4
- `fail_blocked` `R3` Strict 1h next-source intake has source-owned rows and provenance. | `docs/experiments/actionable-regime-confidence/runs/20260511T192432-codex-strict-1h-source-intake-verifier-readback-v1/source-intake-verifier-readback/strict_1h_source_intake_verifier_readback_v1.json` | status=blocked; reason=missing_required_files; missing_files=2; live_files=0
- `fail_blocked` `R4` Existing source panel can supply the strict 1h contract gaps without duplicate evidence. | `docs/experiments/actionable-regime-confidence/runs/20260511T192900-codex-strict-1h-contract-panel-exhaustion-v1/strict-1h-contract-panel-exhaustion/strict_1h_contract_panel_exhaustion_v1.json` | targets_materializable=0; extra_rows=0; intake_files_created=False
- `fail_blocked` `R5` XOM/Sideways has recency-tail repair rows for the next strict 1h gap. | `docs/experiments/actionable-regime-confidence/runs/20260511T192218-codex-stock-regime-kaggle-live-recency-check-v1/kaggle-live-recency/stock_regime_kaggle_live_recency_check_v1.json` | gate=stock_regime_kaggle_live_recency_check_v1=upstream_current_file_no_xom_sideways_tail_repair; xom_sideways_2025=68; xom_sideways_tail=0; xom_sideways_after_2026_01_30=0
- `fail_blocked` `R6` Native sub-hour source labels exist for cross-timeframe validation. | `docs/experiments/actionable-regime-confidence/runs/20260511T192750-codex-native-subhour-external-source-screen-v1/native-subhour-external-source-screen/native_subhour_external_source_screen_v1.json` | quarantine_gate=native_subhour_projection_quarantine_v1=projected_subhour_rows_not_native_source_labels; eligible_rows=0; external_gate=native_subhour_external_source_screen_v1=no_ready_native_subhour_source_labels; ready_native_rows=0
- `fail_blocked` `R7` Other-market/source-label equivalence has suitable confidence. | `docs/experiments/actionable-regime-confidence/runs/20260511T191623-codex-external-source-label-second-screen-v1/external-source-label-second-screen/external_source_label_second_screen_v1.json` | gate=external_source_label_second_screen_v1=no_promotable_source_label_equivalence; accepted_rows_added=0; full_equivalence=False
- `fail_blocked` `R8` Direct Manipulation has full species coverage with real positives and matched controls. | `docs/experiments/actionable-regime-confidence/runs/20260511T193301-codex-direct-manipulation-intake-verifier-readback-v1/direct-manipulation-intake-verifier-readback/direct_manipulation_intake_verifier_readback_v1.json` | species_gate=direct_missing_species_source_screen_v2=no_ready_positive_control_source; ready_sources=0; intake_decision=direct_manipulation_intake_verifier_readback_v1=blocked_missing_direct_intake_files; direct_missing_files=3
- `pass_guardrail` `R9` Do not promote proxy/generated labels or duplicated rows. | `docs/experiments/actionable-regime-confidence/runs/20260511T192900-codex-strict-1h-contract-panel-exhaustion-v1/strict-1h-contract-panel-exhaustion/strict_1h_contract_panel_exhaustion_v1.json` | panel_exhaustion blocks duplicate rows; native subhour quarantine blocks projected rows; HMM-generated labels remain rejected
- `pass_guardrail` `R10` Do not mark the active goal complete until every requirement is covered. | `docs/experiments/actionable-regime-confidence/runs/20260511T192655-codex-current-goal-completion-audit-v22-after-intake-and-subhour-readbacks/completion-audit/current_goal_completion_audit_v22_after_intake_and_subhour_readbacks.json` | v22_update_goal=False; strict_intake_update_goal=False; direct_intake_update_goal=False

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T193504-codex-current-goal-completion-audit-v23-after-direct-intake-and-panel-exhaustion/completion-audit/current_goal_completion_audit_v23_after_direct_intake_and_panel_exhaustion.json`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T193504-codex-current-goal-completion-audit-v23-after-direct-intake-and-panel-exhaustion/completion-audit/current_goal_completion_audit_v23_checklist.csv`
- Unmet requirements CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T193504-codex-current-goal-completion-audit-v23-after-direct-intake-and-panel-exhaustion/completion-audit/current_goal_completion_audit_v23_unmet_requirements.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T193504-codex-current-goal-completion-audit-v23-after-direct-intake-and-panel-exhaustion/checks/current_goal_completion_audit_v23_after_direct_intake_and_panel_exhaustion_assertions.out`
