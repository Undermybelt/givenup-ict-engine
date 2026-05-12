# Current Goal Completion Audit v27 After Live Intake And Tail Rechecks

- Decision: `current_goal_completion_audit_v27=post_v26_rechecks_confirm_strict_full_objective_blocked`
- Checklist rows: `9`
- Unmet rows: `6`
- Unmet ids: `R2, R3, R4, R5, R6, R8`
- New confidence gate since v26: `false`
- Accepted rows added since v26: `0`
- Strict full objective achieved: `false`; `update_goal=false`

## Objective Restatement

Every active regime in Board A must have calibrated >=95% confidence, and the same regime confidence must remain suitable across other markets/species and other cycles/timeframes before reporting completion.

## Post-v26 Evidence Checked

- `docs/experiments/actionable-regime-confidence/runs/20260511T200347-codex-spoofing-layering-current-source-recheck-v1/spoofing-layering-current-source-recheck/spoofing_layering_current_source_recheck_v1.json`
- `docs/experiments/actionable-regime-confidence/runs/20260511T200951-codex-live-intake-verifier-recheck-v2-after-v26/live-intake-verifier-recheck/live_intake_verifier_recheck_v2_after_v26.json`
- `docs/experiments/actionable-regime-confidence/runs/20260511T200909-codex-strict-1h-recency-tail-current-source-recheck-v1/recency-tail-current-source-recheck/strict_1h_recency_tail_current_source_recheck_v1.json`
- `docs/experiments/actionable-regime-confidence/runs/20260511T200726-codex-spoofing-layering-source-acquisition-screen-v1/spoofing-layering-source-acquisition-screen/spoofing_layering_source_acquisition_screen_v1.json`

## Prompt-to-Artifact Checklist

| ID | Status | Evidence | Gap |
|---|---|---|---|
| `R0` | `pass_checked` | Board cursor and ledger were re-read; this v27 audit is generated under docs/experiments for the same board. |  |
| `R1` | `pass_scoped_not_full` | Scoped active-lane 95% evidence persists; Sapienza pump/dump adds 317 event groups with min split Wilson95 LCB 0.970640354706. | This remains scoped evidence, not strict full-market/full-cycle/full-species closure. |
| `R2` | `fail_blocked` | Source-label equivalence verifier status=blocked; missing files=2. | No source_label_equivalence_rows.csv or provenance file is present; no other-market/source-label equivalence can be accepted. |
| `R3` | `fail_blocked` | v26 still carries native sub-hour and strict timeframe blockers; no post-v26 artifact supplies native sub-hour source-owned labels. | Native sub-hour price-root source labels remain missing. |
| `R4` | `fail_blocked` | Intake files present under checked /tmp roots=0; source-label verifier remains blocked. | Strict exact 1h row/provenance intake is still absent. |
| `R5` | `fail_blocked` | Recency gate=strict_1h_recency_tail_current_source_recheck_v1=no_post_2026_01_30_source_owned_tail_rows; rows_after_2026_01_30={'XOM/Sideways': 0, 'UNH/Bear': 0, '^DJI/Sideways': 0, 'AMD/Bear': 0}; ready_external_tail_sources=0. | XOM/Sideways, UNH/Bear, ^DJI/Sideways, and AMD/Bear still have zero post-cutoff source rows. |
| `R6` | `partial_still_blocked` | Pump/dump scoped gate remains accepted, but source_recheck=spoofing_layering_current_source_recheck_v1=no_source_owned_matched_control_rows; acquisition_screen=spoofing_layering_source_acquisition_screen_v1=no_ready_positive_control_intake_source; direct_intake_status=blocked; missing_direct_files=3. | Spoofing/layering, quote stuffing, pinging, bear raid, and painting tape still lack acceptable positive/control row packages. |
| `R7` | `pass_guardrail` | Post-v26 screens keep proprietary, synthetic, simulated, metadata-only, and public-doc-only sources fail-closed; thresholds_relaxed=false and raw_data_committed=false. |  |
| `R8` | `fail_blocked` | R2, R3, R4, R5, and R6 remain uncovered or partial after the post-v26 evidence. | Strict full objective is not achieved; update_goal must remain false. |

## Decision

The post-v26 evidence does not close the strict objective. It confirms the same hard blockers: source-label equivalence intake is missing, native sub-hour/strict `1h` transfer evidence is missing, recency-tail rows remain absent after `2026-01-30`, and direct `Manipulation` still lacks source-owned spoofing/layering plus other species positive/control row packages.
