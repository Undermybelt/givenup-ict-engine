# Current Goal Completion Audit v18 Prompt-to-Artifact

Run ID: `20260511T183611+0800-codex-current-goal-completion-audit-v18-prompt-artifact`

## Objective Restated

Every active regime has confidence >=95 and remains suitably confident when validated on other markets and other timeframes/cycles.

## Decision

- Scoped active-lane status: `accepted_95`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Gate result: `current_goal_completion_audit_v18=scoped_95_present_prompt_artifact_audit_blocks_full_objective`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Prompt-to-Artifact Checklist

| Requirement | Status | Evidence | Gap |
|---|---|---|---|
| every active regime has calibrated confidence >=95 | `pass_scoped` | accepted_95_lanes=['Bull', 'Bear', 'Sideways', 'Crisis', 'Manipulation']; min_price_root_floor=0.9529358324; scoped_direct_manipulation_floor=0.967945 | Scoped active lane passes, but consumer map itself marks full objective false. |
| validated on other markets with source-owned or owner-approved labels | `fail_blocked` | source_equivalence_missing_files=['/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv', '/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_provenance.json']; external_screen_decision=external_source_label_candidate_screen_v1=no_promotable_source_label_equivalence; autoquant_gate=autoquant_local_source_label_equivalence_audit_v1=no_new_source_labels_exact_daily_aapl_only | No source-owned MainRegimeV2 equivalence rows/provenance for QQQ/NQ/crypto/FX/rates/commodities/native sub-hour/direct species. |
| validated on other cycles/timeframes beyond scoped daily/weekly/monthly support | `fail_blocked` | native_subhour_ready_overlap=0/4; strict_1h=41/156 | Native sub-hour source-overlap cells are 0; strict exact 1h remains partial. |
| strict exact 1h ticker/root support complete enough for full objective | `partial_blocked` | accepted=41; blocked=115; total=156 | Provider rows are ready, but source-label support/recency blocks 115 strict rows. |
| source panel recency after 2026-01-30 | `fail_blocked` | source_max_date=2026-01-30; upstream_same_csv_or_parquet_size=True; macro_post_tail_rows=26 feature rows only | Post-tail feature rows are not source labels; upstream source package has no newer label revision. |
| direct Manipulation full species coverage with matched negatives | `fail_blocked` | full_species_complete=False; direct_local_accepted=0; direct_scan_ready=0; hf_schema_decision=blocked_schema_missing_labels_and_controls | Scoped direct overlay passes, but spoofing/layering/quote-stuffing/pinging/bear-raid/painting-tape/social-text variants remain missing or positive-only. |
| do not rely on proxy signals as completion | `pass_guardrail` | external source candidates with labels/signals were screened but blocked without owner-approved MainRegimeV2 equivalence; macro_label_like_fields=[] | Proxy OHLCV/rule labels remain excluded. |
| update_goal only if full objective is achieved | `pass_guardrail` | prior_strict_full_objective=False; this_audit_full_objective=false | Do not call update_goal. |

## Blocking Requirements

- validated on other markets with source-owned or owner-approved labels
- validated on other cycles/timeframes beyond scoped daily/weekly/monthly support
- strict exact 1h ticker/root support complete enough for full objective
- source panel recency after 2026-01-30
- direct Manipulation full species coverage with matched negatives

## Next

Fill the source-label equivalence intake with source-owned rows/provenance, or obtain matched direct Manipulation species rows, then rerun unchanged gates.
