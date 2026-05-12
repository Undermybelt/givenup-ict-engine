# Current Goal Completion Audit v42 After Duplicate Cleanup

- Decision: `current_goal_completion_audit_v42=duplicate_cleanup_still_blocked`.
- Current cursor: `20260511T212004+0800-codex-r6-shak-duplicate-row-cleanup-v1`.
- Direct R6 rows after cleanup: positive `35`, matched negative `35`.
- Direct R6 Wilson95 min LCB: `0.901099`; support ok: `false`; broad normal sample: `false`.
- Ready intake roots: `1/4`.
- Blocked audit rows: `8/8`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Gates

| Requirement | Observed | Required | Pass |
|---|---|---|---:|
| `R1 active-regime confidence` | ``blocked` for strict full objective; prior scoped active-lane `95` evidence remains preserved.` | `all active regimes >=95 source-owned/owner-approved` | `false` |
| `R2 other-market/source-label equivalence` | `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json` | `required files present` | `false` |
| `R3 other-cycle/native-subhour validation` | `native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json` | `required files present` | `false` |
| `R5 source-panel recency extension` | `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json` | `required files present` | `false` |
| `R6 direct support` | `35/35` | `>=50/50` | `false` |
| `R6 direct Wilson95` | `0.901099` | `>=0.95` | `false` |
| `R6 broad normal sample` | `CFTC public order/complaint same-event genuine-order legs are source-described schema/control seeds only; they are not a broad normal-market calibration sample.` | `broad source-owned normal controls` | `false` |
| `R8 completion gate` | `blocked gates remain` | `all rows pass` | `false` |

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T212256-codex-current-goal-completion-audit-v42-after-duplicate-cleanup/completion-audit/current_goal_completion_audit_v42_after_duplicate_cleanup.json`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T212256-codex-current-goal-completion-audit-v42-after-duplicate-cleanup/completion-audit/current_goal_completion_audit_v42_gates.csv`
- Intake-root CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T212256-codex-current-goal-completion-audit-v42-after-duplicate-cleanup/completion-audit/current_goal_completion_audit_v42_intake_roots.csv`
- Verifier outputs: `docs/experiments/actionable-regime-confidence/runs/20260511T212256-codex-current-goal-completion-audit-v42-after-duplicate-cleanup/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T212256-codex-current-goal-completion-audit-v42-after-duplicate-cleanup/checks/current_goal_completion_audit_v42_after_duplicate_cleanup_assertions.out`
