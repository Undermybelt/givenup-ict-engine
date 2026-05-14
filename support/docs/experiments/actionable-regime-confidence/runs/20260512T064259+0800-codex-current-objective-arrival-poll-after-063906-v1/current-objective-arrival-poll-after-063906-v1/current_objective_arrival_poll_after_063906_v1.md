# Current Objective Arrival Poll After 063906 v1

Run id: `20260512T064259+0800-codex-current-objective-arrival-poll-after-063906-v1`

Gate result: `current_objective_arrival_poll_after_063906_v1=not_complete_no_new_source_control_arrival_no_downstream_promotion`

## Completion Audit

- Objective restated: every `MainRegimeV2` root needs accepted 95% calibrated evidence plus cross-market/cross-period validation before downstream promotion.
- Result: not complete.
- Accepted roots: `none`.
- Missing or blocked roots: `Bull, Bear, Sideways, Crisis`.

## Root Readback

- R6 owner/export root: exists `False`, all required files `False`.
- R3 native-subhour root: exists `True`, all required files `True`, policy accepted `false`.
- R3 physical rows: `5032903`; labels `Bear, Bull, Sideways`.
- R5 recency root: exists `False`, all required files `False`.
- New owner/control arrival candidates: `0`.

## Runtime Readback

- Provider command return code: `0`.
- Auto-Quant status: `missing_dependency`; healthy `False`; bootstrap needed `True`.
- analyze-live return code: `0`; decision `Observe only`; pre-Bayes `pass_neutralized`; execution gate `observe`.
- Pre-Bayes latest gate: `pass_neutralized`.
- Workflow: `blocked` / `user_selected_historical_data_missing`.
- Path-ranking export: rows `3`, mature rows `0`, calibrated rows `0`.

## Accounting

- Accepted Board A rows added: `0`.
- Canonical merge: `false`.
- Downstream promotion rerun: `false`.
- Strict full objective: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T064259+0800-codex-current-objective-arrival-poll-after-063906-v1/current-objective-arrival-poll-after-063906-v1/current_objective_arrival_poll_after_063906_v1.json`
- Checklist CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T064259+0800-codex-current-objective-arrival-poll-after-063906-v1/current-objective-arrival-poll-after-063906-v1/prompt_to_artifact_checklist_v1.csv`
- Candidate CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T064259+0800-codex-current-objective-arrival-poll-after-063906-v1/current-objective-arrival-poll-after-063906-v1/current_objective_arrival_poll_candidates_v1.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T064259+0800-codex-current-objective-arrival-poll-after-063906-v1/checks/current_objective_arrival_poll_after_063906_v1_assertions.out`

## Next

Continue from a real source/control unlock only: explicit source/control approval, verifier-native R6 owner-export rows with controls, source-owned R5 recency rows, or verifier-native Crisis-capable R3 MainRegimeV2 labels. Do not run canonical merge or downstream promotion from the TSIE root.
