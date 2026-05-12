# Current Goal Completion Audit v45 After NIFTY Equivalence

Decision: `current_goal_completion_audit_v45=after_nifty_equivalence_partial_schema_ready_still_blocked`.

Objective restatement:
Every active regime must have source-owned or owner-approved >=95 confidence, and must keep suitable confidence when validated on other markets/species and other cycles/timeframes before completion can be reported.

Result:
- Board hash before run: `9408b9d7a111b327f1e6459c121c8eb5df9de186189448897ad8a6e59f33f06a`.
- Current cursor before run: `20260511T213129+0800-codex-current-goal-completion-audit-v45-after-nifty-source-label`.
- Ready intake roots: `2/4` (`source_label_equivalence;direct_manipulation_row_intake`).
- Source-label verifier: `schema_ready_unscored`; rows `3435`; labels `{'Bull': 1213, 'Crisis': 991, 'Sideways': 1231}`; missing root labels `['Bear']`.
- Source-label date range: `2012-02-02` to `2026-03-20`; split counts `{'calibration': 1292, 'heldout_time': 1319, 'test': 824}`.
- Source-panel recency verifier: `blocked`; native sub-hour root ready: `false`.
- R6 direct verifier: `schema_ready_unscored`; positives `24`; matched negatives `24`; matched groups `23`.
- R6 Wilson95 positive/negative/min LCB: `0.862024` / `0.862024` / `0.862024`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

Prompt-to-artifact checklist:

| ID | Status | Evidence | Gap |
|---|---|---|---|
| `R0_named_board` | `pass_checked` | docs/plans/2026-05-10-actionable-regime-confidence-todo.md |  |
| `R1_every_regime_95` | `fail_blocked` | cursor=20260511T213129+0800-codex-current-goal-completion-audit-v45-after-nifty-source-label; ready_roots=2/4; source_label_status=schema_ready_unscored; direct_min_wilson95_lcb=0.862024 | NIFTY source-label intake is schema-ready but unscored and partial; R6 direct confidence is still below 0.95. |
| `R2_other_market_validation` | `partial_blocked` | source_label_rows=3435; labels={'Bull': 1213, 'Crisis': 991, 'Sideways': 1231}; missing_root_labels=['Bear'] | NIFTY supplies Bull/Sideways/Crisis daily source labels but no Bear rows and no accepted confidence gate. |
| `R3_other_cycle_timeframe` | `fail_blocked` | native_subhour_ready=False; recency_status=blocked; NIFTY timeframe=1d | Native sub-hour source-label rows/provenance remain absent, and R5 recency extension remains blocked. |
| `R4_provider_and_full_chain` | `pass_guardrail` | post_cleanup_provider_chain_readback_v1 registered; this audit does not claim chain completion. |  |
| `R5_r6_direct_confidence` | `fail_blocked` | positives=24; controls=24; matched_groups=23; min_lcb=0.862024; broad_normal_sample=False; species_closed=False | R6 is still 24/24 after cleanup; support is below 50/50, Wilson95 is below 0.95, broad normal controls are absent, and species coverage is incomplete. |
| `R6_no_proxy_acceptance` | `pass_guardrail` | This audit treats schema-ready source labels and runtime/provider evidence as partial evidence only. |  |
| `R7_multi_agent_safety` | `pass_guardrail` | board_hash_before=9408b9d7a111b327f1e6459c121c8eb5df9de186189448897ad8a6e59f33f06a; cursor_before=20260511T213129+0800-codex-current-goal-completion-audit-v45-after-nifty-source-label; append-only registration expected |  |
| `R8_update_goal_gate` | `fail_blocked` | failures_present=true | Missing and failed requirements remain; update_goal=false. |

Gates:

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `ready_intake_roots` | `2` | `4` | `false` |
| `source_label_schema_ready` | `schema_ready_unscored` | `schema_ready_unscored` | `true` |
| `source_label_all_root_labels_present` | `Bull,Crisis,Sideways` | `Bear,Bull,Crisis,Sideways` | `false` |
| `source_label_accepted_confidence` | `false` | `true` | `false` |
| `source_label_full_coverage` | `false` | `true` | `false` |
| `source_panel_recency_verifier` | `blocked` | `not_blocked` | `false` |
| `native_subhour_root_ready` | `false` | `true` | `false` |
| `r6_positive_support` | `24` | `>=50` | `false` |
| `r6_negative_support` | `24` | `>=50` | `false` |
| `r6_wilson95_lcb` | `0.862024` | `>=0.95` | `false` |
| `r6_broad_normal_sample` | `false` | `true` | `false` |
| `r6_direct_species_coverage` | `false` | `true` | `false` |

Next:
Fill the missing Bear source-label equivalence, native sub-hour rows, R5 recency extension, and R6 support/broad-normal/direct-species gaps before another strict completion claim.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T213300-codex-current-goal-completion-audit-v45-after-nifty-equivalence/completion-audit/current_goal_completion_audit_v45_after_nifty_equivalence.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T213300-codex-current-goal-completion-audit-v45-after-nifty-equivalence/completion-audit/current_goal_completion_audit_v45_after_nifty_equivalence.md`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213300-codex-current-goal-completion-audit-v45-after-nifty-equivalence/completion-audit/current_goal_completion_audit_v45_checklist.csv`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213300-codex-current-goal-completion-audit-v45-after-nifty-equivalence/completion-audit/current_goal_completion_audit_v45_gates.csv`
- Intake-root CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213300-codex-current-goal-completion-audit-v45-after-nifty-equivalence/completion-audit/current_goal_completion_audit_v45_intake_roots.csv`
- Source-label summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213300-codex-current-goal-completion-audit-v45-after-nifty-equivalence/completion-audit/current_goal_completion_audit_v45_source_label_summary.csv`
- Verifier outputs: `docs/experiments/actionable-regime-confidence/runs/20260511T213300-codex-current-goal-completion-audit-v45-after-nifty-equivalence/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T213300-codex-current-goal-completion-audit-v45-after-nifty-equivalence/checks/current_goal_completion_audit_v45_after_nifty_equivalence_assertions.out`
