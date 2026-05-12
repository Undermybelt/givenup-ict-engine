# Current Goal Completion Audit v32 After R2/R3 Request Packages

- Decision: `current_goal_completion_audit_v32=request_packages_ready_rows_not_acquired_blocked`
- Unmet requirement ids: `R2, R3, R4, R5, R6, R8`
- R2 contact leads: `source_label_equivalence_contact_leads_v1=public_contact_paths_ready_rows_not_acquired`; rows acquired `false`
- R3 native-subhour request package: `native_subhour_intake_request_package_v1=request_ready_rows_not_acquired`; targets `336`; focus cells `4`
- Ready intake roots: `0/4`
- Accepted rows added since v31: `0`; new confidence gate since v31: `false`
- Strict full objective achieved: `false`; `update_goal=false`
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`

## Prompt-to-Artifact Checklist

| ID | Status | Evidence | Gap |
|---|---|---|---|
| `R0` | `pass_checked` | Board, v31 audit, R2 source-label equivalence contact leads, R3 native-subhour intake request package, and live intake roots were checked. |  |
| `R1` | `pass_scoped_not_full` | Scoped active-lane 95% evidence persists; Sapienza pump/dump has 317 event groups and min Wilson LCB 0.970640354706. | Still not strict full-market/full-cycle/full-species closure. |
| `R2` | `fail_blocked` | R2 contact leads=9; rows_acquired=False; request_sent=False; live source-label verifier status=blocked/missing_required_files. | Contact/licensing surfaces are ready, but source-label equivalence rows/provenance remain absent. |
| `R3` | `fail_blocked` | R3 request targets=336; focus blocker cells=4; rows_acquired=False; intake_files_created=False. | Native sub-hour request package is concrete, but no source-owned rows/provenance are present under the intake root. |
| `R4` | `fail_blocked` | Stock-regime contact leads=4; rows_acquired=False; source_label_equivalence_intake_files_created=False; source-label verifier status=blocked/missing_required_files. | Contact paths exist, but strict exact 1h source-owned rows/provenance are not acquired. |
| `R5` | `fail_blocked` | Kaggle refresh decision=kaggle_stock_regime_live_refresh_v1=downloaded_latest_public_dataset_no_post_2026_01_30_rows; date_max=2026-01-30; post_cutoff_target_rows=0; recency verifier status=blocked/missing_required_files. | Latest public Kaggle package still ends at 2026-01-30 and recency-extension files are absent. |
| `R6` | `partial_still_blocked` | Do/Putnins contact leads=4; rows_acquired=False; direct verifier status=blocked/missing_required_files. | Pump/dump scoped gate persists, but spoofing/layering positive/control row packages are still missing. |
| `R7` | `pass_guardrail` | v32 preserves the fail-closed verifier results; request packages do not create labels, commit raw data, or relax thresholds. |  |
| `R8` | `fail_blocked` | Unmet rows remain R2, R3, R4, R5, R6, R8; ready intake roots=0/4; accepted rows added since v31=0. | Strict full objective is not achieved; update_goal must remain false. |

## Intake Roots

| ID | Ready | Missing Files |
|---|---:|---|
| `source_label_equivalence` | `false` | `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json` |
| `native_subhour_source_label` | `false` | `native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json` |
| `source_panel_recency_extension` | `false` | `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json` |
| `direct_manipulation_row_intake` | `false` | `positive_spoofing_layering_rows.csv;matched_negative_normal_activity_rows.csv;provenance_manifest.json` |

## Decision

R2 and R3 now have concrete acquisition/request packages, but neither package contains acquired source-owned rows. The four fail-closed intake roots remain incomplete, so the strict objective remains blocked and the goal must not be marked complete.
