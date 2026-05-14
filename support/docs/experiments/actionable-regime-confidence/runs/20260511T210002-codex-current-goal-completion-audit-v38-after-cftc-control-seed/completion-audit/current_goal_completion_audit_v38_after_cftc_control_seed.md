# Current Goal Completion Audit v38 After CFTC Control Seed

Decision: `current_goal_completion_audit_v38=cftc_control_seed_schema_ready_unscored_strict_objective_blocked`.

Result:
- Direct R6 intake root ready by file presence: `1/4`; ready roots: `direct_manipulation_row_intake`.
- Direct verifier schema-ready/unscored: `true`.
- Accepted rows added since v37: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

Checklist:

| ID | Status | Gap |
|---|---|---|
| `R0` | `pass_checked` | `` |
| `R1` | `pass_scoped_not_full` | `Strict full-market/full-cycle/full-species evidence is still incomplete.` |
| `R2` | `fail_blocked` | `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json` |
| `R3` | `fail_blocked` | `native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json` |
| `R4` | `fail_blocked` | `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json` |
| `R5` | `fail_blocked` | `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json` |
| `R6` | `partial_schema_ready_unscored` | `Only CFTC spoofing/layering seed rows exist; no Wilson95 calibration, heldout-symbol/venue validation, or broader direct species closure.` |
| `R7` | `pass_guardrail` | `` |
| `R8` | `fail_blocked` | `Strict full objective is not achieved; update_goal remains false.` |

Next:
For R6, collect more source-owned positive and same-schema normal-control rows across venues/symbols/periods and run chronological plus heldout-symbol/venue Wilson95 calibration; for R2/R3/R4/R5, populate required /tmp intake roots with source-owned/provenance files and rerun verifiers.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T210002-codex-current-goal-completion-audit-v38-after-cftc-control-seed/completion-audit/current_goal_completion_audit_v38_after_cftc_control_seed.json`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T210002-codex-current-goal-completion-audit-v38-after-cftc-control-seed/completion-audit/current_goal_completion_audit_v38_checklist.csv`
- Unmet requirements CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T210002-codex-current-goal-completion-audit-v38-after-cftc-control-seed/completion-audit/current_goal_completion_audit_v38_unmet_requirements.csv`
- Intake-root CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T210002-codex-current-goal-completion-audit-v38-after-cftc-control-seed/completion-audit/current_goal_completion_audit_v38_intake_roots.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T210002-codex-current-goal-completion-audit-v38-after-cftc-control-seed/checks/current_goal_completion_audit_v38_after_cftc_control_seed_assertions.out`
