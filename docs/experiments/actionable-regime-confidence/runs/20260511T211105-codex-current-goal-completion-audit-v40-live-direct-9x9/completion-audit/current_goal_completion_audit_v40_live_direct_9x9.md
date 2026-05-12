# Current Goal Completion Audit v40 Live Direct 9x9

Decision: `current_goal_completion_audit_v40=live_direct_9x9_schema_ready_calibration_blocked`.

Result:
- Direct verifier: `schema_ready_unscored`; positives `9`; matched negatives `9`; matched groups `8`.
- Breadth: dates `6`, symbols/contracts `4`, venues `2`, sessions `2`.
- Wilson95 LCB positive/negative/min: `0.700855` / `0.700855` / `0.700855`.
- Chronological split ok: `true`; heldout symbol/venue ok: `true`.
- Broad normal sample: `false`; direct species coverage ok: `false`.
- Ready intake roots: `1/4`; ready roots: `direct_manipulation_row_intake`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

Gates:

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `positive_support` | `9` | `50` | `false` |
| `negative_support` | `9` | `50` | `false` |
| `chronological_split` | `6` | `2` | `true` |
| `heldout_symbol_or_venue` | `symbols=4;venues=2` | `symbol>=2 or venue>=2` | `true` |
| `wilson95_lcb` | `0.700855` | `>=0.95` | `false` |
| `broad_normal_sample` | `CFTC same-report or same-complaint genuine-order legs are schema/control seeds only; they are not broad normal-market heldout controls.` | `source-owned broad normal activity sample` | `false` |
| `direct_species_coverage` | `spoofing_layering` | `spoofing_layering;quote_spoofing;quote_stuffing;pinging;bear_raid;painting_tape` | `false` |

Next:
Acquire source-owned or owner-approved broad same-schema normal controls and enough positive rows across additional direct Manipulation species; separately populate R2/R3/R4/R5 source/provenance roots.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T211105-codex-current-goal-completion-audit-v40-live-direct-9x9/completion-audit/current_goal_completion_audit_v40_live_direct_9x9.json`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T211105-codex-current-goal-completion-audit-v40-live-direct-9x9/completion-audit/current_goal_completion_audit_v40_gates.csv`
- Intake-root CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T211105-codex-current-goal-completion-audit-v40-live-direct-9x9/completion-audit/current_goal_completion_audit_v40_intake_roots.csv`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T211105-codex-current-goal-completion-audit-v40-live-direct-9x9/completion-audit/current_goal_completion_audit_v40_checklist.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T211105-codex-current-goal-completion-audit-v40-live-direct-9x9/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T211105-codex-current-goal-completion-audit-v40-live-direct-9x9/checks/current_goal_completion_audit_v40_live_direct_9x9_assertions.out`
