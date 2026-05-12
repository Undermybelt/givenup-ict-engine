# R3/R5 Source-Label Intake Presence Sweep v1

Decision: `r3_r5_source_label_intake_presence_sweep_v1=non_r6_intake_roots_absent_or_incomplete`.

Result:
- Non-R6 intake roots ready: `0/3`.
- Required files present: `0/6`.
- Source-label equivalence verifier status: `blocked`.
- R5 source-panel recency verifier status: `blocked`.
- R3 native-subhour root ready: `false`.
- Bounded local candidate hits in `/tmp`, `/private/tmp`, and `Downloads`: `0`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

Intake Roots:

| Root | Ready | Missing |
|---|---:|---|
| `source_label_equivalence` | `false` | `source_label_equivalence_rows.csv, source_label_equivalence_provenance.json` |
| `native_subhour_source_label` | `false` | `native_subhour_source_label_rows.csv, native_subhour_source_label_provenance.json` |
| `source_panel_recency_extension` | `false` | `stock_market_regimes_2026_extension.csv, source_panel_recency_provenance.json` |

Next:
- Preserve the active V62 R6 owner-export next action. For non-R6 hardening, populate the missing source-label equivalence, native-subhour, or R5 recency intake roots with owner-approved/source-owned files before rerunning the unchanged gates.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T002807-codex-r3-r5-source-label-intake-presence-sweep-v1/r3-r5-source-label-intake-presence-sweep/r3_r5_source_label_intake_presence_sweep_v1.json`
- Intake roots CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T002807-codex-r3-r5-source-label-intake-presence-sweep-v1/r3-r5-source-label-intake-presence-sweep/r3_r5_source_label_intake_roots_v1.csv`
- Candidate hits CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T002807-codex-r3-r5-source-label-intake-presence-sweep-v1/r3-r5-source-label-intake-presence-sweep/r3_r5_source_label_intake_candidate_hits_v1.csv`
- Command output: `docs/experiments/actionable-regime-confidence/runs/20260512T002807-codex-r3-r5-source-label-intake-presence-sweep-v1/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T002807-codex-r3-r5-source-label-intake-presence-sweep-v1/checks/r3_r5_source_label_intake_presence_sweep_v1_assertions.out`
