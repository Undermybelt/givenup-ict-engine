# Source/Control Selected-History Poll After 082215 v1 Correction

Run id: `20260512T082523+0800-codex-source-control-selected-history-poll-after-082215-v1`

Correction gate: `source_control_selected_history_poll_after_082215_v1_correction=parser_false_positive_no_merge_no_rerun`

## Correction

The original v1 readback incorrectly reported `approval_canonical_merge_allowed=true` and `approval_downstream_rerun_allowed=true` because the parser matched option text in the approval decision package. The approval package assertions are authoritative for this readback: `canonical_merge_allowed_now=false`, `downstream_rerun_allowed_now=false`, `approval_present=false`, and gate `r6_oystacher_approval_decision_package_v1=decision_package_ready_no_approval_no_merge`.

## Corrected Decision

No new required source/control root or selected-history unlock arrived after `082215`. R6 owner/export root present false, R5 recency root present false, and R3 native-subhour root remains non-unlocking because `MainRegimeV2` hits are `0` and matched-control support is insufficient. Explicit user-selected history remains false.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; approval canonical merge allowed false; approval downstream rerun allowed false; canonical merge false; selected-data AutoQuant promotion false; downstream promotion rerun false; strict full objective false; trade usable false; `promotion_allowed=false`; `update_goal=false`.

## Artifacts

- Corrected JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T082523+0800-codex-source-control-selected-history-poll-after-082215-v1/source-control-selected-history-poll-after-082215-v1/source_control_selected_history_poll_after_082215_v1_correction.json`
- Corrected assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T082523+0800-codex-source-control-selected-history-poll-after-082215-v1/checks/source_control_selected_history_poll_after_082215_v1_correction_assertions.out`
