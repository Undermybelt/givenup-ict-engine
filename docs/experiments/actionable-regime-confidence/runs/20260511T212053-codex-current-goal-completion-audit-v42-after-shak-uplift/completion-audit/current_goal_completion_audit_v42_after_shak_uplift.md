# Current Goal Completion Audit v42 After Shak Uplift

Decision: `current_goal_completion_audit_v42=post_shak_live_32x32_still_blocked`.

Objective restatement:
Every active regime must have source-owned or owner-approved >=95 confidence, and must keep suitable confidence when validated on other markets/species and other cycles/timeframes before completion can be reported.

Result:
- Board hash before run: `799a2dc249db1f820f8a6296e2e61fe1a72c7df3c88bab700668b39c6101a790`.
- Current cursor before run: `20260511T212004+0800-codex-r6-shak-duplicate-row-cleanup-v1`.
- Ready intake roots: `1/4` (`direct_manipulation_row_intake`).
- R6 direct verifier: `schema_ready_unscored`; positives `32`; matched negatives `32`; matched groups `31`.
- R6 Wilson95 positive/negative/min LCB: `0.892821` / `0.892821` / `0.892821`.
- R6 support gate: `false`; broad normal sample: `false`; direct species closed: `false`.
- Source-label equivalence verifier: `blocked`.
- Source-panel recency verifier: `blocked`.
- Native sub-hour root ready: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

Prompt-to-artifact checklist:

| ID | Status | Evidence | Gap |
|---|---|---|---|
| `R0_named_board` | `pass_checked` | docs/plans/2026-05-10-actionable-regime-confidence-todo.md |  |
| `R1_every_regime_95` | `fail_blocked` | current_cursor=20260511T212004+0800-codex-r6-shak-duplicate-row-cleanup-v1; ready_roots=1/4; direct_min_wilson95_lcb=0.892821 | Strict all-regime 95% objective is still not achieved; R6 direct confidence is below 0.95 and R2/R3/R4/R5 source roots are absent. |
| `R2_other_market_validation` | `fail_blocked` | source_label_equivalence_status=blocked; root=/tmp/ict-engine-source-label-equivalence-intake | source_label_equivalence_rows.csv and source_label_equivalence_provenance.json are absent. |
| `R3_other_cycle_timeframe` | `fail_blocked` | native_subhour_ready=False; recency_status=blocked | native sub-hour source-label rows/provenance and recency-extension rows/provenance are absent. |
| `R4_r6_direct_confidence` | `fail_blocked` | positives=32; controls=32; matched_groups=31; min_lcb=0.892821; broad_normal_sample=False; species_closed=False | R6 improved to 37/37 but support is still below 50/50, Wilson95 is below 0.95, controls are same-event seeds, and species coverage is incomplete. |
| `R5_no_proxy_acceptance` | `pass_guardrail` | This audit keeps VantMacro drafts, source panels without new rows, same-event controls, and OHLCV/provider proxies fail-closed. |  |
| `R6_update_goal_gate` | `fail_blocked` | failures_present=true | Missing and failed requirements remain; update_goal=false. |

Gates:

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `ready_intake_roots` | `1` | `4` | `false` |
| `r6_positive_support` | `32` | `>=50` | `false` |
| `r6_negative_support` | `32` | `>=50` | `false` |
| `r6_wilson95_lcb` | `0.892821` | `>=0.95` | `false` |
| `r6_broad_normal_sample` | `false` | `true` | `false` |
| `r6_direct_species_coverage` | `false` | `true` | `false` |
| `source_label_equivalence_verifier` | `blocked` | `not_blocked` | `false` |
| `source_panel_recency_verifier` | `blocked` | `not_blocked` | `false` |

Next:
R6 needs at least 50/50 source-owned rows plus broad same-schema normal-market controls and broader direct species coverage; R2/R3/R4/R5 still need required source-owned rows/provenance before another completion audit can pass.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T212053-codex-current-goal-completion-audit-v42-after-shak-uplift/completion-audit/current_goal_completion_audit_v42_after_shak_uplift.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T212053-codex-current-goal-completion-audit-v42-after-shak-uplift/completion-audit/current_goal_completion_audit_v42_after_shak_uplift.md`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T212053-codex-current-goal-completion-audit-v42-after-shak-uplift/completion-audit/current_goal_completion_audit_v42_checklist.csv`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T212053-codex-current-goal-completion-audit-v42-after-shak-uplift/completion-audit/current_goal_completion_audit_v42_gates.csv`
- Intake-root CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T212053-codex-current-goal-completion-audit-v42-after-shak-uplift/completion-audit/current_goal_completion_audit_v42_intake_roots.csv`
- Verifier outputs: `docs/experiments/actionable-regime-confidence/runs/20260511T212053-codex-current-goal-completion-audit-v42-after-shak-uplift/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T212053-codex-current-goal-completion-audit-v42-after-shak-uplift/checks/current_goal_completion_audit_v42_after_shak_uplift_assertions.out`
