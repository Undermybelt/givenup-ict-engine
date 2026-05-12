# Current Goal Full Objective Coverage Audit v15

Run id: `20260511T162537+0800-current-goal-full-objective-coverage-audit-v15`.

## Objective Restatement

The user-requested completion criteria are concrete:

1. Every active regime has a calibrated confidence floor at or above 95%.
2. Evidence survives validation on other markets.
3. Evidence survives validation on other timeframes/cycles.
4. Full-cycle coverage is not missing or stale.
5. Full-species coverage is not missing.
6. Final success is not reported until all requirements above are covered by artifacts, not proxies.

## Decision

- Scoped active-lane 95% status: `accepted_95`.
- Full objective achieved: `false`.
- `update_goal`: `false`.
- Gate result: `full_objective_coverage_audit_v15=scoped_95_present_full_cycle_full_species_still_blocked`.

## Prompt-To-Artifact Checklist

| Requirement | Status | Evidence | Notes |
|---|---|---|---|
| `named_authoritative_markdown_updated` | `pass` | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` | same board owns cursor, sections, and Evidence Ledger |
| `every_active_regime_has_95_confidence` | `pass_scoped` | `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.json` | accepted lanes 5/5: Bull,Bear,Sideways,Crisis,Manipulation |
| `mainregimev2_roots_are_exact` | `pass` | `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.json` | Bull,Bear,Sideways,Crisis |
| `price_root_confidence_floor_ge_95` | `pass` | `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.json` | min price-root floor=0.9529358324 |
| `manipulation_direct_not_proxy` | `pass_scoped` | `docs/experiments/actionable-regime-confidence/runs/20260511T131311-codex-direct-manipulation-variety-matrix-v1/direct-manipulation/direct_manipulation_variety_matrix_v1.json` | scoped direct floor=0.967945; full coverage=False |
| `validate_on_other_markets` | `partial` | `docs/experiments/actionable-regime-confidence/runs/20260511T141910-codex-exact-1h-source-universe-expansion-v1/exact-1h-universe/exact_1h_source_universe_expansion_v1.json` | 39-ticker source panel context exists, but full NQ/QQQ/futures/crypto/FX source-label equivalence is not closed |
| `validate_on_other_timeframes` | `partial` | `docs/experiments/actionable-regime-confidence/runs/20260511T131922-codex-source-consensus-axiswise-timeframe-gate-v1/source-consensus-axiswise/source_consensus_axiswise_timeframe_gate_v1.json` | daily/1w/1mo/exact 1h context exists; native sub-hour source overlap remains blocked |
| `full_cycle_coverage` | `partial` | `docs/experiments/actionable-regime-confidence/runs/20260511T155959-current-goal-completion-audit-v14-after-consumer-map/completion-audit/current_goal_completion_audit_v14_after_consumer_map.json` | source recency remains capped at stock-market-regimes panel through 2026-01-30 |
| `full_species_coverage` | `fail` | `docs/experiments/actionable-regime-confidence/runs/20260511T155959-current-goal-completion-audit-v14-after-consumer-map/completion-audit/current_goal_completion_audit_v14_after_consumer_map.json` | full species/cross-market equivalence missing beyond source-panel context |
| `ticker_specific_strict_support` | `partial` | `docs/experiments/actionable-regime-confidence/runs/20260511T141910-codex-exact-1h-source-universe-expansion-v1/exact-1h-universe/exact_1h_source_universe_expansion_v1.json` | strict accepted ticker/root rows=41/156 |
| `direct_manipulation_full_varieties` | `fail` | `docs/experiments/actionable-regime-confidence/runs/20260511T131311-codex-direct-manipulation-variety-matrix-v1/direct-manipulation/direct_manipulation_variety_matrix_v1.json` | missing/blocked varieties include spoofing/layering, quote stuffing, pinging, bear raid or painting tape |
| `do_not_report_final_success_until_complete` | `pass_guardrail` | `docs/experiments/actionable-regime-confidence/runs/20260511T155959-current-goal-completion-audit-v14-after-consumer-map/completion-audit/current_goal_completion_audit_v14_after_consumer_map.json` | full_objective_achieved=false and call_update_goal=false |

## Prioritized Work Orders

| Priority | Gap | Next Artifact | Acceptance |
|---|---|---|---|
| `P0` | `full_species_cross_market_equivalence` | `source_label_equivalence_request_v1` | owner-approved or source-native labels for NQ/QQQ/futures/crypto/FX; no OHLCV proxy labels |
| `P0` | `source_recency_after_2026_01_30` | `source_panel_recency_extension_v1` | source-owned labels beyond 2026-01-30, then rerun exact same gates |
| `P1` | `ticker_specific_strict_support` | `strict_ticker_root_gap_selector_v1` | increase strict ticker/root accepted rows beyond 41/156 without pooled-context promotion |
| `P1` | `native_subhour_timeframe_overlap` | `native_subhour_source_overlap_after_recency_v1` | source-date overlap exists for 1m/5m/15m/30m/90m before calibration |
| `P2` | `direct_manipulation_missing_varieties` | `direct_row_intake_positive_negative_exports_v1` | source-owned positive rows plus matched negatives for spoofing/layering/quote-stuffing/pinging/bear-raid varieties |

## Next

Start with `source_label_equivalence_request_v1` or `source_panel_recency_extension_v1`. Do not run more broad negative sweeps, do not promote proxies, and do not call `update_goal`.
