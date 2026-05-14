# Current Goal Completion Audit v45 After NIFTY Intake

Decision: `current_goal_completion_audit_v45=after_nifty_source_label_partial_still_blocked`.

Objective restatement:
Every active regime must have source-owned or owner-approved >=95 confidence and must retain suitable confidence when validated on other markets/species and other cycles/timeframes.

Result:
- Board hash before run: `ad4166fa969dade1b275d6a9cb01a89b42543d6c89e182027631d91751b2a6ee`.
- Cursor before run: `20260511T212819+0800-codex-nifty-source-label-equivalence-intake-v1`.
- Ready intake roots: `2/4` (`source_label_equivalence;direct_manipulation_row_intake`).
- Source-label equivalence verifier: `schema_ready_unscored`; rows `3435`; labels `{'Bull': 1213, 'Crisis': 991, 'Sideways': 1231}`; dates `2012-02-02..2026-03-20`.
- Source-label limits: all main labels present `false`; timeframes `['1d']`; markets `['india_equity_index']`.
- Native sub-hour ready: `false`; recency verifier: `blocked`.
- R6 direct verifier: `schema_ready_unscored`; positives `24`; matched negatives `24`; matched groups `23`; Wilson95 min LCB `0.862024`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

Prompt-to-artifact checklist:

| ID | Status | Evidence | Gap |
|---|---|---|---|
| `R0_named_board` | `pass_checked` | docs/plans/2026-05-10-actionable-regime-confidence-todo.md |  |
| `R1_every_regime_95` | `fail_blocked` | source_label_status=schema_ready_unscored; source_label_95_gate=False; r6_min_wilson95_lcb=0.862024; ready_roots=2/4 | Source-label equivalence is schema-ready but unscored/partial; R6 Wilson95 remains below 0.95; native sub-hour and recency roots remain absent. |
| `R2_other_market_species_validation` | `partial_blocked` | NIFTY source-label rows=3435; labels={'Bull': 1213, 'Crisis': 991, 'Sideways': 1231}; markets=['india_equity_index']; symbols=['NIFTY500'] | NIFTY provides one other-market daily source-label package for Bull/Crisis/Sideways only; Bear is absent and no 95 confidence gate is produced. |
| `R3_other_cycle_timeframe_validation` | `fail_blocked` | timeframes=['1d']; native_subhour_ready=False; recency_status=blocked | NIFTY rows are daily only; native sub-hour source-label root and recency-extension root remain unavailable. |
| `R4_r6_direct_confidence` | `fail_blocked` | positives=24; controls=24; groups=23; min_lcb=0.862024; broad_normal=False; species_closed=False | R6 remains below 50/50 support and below 0.95 Wilson95, with same-source/event controls and incomplete direct species coverage. |
| `R5_no_proxy_acceptance` | `pass_guardrail` | NIFTY schema readiness is recorded as partial/unscored; R6 same-event controls remain fail-closed; no completion claim. |  |
| `R6_multi_agent_safety` | `pass_guardrail` | board_hash_before=ad4166fa969dade1b275d6a9cb01a89b42543d6c89e182027631d91751b2a6ee; cursor_before=20260511T212819+0800-codex-nifty-source-label-equivalence-intake-v1; append-only V45 audit |  |
| `R7_update_goal_gate` | `fail_blocked` | failures_present=true | Strict full objective remains incomplete; update_goal=false. |

Gates:

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `ready_intake_roots` | `2` | `4` | `false` |
| `source_label_schema_ready` | `schema_ready_unscored` | `schema_ready_unscored` | `true` |
| `source_label_all_main_labels` | `{"Bull": 1213, "Crisis": 991, "Sideways": 1231}` | `Bear/Bull/Crisis/Sideways` | `false` |
| `source_label_confidence_95` | `False` | `True` | `false` |
| `cross_market_complete` | `False` | `True` | `false` |
| `cross_timeframe_complete` | `False` | `True` | `false` |
| `native_subhour_root_ready` | `False` | `True` | `false` |
| `recency_extension_ready` | `False` | `True` | `false` |
| `r6_positive_support` | `24` | `>=50` | `false` |
| `r6_negative_support` | `24` | `>=50` | `false` |
| `r6_wilson95_lcb` | `0.862024` | `>=0.95` | `false` |
| `r6_broad_normal_sample` | `False` | `True` | `false` |
| `r6_direct_species_coverage` | `False` | `True` | `false` |

Next:
Turn source-label schema readiness into real confidence gates only if per-regime Bear/Bull/Crisis/Sideways source rows, cross-market coverage, native sub-hour/other-cycle evidence, recency extension, and unchanged calibration/heldout scoring all pass; otherwise continue filling missing roots.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T213101-codex-current-goal-completion-audit-v45-after-nifty-intake/completion-audit/current_goal_completion_audit_v45_after_nifty_intake.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T213101-codex-current-goal-completion-audit-v45-after-nifty-intake/completion-audit/current_goal_completion_audit_v45_after_nifty_intake.md`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213101-codex-current-goal-completion-audit-v45-after-nifty-intake/completion-audit/current_goal_completion_audit_v45_checklist.csv`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213101-codex-current-goal-completion-audit-v45-after-nifty-intake/completion-audit/current_goal_completion_audit_v45_gates.csv`
- Intake-root CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213101-codex-current-goal-completion-audit-v45-after-nifty-intake/completion-audit/current_goal_completion_audit_v45_intake_roots.csv`
- Verifier outputs: `docs/experiments/actionable-regime-confidence/runs/20260511T213101-codex-current-goal-completion-audit-v45-after-nifty-intake/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T213101-codex-current-goal-completion-audit-v45-after-nifty-intake/checks/current_goal_completion_audit_v45_after_nifty_intake_assertions.out`
