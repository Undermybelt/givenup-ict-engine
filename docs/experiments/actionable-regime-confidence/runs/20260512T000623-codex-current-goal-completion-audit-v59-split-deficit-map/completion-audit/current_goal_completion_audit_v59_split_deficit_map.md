# Current Goal Completion Audit v59 Split Deficit Map

- Run id: `20260512T000623-codex-current-goal-completion-audit-v59-split-deficit-map`
- Board hash at start: `8593cb09cabc29d6b9b99367d6d1f755bb76a939a67eafb7399ced39a7a3fe96`
- Minimum all-success rows for Wilson95 >= 0.95: `73`.
- Live R6 verifier: `schema_ready_unscored` with positives `73` and controls `73`.
- R6 pooled Wilson gate: `true`.
- R6 split gates blocked: `true`.
- Direct species closed: `false`.
- Provider/downstream commands all returned zero: `true`.
- Gate result: `current_goal_completion_audit_v59=not_complete_r6_split_species_r5_r3_blocked`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Key Deficits
- Chronological split supports are train/calibration/test `38/17/18`; fixed-role deficits to Wilson95 are `35/56/55` paired rows.
- Best exact-symbol bucket still needs `64` paired rows; all current exact-symbol buckets would require `2559` paired rows if this all-bucket gate is retained.
- Best exact-venue bucket still needs `44` paired rows; all current exact-venue buckets would require `732` paired rows if this all-bucket gate is retained.
- Missing direct species remain: `quote_stuffing`, `pinging`, `bear_raid_or_painting_tape`, and `pump_dump_social_text_or_onchain`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T000623-codex-current-goal-completion-audit-v59-split-deficit-map/completion-audit/current_goal_completion_audit_v59_split_deficit_map.json`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T000623-codex-current-goal-completion-audit-v59-split-deficit-map/completion-audit/current_goal_completion_audit_v59_checklist.csv`
- Split deficit CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T000623-codex-current-goal-completion-audit-v59-split-deficit-map/completion-audit/r6_split_deficit_map_v59.csv`
- Species deficit CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T000623-codex-current-goal-completion-audit-v59-split-deficit-map/completion-audit/r6_direct_species_deficit_v59.csv`
- Command manifest: `docs/experiments/actionable-regime-confidence/runs/20260512T000623-codex-current-goal-completion-audit-v59-split-deficit-map/completion-audit/current_goal_completion_audit_v59_commands.csv`

## Next
Acquire direct event/order-lifecycle rows that deliberately fill chronological calibration/test support and concentrate on existing exact symbols/venues, while adding missing non-spoofing direct species; rerun V58 calibration and keep R5/R3 blocked.
