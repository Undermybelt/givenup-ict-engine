# Current Goal Completion Audit v18 After External Source Screen

Run ID: `20260511T183632+0800-current-goal-completion-audit-v18-after-external-source-screen`

## Restated Objective

- Every active regime/lane must have its own `>=95%` calibrated confidence evidence.
- Evidence must survive other-market/species and other-timeframe/cycle validation.
- Direct `Manipulation` must use direct row sources with matched negative controls.
- Proxy labels, OHLCV-only/generated labels, or owner-unapproved crosswalks do not count.

## Decision

`current_goal_completion_audit_v18=scoped_95_present_external_source_screen_confirms_full_objective_blocked`

- Scoped active-lane `>=95%` evidence: `true`.
- Strict full objective achieved: `false`; `update_goal=false`.
- External source screen found promising NIFTY/IDX candidates, but no promotable `MainRegimeV2` source-label equivalence.
- Accepted rows added: `0`; new confidence gate: `false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Checklist

- `pass_scoped` - Each active MainRegimeV2/direct lane has its own >=95% calibrated consumer factor.
  Evidence: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.json`
  Coverage: accepted lanes=['Bull', 'Bear', 'Sideways', 'Crisis', 'Manipulation']; accepted_95_lane_count=5
  Gap: This is scoped consumer readiness only, not strict full objective closure.
- `blocked` - Validation survives other markets/species with source-owned labels or owner-approved equivalence.
  Evidence: `docs/experiments/actionable-regime-confidence/runs/20260511T182922-codex-source-label-equivalence-intake-verifier-v1/equivalence-intake-verifier/source_label_equivalence_intake_verifier_manifest_v1.json ; docs/experiments/actionable-regime-confidence/runs/20260511T183328-codex-external-source-label-candidate-screen-v1/external-source-label-screen/external_source_label_candidate_screen_v1.json`
  Coverage: intake gate=source_label_equivalence_intake_verifier_v1=ready_rows_not_acquired; external screen=external_source_label_candidate_screen_v1=no_promotable_source_label_equivalence; candidates=6
  Gap: Required source-label equivalence intake files are missing; NIFTY/IDX external candidates lack owner-approved MainRegimeV2 crosswalk.
- `blocked` - Validation survives other cycles/timeframes, including strict exact 1h and native sub-hour where claimed.
  Evidence: `docs/experiments/actionable-regime-confidence/runs/20260511T181859-codex-strict-1h-gap-triage-v1/strict-1h-gap-triage/strict_1h_gap_triage_v1.json ; docs/experiments/actionable-regime-confidence/runs/20260511T180420-codex-native-subhour-overlap-blocker-v1/native-subhour-overlap/native_subhour_overlap_blocker_v1.json`
  Coverage: strict exact 1h accepted=41/156; native subhour gate=native_subhour_overlap_blocker_v1=no_source_overlap_0of4_cells
  Gap: Strict exact 1h remains partial and native subhour source overlap remains 0/4.
- `blocked` - Source-panel recency extends beyond 2026-01-30 before provider candles after that date are promoted.
  Evidence: `docs/experiments/actionable-regime-confidence/runs/20260511T181454-codex-stock-regime-upstream-refresh-audit-v1/upstream-refresh/stock_regime_upstream_refresh_audit_v1.json`
  Coverage: stock_regime_upstream_refresh_audit_v1=no_new_upstream_recency_extension
  Gap: Known upstream source package still matches local; no newer source-owned recency extension rows.
- `blocked` - Direct Manipulation full species coverage uses direct positive rows plus matched normal controls.
  Evidence: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.json ; docs/experiments/actionable-regime-confidence/runs/20260511T182601-codex-direct-manipulation-source-scan-v2/direct-source-scan/direct_manipulation_source_scan_v2.json`
  Coverage: scoped direct ready=True; full species complete=False; source scan=blocked_no_ready_direct_species_source
  Gap: Missing spoofing/layering, quote stuffing, pinging, bear raid/painting tape, and social/text pump-dump matched-negative row sources.
- `pass_guardrail` - Do not rely on proxy signals or generated/OHLCV-only labels for completion.
  Evidence: `docs/experiments/actionable-regime-confidence/runs/20260511T183328-codex-external-source-label-candidate-screen-v1/external-source-label-screen/external_source_label_candidate_screen_v1.json`
  Coverage: External NIFTY/IDX candidates were screened but not promoted.
  Gap: No proxy promotion occurred; objective remains open.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T183632-current-goal-completion-audit-v18-after-external-source-screen/completion-audit/current_goal_completion_audit_v18_after_external_source_screen.json`
- Checklist CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T183632-current-goal-completion-audit-v18-after-external-source-screen/completion-audit/current_goal_completion_audit_v18_checklist.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T183632-current-goal-completion-audit-v18-after-external-source-screen/checks/current_goal_completion_audit_v18_after_external_source_screen_assertions.out`
