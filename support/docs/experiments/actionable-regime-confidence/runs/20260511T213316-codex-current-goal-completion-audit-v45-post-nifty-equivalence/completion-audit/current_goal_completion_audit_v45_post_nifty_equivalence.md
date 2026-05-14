# Current Goal Completion Audit v45 Post NIFTY Equivalence

Decision: `current_goal_completion_audit_v45=post_nifty_equivalence_schema_ready_still_blocked`.

Result:
- Board hash before run: `39740c685708d7ebbe80b92c2be2c432217adb933c801762902a3ae97c6cd5c3`.
- Current cursor before run: `20260511T213129+0800-codex-current-goal-completion-audit-v45-after-nifty-source-label`.
- Ready intake roots: `2/4` (`source_label_equivalence;direct_manipulation_row_intake`).
- Source-label equivalence verifier: `schema_ready_unscored`; rows `3435`; labels `{'Bull': 1213, 'Sideways': 1231, 'Crisis': 991}`.
- Source-label guardrail: missing Bear `true`; proxy/HMM guardrail `true`; accepted confidence `false`.
- Native sub-hour ready: `false`; recency verifier `blocked`.
- R6 direct verifier: `schema_ready_unscored`; positives `34`; matched negatives `34`; matched groups `33`; Wilson95 min LCB `0.898485`.
- R6 broad normal sample: `false`; direct species closed: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

Prompt-to-artifact checklist:

| ID | Status | Evidence | Gap |
|---|---|---|---|
| `R0_named_board` | `pass_checked` | docs/plans/2026-05-10-actionable-regime-confidence-todo.md |  |
| `R1_every_regime_95` | `fail_blocked` | ready_roots=2/4; source_label_status=schema_ready_unscored; direct_min_lcb=0.898485 | Strict all-regime 95% objective is still not achieved. |
| `R2_other_market_validation` | `partial_schema_ready_fail_closed` | NIFTY rows=3435; labels={'Bull': 1213, 'Sideways': 1231, 'Crisis': 991}; splits={'calibration': 1292, 'heldout_time': 1319, 'test': 824} | The new source-label-equivalence root is schema-ready, but it is partial, daily-only, lacks Bear rows, and remains unscored for accepted confidence. |
| `R3_other_cycle_timeframe` | `fail_blocked` | native_subhour_ready=False; recency_status=blocked | Native sub-hour rows/provenance and post-cutoff recency-extension rows/provenance are still absent. |
| `R4_proxy_guardrail` | `pass_guardrail` | event_species=owner_described_nifty_hmm_market_regime; proxy_guardrail=true | NIFTY owner-described HMM regime labels are schema input only here; no proxy/generated-label acceptance is made. |
| `R5_r6_direct_confidence` | `fail_blocked` | positives=34; controls=34; matched_groups=33; min_lcb=0.898485 | R6 support remains below 50/50, Wilson95 remains below 0.95, controls are not broad normal-market samples, and direct species are incomplete. |
| `R6_provider_chain_guardrail` | `partial_guardrail` | post_cleanup_provider_chain_readback_v1 exists as runtime evidence only when stable. | Provider/downstream execution does not replace missing source-owned confidence gates. |
| `R7_update_goal_gate` | `fail_blocked` | failures_present=true | update_goal=false. |

Gates:

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `ready_intake_roots` | `2` | `4` | `false` |
| `source_label_equivalence_schema` | `schema_ready_unscored` | `schema_ready_unscored` | `true` |
| `source_label_equivalence_full_roots` | `labels={'Bull': 1213, 'Sideways': 1231, 'Crisis': 991}` | `Bull/Bear/Sideways/Crisis source-owned accepted confidence` | `false` |
| `source_label_no_proxy_acceptance` | `proxy_guardrail=true` | `no HMM/proxy/generative acceptance` | `true` |
| `native_subhour_root_ready` | `false` | `true` | `false` |
| `source_panel_recency_verifier` | `blocked` | `not_blocked` | `false` |
| `r6_positive_support` | `34` | `>=50` | `false` |
| `r6_negative_support` | `34` | `>=50` | `false` |
| `r6_wilson95_lcb` | `0.898485` | `>=0.95` | `false` |
| `r6_broad_normal_sample` | `false` | `true` | `false` |
| `r6_direct_species_coverage` | `false` | `true` | `false` |

Next:
Treat the NIFTY package as schema-ready/partial only. Strict completion still needs accepted per-regime confidence, native sub-hour/recency roots, and R6 50/50 plus broad-normal/direct-species evidence.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T213316-codex-current-goal-completion-audit-v45-post-nifty-equivalence/completion-audit/current_goal_completion_audit_v45_post_nifty_equivalence.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T213316-codex-current-goal-completion-audit-v45-post-nifty-equivalence/completion-audit/current_goal_completion_audit_v45_post_nifty_equivalence.md`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213316-codex-current-goal-completion-audit-v45-post-nifty-equivalence/completion-audit/current_goal_completion_audit_v45_checklist.csv`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213316-codex-current-goal-completion-audit-v45-post-nifty-equivalence/completion-audit/current_goal_completion_audit_v45_gates.csv`
- Intake-root CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213316-codex-current-goal-completion-audit-v45-post-nifty-equivalence/completion-audit/current_goal_completion_audit_v45_intake_roots.csv`
- Verifier outputs: `docs/experiments/actionable-regime-confidence/runs/20260511T213316-codex-current-goal-completion-audit-v45-post-nifty-equivalence/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T213316-codex-current-goal-completion-audit-v45-post-nifty-equivalence/checks/current_goal_completion_audit_v45_post_nifty_equivalence_assertions.out`
