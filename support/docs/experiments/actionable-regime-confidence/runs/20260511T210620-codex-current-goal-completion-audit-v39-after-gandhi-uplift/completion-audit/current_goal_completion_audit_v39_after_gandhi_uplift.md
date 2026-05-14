# Current Goal Completion Audit v39 After Gandhi Uplift

Decision: `current_goal_completion_audit_v39=gandhi_rows_expanded_r6_still_calibration_blocked`.

Result:
- Ready intake roots by file presence: `1/4`; ready roots: `direct_manipulation_row_intake`.
- R6 rows after Gandhi uplift: positives `4`, matched negatives `4`.
- R6 Wilson95 min LCB: `0.5101091635454027`; chronological ok: `true`; heldout symbol/venue ok: `true`.
- Broad normal sample: `false`; species coverage ok: `false`.
- Accepted rows added since v38: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

Checklist:

| ID | Status | Gap |
|---|---|---|
| `R0` | `pass_checked` | `` |
| `R1` | `fail_not_full` | `Full per-regime >=95 confidence across the required market/species/cycle axes is not complete.` |
| `R2` | `fail_blocked` | `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json` |
| `R3` | `fail_blocked` | `native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json` |
| `R4` | `fail_blocked` | `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json` |
| `R5` | `fail_blocked` | `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json` |
| `R6` | `partial_expanded_schema_ready_calibration_blocked` | `Support remains below Wilson95 >=0.95, controls are same-report seeds rather than broad normal controls, and direct species coverage is incomplete.` |
| `R7` | `pass_guardrail` | `` |
| `R8` | `fail_blocked` | `Strict full objective is not achieved; update_goal remains false.` |

Next:
Continue source-owned extraction for R6 until support, broad controls, direct species, chronological, and heldout gates all pass; in parallel populate the existing R2/R3/R4/R5 fail-closed intake roots before rerunning completion audit.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T210620-codex-current-goal-completion-audit-v39-after-gandhi-uplift/completion-audit/current_goal_completion_audit_v39_after_gandhi_uplift.json`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T210620-codex-current-goal-completion-audit-v39-after-gandhi-uplift/completion-audit/current_goal_completion_audit_v39_checklist.csv`
- Unmet requirements CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T210620-codex-current-goal-completion-audit-v39-after-gandhi-uplift/completion-audit/current_goal_completion_audit_v39_unmet_requirements.csv`
- Intake-root CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T210620-codex-current-goal-completion-audit-v39-after-gandhi-uplift/completion-audit/current_goal_completion_audit_v39_intake_roots.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T210620-codex-current-goal-completion-audit-v39-after-gandhi-uplift/checks/current_goal_completion_audit_v39_after_gandhi_uplift_assertions.out`
