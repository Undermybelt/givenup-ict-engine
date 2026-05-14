# Current Goal Completion Audit v30 After Native And Recency Requests

- Decision: `current_goal_completion_audit_v30=native_and_recency_requests_ready_rows_not_acquired_blocked`
- Checklist rows: `9`
- Unmet rows: `6`
- Unmet ids: `R2, R3, R4, R5, R6, R8`
- Stock-regime owner request: `stock_regime_owner_recency_request_package_v1=owner_request_ready_rows_not_acquired`
- Native sub-hour sweep: `native_subhour_local_live_intake_sweep_v1=no_native_subhour_source_owned_intake_package`
- New confidence gate since v29: `false`
- Accepted rows added since v29: `0`
- Strict full objective achieved: `false`; `update_goal=false`

## Objective Restatement

Every active regime in Board A must have calibrated >=95% confidence, and the same regime confidence must remain suitable across other markets/species and other cycles/timeframes before reporting completion.

## Post-v29 Evidence Checked

- `docs/experiments/actionable-regime-confidence/runs/20260511T201655-codex-stock-regime-owner-recency-request-package-v1/stock-regime-owner-recency-request-package/stock_regime_owner_recency_request_package_v1.json`
- `docs/experiments/actionable-regime-confidence/runs/20260511T201713-codex-native-subhour-local-live-intake-sweep-v1/native-subhour-local-live-intake-sweep/native_subhour_local_live_intake_sweep_v1.json`

## Prompt-to-Artifact Checklist

| ID | Status | Evidence | Gap |
|---|---|---|---|
| `R0` | `pass_checked` | Board cursor and ledger were re-read; this v27 audit is generated under docs/experiments for the same board. |  |
| `R1` | `pass_scoped_not_full` | Scoped active-lane 95% evidence persists; Sapienza pump/dump adds 317 event groups with min split Wilson95 LCB 0.970640354706. | This remains scoped evidence, not strict full-market/full-cycle/full-species closure. |
| `R2` | `fail_blocked` | Source-label equivalence verifier status=blocked; missing files=2. | No source_label_equivalence_rows.csv or provenance file is present; no other-market/source-label equivalence can be accepted. |
| `R3` | `fail_blocked` | v26 still carries native sub-hour and strict timeframe blockers; no post-v26 artifact supplies native sub-hour source-owned labels. Native sub-hour sweep=native_subhour_local_live_intake_sweep_v1=no_native_subhour_source_owned_intake_package; intake_roots_checked=4; exact_required_intake_files_present=0; ready_sources=0. | No native sub-hour source-owned label intake package is present; raw OHLCV/provider files remain rejected. |
| `R4` | `fail_blocked` | Intake files present under checked /tmp roots=0; source-label verifier remains blocked. Stock-regime owner request=stock_regime_owner_recency_request_package_v1=owner_request_ready_rows_not_acquired; required_files=2; target_rows=4; r4_acquired=False. | R4 request package is ready, but source-owned strict 1h rows/provenance are not acquired. |
| `R5` | `fail_blocked` | Recency gate=strict_1h_recency_tail_current_source_recheck_v1=no_post_2026_01_30_source_owned_tail_rows; rows_after_2026_01_30={'XOM/Sideways': 0, 'UNH/Bear': 0, '^DJI/Sideways': 0, 'AMD/Bear': 0}; ready_external_tail_sources=0. Recency-extension verifier=recency_extension_live_verifier_recheck_v1=missing_recency_extension_intake_files; intake_files_present=0; missing_files=2. Stock-regime owner request=stock_regime_owner_recency_request_package_v1=owner_request_ready_rows_not_acquired; r5_recency_tail_repair_closed=False; known_post_2026_01_30_rows=0. | R5 request package is ready, but no post-2026-01-30 source-owned target rows are acquired. |
| `R6` | `partial_still_blocked` | Pump/dump scoped gate remains accepted, but source_recheck=spoofing_layering_current_source_recheck_v1=no_source_owned_matched_control_rows; acquisition_screen=spoofing_layering_source_acquisition_screen_v1=no_ready_positive_control_intake_source; direct_intake_status=blocked; missing_direct_files=3. Owner request package=do_putnins_owner_request_package_v1=owner_request_ready_rows_not_acquired; required_files=3; required_fields=17; accepted_rows_added=0. Contact leads=do_putnins_contact_leads_v1=public_contact_paths_ready_rows_not_acquired; contact_lead_count=4; request_sent=False; rows_acquired=False. | Contact paths are ready, but no request was sent by this run and no owner-approved rows were acquired; direct species coverage remains partial. |
| `R7` | `pass_guardrail` | Post-v26 screens keep proprietary, synthetic, simulated, metadata-only, and public-doc-only sources fail-closed; thresholds_relaxed=false and raw_data_committed=false. |  |
| `R8` | `fail_blocked` | R2, R3, R4, R5, and R6 remain uncovered or partial after v29 plus native-subhour and stock-regime owner-request readbacks. | Strict full objective is not achieved; update_goal must remain false. |

## Decision

The native-subhour sweep and stock-regime owner request convert more blockers into precise acquisition paths, but neither supplies accepted rows. The strict full objective remains blocked until the required intake files are present and accepted by the fail-closed verifiers.
