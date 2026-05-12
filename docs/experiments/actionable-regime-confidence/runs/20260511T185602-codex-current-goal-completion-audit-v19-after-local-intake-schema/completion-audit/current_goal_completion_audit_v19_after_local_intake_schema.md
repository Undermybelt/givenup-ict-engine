# Current Goal Completion Audit v19 After Local Intake Schema

Run ID: `20260511T185602-codex-current-goal-completion-audit-v19-after-local-intake-schema`

## Objective

Every active regime must have calibrated >=95% confidence and must retain suitable confidence on other markets/species and other cycles/timeframes.

## Decision

`current_goal_completion_audit_v19=scoped_95_present_local_schema_sweep_confirms_full_objective_blocked`

- Strict full objective achieved: `false`; `update_goal=false`.
- Scoped active-lane `>=95%` evidence remains present, but it is not enough for the full objective.
- Accepted rows added: `0`; new confidence gate: `false`.

## Blocking Requirements

- `validated on other markets/species with source-owned or owner-approved labels`: No full source-label equivalence; public/partial slots do not form owner-approved MainRegimeV2 cross-market evidence.
- `local intake files can supply missing source-owned rows/provenance`: No local file matches the external price-root, recency, direct-positive, or direct-control required schemas.
- `validated on other cycles/timeframes with suitable confidence`: Strict exact 1h remains partial and native sub-hour source overlap remains zero.
- `Jan-2026 source tail can promote current strict-1h gate`: Tail support is future-gate preflight only and cannot retroactively accept the fixed 2024/2025 strict gate.
- `direct Manipulation full species/variety coverage with matched controls`: Scoped direct varieties exist, but spoofing/layering lacks matched negatives and quote stuffing/pinging/bear raid/painting tape remain missing.

## Key Evidence

- Source-label other-market gate: `source_label_other_market_readback_v1=partial_sources_no_full_equivalence`; accepted factor/gate total `0`.
- Local intake schema sweep exact matches: `0`; strong partial matches `0`.
- Timeframe/cycle readback gate: `timeframe_cycle_coverage_readback_v1=strict_1h_partial_native_subhour_recency_blocked`.
- Strict exact `1h`: `41/156`.
- Native sub-hour overlap: `0/4`.
- Direct Manipulation remaining unaccepted varieties: `6`.
- Direct missing-species screen gate: `direct_missing_species_source_screen_v1=no_ready_positive_control_source`; ready sources `0`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T185602-codex-current-goal-completion-audit-v19-after-local-intake-schema/completion-audit/current_goal_completion_audit_v19_after_local_intake_schema.json`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T185602-codex-current-goal-completion-audit-v19-after-local-intake-schema/completion-audit/current_goal_completion_audit_v19_checklist.csv`
- Unmet requirements CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T185602-codex-current-goal-completion-audit-v19-after-local-intake-schema/completion-audit/current_goal_completion_audit_v19_unmet_requirements.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T185602-codex-current-goal-completion-audit-v19-after-local-intake-schema/checks/current_goal_completion_audit_v19_after_local_intake_schema_assertions.out`
