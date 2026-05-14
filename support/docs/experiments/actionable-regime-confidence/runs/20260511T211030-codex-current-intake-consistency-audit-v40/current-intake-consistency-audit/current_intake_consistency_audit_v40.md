# Current Intake Consistency Audit v40

Decision: `current_intake_consistency_audit_v40=live_r6_rows_9x9_calibration_blocked`.

Result:
- Ready intake roots: `1/4`; ready roots: `direct_manipulation_row_intake`.
- R6 live CSV rows parsed with `csv.DictReader`: positives `9`, matched negatives `9`, groups `8`.
- R6 breadth: dates `6`, symbols/contracts `4`, venues `2`.
- R6 Wilson95 min LCB: `0.700855`; support required per class for all-success Wilson95 >=0.95: `73`.
- Chronological split ok: `true`; heldout symbol/venue ok: `true`.
- Broad normal sample: `false`; species coverage ok: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

Checklist:

| ID | Status | Gap |
|---|---|---|
| `R0` | `pass_checked` | `` |
| `R1` | `fail_not_full` | `Full per-regime >=95 confidence across all required axes is not complete.` |
| `R2_R4` | `fail_blocked` | `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json` |
| `R3` | `fail_blocked` | `native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json` |
| `R5` | `fail_blocked` | `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json` |
| `R6` | `partial_current_rows_calibration_blocked` | `positive_support;negative_support;wilson95_lcb;broad_normal_sample;direct_species_coverage` |
| `R7` | `pass_guardrail` | `` |
| `R8` | `fail_blocked` | `Strict full objective is not achieved; update_goal remains false.` |

Next:
Acquire broad source-owned normal controls and enough additional direct-species positive/control rows; separately populate R2/R3/R4/R5 required intake roots before rerunning completion audit.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T211030-codex-current-intake-consistency-audit-v40/current-intake-consistency-audit/current_intake_consistency_audit_v40.json`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T211030-codex-current-intake-consistency-audit-v40/current-intake-consistency-audit/current_intake_consistency_audit_v40_gates.csv`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T211030-codex-current-intake-consistency-audit-v40/current-intake-consistency-audit/current_intake_consistency_audit_v40_checklist.csv`
- Intake-root CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T211030-codex-current-intake-consistency-audit-v40/current-intake-consistency-audit/current_intake_consistency_audit_v40_intake_roots.csv`
- Direct verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T211030-codex-current-intake-consistency-audit-v40/current-intake-consistency-audit/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T211030-codex-current-intake-consistency-audit-v40/checks/current_intake_consistency_audit_v40_assertions.out`
