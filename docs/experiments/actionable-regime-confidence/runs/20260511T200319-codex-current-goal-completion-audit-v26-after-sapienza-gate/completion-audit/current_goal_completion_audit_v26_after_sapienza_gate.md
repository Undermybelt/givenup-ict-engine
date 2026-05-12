# Current Goal Completion Audit v26 After Sapienza Gate

- Decision: `current_goal_completion_audit_v26=scoped_sapienza_gate_added_strict_full_objective_blocked`
- Checklist rows: `9`
- Unmet rows: `6`
- Unmet ids: `R2, R3, R4, R5, R6, R8`
- Sapienza accepted event groups: `317`
- Sapienza minimum split Wilson95 LCB: `0.970640354706`
- New confidence gate since v25: `true`
- Strict full objective achieved: `false`; `update_goal=false`

## Objective Restatement

Every active regime must have calibrated `>=95%` confidence, and that confidence must remain suitable across other markets/species and other cycles/timeframes before the goal can be marked complete.

## Checklist

| ID | Status | Evidence | Gap |
|---|---|---|---|
| `R0` | `pass_checked` | Current Cursor updated to sapienza_pumpdump_control_gate_v1. |  |
| `R1` | `pass_scoped_not_full` | Sapienza direct pump/dump gate accepted=True min_lcb=0.970640354706; existing scoped consumer map remains accepted. | Scoped acceptance is not the same as strict full-market/full-cycle/full-species completion. |
| `R2` | `fail_blocked` | local=local_broad_source_owned_label_inventory_v1=no_new_promotable_uncounted_source_owned_labels; v25 failed rows include R2. | No promotable source-owned or owner-approved other-market equivalence rows were found. |
| `R3` | `fail_blocked` | native=native_subhour_source_recheck_v2=no_ready_native_subhour_source_owned_labels; ready_sources=0. | Native sub-hour price-root source labels remain absent. |
| `R4` | `fail_blocked` | exact_search=strict_1h_target_exact_source_search_v1=no_ready_exact_target_source_owned_rows; ready_sources=0. | Strict exact 1h source-owned row intake is still missing. |
| `R5` | `fail_blocked` | rows_after_2026_01_30={'XOM/Sideways': 0, 'UNH/Bear': 0, '^DJI/Sideways': 0, 'AMD/Bear': 0}. | Strict target rows still have zero post-2026-01-30 source-panel rows. |
| `R6` | `partial_still_blocked` | Sapienza accepted 317 pump/dump event groups at min Wilson95 LCB 0.970640354706; direct verifier remains direct_manipulation_intake_verifier_readback_v1=blocked_missing_direct_intake_files. | Spoofing/layering, quote stuffing, pinging, bear raid, and painting tape still lack source-owned positive/control rows. |
| `R7` | `pass_guardrail` | strict_contract=strict_objective_acquisition_contract_v1=contracts_ready_objective_still_blocked; Sapienza raw rows remain under /tmp and are not trade usable. |  |
| `R8` | `fail_blocked` | Rows R2, R3, R4, R5, and R6 remain incomplete after the new Sapienza scoped gate. | Strict full objective is not achieved; update_goal must remain false. |

## Decision

Sapienza materially improves direct `Manipulation` by adding a scoped pump/dump positive-control gate, but the original strict objective remains blocked because the price-root transfer requirements and the remaining direct manipulation species are still uncovered.
