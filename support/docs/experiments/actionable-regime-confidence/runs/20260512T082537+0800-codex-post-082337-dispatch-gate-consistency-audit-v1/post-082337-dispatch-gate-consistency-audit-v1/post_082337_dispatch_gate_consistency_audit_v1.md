# Post-082337 Dispatch Gate Consistency Audit v1

Run id: `20260512T082537+0800-codex-post-082337-dispatch-gate-consistency-audit-v1`

Gate result: `post_082337_dispatch_gate_consistency_audit_v1=contradictory_unlock_flags_fail_closed_no_promotion`

## Scope

Read-only consistency audit for `082337` after its command output reported a
`no_required_root_or_dispatch_unlock` gate while also setting raw unlock booleans
to true. This audit does not mutate target roots, approve R3/R5/R6 evidence,
send owner-export requests, run direct verifier, split calibration, canonical
merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking,
execution-tree promotion, make a trade claim, or call `update_goal`.

## Contradictions

- `082337_valid_required_root_unlock_true_under_no_unlock_gate`
- `082337_source_control_evidence_acquired_true_under_no_unlock_gate`
- `082337_r3_native_subhour_unlock_true_under_no_unlock_gate`
- `082337_valid_required_root_unlock_conflicts_with_082314`
- `082337_source_control_evidence_conflicts_with_082314`
- `dispatch_not_sent_and_no_approved_operator_path`
- `owner_export_dispatch_drafts_missing_in_082337_readback`

## Decision

Treat `082337` as fail-closed diagnostic output only. File presence under the R3
native-subhour root does not satisfy Board A's accepted source/control contract,
and `082314` remains the controlling local arrival-poll readback for this slice:
valid required-root unlock false and source/control evidence acquired false.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false;
R3 native-subhour unlock false; valid required-root unlock false; source/control
evidence acquired false; canonical merge false; selected-data AutoQuant promotion
false; downstream promotion rerun false; strict full objective false; trade usable
false; promotion allowed false; `update_goal=false`.

## Next

Continue source/control acquisition only. Use an approved operator path for owner
exports, explicit same-exhibit `FLIP` control approval, or verifier-native R6/R5/R3
source/control roots before any canonical merge or downstream promotion rerun.
