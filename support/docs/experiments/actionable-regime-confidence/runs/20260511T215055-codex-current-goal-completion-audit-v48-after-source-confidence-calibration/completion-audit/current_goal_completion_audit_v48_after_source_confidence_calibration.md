# Current Goal Completion Audit v48 After Source Confidence Calibration

Decision: `current_goal_completion_audit_v48=source_confidence_calibrated_no_acceptance_2of4_roots_still_blocked`.

Objective restatement:
Every active regime must have source-owned or owner-approved >=95 confidence and must retain suitable confidence across other markets/species and other cycles/timeframes before completion can be reported.

Result:
- Board hash before run: `b8f0f3de90ef8511e420572e6ef3f31afeb893bbae243a723555dc636c2bfeb9`.
- Current cursor before run: `20260511T214328+0800-codex-source-label-equivalence-confidence-calibration-v1`.
- Ready intake roots: `2/4` (`source_label_equivalence;direct_manipulation_row_intake`).
- Source-label verifier: `schema_ready_unscored`; rows `248440`; all roots present `true`.
- Source-label confidence accepted labels: `none`.
- Source-panel recency verifier: `blocked`.
- Native sub-hour root ready: `false`.
- R6 direct verifier: `schema_ready_unscored`; positives `41`; matched negatives `41`; matched groups `40`.
- R6 Wilson95 positive/negative/min LCB: `0.914332` / `0.914332` / `0.914332`.
- R6 support gate: `false`; broad normal sample: `false`; direct species closed: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

Prompt-to-artifact checklist:

| ID | Status | Evidence | Gap |
|---|---|---|---|
| `R0_named_board` | `pass_checked` | docs/plans/2026-05-10-actionable-regime-confidence-todo.md |  |
| `R1_every_regime_95` | `fail_blocked` | source_confidence_accepted_labels=none; r6_min_lcb=0.914332 | No active root has a new accepted 95% package in this slice; source-label confidence scoring rejected all four price roots and R6 remains below 0.95. |
| `R2_other_market_validation` | `fail_blocked` | source_label_status=schema_ready_unscored; rows=248440; labels={'Bear': 54939, 'Bull': 104979, 'Crisis': 30623, 'Sideways': 57899} | Source-label other-market rows are schema-ready, but the confidence calibration accepted zero labels. |
| `R3_other_cycle_timeframe` | `fail_blocked` | native_subhour_ready=False; recency_status=blocked | Native sub-hour rows/provenance and post-2026-01-30 recency-extension rows/provenance are still absent. |
| `R4_provider_and_full_chain` | `partial_guardrail` | latest provider/downstream readback remains 20260511T212339; this audit reran current root verifiers and source-confidence artifact only | No fresh provider/Auto-Quant/Pre-Bayes/BBN/CatBoost/execution-tree rerun was needed for this source-confidence rejection slice. |
| `R5_source_label_confidence_calibration` | `fail_blocked` | artifact=docs/experiments/actionable-regime-confidence/runs/20260511T214328-codex-source-label-equivalence-confidence-calibration-v1/source-label-equivalence-confidence-calibration/source_label_equivalence_confidence_calibration_v1.json; accepted_source_confidence_95_labels=none | All four price roots fail the source-confidence Wilson95 gate across calibration, heldout-market, heldout-time, and test splits. |
| `R6_direct_manipulation_confidence` | `fail_blocked` | positives=41; controls=41; matched_groups=40; min_lcb=0.914332 | R6 is below 50/50 support, Wilson95 remains below 0.95, broad-normal sample is false, and direct species coverage remains incomplete. |
| `R7_no_proxy_acceptance` | `pass_guardrail` | schema-ready source labels, same-event controls, provider proxies, and OHLCV/direct proxies remain fail-closed |  |
| `R8_multi_agent_safety` | `pass_guardrail` | board_hash_before=b8f0f3de90ef8511e420572e6ef3f31afeb893bbae243a723555dc636c2bfeb9; cursor_before=20260511T214328+0800-codex-source-label-equivalence-confidence-calibration-v1; append-only registration expected |  |
| `R9_update_goal_gate` | `fail_blocked` | failures_present=true | Missing and failed requirements remain; update_goal=false. |

Gates:

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `ready_intake_roots` | `2` | `4` | `false` |
| `source_label_verifier` | `schema_ready_unscored` | `schema_ready_unscored` | `true` |
| `source_label_all_roots_present` | `Bear,Bull,Crisis,Sideways` | `Bull,Bear,Sideways,Crisis` | `true` |
| `source_label_confidence_accepted_labels` | `0` | `4` | `false` |
| `source_panel_recency_verifier` | `blocked` | `not_blocked` | `false` |
| `native_subhour_root_ready` | `False` | `True` | `false` |
| `r6_positive_support` | `41` | `>=50` | `false` |
| `r6_negative_support` | `41` | `>=50` | `false` |
| `r6_wilson95_lcb` | `0.914332` | `>=0.95` | `false` |
| `r6_broad_normal_sample` | `False` | `True` | `false` |
| `r6_direct_species_coverage` | `False` | `True` | `false` |

Next:
Acquire native sub-hour source-label rows or post-2026-01-30 recency-extension rows, or expand R6 direct Manipulation to 50/50 broad-normal controls/direct species coverage before another completion claim.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T215055-codex-current-goal-completion-audit-v48-after-source-confidence-calibration/completion-audit/current_goal_completion_audit_v48_after_source_confidence_calibration.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T215055-codex-current-goal-completion-audit-v48-after-source-confidence-calibration/completion-audit/current_goal_completion_audit_v48_after_source_confidence_calibration.md`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T215055-codex-current-goal-completion-audit-v48-after-source-confidence-calibration/completion-audit/current_goal_completion_audit_v48_checklist.csv`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T215055-codex-current-goal-completion-audit-v48-after-source-confidence-calibration/completion-audit/current_goal_completion_audit_v48_gates.csv`
- Verifier outputs: `docs/experiments/actionable-regime-confidence/runs/20260511T215055-codex-current-goal-completion-audit-v48-after-source-confidence-calibration/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T215055-codex-current-goal-completion-audit-v48-after-source-confidence-calibration/checks/current_goal_completion_audit_v48_after_source_confidence_calibration_assertions.out`
